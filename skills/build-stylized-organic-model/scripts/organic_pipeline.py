#!/usr/bin/env python3
"""Rebuild of the 'build-stylized-organic-model' static route from SKILL.md alone.

plan.json -> oriented masses (ellipsoid / superellipsoid / tapered capsule, with taper,
bend, bulge/dent, subtract) -> smooth-union implicit volume -> grid sample ->
marching cubes (one shared-edge mesh) -> manifold checks -> Blender Decimate(COLLAPSE)
QEM to budget -> normalize to height 1.0 (Z up, Y forward) -> materials (per-mass +
color_regions) -> separate eye meshes -> OBJ (Z-up, flat) + GLB (Y-up, flat normals) ->
Pillow depth-sorted flat previews + 96px isometric + report.json.

Usage:
  python3 organic_pipeline.py build plan.json --out DIR/name
  python3 organic_pipeline.py sheet out.jpg name1 name2 ...   (combined isometric+side sheet)
"""
import json, sys, os, subprocess, argparse, tempfile, math
import numpy as np
from skimage.measure import marching_cubes
import trimesh
from PIL import Image, ImageDraw

BLENDER = "blender"
HERE = os.path.dirname(os.path.abspath(__file__))


# ---------------------------------------------------------------- frames
def euler_R(deg):
    rx, ry, rz = np.radians(deg if deg is not None else [0, 0, 0])
    cx, sx, cy, sy, cz, sz = np.cos(rx), np.sin(rx), np.cos(ry), np.sin(ry), np.cos(rz), np.sin(rz)
    Rx = np.array([[1, 0, 0], [0, cx, -sx], [0, sx, cx]])
    Ry = np.array([[cy, 0, sy], [0, 1, 0], [-sy, 0, cy]])
    Rz = np.array([[cz, -sz, 0], [sz, cz, 0], [0, 0, 1]])
    return Rz @ Ry @ Rx  # local -> world


def mirror_part(p):
    q = json.loads(json.dumps(p))
    q["name"] = p["name"] + "_L" if not p["name"].endswith("_R") else p["name"][:-2] + "_L"
    for k in ("center", "a", "b"):
        if k in q:
            q[k][0] = -q[k][0]
    if "euler" in q:  # mirror across X: negate rotations about Y and Z
        q["euler"] = [q["euler"][0], -q["euler"][1], -q["euler"][2]]
    q.pop("mirror", None)
    return q


def expand(parts):
    out = []
    for p in parts:
        out.append(p)
        if p.get("mirror"):
            out.append(mirror_part(p))
    return out


# ---------------------------------------------------------------- SDFs
def to_local(P, p):
    R = euler_R(p.get("euler"))
    L = (P - np.array(p["center"])) @ R  # R^T (P-c)
    r = np.array(p["radii"], float)
    # bend about local x: rotate (y,z) by angle proportional to z/rz  (deg total at z=rz)
    if p.get("bend"):
        th = np.radians(p["bend"]) * (L[:, 2] / r[2])
        c, s = np.cos(th), np.sin(th)
        y, z = L[:, 1].copy(), L[:, 2].copy()
        L[:, 1], L[:, 2] = c * y + s * z, -s * y + c * z
    # taper along local z: section scale s = 1 - taper*z/rz  (taper>0 narrows toward +z)
    if p.get("taper"):
        s = np.clip(1.0 - p["taper"] * (L[:, 2] / r[2]), 0.25, 3.0)
        L[:, 0] /= s
        L[:, 1] /= s
    return L, r


def sdf_part(P, p):
    t = p["type"]
    if t in ("ellipsoid", "superellipsoid"):
        L, r = to_local(P, p)
        e = p.get("exponent", 2.0)
        if t == "ellipsoid" or abs(e - 2.0) < 1e-6:
            k0 = np.linalg.norm(L / r, axis=1)
            k1 = np.linalg.norm(L / (r * r), axis=1)
            return k0 * (k0 - 1.0) / np.maximum(k1, 1e-9)
        f = (np.abs(L / r) ** e).sum(1) ** (1.0 / e)
        return (f - 1.0) * r.min()
    if t == "capsule":
        a, b = np.array(p["a"], float), np.array(p["b"], float)
        r0 = p["r"][0]; r1 = p["r"][1] if len(p["r"]) > 1 else r0
        ba = b - a
        h = np.clip(((P - a) @ ba) / (ba @ ba), 0, 1)
        d = np.linalg.norm(P - (a + h[:, None] * ba), axis=1)
        return d - (r0 + (r1 - r0) * h)
    raise ValueError(t)


def smin(a, b, k):
    if k <= 0:
        return np.minimum(a, b)
    h = np.clip(0.5 + 0.5 * (b - a) / k, 0, 1)
    return b * (1 - h) + a * h - k * h * (1 - h)


def smax(a, b, k):
    return -smin(-a, -b, k)


def field(P, plan):
    parts = expand(plan["masses"])
    d = None
    for p in parts:
        s = sdf_part(P, p)
        k = p.get("blend", plan.get("default_blend", 0.01))
        if d is None:
            d = s
        elif p.get("op") == "subtract":
            d = smax(d, -s, k)
        else:
            d = smin(d, s, k)
    for m in expand(plan.get("modifiers", [])):  # localized bulge (+) / dent (-)
        c = np.array(m["center"])
        g = np.exp(-(np.linalg.norm(P - c, axis=1) / m["radius"]) ** 2)
        amt = m["amount"] if m["type"] == "bulge" else -m["amount"]
        d = d - amt * g
    return d


def nearest_part(P, plan, parts=None):
    parts = parts or [p for p in expand(plan["masses"]) if p.get("op") != "subtract"]
    D = np.stack([sdf_part(P, p) for p in parts], 1)
    return [parts[i] for i in D.argmin(1)]


# ---------------------------------------------------------------- topology checks
def topo_report(V, F):
    rep = {}
    rep["finite_vertices"] = bool(np.isfinite(V).all())
    rep["valid_indices"] = bool(F.min() >= 0 and F.max() < len(V))
    rep["vertices"] = int(len(V)); rep["triangles"] = int(len(F))
    E = np.sort(np.concatenate([F[:, [0, 1]], F[:, [1, 2]], F[:, [2, 0]]]), 1)
    ue, cnt = np.unique(E, axis=0, return_counts=True)
    rep["edges"] = int(len(ue))
    rep["boundary_edges"] = int((cnt == 1).sum())
    rep["nonmanifold_edges"] = int((cnt > 2).sum())
    # winding: each directed edge should appear exactly once
    De = np.concatenate([F[:, [0, 1]], F[:, [1, 2]], F[:, [2, 0]]])
    _, dc = np.unique(De, axis=0, return_counts=True)
    rep["winding_consistent"] = bool((dc == 1).all())
    # closed vertex links: the link (opposite edges) of each vertex forms exactly one cycle
    from collections import defaultdict
    link = defaultdict(list)
    for a, b, c in F:
        link[a].append((b, c)); link[b].append((c, a)); link[c].append((a, b))
    bad = 0
    for v, es in link.items():
        nxt = {}
        ok = True
        for x, y in es:
            if x in nxt: ok = False; break
            nxt[x] = y
        if ok:
            start = es[0][0]; cur = start; n = 0
            while True:
                if cur not in nxt: ok = False; break
                cur = nxt[cur]; n += 1
                if cur == start or n > len(es): break
            ok = ok and n == len(es) and cur == start
        bad += (not ok)
    rep["bad_vertex_links"] = int(bad)
    tri = V[F]
    area = 0.5 * np.linalg.norm(np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0]), axis=1)
    rep["degenerate_faces"] = int((area < 1e-12).sum())
    rep["duplicate_faces"] = int(len(F) - len(np.unique(np.sort(F, 1), axis=0)))
    rep["loose_vertices"] = int(len(V) - len(np.unique(F)))
    m = trimesh.Trimesh(V, F, process=False)
    rep["components"] = int(len(m.split(only_watertight=False)))
    rep["euler_characteristic"] = int(len(V) - len(ue) + len(F))
    vol = float(np.einsum("ij,ij->i", tri[:, 0], np.cross(tri[:, 1], tri[:, 2])).sum() / 6.0)
    rep["signed_volume"] = vol
    rep["volume_positive"] = vol > 0
    # sliver diagnostic (not a pass/fail in the skill): min angle stats
    def ang(a, b, c):
        u, w = b - a, c - a
        cs = np.einsum("ij,ij->i", u, w) / (np.linalg.norm(u, axis=1) * np.linalg.norm(w, axis=1) + 1e-15)
        return np.degrees(np.arccos(np.clip(cs, -1, 1)))
    mins = np.minimum(np.minimum(ang(tri[:, 0], tri[:, 1], tri[:, 2]), ang(tri[:, 1], tri[:, 2], tri[:, 0])), ang(tri[:, 2], tri[:, 0], tri[:, 1]))
    rep["sliver_faces_min_angle_lt_5deg"] = int((mins < 5).sum())
    rep["median_min_angle_deg"] = float(np.median(mins))
    rep["closed_manifold_ok"] = bool(rep["boundary_edges"] == 0 and rep["nonmanifold_edges"] == 0 and rep["winding_consistent"]
                                     and bad == 0 and rep["degenerate_faces"] == 0 and rep["duplicate_faces"] == 0
                                     and rep["loose_vertices"] == 0)
    return rep


# ---------------------------------------------------------------- eyes / accessories
def icosphere(sub, radius, center, scale=(1, 1, 1)):
    s = trimesh.creation.icosphere(subdivisions=sub, radius=1.0)
    V = s.vertices * np.array(scale) * radius + np.array(center)
    return V, np.array(s.faces)


def place_on_surface(guess, plan, embed):
    """Move a point along the field gradient until it sits on the zero set, then sink inward."""
    p = np.array(guess, float)
    for _ in range(60):
        d = field(p[None], plan)[0]
        eps = 1e-4
        g = np.array([(field((p + e)[None], plan)[0] - field((p - e)[None], plan)[0]) / (2 * eps)
                      for e in np.eye(3) * eps])
        g /= np.linalg.norm(g) + 1e-12
        p = p - d * g
        if abs(d) < 1e-5:
            break
    return p - g * embed, g


# ---------------------------------------------------------------- rendering (Pillow)
def view_basis(az_deg, el_deg):
    az, el = np.radians(az_deg), np.radians(el_deg)
    fwd = -np.array([np.cos(el) * np.sin(az), np.cos(el) * np.cos(az), np.sin(el)])  # camera looks along fwd
    up0 = np.array([0, 0, 1.0])
    right = np.cross(fwd, up0); right /= np.linalg.norm(right)
    up = np.cross(right, fwd)
    return right, up, fwd


def render(meshes, az, el, size, title=None, bg=(236, 236, 232), bounds=None):
    """meshes: list of (V, F, face_rgb[N,3] 0..1). Orthographic flat-shaded painter render."""
    right, up, fwd = view_basis(az, el)
    allV = np.concatenate([m[0] for m in meshes])
    if bounds is None:
        X = allV @ right; Y = allV @ up
        cx, cy = (X.max() + X.min()) / 2, (Y.max() + Y.min()) / 2
        span = max(X.max() - X.min(), Y.max() - Y.min()) * 1.12
    else:
        cx, cy, span = bounds
    ss = 3
    W = size * ss
    light = -fwd * 0.55 + up * 0.6 - right * 0.35
    light /= np.linalg.norm(light)
    zbuf = np.full((W, W), np.inf)
    cbuf = np.tile(np.array(bg, float), (W, W, 1))
    for V, F, C in meshes:  # true per-pixel z-buffer (painter sorting mis-ordered limbs in round 1)
        tri = V[F]
        n = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0])
        n /= np.linalg.norm(n, axis=1, keepdims=True) + 1e-15
        facing = n @ (-fwd) > 0
        shade = 0.38 + 0.62 * np.clip(n @ light, 0, 1)
        dz = tri @ fwd
        sx = ((tri @ right) - cx) / span * W + W / 2
        sy = W / 2 - ((tri @ up) - cy) / span * W
        for i in np.nonzero(facing)[0]:
            x, y, z = sx[i], sy[i], dz[i]
            x0, x1 = max(int(np.floor(x.min())), 0), min(int(np.ceil(x.max())), W - 1)
            y0, y1 = max(int(np.floor(y.min())), 0), min(int(np.ceil(y.max())), W - 1)
            if x1 < x0 or y1 < y0:
                continue
            X, Y = np.meshgrid(np.arange(x0, x1 + 1) + 0.5, np.arange(y0, y1 + 1) + 0.5)
            den = (y[1] - y[2]) * (x[0] - x[2]) + (x[2] - x[1]) * (y[0] - y[2])
            if abs(den) < 1e-12:
                continue
            a = ((y[1] - y[2]) * (X - x[2]) + (x[2] - x[1]) * (Y - y[2])) / den
            b = ((y[2] - y[0]) * (X - x[2]) + (x[0] - x[2]) * (Y - y[2])) / den
            c = 1 - a - b
            ins = (a >= -1e-6) & (b >= -1e-6) & (c >= -1e-6)
            Z = a * z[0] + b * z[1] + c * z[2]
            zb = zbuf[y0:y1 + 1, x0:x1 + 1]
            upd = ins & (Z < zb)
            zb[upd] = Z[upd]
            cbuf[y0:y1 + 1, x0:x1 + 1][upd] = np.clip(np.array(C[i]) * shade[i], 0, 1) * 255
    img = Image.fromarray(cbuf.astype(np.uint8)).resize((size, size), Image.LANCZOS)
    if title:
        ImageDraw.Draw(img).text((6, 4), title, fill=(60, 60, 60))
    return img


# ---------------------------------------------------------------- export
def write_obj(path, body, eyes, mats):
    """body/eyes: (V,F,matnames). Z-up source triangles, flat shading via per-face normals."""
    base = os.path.splitext(path)[0]
    mtl = base + ".mtl"
    with open(mtl, "w") as f:
        for name, m in mats.items():
            r, g, b = m["color"]
            f.write(f"newmtl {name}\nKd {r:.4f} {g:.4f} {b:.4f}\nKa 0 0 0\nKs 0.02 0.02 0.02\nNs 4\nd 1\nillum 1\n\n")
    with open(path, "w") as f:
        f.write(f"# organic_pipeline: Z up, Y forward, meters, flat shading, static, no rig\nmtllib {os.path.basename(mtl)}\n")
        off = 0; noff = 0
        for oname, (V, F, M) in [("body", body)] + [(f"eye_{i}", e) for i, e in enumerate(eyes)]:
            f.write(f"o {oname}\n")
            for v in V:
                f.write(f"v {v[0]:.6f} {v[1]:.6f} {v[2]:.6f}\n")
            tri = V[F]
            N = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0])
            N /= np.linalg.norm(N, axis=1, keepdims=True) + 1e-15
            for n in N:
                f.write(f"vn {n[0]:.5f} {n[1]:.5f} {n[2]:.5f}\n")
            f.write("s off\n")
            for mname in sorted(set(M)):
                f.write(f"usemtl {mname}\n")
                for i in np.nonzero(np.array(M) == mname)[0]:
                    a, b, c = F[i] + 1 + off; n = i + 1 + noff
                    f.write(f"f {a}//{n} {b}//{n} {c}//{n}\n")
            off += len(V); noff += len(F)


def write_glb(path, body, eyes, mats):
    """Y-up glTF: (x,y,z)_Zup -> (-x, z, y) so asset front (+Y) faces glTF +Z. Flat normals by unwelding."""
    Rm = np.array([[-1, 0, 0], [0, 0, 1], [0, 1, 0]], float)
    scene = trimesh.Scene()
    split_vertices = 0
    for oname, (V, F, M) in [("body", body)] + [(f"eye_{i}", e) for i, e in enumerate(eyes)]:
        M = np.array(M)
        for mname in sorted(set(M)):
            idx = np.nonzero(M == mname)[0]
            sub = trimesh.Trimesh(V @ Rm.T, F[idx], process=False)
            sub.remove_unreferenced_vertices()
            sub = trimesh.Trimesh(sub.vertices[sub.faces].reshape(-1, 3), np.arange(len(sub.faces) * 3).reshape(-1, 3), process=False)
            fn = sub.face_normals
            sub.vertex_normals = np.repeat(fn, 3, axis=0)
            c = mats[mname]["color"]
            sub.visual = trimesh.visual.TextureVisuals(material=trimesh.visual.material.PBRMaterial(
                name=mname, baseColorFactor=[c[0], c[1], c[2], 1.0], metallicFactor=0.0,
                roughnessFactor=mats[mname].get("roughness", 0.85)))
            split_vertices += len(sub.vertices)
            scene.add_geometry(sub, node_name=f"{oname}_{mname}", geom_name=f"{oname}_{mname}")
    data = trimesh.exchange.gltf.export_glb(scene, include_normals=True)
    with open(path, "wb") as f:
        f.write(data)
    return split_vertices


# ---------------------------------------------------------------- build
def build(plan_path, out):
    plan = json.load(open(plan_path))
    os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
    rep = {"plan": os.path.abspath(plan_path), "subject": plan.get("subject"), "route": "implicit smooth-union -> marching cubes -> Blender Decimate COLLAPSE (QEM)"}
    # 1. sample
    parts = expand(plan["masses"])
    lo = np.array(plan["bounds"][0], float); hi = np.array(plan["bounds"][1], float)
    res = plan.get("resolution", 160)
    h = (hi - lo).max() / res
    axes = [np.arange(lo[i] - 2 * h, hi[i] + 2 * h, h) for i in range(3)]
    G = np.stack(np.meshgrid(*axes, indexing="ij"), -1).reshape(-1, 3)
    D = np.concatenate([field(G[i:i + 400000], plan) for i in range(0, len(G), 400000)]).reshape([len(a) for a in axes])
    rep["grid"] = {"shape": list(D.shape), "voxel": h}
    # guard: field must be positive on the grid boundary (closed surface)
    edge_min = min(D[0].min(), D[-1].min(), D[:, 0].min(), D[:, -1].min(), D[:, :, 0].min(), D[:, :, -1].min())
    rep["grid_boundary_clear"] = bool(edge_min > 0)
    V, F, _, _ = marching_cubes(D, 0.0, spacing=(h, h, h))
    V = V + np.array([a[0] for a in axes])
    F = F.astype(np.int64)
    m = trimesh.Trimesh(V, F, process=True)  # weld coincident verts -> one shared-edge mesh
    comps = m.split(only_watertight=False)
    rep["raw_components"] = len(comps)
    if len(comps) > 1:
        m = max(comps, key=lambda c: len(c.faces))
    V, F = np.array(m.vertices), np.array(m.faces)
    raw = topo_report(V, F)
    if not raw["volume_positive"]:
        F = F[:, ::-1]; raw = topo_report(V, F); rep["flipped_winding_after_mc"] = True
    rep["raw_mesh"] = raw
    # 2. QEM (Blender)
    target = plan["target_triangles"]
    with tempfile.TemporaryDirectory() as td:
        np.savez(f"{td}/in.npz", V=V, F=F)
        r = subprocess.run([BLENDER, "-b", "--factory-startup", "-P", os.path.join(HERE, "blender_decimate.py"), "--",
                            f"{td}/in.npz", f"{td}/out.npz", str(target)], capture_output=True, text=True)
        line = [l for l in r.stdout.splitlines() if l.startswith("DECIMATE")]
        if not line:
            print(r.stdout[-2000:], r.stderr[-2000:]); raise SystemExit("blender decimate failed")
        rep["decimate_log"] = line[0]
        d = np.load(f"{td}/out.npz")
        V2, F2 = d["V"], d["F"]
    # 3. normalize: height 1.0, feet on z=0, centered on x=0 (symmetry plane kept)
    zmin, zmax = V2[:, 2].min(), V2[:, 2].max()
    sc = 1.0 / (zmax - zmin)
    shift = np.array([0.0, 0.0, -zmin])
    Vn = (V2 + shift) * sc
    rep["normalize"] = {"scale": sc, "source_height": zmax - zmin}
    rep["body"] = topo_report(Vn, F2)
    # 4. materials: nearest authored mass, then color_regions (in plan space)
    mats = plan["materials"]
    cent = V2[F2].mean(1)
    body_parts = [p for p in parts if p.get("op") != "subtract"]
    near = nearest_part(cent, plan, body_parts)
    M = [p.get("material", plan.get("base_material")) for p in near]
    for reg in expand(plan.get("color_regions", [])):
        if "center" in reg:
            L, rr = to_local(cent, {**reg, "type": "ellipsoid"})
            inside = (np.linalg.norm(L / rr, axis=1) <= 1.0)
        else:
            inside = np.zeros(len(cent), bool)
        if reg.get("parts"):
            inside &= np.array([p["name"].split("_L")[0].split("_R")[0] in reg["parts"] or p["name"] in reg["parts"] for p in near])
        for i in np.nonzero(inside)[0]:
            M[i] = reg["material"]
    rep["material_face_counts"] = {k: int(sum(1 for x in M if x == k)) for k in sorted(set(M))}
    # 5. eyes (separate tagged meshes, plan space -> normalized)
    eyes = []
    for e in expand(plan.get("eyes", [])):
        c, nrm = place_on_surface(e["center"], plan, e["radius"] * e.get("embed", 0.45))
        Ve, Fe = icosphere(e.get("subdiv", 1), e["radius"], c, e.get("scale", (1, 1, 1)))
        eyes.append(((Ve + shift) * sc, Fe, [e["material"]] * len(Fe)))
    rep["eyes"] = [{"triangles": len(x[1]), **{k: v for k, v in topo_report(x[0], x[1]).items() if k in ("closed_manifold_ok", "components", "volume_positive")}} for x in eyes]
    rep["total_source_triangles"] = int(len(F2) + sum(len(x[1]) for x in eyes))
    rep["budget"] = plan.get("budget")
    rep["within_budget"] = bool(plan["budget"][0] <= rep["total_source_triangles"] <= plan["budget"][1])
    # 6. export
    body = (Vn, F2, M)
    write_obj(out + ".obj", body, eyes, mats)
    rep["glb_split_vertices"] = write_glb(out + ".glb", body, eyes, mats)
    g = trimesh.load(out + ".glb")
    rep["glb_reload"] = {"geometries": len(g.geometry), "triangles": int(sum(len(x.faces) for x in g.geometry.values())),
                         "bounds_yup": np.round(g.bounds, 4).tolist()}
    json.dump(plan, open(out + "_plan_used.json", "w"), indent=1)
    # 7. previews
    col = lambda MM: np.array([mats[x]["color"] for x in MM])
    rm = [(Vn, F2, col(M))] + [(x[0], x[1], col(x[2])) for x in eyes]
    views = [("front", 0, 0), ("side", 90, 0), ("back", 180, 0), ("isometric", 45, 35.264)]
    ims = [render(rm, az, el, 420, title=n) for n, az, el in views]
    sheet = Image.new("RGB", (420 * 4, 420), (255, 255, 255))
    for i, im in enumerate(ims):
        sheet.paste(im, (420 * i, 0)); im.save(f"{out}_{views[i][0]}.png")
    sheet.save(out + "_previews.png")
    render(rm, 45, 35.264, 96).save(out + "_isometric_96px.png")
    rep["unchecked"] = ["self-intersections / clipping", "anatomical correctness or attractiveness (visual review in REPORT.md only)",
                        "rig / animation", "exact bilateral symmetry after QEM", "engine import beyond trimesh GLB reload"]
    json.dump(rep, open(out + "_report.json", "w"), indent=1, default=lambda o: o.item() if hasattr(o, "item") else str(o))
    b = rep["body"]
    print(f"{out}: body tris={b['triangles']} V={b['vertices']} boundary={b['boundary_edges']} nonman={b['nonmanifold_edges']} "
          f"comps={b['components']} euler={b['euler_characteristic']} vol+={b['volume_positive']} ok={b['closed_manifold_ok']} "
          f"slivers<5deg={b['sliver_faces_min_angle_lt_5deg']} total_tris={rep['total_source_triangles']} grid_clear={rep['grid_boundary_clear']}")
    return rep


def sheet(dst, names):
    rows = []
    for n in names:
        a = Image.open(n + "_isometric.png"); b = Image.open(n + "_side.png"); c = Image.open(n + "_isometric_96px.png").resize((192, 192), Image.NEAREST)
        row = Image.new("RGB", (420 * 2 + 200, 420), (255, 255, 255))
        row.paste(a, (0, 0)); row.paste(b, (420, 0)); row.paste(c, (848, 114))
        ImageDraw.Draw(row).text((850, 96), "96px iso (x2 nearest)", fill=(60, 60, 60))
        ImageDraw.Draw(row).text((6, 404), os.path.basename(n), fill=(20, 20, 20))
        rows.append(row)
    S = Image.new("RGB", (rows[0].width, 420 * len(rows)), (255, 255, 255))
    for i, r in enumerate(rows):
        S.paste(r, (0, 420 * i))
    S.save(dst, quality=92)


if __name__ == "__main__":
    if sys.argv[1] == "build":
        ap = argparse.ArgumentParser(); ap.add_argument("cmd"); ap.add_argument("plan"); ap.add_argument("--out", required=True)
        a = ap.parse_args(); build(a.plan, a.out)
    elif sys.argv[1] == "sheet":
        sheet(sys.argv[2], sys.argv[3:])

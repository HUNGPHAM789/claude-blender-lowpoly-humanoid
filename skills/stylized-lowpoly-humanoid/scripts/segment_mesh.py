"""Split a generated mesh into its «khuôn» (molds): the separate pieces a modeller would have made — leather flaps, the belt ring,
the ornament, a hair tie, hair locks (Boss 25/10/2026: «quét ra từng khuôn màu kiểu như vầy là thấy được dây cột tóc · áp dụng cho
quần có belt để tìm chính xác vùng belt và tô màu»).

  python3 segment_mesh.py --mesh <part_fit.glb> --out <dir>/<name> [--crease 35] [--min-faces 150]
    [--image <clean asset png> --raw <raw glb> --fit-json <fit.json>]      # optional: one colour role per mold from the image
  ⇒ <name>_molds.json (one row per mold: faces, centre, size, ring-ness, role) · <name>_molds.png (each mold its own colour)
    <name>_molds_roles.png + <name>_roles.glb when an image is given (each mold painted with ONE game colour)

Molds = connected face patches after cutting every edge whose dihedral angle ≥ --crease (fold lines between overlapping pieces);
patches smaller than --min-faces are merged into the neighbour they share the longest border with.
Ring-ness = how fully a mold wraps around the vertical axis (fraction of 24 angle sectors it touches) — a belt or a hair tie is a ring.
"""
import argparse, json, math, os, sys
import numpy as np
import trimesh
from PIL import Image, ImageDraw
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components


BELT_FROM = 0.88      # skirt molds centred in the top 12 % are the belt (sample: belt band 3.6–6 cm under a 57 cm skirt top)


def segment(m, crease_deg, min_faces):
    adj = m.face_adjacency; ang = np.degrees(m.face_adjacency_angles)
    keep = ang < crease_deg; n = len(m.faces)
    G = coo_matrix((np.ones(keep.sum()), (adj[keep, 0], adj[keep, 1])), shape=(n, n))
    _, lab = connected_components(G, directed=False)
    # merge small molds into the neighbour with the longest shared border
    edge_len = np.linalg.norm(m.vertices[m.face_adjacency_edges[:, 0]] - m.vertices[m.face_adjacency_edges[:, 1]], axis=1)
    for _ in range(6):
        size = np.bincount(lab); small = set(np.where(size < min_faces)[0])
        if not small: break
        border = {}
        for (a, b), L in zip(adj, edge_len):
            la, lb = lab[a], lab[b]
            if la == lb: continue
            if la in small: border[(la, lb)] = border.get((la, lb), 0) + L
            if lb in small: border[(lb, la)] = border.get((lb, la), 0) + L
        best = {}
        for (s, t), L in border.items():
            if s not in best or L > best[s][1]: best[s] = (t, L)
        if not best: break
        remap = np.arange(lab.max() + 1)
        for s, (t, _) in best.items(): remap[s] = t
        for _ in range(10): remap = remap[remap]
        lab = remap[lab]
    _, lab = np.unique(lab, return_inverse=True)
    return lab


def segment_bumps(m, ball, min_faces, iters=40):
    """generated meshes are smooth (no sharp folds) ⇒ molds = convex bumps between concave valleys: h = how far each vertex stands
    out of a Laplacian-smoothed copy along its normal; every vertex climbs h to a peak (watershed); peaks closer than `ball` merge."""
    from scipy.spatial import cKDTree
    sm = m.copy(); trimesh.smoothing.filter_laplacian(sm, lamb=0.5, iterations=iters)
    h = np.einsum("ij,ij->i", m.vertices - sm.vertices, m.vertex_normals); n = len(h)
    nb = [[] for _ in range(n)]
    for a_, b_ in m.edges_unique: nb[a_].append(b_); nb[b_].append(a_)
    up = np.arange(n)
    for i in range(n):
        if nb[i]:
            j = max(nb[i], key=lambda k: h[k])
            if h[j] > h[i]: up[i] = j
    for _ in range(80): up = up[up]
    peaks = np.unique(up); kd = cKDTree(m.vertices[peaks])
    order = peaks[np.argsort(-h[peaks])]; rep = {}
    for p in order:                                                  # merge peaks within `ball` into the highest one
        if p in rep: continue
        for q in kd.query_ball_point(m.vertices[p], ball):
            rep.setdefault(peaks[q], p)
    vlab = np.array([rep.get(x, x) for x in up]); _, vlab = np.unique(vlab, return_inverse=True)
    flab = np.array([np.bincount(vlab[f]).argmax() for f in m.faces])
    # small molds → neighbour sharing the most edges
    for _ in range(6):
        size = np.bincount(flab); small = np.where(size < min_faces)[0]
        if not len(small): break
        votes = {}
        for a_, b_ in m.face_adjacency:
            la, lb = flab[a_], flab[b_]
            if la != lb:
                if size[la] < min_faces: votes.setdefault(la, {}).setdefault(lb, 0); votes[la][lb] += 1
                if size[lb] < min_faces: votes.setdefault(lb, {}).setdefault(la, 0); votes[lb][la] += 1
        for s_, d_ in votes.items(): flab[flab == s_] = max(d_, key=d_.get)
    _, flab = np.unique(flab, return_inverse=True)
    return flab


def main(a):
    m = trimesh.load(a.mesh, force="mesh"); m = trimesh.Trimesh(m.vertices, m.faces, process=True)
    lab = segment_bumps(m, a.ball, a.min_faces) if a.mode == "bumps" else segment(m, a.crease, a.min_faces); C = m.triangles_center; A = m.area_faces
    ax = np.array([np.average(C[:, 0], weights=A), 0, np.average(C[:, 2], weights=A)])
    y0, y1 = m.vertices[:, 1].min(), m.vertices[:, 1].max(); H = y1 - y0
    roles = None
    if a.image:
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        from analyze_outfit import image_roles
        roles = image_roles(a.raw, a.image, a.fit_json, m)
    molds = []
    for k in range(lab.max() + 1):
        f = np.where(lab == k)[0]; P = C[f]; w = A[f]
        sect = np.unique(((np.degrees(np.arctan2(P[:, 0] - ax[0], P[:, 2] - ax[2])) + 180) // 15).astype(int))
        row = {"id": int(k), "faces": int(len(f)), "area_cm2": round(float(w.sum()) * 1e4, 1),
               "centre": np.average(P, axis=0, weights=w).round(4).tolist(), "height_frac": round(float((np.average(P[:, 1], weights=w) - y0) / H), 3),
               "y_span_cm": round(float(np.ptp(P[:, 1])) * 100, 1), "ring": round(len(sect) / 24, 2)}
        if roles is not None:
            sf = f[image_roles.seen[f]]                                  # vote with the faces the image really shows
            vals, cnt = np.unique(roles[sf if len(sf) else f], return_counts=True); row["role_votes"] = {str(v): int(c) for v, c in zip(vals, cnt)}
            row["role"] = str(vals[np.argmax(cnt)]); row["seen_frac"] = round(float(image_roles.seen[f].mean()), 2)
            if a.kind == "hair":                                         # hair: a mold is the TIE when most of what the image shows is light
                light = sum(c for v, c in zip(vals, cnt) if v in ("belt", "lining")); row["role"] = "tie" if len(sf) >= 20 and light > 0.5 * len(sf) else "hair"
        molds.append(row)
    # geometry overrides: a ring in the top 25 % is the belt; small proud front blob at belt height is the ornament
    # geometry decides WHERE a role may live; the image only votes between the roles allowed there
    # (belt rope (196,164,108) and tan lining (176,138,92) are too close in colour to separate by pixels alone)
    top = [r for r in molds if r["height_frac"] >= BELT_FROM] if a.kind == "skirt" else []
    ring_r = np.median([np.hypot(r["centre"][0] - ax[0], r["centre"][2] - ax[2]) for r in top]) if top else 0
    for r in (molds if a.kind == "skirt" else []):
        if "role" not in r: continue
        c_ = np.array(r["centre"]); front = abs(math.degrees(math.atan2(c_[0] - ax[0], c_[2] - ax[2]))) < 40
        if r.get("seen_frac", 1) < 0.2 and r["height_frac"] < BELT_FROM: r["role"] = "outer"; r["rule"] = "unseen by the image ⇒ default outer"; continue
        if r["height_frac"] >= 0.78 and front and np.hypot(c_[0] - ax[0], c_[2] - ax[2]) > ring_r + 0.015 and r["faces"] < 1500:
            r["role"] = "ornament"; r["rule"] = "proud front blob at the belt"; continue
        if r["height_frac"] >= BELT_FROM: r["role"] = "ornament" if (r["role"] == "ornament" and front) else "belt"; r["rule"] = "top band"
        elif r["role"] == "belt": r["role"] = "lining"; r["rule"] = "rope colour below the belt band = lining"
        elif r["role"] == "ornament" and not (r["height_frac"] >= 0.75 and front): r["role"] = "outer"; r["rule"] = "grey away from the belt front"
    json.dump({"mesh": a.mesh, "crease_deg": a.crease, "molds": molds}, open(a.out + "_molds.json", "w"), indent=1)
    np.save(a.out + "_face_molds.npy", lab)                            # face → mold id (same face order as trimesh.load(..., process=True))
    # pictures
    rng = np.random.default_rng(3); rand = rng.integers(40, 230, (lab.max() + 1, 3))
    PAL = {"outer": (74, 53, 37), "lining": (176, 138, 92), "belt": (196, 164, 108), "ornament": (120, 116, 108), "hair": (58, 40, 28), "tie": (196, 164, 108)}
    sets = [("_molds.png", rand[lab])]
    if roles is not None or any("role" in r for r in molds):
        rc = np.array([PAL.get(molds[l].get("role", "outer"), (200, 0, 200)) for l in lab]); sets.append(("_molds_roles.png", rc))
    V, F = m.vertices, m.faces
    for suffix, col in sets:
        tiles = []
        for yaw in (0, 90, 180, 270):
            ar = math.radians(yaw); R = np.array([[math.cos(ar), 0, math.sin(ar)], [0, 1, 0], [-math.sin(ar), 0, math.cos(ar)]])
            W = (V - ax - [0, (y0 + y1) / 2, 0]) @ R.T; s = 300 / (1.3 * max(np.ptp(V[:, 0]), np.ptp(V[:, 2]), H))
            im = Image.new("RGB", (300, 320), (245, 245, 245)); d = ImageDraw.Draw(im)
            for i in np.argsort(W[F][:, :, 2].mean(axis=1)):
                t = W[F[i]]
                if np.cross(t[1] - t[0], t[2] - t[0])[2] <= 0: continue
                d.polygon([(150 + x * s, 160 - y * s) for x, y, _ in t], fill=tuple(int(c) for c in col[i]))
            tiles.append(im)
        sheet = Image.new("RGB", (1200, 320)); [sheet.paste(t, (300 * i, 0)) for i, t in enumerate(tiles)]; sheet.save(a.out + suffix)
    if any("role" in r for r in molds):
        sc = trimesh.Scene()
        for role, rgb in PAL.items():
            f = np.where(np.array([molds[l].get("role") == role for l in lab]))[0]
            if not len(f): continue
            sub = trimesh.Trimesh(V, F[f], process=False); sub.remove_unreferenced_vertices(); sub.visual.face_colors = list(rgb) + [255]
            sc.add_geometry(sub, geom_name=role, node_name=role)
        sc.export(a.out + "_roles.glb")
    big = sorted(molds, key=lambda r: -r["faces"])
    print(f"{len(molds)} molds (crease {a.crease}°): " + ", ".join(f"#{r['id']} {r['faces']}f h{r['height_frac']} ring{r['ring']} {r.get('role', '')}" for r in big[:14]))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--mesh", required=True); ap.add_argument("--out", required=True)
    ap.add_argument("--kind", default="skirt", choices=["skirt", "hair"])
    ap.add_argument("--mode", default="bumps", choices=["bumps", "crease"]); ap.add_argument("--ball", type=float, default=0.03)
    ap.add_argument("--crease", type=float, default=35.0); ap.add_argument("--min-faces", type=int, default=150)
    ap.add_argument("--image"); ap.add_argument("--raw"); ap.add_argument("--fit-json")
    main(ap.parse_args())

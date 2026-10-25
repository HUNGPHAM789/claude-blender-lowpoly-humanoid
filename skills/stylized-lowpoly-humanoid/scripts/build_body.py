"""Stylized low-poly muscular humanoid (primal adult male/female) — built from a ring spec, flat-shaded GLB.

Boss 25/10/2026: «spec chi tiết từng bộ phận, các đường cong … phần torso ở dưới, chỗ lòi ra của ngực … các muscle — một skill
stylized low poly, khác với low poly origami». Reference: references/primal_starter_official_2026-10-25/*.png.

  python3 build_body.py --sex male|female --out <dir>/<name>     ⇒ <name>.glb + <name>.json (parts, tris, landmarks)

Axes: X = body left(+)/right(−), Y = forward(+), Z = up. Feet on Z = 0. All ring numbers in spec/<sex>_spec.json are FRACTIONS of
the reference figure height (feet 0 → hair top 1) so they read straight off the measured silhouettes; `scale_m` turns them into metres.
"""
import argparse, json, math, os
import numpy as np
import trimesh


def load_zup(glb):
    """read a GLB written by build() back into build axes (X left, Y forward, Z up)."""
    m = trimesh.load(glb, force="mesh"); V = m.vertices.copy()
    m.vertices = np.c_[-V[:, 0], V[:, 2], V[:, 1]]; return m

HERE = os.path.dirname(os.path.abspath(__file__))
SPEC = os.path.join(HERE, "..", "spec")


def ring(c, w, df, db, n, twist=0.0, ex=2.2, bumps=()):
    """n points around centre c (x, y, z): half width w, forward depth df, backward depth db; superellipse exponent ex
    (2 = ellipse, >2 = boxier, which reads as planes in low poly). twist rotates the start angle (staggers facets).
    bumps = [[angle_deg, amp, width_deg], …] — radial muscle bulges/grooves (0° = body left +X, 90° = front, 270° = back),
    mirrored across the sagittal plane automatically (give the left one only, or 90°/270° for the midline)."""
    pts = []
    for i in range(n):
        a = 2 * math.pi * i / n + twist
        ca, sa = math.cos(a), math.sin(a)
        x = w * np.sign(ca) * abs(ca) ** (2 / ex)
        y = (df if sa >= 0 else db) * np.sign(sa) * abs(sa) ** (2 / ex)
        f = 1.0; deg = math.degrees(a) % 360
        for b in bumps:
            for ang in {b[0] % 360, (180 - b[0]) % 360}:
                dd = min(abs(deg - ang), 360 - abs(deg - ang)); f += b[1] * math.exp(-(dd / b[2]) ** 2)
        pts.append((c[0] + x * f, c[1] + y * f, c[2]))
    return pts


def loft(rings, cap_bottom=True, cap_top=True):
    """rings: list of equal-length point lists ⇒ triangles (quads split along alternating diagonals = origami-like facets)."""
    V = [p for r in rings for p in r]; n = len(rings[0]); F = []
    for k in range(len(rings) - 1):
        for i in range(n):
            a, b = k * n + i, k * n + (i + 1) % n
            c, d = (k + 1) * n + i, (k + 1) * n + (i + 1) % n
            if (i + k) % 2: F += [(a, b, d), (a, d, c)]
            else: F += [(a, b, c), (b, d, c)]
    if cap_bottom:
        V.append(tuple(np.mean(rings[0], axis=0))); ci = len(V) - 1
        F += [(ci, (i + 1) % n, i) for i in range(n)]
    if cap_top:
        V.append(tuple(np.mean(rings[-1], axis=0))); ci = len(V) - 1; o = (len(rings) - 1) * n
        F += [(ci, o + i, o + (i + 1) % n) for i in range(n)]
    return np.array(V, float), np.array(F, int)


def limb(points, n, twist_step=0.0):
    """points: list of dicts {c:[x,y,z], w, df, db} along a limb axis that may tilt ⇒ rings built in the plane ⟂ to the axis."""
    rings = []
    P = [np.array(p["c"], float) for p in points]
    for k, p in enumerate(points):
        t = (P[min(k + 1, len(P) - 1)] - P[max(k - 1, 0)]); t /= np.linalg.norm(t)
        # local frame: u ≈ X (lateral), v ≈ Y (forward), both ⟂ t
        u = np.cross([0, 1, 0], t); u = u / np.linalg.norm(u) if np.linalg.norm(u) > 1e-6 else np.array([1, 0, 0.])
        v = np.cross(t, u)
        r = []
        for x, y, _ in ring((0, 0, 0), p["w"], p["df"], p["db"], n, twist=k * twist_step, ex=p.get("ex", 2.2), bumps=p.get("bumps", ())):
            r.append(tuple(P[k] + x * u + y * v))
        rings.append(r)
    return loft(rings)


def lobe(c, rx, ry, rz, n=8, m=5, flat_back=True):
    """low-poly ellipsoid (bust, glute cap, deltoid cap): m latitude rows, n sides; flat_back keeps only the front 3/4."""
    V, F = [], []
    for j in range(1, m):
        th = math.pi * j / m
        for i in range(n):
            ph = 2 * math.pi * i / n
            x, y, z = rx * math.sin(th) * math.cos(ph), ry * math.sin(th) * math.sin(ph), rz * math.cos(th)
            if flat_back and y < 0: y *= 0.25
            V.append((c[0] + x, c[1] + y, c[2] + z))
    V += [(c[0], c[1], c[2] + rz), (c[0], c[1], c[2] - rz)]; top, bot = len(V) - 2, len(V) - 1
    for j in range(m - 2):
        for i in range(n):
            a, b = j * n + i, j * n + (i + 1) % n; cc, d = a + n, b + n
            F += [(a, cc, b), (b, cc, d)]
    F += [(top, (i + 1) % n, i) for i in range(n)]
    o = (m - 2) * n; F += [(bot, o + i, o + (i + 1) % n) for i in range(n)]
    return np.array(V, float), np.array(F, int)


def mirror(V, F):
    V2 = V.copy(); V2[:, 0] *= -1
    return V2, F[:, ::-1]


def flat(V, F):
    """unshare vertices ⇒ every triangle keeps its own normal (hard facets = the low-poly look)."""
    return trimesh.Trimesh(vertices=V[F].reshape(-1, 3), faces=np.arange(len(F) * 3).reshape(-1, 3), process=False)


def build(sex, out, shading="smooth"):
    S = json.load(open(os.path.join(SPEC, f"{sex}_spec.json")))
    k = S["scale_m"]; parts = {}
    sc = lambda v: [v[0] * k, v[1] * k, v[2] * k]

    def ring_pts(rows):
        return [dict(c=sc(r["c"]), w=r["w"] * k, df=r["df"] * k, db=r["db"] * k, ex=r.get("ex", 2.2), bumps=r.get("bumps", ())) for r in rows]

    # torso + neck + head: vertical lofts
    for name in ("torso", "neck", "head"):
        sec = S[name]; rows = ring_pts(sec["rings"])
        rings = [ring(r["c"], r["w"], r["df"], r["db"], sec["sides"], twist=(i % 2) * math.pi / sec["sides"] * sec.get("stagger", 0), ex=r["ex"], bumps=r["bumps"]) for i, r in enumerate(rows)]
        parts[name] = loft(rings)
    # limbs, left side then mirrored
    for name in ("upper_arm", "forearm", "hand", "thigh", "shin", "foot"):
        sec = S[name]; V, F = limb(ring_pts(sec["rings"]), sec["sides"], sec.get("twist_step", 0.0))
        parts[name + "_L"] = (V, F); parts[name + "_R"] = mirror(V, F)
    # muscle / anatomy caps
    for c in S.get("lobes", []):
        V, F = lobe(sc(c["c"]), c["r"][0] * k, c["r"][1] * k, c["r"][2] * k, c.get("n", 8), c.get("m", 5), c.get("flat_back", True))
        parts[c["name"] + ("_L" if c.get("mirror") else "")] = (V, F)
        if c.get("mirror"): parts[c["name"] + "_R"] = mirror(V, F)
    skin = S.get("skin_rgba", [226, 160, 132, 255])
    scene = trimesh.Scene(); tris = {}
    for n_, (V, F) in parts.items():
        m = flat(V, F) if shading == "flat" else trimesh.Trimesh(vertices=V, faces=F, process=True)   # smooth = reference look (soft light, faceted outline)
        m.visual.face_colors = skin; scene.add_geometry(m, node_name=n_, geom_name=n_); tris[n_] = len(F)
    os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
    # glTF is Y-up: (x, y, z)_build → (−x, z, y): up = +Y, the body faces +Z (Godot/three.js convention for characters)
    scene.apply_transform(np.array([[-1, 0, 0, 0], [0, 0, 1, 0], [0, 1, 0, 0], [0, 0, 0, 1.]]))
    scene.export(out + ".glb")
    lm = {k_: round(v * k, 4) for k_, v in S.get("landmarks", {}).items()}
    json.dump({"sex": sex, "scale_m": k, "tris_total": int(sum(tris.values())), "tris": tris, "landmarks_m": lm}, open(out + ".json", "w"), indent=1)
    print(f"exported {out}.glb — {len(parts)} parts, {sum(tris.values())} tris")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--sex", required=True, choices=["male", "female"]); ap.add_argument("--out", required=True)
    ap.add_argument("--shading", default="smooth", choices=["smooth", "flat"])
    a = ap.parse_args(); build(a.sex, a.out, a.shading)

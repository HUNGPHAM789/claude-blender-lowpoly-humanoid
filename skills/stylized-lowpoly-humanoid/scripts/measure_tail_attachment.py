"""Ponytail must sit ON the head (Boss 25/10 ×2: «tóc đuôi của V3 nhìn ngang xem lại chỗ cột tóc» · «nữ tóc đuôi chưa sát với đầu»).

  python3 measure_tail_attachment.py --hair female_hair_vN.glb [--max-gap-mm 3] [--json out.json]

The tail root = ponytail vertices within ROOT_BAND of its top. From each root vertex a ray is cast toward the head centre (the scalp
cap's centroid); the gap is how far it travels before hitting hair_masses / the cap. The root is attached when the p25 gap ≤ max (the head-facing
quarter of the root ring; far-side rays cross the tail itself). The tie must also touch: its inner side within max of the hair or of the tail.
Exit 1 when either is off — the side-view white gap Boss saw (v4: tail root ~2 cm behind the hair).
"""
import argparse, json, sys
import numpy as np
import trimesh

ROOT_BAND = 0.03          # m below the tail's top that counts as the root
EMBED = 0.015             # m: a hair surface this close BEHIND a root vertex (away from the head) means it sits inside the masses


def ray_dist(tri, O, D):
    """first positive hit distance of each ray (O[i], D[i]) on triangles tri (Möller–Trumbore, both faces); inf if none"""
    v0, e1, e2 = tri[:, 0], tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0]
    out = np.full(len(O), np.inf)
    for i, (o, d) in enumerate(zip(O, D)):
        p = np.cross(d, e2); det = (e1 * p).sum(1); ok = np.abs(det) > 1e-12
        inv = np.where(ok, 1.0 / np.where(ok, det, 1), 0); t_ = o - v0
        u = (t_ * p).sum(1) * inv; q = np.cross(t_, e1); v = (q * d).sum(1) * inv; t = (q * e2).sum(1) * inv
        hit = ok & (u >= 0) & (v >= 0) & (u + v <= 1) & (t > 1e-6)
        if hit.any(): out[i] = t[hit].min()
    return out


def measure(path):
    s = trimesh.load(path, force="scene"); g = s.geometry
    head = trimesh.util.concatenate([g[k] for k in g if k.startswith(("hair_masses", "hair_cap"))])
    centre = g["hair_cap__movable"].vertices.mean(0) if "hair_cap__movable" in g else head.vertices.mean(0)
    tail = g["ponytail"].vertices; root = tail[tail[:, 1] > tail[:, 1].max() - ROOT_BAND]
    D = centre - root; D /= np.linalg.norm(D, axis=1, keepdims=True)
    gap = ray_dist(head.triangles, root, D)
    gap[ray_dist(head.triangles, root, -D) < EMBED] = 0.0              # hair surface just behind the vertex ⇒ the root is sunk in the masses
    hit = np.isfinite(gap); r = {"root_verts": int(len(root)), "root_hit_frac": round(float(hit.mean()), 3),
                               "root_gap_p25_mm": round(float(np.percentile(np.where(hit, gap, 1.0), 25)) * 1000, 1),
                               "root_gap_min_mm": round(float(gap[hit].min()) * 1000, 1) if hit.any() else None}
    if "tie_rope" in g:
        tie = g["tie_rope"].vertices; Dt = centre - tie; Dt /= np.linalg.norm(Dt, axis=1, keepdims=True)
        both = trimesh.util.concatenate([head, g["ponytail"]])
        gt = ray_dist(both.triangles, tie, Dt); r["tie_gap_p25_mm"] = round(float(np.percentile(np.where(np.isfinite(gt), gt, 1.0), 25)) * 1000, 1)
    return r


def main(a):
    r = measure(a.hair); bad = []
    if r["root_gap_p25_mm"] > a.max_gap_mm: bad.append(f"ponytail root floats {r['root_gap_p25_mm']} mm off the head (p25, ≤ {a.max_gap_mm})")
    if r.get("tie_gap_p25_mm", 0) > a.max_gap_mm: bad.append(f"tie floats {r['tie_gap_p25_mm']} mm off the hair (p25, ≤ {a.max_gap_mm})")
    r["ok"] = not bad; print("tail_attachment:", r)
    if a.json: json.dump(r, open(a.json, "w"), indent=1)
    for b in bad: print("⛔", b)
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--hair", required=True)
    ap.add_argument("--max-gap-mm", type=float, default=3.0); ap.add_argument("--json")
    main(ap.parse_args())

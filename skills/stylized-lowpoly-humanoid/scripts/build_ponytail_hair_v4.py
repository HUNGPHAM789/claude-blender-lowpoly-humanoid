"""Female hair v4 — composed from approved pieces (Boss 25/10: «tóc nữ quay lại V1 cho khúc trước cột tóc - thêm lọn to kiểu 2 mái
nhưng nhỏ dần vào giữa … tóc đuôi của V3 … chỗ cột tóc dùng shape của dây belt»):
  * everything in front of the tie (cap + masses) copied byte-for-byte from female_hair_v1.glb;
  * NEW curtain fringe: 3 locks per side, split at the middle, biggest at the outside, rooted on the v1 hairline, tips ~0.07 H above
    the brow;
  * ponytail clumps copied from female_hair_v3.glb;
  * the tie is a lumpy twisted rope like the skirt's rope belt (5-sided tube, 12 stations, uneven radius, wobble), rope_bone.

  python3 build_ponytail_hair_v4.py --body female_base_lp.glb --measurements female_measurements.json \
      --hair-v1 female_hair_v1.glb --hair-v3 female_hair_v3.glb --out female_hair_v4.glb
"""
import argparse
import json
import math
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from primal_body_frame import export_roles, load_body, load_json  # noqa: E402
from build_spiky_hair import HeadFrame, unit  # noqa: E402
from measure_primal_assets import parts_of  # noqa: E402
import build_hair_masses_v2 as V2  # noqa: E402

FRINGE = [(9.0, 0.20), (21.0, 0.25), (34.0, 0.31)]     # (|azimuth| deg, width ÷ W): inner → outer, outer biggest


def curtain_fringe(hf, H, W, brow):
    tip_y = brow + 0.07 * H
    verts, faces, table = [], [], []
    for sgn in (-1, 1):
        for az, wf in FRINGE:
            th = sgn * az
            ph = hf.bottom_elevation(th) + 3.0
            root_y = hf.scalp_point(th, ph, 0.0)[0][1]
            best = None
            for fac in np.linspace(0.9, 2.4, 16):           # length searched so the tip lands ~0.07 H above the brow
                L = max(0.02, (root_y - tip_y) * fac)
                res = V2.wedge(hf, th, ph, 0.22 * sgn, -1.0, L, wf * W, 0.36, 0.06, 1, None)
                if res is None:
                    continue
                err = abs(res[0][-1][1] - tip_y)
                if best is None or err < best[0]:
                    best = (err, L, res)
            _, L, (V, F, nr) = best
            V = V2.clear_wedge(hf, V, F, nr)
            faces.extend((F + len(verts)).tolist())
            verts.extend(V.tolist())
            table.append({"side": "L" if sgn > 0 else "R", "azimuth_deg": th, "width_cm": round(wf * W * 100, 1),
                          "length_cm": round(L * 100, 1), "tip_above_brow_cm": round(float(V[-1][1] - brow) * 100, 2),
                          "tip_above_brow_H": round(float(V[-1][1] - brow) / H, 3)})
    return np.array(verts), np.array(faces), table


def rope_tie(centre, axis, radius, rng, n_seg=12, n_side=5):
    """the skirt belt's rope grammar wrapped round the tail root: 5-sided twisted tube, uneven radius per station, small wobble."""
    axis = unit(axis)
    a1 = unit(np.array([1.0, 0, 0]) - axis * axis[0])           # lateral (the tail is wide side-to-side)
    a2 = unit(np.cross(axis, a1))
    centres, radii = [], []
    phase = rng.uniform(0, 2 * math.pi)
    for s in range(n_seg):
        t = 2 * math.pi * s / n_seg + rng.uniform(-0.08, 0.08)
        rr = 0.0085 + 0.004 * rng.random()
        wob = 0.003 * math.sin(2 * t + phase) + rng.uniform(-0.0015, 0.0015)
        ra, rb = radius if isinstance(radius, tuple) else (radius, radius)
        centres.append(centre + ra * math.cos(t) * a1 + rb * math.sin(t) * a2 + axis * wob)
        radii.append(rr)
    V, F = [], []
    for s in range(n_seg):
        radial = unit(centres[s] - centre - axis * np.dot(centres[s] - centre, axis))
        for k in range(n_side):
            u = 2 * math.pi * k / n_side + s * 0.9                  # twist
            V.append(centres[s] + radii[s] * (math.cos(u) * radial + math.sin(u) * axis))
    for s in range(n_seg):
        t_ = (s + 1) % n_seg
        for k in range(n_side):
            m = (k + 1) % n_side
            a, b, c, d = s * n_side + k, t_ * n_side + k, t_ * n_side + m, s * n_side + m
            F += [[a, b, c], [a, c, d]]
    V, F = np.array(V), np.array(F)
    cen = np.array(centres)
    tri = V[F]
    nn = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0])
    flip = np.einsum("ij,ij->i", nn, tri.mean(axis=1) - cen[F[:, 0] // n_side]) < 0
    F[flip] = F[flip][:, ::-1]
    return V, F


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--body", required=True)
    ap.add_argument("--measurements", required=True)
    ap.add_argument("--hair-v1", required=True)
    ap.add_argument("--hair-v3", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    meas = load_json(a.measurements)
    body = load_body(a.body)
    hf = HeadFrame(body, meas)                     # v1 hairline (no widow's peak)
    face = meas["face"]
    W = meas["skull"]["width_m"]
    H = float(body.vertices[:, 1].max() - face["chin_y"])
    v1, v3 = parts_of(a.hair_v1), parts_of(a.hair_v3)
    v3info = json.load(open(os.path.splitext(a.hair_v3)[0] + "_parts.json"))
    fv, ff, ftab = curtain_fringe(hf, H, W, face["brow_y"])
    root = np.array(v3info["tie"]["point"])
    tail_dir = unit(np.array([0, -0.12, -1.0]))
    rv, rf = rope_tie(root + tail_dir * 0.012, tail_dir, (0.056, 0.034), np.random.default_rng(5))   # wraps OUTSIDE the 11 × 6 cm tail root
    parts = [("hair_cap__movable", "hair", v1["hair_cap__movable"].vertices, v1["hair_cap__movable"].faces),
             ("hair_masses", "hair", v1["hair_masses"].vertices, v1["hair_masses"].faces),
             ("fringe", "hair", fv, ff),
             ("ponytail", "hair", v3["ponytail"].vertices, v3["ponytail"].faces),
             ("tie_rope", "rope_bone", rv, rf)]
    export_roles(parts, a.out, flat=["fringe", "tie_rope"])
    tris = {p[0]: int(len(p[3])) for p in parts}
    info = {"out": a.out, "from": {"front_of_tie": a.hair_v1, "ponytail": a.hair_v3}, "tris": tris, "tris_total": int(sum(tris.values())),
            "fringe": ftab, "tie": {"point": np.round(root, 4).tolist(), "rope_ring_semi_axes_cm": [5.6, 3.4]}, "clumps": [], "clumps_per_region": {}}
    with open(os.path.splitext(a.out)[0] + "_parts.json", "w") as f:
        json.dump(info, f, indent=1)
    print(json.dumps({"tris": tris, "total": info["tris_total"], "fringe": [(t["side"], t["azimuth_deg"], t["width_cm"], t["length_cm"], t["tip_above_brow_cm"]) for t in ftab]}))


if __name__ == "__main__":
    main()

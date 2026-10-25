"""Compose a skirt from two builds of the SAME raw skirt: faces whose centroid lies on the figure's RIGHT (x < midline) come from
`--right`, every other face comes untouched from `--base` (female round 3: «start FROM the approved file, change only the named
region»). Reports how many base vertices on the left moved (must be 0).

  python3 compose_skirt_sides.py --base female_outfit_v1.glb --right candidate.glb --measurements female_measurements.json --out female_outfit_v3.glb
"""
import argparse
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from primal_body_frame import export_roles, load_json  # noqa: E402
from measure_primal_assets import parts_of  # noqa: E402

ROLE_OF = {"skirt_lining": "leather_tan", "skirt_lower_tier": "leather_dark", "skirt_upper_tier": "leather_dark",
           "rope_belt": "rope_bone", "ornament": "ornament_stone"}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", required=True)
    ap.add_argument("--right", required=True)
    ap.add_argument("--measurements", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--margin", type=float, default=0.03, help="m left of the midline that still counts as 'right' (seam inside the front/back)")
    a = ap.parse_args()
    xm = load_json(a.measurements)["face"]["midline_x"]
    base, right = parts_of(a.base), parts_of(a.right)
    parts, moved_left = [], 0
    for name in ("skirt_lining", "skirt_lower_tier", "skirt_upper_tier", "rope_belt", "ornament"):
        b = base[name]
        if name not in ("skirt_lining", "skirt_lower_tier", "skirt_upper_tier"):
            parts.append((name, ROLE_OF[name], b.vertices, b.faces))
            continue
        r = right[name]
        bc = b.triangles.mean(axis=1)[:, 0]
        rc = r.triangles.mean(axis=1)[:, 0]
        keep_b = b.faces[bc >= xm - a.margin]
        take_r = r.faces[rc < xm - a.margin]
        V = np.vstack([b.vertices, r.vertices])
        F = np.vstack([keep_b, take_r + len(b.vertices)])
        used = np.unique(F)
        remap = -np.ones(len(V), int)
        remap[used] = np.arange(len(used))
        parts.append((name, ROLE_OF[name], V[used], remap[F]))
    export_roles(parts, a.out)
    # left-side identity check: every output vertex with x >= midline must exist in the base file
    from scipy.spatial import cKDTree
    for name, _, V, F in parts:
        left = V[V[:, 0] >= xm]
        d = cKDTree(base[name].vertices).query(left)[0] if len(left) else np.zeros(0)
        moved_left += int((d > 1e-6).sum())
    info = {"out": a.out, "base": a.base, "right_from": a.right, "left_vertices_moved": moved_left,
            "tris": {p[0]: int(len(p[3])) for p in parts}}
    with open(os.path.splitext(a.out)[0] + "_parts.json", "w") as f:
        json.dump(info, f, indent=1)
    print(json.dumps(info))


if __name__ == "__main__":
    main()

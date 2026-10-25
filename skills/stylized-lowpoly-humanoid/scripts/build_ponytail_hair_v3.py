"""Female hair v3 = the APPROVED female_hair_v1.glb with only three changes (Boss 25/10, female round 3:
«lấy lại tóc cũ chỉ thêm độ dày đuôi, thêm lọn, cho ngọn tóc có V chỗ trán»):
  1. ponytail ≈1.5× thicker at the tie, 7 overlapping clumps (v1 had 5), each centreline 4 segments with ≤ 30° per joint, arc
     starting downward early (no horizontal jut);
  2. the cap's front hairline gets the widow's-peak V (v2 cap: snug ≤ 3 mm on the forehead);
  3. tie band resized to the thicker tail.
hair_masses (crown, top, framing locks, sides, back) are copied byte-for-byte from v1. No fringe.

  python3 build_ponytail_hair_v3.py --body female_base_lp.glb --measurements female_measurements.json --hair-v1 female_hair_v1.glb --out female_hair_v3.glb
"""
import argparse
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from primal_body_frame import export_roles, load_body, load_json  # noqa: E402
from build_spiky_hair import HeadFrame  # noqa: E402
from measure_primal_assets import parts_of  # noqa: E402
import build_hair_masses_v2 as V2  # noqa: E402
import build_ponytail_hair as P1  # noqa: E402
import build_ponytail_hair_v2 as P2  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--body", required=True)
    ap.add_argument("--measurements", required=True)
    ap.add_argument("--hair-v1", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    meas = load_json(a.measurements)
    body = load_body(a.body)
    hf = HeadFrame(body, meas)
    face = meas["face"]
    H = float(body.vertices[:, 1].max() - face["chin_y"])
    v1 = parts_of(a.hair_v1)
    v1info = json.load(open(os.path.splitext(a.hair_v1)[0] + "_parts.json"))
    # 2. V hairline cap (the only cap change)
    hf.hairline = P2.widows_peak(hf, face["hairline_y"])
    cap_v, cap_f, _, cols = V2.build_cap(hf, rows_t=(0.0, 0.16, 0.34, 0.56, 0.8), extra_cols=P2.PEAK_COLS)
    cap_v = P2.snug_cap(hf, cap_v, cap_f, cols)
    # 1. thicker, curving tail from the v1 tie point
    root = np.array(v1info["tie"]["point"]) + np.array([0, 0.004, -0.003])
    L_tail = float(root[1] - meas["joints_gltf"]["nguc"][1]) * 1.05
    rng = np.random.default_rng(7)
    specs = [(0.0, 1.0, 0.13), (-0.5, 0.9, 0.11), (0.5, 0.9, 0.11), (-1.0, 0.78, 0.095), (1.0, 0.78, 0.095), (-0.25, 0.68, 0.085), (0.25, 0.68, 0.085)]
    tv, tf, tails = [], [], []
    for i, (lx, ln, wd) in enumerate(specs):
        turns = [rng.uniform(26, 29.5) for _ in range(3)]
        a0 = rng.uniform(-12, -2)              # the arc starts DOWNWARD right after the tie (v2 rose first and jutted out)
        V, F, st = P2.tail_clump(hf.q, root + np.array([lx * 0.014, rng.uniform(-0.006, 0.006), 0]), np.array([lx * 0.14, 0, 0]),
                                 L_tail * ln, wd, 0.063, a0, turns, rng.uniform(-0.25, 0.25))
        tf.extend((F + len(tv)).tolist())
        tv.extend(V.tolist())
        tails.append({"clump": i, "length_cm": round(L_tail * ln * 100, 1), "start_angle_deg": round(a0, 1), **st})
    tv, tf = np.array(tv), np.array(tf)
    bv, bf = P1.tie_band(root + np.array([0, -0.002, -0.006]), np.array([0, 0.45, -1.0]), 0.032, tube=0.011)
    parts = [("hair_cap__movable", "hair", cap_v, cap_f), ("hair_masses", "hair", v1["hair_masses"].vertices, v1["hair_masses"].faces),
             ("ponytail", "hair", tv, tf), ("tie_band", "rope_bone", bv, bf)]
    export_roles(parts, a.out, flat=["ponytail", "tie_band"])   # hair_masses already carries v1's flat vertices: exported as-is
    tris = {p[0]: int(len(p[3])) for p in parts}
    info = {"out": a.out, "from": a.hair_v1, "tie": {"point": np.round(root, 4).tolist()}, "tris": tris, "tris_total": int(sum(tris.values())),
            "tail_clumps": tails, "hairline_table": hf.hairline[:8], "clumps": v1info.get("clumps", []),
            "clumps_per_region": v1info.get("clumps_per_region", {})}
    with open(os.path.splitext(a.out)[0] + "_parts.json", "w") as f:
        json.dump(info, f, indent=1)
    print(json.dumps({"tris": tris, "total": info["tris_total"], "tails": [(t["max_bend_deg"], t["thick_tie_cm"], t["thick_mid_cm"]) for t in tails]}))


if __name__ == "__main__":
    main()

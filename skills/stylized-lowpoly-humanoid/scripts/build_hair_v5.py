"""v5 primal male HAIR = v1 scalp hair (shell + clumps, unchanged) + the sealed v4 beard & moustache + 5 big crown spikes, each the
size of v4's longest chunk (Boss 25/10: «tóc xài tóc V1, add thêm mấy spiky chunk bằng size với chunk dài nhất hiện tại»).

  python3 build_hair_v5.py --body male_base_lp.glb --measurements male_measurements.json --hair-v1 male_hair_v1.glb --out male_hair_v5.glb

The spikes are built with the v4 crown-chunk builder (march over the scalp from the whorl, ridge section, root ROOT_THICK thick),
rooted at the whorl INSIDE the v1 clump layer (roots hidden), tips ≈ 21 cm from the whorl and 8–9 cm off the skull.
"""
import argparse
import json
import math
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from primal_body_frame import export_roles, load_body, load_json  # noqa: E402
from build_spiky_hair import HeadFrame  # noqa: E402
from measure_primal_assets import parts_of  # noqa: E402
import build_hair_masses_v2 as V2  # noqa: E402
import build_hair_crown_chunks_v4 as C4  # noqa: E402

SPIKES = [  # name, azimuth (deg from front, + = figure's left), path on the scalp (m), root width (m), tip stand-off parameter (m)
    ("front", 0.0, 0.10, 0.11, 0.075),
    ("front_left", 58.0, 0.095, 0.10, 0.072),
    ("front_right", -58.0, 0.095, 0.10, 0.072),
    ("back_left", 125.0, 0.095, 0.10, 0.072),
    ("back_right", -125.0, 0.095, 0.10, 0.072),
]


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
    W, D = meas["skull"]["width_m"], meas["skull"]["depth_m"]
    H = float(body.vertices[:, 1].max() - meas["face"]["chin_y"])
    brow = meas["face"]["brow_y"]
    v1 = parts_of(a.hair_v1)
    top, whorl, n_w = C4.find_whorl(hf, D)
    cv, cf, table = [], [], []
    for name, az, path_len, wd, tip_off in SPIKES:
        if name == "front":
            stop = lambda q: q[1] < brow + C4.BROW_CLEAR + 0.03
        else:
            stop = lambda q: q[1] < hf.ear_top_y + 0.02
        pts, nrm, ss = C4.march(hf, whorl, n_w, az, path_len, stop)
        heading = np.array([math.sin(math.radians(az)), 0, math.cos(math.radians(az))])
        Vv, F, rn = C4.chunk(pts, nrm, ss, wd, tip_off, heading)
        Vv = V2.clear_wedge(hf, Vv, F, rn)
        f0 = len(cf)
        cf.extend((F + len(cv)).tolist())
        cv.extend(Vv.tolist())
        tipdir = Vv[-1] - whorl
        sd = float(hf.q.signed_distance(Vv[-1][None])[0][0])
        table.append({"chunk": name, "azimuth_deg_from_front": az, "tip_from_whorl_cm": round(float(np.linalg.norm(tipdir)) * 100, 1),
                      "tip_off_skull_cm": round(sd * 100, 1), "tip_heading_deg": round(math.degrees(math.atan2(tipdir[0], tipdir[2])), 1),
                      "tip": np.round(Vv[-1], 4).tolist(), "length_cm": round(float(np.linalg.norm(tipdir)) * 100, 1), "faces": [f0, len(cf)]})
    cv, cf = np.array(cv), np.array(cf)
    bv, b_out, b_con, envelope, contact, rows_n = V2.build_beard(hf, meas, H, W)
    sv, sf = [], []
    for Vv, F, n in V2.moustache(hf, meas, contact, rows_n):
        Vv = V2.clear_wedge(hf, Vv, F, np.array([n, n, n, n]), min_gap=0.0025)
        sf.extend((F + len(sv)).tolist())
        sv.extend(Vv.tolist())
    sv, sf = np.array(sv), np.array(sf)
    def sub(Vv, F):
        used = np.unique(F)
        remap = -np.ones(len(Vv), int)
        remap[used] = np.arange(len(used))
        return Vv[used], remap[F]
    bov, bof = sub(bv, b_out)
    bcv, bcf = sub(bv, b_con)
    parts = [("hair_shell", "hair", v1["hair_shell"].vertices, v1["hair_shell"].faces),
             ("hair_clumps", "hair", v1["hair_clumps"].vertices, v1["hair_clumps"].faces),
             ("hair_spikes", "hair", cv, cf),
             ("beard_contact__movable", "hair", bcv, bcf), ("beard_outer", "hair", bov, bof), ("moustache", "hair", sv, sf)]
    export_roles(parts, a.out, flat=["hair_spikes", "beard_outer", "moustache"])
    tris = {p[0]: int(len(p[3])) for p in parts}
    info = {"out": a.out, "v1_source": a.hair_v1, "whorl": {"point": np.round(whorl, 4).tolist(), "skull_top": np.round(top, 4).tolist(),
            "back_of_top_cm": round(float(top[2] - whorl[2]) * 100, 1)}, "tris": tris, "tris_total": int(sum(tris.values())),
            "chunks": table, "clumps_per_region": {"v1_clumps": "unchanged", "crown_spikes": len(table)},
            "clumps": [{**t, "region": t["chunk"]} for t in table], "beard": {"lobes": 6, "moustache_lobes": 2, **envelope},
            "closed_before_flat_export": {}, "masks": {"fit_movable": ["beard_contact__movable"],
                                                       "protect_outer": [p[0] for p in parts if not p[0].endswith("__movable")]}}
    with open(os.path.splitext(a.out)[0] + "_parts.json", "w") as f:
        json.dump(info, f, indent=1)
    print(json.dumps({"tris": tris, "total": info["tris_total"], "spikes": [(t["chunk"], t["tip_from_whorl_cm"], t["tip_off_skull_cm"]) for t in table]}))


if __name__ == "__main__":
    main()

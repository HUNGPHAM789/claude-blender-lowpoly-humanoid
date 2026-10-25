"""Beard ↔ sideburn gap and lower-lip band (male beard v9, Boss 25/10: «cho dài ôm hai bên mặt hơn … cover thêm chút nữa chỗ da cằm
môi dưới»).

  python3 measure_beard_sideburn_gap.py --body male_base_lp.glb --measurements male_measurements.json --hair male_hair_v9.glb [--out x.json] [--max-gap-mm 0] [--max-band-mm 5]

GAP: side views (camera at ±x, level), one ray column per mm of depth across the jaw corner — from the ear lobe's front edge to
3.5 cm in front of it — rays every 1 mm in height from the chin up to the ear top. First DRAWN hit (back faces culled, like the
renderer) is beard / scalp hair / skin. In each column the bare-skin run between the highest beard ray and the lowest scalp-hair
ray above it is the gap. SIDEBURN columns = those whose lowest scalp-hair ray is within 15 mm of the sideburn tip (the lowest
scalp hair in front of that ear); further forward the hair above is the temple fringe, not the sideburn (cheek skin by design).
Reported per side as the max over the sideburn columns (0 = the beard meets the sideburn).
BAND: front view, midline ±1 cm: the lower-lip bottom (mouth line − 8 mm, the same rule the v7 builder uses) down to the first
drawn beard hit. Exit 1 when a limit is given and exceeded.
"""
import argparse
import json
import math
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from primal_body_frame import load_body, load_json  # noqa: E402
from analyze_outfit import ray_hits  # noqa: E402
from measure_primal_assets import parts_of  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--body", required=True)
    ap.add_argument("--measurements", required=True)
    ap.add_argument("--hair", required=True)
    ap.add_argument("--out")
    ap.add_argument("--max-gap-mm", type=float)
    ap.add_argument("--max-band-mm", type=float)
    a = ap.parse_args()
    meas = load_json(a.measurements)
    body = load_body(a.body)
    hp = parts_of(a.hair)
    groups = {"beard": [k for k in hp if k.startswith("beard")], "moustache": [k for k in hp if k.startswith("moustache")],
              "hair": [k for k in hp if not (k.startswith("beard") or k.startswith("moustache"))]}
    T, lab = [], []
    for g, names in groups.items():
        for k in names:
            T.append(hp[k].triangles)
            lab += [g] * len(hp[k].triangles)
    T.append(body.triangles)
    lab += ["skin"] * len(body.triangles)
    allt = np.vstack(T)
    lab = np.array(lab)
    nrm = np.cross(allt[:, 1] - allt[:, 0], allt[:, 2] - allt[:, 0])
    f = meas["face"]
    mid = f["midline_x"]
    rep = {"gap": {}, "band": {}}
    ys = np.arange(f["chin_y"] + 0.02, meas["ears"]["left"]["top_point"][1], 0.001)
    for side, s in (("left", 1), ("right", -1)):
        lobe = meas["ears"][side]["lobe_bottom_point"]
        D = np.array([-s, 0.0, 0.0])
        front = (nrm @ D) < 0
        cols = []
        for z in np.arange(lobe[2], lobe[2] + 0.035, 0.001):
            O = np.array([[mid + s * 0.5, y, z] for y in ys])
            H = ray_hits(allt, O, np.tile(D, (len(O), 1)), chunk=200)
            c = np.array([lab[h[front[h]][0]] if len(h[front[h]]) else "none" for h in H])
            bi = np.nonzero(c == "beard")[0]
            gap = None
            if len(bi):
                top_b = bi.max()
                hi = np.nonzero((c == "hair") & (np.arange(len(c)) > top_b))[0]
                if len(hi):
                    run = c[top_b + 1:hi.min()]
                    gap = float(np.sum(run == "skin")) if len(run) else 0.0
            hl = np.nonzero(c == "hair")[0]
            cols.append({"z": round(float(z), 3), "gap_mm": gap, "beard_top_y": round(float(ys[bi.max()]), 3) if len(bi) else None,
                         "hair_low_y": round(float(ys[hl.min()]), 3) if len(hl) else None})
        hv = np.vstack([hp[k].vertices for k in groups["hair"]])
        sel = hv[((hv[:, 0] - mid) * s > 0.055) & (hv[:, 2] > 0.0) & (hv[:, 1] < 1.70)]
        sb_y = float(sel[:, 1].min())
        for c_ in cols:
            c_["sideburn_column"] = c_["hair_low_y"] is not None and c_["hair_low_y"] < sb_y + 0.015
        measured = [c_["gap_mm"] for c_ in cols if c_["gap_mm"] is not None and c_["sideburn_column"]]
        rep["gap"][side] = {"sideburn_tip_y": round(sb_y, 4), "max_gap_mm": max(measured) if measured else None, "sideburn_columns_measured": len(measured),
                            "columns": len(cols), "columns_detail": cols}
    lip_bottom = f["chin_y"] + 0.35 * (f["eye_y"] - f["chin_y"]) - 0.008
    D = np.array([0, 0, -1.0])
    front = (nrm @ D) < 0
    yb = np.arange(lip_bottom, f["chin_y"], -0.0005)
    bands = []
    for dx in (-0.01, -0.005, 0.0, 0.005, 0.01):
        O = np.array([[mid + dx, y, 1.0] for y in yb])
        H = ray_hits(allt, O, np.tile(D, (len(O), 1)), chunk=200)
        c = np.array([lab[h[front[h]][0]] if len(h[front[h]]) else "none" for h in H])
        bi = np.nonzero(c == "beard")[0]
        bands.append(round((lip_bottom - yb[bi.min()]) * 1000, 1) if len(bi) else None)
    rep["band"] = {"lower_lip_bottom_y": round(lip_bottom, 4), "band_mm_at_dx_-10_-5_0_5_10": bands, "max_band_mm": max(b for b in bands if b is not None)}
    short = {"gap_max_mm": {k: v["max_gap_mm"] for k, v in rep["gap"].items()}, "band_max_mm": rep["band"]["max_band_mm"],
             "band_mm": bands}
    print(json.dumps(short))
    if a.out:
        with open(a.out, "w") as fh:
            json.dump(rep, fh, indent=1)
    bad = (a.max_gap_mm is not None and any((v["max_gap_mm"] is None or v["max_gap_mm"] > a.max_gap_mm) for v in rep["gap"].values())) or \
          (a.max_band_mm is not None and rep["band"]["max_band_mm"] > a.max_band_mm)
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()

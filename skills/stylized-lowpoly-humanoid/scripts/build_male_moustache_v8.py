"""Male hair v8 = male_hair_v7.glb with ONLY the moustache replaced (Boss 25/10: «râu mép giông râu trung quốc quá, cho râu bớt lệch
xuống quá nhiều, bản to hơn lông mày, sát lại nhau gần như dính ở giữa liền mạch»).

  python3 build_male_moustache_v8.py --body male_base_lp.glb --measurements male_measurements.json --hair-v7 male_hair_v7.glb --out male_hair_v8.glb

Two broad lobes lying ON the upper lip: inner ends overlap at the philtrum (reads as one shape), centreline droops DROOP_DEG from the
middle to the tip, height (front view) HEIGHT at the thickest ring — taller than the brow (2.1 cm inner end). Every other part is
copied unchanged from v7.
"""
import argparse
import json
import math
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from primal_body_frame import export_roles, load_body, load_json  # noqa: E402
from build_spiky_hair import HeadFrame, unit, az_dir  # noqa: E402
from measure_primal_assets import parts_of  # noqa: E402
import build_hair_masses_v2 as V2  # noqa: E402

DROOP_DEG = 10.0
HEIGHT = 0.029
THICK = 0.010
HALF_SPAN = 0.047


def lobe(hf, meas, sgn):
    q = hf.q
    f = meas["face"]
    mid_x = f["midline_x"]
    nose_bottom = f["eye_y"] - 0.05
    mouth_y = f["chin_y"] + 0.35 * (f["eye_y"] - f["chin_y"])
    yc0 = 0.5 * (nose_bottom + mouth_y) + 0.002          # centre of the upper lip
    xs = [-0.004, 0.016, 0.032, HALF_SPAN]               # inner end crosses the midline: the two lobes overlap
    pts, nrms = [], []
    for x in xs:
        y = yc0 - max(x, 0) * math.tan(math.radians(DROOP_DEG))
        hh, nn, dd = q.first_hit(np.array([[mid_x + sgn * x, y, 0.5]]), np.array([[0, 0, -1.0]]))
        p = hh[0]
        nv = unit(0.6 * unit(nn[0]) + 0.4 * np.array([sgn * 0.3 * (x / HALF_SPAN), 0, 1.0]))
        pts.append(p)
        nrms.append(nv)
    pts, nrms = np.array(pts), np.array(nrms)
    hprof = [0.85, 1.0, 0.85, 0.0]
    tprof = [1.0, 1.0, 0.8, 0.0]
    rings = []
    for i in range(3):
        tang = unit(pts[i + 1] - pts[max(i - 1, 0)]) if i > 0 else unit(pts[1] - pts[0])
        upv = unit(np.cross(tang, nrms[i])) * (1 if sgn > 0 else -1)
        if upv[1] < 0:
            upv = -upv
        hgt, t = HEIGHT * hprof[i], THICK * tprof[i]
        p, n = pts[i], nrms[i]
        rings.append([p + upv * hgt / 2 + n * 0.0025, p + n * (0.0025 + t), p - upv * hgt / 2 + n * 0.0025, p + n * 0.002])
    tip = pts[3] + nrms[3] * 0.004
    V = np.array([v for r in rings for v in r] + [tip])
    F = []
    for r in range(2):
        for i in range(4):
            j = (i + 1) % 4
            F += [[4 * r + i, 4 * r + j, 4 * (r + 1) + j], [4 * r + i, 4 * (r + 1) + j, 4 * (r + 1) + i]]
    for i in range(4):
        F.append([8 + i, 8 + (i + 1) % 4, 12])
    F += [[0, 2, 1], [0, 3, 2]]
    F = np.array(F)
    tri = V[F]
    nrm = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0])
    cen = tri.mean(axis=1)
    axis_pts = np.array([V[0:4].mean(0), V[4:8].mean(0), V[8:12].mean(0), V[12]])
    near = axis_pts[np.argmin(np.linalg.norm(cen[:, None] - axis_pts[None], axis=2), axis=1)]
    flip = np.einsum("ij,ij->i", nrm, cen - near) < 0
    F[flip] = F[flip][:, ::-1]
    V = V2.clear_wedge(hf, V, F, np.array([nrms[0], nrms[1], nrms[2], nrms[3]]), min_gap=0.002)
    return V, F


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--body", required=True)
    ap.add_argument("--measurements", required=True)
    ap.add_argument("--hair-v7", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    meas = load_json(a.measurements)
    body = load_body(a.body)
    hf = HeadFrame(body, meas)
    v7 = parts_of(a.hair_v7)
    parts = [(k, "hair", m.vertices, m.faces) for k, m in v7.items() if not k.startswith("moustache")]
    for sgn, name in ((1, "moustache_L"), (-1, "moustache_R")):
        V, F = lobe(hf, meas, sgn)
        parts.append((name, "hair", V, F))
    # unchanged parts keep their exported vertices exactly; only the new lobes are unmerged for flat shading
    export_roles(parts, a.out, flat=["moustache_L", "moustache_R"])
    info = {"out": a.out, "from": a.hair_v7, "tris": {p[0]: int(len(p[3])) for p in parts},
            "params": {"droop_deg": DROOP_DEG, "height_cm": HEIGHT * 100, "thick_cm": THICK * 100, "half_span_cm": HALF_SPAN * 100},
            "clumps": [], "clumps_per_region": {}, "closed_before_flat_export": {}}
    v7info = json.load(open(os.path.splitext(a.hair_v7)[0] + "_parts.json"))
    info["beard"] = v7info.get("beard", {})
    with open(os.path.splitext(a.out)[0] + "_parts.json", "w") as f:
        json.dump(info, f, indent=1, default=float)
    print(json.dumps(info["tris"]))


if __name__ == "__main__":
    main()

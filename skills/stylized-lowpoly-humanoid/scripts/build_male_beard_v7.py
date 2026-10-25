"""Male hair v7 = hair v6 (scalp cap, v2 masses, 70 % crown chunks — unchanged) + a CHIN-STRAP beard and two thick moustache lobes
(Boss 25/10: «râu quai nón từ chỗ 2 bên pát tóc đi cong xuống vùng dưới môi dưới, còn phía trên môi trên là 2 miếng râu mép dầy»;
v4/v6 beard climbed to the nose wings and read as a mask).

  python3 build_male_beard_v7.py --body male_base_lp.glb --measurements male_measurements.json --hair-v6 male_hair_v6.glb --out male_hair_v7.glb

Beard top edge = the straight line from the sideburn bottom (lobe height, in front of the ear) to the lower-lip corner, lowered by
EDGE_DROP; in the middle it sits just under the lower lip. Same closed contact/outer/lobe/underside construction as v4 (snug contact,
see-through-free caps). Moustache: two separate lobes rooted under the nose either side of the philtrum, sweeping down/out to the
mouth corners, ≥ 8 mm thick, not connected to the cheeks.
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

EDGE_DROP = 0.008


def mouth_points(meas):
    f = meas["face"]
    mouth_y = f["chin_y"] + 0.35 * (f["eye_y"] - f["chin_y"])
    return mouth_y, mouth_y - 0.008, 0.025          # mouth line, lower-lip corner height, corner half-width


def make_top_edge(hf, meas):
    f = meas["face"]
    mid_x = f["midline_x"]
    _, lip_corner_y, lip_cx = mouth_points(meas)
    sb_y = hf.lobe_y
    sb_x = float(np.mean([abs(meas["ears"][s]["lobe_bottom_point"][0] - mid_x) for s in ("left", "right")])) - 0.006
    def line_y(x):
        t = np.clip((x - lip_cx) / (sb_x - lip_cx), 0, 1)
        return lip_corner_y + t * (sb_y - lip_corner_y)
    def top_y(th):
        o = np.array([mid_x, lip_corner_y + 0.02, 0.03])
        h, _, d = hf.q.first_hit(o[None], az_dir(th, 0)[None])
        x = abs(h[0][0] - mid_x) if np.isfinite(d[0]) else 0.0
        return float(min(line_y(x) - EDGE_DROP, lip_corner_y - 0.004) if x < lip_cx else line_y(x) - EDGE_DROP)
    return top_y, line_y


def moustache_lobes(hf, meas):
    q = hf.q
    f = meas["face"]
    mid_x = f["midline_x"]
    nose_bottom = f["eye_y"] - 0.05
    mouth_y, _, lip_cx = mouth_points(meas)
    out = []
    for sgn in (-1, 1):
        y0 = nose_bottom - 0.013            # on the upper lip, just under the nose
        o = np.array([mid_x, y0, 0.03])
        h, n, _ = q.first_hit(o[None], az_dir(sgn * 6.0, 0)[None])
        root = h[0] + unit(n[0]) * 0.003
        nn = unit(0.5 * unit(n[0]) + 0.5 * az_dir(sgn * 4.0, 0))
        target = np.array([mid_x + sgn * (lip_cx + 0.020), mouth_y - 0.002, root[2] - 0.020])   # broad, mostly sideways: a thick lobe over the upper lip
        d = unit(target - root)
        d = unit(d - nn * np.dot(d, nn))
        lat = unit(np.cross(nn, d))
        L = float(np.linalg.norm(target - root)) * 1.05
        V = []
        for k, (wf, tf) in enumerate(((1.0, 0.009), (0.95, 0.010), (0.7, 0.008))):
            p = root + d * L * [0.0, 0.4, 0.75][k]
            V += [p + lat * 0.020 * wf / 2 + nn * 0.002, p + nn * (0.002 + tf), p - lat * 0.020 * wf / 2 + nn * 0.002, p + nn * 0.0015]
        V.append(root + d * L + nn * 0.005)
        V = np.array(V)
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
        V = V2.clear_wedge(hf, V, F, np.array([nn, nn, nn, nn]), min_gap=0.0025)
        thick = float(np.linalg.norm(V[5] - V[7]))
        out.append((V, F, thick))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--body", required=True)
    ap.add_argument("--measurements", required=True)
    ap.add_argument("--hair-v6", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    meas = load_json(a.measurements)
    body = load_body(a.body)
    hf = HeadFrame(body, meas)
    W = meas["skull"]["width_m"]
    H = float(body.vertices[:, 1].max() - meas["face"]["chin_y"])
    top_y, line_y = make_top_edge(hf, meas)
    bv, b_out, b_con, envelope, contact, rows_n = V2.build_beard(hf, meas, H, W, top_y_fn=top_y)
    def sub(Vv, F):
        used = np.unique(F)
        remap = -np.ones(len(Vv), int)
        remap[used] = np.arange(len(used))
        return Vv[used], remap[F]
    bov, bof = sub(bv, b_out)
    bcv, bcf = sub(bv, b_con)
    lobes = moustache_lobes(hf, meas)
    v6 = parts_of(a.hair_v6)
    parts = []
    for name in ("hair_cap__movable", "hair_masses", "hair_chunks"):
        parts.append((name, "hair", v6[name].vertices, v6[name].faces))
    parts += [("beard_contact__movable", "hair", bcv, bcf), ("beard_outer", "hair", bov, bof),
              ("moustache_L", "hair", lobes[1][0], lobes[1][1]), ("moustache_R", "hair", lobes[0][0], lobes[0][1])]
    export_roles(parts, a.out, flat=[p[0] for p in parts if not p[0].endswith("__movable")])
    tris = {p[0]: int(len(p[3])) for p in parts}
    info = {"out": a.out, "tris": tris, "tris_total": int(sum(tris.values())),
            "moustache_thickness_mm": {"L": round(lobes[1][2] * 1000, 1), "R": round(lobes[0][2] * 1000, 1)},
            "beard": {"lobes": 6, "moustache_lobes": 2, **envelope}, "clumps": [], "clumps_per_region": {}, "closed_before_flat_export": {},
            "edge_rule": {"edge_drop_mm": EDGE_DROP * 1000, "lip_corner": mouth_points(meas)}}
    with open(os.path.splitext(a.out)[0] + "_parts.json", "w") as f:
        json.dump(info, f, indent=1, default=float)
    print(json.dumps({"tris": tris, "total": info["tris_total"], "moustache_mm": info["moustache_thickness_mm"]}))


if __name__ == "__main__":
    main()

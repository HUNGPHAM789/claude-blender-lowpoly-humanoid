"""v4: chunks STAND OUT — root 3–4 cm thick, tips 6–12 cm off the skull (round-4 review: v3 «lies flat, a cap with two horns»).

v3 primal male HAIR: 5 big pointed chunks radiating from the crown whorl (front one longest) on a snug hidden cap,
+ the v2 beard and moustache unchanged.

Boss 25/10: «Tóc tôi muốn 4,5 chunk nhọn ra hướng về ra xung quanh từ xoáy đầu (đỉnh đầu ngược ra phía sau là xoáy đầu)
(chunk phía trước dài hơn các chunk hướng khác)».

  python3 build_hair_crown_chunks_v3.py --body male_base_lp.glb --measurements male_measurements.json --out male_hair_v3.glb

Whorl: the skull's top point moved back over the scalp by WHORL_BACK × skull depth (default 0.25).
Each chunk: a path marched over the scalp in 3D from the whorl toward its azimuth (works across the top pole), broad root
(roots overlap at the whorl), diamond section with a ridge, pointed tip lifted outward; 30 tris, closed, flat-shaded.
The front chunk stops above the brow ridge (≥ brow + BROW_CLEAR) so the eyebrow fitter has the brow free.
Geometries: hair_cap__movable, hair_chunks, beard_contact__movable, beard_outer, moustache (role 'hair').
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
import build_hair_masses_v2 as V2  # noqa: E402

WHORL_BACK = 0.25
BROW_CLEAR = 0.035
CHUNKS = [  # name, azimuth from front (deg, + = figure's left), path ON the scalp (m), root width (m), tip stand-off from the skull (m)
    ("front", 0.0, 0.10, 0.11, 0.075),
    ("front_left", 65.0, 0.075, 0.10, 0.065),
    ("front_right", -65.0, 0.075, 0.10, 0.065),
    ("back_left", 122.0, 0.07, 0.10, 0.07),
    ("back_right", -122.0, 0.07, 0.10, 0.07),
]
ROOT_THICK = 0.034


def onto_scalp(hf, p):
    d = unit(p - hf.C)
    h, n, dist = hf.q.first_hit(hf.C[None], d[None])
    if not np.isfinite(dist[0]):
        return None, None
    return h[0], unit(0.5 * unit(n[0]) + 0.5 * d)


def find_whorl(hf, depth):
    top, n_top = onto_scalp(hf, hf.C + np.array([0, 1.0, 0]))
    p, n = top, n_top
    target = WHORL_BACK * depth
    s = 0.0
    while s < target:
        step = min(0.004, target - s)
        t = unit(np.array([0, 0, -1.0]) - n * np.dot([0, 0, -1.0], n))
        p, n = onto_scalp(hf, p + t * step)
        s += step
    return top, p, n


def march(hf, start, n0, az, length, stop, nsteps=40):
    """walk over the scalp from `start` heading toward azimuth `az` (horizontal heading projected on the tangent plane, then
    carried forward — a geodesic-like path that crosses the top pole cleanly)."""
    head = np.array([math.sin(math.radians(az)), 0.0, math.cos(math.radians(az))])
    t = unit(head - n0 * np.dot(head, n0))
    pts, nrm, ss = [start], [n0], [0.0]
    p, n = start, n0
    ds = length / nsteps
    for k in range(nsteps):
        q, nq = onto_scalp(hf, p + t * ds)
        if q is None or stop(q):
            break
        t = unit(q - p)
        t = unit(t - nq * np.dot(t, nq))
        p, n = q, nq
        pts.append(p)
        nrm.append(n)
        ss.append(ss[-1] + ds)
    return np.array(pts), np.array(nrm), np.array(ss)


def chunk(pts, nrm, ss, width, tip_off, heading):
    """a big pointed wedge: 3 rings along the scalp path rising off the skull (ridge section, root ROOT_THICK thick), then a tip
    `tip_off` off the skull, pushed further along the heading. 30 tris, closed."""
    L = ss[-1]
    ks = [0.0, 0.45, 0.85]
    wprof = [1.0, 0.9, 0.55]
    tprof = [ROOT_THICK, ROOT_THICK * 0.95, ROOT_THICK * 0.7]
    lift = [0.0, 0.18, 0.4]
    rings, ring_n = [], []
    for k, wf, t, lf in zip(ks, wprof, tprof, lift):
        i = int(np.argmin(np.abs(ss - k * L)))
        p, n = pts[i], nrm[i]
        tang = unit(pts[min(i + 1, len(pts) - 1)] - pts[max(i - 1, 0)])
        lat = unit(np.cross(n, tang))
        e = V2.MASS_GAP + lf * tip_off
        w = width * wf
        rings.append([p + lat * w / 2 + n * (e + 0.003), p + n * (e + t), p - lat * w / 2 + n * (e + 0.003), p + n * e])
        ring_n.append(n)
    end_t = unit(pts[-1] - pts[-2])
    tip = pts[-1] + unit(0.55 * nrm[-1] + 1.0 * end_t) * tip_off * 1.6   # radiates OUT along its heading, rising off the skull
    Vv = [v for r in rings for v in r] + [tip]
    F = []
    nr = len(rings)
    for r in range(nr - 1):
        for i in range(4):
            j = (i + 1) % 4
            F += [[4 * r + i, 4 * r + j, 4 * (r + 1) + j], [4 * r + i, 4 * (r + 1) + j, 4 * (r + 1) + i]]
    for i in range(4):
        F.append([4 * (nr - 1) + i, 4 * (nr - 1) + (i + 1) % 4, 4 * nr])
    F += [[0, 2, 1], [0, 3, 2]]
    Vv, F = np.array(Vv), np.array(F)
    tri = Vv[F]
    nn = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0])
    cen = tri.mean(axis=1)
    axis_pts = np.array([np.mean(r, axis=0) for r in rings] + [tip])
    near = axis_pts[np.argmin(np.linalg.norm(cen[:, None] - axis_pts[None], axis=2), axis=1)]
    flip = np.einsum("ij,ij->i", nn, cen - near) < 0
    F[flip] = F[flip][:, ::-1]
    return Vv, F, np.array(ring_n + [nrm[-1]])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--body", required=True)
    ap.add_argument("--measurements", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    meas = load_json(a.measurements)
    body = load_body(a.body)
    hf = HeadFrame(body, meas)
    W = meas["skull"]["width_m"]
    D = meas["skull"]["depth_m"]
    H = float(body.vertices[:, 1].max() - meas["face"]["chin_y"])
    brow = meas["face"]["brow_y"]
    top, whorl, n_w = find_whorl(hf, D)
    cap_v, cap_f, _, _ = V2.build_cap(hf, rows_t=(0.0, 0.18, 0.38, 0.6, 0.82))   # denser cap: chords stay within a few mm of the scalp
    cv, cf, table = [], [], []
    for name, az, path_len, wd, tip_off in CHUNKS:
        if name == "front":
            stop = lambda q: q[1] < brow + BROW_CLEAR + 0.03
        else:
            stop = lambda q: q[1] < hf.ear_top_y + 0.02
        pts, nrm, ss = march(hf, whorl, n_w, az, path_len, stop)
        heading = np.array([math.sin(math.radians(az)), 0, math.cos(math.radians(az))])
        Vv, F, rn = chunk(pts, nrm, ss, wd, tip_off, heading)
        Vv = V2.clear_wedge(hf, Vv, F, rn)
        f0 = len(cf)
        cf.extend((F + len(cv)).tolist())
        cv.extend(Vv.tolist())
        tipdir = Vv[-1] - whorl
        sd = float(hf.q.signed_distance(Vv[-1][None])[0][0])
        table.append({"chunk": name, "azimuth_deg_from_front": az, "path_on_scalp_cm": round(float(ss[-1]) * 100, 1),
                      "tip_from_whorl_cm": round(float(np.linalg.norm(tipdir)) * 100, 1), "tip_off_skull_cm": round(sd * 100, 1),
                      "tip": np.round(Vv[-1], 4).tolist(), "length_cm": round(float(np.linalg.norm(tipdir)) * 100, 1),
                      "tip_heading_deg": round(math.degrees(math.atan2(tipdir[0], tipdir[2])), 1), "faces": [f0, len(cf)]})
    cv, cf = np.array(cv), np.array(cf)
    rng = np.random.default_rng(0)
    bv, b_out, b_con, envelope, contact, rows_n = V2.build_beard(hf, meas, H, W)
    sv, sf = [], []
    for Vv, F, n in V2.moustache(hf, meas, contact, rows_n):
        Vv = V2.clear_wedge(hf, Vv, F, np.array([n, n, n, n]), min_gap=0.0025)   # protected: must clear the lip/cheek itself
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
    parts = [("hair_cap", "hair", cap_v, cap_f), ("hair_chunks", "hair", cv, cf),
             ("beard_contact__movable", "hair", bcv, bcf), ("beard_outer", "hair", bov, bof), ("moustache", "hair", sv, sf)]
    export_roles(parts, a.out, flat=[p[0] for p in parts if not p[0].endswith("__movable")])
    tris = {p[0]: int(len(p[3])) for p in parts}
    info = {"out": a.out, "units": {"W_m": W, "H_m": H, "skull_depth_m": D},
            "whorl": {"point": np.round(whorl, 4).tolist(), "skull_top": np.round(top, 4).tolist(),
                      "back_of_top_cm": round(float(top[2] - whorl[2]) * 100, 1), "rule": f"{WHORL_BACK} × skull depth over the scalp"},
            "tris": tris, "tris_total": int(sum(tris.values())), "chunks": table,
            "clumps_per_region": {"crown_chunks": len(table)}, "clumps": [{**t, "region": t["chunk"]} for t in table],
            "beard": {"lobes": 6, "moustache_lobes": 2, **envelope},
            "closed_before_flat_export": {}, "masks": {"fit_movable": [p[0] for p in parts if p[0].endswith("__movable")],
                                                       "protect_outer": [p[0] for p in parts if not p[0].endswith("__movable")]}}
    with open(os.path.splitext(a.out)[0] + "_parts.json", "w") as f:
        json.dump(info, f, indent=1)
    print(json.dumps({"tris": tris, "total": info["tris_total"], "whorl": info["whorl"],
                      "chunks": [(t["chunk"], t["length_cm"], t["tip_heading_deg"]) for t in table]}))


if __name__ == "__main__":
    main()

"""Primal FEMALE hair: the v2 broad-mass grammar turned into the sheet's high PONYTAIL (Boss 25/10: v2 hair «có thể sau này làm
thành primal pony tail»).

  python3 build_ponytail_hair.py --body female_base_lp.glb --measurements female_measurements.json --out female_hair_v1.glb

Parts (role 'hair' unless noted; only the cap may be bent by the fitter):
  hair_cap__movable   concealed scalp cap (hairline, sideburns to the lobe)
  hair_masses         spiky crown + top, side/back masses swept toward the tie, and 2 framing locks per side hanging to the jaw
                      (mirror-symmetric: the fitter's «face-side hair balanced»)
  ponytail            4–5 big pointed masses from the tie down the back to about the shoulder blades
  tie_band (rope_bone) ring at the tail root
Tie point: on the back of the skull at TIE_HEIGHT × head height above the chin (spec root_height_on_head 0.55–0.57).
"""
import argparse
import json
import math
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from primal_body_frame import export_roles, load_body, load_json, BodyQuery  # noqa: E402
from build_spiky_hair import HeadFrame, unit  # noqa: E402
import build_hair_masses_v2 as V2  # noqa: E402

TIE_HEIGHT = 0.56


def layout(hf, H, W):
    brow = hf.face["brow_y"]
    ef, eb, ear_top = hf.ear_front_az, hf.ear_back_az, hf.ear_top_y
    chin = hf.face["chin_y"]
    def stop_fringe(p):
        return p[1] < brow + 0.05 * H
    def stop_side(p):
        az = abs(math.degrees(math.atan2(p[0] - hf.C[0], p[2] - hf.C[2])))
        return ef - 4 < az < eb + 4 and p[1] < ear_top + 0.006
    def stop_frame(p):
        return p[1] < chin + 0.035                       # framing locks hang to about the jaw
    def stop_back(p):
        return p[1] < hf.nape_y + 0.02
    out = []
    # spiky crown + top: up and out (the only upward masses)
    for th in (180, 120, 60, 0, -60, -120):
        out.append(("crown", th, 70, 0.0, -1.0, 0.30 * H, 0.30 * W, 0.45, 0.70, 2, None))   # spiky crown (sheet: tall spikes on top)
    # top/front: short spiky masses lying back-and-up from the hairline, kept above the brow
    for th in (-30, -10, 10, 30):
        out.append(("top", th, 50, 0.0, 1.0, 0.18 * H, 0.26 * W, 0.42, 0.45, 1, None))
    # framing locks: two per side, in front of the ears, hanging down beside the face to the jaw (mirror pairs)
    for th in (52.0, 72.0):
        for sgn in (1, -1):
            out.append(("frame", sgn * th, 30, 0.0, -1.0, 0.75 * H, 0.30 * W, 0.42, 0.14, 1, stop_frame))
    # sides behind the ears: swept back toward the tie
    for sgn in (1, -1):
        for th, ph in ((100, 40), (122, 30)):
            out.append(("side", sgn * th, ph, sgn * 1.0, 0.25, 0.30 * H, 0.26 * W, 0.40, 0.12, 1, stop_side))
    # back: swept UP toward the tie point
    for th in (150, 180, -150):
        out.append(("back", th, -15, 0.0, 1.0, 0.30 * H, 0.28 * W, 0.40, 0.08, 0, None))
    for th in (140, 165, -165, -140):
        out.append(("back", th, 15, 0.0, 1.0, 0.24 * H, 0.26 * W, 0.40, 0.10, 0, None))
    return out


def tail_mass(q, root, d0, length, width, thick, side, fan):
    """one big pointed tail mass: a 3D path from the tie down the back (gravity), 3 diamond rings + tip, 22 tris, closed.
    Pushed off the neck/back by whole rings if it would clip."""
    ks = [0.0, 0.35, 0.7]
    wprof = [0.6, 1.0, 0.7]
    pts = []
    for k in ks + [1.0]:
        s = k * length
        p = root + d0 * min(s, 0.05) + np.array([0, -1.0, 0]) * max(0.0, s - 0.05) * 0.95 + side * fan * s
        p = p + np.array([0, 0, -1.0]) * 0.03 * math.sin(math.pi * k)
        pts.append(p)
    pts = np.array(pts)
    rings, V = [], []
    for i, (k, wf) in enumerate(zip(ks, wprof)):
        tang = unit(pts[i + 1] - pts[i])
        out_n = unit(np.array([0, 0, -1.0]) - tang * np.dot([0, 0, -1.0], tang))
        lat = unit(np.cross(out_n, tang))
        w, t = width * wf, thick * wf
        rings.append([pts[i] + lat * w / 2, pts[i] + out_n * t / 2, pts[i] - lat * w / 2, pts[i] - out_n * t / 2])
    V = np.array([v for r in rings for v in r] + [pts[-1]])
    F = []
    for r in range(2):
        for i in range(4):
            j = (i + 1) % 4
            F += [[4 * r + i, 4 * r + j, 4 * (r + 1) + j], [4 * r + i, 4 * (r + 1) + j, 4 * (r + 1) + i]]
    for i in range(4):
        F.append([8 + i, 8 + (i + 1) % 4, 12])
    F += [[0, 2, 1], [0, 3, 2]]
    F = np.array(F)
    # clear the body: push rings backwards (−Z) until every vertex and face sample stands ≥ 8 mm off the skin
    for _ in range(20):
        smp = np.vstack([V, np.einsum("bk,fkj->fbj", V2.BARY, V[F]).reshape(-1, 3)])
        c = q.clearance(smp)
        if c.min() >= 0.008:
            break
        V = V + np.array([0, 0, -1.0]) * min(0.01, 0.008 - c.min() + 0.001)
    tri = V[F]
    nn = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0])
    cen = tri.mean(axis=1)
    axis_pts = np.vstack([pts[:3], pts[3:]])
    near = axis_pts[np.argmin(np.linalg.norm(cen[:, None] - axis_pts[None], axis=2), axis=1)]
    flip = np.einsum("ij,ij->i", nn, cen - near) < 0
    F[flip] = F[flip][:, ::-1]
    return V, F


def tie_band(centre, axis, radius, tube=0.009, n_seg=8, n_side=4):
    axis = unit(axis)
    a1 = unit(np.cross(axis, [1.0, 0, 0]))
    a2 = np.cross(axis, a1)
    V, F = [], []
    for s in range(n_seg):
        t = 2 * math.pi * s / n_seg
        c = centre + radius * (math.cos(t) * a1 + math.sin(t) * a2)
        radial = unit(c - centre)
        for k in range(n_side):
            u = 2 * math.pi * k / n_side + math.pi / 4
            V.append(c + tube * (math.cos(u) * radial + math.sin(u) * axis))
    for s in range(n_seg):
        for k in range(n_side):
            a, b = s * n_side + k, ((s + 1) % n_seg) * n_side + k
            c, d = ((s + 1) % n_seg) * n_side + (k + 1) % n_side, s * n_side + (k + 1) % n_side
            F += [[a, b, c], [a, c, d]]
    V, F = np.array(V), np.array(F)
    tri = V[F]
    nn = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0])
    ringc = np.array([centre + radius * (math.cos(2 * math.pi * s / n_seg) * a1 + math.sin(2 * math.pi * s / n_seg) * a2) for s in range(n_seg)])
    flip = np.einsum("ij,ij->i", nn, tri.mean(axis=1) - ringc[F[:, 0] // n_side]) < 0
    F[flip] = F[flip][:, ::-1]
    return V, F


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
    chin = meas["face"]["chin_y"]
    H = float(body.vertices[:, 1].max() - chin)
    cap_v, cap_f, _, _ = V2.build_cap(hf, rows_t=(0.0, 0.18, 0.38, 0.6, 0.82))
    mv, mf, table = [], [], []
    for (reg, th, ph, ut, up, L, Wd, thick, lift, layer, stop) in layout(hf, H, W):
        res = V2.wedge(hf, th, ph, ut, up, L, Wd, thick, lift, layer, stop)
        if res is None:
            table.append({"region": reg, "theta": th, "skipped": True})
            continue
        V, F, nr = res
        V = V2.clear_wedge(hf, V, F, nr)
        f0 = len(mf)
        mf.extend((F + len(mv)).tolist())
        mv.extend(V.tolist())
        table.append({"region": reg, "theta": th, "length_cm": round(L * 100, 1), "faces": [f0, len(mf)]})
    mv, mf = np.array(mv), np.array(mf)
    # tie point on the back of the skull
    tie_y = chin + TIE_HEIGHT * H
    o = np.array([hf.C[0], tie_y, hf.C[2]])
    hit, n, _ = hf.q.first_hit(o[None], np.array([[0, 0, -1.0]]))
    root = hit[0] + np.array([0, 0, -0.025])
    tv, tf = [], []
    tails = []
    shoulder_blade_y = meas["joints_gltf"]["nguc"][1]
    L_tail = float(root[1] - shoulder_blade_y)
    for i, (side_x, ln, wd) in enumerate(((0.0, 1.0, 0.10), (-1.0, 0.84, 0.085), (1.0, 0.84, 0.085), (-0.5, 0.66, 0.075), (0.5, 0.66, 0.075))):
        V, F = tail_mass(hf.q, root + np.array([side_x * 0.012, 0, -0.004 * abs(side_x)]), unit(np.array([0, -0.3, -1.0])),
                         L_tail * ln, wd, 0.042, np.array([1.0, 0, 0]) * np.sign(side_x) if side_x else np.zeros(3), 0.13 * abs(side_x))
        tf.extend((F + len(tv)).tolist())
        tv.extend(V.tolist())
        tails.append({"mass": i, "length_cm": round(L_tail * ln * 100, 1), "tip": np.round(V[-1], 3).tolist()})
    tv, tf = np.array(tv), np.array(tf)
    bv, bf = tie_band(root + np.array([0, -0.005, -0.004]), np.array([0, -0.3, -1.0]), 0.024)
    parts = [("hair_cap__movable", "hair", cap_v, cap_f), ("hair_masses", "hair", mv, mf), ("ponytail", "hair", tv, tf),
             ("tie_band", "rope_bone", bv, bf)]
    export_roles(parts, a.out, flat=["hair_masses", "ponytail", "tie_band"])
    tris = {p[0]: int(len(p[3])) for p in parts}
    counts = {}
    for r in table:
        if not r.get("skipped"):
            counts[r["region"]] = counts.get(r["region"], 0) + 1
    info = {"out": a.out, "tie": {"point": np.round(root, 4).tolist(), "height_frac_of_head": TIE_HEIGHT, "y": round(tie_y, 4)},
            "tris": tris, "tris_total": int(sum(tris.values())), "masses_per_region": counts, "tail_masses": tails,
            "clumps": [dict(t, region=t["region"]) for t in table], "clumps_per_region": counts}
    with open(os.path.splitext(a.out)[0] + "_parts.json", "w") as f:
        json.dump(info, f, indent=1)
    print(json.dumps({"tris": tris, "total": info["tris_total"], "counts": counts, "tie": info["tie"], "tails": tails}))


if __name__ == "__main__":
    main()

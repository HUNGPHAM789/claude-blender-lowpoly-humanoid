"""Female ponytail hair v2 (Boss 25/10, female round 2):
  * «sao trán hơi dồ»: the cap's front edge sits ≤ 3 mm off the forehead and blends flat; no front mass stands > 2.5 cm off it
    (the forward crown mass is gone; top masses lie low).
  * «tóc mọc chỗ trán … vùng nhọn giữa trán»: widow's-peak hairline (V at the midline 1.5–2.5 cm under the hairline height at ±3 cm,
    shallow recessions at ±3–4 cm, then down to the temples / sideburns).
  * «thêm tóc mái ngắn»: 7 short fringe locks rooted along that line, tips 0.04–0.10 H above the brow.
  * «tóc đuôi dày hơn và độ cong … tự nhiên»: ponytail ≈1.5× thicker, 7 overlapping clumps, each centreline 4 segments rising then
    arcing down the back, ≤ 30° turn at every joint.

  python3 build_ponytail_hair_v2.py --body female_base_lp.glb --measurements female_measurements.json --out female_hair_v2.glb
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
import build_ponytail_hair as P1  # noqa: E402

CAP_EDGE_GAP = 0.0012
PEAK_COLS = (6, 12, 18, 24, 32, 40)


def widows_peak(hf, hl):
    """hairline y(|azimuth|) with an M / widow's-peak front; the rest of the v1 hairline (temples → sideburn → nape) unchanged."""
    r = 0.09                               # forehead radius from the head centre: x = r·sin(az)
    az = lambda x_cm: round(math.degrees(math.asin(x_cm / 100 / r)), 1)
    front = [(0, hl - 0.020), (az(1.0), hl - 0.014), (az(2.0), hl - 0.006), (az(3.0), hl + 0.002), (az(3.7), hl + 0.006),
             (az(5.0), hl + 0.001), (40, hl - 0.012)]
    rest = [p for p in hf.hairline if p[0] > 44]
    return front + rest


def snug_cap(hf, cap_v, cap_f, cols):
    """re-seat the cap's lowest ring ON the skin (+ CAP_EDGE_GAP along the skin normal) on the front half, then clear only the rows
    above it (the radial clear pass had lifted the front edge 1.3 cm: a ledge on the forehead)."""
    nc = len(cols)
    q = hf.q
    for row, gap in ((0, CAP_EDGE_GAP), (1, 0.003), (2, 0.0035)):      # the first rows lie ON the forehead (no lifted band)
        for i, c in enumerate(cols):
            if abs(c) > 70:
                continue
            k = row * nc + i
            d = unit(cap_v[k] - hf.C)
            h, n, dist = q.first_hit(hf.C[None], d[None])
            if np.isfinite(dist[0]):
                cap_v[k] = h[0] + unit(0.5 * unit(n[0]) + 0.5 * d) * gap
    movable = np.ones(len(cap_v), bool)
    movable[:nc] = False
    total = np.zeros(len(cap_v))
    for _ in range(14):
        smp = np.einsum("bk,fkj->fbj", V2.BARY, cap_v[cap_f]).reshape(-1, 3)
        c = q.clearance(smp).reshape(len(cap_f), len(V2.BARY))
        lack = (0.0015 - c).max(axis=1)
        if lack.max() < 0.0002:
            break
        push = np.zeros(len(cap_v))
        for f, l in zip(cap_f, lack):
            if l > 0:
                push[f] = np.maximum(push[f], min(l + 0.0004, 0.004))
        push[~movable] = 0
        push = np.minimum(push, np.maximum(0, 0.006 - total))     # at most 6 mm lift per vertex: no bulged band over the forehead
        total += push
        cap_v = cap_v + unit(cap_v - hf.C) * push[:, None]
    return cap_v


def layout_v2(hf, H, W):
    out = []
    for item in P1.layout(hf, H, W):
        reg, th = item[0], item[1]
        if reg == "crown" and abs(th) < 1:           # the forward crown mass stood 7.7 cm off the forehead: dropped
            continue
        if reg == "top":                             # top masses lie low (no lift) so nothing at the front stands proud
            item = (reg, th, 56) + item[3:8] + (0.05, 0) + item[10:]
        out.append(item)
    return out


def fringe(hf, H, W, brow):
    """7 short locks rooted ON the widow's-peak line (the centre ones at the peak), falling onto the upper forehead."""
    tip_y = brow + 0.07 * H
    out = []
    for th in (-26, -17, -8, 0, 8, 17, 26):
        ph = hf.bottom_elevation(th) + 2.0
        root_y = hf.scalp_point(th, ph, 0.0)[0][1]
        best = None
        for fac in np.linspace(0.9, 2.2, 14):          # length searched so the TIP lands at ~0.07 H above the brow
            L = max(0.02, (root_y - tip_y) * fac)
            res = V2.wedge(hf, th, ph, 0.12 * np.sign(th), -1.0, L, 0.17 * W, 0.34, 0.04, 0, None)
            if res is None:
                continue
            err = abs(res[0][-1][1] - tip_y)
            if best is None or err < best[0]:
                best = (err, L)
        out.append(("fringe", th, ph, 0.12 * np.sign(th), -1.0, best[1], 0.17 * W, 0.34, 0.04, 0, None))
    return out


def tail_clump(q, root, lateral, length, width, thick, a0_deg, turns_deg, twist):
    """centreline of 4 segments in the plane (−Z back, Y up) rotated by `lateral`: starts rising back at a0, each joint turns down by
    turns_deg[i] (≤ 30°); rings (ridge section) at the first 4 points, pointed tip at the end. 38 tris, closed."""
    seg_frac = [0.12, 0.18, 0.30, 0.40]               # short rise, then the long fall carries most of the length
    ang = math.radians(a0_deg)
    pts = [root]
    dirs = []
    for k in range(4):
        if k > 0:
            ang -= math.radians(turns_deg[k - 1])
        d = np.array([0, math.sin(ang), -math.cos(ang)])
        d = unit(d + lateral * (0.25 + 0.15 * k))
        dirs.append(d)
        pts.append(pts[-1] + d * length * seg_frac[k])
    pts = np.array(pts)
    prof_w = [0.85, 1.0, 0.85, 0.55]
    prof_t = [1.0, 0.95, 0.75, 0.45]
    rings, thick_at = [], []
    for i in range(4):
        tang = unit(pts[i + 1] - pts[max(i - 1, 0)]) if i > 0 else dirs[0]
        out_n = unit(np.array([0, 0, -1.0]) - tang * np.dot([0, 0, -1.0], tang))
        if np.linalg.norm(out_n) < 1e-6:
            out_n = np.array([0, 1.0, 0])
        lat = unit(np.cross(out_n, tang))
        tw = twist * i
        lat, out_n = lat * math.cos(tw) + out_n * math.sin(tw), out_n * math.cos(tw) - lat * math.sin(tw)
        w, t = width * prof_w[i], thick * prof_t[i]
        rings.append([pts[i] + lat * w / 2, pts[i] + out_n * t / 2, pts[i] - lat * w / 2, pts[i] - out_n * t / 2])
        thick_at.append(t)
    V = np.array([v for r in rings for v in r] + [pts[-1]])
    F = []
    for r in range(3):
        for i in range(4):
            j = (i + 1) % 4
            F += [[4 * r + i, 4 * r + j, 4 * (r + 1) + j], [4 * r + i, 4 * (r + 1) + j, 4 * (r + 1) + i]]
    for i in range(4):
        F.append([12 + i, 12 + (i + 1) % 4, 16])
    F += [[0, 2, 1], [0, 3, 2]]
    F = np.array(F)
    for _ in range(25):                               # 8 mm off the neck / back: move the whole clump back
        smp = np.vstack([V, np.einsum("bk,fkj->fbj", V2.BARY, V[F]).reshape(-1, 3)])
        c = q.clearance(smp)
        if c.min() >= 0.008:
            break
        V = V + np.array([0, 0.15, -1.0]) / np.linalg.norm([0, 0.15, -1.0]) * min(0.01, 0.008 - c.min() + 0.001)
    tri = V[F]
    nn = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0])
    cen = tri.mean(axis=1)
    axis_pts = np.vstack([np.array([np.mean(r, axis=0) for r in rings]), V[-1:]])
    near = axis_pts[np.argmin(np.linalg.norm(cen[:, None] - axis_pts[None], axis=2), axis=1)]
    flip = np.einsum("ij,ij->i", nn, cen - near) < 0
    F[flip] = F[flip][:, ::-1]
    seg_dirs = np.diff(pts, axis=0)
    bends = [math.degrees(math.acos(np.clip(np.dot(unit(seg_dirs[k]), unit(seg_dirs[k + 1])), -1, 1))) for k in range(3)]
    return V, F, {"max_bend_deg": round(max(bends), 1), "bends_deg": [round(b, 1) for b in bends],
                  "thick_tie_cm": round(thick_at[0] * 100, 1), "thick_mid_cm": round(0.5 * (thick_at[1] + thick_at[2]) * 100, 1)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--body", required=True)
    ap.add_argument("--measurements", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    meas = load_json(a.measurements)
    body = load_body(a.body)
    hf = HeadFrame(body, meas)
    face = meas["face"]
    W = meas["skull"]["width_m"]
    chin, brow = face["chin_y"], face["brow_y"]
    H = float(body.vertices[:, 1].max() - chin)
    hf.hairline = widows_peak(hf, face["hairline_y"])
    cap_v, cap_f, phib, cols = V2.build_cap(hf, rows_t=(0.0, 0.16, 0.34, 0.56, 0.8), extra_cols=PEAK_COLS)
    cap_v = snug_cap(hf, cap_v, cap_f, cols)
    mv, mf, table = [], [], []
    for (reg, th, ph, ut, up, L, Wd, thick, lift, layer, stop) in layout_v2(hf, H, W) + fringe(hf, H, W, brow):
        res = V2.wedge(hf, th, ph, ut, up, L, Wd, thick, lift, layer, stop)
        if res is None:
            table.append({"region": reg, "theta": th, "skipped": True})
            continue
        V, F, nr = res
        V = V2.clear_wedge(hf, V, F, nr)
        f0 = len(mf)
        mf.extend((F + len(mv)).tolist())
        mv.extend(V.tolist())
        row = {"region": reg, "theta": th, "faces": [f0, len(mf)]}
        if reg == "fringe":
            row["tip_above_brow_cm"] = round(float(V[-1][1] - brow) * 100, 2)
            row["tip_above_brow_H"] = round(float(V[-1][1] - brow) / H, 3)
        table.append(row)
    mv, mf = np.array(mv), np.array(mf)
    tie_y = chin + P1.TIE_HEIGHT * H
    o = np.array([hf.C[0], tie_y, hf.C[2]])
    hit, n, _ = hf.q.first_hit(o[None], np.array([[0, 0, -1.0]]))
    root = hit[0] + np.array([0, 0.004, -0.028])
    L_tail = float(root[1] - meas["joints_gltf"]["nguc"][1]) * 1.05
    tv, tf, tails = [], [], []
    rng = np.random.default_rng(7)
    specs = [(0.0, 1.0, 0.13), (-0.5, 0.9, 0.11), (0.5, 0.9, 0.11), (-1.0, 0.78, 0.095), (1.0, 0.78, 0.095), (-0.25, 0.68, 0.085), (0.25, 0.68, 0.085)]
    for i, (lx, ln, wd) in enumerate(specs):
        turns = [rng.uniform(26, 29.5) for _ in range(3)]
        a0 = rng.uniform(8, 18)
        V, F, st = tail_clump(hf.q, root + np.array([lx * 0.014, rng.uniform(-0.006, 0.006), 0]), np.array([lx * 0.14, 0, 0]),
                              L_tail * ln, wd, 0.063, a0, turns, rng.uniform(-0.25, 0.25))
        tf.extend((F + len(tv)).tolist())
        tv.extend(V.tolist())
        tails.append({"clump": i, "length_cm": round(L_tail * ln * 100, 1), "start_rise_deg": round(a0, 1), **st})
    tv, tf = np.array(tv), np.array(tf)
    bv, bf = P1.tie_band(root + np.array([0, -0.002, -0.006]), np.array([0, 0.45, -1.0]), 0.032, tube=0.011)
    parts = [("hair_cap__movable", "hair", cap_v, cap_f), ("hair_masses", "hair", mv, mf), ("ponytail", "hair", tv, tf),
             ("tie_band", "rope_bone", bv, bf)]
    export_roles(parts, a.out, flat=["hair_masses", "ponytail", "tie_band"])
    tris = {p[0]: int(len(p[3])) for p in parts}
    counts = {}
    for r in table:
        if not r.get("skipped"):
            counts[r["region"]] = counts.get(r["region"], 0) + 1
    info = {"out": a.out, "hairline_table": hf.hairline[:8], "hairline_y": face["hairline_y"], "tie": {"point": np.round(root, 4).tolist()},
            "tris": tris, "tris_total": int(sum(tris.values())), "masses_per_region": counts, "fringe": [r for r in table if r["region"] == "fringe"],
            "tail_clumps": tails, "clumps": table, "clumps_per_region": counts}
    with open(os.path.splitext(a.out)[0] + "_parts.json", "w") as f:
        json.dump(info, f, indent=1)
    print(json.dumps({"tris": tris, "total": info["tris_total"], "counts": counts,
                      "fringe_tips_above_brow_cm": [r.get("tip_above_brow_cm") for r in info["fringe"]],
                      "tails": [(t["max_bend_deg"], t["thick_tie_cm"], t["thick_mid_cm"]) for t in tails]}))


if __name__ == "__main__":
    main()

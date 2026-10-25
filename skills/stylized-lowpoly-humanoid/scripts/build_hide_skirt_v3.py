"""v3 primal male SKIRT — v2 panel grammar, slim at the SIDES so the rest-pose hands clear every part by ≥ HAND_CLEAR
(Boss 25/10: «Tay xuyên váy là do cái quần nó lòi ra quá - thiết kế lại»). v2 notes follow.

v2 primal male SKIRT of overlapping hide PANELS + seated rope belt + long stone pendant (Codex audit 25/10 build brief v2,
steps 18–26; Boss: v1 skirt = «stiff barrel»).

  python3 build_hide_skirt_v3.py --body male_base_lp.glb --measurements male_measurements.json --out male_outfit_v3.glb [--seed 5]

G = belt centre → lowest skirt tip. Construction, inside → out:
  skirt_shell__movable  light concealed coverage tube (waist → top of the hem teeth), single-sided, the fitter may deform it
  skirt_tan_reveals     4 broad tan panels in the gaps between dark panels, longest (their V reveals run up between dark panels)
  skirt_under_panels    7 dark underlapping panels (shorter, rooted at the hip)
  skirt_main_panels     8 dark main panels from the belt, each with its own root, diagonal cut, skew and tip height
  rope_belt             12 stations × 5-sided irregular seated rope
  stone                 elongated faceted pendant (36 tris)
Each panel is a closed lens: front + back surfaces meeting along its outline, PANEL_THICK at the centre line.
Panels hang from their own root following the body profile at their own angle (no per-garment max-radius ring, no serrated rings).
"""
import argparse
import json
import math
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from primal_body_frame import export_roles, load_body, load_json  # noqa: E402
from build_torn_outfit import BodyProfile  # noqa: E402

PANEL_THICK = 0.006
HAND_CLEAR = 0.010
side_w = lambda th: math.sin(math.radians(th)) ** 4      # 0 front/back → 1 at the sides (where the hands hang)
thick_at = lambda th: PANEL_THICK * (1 - 0.33 * side_w(th))
FLARE = 0.03
SHELL_GAP = 0.0045


class Profile:
    """body radius at (y, θ) for hanging leather: above the widest hip = trunk radius; below = the max of the trunk radius from the
    widest hip down to y AT THIS ANGLE ONLY (a panel hangs from its own bulge) + a small flare."""

    def __init__(self, bp):
        self.bp = bp
        self.wy = bp.widest_y
        self._c = {}

    def r(self, y, th):
        key = (round(y / 0.005), round(th / 2.0))
        if key in self._c:
            return self._c[key]
        bp = self.bp
        def at(yy):
            p = np.array([[bp.cx + 0.1 * math.sin(math.radians(th)), yy, bp.cz + 0.1 * math.cos(math.radians(th))]])
            return float(bp.radius_at(p, band=0.008, half_deg=6.0)[0])
        if y >= self.wy:
            v = at(y)
        else:
            hang = max(at(yy) for yy in np.arange(self.wy, y - 1e-6, -0.02)) + FLARE * (self.wy - y)
            w = side_w(th)
            v = max(hang * (1 - w) + at(y) * w, at(y))     # the sides follow the hip/thigh; front/back may hang free
        self._c[key] = v
        return v

    def point(self, y, th, radius):
        c = math.radians(th)
        return np.array([self.bp.cx + radius * math.sin(c), y, self.bp.cz + radius * math.cos(c)])


def panel(pf, th_c, y0, y1, w_root, w_max, skew_deg, diag, e_fn, rows=(0.0, 0.28, 0.55, 0.8)):
    """one hide panel: rows down its own hanging path; each row = left edge, centre, right edge; tip point at s = 1.
    Edges are cut diagonally (left lower than right by `diag`·s) and the centre line skews by `skew_deg`·s."""
    wprof = lambda s: np.interp(s, [0, 0.3, 0.6, 0.85, 1.0], [w_root, w_max, 0.78 * w_max, 0.38 * w_max, 0])
    L, Cf, Cb, Rr = [], [], [], []
    for s in rows:
        y = y0 + (y1 - y0) * s
        th = th_c + skew_deg * s
        r_c = pf.r(y, th)
        half = math.degrees(wprof(s) / 2 / max(r_c, 0.05))
        yl, yr = y - diag * s, y + diag * s
        L.append(pf.point(yl, th - half, pf.r(yl, th - half) + e_fn(yl, th - half)))
        Rr.append(pf.point(yr, th + half, pf.r(yr, th + half) + e_fn(yr, th + half)))
        Cb.append(pf.point(y, th, r_c + e_fn(y, th)))
        Cf.append(pf.point(y, th, r_c + e_fn(y, th) + thick_at(th)))
    th_t = th_c + skew_deg
    tip = pf.point(y1, th_t, pf.r(y1, th_t) + e_fn(y1, th_t) + thick_at(th_t) * 0.5)
    n = len(rows)
    V = L + Cf + Cb + Rr + [tip]
    iL, iF, iB, iR, iT = 0, n, 2 * n, 3 * n, 4 * n
    F = []
    for k in range(n - 1):
        F += [[iL + k, iF + k, iF + k + 1], [iL + k, iF + k + 1, iL + k + 1], [iF + k, iR + k, iR + k + 1], [iF + k, iR + k + 1, iF + k + 1]]
        F += [[iL + k, iB + k + 1, iB + k], [iL + k, iL + k + 1, iB + k + 1], [iB + k, iR + k + 1, iR + k], [iB + k, iB + k + 1, iR + k + 1]]
    k = n - 1
    F += [[iL + k, iF + k, iT], [iF + k, iR + k, iT], [iL + k, iT, iB + k], [iB + k, iT, iR + k]]
    F += [[iL, iB, iF], [iF, iB, iR]]  # top closure
    V = np.array(V)
    F = np.array(F)
    # orient: faces on the front surface point away from the body axis, back-surface faces toward it, the top closure up
    axis = np.array([pf.bp.cx, 0, pf.bp.cz])
    tri = V[F]
    nrm = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0])
    rad = tri.mean(axis=1) - axis
    rad[:, 1] = 0
    has_f = np.isin(F, np.arange(iF, iF + n)).any(axis=1)
    has_b = np.isin(F, np.arange(iB, iB + n)).any(axis=1)
    want = np.where(has_f & has_b, 0, np.where(has_f, 1, -1))
    dots = np.einsum("ij,ij->i", nrm, rad)
    flip = ((want == 1) & (dots < 0)) | ((want == -1) & (dots > 0)) | ((want == 0) & (nrm[:, 1] < 0))
    F[flip] = F[flip][:, ::-1]
    return V, F


def clear_panel(bp, axis, V, F, min_gap=0.003, iters=10):
    """push only offending vertices radially out until vertices and face samples clear the skin (rays through a panel's wide
    chord met the glute/hip bulge — measured 25/10)."""
    from build_hair_masses_v2 import BARY
    rad = V - axis
    rad[:, 1] = 0
    rad /= np.linalg.norm(rad, axis=1, keepdims=True)
    for _ in range(iters):
        pts = np.vstack([V, np.einsum("bk,fkj->fbj", BARY, V[F]).reshape(-1, 3)])
        # TRUNK radius only (radial): the full-body clearance saw the hanging hands and blew the skirt into a bell (measured 25/10)
        c = np.hypot(pts[:, 0] - bp.cx, pts[:, 2] - bp.cz) - bp.radius_at(pts, band=0.008, half_deg=4.0)
        push = np.maximum(min_gap - c[:len(V)], 0)
        lack_f = (min_gap - c[len(V):]).reshape(len(F), len(BARY)).max(axis=1)
        for f, l in zip(F, lack_f):
            if l > 0:
                push[f] = np.maximum(push[f], l)
        if push.max() < 0.0002:
            break
        V = V + rad * (np.minimum(push, 0.01)[:, None] + 0.0003 * (push[:, None] > 0))
    return V


def hand_clear(bp, arm_kd, axis, V, F, clear=HAND_CLEAR, iters=12):
    """pull vertices radially IN where the vertex or a face sample is within `clear` of the rest-pose hand/arm, never below the
    trunk radius + 2 mm (if both cannot hold, the skin wins and the residue is reported by the measure script)."""
    from build_hair_masses_v2 import BARY
    rad = V - axis
    rad[:, 1] = 0
    rad /= np.linalg.norm(rad, axis=1, keepdims=True)
    for _ in range(iters):
        pts = np.vstack([V, np.einsum("bk,fkj->fbj", BARY, V[F]).reshape(-1, 3)])
        d = arm_kd.query(pts)[0]
        need = np.maximum(clear - d, 0)
        pull = need[:len(V)].copy()
        lack_f = need[len(V):].reshape(len(F), len(BARY))
        for f, ls in zip(F, lack_f):
            for b, l in zip(BARY, ls):
                if l > 0:
                    pull[f] = np.maximum(pull[f], l * np.clip(b * 1.6, 0, 1))
        if pull.max() < 0.0003:
            break
        Vn = V - rad * np.minimum(pull, 0.004)[:, None]
        floor = bp.radius_at(Vn, band=0.008, half_deg=4.0) + 0.002
        r_new = np.hypot(Vn[:, 0] - bp.cx, Vn[:, 2] - bp.cz)
        ok = r_new >= floor
        V = np.where(ok[:, None], Vn, V)
    return V


def stack(parts_list):
    V, F = [], []
    for v, f in parts_list:
        F.extend((f + len(V)).tolist())
        V.extend(v.tolist())
    return np.array(V), np.array(F)


def coverage_shell(pf, ys, ncol=16):
    cols = np.arange(ncol) * 360.0 / ncol
    V = [pf.point(y, th, pf.r(y, th) + SHELL_GAP) for y in ys for th in cols]
    F = []
    for r in range(len(ys) - 1):
        for i in range(ncol):
            j = (i + 1) % ncol
            a, b, c, d = r * ncol + i, r * ncol + j, (r + 1) * ncol + j, (r + 1) * ncol + i
            F += [[a, c, b], [a, d, c]]
    V = np.array(V)
    F = np.array(F)
    axis = np.array([pf.bp.cx, 0, pf.bp.cz])
    tri = V[F]
    nrm = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0])
    rad = tri.mean(axis=1) - axis
    rad[:, 1] = 0
    flip = np.einsum("ij,ij->i", nrm, rad) < 0
    F[flip] = F[flip][:, ::-1]
    return V, F


def rope(pf, y_c, outer_r, rng, n_seg=12, n_side=5):
    centres, radii = [], []
    phase = rng.uniform(0, 2 * math.pi)
    for s in range(n_seg):
        th = 360.0 * s / n_seg + rng.uniform(-6, 6)
        rr = 0.016 + 0.005 * rng.random()
        y = y_c + 0.008 * math.sin(2 * math.pi * s / n_seg * 2 + phase) + rng.uniform(-0.004, 0.004)
        R = outer_r(y, th) + rr * 0.85 + 0.003
        centres.append(pf.point(y, th, R))
        radii.append(rr)
    V, F = [], []
    axis = np.array([pf.bp.cx, 0, pf.bp.cz])
    for s in range(n_seg):
        radial = centres[s] - axis
        radial[1] = 0
        radial /= np.linalg.norm(radial)
        for k in range(n_side):
            a = 2 * math.pi * k / n_side + s * 0.9
            V.append(centres[s] + radii[s] * (math.cos(a) * radial + math.sin(a) * np.array([0, 1.0, 0])))
    for s in range(n_seg):
        t = (s + 1) % n_seg
        for k in range(n_side):
            m = (k + 1) % n_side
            a, b, c, d = s * n_side + k, t * n_side + k, t * n_side + m, s * n_side + m
            F += [[a, b, c], [a, c, d]]
    V, F = np.array(V), np.array(F)
    cen_ring = np.array(centres)
    tri = V[F]
    nrm = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0])
    flip = np.einsum("ij,ij->i", nrm, tri.mean(axis=1) - cen_ring[F[:, 0] // n_side]) < 0
    F[flip] = F[flip][:, ::-1]
    return V, F, centres, radii


def stone(top, out_dir, h, w, t):
    """elongated faceted pendant: top point, 3 six-vert rings, bottom point → 6 + 12 + 12 + 6 = 36 tris."""
    up = np.array([0, 1.0, 0])
    side = np.cross(up, out_dir)
    side /= np.linalg.norm(side)
    rings = [(0.18, 0.85), (0.45, 1.0), (0.75, 0.7)]
    V = [top]
    for fy, s in rings:
        c = top - up * h * fy
        for k in range(6):
            a = 2 * math.pi * k / 6 + (0.5 if fy == 0.45 else 0)
            V.append(c + side * (w / 2 * s * math.cos(a)) + out_dir * (t / 2 * s * math.sin(a) + t / 2))
    V.append(top - up * h)
    V = np.array(V)
    F = []
    for k in range(6):
        F.append([0, 1 + (k + 1) % 6, 1 + k])
    for r in range(2):
        for k in range(6):
            a, b = 1 + 6 * r + k, 1 + 6 * r + (k + 1) % 6
            c, d = 1 + 6 * (r + 1) + (k + 1) % 6, 1 + 6 * (r + 1) + k
            F += [[a, b, c], [a, c, d]]
    for k in range(6):
        F.append([19, 13 + k, 13 + (k + 1) % 6])
    F = np.array(F)
    cen = V.mean(axis=0)
    tri = V[F]
    nrm = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0])
    flip = np.einsum("ij,ij->i", nrm, tri.mean(axis=1) - cen) < 0
    F[flip] = F[flip][:, ::-1]
    return V, F


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--body", required=True)
    ap.add_argument("--measurements", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--seed", type=int, default=5)
    a = ap.parse_args()
    rng = np.random.default_rng(a.seed)
    meas = load_json(a.measurements)
    bp = BodyProfile(load_body(a.body), meas)
    from scipy.spatial import cKDTree
    arm_kd = cKDTree(bp.arm_P)
    far = arm_kd.query(bp.P)[0] > 0.02
    bp.P, bp.N = bp.P[far], bp.N[far]
    bp.kd_trunk = cKDTree(bp.P)
    bp._cache, bp._rcache = {}, {}
    ys = np.arange(0.80, 0.98, 0.01)
    bp.widest_y = float(ys[np.argmax([bp.raw(y).mean() for y in ys])])
    pf = Profile(bp)
    waist = meas["torso"]["waist_y"]
    belt_y = waist + 0.004
    root_main = waist + 0.012
    hem_low = meas["torso"]["mid_thigh_y"] - 0.04          # lowest tan tip
    G = belt_y - hem_low
    # SIDE SLITS under the hands: the rest-pose fingers touch the thigh (measured 25/10: hand 0–3 mm off the skin at y 0.80–0.85,
    # azimuth 62–96°), so no leather can pass there with 10 mm clearance. Panels centred in the hand wedge stop above the hand.
    J = meas["joints_gltf"]
    hand_top = max(J["co_tay_L"][1], J["co_tay_R"][1]) + 0.025
    arm_az = np.degrees(np.arctan2(bp.arm_P[:, 0] - bp.cx, bp.arm_P[:, 2] - bp.cz))
    low = bp.arm_P[:, 1] < hand_top
    wedge_L = (float(arm_az[low & (arm_az > 0)].min()) - 6, float(arm_az[low & (arm_az > 0)].max()) + 6)
    wedge_R = (float(arm_az[low & (arm_az < 0)].min()) - 6, float(arm_az[low & (arm_az < 0)].max()) + 6)
    def in_hand_wedge(th, margin=0.0):
        a_ = ((th + 180) % 360) - 180
        return wedge_L[0] - margin <= a_ <= wedge_L[1] + margin or wedge_R[0] - margin <= a_ <= wedge_R[1] + margin
    root_under, root_tan = pf.wy + 0.01, pf.wy + 0.08
    # layer offsets: v2 values front/back, slim stack at the sides (under 3 → tan 7.5 → main 12 mm + 4 mm leather)
    lerp = lambda f, sd, th: f * (1 - side_w(th)) + sd * side_w(th)
    e_main = lambda y, th=0.0: lerp(float(np.interp(y, [root_tan, root_tan + 0.06], [0.027, 0.008])),
                                     float(np.interp(y, [root_tan, root_tan + 0.06], [0.012, 0.005])), th)
    e_under = lambda y, th=0.0: lerp(0.0085, 0.003, th)
    e_tan = lambda y, th=0.0: lerp(0.0165, 0.0075, th)
    mains, unders, tans, table = [], [], [], []
    for i in range(8):
        th = 22.5 + 45 * i + rng.uniform(-6, 6)
        tip = belt_y - G * rng.uniform(0.62, 0.76)
        if in_hand_wedge(th):
            tip = max(tip, hand_top)
        V, F = panel(pf, th, root_main, tip, 0.12, 0.27 * G, rng.uniform(-10, 10), rng.choice([-1, 1]) * rng.uniform(0.015, 0.035), e_main,
                     rows=(0.0, 0.25, 0.5, 0.72, 0.88))
        mains.append((V, F))
        table.append({"panel_id": f"main_{i}", "overlap_group": "main", "theta": round(th, 1), "tip_y": round(tip, 3)})
    gaps = [45 * i + rng.uniform(-5, 5) for i in range(8)]
    for i, th in enumerate(gaps):
        if i == 4:
            continue
        tip = belt_y - G * rng.uniform(0.84, 0.94)
        if in_hand_wedge(th, margin=16.0):  # any part of its width under the hand: no under panel there (side slit)
            continue
        V, F = panel(pf, th, root_under, tip, 0.10, 0.26 * G, rng.uniform(-8, 8), rng.choice([-1, 1]) * rng.uniform(0.01, 0.025), e_under)
        unders.append((V, F))
        table.append({"panel_id": f"under_{i}", "overlap_group": "under", "theta": round(th, 1), "tip_y": round(tip, 3)})
    for th in (180.0 + rng.uniform(-5, 5), 337.5, 22.5, 157.5, 202.5):    # keep 7 under panels: those displaced from the side slits go front/back
        if len(unders) >= 7:
            break
        tip = belt_y - G * rng.uniform(0.84, 0.94)
        V, F = panel(pf, th, root_under, tip, 0.10, 0.26 * G, rng.uniform(-8, 8), rng.choice([-1, 1]) * rng.uniform(0.01, 0.025), e_under)
        unders.append((V, F))
        table.append({"panel_id": f"under_x{len(unders)}", "overlap_group": "under", "theta": round(th, 1), "tip_y": round(tip, 3)})
    for i, gi in enumerate((1, 3, 5, 7)):
        th = gaps[gi] + 6 * (1 if i % 2 else -1)
        tip = belt_y - G * rng.uniform(0.95, 1.0)
        if in_hand_wedge(th):
            tip = max(tip, hand_top)
        V, F = panel(pf, th, root_tan, tip, 0.12, 0.30 * G, rng.uniform(-6, 6), rng.choice([-1, 1]) * rng.uniform(0.01, 0.02), e_tan)
        tans.append((V, F))
        table.append({"panel_id": f"tan_{i}", "lining_reveal_id": i, "overlap_group": "tan", "theta": round(th, 1), "tip_y": round(tip, 3)})
    shell_v, shell_f = coverage_shell(pf, [root_main, 0.5 * (root_main + pf.wy + 0.06), pf.wy + 0.06, pf.wy - 0.05, hem_low + 0.10])
    sa = np.degrees(np.arctan2(shell_v[:, 0] - bp.cx, shell_v[:, 2] - bp.cz))
    for k in range(len(shell_v)):                 # shell notched up to the slit top inside the hand wedge
        if in_hand_wedge(sa[k]) and shell_v[k, 1] < hand_top:
            shell_v[k] = pf.point(hand_top, sa[k], pf.r(hand_top, sa[k]) + SHELL_GAP)
    shell_v = clear_panel(bp, np.array([bp.cx, 0, bp.cz]), shell_v, shell_f)
    axis = np.array([bp.cx, 0, bp.cz])
    mains = [(clear_panel(bp, axis, V, F), F) for V, F in mains]
    unders = [(clear_panel(bp, axis, V, F), F) for V, F in unders]
    tans = [(clear_panel(bp, axis, V, F), F) for V, F in tans]
    hand_report = {}
    def keep_off_hands(name, V, F):
        V = hand_clear(bp, arm_kd, axis, V, F)
        return V
    shell_v = hand_clear(bp, arm_kd, axis, shell_v, shell_f)
    mains = [(hand_clear(bp, arm_kd, axis, V, F), F) for V, F in mains]
    unders = [(hand_clear(bp, arm_kd, axis, V, F), F) for V, F in unders]
    tans = [(hand_clear(bp, arm_kd, axis, V, F), F) for V, F in tans]
    mv, mf = stack(mains)
    uv, uf = stack(unders)
    tv, tf = stack(tans)
    outer_r = lambda y, th: pf.r(y, th) + e_main(y, th) + thick_at(th)
    rv, rf, rc, rr = rope(pf, belt_y, outer_r, rng)
    front = rc[0]
    out_dir = np.array([0, 0, 1.0])
    top = front + np.array([0, -rr[0] * 0.6, rr[0] * 0.9])
    sv, sf = stone(top, out_dir, 0.22 * G, 0.085 * G, 0.022)
    parts = [("skirt_shell__movable", "leather_dark", shell_v, shell_f), ("skirt_tan_reveals", "leather_tan", tv, tf),
             ("skirt_under_panels", "leather_dark", uv, uf), ("skirt_main_panels", "leather_dark", mv, mf),
             ("rope_belt", "rope_bone", rv, rf), ("stone", "ornament_stone", sv, sf)]
    import trimesh
    closed = {p[0]: bool(trimesh.Trimesh(p[2], p[3], process=True).is_watertight) for p in parts}
    export_roles(parts, a.out, flat=[p[0] for p in parts if not p[0].endswith("__movable")])
    tris = {p[0]: int(len(p[3])) for p in parts}
    skirt = sum(v for k, v in tris.items() if k.startswith("skirt"))
    info = {"out": a.out, "G_m": round(G, 3), "belt_y": belt_y, "tris": tris, "skirt_tris": skirt, "panels": table,
            "counts": {"main": len(mains), "under": len(unders), "tan_reveals": len(tans)}, "side_slit": {"hand_top_y": round(hand_top, 3), "wedge_L_deg": [round(x, 1) for x in wedge_L], "wedge_R_deg": [round(x, 1) for x in wedge_R]}, "closed_before_flat_export": closed,
            "masks": {"fit_movable": ["skirt_shell__movable"], "protect_outer": [p[0] for p in parts if not p[0].endswith("__movable")]}}
    with open(os.path.splitext(a.out)[0] + "_parts.json", "w") as f:
        json.dump(info, f, indent=1)
    print(json.dumps({"tris": tris, "skirt": skirt, "G": round(G, 3), "closed": closed}))


if __name__ == "__main__":
    main()

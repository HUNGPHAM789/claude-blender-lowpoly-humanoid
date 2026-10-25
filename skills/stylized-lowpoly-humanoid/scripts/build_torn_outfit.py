"""Procedural torn, layered primal leather SKIRT + rope belt + front stone ornament on a measured base body (no image→3D).

  python3 build_torn_outfit.py --body male_base_lp.glb --measurements male_measurements.json --out male_outfit_v1.glb [--seed 3]

Spec: spec/SPEC_primal_torn_layered_outfit.json (two tiers of pointed flaps, lining peeking in the lower tier, belt band, ornament,
role colours, tri budgets). Frame: glTF metres, Y up, faces +Z; output already in place on the body.

Construction (inside → out)
1. BODY PROFILE: dense surface samples of torso + legs (arm/hand samples dropped by nearest bone), per ring height y and column
   azimuth the farthest sample + a band of ±1.5 cm (a low-poly ring between two body rings must not cut the bulge).
   Below the widest hip the radius never shrinks going down (leather hangs) and flares FLARE per metre.
2. LINING (leather_tan): one band from just under the hip to its own teeth, 1–3 cm longer than the outer teeth, offset a third of a tooth.
3. LOWER TIER (leather_dark): hip → teeth at mid-thigh (hem).
4. UPPER TIER (leather_dark): waist → teeth at ≈ 36 % of the height above the hem, covering the lower tier's roots.
   Each tier is ONE closed sheet THICK thick: outer + inner surfaces meeting at the top edge and along the torn tooth edge.
   Gap rule: inner surface INNER_GAP off the skin, or 3 mm outside the layer underneath; then every face is sampled and pushed out
   until it clears the skin by MIN_CLEAR.
5. ROPE BELT (rope_bone): lumpy 5-sided tube ring ON the waist over the skirt top; ORNAMENT (ornament_stone): faceted lens at the front.
"""
import argparse
import json
import math
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from primal_body_frame import BodyQuery, export_roles, load_body, load_json  # noqa: E402

INNER_GAP = 0.005
THICK = 0.0045
LAYER_SEP = 0.002
MIN_CLEAR = 0.004
FLARE = 0.10
N_COLS = int(os.environ.get("SKIRT_COLS", "24"))   # 8 teeth × 3 columns (spec: male skirt hem teeth 8); female 21 = 7 teeth (frees tris for the hand patch)


def seg_dist(P, a, b):
    ab = b - a
    t = np.clip(((P - a) @ ab) / (ab @ ab), 0, 1)
    return np.linalg.norm(P - (a + t[:, None] * ab), axis=1)


class BodyProfile:
    def __init__(self, body, meas):
        self.q = BodyQuery(body)
        J = {k: np.array(v) for k, v in meas["joints_gltf"].items()}
        P, N = self.q.P, self.q.N
        # nearest bone by SURFACE distance (distance to the segment − its radius): the hand hangs 8 cm from the hip skin but 15 cm
        # from the narrow hip joint, so a plain nearest-segment rule gave the hip side to the arm (measured 25/10: sign flips, skirt +6 cm)
        bones_keep = [("chau", "bung", 0.13), ("bung", "nguc", 0.14), ("nguc", "co", 0.13), ("chau", "hong_L", 0.13), ("chau", "hong_R", 0.13),
                      ("hong_L", "goi_L", 0.08), ("hong_R", "goi_R", 0.08), ("goi_L", "co_chan_L", 0.05), ("goi_R", "co_chan_R", 0.05)]
        bones_arm = []
        for s in ("L", "R"):
            hand_end = J[f"co_tay_{s}"] + (J[f"co_tay_{s}"] - J[f"khuyu_{s}"]) * 0.8
            bones_arm += [(J[f"vai_{s}"], J[f"khuyu_{s}"], 0.05), (J[f"khuyu_{s}"], J[f"co_tay_{s}"], 0.04), (J[f"co_tay_{s}"], hand_end, 0.035)]
        dk = np.min([seg_dist(P, J[a], J[b]) - r for a, b, r in bones_keep], axis=0)
        da = np.min([seg_dist(P, a, b) - r for a, b, r in bones_arm], axis=0)
        keep = dk <= da
        self.P, self.N = P[keep], N[keep]
        self.arm_P = P[~keep]
        from scipy.spatial import cKDTree
        self.kd_trunk = cKDTree(self.P)

        self.torso = meas["torso"]
        self.cx = float(meas["face"]["midline_x"])
        hip0 = round(float(meas["torso"]["hip_joint_y"]), 2)          # male 0.80 → identical to the original fixed ranges
        mid = (self.P[:, 1] > hip0 + 0.05) & (self.P[:, 1] < hip0 + 0.35)
        self.cz = float(0.5 * (self.P[mid, 2].min() + self.P[mid, 2].max()))
        self.cols = (np.arange(N_COLS) * 360.0 / N_COLS)  # 0 = front (+Z), clockwise toward +X
        self._cache = {}
        self._rcache = {}
        ys = np.arange(hip0, hip0 + 0.18, 0.01)
        self.widest_y = float(ys[np.argmax([self.raw(y).mean() for y in ys])])

    def signed_trunk(self, pts):
        """signed distance to torso + legs only (hands hang beside the skirt; they must not inflate it)."""
        d, i = self.kd_trunk.query(pts)
        sg = np.sign(np.einsum("ij,ij->i", pts - self.P[i], self.N[i]))
        sg[sg == 0] = 1
        return d * sg

    def radius_at(self, pts, band=0.012, half_deg=7.0):
        """trunk radius (farthest torso/leg sample) at each point's height and azimuth: the clearance reference for a ring garment
        (radial, so it never flips sign the way a nearest-sample normal does next to a hanging hand)."""
        out = np.zeros(len(pts))
        for k, p in enumerate(pts):
            key = (round(p[1] / 0.004), round(math.degrees(math.atan2(p[0] - self.cx, p[2] - self.cz)) / 3.0))
            if key not in self._rcache:
                y, th = key[0] * 0.004, key[1] * 3.0
                m = np.abs(self.P[:, 1] - y) < band
                d = self.P[m] - np.array([self.cx, 0, self.cz])
                a = np.degrees(np.arctan2(d[:, 0], d[:, 2]))
                sel = np.abs(((a - th + 180) % 360) - 180) < half_deg
                self._rcache[key] = float(np.hypot(d[sel, 0], d[sel, 2]).max()) if sel.any() else 0.0
            out[k] = self._rcache[key]
        return out

    def raw(self, y, band=0.010):
        key = round(y, 4)
        if key in self._cache:
            return self._cache[key]
        m = np.abs(self.P[:, 1] - y) < band
        d = self.P[m] - np.array([self.cx, 0, self.cz])
        th = np.degrees(np.arctan2(d[:, 0], d[:, 2])) % 360
        r = np.hypot(d[:, 0], d[:, 2])
        half = 360.0 / N_COLS / 2 + 2
        out = np.full(N_COLS, np.nan)
        for i, c in enumerate(self.cols):
            dd = np.abs(((th - c + 180) % 360) - 180)
            sel = dd < half
            if sel.any():
                out[i] = r[sel].max()
        if np.isnan(out).any():  # between the legs: carry the neighbours across
            good = ~np.isnan(out)
            idx = np.arange(N_COLS)
            out = np.interp(idx, np.r_[idx[good] - N_COLS, idx[good], idx[good] + N_COLS], np.r_[out[good], out[good], out[good]])
        self._cache[key] = out
        return out

    def hang(self, y):
        """body radius per column with the hang rule: below the widest hip the radius never shrinks and flares."""
        r = self.raw(y)
        if y >= self.widest_y:
            return r
        acc = self.raw(self.widest_y).copy()
        for yy in np.arange(self.widest_y - 0.01, y - 1e-6, -0.01):
            acc = np.maximum(acc, self.raw(yy))
        side = np.sin(np.radians(self.cols)) ** 2           # less flare at the sides, where the hands hang
        return np.maximum(acc, r) + FLARE * (1 - 0.75 * side) * (self.widest_y - y)

    def point(self, y, col_i, radius):
        c = math.radians(self.cols[col_i])
        return np.array([self.cx + radius * math.sin(c), y, self.cz + radius * math.cos(c)])


IRREGULAR = False
TOOTH_ROWS = []


def irregular_teeth(nc, tooth, start, rng):
    """torn hem, not a comb (Boss 25/10: «các nét rách của tà áo hơi bị đều»): tips at irregular gaps (2–5 columns), each tooth its own
    depth (0.45–1.6 × the design depth) and the valleys between them at uneven heights."""
    valley, tip = tooth
    depth = valley - tip
    tips = []
    i = start
    while True:
        tips.append(i % nc)
        i += int(rng.choice([2, 2, 3, 4, 5]))
        if i >= start + nc - 1:
            break
    ty = np.array([valley + rng.uniform(-0.30, 0.12) * depth for _ in range(nc)])   # valleys mostly LOWER (no tall gaps between teeth)
    for t in tips:
        ty[t] = valley - depth * rng.uniform(0.45, 1.6)
        if rng.random() < 0.4:                      # some teeth are broad: the neighbour also drops part-way
            nb = (t + (1 if rng.random() < 0.5 else -1)) % nc
            if nb not in tips:
                ty[nb] = 0.5 * (ty[nb] + ty[t])
    return ty


def tooth_stats(ty, col_deg):
    """per tier: tooth depth / spacing / width coefficient of variation (CV = std / mean)."""
    nc = len(ty)
    tips = [i for i in range(nc) if ty[i] < ty[(i - 1) % nc] and ty[i] < ty[(i + 1) % nc]]
    if len(tips) < 3:
        return None
    depth, spacing, width = [], [], []
    for k, t in enumerate(tips):
        n = tips[(k + 1) % len(tips)]
        gap = (n - t) % nc
        spacing.append(gap * col_deg)
        seg = [ty[(t + j) % nc] for j in range(gap + 1)]
        depth.append(max(seg) - ty[t])
        half = ty[t] + 0.5 * depth[-1]
        w = 0.0
        for sgn in (1, -1):
            j = 0
            while j < nc and ty[(t + sgn * (j + 1)) % nc] < half:
                j += 1
            a_, b_ = ty[(t + sgn * j) % nc], ty[(t + sgn * (j + 1)) % nc]
            frac = (half - a_) / (b_ - a_) if b_ != a_ else 0.5
            w += (j + float(np.clip(frac, 0, 1))) * col_deg
        width.append(w)
    cv = lambda x: float(np.std(x) / np.mean(x)) if np.mean(x) > 0 else 0.0
    return {"teeth": len(tips), "depth_cv": round(cv(depth), 3), "spacing_cv": round(cv(spacing), 3), "width_cv": round(cv(width), 3),
            "depth_cm": [round(d * 100, 1) for d in depth], "spacing_deg": [round(x, 1) for x in spacing]}


def build_layer(bp, rows, tooth, gaps, tip_cols, rng, tip_jit=0.022, val_jit=0.012):
    """rows: ring heights top → bottom (y); tooth = (valley_y, tip_y); gaps: per row + tooth row (inner surface off the hang profile).
    Returns verts, faces, and the per-row radius table (inner) for layering."""
    nc = N_COLS
    ys_rows = list(rows)
    ring_y = [np.full(nc, y) for y in ys_rows]
    if IRREGULAR:
        ty = irregular_teeth(nc, tooth, tip_cols, rng)
    else:
        ty = np.array([tooth[1] + rng.uniform(-tip_jit, tip_jit) if i % 3 == tip_cols else tooth[0] + rng.uniform(-val_jit, val_jit)
                       for i in range(nc)])
    TOOTH_ROWS.append(ty.copy())
    ring_y.append(ty)
    inner = []
    for k, yr in enumerate(ring_y):
        g = gaps[k]
        ring = []
        for i in range(nc):
            r = bp.hang(float(yr[i]))[i] + (g[i] if np.ndim(g) else g)
            ring.append(bp.point(float(yr[i]), i, r))
        inner.append(ring)
    inner = np.array(inner)  # R × C × 3
    return inner


def clear_layer(bp, inner, under_fn, min_clear, iters=10, max_push=0.012):
    """push inner rows out radially until the face samples clear the skin by min_clear and the layer below by LAYER_SEP."""
    R, C = inner.shape[:2]
    axis = np.array([bp.cx, 0, bp.cz])
    def radial(p):
        d = p - axis
        d[..., 1] = 0
        return d / np.linalg.norm(d, axis=-1, keepdims=True)
    bary = [(1/3, 1/3, 1/3), (.5, .5, 0), (0, .5, .5), (.5, 0, .5)]
    total_under = np.zeros((R, C))
    for _ in range(iters):
        push_b = np.zeros((R, C))
        push_u = np.zeros((R, C))
        worst = 0
        for r in range(R - 1):
            for i in range(C):
                j = (i + 1) % C
                quads = [((r, i), (r, j), (r + 1, j)), ((r, i), (r + 1, j), (r + 1, i))]
                for tri in quads:
                    T = np.array([inner[a] for a in tri])
                    pts = np.array([b[0] * T[0] + b[1] * T[1] + b[2] * T[2] for b in bary])
                    rp = np.hypot(pts[:, 0] - bp.cx, pts[:, 2] - bp.cz)
                    lack_b = (bp.radius_at(pts) + min_clear - rp).max()
                    lack_u = under_fn(pts).max() if under_fn is not None else -1
                    for lack, push in ((lack_b, push_b), (lack_u, push_u)):
                        if lack > 0.0003:
                            worst = max(worst, lack)
                            for a in tri:
                                push[a] = max(push[a], min(lack + 0.0005, 0.01))
        if worst == 0:
            break
        # skin clearance is never capped; clearing the layer underneath is capped at max_push in total (a layer must not
        # balloon over a lower one whose own ring cuts a bulge — measured 25/10: +6 cm over the hips)
        push_u = np.minimum(push_u, np.maximum(0, max_push - total_under))
        total_under += push_u
        inner = inner + radial(inner) * np.maximum(push_b, push_u)[..., None]
    return inner


def shell_from_inner(bp, inner, thick):
    """closed sheet: outer = inner + thick radially (top row and tooth row shared → the edge tapers to a blade)."""
    R, C = inner.shape[:2]
    axis = np.array([bp.cx, 0, bp.cz])
    d = inner - axis
    d[..., 1] = 0
    d /= np.linalg.norm(d, axis=-1, keepdims=True)
    outer = inner + d * thick
    verts = []
    idx_in = np.arange(R * C).reshape(R, C)
    verts.extend(inner.reshape(-1, 3))
    # outer rows 1..R-2 are new; row 0 and row R-1 are shared with inner (taper)
    idx_out = idx_in.copy()
    base = len(verts)
    for r in range(1, R - 1):
        for i in range(C):
            idx_out[r, i] = len(verts)
            verts.append(outer[r, i])
    faces = []
    for r in range(R - 1):
        for i in range(C):
            j = (i + 1) % C
            # outer surface: normal out
            a, b, c, e = idx_out[r, i], idx_out[r + 1, i], idx_out[r + 1, j], idx_out[r, j]
            faces += [[a, b, c], [a, c, e]]
            # inner surface: normal in (toward the body)
            a, b, c, e = idx_in[r, i], idx_in[r, j], idx_in[r + 1, j], idx_in[r + 1, i]
            faces += [[a, b, c], [a, c, e]]
    verts = np.array(verts)
    faces = np.array(faces)
    # orient: outer faces must point away from the axis
    tri = verts[faces]
    n = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0])
    cen = tri.mean(axis=1) - axis
    cen[:, 1] = 0
    is_outer = np.zeros(len(faces), bool)
    is_outer[0::4] = True
    is_outer[1::4] = True
    want = np.where(is_outer, 1, -1)
    flip = np.sign(np.einsum("ij,ij->i", n, cen)) != want
    faces[flip] = faces[flip][:, ::-1]
    return verts, faces, outer


def radius_lookup(bp, outer):
    """function pts → how far (m) a point would need to move out to sit LAYER_SEP outside this layer's outer surface."""
    axis = np.array([bp.cx, 0, bp.cz])
    ys = outer[:, :, 1]
    def under(pts):
        need = np.full(len(pts), -1.0)
        for k, p in enumerate(pts):
            d = p - axis
            th = math.degrees(math.atan2(d[0], d[2])) % 360
            i = int(round(th / (360.0 / N_COLS))) % N_COLS
            col_y = ys[:, i]
            if p[1] > col_y.max() or p[1] < col_y.min():
                continue
            col_r = np.hypot(outer[:, i, 0] - axis[0], outer[:, i, 2] - axis[2])
            order = np.argsort(col_y)
            r_out = np.interp(p[1], col_y[order], col_r[order])
            need[k] = r_out + LAYER_SEP - math.hypot(d[0], d[2])
        return need
    return under


def rope_belt(bp, y, skirt_outer_fn, rng, n_seg=14, n_side=5):
    axis = np.array([bp.cx, 0, bp.cz])
    centres, radii = [], []
    for s in range(n_seg):
        th = 360.0 * s / n_seg
        rr = 0.016 + 0.006 * rng.random()
        r_skirt = skirt_outer_fn(y, th)
        c = math.radians(th)
        sag = r_skirt * (1 - math.cos(math.pi / n_seg))
        R = r_skirt + rr + sag + 0.002
        centres.append(axis + np.array([R * math.sin(c), y + rng.uniform(-0.004, 0.004), R * math.cos(c)]))
        radii.append(rr)
    verts, faces = [], []
    for s in range(n_seg):
        c = math.radians(360.0 * s / n_seg)
        radial = np.array([math.sin(c), 0, math.cos(c)])
        up = np.array([0, 1.0, 0])
        for k in range(n_side):
            a = 2 * math.pi * k / n_side + s * 0.6
            verts.append(centres[s] + radii[s] * (math.cos(a) * radial + math.sin(a) * up))
    for s in range(n_seg):
        t = (s + 1) % n_seg
        for k in range(n_side):
            m = (k + 1) % n_side
            a, b, c2, d = s * n_side + k, t * n_side + k, t * n_side + m, s * n_side + m
            faces += [[a, b, c2], [a, c2, d]]
    verts = np.array(verts)
    faces = np.array(faces)
    cen_ring = np.array(centres)
    tri = verts[faces]
    n = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0])
    seg = faces[:, 0] // n_side
    flip = np.einsum("ij,ij->i", n, tri.mean(axis=1) - cen_ring[seg]) < 0
    faces[flip] = faces[flip][:, ::-1]
    return verts, faces, centres, radii


def ornament(centre, h=0.055, w=0.034, t=0.018):
    """faceted stone lens: top + bottom tip, two 6-vert rings → 24 tris."""
    verts = [centre + np.array([0, h / 2, 0]), centre + np.array([0, -h / 2, 0])]
    for yy, s in ((0.14 * h, 1.0), (-0.16 * h, 0.9)):
        for k in range(6):
            a = 2 * math.pi * k / 6 + (0.5 if yy < 0 else 0)
            verts.append(centre + np.array([s * w / 2 * math.cos(a), yy, s * t / 2 * math.sin(a) + t * 0.15]))
    faces = []
    for k in range(6):
        m = (k + 1) % 6
        faces.append([0, 2 + m, 2 + k])
        faces.append([2 + k, 2 + m, 8 + k])
        faces.append([2 + m, 8 + m, 8 + k])
        faces.append([1, 8 + k, 8 + m])
    verts = np.array(verts)
    faces = np.array(faces)
    tri = verts[faces]
    n = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0])
    flip = np.einsum("ij,ij->i", n, tri.mean(axis=1) - centre) < 0
    faces[flip] = faces[flip][:, ::-1]
    return verts, faces


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--body", required=True)
    ap.add_argument("--measurements", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--seed", type=int, default=3)
    ap.add_argument("--light-upper", action="store_true")
    ap.add_argument("--irregular", action="store_true", help="torn hem: irregular tooth depth / spacing / width (female v2)")
    ap.add_argument("--hem-raise", type=float, default=0.0, help="m: lift the hem (female sheet: hem a bit above mid-thigh)")
    a = ap.parse_args()
    rng = np.random.default_rng(a.seed)
    global IRREGULAR
    IRREGULAR = a.irregular
    meas = load_json(a.measurements)
    bp = BodyProfile(load_body(a.body), meas)
    waist = meas["torso"]["waist_y"]
    mid_thigh = meas["torso"]["mid_thigh_y"]
    top = waist + 0.02
    hem_tip = mid_thigh - 0.05 + a.hem_raise                       # teeth tips a little below mid-thigh, valleys above it
    H = top - hem_tip
    # spec tiers (fraction of the height above the hem): lower tier valleys ≈ 0.147 H, upper tier tips ≈ 0.358 H
    lower_valley = hem_tip + 0.147 * H
    upper_tip = hem_tip + 0.358 * H
    upper_valley = upper_tip + 0.12 * H
    lining_top = upper_tip + 0.01
    a_rows = [bp.widest_y + 0.06, bp.widest_y, lining_top - 0.07]   # tucked well up under the upper tier: a low front view saw skin between tiers
    u_rows = [top, waist - 0.06, bp.widest_y + 0.075, max(bp.widest_y, upper_valley + 0.025)]  # last ring stays above the tooth valleys (a valley above it folds the band)
    print("heights", dict(top=round(top, 3), hem_tip=round(hem_tip, 3), widest=bp.widest_y, upper_tip=round(upper_tip, 3)))

    # lining (innermost, tips 3.5 cm longer, a third of a tooth to the side)
    lin_in = build_layer(bp, [lining_top, lining_top - 0.06], (lower_valley - 0.015, hem_tip - 0.035), [INNER_GAP] * 3, 2, rng)
    lin_in = clear_layer(bp, lin_in, None, MIN_CLEAR)
    lv, lf, lout = shell_from_inner(bp, lin_in, THICK)
    under_lin = radius_lookup(bp, lout)
    # lower tier
    gA = [INNER_GAP, INNER_GAP + THICK + LAYER_SEP, INNER_GAP + THICK + LAYER_SEP, INNER_GAP + THICK + LAYER_SEP]  # the lining starts just under the 2nd ring
    A_in = build_layer(bp, a_rows, (lower_valley, hem_tip), gA, 1, rng)
    A_in = clear_layer(bp, A_in, under_lin, MIN_CLEAR)
    av, af, aout = shell_from_inner(bp, A_in, THICK)
    under_A = radius_lookup(bp, aout)
    # upper tier
    gU = [INNER_GAP, INNER_GAP, INNER_GAP + 0.003, INNER_GAP + THICK + LAYER_SEP, INNER_GAP + 2 * (THICK + LAYER_SEP)]  # only the lower tier is under it
    if a.light_upper:      # one ring fewer in the upper tier (frees 96 tris for refinement next to the hands)
        u_rows = [u_rows[0], u_rows[2], u_rows[3]]
        gU = [gU[0], gU[2], gU[3], gU[4]]
    U_in = build_layer(bp, u_rows, (upper_valley, upper_tip), gU, 0, rng, tip_jit=0.02, val_jit=0.01)
    U_in = clear_layer(bp, U_in, under_A, MIN_CLEAR)
    uv, uf, uout = shell_from_inner(bp, U_in, THICK)

    axis = np.array([bp.cx, 0, bp.cz])
    def skirt_outer(y, th):
        i = int(round(th / (360.0 / N_COLS))) % N_COLS
        col_y = uout[:, i, 1]
        col_r = np.hypot(uout[:, i, 0] - axis[0], uout[:, i, 2] - axis[2])
        o = np.argsort(col_y)
        r_u = float(np.interp(y, col_y[o], col_r[o]))
        r_body = float(bp.raw(y)[i])
        return max(r_u, r_body + INNER_GAP + THICK)
    belt_y = waist + 0.002
    bv, bf, bc, br = rope_belt(bp, belt_y, skirt_outer, rng)
    front = bc[0]
    orn_c = front + np.array([0, -0.032, br[0] + 0.004])
    ov, of = ornament(orn_c)
    parts = [("skirt_lining", "leather_tan", lv, lf), ("skirt_lower_tier", "leather_dark", av, af),
             ("skirt_upper_tier", "leather_dark", uv, uf), ("rope_belt", "rope_bone", bv, bf), ("ornament", "ornament_stone", ov, of)]
    export_roles(parts, a.out)
    tris = {p[0]: int(len(p[3])) for p in parts}
    skirt_tris = tris["skirt_lining"] + tris["skirt_lower_tier"] + tris["skirt_upper_tier"]
    info = {"out": a.out, "tris": tris, "skirt_tris": skirt_tris, "top_y": top, "hem_tip_y": hem_tip, "upper_tip_y": upper_tip,
            "lower_valley_y": lower_valley, "belt_y": belt_y, "widest_hip_y": bp.widest_y, "teeth_per_tier": N_COLS // 3}
    names = ["skirt_lining", "skirt_lower_tier", "skirt_upper_tier"]
    info["tooth_stats"] = {n: tooth_stats(t, 360.0 / N_COLS) for n, t in zip(names, TOOTH_ROWS)}
    print(json.dumps(info["tooth_stats"]))
    with open(os.path.splitext(a.out)[0] + "_build.json", "w") as f:
        json.dump(info, f, indent=1)
    print(json.dumps({"tris": tris, "skirt_tris": skirt_tris}))


if __name__ == "__main__":
    main()

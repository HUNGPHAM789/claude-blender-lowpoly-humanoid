"""LEARN the anatomy of the primal base bodies (Boss 25/10/2026): «Xác định vùng T shape của khuôn mặt và gắn lông mày dày vào · Học cách
làm lồi ra của phần dưới ngực nam · Cách đường cong các cơ bắp · bắp tay trước hóp vào chỗ cổ tay rồi lại cong ra chỗ cơ ngón cái ·
Đường cong của mông và đường đi vào · Đường cong của ngực nữ · Cơ cổ vai · Xương quai xanh · Lưng hỏm chỗ spine».

  python3 analyze_anatomy.py --body <body_fit.glb> --joints <joints.json> --sex male|female --out <dir>/<name>
  ⇒ <name>_anatomy.json · <name>_front.png / _back.png (depth-shaded maps with every found feature drawn) · <name>_limbs.png (radius plots)

Frame: glTF metres, Y up, body faces +Z. Joints JSON is Blender (x, y, z) ⇒ glTF (x, z, −y).
Depth maps: 900k surface samples binned on a 2.5 mm grid, FRONT = max z per cell, BACK = min z per cell.
"""
import argparse, json, math
import numpy as np
import trimesh
from PIL import Image, ImageDraw

CELL = 0.0025


def depth_maps(m, axes=(0, 1, 2)):
    """exact z-buffer per triangle (no sampling holes) on the plane (axes[0], axes[1]) with depth axes[2]:
    returns (MAX depth, MIN depth) per 2.5 mm cell — default plane x/y, depth z ⇒ FRONT = max z, BACK = min z."""
    V = m.vertices[:, list(axes)]; Fc = m.faces; x0, y0 = V[:, 0].min(), V[:, 1].min()
    W = int(np.ptp(V[:, 0]) / CELL) + 2; Hh = int(np.ptp(V[:, 1]) / CELL) + 2
    F = np.full((Hh, W), -np.inf); B = np.full((Hh, W), np.inf)
    T = V[Fc]; X = (T[:, :, 0] - x0) / CELL; Y = (T[:, :, 1] - y0) / CELL; Z = T[:, :, 2]
    for i in range(len(Fc)):
        xs, ys, zs = X[i], Y[i], Z[i]
        c0, c1 = int(np.floor(xs.min())), int(np.ceil(xs.max())); r0, r1 = int(np.floor(ys.min())), int(np.ceil(ys.max()))
        cc, rr = np.meshgrid(np.arange(c0, c1 + 1), np.arange(r0, r1 + 1)); px, py = cc.ravel() + 0.5, rr.ravel() + 0.5
        d = (ys[1] - ys[2]) * (xs[0] - xs[2]) + (xs[2] - xs[1]) * (ys[0] - ys[2])
        if abs(d) < 1e-12: continue
        l1 = ((ys[1] - ys[2]) * (px - xs[2]) + (xs[2] - xs[1]) * (py - ys[2])) / d
        l2 = ((ys[2] - ys[0]) * (px - xs[2]) + (xs[0] - xs[2]) * (py - ys[2])) / d; l3 = 1 - l1 - l2
        ok = (l1 >= -1e-6) & (l2 >= -1e-6) & (l3 >= -1e-6)
        if not ok.any(): continue
        z = l1[ok] * zs[0] + l2[ok] * zs[1] + l3[ok] * zs[2]; r_, c_ = rr.ravel()[ok], cc.ravel()[ok]
        np.maximum.at(F, (r_, c_), z); np.minimum.at(B, (r_, c_), z)
    F[np.isinf(F)] = np.nan; B[np.isinf(B)] = np.nan
    return F, B, x0, y0


class Map:
    def __init__(s, A, x0, y0): s.A, s.x0, s.y0 = A, x0, y0
    def col(s, x): return int(round((x - s.x0) / CELL))
    def row(s, y): return int(round((y - s.y0) / CELL))
    def y(s, r): return s.y0 + r * CELL
    def x(s, c): return s.x0 + c * CELL
    def z(s, x, y, half=1):
        c, r = s.col(x), s.row(y); v = s.A[max(0, r - half):r + half + 1, max(0, c - half):c + half + 1]
        return float(np.nanmedian(v)) if np.isfinite(v).any() else np.nan
    def colprof(s, x, ya, yb, half=2):                              # z along y at a fixed x (median over ±half columns)
        ys = np.arange(ya, yb, CELL); return ys, np.array([s.z(x, y, half) for y in ys])


def local_extrema(v, kind, w=4):
    out = []
    for i in range(w, len(v) - w):
        seg = v[i - w:i + w + 1]
        if np.isnan(v[i]) or np.isnan(seg).any(): continue
        if kind == "max" and v[i] == seg.max(): out.append(i)
        if kind == "min" and v[i] == seg.min(): out.append(i)
    return out


RIDGE_FLAT = 0.001   # m; rows within 1 mm of the band peak count as the ridge plateau


def main(body_p, joints_p, sex, out):
    m = trimesh.load(body_p, force="mesh"); m = trimesh.Trimesh(m.vertices, m.faces, process=True)
    Jb = json.load(open(joints_p)); J = {k: np.array([v[0], v[2], -v[1]]) for k, v in Jb.items()}
    F_, B_, x0, y0 = depth_maps(m); Fm, Bm = Map(F_, x0, y0), Map(B_, x0, y0)
    R = {"sex": sex}; marks_f, marks_b = [], []
    chin, top, neck, chest, belly, pelvis = J["dau"][1], J["dinh_dau"][1], J["co"][1], J["nguc"][1], J["bung"][1], J["chau"][1]
    Hd = top - chin
    # ---------------- face: MIDLINE, nose bridge WIDTH, brow ridge per side = the real T zone
    # (Boss 25/10: «chân mày đang bị lệch qua phải, vì bạn chỉ đo T shape ở một điểm còn sóng mũi nó có một khoảng ngang»)
    ys = np.arange(chin + 0.05 * Hd, chin + 0.85 * Hd, CELL)
    xmid_rows = []
    for y in ys:
        r = Fm.row(y); cs = [Fm.col(x) for x in (-0.05, 0.05)]; seg = Fm.A[r, cs[0]:cs[1]]
        if np.isfinite(seg).sum() > 10: xmid_rows.append(Fm.x(cs[0] + int(np.nanargmax(seg))))
    xm = float(np.median(xmid_rows)) if xmid_rows else 0.0
    prom = np.array([Fm.z(xm, y) - np.nanmean([Fm.z(xm - 0.03, y), Fm.z(xm + 0.03, y)]) for y in ys])
    tip_i = int(np.nanargmax(prom[: int(len(ys) * 0.6)]))                 # nose tip in the lower 60 % of the face (above = brow/forehead)
    brow_pts = []; eye_y = []
    for xs in np.arange(0.012, 0.072, 0.004):
        for sgn in (-1, 1):
            yy, zz = Fm.colprof(xm + sgn * xs, ys[tip_i], chin + 0.95 * Hd, half=1)
            mins = local_extrema(zz, "min", 3)
            if not mins: continue
            # brow ridge = the MOST PROUD row in the band just above the socket (Boss 25/10: «chỗ lồi nhất của T shape»); the first local
            # max was a 1-cell bump inside the socket on the male (brow ended up «ở chỗ lõm mắt»)
            eye = mins[0]; hi = min(len(yy), eye + int(0.25 * Hd / CELL))
            if hi - eye < 3: continue
            seg = zz[eye:hi]; b = eye + int(np.argmax(seg >= np.nanmax(seg) - RIDGE_FLAT))   # first row on the plateau = socket rim (female forehead is flat)
            if b <= eye + 1 or zz[b] - zz[eye] < 0.002: continue
            brow_pts.append((sgn * xs, float(yy[b]), float(zz[b]), float(zz[b] - zz[eye]))); eye_y.append(float(yy[eye]))
    face = {"midline_x_cm": round(xm * 100, 2), "nose_tip_y_frac_of_head": round(float((ys[tip_i] - chin) / Hd), 3), "nose_tip_proud_cm": round(float(prom[tip_i] * 100), 2)}
    if brow_pts:
        bp = np.array(brow_pts); by = float(np.median(bp[:, 1])); ey = float(np.median(eye_y))
        # bridge width: at rows between the eyes and the brow, how far from the midline the surface stays within 4 mm of the centre
        hw = []
        for y in np.arange(ey - 0.006, ey + 0.010, CELL):                    # at the SOCKET rows: where the bridge meets the inner eye corner
            zc = Fm.z(xm, y)
            for sgn in (-1, 1):
                for d in np.arange(0.002, 0.04, CELL):
                    if Fm.z(xm + sgn * d, y) < zc - 0.004: hw.append(d); break
        bridge = float(np.median(hw)) if hw else 0.012
        L_ = bp[bp[:, 0] > 0]; R_ = bp[bp[:, 0] < 0]
        face.update({"bridge_half_width_cm": round(bridge * 100, 2), "eye_y_abs": round(ey, 4), "eye_y_frac_of_head": round((ey - chin) / Hd, 3), "brow_y_frac_of_head": round((by - chin) / Hd, 3),
                     "brow_over_eye_socket_cm": round(float(np.median(bp[:, 3]) * 100), 2),
                     "brow_height_left_vs_right_cm": round(float((np.median(L_[:, 1]) - np.median(R_[:, 1])) * 100), 2) if len(L_) and len(R_) else None,
                     "brow_line_rel_midline": [[round(a, 4), round(b, 4), round(c, 4)] for a, b, c, _ in brow_pts],
                     "T_zone": {"brow_band_y": [round(by - 0.01, 4), round(by + 0.015, 4)], "brow_band_x_from_midline": [round(bridge, 4), 0.072],
                                "nose_strip_half_width": round(bridge, 4), "nose_strip_y": [round(float(ys[tip_i]), 4), round(by, 4)]}})
        marks_f += [("brow", [(xm + p[0], p[1]) for p in brow_pts], (40, 30, 25)),
                    ("T", [(xm + dx, y) for y in np.arange(ys[tip_i], by, 0.004) for dx in (-bridge, bridge)], (200, 40, 40)),
                    ("mid", [(xm, y) for y in np.arange(ys[tip_i], by + 0.02, 0.006)], (230, 160, 30))]
    R["face_T_zone"] = face
    # ---------------- ears: lateral bump on the side depth maps; lobe = lowest point ⇒ sideburn / nape hair-root anchors
    from scipy.ndimage import gaussian_filter
    Lmax, Lmin, z0s, y0s = depth_maps(m, axes=(2, 1, 0))                   # plane z/y, depth x: max x = left side, min x = right side
    ears = {}
    for side, A_, sgn in (("left", Lmax, 1), ("right", Lmin, -1)):
        M_ = np.isfinite(A_); Af = np.where(M_, A_, 0.0); sm = gaussian_filter(Af, 8) / np.maximum(gaussian_filter(M_.astype(float), 8), 1e-6)
        bump = sgn * (A_ - sm); r0, r1 = int((chin - 0.02 - y0s) / CELL), int((chin + 0.80 * Hd - y0s) / CELL)
        zc_ = J["dau"][2]; c0, c1 = int((zc_ - 0.07 - z0s) / CELL), int((zc_ + 0.05 - z0s) / CELL)
        win = np.zeros_like(M_); win[max(0, r0):r1, max(0, c0):c1] = True
        ear = win & M_ & (bump > 0.006)
        from scipy.ndimage import label as _lab
        lab, n = _lab(ear)
        if n:
            k = 1 + int(np.argmax([(lab == i).sum() for i in range(1, n + 1)])); rr, cc = np.where(lab == k)
            peak = np.argmax(bump[rr, cc]); lobe = np.argmin(rr); top = np.argmax(rr)
            P = lambda i: [round(float(A_[rr[i], cc[i]]), 4), round(float(y0s + rr[i] * CELL), 4), round(float(z0s + cc[i] * CELL), 4)]
            ears[side] = {"most_proud_point": P(peak), "proud_cm": round(float(bump[rr[peak], cc[peak]] * 100), 2), "lobe_bottom_point": P(lobe), "top_point": P(top),
                          "height_cm": round(float((rr.max() - rr.min()) * CELL * 100), 1), "depth_cm": round(float((cc.max() - cc.min()) * CELL * 100), 1),
                          "lobe_y_frac_of_head": round(float((y0s + rr[lobe] * CELL - chin) / Hd), 3), "top_y_frac_of_head": round(float((y0s + rr[top] * CELL - chin) / Hd), 3)}
    if ears:
        R["ears"] = ears
        R["hair_root_anchors"] = {"sideburn": "from the temple down IN FRONT of the ear to the lobe height (lobe_bottom_point y)",
                                  "behind_ear": "hairline wraps behind the ear top_point and drops to the nape at lobe height",
                                  "lobe_y_frac_of_head": float(np.mean([e["lobe_y_frac_of_head"] for e in ears.values()]))}
    # ---------------- chest: pec underside (male) / breast (female) at the nipple line x
    xc = 0.085 if sex == "male" else 0.075
    yy, zz = Fm.colprof(xc, belly, neck); zz2 = np.array([np.nanmean([a, b]) for a, b in zip(zz, Fm.colprof(-xc, belly, neck)[1])])
    pk = [i for i in local_extrema(zz2, "max", 6) if chest - 0.08 < yy[i] < chest + 0.10]
    if pk:
        p = max(pk, key=lambda i: zz2[i]); below = [i for i in local_extrema(zz2, "min", 4) if i < p]
        f = max(below) if below else int(np.nanargmin(zz2[:p])) if p > 0 else 0
        above = zz2[p:]; up_y = yy[p:]; ok = np.isfinite(above)
        slope_up = math.degrees(math.atan2(float(zz2[p] - above[ok][-1]), float(up_y[ok][-1] - yy[p]))) if ok.sum() > 2 else None
        seg = slice(f, p + 1); dz = np.gradient(zz2[seg], CELL) if p - f > 2 else np.array([0])
        R["chest"] = {"peak_y_above_chest_joint_cm": round(float((yy[p] - chest) * 100), 1), "peak_proud_over_fold_cm": round(float((zz2[p] - zz2[f]) * 100), 2),
                      "fold_below_peak_cm": round(float((yy[p] - yy[f]) * 100), 1), "upper_slope_deg_from_vertical": round(slope_up, 1) if slope_up is not None else None,
                      "underside_max_slope_deg": round(float(math.degrees(math.atan(np.nanmax(np.abs(dz))))), 1), "x_cm": xc * 100,
                      "profile_y_z": [[round(float(a), 4), round(float(b), 4)] for a, b in zip(yy[::4], zz2[::4]) if np.isfinite(b)]}
        marks_f += [("chest peak", [(xc, yy[p]), (-xc, yy[p])], (220, 120, 30)), ("chest fold", [(xc, yy[f]), (-xc, yy[f])], (60, 60, 200))]
    # ---------------- clavicle ridge + trapezius slope (front)
    clav = []
    xs_sh = abs(J["vai_L"][0])
    for xs in np.arange(0.02, xs_sh - 0.02, 0.01):
        for sgn in (-1, 1):
            yy, zz = Fm.colprof(sgn * xs, neck - 0.12, neck - 0.005, half=1)   # clavicle lives just under the neck (lower = pec top edge)
            mx = local_extrema(zz, "max", 3)
            if mx:
                i = max(mx); mn = [k for k in local_extrema(zz, "min", 3) if k < i]
                clav.append((sgn * xs, float(yy[i]), float(zz[i] - (zz[max(mn)] if mn else np.nanmin(zz[:i]) if i > 0 else zz[i]))))
    if clav:
        c_ = np.array(clav); cl = c_[c_[:, 0] > 0]
        R["clavicle"] = {"ridge": [[round(a, 4), round(b, 4)] for a, b, _ in clav], "proud_over_hollow_below_cm": round(float(np.median(c_[:, 2]) * 100), 2),
                         "rise_deg_sternum_to_shoulder": round(float(math.degrees(math.atan(np.polyfit(cl[:, 0], cl[:, 1], 1)[0]))), 1) if len(cl) > 2 else None,
                         "y_below_neck_joint_cm": round(float((neck - np.median(c_[:, 1])) * 100), 1)}
        marks_f.append(("clavicle", [(a, b) for a, b, _ in clav], (30, 140, 60)))
    top_line = []
    for xs in np.arange(0.03, xs_sh + 0.06, 0.005):
        c = Fm.col(xs); colv = Fm.A[:, c]; idx = np.where(np.isfinite(colv) & (np.arange(len(colv)) < Fm.row(chin)))[0]
        if len(idx): top_line.append((xs, Fm.y(idx.max())))
    if top_line:
        t = np.array(top_line); t = t[t[:, 0] <= xs_sh]                   # neck → acromion only (beyond is the deltoid curve)
        chord = np.interp(t[:, 0], [t[0, 0], t[-1, 0]], [t[0, 1], t[-1, 1]])
        R["trapezius"] = {"neck_to_shoulder_drop_cm": round(float((t[0, 1] - t[-1, 1]) * 100), 1),
                          "slope_deg": round(float(math.degrees(math.atan2(t[0, 1] - t[-1, 1], t[-1, 0] - t[0, 0]))), 1),
                          "bulge_over_chord_cm": round(float(np.max(t[:, 1] - chord) * 100), 2), "line": [[round(a, 4), round(b, 4)] for a, b in top_line[::3]]}
        marks_f.append(("trapezius", top_line, (150, 60, 160)))
    # ---------------- back: spine groove, glutes, lower-back hollow
    sp = []
    for y in np.arange(belly - 0.06, neck, 0.01):                     # waist up (below = gluteal cleft, not the spine)
        zc = Bm.z(0, y); zs = np.nanmean([Bm.z(-0.035, y), Bm.z(0.035, y)])
        if np.isfinite(zc) and np.isfinite(zs): sp.append((y, (zc - zs) * 100))    # back surface is −z: groove ⇒ centre less negative ⇒ +
    if sp:
        s_ = np.array(sp); deep = s_[np.argmax(s_[:, 1])]
        R["spine_groove"] = {"depth_cm_by_height_frac_pelvis_to_neck": [[round(float((a - pelvis) / (neck - pelvis)), 3), round(float(b), 2)] for a, b in sp],
                             "max_depth_cm": round(float(deep[1]), 2), "deepest_at_frac_pelvis_to_neck": round(float((deep[0] - pelvis) / (neck - pelvis)), 2),
                             "median_depth_cm": round(float(np.median(s_[:, 1])), 2)}
        marks_b.append(("spine", [(0, a) for a, b in sp if b > 0.3], (200, 40, 40)))
    xg = 0.075 if sex == "male" else 0.085
    yy, zb = Bm.colprof(xg, pelvis - 0.25, belly + 0.05); zb2 = np.array([np.nanmean([a, b]) for a, b in zip(zb, Bm.colprof(-xg, pelvis - 0.25, belly + 0.05)[1])])
    win = np.where((yy > pelvis - 0.20) & (yy < pelvis + 0.10) & np.isfinite(zb2))[0]
    if len(win):
        g = win[np.argmin(zb2[win])]                                     # most-back point = glute peak (back surface is −z)
        lw = np.where((yy < yy[g]) & (yy > yy[g] - 0.14) & np.isfinite(zb2))[0]; f = lw[np.argmax(zb2[lw])] if len(lw) else None
        hw = np.where((yy > yy[g]) & (yy < yy[g] + 0.25) & np.isfinite(zb2))[0]; h_ = hw[np.argmax(zb2[hw])] if len(hw) else None
        R["glutes"] = {"peak_y_from_pelvis_joint_cm": round(float((yy[g] - pelvis) * 100), 1),
                       "proud_over_fold_cm": round(float((zb2[f] - zb2[g]) * 100), 2) if f is not None else None,
                       "fold_below_peak_cm": round(float((yy[g] - yy[f]) * 100), 1) if f is not None else None,
                       "lower_back_hollow_depth_cm": round(float((zb2[h_] - zb2[g]) * 100), 2) if h_ is not None else None,
                       "lower_back_hollow_above_peak_cm": round(float((yy[h_] - yy[g]) * 100), 1) if h_ is not None else None,
                       "profile_y_z": [[round(float(a), 4), round(float(b), 4)] for a, b in zip(yy[::4], zb2[::4]) if np.isfinite(b)]}
        marks_b += [("glute peak", [(xg, yy[g]), (-xg, yy[g])], (220, 120, 30))]
        if f is not None: marks_b.append(("glute fold", [(xg, yy[f]), (-xg, yy[f])], (60, 60, 200)))
        if h_ is not None: marks_b.append(("lower back", [(xg, yy[h_]), (-xg, yy[h_])], (30, 140, 60)))
    # ---------------- limbs: radius profiles along the bones
    V = m.vertices
    SEG = {}
    for b in "LR":
        hand_tip = J[f"co_tay_{b}"] + (J[f"co_tay_{b}"] - J[f"khuyu_{b}"]) / np.linalg.norm(J[f"co_tay_{b}"] - J[f"khuyu_{b}"]) * 0.14
        SEG.update({f"ua{b}": (J[f"vai_{b}"], J[f"khuyu_{b}"]), f"fa{b}": (J[f"khuyu_{b}"], hand_tip), f"th{b}": (J[f"hong_{b}"], J[f"goi_{b}"]),
                    f"sh{b}": (J[f"goi_{b}"], J[f"co_chan_{b}"])})
    SEG["torso"] = (J["chau"], J["co"]); SEG["head"] = (J["dau"], J["dinh_dau"])
    def segd(P, a_, b_):
        ab = b_ - a_; t = np.clip(((P - a_) @ ab) / (ab @ ab), 0, 1); return np.linalg.norm(P - (a_ + t[:, None] * ab), axis=1)
    keys = list(SEG); D = np.stack([segd(V, *SEG[k]) for k in keys]); owner = np.array(keys)[np.argmin(D, axis=0)]
    def limb(a, b, ext=0.0, label="", own=None):
        A_, B_ = J[a], J[b]; d = B_ - A_; L = np.linalg.norm(d); u = d / L; Bx = B_ + u * ext
        t = (V - A_) @ u; perp = V - A_ - np.outer(t, u); r = np.linalg.norm(perp, axis=1)
        sel = (t > -0.02) & (t < L + ext + 0.02) & (r < 0.13) & (np.isin(owner, own) if own else True)
        prof = []
        for s in np.arange(0, L + ext, 0.01):
            k = sel & (np.abs(t - s) < 0.006)
            if k.sum() < 6: prof.append(None); continue
            rr = r[k]; core = rr[rr < np.percentile(rr, 50) * 2.2]
            prof.append(round(float(np.percentile(core, 90)) * 100, 2))
        return {"bone": f"{a}→{b}", "length_cm": round(float(L * 100), 1), "extended_cm": round(ext * 100, 1), "radius_cm_every_1cm": prof}
    limbs = {}
    for side in ("L",):
        limbs["upper_arm"] = limb(f"vai_{side}", f"khuyu_{side}", own=[f"ua{side}"])
        limbs["forearm_to_hand"] = limb(f"khuyu_{side}", f"co_tay_{side}", ext=0.14, own=[f"fa{side}"])
        limbs["thigh"] = limb(f"hong_{side}", f"goi_{side}", own=[f"th{side}"])
        limbs["shin"] = limb(f"goi_{side}", f"co_chan_{side}", own=[f"sh{side}"])
    fa = limbs["forearm_to_hand"]; pr = [p for p in fa["radius_cm_every_1cm"]]; Lf = int(fa["length_cm"])
    seg = [(i, p) for i, p in enumerate(pr) if p is not None]
    if seg:
        belly_ = max([x for x in seg if 3 <= x[0] < Lf * 0.5], key=lambda x: x[1], default=None)   # skip the elbow cap
        wrist = min([x for x in seg if Lf - 6 <= x[0] <= Lf + 3], key=lambda x: x[1], default=None)
        thenar = max([x for x in seg if wrist and x[0] > wrist[0]], key=lambda x: x[1], default=None)
        limbs["forearm_wrist_thumb"] = {"forearm_belly_cm_from_elbow": belly_[0] if belly_ else None, "forearm_belly_radius_cm": belly_[1] if belly_ else None,
                                        "wrist_cm_from_elbow": wrist[0] if wrist else None, "wrist_radius_cm": wrist[1] if wrist else None,
                                        "thenar_cm_from_elbow": thenar[0] if thenar else None, "hand_max_radius_cm": thenar[1] if thenar else None,
                                        "wrist_over_belly": round(wrist[1] / belly_[1], 2) if (wrist and belly_) else None,
                                        "hand_over_wrist": round(thenar[1] / wrist[1], 2) if (wrist and thenar) else None}
    for k_ in ("upper_arm", "thigh", "shin"):
        p_ = [x for x in limbs[k_]["radius_cm_every_1cm"] if x is not None]
        if p_:
            i_ = int(np.argmax(p_)); limbs[k_]["belly_at_frac"] = round(i_ / max(len(p_) - 1, 1), 2); limbs[k_]["belly_over_ends"] = round(p_[i_] / max(min(p_[0], p_[-1]), 0.1), 2)
    R["limbs"] = limbs
    # ---------------- crotch / region between the legs (Boss 25/10: «cách làm vùng giữa 2 chân của nam và nữ khác nhau - đo độ lõm»)
    # apex = where the two thighs stop being one torso (first empty cell on the body midline going down); notch = the thigh gap below it;
    # front: midline proudness (male bulge / female mons) over the groin creases on either side; back: gluteal cleft depth
    xb = float(np.median([J[f"hong_{s_}"][0] for s_ in ("L", "R")])); occ = np.isfinite(F_)
    c_mid = Fm.col(xb); r_pel = Fm.row(pelvis); apex_r = None
    for r in range(r_pel, max(r_pel - int(0.35 / CELL), 0), -1):
        if not occ[r, c_mid - 1:c_mid + 2].any(): apex_r = r + 1; break
    cr = {}
    if apex_r is not None:
        apex_y = Fm.y(apex_r); hipw = abs(J["hong_L"][0] - J["hong_R"][0])
        def gap(y):                                                       # empty run through the midline at height y (front map)
            r = Fm.row(y); row = occ[r]; c0 = c1 = c_mid
            if row[c_mid]: return 0.0
            while c0 > 0 and not row[c0 - 1]: c0 -= 1
            while c1 < len(row) - 1 and not row[c1 + 1]: c1 += 1
            return (c1 - c0 + 1) * CELL
        notch = {f"{d}cm": round(gap(apex_y - d / 100) * 100, 1) for d in (1, 2, 4, 6, 10, 20)}
        # front: per row from the apex up to pelvis + 12 cm, midline z vs the deepest point between the midline and the thigh/hip front
        rows = []
        for y in np.arange(apex_y + 0.005, pelvis + 0.12, CELL * 2):
            zc = Fm.z(xb, y, 2); xs_ = np.arange(0.01, 0.13, CELL); best = None
            for sgn in (-1, 1):
                zz = np.array([Fm.z(xb + sgn * x, y, 1) for x in xs_])
                if not np.isfinite(zz).any(): continue
                pk = int(np.nanargmax(zz)); lo = int(np.nanargmin(zz[:pk + 1])) if pk > 0 else 0
                crease = float(min(zc, zz[pk]) - zz[lo]) if pk > lo else 0.0
                best = (crease, xs_[lo], zc - zz[pk]) if best is None or crease > best[0] else best
            if best: rows.append((y, zc, *best))
        if rows:
            Rw = np.array(rows); i_b = int(np.argmax(Rw[:, 4])); i_c = int(np.argmax(Rw[:, 2]))
            cr["front"] = {"midline_proud_over_thigh_front_cm_max": round(float(Rw[i_b, 4] * 100), 2), "at_cm_above_apex": round(float((Rw[i_b, 0] - apex_y) * 100), 1),
                           "groin_crease_depth_cm_max": round(float(Rw[i_c, 2] * 100), 2), "crease_at_cm_above_apex": round(float((Rw[i_c, 0] - apex_y) * 100), 1),
                           "crease_cm_from_midline": round(float(Rw[i_c, 3] * 100), 1),
                           "profile_every_1cm": [[round(float((y - apex_y) * 100), 1), round(float(pr * 100), 2), round(float(c * 100), 2)] for y, _, c, _, pr in Rw[::2]]}
            marks_f.append(("crease", [(xb + sg * x, y) for y, _, _, x, _ in Rw for sg in (-1, 1)], (40, 120, 200)))
        # back: gluteal cleft = midline vs the glute peaks either side, from the apex up to 15 cm
        cl = []
        for y in np.arange(apex_y + 0.005, apex_y + 0.15, CELL * 2):
            zc = Bm.z(xb, y, 1); side = [np.nanmin([Bm.z(xb + sg * x, y, 1) for x in np.arange(0.03, 0.12, CELL)]) for sg in (-1, 1)]
            if np.isfinite(zc) and np.isfinite(side).all(): cl.append((y, zc - max(side)))
        if cl:
            C_ = np.array(cl); i_ = int(np.argmax(C_[:, 1]))
            cr["back"] = {"gluteal_cleft_depth_cm_max": round(float(C_[i_, 1] * 100), 2), "at_cm_above_apex": round(float((C_[i_, 0] - apex_y) * 100), 1),
                          "cleft_closes_cm_above_apex": round(float((C_[C_[:, 1] > 0.005, 0].max() - apex_y) * 100), 1) if (C_[:, 1] > 0.005).any() else None}
        cr.update({"apex_below_pelvis_joint_cm": round(float((pelvis - apex_y) * 100), 1), "apex_frac_of_height": round(float(apex_y / J["dinh_dau"][1]), 3),
                   "hip_joint_spacing_cm": round(float(hipw * 100), 1), "thigh_gap_width_below_apex": notch})
        marks_f.append(("apex", [(xb, apex_y)], (200, 40, 160)))
    R["crotch"] = cr
    json.dump(R, open(out + "_anatomy.json", "w"), indent=1)
    # ---------------- pictures
    def shade(A, front=True):
        g = np.nan_to_num(A, nan=np.nanmin(A) if front else np.nanmax(A)); gy, gx = np.gradient(g, CELL); n = np.dstack([-gx, -gy, np.ones_like(g) * (1 if front else -1)])
        n /= np.linalg.norm(n, axis=2, keepdims=True); L = np.array([-0.4, 0.5, 0.75 if front else -0.75]); L /= np.linalg.norm(L)
        v = np.clip(n @ L, 0, 1) * 0.75 + 0.25; img = np.dstack([v * 235, v * 195, v * 165]).astype(np.uint8); img[~np.isfinite(A)] = 255
        return Image.fromarray(img[::-1])
    for name, A, Mp, marks, front in (("front", F_, Fm, marks_f, True), ("back", B_, Bm, marks_b, False)):
        im = shade(A, front); d = ImageDraw.Draw(im); Hpx = A.shape[0]
        for lab, pts, col in marks:
            P = [(Mp.col(x), Hpx - 1 - Mp.row(y)) for x, y in pts]
            for px, py in P: d.ellipse((px - 2, py - 2, px + 2, py + 2), fill=col)
            if P: d.text((P[0][0] + 4, P[0][1] - 10), lab, fill=col)
        im = im.resize((im.width * 2, im.height * 2)); im.save(out + f"_{name}.png")
    W, Hh = 900, 260; im = Image.new("RGB", (W, Hh * 4), (255, 255, 255)); d = ImageDraw.Draw(im)
    for k_i, k_ in enumerate(("upper_arm", "forearm_to_hand", "thigh", "shin")):
        p_ = limbs[k_]["radius_cm_every_1cm"]; oy = k_i * Hh; d.text((10, oy + 5), f"{k_} radius (cm) along {limbs[k_]['bone']}", fill=(0, 0, 0))
        mx = max([x for x in p_ if x] + [1])
        pts = [(40 + i * (W - 60) / max(len(p_), 1), oy + Hh - 20 - (x / mx) * (Hh - 50)) for i, x in enumerate(p_) if x]
        if len(pts) > 1: d.line(pts, fill=(180, 80, 40), width=3)
    im.save(out + "_limbs.png")
    print(json.dumps({k: (v if k != "limbs" else {kk: {x: y for x, y in vv.items() if x != "radius_cm_every_1cm"} for kk, vv in v.items()}) for k, v in R.items()
                      if k not in ()}, default=str)[:3000])


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--body", required=True); ap.add_argument("--joints", required=True); ap.add_argument("--sex", required=True); ap.add_argument("--out", required=True)
    a = ap.parse_args(); main(a.body, a.joints, a.sex, a.out)

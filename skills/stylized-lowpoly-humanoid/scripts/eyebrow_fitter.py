"""Eyebrow Fitter — landmark fitting + raycast onto the head mesh + offset along the surface normal (Codex review 25/10/2026, forwarded by
Boss after «Lông mày nam đang bị để ở chỗ lõm mắt · Lông mày nữ cũng chưa dán đúng chỗ lồi nhất của T shape»).

  python3 eyebrow_fitter.py --body <body.glb> --anatomy <name>_anatomy.json --sex male|female --out <brows.glb> [--with-body <body+brows.glb>]
      [--width M] [--angle DEG] [--curve M] [--thickness K] [--surface-offset M]
  ⇒ <brows.glb> · <brows>.report.json (per control point: surface hit, normal, gap, ridge deviation; gates)

1. Landmarks from analyze_anatomy.py face_T_zone: FACE midline (not x = 0 — the male face sits −1.2 cm off the body axis), nose-bridge half
   width at the socket rows, eye-socket row.
2. 7 control points per brow (head, inner body, inner peak, peak, outer peak, outer body, tail). At each one the brow ridge is re-measured with
   front→back rays (socket rim = first row within 1 mm of the peak above the socket); a robust line through them (tilt ≤ 15°) + CURVE arch.
3. Every cross-section point (lower edge, upper edge) is RAYCAST onto the head and pushed out along the SURFACE NORMAL — so the brow follows the
   brow bone round to the temple instead of sinking into the forehead or floating off the skin in the 3/4 and side views.
4. Left brow built, right brow = exact mirror about the face midline. Male: hairy bar + flat spikes in the tangent plane; female: slim arch.
5. Gates (exit 1): ridge (brow centre within 0.8 cm of the most-proud row), skin contact (base ≤ 1.5 mm from the surface), no front vertex
   inside the head, symmetry ≤ 0.3 cm.
"""
import argparse, json, os, sys
import numpy as np
import trimesh

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from analyze_outfit import ray_hits

# male spikes 0: Boss 25/10 «lông mày ko cần sợi nhỏ lòi ra ngoài nữa» (the irregular-hair rule stays for any style that has spikes)
STYLE = {"male": {"width": 0.064, "h_in": 0.026, "h_out": 0.014, "p_in": 0.013, "p_out": 0.008, "frown": 0.005, "curve": 0.003,
                  "spikes": 0, "spike_len": (0.012, 0.020), "spike_w": 0.009, "spike_up_deg": 28},
         # female: shorter, broader, tilted DOWN toward the middle (Boss 25/10: «cho chân mày ngắn lại bản to hơn và độ nghiêng hướng vào
         # giữa từ trên xuống hơn tí - hiện tại nhìn hơi buồn»; the old 5.6 cm × 1.3→0.6 cm brow with its outer end 2.5° low read sad)
         "female": {"width": 0.044, "h_in": 0.019, "h_out": 0.011, "p_in": 0.008, "p_out": 0.005, "frown": 0.002, "curve": 0.003,
                    "spikes": 0, "spike_len": (0, 0), "spike_w": 0, "spike_up_deg": 0, "tilt_deg": 12.0}}   # tilt 12°: 8° still read flat on the face
N_SECTIONS = 13      # strip cross-sections (each raycast); 13 keeps the chord gap < 1 mm on both teachers
U_CTRL = np.array([0.0, 0.15, 0.32, 0.5, 0.66, 0.83, 1.0])     # head · inner body · inner peak · peak · outer peak · outer body · tail
MAX_TILT = 15
RIDGE_TOL = 0.006     # m — the brow's LOWER edge within 6 mm of the ridge (socket rim)
BOTTOM_BELOW = 0.003  # m — lower edge 3 mm under the rim so no skin line shows between brow and ridge
SOCKET_FRAC = 0.4     # a brow vertex may come down at most 40 % of the way from the rim to the eye centre — below that it covers the socket
SOCKET_TOL = 0.0      # m — any vertex under that floor fails
RIDGE_FLAT = 0.001    # m — rows within 1 mm of the band peak = ridge plateau (same rule as analyze_anatomy.py)
CONTACT_TOL = 0.0015  # m — brow base must touch the skin
INSET = 0.001         # m — base sinks 1 mm under the skin so no light leaks between brow and face


class Head:
    """head-only triangles + front→back raycasts returning the hit point and the face normal (rtree-free)."""
    def __init__(s, body, y_lo):
        keep = body.triangles_center[:, 1] > y_lo; s.T = body.triangles[keep]; s.N = body.face_normals[keep]; s.zmax = s.T[:, :, 2].max() + 0.05

    def cast(s, X, Y):
        O = np.c_[X, Y, np.full(len(X), s.zmax)]; D = np.tile([0.0, 0.0, -1.0], (len(X), 1)); hits = ray_hits(s.T, O, D)
        P = np.full((len(X), 3), np.nan); N = np.full((len(X), 3), np.nan)
        for i, h in enumerate(hits):
            if len(h):
                t = h[0]; tri = s.T[t]; e1, e2 = tri[1] - tri[0], tri[2] - tri[0]
                # exact hit: solve the plane of the first triangle along the ray
                n = np.cross(e1, e2); d = (n @ (tri[0] - O[i])) / (n @ D[i]); P[i] = O[i] + d * D[i]; N[i] = s.N[t]
        return P, N

    def smooth_normal(s, x, y, r=0.005):
        """average normal of a small ring of rays — one triangle's normal is too faceted on a low-poly head."""
        a = np.linspace(0, 2 * np.pi, 8, endpoint=False); X = np.r_[x, x + r * np.cos(a)]; Y = np.r_[y, y + r * np.sin(a)]
        _, N = s.cast(X, Y); N = N[np.isfinite(N).all(axis=1)]; n = N.mean(axis=0); return n / np.linalg.norm(n)

    def inside(s, Pts):
        """parity test with +z rays: an odd number of head crossings in front of the point ⇒ the point is inside the head."""
        hits = ray_hits(s.T, Pts, np.tile([0.0, 0.0, 1.0], (len(Pts), 1))); return np.array([len(h) % 2 == 1 for h in hits])


def ridge_y(head, X, y_lo, y_hi):
    """rim height at column X = median of three columns 4 mm apart: on the low-poly game face one column can land on a facet edge and
    read 1.5 cm off (female right outer brow, 25/10)."""
    r = np.array([ridge_y_column(head, X + d, y_lo, y_hi) for d in (-0.004, 0.0, 0.004)])
    return float(np.nanmedian(r)) if np.isfinite(r).any() else np.nan


def ridge_y_column(head, X, y_lo, y_hi):
    ys = np.arange(y_lo, y_hi, 0.0025); P, _ = head.cast(np.full(len(ys), X), ys); z = P[:, 2]
    if not np.isfinite(z).any(): return np.nan
    zf = np.where(np.isfinite(z), z, -9); return float(ys[int(np.argmax(zf >= np.nanmax(z) - RIDGE_FLAT))])


def main(a):
    body = trimesh.load(a.body, force="mesh"); body = trimesh.Trimesh(body.vertices, body.faces, process=True)
    T = json.load(open(a.anatomy))["face_T_zone"]; st = dict(STYLE[a.sex])
    for k, v in (("width", a.width), ("curve", a.curve)):
        if v is not None: st[k] = v
    th = a.thickness if a.thickness is not None else 1.0; off = a.surface_offset if a.surface_offset is not None else 0.0
    xm = T["midline_x_cm"] / 100; bridge = T["bridge_half_width_cm"] / 100; eye_y = T["eye_y_abs"]
    head = Head(body, eye_y - 0.06); y_lo, y_hi = eye_y + 0.004, eye_y + 0.07
    x_in = bridge + 0.001; xs = x_in + U_CTRL * st["width"]
    # 2. ridge at every control point (left side; right is the mirror) → robust line + arch
    ry = np.array([ridge_y(head, xm + x, y_lo, y_hi) for x in xs]); ok = np.isfinite(ry)
    ry_r = np.array([ridge_y(head, xm - x, y_lo, y_hi) for x in xs]); ry = np.where(ok & np.isfinite(ry_r), (ry + ry_r) / 2, ry)  # both sides vote
    # rim points on the side-facing temple are not a rim (female tail read 2 cm high on the low-poly game body): fit the line without them
    fwd = np.array([abs(head.smooth_normal(xm + x, r_)[2]) >= 0.5 if np.isfinite(r_) else False for x, r_ in zip(xs, ry)])
    ok = ok & fwd
    inner, outer = float(np.median(ry[:3][ok[:3]])), float(np.median(ry[3:][ok[3:]]))
    slope = (outer - inner) / max(xs[4] - xs[1], 0.01)
    if a.angle is not None: slope = np.tan(np.radians(a.angle))
    slope = float(np.clip(slope, -np.tan(np.radians(MAX_TILT)), np.tan(np.radians(MAX_TILT))))
    # the brow's LOWER EDGE sits on the ridge (socket rim) — Boss 25/10 (3rd time): «cho lông mày xích lên một chút vì có một nhánh nhỏ lông
    # mày che ngay hốc mắt». Centring the bar on the ridge hung its lower half (≈ 1.3 cm on the male) and the frown-lowered inner head over the
    # socket. The frown now only lowers the TOP edge of the inner head.
    yb_ctrl = inner + slope * (xs - xs[1]) + st["curve"] * 4 * U_CTRL * (1 - U_CTRL) - BOTTOM_BELOW
    if "tilt_deg" in st and a.angle is None:                               # style tilt, pivoting on the brow's middle so the edge stays on the rim
        mid_x = xs[len(xs) // 2]; mid_y = float(np.interp(mid_x, xs, yb_ctrl)); slope = float(np.tan(np.radians(st["tilt_deg"])))
        yb_ctrl = mid_y + slope * (xs - mid_x)                             # straight tilted edge: an arch on top of the tilt read sad again
    # the 7 control points set the SHAPE (left/right ridge votes averaged ⇒ one shape, cast on each side); the strip is resampled into N_SECTIONS cross-sections, each raycast — straight chords between
    # 7 points cut 1.6–2 mm off the curved brow bone (measured 25/10)
    U = np.linspace(0, 1, N_SECTIONS); xs_c = xs; xs = x_in + U * st["width"]; yb = np.interp(U, U_CTRL, yb_ctrl)
    yb = yb - float(os.environ.get("THU_BROW_DROP", "0"))              # reverse-test only: push the brow down toward the socket
    h = (st["h_in"] * (1 - U) + st["h_out"] * U) * th; p = (st["p_in"] * (1 - U) + st["p_out"] * U) * th
    yt = yb + h - st["frown"] * (1 - U); yc = (yb + yt) / 2; h = yt - yb
    # 3. raycast both edges of every cross-section, push out along the smoothed surface normal. EACH side is cast on its own half of the
    # face with the same shape — a geometric mirror sank the female right brow into the skin (the generated face is not symmetric)
    n = len(xs)

    spike_log = []

    def build_side(sgn):
        X = xm + sgn * xs
        Pb, _ = head.cast(X, yc - h / 2); Pt, _ = head.cast(X, yc + h / 2)
        Nb = np.array([head.smooth_normal(x, y) for x, y in zip(X, yc - h / 2)]); Nt = np.array([head.smooth_normal(x, y) for x, y in zip(X, yc + h / 2)])
        if not (np.isfinite(Pb).all() and np.isfinite(Pt).all()): print("⛔ a cross-section missed the head (raycast)"); sys.exit(1)
        # the lower edge goes straight OUT, never down: the brow-ridge normal tilts ≈ 0.4 downward, so offsetting the 13 mm wedge along it
        # dropped the lower front edge ≈ 5 mm into the socket — the «nhánh nhỏ lông mày che ngay hốc mắt» Boss saw (25/10)
        Nbo = Nb.copy(); Nbo[:, 1] = np.maximum(Nbo[:, 1], 0.0); Nbo /= np.linalg.norm(Nbo, axis=1, keepdims=True)
        V = []
        for i in range(n):                                               # wedge: base under the skin, lower front proud, upper front less
            V += [Pb[i] + Nb[i] * (off - INSET), Pb[i] + Nbo[i] * (off + p[i]), Pt[i] + Nt[i] * (off + 0.6 * p[i]), Pt[i] + Nt[i] * (off - INSET)]
        F = []
        for i in range(n - 1):
            for k in range(4):
                a_, b_ = i * 4 + k, i * 4 + (k + 1) % 4; F += [(a_, b_, b_ + 4), (a_, b_ + 4, a_ + 4)]
        F += [(0, 2, 1), (0, 3, 2)]; o = (n - 1) * 4; F += [(o, o + 1, o + 2), (o, o + 2, o + 3)]
        # male hair: flat spikes on the top edge, in the TANGENT plane (up + out toward the temple), lifted along the normal
        # IRREGULAR hairs (Boss 25/10: «lông mày mấy sợi nhô ra hơi đều»): seeded per side — position jittered ±45 % of the spacing,
        # length 0.5–1.6×, angle ±20°, width 0.7–1.3×; THU_BROW_EVEN=1 restores the old even comb (reverse test only)
        even = bool(os.environ.get("THU_BROW_EVEN")); rng = np.random.default_rng(7 if sgn > 0 else 11); ns = st["spikes"]
        pos = (np.arange(ns) + 0.5 + (0 if even else rng.uniform(-0.45, 0.45, ns))) / ns
        lmul = np.ones(ns) if even else rng.uniform(0.5, 1.6, ns); amul = np.zeros(ns) if even else rng.uniform(-20, 20, ns)
        wmul = np.ones(ns) if even else rng.uniform(0.7, 1.3, ns)
        for j in range(ns):
            i = min(n - 2, max(0, int(np.clip(pos[j], 0, 1) * (n - 1)))); u = U[i]
            top = Pt[i] + Nt[i] * (off + 0.3 * p[i]); Nn = Nt[i]
            Tg = Pt[min(i + 1, n - 1)] - Pt[max(i - 1, 0)]; Tg -= Nn * (Tg @ Nn); Tg /= np.linalg.norm(Tg)
            Up = np.array([0.0, 1.0, 0.0]); Up -= Nn * (Up @ Nn) + Tg * (Up @ Tg); Up /= np.linalg.norm(Up)
            L = (st["spike_len"][0] + (st["spike_len"][1] - st["spike_len"][0]) * (0.5 if even else 0.5 + 0.5 * np.sin(j * 2.3))) * th * lmul[j]
            ang = np.radians(st["spike_up_deg"] + 12 * (1 - u) + amul[j]); w = st["spike_w"] * (1 - 0.4 * u) * th * wmul[j]
            spike_log.append((sgn, float(pos[j]), float(L), float(np.degrees(ang))))
            tip = top + Tg * L * np.cos(ang) + Up * L * np.sin(ang) * 0.6 + Nn * 0.002
            b0 = top - Tg * w / 2 - Up * 0.004; b1 = top + Tg * w / 2 - Up * 0.004; bk = top - Up * 0.004 - Nn * 0.006
            i0 = len(V); V += [b0, b1, tip, bk]; F += [(i0, i0 + 1, i0 + 2), (i0 + 1, i0 + 3, i0 + 2), (i0 + 3, i0, i0 + 2)]
        m_ = trimesh.Trimesh(np.array(V), np.array(F), process=False); m_.fix_normals()
        return m_, np.array(V[: 4 * n]).reshape(n, 4, 3), Nb, Nt

    sides = {sgn: build_side(sgn) for sgn in (1, -1)}
    brows = trimesh.util.concatenate([sides[1][0], sides[-1][0]])
    sys.path.insert(0, os.path.expanduser("~/projects/lpm-faceless-humanoid/theme")); import theme_colors as TC
    brows.visual = trimesh.visual.TextureVisuals(material=trimesh.visual.material.PBRMaterial(name="M_hair", baseColorFactor=TC.mau((58, 40, 28)), roughnessFactor=0.85, metallicFactor=0.0))
    sc = trimesh.Scene(); sc.add_geometry(brows, geom_name="eyebrows", node_name="eyebrows"); sc.export(a.out)
    if a.with_body:
        b2 = body.copy(); b2.visual = trimesh.visual.TextureVisuals(material=trimesh.visual.material.PBRMaterial(name="M_skin", baseColorFactor=TC.mau(TC.DA["dat_am"]), roughnessFactor=0.5, metallicFactor=0.0))
        sc2 = trimesh.Scene(); sc2.add_geometry(b2, geom_name="body", node_name="body"); sc2.add_geometry(brows, geom_name="eyebrows", node_name="eyebrows"); sc2.export(a.with_body)
    # 5. report + gates — every number re-measured on the mesh, not taken from the fit
    yc_c = np.interp(U_CTRL, U, yc); h_c = np.interp(U_CTRL, U, h); yb_c = np.interp(U_CTRL, U, yb)
    ridge_now = np.array([[ridge_y(head, xm + sg * x, y_lo, y_hi) for x in xs_c] for sg in (1, -1)])   # [side, control point]
    ridge_dev = (yb_c[None] - ridge_now) * 100                           # LOWER edge vs the rim
    # socket gate: no brow vertex (bar + spikes) may come down more than 40 % of the way from the rim (median of the forward-facing rim
    # points, both sides) to the eye centre. A per-column rim on the low-poly game face read 13 mm "below" a brow that sat on the ridge.
    Nc = np.array([[head.smooth_normal(xm + sg * x, y) for x, y in zip(xs_c, yb_c)] for sg in (1, -1)])
    rim_ok = np.isfinite(ridge_now) & (np.abs(Nc[:, :, 2]) >= 0.5) & (np.arange(len(U_CTRL)) > 0)[None]
    rim_med = float(np.median(ridge_now[rim_ok])) if rim_ok.any() else float(np.nanmedian(ridge_now))
    floor_y = rim_med - SOCKET_FRAC * (rim_med - T["eye_y_abs"])
    socket_drop = max(0.0, floor_y - float(brows.vertices[:, 1].min()))

    def along_normal(Pts, Ns):
        O_ = Pts + Ns * 0.02; out = []
        for hh, o_, d_ in zip(ray_hits(head.T, O_, -Ns), O_, Ns):
            if not len(hh): out.append(np.nan); continue
            tri = head.T[hh[0]]; nn = np.cross(tri[1] - tri[0], tri[2] - tri[0]); out.append((nn @ (tri[0] - o_)) / (nn @ -d_) - 0.02)
        return np.array(out)
    # skin gap measured BETWEEN the cross-sections (at the vertices it is zero by construction): 4 samples on every base edge segment,
    # distance to the skin along the local normal (start 2 cm out, cast back along −N — a front ray is meaningless on the side-facing temple)
    tt = np.linspace(0, 1, 6)[1:-1]; gaps, buried = [], 0
    for sg in (1, -1):
        _, base, Nb, Nt = sides[sg]
        Bs = np.concatenate([base[i, k] * (1 - t) + base[i + 1, k] * t for k in (0, 3) for i in range(n - 1) for t in tt]).reshape(-1, 3)
        Ns_ = np.concatenate([(N_[i] * (1 - t) + N_[i + 1] * t) for N_ in (Nb, Nt) for i in range(n - 1) for t in tt]).reshape(-1, 3)
        Ns_ /= np.linalg.norm(Ns_, axis=1, keepdims=True)
        gaps.append(along_normal(Bs, Ns_) + INSET)                     # > 0: base floats off the skin · < 0: sinks deeper than INSET
        Fr = np.concatenate([base[i, k] * (1 - t) + base[i + 1, k] * t for k in (1, 2) for i in range(n - 1) for t in np.linspace(0, 1, 6)]).reshape(-1, 3)
        buried += int(head.inside(Fr).sum())                            # front edges incl. points between the sections
    gap = np.concatenate(gaps)
    Lv = brows.vertices[brows.vertices[:, 0] > xm]; Rv = brows.vertices[brows.vertices[:, 0] < xm]
    asym = abs((Lv[:, 0].mean() - xm) - (xm - Rv[:, 0].mean())) * 100
    ctrl = [{"name": nm, "x_from_midline_cm": round(float(x * 100), 2), "centre_y": round(float(y), 4), "ridge_y": round(float(r), 4) if np.isfinite(r) else None,
             "ridge_dev_cm": round(float(d), 2) if np.isfinite(d) else None, "normal_lower": [round(float(c), 3) for c in nb], "height_cm": round(float(hh * 100), 2)}
            for nm, x, y, r, d, nb, hh in zip(("head", "inner_body", "inner_peak", "peak", "outer_peak", "outer_body", "tail"), xs_c, yc_c, ridge_now[0], ridge_dev[0], Nc[0], h_c)]
    # ridge is judged where the face looks FORWARD (|n_z| ≥ 0.5): on the side-facing temple a front ray has no "most proud row" (female tail
    # read a plateau 2.5 cm higher); the head point is pulled down by the frown on purpose
    judged = (np.abs(Nc[:, :, 2]) >= 0.5) & (np.arange(len(U_CTRL)) > 0)[None] & np.isfinite(ridge_dev)   # the head sits beside the nose bridge: no rim there
    # a rim read more than 1.5 cm off the median of both sides is a misread (low-poly game face: the female right tail read 2 cm high)
    judged &= np.abs(ridge_now - np.nanmedian(ridge_now[judged])) < 0.015 if judged.any() else judged
    # a style tilt (pivot at the middle) lifts / lowers the ends ON PURPOSE: subtract that designed offset before judging the placement
    if "tilt_deg" in st and a.angle is None:                               # the tilted ends leave the rim ON PURPOSE (Boss's tilt): the ridge gate
        judged &= np.isin(np.arange(len(U_CTRL)), [2, 3, 4])[None]           # judges the pivot (inner peak → outer peak); the socket gate still
        #                                                                     guards how low the lowered inner end may go
    worst = float(np.max(np.abs(ridge_dev[judged]))) if judged.any() else 99
    if os.environ.get("DEBUG_BROW"): print("ridge", np.round(ridge_now, 4).tolist(), "\nlower", np.round(yb_c, 4).tolist(), "\nnz", np.round(Nc[:, :, 2], 2).tolist(), "\njudged", judged.astype(int).tolist())
    rep = {"sex": a.sex, "tris": int(len(brows.faces)), "midline_x_cm": round(xm * 100, 2), "bridge_gap_cm": round(2 * x_in * 100, 2),
           "tilt_deg": round(float(np.degrees(np.arctan(slope))), 1), "params": {"width": st["width"], "angle_deg": a.angle, "curve": st["curve"], "thickness": th, "surface_offset": off},
           "control_points": ctrl, "ridge_dev_worst_cm": round(worst, 2), "below_socket_rim_mm": round(socket_drop * 1000, 1), "ridge_judged_points": int(judged.sum()), "skin_gap_worst_mm": round(float(np.nanmax(np.abs(gap)) * 1000), 2), "skin_gap_samples": int(len(gap)),
           "front_vertices_inside_head": buried, "asymmetry_cm": round(float(asym), 3)}
    json.dump(rep, open(os.path.splitext(a.out)[0] + ".report.json", "w"), indent=1)
    print(f"  lower edge vs socket rim worst {worst:.2f} cm · rim {rim_med:.4f} · eye {T['eye_y_abs']:.4f} · lowest brow {brows.vertices[:, 1].min():.4f} (floor {floor_y:.4f})")
    print(f"eyebrows ({a.sex}): {rep['tris']} tris · midline {rep['midline_x_cm']} cm · bridge gap {rep['bridge_gap_cm']} cm · tilt {rep['tilt_deg']}° · "
          f"ridge dev worst {worst:.2f} cm · skin gap worst {rep['skin_gap_worst_mm']} mm · buried {buried} · asym {asym:.2f} cm → {a.out}")
    fail = []
    if worst > RIDGE_TOL * 100: fail.append("brow is not on the brow ridge (most proud row above the eye socket)")
    if socket_drop > SOCKET_TOL: fail.append(f"brow reaches {socket_drop*1000:.0f} mm below the socket floor line (40 % rim→eye) — it covers the eye socket")
    if np.nanmax(np.abs(gap)) > CONTACT_TOL or np.isnan(gap).mean() > 0.1: fail.append("brow base floats off / sinks into the skin")
    if buried: fail.append(f"{buried} brow front vertices are inside the head")
    if asym > 0.3: fail.append("brows not symmetric about the face midline")
    if st["spikes"] >= 3:                                                   # irregularity of the hairs, per side
        for sg in (1, -1):
            rows = sorted([r_ for r_ in spike_log if r_[0] == sg], key=lambda r_: r_[1])
            Ls = np.array([r_[2] for r_ in rows]); gaps = np.diff([r_[1] for r_ in rows]); angs = np.array([r_[3] for r_ in rows])
            cv_l, cv_g, sd_a = Ls.std() / Ls.mean(), gaps.std() / max(gaps.mean(), 1e-9), angs.std()
            print(f"  hairs side {'L' if sg > 0 else 'R'}: length CV {cv_l:.2f} · spacing CV {cv_g:.2f} · angle sd {sd_a:.1f}° (≥ 2 of: 0.25 / 0.25 / 8°)")
            if int(cv_l >= 0.25) + int(cv_g >= 0.25) + int(sd_a >= 8) < 2: fail.append("brow hairs stick out too evenly (length / spacing / angle all alike)")
    for f_ in fail: print("⛔", f_)
    if fail: sys.exit(1)


def cli(argv=None):
    ap = argparse.ArgumentParser()
    for k in ("--body", "--anatomy", "--sex", "--out"): ap.add_argument(k, required=True)
    ap.add_argument("--with-body")
    for k in ("--width", "--angle", "--curve", "--thickness", "--surface-offset"): ap.add_argument(k, type=float)
    main(ap.parse_args(argv))


if __name__ == "__main__":
    cli()

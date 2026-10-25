"""Build a torn leather BANDEAU top straight on the torso (Boss 25/10/2026: «The female outfit supose to be underarm not overarm» →
«Nữ áo chưa ôm vào nách»). The Hunyuan top was a shoulder cape (its height had to be squashed 0.395× to fit the slot); this one is cut
from the body itself, so it sits UNDER the arms by construction.

  python3 build_bandeau.py --body <base_lp.glb> --joints <joints.json> --anatomy <anatomy.json> --out <top.glb>

Rows: from the under-bust fold to as far above the bust peak as the fold is below it (same landmarks as character-fitter). At each row the
ARM-LESS torso cross-section (convex hull: the band bridges between the breasts) gives the radius per angle; inner sheet = hull +
clearance, outer = + leather thickness. Bottom edge torn into teeth, top rim a light trim — numbers from SPEC_primal_torn_layered_outfit
(female_top: 6 teeth, depth 1.9–2.4 cm; trim on the upper rim; ≤ 450 tris).
"""
import argparse, json, os, sys
import numpy as np
import trimesh
from scipy.spatial import ConvexHull

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "character-fitter", "scripts"))
from fit_engine import Body

SPEC = json.load(open(os.path.join(HERE, "..", "spec", "SPEC_primal_torn_layered_outfit.json")))["garments"]["female_top"]
ANGLES, ROWS = 20, 4      # a row ON the bust peak (3 rows 6.5 cm apart let the bust bulge through the chord between rows, 25/10); 400 ≤ 450 tris
CLEARANCE, THICK = 0.003, 0.006   # 3 mm: sharp body vertices are now contained explicitly (5 mm was only a workaround)
# the top trim is a lumpy ROPE like the skirt's rope belt (Boss 25/10: «Cái chỗ tà vàng trên của áo nữ cho giống shape của belt đi như vậy
# tự nhiên hơn») instead of a flat tan band: 12 stations × 5-sided twisted tube, radius 11–16 mm (8–12 read as a thin line), wobble ±3 mm
ROPE_TRIM = True          # the top trim exists (now a flat binding, below)
# FLAT BINDING (Codex audit 25/10, spec/audits/codex_audit_female_bandeau_armpit.md; Boss: «Phần nách vẫn còn chỗ nhọn, nhọn của dây belt -
# hay là làm thành dây dẹp vẫn giữ texture xoắn đó?»): the round twisted 4-sided rope entered the upper arm as a tapered tan tip. Now a
# rectangular strap 16 mm tall × 3 mm thick lying ON the leather (inner face 0.5 mm off its outer surface, top 2 mm above the leather's
# top edge), sharing the leather's 20 stations, with a zig-zag ridge (±3 mm, 1.5 mm proud) that keeps the twisted-rope facets
# without changing the outline; the ridge fades to flat over the two spans before the strap goes behind the arm.
STRAP_H_UP, STRAP_H_DN, STRAP_T, STRAP_GAP = 0.002, 0.014, 0.003, 0.0005
RIDGE_ZIG, RIDGE_OUT = 0.003, 0.0015
# 20 stations, denser under the arms (65–125° each side) where the strap disappears behind the arm
STATIONS_DEG = [0, 21.7, 43.3, 65, 80, 95, 110, 125, 143.3, 161.7, 180, 198.3, 216.7, 235, 250, 265, 280, 295, 316.7, 338.3]
# OFF since the torso keeps its shoulder blades (fit_engine, 25/10): widening by skin within 2.5 cm picked up ARM skin at the armpit
# and pushed single angles out 2–3.4 cm — the «vật nhọn lòi ra nách» Boss saw
WIDEN_NEAR_SKIN = False
POINT_MAX = 5.0       # mm: longest narrow spur at the armpit (measure_armpit_point.py)
TOP_HUG_MAX = 0.013   # m: top row outer sheet = skin + clearance 3 + thickness 6 (+4 slack)
SPIKE_MAX = 0.012   # m: a row's radius may exceed the mean of its two neighbour angles by at most this (gate)


def section_radius(body, y, ang, c):
    """radius of the arm-less torso's REAL (non-convex) cross-section at height y along each angle from c: where the skin actually is. The
    convex hull bridges the armpit hollow and the spine groove 2–3 cm off the skin; a rope laid on the hull stood out there."""
    seg = trimesh.intersections.mesh_plane(body._torso_mesh(), [0, 1, 0], [0, y, 0]); out = []
    for a in ang:
        d = np.array([np.sin(a), np.cos(a)]); best = 0.0
        for p, q in seg[:, :, [0, 2]]:
            e = q - p; M = np.array([d, -e]).T
            if abs(np.linalg.det(M)) < 1e-12: continue
            t, u = np.linalg.solve(M, p - c)
            if t > 0 and 0 <= u <= 1: best = max(best, t)
        out.append(best)
    return np.array(out)


def hull_radius(body, y, ang):
    """radius of the arm-less torso's convex cross-section at height y along each angle, from the section's centroid — widened by any
    FULL-body skin within 2.5 cm outside that hull in the same angular bin: at the armpit the arm–back junction bulges past the arm-less
    hull and poked through the band (Boss 25/10: «nách trái phía sau - áo bị lộ da»)."""
    seg = trimesh.intersections.mesh_plane(body._torso_mesh(), [0, 1, 0], [0, y, 0])
    P = seg.reshape(-1, 3)[:, [0, 2]]; H = P[ConvexHull(P).vertices]; c = H.mean(axis=0); r = []
    full = trimesh.intersections.mesh_plane(body.mesh, [0, 1, 0], [0, y, 0]).reshape(-1, 3)[:, [0, 2]] - c
    fa = np.arctan2(full[:, 0], full[:, 1]); fr = np.linalg.norm(full, axis=1); half = np.pi / len(ang)
    for a in ang:
        d = np.array([np.sin(a), np.cos(a)]); best = 0.0                 # angle 0 = +Z (front)
        for p, q in zip(H, np.roll(H, -1, axis=0)):
            e = q - p; M = np.array([d, -e]).T
            if abs(np.linalg.det(M)) < 1e-12: continue
            t, u = np.linalg.solve(M, p - c)
            if t > 0 and 0 <= u <= 1: best = max(best, t)
        if WIDEN_NEAR_SKIN:
            near = (np.abs((fa - a + np.pi) % (2 * np.pi) - np.pi) <= half) & (fr <= best + 0.025)
            if near.any(): best = max(best, float(fr[near].max()))
        r.append(best)
    r = np.array(r)
    if os.environ.get("THU_HULL_BRIDGE") != "1":                        # reverse test: =1 keeps the hull bridge at the sides
        # the band bridges the cleavage (between the two breast apexes) but HUGS the skin from each apex round to the back: the hull
        # bridged breast → armpit 1.4–2.4 cm off the skin (Boss 25/10: «vệt tà áo trên đang nhô ra bất bình thường nó phải ôm vào
        # ngực chứ - chỗ 2 bên nách»)
        skin = section_radius(body, y, ang, c); sa = (np.asarray(ang) + np.pi) % (2 * np.pi) - np.pi
        for side in (1, -1):
            front = (side * sa > 0) & (side * sa < np.radians(70)) & (skin > 0.05)
            if not front.any(): continue
            apex = abs(sa[front][np.argmax(skin[front])])
            out = (side * sa > apex) & (skin > 0.05)
            r[out] = np.minimum(r[out], skin[out])
        # under the arm the arm-less section has NO skin (the arm was cut away): the hull there bridged 1–2 cm wider than both
        # neighbours and the top corner showed in front of the left arm as a brown point (Boss 25/10 ×2: «vệt nhọn nâu áo V7 bên nách
        # trái nhìn từ phía trước»). Blend across the gap from the hugged neighbours instead (reverse THU_ARM_GAP_HULL=1).
        # under the arm the arm-less section has NO skin (the arm was cut away): the hull bridged 1–2 cm wider there and the band corner
        # showed in front of the arm as a brown point (Boss 25/10 ×2). A straight CARTESIAN chord from the last trustworthy front point to
        # the first back point, zero pad (Codex: a polar blend still bows outward). Reverse THU_ARM_GAP_HULL=1.
        gap = skin <= 0.05
        if gap.any() and (~gap).any() and os.environ.get("THU_ARM_GAP_HULL") != "1":
            n = len(r); idx = np.arange(n); good = idx[~gap]; A = np.asarray(ang)
            for i in idx[gap]:
                lo = good[good < i]; hi = good[good > i]
                l = lo[-1] if len(lo) else good[-1] - n; h = hi[0] if len(hi) else good[0] + n
                Pl = r[l % n] * np.array([np.sin(A[l % n]), np.cos(A[l % n])]); Ph = r[h % n] * np.array([np.sin(A[h % n]), np.cos(A[h % n])])
                d = np.array([np.sin(A[i]), np.cos(A[i])]); e = Ph - Pl; M = np.array([d, -e]).T
                if abs(np.linalg.det(M)) < 1e-12: continue
                t, u = np.linalg.solve(M, Pl)
                if t > 0: r[i] = min(r[i], t)
    return c, r


def torn_edge(ang, n, depth, width_frac, rng, even, d_rng=(0.55, 1.5), w_rng=(0.6, 1.3)):
    """irregular pointed teeth around the band: tooth k has its own centre (jittered), depth (0.55–1.5×) and half-width (0.6–1.3×);
    `even` = the old regular comb (reverse test only). Returns the per-angle offset and the tooth table for the evenness gate."""
    base = (np.arange(n) + 0.5) / n * 2 * np.pi
    c = base + (0 if even else rng.uniform(-0.4, 0.4, n) * 2 * np.pi / n)
    d = depth * (np.ones(n) if even else rng.uniform(*d_rng, n))
    hw = width_frac * np.pi / n * (np.ones(n) if even else rng.uniform(*w_rng, n))
    off = np.zeros(len(ang))
    for ck, dk, wk in zip(c, d, hw):
        dist = np.abs((ang - ck + np.pi) % (2 * np.pi) - np.pi); off = np.maximum(off, dk * np.clip(1 - dist / wk, 0, None))
    return off, {"centre": np.sort(c % (2 * np.pi)), "depth": d, "half_width": hw}


def evenness(t):
    gaps = np.diff(np.r_[t["centre"], t["centre"][0] + 2 * np.pi])
    cv = lambda x: float(np.std(x) / max(np.mean(x), 1e-9))
    return cv(t["depth"]), cv(gaps), cv(t["half_width"])


def main(a):
    body = Body(a.body, a.joints, a.anatomy)
    peak = body.y["chest"] + body.A.get("chest", {}).get("peak_y_above_chest_joint_cm", 3.0) / 100
    bot = min(body.underbust_y, peak - 0.03); top = peak + 0.9 * (peak - bot)
    ys = np.array([bot, peak, peak + 0.5 * (top - peak), top]) if ROWS == 4 else np.linspace(bot, top, ROWS)
    ang = np.radians(np.array(STATIONS_DEG, float)) % (2 * np.pi); assert len(ang) == ANGLES
    near_j = lambda a_: int(np.argmin(np.abs((ang - a_ + np.pi) % (2 * np.pi) - np.pi)))
    rings = [hull_radius(body, y, ang) for y in ys]
    # every body VERTEX of the torso between two rows must sit inside the band: the low-poly body has sharp vertices (bust / armpit
    # front) that poke out between rows — sampling by area hardly sees them, Boss did («vật nhọn lòi ra nách», 25/10)
    TM = body._torso_mesh(); TV = TM.vertices[np.unique(TM.faces)]       # only vertices still used by torso faces (arm verts stay in the array)
    inband = (TV[:, 1] >= ys[0] - 0.005) & (TV[:, 1] <= ys[-1] + 0.005)
    # the band between two rows is their LINEAR blend, so a vertex at fraction t only needs the blend ≥ its radius; raising BOTH rows to it
    # pushed the top row 1.7–2.8 cm off the breast side by armpit vertices lower down (Boss 25/10 ×2: «vệt tà áo trên đang nhô ra bất
    # bình thường … chỗ 2 bên nách»). The nearer row takes the push (reverse THU_RAISE_BOTH_ROWS=1).
    both = os.environ.get("THU_RAISE_BOTH_ROWS") == "1"
    for v_ in TV[inband]:
        k_hi = int(np.clip(np.searchsorted(ys, v_[1]), 1, len(ys) - 1)); k_lo = k_hi - 1
        t_ = float(np.clip((v_[1] - ys[k_lo]) / (ys[k_hi] - ys[k_lo]), 0, 1)); rr_ = []
        for k_ in (k_lo, k_hi):
            c_, r_ = rings[k_]; d_ = v_[[0, 2]] - c_; a_ = np.arctan2(d_[0], d_[1]) % (2 * np.pi)
            j_ = near_j(a_); rr_.append((k_, j_, float(np.linalg.norm(d_)), r_[j_]))
        (klo, jlo, nlo, rlo), (khi, jhi, nhi, rhi) = rr_
        if both:
            for k_, j_, need, rk in rr_:
                if need > rk: c_, r_ = rings[k_]; r_ = r_.copy(); r_[j_] = need; rings[k_] = (c_, r_)
            continue
        need = nlo * (1 - t_) + nhi * t_; have = rlo * (1 - t_) + rhi * t_
        if need <= have: continue
        k_, j_, w_ = (klo, jlo, 1 - t_) if t_ < 0.5 else (khi, jhi, t_)
        c_, r_ = rings[k_]; r_ = r_.copy(); r_[j_] += (need - have) / max(w_, 1e-3); rings[k_] = (c_, r_)
    # no pointed bumps: an angle may stand at most 6 mm over the mean of its neighbours (leftover arm slivers at the armpit made the top
    # row jut 1.7 cm — «áo nữ đang bị vật nhọn lòi ra nách», 25/10)
    for k_ in range(len(rings)):
        c_, r_ = rings[k_]; r_ = r_.copy()
        for _ in range(0 if os.environ.get("THU_NO_SPIKE_CLAMP") else 6):  # reverse test only: keep the raw armpit slivers
            r_ = np.minimum(r_, (np.roll(r_, 1) + np.roll(r_, -1)) / 2 + 0.006)
        rings[k_] = (c_, r_)
    teeth = SPEC["hem"]["teeth"]; depth = float(np.median(SPEC["hem"]["tooth_depth_cm"])) / 100
    # IRREGULAR torn edges, bottom AND top (Boss 25/10: «các nét rách của tà áo hơi bị đều» · «tà áo phía trên hơi đều chưa tự nhiên»)
    even = bool(os.environ.get("THU_EVEN_HEM")); rng = np.random.default_rng(21)
    drop, t_bot = torn_edge(ang, teeth, depth, 1.0, rng, even)
    rise, t_top = torn_edge(ang, 9, 0.011, 0.9, rng, even, (0.4, 1.8), (0.5, 1.5))   # small torn points on the upper rim
    if ROPE_TRIM: rise = np.zeros(ANGLES)                                   # the rope sits on a plain top edge instead
    bad = []
    for nm, t in (("bottom", t_bot),) + ((("top", t_top),) if not ROPE_TRIM else ()):
        cd, cg, cw = evenness(t); ok = int(cd >= 0.25) + int(cg >= 0.25) + int(cw >= 0.25)
        print(f"  {nm} edge: depth CV {cd:.2f} · spacing CV {cg:.2f} · width CV {cw:.2f} (≥ 2 of 3 at 0.25)")
        if ok < 2: bad.append(f"{nm} torn edge too even")

    # the raised torn points of the top rim and the hanging teeth sit at their OWN height: the radius comes from the torso section there
    # (with the rim radius taken at ys[-1], the raised points fell inside the wider upper chest — 26 «garment under skin» points, 25/10)
    top_r = np.array([hull_radius(body, ys[-1] + rise[j], ang)[1][j] for j in range(ANGLES)])
    bot_r = np.array([hull_radius(body, ys[0] - drop[j], ang)[1][j] for j in range(ANGLES)])

    # FINAL radii, clamped once: taking max(r, top_r) AFTER the spike clamp restored the unclamped radii (Codex audit 25/10)
    FR = []
    for i in range(ROWS):
        r = rings[i][1].copy()
        if i == ROWS - 1 and not ROPE_TRIM: r = np.maximum(r, top_r)
        if i == 0: r = np.maximum(r, bot_r)
        for _ in range(0 if os.environ.get("THU_NO_SPIKE_CLAMP") else 6):
            r = np.minimum(r, (np.roll(r, 1) + np.roll(r, -1)) / 2 + 0.006)
        FR.append(r)
    # containment is the HARD rule and comes last: the clamp above pulled the rows back in and the breast came through the front
    # between the mid and top rows (v9 draft); the nearer row takes the push, as before. Torso vertices hidden UNDER the arm (≤ 2 cm from
    # an arm face) are skipped: they pushed single angles 1.7–3.4 cm out at the armpit (v9 draft spike gate)
    from scipy.spatial import cKDTree
    arm_kd = cKDTree(body.mesh.triangles_center[body.arm_face])
    under_arm = arm_kd.query(TV)[0] < 0.02
    if os.environ.get("THU_CONTAIN_UNDER_ARM") == "1": under_arm[:] = False   # reverse test: old behaviour
    for v_ in TV[inband & ~under_arm]:
        k_hi = int(np.clip(np.searchsorted(ys, v_[1]), 1, len(ys) - 1)); k_lo = k_hi - 1
        t_ = float(np.clip((v_[1] - ys[k_lo]) / (ys[k_hi] - ys[k_lo]), 0, 1)); q_ = []
        for k_ in (k_lo, k_hi):
            c_ = rings[k_][0]; d_ = v_[[0, 2]] - c_; j_ = near_j(np.arctan2(d_[0], d_[1]) % (2 * np.pi)); q_.append((k_, j_, float(np.linalg.norm(d_))))
        (klo, jlo, nlo), (khi, jhi, nhi) = q_
        need = nlo * (1 - t_) + nhi * t_; have = FR[klo][jlo] * (1 - t_) + FR[khi][jhi] * t_
        if need <= have: continue
        # least-norm split over BOTH rows (weights 1−t, t): pushing only the nearer row by Δ/w made a 4.5 cm bump when w was small
        den = (1 - t_) ** 2 + t_ ** 2; dl = need - have
        FR[klo][jlo] += dl * (1 - t_) / den; FR[khi][jhi] += dl * t_ / den
    # fabric BRIDGES over the breast instead of tenting to a point: where a station stands > 6 mm over the mean of its neighbours, raise
    # the NEIGHBOURS (never lower the station — containment stays exact). Reverse THU_NO_BRIDGE=1 → the 2.2 cm spike returns (rc 1).
    # Splitting each push bilinearly over two stations instead was tried 25/10: chest standoff 15.5 → 17.8 mm, underarm 7.0 → 8.3 (gate 8).
    if os.environ.get("THU_NO_BRIDGE") != "1":
        from scipy.optimize import minimize
        a_abs = np.abs((ang + np.pi) % (2 * np.pi) - np.pi)
        W = np.where((a_abs > np.radians(30)) & (a_abs < np.radians(120)), 10.0, 1.0)   # the side must hug (top-edge gate): raise the front first
        for i_, L in enumerate(FR):
            L = L.copy()
            cons = [{"type": "ineq", "fun": lambda r: 0.006 - (r - (np.roll(r, 1) + np.roll(r, -1)) / 2)}]   # each ≤ 6 mm over neighbours
            res = minimize(lambda r: float(np.sum(W * (r - L) ** 2)), L, jac=lambda r: 2 * W * (r - L), method="SLSQP",
                           bounds=[(l_, None) for l_ in L], constraints=cons, options={"maxiter": 500, "ftol": 1e-12})
            FR[i_] = np.maximum(res.x, L)

    def ring_pts(i, off, extra_drop=None):
        c = rings[i][0]; r = FR[i]; y = ys[i] - (extra_drop if extra_drop is not None else 0) + (rise if i == ROWS - 1 else 0)
        return np.c_[c[0] + np.sin(ang) * (r + off), np.full(ANGLES, 0) + y, c[1] + np.cos(ang) * (r + off)]
    V, F, role = [], [], []

    def add_quad(q, want, name):
        """two triangles of quad q (4 vertex ids) wound so their normal points along `want` (per-quad desired direction)."""
        P_ = np.array([V[i_] for i_ in q]); nrm = np.cross(P_[1] - P_[0], P_[2] - P_[0])
        a_, b_, c_, d_ = q
        F.extend([(a_, b_, c_), (a_, c_, d_)] if nrm @ want >= 0 else [(a_, c_, b_), (a_, d_, c_)]); role.extend([name] * 2)

    def band(i0, i1, name):
        base = len(V); rows = list(range(i0, i1 + 1))
        for i in rows:
            dr = drop if i == 0 else None
            V.extend(ring_pts(i, CLEARANCE, dr)); V.extend(ring_pts(i, CLEARANCE + THICK, dr))
        k = lambda ri, side, j: base + (ri * 2 + side) * ANGLES + (j % ANGLES)
        for ri in range(len(rows) - 1):
            for j in range(ANGLES):
                for side, flip in ((1, False), (0, True)):                 # outer faces out, inner faces in
                    a_, b_, c_, d_ = k(ri, side, j), k(ri, side, j + 1), k(ri + 1, side, j + 1), k(ri + 1, side, j)
                    F.extend([(a_, c_, b_), (a_, d_, c_)] if not flip else [(a_, b_, c_), (a_, c_, d_)])
                    # the top inner strip lies on the skin: dropped AFTER the closed leather is oriented (−40 tris for the strap);
                    # dropping it first left an open sheet that fix_normals turned inside-out — the front went see-through (v9 draft)
                    drop_strip = ROPE_TRIM and side == 0 and ri == len(rows) - 2
                    role.extend([name + ("#drop" if drop_strip else "")] * 2)
        for ri, flip in ((0, False), (len(rows) - 1, True)):              # close the bottom and top edges (leather thickness)
            for j in range(ANGLES):
                a_, b_, c_, d_ = k(ri, 0, j), k(ri, 0, j + 1), k(ri, 1, j + 1), k(ri, 1, j)
                F.extend([(a_, b_, c_), (a_, c_, d_)] if not flip else [(a_, c_, b_), (a_, d_, c_)]); role.extend([name] * 2)
    if ROPE_TRIM:
        band(0, ROWS - 1, "leather_dark")
        base = len(V)
        Pt = ring_pts(ROWS - 1, CLEARANCE + THICK); Pm = ring_pts(ROWS - 2, CLEARANCE + THICK)
        skin_t = section_radius(body, ys[-1], ang, np.asarray(rings[-1][0]))
        hidden = skin_t <= 0.05                                         # behind the arm (no torso skin at the top row)
        # ridge relief: 1 in the open, fading to 0 over the two stations before the strap goes behind the arm
        dist_h = np.array([min([min(abs(j - h), ANGLES - abs(j - h)) for h in np.where(hidden)[0]] or [9]) for j in range(ANGLES)])
        relief = np.clip(dist_h / 3.0, 0, 1)
        frames = []
        for j in range(ANGLES):
            up = Pt[j] - Pm[j]; up /= np.linalg.norm(up)
            rad = np.array([np.sin(ang[j]), 0, np.cos(ang[j])]); nn = rad - (rad @ up) * up; nn /= np.linalg.norm(nn)
            o = Pt[j] + nn * STRAP_GAP; zig = 1 if j % 2 == 0 else -1
            it, ib = o + up * STRAP_H_UP, o - up * STRAP_H_DN; ot, ob = it + nn * STRAP_T, ib + nn * STRAP_T
            rg = o + nn * (STRAP_T + RIDGE_OUT * relief[j]) + up * ((STRAP_H_UP - STRAP_H_DN) / 2 + zig * RIDGE_ZIG * relief[j])
            V.extend([it, ib, ot, ob, rg]); frames.append((up, nn))
        vid = lambda j, k_: base + (j % ANGLES) * 5 + k_                # 0 inner-top 1 inner-bottom 2 outer-top 3 outer-bottom 4 ridge
        for j in range(ANGLES):
            k = j + 1; up, nn = frames[j]; up2, nn2 = frames[k % ANGLES]; UP = up + up2; NN = nn + nn2
            add_quad((vid(j, 2), vid(k, 2), vid(k, 4), vid(j, 4)), NN, "rope_bone")    # outer face, upper facet
            add_quad((vid(j, 4), vid(k, 4), vid(k, 3), vid(j, 3)), NN, "rope_bone")    # outer face, lower facet
            add_quad((vid(j, 0), vid(k, 0), vid(k, 2), vid(j, 2)), UP, "rope_bone")    # top thickness
            add_quad((vid(j, 1), vid(k, 1), vid(k, 3), vid(j, 3)), -UP, "rope_bone")   # bottom thickness
    else:
        band(0, ROWS - 2, "leather_dark"); band(ROWS - 2, ROWS - 1, "leather_tan")
    V = np.array(V); F = np.array(F); role = np.array(role)
    sys.path.insert(0, os.path.join(HERE, "..", "..", "..", "theme")); import theme_colors as TC
    COL = {"leather_dark": (74, 53, 37), "leather_tan": (176, 138, 92), "rope_bone": (196, 164, 108)}
    sc = trimesh.Scene()
    for nm in [r_ for r_ in ("leather_dark", "leather_tan", "rope_bone") if (role == r_).any()]:
        sel = (role == nm) | (role == nm + "#drop")
        m = trimesh.Trimesh(V, F[sel], process=False)
        if nm != "rope_bone":                                           # orient the CLOSED leather, then drop the hidden strip
            m.fix_normals(); m.update_faces(~np.char.endswith(role[sel].astype(str), "#drop"))
        m.remove_unreferenced_vertices()
        m.visual = trimesh.visual.TextureVisuals(material=trimesh.visual.material.PBRMaterial(name=f"M_{nm}", baseColorFactor=TC.mau(COL[nm]), roughnessFactor=0.8, metallicFactor=0.0))
        sc.add_geometry(m, geom_name=nm, node_name=nm)
    sc.export(a.out)
    n = int((~np.char.endswith(role.astype(str), "#drop")).sum()); print(f"bandeau: {n} tris (budget {SPEC.get('tri_budget', 450)}) · y {bot:.3f}→{top:.3f} · {teeth} teeth {depth*100:.1f} cm · → {a.out}")
    if n > 450: print("⛔ over the 450-tri budget"); sys.exit(1)
    spikes = [float(np.max(r_ - (np.roll(r_, 1) + np.roll(r_, -1)) / 2)) for r_ in FR]   # on the EMITTED radii
    print(f"  radius spikes per row (cm): {[round(x * 100, 1) for x in spikes]} (≤ {SPIKE_MAX * 100:.1f})")
    if max(spikes) > SPIKE_MAX: bad.append(f"a pointed bump sticks out of the band ({max(spikes) * 100:.1f} cm over its neighbours)")
    # gate: the leather's top row outside the breast apexes (breast side → armpit → back) must hug the skin
    Lv = V[:base][np.abs(V[:base, 1] - ys[-1]) < 1e-6] if ROPE_TRIM else np.zeros((0, 3))   # leather top row only
    if len(Lv):
        c_t = np.asarray(rings[-1][0]); aL = np.arctan2(Lv[:, 0] - c_t[0], Lv[:, 2] - c_t[1]); dL, _ = body.signed(Lv)
        side_ = (np.abs(aL) > np.radians(30)) & (np.abs(aL) < np.radians(120)) & ~body.arm_face[body.Pfi[body.kd.query(Lv)[1]]]
        worst_top = float(dL[side_].max()) if side_.any() else 0.0
        print(f"  top edge off the skin, breast side → armpit: worst {worst_top * 1000:.1f} mm (≤ {TOP_HUG_MAX * 1000:.0f})")
        if worst_top > TOP_HUG_MAX: bad.append(f"the top edge stands {worst_top * 100:.1f} cm off the chest beside the armpit")
    # gate: what the owner sees at the armpit — depth-tested front / ±35° masks per colour, longest narrow spur (measure_armpit_point.py)
    import measure_armpit_point as MAP
    pts = MAP.measure(a.out, a.body); w_ = max(pts, key=pts.get)
    print(f"  armpit point (longest narrow spur): worst {w_} {pts[w_]} mm (≤ {POINT_MAX})")
    if pts[w_] > POINT_MAX: bad.append(f"a point sticks out of the band at the armpit ({w_}, {pts[w_]} mm)")
    for b_ in bad: print("⛔", b_)
    if bad: sys.exit(1)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    for k in ("--body", "--joints", "--anatomy", "--out"): ap.add_argument(k, required=True)
    main(ap.parse_args())

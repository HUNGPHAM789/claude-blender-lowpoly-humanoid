"""LPD spec test — procedural MALE base body + HAIR_SHORT_01 (pure numpy, Z-up, faces -Y).

Every face is a list of 3 or 4 vertex indices with a region label, so Q/T counts are
measured from the source polygon list (not estimated).  Region render-triangle budgets
are hit by construction (ring counts chosen per region); then each region's Q/T split is
reached by triangulating its most non-planar quads (spec: a non-planar quad = 2 tris).
"""
import math, json, sys, os
import numpy as np
GIOI = os.environ.get('GIOI', 'nam')   # 'nam' | 'nu' — cùng topology/số mặt, khác vị trí đỉnh (spec: male/female identical counts)
NU = GIOI == 'nu'
TAY_K = float(os.environ.get('TAY_K', '0.86'))
CO = float(os.environ.get('CO', '0'))   # 0 = tay xoè (bản đã chốt) · 1 = NẮM quanh trụ Ø32 mm (socket cam_*) — Boss 22/10: settler cầm công cụ
R_CAM = 0.016
RHO = R_CAM + float(os.environ.get('RHO_KHE', '0.003'))   # tâm trụ → mặt trong ngón
DN = float(os.environ.get('DN', '0.002')); DV = float(os.environ.get('DV', '0.002'))   # dò lưới 22/10 (check_hold.py): nam ôm 66 % lún 0,5 · nữ 66 % 0,6
TU, TV, TN, TC = (float(x) for x in os.environ.get('CAI', '0.15,0.7,0.7,0.3').split(','))
CAM = {}   # bên → (tâm, trục, r) chưa nhân K_CAO
KHOP = {}  # tâm khớp cho rig (chưa nhân K_CAO): shoulder/khuỷu/cổ tay/đầu bàn tay, hông/gối/cổ chân/mũi chân   # tỉ lệ chiều dài cánh+cẳng tay (1.0 = bản đầu, tay dài)

V = []          # vertices
F = []          # (idx list, region, mat)


def av(p):
    V.append(np.array(p, float)); return len(V) - 1


def af(idx, region, mat=0):
    F.append([list(idx), region, mat])


def P(i): return V[i]


# ------------------------------------------------------------------ generic band (zipper + quad pairing)
def band(A, B, frame_c, fu, fw, region, closed=True):
    """Connect ring A (vertex ids) to ring B. Params from angle in plane (fu,fw) about frame_c.
    Moves are paired into quads (AB/BA/AA/BB); leftovers become triangles."""
    def params(R):
        a = [math.atan2(np.dot(P(i) - frame_c, fw), np.dot(P(i) - frame_c, fu)) for i in R]
        a = np.unwrap(a)
        if a[-1] < a[0]: a = -a
        return a - a[0]
    pa, pb = params(A), params(B)
    # rotate B so its start is closest to A[0] in angle
    n, m = len(A), len(B)
    ang = lambda i: math.atan2(np.dot(P(i) - frame_c, fw), np.dot(P(i) - frame_c, fu))
    # make both increasing in same sense: check sense of A and B separately
    def sense(R):
        a = np.unwrap([ang(i) for i in R]); return 1 if a[-1] > a[0] else -1
    sa, sb = sense(A), sense(B)
    if sa != sb: B = [B[0]] + B[1:][::-1]
    a0 = ang(A[0])
    k = min(range(m), key=lambda j: abs(((ang(B[j]) - a0 + math.pi) % (2 * math.pi)) - math.pi))
    B = B[k:] + B[:k]
    pa = np.unwrap([sa * ang(i) for i in A]); pa = pa - pa[0]
    pb = np.unwrap([sa * ang(i) for i in B]); pb = pb - pb[0]
    pb = (pb + math.pi) % (2 * math.pi) - math.pi if False else pb
    pa = list(pa) + [2 * math.pi]; pb = list(pb) + [2 * math.pi]
    i = j = 0; moves = []
    while i < n or j < m:
        if j >= m or (i < n and (pa[i + 1] + pa[i]) / 2 <= (pb[j + 1] + pb[j]) / 2):
            moves.append('A'); i += 1
        else:
            moves.append('B'); j += 1
    # rotate move list so pairing is cyclic-friendly: start at index 0
    Ai = lambda x: A[x % n]; Bi = lambda x: B[x % m]
    faces = []; i = j = 0; t = 0
    while t < len(moves):
        if t + 1 < len(moves) and len(moves) - t >= 2:
            pair = moves[t] + moves[t + 1]
        else:
            pair = moves[t]
        if pair in ('AB', 'BA'):
            faces.append([Ai(i), Ai(i + 1), Bi(j + 1), Bi(j)]); i += 1; j += 1; t += 2
        elif pair == 'AA':
            faces.append([Ai(i), Ai(i + 1), Ai(i + 2), Bi(j)]); i += 2; t += 2
        elif pair == 'BB':
            faces.append([Ai(i), Bi(j + 2), Bi(j + 1), Bi(j)]); j += 2; t += 2
        elif pair == 'A':
            faces.append([Ai(i), Ai(i + 1), Bi(j)]); i += 1; t += 1
        else:
            faces.append([Ai(i), Bi(j + 1), Bi(j)]); j += 1; t += 1
    for f in faces: af(f, region)
    return faces


def ring(center, fu, fw, ru, rw, angles, push=None):
    ids = []
    for k, a in enumerate(angles):
        r = 1.0 if push is None else push(k, a)
        ids.append(av(center + fu * ru * math.cos(a) * r + fw * rw * math.sin(a) * r))
    return ids


def frame_from(t):
    t = t / np.linalg.norm(t)
    u = np.array([0, 1.0, 0]) - t * t[1]
    if np.linalg.norm(u) < 1e-6: u = np.array([1.0, 0, 0]) - t * t[0]
    u /= np.linalg.norm(u); w = np.cross(t, u)
    return t, u, w


def root_angles(R, c, fu, fw):
    return [math.atan2(np.dot(P(i) - c, fw), np.dot(P(i) - c, fu)) for i in R]


def blend_angles(ra, s):
    """blend root angles toward uniform spacing (same order/sense), s in [0,1]."""
    ra = np.unwrap(ra); n = len(ra); sgn = 1 if ra[-1] > ra[0] else -1
    best = None
    for off in np.linspace(-math.pi, math.pi, 73):
        u = ra[0] + off + sgn * 2 * math.pi * np.arange(n) / n
        e = np.sum((u - ra) ** 2)
        if best is None or e < best[0]: best = (e, u)
    return list((1 - s) * ra + s * best[1])


# ================================================================== BODY (male, 1.75 m)
X, Y, Z = np.eye(3)
N16 = [math.radians(a) for a in range(0, 360, 22)][:0]
TA = [2 * math.pi * k / 16 for k in range(16)]   # torso angles: 0 = front (-Y), +x toward char's left


def tpt(z, w, d, a, yc=0.0, dback=None):
    dd = d if math.cos(a) > 0 else (dback or d)
    return np.array([w * math.sin(a), yc - dd * math.cos(a), z])


# torso rings (z, half-width, half-depth front, half-depth back)
TOR = [(0.865, .165, .105, .120), (0.905, .172, .105, .125), (0.950, .168, .100, .108),
       (1.000, .152, .097, .100), (1.050, .142, .093, .095), (1.100, .148, .097, .098),
       (1.150, .158, .104, .100), (1.200, .168, .112, .104), (1.250, .175, .114, .106),
       (1.300, .182, .110, .104), (1.350, .190, .102, .100), (1.400, .182, .085, .090),
       (1.440, .120, .068, .072)]
if NU:   # nữ: hông/mông rộng, eo thắt, ngực, vai hẹp (spec: «moderately wider pelvis and softer taper», không phóng đại)
    TOR = [(0.865, .176, .106, .130), (0.905, .183, .106, .134), (0.950, .174, .100, .114),
           (1.000, .150, .095, .100), (1.050, .130, .088, .090), (1.100, .133, .090, .092),
           (1.150, .143, .098, .094), (1.200, .153, .108, .098), (1.250, .158, .110, .100),
           (1.300, .163, .104, .098), (1.350, .170, .096, .094), (1.400, .162, .080, .084),
           (1.440, .108, .062, .066)]
T = []
for ti, (z, w, df, db) in enumerate(TOR):
    r = []
    for k, a in enumerate(TA):
        if ti == 10 and k in (4, 12):
            r.append(None); continue              # will be inside arm hole (loose) -> skip
        p = tpt(z, w, df, a, 0.0, db)
        if ti in (0, 1) and k == 8: p[1] -= 0.012      # shallow central sacral transition
        if ti in (7, 8) and k == 0: p[1] += 0.008      # sternum crease
        if NU:   # BẦU NGỰC (Boss 22/10 «nữ thì chưa thấy ngực»): đẩy RIÊNG các đỉnh ±22,5°/±45° ra trước, thu nếp dưới ngực
            # — đẩy đều cả vòng chỉ làm ngực dày hơn, không thành bầu (bản v0.2 lỗi: nhô so với rãnh giữa −1 mm)
            DAY = {7: {1: .024, 15: .024, 2: .015, 14: .015}, 8: {1: .019, 15: .019, 2: .012, 14: .012},
                   9: {1: .007, 15: .007, 2: .004, 14: .004}, 6: {1: -.004, 15: -.004, 2: -.002, 14: -.002}}
            if ti in DAY and k in DAY[ti]: p[1] -= DAY[ti][k]
        if ti in (0, 1, 2) and k in (5, 6, 7, 9, 10, 11): p[1] += ((0.036, 0.032, 0.014) if NU else (0.030, 0.026, 0.010))[ti] * (1.0 if k in (6, 7, 9, 10) else 0.6)  # gluteal projection
        r.append(av(p))
    T.append(r)
HOLE = {4: [(9, 3), (9, 4), (9, 5), (10, 5), (11, 5), (11, 4), (11, 3), (10, 3)]}
holes_faces = {(row, col) for row in (9, 10) for col in (3, 4, 11, 12)}
for row in range(12):
    for col in range(16):
        if (row, col) in holes_faces: continue
        a, b = col, (col + 1) % 16
        af([T[row][a], T[row][b], T[row + 1][b], T[row + 1][a]], 'torso')
# glute share inside torso: row 0 rear 8 cols (4..11), row 1 centre 4 cols (6..9)
GLUTE_TORSO = {(0, c) for c in range(4, 12)} | {(1, c) for c in (6, 7, 8, 9)}
# tag torso faces with (row,col) via order: rebuild tags
fi = 0
for row in range(12):
    for col in range(16):
        if (row, col) in holes_faces: continue
        idx = len(F) - (12 * 16 - len(holes_faces)) + fi
        if (row, col) in GLUTE_TORSO: F[idx][1] = 'glute'
        fi += 1

# ---- neck
NECK = [(1.470, .050, .050), (1.500, .045, .047), (1.530, .047, .049)] if NU else [(1.470, .056, .056), (1.500, .052, .054), (1.530, .054, .056)]
Nr = [ring(np.array([0, 0.004, z]), -Y, X, d, w, [2 * math.pi * k / 8 for k in range(8)]) for z, w, d in NECK]
band(T[12], Nr[0], np.array([0, 0, 1.44]), -Y, X, 'torso')
band(Nr[0], Nr[1], np.array([0, 0, 1.48]), -Y, X, 'neck')
band(Nr[1], Nr[2], np.array([0, 0, 1.51]), -Y, X, 'neck')

# ---- head: 16 non-uniform symmetric columns, 8 rings + crown pole
HA = [0, 16, 34, 55, 80, 105, 130, 155, 180, 205, 230, 255, 280, 305, 326, 344]
HA = [math.radians(a) for a in HA]
HYC = -0.012
# (z, half-width, depth front, depth back)
HR = [(1.540, .058, .062, .050), (1.565, .063, .086, .072), (1.592, .066, .094, .086),
      (1.618, .071, .096, .095), (1.642, .076, .095, .100), (1.662, .078, .094, .104),
      (1.686, .078, .095, .104), (1.722, .066, .080, .090)]
if NU:   # đầu nữ: hẹp hơn 4 %, hàm/cằm (vòng 0–1) thon hơn 12 %
    HR = [(z, w * (0.88 if i <= 1 else 0.96), df * 0.97, db * 0.97) for i, (z, w, df, db) in enumerate(HR)]
POLE_Z = 1.752


def scalp(a, z):
    """shared SCALP_REFERENCE envelope (used for head rings >= r5 and for hair fit)."""
    zs = [h[0] for h in HR] + [POLE_Z]
    ws = [h[1] for h in HR] + [0.0]; dfs = [h[2] for h in HR] + [0.0]; dbs = [h[3] for h in HR] + [0.0]
    w = np.interp(z, zs, ws); df = np.interp(z, zs, dfs); db = np.interp(z, zs, dbs)
    return tpt(z, w, df, a, HYC, db)


FEAT = {  # (ring, col-vertex k) -> (dy forward(-)/back(+), dz)
    (3, 0): (-.021, 0), (4, 0): (-.014, 0), (5, 0): (-.007, 0), (6, 0): (-.004, 0),     # nose tip/bridge
    (2, 0): (-.004, 0), (2, 1): (.004, 0), (2, 15): (.004, 0),                        # lip + crease
    (1, 0): (-.010, -.004), (1, 1): (-.004, 0), (1, 15): (-.004, 0),                  # chin (angular)
    (4, 2): (.010, 0), (4, 14): (.010, 0), (5, 2): (.012, 0), (5, 14): (.012, 0),     # eye socket inset
    (4, 1): (.006, 0), (4, 15): (.006, 0), (5, 1): (.004, 0), (5, 15): (.004, 0),
    (6, 1): (-.006, .002), (6, 15): (-.006, .002), (6, 2): (-.008, .002), (6, 14): (-.008, .002),  # brow ridge
    (3, 3): (-.008, 0), (3, 13): (-.008, 0), (4, 3): (-.010, 0), (4, 13): (-.010, 0),  # cheekbones
    (1, 3): (0, -.004), (1, 13): (0, -.004), (1, 4): (.004, -.008), (1, 12): (.004, -.008),  # jaw angle
}
_ML = os.environ.get("MAT_LOM", "2")   # Boss 23/10 CHỐT mắt C (hốc lõm + bóng da tối) làm MẶC ĐỊNH. Cũ: 0 ô đen (A), 1 chỉ lõm (B)
MAT_LOM = _ML in ("1", "2"); MAT_BONG = _ML == "2"   # Boss 23/10 «chỗ mắt… thay vì black square thì làm thành chỗ lỏm vào dạng abstract faceless» — bản B của A/B
if MAT_LOM:   # hốc mắt SÂU, không vật liệu đen: bóng trong hốc tự đọc thành mắt
    for kk, d in {(4, 1): .016, (4, 15): .016, (4, 2): .020, (4, 14): .020, (5, 1): .012, (5, 15): .012, (5, 2): .018, (5, 14): .018}.items(): FEAT[kk] = (d * (1.35 if MAT_BONG else 1.0), 0)
if NU:   # nữ: cung mày nhẹ, cằm mềm, mũi nhỏ hơn, gò má mềm hơn (spec: «narrower jaw, softer cheek taper, subtler brow ridge»)
    for kk in list(FEAT):
        dy, dz = FEAT[kk]; r_, c_ = kk
        if r_ == 6: FEAT[kk] = (dy * 0.45, dz)          # brow
        elif r_ in (3, 4, 5) and c_ == 0: FEAT[kk] = (dy * 0.8, dz)   # mũi
        elif r_ == 1: FEAT[kk] = (dy * 0.6, dz * 0.6)    # cằm + góc hàm
        elif c_ in (3, 13): FEAT[kk] = (dy * 0.7, dz)   # gò má
H = []
for ri, (z, w, df, db) in enumerate(HR):
    r = []
    for k, a in enumerate(HA):
        p = tpt(z, w, df, a, HYC, db)
        if (ri, k) in FEAT:
            dy, dz = FEAT[(ri, k)]
            # push along local outward normal for side features
            if k in (0,): p[1] += dy
            else:
                nrm = np.array([math.sin(a), -math.cos(a), 0]); p -= nrm * dy * (1 if True else 0)
            p[2] += dz
        r.append(av(p))
    H.append(r)
pole = av([0, HYC + 0.008, POLE_Z])
band(Nr[2], H[0], np.array([0, 0, 1.54]), -Y, X, 'neck')
FACE_COLS = set(list(range(11, 16)) + list(range(0, 5)))     # 10 front columns
EYE = {(4, 1), (4, 14)}
for row in range(7):
    for col in range(16):
        a, b = col, (col + 1) % 16
        reg = 'face' if (col in FACE_COLS or (col in (5, 10) and row <= 4)) else 'skull'
        af([H[row][a], H[row][b], H[row + 1][b], H[row + 1][a]], reg, (3 if MAT_BONG else 1 if not MAT_LOM else 0) if (row, col) in EYE else 0)
for col in range(16):
    af([H[7][col], H[7][(col + 1) % 16], pole], 'skull')


# ---- ears (embedded shells, 8Q+4T each, built for left then mirrored later)
def ear(side):
    s = side
    c = np.array([s * 0.079, 0.010, 1.640])
    base = [av(c + np.array([-s * .006, .016 * math.cos(t), .026 * math.sin(t)])) for t in
            [math.radians(a) for a in (90, 30, -30, -90, -150, 150)]]
    rim = [av(c + np.array([s * .012, .019 * math.cos(t) + .004, .030 * math.sin(t)])) for t in
           [math.radians(a) for a in (90, 30, -30, -90, -150, 150)]]
    for i in range(6):
        af([base[i], base[(i + 1) % 6], rim[(i + 1) % 6], rim[i]], 'ears')
    p = av(c + np.array([s * .004, .004, .010])); q = av(c + np.array([s * .004, .004, -.010]))
    r0, r1, r2, r3, r4, r5 = rim
    af([r1, r2, q, p], 'ears'); af([r4, r5, p, q], 'ears')
    af([r0, r1, p], 'ears'); af([r5, r0, p], 'ears'); af([r2, r3, q], 'ears'); af([r3, r4, q], 'ears')


ear(1); ear(-1)

# ---- symmetric limb builders (left side; right built with mirror=-1)
SIDE_HOLES = {}


def tid(row, k, s):
    return T[row][k if s > 0 else (16 - k) % 16]


def arm_and_hand(s):
    hole = [tid(r, k, s) for r, k in HOLE[4]]
    if s < 0: hole = hole[::-1]
    c0 = np.mean([P(i) for i in hole], axis=0)
    adir = np.array([s * math.sin(math.radians(20)), 0.02, -math.cos(math.radians(20))]); adir /= np.linalg.norm(adir)
    sh = c0 + np.array([s * 0.035, 0, -0.03])
    # (dist along arm, radius_front_back, radius_side)
    prof = [(0.00, .052, .056), (0.05, .050, .052), (0.10, .046, .047), (0.15, .043, .043), (0.21, .040, .040),
            (0.27, .036, .036), (0.30, .038, .034), (0.35, .040, .036), (0.41, .035, .032), (0.47, .030, .027),
            (0.53, .024, .026)]
    if NU: prof = [(d, rf * (0.95 if k == 0 else 0.86), rs * (0.95 if k == 0 else 0.86)) for k, (d, rf, rs) in enumerate(prof)]
    prof = [(d * TAY_K, rf, rs) for d, rf, rs in prof]   # Boss 22/10 «Sửa tay ngắn lại tí»: đầu ngón tay 0,369·H → ~0,41·H
    rings = [hole]
    ra = None
    for k, (d, rf, rs) in enumerate(prof):
        cen = sh + adir * d
        t, u, w = frame_from(adir if k > 0 else (adir + np.array([s, 0, 0])) / 2)
        if ra is None:
            ra = root_angles(hole, cen, u, w)
        ang = blend_angles(ra, min(1.0, 0.5 + 0.25 * k))
        rings.append(ring(cen, u, w, rf, rs, ang))
    for k in range(11):
        cen = sh + adir * prof[min(k, 10)][0]
        t, u, w = frame_from(adir)
        band(rings[k], rings[k + 1], cen, u, w, 'arms')
    ben = 'L' if s > 0 else 'R'
    KHOP[f'vai_{ben}'] = sh.copy(); KHOP[f'khuyu_{ben}'] = sh + adir * prof[5][0]; KHOP[f'co_tay_{ben}'] = sh + adir * prof[-1][0]
    KHOP[f'xuong_don_{ben}'] = np.array([s * 0.025, 0.0, sh[2] + 0.01])
    # ---------------- hand
    wc = sh + adir * prof[-1][0]
    v = adir.copy()
    n = (1 - CO) * np.array([-s * 0.35, -1.0, 0.0]) + CO * np.array([-s, -0.25, 0.0])   # nắm: lòng tay quay VÀO đùi ⇒ trụ nắm chĩa ra trước
    n -= v * np.dot(n, v); n /= np.linalg.norm(n)   # palm normal (forward, slightly in)
    u = np.cross(n, v); u = u if u[0] * s > 0 else -u                                        # thumb side = away from body
    W = rings[-1]

    def hring(dist, N, hw, th, ph=0.0, du=0.0):
        cen = wc + v * dist + u * du
        ids = []
        for j in range(N):
            a = ph + 2 * math.pi * j / N
            ca, sa = math.cos(a), math.sin(a)
            # superellipse-ish rounded rectangle
            uu = hw * np.sign(ca) * abs(ca) ** 0.6; nn = th * np.sign(sa) * abs(sa) ** 0.8
            ids.append(av(cen + u * uu + n * nn))
        return ids, cen
    Bv, cB = hring(0.022, 10, .036, .018, du=0.004)
    C1, cC1 = hring(0.045, 11, .042, .017, du=0.002)
    C2, cC2 = hring(0.065, 11, .044, .016)
    C3, cC3 = hring(0.082, 11, .045, .015)
    # knuckle ring K: P0..P8 (palm, +n) then B8..B0 (back)
    kd = 0.097; HW = .044; TH = .013
    xs = np.linspace(HW, -HW, 9)
    arch = lambda x: -0.004 * (x / HW) ** 2
    Pk = [av(wc + v * (kd + 0.004 * math.cos(math.pi * x / (2 * HW))) + u * x + n * TH) for x in xs]
    Bk = [av(wc + v * (kd + 0.006 * math.cos(math.pi * x / (2 * HW))) + u * x - n * (TH + 0.002) + n * arch(x)) for x in xs]
    K = Pk + Bk[::-1]
    band(W, Bv, wc, u, n, 'hands')
    fB = band(Bv, C1, cB, u, n, 'hands')
    band(C1, C2, cC1, u, n, 'hands'); band(C2, C3, cC2, u, n, 'hands')
    band(C3, K, cC3, u, n, 'hands')
    # thumb hole: two adjacent quads of band Bv->C1 with max (u + 0.6 n) direction
    nb = len(fB); start = len(F) - 0
    cand = []
    for fi_ in range(len(F)):
        f = F[fi_]
        if f[0] in fB and len(f[0]) == 4:
            cand.append(fi_)
    def score(fi_): return np.dot(np.mean([P(i) for i in F[fi_][0]], 0) - cB, u + 0.5 * n)
    cand.sort(key=score, reverse=True)
    f1 = cand[0]
    f2 = next(c for c in cand[1:] if len(set(F[c][0]) & set(F[f1][0])) == 2)
    e1, e2 = F[f1][0], F[f2][0]
    # boundary loop of union
    edges = {}
    for f in (e1, e2):
        for a_, b_ in zip(f, f[1:] + f[:1]):
            key = tuple(sorted((a_, b_))); edges[key] = edges.get(key, 0) + 1
    bnd = [k for k, c in edges.items() if c == 1]
    loop = [bnd[0][0], bnd[0][1]]; bnd = bnd[1:]
    while len(bnd):
        for e in bnd:
            if loop[-1] in e:
                nx = e[1] if e[0] == loop[-1] else e[0]
                bnd.remove(e)
                if nx != loop[0]: loop.append(nx)
                break
    for fidx in sorted((f1, f2), reverse=True): F.pop(fidx)
    # thumb
    tc = np.mean([P(i) for i in loop], 0)
    tdir = (1 - CO) * (u * 0.75 + v * 0.55 + n * 0.45) + CO * (u * TU + v * TV + n * TN); tdir /= np.linalg.norm(tdir)
    digit(loop, tc, tdir, n, [(0.030, .012, .010), (0.058, .010, .008)], 0.075, curl=0.25 + CO * TC)
    # fingers
    lens = [0.078, 0.086, 0.080, 0.062]
    for i in range(4):
        root = [Pk[2 * i], Pk[2 * i + 1], Pk[2 * i + 2], Bk[2 * i + 2], Bk[2 * i + 1], Bk[2 * i]]
        rc = np.mean([P(j) for j in root], 0)
        spread = (1.5 - i) * 0.10 * (1 - CO)
        fd = v + u * spread; fd /= np.linalg.norm(fd)
        L = lens[i]
        rr = .0095 - i * .0006
        digit(root, rc, fd, n, [(L * .40, rr, rr * .85), (L * .70, rr * .9, rr * .78), (L * .92, rr * .78, rr * .68)],
              L, curl=0.18 * (1 - CO), om=(np.cross(v, n), RHO + rr * .85) if CO > 0 else None)
    if CO > 0:
        CAM[s] = (np.mean([P(j) for j in Pk], 0) + n * (R_CAM + TH * 0.0 + DN) + v * DV, u.copy(), R_CAM)


def _quay(x, k, a):
    k = k / np.linalg.norm(k); return x * math.cos(a) + np.cross(k, x) * math.sin(a) + k * np.dot(k, x) * (1 - math.cos(a))


def digit(root, rc, d, n, segs, L, curl, om=None):
    """om = (trục, bán kính tâm-ngón) khi NẮM: mỗi đốt bẻ theo cung tròn ôm trụ — góc = độ dài đốt / bán kính × CO."""
    rings = [root]
    pos = rc.copy(); dd = d.copy(); prev = 0
    th = [((dist - (segs[k - 1][0] if k else 0)) / om[1]) * CO for k, (dist, _, _) in enumerate(segs)] + [((L - segs[-1][0]) / om[1]) * CO] if om else None
    for k, (dist, rw, rt) in enumerate(segs):
        if om: dd = _quay(dd, om[0], ((th[k - 1] if k else 0) + th[k]) / 2)
        dd = dd + n * curl * 0.5; dd /= np.linalg.norm(dd)
        pos = pos + dd * (dist - prev); prev = dist
        t = dd; nn = n - t * np.dot(n, t); nn /= np.linalg.norm(nn); uu = np.cross(t, nn)
        ra = root_angles(root, rc, uu, nn) if k == 0 else ra0
        if k == 0: ra0 = ra
        ang = blend_angles(ra, 0.7 + 0.1 * k)
        rings.append([av(pos + uu * rw * math.cos(a) + nn * rt * math.sin(a)) for a in ang])
    for k in range(len(segs)):
        a, b = rings[k], rings[k + 1]
        for j in range(6):
            af([a[j], a[(j + 1) % 6], b[(j + 1) % 6], b[j]], 'hands')
    if om: dd = _quay(dd, om[0], (th[-2] + th[-1]) / 2)
    dd = dd + n * curl * 0.5; dd /= np.linalg.norm(dd)
    tip = av(pos + dd * (L - prev))
    for j in range(6):
        af([rings[-1][j], rings[-1][(j + 1) % 6], tip], 'hands')


CROTCH = av([0, 0.006, 0.815])


def leg_and_foot(s):
    root = [tid(0, k, s) for k in range(9)] + [CROTCH]
    cx = s * 0.092
    # (z, radius x, radius y, centre y)
    prof = [(0.765, .084, .092, .012), (0.700, .078, .084, .006), (0.640, .072, .076, 0.0),
            (0.585, .066, .070, -.004), (0.540, .060, .062, -.006), (0.505, .055, .057, -.008),
            (0.475, .052, .057, -.010), (0.445, .050, .052, -.006), (0.390, .050, .054, .002),
            (0.320, .052, .058, .010), (0.240, .045, .049, .010), (0.165, .036, .040, .008),
            (0.115, .031, .034, .006), (0.085, .031, .036, .008)]
    if NU:   # đùi trên đầy hơn (hông rộng), cẳng/cổ chân thon
        prof = [(z, rx * (1.06 if k <= 2 else 0.92 if k >= 7 else 0.98), ry * (1.06 if k <= 2 else 0.92 if k >= 7 else 0.98), cy)
                for k, (z, rx, ry, cy) in enumerate(prof)]
    ben = 'L' if s > 0 else 'R'
    KHOP[f'hong_{ben}'] = np.array([cx, 0.0, 0.80]); KHOP[f'goi_{ben}'] = np.array([cx - s * 0.002 * 1.8, -0.004, 0.475])
    KHOP[f'co_chan_{ben}'] = np.array([cx, 0.008, 0.085]); KHOP[f'mui_chan_{ben}'] = np.array([cx, -0.15, 0.02])
    rings = [root]; c0 = np.array([cx, 0, 0.83])
    ra = root_angles(root, c0, -Y, X)
    for k, (z, rx, ry, cy) in enumerate(prof):
        cen = np.array([cx - s * 0.002 * k * 0.3, cy, z])
        if k == 6:   # knee ring: 12 verts with kneecap
            ang = [2 * math.pi * j / 12 for j in range(12)]
            ids = []
            for j, a in enumerate(ang):
                kp = 1.12 if j in (0, 1, 11) else 1.0
                ids.append(av(cen + (-Y) * ry * math.cos(a) * kp + X * rx * math.sin(a) * s))
            rings.append(ids); continue
        ang = blend_angles(ra, min(1.0, 0.35 + 0.22 * k))
        def push(j, a, k=k):
            # gluteal fold / calf
            back = -math.cos(a)
            f = 1.0
            if k in (0, 1, 2) and back > 0.2: f += (0.30, 0.20, 0.08)[k] * back
            if k in (9, 10) and back > 0.2: f += 0.10 * back
            return f
        ids = []
        for j, a in enumerate(ang):
            ids.append(av(cen + (-Y) * ry * math.cos(a) * push(j, a) + X * rx * math.sin(a) * push(j, a)))
        rings.append(ids)
    nb = []
    for k in range(14):
        cen = np.array([cx, 0, (P(rings[k][1])[2] + P(rings[k + 1][1])[2]) / 2])
        nb.append(band(rings[k], rings[k + 1], cen, -Y, X, 'legs'))
    # glute share: rows 0..3 five most-rear faces, row 4 two most-rear
    for k, cnt in enumerate([5, 5, 5, 5, 2]):
        fl = [f for f in nb[k]]
        fl.sort(key=lambda f: -np.mean([P(i)[1] for i in f]))
        sel = fl[:cnt]
        for f in F:
            if f[0] in sel and f[1] == 'legs': f[1] = 'glute'
    # foot
    A = rings[-1]; ac = np.array([cx, 0.008, 0.085])
    def fring(z, cy, rx, ry, N=12):
        out = []
        for j in range(N):
            a = 2 * math.pi * j / N
            yy = cy - ry * math.cos(a); xx = cx + s * rx * math.sin(a) * (1.0 + 0.15 * max(0, math.cos(a)))
            out.append(av([xx, yy, z]))
        return out
    F1 = fring(0.052, -0.010, .040, .068)
    F2 = fring(0.024, -0.040, .047, .118)
    F3 = fring(0.000, -0.040, .044, .114)
    band(A, F1, ac, -Y, X, 'feet')
    band(F1, F2, np.array([cx, -0.01, .04]), -Y, X, 'feet')
    band(F2, F3, np.array([cx, -0.04, .01]), -Y, X, 'feet')
    sidx = 6  # heel (a=pi)
    R = F3; r_ = lambda o: R[(sidx + o) % 12]
    af([r_(0), r_(1), r_(-1)], 'feet')
    for o in range(1, 5):
        af([r_(o), r_(o + 1), r_(-o - 1), r_(-o)], 'feet')
    af([r_(5), r_(6), r_(-5)], 'feet')


for s in (1, -1):
    arm_and_hand(s)
    leg_and_foot(s)

# ================================================================== region Q/T adjustment
TARGET = {'face': (64, 32), 'skull': (32, 16), 'ears': (16, 8), 'neck': (24, 8), 'torso': (160, 48),
          'arms': (160, 32), 'hands': (276, 60), 'glute': (48, 16), 'legs': (224, 32), 'feet': (64, 32)}


def nonplanarity(f):
    p = np.array([P(i) for i in f])
    nrm = np.cross(p[2] - p[0], p[3] - p[1]); nn = np.linalg.norm(nrm)
    if nn < 1e-12: return 0
    nrm /= nn; c = p.mean(0)
    return float(np.max(np.abs((p - c) @ nrm)) / (np.linalg.norm(p[2] - p[0]) + 1e-9))


def split_to_target(region, target_T):
    idx = [i for i, f in enumerate(F) if f[1] == region]
    T0 = sum(1 for i in idx if len(F[i][0]) == 3)
    need = target_T - T0
    if need <= 0 or need % 2: return T0, need
    k = need // 2
    quads = [i for i in idx if len(F[i][0]) == 4]
    cent = {i: np.mean([P(j) for j in F[i][0]], 0) for i in quads}
    # pair mirror quads
    used = set(); pairs = []
    for i in sorted(quads, key=lambda i: -nonplanarity(F[i][0])):
        if i in used: continue
        c = cent[i]
        if abs(c[0]) < 1e-4:
            pairs.append((i,)); used.add(i); continue
        mc = c * np.array([-1, 1, 1])
        j = min((q for q in quads if q not in used and q != i), key=lambda q: np.linalg.norm(cent[q] - mc))
        used |= {i, j}; pairs.append((i, j))
    chosen = []
    for pr in pairs:
        if len(chosen) + len(pr) <= k: chosen += list(pr)
        if len(chosen) == k: break
    new = []
    for i in chosen:
        f, reg, mat = F[i]
        p = [P(j) for j in f]
        # split along the diagonal that makes the fold read (shorter diagonal)
        if np.linalg.norm(p[0] - p[2]) <= np.linalg.norm(p[1] - p[3]):
            new += [[[f[0], f[1], f[2]], reg, mat], [[f[0], f[2], f[3]], reg, mat]]
        else:
            new += [[[f[0], f[1], f[3]], reg, mat], [[f[1], f[2], f[3]], reg, mat]]
    for i in sorted(chosen, reverse=True): F.pop(i)
    F.extend(new)
    return T0, need


PRE = {}
for reg, (tq, tt) in TARGET.items():
    idx = [f for f in F if f[1] == reg]
    PRE[reg] = (sum(len(f[0]) == 4 for f in idx), sum(len(f[0]) == 3 for f in idx))
    split_to_target(reg, tt)

K_CAO = (1.65 / 1.752) if NU else 1.0   # spec: nam 1,75 m · nữ 1,65 m — co đều toàn thân (topology giữ nguyên)
BODY = dict(V=[list(map(float, np.asarray(v) * K_CAO)) for v in V], F=F, pre=PRE, target=TARGET)

# ================================================================== HAIR_SHORT_01 (authored in HAIR_SOCKET space)
SOCKET = np.array([0.0, HYC, 1.640])   # head-centre-ish, parented to head
V2 = []; F2 = []


def hv(p): V2.append(np.array(p, float)); return len(V2) - 1


def hf(f, g): F2.append([list(f), g, 2])


HEAD_H = POLE_Z - 1.545
OFF = 0.0075 * HEAD_H          # 0.75% head height cap offset (spec 0.5-1.0%)


def hpt(a, z, thick):
    p = scalp(a, min(z, POLE_Z - 1e-4))
    radial = np.array([p[0], p[1] - HYC, 0.0]); rn = np.linalg.norm(radial)
    up = (z - 1.62) / (POLE_Z - 1.62)
    nrm = radial / (rn + 1e-9) * (1 - up) + np.array([0, 0, 1.0]) * up
    nrm /= np.linalg.norm(nrm)
    return p + nrm * (OFF + thick) - SOCKET


SW = math.radians(14)   # swept to the character's right
hpole = hv(np.array([0, HYC + .004, POLE_Z + OFF + .016]) - SOCKET)
A8 = [2 * math.pi * k / 8 + math.pi / 8 for k in range(8)]
H1 = [hv(hpt(a, 1.744, .017)) for a in A8]
H2 = [hv(hpt(a + SW * .3, 1.728, .019)) for a in A8]
H3 = [hv(hpt(a + SW * .5, 1.705, .020)) for a in A8]
for k in range(8): hf([H1[k], H1[(k + 1) % 8], hpole], 'crown')
for R1, R2 in ((H1, H2), (H2, H3)):
    for k in range(8): hf([R1[k], R1[(k + 1) % 8], R2[(k + 1) % 8], R2[k]], 'crown')
# H4: 12 verts; front hairline higher
A12 = [2 * math.pi * k / 12 for k in range(12)]


def zline(a, zf, zb):
    c = math.cos(a); return zb + (zf - zb) * (0.5 + 0.5 * c)


H4 = [hv(hpt(a + SW * .7, zline(a, 1.700, 1.668), .018)) for a in A12]
# band H3(8)->H4(12): 8 quads + 4 tris via insertion pattern (zipper)
i = j = 0
pa = [(a + SW * .5) % (2 * math.pi) for a in A8]; pb = [(a + SW * .7) % (2 * math.pi) for a in A12]
order = sorted([(p, 'A', k) for k, p in enumerate(pa)] + [(p, 'B', k) for k, p in enumerate(pb)])
# simple explicit: each H3 edge k spans H4 verts; build by angular ownership
own = {}
for kb, p in enumerate(pb):
    ka = max([k for k in range(8) if pa[k] <= p] or [7])
    own.setdefault(ka, []).append(kb)
for k in range(8):
    bs = sorted(own.get(k, []), key=lambda b: (pb[b] - pa[k]) % (2 * math.pi))
    nxt_first = sorted(own.get((k + 1) % 8, []), key=lambda b: (pb[b] - pa[(k + 1) % 8]) % (2 * math.pi))
    a0, a1 = H3[k], H3[(k + 1) % 8]
    chain = [H4[b] for b in bs] + [H4[nxt_first[0]]] if nxt_first else [H4[b] for b in bs]
    # fan: tris for extra, last quad
    for t in range(len(chain) - 2):
        hf([a0, chain[t + 1], chain[t]], 'side_rear')
    hf([a0, a1, chain[-1], chain[-2]], 'side_rear')
# H5 (12 verts, cols 1..10 i.e. not the 2 front columns 11,0)
H5 = {k: hv(hpt(A12[k] + SW, zline(A12[k], 1.655, 1.600) - (0.012 if k in (2, 10) else 0), .014)) for k in range(1, 12)}
for k in range(1, 11):
    hf([H4[k], H4[k + 1], H5[k + 1], H5[k]], 'side_rear')
# clump tips (built after the rim: they hang from the inner rim edge so every edge stays manifold)
TIPS = []
for k in range(1, 11):
    m = (P2 := None)
    a = (A12[k] + A12[k + 1]) / 2 + SW * 1.3
    TIPS.append((k, a))
# front swept fringe: H4 verts 11,0,1 -> 3 rows swept to character's right (-x)
fr = [H4[11], H4[0], H4[1]]
rows = []
for r_, (dz, dx, th) in enumerate([(-.010, -.010, .016), (-.020, -.022, .013), (-.028, -.036, .010)]):
    rows.append([hv(V2[i] + np.array([dx, -0.007 * (r_ + 1), dz]) * np.array([1, 1, 1])) for i in fr])
prev = fr
for rr in rows:
    hf([prev[0], prev[1], rr[1], rr[0]], 'front'); hf([prev[1], prev[2], rr[2], rr[1]], 'front'); prev = rr
t1 = hv((V2[prev[0]] + V2[prev[1]]) / 2 + np.array([-.016, -.012, -.014]))
t2 = hv((V2[prev[1]] + V2[prev[2]]) / 2 + np.array([-.012, -.012, -.010]))
hf([prev[0], prev[1], t1], 'front'); hf([prev[1], prev[2], t2], 'front')
# side wings of fringe (connect fringe edge to H5 at cols 1 and 11)
hf([H4[1], rows[0][2], H5[1]], 'front'); hf([H4[11], rows[0][0], H5[11]], 'front')
hf([rows[0][2], rows[1][2], H5[1]], 'front'); hf([rows[0][0], rows[1][0], H5[11]], 'front')
# underside rim: inward lip from H5 ring (cols 1..11) to scalp-offset ring
U = {k: hv(hpt(A12[k] + SW, zline(A12[k], 1.660, 1.606) + 0.006, 0.0)) for k in range(1, 12)}
for k in range(1, 11):
    hf([H5[k], H5[k + 1], U[k + 1], U[k]], 'rim')
for k, a in TIPS:
    tip = hv(hpt(a, zline(a, 1.640, 1.585) - 0.012, .012))
    hf([U[k], U[k + 1], tip], 'side_rear')

HAIR_TARGET = {'crown': (16, 8), 'side_rear': (16, 8), 'front': (12, 12), 'rim': (4, 4)}
HAIR = dict(V=[list(map(float, np.asarray(v) * K_CAO)) for v in V2], F=F2, socket=list(map(float, SOCKET * K_CAO)), target=HAIR_TARGET,
            off=OFF, head_h=HEAD_H)

if __name__ == '__main__':
    out = sys.argv[1] if len(sys.argv) > 1 else 'geometry.json'
    cam = {('cam_L' if s > 0 else 'cam_R'): dict(vi_tri=list(map(float, c * K_CAO)), len=list(map(float, a)), r=r) for s, (c, a, r) in CAM.items()}
    KHOP.update(chau=np.array([0, 0, 0.88]), bung=np.array([0, 0, 1.02]), nguc=np.array([0, 0, 1.20]), co=np.array([0, 0.004, 1.47]),
                dau=np.array([0, HYC, 1.55]), dinh_dau=np.array([0, HYC, POLE_Z]))
    khop = {k: list(map(float, np.asarray(v) * K_CAO)) for k, v in KHOP.items()}
    json.dump(dict(body=BODY, hair=HAIR, socket=cam, khop=khop), open(out, 'w'))
    from collections import Counter
    for reg in TARGET:
        fl = [f for f in F if f[1] == reg]
        q = sum(len(f[0]) == 4 for f in fl); t = sum(len(f[0]) == 3 for f in fl)
        print(f"{reg:7s} Q{q:4d} T{t:4d} render {2*q+t:4d}   target Q{TARGET[reg][0]} T{TARGET[reg][1]} "
              f"render {2*TARGET[reg][0]+TARGET[reg][1]}  pre-split {PRE[reg]}")
    for g in HAIR_TARGET:
        fl = [f for f in F2 if f[1] == g]
        q = sum(len(f[0]) == 4 for f in fl); t = sum(len(f[0]) == 3 for f in fl)
        print(f"hair {g:9s} Q{q} T{t} render {2*q+t}  target {HAIR_TARGET[g]}")

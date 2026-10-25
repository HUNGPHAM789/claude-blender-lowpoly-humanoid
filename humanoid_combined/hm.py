#!/usr/bin/env python3
"""HM — COMBINED low-poly origami humanoid (Boss 22/10/2026: «gộp 3 spec: của mình, chi tiết, và rút gọn»).

Backbone = LPM (A): continuous ring-lofted torso from a SECTION TABLE, separate closed limb parts, sockets + .json
contract, Y-up GLB, measured gates that fail the build.  Detailed spec (B) gives the chi_tiet budgets, face and
5-finger hand.  Simplified concept (C) gives the rut_gon body form + glutes, simple face and budgets.

Two tiers (see SKILL.md):
  rut_gon   isometric game, ~1,100–1,300 render tris — simplified body/glutes, LPM grip hand, simple face (or --faceless)
  chi_tiet  ~2,300–2,500 render tris — detailed budgets, 5-finger hand, detailed face

Usage:
  python3 hm.py --tier rut_gon|chi_tiet --gioi nam|nu --out <dir>/<name> [--faceless] [--co 0..1] [--hair none|short|bob]
  ⇒ <name>.glb (body), <name>.json (contract + counts), [<name>_HAIR.glb], then runs hm_check.py — any gate red ⇒ exit 1.
Coords while building: metres, Z-up, feet at z=0, character faces −Y.  GLB is Y-up (glTF).
"""
import argparse, json, math, os, subprocess, sys
import numpy as np, trimesh
from scipy.spatial import ConvexHull
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hand as tay   # LPM grip hand (copied verbatim from lpm-faceless-humanoid/hand.py)

# ============================================================== LANDMARKS (metres, at the working height)
# Heights from the detailed spec (male 1.75, female 1.65, ≈7.5 heads).  Limb lengths are measured ALONG the
# segment (A-pose 25°).  Everything else (sockets, joints) is derived from this table — no free-floating numbers.
LANDMARK = {
 "nam": dict(H=1.75, dinh=1.750, cam=1.515, co_day=1.463, vai_tren=1.415, vai=(0.172, 0.008, 1.380),
             canh_tay=0.292, cang_tay=0.258, hang=(0.089, 0.010, 0.875), day_chau=0.817, goi=0.486, co_chan=0.083),
 "nu":  dict(H=1.65, dinh=1.650, cam=1.428, co_day=1.380, vai_tren=1.334, vai=(0.150, 0.007, 1.302),
             canh_tay=0.282, cang_tay=0.246, hang=(0.090, 0.013, 0.830), day_chau=0.775, goi=0.458, co_chan=0.078),
}
GOC_TAY = math.radians(25)            # A-pose arm angle (LPM 25°; detailed spec "about 20°")

# ============================================================== TIERS
TIER = {
 "rut_gon":  dict(budget=(1100, 1300), budget_faceless=(950, 1200), arm_n=6, leg_n=8, neck_n=6, foot_n=6,
                  # render-tri budget per region (simplified-derived; hands = LPM grip hand)
                  regions=dict(head=185, neck=24, torso=260, arms=170, hands=150, legs=250, feet=72)),
 "chi_tiet": dict(budget=(2300, 2500), budget_faceless=(2150, 2400), arm_n=8, leg_n=10, neck_n=8, foot_n=8,
                  regions=dict(head=296, neck=56, torso=480, arms=352, hands=612, legs=480, feet=160)),
}

# ============================================================== TORSO SECTION TABLES (reference 1.80 m, × H/1.80)
# (name, z, half-width X, half-depth Y, centre Y, {angle°: radial push}, [{angle°: z offset m}])
# angle 0 = mid-chest (−Y), 180 = mid-back; one entry applies to ± sides.  Pushes are BUMPS of width 15°, so the
# 14-vertex LPM ring reproduces the LPM table exactly and denser rings get the same shape.
W_BOTTOM = {0: 0.010, 30: 0.030, 60: 0.035, 90: 0.040, 120: 0.020, 150: -0.012, 165: -0.010, 180: 0.030}  # «W» crotch rim
THAN = {
 # rut_gon female = simplified test table (Boss: «body form đẹp, với mông chuẩn»)
 ("rut_gon", "nu"): [
  ("co_day",   1.505, 0.060, 0.055, 0.010, {}),
  ("vai",      1.455, 0.165, 0.082, 0.010, {0: 0.85, 180: 0.92}),
  ("nguc",     1.355, 0.152, 0.118, -0.010, {0: 0.86, 30: 1.12, 60: 1.04, 180: 0.90}),
  ("duoi_nguc", 1.270, 0.132, 0.096, 0.004, {180: 0.89}),
  ("eo",       1.150, 0.114, 0.084, 0.008, {180: 0.86}),
  ("hong",     0.960, 0.186, 0.114, 0.022, {150: 1.04, 180: 0.94}),
  ("mong",     0.905, 0.180, 0.126, 0.030, {150: 1.10, 165: 1.06, 180: 0.86}),
  ("mong_duoi", 0.872, 0.172, 0.122, 0.030, {0: 0.92, 150: 1.12, 165: 1.07, 180: 0.84}),
  ("day_chau", 0.845, 0.146, 0.100, 0.024, {0: 0.85, 150: 1.05, 180: 0.80}, W_BOTTOM),
 ],
 # rut_gon male = LPM male rows in the simplified 8-row layout (+ simplified glute_low row, male-strength pushes)
 ("rut_gon", "nam"): [
  ("co_day",   1.505, 0.070, 0.062, 0.010, {}),
  ("vai",      1.455, 0.185, 0.090, 0.010, {0: 0.85, 180: 0.92}),
  ("nguc",     1.360, 0.170, 0.112, -0.004, {0: 0.93, 30: 1.03, 180: 0.90}),
  ("duoi_nguc", 1.260, 0.155, 0.103, 0.001, {180: 0.89}),
  ("eo",       1.140, 0.138, 0.094, 0.006, {180: 0.88}),
  ("hong",     0.955, 0.176, 0.110, 0.016, {150: 1.03, 180: 0.94}),
  ("mong",     0.895, 0.170, 0.118, 0.024, {150: 1.07, 165: 1.04, 180: 0.88}),
  ("mong_duoi", 0.866, 0.162, 0.114, 0.024, {0: 0.92, 150: 1.08, 165: 1.05, 180: 0.86}),
  ("day_chau", 0.840, 0.150, 0.098, 0.018, {0: 0.85, 150: 1.04, 180: 0.80}, W_BOTTOM),
 ],
 # chi_tiet = LPM 9-row tables densified to 12 rows (armpit, belly, glute_low added)
 ("chi_tiet", "nam"): [
  ("co_day",   1.505, 0.070, 0.062, 0.010, {}),
  ("vai",      1.455, 0.185, 0.090, 0.010, {0: 0.85, 180: 0.92}),
  ("nach",     1.410, 0.180, 0.104, 0.002, {0: 0.90, 30: 1.02, 180: 0.91}),
  ("nguc",     1.360, 0.170, 0.112, -0.004, {0: 0.93, 30: 1.03, 180: 0.90}),
  ("duoi_nguc", 1.270, 0.158, 0.104, 0.000, {180: 0.90}),
  ("bung",     1.200, 0.148, 0.098, 0.003, {180: 0.89}),
  ("eo",       1.130, 0.140, 0.094, 0.006, {180: 0.88}),
  ("mao_chau", 1.035, 0.158, 0.100, 0.008, {}),
  ("hong",     0.955, 0.176, 0.110, 0.016, {150: 1.03, 180: 0.94}),
  ("mong",     0.893, 0.170, 0.118, 0.024, {150: 1.07, 165: 1.04, 180: 0.88}),
  ("mong_duoi", 0.865, 0.162, 0.114, 0.024, {0: 0.92, 150: 1.08, 165: 1.05, 180: 0.86}),
  ("day_chau", 0.840, 0.150, 0.098, 0.018, {0: 0.85, 150: 1.04, 180: 0.80}, W_BOTTOM),
 ],
 ("chi_tiet", "nu"): [
  ("co_day",   1.505, 0.060, 0.055, 0.010, {}),
  ("vai",      1.455, 0.165, 0.082, 0.010, {0: 0.85, 180: 0.92}),
  ("nach",     1.405, 0.158, 0.105, -0.002, {0: 0.88, 30: 1.06, 180: 0.91}),
  ("nguc",     1.355, 0.152, 0.118, -0.010, {0: 0.86, 30: 1.12, 60: 1.04, 180: 0.90}),
  ("duoi_nguc", 1.285, 0.140, 0.098, 0.004, {180: 0.90}),
  ("bung",     1.215, 0.126, 0.090, 0.006, {180: 0.88}),
  ("eo",       1.150, 0.116, 0.085, 0.008, {180: 0.86}),
  ("mao_chau", 1.045, 0.160, 0.102, 0.012, {}),
  ("hong",     0.960, 0.186, 0.114, 0.022, {150: 1.04, 180: 0.94}),
  ("mong",     0.905, 0.180, 0.126, 0.030, {150: 1.10, 165: 1.06, 180: 0.86}),
  ("mong_duoi", 0.872, 0.172, 0.122, 0.030, {0: 0.92, 150: 1.12, 165: 1.07, 180: 0.84}),
  ("day_chau", 0.845, 0.146, 0.100, 0.024, {0: 0.85, 150: 1.05, 180: 0.80}, W_BOTTOM),
 ],
}
_HALF = {"rut_gon": [0, 30, 60, 90, 120, 150, 165, 180],                       # 14 verts/ring (LPM)
         "chi_tiet": [0, 20, 40, 60, 80, 100, 120, 140, 152, 165, 180]}        # 20 verts/ring
GOC_THAN = {k: v + [360 - g for g in reversed(v[1:-1])] for k, v in _HALF.items()}


def bump(keo, g, w=15.0):
    """radial factor at angle g from keyed bumps (symmetric ±): Σ (f−1)·max(0, 1−|Δ|/w)."""
    g = abs(((g + 180) % 360) - 180); f = 1.0
    for k, v in keo.items():
        d = abs(g - k)
        if d < w: f += (v - 1.0) * (1 - d / w)
    return f


def vong(z, nr, ns, yc, keo, goc, dz=None, p=2.6):
    pts = []
    for g in goc:
        t = math.radians(g); s_, c = math.sin(t), math.cos(t)
        x = nr * math.copysign(abs(s_) ** (2 / p), s_); y = -ns * math.copysign(abs(c) ** (2 / p), c)
        f = bump(keo, g); zz = z + (bump({k: 1 + v for k, v in dz.items()}, g) - 1 if dz else 0.0)
        pts.append((x * f, yc + y * f, zz))
    return pts


def loft(rings, cap0, cap1):
    """rings of equal size → closed mesh; fan caps to points cap0 (first ring) and cap1 (last ring)."""
    n = len(rings[0]); V, F, idx = [], [], []
    for r in rings:
        i0 = len(V); V += [tuple(map(float, p)) for p in r]; idx.append(list(range(i0, i0 + n)))
    for a, b in zip(idx[:-1], idx[1:]):
        for k in range(n):
            a0, a1, b0, b1 = a[k], a[(k + 1) % n], b[k], b[(k + 1) % n]
            F += [(a0, b0, a1), (a1, b0, b1)]
    i0 = len(V); V.append(tuple(map(float, cap0))); i1 = len(V); V.append(tuple(map(float, cap1)))
    for k in range(n):
        F.append((idx[0][(k + 1) % n], i0, idx[0][k])); F.append((idx[-1][k], i1, idx[-1][(k + 1) % n]))
    m = trimesh.Trimesh(np.array(V, float), np.array(F), process=True); m.fix_normals(); return m


def khoi(pts):
    pts = np.array(pts, float); h = ConvexHull(pts)
    m = trimesh.Trimesh(pts, h.simplices, process=True); m.fix_normals(); return m


def khung(truc):
    """fixed frame for rings around an axis: a = world-X-ish (lateral), b = the rest.  SAME a for every ring of a
    limb ⇒ ring phase is aligned (the simplified build alternated phase per ring ⇒ «xoắn thịt» spiral bands)."""
    t = np.array(truc, float); t /= np.linalg.norm(t)
    ref = np.array((0, 1.0, 0)) if abs(t[1]) < 0.9 else np.array((0, 0, 1.0))
    a = np.cross(ref, t); a /= np.linalg.norm(a); b = np.cross(t, a); return t, a, b


def vong_truc(c, t, a, b, rx, ry, n, keo=None):
    return [np.asarray(c, float) + (keo or {}).get(k, 1.0) * (rx * math.cos(2 * math.pi * k / n) * a + ry * math.sin(2 * math.pi * k / n) * b)
            for k in range(n)]


def chi(p0, p1, tram, n, t_override=None):
    """limb segment loft p0→p1. tram = [(t along 0..1 (may be <0 / >1), rx, ry, {k: push})]; ONE frame for all rings."""
    p0, p1 = np.asarray(p0, float), np.asarray(p1, float); L = p1 - p0
    t, a, b = khung(L if t_override is None else t_override)
    rings = [vong_truc(p0 + L * u, t, a, b, rx, ry, n, keo) for (u, rx, ry, *k) in tram for keo in [k[0] if k else None]]
    c0 = p0 + L * (tram[0][0] - 0.03); c1 = p0 + L * (tram[-1][0] + 0.03)
    return loft(rings, c0, c1)


# ============================================================== HEADS (head-local, built Z-up then fitted to landmarks)
# rut_gon face = simplified (C) loft head, 10 verts × 8 rings, dark eye quads.
LPS_ANG = [0, 18, 45, 80, 125, 180, 235, 280, 315, 342]
LPS_RINGS = [  # z (chin=0), half-width, depth front, depth back, push, [dz]
    (0.000, 0.020, 0.068, 0.012, {0: 1.00}),
    (0.030, 0.044, 0.082, 0.048, {0: 0.97}),
    (0.062, 0.060, 0.086, 0.078, {0: 1.28, 18: 1.02, 45: 1.03}),
    (0.094, 0.066, 0.085, 0.095, {0: 1.15, 18: 0.95, 45: 0.96}),
    (0.112, 0.068, 0.087, 0.098, {0: 1.08, 18: 0.95, 45: 0.97}),
    (0.142, 0.070, 0.089, 0.101, {0: 1.00, 18: 1.02}),
    (0.182, 0.069, 0.079, 0.099, {}),
    (0.216, 0.052, 0.054, 0.074, {}),
]


def _sym(d, g):
    g = abs(((g + 180) % 360) - 180)
    for k, v in d.items():
        if abs(g - k) < 1.0: return v
    return 1.0


def _ring_fb(z, w, df, db, yc, push, angles, p=2.4):
    out = []
    for g in angles:
        t = math.radians(g); s_, c = math.sin(t), math.cos(t); d = df if c >= 0 else db
        x = w * math.copysign(abs(s_) ** (2 / p), s_); y = -d * math.copysign(abs(c) ** (2 / p), c); f = _sym(push, g)
        out.append((x * f, yc + y * f, z))
    return out


def head_lps():
    rings = [_ring_fb(z, w, df, db, 0.0, pu, LPS_ANG) for (z, w, df, db, pu) in LPS_RINGS]
    m = loft(rings, (0, 0.030, 0.018), (0, 0.010, 0.236))
    n = len(LPS_ANG)
    eyes = {}
    for side, ks in (("L", (1,)), ("R", (8,))):        # band 3→4, segments 18→45 (char. left = +x) and 315→342
        pts = []
        for k in ks:
            for r in (3, 4):
                pts += [rings[r][k], rings[r][(k + 1) % n]]
        eyes[side] = np.array(pts)
    ears = [khoi([(sx * x, y, z) for x, y, z in ((0.064, 0.000, 0.126), (0.064, 0.030, 0.118), (0.079, 0.016, 0.120),
                                                  (0.081, 0.030, 0.100), (0.074, 0.022, 0.078), (0.064, 0.006, 0.080),
                                                  (0.064, 0.034, 0.094))]) for sx in (1, -1)]
    return m, eyes, ears, 0.236


# chi_tiet face = detailed (B) head: 16 non-uniform columns × 8 rings + crown pole, feature offsets
D_ANG = [0, 16, 34, 55, 80, 105, 130, 155, 180, 205, 230, 255, 280, 305, 326, 344]
D_RINGS = [(0.000, .058, .062, .050), (0.025, .063, .086, .072), (0.052, .066, .094, .086), (0.078, .071, .096, .095),
           (0.102, .076, .095, .100), (0.122, .078, .094, .104), (0.146, .078, .095, .104), (0.182, .066, .080, .090)]
D_POLE = 0.212
D_FEAT = {(3, 0): (-.021, 0), (4, 0): (-.014, 0), (5, 0): (-.007, 0), (6, 0): (-.004, 0),
          (2, 0): (-.004, 0), (2, 1): (.004, 0), (2, 15): (.004, 0),
          (1, 0): (-.010, -.004), (1, 1): (-.004, 0), (1, 15): (-.004, 0),
          (4, 2): (.010, 0), (4, 14): (.010, 0), (5, 2): (.012, 0), (5, 14): (.012, 0),
          (4, 1): (.006, 0), (4, 15): (.006, 0), (5, 1): (.004, 0), (5, 15): (.004, 0),
          (6, 1): (-.006, .002), (6, 15): (-.006, .002), (6, 2): (-.008, .002), (6, 14): (-.008, .002),
          (3, 3): (-.008, 0), (3, 13): (-.008, 0), (4, 3): (-.010, 0), (4, 13): (-.010, 0),
          (1, 3): (0, -.004), (1, 13): (0, -.004), (1, 4): (.004, -.008), (1, 12): (.004, -.008)}


def head_detailed():
    yc = -0.012; rings = []
    for ri, (z, w, df, db) in enumerate(D_RINGS):
        r = []
        for k, g in enumerate(D_ANG):
            a = math.radians(g); s_, c = math.sin(a), math.cos(a); d = df if c >= 0 else db
            p = np.array((w * math.copysign(abs(s_) ** (2 / 2.4), s_), yc - d * math.copysign(abs(c) ** (2 / 2.4), c), z))
            if (ri, k) in D_FEAT:
                dy, dz_ = D_FEAT[(ri, k)]
                if k == 0: p[1] += dy
                else: p -= np.array((math.sin(a), -math.cos(a), 0)) * dy
                p[2] += dz_
            r.append(p)
        rings.append(r)
    m = loft(rings, (0, yc, 0.012), (0, yc + 0.008, D_POLE))
    eyes = {"L": np.array([rings[4][1], rings[4][2], rings[5][1], rings[5][2]]),
            "R": np.array([rings[4][14], rings[4][15], rings[5][14], rings[5][15]])}
    ears = []
    for sx in (1, -1):
        c = np.array((sx * 0.079, 0.010, 0.100)); P = []
        for a in (90, 30, -30, -90, -150, 150):
            t = math.radians(a)
            P.append(c + (-sx * .006, .016 * math.cos(t), .026 * math.sin(t)))
            P.append(c + (sx * .012, .019 * math.cos(t) + .004, .030 * math.sin(t)))
        ears.append(khoi(P))
    return m, eyes, ears, D_POLE


# faceless = LPM gem head (A), 48 tris incl. forehead; LPM absolute coords → local (chin = 0)
LPM_GEM = [(0, 0.015, 1.800), (0.072, 0.005, 1.775), (-0.072, 0.005, 1.775), (0, 0.098, 1.745), (0.078, 0.07, 1.70),
           (-0.078, 0.07, 1.70), (0, -0.092, 1.725), (0.062, -0.082, 1.722), (-0.062, -0.082, 1.722),
           (0, -0.116, 1.658), (0.016, -0.100, 1.645), (-0.016, -0.100, 1.645), (0.070, -0.066, 1.665), (-0.070, -0.066, 1.665),
           (0.082, 0.0, 1.668), (-0.082, 0.0, 1.668), (0.088, 0.012, 1.650), (-0.088, 0.012, 1.650),
           (0.058, 0.075, 1.618), (-0.058, 0.075, 1.618), (0.060, -0.032, 1.585), (-0.060, -0.032, 1.585),
           (0, -0.083, 1.568), (0.024, -0.074, 1.562), (-0.024, -0.074, 1.562),
           (0, -0.086, 1.768), (0.050, -0.074, 1.764), (-0.050, -0.074, 1.764), (0, -0.060, 1.792), (0.040, -0.050, 1.788), (-0.040, -0.050, 1.788)]


def head_gem(gioi):
    h = 0.92 if gioi == "nu" else 1.0
    P = [((x * h if z < 1.60 else x), y, z - 1.562) for x, y, z in LPM_GEM]
    return khoi(P), {}, [], 1.800 - 1.562


def fit_head(parts, hh_local, LM, gioi):
    """uniform scale so chin→top = LM dinh − cam; chin at LM cam.  Female heads 4 % narrower."""
    k = (LM["dinh"] - LM["cam"]) / hh_local
    T = np.diag([k * (0.96 if gioi == "nu" else 1.0), k, k, 1.0]); T[2, 3] = LM["cam"]
    for m in parts: m.apply_transform(T)
    return k


# ============================================================== 5-FINGER HAND (chi_tiet, detailed spec B)
FINGERS = [  # name, v offset at knuckle (+v = thumb side), length, base radius, tip radius
    ("ngon_tro", 0.026, 0.076, 0.0090, 0.0062), ("ngon_giua", 0.009, 0.084, 0.0094, 0.0064),
    ("ngon_ap", -0.009, 0.079, 0.0090, 0.0060), ("ngon_ut", -0.026, 0.063, 0.0080, 0.0054)]


def _finger(base, d0, n_axis, v_axis, L, r0, r1, segs, curl):
    """6-sided finger: rings at knuckle + each joint, flexing toward +n by `curl` rad per joint. One fixed lateral axis
    (v) per finger ⇒ ring phase aligned.  Returns closed mesh (base cap sits inside the palm)."""
    rings, pos, d = [], np.asarray(base, float), np.asarray(d0, float)
    frac = np.cumsum([0] + segs)
    for i, f in enumerate(frac):
        if i > 0:
            pos = pos + d * L * segs[i - 1]
            d = np.cos(curl) * d + np.sin(curl) * n_axis; n_axis = np.cross(d, v_axis) * -1 if False else n_axis - d * np.dot(n_axis, d)
            n_axis /= np.linalg.norm(n_axis)
        r = r0 + (r1 - r0) * f
        b = np.cross(d, v_axis); b /= np.linalg.norm(b); a = np.cross(b, d)
        rings.append([pos + r * math.cos(2 * math.pi * k / 6) * a + r * 0.85 * math.sin(2 * math.pi * k / 6) * b for k in range(6)])
    return loft(rings, rings[0][0] * 0 + np.mean(rings[0], axis=0) - d0 * 0.004, pos + d * 0.006)


def hand5(co, s, nu):
    """local (u along forearm, v thumb side, n palm normal) parts {name: mesh in local coords}."""
    k = s * (0.92 if nu else 1.0)
    u, v, n = np.eye(3)
    parts = {}
    rings = []
    for (uu, w, th, nc) in ((0.000, 0.028, 0.014, 0.0), (0.040, 0.037, 0.016, 0.002), (0.078, 0.042, 0.013, 0.001), (0.094, 0.040, 0.010, 0.0)):
        rings.append([k * (uu * u + w * math.cos(2 * math.pi * j / 8) * v + (th * math.sin(2 * math.pi * j / 8) + nc) * n) for j in range(8)])
    parts["ban_tay"] = loft(rings, k * (-0.008 * u), k * (0.100 * u))
    curl = math.radians(8 + 75 * co)
    for name, vo, L, r0, r1 in FINGERS:
        base = k * (0.082 * u + vo * v)
        d0 = u + v * (vo * 0.6)
        d0 /= np.linalg.norm(d0)
        parts[name] = _finger(base, d0, n.copy(), v, L * k, r0 * k, r1 * k, [0.45, 0.30, 0.25], curl)
    tb = k * (0.024 * u + 0.030 * v + 0.006 * n)
    td = np.array((0.60, 0.62, 0.40 + 0.5 * co)); td /= np.linalg.norm(td)
    parts["ngon_cai"] = _finger(tb, td, n.copy(), np.cross(n, td) / np.linalg.norm(np.cross(n, td)), 0.066 * k, 0.0110 * k, 0.0075 * k, [0.55, 0.45], math.radians(6 + 40 * co))
    return parts


# ============================================================== BUILD
def build(tier, gioi, faceless, co):
    TI = TIER[tier]; LM = LANDMARK[gioi]; H = LM["H"]; s = H / 1.80
    bo, sk, vung = {}, {}, {}           # parts, sockets, region of each part

    def add(name, m, region):
        bo[name] = m; vung[name] = region

    # ---- torso: continuous ring loft from the per-tier section table (LPM backbone)
    goc = GOC_THAN[tier]; bang = THAN[(tier, gioi)]
    ds = [vong(z * s, nr * s, ns * s, yc * s, r[0], goc, ({g: d * s for g, d in r[1].items()} if len(r) > 1 else None))
          for (_, z, nr, ns, yc, *r) in bang]
    tren = np.mean(ds[0], axis=0) + (0, 0, 0.012 * s)
    duoi = np.mean(ds[-1], axis=0) + (0, -0.025 * s, 0.020 * s)
    add("than", loft(ds, tren, duoi), "torso")
    moc = {t: round(z * s, 4) for (t, z, *_) in bang}

    # ---- neck + head
    co_n = TI["neck_n"]
    tram_co = [(0, 0.050 * s, 0.047 * s), (1, 0.044 * s, 0.043 * s)] if tier == "rut_gon" else \
              [(0, 0.050 * s, 0.047 * s), (0.5, 0.047 * s, 0.045 * s), (1, 0.044 * s, 0.043 * s)]
    add("co", chi((0, 0.012 * s, LM["co_day"] - 0.04 * s), (0, 0.012 * s, LM["cam"] + 0.06 * s), tram_co, co_n), "neck")
    if faceless: hm, eyes, ears, hh = head_gem(gioi)
    elif tier == "rut_gon": hm, eyes, ears, hh = head_lps()
    else: hm, eyes, ears, hh = head_detailed()
    eye_m = {sd: trimesh.Trimesh(pts, ConvexHull(pts, qhull_options="QJ").simplices) for sd, pts in eyes.items()}
    k = fit_head([hm] + ears + list(eye_m.values()), hh, LM, gioi)
    add("dau", hm, "head")
    for sd, e in zip(("L", "R"), ears): add(f"tai_{sd}", e, "head")
    hz0, hz1 = hm.bounds[0][2], hm.bounds[1][2]; hcy = float(np.mean(hm.bounds[:, 1]))
    sk["dau"] = dict(vi_tri=(0, 0.012 * s, LM["cam"] + 0.03 * s), len=(0, 0, 1))
    sk["HAIR"] = dict(vi_tri=(0.0, hcy, hz0 + 0.55 * (hz1 - hz0)), len=(0, 0, 1))      # skull centre at brow height
    eye_meshes = {}
    for sd, e in eye_m.items():           # dark eye patch = copy of the socket faces pushed 0.6 mm out of the head
        c = e.vertices.mean(axis=0); nrm = c - np.array(sk["HAIR"]["vi_tri"]); nrm[2] = 0; nrm /= np.linalg.norm(nrm)
        flat = e.copy(); flat.vertices = e.vertices + nrm * 0.0006
        eye_meshes[f"mat_{sd}"] = flat

    # ---- arms, hands, legs, feet
    for ten, sx in (("L", 1), ("R", -1)):
        vai = np.array((sx * LM["vai"][0], LM["vai"][1], LM["vai"][2]))
        h = np.array((sx * math.sin(GOC_TAY), 0.0, -math.cos(GOC_TAY)))
        khuyu = vai + h * LM["canh_tay"]; co_tay = khuyu + h * LM["cang_tay"] + np.array((0, -0.012, 0)) * s
        r1 = (0.046 if gioi == "nam" else 0.040) * s; r2 = (0.036 if gioi == "nam" else 0.030) * s
        if tier == "rut_gon":
            ut = [(-0.10, r1 * 0.62, r1 * 0.66), (0.10, r1 * 1.0, r1 * 0.98), (0.55, r1 * 0.92, r1 * 0.88), (1.0, r1 * 0.68, r1 * 0.70)]
            ft = [(-0.06, r2 * 0.95, r2 * 0.92), (0.30, r2 * 1.02, r2 * 0.98), (0.70, r2 * 0.80, r2 * 0.70), (1.0, r2 * 0.66, r2 * 0.52)]
        else:
            ut = [(-0.10, r1 * 0.62, r1 * 0.66), (0.06, r1 * 0.98, r1 * 0.96), (0.22, r1 * 1.02, r1 * 0.98), (0.50, r1 * 0.92, r1 * 0.90),
                  (0.80, r1 * 0.80, r1 * 0.78), (1.0, r1 * 0.68, r1 * 0.70)]
            ft = [(-0.06, r2 * 0.95, r2 * 0.92), (0.15, r2 * 1.04, r2 * 1.0), (0.35, r2 * 1.02, r2 * 0.96), (0.70, r2 * 0.80, r2 * 0.70),
                  (1.0, r2 * 0.66, r2 * 0.52)]
        add(f"canh_tay_{ten}", chi(vai, khuyu, ut, TI["arm_n"]), "arms")
        add(f"cang_tay_{ten}", chi(khuyu, co_tay, ft, TI["arm_n"]), "arms")
        M, O = tay.khung_the_gioi(co_tay, h, sx)
        W = lambda p: O + M @ np.asarray(p, float)
        if tier == "rut_gon":     # LPM 5-block grip hand
            cuc_bo, khop_t, (tc, tt, tr) = tay.dung_tay(co, 1.0, nu=(gioi == "nu"))   # grip angles were solved at hand scale 1.0 (Ø32 grip does not scale) — keep it
            for tn, pts in cuc_bo.items(): add(f"{tn}_{ten}", khoi([W(p) for p in pts]), "hands")
            sk[f"cam_{ten}"] = dict(vi_tri=tuple(W(tc)), len=tuple(M @ tt), r=tr)
        else:                     # detailed 5-finger hand
            for tn, m in hand5(co, s, gioi == "nu").items():
                g = m.copy(); g.vertices = np.array([W(p) for p in m.vertices]); g.fix_normals(); add(f"{tn}_{ten}", g, "hands")
            sk[f"cam_{ten}"] = dict(vi_tri=tuple(W((0.076 * s, 0, 0.028 * s))), len=tuple(M @ np.array((0, 1.0, 0))), r=0.016)
        sk[f"ban_tay_{ten}"] = dict(vi_tri=tuple(co_tay), len=tuple(h))
        hang = np.array((sx * LM["hang"][0], LM["hang"][1], LM["hang"][2]))
        goi = np.array((sx * LM["hang"][0] * 0.96, -0.008 * s, LM["goi"]))
        ca = np.array((sx * LM["hang"][0] * 0.92, 0.018 * s, LM["co_chan"]))
        rd = (0.088 if gioi == "nam" else 0.092) * s; rb = (0.058 if gioi == "nam" else 0.054) * s
        p_top = hang + np.array((0, 0, 0.05)) * s
        kn = TI["leg_n"]; ki = kn // 4      # vertex index facing front (−Y) for knee-cap push
        if tier == "rut_gon":
            dt = [(0.0, rd * 0.90, rd * 0.94), (0.30, rd * 0.95, rd * 0.93), (0.60, rd * 0.80, rd * 0.80), (0.85, rd * 0.66, rd * 0.67), (1.0, rd * 0.58, rd * 0.60, {3 * kn // 4: 1.12})]
            ct = [(0.0, rb * 0.92, rb * 0.95, {3 * kn // 4: 1.10}), (0.28, rb, rb * 1.08), (0.65, rb * 0.74, rb * 0.78), (1.0, rb * 0.50, rb * 0.55)]
        else:
            dt = [(0.0, rd * 0.90, rd * 0.94), (0.18, rd * 0.99, rd * 0.97), (0.40, rd * 0.92, rd * 0.90), (0.62, rd * 0.80, rd * 0.80),
                  (0.84, rd * 0.66, rd * 0.67), (1.0, rd * 0.58, rd * 0.60, {3 * kn // 4: 1.12})]
            ct = [(0.0, rb * 0.92, rb * 0.95, {3 * kn // 4: 1.10}), (0.14, rb * 0.98, rb * 1.04), (0.32, rb, rb * 1.10),
                  (0.62, rb * 0.76, rb * 0.80), (0.86, rb * 0.56, rb * 0.60), (1.0, rb * 0.50, rb * 0.55)]
        add(f"dui_{ten}", chi(p_top, goi, dt, kn), "legs")
        add(f"cang_chan_{ten}", chi(goi, ca, ct, kn), "legs")
        # foot: loft along −Y from heel to toe (simplified r6 profile; chi_tiet 8-gon, 4 stations)
        nf = TI["foot_n"]
        prof = (lambda w, hgt: [(w * math.cos(2 * math.pi * j / nf), hgt * (0.5 + 0.5 * math.sin(2 * math.pi * j / nf))) for j in range(nf)])
        st = ([(0.035, 0.026, 0.070), (-0.030, 0.036, 0.088), (-0.120, 0.041, 0.034)] if tier == "rut_gon" else
              [(0.040, 0.025, 0.066), (0.0, 0.034, 0.090), (-0.060, 0.039, 0.064), (-0.125, 0.041, 0.032)])
        base = np.array((ca[0], ca[1], 0.0))
        rings = [[base + np.array((x, y * s, z)) * (1, 1, 1) * s if False else base + np.array((x * s, y * s, zz * s)) for (x, zz) in prof(w, hh_)]
                 for (y, w, hh_) in st]
        add(f"ban_chan_{ten}", loft(rings, base + np.array((0, 0.055, 0.030)) * s, base + np.array((sx * -0.004, -0.170, 0.012)) * s), "feet")
        sk[f"ban_chan_{ten}"] = dict(vi_tri=tuple(ca), len=(0, -1, 0))
    sk["lung"] = dict(vi_tri=(0, 0.12 * s, 1.30 * s), len=(0, 1, 0))
    sk["hong_L"] = dict(vi_tri=(0.17 * s, 0.0, 1.0 * s), len=(1, 0, 0))
    sk["hong_R"] = dict(vi_tri=(-0.17 * s, 0.0, 1.0 * s), len=(-1, 0, 0))
    day = min(m.bounds[0][2] for m in bo.values())
    for m in list(bo.values()) + list(eye_meshes.values()): m.apply_translation((0, 0, -day))
    for v in sk.values(): v["vi_tri"] = (v["vi_tri"][0], v["vi_tri"][1], v["vi_tri"][2] - day)
    moc = {t: round(z - day, 4) for t, z in moc.items()}
    return bo, sk, vung, eye_meshes, moc, dict(head_scale=round(k, 4), chin=LM["cam"] - day, head_top=float(hm.bounds[1][2]))


# ============================================================== HAIR (replaceable-assets recipe D)
HAIR_K = 1.032   # replaceable-assets recipe: scale the scalp facets ~3 % out about HAIR_SOCKET


def build_hair(head, socket, style, chin, top):
    """cap = the head's OWN facets above a hairline, scaled k=1.032 about HAIR_SOCKET (parallel copies of the scalp
    facets ⇒ cannot clip a star-shaped head).  bob = side/back boundary extruded down to below the chin."""
    K = HAIR_K; hh = top - chin; S = np.asarray(socket, float)
    cut = (lambda ang: 0.80 if ang < 40 else (0.60 if ang < 110 else 0.47)) if style == "short" else \
          (lambda ang: 0.80 if ang < 40 else 0.62)
    V = head.vertices; keep = []
    for fi, f in enumerate(head.faces):
        c = V[f].mean(axis=0); ang = abs(math.degrees(math.atan2(c[0], -(c[1] - S[1]))))
        if c[2] >= chin + cut(ang) * hh: keep.append(fi)
    cap = head.submesh([keep], append=True)
    cap.vertices = S + (cap.vertices - S) * K
    Vh = [tuple(p) for p in cap.vertices]; Fh = [tuple(f) for f in cap.faces]
    if style == "bob":
        e = np.sort(cap.edges, axis=1); u, cnt = np.unique(e, axis=0, return_counts=True); bnd = u[cnt == 1]
        drop = {}
        def low(i):
            if i not in drop:
                p = np.array(Vh[i]); r = p - S; r[2] = 0; r /= np.linalg.norm(r)
                drop[i] = len(Vh); Vh.append(tuple(p + np.array((0, 0, -(p[2] - (chin - 0.035)))) + r * 0.018))
            return drop[i]
        for a, b in bnd:
            pa, pb = cap.vertices[a], cap.vertices[b]
            ok = all(abs(math.degrees(math.atan2(p[0], -(p[1] - S[1])))) > 55 for p in (pa, pb))
            if ok: Fh += [(a, b, low(b)), (a, low(b), low(a))]
    m = trimesh.Trimesh(np.array(Vh), np.array(Fh), process=False)
    fn = m.face_normals; out = np.einsum("ij,ij->i", fn, m.triangles_center - S) < 0
    F2 = m.faces.copy(); F2[out] = F2[out][:, ::-1]
    return trimesh.Trimesh(m.vertices, F2, process=False)


def xuat(bo, sk, eyes, out, meta, hair=None):
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    Y = trimesh.transformations.rotation_matrix(-math.pi / 2, (1, 0, 0))
    def scene(parts, sockets):
        sc = trimesh.Scene()
        for ten, m in parts.items():
            g = m.copy(); g.apply_transform(Y); sc.add_geometry(g, node_name=ten, geom_name=ten)
        for ten, v in sockets.items():
            sc.graph.update(frame_to="SOCKET_" + ten, frame_from=sc.graph.base_frame, matrix=Y @ trimesh.transformations.translation_matrix(v["vi_tri"]))
        return sc
    scene({**bo, **eyes}, sk).export(out + ".glb")
    if hair is not None:
        scene({"HAIR_" + meta["hair"].upper(): hair}, {"HAIR": sk["HAIR"]}).export(out + "_HAIR.glb")
    json.dump(dict(meta, bo_phan=sorted(bo), mat=sorted(eyes),
                   socket={k: dict(vi_tri=[round(float(x), 4) for x in v["vi_tri"]], len=[round(float(x), 4) for x in v["len"]],
                                   **({"r": v["r"]} if "r" in v else {})) for k, v in sk.items()},
                   toa_do="m, Z-up, feet z=0, faces -Y (GLB: Y-up)"), open(out + ".json", "w"), ensure_ascii=False, indent=1)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--tier", required=True, choices=list(TIER)); ap.add_argument("--gioi", default="nam", choices=["nam", "nu"])
    ap.add_argument("--out", required=True); ap.add_argument("--faceless", action="store_true")
    ap.add_argument("--co", type=float, default=0.0, help="hand: 0 open, 1 grip Ø32 mm at socket cam_*")
    ap.add_argument("--hair", default="none", choices=["none", "short", "bob"])
    a = ap.parse_args()
    bo, sk, vung, eyes, moc, info = build(a.tier, a.gioi, a.faceless, a.co)
    hair = build_hair(bo["dau"], sk["HAIR"]["vi_tri"], a.hair, info["chin"], info["head_top"]) if a.hair != "none" else None
    dem = {}
    for ten, m in bo.items(): dem[vung[ten]] = dem.get(vung[ten], 0) + len(m.faces)
    meta = dict(tier=a.tier, gioi=a.gioi, cao=LANDMARK[a.gioi]["H"], faceless=a.faceless, co_tay=a.co, hair=a.hair,
                phien_ban="HM 1.0 (LPM 2.6 + detailed v1 + simplified)", moc_than=moc, landmark=LANDMARK[a.gioi],
                tris_vung=dem, tris_tong=sum(dem.values()), tris_mat=sum(len(m.faces) for m in eyes.values()),
                tris_toc=(len(hair.faces) if hair is not None else 0), vung=vung, **info)
    xuat(bo, sk, eyes, a.out, meta, hair)
    print(f"exported {a.out}.glb — {len(bo)} parts, {meta['tris_tong']} render tris {dem}" + (f", hair {len(hair.faces)} tris" if hair is not None else ""))
    rc = subprocess.call([sys.executable, os.path.join(os.path.dirname(os.path.abspath(__file__)), "hm_check.py"), a.out])
    sys.exit(rc)

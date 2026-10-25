#!/usr/bin/env python3
"""HM gates — run AUTOMATICALLY at the end of hm.py (any red ⇒ exit 1 ⇒ build fails).  Manual: python3 hm_check.py <out>
Reverse tests on foreign GLBs:   python3 hm_check.py --xoan <file.glb>      (ring-twist gate only)
                                  python3 hm_check.py --tay <file.glb>       (arm-length gate only)
Everything is measured on the EXPORTED files, never on the builder's intentions.

Ported from LPM check_lpm.py: ① watertight ③ height/floor ④ volume ⑤ continuous torso ⑥ contract ⑦ symmetry ⑧ waist
  ⑨ head facet density ⑩ light glutes ⑪ forehead ⑫ no-skirt «W» rim ⑮ grip (rut_gon / LPM hand)
NEW: ② per-tier triangle budget (+ per-region ±30 %) · ⑯ ring twist ≤ 8° on every lofted limb · ⑰ arm length
  shoulder→fingertip 0.42–0.45 H and fingertip height ≥ 0.38 H · ⑱ hair inside head 0/4,000 · ⑲ landmarks
"""
import json, math, os, sys
import numpy as np, trimesh

BAC_TOI_DA = 0.020
XOAN_MAX = 8.0                 # deg between consecutive rings
TAY_LH = (0.42, 0.45)          # shoulder corner → fingertip / height
TAY_TIP = (0.38, 0.47)         # fingertip height / height
Z = trimesh.transformations.rotation_matrix(math.pi / 2, (1, 0, 0))     # Y-up → Z-up


def doc_glb(path):
    sc = trimesh.load(path, force="scene"); bo = {}
    for node in sc.graph.nodes_geometry:
        T, g = sc.graph[node]; m = sc.geometry[g].copy(); m.apply_transform(Z @ T); bo[node] = m
    return bo


# ------------------------------------------------------------------ ⑯ ring twist (generic, works on any GLB)
def xoan_mot(m, gap=0.006):
    """max twist (deg) between consecutive rings of a lofted shell, measured from vertices only.
    Rings = clusters of vertices along the shell's principal axis (split at axial gaps > `gap`), modal size ≥ 5.
    Angle of each vertex about the ring centroid, normalised by the ring's spread on 2 fixed axes (undoes ellipse);
    twist(i→i+1) = mean over ring i+1 of the angular distance to the nearest vertex of ring i.  None = not a loft."""
    v = np.unique(np.round(m.vertices, 6), axis=0)
    c0 = v.mean(axis=0); _, _, Vt = np.linalg.svd(v - c0); ax = Vt[0]
    ext = np.ptp((v - c0) @ Vt.T, axis=0)
    if ext[0] < 0.15 or ext[0] / max(ext[1], 1e-6) < 2.5: return None
    t = (v - c0) @ ax; o = np.argsort(t); t = t[o]; v = v[o]
    cuts = np.where(np.diff(t) > gap)[0] + 1; groups = np.split(np.arange(len(v)), cuts)
    sizes = [len(g) for g in groups if len(g) >= 5]
    if not sizes: return None
    n = max(set(sizes), key=sizes.count); rings = [v[g] for g in groups if len(g) == n]
    if len(rings) < 3: return None
    e1 = np.array((1.0, 0, 0)) if abs(ax[0]) < 0.8 else np.array((0, 1.0, 0))
    e1 = e1 - ax * (e1 @ ax); e1 /= np.linalg.norm(e1); e2 = np.cross(ax, e1)
    angs = []
    for r in rings:
        d = r - r.mean(axis=0); x, y = d @ e1, d @ e2
        angs.append(np.degrees(np.arctan2(y / (np.std(y) + 1e-9), x / (np.std(x) + 1e-9))))
    worst = 0.0
    for a, b in zip(angs[:-1], angs[1:]):
        dd = np.abs(((b[:, None] - a[None, :]) + 180) % 360 - 180).min(axis=1)
        worst = max(worst, float(dd.mean()))
    return worst, n, len(rings)


def xoan_glb(path, ten_bo=None):
    bo = doc_glb(path); kq = {}
    for ten, m in bo.items():
        if ten_bo and not any(ten.startswith(p) for p in ten_bo): continue
        comps = m.split(only_watertight=False) if len(m.faces) > 400 else [m]
        for i, c in enumerate(comps):
            r = xoan_mot(c)
            if r: kq[f"{ten}#{i}" if len(comps) > 1 else ten] = r
    return kq


# ------------------------------------------------------------------ ⑰ arm length (generic)
def tay_glb(path):
    """shoulder = the upper-lateral CORNER of the front silhouette: max (x + z) over vertices with x>0, z<0.86 H
    (head excluded); fingertip = lowest vertex with x > 0.14 H.  Both from the merged mesh, any topology."""
    bo = doc_glb(path); v = np.vstack([m.vertices for k, m in bo.items() if not k.startswith(("mat_", "HAIR"))])
    lo = v[:, 2].min(); H = np.ptp(v[:, 2]); v = v.copy(); v[:, 2] -= lo
    R = v[v[:, 0] > 0]; arm = R[R[:, 0] > 0.14 * H]; tip = arm[np.argmin(arm[:, 2])]
    U = R[R[:, 2] < 0.86 * H]; sh = U[np.argmax(U[:, 0] + U[:, 2])]
    return float(np.linalg.norm(tip - sh) / H), float(tip[2] / H), sh, tip, H


def tay_ok(lh, tz):
    return TAY_LH[0] <= lh <= TAY_LH[1] and TAY_TIP[0] <= tz <= TAY_TIP[1]


def tia(m, o, d):
    """all hit distances t>0 of ray o + t·d against mesh m (Möller–Trumbore, numpy only — no rtree)."""
    tri = m.triangles; o = np.asarray(o, float); d = np.asarray(d, float) / np.linalg.norm(d)
    e1, e2 = tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0]
    pv = np.cross(d, e2); det = np.einsum("ij,ij->i", e1, pv); ok = np.abs(det) > 1e-12
    inv = np.where(ok, 1.0 / np.where(ok, det, 1), 0); tv = o - tri[:, 0]
    u = np.einsum("ij,ij->i", tv, pv) * inv; qv = np.cross(tv, e1); v = (qv @ d) * inv
    t = np.einsum("ij,ij->i", e2, qv) * inv
    return list(t[ok & (u >= 0) & (v >= 0) & (u + v <= 1) & (t > 1e-9)])


def cham(m, x, z, tu_truoc=True):
    tri = m.triangles; o = np.array([x, 0.0, z]); d = np.array([0.0, 1.0, 0.0])
    e1, e2 = tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0]
    pv = np.cross(d, e2); det = np.einsum("ij,ij->i", e1, pv); ok = np.abs(det) > 1e-12
    inv = np.where(ok, 1.0 / np.where(ok, det, 1), 0); tv = o - tri[:, 0]
    u = np.einsum("ij,ij->i", tv, pv) * inv; qv = np.cross(tv, e1); v = (qv @ d) * inv
    t = np.einsum("ij,ij->i", e2, qv) * inv
    hit = ok & (u >= 0) & (v >= 0) & (u + v <= 1)
    if not hit.any(): return None
    return float(t[hit].min() if tu_truoc else t[hit].max())


def soi(out):
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import hm, hand as _tay
    loi, ghi = [], []
    meta = json.load(open(out + ".json")); tier = meta["tier"]; gioi = meta["gioi"]; cao = meta["cao"]; k = cao / 1.8
    tat = doc_glb(out + ".glb"); bo = {n: m for n, m in tat.items() if not n.startswith("mat_")}
    # ①
    ho = [n for n, m in bo.items() if not m.is_watertight]
    (loi if ho else ghi).append(f"① watertight: {'OPEN ' + ', '.join(ho) if ho else 'all ' + str(len(bo)) + ' parts'}")
    # ② budget, measured
    tg = sum(len(m.faces) for m in bo.values()); TI = hm.TIER[tier]
    lo_, hi_ = TI["budget_faceless"] if meta["faceless"] else TI["budget"]
    (ghi if lo_ <= tg <= hi_ else loi).append(f"② render tris {tg} ({lo_}–{hi_}, tier {tier}{' faceless' if meta['faceless'] else ''})")
    dem = {}
    for n, m in bo.items(): dem[meta["vung"][n]] = dem.get(meta["vung"][n], 0) + len(m.faces)
    lech = {r: (dem.get(r, 0), b) for r, b in TI["regions"].items() if not (r == "head" and meta["faceless"])
            and abs(dem.get(r, 0) - b) > 0.30 * b}
    (loi if lech else ghi).append(f"② regions (±30 %): {dem}" + (f" OFF: {lech}" if lech else ""))
    # ③
    zlo = min(m.bounds[0][2] for m in bo.values()); zhi = max(m.bounds[1][2] for m in bo.values())
    (ghi if abs(zhi - zlo - cao) <= cao * 0.01 else loi).append(f"③ height {zhi - zlo:.3f} m (target {cao})")
    (ghi if -0.005 <= zlo <= 0.010 else loi).append(f"③ floor {zlo * 1000:+.1f} mm")
    # ④
    vol = sum(m.volume for m in bo.values()); kk = k ** 3
    (ghi if 0.050 * kk <= vol <= 0.095 * kk else loi).append(f"④ volume {vol:.4f} m³ ({0.050 * kk:.3f}–{0.095 * kk:.3f})")
    th = bo["than"]; mt = meta["moc_than"]
    # ⑤
    z0, z1 = mt["mong"], mt["vai"]; cu, xau, so = None, [], 0
    for z in np.arange(z0 + 0.005, z1, 0.01):
        if any(abs(z - zm) < 0.003 for zm in mt.values()): continue
        s_ = th.section(plane_origin=(0, 0, z), plane_normal=(0, 0, 1))
        if s_ is None: xau.append((round(float(z), 3), "cut")); continue
        if len(s_.entities) != 1: xau.append((round(float(z), 3), f"{len(s_.entities)} loops"))
        p = s_.vertices; r, d = np.ptp(p[:, 0]), np.ptp(p[:, 1]); so += 1
        if cu is not None and max(abs(r - cu[0]), abs(d - cu[1])) > BAC_TOI_DA: xau.append((round(float(z), 3), round(max(abs(r - cu[0]), abs(d - cu[1])) * 1000)))
        cu = (r, d)
    (loi if xau else ghi).append(f"⑤ continuous torso: {so} slices" + (f", steps {xau[:5]}" if xau else f", no step > {BAC_TOI_DA * 1000:.0f} mm"))
    # ⑧
    def rong(z):
        s_ = th.section(plane_origin=(0, 0, z + 0.004), plane_normal=(0, 0, 1)); return np.ptp(s_.vertices[:, 0]) if s_ is not None else 0
    e, n, h = rong(mt["eo"]), rong(mt["nguc"]), rong(mt["hong"]); ti = e / min(n, h)
    (ghi if ti <= 0.93 else loi).append(f"⑧ waist/min(chest,hip) = {ti:.2f} (≤0.93)")
    # ⑨ head density vs torso (Boss 22/10: uniform facet density)
    dau = bo["dau"]; md = len(dau.faces) / (dau.area * 100); mth = len(th.faces) / (th.area * 100); r_ = md / mth
    lim = (80, 1.5) if meta["faceless"] else ((200, 3.5) if tier == "rut_gon" else (300, 3.5))
    (ghi if len(dau.faces) <= lim[0] and r_ <= lim[1] else loi).append(
        f"⑨ head {len(dau.faces)} tris (≤{lim[0]}), density {r_:.1f}× torso (≤{lim[1]}×)")
    # ⑩ glutes
    xm = 0.065 * k
    mui = [cham(th, sx * xm, mt["mong"], False) for sx in (1, -1)]; khe = cham(th, 0.0, mt["mong"] + 0.004, False); lung = cham(th, 0.0, mt["eo"] + 0.004, False)
    if None in mui or khe is None or lung is None: loi.append("⑩ glutes: ray missed")
    else:
        nho = (min(mui) - lung) * 1000; sk_ = (min(mui) - khe) * 1000
        doc = [(z, cham(th, xm, z, False)) for z in np.arange(mt["mong"] - 0.08, mt["mong"] + 0.10, 0.005)]
        doc = [(z, y) for z, y in doc if y is not None]; xe = (mt["mong"] - max(doc, key=lambda q: q[1])[0]) * 1000
        lo, hi = (30, 60) if gioi == "nam" else (40, 80)
        (ghi if lo <= nho <= hi and 5 <= sk_ <= 20 and xe <= 30 else loi).append(
            f"⑩ glutes: projection {nho:.0f} mm ({lo}–{hi}) · cleft {sk_:.0f} mm (5–20) · sag {xe:.0f} mm (≤30)")
    # ⑪ forehead (head-relative: brow 0.62, forehead 0.80 of chin→top)
    c0, c1 = meta["chin"], meta["head_top"]; hh = c1 - c0
    y_may = cham(dau, 0.0, c0 + 0.62 * hh); y_tran = cham(dau, 0.0, c0 + 0.80 * hh)
    if y_may is None or y_tran is None: loi.append("⑪ forehead: ray missed")
    else: (ghi if (y_tran - y_may) * 1000 <= 25 else loi).append(f"⑪ forehead recedes {(y_tran - y_may) * 1000:.0f} mm behind brow (≤25)")
    # ⑫ «W» rim
    def day_vien(x):
        zs = [z for z in np.arange(mt["mong"], 0.70 * k, -0.002) if cham(th, x, z, False) is not None]; return min(zs) if zs else None
    zk, zm, zh = day_vien(0.0), day_vien(0.065 * k), day_vien(0.14 * k)
    if None in (zk, zm, zh): loi.append("⑫ rim: ray missed")
    else: (ghi if (zk - zm) * 1000 >= 15 and (zh - zm) * 1000 >= 15 else loi).append(
        f"⑫ no skirt: cleft rim {(zk - zm) * 1000:.0f} mm, hip rim {(zh - zm) * 1000:.0f} mm above cheek rim (≥15)")
    # ⑮ grip (rut_gon uses the LPM hand)
    if tier == "rut_gon":
        for ben in ("L", "R"):
            tn = [f"{q}_{ben}" for q in ("ban_tay", "ngon1", "ngon2", "cai1", "cai2")]; sc_ = meta["socket"][f"cam_{ben}"]
            om, lun = _tay.do_nam({q: bo[q].vertices for q in tn}, (np.array(sc_["vi_tri"]), np.array(sc_["len"]), sc_["r"]))
            can = 75 if meta["co_tay"] >= 0.95 else 0
            (ghi if lun <= 1.5 and om >= can else loi).append(f"⑮ grip {ben} (co={meta['co_tay']:g}): wrap {om:.0f}% (≥{can}) · penetration {lun:.1f} mm (≤1.5)")
    else:
        ghi.append("⑮ grip: not gated for the 5-finger hand (chi_tiet) — --co only curls fingers")
    # ⑥ contract
    need = {"than", "co", "dau", "canh_tay_L", "canh_tay_R", "cang_tay_L", "cang_tay_R", "dui_L", "dui_R", "cang_chan_L", "cang_chan_R",
            "ban_tay_L", "ban_tay_R", "ban_chan_L", "ban_chan_R"}
    need |= {f"{q}_{b}" for b in "LR" for q in (("ngon1", "ngon2", "cai1", "cai2") if tier == "rut_gon" else ("ngon_cai", "ngon_tro", "ngon_giua", "ngon_ap", "ngon_ut"))}
    if not meta["faceless"]: need |= {"tai_L", "tai_R"}
    need_s = {"dau", "HAIR", "ban_tay_L", "ban_tay_R", "ban_chan_L", "ban_chan_R", "cam_L", "cam_R", "lung", "hong_L", "hong_R"}
    th_ = need - set(bo); ts_ = need_s - set(meta["socket"])
    (loi if th_ or ts_ else ghi).append(f"⑥ contract: missing parts {sorted(th_) or '—'}, missing sockets {sorted(ts_) or '—'}")
    # ⑦
    lech = [q for q in bo if q.endswith("_L") and (q[:-2] + "_R" not in bo or np.max(np.abs(bo[q].extents - bo[q[:-2] + "_R"].extents) / np.maximum(bo[q].extents, 1e-6)) > 0.03)]
    (loi if lech else ghi).append(f"⑦ symmetry: {', '.join(lech) if lech else 'all L/R pairs < 3 %'}")
    # ⑯ ring twist on every lofted limb
    xo = xoan_glb(out + ".glb", ("canh_tay", "cang_tay", "dui", "cang_chan", "ban_chan", "co"))
    bad = {q: round(v[0], 1) for q, v in xo.items() if v[0] > XOAN_MAX}
    worst = max((v[0] for v in xo.values()), default=0)
    (loi if bad or len(xo) < 8 else ghi).append(f"⑯ ring twist: {len(xo)} lofted limbs measured, worst {worst:.1f}° (≤{XOAN_MAX}°)" + (f" BAD {bad}" if bad else ""))
    # ⑰ arm length (open hand only — a fist shortens the reach)
    lh, tz, sh, tip, Hm = tay_glb(out + ".glb")
    if meta["co_tay"] < 0.5:
        (ghi if tay_ok(lh, tz) else loi).append(f"⑰ arm: shoulder→fingertip {lh:.3f} H ({TAY_LH[0]}–{TAY_LH[1]}) · fingertip at {tz:.3f} H ({TAY_TIP[0]}–{TAY_TIP[1]})")
    else: ghi.append(f"⑰ arm: skipped (co={meta['co_tay']:g}); measured {lh:.3f} H, tip {tz:.3f} H")
    # ⑱ hair inside head
    if meta.get("hair", "none") != "none":
        hair = list(doc_glb(out + "_HAIR.glb").values())[0]
        pts, _ = trimesh.sample.sample_surface(hair, 4000, seed=7)
        inside = int(sum(len(tia(dau, p, np.array((0.3, 0.5, 0.81)))) % 2 for p in pts))      # ray parity
        S = np.array(meta["socket"]["HAIR"]["vi_tri"]); top = pts[pts[:, 2] > c0 + 0.5 * hh]
        d = np.array([np.linalg.norm(p - S) - max(tia(dau, S, (p - S) / np.linalg.norm(p - S)), default=0) for p in top])
        (ghi if inside == 0 else loi).append(f"⑱ hair ({meta['hair']}, {len(hair.faces)} tris): {inside}/4000 samples inside head · scalp gap min {d.min() * 1000:.1f} / median {np.median(d) * 1000:.1f} mm")
    # ⑲ landmarks (measured vs table)
    LM = meta["landmark"]; off = LM["H"] - zhi   # mesh top = LM dinh after flooring
    vai_m = mt["vai"]; d1 = abs(vai_m - (LM["vai_tren"] - (LM["dinh"] - zhi)))
    d2 = abs(zhi - LM["dinh"]); d3 = abs(c0 - LM["cam"])
    (ghi if max(d1, d2, d3) <= 0.015 else loi).append(f"⑲ landmarks: shoulder-top Δ{d1 * 1000:.0f} · top Δ{d2 * 1000:.0f} · chin Δ{d3 * 1000:.0f} mm (≤15)")
    for d_ in ghi: print("  ✅", d_)
    for d_ in loi: print("  ❌", d_)
    print(("⛔ HM FAIL " if loi else "✅ HM PASS ") + out)
    return 1 if loi else 0


if __name__ == "__main__":
    if sys.argv[1] == "--xoan":
        kq = xoan_glb(sys.argv[2]); bad = {q: v for q, v in kq.items() if v[0] > XOAN_MAX}
        for q, v in kq.items(): print(f"  {'❌' if v[0] > XOAN_MAX else '✅'} {q}: twist {v[0]:.1f}° ({v[1]}-gon, {v[2]} rings)")
        print("⛔ TWIST FAIL" if bad or not kq else "✅ TWIST PASS"); sys.exit(1 if bad or not kq else 0)
    if sys.argv[1] == "--tay":
        lh, tz, sh, tip, H = tay_glb(sys.argv[2])
        print(f"  H {H:.3f} · shoulder {np.round(sh, 3)} · tip {np.round(tip, 3)} · L/H {lh:.3f} · tip {tz:.3f} H")
        print("✅ ARM PASS" if tay_ok(lh, tz) else "⛔ ARM FAIL"); sys.exit(0 if tay_ok(lh, tz) else 1)
    sys.exit(soi(sys.argv[1]))

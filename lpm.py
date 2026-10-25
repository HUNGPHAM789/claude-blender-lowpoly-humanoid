#!/usr/bin/env python3
"""LPM — Low-Poly Model: thân người trơn kiểu origami (mặt phẳng, không mặt cong).

Kiến trúc (v2):
  • THÂN  = MỘT lưới liền, dựng bằng các VÒNG 8 đỉnh theo BẢNG MẶT CẮT (cổ → đáy chậu).
            Hình lõm (eo thắt, khe mông, rãnh lưng) làm được vì vòng nối vòng, không dùng ConvexHull.
  • CHI   = khối lồi KÍN RỜI (ConvexHull): bắp tay, khuỷu, cẳng tay, đùi, gối, cẳng chân.
  • ĐẦU · BÀN TAY · BÀN CHÂN = khối kín RỜI, gắn qua SOCKET ⇒ tháo ra thay tóc/mũ, găng, giày.
  • Mọi bộ phận là một node có tên trong GLB; socket là node rỗng `SOCKET_<tên>` + file .json bên cạnh.

Dùng:
  python3 lpm.py --out <thư mục>/<tên> [--gioi nam|nu] [--cao 1.80]
  ⇒ <tên>.glb, <tên>.obj, <tên>.json, rồi TỰ CHẠY check_lpm.py — cửa trượt thì thoát mã 1.
Toạ độ: mét, Z lên, chân chạm z=0, mặt nhìn -Y (GLB đã đổi sang Y-lên theo chuẩn glTF).
"""
import argparse, json, math, os, subprocess, sys
import numpy as np, trimesh
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hand as tay
from scipy.spatial import ConvexHull

# ---------------------------------------------------------------- BẢNG MẶT CẮT THÂN (người 1,80 m)
# (tên mốc, z, nửa rộng X, nửa sâu Y, tâm Y, {góc°: hệ số đẩy theo bán kính})
# Góc đo từ GIỮA NGỰC (0°, phía −Y) vòng ra sau (180° = giữa LƯNG); một góc áp cho CẢ HAI bên (±).
# Đỉnh ở 0 · 30 · 60 · 90 · 120 · 150 · 165 · 180° (GOC_THAN, 14 đỉnh/vòng): ±165° là MÉP KHE MÔNG —
# thiếu nó thì khe chỉ là một đỉnh, nhìn từ sau mông thành tấm ván phẳng (đã dính v2.1 lần 1).
THAN = {
 "nam": [
  ("co_day",     1.505, 0.070, 0.062, 0.010, {}),
  ("vai",        1.455, 0.185, 0.090, 0.010, {0: 0.85, 180: 0.92}),
  ("nguc",       1.360, 0.170, 0.112, -0.004, {0: 0.93, 30: 1.03, 180: 0.90}),   # rãnh ức, cơ ngực, rãnh sống lưng
  ("duoi_nguc",  1.270, 0.158, 0.104, 0.000, {180: 0.90}),
  ("eo",         1.130, 0.140, 0.094, 0.006, {180: 0.88}),
  ("mao_chau",   1.035, 0.158, 0.100, 0.008, {}),
  ("hong",       0.955, 0.176, 0.110, 0.016, {150: 1.03, 180: 0.94}),
  ("mong",       0.885, 0.168, 0.116, 0.024, {150: 1.06, 165: 1.03, 180: 0.88}),   # nhô NHẸ + khe nông (Boss 22/10: «chỉ cần 1 chút»)
  # ĐÁY THÂN CONG (v2.3, Boss 22/10 «mông chưa làm mất cạnh dưới (giống váy)»): viền đáy nhìn từ sau phải hình «W»
  # — thấp nhất dưới mỗi múi (150–165°), NHÔ LÊN ở khe (180°) và hai bên hông (90–120°); trước: háng (30–60°) nhô lên.
  # Phần tử thứ 7 = {góc°: lệch z (m)}. Viền đáy phẳng ngang = gấu váy.
  ("day_chau",   0.840, 0.150, 0.098, 0.018, {0: 0.85, 150: 1.04, 180: 0.80},
                 {0: 0.010, 30: 0.030, 60: 0.035, 90: 0.040, 120: 0.020, 150: -0.012, 165: -0.010, 180: 0.030}),
 ],
 "nu": [
  ("co_day",     1.505, 0.060, 0.055, 0.010, {}),
  ("vai",        1.455, 0.165, 0.082, 0.010, {0: 0.85, 180: 0.92}),
  ("nguc",       1.355, 0.152, 0.118, -0.010, {0: 0.86, 30: 1.12, 60: 1.04, 180: 0.90}),  # hai bầu ngực + khe
  ("duoi_nguc",  1.285, 0.140, 0.098, 0.004, {180: 0.90}),
  ("eo",         1.145, 0.122, 0.088, 0.008, {180: 0.86}),
  ("mao_chau",   1.045, 0.160, 0.102, 0.012, {}),
  ("hong",       0.960, 0.186, 0.114, 0.022, {150: 1.04, 180: 0.94}),
  ("mong",       0.890, 0.178, 0.122, 0.030, {150: 1.08, 165: 1.04, 180: 0.86}),
  ("day_chau",   0.845, 0.160, 0.104, 0.024, {0: 0.85, 150: 1.05, 180: 0.80},
                 {0: 0.010, 30: 0.030, 60: 0.035, 90: 0.040, 120: 0.020, 150: -0.012, 165: -0.010, 180: 0.030}),
 ]}
# điểm khớp (x, y, z) người 1,80 m — tay chữ A 25°
KHOP = {
 "nam": dict(vai=(0.195, 0.008, 1.425), hang=(0.092, 0.010, 0.900), goi_z=0.500, co_chan_z=0.085,
             canh_tay=(0.300, 0.058, 0.042), cang_tay=(0.265, 0.045, 0.030), dui=(0.088, 0.060), bap=(0.058, 0.036)),
 "nu":  dict(vai=(0.175, 0.008, 1.425), hang=(0.098, 0.014, 0.905), goi_z=0.500, co_chan_z=0.085,
             canh_tay=(0.290, 0.050, 0.036), cang_tay=(0.255, 0.040, 0.026), dui=(0.092, 0.058), bap=(0.054, 0.033)),
}
GOC_TAY = math.radians(25)
CO_TAY = 0.0          # 0 = xoè, 1 = nắm (đặt bằng --co)
KHOP_TAY = {}         # bản lề bàn tay (thế giới) — ghi vào .json cho rig
SO_DINH = 12
_NUA_THAN = [0, 30, 60, 90, 120, 150, 165, 180]
GOC_THAN = _NUA_THAN + [360 - g for g in reversed(_NUA_THAN[1:-1])]


def he_so(keo, goc_do):
    """hệ số đẩy tại góc (đối xứng ±): lấy mốc gần nhất trong 1°, không có thì 1."""
    g = abs(((goc_do + 180) % 360) - 180)
    for k, v in keo.items():
        if abs(g - k) < 1.0: return v
    return 1.0


def vong(z, nr, ns, yc, keo, p=2.6, n=SO_DINH, ns_sau=None, goc=None, dz=None):
    """vòng siêu-elip (p>2 ⇒ vuông vức hơn elip). keo: {góc°: hệ số} đẩy theo bán kính, đối xứng hai bên.
    goc: danh sách góc° tuỳ ý (0 → 360) thay cho n góc đều — dồn đỉnh vào chỗ cần nét (sống mũi)."""
    pts = []
    for t in ([math.radians(g) for g in goc] if goc else [2 * math.pi * k / n for k in range(n)]):
        s, c = math.sin(t), math.cos(t)
        sau = ns if (ns_sau is None or c >= 0) else ns_sau
        x = nr * math.copysign(abs(s) ** (2 / p), s)
        y = -sau * math.copysign(abs(c) ** (2 / p), c)
        f = he_so(keo, math.degrees(t))
        pts.append((x * f, yc + y * f, z + (he_so(dz, math.degrees(t)) - 1.0 if dz else 0.0)))
    return pts


def loft(ds_vong, nap_tren, nap_duoi):
    """nối các vòng cùng số đỉnh thành lưới kín; bịt 2 đầu bằng quạt về điểm nap_*."""
    n = len(ds_vong[0]); V, F, idx = [], [], []
    for r in ds_vong:
        i0 = len(V); V += r; idx.append(list(range(i0, i0 + n)))
    for a, b in zip(idx[:-1], idx[1:]):
        for k in range(n):
            a0, a1, b0, b1 = a[k], a[(k + 1) % n], b[k], b[(k + 1) % n]
            F += [(a0, b0, a1), (a1, b0, b1)]
    it = len(V); V.append(tuple(nap_tren)); id_ = len(V); V.append(tuple(nap_duoi))
    for k in range(n):
        F.append((idx[0][(k + 1) % n], it, idx[0][k])); F.append((idx[-1][k], id_, idx[-1][(k + 1) % n]))
    m = trimesh.Trimesh(np.array(V, float), np.array(F), process=True); m.fix_normals(); return m


def than_lien(bang, s):
    """lưới thân liền: nối vòng-vòng (12 đỉnh), bịt cổ + đáy chậu bằng quạt."""
    ds = [vong(z * s, nr * s, ns * s, yc * s, r[0], goc=GOC_THAN,
               dz={g: 1.0 + d * s for g, d in r[1].items()} if len(r) > 1 else None)
          for (_, z, nr, ns, yc, *r) in bang]
    tren = np.mean(ds[0], axis=0) + (0, 0, 0.012 * s)
    # chóp đáy chậu: NÂNG lên ngang khe + dời ra trước, giấu giữa hai đùi — để thấp nhất ở giữa thì viền đáy thành bát/gấu váy
    duoi = np.mean(ds[-1], axis=0) + (0, -0.025 * s, 0.020 * s)
    return loft(ds, tren, duoi)


def khoi(pts):
    pts = np.array(pts, float); h = ConvexHull(pts)
    m = trimesh.Trimesh(pts, h.simplices, process=True); m.fix_normals(); return m


def vong_truc(c, truc, rx, ry, n, lech=0.0):
    """vòng n đỉnh quanh trục bất kỳ; rx theo hướng NGANG (X thế giới) nếu được, ry theo hướng còn lại.
    ⚠ bài học v1: chọn trục tham chiếu sai làm khúc bụng xoay 90° (sâu 30 cm, rộng 17 cm)."""
    truc = np.array(truc, float); truc /= np.linalg.norm(truc)
    ref = np.array((0, 1.0, 0)) if abs(truc[1]) < 0.9 else np.array((0, 0, 1.0))
    a = np.cross(ref, truc); a /= np.linalg.norm(a); b = np.cross(truc, a)
    return [np.array(c) + rx * math.cos(2 * math.pi * k / n + lech) * a + ry * math.sin(2 * math.pi * k / n + lech) * b
            for k in range(n)]


def doan(p0, p1, r0, r1, giua=None, n=6):
    p0, p1 = np.array(p0, float), np.array(p1, float); t = p1 - p0
    pts = vong_truc(p0, t, *r0, n) + vong_truc(p1, t, *r1, n)
    if giua: pts += vong_truc(p0 + t * giua[0], t, *giua[1], n, math.pi / n)
    return khoi(pts)


def dau(s, gioi):
    """đầu ĐÁ QUÝ (ConvexHull ~40 tam giác): sọ, trán, sống mũi, gò má, góc hàm, cằm, tai. KHÔNG tóc.
    Boss 22/10: «tôi thích phiên bản chưa nâng cấp mắt mũi hơn… thêm nhiều mặt phẳng quá so với toàn body»
    ⇒ bản loft vùng T (360 tam giác, 27/dm² = 6× thân) BỊ BỎ. Mật độ mặt đầu phải ≈ thân (cửa ⑨)."""
    h = 0.92 if gioi == "nu" else 1.0          # hàm nữ thon hơn
    P = [(0, 0.015, 1.800), (0.072, 0.005, 1.775), (-0.072, 0.005, 1.775), (0, 0.098, 1.745), (0.078, 0.07, 1.70),
         (-0.078, 0.07, 1.70), (0, -0.092, 1.725), (0.062, -0.082, 1.722), (-0.062, -0.082, 1.722),
         (0, -0.116, 1.658), (0.016, -0.100, 1.645), (-0.016, -0.100, 1.645),                       # sống + cánh mũi
         (0.070, -0.066, 1.665), (-0.070, -0.066, 1.665), (0.082, 0.0, 1.668), (-0.082, 0.0, 1.668),
         (0.088, 0.012, 1.650), (-0.088, 0.012, 1.650),                                             # tai
         (0.058, 0.075, 1.618), (-0.058, 0.075, 1.618),
         (0.060 * h, -0.032, 1.585), (-0.060 * h, -0.032, 1.585),                                   # góc hàm
         (0, -0.083, 1.568), (0.024 * h, -0.074, 1.562), (-0.024 * h, -0.074, 1.562),                # cằm
         # TRÁN (v2.3, Boss 22/10 «nhìn ngang thì hơi thiếu phần trán»): +6 điểm = +10 tam giác (38→48);
         # trán lùi sau cung mày 57 → 11 mm. Thêm 2 điểm cung mày (+4 tam giác) không thấy khác ⇒ không dùng.
         (0, -0.086, 1.768), (0.050, -0.074, 1.764), (-0.050, -0.074, 1.764),
         (0, -0.060, 1.792), (0.040, -0.050, 1.788), (-0.040, -0.050, 1.788)]
    return khoi([(x * s, y * s, z * s) for x, y, z in P])


def dung(gioi="nam", cao=1.80):
    s = cao / 1.80; K = KHOP[gioi]
    bo, sk = {}, {}                      # bộ phận, socket
    bo["than"] = than_lien(THAN[gioi], s)
    bo["co"] = doan((0, 0.012 * s, 1.49 * s), (0, 0.012 * s, 1.615 * s), (0.052 * s, 0.048 * s), (0.046 * s, 0.044 * s))
    bo["dau"] = dau(s, gioi)
    sk["dau"] = dict(vi_tri=(0, 0.012 * s, 1.585 * s), len=(0, 0, 1))
    for ten_ben, sx in (("L", 1), ("R", -1)):
        vai = np.array((sx * K["vai"][0], K["vai"][1], K["vai"][2])) * s
        h = np.array((sx * math.sin(GOC_TAY), 0.0, -math.cos(GOC_TAY)))
        L1, r1a, r1b = K["canh_tay"]; L2, r2a, r2b = K["cang_tay"]
        khuyu = vai + h * L1 * s; co_tay = khuyu + h * L2 * s + np.array((0, -0.012, 0)) * s
        # cơ delta: chỏm ôm đầu cánh tay (vòng quanh TRỤC CÁNH TAY), không chĩa mũi nhọn lên trời
        bo[f"bap_vai_{ten_ben}"] = khoi(vong_truc(vai + h * 0.02 * s, h, r1a * 1.18 * s, r1a * 1.12 * s, 6)
                                       + vong_truc(vai + h * 0.11 * s, h, r1a * 1.04 * s, r1a * 1.0 * s, 6, math.pi / 6)
                                       + [vai + np.array((-sx * 0.035, 0, 0.040)) * s])
        bo[f"canh_tay_{ten_ben}"] = doan(vai, khuyu, (r1a * s, r1a * s), (r1b * s, r1b * 1.05 * s), giua=(0.35, (r1a * 0.95 * s, r1a * 1.05 * s)))
        bo[f"khuyu_{ten_ben}"] = khoi(vong_truc(khuyu, h, r1b * 1.1 * s, r1b * 1.1 * s, 4) + [khuyu + h * 0.045 * s, khuyu - h * 0.045 * s])
        bo[f"cang_tay_{ten_ben}"] = doan(khuyu, co_tay, (r2a * 1.05 * s, r2a * 1.1 * s), (r2b * s, r2b * 0.85 * s), giua=(0.28, (r2a * 1.1 * s, r2a * 1.12 * s)))
        # BÀN TAY «găng hở ngón cái» 5 khối, co được để NẮM (hand.py — Boss 22/10 «tay với 1 ngón cái? co lại để nắm?»)
        M, O = tay.khung_the_gioi(co_tay, h, sx)
        cuc_bo, khop_t, (tc, tt, tr) = tay.dung_tay(CO_TAY, s, nu=(gioi == "nu"))
        W = lambda p: O + M @ np.asarray(p, float)
        for ten, pts in cuc_bo.items():
            bo[f"{ten}_{ten_ben}"] = khoi([W(p) for p in pts])
        sk[f"ban_tay_{ten_ben}"] = dict(vi_tri=tuple(co_tay), len=tuple(h))
        sk[f"cam_{ten_ben}"] = dict(vi_tri=tuple(W(tc)), len=tuple(M @ tt), r=tr)          # tâm trụ nắm Ø32 mm, len = trục trụ
        KHOP_TAY[ten_ben] = {k: dict(tam=[round(x, 4) for x in W(c)], truc=[round(x, 4) for x in M @ a]) for k, (c, a) in khop_t.items()}
        hang = np.array((sx * K["hang"][0], K["hang"][1], K["hang"][2])) * s
        goi = np.array((sx * K["hang"][0] * 0.96, -0.008, K["goi_z"])) * s
        ca = np.array((sx * K["hang"][0] * 0.92, 0.018, K["co_chan_z"])) * s
        rd, rg = K["dui"]; rb, rc = K["bap"]
        bo[f"dui_{ten_ben}"] = doan(hang + np.array((0, 0, 0.05)) * s, goi, (rd * s, rd * 0.98 * s), (rg * s, rg * s), giua=(0.32, (rd * 0.96 * s, rd * 1.0 * s)))
        bo[f"goi_{ten_ben}"] = khoi(vong_truc(goi, ca - goi, rg * 1.04 * s, rg * 1.04 * s, 4) + [goi + np.array((0, -0.062, 0.01)) * s])
        bo[f"cang_chan_{ten_ben}"] = doan(goi, ca, (rb * 0.98 * s, rb * s), (rc * s, rc * 1.1 * s), giua=(0.27, (rb * s, rb * 1.12 * s)))
        bo[f"ban_chan_{ten_ben}"] = khoi([ca + np.array(d) * s for d in (
            (0.034, 0.05, 0.02), (-0.034, 0.05, 0.02), (0.04, 0.045, -0.085), (-0.038, 0.045, -0.085),
            (0.046, -0.15, -0.085), (-0.04, -0.15, -0.085), (0.03, -0.175, -0.06), (-0.024, -0.175, -0.06),
            (0.034, -0.035, 0.035), (-0.034, -0.035, 0.035))])
        sk[f"ban_chan_{ten_ben}"] = dict(vi_tri=tuple(ca), len=(0, -1, 0))
    sk["lung"] = dict(vi_tri=(0, 0.12 * s, 1.30 * s), len=(0, 1, 0))
    sk["hong_L"] = dict(vi_tri=(0.17 * s, 0.0, 1.0 * s), len=(1, 0, 0))
    sk["hong_R"] = dict(vi_tri=(-0.17 * s, 0.0, 1.0 * s), len=(-1, 0, 0))
    day = min(m.bounds[0][2] for m in bo.values())
    for m in bo.values(): m.apply_translation((0, 0, -day))
    for v in sk.values(): v["vi_tri"] = (v["vi_tri"][0], v["vi_tri"][1], v["vi_tri"][2] - day)
    return bo, sk


def xuat(bo, sk, out, meta):
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    trimesh.util.concatenate(list(bo.values())).export(out + ".obj")
    Y = trimesh.transformations.rotation_matrix(-math.pi / 2, (1, 0, 0))          # Z-lên → Y-lên (glTF)
    sc = trimesh.Scene()
    for ten, m in bo.items():
        g = m.copy(); g.apply_transform(Y); sc.add_geometry(g, node_name=ten, geom_name=ten)
    for ten, v in sk.items():
        T = Y @ trimesh.transformations.translation_matrix(v["vi_tri"])
        sc.graph.update(frame_to="SOCKET_" + ten, frame_from=sc.graph.base_frame, matrix=T)
    sc.export(out + ".glb")
    json.dump(dict(meta, bo_phan=sorted(bo), socket={k: dict(vi_tri=[round(float(x), 4) for x in v["vi_tri"]], len=[float(x) for x in v["len"]], **({"r": v["r"]} if "r" in v else {}))
                                                    for k, v in sk.items()},
                   toa_do="m, Z-up, chân z=0, nhìn -Y (GLB: Y-up)"), open(out + ".json", "w"), ensure_ascii=False, indent=1)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--out", required=True)
    ap.add_argument("--gioi", default="nam", choices=["nam", "nu"]); ap.add_argument("--cao", type=float, default=1.80)
    ap.add_argument("--co", type=float, default=0.0, help="bàn tay: 0 = xoè, 1 = nắm quanh trụ Ø32 mm")
    a = ap.parse_args()
    CO_TAY = a.co
    bo, sk = dung(a.gioi, a.cao)
    moc = {t: round(z * a.cao / 1.80, 4) for (t, z, *_) in THAN[a.gioi]}
    xuat(bo, sk, a.out, dict(gioi=a.gioi, cao=a.cao, phien_ban="LPM 2.6 faceless", moc_than=moc, co_tay=a.co, khop_tay=KHOP_TAY))
    print(f"đã xuất {a.out}.glb/.obj/.json — {len(bo)} bộ phận, {sum(len(m.faces) for m in bo.values())} tam giác")
    rc = subprocess.call([sys.executable, os.path.join(os.path.dirname(os.path.abspath(__file__)), "check_lpm.py"), a.out])
    sys.exit(rc)                                                                  # cửa soi trượt ⇒ build trượt

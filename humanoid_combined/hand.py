"""Bàn tay LPM — «GĂNG HỞ NGÓN CÁI» co được để NẮM (Boss 22/10/2026: «tay với 1 ngón cái? có thể co lại để nắm?»).

5 khối lồi KÍN rời, mỗi khối quay quanh MỘT bản lề (rig chỉ cần 4 xương/tay):
  ban_tay   lòng bàn tay (cổ tay → hàng đốt ngón)
  ngon1     khối 4 ngón dính, đốt gần   — bản lề KHỚP NGÓN (trục ngang bàn tay)
  ngon2     khối 4 ngón dính, đốt xa    — bản lề GIỮA NGÓN (song song)
  cai1      ngón cái đốt gần            — bản lề GỐC CÁI (trục chéo ⇒ vừa gập vừa đối diện)
  cai2      ngón cái đốt xa             — bản lề ĐỐT CÁI
Một tham số `co` ∈ [0, 1]: 0 = xoè thả lỏng, 1 = nắm quanh trụ Ø32 mm (báng súng / cán kiếm) tại socket `cam_*`.

Hệ toạ độ CỤC BỘ của bàn tay (mét, người 1,80 m — nhân `s` khi cao khác):
  u = dọc bàn tay, từ cổ tay ra đầu ngón (= hướng cẳng tay `h`)
  v = ngang bàn tay, phía NGÓN CÁI là +v
  n = pháp tuyến LÒNG bàn tay (+n = phía lòng)
"""
import math
import numpy as np

# ---- kích thước (người 1,80 m) — sửa ở ĐÂY, đừng chèn khối
TAY = dict(
    long_dai=0.095,             # cổ tay → khớp ngón
    long_rong=(0.032, 0.042),   # nửa rộng: cổ tay, khớp ngón
    long_day=(0.013, 0.011),    # nửa dày
    ngon1=(0.045, 0.040, 0.010),   # dài, nửa rộng, nửa dày
    ngon2=(0.035, 0.033, 0.008),
    cai_goc=(0.025, 0.040, 0.010),  # (u, v, n) chỗ bản lề gốc cái trên lòng
    cai1=(0.040, 0.011), cai2=(0.030, 0.009),  # dài, bán kính
)
# góc ở co = 1 (độ). Đo bằng cửa ⑮: 4 ngón + cái phải ÔM KÍN trụ Ø32 mm.
GOC_NAM = dict(khop=76.0, giua=90.0, cai_doi=90.0, cai_gap=20.0)   # máy dò lưới 22/10: ôm 81 %, lún 0,9 mm
GOC_NAM_NU = dict(khop=80.0, giua=70.0, cai_doi=80.0, cai_gap=30.0)   # tay nữ nhỏ 8 %, dò riêng: ôm 78 %, lún 0,4 mm
TRU_NAM = dict(u=0.076, n=0.028, r=0.016)   # trụ nắm Ø32 mm (cục bộ), trục theo v — = socket `cam_*` khi co = 1
TRU_NAM_NU = dict(u=0.068, n=0.030, r=0.016)


def _xoay(p, tam, truc, goc):
    """xoay điểm p quanh trục đi qua `tam` (Rodrigues)."""
    k = np.asarray(truc, float); k /= np.linalg.norm(k); v = np.asarray(p, float) - tam
    c, s_ = math.cos(goc), math.sin(goc)
    return tam + v * c + np.cross(k, v) * s_ + k * np.dot(k, v) * (1 - c)


def _hop(u0, u1, r0, r1, d0, d1, vat=0.0):
    """hộp thon 8 đỉnh dọc u (hơi vát mép trên để không thành gạch). Điểm (u, v, n)."""
    pts = []
    for u, r, d in ((u0, r0, d0), (u1, r1, d1)):
        for sv in (1, -1):
            for sn in (1, -1):
                pts.append((u, sv * r, sn * d * (1 - vat if sn < 0 else 1)))
    return pts


def _lang_tru(goc, dau, r0, r1, n=6):
    """lăng trụ n cạnh từ `goc` theo hướng `dau` (vector đơn vị * dài)."""
    goc = np.asarray(goc, float); dau = np.asarray(dau, float); L = np.linalg.norm(dau); t = dau / L
    a = np.cross(t, (0, 0, 1.0)) if abs(t[2]) < 0.9 else np.cross(t, (1.0, 0, 0)); a /= np.linalg.norm(a); b = np.cross(t, a)
    pts = []
    for p, r in ((goc, r0), (goc + dau, r1)):
        for k in range(n):
            th = 2 * math.pi * k / n; pts.append(p + r * (math.cos(th) * a + math.sin(th) * b))
    pts.append(goc + dau * 1.08)   # đầu ngón vát nhẹ
    return pts


def dung_tay(co=0.0, s=1.0, nu=False):
    """trả (bo_phan_cuc_bo: {ten: [điểm (u,v,n)]}, khop: {ten: (tâm, trục)}, tru: (tâm, trục, r)) — chưa đặt vào thế giới."""
    T = {k: (tuple(x * s for x in v) if isinstance(v, tuple) else v * s) for k, v in TAY.items()}
    if nu:   # tay nữ thon hơn 8 %
        T = {k: (tuple(x * 0.92 for x in v) if isinstance(v, tuple) else v * 0.92) for k, v in T.items()}
    L = T["long_dai"]; (rw, rk), (dw, dk) = T["long_rong"], T["long_day"]
    bo = {}
    long_ = _hop(0, L, rw, rk, dw, dk) + [(0.030 * s, rw * 1.05, dw * 1.35)]          # gò ngón cái (mô cái)
    bo["ban_tay"] = long_
    # 4 ngón dính — 2 đốt
    l1, r1, d1 = T["ngon1"]; l2, r2, d2 = T["ngon2"]
    ngon1 = _hop(L, L + l1, r1, r1 * 0.94, d1, d1 * 0.92, vat=0.15)
    ngon2 = _hop(L + l1, L + l1 + l2, r2, r2 * 0.80, d2, d2 * 0.75, vat=0.15) + [(L + l1 + l2 + 0.006 * s, 0.0, 0.0)]
    G = GOC_NAM_NU if nu else GOC_NAM; TR = TRU_NAM_NU if nu else TRU_NAM
    a1, a2 = math.radians(G["khop"] * co), math.radians(G["giua"] * co)
    truc_v = np.array((0, 1.0, 0))
    khop1 = np.array((L, 0, 0.0)); khop2 = np.array((L + l1, 0, 0.0))
    # gập về phía lòng (+n): quay quanh -v   (u → n)
    ngon1 = [_xoay(p, khop1, -truc_v, a1) for p in ngon1]
    k2 = _xoay(khop2, khop1, -truc_v, a1)
    ngon2 = [_xoay(_xoay(p, khop1, -truc_v, a1), k2, -truc_v, a2) for p in ngon2]
    bo["ngon1"], bo["ngon2"] = ngon1, ngon2
    # ngón cái — gốc trên mép +v gần cổ tay, hướng xoè chéo ra
    g = np.array(T["cai_goc"]); (lc1, rc1), (lc2, rc2) = T["cai1"], T["cai2"]
    huong0 = np.array((0.62, 0.62, 0.48)); huong0 /= np.linalg.norm(huong0)
    truc_doi = np.array((1.0, 0, 0))                        # đối diện: lật ngón cái sang phía lòng quanh trục u
    b_doi = math.radians(G["cai_doi"] * co)
    huong = _xoay(huong0, np.zeros(3), truc_doi, b_doi)
    truc_gap = np.cross(huong, (0, 0, 1.0)); truc_gap /= np.linalg.norm(truc_gap)
    cai1 = _lang_tru(g, huong * lc1, rc1, rc1 * 0.9, n=5)[:-1]
    k_cai = g + huong * lc1
    huong2 = _xoay(huong, np.zeros(3), np.cross(huong, truc_v) if co > 0 else truc_gap, math.radians(G["cai_gap"] * co))
    cai2 = _lang_tru(k_cai, huong2 * lc2, rc2, rc2 * 0.75, n=5)
    bo["cai1"], bo["cai2"] = cai1, cai2
    khop = {"khop_ngon": (khop1, -truc_v), "giua_ngon": (k2, -truc_v), "goc_cai": (g, truc_doi), "dot_cai": (k_cai, truc_gap)}
    tru = (np.array((TR["u"] * s, 0, TR["n"] * s)), truc_v, TR["r"])        # r KHÔNG nhân s: báng súng không co theo người
    return bo, khop, tru


def khung_the_gioi(co_tay, h, sx):
    """ma trận cột [u v n] → thế giới cho tay bên sx (+1 trái, −1 phải), tư thế chữ A: lòng tay hướng vào đùi, ngón cái ra TRƯỚC (−Y)."""
    u = np.asarray(h, float); u /= np.linalg.norm(u)
    n = np.array((-sx, 0.0, 0.0)); n = n - u * np.dot(n, u); n /= np.linalg.norm(n)   # lòng hướng vào thân
    v = np.cross(n, u)
    if v[1] > 0: v = -v                                                               # ngón cái ra trước
    return np.column_stack((u, v, n)), np.asarray(co_tay, float)


# ---------------------------------------------------------------- ĐO NẮM (cửa ⑮)
def _nua_khong_gian(pts):
    from scipy.spatial import ConvexHull
    h = ConvexHull(np.asarray(pts, float)); return h.equations          # a·x + b <= 0 là bên trong


def _tia_loi(eq, p, d):
    """tia p + t·d cắt khối lồi (nửa không gian): trả t vào (≥0) hoặc None."""
    a, b = eq[:, :3], eq[:, 3]; ad = a @ d; ap = a @ p + b
    lo, hi = 0.0, 1e9
    for x, y in zip(ad, ap):
        if abs(x) < 1e-12:
            if y > 0: return None
        elif x > 0: hi = min(hi, -y / x)
        else: lo = max(lo, -y / x)
    return lo if lo <= hi else None


def do_nam(bo, tru, so_tia=36, ke=0.012):
    """(độ ôm %, độ lún mm): tia từ trục trụ ra mọi hướng ⊥ trục; ôm = tỉ lệ tia chạm tay trong [r−2, r+ke] mm.
    lún = khoảng lún sâu nhất của tay vào trụ (mm, >0 là xuyên)."""
    tam, truc, r = tru; truc = truc / np.linalg.norm(truc)
    a = np.cross(truc, (1.0, 0, 0)); a /= np.linalg.norm(a); b = np.cross(truc, a)
    eqs = [_nua_khong_gian(p) for p in bo.values()]
    om, lun = 0, 0.0
    for lat in (-0.02, 0.0, 0.02):                     # 3 lát dọc trụ (ngón trỏ / giữa / út)
        for k in range(so_tia):
            th = 2 * math.pi * k / so_tia; d = math.cos(th) * a + math.sin(th) * b; p = tam + truc * lat
            ts = [t for e in eqs if (t := _tia_loi(e, p, d)) is not None]
            if ts:
                t = min(ts)
                if t <= r + ke: om += 1
                lun = max(lun, (r - t) * 1000)
    return 100.0 * om / (3 * so_tia), lun

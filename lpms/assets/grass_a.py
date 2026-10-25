"""CỎ A — «lá gấp origami» (Boss 23/10: «cỏ này xấu nha, ko hợp cozy… tự tạo cỏ, tự animation nhẹ»).
Bụi 3–6 LÁ RỘNG gấp nếp giữa như giấy cắt, ngả ra ngoài 18–40°, đoạn trên cong thêm; 2 dải màu/lá (gốc co_goc → ngọn),
lá sau/trong ngọn co_giua, lá trước/ngoài ngọn co_ngon ⇒ 3 tông phẳng. 12 tam giác/lá. BIEN = S|M|L (2–3 cỡ cho rải)."""
from lpms_helpers import *
BIEN = "M"
CO = dict(S=(3, 0.20, 0.085, 5), M=(5, 0.30, 0.10, 7), L=(6, 0.40, 0.12, 9))    # số lá, cao, rộng, seed
META = dict(ten=f"grass_a_{BIEN.lower()}", dat=True, ngan_sach=80)


def build():
    n, H, W, sd = CO[BIEN]; rng = np.random.default_rng(sd); p = {}
    for k in range(n):
        yaw = 2 * math.pi * k / n + rng.uniform(-0.35, 0.35)
        ngoai = k % 2 == 0                                                   # lá ngoài sáng hơn, ngả nhiều hơn
        h = H * rng.uniform(0.75, 1.0) * (0.85 if ngoai else 1.0)
        r = 0.012 + 0.01 * rng.random()
        duoi, tren = la_gap((r * math.cos(yaw), r * math.sin(yaw)), yaw, rng.uniform(26, 40) if ngoai else rng.uniform(14, 22), h,
                            W * rng.uniform(0.85, 1.1), "co_goc", "co_ngon" if ngoai else "co_giua", cong=rng.uniform(10, 22))
        p[f"la_{k}_goc"] = duoi; p[f"la_{k}_ngon"] = tren
    return p

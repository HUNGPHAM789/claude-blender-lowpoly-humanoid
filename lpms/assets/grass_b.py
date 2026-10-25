"""CỎ B — «ụ cỏ tròn» (Boss 23/10 cozy grass): ụ low-poly mềm (khối méo dẹt, mặt to) + váy tối sát đất + mũ sáng lệch sáng,
vài ngọn lá chóp nhô lên. 3 tông phẳng: co_goc (váy) · co_giua (ụ) · co_ngon (mũ + ngọn). BIEN = S|M|L."""
from lpms_helpers import *
BIEN = "M"
CO = dict(S=(0.13, 2, 11), M=(0.19, 3, 12), L=(0.26, 4, 13))     # bán kính ụ, số ngọn, seed
META = dict(ten=f"grass_b_{BIEN.lower()}", dat=True, ngan_sach=80)


def build():
    R, n, sd = CO[BIEN]; rng = np.random.default_rng(sd); p = {}
    p["vay"] = khoi_meo((0, 0, 0.0), R * 1.02, "co_goc", seed=sd, meo=0.08, n=8, det=(1, 1, 0.30))
    p["u"] = khoi_meo((0, 0, R * 0.12), R, "co_giua", seed=sd + 1, meo=0.08, n=12, det=(1, 1, 0.72))
    if BIEN != "S":
        p["mu"] = khoi_meo((-0.18 * R, -0.12 * R, R * 0.42), R * 0.52, "co_ngon", seed=sd + 2, meo=0.10, n=7, det=(1, 1, 0.55))
    for k in range(n):
        a = 2 * math.pi * k / n + rng.uniform(-0.4, 0.4); r = R * rng.uniform(0.25, 0.55)
        x, y = r * math.cos(a), r * math.sin(a); z0 = R * 0.35; h = R * rng.uniform(0.75, 1.05); w = R * 0.32
        tl = (math.cos(a + 1.57) * w / 2, math.sin(a + 1.57) * w / 2)
        tip = (x + math.cos(a) * h * 0.45, y + math.sin(a) * h * 0.45, z0 + h)
        p[f"ngon_{k}"] = khoi([(x - tl[0], y - tl[1], z0), (x + tl[0], y + tl[1], z0), (x - math.cos(a) * w * 0.35, y - math.sin(a) * w * 0.35, z0 - 0.01), tip], "co_ngon")
    for m in p.values(): m.vertices[:, 2] = np.maximum(m.vertices[:, 2], -0.01)   # đáy phẳng, vùi 1 cm
    return p

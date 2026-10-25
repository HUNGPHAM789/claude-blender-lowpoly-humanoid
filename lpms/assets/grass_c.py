"""CỎ C — «lá cao thưa + chấm hoa» (Boss 23/10 cozy grass): 2–4 lá mảnh cao gấp nếp, cong ra ngoài (co_goc → co_ngon),
1–2 cọng hoa (thân 3 cạnh co_giua + đầu hoa bát diện 8 mặt màu kem/vàng/hồng phấn). BIEN = S|M|L."""
from lpms_helpers import *
BIEN = "M"
CO = dict(S=(2, 0.36, 1, 21), M=(3, 0.50, 1, 22), L=(4, 0.62, 2, 23))     # số lá, cao, số hoa, seed
META = dict(ten=f"grass_c_{BIEN.lower()}", dat=True, ngan_sach=80)
HOA = ("hoa_kem", "hoa_vang", "hoa_hong")


def build():
    n, H, nh, sd = CO[BIEN]; rng = np.random.default_rng(sd); p = {}
    for k in range(n):
        yaw = 2 * math.pi * k / n + rng.uniform(-0.5, 0.5)
        duoi, tren = la_gap((0.01 * math.cos(yaw), 0.01 * math.sin(yaw)), yaw, rng.uniform(10, 22), H * rng.uniform(0.7, 1.0), 0.04,
                            "co_goc", "co_ngon", cong=rng.uniform(18, 30), tram=0.55, rong_goc=0.7)
        p[f"la_{k}_goc"] = duoi; p[f"la_{k}_ngon"] = tren
    for j in range(nh):
        a = rng.uniform(0, 2 * math.pi); g = np.array((0.03 * math.cos(a), 0.03 * math.sin(a), -0.01))
        dinh = g + np.array((0.06 * math.cos(a), 0.06 * math.sin(a), H * rng.uniform(0.75, 0.95)))
        p[f"than_hoa_{j}"] = ong(g, dinh, 0.006, 0.004, "co_giua", n=3)
        r = 0.028; c = dinh + np.array((0, 0, r * 0.5))
        p[f"hoa_{j}"] = khoi([c + v for v in (np.eye(3) * r).tolist() + (-np.eye(3) * r * np.array((1, 1, 0.7))).tolist()], HOA[(sd + j) % 3])
    return p

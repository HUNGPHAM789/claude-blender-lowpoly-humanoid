"""Cụm đá lớn ~2,4 m (mỏ đá cho cuốc chim): 3 tảng cao thấp + đá vụn chân."""
from lpms_helpers import *
META = dict(ten="rock_large", dat=True, ngan_sach=450)


def build():
    def vui(m, mau):
        v = m.vertices.copy(); v[:, 2] = np.maximum(v[:, 2], -0.02); return khoi(v, mau)
    p = {"tang_cao": vui(khoi_meo((0, 0, 0.9), 0.85, "da", seed=51, meo=0.18, n=14, det=(0.9, 0.8, 1.25)), "da"),
         "tang_trai": vui(khoi_meo((-0.95, 0.3, 0.45), 0.6, "da_sang", seed=52, meo=0.22, n=12, det=(1.1, 0.9, 0.8)), "da_sang"),
         "tang_phai": vui(khoi_meo((0.85, -0.35, 0.35), 0.5, "da", seed=53, meo=0.22, n=12, det=(1, 1, 0.75)), "da")}
    for k, c in enumerate([(0.3, 0.95, 0.06), (-0.5, -0.8, 0.05), (1.35, 0.35, 0.05), (-1.5, -0.3, 0.06)]):
        p[f"vun_{k}"] = vui(khoi_meo(c, 0.13, "da_sang", seed=60 + k, meo=0.25, n=8, det=(1, 1, 0.6)), "da_sang")
    return p

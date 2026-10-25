"""Bạch dương ~7 m: thân trắng mảnh hơi nghiêng, tán thuôn dài lá vàng-xanh."""
from lpms_helpers import *
META = dict(ten="tree_birch", dat=True, ngan_sach=400)


def build():
    p = {"than": ong((0, 0, -0.02), (0.15, 0, 4.8), 0.13, 0.06, "vo_bach", n=6),
         "canh": ong((0.08, 0, 3.2), (0.7, 0.2, 4.2), 0.05, 0.03, "vo_bach", n=4)}
    for k, (c, r, det) in enumerate([((0.15, 0, 5.2), 0.95, (1, 1, 1.9)), ((0.6, 0.2, 4.4), 0.7, (1, 1, 1.4)), ((-0.25, -0.1, 4.2), 0.65, (1, 1, 1.5))]):
        p[f"tan_{k}"] = khoi_meo(c, r, "la_vang" if k == 0 else "la", seed=20 + k, meo=0.08, n=18, det=det)
    return p

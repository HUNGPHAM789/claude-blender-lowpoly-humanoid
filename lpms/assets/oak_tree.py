"""Cây sồi tán tròn ~5 m: thân to, 2 cành chạc, tán = 5 khối méo chồng nhau."""
from lpms_helpers import *
META = dict(ten="oak_tree", dat=True, ngan_sach=500)


def build():
    p = {"than": ong((0, 0, -0.02), (0, 0, 2.3), 0.28, 0.20, "go", n=7),
         "re": khoi_meo((0, 0, 0.09), 0.42, "go", seed=9, meo=0.15, n=10, det=(1, 1, 0.25)),
         "canh_a": ong((0, 0, 2.1), (0.9, 0.3, 3.1), 0.14, 0.07, "go", n=5),
         "canh_b": ong((0, 0, 2.2), (-0.7, -0.5, 3.2), 0.13, 0.07, "go", n=5)}
    # tán = 1 khối chính TRÒN + 2 khối phụ (bản 5 khối chồng nhau trông như giấy vo — 22/10)
    for k, (c, r, n) in enumerate([((0.1, 0.0, 3.7), 1.65, 30), ((1.05, 0.35, 3.25), 0.95, 18), ((-0.95, -0.4, 3.35), 0.9, 18)]):
        p[f"tan_{k}"] = khoi_meo(c, r, "la" if k == 0 else "la_toi", seed=10 + k, meo=0.06, n=n, det=(1, 1, 0.8))
    return p

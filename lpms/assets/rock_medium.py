"""Đá vừa ~1,1 m: khối chính + khối phụ tựa vào, mảng rêu trên đỉnh."""
from lpms_helpers import *
META = dict(ten="rock_medium", dat=True, ngan_sach=300)


def build():
    def vui(m, mau):
        v = m.vertices.copy(); v[:, 2] = np.maximum(v[:, 2], -0.02); return khoi(v, mau)
    return {"da_chinh": vui(khoi_meo((0, 0, 0.30), 0.62, "da", seed=41, meo=0.2, n=13, det=(1.0, 0.85, 0.75)), "da"),
            "da_phu": vui(khoi_meo((0.55, 0.25, 0.10), 0.32, "da_sang", seed=42, meo=0.25, n=10, det=(1, 1, 0.7)), "da_sang"),
            "reu": khoi_meo((-0.05, 0.0, 0.72), 0.30, "reu", seed=43, meo=0.15, n=9, det=(1.1, 0.9, 0.25))}

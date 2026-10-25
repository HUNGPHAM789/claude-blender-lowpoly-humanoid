"""Đá nhỏ ~0,5 m: một khối méo dẹt, nửa vùi."""
from lpms_helpers import *
META = dict(ten="rock_small", dat=True, ngan_sach=200)


def build():
    m = khoi_meo((0, 0, 0.0), 0.28, "da", seed=31, meo=0.15, n=18, det=(1.1, 0.9, 0.75))
    m.vertices[:, 2] = np.maximum(m.vertices[:, 2] + 0.08, -0.02)      # mặt đáy phẳng, vùi 2 cm
    return {"da": khoi(m.vertices, "da")}

"""Cây thông ~6 m: thân thon + 4 tầng nón lệch nhau. Đặt trên đất (z=0)."""
from lpms_helpers import *
META = dict(ten="pine_tree", dat=True, ngan_sach=400)
CAO = 6.0


def build():
    p = {"than": ong((0, 0, -0.02), (0, 0, CAO * 0.55), 0.16, 0.07, "go_toi", n=6)}
    tang = [(0.18, 0.55, 1.45), (0.36, 0.70, 1.15), (0.53, 0.84, 0.85), (0.68, 1.0, 0.55)]   # (đáy, đỉnh) theo phần cao, bán kính
    for k, (d, t, r) in enumerate(tang):
        p[f"la_{k}"] = non(CAO * d, CAO * t, r, "la_toi" if k % 2 else "la", n=7, seed=k, xoay=0.4 * k)
    return p

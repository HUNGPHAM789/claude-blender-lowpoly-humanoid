"""Khúc gỗ VÁC VAI (Boss 22/10: «miếng gỗ carry bự hơn dài hơn chút, hay là 3 miếng chồng hình tam giác… setup sẵn để sau này upgrade
wood carry capacity 1 plank, 2 plank, 3 plank»). Một khúc: trục +Z (giống khuc_go cũ), tâm ở gốc toạ độ. Cảnh ghép 1/2/3 khúc (chop_tree_scene.py --khuc N).
Đầu khúc lộ ruột gỗ như gốc cây: dác kem, lõi nâu cam, viền vỏ; một mấu cành cụt cho đỡ trơn."""
from lpms_helpers import *

META = dict(ten="carried_log", cam=False, ngan_sach=400)
R, L = 0.10, 1.45   # khúc cũ r 0,075 · dài 1,2


def build():
    p = {"vo": ong((0, 0, -L / 2), (0, 0, L / 2), R, R * 0.93, "go", n=9)}
    for k, s in enumerate((-1, 1)):
        z = s * L / 2; r_ = R if s < 0 else R * 0.93
        p[f"dac_{k}"] = ong((0, 0, z - s * 0.002), (0, 0, z + s * 0.004), r_ * 0.84, r_ * 0.84, "may", n=9)
        p[f"loi_{k}"] = ong((0, 0, z), (0, 0, z + s * 0.006), r_ * 0.40, r_ * 0.40, "dong", n=7)
    p["mau_canh"] = ong((0.0, 0.07, 0.25), (0.0, 0.16, 0.33), 0.03, 0.022, "go", n=5)
    return p

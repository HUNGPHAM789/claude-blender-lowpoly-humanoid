"""Cuốc chim lưỡi liềm đập đá (Boss 22/10). Hợp đồng cầm: gốc = chỗ cầm, cán +Z, lưỡi +X."""
from lpms_helpers import *

META = dict(ten="pickaxe", cam=True, ngan_sach=600)
Z = 0.80          # độ cao đầu cuốc trên cán
CONG = 1.25       # độ cong lưỡi liềm: z = Z − CONG·x²
DAI = (0.30, 0.28)  # mũi trước / mũi sau


def build():
    p = {"can": ong((0, 0, -0.14), (0, 0, Z + 0.02), 0.015, 0.018, "go"),
         "khau": ong((0, 0, Z - 0.035), (0, 0, Z + 0.045), 0.026, 0.026, "sat")}
    for ten, L, s in (("truoc", DAI[0], 1), ("sau", DAI[1], -1)):
        xs = np.linspace(0, L, 7) * s
        duong = [(x, 0, Z + 0.02 - CONG * x * x) for x in xs]
        k = [0.032 * (1 - abs(x) / L) + 0.004 for x in xs]
        for kk, m in quet([(1, 0), (0, 0.75), (-1, 0), (0, -0.75)], duong, "sat", ti_le=k).items():
            p[f"mui_{ten}_{kk}"] = m
    return p

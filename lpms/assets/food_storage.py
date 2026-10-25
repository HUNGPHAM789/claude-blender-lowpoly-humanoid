"""KHO THỨC ĂN HỞ kệ 2 bậc (Boss 23/10/2026: «Dựng… kho thuc an») — ĐÚNG SPEC Codex `~/projects/GameDev/concept/food/SPEC.md` §2
(concept food_storage.png). 6 rổ đan bát giác (3 dưới z0,42 · 3 trên z0,88), mỗi ô 6 quả = 36 đơn vị; quả là bộ phận dau_<ô>_<k> (ẩn theo kho Q:
ô i có clamp(Q−6i,0,6) quả, lấy ra từ ô cao nhất, quả cao nhất). Điểm gửi: đứng (0,−0.96,0) quay +Y, đặt rổ (0,−0.30,0.42)."""
import math
import numpy as np
from lpms_helpers import *

META = dict(ten="food_storage", dat=True, ngan_sach=3400)
HANG = {"duoi": (-0.30, 0.42), "tren": (0.27, 0.88)}
O = [(-0.51, -0.30, 0.42), (0, -0.30, 0.42), (0.51, -0.30, 0.42), (-0.51, 0.27, 0.88), (0, 0.27, 0.88), (0.51, 0.27, 0.88)]
F = [(-0.072, -0.060, 0.100), (0.072, -0.060, 0.100), (0, 0.066, 0.100), (-0.070, 0.047, 0.145), (0.070, 0.047, 0.145), (0, -0.018, 0.196)]


def B(c, sx, sy, sz, mau):
    return khoi([(c[0] + a * sx / 2, c[1] + b * sy / 2, c[2] + d * sz / 2) for a in (-1, 1) for b in (-1, 1) for d in (-1, 1)], mau)


def P(r, t, z): return (r * math.cos(t), r * math.sin(t), z)


def Wd(r0, r1, z0, z1, t0, t1, d, goc, mau):
    pts = [P(r0, t0, z0), P(r0, t1, z0), P(r1, t0, z1), P(r1, t1, z1), P(r0 - d, t0, z0), P(r0 - d, t1, z0), P(r1 - d, t0, z1), P(r1 - d, t1, z1)]
    return khoi([(x + goc[0], y + goc[1], z + goc[2]) for x, y, z in pts], mau)


def build():
    p = {}
    for ten, (Y, H) in HANG.items():
        for k, q in enumerate((-0.16, 0, 0.16)): p[f"van_{ten}_{k}"] = B((0, Y + q, H - 0.025), 1.60, 0.15, 0.05, "go_sang")
        p[f"diem_truoc_{ten}"] = B((0, Y - 0.215, H - 0.075), 1.60, 0.055, 0.10, "go_sang")
        p[f"diem_sau_{ten}"] = B((0, Y + 0.215, H - 0.075), 1.60, 0.055, 0.10, "go")
        for x in (-0.78, 0.78):
            for y in (Y - 0.225, Y + 0.225):
                p[f"chan_{ten}_{x:+.2f}_{y:+.3f}"] = ong((x, y, 0), (x, y, H + 0.035), 0.060, 0.052, "go_sang")
                for j in range(6):
                    t = 2 * math.pi * j / 6; p[f"dai_{ten}_{x:+.2f}_{y:+.3f}_{j}"] = Wd(0.064, 0.064, H - 0.055, H - 0.020, t, t + 2 * math.pi / 6, 0.009, (x, y, 0), "day")
    for x in (-0.78, 0.78): p[f"thanh_noi_{x:+.2f}"] = B((x, -0.015, 0.23), 0.065, 1.02, 0.075, "go")
    for i, S in enumerate(O):
        p[f"ro_{i}_day"] = ong(S, (S[0], S[1], S[2] + 0.025), 0.140, 0.145, "may", n=8)
        for j in range(8):
            t = math.pi / 8 + j * math.pi / 4
            p[f"ro_{i}_than_{j}"] = Wd(0.145, 0.200, 0.025, 0.145, t, t + math.pi / 4, 0.015, S, "may")
            p[f"ro_{i}_mieng_{j}"] = Wd(0.209, 0.209, 0.135, 0.160, t, t + math.pi / 4, 0.024, S, "may")
        for k, f in enumerate(F): p[f"dau_{i}_{k}"] = cau((S[0] + f[0], S[1] + f[1], S[2] + f[2]), 0.064, "berry")
    return p

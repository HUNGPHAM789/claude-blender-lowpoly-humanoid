"""GÙI ĐEO LƯNG đan nan (Boss 23/10: «một cái backpack dạng rổ hay gì đó của thời này và small rocks ở trong? Cái này scaleable cho food,
rocks, fishes…»). RỖNG miệng trên để thấy hàng bên trong. Gốc = tâm đáy, trục +Z; mặt tì lưng = phía -Y. Nan đứng + 3 đai ngang + đáy.
Hàng chở xếp vào LÒNG (bán kính trong ở cao z: R_TRONG(z)) — cảnh đọc R_DAY/R_MIENG/CAO từ META."""
import math
from lpms_helpers import *

R_DAY, R_MIENG, CAO, DAY_NAN = 0.11, 0.175, 0.40, 0.012
META = dict(ten="back_basket", dat=True, ngan_sach=900, r_day=R_DAY, r_mieng=R_MIENG, cao=CAO)
N_NAN = 16


def r_z(z): return R_DAY + (R_MIENG - R_DAY) * z / CAO


def build():
    p = {"day": ong((0, 0, 0), (0, 0, 0.018), R_DAY, R_DAY, "go", n=N_NAN)}
    for k in range(N_NAN):   # nan đứng: dải mỏng nghiêng theo thành, khe hở 35% cho thấy đan
        a0 = 2 * math.pi * k / N_NAN; a1 = a0 + 2 * math.pi / N_NAN * 0.65; pts = []
        for z in (0.0, CAO):
            for a in (a0, a1):
                for dr in (0.0, -DAY_NAN): r = r_z(z) + dr; pts.append((r * math.cos(a), r * math.sin(a), z))
        p[f"nan_{k}"] = khoi(pts, "may" if k % 2 else "go_sang")
    for j, z in enumerate((0.06, CAO * 0.5, CAO - 0.025)):   # đai ngang hơi nhô ngoài
        n = N_NAN; r = r_z(z) + 0.006
        for k in range(n):
            a0, a1 = 2 * math.pi * k / n, 2 * math.pi * (k + 1) / n
            p[f"dai_{j}_{k}"] = khoi([(rr * math.cos(a), rr * math.sin(a), zz) for a in (a0, a1) for rr in (r, r - 0.016) for zz in (z - 0.013, z + 0.013)], "go")
    return p

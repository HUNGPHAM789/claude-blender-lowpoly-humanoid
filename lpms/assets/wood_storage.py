"""KHO GỖ HỞ (Boss 23/10: «open storage (visible what are being stored)»). Không vách, không mái: nền đất nện + 2 thanh kê + 4 cọc giữ biên
lớp đáy. Gỗ nằm dọc trục Y, chồng tháp 5-4-3-2-1 (15 khúc) — vị trí ô lấy từ skill settler-storage/scripts/storage.py (một nguồn sự thật)."""
import os, sys, math
sys.path.insert(0, os.path.expanduser("~/.hermes/skills/creative/settler-storage/scripts"))
import storage as kho
from lpms_helpers import *

META = dict(ten="wood_storage", dat=True, ngan_sach=600)
R = kho.R_GO; NUA = 5 * R            # nửa bề rộng lớp đáy
COC_X = NUA + 0.036; COC_R = 0.035


def build():
    p = {"nen": khoi([(x, y, z) for x in (-0.78, 0.78) for y in (-0.92, 0.92) for z in (-0.02, 0.0)], "da_sang")}
    for k, y in enumerate((-0.5, 0.5)):   # thanh kê ngang dưới lớp đáy (gỗ không chạm đất ẩm)
        p[f"ke_{k}"] = khoi([(x, y + dy, z) for x in (-0.68, 0.68) for dy in (-0.06, 0.06) for z in (0.0, kho.Z0)], "go_toi")
    for k, (sx, y) in enumerate([(sx, y) for sx in (-1, 1) for y in (-0.5, 0.5)]):   # cọc biên nghiêng ra ngoài 6°
        x0 = sx * COC_X; p[f"coc_{k}"] = ong((x0, y, 0.0), (x0 + sx * 0.06, y, 0.62), COC_R, COC_R * 0.85, "go", n=6)
    return p

"""THÙNG ĐÁ HỞ (Boss 23/10: đá «stack đc nhìu hơn ở storage… per slot»). Sàn gỗ + vách thấp 4 phía (thấp hơn đống để THẤY hàng trong kho)
+ 4 cọc góc. Lòng thùng/sàn lấy từ settler-storage/scripts/storage.py (NUA_THUNG, Z0) — một nguồn sự thật; đống 4-3-2-1 = 30 cục/ô."""
import os, sys
sys.path.insert(0, os.path.expanduser("~/.hermes/skills/creative/settler-storage/scripts"))
import storage as kho
from lpms_helpers import *

META = dict(ten="stone_storage", dat=True, ngan_sach=300)
N = kho.NUA_THUNG; T = 0.03; H = kho.Z0 + 0.15


def build():
    p = {"san": khoi([(x, y, z) for x in (-N - T, N + T) for y in (-N - T, N + T) for z in (0.0, kho.Z0)], "go_toi")}
    for k, (sx, sy) in enumerate(((1, 0), (-1, 0), (0, 1), (0, -1))):
        if sx: pts = [(sx * x, y, z) for x in (N, N + T) for y in (-N - T, N + T) for z in (kho.Z0, H)]
        else: pts = [(x, sy * y, z) for x in (-N, N) for y in (N, N + T) for z in (kho.Z0, H)]
        p[f"vach_{k}"] = khoi(pts, "go")
    for k, (sx, sy) in enumerate([(sx, sy) for sx in (-1, 1) for sy in (-1, 1)]):
        c = (sx * (N + T * 0.5), sy * (N + T * 0.5)); p[f"coc_{k}"] = ong((*c, 0.0), (*c, H + 0.06), 0.028, 0.024, "go_sang", n=6)
    return p

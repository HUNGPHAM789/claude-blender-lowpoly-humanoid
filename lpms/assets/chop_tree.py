"""Cây để CHẶT (Boss 22/10: «4 cú rung, cú swing thứ 5 cây gãy… còn gốc cây… cây ngã physics»).
Thân thẳng r 0,2 m (khớp cây trụ cảnh chặt), cao 3,2 m, rễ loe, tán lá trên đỉnh lệch nhẹ. Vết khuyết + chỗ gãy do cảnh Blender cắt
(chop_tree_scene.py); asset này là cây NGUYÊN. Bộ phận tên than* = gỗ (bị cắt), tan* = lá (đi theo phần ngã)."""
import math
from lpms_helpers import *

META = dict(ten="chop_tree", dat=True, ngan_sach=900, bao_tan=dict(tam=(0.0, 0.0, 3.6), ban_kinh=(1.05, 1.05, 0.95)))
R, CAO = 0.20, 3.2


def build():
    p = {"than": ong((0, 0, -0.02), (0, 0, CAO), R, 0.13, "go", n=9),
         "re": khoi_meo((0, 0, 0.06), 0.30, "go", seed=4, meo=0.15, n=12, det=(1, 1, 0.22)),
         "than_canh_a": ong((0, 0, 2.5), (0.55, 0.15, 3.25), 0.07, 0.04, "go", n=5),
         "than_canh_b": ong((0, 0, 2.7), (-0.45, -0.25, 3.35), 0.06, 0.035, "go", n=5)}
    # TÁN (Boss 23/10 «chỗ lồi ra như cái sừng… 2 màu nhưng ko phải 1 vệt lồi màu đậm»): 1 khối chính + 6 cụm SÁNG chồng sâu, tất cả trong
    # vỏ bao bầu dục (cửa lpms «tán không sừng» ≤ 1,10×); 2 tông theo ÁNH SÁNG = đĩa bóng đậm dẹt dưới đáy tán, chỉ lộ ở mặt dưới
    p["tan_chinh"] = khoi_meo((0.0, 0.0, 3.7), 0.86, "la", seed=20, meo=0.06, n=30, det=(1, 1, 0.86))
    for k in range(5):
        a = 2 * math.pi * k / 5 + 0.4
        p[f"tan_cum_{k}"] = khoi_meo((0.42 * math.cos(a), 0.42 * math.sin(a), 3.78 + 0.06 * (k % 2)), 0.52, "la", seed=30 + k, meo=0.07, n=16, det=(1, 1, 0.85))
    p["tan_dinh"] = khoi_meo((0.05, 0.0, 4.06), 0.46, "la", seed=40, meo=0.07, n=16, det=(1, 1, 0.85))
    p["tan_bong_toi"] = khoi_meo((0.0, 0.0, 3.26), 0.62, "la_toi", seed=41, meo=0.05, n=20, det=(1, 1, 0.45))   # nhỏ hơn khối sáng ⇒ tán sáng phủ trùm, chỉ lộ viền dưới
    return p

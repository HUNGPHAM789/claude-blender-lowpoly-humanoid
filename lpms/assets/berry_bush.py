"""BỤI BERRY (Boss 23/10/2026: «Dựng berry bush… ship với mat C») — dựng ĐÚNG SPEC Codex `~/projects/GameDev/concept/food/SPEC.md` §1
(concept berry_bush.png). 6 thuỳ lá (khối L tất định), gốc + 3 nhánh, 9 chùm × 3 quả (bộ phận qua_*). Trạng thái ĐÃ HÁI = ẩn mọi qua_*.
Thứ tự hái từng chùm: 6,7,8,4,5,3,1,2,0. Điểm đứng hái (nữ, tay không): (0,−0.77,0) quay +Y; đích tay (0,−0.25,0.66)…"""
import math
import numpy as np, trimesh
from lpms_helpers import *

META = dict(ten="berry_bush", dat=True, ngan_sach=1500)
THU_TU_HAI = (6, 7, 8, 4, 5, 3, 1, 2, 0)


def L(c, rx, ry, rz, mau):
    """THUỲ LÁ = cầu đa diện chia 1 (42 đỉnh) kéo dãn (rx, ry, rz). LỆCH SPEC có chủ ý: khối 14 điểm của SPEC ra hình THOI nhọn,
    concept là thuỳ TRÒN kiểu geodesic (so ảnh 23/10). Tâm/bán kính giữ đúng SPEC."""
    v = trimesh.creation.icosphere(subdivisions=1, radius=1.0).vertices * np.array((rx, ry, rz)) + np.asarray(c, float)
    return khoi(v, mau)


def tia(m, o, d):
    """Möller–Trumbore bằng numpy (máy không có rtree): khoảng cách chạm GẦN nhất theo d, hoặc None."""
    tri = m.triangles; e1, e2 = tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0]; pv = np.cross(d, e2); det = np.einsum("ij,ij->i", e1, pv)
    ok = np.abs(det) > 1e-12; inv = np.where(ok, 1 / np.where(ok, det, 1), 0); tv = o - tri[:, 0]
    u = np.einsum("ij,ij->i", tv, pv) * inv; qv = np.cross(tv, e1); v = (qv @ d) * inv; t = np.einsum("ij,ij->i", e2, qv) * inv
    h = ok & (u >= 0) & (v >= 0) & (u + v <= 1) & (t > 0)
    return float(t[h].min()) if h.any() else None


CUM = [((0, -0.035, 0.844), (0, -0.35, 0.93675)), ((-0.36, 0.115, 0.725), (-0.40, -0.20, 0.89443)), ((0.36, 0.115, 0.725), (0.40, -0.20, 0.89443)),
       ((0, -0.225, 0.655), (0, -0.80, 0.60)), ((-0.405, -0.245, 0.585), (-0.50, -0.65, 0.57228)), ((0.405, -0.245, 0.585), (0.50, -0.65, 0.57228)),
       ((0, -0.345, 0.555), (0, -0.70, 0.71414)), ((-0.23, -0.32, 0.425), (-0.20, -0.85, 0.48734)), ((0.23, -0.32, 0.425), (0.20, -0.85, 0.48734))]


def build():
    p = {"goc": ong((0, 0, 0), (0, 0, 0.32), 0.075, 0.045, "go"),
         "nhanh_trai": ong((0, 0, 0.09), (-0.27, 0, 0.38), 0.045, 0.025, "go"),
         "nhanh_phai": ong((0, 0, 0.09), (0.27, 0.02, 0.38), 0.045, 0.025, "go"),
         "nhanh_sau": ong((0, 0, 0.19), (0, 0.22, 0.48), 0.032, 0.018, "go_toi"),
         "la_dinh": L((0, 0.04, 0.64), 0.30, 0.29, 0.26, "la"),
         "la_truoc_trai": L((-0.30, -0.12, 0.47), 0.25, 0.27, 0.22, "la"),
         "la_truoc_phai": L((0.30, -0.12, 0.47), 0.25, 0.27, 0.22, "la"),
         "la_truoc_giua": L((0, -0.23, 0.43), 0.25, 0.22, 0.18, "la"),
         "la_sau_trai": L((-0.27, 0.20, 0.59), 0.22, 0.23, 0.19, "la_toi"),
         "la_sau_phai": L((0.27, 0.20, 0.59), 0.22, 0.23, 0.19, "la")}
    la = trimesh.util.concatenate([m for k, m in p.items() if k.startswith("la_")])
    for i, (C, N) in enumerate(CUM):   # bám quả lên MẶT lá: tia từ C+0,2N theo −N, lấy chạm đầu + 0,022N (SPEC §1)
        N = np.asarray(N, float); N /= np.linalg.norm(N); C = np.asarray(C, float)
        t_ = tia(la, C + 0.20 * N, -N)
        if t_ is not None: C = C + 0.20 * N - N * t_ + 0.022 * N
        U = np.cross((0, 0, 1.0), N); U /= np.linalg.norm(U); Vv = np.cross(N, U)
        for k, o in enumerate((-0.033 * U - 0.019 * Vv, 0.033 * U - 0.019 * Vv, 0.038 * Vv)):
            p[f"qua_{i}_{k}"] = cau(C + o, 0.035, "berry")
    return p

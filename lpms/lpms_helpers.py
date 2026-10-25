"""Hàm dựng cho chương trình asset LPM Studio — `lpms discover <từ>` tìm trong docstring ở đây (kiểu kiln_discover).
Hệ toạ độ asset: mét, Z lên. Món cầm tay theo HỢP ĐỒNG CẦM: gốc = tâm chỗ cầm, cán = +Z, phía làm việc = +X.
Màu: bảng MAU nhà (sRGB ghi thẳng — Boss 22/10 «tôi thích màu bên mình hơn»)."""
import math, os, sys
import numpy as np, trimesh
sys.path.insert(0, os.path.expanduser("~/projects/lpm-faceless-humanoid/theme")); import theme_colors as TM   # theme màu dùng chung (Boss 23/10: áp tông nai B cho cả game)
from scipy.spatial import ConvexHull

MAU = {"da_lua": [140, 134, 124, 255],   # đá lửa đầu spear/tên — bảng tools.py gọi là «da» (140,134,124) ≠ «da» ở đây (112,106,98); 23/10 giá vũ khí lộ ra
       "go": [128, 92, 58, 255], "go_sang": [170, 130, 84, 255], "sat": [118, 122, 128, 255], "da": [112, 106, 98, 255],
       "may": [196, 164, 108, 255], "berry": [150, 30, 52, 255], "berry2": [70, 40, 110, 255], "day": [225, 220, 205, 255],
       "long": [215, 210, 200, 255], "dong": [176, 120, 72, 255],
       "la": [86, 124, 60, 255], "la_toi": [58, 92, 52, 255], "la_vang": [150, 140, 64, 255], "vo_bach": [214, 208, 196, 255],
       # WORLD COLOR SPEC V1 (Boss 25/10/2026 «dùng mã màu này» — specs/WORLD_COLOR_SPEC_V1.png): trees, stone, grass, sand, dirt, deer
       # (supersedes the Ghibli match of the same day). Non-V1 pack colours (rope, berries, mushrooms, flowers) stay below.
       "yk_la_sang": [128, 167, 76, 255], "yk_la": [100, 138, 56, 255], "yk_la_dam": [60, 98, 43, 255], "yk_vo_sang": [138, 100, 66, 255],
       "yk_vo": [104, 72, 46, 255], "yk_vo_dam": [76, 52, 33, 255], "yk_go_cat": [138, 100, 66, 255], "yk_da_sang": [169, 162, 148, 255],
       "yk_da": [128, 122, 112, 255], "yk_da_dam": [97, 92, 84, 255], "yk_vach": [128, 122, 112, 255], "yk_reu": [89, 115, 74, 255],
       "yk_co_sang": [159, 188, 91, 255], "yk_co": [127, 162, 72, 255], "yk_co_dam": [88, 117, 52, 255], "yk_co_kho": [179, 161, 91, 255],
       "yk_cat_sang": [227, 211, 165, 255], "yk_cat": [210, 190, 136, 255], "yk_cat_dam": [183, 157, 103, 255], "yk_dat_sang": [155, 122, 85, 255],
       "yk_dat": [123, 93, 62, 255], "yk_dat_dam": [93, 67, 45, 255], "yk_long_sang": [185, 137, 87, 255], "yk_long": [156, 108, 67, 255],
       "yk_long_dam": [110, 74, 46, 255], "yk_bung": [216, 176, 138, 255], "yk_sung": [213, 195, 154, 255],
       "yk_day": [163, 111, 47, 255], "yk_qua": [201, 42, 27, 255], "yk_nam_do": [228, 47, 16, 255], "yk_than_nam": [243, 234, 196, 255],
       "yk_nam_nau": [105, 64, 41, 255], "yk_nam_tim": [144, 79, 220, 255], "yk_nam_cam": [201, 134, 3, 255], "yk_hoa_hong": [245, 136, 250, 255],
       "yk_hoa_trang": [235, 235, 235, 255], "yk_nhuy": [255, 237, 0, 255], "yk_may": [248, 248, 248, 255],
       # firepit embers / flame (no fire in the pack — same saturated family: red/orange/yellow rows of its texture)
       "yk_than": [52, 46, 42, 255], "yk_lua": [242, 108, 24, 255], "yk_lua_vang": [255, 204, 0, 255],
       # leaf of the 3-branch oak (stylized_oak_v2 M_OakLeafUnified); Boss 25/10: birch leaves must match it
       "la_soi": [74, 136, 56, 255],
       # firepit (Boss 25/10 «ngoại trừ animal và settlers, và firepit»): charcoal bed, ash, flame outer/inner
       "than": [52, 46, 42, 255], "tro": [128, 120, 110, 255], "lua": [232, 112, 44, 255], "lua_vang": [248, 200, 92, 255],
       "go_toi": [96, 70, 50, 255], "da_sang": [138, 132, 122, 255], "reu": [96, 116, 64, 255],
       # cozy grass (Boss 23/10 «cỏ này xấu… ko hợp cozy»): 3 flat bands root→tip, warm sage/olive (not neon) + flower dots
       "co_goc": [66, 92, 48, 255], "co_giua": [98, 128, 62, 255], "co_ngon": [148, 158, 86, 255],
       "hoa_kem": [236, 222, 182, 255], "hoa_vang": [226, 188, 96, 255], "hoa_hong": [206, 140, 128, 255],
       # meat (meat_storage, Boss 23/10 «Storage stacking display thịt»): smoked haunch, lighter cut face, fat, bone
       "thit": [128, 50, 38, 255], "thit_tuoi": [172, 76, 62, 255], "mo": [226, 204, 172, 255], "xuong": [222, 210, 184, 255]}


def _to(m, mau):
    m.visual = trimesh.visual.TextureVisuals(material=trimesh.visual.material.PBRMaterial(
        name=mau, baseColorFactor=TM.mau(MAU[mau]), metallicFactor=0.3 if mau in ("sat", "dong") else 0.0, roughnessFactor=0.8))
    return m


def khoi(pts, mau):
    """KHỐI LỒI qua tập điểm (convex hull) — khối cứng kín. Dùng cho lưỡi, đầu búa, nêm, hộp vát."""
    p = np.asarray(pts, float); m = trimesh.Trimesh(p, ConvexHull(p).simplices, process=True); m.fix_normals()
    return _to(m, mau)


def ong(a, b, r0, r1, mau, n=6):
    """LĂNG TRỤ n cạnh từ điểm a tới b, bán kính r0→r1 (cán, thân, ống thon). Kín."""
    a, b = np.asarray(a, float), np.asarray(b, float); t = (b - a) / np.linalg.norm(b - a)
    u = np.cross(t, (0, 0, 1.0) if abs(t[2]) < 0.9 else (1.0, 0, 0)); u /= np.linalg.norm(u); v = np.cross(t, u)
    return khoi([c + r * (math.cos(2 * math.pi * k / n) * u + math.sin(2 * math.pi * k / n) * v) for c, r in ((a, r0), (b, r1)) for k in range(n)], mau)


def quet(bien_dang, duong, mau, ti_le=None):
    """QUÉT biên dạng 2D (u, v) dọc đường gấp khúc 3D, ti_le mỗi trạm — mượn ý sweepProfile của Kiln.
    Dựng thành CHUỖI KHỐI LỒI nối tiếp (mỗi khúc là hull của 2 mặt cắt) ⇒ mỗi khúc KÍN, cong mượt theo đường.
    Ví dụ: đầu cuốc chim lưỡi liềm, cánh cung, quai giỏ. Trả {tên_khúc: mesh}."""
    P = np.asarray(duong, float); s = ti_le or [1.0] * len(P); out = {}
    def mat(i):
        t = P[min(i + 1, len(P) - 1)] - P[max(i - 1, 0)]; t /= np.linalg.norm(t)
        u = np.cross(t, (0, 1.0, 0) if abs(t[1]) < 0.9 else (1.0, 0, 0)); u /= np.linalg.norm(u); v = np.cross(t, u)
        k = s[i] if np.ndim(s[i]) == 0 else s[i][0]
        return [P[i] + k * (a * u + b * v) for a, b in bien_dang]
    for i in range(len(P) - 1):
        out[f"khuc_{i}"] = khoi(mat(i) + mat(i + 1), mau)
    return out


def dun(bien_dang, day, mau, vat=0.0, truc="y"):
    """ĐÙN biên dạng 2D LỒI (x, z) dày `day` theo trục, vát mép `vat` — mượn extrudeProfile(bevel) của Kiln.
    Biên dạng lõm ⇒ chia thành nhiều phần lồi rồi gọi nhiều lần. Ví dụ: lưỡi rìu, lưỡi xẻng."""
    pts = []
    for a, b in bien_dang:
        for d, co in ((-day / 2, vat), (day / 2, vat), (-day / 2 + vat, 0), (day / 2 - vat, 0)):
            p = np.array((a, 0.0, b)); c = np.mean(bien_dang, 0); q = p - np.array((c[0], 0, c[1]))
            p = p - q / (np.linalg.norm(q) + 1e-9) * co
            p[1] = d; pts.append(p if truc == "y" else p[[0, 2, 1]])
    return khoi(pts, mau)


def cau(tam, r, mau):
    """CẦU low-poly (icosphere 20 mặt) — quả mọng, núm."""
    m = trimesh.creation.icosphere(subdivisions=0, radius=r); m.apply_translation(tam); return khoi(m.vertices, mau)


def khoi_meo(tam, ban_kinh, mau, seed=0, meo=0.25, n=14, det=(1, 1, 1)):
    """KHỐI MÉO lồi quanh tâm: n điểm trên cầu bị nhiễu bán kính ±meo, kéo giãn theo det (x, y, z) — ĐÁ, TÁN LÁ, bụi cây.
    Seed cố định ⇒ dựng lại ra y hệt. Kín, mặt to kiểu low-poly."""
    rng = np.random.default_rng(seed); v = rng.normal(size=(n, 3)); v /= np.linalg.norm(v, axis=1)[:, None]
    v *= (1 + rng.uniform(-meo, meo, (n, 1))) * ban_kinh; v *= np.asarray(det, float)
    return khoi(v + np.asarray(tam, float), mau)


def non(day_z, dinh_z, r, mau, n=7, seed=0, xoay=0.0):
    """NÓN n cạnh (tầng lá thông): đáy ở z=day_z bán kính r, đỉnh z=dinh_z; đáy hơi răng cưa theo seed."""
    rng = np.random.default_rng(seed)
    pts = [(r * (1 + rng.uniform(-.12, .12)) * math.cos(xoay + 2 * math.pi * k / n), r * (1 + rng.uniform(-.12, .12)) * math.sin(xoay + 2 * math.pi * k / n),
            day_z + rng.uniform(-.06, .06) * r) for k in range(n)]
    return khoi(pts + [(0, 0, dinh_z)], mau)


def la_gap(goc, yaw, nghieng, cao, rong, mau_duoi, mau_tren, cong=12.0, gap=0.35, tram=0.45, rong_goc=0.5):
    """LÁ GẤP origami (cỏ, lá dứa, lá non): dải thon có NẾP GẤP dọc giữa (mặt cắt chữ V, sâu gap·rộng), 2 đoạn màu
    gốc→tram (lăng trụ V, 8 tam giác, mau_duoi) và tram→ngọn (chóp 4 tam giác, mau_tren) = 12 tam giác/lá, mỗi đoạn kín.
    goc=(x,y) chân lá trên đất; yaw = hướng ngả (rad); nghieng = độ ngả khỏi trục đứng (độ); đoạn trên ngả thêm `cong` độ.
    rong = bề rộng ở trạm giữa (lá phình), gốc = rong_goc·rong. Dùng cho asset cỏ cozy (grass/cozy, Boss 23/10)."""
    d = np.array((math.cos(yaw), math.sin(yaw), 0.0)); u = np.array((-math.sin(yaw), math.cos(yaw), 0.0))   # u = ngang lá
    def truc(do):
        a = math.radians(do); return math.sin(a) * d + math.cos(a) * np.array((0, 0, 1.0))
    p0 = np.array((goc[0], goc[1], -0.01)); p1 = p0 + truc(nghieng) * cao * tram; p2 = p1 + truc(nghieng + cong) * cao * (1 - tram)
    def mat(p, w, t):
        n = np.cross(u, t); n /= np.linalg.norm(n)                     # pháp tuyến mặt lá; nếp lùi về phía sau
        return [p - u * w / 2, p + u * w / 2, p - n * gap * w]
    t0 = truc(nghieng); t1 = truc(nghieng + cong * 0.5)
    duoi = khoi(mat(p0, rong * rong_goc, t0) + mat(p1, rong, t1), mau_duoi)
    tren = khoi(mat(p1, rong, t1) + [p2], mau_tren)
    return duoi, tren

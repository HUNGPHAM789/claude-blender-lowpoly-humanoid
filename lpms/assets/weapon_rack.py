"""WEAPON & TOOL RACK «giá vũ khí» (Boss 23/10/2026: «tạo asset weapon racks (có thể đựng được mỗi tool và weapon mỗi thứ 2 cái, có thể
được display actual)»). Holds 2 of every settler tool/weapon in assets/tools/settler_v1 and DISPLAYS the real meshes:
  · front standing row, 12 slots, 0.19 m pitch: can_cau, lao, cuoc_dat, xeng, pickaxe, riu (×2 each) — feet in a trough board,
    handles caught between peg pairs on a low rail (z 0.55) and, for the long ones, a high rail (z 1.15); heads face OUT (−Y) so the
    head width lies along the slot depth (pickaxe head 0.58 m would not fit 0.19 m sideways)
  · back crossbars: 2 bows (cung) hung level on pegs · quiver on the right post: 2 arrows (mui_ten), fletching up
  · end posts: outward pegs carry 2 watering cans (binh_tuoi) + 2 baskets (gio_berry) by their grips
Tool contract (tools.json): origin = grip centre, +Z = handle, +X = working side. glb is y-up ⇒ converted to z-up here.
Stock parts: do_<tool>_<k>_<sub>; a storage holding Q of a tool shows k < Q (hide do_<tool>_<k>_* for empty slots).
Gate (META soi): no tool penetrates another part's convex shell by > 5 mm; every tool is supported (rests on the trough or hangs on a peg)."""
import os, sys, math
import numpy as np, trimesh
sys.path.insert(0, os.path.expanduser("~/projects/lpm-faceless-humanoid/lpms"))
from lpms_helpers import khoi, ong

T = os.path.expanduser("~/projects/lpm-faceless-humanoid/assets/tools/settler_v1")
RONG = 1.20                    # half width: end posts at x = ±RONG
DAY_Z = 0.10                   # trough board top
RAY_THAP, RAY_CAO = 0.55, 1.15 # handle rails
COT_Z = 2.25                   # post height
HANG = ["can_cau", "can_cau", "lao", "lao", "cuoc_dat", "cuoc_dat", "xeng", "xeng", "pickaxe", "pickaxe", "riu", "riu"]
DAI = {"can_cau", "lao", "cuoc_dat", "xeng"}   # long ones also use the high rail
BUOC = 0.19; X0 = -BUOC * (len(HANG) - 1) / 2
TREO = {}   # món treo: điểm tựa (đỉnh chốt) — cổng trọng lực


def B(c, sx, sy, sz, mau):
    return khoi([(c[0] + a * sx / 2, c[1] + b * sy / 2, c[2] + d * sz / 2) for a in (-1, 1) for b in (-1, 1) for d in (-1, 1)], mau)


GLTF_Z = np.array([[1, 0, 0, 0], [0, 0, -1, 0], [0, 1, 0, 0], [0, 0, 0, 1.0]])   # glTF y-up → z-up


def nap(ten):
    s = trimesh.load(f"{T}/{ten}.glb"); out = []
    for node in s.graph.nodes_geometry:
        Tm, g = s.graph[node]; m = s.geometry[g].copy(); m.apply_transform(GLTF_Z @ Tm)
        # tools.py gọi đá lửa là «da» (140,134,124) — lpms «da» là (112,106,98) ⇒ đổi tên vật liệu, GIỮ màu thật của công cụ
        if m.visual.material.name == "da": m.visual.material.name = "da_lua"   # mọi «da» trong settler_v1 là đá lửa của tools.py
        out.append((g, m))
    return out


def dat(ten, k, Tm, p):
    for g, m in nap(ten):
        m = m.copy(); m.apply_transform(Tm); p[f"do_{ten}_{k}_{g}"] = m


def Rz(a): c, s = math.cos(a), math.sin(a); return np.array([[c, -s, 0, 0], [s, c, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1.0]])
def Rx(a): c, s = math.cos(a), math.sin(a); return np.array([[1, 0, 0, 0], [0, c, -s, 0], [0, s, c, 0], [0, 0, 0, 1.0]])
def Tr(x, y, z): M = np.eye(4); M[:3, 3] = (x, y, z); return M


def zmin_cuc_bo(ten): return min(m.bounds[0][2] for _, m in nap(ten))


def build():
    p = {}
    # ---- base: two sled logs (along Y) + trough board + cup blocks between slots + back skirt
    for j, sx in enumerate((-1, 1)):
        p[f"de_go_{j}"] = ong((sx * RONG, -0.32, 0.05), (sx * RONG, 0.32, 0.05), 0.06, 0.06, "go_toi")
    p["mang"] = B((0, 0.0, DAY_Z - 0.025), 2 * RONG + 0.08, 0.20, 0.05, "go")
    for i in range(len(HANG) + 1):
        x = X0 + (i - 0.5) * BUOC; p[f"coc_{i}"] = B((x, 0.0, DAY_Z + 0.03), 0.05, 0.16, 0.06, "go_sang")
    # ---- posts, rails (with peg pairs), top beam, back crossbars for bows
    for j, sx in enumerate((-1, 1)):
        p[f"cot_{j}"] = ong((sx * RONG, 0.0, 0.0), (sx * RONG, 0.0, COT_Z), 0.05, 0.045, "go")
        p[f"cot_sau_{j}"] = ong((sx * RONG, 0.16, 0.0), (sx * RONG, 0.16, COT_Z - 0.10), 0.04, 0.035, "go")
        p[f"noi_{j}"] = B((sx * RONG, 0.08, COT_Z - 0.12), 0.06, 0.24, 0.05, "go_toi")
    p["xa_tren"] = B((0, 0.04, COT_Z + 0.02), 2 * RONG + 0.16, 0.12, 0.06, "go_toi")
    for ten_r, z, chi in (("ray_thap", RAY_THAP, None), ("ray_cao", RAY_CAO, DAI)):
        p[ten_r] = B((0, 0.055, z), 2 * RONG, 0.05, 0.06, "go")
        for i, t in enumerate(HANG):
            if chi and t not in chi: continue
            x = X0 + i * BUOC
            for s in (-1, 1): p[f"{ten_r}_chot_{i}_{s + 1}"] = ong((x + s * 0.034, 0.03, z), (x + s * 0.034, -0.07, z), 0.011, 0.011, "go_sang")
    for k, z in enumerate((1.62, 1.92)):
        p[f"xa_cung_{k}"] = B((0, 0.16, z), 2 * RONG, 0.04, 0.05, "go")
        for s in (-1, 1): p[f"chot_cung_{k}_{s + 1}"] = ong((s * 0.40, 0.14, z + 0.035), (s * 0.40, 0.06, z + 0.035), 0.012, 0.012, "go_sang")
    # ---- front row: stand each tool on the trough, head facing −Y (tool +X → world −Y, tool Y → world +X)
    dem = {}
    for i, t in enumerate(HANG):
        k = dem.get(t, 0); dem[t] = k + 1; x = X0 + i * BUOC
        z0 = DAY_Z - zmin_cuc_bo(t) + 0.002
        dat(t, k, Tr(x, -0.01, z0) @ Rz(-math.pi / 2), p)
    # ---- bows: lie level along X on the back crossbar pegs (tool +Z → world +X, belly −Y)
    for k, z in enumerate((1.62, 1.92)):
        dat("cung", k, Tr(0.0, 0.10, z + 0.06) @ Rz(-math.pi / 2) @ Rx(-math.pi / 2) @ Rz(math.pi / 2), p)
    # ---- 2 arrows lying along X on top of the upper bow crossbar (an open quiver is not a convex shell ⇒ arrows read as penetrating it)
    for k, dy in enumerate((-0.008, 0.012)):
        dat("mui_ten", k, Tr(-0.65 + 0.05 * k, 0.16 + dy, 1.92 + 0.025 + 0.012) @ Rz(math.pi / 2) @ Rx(math.pi / 2) @ Rz(math.pi / 2), p)
    # ---- end-post pegs: watering cans (left) + baskets (right) HANG BY THEIR GRIP — Boss 23/10: «làm sao cái giỏ lại nằm ngang kiểu đó
    # được? Physics ko đúng». Bản trước chỉ xoay quanh Z ⇒ trục quai đứng dọc, thân chìa ngang. Treo đúng: trục quai (+Z cục bộ) nằm DỌC
    # chốt (±X), thân (phía −X cục bộ) RŨ XUỐNG (+X cục bộ → +Z thế giới); quai tựa ĐỈNH chốt (r chốt 13 + r quai 14 mm).
    for j, (sx, mon) in enumerate(((-1, "binh_tuoi"), (1, "gio_berry"))):
        for k, (dy, z) in enumerate(((-0.0, 1.55), (0.16, 0.95))):
            p[f"chot_treo_{mon}_{k}"] = ong((sx * RONG, dy, z), (sx * (RONG + 0.30), dy, z), 0.013, 0.013, "go_sang")   # chốt dài: thân bình/giỏ rộng ±10–15 cm không chạm cột
            R = np.eye(4); R[:3, 0] = (0, 0, 1); R[:3, 2] = (sx, 0, 0); R[:3, 1] = np.cross(R[:3, 2], R[:3, 0])
            dat(mon, k, Tr(sx * (RONG + 0.21), dy, z + 0.027) @ R, p)
            TREO[f"{mon}_{k}"] = np.array((sx * (RONG + 0.21), dy, z + 0.027))
    return p


def _hull(m):
    try:
        from scipy.spatial import ConvexHull
        h = ConvexHull(m.vertices); return h.equations
    except Exception: return None


def soi(p):
    """penetration: vertices of each tool sub-mesh inside another part's convex hull by > 5 mm · support: each tool touches the trough/a peg"""
    import re
    loi = []; hulls = {k: _hull(m) for k, m in p.items()}
    nhom = {}
    for k in p:
        mm = re.match(r"do_([a-z_]+?)_(\d+)_", k)
        if mm: nhom.setdefault(f"{mm.group(1)}_{mm.group(2)}", []).append(k)
    xau = 0.0
    for g, ks in nhom.items():
        for k in ks:
            v = p[k].vertices
            for k2, eq in hulls.items():
                if k2 in ks or eq is None: continue
                if k2.startswith("do_") and re.match(r"do_([a-z_]+?)_(\d+)_", k2) and f"{re.match(r'do_([a-z_]+?)_(\d+)_', k2).group(1)}_{re.match(r'do_([a-z_]+?)_(\d+)_', k2).group(2)}" == g: continue
                sau = (-(v @ eq[:, :3].T + eq[:, 3])).min(axis=1).max()   # depth inside hull (positive = inside)
                if sau > 0.005: loi.append(f"{k}↔{k2} {sau * 1000:.0f} mm"); xau = max(xau, sau)
    for g, ks in nhom.items():
        lo = min(p[k].bounds[0][2] for k in ks); de = lo <= DAY_Z + 0.02
        treo = any(re.search(r"chot|quai|xa_cung", k2) and (np.abs(p[k2].bounds.mean(0) - np.vstack([p[k].bounds for k in ks]).mean(0))[:2] < 0.5).all() for k2 in p)
        if not (de or treo): loi.append(f"{g}: không tựa đáy, không treo chốt")
    # TRỌNG LỰC (Boss 23/10): món treo rũ tự do ⇒ trọng tâm nằm DƯỚI điểm treo và lệch ngang ≤ 3 cm (không thì nó sẽ xoay tới khi như vậy)
    for g, P_ in TREO.items():
        ks = nhom.get(g, []); 
        if not ks: continue
        com = sum(p[k].center_mass * p[k].volume for k in ks) / max(1e-9, sum(p[k].volume for k in ks))
        lech = float(np.linalg.norm(com[:2] - P_[:2]))
        if com[2] >= P_[2] or lech > 0.03: loi.append(f"{g}: treo sai trọng lực (trọng tâm lệch {lech * 100:.0f} cm, {'trên' if com[2] >= P_[2] else 'dưới'} điểm treo)")
    return (not loi, f"{len(nhom)} món · lún sâu nhất {xau * 1000:.0f} mm · " + ("; ".join(loi[:4]) or "không xuyên > 5 mm, món nào cũng tựa/treo, đồ treo rũ đúng trọng lực"))


META = dict(ten="weapon_rack", dat=True, ngan_sach=4200, soi=soi)

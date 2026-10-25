"""KHO HỞ (open storage) cho settler — Boss 23/10/2026: «dùng skill tạo open storage (visible what are being stored)… gỗ stack 5 layers -
1st layer 5 planks side by side and reduce as it raise layer 4-3-2-1… khi bị lấy đi… disappear from top to bottom fade out fast».
Một nguồn sự thật cho: vị trí ô (asset kho + cảnh + game), thứ tự XẾP (đáy trái→phải, lên lớp) và LẤY (ngược lại: trên xuống), thời gian mờ.
Toạ độ khung KHO: gỗ nằm dọc trục Y, tâm kho ở gốc, mặt đà (thanh kê) ở z = Z0."""
import math, os, sys

R_GO = 0.10            # bán kính khúc gỗ (lpms carried_log, tỉ lệ 1)
DAI_GO = 1.45
LOP = (5, 4, 3, 2, 1)  # 15 khúc
Z0 = 0.08              # mặt trên thanh kê
MO_NHANH = 6           # khung mờ vào/ra (24 fps ≈ 0,25 s)


def o_chua(r=R_GO, lop=LOP, z0=Z0):
    """các ô theo THỨ TỰ XẾP: [(chỉ số, lớp, x, z)]. Lớp trên nằm vào KHE giữa 2 khúc dưới: lệch x = r, cao thêm √3·r."""
    out = []; k = 0
    for L, n in enumerate(lop):
        for i in range(n):
            out.append((k, L, (i - (n - 1) / 2) * 2 * r, z0 + r + L * math.sqrt(3) * r)); k += 1
    return out


def thu_tu_lay(so_dang_co):
    """lấy ra từ TRÊN xuống: ngược thứ tự xếp."""
    return list(range(so_dang_co - 1, -1, -1))


def soi_kho(r=R_GO, lop=LOP, z0=Z0, coc_x=None, coc_r=0.035):
    """CỬA: (1) không 2 khúc nào chồng (tâm ≥ 2r) · (2) mỗi khúc lớp trên tì đúng 2 khúc dưới (tâm = 2r) · (3) lớp đáy tì thanh kê
    · (4) cọc biên không cắm vào khúc nào. Trả (đạt, chi tiết)."""
    o = o_chua(r, lop, z0); loi = []
    for a in o:
        for b in o:
            if a[0] < b[0] and math.hypot(a[2] - b[2], a[3] - b[3]) < 2 * r - 1e-6: loi.append(f"chồng {a[0]}-{b[0]}")
        if a[1] > 0:
            tua = [b for b in o if b[1] == a[1] - 1 and abs(math.hypot(a[2] - b[2], a[3] - b[3]) - 2 * r) < 1e-6]
            if len(tua) != 2: loi.append(f"ô {a[0]} tì {len(tua)} khúc")
        elif abs(a[3] - r - z0) > 1e-6: loi.append(f"ô {a[0]} không tì thanh kê")
    if coc_x is not None:
        for a in o:
            for s in (-1, 1):
                d = math.hypot(a[2] - s * coc_x, 0) - r - coc_r
                if d < -1e-6 and a[3] - r < 0.6: loi.append(f"cọc cắm ô {a[0]}")
    return (not loi), loi


# ---------------- KHO ĐÁ / đồ rời (Boss 23/10: «nó cũng stack và stack đc nhìu hơn ở storage đúng ko? Per slot»)
# Một Ô (slot) chứa NHIỀU đơn vị hơn gỗ: đống tháp vuông 4×4-3×3-2×2-1 = 30 cục (gỗ: 15 khúc/ô). Mỗi chuyến gùi = DA_MOI_CHUYEN cục.
# Lớp trên nằm vào HỐC giữa 4 cục dưới: lệch (r, r), cao thêm √2·r (xếp cầu chặt). Đổi sức chứa = đổi LOP_DA (vd (5,4,3,2,1) = 55).
R_DA = 0.065           # bán kính bao của cục đá nhỏ (lpms pebble) — cục thật ≤ R_DA nên không chồng
LOP_DA = (4, 3, 2, 1)
DA_MOI_CHUYEN = 5      # sức chở một gùi
NUA_THUNG = 0.29       # nửa lòng thùng đá (vách trong)


def o_chua_dong(r=R_DA, lop=LOP_DA, z0=Z0):
    """ô ĐỐNG theo THỨ TỰ XẾP: [(chỉ số, lớp, x, y, z)] — đáy theo hàng, rồi lên lớp."""
    out = []; k = 0
    for L, n in enumerate(lop):
        for j in range(n):
            for i in range(n):
                out.append((k, L, (i - (n - 1) / 2) * 2 * r, (j - (n - 1) / 2) * 2 * r, z0 + r + L * math.sqrt(2) * r)); k += 1
    return out


def suc_chua(lop=LOP_DA):
    return sum(n * n for n in lop)


def soi_dong(r=R_DA, lop=LOP_DA, z0=Z0, nua_thung=NUA_THUNG):
    """CỬA đống: (1) không 2 cục chồng (tâm ≥ 2r) · (2) mỗi cục lớp trên tì đúng 4 cục dưới · (3) lớp đáy tì đáy thùng · (4) không cục nào lấn vách."""
    o = o_chua_dong(r, lop, z0); loi = []
    d3 = lambda a, b: math.dist(a[2:5], b[2:5])
    for a in o:
        for b in o:
            if a[0] < b[0] and d3(a, b) < 2 * r - 1e-6: loi.append(f"chồng {a[0]}-{b[0]}")
        if a[1] > 0:
            tua = [b for b in o if b[1] == a[1] - 1 and abs(d3(a, b) - 2 * r) < 1e-6]
            if len(tua) != 4: loi.append(f"ô {a[0]} tì {len(tua)} cục")
        elif abs(a[4] - r - z0) > 1e-6: loi.append(f"ô {a[0]} không tì đáy")
        if max(abs(a[2]), abs(a[3])) + r > nua_thung + 1e-6: loi.append(f"ô {a[0]} lấn vách")
    return (not loi), loi


# ---------------- KHO THỊT (Boss 23/10/2026: «Storage stacking display thịt») — meat after hunt → process → carry home.
# Two slot kinds: HOOKS on the smoking-rack bar (one haunch each, bone up) + PILES on the slatted table (brick stacking 4-3-2-1 = 10/pile,
# every upper cut rests across 2 lower cuts whose BIG ENDS point opposite ways ⇒ two contact lines straddle its centre of mass).
# Meat-cut local frame (lpms assets/meat_piece.py): length along +X (big end +X, bone −X), FLAT bottom z=0, top plateau z=THIT_CAO.
THIT_CAO = 0.075       # cut height (flat bottom → top plateau at the big end)
THIT_KHE = 0.001       # air gap between pile layers
THIT_GIAN = 0.13       # centre spacing of cuts inside a pile layer
LOP_THIT = (4, 3, 2, 1)
THIT_MOC = (-0.202, 0.0, 0.035)   # tie point (lowest-x vertex of the bone knob icosphere) in the cut's local frame
BAN_Z = 0.55           # table top (slat top)
BAN_Y = -0.25          # table centre line = cut origin y in piles
DONG_X = (-0.33, 0.33) # pile centres
MOC_X = tuple(round(-0.56 + 0.16 * i, 2) for i in range(8))   # 8 hooks
MOC_Y = 0.33; MOC_Z = 1.31        # hook tip (bar at z 1.40)


def o_chua_thit():
    """Meat slots in FILL order (front → back: table piles layer by layer, both piles growing together; then hooks centre-out).
    Each: dict(k, loai 'dong'|'moc', nhom (pile index | hook index), lop, vi_tri (x,y,z) of the cut origin, ry, rz degrees).
    Cut transform = T(vi_tri) · Rz(rz) · Ry(ry)  (see ma_tran_thit). Withdraw = reverse (thu_tu_lay)."""
    out = []; k = 0
    for L, n in enumerate(LOP_THIT):
        for i in range(n):
            for p, cx in enumerate(DONG_X):
                s = 1 if (i + L) % 2 == 0 else -1          # big end +Y / −Y alternating
                out.append(dict(k=k, loai="dong", nhom=p, lop=L, vi_tri=(round(cx + (i - (n - 1) / 2) * THIT_GIAN, 4), BAN_Y,
                                round(BAN_Z + L * (THIT_CAO + THIT_KHE), 4)), ry=0.0, rz=90.0 * s)); k += 1
    for j in sorted(range(len(MOC_X)), key=lambda j: (abs(MOC_X[j]), MOC_X[j])):
        # Ry(90°) maps local (x,y,z) → (z, y, −x): bone up; tie point THIT_MOC lands exactly under the hook tip, 1 mm below it
        out.append(dict(k=k, loai="moc", nhom=j, lop=0, vi_tri=(round(MOC_X[j] - THIT_MOC[2], 4), MOC_Y, round(MOC_Z + THIT_MOC[0] - 0.001, 4)),
                        ry=90.0, rz=0.0)); k += 1
    return out


def suc_chua_thit():
    o = o_chua_thit(); dong = sum(n for n in LOP_THIT)
    return dict(moi_dong=dong, so_dong=len(DONG_X), moc=len(MOC_X), tong=len(o))


def ma_tran_thit(o):
    import numpy as np
    a, b = math.radians(o["ry"]), math.radians(o["rz"])
    Ry = np.array([[math.cos(a), 0, math.sin(a)], [0, 1, 0], [-math.sin(a), 0, math.cos(a)]])
    Rz = np.array([[math.cos(b), -math.sin(b), 0], [math.sin(b), math.cos(b), 0], [0, 0, 1]])
    M = np.eye(4); M[:3, :3] = Rz @ Ry; M[:3, 3] = o["vi_tri"]; return M


def soi_thit(parts, tol=0.005, buoc=0.003):
    """GATE meat storage on the REAL meshes. parts = {name: trimesh} in storage frame (Z up); cut parts are `thit_<NN>_*`,
    hook parts `moc_*`, everything else = rack. Checks:
      (1) no cut penetrates another cut or the rack by more than tol (signed depth vs each convex part, sampled every ~buoc m);
      (2) every cut is SUPPORTED: either RESTS (its lowest points touch a surface within tol and its centre of mass lies inside
          the xy hull of those contacts) or HANGS (touches a `moc_*` part within tol, centre of mass below it, ≤ 3 cm off plumb).
    Returns (ok, errors, stats)."""
    import numpy as np, trimesh
    from scipy.spatial import cKDTree, Delaunay
    nhom = {}
    for ten, m in parts.items():
        if ten.startswith("thit_"): nhom.setdefault(ten.split("_")[1], []).append(ten)
    def mau(m, it=None):
        n = max(200, int(m.area / buoc ** 2)) if it is None else it
        return np.vstack([trimesh.sample.sample_surface(m, n, seed=1)[0], m.vertices])
    def sau(P, m):   # penetration depth of points P into convex part m (0 when outside)
        h = m.convex_hull; eq = np.column_stack([h.face_normals, -np.einsum("ij,ij->i", h.face_normals, h.triangles[:, 0])])
        s = P @ eq[:, :3].T + eq[:, 3]; mx = s.max(1); return np.where(mx < 0, -mx, 0.0)
    bb = {t: m.bounds for t, m in parts.items()}
    cham = lambda a, b, e: np.all(bb[a][0] - e <= bb[b][1]) and np.all(bb[b][0] - e <= bb[a][1])
    loi = []; lun_max = 0.0; mau_cache = {t: mau(m) for t, m in parts.items()}
    ten_all = list(parts)
    for nn, ts in nhom.items():
        for a in ts:
            for b in ten_all:
                if b in ts or (b.startswith("thit_") and b.split("_")[1] < nn) or not cham(a, b, 0.0): continue
                d = max(float(sau(mau_cache[a], parts[b]).max()), float(sau(mau_cache[b], parts[a]).max()))
                lun_max = max(lun_max, d)
                if d > tol: loi.append(f"{a} penetrates {b} {d * 1000:.1f} mm")
    # support
    for nn, ts in nhom.items():
        U = trimesh.util.concatenate([parts[t] for t in ts]); com = U.center_mass if U.is_volume else U.centroid
        P = np.vstack([mau_cache[t] for t in ts]); zmin = P[:, 2].min()
        khac = [b for b in ten_all if b not in ts and any(cham(t, b, tol) for t in ts)]
        if not khac: loi.append(f"cut {nn} floats (nothing within {tol * 1000:.0f} mm)"); continue
        moc = [b for b in khac if b.startswith("moc_")]
        if moc:
            Q = np.vstack([mau_cache[b] for b in moc]); dd, _ = cKDTree(Q).query(P); c = P[dd <= tol + buoc]
            if len(c) and com[2] < c[:, 2].mean() and np.linalg.norm(com[:2] - c[:, :2].mean(0)) <= 0.03: continue
            loi.append(f"cut {nn} on hook but not hanging plumb (contacts {len(c)})"); continue
        Q = np.vstack([mau_cache[b] for b in khac]); dd, _ = cKDTree(Q).query(P)
        c = P[(dd <= tol + buoc) & (P[:, 2] <= zmin + 0.012)]
        if len(c) < 3: loi.append(f"cut {nn} not supported ({len(c)} bottom contacts)"); continue
        try: ok_in = Delaunay(c[:, :2], qhull_options="QJ").find_simplex(com[:2]) >= 0
        except Exception: ok_in = False
        if not ok_in: loi.append(f"cut {nn} tips over (centre of mass outside its contacts)")
    return (not loi), loi, dict(cuts=len(nhom), max_penetration_mm=round(lun_max * 1000, 2))


if __name__ == "__main__":
    ok, loi = soi_kho(coc_x=5 * R_GO + 0.036)
    print("✅" if ok else "⛔", len(o_chua()), "ô", loi)
    ok2, loi2 = soi_dong(); print("✅" if ok2 else "⛔", "đống đá", suc_chua(), "cục/ô", loi2[:5])
    ok3, _ = soi_dong(nua_thung=0.24); print("thử ngược vách hẹp 0,24 ⇒", "BẮT" if not ok3 else "LỌT")
    if len(sys.argv) > 1 and sys.argv[1] == "thit":   # MEAT gate on the real meat_storage meshes; exit 1 on fail; --nguoc = reverse tests
        sys.path[:0] = [os.path.expanduser("~/projects/lpm-faceless-humanoid/lpms"), os.path.expanduser("~/projects/lpm-faceless-humanoid/lpms/assets")]
        import meat_storage
        ok4, loi4, st = soi_thit(meat_storage.build()); print("✅" if ok4 else "⛔", "kho thịt", suc_chua_thit(), st, loi4[:6])
        if "--nguoc" in sys.argv:
            K = sys.modules["kho"]; bat = []   # meat_storage reads the IMPORTED module, not __main__
            for ten, gt in (("THIT_GIAN", 0.10), ("THIT_KHE", 0.02), ("THIT_MOC", (-0.23, 0.0, 0.035))):
                cu = getattr(K, ten); setattr(K, ten, gt); r = soi_thit(meat_storage.build()); setattr(K, ten, cu)
                print(f"reverse {ten}={gt} ⇒", "CAUGHT" if not r[0] else "MISSED", r[1][:2]); bat.append(not r[0])
            ok4 = ok4 and all(bat)
        sys.exit(0 if ok4 else 1)

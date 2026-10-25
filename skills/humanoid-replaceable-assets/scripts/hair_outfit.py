"""Tóc + đồ đơn giản cho phiên bản chi tiết (LPD) — asset RỜI, gắn lên thân, không trộn vào thân.
Boss 22/10/2026: «Giờ tóc đơn giản cho nam và nữ. Đồ đơn giản cho nam và nữ — đồ thời nào là dễ làm RTS settler nhất? Giống GodUs?»
⇒ chọn đồ DÂN LÀNG SƠ KHAI: nam = áo chui đầu tới giữa đùi + thắt lưng + quần ống + giày vải; nữ = váy dài tới bắp chân + thắt lưng + giày.

Cách dựng (đo, không đoán):
  · TÓC: lưới 16 cột (góc HA của đầu) × hàng z, đặt trên chính SCALP_REFERENCE của đầu (scalp(a, z)), nới k quanh HAIR_SOCKET;
    phần rủ xuống (bob) giữ mặt cắt ở tầng tai và nới đủ để KHÔNG chạm tai; mép tóc răng cưa xen kẽ (stylized nhẹ).
  · ÁO/QUẦN: vỏ = mặt thân theo vùng (torso/glute/arms/legs/feet) dời theo pháp tuyến đỉnh 8–12 mm, hở cổ/tay/gấu.
  · VẠT ÁO / VÁY: ống 16 cạnh, bán kính mỗi hướng = điểm xa nhất của thân+chân ở tầng z đó + khe hở, loe dần xuống gấu.
Chạy: GIOI=nam|nu python3 hair_outfit.py out_<gioi>   ⇒ <TOC>.glb, <DO>.glb ; cửa không-lún chạy cuối (exit 1).
"""
import os, sys, math, importlib
import numpy as np, trimesh

OUT = sys.argv[1]
os.makedirs(OUT, exist_ok=True)
_argv = sys.argv; sys.argv = [sys.argv[0]]                 # geometry.py đọc argv khi chạy như main; import thì không
G = importlib.import_module("geometry"); sys.argv = _argv
NU, K = G.NU, G.K_CAO
Vb = np.array(G.V, float); Fb = G.F                       # thân (toạ độ chưa co K)

MAU = {"toc": [40, 30, 24, 255] if not NU else [22, 20, 22, 255],
       "ao": [176, 138, 92, 255], "quan": [104, 78, 56, 255], "vay": [96, 128, 112, 255],
       "that_lung": [70, 48, 32, 255], "giay": [82, 60, 44, 255]}


def vat_lieu(ten):
    return trimesh.visual.material.PBRMaterial(name=ten, baseColorFactor=MAU[ten], metallicFactor=0.0, roughnessFactor=0.85)


def luoi(V, F, ten):
    m = trimesh.Trimesh(np.asarray(V) * K, np.asarray(F), process=True)
    m.visual = trimesh.visual.TextureVisuals(material=vat_lieu(ten)); return m


# ------------------------------------------------------------------ TÓC
def toc():
    S = G.SOCKET; HA = G.HA
    z_dinh = G.POLE_Z
    V, F = [], []
    # gấu tóc theo cột (độ): mặt trước dừng trên cung mày; nam: hai bên trên tai, sau gáy ngắn; nữ: bob tới hàm
    def gau(a_deg):
        a = (a_deg + 180) % 360 - 180; aa = abs(a)
        if aa <= 40: return 1.708                         # mái trước, trên cung mày (1,716)
        if NU:
            return 1.625 if aa <= 60 else 1.585            # bob ngang hàm
        return 1.676 if aa <= 135 else 1.612               # nam: trên tai (đỉnh tai 1,670) tới hết cột 130°, gáy 1,612 — chuyển sớm hơn thì mặt tóc chéo qua mép sau tai
    hang = 12
    # Bám vào mặt đầu THẬT (gồm tai): tia từ tâm đầu ra, đặt tóc tại điểm chạm xa nhất + KHE. (Bao scalp nội suy nằm
    # thấp hơn lưới thật ở chỏm sau 8 mm ⇒ bản đầu lún 147/4000 điểm — đừng dùng scalp để đặt tóc.)
    dau_tg = np.array([[Vb[i] for i in tri] for f in Fb if f[1] in ("face", "skull", "ears")
                       for tri in ([f[0][:3]] if len(f[0]) == 3 else [[f[0][0], f[0][1], f[0][2]], [f[0][0], f[0][2], f[0][3]]])])
    def cham_xa(o, d):
        e1, e2 = dau_tg[:, 1] - dau_tg[:, 0], dau_tg[:, 2] - dau_tg[:, 0]; pv = np.cross(d, e2); det = np.einsum("ij,ij->i", e1, pv)
        ok = np.abs(det) > 1e-12; inv = np.where(ok, 1 / np.where(ok, det, 1), 0); tv = o - dau_tg[:, 0]
        u = np.einsum("ij,ij->i", tv, pv) * inv; qv = np.cross(tv, e1); v = (qv @ d) * inv; t = np.einsum("ij,ij->i", e2, qv) * inv
        h = ok & (u >= -1e-9) & (v >= -1e-9) & (u + v <= 1 + 1e-9) & (t > 0)
        return float(t[h].max()) if h.any() else None
    KHE = 0.011   # khe 4 mm lún: mặt tóc giữa 2 đỉnh là dây cung, cắt vào chỗ đầu phồng
    cot = []
    for j, a in enumerate(HA):
        ad = math.degrees(a); truoc = abs((ad + 180) % 360 - 180) <= 40
        zg = gau(ad) + (0 if truoc else (0.007 if j % 2 else -0.004))
        ids = []
        for i in range(hang):
            t = i / (hang - 1); z = z_dinh - 0.004 - t * (z_dinh - 0.004 - zg)
            if z >= 1.70:   # chỏm: tia từ tâm đầu
                d = G.scalp(a, z) - S; d /= np.linalg.norm(d); r = cham_xa(S, d)
                q = S + d * ((r if r else 0.08) + KHE)
            else:           # rủ xuống: tia NGANG từ trục đầu ở tầng z, qua cả tai; dưới đầu thì giữ mặt cắt tầng 1,70
                o = np.array([0.0, G.HYC, z]); d = np.array([math.sin(a), -math.cos(a), 0.0])
                r = cham_xa(o, d); r70 = cham_xa(np.array([0.0, G.HYC, 1.70]), d) or 0.08
                phong = (0.010 if NU else 0.002) * min(1.0, (1.70 - z) / 0.03)    # bob phồng nhẹ ra
                tham = 0.006 if 40 < abs((ad + 180) % 360 - 180) < 75 else 0.0      # cột kề mái: mặt chéo qua thái dương
                q = o + d * (max(r or 0.0, r70 * (0.97 if NU else 1.0)) + KHE + 0.004 + phong + tham)   # +4 mm qua vành tai
            if i == hang - 1:
                q = q + np.array([q[0] - S[0], q[1] - S[1], 0]) * (0.05 if NU else 0.02)   # gấu loe nhẹ
            ids.append(len(V)); V.append(q)
        cot.append(ids)
    n = len(HA)
    for j in range(n):
        a, b = cot[j], cot[(j + 1) % n]
        for i in range(hang - 1):
            F.append([a[i], b[i], b[i + 1]]); F.append([a[i], b[i + 1], a[i + 1]])
    dinh = len(V); V.append(np.array([0, G.HYC + 0.004, z_dinh + 0.012]))
    for j in range(n): F.append([cot[(j + 1) % n][0], cot[j][0], dinh])
    m = trimesh.Trimesh(np.array(V), np.array(F), process=True); m.fix_normals()
    return m


# ------------------------------------------------------------------ ĐỒ
def phap_tuyen_dinh():
    tri = trimesh.Trimesh(Vb, [f[0][:3] for f in Fb] + [[f[0][0], f[0][2], f[0][3]] for f in Fb if len(f[0]) == 4], process=False)
    tri.fix_normals(); return tri.vertex_normals


NV = phap_tuyen_dinh()


def vo(chon, day):
    """vỏ áo/quần: các mặt thân thoả `chon(f, tâm)` dời theo pháp tuyến đỉnh `day` mét."""
    dung = [f for f in Fb if chon(f, Vb[f[0]].mean(0))]
    ids = sorted({i for f in dung for i in f[0]}); moi = {i: k for k, i in enumerate(ids)}
    V = [Vb[i] + NV[i] * day for i in ids]; F = []
    for f in dung:
        q = [moi[i] for i in f[0]]
        F.append(q[:3]) if len(q) == 3 else F.extend([[q[0], q[1], q[2]], [q[0], q[2], q[3]]])
    return V, F


def ong(z0, z1, khe, loe, so_hang=5, n=16, bo_tay=True):
    """ống 16 cạnh bao THÂN+CHÂN (bỏ tay) từ z0 xuống z1; bán kính mỗi hướng = điểm xa nhất ở tầng z + khe, loe dần."""
    vung = {"torso", "glute", "legs"}
    # đo theo ĐIỂM RẢI DÀY trên mặt thân, không theo đỉnh: giữa vòng đùi đầu (0,765) và vòng hông (0,865) gần như
    # không có đỉnh ⇒ ống bị thu nhỏ chui vào người (đo 22/10: vạt áo lún 755/2000 điểm)
    tri = [Vb[t] for f in Fb if f[1] in vung for t in ([f[0][:3]] if len(f[0]) == 3 else [f[0][:3], [f[0][0], f[0][2], f[0][3]]])]
    P, _ = trimesh.sample.sample_surface(trimesh.Trimesh(np.array(tri).reshape(-1, 3), np.arange(len(tri) * 3).reshape(-1, 3), process=False), 60000, seed=3)
    V, F, hangs = [], [], []
    for h in range(so_hang):
        t = h / (so_hang - 1); z = z0 + (z1 - z0) * t
        lop = P[np.abs(P[:, 2] - z) < 0.015]
        c = np.array([0.0, lop[:, 1].mean(), z])
        ids = []
        for j in range(n):
            a = 2 * math.pi * j / n; d = np.array([math.sin(a), -math.cos(a), 0])
            r = max(float(((lop - c) @ d).max()), 0.05) + khe + loe * t
            ids.append(len(V)); V.append(c + d * r)
        hangs.append(ids)
    for h in range(so_hang - 1):
        a, b = hangs[h], hangs[h + 1]
        for j in range(n):
            F += [[a[j], a[(j + 1) % n], b[(j + 1) % n]], [a[j], b[(j + 1) % n], b[j]]]
    return V, F


def vanh(z, cao, day):
    """thắt lưng: vành theo mặt cắt thân ở tầng z, nới `day`."""
    P = np.array([p for f in Fb if f[1] in ("torso", "glute") for p in Vb[f[0]]])
    lop = P[np.abs(P[:, 2] - z) < 0.035]; c = np.array([0.0, lop[:, 1].mean(), z]); n = 16; V = []; F = []
    for dz in (cao / 2, -cao / 2):
        for j in range(n):
            a = 2 * math.pi * j / n; d = np.array([math.sin(a), -math.cos(a), 0])
            V.append(c + d * (float(((lop - c) @ d).max()) + day) + np.array([0, 0, dz]))
    for j in range(n):
        F += [[j, (j + 1) % n, n + (j + 1) % n], [j, n + (j + 1) % n, n + j]]
    return V, F


def do():
    parts = {}
    co_ao = 1.452                                           # hở cổ
    than = lambda f, c: f[1] in ("torso", "glute") and Vb[f[0]][:, 2].max() < co_ao
    tay_ngan = lambda f, c: f[1] == "arms" and c[2] > 1.27   # tay áo ngắn
    if not NU:
        V, F = vo(lambda f, c: than(f, c) or tay_ngan(f, c), 0.011); parts["ao_than"] = luoi(V, F, "ao")
        V, F = ong(0.90, 0.745, 0.016, 0.018); parts["ao_vat"] = luoi(V, F, "ao")         # vạt áo trên đầu ngón tay (0,716 m): dài hơn ⇒ bàn tay xuyên vạt (đo: 655/2000)
        V, F = vo(lambda f, c: f[1] == "legs" and c[2] > 0.115, 0.008); parts["quan"] = luoi(V, F, "quan")
        V, F = vanh(0.975, 0.040, 0.020); parts["that_lung"] = luoi(V, F, "that_lung")
    else:
        V, F = vo(lambda f, c: than(f, c) or tay_ngan(f, c), 0.010); parts["vay_than"] = luoi(V, F, "vay")
        V, F = ong(0.96, 0.30, 0.016, 0.060, so_hang=7); parts["vay_duoi"] = luoi(V, F, "vay")   # váy tới bắp chân, loe
        V, F = vanh(1.060, 0.034, 0.018); parts["that_lung"] = luoi(V, F, "that_lung")
    V, F = vo(lambda f, c: f[1] == "feet" or (f[1] == "legs" and c[2] < 0.115), 0.007); parts["giay"] = luoi(V, F, "giay")
    return parts


# ------------------------------------------------------------------ CỬA: không lún vào người
def ben_trong(points, M):
    """parity BỎ PHIẾU 3 tia lệch hướng (đa số) — tia trục +X trùng mặt phẳng vòng đỉnh đi qua CẠNH, bị đếm đôi
    (hiệu chỉnh 22/10: tia đơn báo sai 4/8 điểm chắc chắn trong người; 3 tia lệch: 0/8)."""
    tri = M.triangles; e1, e2 = tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0]
    phieu = np.zeros(len(points), int)
    for d in (np.array([1.0, 0.0137, 0.0071]), np.array([-0.0113, 1.0, 0.0193]), np.array([0.0171, -0.0089, 1.0])):
        d = d / np.linalg.norm(d)
        pv = np.cross(d, e2); det = np.einsum("ij,ij->i", e1, pv); ok = np.abs(det) > 1e-12; inv = np.where(ok, 1 / np.where(ok, det, 1), 0)
        for s in range(0, len(points), 400):
            P = points[s:s + 400]; tv = P[:, None, :] - tri[None, :, 0]
            u = np.einsum("pij,ij->pi", tv, pv) * inv; qv = np.cross(tv, e1[None]); v = (qv @ d) * inv
            t = np.einsum("pij,ij->pi", qv, e2) * inv
            hit = ok[None] & (u >= 0) & (v >= 0) & (u + v <= 1) & (t > 1e-6)
            phieu[s:s + 400] += (hit.sum(1) % 2) == 1
    return phieu >= 2


def main():
    than = trimesh.Trimesh(Vb * K, [f[0][:3] for f in Fb] + [[f[0][0], f[0][2], f[0][3]] for f in Fb if len(f[0]) == 4], process=True)
    dau = trimesh.Trimesh(Vb * K, [ff for f in Fb if f[1] in ("face", "skull", "neck")
                                     for ff in ([f[0][:3]] if len(f[0]) == 3 else [[f[0][0], f[0][1], f[0][2]], [f[0][0], f[0][2], f[0][3]]])], process=True)
    t = toc(); t.vertices *= K; t.visual = trimesh.visual.TextureVisuals(material=vat_lieu("toc"))
    parts = do()
    Y = trimesh.transformations.rotation_matrix(-math.pi / 2, (1, 0, 0))
    ten_toc = "HAIR_SHORT_M" if not NU else "HAIR_BOB_F"; ten_do = "OUTFIT_SETTLER_M" if not NU else "OUTFIT_SETTLER_F"
    sc = trimesh.Scene(); g = t.copy(); g.apply_transform(Y); sc.add_geometry(g, node_name=ten_toc); sc.export(f"{OUT}/{ten_toc}.glb")
    sc = trimesh.Scene()
    for k_, m in parts.items():
        g = m.copy(); g.apply_transform(Y); sc.add_geometry(g, node_name=k_)
    sc.export(f"{OUT}/{ten_do}.glb")
    loi = []
    ptoc, _ = trimesh.sample.sample_surface(t, 4000, seed=1)
    nt = int(ben_trong(ptoc, than).sum()); print(f"  {'✅' if nt == 0 else '❌'} tóc: {nt}/4000 điểm lún vào người (0)"); loi += [nt] if nt else []
    tong = 0
    for k_, m in parts.items():
        p, _ = trimesh.sample.sample_surface(m, 2000, seed=2); n_ = int(ben_trong(p, than).sum()); tong += n_
        print(f"  {'✅' if n_ <= 40 else '❌'} {k_}: {n_}/2000 điểm lún vào người (≤2 %) · {len(m.faces)} tam giác")
        if n_ > 40: loi.append(n_)
    print(f"  tóc {len(t.faces)} tam giác · đồ {sum(len(m.faces) for m in parts.values())} tam giác")
    print(("⛔ TÓC/ĐỒ TRƯỢT" if loi else "✅ TÓC/ĐỒ ĐẠT"), OUT)
    sys.exit(1 if loi else 0)


if __name__ == "__main__":
    main()

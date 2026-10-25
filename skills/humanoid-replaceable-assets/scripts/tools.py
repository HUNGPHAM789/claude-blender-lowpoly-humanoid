"""Bộ công cụ settler low-poly (Boss 22/10/2026): giỏ hái berry · cung + tên săn hươu · rìu chặt cây · cuốc chim (đá) ·
cuốc đất · xẻng · bình tưới · cần câu.
Dựng bằng KHỐI LỒI (ConvexHull) ghép — đồ cứng, không dùng skill organic (organic ra khối mềm kiểu đất nặn).

HỢP ĐỒNG CẦM (khớp socket `cam_*` của bàn tay nắm `--co 1`, trụ Ø32 mm):
  · gốc toạ độ (0,0,0) = TÂM CHỖ CẦM; trục CÁN = +Z cục bộ; phía «làm việc» (lưỡi, mũi, vòi) = +X cục bộ.
  · bán kính cán tại chỗ cầm 13–17 mm (cửa ⑥) ⇒ bàn tay ôm được, lún ≤1,5 mm.
Chạy: python3 tools.py <thư mục>  ⇒ <tên>.glb mỗi món + tools.json ; cửa đo chạy cuối (exit 1).
"""
import json, math, os, sys
import numpy as np, trimesh
sys.path.insert(0, os.path.expanduser("~/projects/lpm-faceless-humanoid/theme")); import theme_colors as TM   # theme màu dùng chung (Boss 23/10: áp tông nai B cho cả game)
from scipy.spatial import ConvexHull

OUT = sys.argv[1] if len(sys.argv) > 1 else "tools_out"
MAU = {"go": [128, 92, 58, 255], "go_sang": [170, 130, 84, 255], "sat": [118, 122, 128, 255], "da": [140, 134, 124, 255],
       "may": [196, 164, 108, 255], "berry": [150, 30, 52, 255], "berry2": [70, 40, 110, 255], "day": [225, 220, 205, 255],
       "long": [215, 210, 200, 255], "dong": [176, 120, 72, 255]}


def srgb_tuyen_tinh(c):
    """glTF baseColorFactor là màu TUYẾN TÍNH. Ghi thẳng sRGB ⇒ màu nhạt bạc (Boss 22/10 thích bản Kiln «màu nóng»: Kiln đổi đúng)."""
    return [((x / 255) / 12.92 if x / 255 <= 0.04045 else ((x / 255 + 0.055) / 1.055) ** 2.4) if i < 3 else x / 255 for i, x in enumerate(c)]


def khoi(pts, mau):
    p = np.asarray(pts, float); m = trimesh.Trimesh(p, ConvexHull(p).simplices, process=True); m.fix_normals()
    m.visual = trimesh.visual.TextureVisuals(material=trimesh.visual.material.PBRMaterial(
        # Boss 23/10 lật quyết định 22/10 («tôi thích màu bên mình hơn» = tông nhạt): áp theme «Đất ấm» của nai B ⇒ nạp màu qua theme_colors
        name=mau, baseColorFactor=TM.mau(MAU[mau]), metallicFactor=0.3 if mau in ("sat", "dong") else 0.0, roughnessFactor=0.8))
    return m


def ong(a, b, r0, r1, mau, n=6):
    """lăng trụ n cạnh từ a tới b (cán, thân)."""
    a, b = np.asarray(a, float), np.asarray(b, float); t = (b - a) / np.linalg.norm(b - a)
    u = np.cross(t, (0, 0, 1.0) if abs(t[2]) < 0.9 else (1.0, 0, 0)); u /= np.linalg.norm(u); v = np.cross(t, u)
    pts = [c + r * (math.cos(2 * math.pi * k / n) * u + math.sin(2 * math.pi * k / n) * v) for c, r in ((a, r0), (b, r1)) for k in range(n)]
    return khoi(pts, mau)


def hop(c, sx, sy, sz, mau, vat=0.0):
    c = np.asarray(c, float)
    return khoi([c + np.array((x * sx, y * sy, z * sz * (1 - vat if x > 0 else 1))) for x in (-.5, .5) for y in (-.5, .5) for z in (-.5, .5)], mau)


R_CAN = 0.015   # bán kính cán tại chỗ cầm


def riu():
    return {"can": ong((0, 0, -0.14), (0, 0, 0.58), R_CAN, 0.017, "go"),
            "luoi": khoi([(-0.03, -0.02, 0.50), (-0.03, 0.02, 0.50), (-0.03, -0.02, 0.60), (-0.03, 0.02, 0.60),          # gáy rìu
                          (0.05, -0.016, 0.505), (0.05, 0.016, 0.505), (0.05, -0.016, 0.595), (0.05, 0.016, 0.595),
                          (0.15, -0.003, 0.45), (0.15, 0.003, 0.45), (0.15, -0.003, 0.645), (0.15, 0.003, 0.645)], "sat")}   # lưỡi loe


def riu_dai():
    """rìu HAI TAY (Boss 22/10: «need two hands chop from side swing in»): cán 1,05 m; tay phải ở gốc, tay trái ở z = −0,24 (gần đuôi cán)."""
    return {"can": ong((0, 0, -0.32), (0, 0, 0.73), R_CAN, 0.017, "go"),
            "luoi": khoi([(-0.035, -0.022, 0.62), (-0.035, 0.022, 0.62), (-0.035, -0.022, 0.73), (-0.035, 0.022, 0.73),
                          (0.06, -0.018, 0.625), (0.06, 0.018, 0.625), (0.06, -0.018, 0.725), (0.06, 0.018, 0.725),
                          (0.17, -0.003, 0.57), (0.17, 0.003, 0.57), (0.17, -0.003, 0.785), (0.17, 0.003, 0.785)], "sat")}


def pickaxe():
    """cuốc chim LƯỠI LIỀM (Boss 22/10: «chưa có cuốc lưỡi liềm đập đá»): đầu cong như trăng khuyết, hai mũi chúc xuống,
    ghép từ các khúc lồi nối tiếp dọc cung z = z0 − k·x² (mặt cắt thoi thu nhỏ dần về mũi)."""
    z = 0.80; parts = {"can": ong((0, 0, -0.14), (0, 0, z + 0.02), R_CAN, 0.018, "go"),
                       "khau": ong((0, 0, z - 0.035), (0, 0, z + 0.045), 0.026, 0.026, "sat")}
    def mat_cat(x, L):
        t = abs(x) / L; cz = z + 0.02 - 1.25 * x * x; dz = 0.032 * (1 - t) + 0.004; dy = 0.024 * (1 - t) + 0.003
        return [(x, 0, cz + dz), (x, 0, cz - dz), (x, dy, cz), (x, -dy, cz)]
    for ben, L in (("truoc", 0.30), ("sau", 0.28)):
        xs = np.linspace(0, L, 6) * (1 if ben == "truoc" else -1)
        for k in range(5):
            pts = mat_cat(xs[k], L) + (mat_cat(xs[k + 1], L) if k < 4 else [(xs[5], 0, z + 0.02 - 1.25 * xs[5] ** 2)])
            parts[f"mui_{ben}_{k}"] = khoi(pts, "sat")
    return parts


def cuoc_dat():
    z = 1.05
    return {"can": ong((0, 0, -0.14), (0, 0, z + 0.03), R_CAN, 0.017, "go"),
            "khau": ong((0, 0, z - 0.03), (0, 0, z + 0.04), 0.024, 0.024, "sat"),
            "luoi": khoi([(0.015, -0.07, z + 0.03), (0.015, 0.07, z + 0.03), (0.035, -0.07, z + 0.03), (0.035, 0.07, z + 0.03),   # lưỡi to, cắm chéo xuống ~70°
                          (0.10, -0.085, z - 0.17), (0.10, 0.085, z - 0.17), (0.115, -0.085, z - 0.165), (0.115, 0.085, z - 0.165)], "sat")}


def xeng():
    # chỗ cầm = tay trên; cán đi xuống −Z tới lưỡi; quai chữ D ở trên
    return {"can": ong((0, 0, -0.80), (0, 0, 0.12), R_CAN, 0.016, "go"),
            "quai": khoi([(-0.06, -0.012, 0.12), (0.06, -0.012, 0.12), (-0.06, 0.012, 0.12), (0.06, 0.012, 0.12),
                          (-0.05, -0.012, 0.20), (0.05, -0.012, 0.20), (-0.05, 0.012, 0.20), (0.05, 0.012, 0.20)], "go"),
            "luoi": khoi([(-0.11, -0.012, -0.80), (0.11, -0.012, -0.80), (-0.11, 0.004, -0.80), (0.11, 0.004, -0.80),
                          (-0.10, -0.022, -1.06), (0.10, -0.022, -1.06), (0, -0.026, -1.12), (0, -0.008, -1.12)], "sat")}


def cung():
    parts = {"cho_cam": ong((0, 0, -0.06), (0, 0, 0.06), R_CAN, R_CAN, "go_sang")}
    # hai cánh cung cong về −X (phía người bắn), dây ở x = −0,13
    for s in (1, -1):
        pts = [(0, 0, 0.06 * s)] + [(-0.12 * (t ** 1.6), 0, s * (0.06 + 0.62 * t)) for t in np.linspace(0.2, 1.0, 5)]
        for (a, b) in zip(pts[:-1], pts[1:]):
            k = abs(b[2]) / 0.68
            parts[f"canh_{'tren' if s > 0 else 'duoi'}_{abs(round(b[2] * 100))}"] = ong(a, b, 0.012 * (1 - 0.55 * k) + 0.004, 0.012 * (1 - 0.6 * k) + 0.003, "go")
    parts["day"] = ong((-0.12, 0, 0.68), (-0.12, 0, -0.68), 0.0015, 0.0015, "day", n=4)
    return parts


def mui_ten():
    return {"than": ong((0, 0, -0.35), (0, 0, 0.33), 0.004, 0.004, "go_sang", n=5),
            "dau": khoi([(0, 0, 0.40), (0.012, 0, 0.33), (-0.012, 0, 0.33), (0, 0.004, 0.33), (0, -0.004, 0.33)], "da"),
            **{f"long_{k}": khoi([(0, 0, -0.34), (0, 0, -0.24),
                                  (0.016 * math.cos(2 * math.pi * k / 3), 0.016 * math.sin(2 * math.pi * k / 3), -0.33),
                                  (0.016 * math.cos(2 * math.pi * k / 3), 0.016 * math.sin(2 * math.pi * k / 3), -0.27),
                                  (0.0008, 0.0008, -0.30)], "long") for k in range(3)}}


def can_cau():
    """cần câu CONG ĐỀU (Boss 22/10: «Cần câu nhìn như bị gãy» — bản cũ gập 25° một lần): 6 khúc, mỗi khớp ≤ 4°, thon dần."""
    parts = {"can": ong((0, 0, -0.25), (0, 0, 0.30), R_CAN + 0.001, R_CAN, "go")}
    p = np.array((0, 0, 0.30)); goc = 0.0; L = 1.55 / 6
    for k in range(6):
        goc += math.radians(4); d = np.array((math.sin(goc), 0, math.cos(goc)))
        r0, r1 = R_CAN - (R_CAN - 0.0035) * k / 6, R_CAN - (R_CAN - 0.0035) * (k + 1) / 6
        parts[f"ngon_{k}"] = ong(p, p + d * L, r0, r1, "go_sang" if k else "go", n=6); p = p + d * L
    parts["cuon"] = ong((0.03, -0.02, 0.10), (0.03, 0.02, 0.10), 0.028, 0.028, "dong", n=8)
    parts["khuyen"] = ong(p, p + d * 0.03, 0.006, 0.002, "sat", n=4)
    return parts


def lao():
    """LAO SĂN (Boss 23/10/2026: «gắn cung và cây lao (chưa tạo)» — clip LTX phóng lao seed 2): cán 1,7 m thon hai đầu, gốc = điểm
    cân bằng (~45% từ đuôi) = chỗ cầm Ø29 mm (cửa 13–17 mm bán kính), mũi đá ghè hình lá 16 cm buộc dây, đoạn cầm quấn da."""
    parts = {"cho_cam": ong((0, 0, -0.07), (0, 0, 0.07), R_CAN, R_CAN, "go_sang"),
             "can_sau": ong((0, 0, -0.77), (0, 0, -0.07), 0.010, R_CAN, "go"),
             "can_truoc": ong((0, 0, 0.07), (0, 0, 0.93), R_CAN, 0.011, "go"),
             "quan_da": ong((0, 0, -0.06), (0, 0, 0.06), R_CAN + 0.0015, R_CAN + 0.0015, "day", n=8)}
    # mũi đá hình lá: 2 mặt ghè (dẹt theo Y), gờ giữa
    parts["mui"] = khoi([(0, 0, 1.10), (0.024, 0, 1.00), (-0.024, 0, 1.00), (0.017, 0, 0.94), (-0.017, 0, 0.94),
                         (0, 0.007, 1.00), (0, -0.007, 1.00), (0, 0, 0.92)], "da")
    parts["buoc"] = ong((0, 0, 0.90), (0, 0, 0.97), 0.0135, 0.0125, "day", n=8)
    return parts


def goc_gay(parts):
    """góc gập lớn nhất (độ) giữa trục các khúc liên tiếp can → ngon_0 → … (trục = hướng chính PCA của đỉnh)."""
    ten = ["can"] + sorted((k for k in parts if k.startswith("ngon_")), key=lambda k: int(k.split("_")[1]))
    truc = []
    for k in ten:
        v = parts[k].vertices - parts[k].vertices.mean(0); a = np.linalg.svd(v, full_matrices=False)[2][0]
        truc.append(a if a[2] > 0 else -a)
    return max(math.degrees(math.acos(min(1, abs(float(np.dot(a, b)))))) for a, b in zip(truc, truc[1:]))


def binh_tuoi():
    # cầm ở quai trên: trục quai = +Z cục bộ ⇒ thân bình nằm phía −X (dưới tay khi xách)
    parts = {"quai": ong((0, 0, -0.07), (0, 0, 0.07), R_CAN, R_CAN, "dong")}
    tam = np.array((-0.17, 0, 0))
    vong = lambda x, r: [tam + np.array((x, r * math.cos(2 * math.pi * k / 8), r * math.sin(2 * math.pi * k / 8))) for k in range(8)]
    parts["than"] = khoi(vong(-0.10, 0.095) + vong(0.11, 0.105), "dong")
    parts["chan_quai"] = khoi([(-0.02, -0.01, -0.07), (-0.02, 0.01, -0.07), (-0.08, -0.01, -0.07), (-0.08, 0.01, -0.07),
                               (-0.02, -0.01, 0.07), (-0.02, 0.01, 0.07), (-0.08, -0.01, 0.07), (-0.08, 0.01, 0.07)], "dong")
    goc = tam + np.array((-0.06, 0, 0.09)); dau = goc + np.array((0.20, 0, 0.25))   # vòi từ đáy trước chếch LÊN (+X = lên khi xách)
    parts["voi"] = ong(goc, dau, 0.018, 0.009, "dong")
    parts["sen"] = ong(dau, dau + (dau - goc) / np.linalg.norm(dau - goc) * 0.03, 0.022, 0.022, "dong", n=8)
    return parts


def gio_berry():
    # cầm ở đỉnh quai: trục quai = +Z ⇒ giỏ treo phía −X
    parts = {"quai_tren": ong((0, 0, -0.05), (0, 0, 0.05), R_CAN, R_CAN, "may")}
    for s in (1, -1):
        parts[f"quai_{'a' if s > 0 else 'b'}"] = ong((0, 0, 0.05 * s), (-0.20, 0, 0.13 * s), 0.009, 0.009, "may")
    tam = np.array((-0.27, 0, 0))
    vong = lambda x, r: [tam + np.array((x, r * math.cos(2 * math.pi * k / 8), r * math.sin(2 * math.pi * k / 8))) for k in range(8)]
    parts["gio"] = khoi(vong(0.07, 0.15) + vong(-0.07, 0.11), "may")
    rng = np.random.default_rng(3)
    for k in range(9):
        c = tam + np.array((0.075 + rng.uniform(0, 0.02), rng.uniform(-0.09, 0.09), rng.uniform(-0.09, 0.09)))
        ico = trimesh.creation.icosphere(subdivisions=0, radius=0.024); ico.apply_translation(c)
        parts[f"berry_{k}"] = khoi(ico.vertices, "berry" if k % 3 else "berry2")
    return parts


BO = {"riu": (riu, "rìu chặt cây"), "riu_dai": (riu_dai, "rìu hai tay"), "pickaxe": (pickaxe, "cuốc chim đập đá"), "cuoc_dat": (cuoc_dat, "cuốc đất"),
      "xeng": (xeng, "xẻng"), "cung": (cung, "cung săn hươu"), "lao": (lao, "lao săn"), "mui_ten": (mui_ten, "mũi tên"),
      "can_cau": (can_cau, "cần câu"), "binh_tuoi": (binh_tuoi, "bình tưới"), "gio_berry": (gio_berry, "giỏ hái berry")}
CO_CAN = {"lao", "riu", "riu_dai", "pickaxe", "cuoc_dat", "xeng", "cung", "can_cau", "binh_tuoi", "gio_berry"}   # món có chỗ cầm


def ban_kinh_cho_cam(parts):
    """bán kính mặt cắt TẠI GỐC (z = 0) của khối chứa gốc — đo trên lưới, không đọc số trong code."""
    for m in parts.values():
        s = m.section(plane_origin=(0, 0, 0), plane_normal=(0, 0, 1))
        if s is not None and np.linalg.norm(s.vertices[:, :2].mean(0)) < 0.01:
            return float(np.linalg.norm(s.vertices[:, :2] - s.vertices[:, :2].mean(0), axis=1).mean())
    return None


def main():
    os.makedirs(OUT, exist_ok=True)
    Y = trimesh.transformations.rotation_matrix(-math.pi / 2, (1, 0, 0)); loi = []; bao = {}
    for ten, (fn, mo_ta) in BO.items():
        parts = fn(); tg = sum(len(m.faces) for m in parts.values()); kin = all(m.is_watertight for m in parts.values())
        mau_nha = all(np.allclose(np.asarray(m.visual.material.baseColorFactor, float) / (255 if np.asarray(m.visual.material.baseColorFactor).max() > 1 else 1),
                                  np.asarray(TM.mau(MAU[m.visual.material.name])), atol=0.01) for m in parts.values())   # cửa ⑧ màu nhà (Boss 22/10)
        r = ban_kinh_cho_cam(parts) if ten in CO_CAN else None
        dai = float(np.ptp(np.vstack([m.vertices for m in parts.values()]), axis=0).max())
        gay = goc_gay(parts) if ten == "can_cau" else None   # cửa ⑦ cần câu không gãy: mọi khớp ≤ 8°
        ok = kin and tg <= 600 and (r is None or 0.013 <= r <= 0.017) and (gay is None or gay <= 8) and mau_nha
        (lambda: None)() if ok else loi.append(ten)
        print(f"  {'✅' if ok else '❌'} {ten:10s} {mo_ta:18s} {tg:4d} tam giác · kín {kin} · dài {dai:.2f} m · cán tại gốc " + (f"{r * 1000:.1f} mm" if r else "—") + (f" · khớp gập lớn nhất {gay:.0f}°" if gay is not None else ""))
        sc = trimesh.Scene()
        for k, m in parts.items():
            g = m.copy(); g.apply_transform(Y); sc.add_geometry(g, node_name=k)
        sc.export(f"{OUT}/{ten}.glb"); bao[ten] = dict(mo_ta=mo_ta, tam_giac=tg, dai_m=round(dai, 3), r_can_mm=None if r is None else round(r * 1000, 1))
    json.dump(dict(hop_dong="gốc = tâm chỗ cầm; trục cán = +Z; phía làm việc = +X; khớp socket cam_* (trụ Ø32, --co 1)", mon=bao),
              open(f"{OUT}/tools.json", "w"), ensure_ascii=False, indent=1)
    print("⛔ CÔNG CỤ TRƯỢT " + ", ".join(loi) if loi else "✅ CÔNG CỤ ĐẠT", OUT); sys.exit(1 if loi else 0)


if __name__ == "__main__":
    main()

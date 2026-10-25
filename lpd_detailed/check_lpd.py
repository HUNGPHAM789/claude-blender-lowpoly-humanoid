"""Cửa soi LPD (phiên bản chi tiết) — đo trên GLB đã xuất. python3 check_lpd.py <BODY.glb> nam|nu  ⇒ rc=1 nếu trượt.
① tổng 2.420 tam giác (spec) ② ĐẦU NGÓN TAY: điểm thấp nhất của tay / chiều cao ∈ [0,39; 0,44] (Boss 22/10 «tay hơi dài»: bản đầu 0,369)
③ NGỰC (nữ): nhô trước ≥15 mm so với rãnh giữa ngực VÀ ≥15 mm so với nếp dưới ngực · nam: nhô ≤10 mm (Boss 22/10 «nữ thì chưa thấy ngực»)."""
import sys, math, numpy as np, trimesh


def tia_truoc(m, x, z):
    tri = m.triangles; o = np.array([x, -5.0, z]); d = np.array([0, 1.0, 0])
    e1, e2 = tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0]; pv = np.cross(d, e2); det = np.einsum("ij,ij->i", e1, pv)
    ok = np.abs(det) > 1e-12; inv = np.where(ok, 1 / np.where(ok, det, 1), 0); tv = o - tri[:, 0]
    u = np.einsum("ij,ij->i", tv, pv) * inv; qv = np.cross(tv, e1); v = (qv @ d) * inv; t = np.einsum("ij,ij->i", e2, qv) * inv
    h = ok & (u >= 0) & (v >= 0) & (u + v <= 1)
    return float(t[h].min() - 5.0) if h.any() else None


def soi(path, gioi):
    sc = trimesh.load(path, force="scene"); m = sc.to_geometry()
    m.apply_transform(trimesh.transformations.rotation_matrix(math.pi / 2, (1, 0, 0)))   # Y-lên → Z-lên
    m.apply_translation((0, 0, -m.bounds[0][2])); H = m.bounds[1][2]; loi, ghi = [], []
    tg = len(m.faces); (ghi if tg == 2420 else loi).append(f"① tam giác {tg} (2.420)")
    v = m.vertices; tay = v[np.abs(v[:, 0]) > 0.24 * H / 1.75]                          # đỉnh ngoài thân = tay
    r = tay[:, 2].min() / H; (ghi if 0.39 <= r <= 0.44 else loi).append(f"② đầu ngón tay ở {r:.3f}·H (0,39–0,44)")
    k = H / 1.75; z = 1.225 * k
    nguc = min(y for y in (tia_truoc(m, sx * 0.055 * k, z) for sx in (1, -1)) if y is not None)
    giua = tia_truoc(m, 0.0, z); duoi = tia_truoc(m, 0.055 * k, 1.15 * k)
    nho1 = (giua - nguc) * 1000; nho2 = (duoi - nguc) * 1000
    if gioi == "nu": ok = nho1 >= 15 and nho2 >= 15; can = "≥15/≥15"
    else: ok = nho1 <= 10 and nho2 <= 10; can = "≤10/≤10"   # cơ ngực nam nhô tự nhiên ~8 mm
    (ghi if ok else loi).append(f"③ ngực: nhô trước rãnh giữa {nho1:.0f} mm · trước nếp dưới {nho2:.0f} mm ({can})")
    import json, struct   # ④ MẮT = hốc lõm + bóng (Boss 23/10 chốt C «Lấy design mặt C»), cấm ô mắt đen Eye_Dark
    b_ = open(path, "rb").read(); j_ = json.loads(b_[20:20 + struct.unpack("<I", b_[12:16])[0]]); vl = [x["name"] for x in j_.get("materials", [])]
    (ghi if "Eye_Dark" not in vl and "Socket_Shade" in vl else loi).append(f"④ mắt hốc lõm + bóng (vật liệu: {vl})")
    for d in ghi: print("  ✅", d)
    for d in loi: print("  ❌", d)
    print(("⛔ LPD TRƯỢT " if loi else "✅ LPD ĐẠT ") + path); return 1 if loi else 0


if __name__ == "__main__":
    sys.exit(soi(sys.argv[1], sys.argv[2]))

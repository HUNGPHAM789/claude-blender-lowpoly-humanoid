"""VỎ VA CHẠM (boundary layer) — Boss 22/10/2026: «Toàn bộ body của nhân vật hay bất cứ vật thể nào cũng phải set boundary layer sau khi
chốt xong modeling finished của vật thể đó».
  · NHÂN VẬT (có rig + skin): `vo_nguoi(rig, meshes)` — mỗi xương biến dạng 1 VIÊN NANG (capsule) fit từ các đỉnh có trọng số ≥ 0,5
    (thân + quần áo + tóc), ở tư thế NGHỈ, lưu theo khung xương ⇒ đi theo mọi tư thế. Gọi ngay sau khi gắn skin (animate.py sau H.da).
  · VẬT TĨNH (lpms): khối lồi từng bộ phận (lpms.py ghi shatter.json khi render).
  · Đo: `kc(p, vo_tg)` = khoảng cách CÓ DẤU từ điểm tới vỏ (âm = trong vỏ = xuyên). Mọi cửa tiếp xúc/xuyên dùng chung vỏ này,
    ⛔ không tự đặt bán kính tay (R_DAU = 0,095 kiểu đoán).
"""
import json, math
import numpy as np
import bpy, mathutils

V = mathutils.Vector


def vo_nguoi(rig, meshes, out=None, nguong=0.5, pc=95):
    """capsule/xương: trục = đầu→đuôi xương (nghỉ); đoạn = khoảng chiếu của đỉnh; r = phân vị pc khoảng cách vuông góc. Trả {xương: (a, b, r)} khung xương."""
    vo = {}
    for b in rig.data.bones:
        if not b.use_deform: continue
        h = b.head_local; t = b.tail_local; ax = (t - h).normalized(); pts = []
        for o in meshes:
            g = o.vertex_groups.get(b.name)
            if g is None: continue
            Mo = rig.matrix_world.inverted() @ o.matrix_world
            for v in o.data.vertices:
                for e in v.groups:
                    if e.group == g.index and e.weight >= nguong: pts.append(Mo @ v.co); break
        if len(pts) < 6: continue
        P = np.array([tuple(p - h) for p in pts]); a_ = np.asarray(tuple(ax)); s = P @ a_; d = np.linalg.norm(P - np.outer(s, a_), axis=1)
        r = float(np.percentile(d, pc)); s0, s1 = float(np.percentile(s, 2)) + r * 0.5, float(np.percentile(s, 98)) - r * 0.5
        if s1 < s0: s0 = s1 = (s0 + s1) / 2
        Mi = b.matrix_local.inverted(); vo[b.name] = (list(Mi @ (h + ax * s0)), list(Mi @ (h + ax * s1)), round(r, 4))
    if out: json.dump(vo, open(out, "w"), indent=1)
    return vo


def vo_the_gioi(rig, vo):
    """capsule ở TƯ THẾ HIỆN TẠI (thế giới): [(xương, A, B, r)]."""
    W = rig.matrix_world; out = []
    for b, (a, c, r) in vo.items():
        M = W @ rig.pose.bones[b].matrix; out.append((b, M @ V(a), M @ V(c), r))
    return out


def kc_doan(p, a, b):
    ab = b - a; t = 0.0 if ab.length_squared < 1e-12 else max(0.0, min(1.0, (p - a).dot(ab) / ab.length_squared)); return (p - (a + ab * t)).length


def kc(p, vo_tg, bo_qua=()):
    """khoảng cách có dấu điểm → vỏ (âm = xuyên), trả (giá trị, xương gần nhất)."""
    best = (9.0, None)
    for b, A, B, r in vo_tg:
        if b in bo_qua: continue
        d = kc_doan(p, A, B) - r
        if d < best[0]: best = (d, b)
    return best


def kc_tru(c, ax, r_tru, dai, vo_tg, bo_qua=(), mau=9):
    """khe hở nhỏ nhất giữa một TRỤ (khúc gỗ, cán) và vỏ người: lấy mẫu dọc trục trụ, trừ bán kính trụ."""
    best = (9.0, None)
    for i in range(mau):
        p = c + ax * dai * (i / (mau - 1) - 0.5); d, b = kc(p, vo_tg, bo_qua); d -= r_tru
        if d < best[0]: best = (d, b)
    return best


def vo_vat(parts):
    """vật tĩnh (trimesh parts): khối lồi từng bộ phận ⇒ {bộ phận: đỉnh hull}. Dùng trong lpms.py."""
    return {k: np.round(m.convex_hull.vertices, 5).tolist() for k, m in parts.items()}


def long_ban_tay(rig, meshes, b, nguong=0.5):
    """NHÃN LÒNG BÀN TAY (Boss 23/10 «Có setup hay label nào cho mặt bàn tay hay gì ko»): đo từ lưới ở tư thế NGHỈ, khung xương hand_<b>.
    Hướng lòng tay = phía các ĐẦU NGÓN lệch khỏi trục xương (ngón luôn cong về lòng tay); tâm lòng tay = điểm ngoài cùng theo hướng đó ở giữa
    bàn tay. Trả {"tam": [x,y,z], "phap_tuyen": [x,y,z], "do_tin": độ lệch đầu ngón m} — tâm tính từ ĐẦU xương (cổ tay), toạ độ khung xương."""
    bone = rig.data.bones[f"hand_{b}"]; Mi = bone.matrix_local.inverted(); L = bone.length; pts = []
    for o in meshes:
        g = o.vertex_groups.get(f"hand_{b}")
        if g is None: continue
        Mo = rig.matrix_world.inverted() @ o.matrix_world
        for v in o.data.vertices:
            if any(e.group == g.index and e.weight >= nguong for e in v.groups): pts.append(Mi @ (Mo @ v.co))
    P = np.array([tuple(p) for p in pts]); y85 = np.percentile(P[:, 1], 85)
    tip = P[P[:, 1] >= y85][:, [0, 2]].mean(0) - P[:, [0, 2]].mean(0); do_tin = float(np.linalg.norm(tip))
    pn = np.array((tip[0], 0.0, tip[1])) / max(1e-9, do_tin)
    band = P[(P[:, 1] >= 0.3 * L) & (P[:, 1] <= 0.75 * L)]; ra = float((band @ pn).max())
    tam = band.mean(0); tam = tam - pn * (tam @ pn) + pn * ra
    return {"tam": [round(float(x), 4) for x in tam], "phap_tuyen": [round(float(x), 4) for x in pn], "do_tin": round(do_tin, 4)}

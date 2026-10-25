"""ĐO NÁCH LÕM (Boss 23/10/2026: «Nách bị lỏm gắt»): mặt da VÙNG NÁCH = mặt có đỉnh mang trọng số bắp tay (upperarm_*) VÀ thân
(chest/clavicle/spine) — tỉ lệ diện tích hiện tại / lúc nghỉ; da sụp ⇒ mặt co lại. Trả {b: (tỉ lệ nhỏ nhất, phân vị 10 %)}."""
import bpy, numpy as np


def mat_nach(o, b, nguong=0.15):
    nh = {g.index: g.name for g in o.vertex_groups}; tay = f"upperarm_{b}"; than = {"chest", f"clavicle_{b}", "spine"}
    def co(v, ten): return any(nh.get(e.group) in ten and e.weight >= nguong for e in v.groups)
    vt = [co(v, {tay}) for v in o.data.vertices]; vth = [co(v, than) for v in o.data.vertices]
    return [p.index for p in o.data.polygons if any(vt[i] for i in p.vertices) and any(vth[i] for i in p.vertices)]


def dien_tich(o, ids, eval_=True):
    if eval_:
        dg = bpy.context.evaluated_depsgraph_get(); oe = o.evaluated_get(dg); me = oe.to_mesh()
    else: me = o.data
    P = np.array([tuple(v.co) for v in me.vertices]); out = []
    for i in ids:
        vs = me.polygons[i].vertices; a = P[vs[0]]; s = 0.0
        for k in range(1, len(vs) - 1): s += 0.5 * np.linalg.norm(np.cross(P[vs[k]] - a, P[vs[k + 1]] - a))
        out.append(s)
    if eval_: oe.to_mesh_clear()
    return np.array(out)


def measure_armpit(o, khung, sc=None):
    sc = sc or bpy.context.scene; kq = {}
    for b in "LR":
        ids = mat_nach(o, b)
        if not ids: continue
        a0 = dien_tich(o, ids, eval_=False) + 1e-9; mn = 9.0; p10 = 9.0
        for f in khung:
            sc.frame_set(f); r = dien_tich(o, ids) / a0; mn = min(mn, float(r.min())); p10 = min(p10, float(np.percentile(r, 10)))
        kq[b] = (round(mn, 3), round(p10, 3), len(ids))
    return kq


def them_xuong_nach(rig, meshes, ban_kinh=0.13, chia=0.5):
    """XƯƠNG PHỤ VAI–NÁCH (Boss 23/10: «Làm xương phụ vai nách»): xương `nach_<b>` ở khớp vai, CON của xương đòn, hướng như bắp tay lúc nghỉ.
    Đỉnh da trong bán kính quanh khớp vai mà trọng số trộn bắp tay + thân ⇒ chuyển 2·min(bắp, thân)·chia sang xương phụ (lấy đều từ hai bên).
    Xoay mỗi khung bằng nuong_xuong_nach(). Xuất glTF như xương thường ⇒ engine nào cũng chạy (khác DQS)."""
    import mathutils
    bpy.ops.object.select_all(action="DESELECT"); rig.select_set(True); bpy.context.view_layer.objects.active = rig; bpy.ops.object.mode_set(mode="EDIT")
    E = rig.data.edit_bones
    for b in "LR":
        ua = E[f"upperarm_{b}"]; nb = E.new(f"nach_{b}"); nb.head = ua.head.copy(); nb.tail = ua.head + (ua.tail - ua.head).normalized() * 0.08
        nb.roll = ua.roll; nb.parent = E[f"clavicle_{b}"]; nb.use_connect = False; nb.use_deform = True
    bpy.ops.object.mode_set(mode="OBJECT")
    for pb in rig.pose.bones: pb.rotation_mode = "QUATERNION"
    so = {}
    for o in meshes:
        nh = {g.index: g.name for g in o.vertex_groups}; M = rig.matrix_world.inverted() @ o.matrix_world
        for b in "LR":
            vai = rig.data.bones[f"upperarm_{b}"].head_local; gh = o.vertex_groups.get(f"nach_{b}") or o.vertex_groups.new(name=f"nach_{b}")
            gu = o.vertex_groups.get(f"upperarm_{b}"); than = [o.vertex_groups.get(n) for n in ("chest", f"clavicle_{b}", "spine") if o.vertex_groups.get(n)]
            if gu is None: continue
            k = 0
            for v in o.data.vertices:
                if ((M @ v.co) - vai).length > ban_kinh: continue
                w = {nh[e.group]: e.weight for e in v.groups}; wu = w.get(f"upperarm_{b}", 0.0); wt = sum(w.get(g.name, 0.0) for g in than)
                h = 2 * min(wu, wt) * chia
                if h < 0.02: continue
                gh.add([v.index], h, "REPLACE"); gu.add([v.index], wu - h / 2, "REPLACE")
                for g in than:   # bớt đều phần thân theo tỉ lệ
                    wg = w.get(g.name, 0.0)
                    if wg > 0: g.add([v.index], max(0.0, wg - (h / 2) * wg / wt), "REPLACE")
                k += 1
            so[(o.name, b)] = k
    return so


def nuong_xuong_nach(rig, khung, chia=0.5):
    """mỗi khung: xương phụ xoay = slerp(«cứng theo xương đòn», «cứng theo bắp tay», chia) ⇒ da nách nằm giữa, không gãy gập."""
    W = rig.matrix_world
    for f in khung:
        bpy.context.scene.frame_set(f); bpy.context.view_layer.update()
        for b in "LR":
            Bn, Bc, Bu = rig.data.bones[f"nach_{b}"], rig.data.bones[f"clavicle_{b}"], rig.data.bones[f"upperarm_{b}"]
            Pc, Pu = rig.pose.bones[f"clavicle_{b}"], rig.pose.bones[f"upperarm_{b}"]; pn = rig.pose.bones[f"nach_{b}"]
            qa = (Pc.matrix.to_3x3().normalized() @ Bc.matrix_local.to_3x3().normalized().inverted() @ Bn.matrix_local.to_3x3().normalized()).to_quaternion()
            qb = (Pu.matrix.to_3x3().normalized() @ Bu.matrix_local.to_3x3().normalized().inverted() @ Bn.matrix_local.to_3x3().normalized()).to_quaternion()
            if qa.dot(qb) < 0: qb = -qb
            m = qa.slerp(qb, chia).to_matrix().to_4x4(); m.translation = Pu.matrix.translation; pn.matrix = m; bpy.context.view_layer.update()
            pn.keyframe_insert("rotation_quaternion", frame=f); pn.keyframe_insert("location", frame=f)


def measure_armpit_ids(o, ids_theo_ben, khung, sc=None):
    """như measure_armpit nhưng trên TẬP MẶT CỐ ĐỊNH (lấy từ trọng số GỐC trước khi sửa) ⇒ so trước/sau công bằng."""
    sc = sc or bpy.context.scene; kq = {}
    for b, ids in ids_theo_ben.items():
        a0 = dien_tich(o, ids, eval_=False) + 1e-9; mn = 9.0; p10 = 9.0
        for f in khung:
            sc.frame_set(f); r = dien_tich(o, ids) / a0; mn = min(mn, float(r.min())); p10 = min(p10, float(np.percentile(r, 10)))
        kq[b] = (round(mn, 3), round(p10, 3), len(ids))
    return kq

"""humanoid-rig-animation — lõi chạy TRONG Blender (bpy). Skill CHA: rig, bộ đổi trục giải phẫu, IK chân theo tiếp đất,
gắn đạo cụ, retarget BVH (Kimodo/SOMA), cửa đo, render, xuất GLB. Skill con (vd settler-actions) chỉ đưa JSON clip + hồ sơ rig.

Spec gốc: hỏi ChatGPT 2 vòng 22/10/2026 (spec/tra1.md, tra2.md). Quy ước:
  · Nhân vật: Z lên, mặt nhìn −Y, TRÁI = +X. Đơn vị m, độ (đổi radian ở biên Blender). 24 fps, khoá 0…N, vòng lặp chơi [0,N).
  · Trục giải phẫu (không gian nghỉ của nhân vật): thân yaw +Z, pitch(cúi) +X, roll(nghiêng trái) +Y; hông/shoulder gập −X;
    gối gập +X; khuỷu gập −X; dạng trái −Y / dạng phải +Y; cổ chân gập mu −X. Xoay dọc = trục xương.
  · B_i = Π Q(R_i⁻¹·a, θ) theo thứ tự: thân yaw→pitch→roll; hông/shoulder gập→dạng→xoay; khuỷu gập→sấp ngửa; gối chỉ gập.
    (Bản tay đầu tiên «vặn» quanh Z local = NGHIÊNG NGANG — cửa ⓪ bắt lỗi này.)
"""
import bpy, bmesh, json, math, os, subprocess, shutil, mathutils
V = mathutils.Vector; Q = mathutils.Quaternion; M4 = mathutils.Matrix
FPS = 24

TRUC = {  # kênh → trục giải phẫu (không gian nghỉ nhân vật); 'doc' = dọc xương
    "yaw": V((0, 0, 1)), "pitch": V((1, 0, 0)), "roll": V((0, 1, 0)),
    "flex_hip": V((-1, 0, 0)), "flex_knee": V((1, 0, 0)), "flex_sh": V((-1, 0, 0)), "flex_el": V((-1, 0, 0)), "dorsi": V((-1, 0, 0)),
}
THU_TU = {"than": ("yaw", "pitch", "roll"), "chi_tren": ("flex", "abd", "twist"), "khuyu": ("flex", "twist"), "goi": ("flex",)}
LOAI = {"hips": "than", "spine": "than", "chest": "than", "neck": "than", "head": "than",
        "upperarm_L": "chi_tren", "upperarm_R": "chi_tren", "thigh_L": "chi_tren", "thigh_R": "chi_tren",
        "forearm_L": "khuyu", "forearm_R": "khuyu", "shin_L": "goi", "shin_R": "goi", "clavicle_L": "chi_tren", "clavicle_R": "chi_tren",   # đòn: abd = nâng
        "hand_L": "khuyu", "hand_R": "khuyu", "foot_L": "goi", "foot_R": "goi"}


def truc_kenh(xuong, kenh):
    ben = xuong[-1] if xuong[-2:] in ("_L", "_R") else ""
    if kenh in ("yaw", "pitch", "roll"): return TRUC[kenh]
    if kenh == "abd": return V((0, -1, 0)) if ben == "L" else V((0, 1, 0))
    if kenh == "flex":
        if xuong.startswith(("thigh",)): return TRUC["flex_hip"]
        if xuong.startswith(("shin",)): return TRUC["flex_knee"]
        if xuong.startswith(("upperarm",)): return TRUC["flex_sh"]
        if xuong.startswith(("forearm", "hand")): return TRUC["flex_el"]
        if xuong.startswith("foot"): return TRUC["dorsi"]
    return None   # twist: trục xương


def q_giai_phau(rig, xuong, kenh):
    """B_i từ dict kênh→độ theo đúng thứ tự cho loại khớp."""
    R = rig.data.bones[xuong].matrix_local.to_quaternion(); Ri = R.inverted(); q = Q()
    for k in THU_TU[LOAI[xuong]]:
        g = kenh.get(k, 0.0)
        if not g: continue
        a = truc_kenh(xuong, k)
        al = V((0, 1, 0)) if a is None else (Ri @ a).normalized()   # trục dọc xương = +Y local
        q = q @ Q(al, math.radians(g))
    return q.normalized()


# ------------------------------------------------------------------ RIG + DA
def nhap(f):
    t = set(bpy.data.objects); bpy.ops.import_scene.gltf(filepath=f)
    ms = [o for o in bpy.data.objects if o not in t and o.type == "MESH"]
    for o in ms:   # nướng biến đổi glTF vào lưới
        mw = o.matrix_world.copy(); o.parent = None; o.data.transform(mw); o.matrix_world = M4.Identity(4)
        for p in o.data.polygons: p.use_smooth = False
    for o in [o for o in bpy.data.objects if o not in t and o.type == "EMPTY"]: bpy.data.objects.remove(o)
    return ms


def xuong_tu_khop(K):
    X = [("hips", "chau", "bung", "goc"), ("spine", "bung", "nguc", "hips"), ("chest", "nguc", "co", "spine"),
         ("neck", "co", "dau", "chest"), ("head", "dau", "dinh_dau", "neck")]
    for b in "LR":
        K[f"cuoi_tay_{b}"] = K[f"co_tay_{b}"] + (K[f"co_tay_{b}"] - K[f"khuyu_{b}"]).normalized() * 0.10
        X += [(f"clavicle_{b}", f"xuong_don_{b}", f"vai_{b}", "chest"), (f"upperarm_{b}", f"vai_{b}", f"khuyu_{b}", f"clavicle_{b}"),
              (f"forearm_{b}", f"khuyu_{b}", f"co_tay_{b}", f"upperarm_{b}"), (f"hand_{b}", f"co_tay_{b}", f"cuoi_tay_{b}", f"forearm_{b}"),
              (f"thigh_{b}", f"hong_{b}", f"goi_{b}", "hips"), (f"shin_{b}", f"goi_{b}", f"co_chan_{b}", f"thigh_{b}"),
              (f"foot_{b}", f"co_chan_{b}", f"mui_chan_{b}", f"shin_{b}")]
    return X


def dung_rig(K):
    sc = bpy.context.scene; arm = bpy.data.armatures.new("rig"); ob = bpy.data.objects.new("rig", arm); sc.collection.objects.link(ob)
    bpy.context.view_layer.objects.active = ob; bpy.ops.object.mode_set(mode="EDIT"); eb = arm.edit_bones
    g = eb.new("goc"); g.head = (0, 0, 0); g.tail = (0, 0.25, 0); g.use_deform = False
    K = dict(K)
    for b_ in "LR": K[f"goi_{b_}"] = K[f"goi_{b_}"] + V((0, -0.02, 0))   # gối nghỉ gập sẵn ~5° (spec): chân thẳng = điểm kỳ dị IK ⇒ gót lún 18–26 mm
    for ten, h, t, cha in xuong_tu_khop(K):
        b = eb.new(ten); b.head = K[h]; b.tail = K[t]; b.parent = eb[cha]
        b.align_roll(V((0, 0, 1)) if ten.startswith("foot") else V((0, -1, 0)))
    for b in "LR":
        ik = eb.new(f"ik_{b}"); ik.head = K[f"co_chan_{b}"]; ik.tail = K[f"mui_chan_{b}"]; ik.align_roll(V((0, 0, 1))); ik.use_deform = False
    bpy.ops.object.mode_set(mode="POSE")
    for b in "LR":
        c = ob.pose.bones[f"shin_{b}"].constraints.new("IK"); c.target = ob; c.subtarget = f"ik_{b}"; c.chain_count = 2
        sh = ob.pose.bones[f"shin_{b}"]; sh.lock_ik_y = sh.lock_ik_z = True   # gối = bản lề; đùi ĐƯỢC xoắn (khoá xoắn + hông yaw ⇒ IK hụt 18–26 mm, gót lún)
        r = ob.pose.bones[f"foot_{b}"].constraints.new("COPY_ROTATION"); r.target = ob; r.subtarget = f"ik_{b}"
    for pb in ob.pose.bones: pb.rotation_mode = "QUATERNION"
    bpy.ops.object.mode_set(mode="OBJECT"); return ob


def da(than, do, toc, rig):
    """thân: hàn đỉnh → heat weight → ≤4 ảnh hưởng, chuẩn hoá; đồ: chép trọng số từ thân; tóc: cứng theo đầu."""
    bm = bmesh.new(); bm.from_mesh(than.data); bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5); bm.to_mesh(than.data); bm.free()
    bpy.ops.object.select_all(action="DESELECT"); than.select_set(True); rig.select_set(True); bpy.context.view_layer.objects.active = rig
    bpy.ops.object.parent_set(type="ARMATURE_AUTO")
    bpy.context.view_layer.objects.active = than
    bpy.ops.object.vertex_group_limit_total(group_select_mode="ALL", limit=4); bpy.ops.object.vertex_group_normalize_all(lock_active=False)
    trong = sum(1 for v in than.data.vertices if not v.groups)
    if trong:   # bone heat KHÔNG lan tới đảo lưới rời (tai nữ: 28 đỉnh, 23/10) ⇒ chép trọng số từ đỉnh CÓ trọng số gần nhất; vẫn báo số đã chép
        kd = mathutils.kdtree.KDTree(len(than.data.vertices)); co_ = [v for v in than.data.vertices if v.groups]
        for i, v in enumerate(co_): kd.insert(v.co, i)
        kd.balance(); ten_ = {g.index: g.name for g in than.vertex_groups}
        for v in [v for v in than.data.vertices if not v.groups]:
            nguon = co_[kd.find(v.co)[1]]
            for e in nguon.groups: than.vertex_groups[ten_[e.group]].add([v.index], e.weight, "REPLACE")
        print("DA chép trọng số lân cận cho", trong, "đỉnh (đảo lưới rời)")
        trong = sum(1 for v in than.data.vertices if not v.groups)
    for o in do:
        for g in than.vertex_groups: o.vertex_groups.new(name=g.name)
        m = o.modifiers.new("dt", "DATA_TRANSFER"); m.object = than; m.use_vert_data = True; m.data_types_verts = {"VGROUP_WEIGHTS"}
        m.vert_mapping = "POLYINTERP_NEAREST"; m.layers_vgroup_select_src = "ALL"; m.layers_vgroup_select_dst = "NAME"
        bpy.context.view_layer.objects.active = o; bpy.ops.object.modifier_apply(modifier="dt")
        o.modifiers.new("arm", "ARMATURE").object = rig; o.parent = rig
    for o in toc:
        o.vertex_groups.new(name="head").add([v.index for v in o.data.vertices], 1.0, "REPLACE")
        o.modifiers.new("arm", "ARMATURE").object = rig; o.parent = rig
    return trong


def gan_dao_cu(rig, f_glb, ben, socket, huong_x):
    """đạo cụ cầm tay: gốc = socket cam_*, +Z món = trục socket, +X món theo huong_x. Gắn ở TƯ THẾ NGHỈ, trước khi đặt khoá."""
    ms = nhap(f_glb); e = bpy.data.objects.new("dc_" + os.path.basename(f_glb)[:-4], None); bpy.context.scene.collection.objects.link(e)
    for o in ms: o.parent = e
    z = V(socket["len"]).normalized(); x = V(huong_x); x = (x - z * x.dot(z)).normalized()
    W = M4.Translation(V(socket["vi_tri"])) @ M4((x, z.cross(x), z)).transposed().to_4x4()
    e.parent = rig; e.parent_type = "BONE"; e.parent_bone = f"hand_{ben}"; bpy.context.view_layer.update(); e.matrix_world = W
    return e


def ngam(rig, ten, dich):
    """xoay pose-bone (theo thế giới) để hướng đầu→đuôi trùng `dich` (giữ vị trí đầu)."""
    pb = rig.pose.bones[ten]; W = rig.matrix_world; cur = ((W @ pb.tail) - (W @ pb.head)).normalized()
    R = cur.rotation_difference(dich.normalized()).to_matrix(); m = pb.matrix.copy(); t = m.translation.copy()
    m3 = R @ m.to_3x3(); m4 = m3.to_4x4(); m4.translation = t; pb.matrix = m4; bpy.context.view_layer.update()


def riu_tu_mocap(dao_cu, N, dai=0.67):
    """quỹ đạo rìu từ hai cổ tay NGUỒN (MP_TAY): gốc = cổ tay phải, cán = hướng phải→trái (làm mượt 5 khung), lưỡi = chiều chuyển động đầu rìu."""
    dao_cu.parent = None; dao_cu.rotation_mode = "QUATERNION"; Z = []
    if os.environ.get("CHU_KY") and "," in os.environ["CHU_KY"]:   # trộn mối nối cho chính quỹ đạo rìu: khung b ≡ khung a
        a_, b_ = (int(x) for x in os.environ["CHU_KY"].split(",")); b_ = min(b_, len(MP_TAY) - 1); k_ = int(os.environ.get("TRON", "4")); dR = MP_TAY[a_][0] - MP_TAY[b_][0]; dL = MP_TAY[a_][1] - MP_TAY[b_][1]
        for f in range(b_ - k_, b_ + 1):
            u = (f - (b_ - k_)) / k_; w = u * u * (3 - 2 * u); MP_TAY[f] = (MP_TAY[f][0] + dR * w, MP_TAY[f][1] + dL * w)
    for R_, L_ in MP_TAY: Z.append((R_ - L_).normalized())
    Zs = [sum(Z[max(0, i - 2): i + 3], V()).normalized() for i in range(len(Z))]
    dau = [MP_TAY[i][0] + Zs[i] * dai for i in range(len(Z))]; xp = None
    for f in range(min(N, len(Z) - 1) + 1):
        z = Zs[f]; v = dau[min(f + 1, len(dau) - 1)] - dau[max(f - 1, 0)]; x = v - z * v.dot(z)
        x = x.normalized() if x.length > 1e-3 else (xp or z.orthogonal().normalized())
        if xp is not None and x.dot(xp) < -0.2 and v.length < 0.05: x = xp   # đầu rìu gần như đứng yên: giữ chiều lưỡi
        xp = x
        dao_cu.matrix_world = mathutils.Matrix.Translation(MP_TAY[f][0]) @ mathutils.Matrix((x, z.cross(x), z)).transposed().to_4x4()
        dao_cu.keyframe_insert("location", frame=f); dao_cu.keyframe_insert("rotation_quaternion", frame=f)


def z_nam(zc, f):
    """chỗ nắm trên cán: số cố định, hoặc {khung: z} nội suy tuyến tính — tay TRƯỢT dọc cán (người thật chém: tay phải trượt xuống sát tay trái
    lúc trúng; giữ cố định ⇒ tay phải với 0,60 m > tầm 0,56 m, lệch nắm 130 mm — 22/10)."""
    if not isinstance(zc, dict): return zc
    k = sorted((int(a), b) for a, b in zc.items())
    if f <= k[0][0]: return k[0][1]
    for (a, za), (b, zb) in zip(k, k[1:]):
        if f <= b: return za + (zb - za) * (f - a) / (b - a)
    return k[-1][1]


def nam_hai_tay(rig, SK, dao_cu, tay, N):
    """RÌU HAI TAY — giải tích, không dùng IK của Blender (cực khuỷu chập chờn, nắm trượt 21 cm, cổ tay gập 141°):
    bàn tay ⟂ cán, chĩa từ vai về chỗ nắm; trục nắm = trục cán; cổ tay = chỗ nắm − R·o0; khuỷu = điểm trên vòng tròn 2 đoạn
    gần nhất với «cổ tay − hướng bàn tay × dài cẳng» (cẳng nối thẳng bàn tay)."""
    sc = bpy.context.scene; W = rig.matrix_world
    for f in range(N + 1):
        sc.frame_set(f); bpy.context.view_layer.update(); M = dao_cu.matrix_world; z = (M.to_3x3() @ V((0, 0, 1))).normalized()
        for ben, z_cam in tay:
            hb = rig.data.bones[f"hand_{ben}"]; so = SK[f"cam_{ben}"]
            a0 = V(so["len"]).normalized(); h0 = (hb.tail_local - hb.head_local).normalized(); o0 = V(so["vi_tri"]) - hb.head_local
            g = M @ V((0, 0, z_nam(z_cam, f))); S_ = W @ rig.pose.bones[f"upperarm_{ben}"].head
            h_goc = (g - S_) - z * (g - S_).dot(z); h_goc = h_goc.normalized() if h_goc.length > 1e-4 else V((0, -1, 0))
            a0p = (a0 - h0 * a0.dot(h0)).normalized(); B0 = mathutils.Matrix((h0, a0p, h0.cross(a0p))).transposed()
            Lu = rig.data.bones[f"upperarm_{ben}"].length; Lf = rig.data.bones[f"forearm_{ben}"].length
            tot = None
            for dg in range(-60, 61, 10):   # dò hướng bàn tay quanh cán (±90°: khuỷu đạt nhưng cổ tay 71° — chọn ±60): chọn cổ tay gập ÍT NHẤT (cổ tay gập 50,4° với hướng cố định)
                h = mathutils.Quaternion(z, math.radians(dg)) @ h_goc
                zp = (z - h * z.dot(h)).normalized(); B = mathutils.Matrix((h, zp, h.cross(zp))).transposed(); R = B @ B0.transposed()
                Wt = g - R @ o0; d_ = Wt - S_; dl = min(d_.length, Lu + Lf - 1e-4); u = d_.normalized()
                a_ = (Lu * Lu - Lf * Lf + dl * dl) / (2 * dl); r_ = math.sqrt(max(0.0, Lu * Lu - a_ * a_)); Cc = S_ + u * a_
                Eh = Wt - h * Lf; v1 = (Eh - Cc) - u * (Eh - Cc).dot(u); dn = V((0, 0, -1)) - u * (-u.z)
                cg = W @ rig.pose.bones["chest"].head; ngoai = S_ - V((cg.x, cg.y, S_.z)); ngoai.z = 0   # hướng ra ngoài vai
                ngoai = (ngoai - u * ngoai.dot(u)); ngoai = ngoai.normalized() if ngoai.length > 1e-5 else dn
                for w_, w2 in ((0.0, 0.0), (0.35, 0.0), (0.7, 0.0), (1.0, 0.0), (0.3, 0.4), (0.5, 0.5), (0.2, 0.7), (0.0, 1.0)):
                    # khuỷu: «cẳng nối thẳng bàn tay» → «buông xuống» → «ra NGOÀI» (Codex: cổ tay chờ gập 63°, khuỷu lấy đà 147°)
                    v = v1.normalized() * (1 - w_ - w2) + dn.normalized() * w_ + ngoai * w2 if v1.length > 1e-5 else dn
                    v = (v - u * v.dot(u)); v = v.normalized() if v.length > 1e-5 else u.orthogonal().normalized()
                    E = Cc + v * r_; Wr = S_ + u * dl
                    gap_khuyu = 180 - math.degrees((S_ - E).angle(Wr - E))
                    diem = math.degrees((Wr - E).angle(h)) + float(os.environ.get("PHAT_KHUYU_CAO", "2.0")) * max(0.0, (E.z - (S_.z - 0.10)) * 100) \
                        + 5.0 * max(0.0, gap_khuyu - 140) + (1000 if d_.length > Lu + Lf else 0)
                    if tot is None or diem < tot[0]: tot = (diem, R, E, Wr)
            _, R, E, Wr = tot
            ngam(rig, f"upperarm_{ben}", E - S_); ngam(rig, f"forearm_{ben}", Wr - E)
            pbh = rig.pose.bones[f"hand_{ben}"]; m = (R @ hb.matrix_local.to_3x3()).to_4x4(); m.translation = pbh.matrix.translation; pbh.matrix = m
            bpy.context.view_layer.update()
            for x in ("upperarm", "forearm", "hand"): rig.pose.bones[f"{x}_{ben}"].keyframe_insert("rotation_quaternion", frame=f)


def bam_can(rig, SK, dao_cu, ben, z_cam, N, nhac=0.0, cuc=None, cuc_goc=0.0, ngang=0.0, xoay_tay=True):
    """TAY THỨ HAI bám cán (rìu hai tay): IK cẳng+cánh tay tới cổ tay đích sao cho socket cam_<ben> nằm trên cán ở z_cam (toạ độ món),
    rồi xoay bàn tay cho trục nắm trùng trục cán. Nướng theo từng khung (món là con của tay kia ⇒ không phụ thuộc vòng)."""
    sc = bpy.context.scene; hb = rig.data.bones[f"hand_{ben}"]; so = SK[f"cam_{ben}"]
    a0 = V(so["len"]).normalized(); o0 = V(so["vi_tri"]) - hb.head_local; H0 = hb.matrix_local.to_quaternion()
    tg = bpy.data.objects.new(f"ik_tay_{ben}", None); sc.collection.objects.link(tg)
    c = rig.pose.bones[f"forearm_{ben}"].constraints.new("IK"); c.target = tg; c.chain_count = 2
    if cuc is not None:   # cực khuỷu (theo ngực) ⇒ khuỷu không lật qua lại (Boss 22/10 «cùi chỏ tay vác đang lật qua lật lại»)
        c.pole_target = cuc; c.pole_angle = math.radians(cuc_goc)
    # xoay bàn tay TÍNH TỪ HƯỚNG CẲNG HIỆN TẠI (xoay từ tư thế nghỉ thẳng sang trục cán ⇒ cổ tay gập 176°, cửa ⑭ bắt 22/10)
    pbh = rig.pose.bones[f"hand_{ben}"]; pbf = rig.pose.bones[f"forearm_{ben}"]; F0 = rig.data.bones[f"forearm_{ben}"].matrix_local.to_quaternion()
    h0_ben = (rig.data.bones[f"hand_{ben}"].tail_local - rig.data.bones[f"hand_{ben}"].head_local).normalized(); Lf_ben = rig.data.bones[f"forearm_{ben}"].length
    cuc_tu_dong = None
    if cuc is None and os.environ.get("CUC_TU_DONG", "1") == "1":
        cuc_tu_dong = bpy.data.objects.new(f"cuc_tu_dong_{ben}", None); sc.collection.objects.link(cuc_tu_dong)
        c.pole_target = cuc_tu_dong; c.pole_angle = math.radians(float(os.environ.get("CUC_GOC_TAY", "0")))
    for f in range(N + 1):
        sc.frame_set(f); bpy.context.view_layer.update(); M = dao_cu.matrix_world
        z = (M.to_3x3() @ V((0, 0, 1))).normalized(); g = M @ V((0, 0, z_cam)) + V((0, 0, nhac))
        if ngang: g = g + (M.to_3x3() @ V((1, 0, 0))).normalized() * ngang
        pbh.rotation_quaternion = mathutils.Quaternion(); q = mathutils.Quaternion()
        for _ in range(4):
            Rf = pbf.matrix.to_quaternion() @ F0.inverted()            # cẳng đã xoay bao nhiêu so với nghỉ
            a_cur = Rf @ a0; q1 = a_cur.rotation_difference(z) @ Rf     # theo cẳng + nắn trục nắm vào cán
            # còn tự do XOAY QUANH CÁN: chọn góc để hướng bàn tay gần hướng cẳng nhất (xoay ngắn nhất từng bẻ ngược 171°)
            h0 = (rig.data.bones[f"hand_{ben}"].tail_local - rig.data.bones[f"hand_{ben}"].head_local).normalized(); h1 = q1 @ h0
            d = ((rig.matrix_world @ pbf.tail) - (rig.matrix_world @ pbf.head)).normalized(); dp = d - z * d.dot(z); hp = h1 - z * h1.dot(z)
            if dp.length > 1e-4 and hp.length > 1e-4:
                ang = math.atan2(hp.cross(dp).dot(z), hp.dot(dp)); q = mathutils.Quaternion(z, ang) @ q1
            else: q = q1
            tg.location = g - q @ o0; bpy.context.view_layer.update()
        tg.keyframe_insert("location", frame=f)
        if cuc_tu_dong is not None:   # cực khuỷu = chỗ khuỷu NÊN nằm: lùi từ cổ tay ngược hướng bàn tay một đoạn cẳng ⇒ cẳng ⟂ cán
            hw = (q @ h0_ben).normalized(); cuc_tu_dong.location = tg.location - hw * Lf_ben; cuc_tu_dong.keyframe_insert("location", frame=f)
        m = (q @ H0).to_matrix().to_4x4(); m.translation = pbh.matrix.translation; pbh.matrix = m
        bpy.context.view_layer.update(); pbh.keyframe_insert("rotation_quaternion", frame=f)
    return tg


def riu_quat(dao_cu, qd, N, vong=True, lech=None):
    """RÌU LÀ CHỦ (spec: «Axe is master; both hands solve to grip targets»; Boss 22/10 «đo vòng cung của mũi rìu có đi đúng hình cánh quạt ko?»).
    qd = {tam:[x,y,z], r_tay:m, dai:m (tay→tâm lưỡi), keys:{f:[θ°, cao_tay, cao_luoi]}} — θ=0 hướng trước (−Y), dương = sang TRÁI (+X).
    Đầu rìu đi trên mặt quạt quanh `tam`; cán hướng TỎA RA từ tâm; lưỡi (+X món) = tiếp tuyến chiều θ tăng (= chiều chém)."""
    tam = V(qd["tam"]); keys = {float(k): dict(th=v[0], ht=v[1], hd=v[2], r=(v[3] if len(v) > 3 else qd["r_tay"])) for k, v in qd["keys"].items()}   # noi_suy cần dict; r riêng từng khoá
    dao_cu.parent = None; dao_cu.rotation_mode = "QUATERNION"
    for f in range(N + 1):
        k_ = noi_suy(keys, f, vong, N); th, ht, hd, r_k = k_["th"], k_["ht"], k_["hd"], k_["r"]; t = math.radians(th)
        d = V((math.sin(t), -math.cos(t), 0)); tg = V((math.cos(t), math.sin(t), 0))
        g = V((tam.x, tam.y, 0)) + d * r_k + V((0, 0, ht)) + (lech[f] if lech else V()); dh = hd - ht   # lech: tâm quạt theo NGỰC thân mocap (tâm cố định ⇒ tay với hụt 131 mm)
        ngang = math.sqrt(max(1e-6, qd["dai"] ** 2 - dh * dh)); z = (d * ngang + V((0, 0, dh))).normalized()
        x = (tg - z * tg.dot(z)).normalized()
        dao_cu.matrix_world = M4.Translation(g) @ mathutils.Matrix((x, z.cross(x), z)).transposed().to_4x4()
        dao_cu.keyframe_insert("location", frame=f); dao_cu.keyframe_insert("rotation_quaternion", frame=f)


def do_quat(dao_cu, qd, N, cua_so, dau_local=(0.12, 0, 0.67)):
    """cửa cánh quạt: trong cửa sổ chém — lệch khỏi mặt phẳng (mm), biến thiên bán kính (%), θ tăng đơn điệu, lưỡi đi trước (cos ≥ 0.8)."""
    sc = bpy.context.scene; tam = V(qd["tam"]); P = []; X = []
    for f in range(cua_so[0], cua_so[1] + 1):
        sc.frame_set(f); bpy.context.view_layer.update(); M = dao_cu.matrix_world
        P.append(M @ V(dau_local)); X.append((M.to_3x3() @ V((1, 0, 0))).normalized())
    c = sum(P, V()) / len(P); import numpy as np
    A = np.array([list(p - c) for p in P]); n = V(np.linalg.svd(A)[2][2]); lech = max(abs((p - c).dot(n)) for p in P)
    # độ tròn quanh TÂM CUNG KHỚP (Kasa) trong mặt phẳng — tâm cố định sai khi thân mocap dời (báo 29 % cho cung tròn, 22/10)
    e1 = n.orthogonal().normalized(); e2 = n.cross(e1); Q2 = [((p - c).dot(e1), (p - c).dot(e2)) for p in P]
    A2 = np.array([[2 * x, 2 * y, 1] for x, y in Q2]); b2 = np.array([x * x + y * y for x, y in Q2]); cx, cy, _ = np.linalg.lstsq(A2, b2, rcond=None)[0]
    r = [math.hypot(x - cx, y - cy) for x, y in Q2]; bt = (max(r) - min(r)) / (sum(r) / len(r))
    th = [math.degrees(math.atan2(p.x - tam.x, -(p.y - tam.y))) for p in P]; don_dieu = all(b >= a - 1 for a, b in zip(th, th[1:]))
    dan = min(((P[i + 1] - P[i - 1]).normalized().dot(X[i])) for i in range(1, len(P) - 1) if (P[i + 1] - P[i - 1]).length > 1e-4)
    return dict(quat_lech_mat_mm=round(lech * 1000, 1), quat_ban_kinh_pct=round(bt * 100, 1), quat_don_dieu=don_dieu,
                quat_quet_deg=round(th[-1] - th[0], 1), luoi_di_truoc_cos=round(dan, 2))


def riu_xuyen_than(rig, than, dao_cu, N):
    """⑮ cán + đầu rìu lún vào THÂN (bỏ bàn tay, cẳng tay) — mm lớn nhất (Codex: «shaft outside the torso»)."""
    from mathutils.bvhtree import BVHTree
    sc = bpy.context.scene; ten = {g.index: g.name for g in than.vertex_groups}; sau = 0.0; o = None
    bo = {i for i, pl in enumerate(than.data.polygons) if sum((ten[max(than.data.vertices[v].groups, key=lambda x: x.weight).group] if than.data.vertices[v].groups else "") in ("hand_R", "hand_L", "forearm_R", "forearm_L") for v in pl.vertices) * 2 > len(pl.vertices)}
    for f in range(N + 1):
        sc.frame_set(f); dg = bpy.context.evaluated_depsgraph_get(); me = than.evaluated_get(dg).to_mesh()
        bvh = BVHTree.FromPolygons([than.matrix_world @ v.co for v in me.vertices], [list(pl.vertices) for i, pl in enumerate(me.polygons) if i not in bo]); than.evaluated_get(dg).to_mesh_clear()
        M = dao_cu.matrix_world
        for zz in [x / 20 for x in range(-6, 15)]:
            q = M @ V((0, 0, zz)); loc, _, _, d = bvh.find_nearest(q)
            if loc is not None and d < 0.2 and trong_bvh(bvh, q) and d > sau: sau = d; o = f
    return round(sau * 1000, 1), o


def do_nam_can(rig, SK, dao_cu, tay, N):
    """sai số nắm: vị trí socket cam_* tới điểm trên cán (mm) và góc trục nắm–trục cán (độ), lớn nhất theo khung."""
    sc = bpy.context.scene; loi, goc = 0.0, 0.0; o_dau = None
    for f in range(N + 1):
        sc.frame_set(f); bpy.context.view_layer.update(); M = dao_cu.matrix_world; z = (M.to_3x3() @ V((0, 0, 1))).normalized()
        for ben, zc in tay:
            hb = rig.data.bones[f"hand_{ben}"]; Mh = rig.matrix_world @ rig.pose.bones[f"hand_{ben}"].matrix @ hb.matrix_local.inverted()
            sp = Mh @ V(SK[f"cam_{ben}"]["vi_tri"]); sa = (Mh.to_3x3() @ V(SK[f"cam_{ben}"]["len"])).normalized()
            e = (sp - M @ V((0, 0, z_nam(zc, f)))).length
            if e > loi: loi = e; o_dau = (f, ben)
            goc = max(goc, math.degrees(sa.angle(z)))
    return dict(nam_lech_mm=round(loi * 1000, 1), nam_goc_deg=round(goc, 1), nam_lech_o=o_dau if loi else None)


def khoang(N):
    """khoảng khung GIAO: 1 chu kỳ đã cắt (CHU_KY) hoặc cả clip — cửa đo không được quét phần thừa của đoạn Kimodo (từng báo trượt 121 mm, khuỷu 16°)."""
    sc = bpy.context.scene
    return (sc.frame_start, sc.frame_end) if os.environ.get("CHU_KY") else (0, N)


def lat_khuyu(rig, ben, N):
    """đo khuỷu lật: góc giữa hướng khuỷu (so với trung điểm vai–cổ tay) của các khung liền nhau; trả (bước lớn nhất °, tổng °)."""
    sc = bpy.context.scene; W = rig.matrix_world; tr = None; mx = 0.0; tong = 0.0
    for f in range(khoang(N)[0], khoang(N)[1] + 1):
        sc.frame_set(f); bpy.context.view_layer.update(); P = rig.pose.bones
        sh = W @ P[f"upperarm_{ben}"].head; el = W @ P[f"forearm_{ben}"].head; wr = W @ P[f"forearm_{ben}"].tail
        a = (wr - sh).normalized(); d = (el - sh) - a * (el - sh).dot(a)
        if d.length < 1e-4: continue
        d.normalize()
        if tr is not None: g = math.degrees(d.angle(tr)); mx = max(mx, g); tong += g
        tr = d
    return round(mx, 1), round(tong, 1)


def tay_xuyen_go(rig, than, go, N, ben="R", r=0.09):
    """⑤b đỉnh lưới BÀN TAY + CẲNG TAY (xương trội) lún vào khối trụ gỗ (mm) — vùng tiếp xúc tay bị loại khỏi cửa ⑤ nên phải đo riêng."""
    sc = bpy.context.scene; ten = {g.index: g.name for g in than.vertex_groups}
    chon = [v.index for v in than.data.vertices if v.groups and ten[max(v.groups, key=lambda x: x.weight).group] in (f"hand_{ben}", f"forearm_{ben}")]
    sau = 0.0
    for f in range(khoang(N)[0], khoang(N)[1] + 1):
        sc.frame_set(f); dg = bpy.context.evaluated_depsgraph_get(); me = than.evaluated_get(dg).to_mesh()
        Mi = go.matrix_world.inverted(); rr = r * go.scale.x
        for i in chon:
            q = Mi @ (than.matrix_world @ me.vertices[i].co)
            if abs(q.z) < 0.6 / max(go.scale.z, 1e-6):
                d = math.hypot(q.x * go.scale.x, q.y * go.scale.y)
                if d < rr: sau = max(sau, rr - d)
        than.evaluated_get(dg).to_mesh_clear()
    return round(sau * 1000, 1)


# ------------------------------------------------------------------ CLIP từ JSON (bản A)
def noi_suy(keys, f, vong, N):
    """khoá {frame: giá trị|dict} → giá trị tại f; Catmull–Rom tuần hoàn khi vòng lặp (tiếp tuyến khớp ở mối nối)."""
    ks = sorted((float(k), v) for k, v in keys.items())
    if len(ks) == 1: return ks[0][1]
    fr = [k for k, _ in ks]; vs = [v for _, v in ks]
    def gt(i):
        if vong:
            n = len(ks) - (1 if fr[-1] == N else 0); j = i % n; d = (i // n) * N
            return fr[j] + d, vs[j]
        i = max(0, min(len(ks) - 1, i)); return fr[i], vs[i]
    if vong: f = f % N
    i = max(0, max(j for j in range(len(fr)) if fr[j] <= f) if f >= fr[0] else 0)
    if not vong and f >= fr[-1]: return vs[-1]
    (f0, p0), (f1, p1) = gt(i), gt(i + 1); (_, pm), (_, p2) = gt(i - 1), gt(i + 2)
    t = 0 if f1 == f0 else (f - f0) / (f1 - f0)
    def cr(a, b, c, d):
        return 0.5 * ((2 * b) + (-a + c) * t + (2 * a - 5 * b + 4 * c - d) * t * t + (-a + 3 * b - 3 * c + d) * t ** 3)
    if isinstance(p0, dict):
        ks_ = set(p0) | set(p1) | set(pm) | set(p2)
        return {k: cr(pm.get(k, 0), p0.get(k, 0), p1.get(k, 0), p2.get(k, 0)) for k in ks_}
    return cr(pm, p0, p1, p2)


def chan_dat(rig, K, clip, f, s):
    """mục tiêu IK bàn chân (thế giới) theo lịch tiếp đất: chạm = đứng yên; nhón gót = xoay quanh mũi; bay = cung có độ nhấc."""
    g = clip["gait"]; N = clip["end_frame"]; v = clip["root"].get("speed_mps", 0.0) * s; L = v * N / FPS   # quãng 1 chu kỳ
    out = {}
    for ben in "LR":
        c = g["contacts"][ben]; on, off = c["on"], c["off"]; heel = c.get("heel_rise", off)
        rest = K[f"co_chan_{ben}"].copy(); rest.x += math.copysign(g.get("width_extra_m", 0.0), rest.x)
        if L == 0:
            out[ben] = (rest + V(g.get("offset", {}).get(ben, (0, 0, 0))), 0.0); continue
        def y_dat(k):   # chỗ đặt chân lần k (thế giới): chân chạm tại khung on + k·N, gốc lúc đó ở −v·t
            return -(L * (on + k * N) / N) - L / 4 + g.get("lead_m", 0.0) * s   # chạm gót TRƯỚC hông nửa bước (bản đầu đặt ngay dưới hông ⇒ chân sau vươn 130 %)
        ff = f
        # pha hiện tại so với lần chạm gần nhất
        k = math.floor((ff - on) / N); t_in = ff - (on + k * N); stance = (off - on) % N or N
        if t_in < stance:
            y = y_dat(k); z = 0.0; pitch = 0.0
            if t_in >= (heel - on) % N:   # nhón gót: xoay quanh mũi, tới góc toe-off
                u = (t_in - (heel - on) % N) / max(1e-6, stance - (heel - on) % N)
                pitch = g.get("toe_off_deg", 25) * u
            out[ben] = (V((rest.x, rest.y + y, rest.z + z)), pitch)
        else:
            u = (t_in - stance) / (N - stance); sm = 0.5 - 0.5 * math.cos(math.pi * u)
            y = y_dat(k) + (y_dat(k + 1) - y_dat(k)) * sm; z = g["swing_h_m"] * s * math.sin(math.pi * min(1, u * 1.15))
            pitch = g.get("toe_off_deg", 25) * max(0.0, 1 - u * 2.5) - 8 * math.sin(math.pi * u)
            out[ben] = (V((rest.x, rest.y + y, rest.z + z)), pitch)
    return out


def dat_ik(rig, ben, p, pitch_deg, f, mui):
    """đặt xương ik_<ben> tại cổ chân p (thế giới), gập quanh mũi chân khi pitch>0 (gót nhấc, mũi giữ nguyên)."""
    b = rig.data.bones[f"ik_{ben}"]; pb = rig.pose.bones[f"ik_{ben}"]
    q = Q(V((1, 0, 0)), math.radians(pitch_deg))     # quanh trục X thế giới: dương = gót lên
    if pitch_deg > 0:   # giữ mũi: cổ_chân = mũi − q·(mũi−cổ_chân)
        toe = p + (mui - b.head_local); p = toe - q @ (mui - b.head_local)
    Rl = b.matrix_local.to_3x3()
    pb.location = Rl.inverted() @ (p - b.head_local); pb.keyframe_insert("location", frame=f)
    pb.rotation_quaternion = (Rl.inverted() @ q.to_matrix() @ Rl).to_quaternion(); pb.keyframe_insert("rotation_quaternion", frame=f)


def dung_clip(rig, K, clip, s=1.0):
    N = clip["end_frame"]; vong = clip["loop"]; v = clip["root"].get("speed_mps", 0.0) * s
    for f in range(0, N + 1):
        pb = rig.pose.bones["goc"]; pb.location = (0, -v * f / FPS, 0); pb.keyframe_insert("location", frame=f)   # goc: trục Y local = +Y thế giới
        p = noi_suy(clip["pelvis"], f, vong, N) if clip.get("pelvis") else {}
        h = rig.pose.bones["hips"]
        h.location = rig.data.bones["hips"].matrix_local.to_3x3().inverted() @ V((p.get("x_mm", 0) / 1000 * s, p.get("y_mm", 0) / 1000 * s, (p.get("z_mm", 0) + clip.get("hips_drop_mm", 20) * -1) / 1000 * s))
        h.keyframe_insert("location", frame=f)
        h.rotation_quaternion = q_giai_phau(rig, "hips", p); h.keyframe_insert("rotation_quaternion", frame=f)
        for xg, keys in clip.get("joints", {}).items():
            k = noi_suy(keys, f, vong, N); pbx = rig.pose.bones[xg]
            pbx.rotation_quaternion = q_giai_phau(rig, xg, k); pbx.keyframe_insert("rotation_quaternion", frame=f)
        for ben, (pos, pitch) in chan_dat(rig, K, clip, f, s).items():
            dat_ik(rig, ben, pos, pitch, f, K[f"mui_chan_{ben}"])


# ------------------------------------------------------------------ RETARGET BVH (bản B)
SOMA = {"hips": "Hips", "spine": "Spine2", "chest": "Chest", "neck": "Neck2", "head": "Head",
        "clavicle_L": "LeftShoulder", "upperarm_L": "LeftArm", "forearm_L": "LeftForeArm", "hand_L": "LeftHand",
        "clavicle_R": "RightShoulder", "upperarm_R": "RightArm", "forearm_R": "RightForeArm", "hand_R": "RightHand",
        "thigh_L": "LeftLeg", "shin_L": "LeftShin", "foot_L": "LeftFoot", "thigh_R": "RightLeg", "shin_R": "RightShin", "foot_R": "RightFoot"}


def retarget(rig, K, f_bvh, N_toi=None):
    """BVH Kimodo (cm, Y-lên) → rig: chuyển hướng toàn cục G_t = G_s·G_s0⁻¹·(căn hướng nghỉ)·G_t0; gốc tỉ lệ chiều dài chân;
    rồi khoá chân: chân thấp & chậm ⇒ neo vị trí trung vị (spec vòng 2 §4)."""
    t = set(bpy.data.objects); NGUON_POSE.clear(); NGUON_VT.clear()
    bpy.ops.import_anim.bvh(filepath=f_bvh, global_scale=0.01, axis_forward="-Z", axis_up="Y", update_scene_fps=False, update_scene_duration=False)   # BVH Y-lên ⇒ Blender Z-lên
    src = [o for o in bpy.data.objects if o not in t and o.type == "ARMATURE"][0]
    a = src.animation_data.action; f0, f1 = (int(x) for x in a.frame_range)
    sfps = round(1 / float(open(f_bvh).read().split("Frame Time:")[1].split()[0]))
    sc = bpy.context.scene
    # hướng: Kimodo nhìn +Z(BVH) → sau import axis_forward=Y nhìn ±Y; đo hướng mặt bằng vector hông trái-phải
    sc.frame_set(f0); bpy.context.view_layer.update()
    def gpos(o, n, dau=True): pb = o.pose.bones[n]; return o.matrix_world @ (pb.head if dau else pb.tail)
    lr = gpos(src, "LeftLeg") - gpos(src, "RightLeg"); fwd = V((0, 0, 1)).cross(lr).normalized()   # trái × lên = trước? (trái=+X, trước=−Y ⇒ lên×trái)
    fwd = lr.cross(V((0, 0, 1))).normalized()   # với trái=+X: (+X)×(+Z) = −Y = trước
    goc_xoay = math.atan2(fwd.x, -fwd.y)       # lệch so với −Y
    sc.frame_set(f1); bpy.context.view_layer.update(); di = gpos(src, "Hips") - (sc.frame_set(f0) or bpy.context.view_layer.update() or gpos(src, "Hips"))
    di.z = 0
    if di.length > 0.5 and not os.environ.get("CU_HUONG"):   # Boss 22/10: chạy chếch 16° ⇒ bàn chân (khoá 0°) lệch hướng chạy. Xoay theo HƯỚNG ĐI THẬT.
        goc_xoay = math.atan2(di.x, -di.y)
    sc.frame_set(f0); bpy.context.view_layer.update()
    C = M4.Rotation(-goc_xoay, 4, "Z")
    # tỉ lệ chân
    Ls = (gpos(src, "LeftLeg") - gpos(src, "LeftShin")).length + (gpos(src, "LeftShin") - gpos(src, "LeftFoot")).length
    Lt = (K["hong_L"] - K["goi_L"]).length + (K["goi_L"] - K["co_chan_L"]).length; k = Lt / Ls
    # nghỉ: hướng nguồn ở rest (T-pose chuẩn) và hướng đích ở rest; căn hướng xương đích theo hướng xương nguồn
    Gs0 = {n: (C @ src.matrix_world @ src.data.bones[SOMA[n]].matrix_local).to_quaternion() for n in SOMA}
    Gt0 = {n: rig.data.bones[n].matrix_local.to_quaternion() for n in SOMA}   # hướng nghỉ đích (armature)
    can = {}
    for n in SOMA:
        bs = src.data.bones[SOMA[n]]; ds = (C.to_3x3() @ src.matrix_world.to_3x3() @ (bs.tail_local - bs.head_local)).normalized()
        bt = rig.data.bones[n]; dt = (bt.tail_local - bt.head_local).normalized()
        can[n] = ds.rotation_difference(dt)    # quay hướng nguồn → hướng đích (xấp xỉ: tối thiểu, không xoắn)
    for pb_ in rig.pose.bones:
        for c in pb_.constraints: c.mute = True          # chép FK trước; IK bật lại sau khi khoá chân
    KHUNG = {"hips": ("Hips", "Spine1", "LeftLeg", "RightLeg"), "spine": ("Spine2", "Chest", "LeftArm", "RightArm"), "chest": ("Chest", "Neck1", "LeftArm", "RightArm"),
             "neck": ("Neck1", "Head", "LeftArm", "RightArm"), "head": ("Head", "HeadEnd", "LeftEye", "RightEye")}
    DOAN = {f"{t}_{b}": (f"{s1}", f"{s2}") for b, B in (("L", "Left"), ("R", "Right")) for t, s1, s2 in
            (("clavicle", B + "Shoulder", B + "Arm"), ("upperarm", B + "Arm", B + "ForeArm"), ("forearm", B + "ForeArm", B + "Hand"),
             ("hand", B + "Hand", B + "HandMiddle1"), ("thigh", B + "Leg", B + "Shin"), ("shin", B + "Shin", B + "Foot"), ("foot", B + "Foot", B + "ToeBase"))}
    for n_, (a_, b_) in list(DOAN.items()):
        if b_ not in src.pose.bones: DOAN[n_] = (a_, a_ + "End") if a_ + "End" in src.pose.bones else (a_, a_)
    def khung(o, q, Cm, rest=False):
        P_ = (lambda n: Cm @ o.matrix_world @ (o.data.bones[n].head_local)) if rest else (lambda n: Cm @ o.matrix_world @ o.pose.bones[n].head)
        up = (P_(q[1]) - P_(q[0])).normalized(); lat = (P_(q[2]) - P_(q[3])); lat = (lat - up * lat.dot(up)).normalized()
        return mathutils.Matrix((lat, up.cross(lat), up)).transposed()
    Fs0 = {n: khung(src, q, mathutils.Matrix.Identity(4), rest=True) for n, q in KHUNG.items()}   # nghỉ KHÔNG nhân C (nhân C ⇒ liên hợp, thân vẫn quay 15° lệch hướng chạy)
    def khung_dich(n):
        bt = rig.data.bones; m = {"hips": ("chau", "bung", "hong_L", "hong_R"), "spine": ("bung", "nguc", "vai_L", "vai_R"), "chest": ("nguc", "co", "vai_L", "vai_R"),
                                 "neck": ("co", "dau", "vai_L", "vai_R"), "head": ("dau", "dinh_dau", "vai_L", "vai_R")}[n]
        up = (K[m[1]] - K[m[0]]).normalized(); lat = K[m[2]] - K[m[3]]; lat = (lat - up * lat.dot(up)).normalized()
        return mathutils.Matrix((lat, up.cross(lat), up)).transposed()
    # hướng nghỉ đích tính theo khung đích: G_t(t) = R_w · G_t0 với R_w = F_s(t)·F_s0⁻¹ (cùng hệ khung trái-phải/dọc)
    for n in KHUNG:
        Fs0[n] = Fs0[n] @ khung_dich(n).inverted() @ khung_dich(n)
    sc.frame_set(f0); bpy.context.view_layer.update()
    src_hip_rest = (C @ src.matrix_world @ src.data.bones["Hips"].head_local).z
    bu_hong = rig.data.bones["hips"].head_local.z - src_hip_rest * k
    hip0 = (C @ gpos(src, "Hips")); thu_tu = [n for n, *_ in xuong_tu_khop(dict(K)) if n in SOMA]
    tiep_chan = {}; huong_chan_goc = {}
    N = int((f1 - f0) * FPS / sfps); vet = {"L": [], "R": []}; huong_chan = {"L": [], "R": []}; cang_nguon = {"L": [], "R": []}; dui_nguon = {"L": [], "R": []}; hong_ngang = []
    for f in range(0, N + 1):
        fs = f0 + f * sfps / FPS; sc.frame_set(int(fs), subframe=fs - int(fs)); bpy.context.view_layer.update()
        hp = C @ gpos(src, "Hips"); dlt = (hp - hip0) * k
        g = rig.pose.bones["goc"]; g.location = (dlt.x, dlt.y, 0); g.keyframe_insert("location", frame=f)   # dời ngang = root motion
        for n in thu_tu:
            pb = rig.pose.bones[n]; cur = pb.matrix.copy(); h = cur.translation.copy()
            if n in KHUNG:   # thân/đầu: khung 2 vector (dọc + trái-phải) — không phụ thuộc quy ước trục local của 2 rig
                Fs = khung(src, KHUNG[n], C); Rw = Fs @ Fs0[n].inverted()
                Gt = (Rw @ Gt0[n].to_matrix()).to_4x4()
            else:            # chi: xoay hướng đoạn đích (đã theo cha) trùng hướng đoạn nguồn
                a_, b_ = DOAN[n]; ds = (C.to_3x3() @ (gpos(src, a_) - gpos(src, b_, True) if False else (src.matrix_world @ src.pose.bones[b_].head - src.matrix_world @ src.pose.bones[a_].head))).normalized()
                ds = (C.to_3x3() @ (src.matrix_world @ src.pose.bones[b_].head - src.matrix_world @ src.pose.bones[a_].head)).normalized()
                dc = (rig.matrix_world.to_3x3() @ (pb.tail - pb.head)).normalized()
                Gt = (dc.rotation_difference(ds).to_matrix() @ cur.to_3x3()).to_4x4()
            Gt.translation = h
            if n == "hips": Gt.translation = V((rig.data.bones["hips"].head_local.x + dlt.x, rig.data.bones["hips"].head_local.y + dlt.y, hp.z * k + bu_hong))
            pb.matrix = Gt
            if n != "hips": pb.location = (0, 0, 0)
            bpy.context.view_layer.update()
            pb.keyframe_insert("rotation_quaternion", frame=f)
            if n == "hips": pb.keyframe_insert("location", frame=f)
        ghi_nguon_pose(rig, f)   # P1-k: mốc nguồn Kimodo (sau chép góc, trước khoá chân)
        for b in "LR":   # vị trí cổ chân FK (đùi/cẳng nguồn) — trước khoá chân; + hướng bàn chân nguồn
            vet[b].append((rig.matrix_world @ rig.pose.bones[f"shin_{b}"].tail).copy())
            B = "Left" if b == "L" else "Right"
            huong_chan[b].append((C.to_3x3() @ (src.matrix_world @ src.pose.bones[B + "ToeBase"].head - src.matrix_world @ src.pose.bones[B + "Foot"].head)).normalized())
            cang_nguon[b].append((C.to_3x3() @ (src.matrix_world @ src.pose.bones[B + "Foot"].head - src.matrix_world @ src.pose.bones[B + "Shin"].head)).normalized())
            dui_nguon[b].append((C.to_3x3() @ (src.matrix_world @ src.pose.bones[B + "Shin"].head - src.matrix_world @ src.pose.bones[B + "Leg"].head)).normalized())
            hong_ngang.append((C.to_3x3() @ (src.matrix_world @ src.pose.bones["LeftLeg"].head - src.matrix_world @ src.pose.bones["RightLeg"].head)).normalized())
    for pb_ in rig.pose.bones:
        for c in pb_.constraints: c.mute = False
    # khoá chân: thấp (≤ 2 cm trên mức nghỉ) & chậm (< 0,15 m/s) ≥ 2 khung ⇒ neo trung vị
    for b in "LR":
        z0 = K[f"co_chan_{b}"].z; P = vet[b]; tiep = []
        for i in range(len(P)):
            sp = (P[min(i + 1, len(P) - 1)] - P[max(i - 1, 0)]).length * FPS / 2
            tiep.append(P[i].z - z0 <= 0.02 and sp < 0.15)
        i = 0
        while i < len(P):
            if tiep[i]:
                j = i
                while j + 1 < len(P) and tiep[j + 1]: j += 1
                if j - i + 1 >= 2:
                    xs = sorted(p.x for p in P[i:j + 1]); ys = sorted(p.y for p in P[i:j + 1]); m = (j - i) // 2
                    for q in range(i, j + 1): P[q] = V((xs[m], ys[m], z0))
                i = j + 1
            else: i += 1
        huong_chan_goc[b] = [x.copy() for x in huong_chan[b]]
        D = huong_chan[b]; tiep2 = tiep
        # trong đoạn chạm đất: một hướng cố định (trung bình đoạn) — bàn chân không xoay trên mặt đất
        i = 0
        while i < len(D):
            if tiep2[i]:
                j = i
                while j + 1 < len(D) and tiep2[j + 1]: j += 1
                tb = sum(D[i:j + 1], V()).normalized()
                for q in range(i, j + 1): D[q] = tb
                i = j + 1
            else: i += 1
        tiep_chan[b] = list(tiep2)
        KEP = float(os.environ.get("KEP_MUI_CHAN", "8"))   # mũi chân mở tối đa ±8° quanh hướng đi (Kimodo mở tới 19°: «chỉa qua 1 bên»)
        for q_ in range(len(D)):
            d = D[q_]; ng = math.hypot(d.x, d.y)
            if ng > 1e-3 and (tiep2[q_] or os.environ.get("KEP_CA_VUNG")):   # CHỈ kẹp khi CHẠM ĐẤT (kẹp cả pha vung ⇒ gãy cổ chân, Boss 22/10 khoanh đỏ)
                y_ = max(-KEP, min(KEP, math.degrees(math.atan2(d.x, -d.y)))); D[q_] = V((ng * math.sin(math.radians(y_)), -ng * math.cos(math.radians(y_)), d.z)).normalized()
        bn = rig.data.bones[f"ik_{b}"]; d0 = (bn.tail_local - bn.head_local).normalized(); Rl = bn.matrix_local.to_3x3()
        for f, p in enumerate(P):
            dat_ik(rig, b, p, 0.0, f, K[f"mui_chan_{b}"])
            if os.environ.get("CU_HUONG"): continue   # thử ngược: bàn chân khoá 0° như bản cũ
            q = d0.rotation_difference(D[f]); pb = rig.pose.bones[f"ik_{b}"]
            pb.rotation_quaternion = (Rl.inverted() @ q.to_matrix() @ Rl).to_quaternion(); pb.keyframe_insert("rotation_quaternion", frame=f)
    for b in "LR":   # pha vung: hướng bàn chân = hướng cẳng ĐÍCH xoay đúng góc cổ chân NGUỒN (giữ dáng cổ chân, không ép theo thế giới)
        bn = rig.data.bones[f"ik_{b}"]; d0 = (bn.tail_local - bn.head_local).normalized(); Rl = bn.matrix_local.to_3x3()
        for f in range(N + 1):
            if tiep_chan[b][f] or os.environ.get("CU_HUONG") or os.environ.get("KEP_CA_VUNG"): continue
            sc.frame_set(f); bpy.context.view_layer.update(); W = rig.matrix_world; Pb = rig.pose.bones
            cang_t = ((W @ Pb[f"shin_{b}"].tail) - (W @ Pb[f"shin_{b}"].head)).normalized()
            dui_t = ((W @ Pb[f"thigh_{b}"].tail) - (W @ Pb[f"thigh_{b}"].head)).normalized()
            lr_t = (W @ Pb["thigh_L"].head) - (W @ Pb["thigh_R"].head)
            def khung_chan(dui, cang, lr):   # e1 dọc cẳng, e2 trục bản lề gối (dùi×cẳng; gối thẳng ⇒ trục hông trái-phải), e3 = e1×e2
                e2 = dui.cross(cang)
                if e2.length < 0.15: e2 = lr - cang * lr.dot(cang)
                e2.normalize(); e3 = cang.cross(e2).normalized(); return cang, e2, e3
            s1, s2, s3 = khung_chan(dui_nguon[b][f], cang_nguon[b][f], hong_ngang[f]); t1, t2, t3 = khung_chan(dui_t, cang_t, lr_t)
            fs = huong_chan_goc[b][f]
            if s2.dot(t2) < 0: t2, t3 = -t2, -t3   # cùng chiều bản lề
            D = (t1 * fs.dot(s1) + t2 * fs.dot(s2) + t3 * fs.dot(s3)).normalized()   # bàn chân trong KHUNG CHÂN nguồn → khung chân đích
            if (W @ Pb[f"foot_{b}"].head).z - K[f"co_chan_{b}"].z <= 0.02:   # sát đất (sắp chạm / vừa nhấc): vẫn kẹp hướng quanh hướng đi
                ng = math.hypot(D.x, D.y); KEP_ = float(os.environ.get("KEP_MUI_CHAN", "8"))
                if ng > 1e-3:
                    y_ = max(-KEP_, min(KEP_, math.degrees(math.atan2(D.x, -D.y)))); D = V((ng * math.sin(math.radians(y_)), -ng * math.cos(math.radians(y_)), D.z)).normalized()
            q = d0.rotation_difference(D); pb = Pb[f"ik_{b}"]
            pb.rotation_quaternion = (Rl.inverted() @ q.to_matrix() @ Rl).to_quaternion(); pb.keyframe_insert("rotation_quaternion", frame=f)
    bpy.data.objects.remove(src)
    return N


def guong_tay(rig, N, dich="R"):
    """tay `dich` = ảnh gương (qua mặt X=0, tính theo khung của hông) của tay kia, lệch NỬA chu kỳ bước.
    Chu kỳ = trung vị khoảng cách giữa các lần chạm đất của chân trái (cực tiểu độ cao cổ chân)."""
    sc = bpy.context.scene; nguon = "L" if dich == "R" else "R"; W = rig.matrix_world
    z = []
    for f in range(N + 1):
        sc.frame_set(f); bpy.context.view_layer.update(); z.append((W @ rig.pose.bones["foot_L"].head).z)
    zmin = min(z); cham = [i for i in range(1, N + 1) if z[i] - zmin < 0.01 and z[i - 1] - zmin >= 0.01]   # khung TIẾP ĐẤT (cực tiểu cục bộ cho 21 thay vì ~28)
    ds = sorted(b - a for a, b in zip(cham, cham[1:]) if b - a > 12); T = ds[len(ds) // 2] if ds else N; nua = T // 2
    S = mathutils.Matrix.Diagonal((-1, 1, 1, 1))
    chuoi = ["clavicle", "upperarm", "forearm", "hand"]; luu = {}
    for f in range(N + 1):   # đọc tay nguồn ở khung f+nửa chu kỳ, trong khung toạ độ của hông (bỏ xoay/dời của thân)
        sc.frame_set(min(N, f + nua) if f + nua <= N else f - nua); bpy.context.view_layer.update()
        H_ = rig.pose.bones["hips"].matrix
        luu[f] = {c: H_.inverted() @ rig.pose.bones[f"{c}_{nguon}"].matrix for c in chuoi}
    for f in range(N + 1):
        sc.frame_set(f); bpy.context.view_layer.update(); H_ = rig.pose.bones["hips"].matrix
        for c in chuoi:
            pb = rig.pose.bones[f"{c}_{dich}"]; m = H_ @ (S @ luu[f][c] @ S)
            # S·M·S giữ det = +1 và cho đúng trục tay đối diện (X_R = −S·X_L); lật thêm cột X ⇒ xoắn vai (bản đầu, 22/10)
            m4 = m.to_3x3().to_4x4(); m4.translation = pb.matrix.translation
            pb.matrix = m4; pb.location = (0, 0, 0); bpy.context.view_layer.update(); pb.keyframe_insert("rotation_quaternion", frame=f)
    return dict(chu_ky=T, lan_cham_L=cham[:6])


def tim_chu_ky(rig, N, tmin, tmax):
    """dò cặp khung [a,b] (b−a trong [tmin,tmax]) có tư thế (so với gốc) gần nhau nhất — dùng cho clip Kimodo không có mốc chu kỳ."""
    sc = bpy.context.scene; P = {}
    for f in range(N + 1):
        sc.frame_set(f); bpy.context.view_layer.update(); W = rig.matrix_world; r = W @ rig.pose.bones["goc"].head
        P[f] = [(W @ p.tail) - r for p in rig.pose.bones if p.bone.use_deform]
    best = None
    for a in range(max(2, N // 6), N - tmin):
        for b in range(a + tmin, min(N - 1, a + tmax) + 1):
            e = max((x - y).length for x, y in zip(P[a], P[b]))
            if best is None or e < best[0]: best = (e, a, b)
    return best


def cat_chu_ky(rig, a, b, k=4):
    """cắt 1 chu kỳ [a,b] của clip sinh ra (Kimodo không lặp vòng) và TRỘN mối nối: k khung cuối trộn dần (smoothstep) về tư thế khung f−T
    (liên tục với khung a), vị trí gốc/IK cộng quãng dời 1 chu kỳ ⇒ khung b ≡ khung a + dời (ChatGPT vòng 3 bước 6)."""
    sc = bpy.context.scene; T = b - a
    def doc(f):
        sc.frame_set(f); bpy.context.view_layer.update()
        return {p.name: (p.rotation_quaternion.copy(), p.location.copy()) for p in rig.pose.bones}
    sc.frame_set(a); bpy.context.view_layer.update(); g0 = rig.pose.bones["goc"].location.copy()
    sc.frame_set(b); bpy.context.view_layer.update(); g1 = rig.pose.bones["goc"].location.copy(); dl = g1 - g0
    W = {}
    for f in range(b - k, b + 1):
        W[f] = (doc(f), doc(f - T))
    for f, (cur, prev) in W.items():
        u = (f - (b - k)) / k; w = u * u * (3 - 2 * u)
        for n, (q, l) in cur.items():
            pb = rig.pose.bones[n]; q2, l2 = prev[n]
            if q.dot(q2) < 0: q2 = -q2
            pb.rotation_quaternion = q.slerp(q2, w)
            if n == "goc": l2 = l2 + dl
            elif n.startswith("ik_"):
                Rl = rig.data.bones[n].matrix_local.to_3x3(); l2 = l2 + Rl.inverted() @ (rig.data.bones["goc"].matrix_local.to_3x3() @ dl)
            pb.location = l.lerp(l2, w)
            pb.keyframe_insert("rotation_quaternion", frame=f); pb.keyframe_insert("location", frame=f)
    sc.frame_start, sc.frame_end = a, b - 1
    return dict(chu_ky=[a, b], tron_khung=k, doi_goc_m=round(dl.length, 3))


def retarget_mp(rig, K, f_json, t0, t1, khoa=False):
    """MOCAP từ video (MediaPipe pose_world_landmarks, Boss 22/10 «lấy từ footage và motioncapture it») → rig settler.
    MP: x phải ảnh, y xuống, z xa camera, gốc giữa hông ⇒ Blender (x, z, −y). Làm mượt 5 khung, lấy mẫu lại 24 fps, quay cho mặt nhìn −Y.
    Chi: khớp hướng đoạn; thân/đầu: khung 2 vector (lên + trái-phải) so với khung NGHỈ của rig đích; cao hông theo tỉ lệ chân; chân đứng yên ⇒ khoá."""
    d = json.load(open(f_json)); Fr = [f for f in d["frames"] if f.get("w") and t0 <= f["t"] <= t1]
    def bl(p): return V((p[0], p[2], -p[1]))
    raw = [[bl(p) for p in f["w"]] for f in Fr]; T = [f["t"] for f in Fr]
    sm = []
    for i in range(len(raw)):   # trung bình trượt 5 khung (MP rung)
        w_ = raw[max(0, i - 2): i + 3]; sm.append([sum((r[j] for r in w_), V()) / len(w_) for j in range(33)])
    N = int(round((T[-1] - T[0]) * FPS)); P = []
    for f in range(N + 1):
        t = T[0] + f / FPS; i = max(0, min(len(T) - 2, max(k for k in range(len(T)) if T[k] <= t) if t >= T[0] else 0)); u = 0 if T[i + 1] == T[i] else (t - T[i]) / (T[i + 1] - T[i])
        P.append([sm[i][j].lerp(sm[i + 1][j], max(0, min(1, u))) for j in range(33)])
    up = V((0, 0, 1)); fw = V()
    for p in P: lr = p[23] - p[24]; lr.z = 0; fw += lr.cross(up)
    fw.z = 0; fw.normalize(); C = mathutils.Matrix.Rotation(-math.atan2(fw.x, -fw.y), 3, "Z")   # mặt nhìn −Y
    P = [[C @ q for q in p] for p in P]
    Ls = sum(((p[23] - p[25]).length + (p[25] - p[27]).length + (p[24] - p[26]).length + (p[26] - p[28]).length) / 2 for p in P) / len(P)
    Lt = (K["hong_L"] - K["goi_L"]).length + (K["goi_L"] - K["co_chan_L"]).length; k = Lt / Ls
    nen = min(min(p[27].z, p[28].z) for p in P)
    def khung(up_, lat):
        up_ = up_.normalized(); lat = (lat - up_ * lat.dot(up_)).normalized(); return mathutils.Matrix((lat, up_.cross(lat), up_)).transposed()
    mid = lambda a, b: (a + b) / 2
    def khung_nguon(p, n):
        if n == "hips": return khung(mid(p[11], p[12]) - mid(p[23], p[24]), p[23] - p[24])
        if n in ("spine", "chest"): return khung(mid(p[11], p[12]) - mid(p[23], p[24]), p[11] - p[12])
        if n == "neck": return khung(mid(p[7], p[8]) - mid(p[11], p[12]), p[11] - p[12])
        return khung(mid(p[7], p[8]) - mid(p[11], p[12]), p[7] - p[8])   # head
    def khung_dich(n):
        if n == "hips": return khung(mid(K["vai_L"], K["vai_R"]) - mid(K["hong_L"], K["hong_R"]), K["hong_L"] - K["hong_R"])
        if n in ("spine", "chest"): return khung(mid(K["vai_L"], K["vai_R"]) - mid(K["hong_L"], K["hong_R"]), K["vai_L"] - K["vai_R"])
        if n == "neck": return khung(K["dau"] - mid(K["vai_L"], K["vai_R"]), K["vai_L"] - K["vai_R"])
        return khung(K["dinh_dau"] - K["dau"], K["vai_L"] - K["vai_R"])
    F0 = {n: khung_dich(n) for n in ("hips", "spine", "chest", "neck", "head")}
    G0 = {n: rig.data.bones[n].matrix_local.to_3x3() for n in F0}
    DOAN = {f"{t}_{b}": (j1, j2) for b, o in (("L", 0), ("R", 1)) for t, j1, j2 in
            (("upperarm", 11 + o, 13 + o), ("forearm", 13 + o, 15 + o), ("thigh", 23 + o, 25 + o), ("shin", 25 + o, 27 + o), ("foot", 27 + o, 31 + o))}
    sc = bpy.context.scene; W = rig.matrix_world
    for pb_ in rig.pose.bones:
        for c in pb_.constraints: c.mute = True
    vet = {"L": [], "R": []}; hip0 = None
    global MP_TAY; MP_TAY = []   # cổ tay NGUỒN đã đổi sang không gian đích (hông đích + (nguồn − hông nguồn)·k) — để dựng quỹ đạo rìu
    for f, p in enumerate(P):
        sc.frame_set(f); bpy.context.view_layer.update()
        hc = mid(p[23], p[24]); hip0 = hip0 or hc.copy()
        hz_ = K["co_chan_L"].z + ((p[23].z + p[24].z) / 2 - nen) * k
        goc_d = V((mid(K["hong_L"], K["hong_R"]).x + (hc.x - hip0.x) * k, mid(K["hong_L"], K["hong_R"]).y + (hc.y - hip0.y) * k, hz_))
        MP_TAY.append((goc_d + (p[16] - hc) * k, goc_d + (p[15] - hc) * k))   # (R, L)
        for n in ("hips", "spine", "chest", "neck", "head"):
            pb = rig.pose.bones[n]; Fs = khung_nguon(p, n)
            if n == "spine": Fs = khung_nguon(p, "hips").to_quaternion().slerp(khung_nguon(p, "chest").to_quaternion(), 0.5).to_matrix()
            Rm = Fs @ F0[n].inverted() @ G0[n]; m = Rm.to_4x4(); m.translation = pb.matrix.translation
            if n == "hips":
                hz = K["co_chan_L"].z + ((p[23].z + p[24].z) / 2 - nen) * k + (K["chau"].z - K["hong_L"].z)
                m.translation = V((rig.data.bones["hips"].head_local.x + (hc.x - hip0.x) * k, rig.data.bones["hips"].head_local.y + (hc.y - hip0.y) * k, hz))
            pb.matrix = m
            if n != "hips": pb.location = (0, 0, 0)
            bpy.context.view_layer.update(); pb.keyframe_insert("rotation_quaternion", frame=f)
            if n == "hips": pb.keyframe_insert("location", frame=f)
        for n, (j1, j2) in DOAN.items():   # thứ tự cha→con giữ trong dict
            ngam(rig, n, p[j2] - p[j1]); rig.pose.bones[n].location = (0, 0, 0); bpy.context.view_layer.update()
            rig.pose.bones[n].keyframe_insert("rotation_quaternion", frame=f)
        for b, o in (("L", 0), ("R", 1)):   # bàn tay: cổ tay → giữa ngón trỏ & út
            ngam(rig, f"hand_{b}", mid(p[17 + o], p[19 + o]) - p[15 + o]); rig.pose.bones[f"hand_{b}"].keyframe_insert("rotation_quaternion", frame=f)
            vet[b].append((W @ rig.pose.bones[f"shin_{b}"].tail).copy())
    for pb_ in rig.pose.bones:
        for c in pb_.constraints: c.mute = False
    for b in "LR":   # chân: chuyển động ngang < 6 cm ⇒ KHOÁ cả đoạn ở vị trí trung vị (đứng chặt); không thì theo FK
        xs = sorted(v.x for v in vet[b]); ys = sorted(v.y for v in vet[b]); m_ = len(xs) // 2
        tb = V((xs[m_], ys[m_], K[f"co_chan_{b}"].z)); khoa_b = khoa or max((v - tb).xy.length for v in vet[b]) < 0.06   # clip đứng yên ⇒ luôn khoá (MP rung chân 4–13 cm ⇒ lơ lửng 40,6 mm)
        for f, v in enumerate(vet[b]): dat_ik(rig, b, tb if khoa_b else V((v.x, v.y, max(v.z, K[f"co_chan_{b}"].z))), 0.0, f, K[f"mui_chan_{b}"])
    # hông nguồn cao hơn tầm với của chân đích (dáng tấn rộng) ⇒ IK duỗi thẳng mà cổ chân vẫn LƠ LỬNG (đo 40,6 mm, 22/10):
    # hạ hông từng khung đúng bằng khoảng hở lớn nhất của cổ chân đứng so với đích IK, lặp 3 vòng
    pb = rig.pose.bones["hips"]
    for _ in range(3):
        for f in range(N + 1):
            sc.frame_set(f); bpy.context.view_layer.update()
            ho = max((W @ rig.pose.bones[f"shin_{b}"].tail).z - (W @ rig.pose.bones[f"ik_{b}"].head).z for b in "LR")
            if ho > 0.001:
                m = pb.matrix.copy(); m.translation.z -= ho; pb.matrix = m; bpy.context.view_layer.update(); pb.keyframe_insert("location", frame=f)
    return N


# ------------------------------------------------------------------ CỬA ĐO (10 cửa tối thiểu, đo trên xương)
def trong_bvh(bvh, q):
    """điểm q trong lưới kín? đếm giao 3 tia lệch hướng, bỏ phiếu đa số (pháp tuyến gần nhất báo nhầm 715 mm — 22/10)."""
    phieu = 0
    for d in (V((1, 0.0137, 0.0071)), V((-0.0113, 1, 0.0193)), V((0.0171, -0.0089, 1))):
        d.normalize(); o = q.copy(); n = 0
        for _ in range(64):
            loc, _, _, _ = bvh.ray_cast(o, d)
            if loc is None: break
            n += 1; o = loc + d * 1e-5
        phieu += n % 2
    return phieu >= 2


def ti_le_chan(K):
    """s = chiều dài chân settler / chân người 0,86 m — sải và tốc độ trong spec là cho người thật."""
    return ((K['hong_L'] - K['goi_L']).length + (K['goi_L'] - K['co_chan_L']).length) / 0.86


CHAN_RUNG_MAX_MM = 60.0   # mm/khung² — hiệu chuẩn 24/10: Kimodo walk 48,8 × 1,2 (bow 25,0 · idle 0); lao trước sửa 154,9
CHAN_RUNG_MAX_DEG = 16.0  # °/khung² — hiệu chuẩn 24/10: Kimodo walk 13,4 × 1,2 (bow 8,5 · idle 0); lao trước sửa 32,2
JITTER_SOLVE_FRACTION = 0.9   # P1-j: bộ giải (thư giãn đường vào/ra, kẹp gia tốc dốc) nhắm 90 % ngưỡng cửa rung — kết quả không nằm đúng mép (60,0 / 16,0 đo 24/10)
ANKLE_ANGLE_MAX_DEG = 150.0   # ⑬ biên trên (cẳng ↔ bàn chân, duỗi mũi); biên dưới = profile cham.co_chan_gap_min_deg. Hậu kỳ P1-j kẹp cả biên này (153,9° @L93 trước đó không ai kẹp)
CHAN_THAP_V_MAX = 4.5   # m/s — HIỆU CHUẨN 23/10 trên pose đã bake: idle 0.00 · Kimodo bow 0.38 · Kimodo walk (B/walk.bvh) 3.74 ⇒ 3.74 × 1.2; lao P1 8.56 · no-hysteresis 10.48 (phải rớt)


def cua(rig, K, N, clip, than=None, dao_cu=None, go=None):
    s = ti_le_chan(K)
    sc = bpy.context.scene; ups = 1; kq = {}   # khung nguyên = thứ game nhận (IK Blender ở subframe cho số rác: −175 mm ở khung 31,5)
    mui = {b: [] for b in "LR"}; got = {b: [] for b in "LR"}; goi = []; khuyu = []; tay_dau = []; root = []; hz = []
    def ang(a, b, c): return math.degrees((a - b).angle(c - b))
    for i in range(khoang(N)[0] * ups, khoang(N)[1] * ups + 1):
        f = i / ups; sc.frame_set(int(f), subframe=f - int(f)); bpy.context.view_layer.update(); W = rig.matrix_world
        for b in "LR":
            P = rig.pose.bones
            got[b].append(W @ P[f"foot_{b}"].head); mui[b].append(W @ P[f"foot_{b}"].tail)
            goi.append(180 - ang(W @ P[f"thigh_{b}"].head, W @ P[f"shin_{b}"].head, W @ P[f"shin_{b}"].tail))
            khuyu.append(180 - ang(W @ P[f"upperarm_{b}"].head, W @ P[f"forearm_{b}"].head, W @ P[f"forearm_{b}"].tail))
        root.append(W @ rig.pose.bones["goc"].head); hz.append((W @ rig.pose.bones["hips"].head).z)
        if dao_cu is not None: tay_dau.append((W @ rig.pose.bones["head"].tail).z)
    # ① trượt: trong các đoạn chân thấp (gót ≤ 1 cm trên nghỉ và mũi ≤ 1 cm) — quãng XY lớn nhất
    # ĐỘ PHỦ (audit ChatGPT 23/10 #1): không có khung chạm ⇒ trượt = 0 là cổng MÙ (lao LTX lơ lửng: 0 mm; chạm đất thật: 470 mm).
    # Nay đếm khung chạm; phủ < 30 % khung-chân ⇒ «khong_do_duoc» và TRƯỢT (clip có pha bay thật: clip.requirements.phu_cham_min_pct).
    truot = 0.0; n_cham = 0; truot_o = None
    for b in "LR":
        z0g, z0m = K[f"co_chan_{b}"].z, K[f"mui_chan_{b}"].z; seg = []
        def _do(seg, f_end):
            nonlocal truot, truot_o
            if len(seg) > 1:
                t_ = max((p - seg[0]).xy.length for p in seg)
                if t_ > truot: truot, truot_o = t_, [b, f_end - len(seg) + 1, f_end]   # đoạn chạm (theo cửa) trượt nhất: [bên, khung đầu, khung cuối]
        for i_, (g_, m_) in enumerate(zip(got[b], mui[b])):
            if g_.z - z0g <= 0.01 and m_.z - z0m <= 0.01: seg.append(g_); n_cham += 1
            else: _do(seg, i_ - 1); seg = []
        _do(seg, len(got[b]) - 1)
    kq["1_truot_o"] = truot_o
    # 1c CHÂN THẤP MÀ BAY (audit 23/10: ① chỉ nhìn ≤ 1 cm, bộ giải mới để chân tự do ở +2 cm ⇒ chân lướt 492 mm sát đất mà ① = 0): đo từ pose ĐÃ BAKE,
    # không dùng danh sách chạm của bộ giải — khung nào min(cổ chân, mũi) ≤ 3 cm mà tốc độ XY cổ chân > CHAN_THAP_V_MAX ⇒ cộng quãng. Hiệu chuẩn: xem CHAN_THAP_V_MAX.
    bay = 0.0; v_thap = 0.0
    for b in "LR":
        z0g, z0m = K[f"co_chan_{b}"].z, K[f"mui_chan_{b}"].z
        thap = [min(g_.z - z0g, m_.z - z0m) <= 0.03 for g_, m_ in zip(got[b], mui[b])]
        for i_ in range(1, len(got[b])):
            if thap[i_] and thap[i_ - 1]:
                d_ = (got[b][i_] - got[b][i_ - 1]).xy.length; v_ = d_ * FPS; v_thap = max(v_thap, v_)
                if v_ > CHAN_THAP_V_MAX: bay += d_
    kq["1c_chan_thap_bay_mm"] = round(bay * 1000, 1); kq["1c_toc_do_thap_max_mps"] = round(v_thap, 2)
    # CHÂN LƠ LỬNG + CHÂN RUNG (Boss 24/10 xem clip lao: «hỏng chân khỏi mặt đất một nhịp sau khi phóng lao» · «chân sau giờ glitch giựt giựt» — cửa cũ mù cả hai).
    # Đo từ pose đã bake. Lơ lửng = CẢ bàn chân (cổ chân và mũi) 3–20 cm trên nền, tốc độ XY < 0,35 m/s, chân kia
    # đang đứng (≤ 1 cm), hông không bật (|sai phân 2| < 1 cm), ≥ 3 khung liền. Rung = sai phân bậc 2 vị trí cổ chân (mm) và dốc bàn chân (°): RMS báo,
    # MAX là cửa — hiệu chuẩn 24/10 trên pose bake: idle 0/0 · Kimodo bow 25,0 mm / 8,5° · Kimodo walk 48,8 mm / 13,4° ⇒ CHAN_RUNG_MAX_MM 60 · CHAN_RUNG_MAX_DEG 16;
    # lao trước sửa 154,9 mm / 32,2° (phải rớt).
    lo_lung = 0; lo_lung_o = []; rung_mm = {}; rung_deg = {}
    hz2 = [abs(hz[i + 1] - 2 * hz[i] + hz[i - 1]) for i in range(1, len(hz) - 1)] if len(hz) > 2 else []
    for b in "LR":
        o_ = "R" if b == "L" else "L"; z0g, z0m = K[f"co_chan_{b}"].z, K[f"mui_chan_{b}"].z; g_, m_ = got[b], mui[b]; n_ = len(g_); run = []
        for i_ in range(1, n_ - 1):
            vxy = (g_[i_] - g_[i_ - 1]).xy.length * FPS; dz = abs(g_[i_].z - g_[i_ - 1].z); h_ = g_[i_].z - z0g
            ok = 0.03 <= min(h_, m_[i_].z - z0m) <= 0.20 and vxy < 0.35 and (got[o_][i_].z - K[f"co_chan_{o_}"].z) <= 0.01 and hz2[i_ - 1] < 0.01   # CẢ bàn chân rời đất (nhón gót tĩnh không phải treo)
            if ok: run.append(i_)
            else:
                if len(run) >= 3: lo_lung += len(run); lo_lung_o.append([b, run[0], run[-1]])
                run = []
        if len(run) >= 3: lo_lung += len(run); lo_lung_o.append([b, run[0], run[-1]])
        a2 = [(g_[i_ + 1] - 2 * g_[i_] + g_[i_ - 1]).length for i_ in range(1, n_ - 1)]
        doc = [math.degrees(math.atan2((m_[i_] - g_[i_]).z, (m_[i_] - g_[i_]).xy.length)) for i_ in range(n_)]; p2 = [abs(doc[i_ + 1] - 2 * doc[i_] + doc[i_ - 1]) for i_ in range(1, n_ - 1)]
        rung_mm[b] = (math.sqrt(sum(x * x for x in a2) / max(1, len(a2))) * 1000, max(a2) * 1000 if a2 else 0.0, (a2.index(max(a2)) + 1) if a2 else None)
        rung_deg[b] = (math.sqrt(sum(x * x for x in p2) / max(1, len(p2))), max(p2) if p2 else 0.0, (p2.index(max(p2)) + 1) if p2 else None)
    kq["chan_lo_lung_frames"] = lo_lung; kq["chan_lo_lung_o"] = lo_lung_o
    kq["chan_rung_mm"] = round(max(rung_mm[b][0] for b in "LR"), 2); kq["chan_rung_max_mm"] = round(max(rung_mm[b][1] for b in "LR"), 1); kq["chan_rung_max_o"] = max(("LR"), key=lambda b: rung_mm[b][1]) + str(rung_mm[max("LR", key=lambda b: rung_mm[b][1])][2])
    kq["chan_rung_deg"] = round(max(rung_deg[b][0] for b in "LR"), 2); kq["chan_rung_max_deg"] = round(max(rung_deg[b][1] for b in "LR"), 1); kq["chan_rung_max_deg_o"] = max("LR", key=lambda b: rung_deg[b][1]) + str(rung_deg[max("LR", key=lambda b: rung_deg[b][1])][2])
    kq["glitch_sua"] = list(SAM_GLITCH); kq["1_anh2d"] = SAM_ANH2D; kq["kep_co_tay"] = SAM_KEP_TAY
    kq.update(than_rung(rig, khoang(N)[0], khoang(N)[1]))   # P1-k: toàn thân so với nguồn (cửa trong animate.py)
    # HÔNG RUNG (P1 23/10, Boss «rung rung»): RMS sai phân bậc 2 của hips.z (mm) — chỉ BÁO; cửa khi fixture dương đo sạch (test_spec/README)
    kq["hong_rung_mm"] = round(math.sqrt(sum((hz[i + 1] - 2 * hz[i] + hz[i - 1]) ** 2 for i in range(1, len(hz) - 1)) / max(1, len(hz) - 2)) * 1000, 2) if len(hz) > 2 else 0.0
    kq["1_truot_chan_mm"] = round(truot * 1000, 1); kq["1_phu_cham_pct"] = round(100 * n_cham / max(1, len(got["L"]) + len(got["R"])), 1)
    if kq["1_phu_cham_pct"] < clip.get("requirements", {}).get("phu_cham_min_pct", 30): kq["1_truot_chan_mm"] = "khong_do_duoc"
    # ⑪ mũi chân lệch hướng hông khi chạm đất (Boss 22/10: «bàn chân lúc chạy chỉa qua 1 bên»). ĐỊNH NGHĨA LẠI (Boss 23/10 «Đồng ý cả hai»):
    # chân ĐANG ĐỨNG (đoạn ≥ 2 khung liên tiếp ≤ 1 cm) so với hướng hông TẠI KHUNG ĐẦU đoạn đứng; hông được xoay tại chỗ trên chân trụ tới
    # chan.xoay_tai_cho_max_deg (đo 23/10: tịnh tiến 0,0 mm trong mọi đoạn ⇒ vi phạm cũ là xoay thuần, xoay trên mũi bàn chân là có thật).
    # Khung thấp đơn lẻ: so từng khung như cũ. `11_cu_deg` = số cũ (từng khung) để đối chiếu.
    lech = 0.0; lech_cu = 0.0; xoay_tc = 0.0; HU = []; DF = {b: [] for b in "LR"}; THAP = {b: [] for b in "LR"}; CUA11 = []
    for i in range(khoang(N)[0] * ups, khoang(N)[1] * ups + 1):
        f = i / ups; sc.frame_set(int(f)); bpy.context.view_layer.update(); W = rig.matrix_world; Pb = rig.pose.bones
        lr = (W @ Pb["thigh_L"].head) - (W @ Pb["thigh_R"].head); h = lr.cross(V((0, 0, 1))); h.z = 0
        if (root[-1] - root[0]).length > 0.3: h = (root[-1] - root[0]); h.z = 0   # có di chuyển: so với HƯỚNG ĐI (thứ mắt thấy), không với hông lắc ±5°
        HU.append(h.normalized() if h.length > 1e-4 else None)
        for b in "LR":
            THAP[b].append((W @ Pb[f"foot_{b}"].head).z - K[f"co_chan_{b}"].z <= 0.01)
            d = (W @ Pb[f"foot_{b}"].tail) - (W @ Pb[f"foot_{b}"].head); d.z = 0; DF[b].append(d.normalized() if d.length > 1e-4 else None)
    XOAY_MAX = 0.0 if os.environ.get("THU_XOAY_TAI_CHO_0") else nap_motion_profile()["chan"]["xoay_tai_cho_max_deg"]   # thử ngược: không cho xoay tại chỗ ⇒ ⑪ pivot phải rớt
    for b in "LR":
        n_ = len(THAP[b]); i = 0
        while i < n_:
            if not THAP[b][i]: i += 1; continue
            j = i
            while j < n_ and THAP[b][j]: j += 1
            h0 = HU[i]
            for k in range(i, j):
                d, h = DF[b][k], HU[k]
                if d is None or h is None: continue
                lech_cu = max(lech_cu, math.degrees(d.angle(h)))
                if j - i >= 2 and h0 is not None: lech = max(lech, math.degrees(d.angle(h0))); xoay_tc = max(xoay_tc, math.degrees(h.angle(h0)))
                else: lech = max(lech, math.degrees(d.angle(h)))
                if os.environ.get("CUA_DUMP"): CUA11.append([b, i, k, round(math.degrees(d.angle(h0)), 1) if h0 is not None else None, round(math.degrees(h.angle(h0)), 1) if h0 is not None else None, round(math.degrees(d.angle(h)), 1)])
            i = j
    kq["11_chan_lech_huong_deg"] = round(lech, 1); kq["11_cu_deg"] = round(lech_cu, 1); kq["11_xoay_tai_cho_deg"] = round(xoay_tc, 1); kq["11_xoay_tai_cho_max_deg"] = XOAY_MAX
    co = []; vat = []; CUA_DUMP = {}   # ⑬ góc cổ chân (cẳng ↔ bàn chân); nghỉ ≈ 90–100°. Gãy gập ⇒ ra ngoài [55°, 150°]
    for f in range(khoang(N)[0], khoang(N)[1] + 1):
        sc.frame_set(f); bpy.context.view_layer.update(); W = rig.matrix_world; Pb = rig.pose.bones
        for b in "LR":
            a_ = (W @ Pb[f"shin_{b}"].head) - (W @ Pb[f"shin_{b}"].tail); c_ = (W @ Pb[f"foot_{b}"].tail) - (W @ Pb[f"foot_{b}"].head)
            co.append(math.degrees(a_.angle(c_)))
            th = (W @ Pb[f"thigh_{b}"].tail) - (W @ Pb[f"thigh_{b}"].head); sh_ = -a_; nrm = th.cross(sh_)
            vung = (W @ Pb[f"foot_{b}"].head).z - K[f"co_chan_{b}"].z > 0.02   # pha VUNG (Boss khoanh đỏ); chạm đất do cửa ⑪ lo
            if vung and math.degrees(th.angle(sh_)) > 15 and nrm.length > 1e-6 and c_.length > 1e-6:   # gối gập rõ ⇒ có mặt phẳng chân
                vat.append(abs(90 - math.degrees(nrm.normalized().angle(c_.normalized()))))
            if os.environ.get("CUA_DUMP"):   # chẩn đoán ⑬/13b theo đúng công thức cửa, từng khung (sau khi hạ hông)
                CUA_DUMP.setdefault(b, []).append([f, round((W @ Pb[f"foot_{b}"].head).z - K[f"co_chan_{b}"].z, 3), round(co[-1], 1), round(abs(90 - math.degrees(nrm.normalized().angle(c_.normalized()))), 1) if nrm.length > 1e-6 and c_.length > 1e-6 else None, round(math.degrees(th.angle(sh_)), 1), bool(vung), round(((W @ Pb[f"foot_{b}"].head) - (W @ Pb[f"shin_{b}"].tail)).length * 1000, 1)])
    kq["13_co_chan_min_max"] = [round(min(co), 1), round(max(co), 1)]
    if os.environ.get("CUA_DUMP"):
        CUA_DUMP["11"] = CUA11; CUA_DUMP["hips_z"] = [round(z, 4) for z in hz]
        CUA_DUMP["vet"] = {b: [[i_, round(g_.z - K[f"co_chan_{b}"].z, 4), round(m_.z - K[f"mui_chan_{b}"].z, 4), round(g_.x, 4), round(g_.y, 4), round(math.degrees(math.atan2((m_ - g_).z, (m_ - g_).xy.length)), 2), round(math.degrees(math.atan2((m_ - g_).y, (m_ - g_).x)), 2)] for i_, (g_, m_) in enumerate(zip(got[b], mui[b]))] for b in "LR"}
        json.dump(CUA_DUMP, open(os.environ["CUA_DUMP"], "w"))
    ct = []   # ⑭ cổ tay gập (cẳng ↔ bàn tay) ≤ 50°
    for f in range(khoang(N)[0], khoang(N)[1] + 1):
        sc.frame_set(f); bpy.context.view_layer.update(); W = rig.matrix_world; Pb = rig.pose.bones
        for b in "LR":
            fa = (W @ Pb[f"forearm_{b}"].tail) - (W @ Pb[f"forearm_{b}"].head); hd = (W @ Pb[f"hand_{b}"].tail) - (W @ Pb[f"hand_{b}"].head)
            ct.append(math.degrees(fa.angle(hd)))
    kq["14_co_tay_gap_max_deg"] = round(max(ct), 1)
    kq["13b_ban_chan_vat_khoi_mat_chan_deg"] = round(max(vat), 1) if vat else 0.0   # Boss 22/10 khoanh đỏ: bàn chân chĩa NGANG khi cẳng gập ra sau
    # ② lún đất
    thap = min(min(g_.z - K[f"co_chan_{b}"].z for g_ in got[b]) for b in "LR"); thap2 = min(min(m_.z - K[f"mui_chan_{b}"].z for m_ in mui[b]) for b in "LR")
    kq["2_lun_dat_mm"] = round(min(thap, thap2) * 1000, 1)
    # ③ khớp: gối 3–140°, khuỷu 5–145°
    kq["3_goi_min_max"] = [round(min(goi), 1), round(max(goi), 1)]; kq["3_khuyu_min_max"] = [round(min(khuyu), 1), round(max(khuyu), 1)]
    # ⑥ mối nối vòng lặp: vị trí xương (bỏ dời gốc) khung 0 vs N
    if clip.get("loop"):
        def pose(f):
            sc.frame_set(f); bpy.context.view_layer.update(); W = rig.matrix_world; r = W @ rig.pose.bones["goc"].head
            return [(W @ p.head) - r for p in rig.pose.bones if p.bone.use_deform]
        a_, b_ = pose(khoang(N)[0]), pose(khoang(N)[1] + 1 if os.environ.get("CHU_KY") else N); kq["6_moi_noi_mm"] = round(max((x - y).length for x, y in zip(a_, b_)) * 1000, 1)
    # ⑦ giật: bước góc lớn nhất 96 Hz trên các xương deform (cảnh báo)
    # ⑧ quãng gốc đúng tốc độ
    if clip["root"].get("speed_mps"):
        q = clip["root"]["speed_mps"] * s * N / FPS; kq["8_sai_quang_pct"] = round(abs((root[-1] - root[0]).length - q) / q * 100, 2)
    # ⑩ đọc được hành động
    yc = clip.get("requirements", {})
    if "hit_cao_m" in yc and dao_cu is not None:   # ⑩ chặt NGANG: lưỡi ở độ cao thân cây lúc trúng, cán gần nằm ngang
        hit = next((e["frame"] for e in clip.get("events", []) if e["name"] == "hit"), N // 2)
        sc.frame_set(hit); bpy.context.view_layer.update(); M = dao_cu.matrix_world
        dau = M @ V((0.12, 0, 0.67)); zt = (M.to_3x3() @ V((0, 0, 1))).normalized()
        kq["10_luoi_cao_m"] = round(dau.z, 2); kq["10_can_lech_ngang_deg"] = round(math.degrees(math.asin(abs(zt.z))), 1)
    elif clip["id"].startswith("chop") and dao_cu is not None:
        z = []
        for f in range(khoang(N)[0], khoang(N)[1] + 1):
            sc.frame_set(f); bpy.context.view_layer.update(); z.append(max((o.matrix_world @ V(c)).z for o in dao_cu.children for c in o.bound_box))   # điểm cao nhất lưới rìu (gốc mảnh = chỗ cầm ⇒ đo nhầm)
        sc.frame_set(0); bpy.context.view_layer.update(); kq["10_riu_tren_dinh_dau_m"] = round(max(z) - (rig.matrix_world @ rig.pose.bones["head"].tail).z, 2)
    if go is not None and than is not None:   # ⑤ đạo cụ xuyên thân (BVH thân đã biến dạng; trong = phía ngược pháp tuyến)
        from mathutils.bvhtree import BVHTree
        sau = 0.0; vg = go.data.vertices; ed = go.data.edges
        # vùng TIẾP XÚC có chủ đích (spec: loại trừ «explicit contact patches»): mặt có xương trội thuộc danh sách clip
        cho_phep = set(clip.get("tiep_xuc", [])); ten_g = {g.index: g.name for g in than.vertex_groups}
        def troi(vi):
            gs = than.data.vertices[vi].groups; return ten_g[max(gs, key=lambda x: x.weight).group] if len(gs) else ""
        bo_mat = {i for i, pl in enumerate(than.data.polygons) if sum(troi(v) in cho_phep for v in pl.vertices) * 2 > len(pl.vertices)}
        kq["5_mat_tiep_xuc_bo_qua"] = len(bo_mat)
        for f in range(khoang(N)[0], khoang(N)[1] + 1, 2):
            sc.frame_set(f); dg = bpy.context.evaluated_depsgraph_get(); ev = than.evaluated_get(dg); me = ev.to_mesh()
            bvh = BVHTree.FromPolygons([v.co.copy() for v in me.vertices], [list(pl.vertices) for i, pl in enumerate(me.polygons) if i not in bo_mat]); ev.to_mesh_clear()
            Mi = than.matrix_world.inverted(); Mg = go.matrix_world
            for e in ed:
                a_, b_ = Mg @ vg[e.vertices[0]].co, Mg @ vg[e.vertices[1]].co
                for t in range(11):
                    q = Mi @ (a_.lerp(b_, t / 10)); loc, nrm, _, d = bvh.find_nearest(q)
                    if loc is not None and d < 0.25 and trong_bvh(bvh, q) and d > sau: sau = d; kq["5_noi_xuyen"] = [f, [round(x, 2) for x in (than.matrix_world @ loc)]]
        kq["5_go_xuyen_than_mm"] = round(sau * 1000, 1)
    if "10_luoi_cao_m" in kq:
        lo, hi = yc["hit_cao_m"]; kq["10_ngang_dat"] = lo <= kq["10_luoi_cao_m"] <= hi and kq["10_can_lech_ngang_deg"] <= yc.get("can_ngang_max_deg", 35)
    dat = kq["14_co_tay_gap_max_deg"] <= 50 and kq["13b_ban_chan_vat_khoi_mat_chan_deg"] <= 25 and 55 <= kq["13_co_chan_min_max"][0] and kq["13_co_chan_min_max"][1] <= ANKLE_ANGLE_MAX_DEG and kq.get("11_chan_lech_huong_deg", 0) <= clip.get("requirements", {}).get("chan_lech_max_deg", 12) and kq.get("11_xoay_tai_cho_deg", 0) <= kq.get("11_xoay_tai_cho_max_deg", 30) and kq.get("10_ngang_dat", True) and kq.get("5_go_xuyen_than_mm", 0) <= 3 and kq["1_truot_chan_mm"] != "khong_do_duoc" and kq["1_truot_chan_mm"] <= 5 and kq["2_lun_dat_mm"] >= -3 and kq["3_goi_min_max"][1] <= 140 and kq["3_khuyu_min_max"][0] >= -2 \
        and kq.get("6_moi_noi_mm", 0) <= 1.5 and kq.get("8_sai_quang_pct", 0) <= 0.5 and kq.get("10_riu_tren_dinh_dau_m", 1) >= 0.25
    kq["dat"] = bool(dat); return kq


def thu_truc(rig):
    """cửa ⓪: mỗi kênh +20° đơn lẻ phải đưa đầu mút đúng hướng giải phẫu (bắt lỗi vặn nhầm trục)."""
    sc = bpy.context.scene; loi = []
    tat = [c for pb in rig.pose.bones for c in pb.constraints]   # tắt IK/copy khi thử trục (IK kéo đùi về đích ⇒ báo sai)
    for c in tat: c.mute = True
    thu = [("chest", {"pitch": 20}, "tail", lambda d: d.y < 0, "cúi→trước"), ("chest", {"yaw": 20}, "tail_xy", None, "yaw: không đổi cao"),
           ("thigh_L", {"flex": 20}, "tail", lambda d: d.y < 0, "gập hông→gối ra trước"), ("upperarm_R", {"flex": 20}, "tail", lambda d: d.y < 0, "gập vai→khuỷu ra trước"),
           ("upperarm_L", {"abd": 20}, "tail", lambda d: d.x > 0, "dạng trái→+X"), ("upperarm_R", {"abd": 20}, "tail", lambda d: d.x < 0, "dạng phải→−X"),
           ("forearm_L", {"flex": 30}, "tail", lambda d: d.y < 0, "gập khuỷu→tay ra trước")]
    for xg, k, _, ok, mo in thu:
        pb = rig.pose.bones[xg]; bpy.context.view_layer.update(); t0 = (rig.matrix_world @ pb.tail).copy()
        pb.rotation_quaternion = q_giai_phau(rig, xg, k); bpy.context.view_layer.update(); t1 = rig.matrix_world @ pb.tail
        pb.rotation_quaternion = Q(); bpy.context.view_layer.update(); d = t1 - t0
        if ok is None:
            if abs(d.z) > 0.01: loi.append(mo)
        elif not ok(d): loi.append(mo)
    for c in tat: c.mute = False
    return loi


def render(rig, N, out, theo=True, anh=False):
    sc = bpy.context.scene
    for e, r in ((4.0, (45, 0, 45)), (0.45, (60, 0, 60)), (0.6, (60, 0, 160))):
        l = bpy.data.objects.new("l", bpy.data.lights.new("l", "SUN")); sc.collection.objects.link(l); l.data.energy = e
        l.data.angle = math.radians(8); l.data.use_shadow = e >= 2.5; l.data.use_shadow_jitter = True; l.rotation_euler = [math.radians(x) for x in r]
    w = bpy.data.worlds.new("W"); sc.world = w; w.use_nodes = True; w.node_tree.nodes["Background"].inputs[0].default_value = (0.42, 0.44, 0.40, 1)
    bpy.ops.mesh.primitive_plane_add(size=40); p = bpy.context.object; m = bpy.data.materials.new("dat"); m.use_nodes = True
    m.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.30, 0.25, 0.17, 1); p.data.materials.append(m)
    c = bpy.data.cameras.new("c"); c.type = "ORTHO"; c.ortho_scale = 2.8; c.clip_end = 100; co = bpy.data.objects.new("c", c); sc.collection.objects.link(co); sc.camera = co
    co.rotation_euler = (math.radians(float(os.environ.get("CAM_X", "72"))), 0, math.radians(float(os.environ.get("CAM_Z", "-38")))); co.location = V((0, 0, 0.95)) + co.rotation_euler.to_matrix() @ V((0, 0, 30))   # CAM_Z 0 = chính diện (so với video gốc)
    if theo:
        t = co.constraints.new("CHILD_OF"); t.target = rig; t.subtarget = "goc"
        for a_ in ("x", "y", "z"): setattr(t, f"use_rotation_{a_}", False)
        t.set_inverse_pending = False
    sc.render.engine = "BLENDER_EEVEE"; sc.view_settings.view_transform = "Standard"; sc.render.resolution_x, sc.render.resolution_y = 480, 560
    if not os.environ.get("CHU_KY"): sc.frame_start, sc.frame_end = 0, N - 1
    tmp = out[:-4] + "_frames"; shutil.rmtree(tmp, ignore_errors=True); os.makedirs(tmp)
    sc.render.image_settings.file_format = "PNG"; sc.render.filepath = tmp + "/f_"; bpy.ops.render.render(animation=True)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", str(FPS), "-start_number", str(sc.frame_start), "-i", tmp + "/f_%04d.png", "-pix_fmt", "yuv420p", out])
    shutil.rmtree(tmp)


CAN_DIR = []; CAN_NGUON = []; XOAY_TAY = []


def tay_theo_nguon(rig, f_json, t0, N, muot=3):
    """TAY từ nguồn mocap riêng (SAM 3D Body — bàn tay tốt nhất) đặt lên thân đã retarget (GVHMR).
    Boss 22/10: «compare the gap between body… to the hand to get the exact gap and position, maybe triangle gap measurement».
    Mỗi khung: khung THÂN nguồn Fs (tam giác vai L–vai R–giữa hông) và khung thân đích Ft (cùng tam giác trên rig);
    hướng cánh tay / cẳng tay / bàn tay của nguồn đổi sang local Fs rồi đặt lên đích qua Ft ⇒ giữ đúng tam giác vai–khuỷu–cổ tay so với thân.
    Trả về sai số: vị trí cổ tay trong khung thân, chia chiều cao thân (nguồn vs đích), lớn nhất theo khung."""
    d = json.load(open(f_json)); Fr = [f for f in d["frames"] if f.get("w")]
    def bl(p): return V((p[0], p[2], -p[1]))
    T = [f["t"] for f in Fr]; R = [[bl(p) for p in f["w"]] for f in Fr]
    S = [[sum((r[j] for r in R[max(0, i - muot // 2): i + muot // 2 + 1]), V()) / len(R[max(0, i - muot // 2): i + muot // 2 + 1]) for j in range(33)] for i in range(len(R))]
    def lay(t):
        i = max(0, min(len(T) - 2, max((k for k in range(len(T)) if T[k] <= t), default=0))); u = max(0.0, min(1.0, (t - T[i]) / max(1e-6, T[i + 1] - T[i])))
        return [S[i][j].lerp(S[i + 1][j], u) for j in range(33)]
    # trục RÌU đo từ video (do_riu.py: điểm ảnh rìu + tia camera) — út→trỏ của SAM 3D chỉ khớp 3/8 khung (22/10)
    CAN_T = [(f["t"], bl(f["can"])) for f in Fr if f.get("can")]
    def lay_can(t):   # chỉ khi có khung đo tin cậy trong ±1 khung nguồn; không thì None ⇒ dùng hướng út→trỏ của bàn tay
        fps_ = d.get("fps", 30)
        for (ta, va), (tb, vb) in zip(CAN_T, CAN_T[1:]):   # nội suy giữa 2 khung đo tin cậy nếu trống ≤ 4 khung nguồn
            if ta <= t <= tb and tb - ta <= 4.5 / fps_: return va.slerp(vb, (t - ta) / max(1e-6, tb - ta))   # (rìu chồng chân f12–15: Codex FAIL)
        gan = min(CAN_T, key=lambda x: abs(x[0] - t))
        if abs(gan[0] - t) > 0.6 / fps_: return None   # một phía, xa ⇒ không mượn (f23 mượn khung 45 ⇒ rìu ngang — Codex FAIL)
        return gan[1]
    def khung(vL, vR, hc):
        mid = (vL + vR) / 2; x = (vL - vR).normalized(); z = (mid - hc); z = (z - x * z.dot(x)).normalized(); y = z.cross(x)
        return mathutils.Matrix((x, y, z)).transposed(), mid, (mid - hc).length
    sc = bpy.context.scene; W = rig.matrix_world; loi = 0.0; o_ = None; bang = []; khe = []
    global CAN_DIR, CAN_NGUON, XOAY_TAY; CAN_DIR = []; CAN_NGUON = []; XOAY_TAY = []
    # XOAY cổ tay NGUỒN (SAM 3D Body pred_global_rots, khung MHR = F·toạ độ, F = diag(1,−1,−1); kiểm 22/10: lệch 0,0° với F, 23–163° không F)
    # đổi sang toạ độ bl: R' = (B·F) R (B·F)ᵀ, B: (x,y,z) → (x, z, −y). Boss 22/10: «lấy điểm rig bàn tay trong hình transfer thẳng qua rig»
    thu = os.path.dirname(f_json); RK = {}
    kf = os.path.join(thu, "khop_mhr.json")
    if os.path.exists(kf):
        import numpy as np
        ten = json.load(open(kf))["ten"]; jw = {"R": ten.index("r_wrist"), "L": ten.index("l_wrist")}
        BF = mathutils.Matrix(((1, 0, 0), (0, 0, 1), (0, -1, 0))) @ mathutils.Matrix(((1, 0, 0), (0, -1, 0), (0, 0, -1)))
        for f_ in Fr:
            pth = os.path.join(thu, f"m_{round(f_['t'] * d.get('fps', 30)):04d}.npz")
            if os.path.exists(pth):
                Rm = np.load(pth)["R"]; RK[f_["t"]] = {b_: (BF @ mathutils.Matrix(Rm[jw[b_]].tolist()) @ BF.transposed()).to_quaternion() for b_ in "LR"}
    TK = sorted(RK)
    def lay_xoay(t, b_):
        if not TK: return None
        if t <= TK[0]: return RK[TK[0]][b_]
        for ta, tb in zip(TK, TK[1:]):
            if t <= tb:
                qa, qb = RK[ta][b_], RK[tb][b_]
                if qa.dot(qb) < 0: qb = -qb
                return qa.slerp(qb, (t - ta) / max(1e-6, tb - ta))
        return RK[TK[-1]][b_]
    for pb_ in rig.pose.bones:
        if pb_.name.startswith(("upperarm", "forearm", "hand")):
            for c in pb_.constraints: c.mute = True
    for f in range(N + 1):
        p = lay(t0 + f / FPS); sc.frame_set(f); bpy.context.view_layer.update()
        Fs, ms, hs = khung(p[11], p[12], (p[23] + p[24]) / 2)
        Pb = rig.pose.bones; wv = lambda n, duoi=False: W @ (Pb[n].tail if duoi else Pb[n].head)
        Ft, mt, ht = khung(wv("upperarm_L"), wv("upperarm_R"), (wv("thigh_L") + wv("thigh_R")) / 2)
        doi = lambda v: Ft @ (Fs.transposed() @ v)
        for b, o in (("L", 0), ("R", 1)):
            # XƯƠNG ĐÒN gánh 25 % (≤ 20°) hướng bắp tay nguồn so với lúc nghỉ (Boss «tay trái xoắn»: đòn đứng yên ⇒ nách trái thắt 0,42 ở f18)
            if f"clavicle_{b}" in Pb and float(os.environ.get("DON_TY_LE", "0")) > 0:   # tắt mặc định: không đổi nách (0,42→0,39), thước đo nách chưa tin được
                pc = Pb[f"clavicle_{b}"]; pc.rotation_quaternion = mathutils.Quaternion(); bpy.context.view_layer.update()
                Mch = (W @ Pb["chest"].matrix).to_3x3().normalized() @ rig.data.bones["chest"].matrix_local.to_3x3().inverted()
                u_nghi = (Mch @ (rig.data.bones[f"upperarm_{b}"].tail_local - rig.data.bones[f"upperarm_{b}"].head_local)).normalized()
                q_ = u_nghi.rotation_difference(doi(p[13 + o] - p[11 + o]).normalized()); g_ = min(q_.angle * float(os.environ.get("DON_TY_LE", "0.25")), math.radians(20))
                ax_ = q_.axis; m = pc.matrix.copy(); t = m.translation.copy(); m2 = mathutils.Matrix.Rotation(g_, 4, W.inverted().to_3x3() @ ax_) @ m; m2.translation = t
                pc.matrix = m2; bpy.context.view_layer.update(); pc.keyframe_insert("rotation_quaternion", frame=f)
            # VỊ TRÍ cổ tay = khoảng cách đo trong tam giác thân nguồn × cỡ thân đích (chép góc thôi ⇒ lệch 18 % vì tỉ lệ tay khác);
            # khuỷu: điểm trên vòng 2 đoạn gần hướng khuỷu nguồn nhất
            S_ = wv(f"upperarm_{b}"); Lu = rig.data.bones[f"upperarm_{b}"].length; Lf = rig.data.bones[f"forearm_{b}"].length
            if os.environ.get("TAY_TL", "tay") == "tay":   # HƯỚNG vai→cổ tay đo trong khung thân; ĐỘ DUỖI = (vai–cổ tay / dài tay) của nguồn × dài tay đích
                # (nhân theo CAO THÂN ⇒ tay settler dài hơn so với thân ⇒ cổ tay quá gần vai ⇒ khuỷu trái bung ra ngoài — Boss 22/10 «tay trái xoắn xoắn»)
                ds = p[15 + o] - p[11 + o]; Ls = (p[13 + o] - p[11 + o]).length + (p[15 + o] - p[13 + o]).length
                Wt = S_ + doi(ds).normalized() * (ds.length / Ls) * (Lu + Lf)
            else: Wt = mt + Ft @ (Fs.transposed() @ (p[15 + o] - ms)) * (ht / hs)
            dv = Wt - S_; dl = min(dv.length, Lu + Lf - 1e-4); u = dv.normalized()
            a_ = (Lu * Lu - Lf * Lf + dl * dl) / (2 * dl); r_ = math.sqrt(max(0.0, Lu * Lu - a_ * a_)); C_ = S_ + u * a_
            Eh = S_ + doi(p[13 + o] - p[11 + o]).normalized() * Lu; v_ = (Eh - C_) - u * (Eh - C_).dot(u)
            v_ = v_.normalized() if v_.length > 1e-6 else u.orthogonal().normalized(); E_ = C_ + v_ * r_
            ngam(rig, f"upperarm_{b}", E_ - S_); bpy.context.view_layer.update()
            ngam(rig, f"forearm_{b}", (S_ + u * dl) - E_); bpy.context.view_layer.update()
            ngam(rig, f"hand_{b}", doi((p[17 + o] + p[19 + o]) / 2 - p[15 + o])); bpy.context.view_layer.update()
            for x in ("upperarm", "forearm", "hand"): Pb[f"{x}_{b}"].keyframe_insert("rotation_quaternion", frame=f)
            a = Fs.transposed() @ (p[15 + o] - ms) / hs; c = Ft.transposed() @ (wv(f"forearm_{b}", True) - mt) / ht
            if (a - c).length > loi: loi = (a - c).length; o_ = (f, b)
            bang.append((f, b, [round(x * 100) for x in a], [round(x * 100) for x in c]))
        # hướng CÁN đo từ bàn tay nguồn: nắm cán ⇒ cán chạy ngang lòng bàn tay từ phía ngón út sang ngón trỏ (cả hai tay cùng chiều)
        cv = lay_can(t0 + f / FPS) if CAN_T else None; nguon_can = "video" if cv is not None else "ban_tay"
        cv = cv if cv is not None else ((p[19] - p[17]) + (p[20] - p[18])).normalized()
        zc = doi(cv).normalized()
        if CAN_DIR and nguon_can == "ban_tay" and zc.dot(CAN_DIR[-1]) < 0: zc = -zc   # hướng bàn tay: giữ chiều liền mạch
        CAN_DIR.append(zc); CAN_NGUON.append(nguon_can)
        Cm = Ft @ Fs.transposed()   # khung thân nguồn → thân đích (khung này)
        XOAY_TAY.append({b_: (Cm @ q_.to_matrix()) for b_ in "LR" if (q_ := lay_xoay(t0 + f / FPS, b_)) is not None} if TK else {})
    # khoảng cách HAI cổ tay / chiều cao thân (nguồn vs đích) — «gap» Boss hỏi
    for f in range(N + 1):
        p = lay(t0 + f / FPS); sc.frame_set(f); bpy.context.view_layer.update(); Pb = rig.pose.bones; wv = lambda n, duoi=False: W @ (Pb[n].tail if duoi else Pb[n].head)
        hs = ((p[11] + p[12]) / 2 - (p[23] + p[24]) / 2).length; ht = ((wv("upperarm_L") + wv("upperarm_R")) / 2 - (wv("thigh_L") + wv("thigh_R")) / 2).length
        khe.append((f, round((p[15] - p[16]).length / hs * 100), round((wv("forearm_L", True) - wv("forearm_R", True)).length / ht * 100)))
    # TOÀN THÂN theo GÓC đoạn xương trong khung tam giác thân (khoảng cách sai vì settler khác tỉ lệ người — đo kiểu đó báo 36–105 %, 22/10)
    doan = {"dau": ((11, 12), (7, 8), "neck", "head"), "dui_L": (23, 25, "thigh_L", None), "dui_R": (24, 26, "thigh_R", None),
            "cang_chan_L": (25, 27, "shin_L", None), "cang_chan_R": (26, 28, "shin_R", None)}; lech_than = {k: 0 for k in doan}
    for f in range(N + 1):
        p = lay(t0 + f / FPS); sc.frame_set(f); bpy.context.view_layer.update(); Pb = rig.pose.bones; wv = lambda n, duoi=False: W @ (Pb[n].tail if duoi else Pb[n].head)
        Fs, ms, hs = khung(p[11], p[12], (p[23] + p[24]) / 2); Ft, mt, ht = khung(wv("upperarm_L"), wv("upperarm_R"), (wv("thigh_L") + wv("thigh_R")) / 2)
        for k, (a_, b_, xn, xn2) in doan.items():
            if k == "dau": vs = (p[7] + p[8]) / 2 - (p[11] + p[12]) / 2; vt = wv("head", True) - wv("neck")
            else: vs = p[b_] - p[a_]; vt = wv(xn, True) - wv(xn)
            e = math.degrees((Fs.transposed() @ vs).angle(Ft.transposed() @ vt)); lech_than[k] = max(lech_than[k], round(e, 1))
            if os.environ.get("IN_LECH") and k in ("dui_L", "dau"): print("LECH", f, k, round(e, 1))
    json.dump(dict(co_tay=bang, khe_hai_tay=khe, than_lech_deg=lech_than), open(os.environ.get("TAY_BANG", "/tmp/hand_bang.json"), "w")); print("than_lech_deg", lech_than)
    return dict(tay_lech_than_pct=round(loi * 100, 1), tay_lech_o=o_)


def ban_le_khuyu(rig, b, x_truoc=None):
    """KHUỶU LÀ BẢN LỀ (Boss 22/10 «tay trái đang bị xoắn xoắn»: bắp tay trái xoắn −124…+14° so với vai vì chỉ khớp HƯỚNG ⇒ xoắn tự do).
    Đặt xoắn bắp tay sao cho trục gập khuỷu (gập = quanh −X cục bộ) ⟂ mặt phẳng vai–khuỷu–cổ tay; cẳng tay cùng trục bản lề.
    Tay gần thẳng (mặt phẳng bất định) ⇒ giữ trục của khung trước. Trả về trục bản lề (thế giới) để nối khung sau. Giữ nguyên thế giới của bàn tay."""
    W = rig.matrix_world; P = rig.pose.bones; pu, pf, ph = P[f"upperarm_{b}"], P[f"forearm_{b}"], P[f"hand_{b}"]
    Mh = (W @ ph.matrix).copy()
    S_ = W @ pu.head; E_ = W @ pf.head; Wr = W @ pf.tail; u = (E_ - S_).normalized(); v = (Wr - E_).normalized(); n = u.cross(v)
    k0 = (W @ pu.matrix).to_3x3().normalized().col[0]; k0 = (k0 - u * k0.dot(u)).normalized()   # xoắn TỰ NHIÊN (xoay ngắn nhất từ tư thế nghỉ)
    kh = n.normalized() * float(os.environ.get("BAN_LE_DAU", "1")) if n.length > 1e-4 else k0   # trục +X theo bản lề (−n ⇒ lệch 180°, đo 22/10)
    if kh.dot(k0) < 0 and n.length < 0.3: kh = -kh
    w_ = max(0.0, min(1.0, (n.length - 0.08) / 0.30))   # tay gần THẲNG ⇒ bản lề bất định ⇒ nghiêng về xoắn tự nhiên (mang xoắn khung trước ⇒ nách trái thắt 0,42 ở f18)
    k = kh * w_ + k0 * (1 - w_); k = (k - u * k.dot(u)); k = k.normalized() if k.length > 1e-4 else k0
    for pb, y in ((pu, u), (pf, v)):
        kk = (k - y * k.dot(y)).normalized(); R = mathutils.Matrix((kk, y, kk.cross(y))).transposed()
        m = (W.inverted().to_3x3() @ R).to_4x4(); m.translation = pb.matrix.translation; pb.matrix = m; bpy.context.view_layer.update()
    mh_ = (W.inverted().to_3x3() @ Mh.to_3x3().normalized()).to_4x4(); mh_.translation = ph.matrix.translation; ph.matrix = mh_; bpy.context.view_layer.update()   # CHỈ khôi phục XOAY (gán cả ma trận ⇒ bàn tay bị kéo về cổ tay cũ, tách khỏi cẳng tay)
    return k.copy()


# ------------------------------------------------------------------ SAM 3D BODY → RIG: chuyển NGUYÊN độ xoay (cả xoắn), không chỉnh tay
# Boss 22/10: «Redo from original whole thing from SAM 3D… make sure all rig of sam 3D is matching rig we have on our character include the hand,
# make sure you dont twist arm and adjusting». Công thức chuẩn: M_b(t) = Y · C·R_j(t)·R_j,bind⁻¹·Cᵀ · M_b,khớp_bind.
SAM_MAP = {   # xương settler: (khớp MHR lấy XOAY, đầu đoạn, đuôi đoạn) — đoạn dùng hiệu chỉnh hướng lúc bind
    "hips": ("root", "root", "c_spine1"), "spine": ("c_spine1", "c_spine1", "c_spine3"), "chest": ("c_spine3", "c_spine3", "c_neck"),
    "neck": ("c_neck", "c_neck", "c_head"), "head": ("c_head", "c_neck", "c_head"),
    **{f"{x}_{B}": v for B, s_ in (("L", "l"), ("R", "r")) for x, v in (
        ("clavicle", (f"{s_}_clavicle", f"{s_}_clavicle", f"{s_}_uparm")), ("upperarm", (f"{s_}_uparm", f"{s_}_uparm", f"{s_}_lowarm")),
        ("forearm", (f"{s_}_lowarm", f"{s_}_lowarm", f"{s_}_wrist")), ("hand", (f"{s_}_wrist", f"{s_}_wrist", f"{s_}_middle1")),
        ("thigh", (f"{s_}_upleg", f"{s_}_upleg", f"{s_}_lowleg")), ("shin", (f"{s_}_lowleg", f"{s_}_lowleg", f"{s_}_foot")),
        ("foot", (f"{s_}_transversetarsal", f"{s_}_talocrural", f"{s_}_ball")))}}
SAM_CHAN = (0, 0, 0)   # placeholder
SAM_KHUNG = {}


def retarget_sam(rig, K, thu, t0, t1, khoa=True):
    import numpy as np, glob
    ten = json.load(open(os.path.join(thu, "khop_mhr.json")))["ten"]; ix = {n: i for i, n in enumerate(ten)}; nJ = len(ten)   # MHR 127 / SMPL-X 62
    # NGUỒN GỐC (audit ChatGPT 23/10 #5): rig từ VIDEO (GVHMR) phải đi qua khop_video.py (video_sang_rig.sh) — không thì hông trễ pha + mặt đất
    # sai như combo lao. Rig nối (noi_rig) kiểm từng đoạn. BO_KHOP_VIDEO=1 để cố ý bỏ qua (ghi lý do).
    def _thieu_khop(d_):
        tl_ = os.path.join(d_, "trong_luc.json"); ng_ = json.load(open(tl_)).get("nguon", "") if os.path.exists(tl_) else ""
        if os.path.exists(os.path.join(d_, "noi.json")):
            return [x for s_ in json.load(open(os.path.join(d_, "noi.json")))["doan"] for x in _thieu_khop(os.path.expanduser(s_.split(":")[0]) if os.path.isabs(os.path.expanduser(s_.split(":")[0])) else os.path.join(os.path.dirname(d_), s_.split(":")[0]))]
        return [d_] if "GVHMR" in ng_ and not os.path.exists(os.path.join(d_, "khop_video.json")) else []
    thieu = _thieu_khop(thu)
    if thieu and not os.environ.get("BO_KHOP_VIDEO"): raise SystemExit(f"⛔ rig từ video CHƯA khớp video (chạy ~/mocap/scripts/video_sang_rig.sh): {thieu}")
    # LICENCE / PROVENANCE (P2 24/10/2026, plan §1b): the game is SOLD ⇒ GVHMR (ZJU «educational, research and non-profit purposes only») and
    # SMPL-X (MPI forbids «production of other artifacts for commercial purposes») must never feed a shipped clip. source.json {estimator} is the
    # declaration (sam3d_to_rig.py / gvhmr_sang_rig.py write it); folders without it are judged by the «nguon» strings. Research only: ALLOW_GVHMR_RESEARCH=1.
    def _estimator(d_):
        sj_ = os.path.join(d_, "source.json")
        if os.path.exists(sj_): return str(json.load(open(sj_)).get("estimator", "")).lower()
        ng_ = " ".join(json.load(open(os.path.join(d_, x))).get("nguon", "") for x in ("trong_luc.json", "khop_mhr.json") if os.path.exists(os.path.join(d_, x)))
        return "gvhmr" if "GVHMR" in ng_ else ("smplx" if "SMPL-X" in ng_ and "HY-Motion" not in ng_ else "unknown")
    def _nguon_cam(d_):
        if os.path.exists(os.path.join(d_, "noi.json")):
            return [x for s_ in json.load(open(os.path.join(d_, "noi.json")))["doan"] for x in _nguon_cam(os.path.expanduser(s_.split(":")[0]) if os.path.isabs(os.path.expanduser(s_.split(":")[0])) else os.path.join(os.path.dirname(d_), s_.split(":")[0]))]
        return [(d_, _estimator(d_))] if _estimator(d_) in ("gvhmr", "smplx") else []
    cam_ = _nguon_cam(thu)
    if cam_ and os.environ.get("ALLOW_GVHMR_RESEARCH") != "1":
        raise SystemExit("⛔ LICENCE: rig folder from GVHMR / SMPL-X — research-only sources (ZJU GVHMR: «educational, research and non-profit purposes only»; MPI SMPL-X: no commercial artefacts) and the game is sold (plan §1b). "
                         "Use the clean path ~/mocap/scripts/run_sam3d_rig.py → sam3d_to_rig.py (SAM 3D Body / MHR, Apache-2.0) or Kimodo. Research only: ALLOW_GVHMR_RESEARCH=1. Folders: %s" % cam_)
    if cam_: print("⚠️ LICENCE: GVHMR/SMPL-X source allowed for RESEARCH only (ALLOW_GVHMR_RESEARCH=1) — never ship this clip:", cam_)
    sj = os.path.join(thu, "source.json"); print("NGUON_RIG:", json.load(open(sj)) if os.path.exists(sj) else {"estimator": _estimator(thu), "source.json": "missing (inferred from nguon strings)"})
    Gb = np.load(os.path.join(thu, "mhr_bind_G.npy")); Pb = np.load(os.path.join(thu, "mhr_bind_P.npy"))
    C = mathutils.Matrix(((1, 0, 0), (0, 0, -1), (0, 1, 0)))   # MHR gốc (y lên, mặt +z) → Blender (z lên, mặt −y)
    F = np.diag([1.0, -1.0, -1.0])                              # pred_joint_coords = lật y,z so với khung xoay (kiểm: lệch 0,0°)
    # TRỌNG LỰC: camera nguồn chúc xuống ~15° (GVHMR đo) ⇒ xoay dữ liệu SAM cho «lên» trùng trục đứng (không sửa ⇒ thân gập/nghiêng, chân khoá phẳng)
    Qn = mathutils.Matrix.Identity(3); tl = os.path.join(thu, "trong_luc.json")
    if os.path.exists(tl):
        u_cv = V(json.load(open(tl))["len_trong_luc_cv"]); u_n = V((u_cv.x, -u_cv.y, -u_cv.z)); Qn = u_n.rotation_difference(V((0, 1, 0))).to_matrix()
    CQ = C @ Qn
    global SAM_KHUNG; SAM_KHUNG = dict(CQ=CQ, C=C)
    fs = sorted(glob.glob(os.path.join(thu, "m_*.npz"))); T = []; RQ = []; JP = []
    for p_ in fs:
        i = int(p_[-8:-4]); t = i / 30.0
        if t < t0 - 0.1 or t > t1 + 0.1: continue
        d = np.load(p_); T.append(t); JP.append([CQ @ V((F @ d["J"][k]).tolist()) for k in range(nJ)])
        RQ.append([(CQ @ mathutils.Matrix(d["R"][k].tolist()) @ C.transposed()).to_quaternion() for k in range(nJ)])
    for k in range(nJ):   # liền mạch dấu quaternion theo thời gian
        for i in range(1, len(RQ)):
            if RQ[i][k].dot(RQ[i - 1][k]) < 0: RQ[i][k] = -RQ[i][k]
    global SAM_GLITCH, SAM_ANH2D, SAM_KEP_TAY; SAM_GLITCH = []; SAM_ANH2D = None; SAM_KEP_TAY = None
    PRO = nap_motion_profile()
    if not os.environ.get("THU_KHONG_SUA_GLITCH"):   # SỬA GLITCH NGUỒN (audit 23/10: khung 59–62 chân nhảy 587/357 mm rồi quay lại ⇒ chân bay 492 mm sát đất)
        T, JP, RQ, SAM_GLITCH = sua_glitch_nguon(T, JP, RQ, nJ, PRO["glitch"], json.load(open(os.path.join(thu, "khop_mhr.json"))).get("cha"))
        if SAM_GLITCH: print("GLITCH_SUA (khung nguồn nội suy lại):", SAM_GLITCH)
    # LÀM MƯỢT NGUỒN (P1-k 24/10, Boss lần 3 «vẫn còn giật nhẹ lúc phóng lao»): đo toàn thân so với nguồn ⇒ thân trên ra = nguồn tới 0,25°/khung²,
    # hông XY ra = nguồn từng khung (115,6 mm/khung² @47 · 132,6 @50 ≈ 7–8 g — nhiễu dịch chuyển GVHMR) ⇒ giật nằm Ở NGUỒN. Lọc one-euro (Casiez 2012)
    # hai chiều (không trễ pha) trên vị trí khớp và xoay khớp TRƯỚC retarget: cắt thấp lúc chậm, mở lúc nhanh ⇒ đỉnh tốc độ tay lúc phóng giữ nguyên
    # (nghiệm thu: v tay cổ tay lúc phóng trước/sau, in bên dưới). Tham số: motion_profile.lam_muot_nguon. Thử ngược: THU_KHONG_LAM_MUOT_NGUON=1.
    def _v_tay_max(JP_):
        return max(((JP_[i + 1][ix[w]] - JP_[i - 1][ix[w]]).length * 15.0, i, w) for i in range(1, len(JP_) - 1) for w in ("l_wrist", "r_wrist"))
    def _hong_acc_max(JP_):
        return max(((JP_[i + 1][ix["root"]] - 2 * JP_[i][ix["root"]] + JP_[i - 1][ix["root"]]).xy.length * 1000 * (24.0 / 30.0) ** 2, i) for i in range(1, len(JP_) - 1))
    if not os.environ.get("THU_KHONG_LAM_MUOT_NGUON") and os.environ.get("LAM_MUOT_NGUON", "1") != "0" and (PRO.get("lam_muot_nguon", {}).get("bat", 0) or os.environ.get("LAM_MUOT_NGUON")):   # mặc định TẮT (24/10): bật đổi cửa sổ chạm (R 50–54 mới) ⇒ 24 fixture sam phải đo lại; LAM_MUOT_NGUON=1 để bật
        LM = PRO["lam_muot_nguon"]; v0 = _v_tay_max(JP); h0 = _hong_acc_max(JP)
        _quang = lambda JP_: max((JP_[i][ix["root"]] - JP_[0][ix["root"]]).xy.length for i in range(len(JP_)))   # tầm lao của hông (XY xa nhất so với khung đầu)
        q0 = _quang(JP); JP, RQ = lam_muot_nguon(JP, RQ, nJ, LM, ix["root"]); v1 = _v_tay_max(JP); h1 = _hong_acc_max(JP); q1 = _quang(JP)
        print("LAM_MUOT_NGUON (one-euro 2 chiều): v tay max %.2f → %.2f m/s (khung nguồn %d → %d, %s) · hông XY gia tốc max %.1f → %.1f mm/khung²(24fps) @%d → @%d · giữ đỉnh %.0f %% · tầm lao hông %.3f → %.3f m (giữ %.1f %%)"
              % (v0[0], v1[0], v0[1], v1[1], v1[2], h0[0], h1[0], h0[1], h1[1], 100 * v1[0] / max(1e-6, v0[0]), q0, q1, 100 * q1 / max(1e-6, q0)))
        if v1[0] < LM["giu_dinh_toi_thieu"] * v0[0]: raise SystemExit("⛔ LAM_MUOT_NGUON nuốt đỉnh tốc độ tay (%.2f < %.2f × %.2f) — hạ beta/nâng min_cutoff trong profile" % (v1[0], LM["giu_dinh_toi_thieu"], v0[0]))
        if abs(q1 - q0) > LM["lech_tam_lao_toi_da"] * q0: raise SystemExit("⛔ LAM_MUOT_NGUON đổi tầm lao hông quá %.0f %% (%.3f → %.3f m) — lọc gốc quá mạnh" % (100 * LM["lech_tam_lao_toi_da"], q0, q1))
    if int(os.environ.get("SAM_LOC", "1")) > 1:   # (tắt mặc định: bản lọc làm trượt chân 710 mm — chưa tìm lỗi) LỌC RUNG (chuẩn dọn mocap): trung bình quaternion 3 khung nguồn — cổ tay SAM rung ⇒ lưỡi rìu giật 50°/frames
        h_ = int(os.environ.get("SAM_LOC", "1")) // 2; RQ0 = [list(r) for r in RQ]
        for i in range(len(RQ)):
            for k in range(nJ):
                acc = mathutils.Vector((0, 0, 0, 0))
                for j in range(max(0, i - h_), min(len(RQ), i + h_ + 1)): acc += mathutils.Vector(RQ0[j][k])
                RQ[i][k] = mathutils.Quaternion(acc.normalized())
    N = int(round((T[-1] - T[0]) * FPS)) if t1 >= T[-1] else int(round((t1 - t0) * FPS)) + 1
    N = min(N, int((T[-1] - t0) * FPS))
    def lay(t):
        i = max(0, min(len(T) - 2, max((k for k in range(len(T)) if T[k] <= t), default=0))); u = max(0.0, min(1.0, (t - T[i]) / (T[i + 1] - T[i])))
        return [RQ[i][k].slerp(RQ[i + 1][k], u) for k in range(nJ)], [JP[i][k].lerp(JP[i + 1][k], u) for k in range(nJ)]
    # hướng mặt trung bình → −Y (Y = xoay quanh Z)
    lat = V()
    for jp in JP: l_ = jp[ix["l_upleg"]] - jp[ix["r_upleg"]]; l_.z = 0; lat += l_
    Y = mathutils.Matrix.Rotation(-math.atan2(lat.y, lat.x), 3, "Z"); SAM_KHUNG["Y"] = Y
    CAN_T_ = [(f_["t"], V(f_["can"])) for f_ in (json.load(open(os.path.join(thu, "sam3d_mp.json")))["frames"] if os.path.exists(os.path.join(thu, "sam3d_mp.json")) else []) if f_.get("can")]
    SAM_KHUNG["can"] = CAN_T_   # trục rìu đo từ video (khung cv) — đổi sang Blender: Y·CQ·F
    # hiệu chỉnh 1 lần ở tư thế bind
    OFF = {}
    for b, (jr, ja, jb) in SAM_MAP.items():
        if b not in rig.data.bones: continue
        Rb = rig.data.bones[b].matrix_local.to_3x3(); dr = (rig.data.bones[b].tail_local - rig.data.bones[b].head_local).normalized()
        ds = (C @ V((Pb[ix[jb]] - Pb[ix[ja]]).tolist())).normalized()
        if b == "head": ds = (C @ V((Pb[ix["c_head"]] - Pb[ix["c_neck"]]).tolist())).normalized()
        # THÂN (Boss 22/10 «lúc chặt cây cái lưng của settler bị cong dữ vậy»): cột sống settler nghỉ THẲNG ⇒ hiệu chỉnh hips/spine/chest theo TRỤC THÂN
        # chung (chậu→cổ). Theo từng đoạn: SMPL-X spine2→spine3 chỉ 5,2 cm, nghiêng sẵn 30° ⇒ lưng dưới khoá gập +30°, ngực ngửa −36° bù (lưng gù chữ S)
        if b in ("hips", "spine", "chest") and os.environ.get("THAN_THEO_TRUC", "1") == "1": ds = (C @ V((Pb[ix["c_neck"]] - Pb[ix["root"]]).tolist())).normalized()
        Mm = dr.rotation_difference(ds).to_matrix() @ Rb; Gbb = C @ mathutils.Matrix(Gb[ix[jr]].tolist()) @ C.transposed()
        OFF[b] = Gbb.transposed() @ Mm
    # chiều dài chân (tỉ lệ vị trí hông)
    Ls = (JP[0][ix["l_upleg"]] - JP[0][ix["l_lowleg"]]).length + (JP[0][ix["l_lowleg"]] - JP[0][ix["l_foot"]]).length
    Lt = (K["hong_L"] - K["goi_L"]).length + (K["goi_L"] - K["co_chan_L"]).length; kk = Lt / Ls
    nen = min(min(jp[ix["l_foot"]].z, jp[ix["r_foot"]].z) for jp in JP)
    # MẶC ĐỊNH (Boss 23/10/2026 «đưa vào»): mặt đất = bách phân vị 25 chân thấp nhất mỗi khung — GVHMR có khung chân lún ±10 cm ⇒ min kéo lệch
    # cả clip (LTX v4 lơ lửng 10 cm). NEN_PCT=0 = hành vi cũ (min tuyệt đối) để thử ngược.
    NEN_PCT_ = float(os.environ.get("NEN_PCT", PRO["nen_pct"]))
    if NEN_PCT_ > 0:
        import numpy as _np; nen = float(_np.percentile([min(jp[ix["l_foot"]].z, jp[ix["r_foot"]].z) for jp in JP], NEN_PCT_))
    sc = bpy.context.scene; W = rig.matrix_world
    for pb_ in rig.pose.bones:
        for c in pb_.constraints: c.mute = True
    thu_tu = ["hips", "spine", "chest", "neck", "head"] + [f"{x}_{B}" for B in "LR" for x in ("clavicle", "upperarm", "forearm", "hand", "thigh", "shin", "foot")]
    vet = {"L": [], "R": []}; r0 = None; global SAM_NGUON; SAM_NGUON = []; huong_fk = {"L": [], "R": []}; huong_hong = []; NGUON_POSE.clear(); NGUON_VT.clear()
    LB_TAY = {}; KEP_TAY = {}   # nhãn lòng bàn tay từ lưới con của rig (cùng nguồn với cửa ⑭b ở animate.py)
    try:
        import sys as _sys; _sys.path.insert(0, os.path.expanduser("~/.hermes/skills/creative/las-physics/scripts")); import shatter as _VO
        _luoi = [o for o in bpy.data.objects if o.type == "MESH" and o.parent == rig]
        LB_TAY = {B: _VO.long_ban_tay(rig, _luoi, B)["phap_tuyen"] for B in "LR"}
    except Exception as e_: print(f"⛔ KEP_CO_TAY BỎ QUA: không lấy được nhãn lòng bàn tay ({e_.__class__.__name__}: {e_}) ⇒ cổ tay KHÔNG được kẹp (cửa ⑭b sẽ đo)"); LB_TAY = {}
    SAM_KEP_TAY = bool(LB_TAY) and not os.environ.get("THU_KHONG_KEP_CO_TAY")
    for f in range(N + 1):
        sc.frame_set(f); bpy.context.view_layer.update(); q, jp = lay(t0 + f / FPS); SAM_NGUON.append((q, jp))
        r_ = Y @ jp[ix["root"]]; r0 = r0 or r_.copy()
        for b in thu_tu:
            if b not in OFF: continue
            qj = q[ix[SAM_MAP[b][0]]]
            if b.startswith("forearm_"):   # MHR để xoắn cẳng tay ở wrist_twist ⇒ cẳng tay settler nhận 50 % (lowarm→wrist_twist); không chia ⇒ cổ tay xoắn 80° so cẳng
                jt = ix[("l" if b.endswith("L") else "r") + "_wrist_twist"]; jl = ix[SAM_MAP[b][0]]
                rb = (C @ mathutils.Matrix(Gb[jl].tolist()) @ C.transposed()).to_quaternion().inverted() @ (C @ mathutils.Matrix(Gb[jt].tolist()) @ C.transposed()).to_quaternion()
                dl_ = (qj.inverted() @ q[jt]) @ rb.inverted()   # phần xoắn ĐỔI so với bind (trộn thẳng xoay toàn cục ⇒ cộng cả lệch bind, cẳng lệch +40–62°)
                if dl_.w < 0: dl_ = -dl_
                qj = qj @ mathutils.Quaternion().slerp(dl_, float(os.environ.get("CANG_XOAN", "0.5")))
            pb = rig.pose.bones[b]; M = Y @ qj.to_matrix() @ OFF[b]
            m = (W.inverted().to_3x3() @ M).to_4x4(); m.translation = pb.matrix.translation
            if b == "hips":
                h0 = rig.data.bones["hips"].head_local
                m.translation = V((h0.x + (r_.x - r0.x) * kk, h0.y + (r_.y - r0.y) * kk, K["co_chan_L"].z + (jp[ix["root"]].z - nen) * kk))
            pb.matrix = m; bpy.context.view_layer.update()
            if b != "hips": pb.location = (0, 0, 0)
            pb.keyframe_insert("rotation_quaternion", frame=f)
            if b == "hips": pb.keyframe_insert("location", frame=f)
        ghi_nguon_pose(rig, f)   # P1-k: mốc nguồn (sau chép góc, trước mọi chỉnh sửa)
        # TỈ LỆ: chép góc thì tay settler (vai rộng hơn so với tay) TÁCH nhau dù góc đúng ⇒ đích cổ tay = giữa vai settler + (giữa vai→cổ tay nguồn) × tỉ lệ dài tay;
        # giải 2 đoạn, khuỷu theo hướng khuỷu SAM; bắp/cẳng tay chỉ BẺ HƯỚNG từ tư thế SAM (giữ nguyên xoắn), bàn tay giữ nguyên xoay cổ tay SAM
        if os.environ.get("SAM_TAY_TL", "1") == "1":
            Pb_ = rig.pose.bones; vs_ = (Y @ jp[ix["l_uparm"]] + Y @ jp[ix["r_uparm"]]) / 2; vt_ = ((W @ Pb_["upperarm_L"].head) + (W @ Pb_["upperarm_R"].head)) / 2
            for B, s_ in (("L", "l"), ("R", "r")):
                pu, pf, ph = Pb_[f"upperarm_{B}"], Pb_[f"forearm_{B}"], Pb_[f"hand_{B}"]; Mh = (W @ ph.matrix).copy()
                Lu = rig.data.bones[f"upperarm_{B}"].length; Lf = rig.data.bones[f"forearm_{B}"].length
                Ls_ = (jp[ix[f"{s_}_lowarm"]] - jp[ix[f"{s_}_uparm"]]).length + (jp[ix[f"{s_}_wrist"]] - jp[ix[f"{s_}_lowarm"]]).length
                Wt = vt_ + (Y @ jp[ix[f"{s_}_wrist"]] - vs_) * ((Lu + Lf) / Ls_)
                S_ = W @ pu.head; dv = Wt - S_; dl = min(dv.length, Lu + Lf - 1e-4); u = dv.normalized()
                a_ = (Lu * Lu - Lf * Lf + dl * dl) / (2 * dl); r_ = math.sqrt(max(0.0, Lu * Lu - a_ * a_)); C_ = S_ + u * a_
                Es = Y @ jp[ix[f"{s_}_lowarm"]] - Y @ jp[ix[f"{s_}_uparm"]]; v_ = Es - u * Es.dot(u); v_ = v_.normalized() if v_.length > 1e-5 else u.orthogonal().normalized()
                E_ = C_ + v_ * r_
                for pb_, d_ in ((pu, E_ - S_), (pf, (S_ + u * dl) - E_)):
                    M0 = (W @ pb_.matrix).to_3x3().normalized(); q_ = M0.col[1].rotation_difference(d_.normalized())
                    m = (W.inverted().to_3x3() @ (q_.to_matrix() @ M0)).to_4x4(); m.translation = pb_.matrix.translation; pb_.matrix = m; bpy.context.view_layer.update()
                    pb_.keyframe_insert("rotation_quaternion", frame=f)
                mh_ = (W.inverted().to_3x3() @ Mh.to_3x3().normalized()).to_4x4(); mh_.translation = ph.matrix.translation; ph.matrix = mh_; bpy.context.view_layer.update()   # CHỈ khôi phục XOAY (gán cả ma trận ⇒ bàn tay bị kéo về cổ tay cũ, tách khỏi cẳng tay); ph.keyframe_insert("rotation_quaternion", frame=f)
        if LB_TAY and not os.environ.get("THU_KHONG_KEP_CO_TAY"):   # ⑭/⑭b: cổ tay SAM/GVHMR không tin được ⇒ kẹp về biên độ giải phẫu (co_tay trong motion_profile)
            for B in "LR":
                g_ = kep_co_tay_sam(rig, B, LB_TAY[B], CO_TAY_ROM, PRO["co_tay"]["tong_toi_da_deg"], f)
                if g_ < 1.0: KEP_TAY[B] = KEP_TAY.get(B, 0) + 1
        for B in "LR":
            vet[B].append((W @ rig.pose.bones[f"shin_{B}"].tail).copy())
            pf_ = rig.pose.bones[f"foot_{B}"]; huong_fk[B].append(((W @ pf_.tail) - (W @ pf_.head)).normalized())
        hh_ = ((W @ rig.pose.bones["thigh_L"].head) - (W @ rig.pose.bones["thigh_R"].head)).cross(V((0, 0, 1))); hh_.z = 0; huong_hong.append(hh_.normalized() if hh_.length > 1e-6 else V((0, -1, 0)))   # hướng hông (cửa ⑪ đo vậy)
    for pb_ in rig.pose.bones:
        for c in pb_.constraints: c.mute = False
    # ---------------------------------------------------------------- CHÂN + HÔNG: BỘ CHẠM ĐẤT (P1 23/10/2026)
    # Boss 23/10: «trượt lên trượt xuống… rung rung» — bản cũ: ghim theo TRUNG VỊ cả đoạn chạm (chân nguồn trôi trong đoạn ⇒ ghim sai),
    # chân nguồn DƯỚI nền mà đang di chuyển bị kẹp lên đúng nền ⇒ trượt 422 mm; hông hạ TỪNG KHUNG (vòng `ho` 3 lượt) ⇒ rung.
    # Nay (ý tưởng từ mixamo-llm-mocap/retarget_smplx.py, MIT — chỉ port LOGIC, ngưỡng ở assets/motion_profile.json):
    #  ① chạm = nhiều bằng chứng + TRỄ (vào: thấp VÀ chậm; ở lại: chưa cao VÀ chưa nhanh; ảnh 2D MediaPipe đứng yên ⇒ chạm dù 3D trôi) + đoạn ≥ N khung
    #  ② neo = vị trí chân ở KHUNG ĐẦU đoạn chạm (trung vị 3 khung đầu), giữ suốt đoạn; nguồn trôi > troi_cat_m hoặc xoay > xoay_cat_deg ⇒ cắt, neo mới
    #  ③ chân lơ lửng trong đoạn chạm ⇒ hạ xuống nền (≤ ha_moi_khung_m/frames); chân TỰ DO không dưới nền (+ bay_ho_m để chân đang bay không bị đếm là chạm);
    #     pha bay (hai chân rời đất) giữ nguyên
    #  ④ hông: hạ theo ĐƯỜNG CONG MƯỢT (max chạy cửa sổ ≥ 9 khung + gaussian), tối đa ha_toi_da_m, KHÔNG từng khung
    #  ⑤ IK 2 đoạn giữ nguyên; hướng bàn chân trong đoạn chạm = yaw NEO (trung vị yaw nguồn, kẹp ±mui_lech_max_deg quanh hướng hông) ⇒ hết xoay vào
    # Thử ngược: THU_KHONG_HYSTERESIS=1 (một ngưỡng + neo trung vị, như bản cũ) · THU_HONG_TUNG_FRAME=1 (hông hạ từng khung) · THU_PHANG_0 (phẳng = 0°).
    CH = PRO["cham"]; HG = PRO["hong"]; KHUNG = {}; HUONG = {}
    anh = None if os.environ.get("THU_KHONG_ANH2D") else anh_chan_dung_yen(thu, t0, N, Lt, CH); SAM_ANH2D = anh is not None   # THU_KHONG_ANH2D=1: thử ngược không bằng chứng ảnh
    for B in "LR":
        z0 = K[f"co_chan_{B}"].z; P_ = vet[B]; n_ = len(P_); bn = rig.data.bones[f"ik_{B}"]; d0 = (bn.tail_local - bn.head_local).normalized()
        L_chan = (bn.tail_local - bn.head_local).length; Rl = bn.matrix_local.to_3x3(); ng0 = math.hypot(d0.x, d0.y)
        yaw_src = [math.atan2(D.y, D.x) for D in huong_fk[B]]
        if os.environ.get("KHOA_CA_CLIP") or khoa == "ca_clip":
            xs = sorted(v.x for v in P_); ys = sorted(v.y for v in P_); m_ = n_ // 2; tb = V((xs[m_], ys[m_], z0)); dich = [tb] * n_
            doan = [(0, n_ - 1, tb, None)]; trong = [True] * n_
        else:
            doan, trong = doan_cham(P_, z0, anh[B] if anh else None, yaw_src, huong_hong, CH)
            dich = dich_chan(P_, z0, doan, trong, CH)
        KHUNG[B] = dict(doan=[(a_, b_) for a_, b_, _, _ in doan], phu=round(100 * sum(trong) / n_, 1), neo={a_: neo for a_, b_, neo, _ in doan}, yaw={a_: y_ for a_, b_, _, y_ in doan})
        v_out = [((dich[f] - dich[f - 1]).length * FPS if f > 0 else 0.0) for f in range(n_)]   # P1-l: ĐÚNG công thức cửa ㉓ (bước lùi) — sai phân giữa phẳng hoá 1 khung lẻ (R41: 0,34 ⇒ snap −36 → −22 → −38 = 29,3°)
        for f in range(n_):
            dat_ik(rig, B, dich[f], 0.0, f, K[f"mui_chan_{B}"])
            D = huong_fk[B][f].copy()
            # «phẳng» = ĐỘ DỐC NGHỈ (cổ chân 8,5 cm → mũi sát đất), KHÔNG phải 0° — Boss 23/10: «Sao bàn chân ko chạm đất hoàn toàn mà
            # mũi chân chỉa lên vậy». Phẳng khi: trong đoạn chạm (yaw = neo) HOẶC chân thấp & chậm (đúng điều kiện cửa ㉓).
            neo_yaw = next((y_ for a_, b_, _, y_ in doan if a_ <= f <= b_), None)
            if trong[f] and neo_yaw is not None: D = V((math.cos(neo_yaw) * ng0, math.sin(neo_yaw) * ng0, d0.z))
            elif trong[f] or (dich[f].z - z0 <= CH["phang_cao_m"] and v_out[f] < CH["phang_v_mps"]):
                ng = math.hypot(D.x, D.y) or 1.0; D = V((D.x / ng * ng0, D.y / ng * ng0, d0.z))
            if os.environ.get("THU_PHANG_0") and trong[f]: D = V((D.x, D.y, 0.0)).normalized()
            zm0 = K[f"mui_chan_{B}"].z; mui_z = dich[f].z + D.normalized().z * L_chan
            if mui_z < zm0 - 0.005 and not trong[f]:   # chân TỰ DO: mũi xuyên đất ⇒ NÂNG bàn chân, giữ dốc (bẻ dốc ở đây = rung 40°/khung² @R50, P1-h)
                dich[f] = V((dich[f].x, dich[f].y, dich[f].z + (zm0 - 0.005 - mui_z))); dat_ik(rig, B, dich[f], 0.0, f, K[f"mui_chan_{B}"]); mui_z = zm0 - 0.005
            if mui_z < zm0 - 0.005:   # chân đứng: mũi xuyên đất ⇒ hạ dốc vừa đủ cho mũi chạm nền
                ng = math.hypot(D.x, D.y) or 1.0; dz = max(-1.0, min(1.0, (zm0 - dich[f].z) / L_chan)); r_ = math.sqrt(max(0.0, 1 - dz * dz)); D = V((D.x / ng * r_, D.y / ng * r_, dz))
            q = d0.rotation_difference(D.normalized()); pb_ = rig.pose.bones[f"ik_{B}"]
            pb_.rotation_quaternion = (Rl.inverted() @ q.to_matrix() @ Rl).to_quaternion(); pb_.keyframe_insert("rotation_quaternion", frame=f)
            if os.environ.get("CHAM_DAT_DUMP"):
                sc.frame_set(f); bpy.context.view_layer.update(); pfb = rig.pose.bones[f"foot_{B}"]; dfb = (W @ pfb.tail) - (W @ pfb.head); dfb.z = 0
                a2 = (W @ Pb_[f"shin_{B}"].head) - (W @ Pb_[f"shin_{B}"].tail) if (Pb_ := rig.pose.bones) else None; c2 = (W @ pfb.tail) - (W @ pfb.head); th2 = (W @ Pb_[f"thigh_{B}"].tail) - (W @ Pb_[f"thigh_{B}"].head); n2 = th2.cross(-a2)
                HUONG.setdefault(B, []).append([round((W @ pfb.head).z - z0, 3), round(math.degrees(dfb.angle(huong_hong[f])), 1) if dfb.length > 1e-4 else None, bool(trong[f]),
                                                round(math.degrees(a2.angle(c2)), 1), round(abs(90 - math.degrees(n2.normalized().angle(c2.normalized()))), 1) if n2.length > 1e-6 else None, round(math.degrees(th2.angle(-a2)), 1), round(math.degrees(D.normalized().angle(a2.normalized())), 1)])
        KHUNG[B]["dich"] = dich
    if SAM_KEP_TAY: print("KEP_CO_TAY (khung cổ tay bị co về biên độ):", KEP_TAY)
    print("CHAM_DAT", {B: KHUNG[B]["doan"] for B in "LR"}, "phủ", {B: KHUNG[B]["phu"] for B in "LR"}, "ảnh2D", "có" if anh else "không")
    if os.environ.get("CHAM_DAT_DUMP"):   # chẩn đoán: từng khung cổ chân nguồn (FK) · đích · trong đoạn · ảnh 2D yên
        json.dump({B: dict(doan=KHUNG[B]["doan"], nguon=[list(p) for p in vet[B]], dich=[list(p) for p in KHUNG[B]["dich"]], yen=(anh[B] if anh else None), z0=K[f"co_chan_{B}"].z, huong=HUONG.get(B)) for B in "LR"}, open(os.environ["CHAM_DAT_DUMP"], "w"))
    # HÔNG: đường cong hạ mượt (④). Đo hạ cần từng khung (hông → đích cổ chân vượt tầm chân), rồi max chạy + gaussian, kẹp ha_toi_da_m.
    pb = rig.pose.bones["hips"]; ha_can = []; L_voi = Lt * HG["voi_ti_le"]
    for f in range(N + 1):
        sc.frame_set(f); bpy.context.view_layer.update(); d_ = 0.0
        for B in "LR":
            hip = W @ rig.pose.bones[f"thigh_{B}"].head; t_ = KHUNG[B]["dich"][f]; dxy = math.hypot(hip.x - t_.x, hip.y - t_.y)
            d_ = max(d_, hip.z - t_.z - math.sqrt(max(0.0, L_voi * L_voi - dxy * dxy)))
        ha_can.append(max(0.0, d_))
    if os.environ.get("THU_HONG_KHONG_HA"): HG = dict(HG, ha_toi_da_m=0.0)   # thử ngược: không hạ hông ⇒ chân sau lao không với tới ⇒ ⑬/13b
    ha = ha_can if os.environ.get("THU_HONG_TUNG_FRAME") else hong_muot(ha_can, HG)
    for f in range(N + 1):
        if ha[f] <= 0.0005: continue
        sc.frame_set(f); bpy.context.view_layer.update(); m = pb.matrix.copy(); m.translation.z -= ha[f]; pb.matrix = m; bpy.context.view_layer.update(); pb.keyframe_insert("location", frame=f)
    print("HONG_HA mm: cần max %.0f · áp max %.0f · kẹp %s · khung cần > kẹp: %s" % (max(ha_can) * 1000, max(ha) * 1000, "có" if max(ha_can) > HG["ha_toi_da_m"] else "không", [(f, round(x * 1000)) for f, x in enumerate(ha_can) if x > HG["ha_toi_da_m"]][:20]))
    # NHÓN GÓT (③ của mixamo-llm-mocap: «set the hovering foot down with its own leg», hông chỉ hạ ≤ ha_toi_da_m): khung đứng mà neo vẫn ngoài tầm sau khi
    # hạ hông ⇒ MŨI giữ ở neo, gót nhấc đúng phần thiếu (chân sau lúc lao đứng trên mũi — đúng giải phẫu, cẳng ngả không ép bàn chân gập mu quá biên).
    # Không nhón ⇒ IK kéo căng chân, bàn chân rời neo (⑬ 46° / 13b 41° đo 23/10). Thử ngược: THU_KHONG_NHON=1.
    nhon_ = {}
    if not os.environ.get("THU_KHONG_NHON"):
        for f in range(N + 1):
            thieu = ha_can[f] - ha[f]
            if thieu <= 0.002: continue
            sc.frame_set(f); bpy.context.view_layer.update(); d_ = {}
            for B in "LR":
                if not any(a_ <= f <= b_ for a_, b_ in KHUNG[B]["doan"]): continue
                hip = W @ rig.pose.bones[f"thigh_{B}"].head; t_ = KHUNG[B]["dich"][f]; dxy = math.hypot(hip.x - t_.x, hip.y - t_.y)
                d_[B] = max(0.0, hip.z - t_.z - math.sqrt(max(0.0, L_voi * L_voi - dxy * dxy)))
            for B, dz in d_.items():
                if dz <= 0.002: continue
                bn = rig.data.bones[f"ik_{B}"]; d0 = (bn.tail_local - bn.head_local).normalized(); L_chan = (bn.tail_local - bn.head_local).length; Rl = bn.matrix_local.to_3x3()
                pb_ = rig.pose.bones[f"ik_{B}"]; D = (Rl @ pb_.rotation_quaternion.to_matrix() @ Rl.inverted()) @ d0; D = D.normalized()
                mui = KHUNG[B]["dich"][f] + D * L_chan; zn = max(-1.0, D.z - dz / L_chan); r_ = math.sqrt(max(0.0, 1 - zn * zn)); ng = math.hypot(D.x, D.y) or 1.0
                Dn = V((D.x / ng * r_, D.y / ng * r_, zn)); t_moi = mui - Dn * L_chan
                dat_ik(rig, B, t_moi, 0.0, f, K[f"mui_chan_{B}"]); q = d0.rotation_difference(Dn); pb_.rotation_quaternion = (Rl.inverted() @ q.to_matrix() @ Rl).to_quaternion(); pb_.keyframe_insert("rotation_quaternion", frame=f)
                nhon_[B] = nhon_.get(B, 0) + 1
        if nhon_: print("NHON_GOT (khung đứng nhón gót vì neo ngoài tầm sau khi hạ hông ≤ kẹp):", nhon_)
    # BIÊN ĐỘ CỔ CHÂN — HẬU KỲ, sau khi hạ hông + nhón (đo 23/10: mặt phẳng đùi–cẳng của chân gần thẳng (gối 14–27°) xoay mạnh khi hông dời
    # vài cm ⇒ kẹp TRƯỚC khi hạ hông đo D·n = 0,27 còn cửa đo 0,61; chân sau lao: hạ hông ⇒ gối gập 37° ⇒ bàn chân phẳng gập mu 46°).
    # Đúng công thức cửa ⑬/13b trên tư thế CUỐI: chân đứng gập mu quá biên ⇒ NHÓN GÓT quanh mũi; chân tự do ⇒ xoay D ra khỏi cẳng tới biên,
    # và ép D về trong mặt phẳng chân (≤ ban_chan_vat_max_deg) khi gối gập rõ. Thử ngược: THU_KHONG_KEP_CHAN=1.
    if not os.environ.get("THU_KHONG_KEP_CHAN"):
        kep_ = {}
        # lượt KHÔ: góc nhón CẦN từng khung đứng (bàn chân phẳng so với cẳng sau khi hạ hông), rồi làm mượt theo đoạn
        NHON_MUOT = {}; D_CUOI = {}; D_TRUOC = {}; T_CUOI = {}; DOC2 = {}; KEP_DANG = {}; Q_CUOI = {}
        for B in "LR":
            bn = rig.data.bones[f"ik_{B}"]; d0 = (bn.tail_local - bn.head_local).normalized(); Rl = bn.matrix_local.to_3x3(); L_chan = (bn.tail_local - bn.head_local).length; can = [0.0] * (N + 1); lim = math.radians(CH["co_chan_gap_min_deg"])
            for a0, b0 in KHUNG[B]["doan"]:
                for f in range(a0, b0 + 1):
                    # lặp tới góc nhón HỘI TỤ (nâng cổ chân ⇒ IK giải lại ⇒ cẳng ngả theo ⇒ một lần áp chỉ được 20–50 %), rồi TRẢ LẠI key gốc — chỉ ghi nhận góc cần
                    sc.frame_set(f); bpy.context.view_layer.update(); Pb_ = rig.pose.bones; pb_ = Pb_[f"ik_{B}"]; q_goc = pb_.rotation_quaternion.copy(); t_goc = KHUNG[B]["dich"][f].copy()
                    D = ((Rl @ q_goc.to_matrix() @ Rl.inverted()) @ d0).normalized(); t_ = t_goc.copy(); tong = 0.0
                    for _lan in range(8):
                        a_ = ((W @ Pb_[f"shin_{B}"].head) - (W @ Pb_[f"shin_{B}"].tail)).normalized(); th2 = lim - D.angle(a_)
                        if th2 <= 1e-3: break
                        tong += th2; mui = t_ + D * L_chan; ben = V((0, 0, 1)).cross(V((D.x, D.y, 0)).normalized()); Dn = mathutils.Matrix.Rotation(th2, 3, ben) @ D
                        if Dn.z > D.z: Dn = mathutils.Matrix.Rotation(-th2, 3, ben) @ D
                        D = Dn.normalized(); t_ = mui - D * L_chan; dat_ik(rig, B, t_, 0.0, f, K[f"mui_chan_{B}"])
                        q = d0.rotation_difference(D); pb_.rotation_quaternion = (Rl.inverted() @ q.to_matrix() @ Rl).to_quaternion(); pb_.keyframe_insert("rotation_quaternion", frame=f); sc.frame_set(f); bpy.context.view_layer.update()
                    can[f] = tong
                    if f == b0 and b0 < N and not os.environ.get("THU_KHONG_NHON_DOAN_TRUOC"):
                        # P1-p ĐOÁN TRƯỚC CUỐI ĐOẠN: ⑬ ở khung tự do ĐẦU (cẳng đã vung sau phóng) đòi bàn chân kéo lê chúc −80° ngay lập tức (P1-o: dư 74° @R54, 50° @R79 —
                        # vô nghiệm với kẹp gia tốc). Nay: tính góc nhón CẦN th_req để ⑬ ≥ lim với cẳng của khung b0+1 ĐÚNG như sẽ bake (cổ chân khung đầu rời đoạn nằm
                        # cách cổ chân đứng ≤ 0,9·60 mm — bước đầu của đường rời), rồi RAMP nhón trong các khung đứng cuối: can[b0−j] ≥ th_req − (j+1)·gh (mũi vẫn neo ⇒
                        # ① sạch; mũi dưới đất ⇒ không lơ lửng). Khung tự do đầu chỉ còn ≤ gh phải xoay. Thử ngược: THU_KHONG_NHON_DOAN_TRUOC=1.
                        pb1 = Pb_[f"ik_{B}"]; sc.frame_set(f + 1); bpy.context.view_layer.update(); q1_luu = pb1.rotation_quaternion.copy(); t1 = KHUNG[B]["dich"][f + 1].copy()
                        dv_ = t1 - t_goc; buoc = CHAN_RUNG_MAX_MM / 1000.0 * JITTER_SOLVE_FRACTION; t1b = t_goc + dv_ * (buoc / dv_.length) if dv_.length > buoc else t1
                        dat_ik(rig, B, t1b, 0.0, f + 1, K[f"mui_chan_{B}"]); sc.frame_set(f + 1); bpy.context.view_layer.update(); a_n = ((W @ Pb_[f"shin_{B}"].head) - (W @ Pb_[f"shin_{B}"].tail)).normalized()
                        dat_ik(rig, B, t1, 0.0, f + 1, K[f"mui_chan_{B}"]); pb1.rotation_quaternion = q1_luu; pb1.keyframe_insert("rotation_quaternion", frame=f + 1)   # trả lại key lượt 1
                        ben0 = V((0, 0, 1)).cross(V((D.x, D.y, 0)).normalized())
                        def _nang(th):
                            Dn_ = mathutils.Matrix.Rotation(th, 3, ben0) @ D
                            if Dn_.z > D.z: Dn_ = mathutils.Matrix.Rotation(-th, 3, ben0) @ D
                            return Dn_.normalized()
                        th_req = 0.0
                        if _nang(0.0).angle(a_n) < lim - 1e-3:
                            lo_, hi_ = 0.0, math.radians(85.0)
                            for _ in range(20):
                                m_ = (lo_ + hi_) / 2
                                if _nang(m_).angle(a_n) >= lim: hi_ = m_
                                else: lo_ = m_
                            th_req = hi_
                        gh_r = math.radians(CHAN_RUNG_MAX_DEG * JITTER_SOLVE_FRACTION)
                        for j in range(0, 8):
                            ff = f - j; muc = th_req - (j + 1) * gh_r
                            if ff < a0 or muc <= 0: break
                            can[ff] = max(can[ff], muc)
                        if os.environ.get("EXIT_PITCH_DEBUG"): print("NHON_TRUOC", B, "b0", f, "th_req_deg", round(math.degrees(th_req), 1), "ramp", [(f - j, round(math.degrees(can[f - j]), 1)) for j in range(0, 6) if f - j >= a0])
                        sc.frame_set(f); bpy.context.view_layer.update()
                    if tong > 0: dat_ik(rig, B, t_goc, 0.0, f, K[f"mui_chan_{B}"]); pb_.rotation_quaternion = q_goc; pb_.keyframe_insert("rotation_quaternion", frame=f); KHUNG[B]["dich"][f] = t_goc
            muot = list(can)
            if not os.environ.get("THU_NHON_TUNG_KHUNG"):
                r_ = int(CH["nhon_lam_muot_khung"]); minr = math.radians(CH["nhon_got_toi_thieu_deg"])
                for a0, b0 in KHUNG[B]["doan"]:
                    for f in range(a0, b0 + 1):
                        m_ = max(can[max(a0, f - r_):min(b0, f + r_) + 1]); muot[f] = max(m_, minr) if m_ > 1e-4 else 0.0
                    for f in range(a0 + 1, b0 + 1):   # P1-k: nhón không được RƠI về phẳng trong r_ khung cuối đoạn (max chạy cắt ở biên ⇒ R54 phẳng 1 khung trước khi rời: 4,3 cm → 0 → 100,8 mm)
                        if muot[f] < muot[f - 1] - 1e-4 and b0 - f < r_: muot[f] = muot[f - 1]
            NHON_MUOT[B] = muot
        def _doc_nhon(D_phang, th):   # dốc đã nhón th (rad) quanh mũi, từ dốc phẳng
            if th <= 1e-4: return D_phang
            ben = V((0, 0, 1)).cross(V((D_phang.x, D_phang.y, 0)).normalized()); Dn = mathutils.Matrix.Rotation(th, 3, ben) @ D_phang
            if Dn.z > D_phang.z: Dn = mathutils.Matrix.Rotation(-th, 3, ben) @ D_phang
            return Dn.normalized()
        # ĐƯỜNG XY VÀO NEO (P1-j): mờ smootherstep một mình chỉ dời cú hãm của nguồn (133 → 26 mm/frames @L47→48) vào giữa cửa sổ (62 → 109 → 40 mm = 70,1 mm @L46).
        # Nay: khởi đầu từ mờ P1-i rồi THƯ GIÃN gia tốc ≤ CHAN_RUNG_MAX_MM/khung² (đúng sai phân bậc 2 cửa đo) với hai đầu cố định: khung tự do cuối
        # trước cửa sổ và cổ chân NHÓN của đoạn (đứng yên từ a0). Thử ngược: THU_VAO_KHONG_MO=1 (không mờ, không thư giãn).
        VAO_XY = {B: {} for B in "LR"}
        if not os.environ.get("THU_VAO_KHONG_MO"):
            mk_ = int(CH["mo_khoa_khung"]); gh_m = CHAN_RUNG_MAX_MM / 1000.0 * JITTER_SOLVE_FRACTION
            for B in "LR":
                bn = rig.data.bones[f"ik_{B}"]; d0 = (bn.tail_local - bn.head_local).normalized(); L_chan = (bn.tail_local - bn.head_local).length; ng0 = math.hypot(d0.x, d0.y)
                for a0, b0 in KHUNG[B]["doan"]:
                    if a0 - mk_ - 2 < 0 or any(a1 <= k <= b1 for a1, b1 in KHUNG[B]["doan"] for k in range(a0 - mk_, a0)): continue   # không đủ mk khung tự do ⇒ mờ từng khung như cũ
                    yv = KHUNG[B]["yaw"][a0]; Dp = V((math.cos(yv) * ng0, math.sin(yv) * ng0, d0.z)).normalized(); Dr = _doc_nhon(Dp, NHON_MUOT[B][a0]); neo_ = KHUNG[B]["neo"][a0]
                    p = {f: V((KHUNG[B]["dich"][f].x, KHUNG[B]["dich"][f].y, 0.0)) for f in range(a0 - mk_ - 2, a0)}
                    p[a0] = V((neo_.x + (Dp.x - Dr.x) * L_chan, neo_.y + (Dp.y - Dr.y) * L_chan, 0.0)); p[a0 + 1] = p[a0].copy()
                    for f in range(a0 - mk_, a0): p[f] = p[f] + (p[a0] - p[f]) * (1.0 - _smootherstep((a0 - f) / mk_))
                    for _ in range(80):
                        xau = 0.0
                        for c in range(a0 - mk_ - 1, a0 + 1):
                            a = p[c + 1] - 2 * p[c] + p[c - 1]
                            if a.length <= gh_m: continue
                            du = a * (1.0 - gh_m / a.length); xau = max(xau, a.length)
                            if a0 - mk_ <= c < a0: p[c] = p[c] + du / 2
                            elif c == a0 - mk_ - 1: p[c + 1] = p[c + 1] - du
                            else: p[c - 1] = p[c - 1] - du
                        if xau == 0.0: break
                    for f in range(a0 - mk_, a0 + 1): VAO_XY[B][f] = (p[f].x, p[f].y)   # kể cả neo (a0) — đầu cố định cho đường RA của đoạn trước khi hai cửa sổ chồng nhau
                    if os.environ.get("EXIT_PITCH_DEBUG"): print("VAO_XY", B, a0, "con_xau_m", round(xau, 4), [(f, round(p[f].x, 3), round(p[f].y, 3)) for f in range(a0 - mk_ - 1, a0 + 1)])
        # ĐƯỜNG XYZ RỜI ĐOẠN (P1-j): cổ chân rời nhón 3,9 cm mà z tự do của dich_chan đi từ nền phẳng (hãm 10 cm/frames) ⇒ bật 3,9 → 9,9 cm trong 1 khung = 69,4 mm @R80
        # (mờ XY P1-i không chạm z). Tính LƯỜI ở khung đầu sau đoạn (T_CUOI đã biết): khởi đầu = mờ XY P1-i + z dich_chan, thư giãn gia tốc ≤ CHAN_RUNG_MAX_MM/khung²
        # với hai đầu cố định (T_CUOI; 2 khung sau cửa sổ, hoặc neo đoạn kế nếu nó bắt đầu trong cửa sổ). Thử ngược: THU_RA_KHONG_THU_GIAN=1.
        RA_XYZ = {B: {} for B in "LR"}; Q_RA = {B: {} for B in "LR"}
        def _duong_xoay_ra(B, b0, q_b0, pos=None):
            """P1-o: THƯ GIÃN XOAY bàn chân cả cửa sổ rời đoạn (như _duong_ra cho vị trí): biến = xoay thế giới q[f] các khung tự do sau b0 (khởi đầu = đường
            nguồn liên tục lật từ q_b0), hai đầu cố định (q_b0 với vận tốc 0; 2 khung nguồn sau cửa sổ), cực tiểu hoá sai phân bậc 2 xoay ≤ gh và dốc ≤ gh,
            với ⑬ ∈ [co_chan_gap_min, 150] và 13b ≤ ban_chan_vat_max CHIẾU vào mỗi vòng (ràng buộc trong bài toán, không phải ghi đè sau: ba biên
            đánh nhau từng khung ⇒ ×11,6 @R82). Cửa sổ dài ra tới 3·mk nếu chưa hội tụ. Thử ngược: THU_XOAY_RA_KHONG_THU_GIAN=1."""
            bn = rig.data.bones[f"ik_{B}"]; d0 = (bn.tail_local - bn.head_local).normalized(); Rl = bn.matrix_local.to_3x3(); mk_ = int(CH["mo_khoa_khung"])
            gh = math.radians(CHAN_RUNG_MAX_DEG * JITTER_SOLVE_FRACTION); gh_s = CHAN_RUNG_MAX_DEG * JITTER_SOLVE_FRACTION
            lim_ = math.radians(55.0); lim_max_ = math.radians(ANKLE_ANGLE_MAX_DEG); lv_ = math.radians(25.0)   # biên CỨNG của cửa ⑬ / 13b (lề bộ giải 60/20 làm bài toán vô nghiệm)
            a1 = min([a for a, b in KHUNG[B]["doan"] if a > b0], default=N + 1); cuoi_tu_do = min(a1 - mk_ - 1, N)   # không chạm cửa sổ mờ-vào của đoạn kế
            if cuoi_tu_do <= b0: return {}
            # hướng nguồn (pose lượt 1, chưa hậu kỳ) + cẳng/đùi từng khung
            D_src = {}; A_ = {}; TH_ = {}; q_luu = {}
            for f in range(b0, min(cuoi_tu_do + 2, N) + 1):   # 1) hướng nguồn (pose lượt 1) + lưu key xoay
                sc.frame_set(f); bpy.context.view_layer.update(); pbq = rig.pose.bones[f"ik_{B}"].rotation_quaternion.copy(); q_luu[f] = pbq
                D_src[f] = (((Rl @ pbq.to_matrix() @ Rl.inverted()).to_quaternion()) @ d0).normalized()
            for ff, pp in (pos or {}).items():   # 2) áp đường vị trí rời đã thư giãn (dat_ik ghi cả key xoay = 0 ⇒ trả lại key xoay lượt 1)
                dat_ik(rig, B, pp, 0.0, ff, K[f"mui_chan_{B}"]); pb_ = rig.pose.bones[f"ik_{B}"]; pb_.rotation_quaternion = q_luu.get(ff, pb_.rotation_quaternion); pb_.keyframe_insert("rotation_quaternion", frame=ff)
            for f in range(b0, min(cuoi_tu_do + 2, N) + 1):   # 3) cẳng/đùi từ pose SẼ bake
                sc.frame_set(f); bpy.context.view_layer.update()
                A_[f] = ((W @ rig.pose.bones[f"shin_{B}"].head) - (W @ rig.pose.bones[f"shin_{B}"].tail)).normalized(); TH_[f] = ((W @ rig.pose.bones[f"thigh_{B}"].tail) - (W @ rig.pose.bones[f"thigh_{B}"].head)).normalized()
            def _goc(q): return min(q.angle, 2 * math.pi - q.angle)
            def _sl(q): Dv = q @ d0; return math.degrees(math.atan2(Dv.z, math.hypot(Dv.x, Dv.y)))
            def _al(qa, qb): return -qb if qa.dot(qb) < 0 else qb
            # 13b DỐC DẦN (P1-o): chân trụ rời đoạn đang lệch mặt phẳng chân vat0 (thân xoay trên chân trụ, ⑪ cho phép) ⇒ biên 13b hạ từ vat0 về 25° tối đa 2·gh mỗi khung
            # (biên kiểu vận tốc: dàn cú vung ra nhiều khung thay vì bẻ 1 khung −39 → −82°). Cửa 13b vẫn đo thật trên khung vung.
            nrm0 = TH_[b0].cross(-A_[b0]); vat0 = abs(90 - math.degrees(nrm0.normalized().angle(D_src[b0]))) if nrm0.length > 1e-6 else 0.0
            def _lv(f): return math.radians(max(math.degrees(lv_), vat0 - (f - b0) * 2 * gh_s))
            def _chieu(f, q):   # chiếu ⑬ + 13b lên hướng D rồi giữ lật: q ← rot(D→D')·q
                D = (q @ d0).normalized(); a_ = A_[f]; th_ = TH_[f]; D2 = D.copy(); lvf = _lv(f)
                ang = D2.angle(a_)
                if ang < lim_ - 1e-3 or ang > lim_max_ + 1e-3:
                    tr = (D2 - a_ * D2.dot(a_)); tr = tr.normalized() if tr.length > 1e-6 else V((0, -1, 0)); g_ = lim_ if ang < lim_ else lim_max_; D2 = (a_ * math.cos(g_) + tr * math.sin(g_)).normalized()
                nrm = th_.cross(-a_)
                if nrm.length > 1e-6 and math.degrees(th_.angle(-a_)) > 15:
                    nrm.normalize(); c_ = D2.dot(nrm)
                    if abs(c_) > math.sin(lvf): Dp = (D2 - nrm * c_); Dp = Dp.normalized() if Dp.length > 1e-6 else D2; D2 = (Dp * math.cos(lvf) + nrm * (math.sin(lvf) if c_ > 0 else -math.sin(lvf))).normalized()
                if (D2 - D).length < 1e-9: return q
                q2 = D.rotation_difference(D2) @ q; return _al(q, q2).normalized()
            def _dat_doc(q, s2):   # đặt dốc s2 (°) giữ hướng ngang và lật
                D = (q @ d0).normalized(); hx = V((D.x, D.y, 0)); hx = hx.normalized() if hx.length > 1e-6 else V((0, -1, 0))
                D2 = (hx * math.cos(math.radians(s2)) + V((0, 0, math.sin(math.radians(s2))))).normalized(); return _al(q, D.rotation_difference(D2) @ q).normalized()
            best = None
            for dai in range(mk_, 3 * mk_ + 1):
                M = list(range(b0 + 1, min(b0 + dai, cuoi_tu_do) + 1)); end = M[-1]
                q = {b0 - 1: q_b0.copy(), b0: q_b0.copy()}
                for f in range(b0 + 1, min(end + 2, N) + 1):   # khởi đầu: đường nguồn liên tục lật
                    qp = q[f - 1]; qn = (qp @ d0).normalized().rotation_difference(D_src[f]) @ qp; q[f] = _al(qp, qn).normalized()
                if end + 2 > N: q[end + 2] = q[min(end + 1, N)].copy()
                if end + 1 > N: q[end + 1] = q[N].copy()
                for f in M: q[f] = _chieu(f, q[f])
                xau = 0.0
                for _ in range(120):
                    xau = 0.0
                    for c in range(b0, end + 2):
                        q0_, q1_, q2_ = q[c - 1], q[c], q[c + 1]; a = (q2_ @ q1_.inverted()) @ (q1_ @ q0_.inverted()).inverted(); ang = _goc(a)
                        s_acc = _sl(q2_) - 2 * _sl(q1_) + _sl(q0_)
                        if ang > gh:
                            xau = max(xau, math.degrees(ang) - math.degrees(gh)); k_ = 1.0 - gh / ang
                            if c in M: q[c] = _al(q[c], q[c].slerp(_al(q[c], q[c - 1].slerp(_al(q[c - 1], q[c + 1]), 0.5)), 0.5 * k_)).normalized()
                            elif c == b0: q[c + 1] = _al(q[c + 1], q[c + 1].slerp(_al(q[c + 1], q[c]), k_)).normalized()   # vận tốc 0 ở đầu: dự báo = q_b0
                            else: q[c - 1] = _al(q[c - 1], q[c - 1].slerp(_al(q[c - 1], q[c] @ (q[c + 1] @ q[c].inverted()).inverted()), k_)).normalized()
                        if abs(s_acc) > gh_s:
                            xau = max(xau, abs(s_acc) - gh_s); du = abs(s_acc) - gh_s
                            if c in M: q[c] = _dat_doc(q[c], _sl(q[c]) + (du / 2 if s_acc < 0 else -du / 2))
                            elif c == b0: q[c + 1] = _dat_doc(q[c + 1], _sl(q[c + 1]) - (du if s_acc > 0 else -du))
                            else: q[c - 1] = _dat_doc(q[c - 1], _sl(q[c - 1]) - (du if s_acc > 0 else -du))
                    for f in M: q[f] = _chieu(f, q[f])
                    if xau <= 1e-3: break
                best = (xau, {f: q[f].copy() for f in M})
                if xau <= 1e-3 or end >= cuoi_tu_do: break
            if os.environ.get("EXIT_PITCH_DEBUG"): print("Q_RA", B, b0, "dai", len(best[1]), "con_xau_deg", round(best[0], 2), [(f, round(_sl(qq), 1), round(math.degrees(math.atan2((qq @ d0).y, (qq @ d0).x)), 1)) for f, qq in sorted(best[1].items())])
            return best[1]
        def _duong_ra(B, b0):
            mk_ = int(CH["mo_khoa_khung"]); gh_m = CHAN_RUNG_MAX_MM / 1000.0 * JITTER_SOLVE_FRACTION; tc = T_CUOI[B]
            a1 = min([a for a, b in KHUNG[B]["doan"] if a > b0], default=N + 1)
            for dai in range(mk_, 3 * mk_ + 1):   # P1-k: cửa sổ rời có thể DÀI RA (tới 3·mk) khi 4 khung không đủ để đuổi kịp nguồn (R54 sau phóng: 100,7 mm)
                M = list(range(b0 + 1, min(b0 + dai, a1 - 1, N) + 1))
                if not M: return {}
                p, xau = _tha_duong_ra(B, b0, M, a1, tc, mk_, gh_m)
                if xau == 0.0 or M[-1] >= min(a1 - 1, N): break
            if os.environ.get("EXIT_PITCH_DEBUG"): print("RA_XYZ", B, b0, "dai", len(M), "con_xau_m", round(xau, 4), [(f, round(p[f].x, 3), round(p[f].y, 3), round(p[f].z - K[f"co_chan_{B}"].z, 3)) for f in range(b0, M[-1] + 3)])
            return {f: p[f].copy() for f in M}
        def _tha_duong_ra(B, b0, M, a1, tc, mk_, gh_m):
            p = {b0 - 1: tc.copy(), b0: tc.copy()}
            for f in M:
                t = KHUNG[B]["dich"][f]; x, y = VAO_XY[B].get(f, (t.x, t.y)); w_ = 1.0 - _smootherstep((f - b0) / mk_)
                p[f] = V((x + (tc.x - x) * w_, y + (tc.y - y) * w_, t.z))
            for f in (M[-1] + 1, M[-1] + 2):   # đuôi cố định
                if f > N: p[f] = p[f - 1].copy()
                elif f >= a1: x, y = VAO_XY[B].get(a1, (KHUNG[B]["dich"][a1].x, KHUNG[B]["dich"][a1].y)); p[f] = V((x, y, KHUNG[B]["dich"][a1].z))
                else: p[f] = KHUNG[B]["dich"][f].copy()
            xau = 0.0
            for _ in range(80):
                xau = 0.0
                for c in range(b0, M[-1] + 2):
                    a = p[c + 1] - 2 * p[c] + p[c - 1]
                    if a.length <= gh_m: continue
                    du = a * (1.0 - gh_m / a.length); xau = max(xau, a.length)
                    if c == b0: p[c + 1] = p[c + 1] - du
                    elif c == M[-1] + 1: p[c - 1] = p[c - 1] - du
                    else: p[c] = p[c] + du / 2
                if xau == 0.0: break
            return p, xau
        for f in range(N + 1):
            for B in "LR":
                sc.frame_set(f); bpy.context.view_layer.update(); Pb_ = rig.pose.bones
                bn = rig.data.bones[f"ik_{B}"]; d0 = (bn.tail_local - bn.head_local).normalized(); L_chan = (bn.tail_local - bn.head_local).length; Rl = bn.matrix_local.to_3x3()
                pb_ = Pb_[f"ik_{B}"]; D = ((Rl @ pb_.rotation_quaternion.to_matrix() @ Rl.inverted()) @ d0).normalized()
                a_ = ((W @ Pb_[f"shin_{B}"].head) - (W @ Pb_[f"shin_{B}"].tail)).normalized(); th_ = ((W @ Pb_[f"thigh_{B}"].tail) - (W @ Pb_[f"thigh_{B}"].head)).normalized()
                lim = math.radians(CH["co_chan_gap_min_deg"]); dung = any(a0 <= f <= b0 for a0, b0 in KHUNG[B]["doan"]); doi = False; t_ = KHUNG[B]["dich"][f]; tong_nhon = 0.0
                # P1-n THAM SỐ HOÁ XOAY BÀN CHÂN: khung tự do = xoay LIÊN TỤC THEO LẬT q_f = rot(D_{f−1}→D_f)·q_{f−1} (bản cũ: xoay tối thiểu d0→D mỗi khung ⇒ lật
                # bật gần thẳng đứng, R82 29,9°); khung đứng = xoay tối thiểu (đế phẳng); mọi mờ = SLERP xoay (không trộn vector hướng — R48 21,4°)
                q_prev = DOC2[B][-1] if DOC2.get(B) else None; q_ap = None
                _q_min = lambda Dv: d0.rotation_difference(Dv)
                def _q_lt(Dv, qp=None):
                    qp = q_prev if qp is None else qp
                    if qp is None: return _q_min(Dv)
                    q_ = (qp @ d0).normalized().rotation_difference(Dv) @ qp
                    return -q_ if q_.dot(qp) < 0 else q_
                def _slerp(qa, qb, w):
                    qb = -qb if qa.dot(qb) < 0 else qb; return qa.slerp(qb, max(0.0, min(1.0, w))).normalized()
                thieu = lim - D.angle(a_)
                mk_ = int(CH["mo_khoa_khung"]); ng0 = math.hypot(d0.x, d0.y)
                if not dung:   # vừa rời đoạn đứng: DỐC bàn chân mờ dần từ dốc cuối đoạn sang dốc nguồn (P1-g: dốc nhảy −37° → −75° trong 2 khung lúc nhấc = rung 32°/khung²)
                    truoc = [b0 for a0, b0 in KHUNG[B]["doan"] if b0 < f and f - b0 <= mk_]
                    if truoc and B in D_CUOI and all(not any(a0 <= k <= b0 for a0, b0 in KHUNG[B]["doan"]) for k in range(truoc[-1] + 1, f)):
                        if f == truoc[-1] + 1 and os.environ.get("XOAY_RA_THU_GIAN") == "1":   # ⛔ MẶC ĐỊNH TẮT (P1-p đo lại): đoán trước cuối đoạn chỉ cần 9°/3° ở b0+1 — nhu cầu −80° nằm ở b0+2 (cẳng IK quất khi cổ chân đi qua dưới gối gập) ⇒ thư giãn vẫn dư 74°/50° (50,6° @R55); bản từng khung P1-n (×11,6) là tốt nhất đo được   # ⛔ MẶC ĐỊNH TẮT (P1-o đo): bài toán vô nghiệm ở R54/R79 — ⑬ đòi bàn chân kéo lê rơi −30 → −80° ngay khung tự do đầu (dư 74°/50°) ⇒ 50,5° @R55, ×39; phải đoán trước bằng nhón dần cuối đoạn (chưa làm)   # P1-o: thư giãn xoay cả cửa sổ — SAU khi đã có đường vị trí rời (cẳng đọc từ pose SẼ bake: pose lượt 1 để cổ chân 10 cm ⇒ ⑬ chiếu sai, −80° @56)
                            if not os.environ.get("THU_RA_KHONG_THU_GIAN"): RA_XYZ[B] = _duong_ra(B, truoc[-1])
                            Q_RA[B] = _duong_xoay_ra(B, truoc[-1], Q_CUOI[B], RA_XYZ[B])
                        if f in Q_RA[B]: q_ap = Q_RA[B][f].copy()
                        else: w_ = 1.0 - _smootherstep((f - truoc[-1]) / mk_); q_ap = _slerp(_q_lt(D), Q_CUOI[B], w_)   # P1-n: slerp xoay (không trộn vector)
                        D = (q_ap @ d0).normalized(); doi = True
                    # SẮP vào đoạn đứng (P1-h: L f47 dốc −1,3° → −22,4° trong 1 khung = rung 24,9°/khung²): mờ dần sang dốc đứng (đã nhón) của đoạn sắp tới
                    sau = [a0 for a0, b0 in KHUNG[B]["doan"] if a0 > f and a0 - f <= mk_]
                    if sau and all(not any(a0 <= k <= b0 for a0, b0 in KHUNG[B]["doan"]) for k in range(f + 1, sau[0])):
                        yv = KHUNG[B]["yaw"][sau[0]]; Dp = V((math.cos(yv) * ng0, math.sin(yv) * ng0, d0.z)).normalized(); Dr = _doc_nhon(Dp, NHON_MUOT[B][sau[0]])
                        w_ = 1.0 - _smootherstep((sau[0] - f) / mk_); q_ap = _slerp(q_ap if q_ap is not None else _q_lt(D), _q_min(Dr), w_); D = (q_ap @ d0).normalized(); doi = True   # P1-n: slerp xoay — cũng là mờ LẬT về đế phẳng trước khi đặt chân
                        neo_ = KHUNG[B]["neo"][sau[0]]; tx = neo_.x + Dp.x * L_chan - Dr.x * L_chan; ty = neo_.y + Dp.y * L_chan - Dr.y * L_chan   # cổ chân NHÓN của đoạn sắp tới (neo phẳng lệch 7,8 cm ⇒ 77,8 mm @R65)
                        if f in VAO_XY[B]: tx, ty = VAO_XY[B][f]; t_ = V((tx, ty, t_.z))   # P1-j: đường vào đã thư giãn gia tốc
                        else: t_ = V((t_.x + (tx - t_.x) * w_, t_.y + (ty - t_.y) * w_, t_.z))
                        KHUNG[B]["dich"][f] = t_; dat_ik(rig, B, t_, 0.0, f, K[f"mui_chan_{B}"])
                    # RỜI đoạn (P1-i): XY mờ khỏi vị trí cổ chân CUỐI đoạn (sau nhón) theo thời gian; dốc: gia tốc ≤ CHAN_RUNG_MAX_DEG/khung² (hiệu chuẩn walk 13,4 ×1,2)
                    if truoc and B in T_CUOI and all(not any(a0 <= k <= b0 for a0, b0 in KHUNG[B]["doan"]) for k in range(truoc[-1] + 1, f)):
                        w_ = 1.0 - _smootherstep((f - truoc[-1]) / mk_); tc = T_CUOI[B]
                        if f == truoc[-1] + 1 and not os.environ.get("THU_RA_KHONG_THU_GIAN") and f not in RA_XYZ[B]: RA_XYZ[B] = _duong_ra(B, truoc[-1])
                        if f in RA_XYZ[B]: t_ = RA_XYZ[B][f].copy()   # P1-j: đường rời đã thư giãn gia tốc (XYZ)
                        else: t_ = V((t_.x + (tc.x - t_.x) * w_, t_.y + (tc.y - t_.y) * w_, t_.z))
                        KHUNG[B]["dich"][f] = t_; dat_ik(rig, B, t_, 0.0, f, K[f"mui_chan_{B}"]); doi = True
                    D_TRUOC[B] = D.copy()
                    # P1-j: các khối trên dời cổ chân (đường vào/ra) ⇒ IK giải lại ⇒ cẳng đổi hướng: đọc lại cẳng/đùi TRƯỚC khi kẹp ⑬/13b (đo cẳng cũ ⇒ ⑬ 153,9° @L93 lọt)
                    sc.frame_set(f); bpy.context.view_layer.update()
                    a_ = ((W @ Pb_[f"shin_{B}"].head) - (W @ Pb_[f"shin_{B}"].tail)).normalized(); th_ = ((W @ Pb_[f"thigh_{B}"].tail) - (W @ Pb_[f"thigh_{B}"].head)).normalized(); thieu = lim - D.angle(a_)
                lim_max = math.radians(ANKLE_ANGLE_MAX_DEG)
                if dung:
                    # NHÓN GÓT THEO ĐOẠN (P1-g) + VÀO ĐOẠN TỪ TRÊN KHÔNG (P1-h, Boss «hỏng chân khỏi mặt đất một nhịp»): góc nhón th2 đã tính trước và làm mượt;
                    # mũi bàn chân neo T (mũi của bàn chân phẳng tại neo, trên nền); cổ chân HẠ theo đường cong mượt tới ĐỘ CAO NHÓN z_ts (không hạ xuống nền rồi
                    # bật lên 8,6 cm), dốc mờ từ dốc tự do khung trước vào dốc đứng theo PHẦN ĐƯỜNG ĐÃ HẠ (xong trước khi còn 3 cm — ㉓), và mờ nhanh hơn nếu
                    # cần để mũi không xuyên đất (bẻ dốc chứ không đội cổ chân lên). ⛔ không bao giờ xếp nhón 36° lên bàn chân phẳng đang lơ lửng 9 cm.
                    a0, b0 = next((a, b) for a, b in KHUNG[B]["doan"] if a <= f <= b); th2 = NHON_MUOT[B][f]; yv = KHUNG[B]["yaw"][a0]; neo = KHUNG[B]["neo"][a0]
                    Dp = V((math.cos(yv) * ng0, math.sin(yv) * ng0, d0.z)).normalized(); zm0 = K[f"mui_chan_{B}"].z
                    T = V((neo.x + Dp.x * L_chan, neo.y + Dp.y * L_chan, zm0))   # mũi neo — KHÔNG đổi khi lăn mũi (P1-m)
                    # LĂN MŨI CUỐI ĐOẠN (P1-m): 3 khung cuối đoạn đứng (không phải cuối clip) hướng bàn chân nghiêng dần về hướng nguồn của khung tự do đầu
                    # và gót nhấc dần (≥ nhon_got_toi_thieu·w) — mũi vẫn neo ⇒ khung tự do đầu còn < 14° phải xoay (trước: 25° @R37 do ⑬ ép khi cẳng vung).
                    # Thử ngược: THU_KHONG_LAN_MUI=1.
                    w_lan = 0.0
                    if b0 < N and f >= b0 - 2 and os.environ.get("LAN_MUI"):   # ⛔ MẶC ĐỊNH TẮT (P1-m đo): xoay yaw quanh mũi của bàn chân phẳng = gót TRƯỢT (① 25,1 mm L0–19, 13b 48,3, ⑪ 19,1, 110,8 mm @R78) — chỉ bật để nghiên cứu
                        w_lan = _smootherstep((f - (b0 - 3)) / 3.0); Ds = huong_fk[B][min(N, b0 + 1)]; y_s = math.atan2(Ds.y, Ds.x)
                        dy = (y_s - yv + math.pi) % (2 * math.pi) - math.pi; yv2 = yv + dy * w_lan
                        Dp = V((math.cos(yv2) * ng0, math.sin(yv2) * ng0, d0.z)).normalized(); th2 = max(th2, math.radians(CH["nhon_got_toi_thieu_deg"]) * w_lan)
                    Dr = _doc_nhon(Dp, th2); z_ts = T.z - Dr.z * L_chan
                    z0_ = K[f"co_chan_{B}"].z; h_vao = KHUNG[B].setdefault("h_vao", {}).get(a0)
                    if h_vao is None: h_vao = max(z_ts, vet[B][a0].z); KHUNG[B]["h_vao"][a0] = h_vao
                    rate = 0.02 if os.environ.get("THU_HA_CHAM") else CH["ha_moi_khung_m"]; z_n = max(z_ts, h_vao - (f - a0) * rate)
                    if h_vao - z_ts > 1e-3 and z_n - z_ts > 0.03: w_ = _smootherstep((h_vao - z_n) / (h_vao - z_ts - 0.03))
                    else: w_ = 1.0
                    D_vao = D_TRUOC.get(B, Dp)
                    if os.environ.get("THU_VAO_KHONG_MO"): w_ = 1.0   # thử ngược: không mờ dốc lúc vào (bản P1-g)
                    q_vao = q_prev if q_prev is not None else _q_min(D_vao); q_st = _q_min(Dr)
                    def _blend(w): return (_slerp(q_vao, q_st, w) @ d0).normalized()   # P1-n: slerp xoay từ xoay khung trước (liên tục lật) về xoay đứng (đế phẳng)
                    w_ap = w_; D = _blend(w_)
                    if z_n + D.z * L_chan < zm0 - 0.002:   # mũi xuyên đất ở dốc này ⇒ mờ nhanh hơn (chia đôi) tới khi mũi ≥ nền — cổ chân vẫn theo đường cong
                        lo_, hi_ = w_, 1.0
                        for _ in range(8):
                            m_ = (lo_ + hi_) / 2
                            if z_n + _blend(m_).z * L_chan >= zm0 - 0.002: hi_ = m_
                            else: lo_ = m_
                        w_ap = hi_; D = _blend(hi_)
                    q_ap = _slerp(q_vao, q_st, w_ap)
                    t_ = V((T.x - D.x * L_chan, T.y - D.y * L_chan, z_n)); tong_nhon = th2
                    KHUNG[B]["dich"][f] = t_; dat_ik(rig, B, t_, 0.0, f, K[f"mui_chan_{B}"]); doi = True
                elif thieu > 1e-3:
                    tr = (D - a_ * D.dot(a_)); tr = tr.normalized() if tr.length > 1e-6 else V((0, -1, 0)); D = (a_ * math.cos(lim) + tr * math.sin(lim)).normalized(); doi = True
                elif D.angle(a_) > lim_max + 1e-3:   # P1-j: chân tự do duỗi mũi quá biên trên ⑬ ⇒ xoay D về phía cẳng tới biên
                    tr = (D - a_ * D.dot(a_)); tr = tr.normalized() if tr.length > 1e-6 else V((0, -1, 0)); D = (a_ * math.cos(lim_max) + tr * math.sin(lim_max)).normalized(); doi = True
                nrm = th_.cross(-a_); zm0 = K[f"mui_chan_{B}"].z
                for _lan in range(2):   # mặt phẳng chân rồi mũi-không-xuyên-đất, lặp 2 lượt (sửa mũi đổi dốc ⇒ lệch mặt phẳng lại; đo 23/10: 1 lượt còn 36°)
                    if (not dung or t_.z - K[f"co_chan_{B}"].z > 0.02) and nrm.length > 1e-6 and math.degrees(th_.angle(-a_)) > 15:   # khung đứng còn đang hạ (> 2 cm) vẫn là chân trên không với cửa 13b
                        nrm.normalize(); lv = math.radians(CH["ban_chan_vat_max_deg"]); c_ = D.dot(nrm)
                        if abs(c_) > math.sin(lv):
                            Dp = (D - nrm * c_); Dp = Dp.normalized() if Dp.length > 1e-6 else D; D = (Dp * math.cos(lv) + nrm * (math.sin(lv) if c_ > 0 else -math.sin(lv))).normalized(); doi = True
                    mui_z = t_.z + D.z * L_chan
                    if mui_z < zm0 - 0.002 and not dung:   # chân TỰ DO: mũi xuyên đất ⇒ NÂNG cả bàn chân (giữ dốc nguồn — bẻ dốc tại 2 cm ⇒ rung 145 mm/khung² @R50, P1-g)
                        t_ = V((t_.x, t_.y, t_.z + (zm0 - 0.002 - mui_z))); KHUNG[B]["dich"][f] = t_; dat_ik(rig, B, t_, 0.0, f, K[f"mui_chan_{B}"]); doi = True; mui_z = zm0 - 0.002
                    if mui_z < zm0 - 0.002:   # chân đứng: mũi xuyên đất sau khi kẹp ⇒ nâng mũi lên nền (② đo −42,9 mm khi thiếu bước này; cửa ② cho −3 mm ⇒ dung sai 2 mm)
                        dz = max(-1.0, min(1.0, (zm0 - t_.z) / L_chan)); xong = False
                        if not dung and nrm.length > 1e-6 and math.degrees(th_.angle(-a_)) > 15:   # chân tự do có mặt phẳng: xoay TRONG mặt phẳng chân (giữ 13b) tới khi mũi chạm nền
                            u1 = (D - nrm * D.dot(nrm)); u1 = u1.normalized() if u1.length > 1e-6 else D; u2 = nrm.cross(u1).normalized(); R_ = math.hypot(u1.z, u2.z)
                            if R_ >= abs(dz) + 1e-6:
                                ph0 = math.atan2(u2.z, u1.z); da = math.acos(max(-1.0, min(1.0, dz / R_))); th = min((ph0 + da, ph0 - da), key=lambda t: abs((t + math.pi) % (2 * math.pi) - math.pi))
                                D = (u1 * math.cos(th) + u2 * math.sin(th)).normalized(); xong = True
                        if not xong:
                            ng = math.hypot(D.x, D.y) or 1.0; r_ = math.sqrt(max(0.0, 1 - dz * dz)); D = V((D.x / ng * r_, D.y / ng * r_, dz)).normalized()
                        doi = True
                sap_vao = (not dung) and any(a0 > f and a0 - f <= int(CH["mo_khoa_khung"]) for a0, b0 in KHUNG[B]["doan"])
                trong_cua_ra = (not dung) and bool([b0 for a0, b0 in KHUNG[B]["doan"] if b0 < f and f - b0 <= int(CH["mo_khoa_khung"])])
                if dung or sap_vao: KEP_DANG[B] = False
                if f in Q_RA[B]: KEP_DANG[B] = False   # P1-o: khung đã thư giãn cả cửa sổ (ràng buộc thoả chung) ⇒ không kẹp từng khung nữa
                if (trong_cua_ra or KEP_DANG.get(B)) and not sap_vao and f not in Q_RA[B] and len(DOC2.get(B, [])) == 2 and not os.environ.get("THU_KHONG_KEP_GIA_TOC_DOC"):   # ÁP SAU CÙNG (sau kẹp ⑬/13b + nâng mũi, nếu không chúng phá lại: 22,4° @L95)   # cửa sổ RỜI đoạn, và TIẾP TỤC chừng nào còn phải kẹp (P1-l: dừng ở mép 4 khung khi còn trễ ⇒ 29,3° @R41 ngay khung sau); không áp khi sắp vào (đánh nhau với mờ-vào: 75,7° @R62)
                    # P1-l: kẹp gia tốc TOÀN XOAY bàn chân (dốc + hướng + lật) — cửa đo góc trắc địa của sai phân bậc 2 xoay thế giới; bản P1-j chỉ kẹp DỐC ⇒ foot_R ×13–16
                    # ở mọi lần rời đoạn (hướng mờ từ yaw neo về yaw nguồn trong 1 khung). Dự báo = q1·(q1·q0⁻¹) (vận tốc góc không đổi); lệch > gh ⇒ slerp từ dự báo về muốn đúng gh.
                    q0_, q1_ = DOC2[B]; q_du = (q1_ @ q0_.inverted()) @ q1_; gh = math.radians(CHAN_RUNG_MAX_DEG * JITTER_SOLVE_FRACTION)
                    _sl = lambda Dv: math.degrees(math.atan2(Dv.z, math.hypot(Dv.x, Dv.y))); s0_, s1_ = _sl(q0_ @ d0), _sl(q1_ @ d0); du_s = 2 * s1_ - s0_; gh_s = CHAN_RUNG_MAX_DEG * JITTER_SOLVE_FRACTION
                    lim_cung = math.radians(55.0)   # biên CỨNG của cửa ⑬ (55°) — biên bộ giải 60° là lề an toàn; khi xung đột với kẹp gia tốc, giải phẫu thắng ở biên cứng
                    lech = 0.0; KEP_DANG[B] = False
                    for _vong in range(3):   # P1-m: lặp [kẹp xoay → kẹp DỐC → ⑬ → 13b] — lấy cái nghiêm hơn; gần bàn chân dựng đứng yaw và dốc không đồng ý (R82: xoay 13° mà dốc 28,6°)
                        q_muon = q_ap if (q_ap is not None and ((q_ap @ d0) - D).length < 1e-6) else _q_lt(D)   # P1-n: ứng viên (xoay trước: xoay-sau cho ×8,5 nhưng dốc 23,2 + 13b 30,7 @R82 — ba ràng buộc không đồng thời thoả được ở bàn chân dựng đứng) = xoay liên tục lật (không phải tối thiểu)
                        if q_muon.dot(q_du) < 0: q_muon = -q_muon
                        lech = q_muon.rotation_difference(q_du).angle
                        if lech > gh: q_ap = q_du.slerp(q_muon, gh / lech).normalized(); D = (q_ap @ d0).normalized(); doi = True; KEP_DANG[B] = True
                        s_ = _sl(D); gia_s = s_ - du_s
                        if abs(gia_s) > gh_s:   # dốc: sai phân bậc 2 ≤ gh (đúng thứ cửa chan_rung_max_deg đo), giữ hướng ngang
                            s2 = du_s + max(-gh_s, min(gh_s, gia_s)); hx = V((D.x, D.y, 0)); hx = hx.normalized() if hx.length > 1e-6 else V((0, -1, 0))
                            D = (hx * math.cos(math.radians(s2)) + V((0, 0, math.sin(math.radians(s2))))).normalized(); doi = True; q_ap = None; KEP_DANG[B] = True
                        ang_ = D.angle(a_)   # ⑬ thắng kẹp gia tốc (giải phẫu trước, ở biên cứng 55°)
                        if ang_ < lim_cung - 1e-3 or ang_ > lim_max + 1e-3:
                            tr = (D - a_ * D.dot(a_)); tr = tr.normalized() if tr.length > 1e-6 else V((0, -1, 0)); g_ = lim_cung if ang_ < lim_cung else lim_max
                            D = (a_ * math.cos(g_) + tr * math.sin(g_)).normalized(); doi = True; q_ap = None
                        if nrm.length > 1e-6 and math.degrees(th_.angle(-a_)) > 15:   # P1-l: 13b thắng kẹp gia tốc (slerp toàn xoay đưa D ra khỏi mặt phẳng chân: 13b 30,7°)
                            # P1-n: ở biên CỨNG của cửa 13b (25°) chứ không phải lề bộ giải 20° — chân đứng rời đoạn lệch mặt phẳng 43,8° (hông đã xoay 37° trên chân trụ, ⑪ cho phép)
                            # và 13b kéo về 20° trong MỘT khung = 24° yaw @R37 (⑬ ở đó 75–81°, không phải thủ phạm)
                            nrm.normalize(); lv = math.radians(25.0); c_ = D.dot(nrm)
                            if abs(c_) > math.sin(lv):
                                Dp = (D - nrm * c_); Dp = Dp.normalized() if Dp.length > 1e-6 else D; D = (Dp * math.cos(lv) + nrm * (math.sin(lv) if c_ > 0 else -math.sin(lv))).normalized(); doi = True; q_ap = None
                    if os.environ.get("EXIT_PITCH_DEBUG"): print("EXIT_ROT", B, f, "lech_deg", round(math.degrees(lech), 1), "kep", q_ap is not None, "slope", round(math.degrees(math.atan2(D.z, math.hypot(D.x, D.y))), 1), "dich_z_cm", round((t_.z - K[f"co_chan_{B}"].z) * 100, 1))
                if not dung:   # P1-l: «phẳng khi thấp & chậm» (đúng định nghĩa cửa ㉓) là thao tác dốc CUỐI CÙNG của chân tự do (P1-k đặt trước 13b/mũi/kẹp ⇒ bị đẩy lại: ㉓ 11,7 @L44)
                    def _vt(f_):   # vị trí cổ chân SẼ bake: đường vào/ra đã thư giãn nếu có, không thì đích dich_chan (đọc đích thô ⇒ v quá cao ⇒ luật không chạy, ㉓ 11,6 @L44)
                        f_ = max(0, min(N, f_)); p_ = KHUNG[B]["dich"][f_]
                        if f_ in RA_XYZ.get(B, {}): return RA_XYZ[B][f_]
                        if f_ in VAO_XY[B]: return V((VAO_XY[B][f_][0], VAO_XY[B][f_][1], p_.z))
                        return p_
                    v_post = (t_ - _vt(f - 1)).length * FPS if f > 0 else 0.0   # ĐÚNG công thức cửa ㉓ (animate.py): bước LÙI |p[f]−p[f−1]|·FPS — sai phân giữa cho R41 0,34 (snap phẳng 1 khung ⇒ 29,3°) và L44 0,8 (bỏ qua, cửa đo 0,30)
                    if os.environ.get("EXIT_PITCH_DEBUG") and 36 <= f <= 46: print("FLAT?", B, f, "h_cm", round((t_.z - K[f"co_chan_{B}"].z) * 100, 1), "v_post", round(v_post, 2), "kep_dang", KEP_DANG.get(B), "trong_cua_ra", trong_cua_ra, "sap_vao", sap_vao, "slope", round(math.degrees(math.atan2(D.z, math.hypot(D.x, D.y))), 1))
                    if t_.z - K[f"co_chan_{B}"].z <= CH["phang_cao_m"] and v_post < CH["phang_v_mps"]:
                        ng_ = math.hypot(D.x, D.y) or 1.0; Df = V((D.x / ng_ * ng0, D.y / ng_ * ng0, d0.z)).normalized()
                        if Df.angle(D) > 1e-3: D = Df; doi = True; q_ap = None
                if dung: D_CUOI[B] = D.copy(); T_CUOI[B] = t_.copy()
                # P1-n xoay cuối cùng: q_ap nếu còn khớp D; khung đứng = xoay tối thiểu (đế phẳng); khung tự do = liên tục lật từ khung trước — và LUÔN ghi key khung tự do
                if q_ap is not None and ((q_ap @ d0) - D).length < 1e-6: q_the = q_ap
                elif dung: q_the = _q_min(D)
                else: q_the = _q_lt(D)
                if not dung: doi = True
                if dung: Q_CUOI[B] = q_the.copy()
                if B in DOC2 and DOC2[B] and q_the.dot(DOC2[B][-1]) < 0: q_the = -q_the
                DOC2[B] = ([DOC2[B][-1]] if B in DOC2 and DOC2[B] else []) + [q_the]   # 2 xoay thế giới gần nhất (kẹp gia tốc toàn xoay, P1-l)
                if doi:
                    pb_.rotation_quaternion = (Rl.inverted() @ q_the.to_matrix() @ Rl).to_quaternion(); pb_.keyframe_insert("rotation_quaternion", frame=f); kep_[B] = kep_.get(B, 0) + 1
                if os.environ.get("NHON_DEBUG") and B == "R" and 63 <= f <= 82:
                    sc.frame_set(f); bpy.context.view_layer.update(); fb_ = Pb_[f"foot_{B}"]; hh = (W @ fb_.head).z - K[f"co_chan_{B}"].z; fd = (W @ fb_.tail) - (W @ fb_.head)
                    print("NHON", f, "dung", dung, "doi", doi, "tong_nhon_deg", round(math.degrees(tong_nhon), 1), "goc_D_cang", round(math.degrees(D.angle(a_)), 1), "dich_h_cm", round((t_.z - K[f"co_chan_{B}"].z) * 100, 1), "foot_head_h_cm", round(hh * 100, 1), "foot_slope_deg", round(math.degrees(math.atan2(fd.z, math.hypot(fd.x, fd.y))), 1), "D_slope_deg", round(math.degrees(math.atan2(D.z, math.hypot(D.x, D.y))), 1))
        if kep_: print("KEP_CO_CHAN (khung kẹp biên độ cổ chân hậu kỳ):", kep_)
    return N


# ------------------------------------------------------------------ bộ chạm đất (helpers của retarget_sam, P1 23/10/2026)
SAM_GLITCH = []; SAM_ANH2D = None; SAM_KEP_TAY = None
# P1-k (24/10, Boss lần 3 «vẫn còn giật nhẹ lúc phóng lao»): tư thế NGUỒN đã đổi khung (xoay thế giới từng xương, ngay sau khi chép góc, TRƯỚC mọi
# chỉnh sửa: kẹp cổ tay, tỉ lệ tay, chạm đất, hạ hông, hậu kỳ) — mốc so sánh cho cửa than_rung (luật phòng ngừa #2: đo so với nguồn độc lập).
THAN_XUONG = ["hips", "spine", "chest", "neck", "head"] + [f"{x}_{B}" for B in "LR" for x in ("clavicle", "upperarm", "forearm", "hand", "thigh", "shin", "foot")]
NGUON_POSE = {}   # xương → [quaternion thế giới mỗi khung]; rỗng = không có nguồn (build) ⇒ cửa than_rung chỉ báo
NGUON_VT = {}     # xương → [vị trí đầu xương thế giới mỗi khung]
def ghi_nguon_pose(rig, f):
    W = rig.matrix_world
    for b in THAN_XUONG:
        if b not in rig.pose.bones: continue
        M = (W @ rig.pose.bones[b].matrix); q = M.to_3x3().normalized().to_quaternion()
        L = NGUON_POSE.setdefault(b, [])
        if L and q.dot(L[-1]) < 0: q = -q
        L.append(q); NGUON_VT.setdefault(b, []).append(M.translation.copy())
def _gia_toc_goc(qs):
    """sai phân bậc 2 của xoay (°): góc trắc địa của (q[f+1]·q[f]⁻¹)·(q[f]·q[f−1]⁻¹)⁻¹, bất biến với đổi hệ quy chiếu cố định; [None, a1 … a(n−2), None]"""
    out = [None] * len(qs)
    for f in range(1, len(qs) - 1):
        d1 = qs[f] @ qs[f - 1].inverted(); d2 = qs[f + 1] @ qs[f].inverted(); a = d2 @ d1.inverted()
        out[f] = 2.0 * math.degrees(math.acos(max(-1.0, min(1.0, abs(a.w)))))
    return out
THAN_RUNG_NEN_DEG = 2.0   # ° — sàn của «gia tốc nguồn» trong tỉ số (nguồn gần tĩnh ⇒ không chia cho ~0)
THAN_RUNG_RATIO_MAX = 10.0   # cửa than_rung — hiệu chuẩn 24/10 trên dương có nguồn: Kimodo bow 8,38 (foot_L @21) · Kimodo walk 7,01 (foot_L @42) ⇒ ×1,2; lao P1-j 15,6 (foot_R @36, rời đoạn) phải rớt
HONG_RUNG_XY_MAX_MM = 34.0   # mm/khung² (24 fps) gia tốc XY hông — biên VẬT LÝ 2 g (9,81·2/24² = 34 mm); dương đo: idle 0,1 · bow 8,4 · walk 6,1; nguồn lao GVHMR 132,6 @50 (7,8 g) phải rớt
def than_rung(rig, f0, f1):
    """P1-k: TOÀN THÂN so với NGUỒN. Từng xương: gia tốc góc (sai phân bậc 2 xoay thế giới) của pose ĐÃ BAKE vs của nguồn cùng xương, cửa sổ ±1 khung;
    tỉ số = ra / max(nguồn_±1, THAN_RUNG_NEN_DEG). Kèm giật toàn thân (sai phân bậc 3 vị trí khớp, mm, trung bình các khớp) và rung XY hông/lưng (mm).
    THAN_DUMP=<path> ghi bảng từng xương/khung."""
    sc = bpy.context.scene; W = rig.matrix_world; qs = {b: [] for b in THAN_XUONG if b in rig.pose.bones}; ps = {b: [] for b in qs}
    for f in range(f0, f1 + 1):
        sc.frame_set(f); bpy.context.view_layer.update()
        for b in qs:
            M = W @ rig.pose.bones[b].matrix; q = M.to_3x3().normalized().to_quaternion()
            if qs[b] and q.dot(qs[b][-1]) < 0: q = -q
            qs[b].append(q); ps[b].append(M.translation.copy())
    n = f1 - f0 + 1; co_nguon = bool(NGUON_POSE) and all(len(NGUON_POSE.get(b, [])) >= f1 + 1 for b in qs)
    bang = {}; max_ratio = 0.0; o_ratio = None; max_vuot = 0.0; o_vuot = None
    for b in qs:
        ra = _gia_toc_goc(qs[b]); ng = _gia_toc_goc(NGUON_POSE[b][f0:f1 + 1]) if co_nguon else None
        row = dict(ra_max=0.0, ra_p95=0.0, ng_max=None, ng_p95=None, ratio_max=None, o=None)
        v_ra = [x for x in ra if x is not None]; v_ra_s = sorted(v_ra)
        if v_ra: row["ra_max"] = round(max(v_ra), 2); row["ra_p95"] = round(v_ra_s[int(0.95 * (len(v_ra_s) - 1))], 2)
        if ng:
            v_ng = sorted(x for x in ng if x is not None); row["ng_max"] = round(max(v_ng), 2); row["ng_p95"] = round(v_ng[int(0.95 * (len(v_ng) - 1))], 2)
            rt = []
            for f in range(1, n - 1):
                cs = max(x for x in ng[max(1, f - 1):min(n - 1, f + 2)] if x is not None); r_ = ra[f] / max(cs, THAN_RUNG_NEN_DEG); rt.append((r_, f + f0, ra[f], cs))
                if r_ > max_ratio: max_ratio, o_ratio = r_, [b, f + f0, round(ra[f], 2), round(cs, 2)]
                if ra[f] - cs > max_vuot: max_vuot, o_vuot = ra[f] - cs, [b, f + f0, round(ra[f], 2), round(cs, 2)]
            w_ = max(rt); row["ratio_max"] = round(w_[0], 2); row["o"] = [w_[1], round(w_[2], 2), round(w_[3], 2)]
            if os.environ.get("THAN_DUMP"): row["ra"] = [None if x is None else round(x, 2) for x in ra]; row["ng"] = [None if x is None else round(x, 2) for x in ng]
        elif os.environ.get("THAN_DUMP"): row["ra"] = [None if x is None else round(x, 2) for x in ra]
        bang[b] = row
    # giật toàn thân (sai phân bậc 3 vị trí, mm, trung bình các khớp) + rung XY hông/lưng
    giat = []
    for f in range(1, n - 2):
        giat.append(sum((ps[b][f + 2] - 3 * ps[b][f + 1] + 3 * ps[b][f] - ps[b][f - 1]).length for b in ps) / len(ps) * 1000)
    xy = {b: max(((ps[b][f + 1] - 2 * ps[b][f] + ps[b][f - 1]).xy.length * 1000) for f in range(1, n - 1)) for b in ("hips", "spine", "chest") if b in ps}
    xy_ng = {}
    if co_nguon and all(len(NGUON_VT.get(b, [])) >= f1 + 1 for b in xy):
        for b in xy:
            P = NGUON_VT[b][f0:f1 + 1]; xy_ng[b] = max(((P[f + 1] - 2 * P[f] + P[f - 1]).xy.length * 1000) for f in range(1, n - 1))
        if os.environ.get("THAN_DUMP"):
            bang["_hong_xy"] = dict(ra=[round((ps["hips"][f + 1] - 2 * ps["hips"][f] + ps["hips"][f - 1]).xy.length * 1000, 1) for f in range(1, n - 1)],
                                    ng=[round((NGUON_VT["hips"][f0 + f + 1] - 2 * NGUON_VT["hips"][f0 + f] + NGUON_VT["hips"][f0 + f - 1]).xy.length * 1000, 1) for f in range(1, n - 1)])
    kq = {"hong_rung_xy_ng_mm": {b: round(v, 1) for b, v in xy_ng.items()},"than_rung_co_nguon": co_nguon, "than_rung_max_ratio": round(max_ratio, 2) if co_nguon else None, "than_rung_o": o_ratio, "than_rung_vuot_deg": round(max_vuot, 2) if co_nguon else None, "than_rung_vuot_o": o_vuot,
          "giat_toan_than_mm": round(sum(giat) / max(1, len(giat)), 2) if giat else 0.0, "giat_toan_than_max_mm": round(max(giat), 2) if giat else 0.0, "giat_toan_than_max_o": (giat.index(max(giat)) + 1 + f0) if giat else None,
          "hong_rung_xy_mm": {b: round(v, 1) for b, v in xy.items()}}
    top = sorted([kv for kv in bang.items() if not kv[0].startswith("_")], key=lambda kv: -(kv[1]["ratio_max"] if kv[1]["ratio_max"] is not None else kv[1]["ra_max"]))[:8]
    print("THAN_RUNG (°/khung², ra vs nguồn) top:", " · ".join(f"{b} ra {r['ra_max']}/{r['ra_p95']} ng {r['ng_max']}/{r['ng_p95']} ×{r['ratio_max']} @{r['o']}" for b, r in top))
    if os.environ.get("THAN_DUMP"): json.dump(dict(bang=bang, giat=[round(x, 2) for x in giat], f0=f0, kq=kq), open(os.environ["THAN_DUMP"], "w"))
    return kq


def _one_euro_1d(xs, fs, LM, beta):
    """one-euro (Casiez 2012) một chiều trên chuỗi Vector: cutoff = min_cutoff + beta·|v̂|; trả danh sách đã lọc (có trễ pha — gọi 2 chiều ở lam_muot_nguon)."""
    def alpha(fc): tau = 1.0 / (2 * math.pi * fc); return 1.0 / (1.0 + tau * fs)
    out = [xs[0].copy()]; dx_hat = xs[0] * 0.0
    for i in range(1, len(xs)):
        dx = (xs[i] - out[-1]) * fs; a_d = alpha(LM["d_cutoff_hz"]); dx_hat = dx_hat + (dx - dx_hat) * a_d
        fc = LM["min_cutoff_hz"] + beta * dx_hat.length; a = alpha(fc); out.append(out[-1] + (xs[i] - out[-1]) * a)
    return out
def _one_euro_quat(qs, fs, LM, beta):
    """one-euro cho quaternion: slerp về giá trị thô với alpha(cutoff), tốc độ góc ước lượng (rad/s) từ góc giữa 2 khung thô, lọc thấp."""
    def alpha(fc): tau = 1.0 / (2 * math.pi * fc); return 1.0 / (1.0 + tau * fs)
    out = [qs[0].copy()]; w_hat = 0.0
    for i in range(1, len(qs)):
        w = qs[i].rotation_difference(qs[i - 1]).angle * fs; w_hat += (w - w_hat) * alpha(LM["d_cutoff_hz"])
        fc = LM["min_cutoff_hz"] + beta * w_hat; q = out[-1].slerp(qs[i], alpha(fc))
        if q.dot(out[-1]) < 0: q = -q
        out.append(q)
    return out
def lam_muot_nguon(JP, RQ, nJ, LM, k_root=None):
    """P1-k: lọc one-euro HAI CHIỀU (tiến + lùi, lấy trung bình ⇒ không trễ pha) từng khớp: vị trí (m, beta_vi_tri theo m/s) và xoay (beta_xoay theo rad/s).
    P1-l: khớp GỐC (dịch chuyển hông) lọc MẠNH hơn (min_cutoff_root_hz, beta_root) — xương chậu không có 7 g hợp lệ; cổ tay vẫn theo beta_vi_tri."""
    fs = float(LM.get("fs_nguon", 30.0)); n = len(JP); JP2 = [list(j) for j in JP]; RQ2 = [list(r) for r in RQ]
    for k in range(nJ):
        LMk, beta = (dict(LM, min_cutoff_hz=LM["min_cutoff_root_hz"]), LM["beta_root"]) if (k == k_root and "beta_root" in LM) else (LM, LM["beta_vi_tri"])
        xs = [JP[i][k] for i in range(n)]; f_ = _one_euro_1d(xs, fs, LMk, beta); b_ = _one_euro_1d(xs[::-1], fs, LMk, beta)[::-1]
        for i in range(n): JP2[i][k] = (f_[i] + b_[i]) * 0.5
        qs = [RQ[i][k] for i in range(n)]; fq = _one_euro_quat(qs, fs, LM, LM["beta_xoay"]); bq = _one_euro_quat(qs[::-1], fs, LM, LM["beta_xoay"])[::-1]
        for i in range(n):
            q = fq[i].slerp(bq[i], 0.5) if fq[i].dot(bq[i]) >= 0 else fq[i].slerp(-bq[i], 0.5)
            if q.dot(RQ[i][k]) < 0: q = -q
            RQ2[i][k] = q
    return JP2, RQ2


def sua_glitch_nguon(T, JP, RQ, nJ, G, cha=None):
    """Khung nguồn OUTLIER, xét TỪNG KHỚP (23/10: xét cả khung thì bàn tay đang ném (> 0,25 m/frames thật) phủ quyết việc sửa chân): khớp k nhảy
    > max_m_per_frame so với khung trước RỒI quay về (≤ max_m_per_frame so với khung trước-nhảy) trong ≤ quay_lai_khung khung ⇒ vị trí k lerp,
    xoay của k VÀ của cha(k) slerp qua khoảng nhảy (vị trí con lệch là do xoay cha). Lao thật = lớn nhưng ĐƠN ĐIỆU ⇒ không quay về ⇒ giữ.
    Trả (T, JP, RQ, [[khung_đầu, khung_cuối, số_khớp], ...]) — khung đánh số theo nguồn 30 fps."""
    thr = float(G["max_m_per_frame"]); K_ = int(G["quay_lai_khung"]); n = len(T); sua = {}; cha = cha or [-1] * nJ
    for k in range(nJ):
        i = 1
        while i < n:
            if (JP[i][k] - JP[i - 1][k]).length <= thr: i += 1; continue
            j = next((jj for jj in range(i + 1, min(n, i + K_ + 1)) if (JP[jj][k] - JP[i - 1][k]).length <= thr), None)
            if j is None: i += 1; continue   # không quay về ⇒ chuyển động thật
            j2 = min(n - 1, j + 1)   # khung quay-về: vị trí đã về nhưng XOAY còn lệch (đo 24/10: 145 mm/khung² @R50) ⇒ nội suy xoay tới khung sau nó
            for f in range(i, j):
                u = (f - (i - 1)) / (j - (i - 1)); JP[f][k] = JP[i - 1][k].lerp(JP[j][k], u)
            for f in range(i, j2):
                u = (f - (i - 1)) / (j2 - (i - 1))
                for q_ in {k, cha[k]} - {-1}: RQ[f][q_] = RQ[i - 1][q_].slerp(RQ[j2][q_], u)
            sua.setdefault((i, j - 1), set()).add(k); i = j
    return T, JP, RQ, [[int(round(T[a] * 30)), int(round(T[b] * 30)), len(ks)] for (a, b), ks in sorted(sua.items())]


def nap_motion_profile():
    """assets/motion_profile.json (có version) — mọi ngưỡng của retarget_sam nằm đây, không còn số ma thuật trong code."""
    p = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets", "motion_profile.json"); d = json.load(open(p))
    if d.get("version") != 1: raise SystemExit(f"⛔ motion_profile.json version {d.get('version')} ≠ 1 ({p})")
    return d


def _smootherstep(x):
    x = max(0.0, min(1.0, x)); return x * x * x * (x * (x * 6 - 15) + 10)


def anh_chan_dung_yen(thu, t0, N, Lt, CH):
    """BẰNG CHỨNG ẢNH 2D (MediaPipe pose.json ghi trong khop_video.json): bàn chân (cổ chân·gót·mũi) đứng yên trên ảnh ⇒ đứng yên ngoài đời
    (camera tĩnh) — độc lập với 3D đang trôi (GVHMR trượt chân trụ tới 2 m/s trong khi video thấy đứng yên, PITFALLS #52/#59).
    Tốc độ px/s trên track lọc trung vị ±anh_loc_khung, chuẩn hoá theo chiều dài chân px rồi nhân chiều dài chân đích ⇒ m/s cùng đơn vị ngưỡng.
    Trả {L: [bool]*(N+1), R: [...]} hoặc None khi không có pose."""
    import numpy as np
    kv = os.path.join(thu, "khop_video.json")
    if not os.path.exists(kv): return None
    pz = json.load(open(kv)).get("pose", "")
    if not pz or not os.path.exists(pz): print(f"⚠️ chạm đất: không có pose 2D ({pz}) ⇒ chỉ dùng bằng chứng 3D"); return None
    v = json.load(open(pz)); fv = float(v["fps"]); Wp, Hp = v["w"], v["h"]; fr = v["frames"]
    Lm = np.full((len(fr), 33, 3), np.nan)
    for i, f_ in enumerate(fr):
        if f_.get("people"): Lm[i] = [[p[0] * Wp, p[1] * Hp, p[2]] for p in f_["people"][0]["lm"]]
    leg_px = float(np.nanmedian(np.linalg.norm(Lm[:, 23, :2] - Lm[:, 25, :2], axis=1) + np.linalg.norm(Lm[:, 25, :2] - Lm[:, 27, :2], axis=1)))
    r = int(CH["anh_loc_khung"]); out = {}
    for B, idx in (("L", (27, 29, 31)), ("R", (28, 30, 32))):
        P = Lm[:, idx, :2].copy(); n = len(P)
        Pm = np.array([np.nanmedian(P[max(0, i - r):i + r + 1], axis=0) for i in range(n)])   # lọc trung vị theo thời gian (giết nhảy 1 khung)
        sp = np.zeros(n)
        for i in range(n):
            a_, b_ = max(0, i - 1), min(n - 1, i + 1)
            sp[i] = float(np.nanmedian(np.linalg.norm(Pm[b_] - Pm[a_], axis=1))) * fv / max(1, b_ - a_)
        sp = np.array([np.nanmean(sp[max(0, i - 1):i + 2]) for i in range(n)]) / leg_px * Lt
        tin = np.nanmin(Lm[:, idx, 2], axis=1)
        yen = []
        for f in range(N + 1):
            vf = int(round((t0 + f / FPS) * fv)); vf = max(0, min(n - 1, vf))
            yen.append(bool(np.isfinite(sp[vf]) and sp[vf] < CH["anh_v_mps"] and tin[vf] >= CH["anh_tin_cay"]))
        out[B] = yen
    return out


def doan_cham(P_, z0, yen, yaw_src, huong_hong, CH):
    """①② máy trạng thái TRỄ + neo khung đầu + cắt (= THẢ) khi trôi/xoay. P_: cổ chân FK (thế giới) từng khung; yen: ảnh 2D đứng yên (hoặc None).
    Sau khi thả: mo_khoa_khung khung không được vào đoạn mới (chân mờ khoá rồi mới đặt lại — đặt ngay = dịch chuyển tức thời khi chân còn thấp).
    Trả ([(a, b, neo_xy(Vector), yaw_neo)], trong[bool])."""
    n_ = len(P_)
    v_ = [((P_[min(f + 1, n_ - 1)] - P_[max(f - 1, 0)]) * (FPS / 2)) for f in range(n_)]
    vxy = [math.hypot(v.x, v.y) for v in v_]; vxy = [sum(vxy[max(0, f - 1):f + 2]) / len(vxy[max(0, f - 1):f + 2]) for f in range(n_)]
    h = [p.z - z0 for p in P_]; yen = yen or [False] * n_; cu = bool(os.environ.get("THU_KHONG_HYSTERESIS"))
    yaw_m = [sorted(yaw_src[max(0, f - 2):f + 3])[len(yaw_src[max(0, f - 2):f + 3]) // 2] for f in range(n_)]   # yaw nguồn lọc trung vị 5 khung
    def _neo(a_, b_):
        if os.environ.get("THU_NEO_TRUNG_VI"): b_ = min(b_, a_ + 2)   # thử ngược: neo = trung vị 3 khung đầu (bản P1: chân giật 8–13 cm lúc đặt)
        xs = sorted(P_[k].x for k in range(a_, b_ + 1)); ys = sorted(P_[k].y for k in range(a_, b_ + 1)); return V((xs[len(xs) // 2], ys[len(ys) // 2], z0))
    if cu:   # thử ngược: một ngưỡng (vào = ra), không ảnh, không thả, neo = trung vị CẢ đoạn — hành vi cũ (trượt 422 mm)
        vao = o = lambda f: h[f] <= CH["vao_cao_m"] and vxy[f] < CH["phang_v_mps"]
    else:
        xuong = lambda f: f > 0 and h[f] < h[f - 1] and h[f] <= CH["vao_xuong_cao_m"] and vxy[f] <= CH["ra_v_mps"]   # đang HẠ xuống dưới 6 cm và chậm ⇒ đặt chân (P1-g)
        vao = lambda f: (h[f] <= CH["vao_cao_m"] and vxy[f] <= CH["vao_v_mps"]) or (yen[f] and h[f] <= CH["anh_vao_cao_m"]) or xuong(f)
        o = lambda f: (h[f] <= CH["ra_cao_m"] and vxy[f] <= CH["ra_v_mps"]) or (yen[f] and h[f] <= CH["anh_o_cao_m"])
    doan = []; bat = None; neo = None; khoa_den = 0
    for f in range(n_):
        if bat is None:
            if f >= khoa_den and vao(f): bat = f; neo = _neo(f, min(n_ - 1, f + int(CH["neo_khung"]) - 1))
            continue
        troi = (not cu) and (P_[f] - neo).xy.length > CH["troi_cat_m"] and not yen[f]
        xoay = (not cu) and abs((yaw_m[f] - yaw_m[bat] + math.pi) % (2 * math.pi) - math.pi) > math.radians(CH["xoay_cat_deg"]) and not yen[f]
        if not o(f) or troi or xoay:
            doan.append((bat, f - 1, neo if not cu else _neo(bat, f - 1))); bat = None; khoa_den = f + int(CH["mo_khoa_khung"])
    if bat is not None: doan.append((bat, n_ - 1, neo if not cu else _neo(bat, n_ - 1)))
    doan = [(a_, b_, neo) for a_, b_, neo in doan if b_ - a_ + 1 >= (2 if cu else int(CH["toi_thieu_khung"]))]
    # yaw neo: trung vị yaw nguồn trong đoạn, kẹp ±mui_lech_max_deg quanh hướng hông TẠI KHUNG ĐẦU đoạn (Boss 23/10 «Đồng ý cả hai»: cửa ⑪ so với
    # hướng hông lúc đặt chân, hông được xoay tại chỗ sau đó) ⇒ hết «bàn chân xoay vô»; bản trước lấy trung vị hướng hông cả đoạn ⇒ lệch 54° so với lúc đặt
    ra = []
    for a_, b_, neo in doan:
        ys = sorted(yaw_m[a_:b_ + 1]); y_ = ys[len(ys) // 2]
        yh = math.atan2(huong_hong[a_].y, huong_hong[a_].x)
        d_ = (y_ - yh + math.pi) % (2 * math.pi) - math.pi; lim = math.radians(CH["mui_lech_max_deg"])
        ra.append((a_, b_, neo, yh + max(-lim, min(lim, d_))))
    trong = [False] * n_
    for a_, b_, _, _ in ra:
        for k in range(a_, b_ + 1): trong[k] = True
    return ra, trong


def dich_chan(P_, z0, doan, trong, CH):
    """③ đích cổ chân từng khung: trong đoạn chạm xy = neo, z hạ dần về nền (≤ ha_moi_khung_m/frames); ngoài đoạn: xy theo nguồn, z = max(nguồn,
    nền + bay_ho_m) (chân đang di chuyển không nằm trong nền ⇒ không bị đếm là chạm rồi trượt), lên không nhanh hơn len_moi_khung_m/khung;
    mo_khoa_khung khung sau khi thả: khoá xy mờ dần theo THỜI GIAN × ĐỘ CAO (chân còn sát đất ⇒ còn khoá ⇒ không trượt lúc nhấc)."""
    n_ = len(P_); dich = [None] * n_; chu = [-1] * n_; mk = int(CH["mo_khoa_khung"])
    for i_, (a_, b_, neo, _) in enumerate(doan):
        for k in range(a_, b_ + 1): chu[k] = i_
    if not os.environ.get("THU_KHONG_MUOT_TU_DO"):   # P1-h: chân TỰ DO gia tốc quá mức người (CHAN_RUNG_MAX_MM, hiệu chuẩn walk 48,8 ×1,2) = ước lượng gãy khúc (R50: 1,7→0,7→1,2→2,2 m/s) ⇒ làm mượt cục bộ XY, lặp
        P_ = [p.copy() for p in P_]; gh = CHAN_RUNG_MAX_MM / 1000.0
        for _ in range(4):
            for f in range(1, n_ - 1):
                if chu[f] >= 0 or chu[f - 1] >= 0 or chu[f + 1] >= 0: continue
                if (P_[f + 1] - 2 * P_[f] + P_[f - 1]).xy.length > gh: P_[f] = V(((P_[f - 1].x + P_[f + 1].x) / 2, (P_[f - 1].y + P_[f + 1].y) / 2, P_[f].z))
    for f in range(n_):
        if chu[f] >= 0:
            a_, b_, neo, _ = doan[chu[f]]; h_vao = max(0.0, P_[a_].z - z0); n = f - a_
            z = z0 + min(max(0.0, P_[f].z - z0), max(0.0, h_vao - n * (0.02 if os.environ.get("THU_HA_CHAM") else CH["ha_moi_khung_m"])))   # THU_HA_CHAM=1: hạ 2 cm/frames (bản P1, treo 3 khung)
            dich[f] = V((neo.x, neo.y, z)); continue
        if os.environ.get("THU_KHONG_HYSTERESIS"): dich[f] = V((P_[f].x, P_[f].y, max(P_[f].z, z0))); continue   # thử ngược: chân tự do kẹp đúng nền (bản cũ) ⇒ trượt
        z = max(P_[f].z, z0 + CH["bay_ho_m"])
        if f > 0 and z > dich[f - 1].z + CH["len_moi_khung_m"]: z = dich[f - 1].z + CH["len_moi_khung_m"]   # chỉ hãm lúc LÊN (đuổi theo nguồn đang cao)
        p = V((P_[f].x, P_[f].y, z))
        # (mờ khoá XY lúc RỜI đoạn: chuyển sang hậu kỳ P1-i — neo theo vị trí cổ chân CUỐI đoạn (sau nhón), chỉ theo thời gian: chân rời nhón 3,9 cm bị bản cũ bỏ khoá ngay ⇒ nhảy 10 cm @R80)
        # (giảm tốc XY vào neo TRƯỚC khi đặt: cũng chỉ ở hậu kỳ (P1-j) — bản P1-h/P1-i mờ ở đây về neo PHẲNG rồi hậu kỳ mờ lại về cổ chân NHÓN = hai lần mờ ⇒ 94,1 mm @L46)
        dich[f] = p
    return dich


def hong_muot(ha_can, HG):
    """④ hạ hông = max chạy (cửa sổ cua_so_khung) rồi gaussian sigma_khung, kẹp ha_toi_da_m — mượt, không bao giờ từng khung."""
    n = len(ha_can); r = int(HG["cua_so_khung"]) // 2; env = [max(ha_can[max(0, f - r):f + r + 1]) for f in range(n)]
    s = float(HG["sigma_khung"]); k = [math.exp(-0.5 * (i / s) ** 2) for i in range(-3 * int(math.ceil(s)), 3 * int(math.ceil(s)) + 1)]; k = [x / sum(k) for x in k]; m = len(k) // 2
    out = []
    for f in range(n):
        acc = 0.0
        for i, w in enumerate(k): acc += w * env[max(0, min(n - 1, f + i - m))]
        out.append(min(float(HG["ha_toi_da_m"]), acc))
    return out


def kep_co_tay_sam(rig, b, lb_n, rom, tong_max, f):
    """KẸP CỔ TAY theo biên độ (P1 23/10, cửa ⑭b: Boss «sai với anatomy»): co lại chuyển động cổ tay so với cẳng (slerp về trung tính, chia đôi
    10 lượt) tới khi vuot_co_tay = 0 VÀ góc tổng cẳng↔bàn ≤ tong_max (cửa ⑭). Giữ nguyên vị trí cổ tay. Trả hệ số giữ lại (1 = không kẹp)."""
    pf, ph = rig.pose.bones[f"forearm_{b}"], rig.pose.bones[f"hand_{b}"]; W = rig.matrix_world
    Rf0, Rh0 = rig.data.bones[f"forearm_{b}"].matrix_local.to_3x3().normalized(), rig.data.bones[f"hand_{b}"].matrix_local.to_3x3().normalized(); rel0 = Rf0.inverted() @ Rh0
    Rf = pf.matrix.to_3x3().normalized(); Rh = ph.matrix.to_3x3().normalized(); q = ((Rf.inverted() @ Rh) @ rel0.inverted()).to_quaternion()
    def dat(s_):
        m = (Rf @ Q().slerp(q, s_).to_matrix() @ rel0).to_4x4(); m.translation = ph.matrix.translation; ph.matrix = m; bpy.context.view_layer.update()
    def ok():
        d = co_tay_giai_phau(rig, b, lb_n); fa = (W @ pf.tail) - (W @ pf.head); hd = (W @ ph.tail) - (W @ ph.head)
        return vuot_co_tay(d, rom) <= 0 and math.degrees(fa.angle(hd)) <= tong_max
    if ok(): return 1.0
    lo, hi = 0.0, 1.0
    for _ in range(10):
        s_ = (lo + hi) / 2; dat(s_)
        if ok(): lo = s_
        else: hi = s_
    dat(lo); ph.keyframe_insert("rotation_quaternion", frame=f); return lo


def kiem_khop_sam(rig, N):
    """KIỂM rig SAM ↔ settler mỗi khung: góc lệch HƯỚNG đoạn xương và lệch XOẮN (trục phụ) giữa xương settler và khớp nguồn đã đổi khung (Y·C)."""
    W = rig.matrix_world; sc = bpy.context.scene; lech = {}; xoan = {}
    ten = None
    for f in range(min(N + 1, len(SAM_NGUON))):
        sc.frame_set(f); bpy.context.view_layer.update()
        for b in SAM_MAP:
            if b not in rig.pose.bones or b in ("hips", "head") or b.startswith(("thigh", "shin", "foot")): continue
            M = (W @ rig.pose.bones[b].matrix).to_3x3().normalized(); d_t = M.col[1]
            lech[b] = max(lech.get(b, 0), 0)
    return lech


def keo_tay_giu_xoan(rig, B, d):
    """Dời cổ tay một đoạn d (thế giới) bằng giải 2 đoạn: khuỷu giữ MẶT PHẲNG hiện tại, bắp/cẳng tay chỉ BẺ HƯỚNG tối thiểu từ tư thế đang có
    (giữ nguyên XOẮN — Boss «dont twist arm»), bàn tay giữ nguyên xoay thế giới."""
    W = rig.matrix_world; P = rig.pose.bones; pu, pf, ph = P[f"upperarm_{B}"], P[f"forearm_{B}"], P[f"hand_{B}"]; Mh = (W @ ph.matrix).copy()
    Lu = rig.data.bones[f"upperarm_{B}"].length; Lf = rig.data.bones[f"forearm_{B}"].length
    S_ = W @ pu.head; E0 = W @ pf.head; Wt = (W @ pf.tail) + d; dv = Wt - S_; dl = min(dv.length, Lu + Lf - 1e-4); u = dv.normalized()
    a_ = (Lu * Lu - Lf * Lf + dl * dl) / (2 * dl); r_ = math.sqrt(max(0.0, Lu * Lu - a_ * a_)); C_ = S_ + u * a_
    v_ = (E0 - C_) - u * (E0 - C_).dot(u); v_ = v_.normalized() if v_.length > 1e-5 else u.orthogonal().normalized(); E_ = C_ + v_ * r_
    for pb_, d_ in ((pu, E_ - S_), (pf, (S_ + u * dl) - E_)):
        M0 = (W @ pb_.matrix).to_3x3().normalized(); q_ = M0.col[1].rotation_difference(d_.normalized())
        m = (W.inverted().to_3x3() @ (q_.to_matrix() @ M0)).to_4x4(); m.translation = pb_.matrix.translation; pb_.matrix = m; bpy.context.view_layer.update()
    mh_ = (W.inverted().to_3x3() @ Mh.to_3x3().normalized()).to_4x4(); mh_.translation = ph.matrix.translation; ph.matrix = mh_; bpy.context.view_layer.update()   # CHỈ khôi phục XOAY (gán cả ma trận ⇒ bàn tay bị kéo về cổ tay cũ, tách khỏi cẳng tay)


# ------------------------------------------------------------------ CỔ TAY THEO GIẢI PHẪU (Boss 23/10/2026: «Ko được để cổ tay gập như vầy,
# như vầy là sai với anatomy» — cổ tay bẻ NGANG gắt ở đỉnh cú giơ cuốc, trong khi cửa cũ chỉ đo TỔNG góc cẳng↔bàn ≤ 70° nên lọt)
CO_TAY_ROM = dict(gap=80.0, ngua=70.0, tru=30.0, quay=20.0, xoan=15.0)   # gập về lòng · ngửa ra mu · lệch về NGÓN ÚT (trụ) · về NGÓN CÁI (quay) · xoắn TẠI cổ tay
CO_TAY_BO = dict(gap=25.0, ngua=10.0, tru=25.0, quay=10.0, xoan=15.0)     # pha PHÁT LỰC (bổ/đập): «phải thẳng hoặc cong vô nhẹ so với cánh tay» (Boss 23/10)
NGON_CAI_NGHI = (0.0, -1.0, 0.0)   # tư thế NGHỈ chuẩn (lòng tay hướng vào đùi, kiểm cos 0,89): ngón cái chĩa ra TRƯỚC (−Y armature)


def co_tay_giai_phau(rig, b, lb_n):
    """Tách chuyển động bàn tay so với cẳng tay (tính từ tư thế NGHỈ = cổ tay trung tính) thành gập/ngửa (quanh trục ngang lòng tay),
    lệch ngang (quanh pháp tuyến lòng tay — nhãn vo.long_ban_tay) và xoắn (quanh trục cẳng). gap>0 = về lòng · lech>0 = về NGÓN ÚT, <0 = về NGÓN CÁI."""
    bf, bh = rig.data.bones[f"forearm_{b}"], rig.data.bones[f"hand_{b}"]; pf, ph = rig.pose.bones[f"forearm_{b}"], rig.pose.bones[f"hand_{b}"]
    Rf0, Rh0 = bf.matrix_local.to_3x3().normalized(), bh.matrix_local.to_3x3().normalized()
    Rf, Rh = pf.matrix.to_3x3().normalized(), ph.matrix.to_3x3().normalized()
    M = (Rf.inverted() @ Rh) @ (Rf0.inverted() @ Rh0).inverted()        # chuyển động cổ tay trong khung cẳng tay
    q = M.to_quaternion()
    a = V((0, 1, 0))                                                    # trục dọc cẳng tay (+Y xương)
    n = ((Rf0.inverted() @ Rh0) @ V(lb_n)); n = (n - a * n.dot(a)).normalized(); r = a.cross(n).normalized()
    cai = Rf0.inverted() @ V(NGON_CAI_NGHI)                             # hướng ngón cái lúc nghỉ, trong khung cẳng
    p = V((q.x, q.y, q.z)); pa = a * p.dot(a); tw = Q((q.w, pa.x, pa.y, pa.z)).normalized()
    sw = q @ tw.inverted()
    xoan = math.degrees(tw.angle); xoan = min(xoan, 360 - xoan)
    ax, ang = sw.axis, sw.angle
    if ang > math.pi: ang -= 2 * math.pi
    g = math.degrees(ang * ax.dot(r)); psi = ang * ax.dot(n)            # psi > 0: bàn tay nghiêng về −r
    l = math.degrees(abs(psi)) * (-1 if ((-r) * (1 if psi > 0 else -1)).dot(cai) > 0 else 1)   # về phía ngón cái ⇒ âm
    return dict(gap=round(g, 1), lech=round(l, 1), xoan=round(xoan, 1))


def vuot_co_tay(d, rom=CO_TAY_ROM):
    """độ vượt biên độ (0 = trong biên)."""
    return max(0.0, d["gap"] - rom["gap"], -d["gap"] - rom["ngua"], d["lech"] - rom["tru"], -d["lech"] - rom["quay"], d["xoan"] - rom["xoan"])


# ------------------------------------------------------------------ BÀN CHÂN KHÔNG XOAY VÀO (Boss 23/10/2026: «lúc đi bộ, bàn chân phải nó cứ
# xoay vô, kiểu khó chịu lắm» — đo clip walk Kimodo: chạm đất phải +1,9° VÀO / trái 3,4° RA, lúc vung phải tới 50–75° vào).
# Sửa bằng XOAY CẢ CHÂN quanh trục hông→cổ chân (xoay trong/ngoài khớp háng): cổ chân ĐỨNG YÊN (không trượt), gối xoay theo — đúng giải phẫu.
CHAN_MO_RA = 6.0      # mũi chân mở ra ngoài khi đi (người thật ~5–7°)
CHAN_VAO_MAX = 8.0    # cửa: xoay VÀO ≤ 8° (đo walk: gốc 74,7° → 3,8/7,3°). Ép 0° phải hy sinh độ mượt ⇒ rung (Boss 23/10 chê) — ưu tiên KHÔNG RUNG
CHAN_RA_MAX = 22.0   # mở RA ~20° ở pha vung là tự nhiên (walk sau sửa: 19,6°); cái gây khó chịu là xoay VÀO
CHAN_RUNG_THEM = 3.0  # cửa: đổi tốc xoay đùi (°/khung²) không được vượt clip gốc quá 3


def goc_mui_chan(rig, b, huong):
    """(độ mở RA ngoài so với hướng đi, tỉ lệ ngang). Dương = ra ngoài, âm = VÀO trong."""
    W = rig.matrix_world; pb = rig.pose.bones[f"foot_{b}"]; d = (W @ pb.tail) - (W @ pb.head)
    ngang = V((d.x, d.y, 0)); ti = ngang.length / max(d.length, 1e-9)
    if ngang.length < 1e-6: return 0.0, 0.0
    h = V((huong.x, huong.y, 0)).normalized(); trai = V((0, 0, 1)).cross(h)   # trái của hướng đi
    ben = 1 if (W @ pb.head - W @ rig.pose.bones["hips"].head).dot(trai) > 0 else -1   # chân bên trái hay phải của hướng đi
    goc = math.degrees(math.atan2(ngang.normalized().dot(trai), ngang.normalized().dot(h)))
    return goc * ben, ti


def sua_chan_xoay(rig, f0, f1, mo=CHAN_MO_RA, ti_min=0.5, lo=3.0, hi=14.0, cua_so=2, kep=45.0):
    """Đưa mũi chân về [lo, hi] độ mở RA (chỉ sửa khung lệch khỏi khoảng đó) bằng xoay đùi quanh trục hông→cổ chân. Trả cửa
    {L/R: (vào_max, ra_max)} + {"rung_L/R": (đổi tốc đùi max °/khung², gốc)}.
    v1 (23/10) chọn góc TỪNG KHUNG bằng thử dấu ⇒ đùi giật 44°/frames (gốc ≤11) — Boss «Sao animation này chân bị rung». Giờ: đo trên tư thế
    GỐC (độ dốc góc-mũi/góc-xoay bằng thử ±2°), nội suy khung chân dựng, LÀM MƯỢT Gauss ±cua_so, kẹp ±kep, rồi mới áp một lần."""
    sc = bpy.context.scene; W = rig.matrix_world
    sc.frame_set(f0); h0 = W @ rig.pose.bones["hips"].head; sc.frame_set(f1); h1 = W @ rig.pose.bones["hips"].head
    huong = (h1 - h0); huong.z = 0; huong.normalize()
    def xoay(pt, hip, ax, deg, Mw):
        pt.matrix = W.inverted() @ (mathutils.Matrix.Translation(hip) @ mathutils.Matrix.Rotation(math.radians(deg), 4, ax) @ mathutils.Matrix.Translation(-hip) @ Mw)
        bpy.context.view_layer.update()
    def toc_dui(b):
        prev = None; v = []
        for f in range(f0, f1 + 1):
            sc.frame_set(f); q = (W @ rig.pose.bones[f"thigh_{b}"].matrix).to_quaternion()
            if prev is not None: a_ = math.degrees(prev.rotation_difference(q).angle); v.append(min(a_, 360 - a_))
            prev = q
        return max((abs(v[i] - v[i - 1]) for i in range(1, len(v))), default=0.0)
    goc_rung = {b: toc_dui(b) for b in ("L", "R")}
    for b in ("L", "R"):
        can = {}
        for f in range(f0, f1 + 1):   # 1) đo trên tư thế gốc
            sc.frame_set(f); bpy.context.view_layer.update(); pt = rig.pose.bones[f"thigh_{b}"]; pt.rotation_mode = "QUATERNION"
            g0, ti = goc_mui_chan(rig, b, huong)
            if ti < ti_min: continue
            dich = (lo + 1 if g0 < lo else hi - 1 if g0 > hi else g0) - g0
            if dich == 0: can[f] = 0.0; continue
            hip = W @ pt.head; ax = ((W @ rig.pose.bones[f"foot_{b}"].head) - hip).normalized(); Mw = W @ pt.matrix
            xoay(pt, hip, ax, 2.0, Mw); g1, _ = goc_mui_chan(rig, b, huong); pt.matrix = W.inverted() @ Mw; bpy.context.view_layer.update()
            doc = (g1 - g0) / 2.0
            if abs(doc) > 0.3: can[f] = max(-kep, min(kep, dich / doc))
        ks = sorted(can)
        if not ks: continue
        day = {}
        for f in range(f0, f1 + 1):   # 2) nội suy + làm mượt
            if f in can: day[f] = can[f]; continue
            a = max([k for k in ks if k < f], default=None); c = min([k for k in ks if k > f], default=None)
            day[f] = can[a] if c is None else can[c] if a is None else can[a] + (can[c] - can[a]) * (f - a) / (c - a)
        mu = {}
        for f in day:
            ws = [(math.exp(-0.5 * ((k - f) / (cua_so / 2)) ** 2), day[k]) for k in range(max(f0, f - cua_so), min(f1, f + cua_so) + 1)]
            mu[f] = sum(w * x for w, x in ws) / sum(w for w, _ in ws)
        truoc = None
        for f in range(f0, f1 + 1):   # 3) áp một lần, quaternion liên tục
            sc.frame_set(f); bpy.context.view_layer.update(); pt = rig.pose.bones[f"thigh_{b}"]
            hip = W @ pt.head; ax = ((W @ rig.pose.bones[f"foot_{b}"].head) - hip).normalized()
            xoay(pt, hip, ax, mu[f], W @ pt.matrix)
            if truoc is not None and pt.rotation_quaternion.dot(truoc) < 0: pt.rotation_quaternion = -pt.rotation_quaternion
            truoc = pt.rotation_quaternion.copy(); pt.keyframe_insert("rotation_quaternion", frame=f)
    cua = do_chan_xoay(rig, f0, f1)
    for b in ("L", "R"): cua[f"rung_{b}"] = (round(toc_dui(b), 1), round(goc_rung[b], 1))
    return cua


def do_chan_xoay(rig, f0, f1):
    """CHỈ ĐO (không sửa): {L/R: (vào_max, ra_max)} trên khung tỉ lệ ngang ≥ 0,5 — dùng cho thử ngược cửa ㉑."""
    sc = bpy.context.scene; W = rig.matrix_world
    sc.frame_set(f0); h0 = W @ rig.pose.bones["hips"].head; sc.frame_set(f1); h1 = W @ rig.pose.bones["hips"].head
    huong = (h1 - h0); huong.z = 0; huong.normalize(); cua = {}
    for b in ("L", "R"):
        gs = []
        for f in range(f0, f1 + 1):
            sc.frame_set(f); g, ti = goc_mui_chan(rig, b, huong)
            if ti >= 0.5: gs.append(g)
        cua[b] = (round(max(0.0, -min(gs)), 1), round(max(gs), 1)) if gs else (0.0, 0.0)
    return cua


# ------------------------------------------------------------------ ẨN DA DƯỚI QUẦN ÁO (Boss 23/10/2026: «Đùi sau có vệt trắng là gì?» — da thân lòi
# qua quần ở nếp mông-đùi khi chân duỗi ra sau; có sẵn trong clip gốc). Chuẩn game: xoá mặt da bị đồ PHỦ KÍN (không bao giờ thấy) ⇒ không còn gì để lòi.
DA_PHU_QUAN = ("thigh_L", "thigh_R", "shin_L", "shin_R", "foot_L", "foot_R")


def an_da_duoi_do(than, xuong=DA_PHU_QUAN):
    """xoá mặt của lưới thân có xương trọng số lớn nhất thuộc `xuong` (mọi đỉnh của mặt). Trả số mặt đã xoá."""
    import bmesh as _bm
    gi = {g.index: g.name for g in than.vertex_groups}
    tro = [gi.get(max(v.groups, key=lambda e: e.weight).group) if v.groups else None for v in than.data.vertices]
    bm = _bm.new(); bm.from_mesh(than.data); bm.faces.ensure_lookup_table()
    xoa = [f for f in bm.faces if all(tro[v.index] in xuong for v in f.verts)]
    _bm.ops.delete(bm, geom=xoa, context="FACES"); bm.to_mesh(than.data); bm.free(); than.data.update()
    return len(xoa)

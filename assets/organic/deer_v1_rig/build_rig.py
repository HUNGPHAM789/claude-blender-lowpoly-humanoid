"""Rig + animation cho NAI low-poly (deer_v1/deer.glb) — Boss 23/10/2026: «Rồi giờ tới săn nai. Animation cho nai - ăn cỏ idle, đi bộ, chạy,
chết - có dùng kimodo ko?» ⇒ KHÔNG: Kimodo chỉ có khung NGƯỜI (somaskel30/77, smplx22) + robot G1, không có thú 4 chân. Làm bằng CODE theo
khuôn rabbit_v1_rig (khung xương từ khối plan, heat weight + làm sạch theo capsule + luật đường giữa), thêm KHOÁ MÓNG bằng IK 2 đoạn.
  blender -b -P build_rig.py  ⇒  deer_rig.blend · deer_rigged.glb · checks.json · <action>.mp4 (render_loops riêng)
Quy ước: Blender Z lên, nai nhìn −Y, trái của nai = +X (.L). Mỗi xương roll sao cho X cục bộ = +X thế giới ⇒ xoay quanh X cục bộ = gật (pitch).
Exit 1 nếu cửa trượt."""
import bpy, bmesh, json, math, os, sys
from mathutils import Vector as V, Matrix as M4, Quaternion as Q
from mathutils.bvhtree import BVHTree

HERE = os.path.dirname(os.path.abspath(__file__)); SRC = os.path.join(HERE, "..", "deer_v1", "deer.glb"); FPS = 24
S = 0.8572583964950211   # plan → lưới (deer_report.json normalize.scale)


def P(x, y, z): return V((S * x, -S * y, S * z))   # plan (+Y trước) → Blender (−Y trước)


# ---------------------------------------------------------------- nhập + hàn
bpy.ops.wm.read_factory_settings(use_empty=True); sc = bpy.context.scene; sc.render.fps = FPS
bpy.ops.import_scene.gltf(filepath=SRC)
for o in list(bpy.data.objects):
    if o.parent: mw = o.matrix_world.copy(); o.parent = None; o.matrix_world = mw
bpy.data.objects.remove(bpy.data.objects["world"])
than_p = [o for o in bpy.data.objects if o.name.startswith("body_")]; mat = sorted([o for o in bpy.data.objects if o.name.startswith("eye_")], key=lambda o: o.matrix_world.translation.x)
bpy.ops.object.select_all(action="DESELECT")
for o in than_p: o.select_set(True)
bpy.context.view_layer.objects.active = than_p[0]; bpy.ops.object.join(); than = bpy.context.view_layer.objects.active; than.name = "deer_body"
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
bm = bmesh.new(); bm.from_mesh(than.data); bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5); bm.to_mesh(than.data); bm.free()
for p in than.data.polygons: p.use_smooth = False
for e in mat:
    bpy.ops.object.select_all(action="DESELECT"); e.select_set(True); bpy.context.view_layer.objects.active = e; bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
mat[0].name, mat[1].name = "deer_eye.R", "deer_eye.L"
print("THAN đỉnh", len(than.data.vertices), "mặt", len(than.data.polygons))

# ---------------------------------------------------------------- khung xương (từ khối plan)
XUONG = {   # tên: (đầu, đuôi, cha)
    "root": (V((0, 0, 0)), V((0, 0, 0.2)), None),
    "pelvis": (P(0, -0.22, 0.58), P(0, 0, 0.56), "root"),
    "spine": (P(0, 0, 0.56), P(0, 0.2, 0.57), "pelvis"),
    "chest": (P(0, 0.2, 0.57), P(0, 0.26, 0.62), "spine"),
    "neck": (P(0, 0.26, 0.62), P(0, 0.40, 0.84), "chest"),
    "head": (P(0, 0.40, 0.84), P(0, 0.57, 0.81), "neck"),
    "tail": (P(0, -0.33, 0.62), P(0, -0.39, 0.55), "pelvis"),
}
for s, sx in (("L", 1), ("R", -1)):
    XUONG.update({
        f"ear.{s}": (P(sx * 0.045, 0.41, 0.89), P(sx * 0.075, 0.41, 0.975), "head"),
        f"upperarm.{s}": (P(sx * 0.07, 0.23, 0.50), P(sx * 0.065, 0.25, 0.26), "chest"),
        f"forearm.{s}": (P(sx * 0.065, 0.25, 0.26), P(sx * 0.06, 0.24, 0.035), f"upperarm.{s}"),
        f"fhoof.{s}": (P(sx * 0.06, 0.24, 0.035), P(sx * 0.06, 0.275, 0.0), f"forearm.{s}"),
        f"thigh.{s}": (P(sx * 0.075, -0.24, 0.52), P(sx * 0.07, -0.31, 0.28), "pelvis"),
        f"shank.{s}": (P(sx * 0.07, -0.31, 0.28), P(sx * 0.065, -0.26, 0.035), f"thigh.{s}"),
        f"hhoof.{s}": (P(sx * 0.065, -0.26, 0.035), P(sx * 0.065, -0.225, 0.0), f"shank.{s}"),
    })
arm = bpy.data.armatures.new("deer_rig"); rig = bpy.data.objects.new("deer_rig", arm); sc.collection.objects.link(rig)
bpy.context.view_layer.objects.active = rig; bpy.ops.object.mode_set(mode="EDIT")
for ten, (h, t, cha) in XUONG.items():
    eb = arm.edit_bones.new(ten); eb.head, eb.tail = h, t
    d = (t - h).normalized(); z = V((1, 0, 0)).cross(d)
    eb.align_roll(z if z.length > 1e-3 else V((0, 1, 0)))   # X cục bộ = +X thế giới
    eb.use_deform = ten != "root"
for ten, (h, t, cha) in XUONG.items():
    if cha: arm.edit_bones[ten].parent = arm.edit_bones[cha]; arm.edit_bones[ten].use_connect = False
bpy.ops.object.mode_set(mode="OBJECT")

# ---------------------------------------------------------------- trọng số: heat → dọn theo capsule + đường giữa → gạc = đầu
bpy.ops.object.select_all(action="DESELECT"); than.select_set(True); rig.select_set(True); bpy.context.view_layer.objects.active = rig
bpy.ops.object.parent_set(type="ARMATURE_AUTO")
R_CAP = {"upperarm": 0.075, "forearm": 0.045, "fhoof": 0.04, "thigh": 0.10, "shank": 0.045, "hhoof": 0.04, "ear": 0.05, "tail": 0.06}
def kc_doan(p, a, b):
    ab = b - a; t = max(0.0, min(1.0, (p - a).dot(ab) / ab.length_squared)); return (p - (a + ab * t)).length
gi = {g.index: g.name for g in than.vertex_groups}; bo = 0
mi_gac = [i for i, m in enumerate(than.data.materials) if m and m.name.startswith("antler")]
gac = {v for p in than.data.polygons if p.material_index in mi_gac for v in p.vertices}
for v in than.data.vertices:
    for e in list(v.groups):
        ten = gi[e.group]; goc = ten.split(".")[0]
        if goc in R_CAP:
            h, t, _ = XUONG[ten]
            if kc_doan(v.co, h, t) > R_CAP[goc] * 1.5 or (ten.endswith(".L") and v.co.x < -0.012) or (ten.endswith(".R") and v.co.x > 0.012):
                than.vertex_groups[ten].remove([v.index]); bo += 1
for i in gac:
    for g in than.vertex_groups: g.remove([i])
    than.vertex_groups["head"].add([i], 1.0, "REPLACE")
trong = [v for v in than.data.vertices if not v.groups]
for v in trong:   # gán xương gần nhất cùng phía
    tot = min(((kc_doan(v.co, h, t), ten) for ten, (h, t, _) in XUONG.items() if ten != "root" and not (ten.endswith(".L") and v.co.x < -0.012) and not (ten.endswith(".R") and v.co.x > 0.012)))
    than.vertex_groups[tot[1]].add([v.index], 1.0, "REPLACE")
bpy.context.view_layer.objects.active = than
bpy.ops.object.vertex_group_clean(group_select_mode="ALL", limit=0.01); bpy.ops.object.vertex_group_limit_total(group_select_mode="ALL", limit=4); bpy.ops.object.vertex_group_normalize_all(lock_active=False)
print("TRONG_SO bỏ", bo, "· gán lại", len(trong), "· còn trống", sum(1 for v in than.data.vertices if not v.groups))
for e in mat:
    mw = e.matrix_world.copy(); e.parent = rig; e.parent_type = "BONE"; e.parent_bone = "head"; bpy.context.view_layer.update(); e.matrix_world = mw

# ---------------------------------------------------------------- công cụ tư thế
W = rig.matrix_world; PB = rig.pose.bones
for pb in PB: pb.rotation_mode = "QUATERNION"


def nghi():
    for pb in PB: pb.location = V(); pb.rotation_quaternion = Q(); pb.scale = V((1, 1, 1))
    bpy.context.view_layer.update()


def quay(ten, deg, truc=(1, 0, 0)):   # xoay CỘNG THÊM quanh trục cục bộ (X = gật)
    pb = PB[ten]; pb.rotation_quaternion = pb.rotation_quaternion @ Q(V(truc), math.radians(deg))


def dat_mat(ten, Rw):
    pb = PB[ten]; m = (W.inverted().to_3x3() @ Rw).to_4x4(); m.translation = pb.matrix.translation; pb.matrix = m; bpy.context.view_layer.update()


def goc_root(dich, quay_y=0.0, quay_x=0.0):   # root: dời thế giới + lăn quanh trục thân (Y) + chúc quanh X
    pb = PB["root"]; R = (M4.Rotation(math.radians(quay_y), 4, "Y") @ M4.Rotation(math.radians(quay_x), 4, "X"))
    m = M4.Translation(dich) @ R @ pb.bone.matrix_local; pb.matrix = W.inverted() @ m; bpy.context.view_layer.update()


def ik_chan(tren, duoi, dich, pole):
    """IK 2 đoạn đóng: đặt hướng xương trên/dưới sao cho đuôi xương dưới (cổ móng) tới `dich`; khớp giữa gần `pole`."""
    pu, pl = PB[tren], PB[duoi]; S_ = W @ pu.head; Lu, Ll = pu.bone.length, pl.bone.length
    d = min(max((dich - S_).length, abs(Lu - Ll) + 1e-4), 0.999 * (Lu + Ll)); u = (dich - S_).normalized()
    a = (Lu * Lu - Ll * Ll + d * d) / (2 * d); r = math.sqrt(max(0.0, Lu * Lu - a * a)); v = (pole - u * pole.dot(u)).normalized(); E = S_ + u * a + v * r
    for pb, huong in ((pu, E - S_), (pl, (S_ + u * d) - E)):
        M0 = (W @ pb.matrix).to_3x3().normalized(); dat_mat(pb.name, Q(M0.col[1].rotation_difference(huong.normalized())).to_matrix() @ M0)
    return (W @ pl.tail - dich).length


CHAN = {f"F{s}": (f"upperarm.{s}", f"forearm.{s}", f"fhoof.{s}", V((0, -1, 0.2))) for s in "LR"}   # gối trước (cổ tay) gập ⇒ khớp dồn ra TRƯỚC
CHAN.update({f"H{s}": (f"thigh.{s}", f"shank.{s}", f"hhoof.{s}", V((0, 1, 0.2))) for s in "LR"})   # khoeo sau chĩa ra SAU
nghi(); CO_MONG0 = {k: (W @ PB[d].tail).copy() for k, (t_, d, m_, p_) in CHAN.items()}
MONG_R0 = {k: (W @ PB[m_].matrix).to_3x3().copy() for k, (t_, d, m_, p_) in CHAN.items()}


def de_mong(k, nhac=0.0):   # móng: giữ hướng nghỉ (phẳng đất); lúc vung gập mũi móng ra sau theo độ nhấc
    m_ = CHAN[k][2]; R = MONG_R0[k]
    if nhac > 0: R = M4.Rotation(math.radians(55 * nhac) * (1 if k[0] == "F" else 1), 3, V((1, 0, 0))) @ R
    dat_mat(m_, R)


def chot(f, tat_ca=True):
    for pb in PB:
        pb.keyframe_insert("rotation_quaternion", frame=f)
        if pb.name == "neck": pb.keyframe_insert("scale", frame=f)
        if pb.name == "root": pb.keyframe_insert("location", frame=f)


def hanh_dong(ten):
    rig.animation_data_create(); a = bpy.data.actions.new(ten); a.use_fake_user = True; rig.animation_data.action = a; return a


# ---------------------------------------------------------------- DÁNG ĐI / CHẠY: chu kỳ T khung, vận tốc v, pha từng chân, tỉ lệ chạm đất β
def dang(ten, T, v, pha, beta, nhac, nhun=0.0, cui=0.0, gap_than=0.0, chuc=0.0, ha=0.0):
    hanh_dong(ten); L = v * T * beta / FPS; TRUOC = V((0, -1, 0)); mong = {}
    for f in range(0, T + 1):
        nghi(); x = v * f / FPS; u0 = f / T
        z_than = nhun * math.cos(4 * math.pi * u0) if nhun else 0.0
        goc_root(TRUOC * x + V((0, 0, z_than - ha)), quay_x=chuc * math.sin(2 * math.pi * u0))   # ha: hạ thân cho chân hơi chùng (chân thẳng ⇒ đầu/cuối pha chạm ngoài tầm với ⇒ móng trượt)
        if gap_than: quay("pelvis", gap_than * math.sin(2 * math.pi * u0)); quay("chest", -gap_than * math.sin(2 * math.pi * u0))
        quay("neck", cui * math.sin(4 * math.pi * u0)); quay("head", -0.6 * cui * math.sin(4 * math.pi * u0))
        quay("tail", 8 * math.sin(2 * math.pi * u0)); bpy.context.view_layer.update()
        for k in ("FL", "FR", "HL", "HR"):
            u = (u0 + pha[k]) % 1.0
            if u < beta: dd = L / 2 - L * u / beta; h = 0.0; nh = 0.0
            else: s = (u - beta) / (1 - beta); e = s * s * (3 - 2 * s); dd = -L / 2 + L * e; h = nhac * math.sin(math.pi * s); nh = math.sin(math.pi * s)
            dich = CO_MONG0[k] + TRUOC * (x + dd) + V((0, 0, h))
            ik_chan(CHAN[k][0], CHAN[k][1], dich, (W @ PB[CHAN[k][0]].head) + CHAN[k][3] - (W @ PB[CHAN[k][0]].head) * 0 - (W @ PB[CHAN[k][0]].head) + V() if False else CHAN[k][3])
            de_mong(k, nh); mong.setdefault(k, []).append((f, u < beta, (W @ PB[CHAN[k][1]].tail).copy()))
        chot(f)
    return mong


PHA_DI = {"HL": 0.0, "FL": 0.25, "HR": 0.5, "FR": 0.75}            # đi 4 nhịp kiểu hươu nai (sau trái → trước trái → sau phải → trước phải)
PHA_CHAY = {"HL": 0.0, "HR": 0.08, "FL": 0.42, "FR": 0.52}          # phi nước đại xoay (rotary gallop), có pha lơ lửng
MONG = {}
# sải theo TỈ LỆ CHÂN (~0,40 m): v1 đi 1,1 m/s (sải 0,97 m), chạy 5 m/s ⇒ móng trượt 33 / 108 mm/frames
MONG["walk"] = dang("walk", 28, 0.45, PHA_DI, 0.62, 0.06, nhun=0.006, cui=4.0, ha=0.035)
MONG["run"] = dang("run", 12, 2.3, PHA_CHAY, 0.25, 0.13, nhun=0.025, cui=6.0, gap_than=9.0, chuc=4.0, ha=0.06)

# ---------------------------------------------------------------- ĂN CỎ (idle lặp 96): cúi mõm sát đất, dứt cỏ, vẫy đuôi, giật tai, ngẩng nhìn rồi cúi lại
hanh_dong("graze")
def mom(): return W @ PB["head"].tail
TL_DAU = -0.1   # đầu NGỬA nhẹ ngược cổ để mõm chúc xuống đất (+0,7 cùng chiều ⇒ mặt cuộn vào ngực, gạc chĩa trước)


def cui_toi(dz_dich, cap=1.0, truoc=None):
    """QUÉT góc cổ 0–90° bước 2°, lấy góc ĐẦU TIÊN đưa mõm xuống ≤ dz_dich mà lưới không lún đất. v2 chia đôi trên 0–110°:
    độ cao mõm KHÔNG đơn điệu (quá ngưỡng đầu cuộn vào dưới ngực, mõm lên lại) ⇒ chọn nhầm, đầu cắm đất."""
    nghi_co(); z0 = mom().z; quay("neck", 20); bpy.context.view_layer.update(); dau = 1.0 if mom().z < z0 else -1.0; DAU_CO[0] = dau
    tot = (9.0, 0.0)
    for g in range(0, 102, 2):
        nghi_co(); quay("neck", dau * g * cap); quay("head", dau * TL_DAU * g * cap); bpy.context.view_layer.update()
        dg = bpy.context.evaluated_depsgraph_get(); oe = than.evaluated_get(dg); me = oe.to_mesh(); zmin = min((than.matrix_world @ v.co).z for v in me.vertices); oe.to_mesh_clear()
        if zmin < -0.005: break
        tot = min(tot, (abs(mom().z - dz_dich), float(g)))
        if mom().z <= dz_dich: break
    return tot[1]


def nghi_co(keo=None):
    for b in ("neck", "head"): PB[b].rotation_quaternion = Q()
    PB["neck"].scale = V((1, KEO_CO if keo is None else keo, 1)); bpy.context.view_layer.update()


# CHÚI THÂN khi ăn: gốc cổ cao 0,53 m > cổ + đầu ~0,37 m ⇒ chỉ gập cổ thì mõm không tới đất (v2: kịch 95°, mõm 31 cm).
# Nai thật chúi thân trước + chân trước hơi khuỵu: chúi root, hạ thân, rồi IK 4 chân về chỗ móng cũ.
def chui(psi, ha):
    goc_root(V((0, 0, -ha)), quay_x=psi)
    for k in ("FL", "FR", "HL", "HR"): ik_chan(CHAN[k][0], CHAN[k][1], CO_MONG0[k], CHAN[k][3]); de_mong(k)
nghi(); z_ng = (W @ PB["chest"].head).z; chui(8, 0.0); DAU_CHUI = 1.0 if (W @ PB["chest"].head).z < z_ng else -1.0; nghi()
PSI, HA_AN = 10 * DAU_CHUI, 0.03
KEO_CO = 1.5   # cổ DÀI ra khi ăn (cổ lưới ngắn ⇒ chúi 18° thì chân trước khuỵu như quỳ)
DAU_CO = [1.0]; nghi(); chui(PSI, HA_AN); G_CO = cui_toi(0.025); G_CO *= DAU_CO[0]
print("AN_CO gật cổ", round(G_CO, 1), "° để mõm 2,5 cm trên đất")
MOM_Z = []
for f in range(0, 97):
    nghi(); u = f / 96
    ngang = 0.0
    if 54 <= f <= 80: s0 = (f - 54) / 26; ng0 = math.sin(math.pi * s0) ** 0.6
    else: ng0 = 0.0
    chui(PSI * (1 - ng0), HA_AN * (1 - ng0))   # ngẩng nhìn quanh ⇒ thân cũng đứng lên
    if 54 <= f <= 80: s = (f - 54) / 26; ngang = math.sin(math.pi * s) ** 0.6   # ngẩng lên nhìn quanh
    g = G_CO * (1 - ngang) + (-8.0 * DAU_CO[0]) * ngang
    if ngang < 0.05: g -= DAU_CO[0] * 3.0 * max(0.0, math.sin(2 * math.pi * f / 12))   # dứt cỏ: giật lên nhẹ   # dứt cỏ: giật cổ lên nhẹ mỗi 12 khung
    PB["neck"].scale = V((1, 1 + (KEO_CO - 1) * (1 - ng0), 1)); quay("neck", g); quay("head", TL_DAU * g)
    if ngang > 0: quay("head", 18 * ngang * math.sin(2 * math.pi * (f - 54) / 26), (0, 0, 1))
    quay("tail", 25 * max(0.0, math.sin(2 * math.pi * (f - 28) / 10)) if 28 <= f <= 38 else 0.0)
    if 44 <= f <= 50: quay("ear.L", -30 * math.sin(math.pi * (f - 44) / 6))
    quay("chest", 1.2 * math.sin(2 * math.pi * f / 48)); bpy.context.view_layer.update()   # thở
    giat = max(0.0, math.sin(2 * math.pi * f / 12))
    MOM_Z.append(mom().z if (ngang < 0.05 and giat < 0.05) else None); chot(f)   # đo ở ĐÁY nhịp dứt cỏ (lúc ngậm cỏ); nhịp giật nhấc mõm là cố ý

# ---------------------------------------------------------------- CHẾT (48): trúng tên giật mình → khuỵu chân trước → sụp chân sau → đổ nghiêng → gục đầu
hanh_dong("death")
def ease(s): s = max(0.0, min(1.0, s)); return s * s * (3 - 2 * s)
for f in range(0, 49):
    nghi(); a = ease((f - 4) / 12); b = ease((f - 10) / 12); c = ease((f - 18) / 16); d = ease((f - 28) / 14)
    if f < 6: quay("neck", -10 * math.sin(math.pi * f / 6)); quay("head", -8 * math.sin(math.pi * f / 6))   # giật mình
    for s in "LR":
        quay(f"upperarm.{s}", -35 * a); quay(f"forearm.{s}", 110 * a); quay(f"fhoof.{s}", 40 * a)           # khuỵu chân trước
        quay(f"thigh.{s}", 30 * b); quay(f"shank.{s}", -70 * b); quay(f"hhoof.{s}", -30 * b)               # sụp chân sau
        quay(f"upperarm.{s}", 35 * a * c + 20 * c); quay(f"forearm.{s}", -110 * a * c + 20 * c)           # nằm rồi: chân duỗi dần
        quay(f"thigh.{s}", -30 * b * c - 15 * c); quay(f"shank.{s}", 70 * b * c + 15 * c)
    quay("neck", 25 * a - 10 * d); quay("head", 10 * d); quay("ear.L", 30 * d); quay("ear.R", 30 * d); quay("tail", -20 * d)
    goc_root(V((0.18 * c, 0, 0)), quay_y=-86 * c)
    # kẹp sàn: điểm thấp nhất của lưới = 0 (không lún, không lơ lửng khi đã nằm)
    dg = bpy.context.evaluated_depsgraph_get(); oe = than.evaluated_get(dg); me = oe.to_mesh(); zmin = min((than.matrix_world @ v.co).z for v in me.vertices); oe.to_mesh_clear()
    if zmin < 0 or c > 0.5: goc_root(V((0.18 * c, 0, -zmin)), quay_y=-86 * c)
    chot(f)

# ---------------------------------------------------------------- CỬA
def tg_than():
    dg = bpy.context.evaluated_depsgraph_get(); oe = than.evaluated_get(dg); me = oe.to_mesh()
    P_ = [than.matrix_world @ v.co for v in me.vertices]; F_ = [tuple(p.vertices) for p in me.polygons]; oe.to_mesh_clear(); return P_, F_
def the_tich(P_, F_):
    bm = bmesh.new(); vs = [bm.verts.new(p) for p in P_]
    for f_ in F_:
        try: bm.faces.new([vs[i] for i in f_])
        except ValueError: pass
    v = abs(bm.calc_volume()); bm.free(); return v
nghi(); rig.animation_data.action = None; nghi(); P0, F0 = tg_than(); V0 = the_tich(P0, F0)
CUA = {}; DAT = True
for ten, T in (("walk", 28), ("run", 12), ("graze", 96), ("death", 48)):
    rig.animation_data.action = bpy.data.actions[ten]
    if rig.animation_data.action.slots: rig.animation_data.action_slot = rig.animation_data.action.slots[0]
    zmin = 9.0; dvol = 0.0
    for f in range(0, T + 1):
        sc.frame_set(f); P_, F_ = tg_than(); zmin = min(zmin, min(p.z for p in P_)); dvol = max(dvol, abs(the_tich(P_, F_) / V0 - 1))
    cu = {"lun_dat_mm": round(min(0.0, zmin) * 1000, 1), "the_tich_doi_pct": round(dvol * 100, 1)}
    if ten in MONG:   # móng trượt khi chạm đất (thế giới, sau khi đánh giá lại hành động)
        tr = 0.0
        for k, ds in MONG[ten].items():
            dang_cham = [p for (f, c, p) in ds if c]
            ky = []
            for (f, c, p) in ds:
                if c: sc.frame_set(f); ky.append((f, (W @ PB[CHAN[k][1]].tail).copy()))
            for (f1, p1), (f2, p2) in zip(ky, ky[1:]):
                if f2 == f1 + 1: tr = max(tr, (V((p2.x, p2.y, 0)) - V((p1.x, p1.y, 0))).length)
        cu["mong_truot_mm_khung"] = round(tr * 1000, 1)
    if ten in ("walk", "run", "graze"):   # lặp liền mạch: khung cuối = khung đầu (trừ dời root khi đi/chạy)
        sc.frame_set(0); a0 = {pb.name: pb.matrix.copy() for pb in PB if pb.name != "root"}
        sc.frame_set(T); cu["noi_vong"] = round(max((a0[n].to_quaternion().rotation_difference(PB[n].matrix.to_quaternion()).angle for n in a0)), 4)
    if ten == "graze": cu["mom_cao_max_mm"] = round(max(z for z in MOM_Z if z is not None) * 1000, 1)
    ok = cu["lun_dat_mm"] >= -10 and cu["the_tich_doi_pct"] <= 18 and cu.get("mong_truot_mm_khung", 0) <= 10 and cu.get("noi_vong", 0) <= 0.02 and cu.get("mom_cao_max_mm", 0) <= 40
    cu["dat"] = bool(ok); DAT = DAT and ok; CUA[ten] = cu; print("CUA", ten, json.dumps(cu, ensure_ascii=False))
json.dump(CUA, open(os.path.join(HERE, "checks.json"), "w"), indent=1, ensure_ascii=False)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, "deer_rig.blend"))
try:
    bpy.ops.object.select_all(action="DESELECT"); rig.select_set(True); than.select_set(True)
    for e in mat: e.select_set(True)
    bpy.ops.export_scene.gltf(filepath=os.path.join(HERE, "deer_rigged.glb"), use_selection=True, export_animations=True, export_animation_mode="ACTIONS")
except Exception as ex: print("GLB lỗi", ex)
print("✅ ĐẠT nai" if DAT else "⛔ TRƯỢT nai"); sys.exit(0 if DAT else 1)

"""CLI skill humanoid-rig-animation (chạy trong Blender):
  blender -b -P animate.py -- build    --profile <rig-profile.json> --gioi nam|nu --toc <màu> --clip <clip.json> --out <dir>
  blender -b -P animate.py -- retarget --profile <rig-profile.json> --gioi nam|nu --toc <màu> --clip <clip.json> --bvh <file.bvh> --out <dir>
Ra: <dir>/<id>.mp4 · <id>.glb · <id>_gates.json ; exit 1 nếu cửa trượt (kể cả cửa ⓪ trục giải phẫu)."""
import bpy, sys, os, json, math, argparse, mathutils
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import humanoid_anim as H
V = mathutils.Vector; M4 = mathutils.Matrix

a = sys.argv[sys.argv.index("--") + 1:]
ap = argparse.ArgumentParser(); ap.add_argument("lenh"); ap.add_argument("--profile", required=True); ap.add_argument("--gioi", default="nam")
ap.add_argument("--toc", default="dark_brown"); ap.add_argument("--clip", required=True); ap.add_argument("--out", required=True); ap.add_argument("--bvh"); ap.add_argument("--mp"); ap.add_argument("--tu", type=float, default=0); ap.add_argument("--den", type=float, default=1e9)
g = ap.parse_args(a); os.makedirs(g.out, exist_ok=True)
P = json.load(open(g.profile)); CP = P["gioi"][g.gioi]; clip = json.load(open(g.clip))
for k in ("joints",):
    clip[k] = {x: {float(f): v for f, v in ks.items()} for x, ks in clip.get(k, {}).items()}
clip["pelvis"] = {float(f): v for f, v in clip.get("pelvis", {}).items()}

bpy.ops.wm.read_factory_settings(use_empty=True); sc = bpy.context.scene; sc.render.fps = H.FPS
G = json.load(open(os.path.expanduser(CP["geom"]))); K = {k: V(v) for k, v in G["khop"].items()}; SK = G["socket"]
than = H.nhap(os.path.expanduser(CP["than"]))[0]; toc = H.nhap(os.path.expanduser(CP["toc"].format(mau={"nau_dam": "dark_brown", "den": "black", "hat_de": "chestnut"}.get(g.toc, g.toc)))); do = H.nhap(os.path.expanduser(CP["do"]))
NGA = bpy.data.materials.new("nga"); NGA.use_nodes = True; NGA.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = tuple(P.get("mau_da", (0.80, 0.66, 0.52, 1)))
# GIỮ vật liệu gốc của body build (da theme «Đất ấm» Body_Ivory + hốc mắt C Socket_Shade) — Boss 23/10/2026: «sao settler thấy bị
# mất con mắt rồi, tôi nhớ là đen mờ mà phải ko?»: bản cũ đè MỌI vật liệu trừ tên chứa eye/dark ⇒ Socket_Shade thành da, mất mắt ở mọi clip.
GIU_VL = ("eye", "dark") if os.environ.get("THU_MAT_CU") else ("eye", "dark", "socket", "shade", "body_ivory")
MAT_MAT = [sl.material.name for sl in than.material_slots if sl.material and any(k in sl.material.name.lower() for k in ("eye", "socket", "shade"))]
for sl in than.material_slots:
    if sl.material and not any(k in sl.material.name.lower() for k in GIU_VL): sl.material = NGA
for o in do + toc:   # tóc cũng phải tắt cull (quên ⇒ tóc chỉ còn viền, nhìn như hói)
    for sl in o.material_slots:
        if sl.material: sl.material.use_backface_culling = False
rig = H.dung_rig(K); trong = H.da(than, do, toc, rig)
sys.path.insert(0, os.path.expanduser("~/.hermes/skills/creative/las-physics/scripts")); import shatter as VO   # VỎ VA CHẠM thân (Boss 22/10: mọi vật đã chốt modeling phải có boundary layer)
VO_NGUOI = VO.vo_nguoi(rig, [than] + list(do) + list(toc)); os.makedirs(g.out, exist_ok=True)
VO_NGUOI["_long_ban_tay"] = {b_: VO.long_ban_tay(rig, [than] + list(do), b_) for b_ in "LR"}   # NHÃN lòng bàn tay (Boss 23/10); json.dump(VO_NGUOI, open(os.path.join(g.out, "body_shell.json"), "w"), indent=1)
print("VO_NGUOI", len(VO_NGUOI), "capsule", {b: v[2] for b, v in VO_NGUOI.items() if b in ("head", "chest", "hand_R", "thigh_L")})
loi_truc = H.thu_truc(rig)

CHE_DO_B = os.environ.get("GO_B")   # retarget: «kep» (kẹp nách–hông, Boss 22/10) | «vai_B» (trên vai, theo tư thế B)
# đạo cụ — gắn ở TƯ THẾ NGHỈ trước mọi khoá
dc = None; go = None; TOOLS = os.path.expanduser(P["tools"])
for pr in clip.get("props", []):
    if pr["asset"] == "khuc_go":
        bpy.ops.mesh.primitive_cylinder_add(vertices=7, radius=0.09, depth=1.2); go = bpy.context.object; go.name = "khuc_go"
        m = bpy.data.materials.new("go"); m.use_nodes = True; m.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.36, 0.24, 0.14, 1); go.data.materials.append(m)
        # gỗ dọc ±Y trên vai phải, cao hơn vai 18 cm; đầu trước NÂNG 5° (X 85°) và chếch RA NGOÀI 8° (Z −8°)
        vai = K["vai_R"]; W0 = M4.Translation(V((vai.x * 1.0, vai.y + 0.02, vai.z + 0.18))) @ M4.Rotation(math.radians(-8), 4, "Z") @ M4.Rotation(math.radians(85), 4, "X")
        go.matrix_world = W0; go.parent = rig; go.parent_type = "BONE"; go.parent_bone = "clavicle_R"; bpy.context.view_layer.update(); go.matrix_world = W0   # theo VAI (gắn ngực ⇒ vai nâng xuyên gỗ 45–88 mm)
        pr_go = pr
    else:
        e = H.gan_dao_cu(rig, f"{TOOLS}/{pr['asset']}.glb", pr["ben"], SK[f"cam_{pr['ben']}"], pr["huong"])
        if pr["ben"] == "R": dc = e

if os.environ.get("KHONG_DAO_CU"):   # Boss 22/10: đi tay không — bỏ rìu
    for o in [o for o in bpy.data.objects if o.name.startswith("dc_")]:
        for ch in list(o.children): bpy.data.objects.remove(ch)
        bpy.data.objects.remove(o)
    dc = None; clip["props"] = []
if g.lenh in ("retarget", "mocap", "sam"):   # bản B / mocap: đạo cụ theo TƯ THẾ NGUỒN, không theo bảng A
    for pr in clip.get("props", []):
        if pr["asset"] == "khuc_go" and CHE_DO_B: pr["che_do"] = CHE_DO_B
        if pr.get("tay_hai"): pr["theo_hai_tay"] = True
if g.lenh == "build":
    H.dung_clip(rig, K, clip, s=H.ti_le_chan(K)); N = clip["end_frame"]
elif g.lenh == "sam":   # SAM 3D Body → rig: NGUYÊN độ xoay mọi khớp (Boss 22/10 «redo… from SAM 3D… dont twist arm and adjusting»)
    N = H.retarget_sam(rig, K, g.mp, g.tu, g.den, khoa=clip["root"].get("mode") == "stationary"); clip["end_frame"] = N
elif g.lenh == "mocap":   # video → MediaPipe 3D → rig (Boss 22/10)
    N = H.retarget_mp(rig, K, g.mp, g.tu, g.den, khoa=clip["root"].get("mode") == "stationary" and os.environ.get("KHOA_CHAN", "1") == "1"); clip["end_frame"] = N
else:
    N = H.retarget(rig, K, g.bvh); clip["end_frame"] = N
    if os.environ.get("TAY_GUONG"):   # Boss 22/10: «mirror tay cầm rìu… ngược lại với tay kia đang vung bình thường»
        print("gương tay", H.guong_tay(rig, N, os.environ["TAY_GUONG"]))
if g.lenh == "mocap" and clip.get("them_xoay_nguc"):   # MediaPipe đo chiều sâu kém ⇒ thân xoay vai quá ít lúc lấy đà (tay trái với hụt 80–112 mm):
    xk = {float(k): dict(y=v) for k, v in clip["them_xoay_nguc"].items()}   # cộng yaw quanh Z thế giới (âm = quay PHẢI), chia spine 0,4 / chest 0,6
    for f in range(N + 1):
        sc.frame_set(f); bpy.context.view_layer.update(); yv = H.noi_suy(xk, f, True, N)["y"]
        for xn, w_ in (("spine", 0.4), ("chest", 0.6)):
            pb = rig.pose.bones[xn]; m = pb.matrix.copy(); t = m.translation.copy()
            m2 = mathutils.Matrix.Rotation(math.radians(yv * w_), 4, "Z") @ m; m2.translation = t; pb.matrix = m2; bpy.context.view_layer.update()
            pb.keyframe_insert("rotation_quaternion", frame=f)
TAY_KQ = None; NAM_KQ = None
if g.lenh == "mocap" and os.environ.get("TAY_TU"):   # tay lấy từ nguồn khác (SAM 3D Body), đo theo tam giác thân — Boss 22/10
    TAY_KQ = H.tay_theo_nguon(rig, os.environ["TAY_TU"], g.tu, N); print("tay_tu", TAY_KQ)
if g.lenh in ("retarget", "mocap", "sam"):   # mocap cũng phải cắt + trộn mối nối (bỏ sót ⇒ mối nối 211 mm, 22/10)
    if os.environ.get("CHU_KY"):   # "a,b": cắt 1 chu kỳ + trộn mối nối
        if os.environ["CHU_KY"].startswith("auto"):   # auto:tmin:tmax
            _, tmin, tmax = os.environ["CHU_KY"].split(":"); e_, a_, b_ = H.tim_chu_ky(rig, N, int(tmin), int(tmax)); print("dò chu kỳ", a_, b_, round(e_ * 1000, 1), "mm")
        else:
            a_, b_ = (int(x) for x in os.environ["CHU_KY"].split(","))
        print("chu kỳ", H.cat_chu_ky(rig, a_, b_, int(os.environ.get("TRON", "4"))))

quat = None
for pr in clip.get("props", []):
    if pr.get("quy_dao") and dc is not None and g.lenh == "build":   # rìu là chủ: quỹ đạo cánh quạt, HAI tay IK bám cán
        quat = pr; H.riu_quat(dc, pr["quy_dao"], N, clip["loop"])
        H.nam_hai_tay(rig, SK, dc, pr["tay"], N)   # giải tích (IK Blender: cổ tay gập 141–176°)
    elif pr.get("tay_hai") and dc is not None and g.lenh == "build":   # tay thứ hai bám cán (rìu hai tay)
        H.bam_can(rig, SK, dc, pr["tay_hai"]["ben"], pr["tay_hai"]["z"], N)

def W_(n, duoi=False): pb = rig.pose.bones[n]; return rig.matrix_world @ (pb.tail if duoi else pb.head)
def truoc_hong():
    trai = W_("thigh_L") - W_("thigh_R"); up = V((0, 0, 1)); return trai.cross(up).normalized()
if go is not None and pr_go.get("che_do") == "vai_B":   # nghiêng đầu NÉ khúc gỗ (người thật vác vai phải nghiêng đầu sang trái)
    ng = float(os.environ.get("DAU_NE", "8"))
    for f in range(N + 1):
        sc.frame_set(f); bpy.context.view_layer.update()
        for xn, w_ in (("neck", 0.5), ("head", 0.5)):
            pb = rig.pose.bones[xn]; ax = -truoc_hong()   # quanh trục −trước: dương = nghiêng TRÁI (+X)
            m = pb.matrix.copy(); Rw = mathutils.Quaternion(ax, math.radians(ng * w_)).to_matrix().to_4x4()
            t = m.translation.copy(); m2 = Rw @ m; m2.translation = t; pb.matrix = m2; bpy.context.view_layer.update()
            pb.keyframe_insert("rotation_quaternion", frame=f)
    go.scale = (0.85, 0.85, 1.0)
if go is not None and pr_go.get("che_do") in ("kep", "vai_B"):
    go.parent = None
    if pr_go["che_do"] == "kep":   # gỗ nhỏ hơn cho kẹp nách (r 6,5 cm)
        go.scale = (0.72, 0.72, 1.0)
    for f in range(N + 1):
        sc.frame_set(f); bpy.context.view_layer.update()
        if pr_go["che_do"] == "kep":
            c = (W_("upperarm_R") + W_("forearm_R") + W_("hand_R")) / 3
            c = c - V((0, 0, 1)).cross(truoc_hong()) * 0.025   # ra ngoài (phải) 2,5 cm: sát quá chạm sườn 4,4 mm
        else:   # Boss 22/10 «gỗ chưa sát vào gần cổ và chưa thật sự trên vai»: giữa cổ–khớp vai, hạ tới khi VỪA CHẠM thân
            c = W_("neck").lerp(W_("upperarm_R"), float(os.environ.get("GO_VAI_T", "0.75"))) + V((0, 0, 0.30))
        fw = truoc_hong(); fw.z = math.sin(math.radians(5)); fw.normalize()
        R = V((0, 0, 1)).rotation_difference(fw).to_matrix().to_4x4()
        if pr_go["che_do"] == "vai_B":   # hạ từng 3 mm tới khi mẫu đáy gỗ chạm mặt thân (BVH thân đã biến dạng, bỏ tay/cẳng phải)
            from mathutils.bvhtree import BVHTree
            dg = bpy.context.evaluated_depsgraph_get(); me = than.evaluated_get(dg).to_mesh()
            ten = {gg.index: gg.name for gg in than.vertex_groups}
            bo = {i for i, pl in enumerate(than.data.polygons) if sum((ten[max(than.data.vertices[v].groups, key=lambda x: x.weight).group] if than.data.vertices[v].groups else "") in ("hand_R", "forearm_R") for v in pl.vertices) * 2 > len(pl.vertices)}
            bvh = BVHTree.FromPolygons([than.matrix_world @ v.co for v in me.vertices], [list(pl.vertices) for i, pl in enumerate(me.polygons) if i not in bo]); than.evaluated_get(dg).to_mesh_clear()
            mau = [M4.Translation(V((0, 0, 0))) @ R @ V((0.09 * go.scale.x * math.cos(a_), 0.09 * go.scale.x * math.sin(a_), z_)) for a_ in [i * math.pi / 6 for i in range(12)] for z_ in (-0.5, -0.25, 0, 0.25, 0.5)]
            for _ in range(120):
                if any(H.trong_bvh(bvh, c + m) for m in mau) or any((bvh.find_nearest(c + m)[3] or 1) < 0.002 for m in mau): break
                c = c - V((0, 0, 0.003))
            c = c + V((0, 0, 0.004))   # nhấc 4 mm: chạm chứ không lún
        go.matrix_world = M4.Translation(c) @ R @ M4.Diagonal((*go.scale, 1.0)) if False else M4.Translation(c) @ R
        if pr_go["che_do"] == "kep": go.scale = (0.72, 0.72, 1.0)
        else: go.scale = (0.85, 0.85, 1.0)
        go.keyframe_insert("location", frame=f); go.rotation_mode = "QUATERNION"; go.keyframe_insert("rotation_quaternion", frame=f)
if go is not None and pr_go.get("che_do") == "vai_B" and os.environ.get("TAY_GIU_GO"):   # Boss 22/10: «vác gỗ trên vai thì tay phải giữ trên vai»
    cuc = bpy.data.objects.new("cuc_khuyu_R", None); sc.collection.objects.link(cuc)
    # cực khuỷu KHOÁ TỪNG KHUNG theo vai + hướng thân (bản gắn-xương đặt lúc gốc đã chạy xa ⇒ cực nằm sau lưng 3,4 m, vô tác dụng)
    ra, tr, xu = (float(x) for x in os.environ.get("CUC_VT", "0.40,0.10,0.40").split(","))   # ra ngoài, ra trước, xuống
    for f in range(N + 1):
        sc.frame_set(f); bpy.context.view_layer.update(); fw = truoc_hong(); phai = -V((0, 0, 1)).cross(fw)
        cuc.location = W_("upperarm_R") + phai * ra + fw * tr - V((0, 0, xu)); cuc.keyframe_insert("location", frame=f)
    r_go = 0.09 * go.scale.x
    # nắm tay ở MẶT NGOÀI phía trước gỗ (lên đỉnh thì tay settler duỗi thẳng, khuỷu nằm trong gỗ: tay xuyên gỗ 76–89 mm)
    H.bam_can(rig, SK, go, "R", float(os.environ.get("TAY_GIU_GO_Z", "0.22")), N, nhac=float(os.environ.get("TAY_NHAC", "0.0")), cuc=cuc,
              cuc_goc=float(os.environ.get("CUC_GOC", "0")), ngang=-(r_go + float(os.environ.get("TAY_NGANG_THEM", "0.05"))), xoay_tay=False)   # nắm tay trên mặt gỗ, trước vai (0,20 chạm mặt; −0,22 sau vai), dọc theo khúc gỗ
if dc is not None and g.lenh == "sam" and any(pr.get("qua_hai_nam") for pr in clip.get("props", [])):
    # SAM THUẦN: KHÔNG chỉnh tay (Boss «dont twist arm and adjusting»). Cán đi qua 2 socket nắm; chiều cán theo rìu ĐO trong video;
    # lưỡi gắn cứng theo bàn tay phải (chiều chốt ở khung trúng); chỉ ĐO độ vênh trục nắm–cán
    def sock(b):
        hb = rig.data.bones[f"hand_{b}"]; return rig.matrix_world @ rig.pose.bones[f"hand_{b}"].matrix @ hb.matrix_local.inverted() @ V(SK[f"cam_{b}"]["vi_tri"])
    KH = H.SAM_KHUNG; Fm = mathutils.Matrix(((1, 0, 0), (0, -1, 0), (0, 0, -1)))
    def can_video(t):
        if not KH.get("can"): return None
        gan = min(KH["can"], key=lambda x: abs(x[0] - t)); return (KH["Y"] @ KH["CQ"] @ Fm @ gan[1]).normalized()
    dc.parent = None; dc.rotation_mode = "QUATERNION"; Z = []; G = []; XR = []; vench = 0.0; LECH_NAM = []
    DAU_S = {}; H_PREV = {}; H_CUR = {}
    def xoay_ban_tay(b, z):   # CHỈ BÀN TAY (Boss «adjust only hands and axe»): trục nắm = cán, cổ tay thẳng nhất (hướng tay = cẳng tay ⟂ cán), chiều chốt 1 lần
        pb = rig.pose.bones[f"hand_{b}"]; hb = rig.data.bones[f"hand_{b}"]; Wm = rig.matrix_world; Mh = Wm @ pb.matrix @ hb.matrix_local.inverted()
        sa = (Mh.to_3x3() @ V(SK[f"cam_{b}"]["len"])).normalized()
        if b not in DAU_S: DAU_S[b] = 1 if sa.dot(z) >= 0 else -1
        dz = z * DAU_S[b]; fa = ((Wm @ rig.pose.bones[f"forearm_{b}"].tail) - (Wm @ rig.pose.bones[f"forearm_{b}"].head)).normalized(); h = fa - dz * fa.dot(dz)
        if b in H_PREV:   # cẳng tay gần // cán ⇒ hướng tay bất định, lật (bước xoắn 125°, cổ tay 107°) ⇒ kéo về khung trước theo độ bất định
            hp_ = H_PREV[b] - dz * H_PREV[b].dot(dz); h = h + hp_ * max(0.0, 0.5 - h.length) * 4
        h = h.normalized() if h.length > 1e-4 else dz.orthogonal().normalized()
        H_CUR[b] = h.copy()
        a0 = V(SK[f"cam_{b}"]["len"]).normalized(); h0 = (hb.tail_local - hb.head_local).normalized(); a0p = (a0 - h0 * a0.dot(h0)).normalized()
        B0 = mathutils.Matrix((h0, a0p, h0.cross(a0p))).transposed(); B = mathutils.Matrix((h, dz, h.cross(dz))).transposed()
        m = (Wm.inverted().to_3x3() @ (B @ B0.transposed()) @ hb.matrix_local.to_3x3()).to_4x4(); m.translation = pb.matrix.translation; pb.matrix = m; bpy.context.view_layer.update()
    fe = sc.frame_end + 1 if os.environ.get("CHU_KY") else N
    for f in range(0 if not os.environ.get("RIU3D") else N + 1, N + 1):
        ff = f if f < fe else f - fe; sc.frame_set(ff); bpy.context.view_layer.update(); pR, pL = sock("R"), sock("L")
        cvv = can_video(g.tu + ff / H.FPS)
        if os.environ.get("CAN_THEO", "nam") == "video" and os.environ.get("TAY_NAM_CAN", "1") == "1" and f < fe and cvv is not None:
            # CHỈ BÀN TAY: cán theo rìu ĐO (video); mỗi bàn tay: trục nắm // cán, dò góc XOAY QUANH CÁN để socket sát trục cán nhất, phạt cổ tay gập > 40°
            for _ in range(3):
                pR, pL = sock("R"), sock("L"); m_ = (pR + pL) / 2
                for b_ in "LR":
                    pb = rig.pose.bones[f"hand_{b_}"]; hb = rig.data.bones[f"hand_{b_}"]; Wm = rig.matrix_world; Mh = Wm @ pb.matrix @ hb.matrix_local.inverted()
                    sa = (Mh.to_3x3() @ V(SK[f"cam_{b_}"]["len"])).normalized()
                    if b_ not in DAU_S: DAU_S[b_] = 1 if sa.dot(cvv) >= 0 else -1
                    dz = cvv * DAU_S[b_]; fa = ((Wm @ rig.pose.bones[f"forearm_{b_}"].tail) - (Wm @ rig.pose.bones[f"forearm_{b_}"].head)).normalized()
                    h_s = fa - dz * fa.dot(dz); h_s = h_s.normalized() if h_s.length > 1e-4 else dz.orthogonal().normalized()
                    a0 = V(SK[f"cam_{b_}"]["len"]).normalized(); h0 = (hb.tail_local - hb.head_local).normalized(); a0p = (a0 - h0 * a0.dot(h0)).normalized()
                    o0 = V(SK[f"cam_{b_}"]["vi_tri"]) - hb.head_local; B0 = mathutils.Matrix((h0, a0p, h0.cross(a0p))).transposed(); co = Wm @ pb.head
                    tot = None
                    for dg in range(-180, 180, 10):
                        h = mathutils.Quaternion(dz, math.radians(dg)) @ h_s; Rr = mathutils.Matrix((h, dz, h.cross(dz))).transposed() @ B0.transposed()
                        so = co + Rr @ o0; q_ = so - m_; dd = (q_ - dz * q_.dot(dz)).length; gap = math.degrees(fa.angle(h))
                        c_ = dd * 1000 + max(0.0, gap - 40) * 3
                        if tot is None or c_ < tot[0]: tot = (c_, Rr)
                    m = (Wm.inverted().to_3x3() @ tot[1] @ hb.matrix_local.to_3x3()).to_4x4(); m.translation = pb.matrix.translation; pb.matrix = m; bpy.context.view_layer.update()
            for b_ in "LR": rig.pose.bones[f"hand_{b_}"].keyframe_insert("rotation_quaternion", frame=ff)
            pR, pL = sock("R"), sock("L")
        elif os.environ.get("TAY_NAM_CAN", "1") == "1" and f < fe:
            for _ in range(4):
                z0 = (pR - pL).normalized(); cv0 = can_video(g.tu + ff / H.FPS)
                if cv0 is not None and z0.dot(cv0) < 0: z0 = -z0
                for b_ in "LR": xoay_ban_tay(b_, z0)
                pR, pL = sock("R"), sock("L")
            for b_ in "LR": rig.pose.bones[f"hand_{b_}"].keyframe_insert("rotation_quaternion", frame=ff)
        z = (pR - pL).normalized(); cv_ = can_video(g.tu + ff / H.FPS)
        if cv_ is not None:
            if z.dot(cv_) < 0: z = -z
            vench = max(vench, math.degrees(z.angle(cv_)))
            if os.environ.get("CAN_THEO", "nam") == "video": z = cv_.copy()   # hướng cán = rìu ĐO trong video (Codex: f4/f12 đường 2 nắm lệch hướng mẫu); tay giữ nguyên
        m0 = (pR + pL) / 2
        if os.environ.get("KEO_LEN_CAN", "0") == "1":   # nắm tay LÊN trục cán (tay SAM và rìu video lệch tới 150 mm): chỉ dời vị trí, giữ xoắn
            for _ in range(3):
                pR, pL = sock("R"), sock("L"); m0 = (pR + pL) / 2
                for b_, p_ in (("R", pR), ("L", pL)): H.keo_tay_giu_xoan(rig, b_, (m0 + z * (p_ - m0).dot(z)) - p_)
            for b_ in "LR":
                for x_ in ("upperarm", "forearm", "hand"): rig.pose.bones[f"{x_}_{b_}"].keyframe_insert("rotation_quaternion", frame=ff)
            pR, pL = sock("R"), sock("L"); m0 = (pR + pL) / 2
        LECH_NAM.append(max(((p_ - m0) - z * (p_ - m0).dot(z)).length for p_ in (pR, pL)))
        m_ = (pR + pL) / 2; tmin = min((pR - m_).dot(z), (pL - m_).dot(z)); G.append(m_ + z * (tmin + 0.28)); Z.append(z)
        hx = (rig.matrix_world @ rig.pose.bones["hand_R"].matrix).to_3x3().normalized().col[2]; XR.append((hx - z * hx.dot(z)).normalized())
    if os.environ.get("RIU3D"):   # RÌU ĐO (fit 3D cả chuỗi từ SAM2) LÁI: đặt rìu theo số đo, IK tối thiểu VỊ TRÍ cổ tay (giữ khuỷu/xoắn GVHMR), tay nắm
        # Boss 22/10 «Allow minimal arm IK (wrist position only, keep elbow direction and twist from GVHMR), measured axe drives it»
        R3 = json.load(open(os.environ["RIU3D"])); Sj = json.load(open(os.environ["SAM_KP"])); fps_s = 30.0
        frk = {round(f_["t"] * fps_s): f_ for f_ in Sj["frames"] if f_.get("w")}; kk3 = sorted(int(k) for k in R3["khung"])
        def blv(p_): return V((p_[0], p_[2], -p_[1]))
        def khung3(vL, vR, hc):
            mid = (vL + vR) / 2; x_ = (vL - vR).normalized(); z_ = mid - hc; z_ = (z_ - x_ * z_.dot(x_)).normalized(); return mathutils.Matrix((x_, z_.cross(x_), z_)).transposed(), mid
        L_RIU = 0.67 + 0.32   # rìu settler: đuôi −0,32 → tâm lưỡi 0,67 (gốc = chỗ nắm tay phải)
        if os.environ.get("RIU_TL"): dc.scale = (float(os.environ["RIU_TL"]),) * 3   # thử: rìu theo TỈ LỆ rìu mẫu (rìu mẫu 0,53 m ≈ 1 sải tay; riu_dai gấp đôi ⇒ lưỡi thấp)
        # clip gốc LẶP KHUNG (mỗi tư thế giữ 2 khung @30 fps: trục rìu 0–1° rồi nhảy 27–59°/115 cm) ⇒ bỏ khung trùng, NỘI SUY giữa tư thế thật
        giu = []
        for k in kk3:
            if k not in frk: continue
            if giu:
                rp = R3["khung"][str(giu[-1])]; rc = R3["khung"][str(k)]
                if math.degrees(V(rp["d"]).angle(V(rc["d"]))) < 1.5 and (V(rp["Hc"]) - V(rc["Hc"])).length < 0.03: continue
            giu.append(k)
        def lay3(t):
            ts = [q / fps_s for q in giu]; i = max(0, min(len(ts) - 2, max((j for j in range(len(ts)) if ts[j] <= t), default=0))); u = max(0.0, min(1.0, (t - ts[i]) / (ts[i + 1] - ts[i])))
            a3, b3 = R3["khung"][str(giu[i])], R3["khung"][str(giu[i + 1])]
            da, db = V(a3["d"]), V(b3["d"]); dd = da.slerp(db, u) if da.dot(db) > -0.99 else da
            r3 = dict(Hc=list(V(a3["Hc"]).lerp(V(b3["Hc"]), u)), d=list(dd.normalized()), Lb=a3["Lb"])
            wa, wb = frk[giu[i]]["w"], frk[giu[i + 1]]["w"]
            return r3, [blv(V(pa[:3]).lerp(V(pb[:3]), u)) for pa, pb in zip(wa, wb)], giu[i]
        Z = []; G = []; XR = []; MUC = []; KQ3 = []; MUC_F = []; FW = []
        for f in range(N + 1):
            ff = f if f < fe else f - fe; sc.frame_set(ff); bpy.context.view_layer.update()
            if f >= fe:   # khung cuối chu kỳ ≡ khung 0
                Z.append(Z[0]); G.append(G[0]); MUC_F.append(MUC_F[0]); FW.append(FW[0]); continue
            t_ = g.tu + ff / H.FPS; r3, w_, k = lay3(t_)
            Fs, ms = khung3(w_[11], w_[12], (w_[23] + w_[24]) / 2)
            Pb = rig.pose.bones; Wm = rig.matrix_world; wv = lambda n, duoi=False: Wm @ (Pb[n].tail if duoi else Pb[n].head)
            Ft, mt = khung3(wv("upperarm_L"), wv("upperarm_R"), (wv("thigh_L") + wv("thigh_R")) / 2)
            Ls = (w_[13] - w_[11]).length + (w_[15] - w_[13]).length; Lt = rig.data.bones["upperarm_L"].length + rig.data.bones["forearm_L"].length; s_ = Lt / Ls
            doi = lambda v_: Ft @ (Fs.transposed() @ v_)
            Hs = blv(r3["Hc"]); ds = blv(r3["d"]).normalized(); Ht = mt + doi(Hs - ms) * s_; dt = doi(ds).normalized()
            if os.environ.get("IN_R3") and ff in (0, 8, 16):
                print("R3", ff, "k", k, "|Hs-ms|", round((Hs - ms).length, 2), "s", round(s_, 2), "|wR-ms|", round((w_[16] - ms).length, 2), "|wR-Hs| doc truc", round((w_[16] - Hs).dot(ds), 2),
                      "Lb", round(r3["Lb"], 2), "|Ht-mt|", round((Ht - mt).length, 2), "Lt", round(Lt, 2), "vai_t", [round(x, 2) for x in mt], "Hs", [round(x, 2) for x in Hs], "ms", [round(x, 2) for x in ms])
            muc = {}; tl_ = dc.scale[0]
            lam_R = (w_[16] - Hs).dot(ds); muc["R"] = mt + doi((Hs + ds * lam_R) - ms) * s_   # tay PHẢI: cổ tay nguồn chiếu lên trục → khung thân settler
            # tay TRÁI CỐ ĐỊNH sát đuôi cán (Boss «left hand not attach… hold and unhold»: theo cổ tay mẫu ⇒ trượt −0,07…−0,54, ra ngoài đuôi −0,32)
            muc["L"] = muc["R"] + dt * (float(os.environ.get("NAM_TRAI", "-0.28")) * tl_)
            # RÌU KHÔNG XUYÊN NGƯỜI: khối trụ quanh đùi/cẳng chân/thân; điểm dọc rìu (đuôi −0,32 → lưỡi 0,73 tính từ nắm phải) lún vào ⇒ đẩy cả rìu + 2 điểm nắm ra
            # (rìu đo + thân GVHMR khác người mẫu ⇒ cán xuyên đùi 46 mm ở f11). Chỉ dời RÌU, tay theo bằng IK
            TRU = [("thigh_L", 0.08), ("thigh_R", 0.08), ("shin_L", 0.06), ("shin_R", 0.06), ("hips", 0.15), ("spine", 0.15), ("chest", 0.16)]
            for _ in range(4):
                day = V()
                for sa_ in [x_ / 10 for x_ in range(-3, 8)]:
                    q_ = muc["R"] + dt * sa_
                    for nb, r_ in TRU:
                        a_ = wv(nb); b_ = wv(nb, True); ab = b_ - a_; u_ = max(0.0, min(1.0, (q_ - a_).dot(ab) / ab.length_squared)); c_ = a_ + ab * u_; v_ = q_ - c_
                        if v_.length < r_ + 0.015:
                            dv_ = (v_.normalized() if v_.length > 1e-5 else Ft.col[1] * -1) * (r_ + 0.015 - v_.length)
                            if dv_.length > day.length: day = dv_
                if day.length < 1e-4: break
                for b_ in "LR": muc[b_] = muc[b_] + day
            MUC_F.append({b_: v_.copy() for b_, v_ in muc.items()}); KQ3.append(0.0)
            Z.append(dt); G.append(muc["R"].copy())   # gốc món (z=0) = chỗ nắm tay PHẢI
            lr_ = wv("thigh_L") - wv("thigh_R"); fw0 = lr_.cross(V((0, 0, 1))); fw0.z = 0; FW.append(fw0.normalized())   # hướng TRƯỚC của hông
        # LƯỠI (+X) LUÔN HƯỚNG VỀ PHÍA TRƯỚC (Boss 22/10 «blade of the axe gotta be always pointing toward the front»): hướng trước của HÔNG (ngang)
        # chiếu ⟂ cán; cán gần // hướng trước ⇒ giữ khung trước. (theo chiều chuyển động ⇒ lật nghiêng lúc chậm/đổi chiều; theo bàn tay ⇒ xoắn theo tay)
        xp_ = None; LUOI_NGANG = os.environ.get("LUOI_NGANG", "1") == "1"
        for i in range(len(G)):
            z_ = Z[i]; fw_ = FW[i]; x_ = fw_ - z_ * fw_.dot(z_)
            if x_.length < 0.3 and xp_ is not None: x_ = x_ + (xp_ - z_ * xp_.dot(z_)) * (0.3 - x_.length) * 4
            x_ = x_.normalized() if x_.length > 1e-5 else (xp_ if xp_ is not None else z_.orthogonal().normalized())
            # LƯỠI NẰM NGANG (Boss 22/10 «blade is pointing upward, supose to be horizontol»): hướng trước ⟂ cán ngóc lên khi cán nghiêng
            # (đo: thành phần đứng 0,5–0,86 ở khung giơ rìu) ⇒ lấy hướng NGANG duy nhất ⟂ cán (cán × Z), dấu theo phía trước, liền mạch
            h_ = z_.cross(V((0, 0, 1)))
            if LUOI_NGANG and h_.length > 0.2:
                h_.normalize(); xt_ = None
                if xp_ is not None:   # lưỡi khung trước, chuyển sang cán mới (xoay nhỏ nhất) ⇒ chọn DẤU theo nó (liền mạch), chỉ khung 0 chọn theo phía trước
                    xt_ = Z[i - 1].rotation_difference(z_) @ xp_; xt_ = (xt_ - z_ * xt_.dot(z_)).normalized()
                x_ = h_ if h_.dot(xt_ if xt_ is not None else x_) >= 0 else -h_
                if xt_ is not None:   # lưỡi không vặn quanh cán > 30°/frames (cán chúc thẳng xuống ⇒ hướng ngang quay 97°/frames)
                    g_ = math.atan2(z_.dot(xt_.cross(x_)), xt_.dot(x_)); x_ = mathutils.Quaternion(z_, max(-0.52, min(0.52, g_))) @ xt_
            XR.append(x_); xp_ = x_
            if os.environ.get("IN_XR"):
                h_ = z_.cross(V((0, 0, 1))); print("XR", i, "buoc", round(math.degrees(x_.angle(XR[-2])), 0) if len(XR) > 1 else 0, "phuong_can", round(math.degrees(math.atan2(z_.y, z_.x))), "luoi_z", round(x_.z, 2), "can_z", round(z_.z, 2), "fw·x", round(fw_.dot(x_), 2), "ngang·x", round(abs(h_.normalized().dot(x_)) if h_.length > 1e-4 else 0, 2))
        if LUOI_NGANG and sum(FW[i].dot(XR[i]) for i in range(len(XR))) < 0: XR = [-x_ for x_ in XR]   # lưỡi ngang liền mạch có 2 dấu ⇒ lấy dấu hướng TRƯỚC nhiều nhất cả clip
        # TAY: XOAY CỨNG THEO RÌU (1 phép nắm cố định / tay, hiệu chỉnh ở khung trúng bằng nắm cổ-tay-thẳng) + IK vị trí cổ tay cho socket đúng chỗ trên cán
        fh_ = next((e["frame"] for e in clip.get("events", []) if e["name"] == "hit"), N // 3)
        def mrot(i): z_ = Z[i]; x_ = XR[i]; return mathutils.Matrix((x_, z_.cross(x_), z_)).transposed()
        sc.frame_set(fh_); bpy.context.view_layer.update(); CN = {}
        for _ in range(4):
            for b_ in "LR": xoay_ban_tay(b_, Z[fh_]); H.keo_tay_giu_xoan(rig, b_, MUC_F[fh_][b_] - sock(b_))
        for b_ in "LR": CN[b_] = mrot(fh_).transposed() @ (rig.matrix_world @ rig.pose.bones[f"hand_{b_}"].matrix).to_3x3().normalized()
        # GÓC NẮM tối ưu cả clip: xoay phép nắm quanh trục cán (z cục bộ rìu) θ — chọn θ cho p95 độ gập cổ tay nhỏ nhất (hiệu chỉnh ở khung trúng ⇒ cổ tay trái 145°)
        FA = []
        for f in range(fe):
            sc.frame_set(f); bpy.context.view_layer.update(); FA.append({b_: ((rig.matrix_world @ rig.pose.bones[f"forearm_{b_}"].tail) - (rig.matrix_world @ rig.pose.bones[f"forearm_{b_}"].head)).normalized() for b_ in "LR"})
            FA[-1]["vai"] = {b_: ((rig.matrix_world @ rig.pose.bones[f"upperarm_{b_}"].head), (rig.matrix_world @ rig.pose.bones[f"forearm_{b_}"].head), (rig.matrix_world @ rig.pose.bones[f"forearm_{b_}"].tail)) for b_ in "LR"}
        XKM = int(os.environ.get("XOAY_KHUYU", "90"))
        def gap_min(f, b_, hd_):   # độ gập cổ tay nhỏ nhất đạt được khi cho khuỷu xoay quanh trục vai→cổ tay trong ±XKM°
            if not XKM: return math.degrees(FA[f][b_].angle(hd_))
            s0, e0, w0 = FA[f]["vai"][b_]; ax_ = (w0 - s0).normalized()
            return min(math.degrees((w0 - (s0 + mathutils.Quaternion(ax_, math.radians(dg)) @ (e0 - s0))).angle(hd_)) for dg in range(-XKM, XKM + 1, 6))
        for b_ in "LR":
            h0_ = (rig.data.bones[f"hand_{b_}"].tail_local - rig.data.bones[f"hand_{b_}"].head_local).normalized(); tot = None
            for dg in range(0, 360, 10):
                Cq = mathutils.Matrix.Rotation(math.radians(dg), 3, "Z") @ CN[b_]
                gs = sorted(gap_min(f, b_, mrot(f) @ Cq @ rig.data.bones[f"hand_{b_}"].matrix_local.to_3x3().inverted() @ h0_) for f in range(fe))
                c_ = gs[int(0.95 * (len(gs) - 1))]
                if tot is None or c_ < tot[0]: tot = (c_, Cq, dg)
            CN[b_] = tot[1]; print("goc_nam", b_, "θ", tot[2], "p95 gập (ước)", round(tot[0], 1))
        # XOAY KHUỶU (Boss 22/10 «Xoay khuỷu tay thử»): quay cả cánh tay quanh trục vai→cổ tay (cổ tay đứng yên) cho cẳng tay thẳng hàng bàn tay.
        # Chọn góc cả clip bằng Viterbi (gập cổ tay + phạt khuỷu nhảy + phạt xa tư thế GVHMR); chọn tham lam từng khung ⇒ khuỷu lật 147°/frames (đo 22/10)
        XOAY_KHUYU = int(os.environ.get("XOAY_KHUYU", "90")); BK = 6; XK = {"L": [], "R": []}; GAP = {"L": [], "R": []}
        PH_NHAY = float(os.environ.get("XK_PHAT", "0.5")); PH_XA = float(os.environ.get("XK_XA", "0.1"))
        def dat_tay(ff, Rx):
            for _ in range(3):
                for b_ in "LR":
                    ph_ = rig.pose.bones[f"hand_{b_}"]; m_ = (rig.matrix_world.inverted().to_3x3() @ Rx @ CN[b_]).to_4x4(); m_.translation = ph_.matrix.translation
                    ph_.matrix = m_; bpy.context.view_layer.update(); H.keo_tay_giu_xoan(rig, b_, MUC_F[ff][b_] - sock(b_))
        def hinh_tay(b_, Rx):
            Wm_ = rig.matrix_world; pu_ = rig.pose.bones[f"upperarm_{b_}"]; pf_ = rig.pose.bones[f"forearm_{b_}"]
            s0 = Wm_ @ pu_.head; w0 = Wm_ @ pf_.tail; e0 = Wm_ @ pf_.head; ax_ = (w0 - s0).normalized()
            hb_ = rig.data.bones[f"hand_{b_}"]; hd_ = (Rx @ CN[b_] @ hb_.matrix_local.to_3x3().inverted() @ (hb_.tail_local - hb_.head_local).normalized()).normalized()
            return s0, e0, w0, ax_, hd_
        PHI = list(range(-XOAY_KHUYU, XOAY_KHUYU + 1, BK)) if XOAY_KHUYU else [0]; CHON = {b_: [0] * fe for b_ in "LR"}
        if XOAY_KHUYU:
            HT = {b_: [] for b_ in "LR"}
            for ff in range(fe):   # lượt A: đo hình học tay (chưa xoay) mỗi khung
                sc.frame_set(ff); bpy.context.view_layer.update(); Rx = mrot(ff); dat_tay(ff, Rx)
                for b_ in "LR": HT[b_].append(hinh_tay(b_, Rx))
            for b_ in "LR":
                CP = []; PO = []
                for (s0, e0, w0, ax_, hd_) in HT[b_]:
                    po0 = (e0 - s0) - ax_ * (e0 - s0).dot(ax_); cp_ = []; po_ = []
                    for dg in PHI:
                        q_ = mathutils.Quaternion(ax_, math.radians(dg)); cp_.append(math.degrees((w0 - (s0 + q_ @ (e0 - s0))).angle(hd_)) + PH_XA * abs(dg)); po_.append(q_ @ po0)
                    CP.append(cp_); PO.append(po_)
                D = [CP[0][:]]; BT = []
                for i in range(1, fe):
                    d_ = []; bt_ = []
                    for k in range(len(PHI)):
                        best = min(range(len(PHI)), key=lambda j: D[-1][j] + PH_NHAY * math.degrees(PO[i - 1][j].angle(PO[i][k])))
                        d_.append(D[-1][best] + PH_NHAY * math.degrees(PO[i - 1][best].angle(PO[i][k])) + CP[i][k]); bt_.append(best)
                    D.append(d_); BT.append(bt_)
                k = min(range(len(PHI)), key=lambda j: D[-1][j]); duong = [k]
                for bt_ in reversed(BT): k = bt_[k]; duong.append(k)
                CHON[b_] = [PHI[k] for k in reversed(duong)]
        for f in range(N + 1):
            ff = f if f < fe else f - fe
            if f >= fe:
                for b_ in "LR":
                    for x_ in ("upperarm", "forearm", "hand"):
                        pb_ = rig.pose.bones[f"{x_}_{b_}"]; sc.frame_set(0); q0_ = pb_.rotation_quaternion.copy(); sc.frame_set(f); pb_.rotation_quaternion = q0_; pb_.keyframe_insert("rotation_quaternion", frame=f)
                continue
            sc.frame_set(ff); bpy.context.view_layer.update(); Rx = mrot(ff); dat_tay(ff, Rx)
            if XOAY_KHUYU:
                for b_ in "LR":
                    s0, e0, w0, ax_, hd_ = hinh_tay(b_, Rx); Wm_ = rig.matrix_world; pu_ = rig.pose.bones[f"upperarm_{b_}"]; XK[b_].append(CHON[b_][ff])
                    R4 = M4.Translation(s0) @ mathutils.Quaternion(ax_, math.radians(CHON[b_][ff])).to_matrix().to_4x4() @ M4.Translation(-s0)
                    pu_.matrix = Wm_.inverted() @ R4 @ Wm_ @ pu_.matrix; bpy.context.view_layer.update()
                dat_tay(ff, Rx)
            for b_ in "LR":
                Pb_ = rig.pose.bones; Wm_ = rig.matrix_world
                GAP[b_].append(round(math.degrees(((Wm_ @ Pb_[f"forearm_{b_}"].tail) - (Wm_ @ Pb_[f"forearm_{b_}"].head)).angle((Wm_ @ Pb_[f"hand_{b_}"].tail) - (Wm_ @ Pb_[f"hand_{b_}"].head)))))
            KQ3[ff] = max((sock(b_) - MUC_F[ff][b_]).length for b_ in "LR") if ff < len(KQ3) else 0
            for b_ in "LR":
                for x_ in ("upperarm", "forearm", "hand"): rig.pose.bones[f"{x_}_{b_}"].keyframe_insert("rotation_quaternion", frame=ff)
        LECH_NAM = KQ3; print("riu3d: nắm lệch mục tiêu max mm", round(max(KQ3) * 1000, 1))
        if XOAY_KHUYU: print("xoay_khuyu độ L", XK["L"], "R", XK["R"])
        print("gap_co_tay L", GAP["L"], "R", GAP["R"])
    fh = next((e["frame"] for e in clip.get("events", []) if e["name"] == "hit"), N // 3)
    vh = (G[fh + 1] + Z[fh + 1] * 0.67) - (G[fh - 1] + Z[fh - 1] * 0.67); dx = 1 if XR[fh].dot(vh) >= 0 else -1
    if os.environ.get("RIU3D"): dx = 1   # XR đã = hướng trước hông (+X mesh = mép lưỡi); lật theo chiều chém ⇒ lưỡi quay ra SAU + rìu lệch 180° so với tay nắm (Boss 22/10 «Lưỡi axe đang quay ngược về sau»)
    xp = None; zp = None; LIM = math.radians(float(os.environ.get("RIU_XOAY_MAX", "25")))
    for f in range(N + 1):
        z = Z[f]; x = XR[f] * dx
        if xp is not None and not os.environ.get("RIU3D"):   # (RIU3D: XR đã mượt + tay nắm cứng theo XR ⇒ rìu theo ĐÚNG XR) VẬT LÝ: tay không vặn rìu > 25°/frames quanh cán (cổ tay SAM rung ⇒ lưỡi giật 50°)
            xt = zp.rotation_difference(z) @ xp; xt = (xt - z * xt.dot(z)).normalized(); g_ = math.atan2(z.dot(xt.cross(x)), xt.dot(x))
            x = mathutils.Quaternion(z, max(-LIM, min(LIM, g_))) @ xt
        x = (x - z * x.dot(z)).normalized(); xp = x.copy(); zp = z.copy()
        dc.matrix_world = M4.Translation(G[f]) @ M4((x, z.cross(x), z)).transposed().to_4x4() @ mathutils.Matrix.Diagonal((*dc.scale, 1.0))
        dc.keyframe_insert("location", frame=f); dc.keyframe_insert("rotation_quaternion", frame=f)
    # ĐỔI NHỊP (Boss 22/10 «make the swing fast at the swing frame to show the strong swing»): ánh xạ thời gian TĂNG ĐƠN ĐIỆU lên MỌI
    # keyframe (người + rìu), giữ khung 0 và khung cuối chu kỳ ⇒ vòng lặp vẫn khít. Mặc định: giữ đỉnh lâu hơn (0→2 ⇒ 0→3), vung 2→8 ⇒ 3→6
    # (nhanh ×2), theo đà 8→12 ⇒ 6→11, phần còn lại giãn đều. Mốc "hit" dời theo. DOI_NHIP="" ⇒ tắt.
    TOC = {}
    dn_ = os.environ.get("DOI_NHIP", ";".join(f"{a}:{b}" for a, b in clip.get("doi_nhip", [])))
    if dn_:
        mo = sorted(tuple(float(x) for x in c.split(":")) for c in dn_.split(";"))
        def tg(x):
            if x <= mo[0][0] or x >= mo[-1][0]: return x
            for (a0, b0), (a1, b1) in zip(mo, mo[1:]):
                if a0 <= x <= a1: return b0 + (b1 - b0) * (x - a0) / (a1 - a0)
        for ob_ in (rig, dc):
            ad_ = ob_.animation_data
            if not (ad_ and ad_.action): continue
            from bpy_extras import anim_utils
            cb_ = anim_utils.action_get_channelbag_for_slot(ad_.action, ad_.action_slot)   # Blender 5: Action.fcurves đã bỏ ⇒ qua channelbag
            for fc in (cb_.fcurves if cb_ else []):
                for kp in fc.keyframe_points:
                    kp.co.x = tg(kp.co.x); kp.interpolation = "BEZIER"; kp.handle_left_type = kp.handle_right_type = "AUTO_CLAMPED"
                fc.update()
        for e in clip.get("events", []): e["frame"] = round(tg(e["frame"]))
        for pr in clip.get("props", []):
            if pr.get("cua_so_chem"): pr["cua_so_chem"] = [round(tg(x)) for x in pr["cua_so_chem"]]
        print("doi_nhip", mo, "hit →", [e["frame"] for e in clip.get("events", [])])
        # tốc độ cục bộ (khung gốc / khung mới) để cửa ⑯ đo rung theo THỜI GIAN GỐC, không phạt cú vung nhanh có chủ đích
        for (a0, b0), (a1, b1) in zip(mo, mo[1:]):
            for f_ in range(int(math.ceil(b0)), int(math.floor(b1)) + 1): TOC[f_] = max(TOC.get(f_, 0), (a1 - a0) / max(1e-6, b1 - b0))
        if os.environ.get("RIU3D"):   # NẮM CỐ ĐỊNH sau đổi nhịp: nội suy key lẻ làm tay/rìu trôi 21,5° ⇒ rìu xoay CỨNG theo tay phải từng khung nguyên
            kq_ = []
            for f_ in range(sc.frame_start, sc.frame_end + 2):
                sc.frame_set(f_); bpy.context.view_layer.update()
                Rh_ = (rig.matrix_world @ rig.pose.bones["hand_R"].matrix).to_3x3().normalized() @ CN["R"].inverted()
                kq_.append((f_, dc.matrix_world.translation.copy(), Rh_))
            dc.animation_data_clear()
            for f_, t_, R_ in kq_:
                dc.matrix_world = M4.Translation(t_) @ R_.to_4x4() @ mathutils.Matrix.Diagonal((*dc.scale, 1.0))
                dc.keyframe_insert("location", frame=f_); dc.keyframe_insert("rotation_quaternion", frame=f_)
            for f_, t_, R_ in kq_:   # tay TRÁI cũng nắm cứng theo rìu sau đổi nhịp (nội suy riêng ⇒ lệch cán 23,5°, đo 22/10)
                sc.frame_set(f_); bpy.context.view_layer.update(); ph_ = rig.pose.bones["hand_L"]
                m_ = (rig.matrix_world.inverted().to_3x3() @ R_ @ CN["L"]).to_4x4(); m_.translation = ph_.matrix.translation
                ph_.matrix = m_; bpy.context.view_layer.update(); ph_.keyframe_insert("rotation_quaternion", frame=f_)
    ng_ = 0.0
    for f in range(sc.frame_start, sc.frame_end + 1):
        sc.frame_set(f); bpy.context.view_layer.update(); zz = (dc.matrix_world.to_3x3() @ V((0, 0, 1))).normalized()
        for b in "LR":
            hb = rig.data.bones[f"hand_{b}"]; Mh = rig.matrix_world @ rig.pose.bones[f"hand_{b}"].matrix @ hb.matrix_local.inverted()
            sa = (Mh.to_3x3() @ V(SK[f"cam_{b}"]["len"])).normalized(); ng_ = max(ng_, min(math.degrees(sa.angle(zz)), math.degrees(sa.angle(-zz))))
    def buoc_xoan(lay):
        bmax = 0.0; prev = None
        for f in range(sc.frame_start, sc.frame_end + 2):
            sc.frame_set(f); bpy.context.view_layer.update(); a_, x_ = lay()
            if prev:
                a0, x0 = prev; xt = a0.rotation_difference(a_) @ x0; xt = (xt - a_ * xt.dot(a_)).normalized(); xx = (x_ - a_ * x_.dot(a_)).normalized()
                bmax = max(bmax, abs(math.degrees(math.atan2(a_.dot(xt.cross(xx)), xt.dot(xx)))) / max(1.0, TOC.get(f, 1.0)))   # đổi nhịp: đo theo thời gian gốc
            prev = (a_, x_)
        return round(bmax, 1)
    def truc_xuong(n):
        def g2():
            M = (rig.matrix_world @ rig.pose.bones[n].matrix).to_3x3().normalized(); return M.col[1].normalized(), M.col[0].normalized()
        return g2
    NAM_KQ = dict(nam_goc_vench_deg=round(ng_, 1), can_vench_video_deg=round(vench, 1), nam_lech_can_mm=round(max(LECH_NAM) * 1000, 1),
                  **{"16_riu_xoay_quanh_can_buoc_deg": buoc_xoan(lambda: ((dc.matrix_world.to_3x3() @ V((0, 0, 1))).normalized(), (dc.matrix_world.to_3x3() @ V((1, 0, 0))).normalized())),
                     "16_tay_xoan_buoc_deg": max(buoc_xoan(truc_xuong(f"{x}_{b}")) for x in ("hand", "forearm") for b in "LR")})
    if os.environ.get("RIU3D"):   # ⑰ LƯỠI (+X mesh) hướng TRƯỚC hông (Boss 22/10 «Lưỡi axe đang quay ngược về sau») · ⑱ NẮM CỐ ĐỊNH: chỗ nắm trượt dọc cán (Boss «chỉ cần nắm cố định là xong»)
        cs_ = []; doc_ = {"L": [], "R": []}; ngang_ = []
        cso_ = next((pr.get("cua_so_chem") for pr in clip.get("props", []) if pr.get("cua_so_chem")), None)
        for f in range(H.khoang(N)[0], H.khoang(N)[1] + 1):
            sc.frame_set(f); bpy.context.view_layer.update(); Pb_ = rig.pose.bones; Wm_ = rig.matrix_world
            lr_ = (Wm_ @ Pb_["thigh_L"].head) - (Wm_ @ Pb_["thigh_R"].head); fw_ = lr_.cross(V((0, 0, 1))); fw_.z = 0; fw_.normalize()
            Md_ = dc.matrix_world.to_3x3().normalized()
            if abs(Md_.col[2].normalized().z) <= 0.65: ngang_.append(abs(Md_.col[0].normalized().z))   # cán gần thẳng đứng ⇒ «ngang» không xác định, bỏ
            if os.environ.get("IN_XR"): print("DOC", f, round(Md_.col[0].normalized().z, 2), "fw", round(Md_.col[0].dot(fw_), 2))
            if not cso_ or cso_[0] <= f <= cso_[1]: cs_.append(Md_.col[0].dot(fw_))   # ⑰ chỉ trong cửa sổ VUNG→TRÚNG (giơ qua vai: lưỡi ngang buộc chếch sau)
            for b_ in "LR": doc_[b_].append((sock(b_) - dc.matrix_world.translation).dot(Md_.col[2].normalized()))
        NAM_KQ["17_luoi_truoc_cos_min"] = round(min(cs_), 2)
        NAM_KQ["19_luoi_doc_max"] = round(max(ngang_), 2)   # ⑲ Boss 22/10 «blade is pointing upward, supose to be horizontol»: |thành phần đứng của lưỡi|
        NAM_KQ["18_nam_truot_doc_can_mm"] = round(max(max(v_) - min(v_) for v_ in doc_.values()) * 1000, 1)
    # ⑳ LƯNG GẬP KHÚC (Boss 22/10 «lúc chặt cây cái lưng của settler bị cong dữ vậy»): xoay ngực so với lưng dưới (trừ tư thế nghỉ).
    # Người mẫu 2–13°; hiệu chỉnh theo đoạn spine2→spine3 (5 cm, nghiêng sẵn 30°) cho 36–41° ⇒ lưng gù chữ S. Ngưỡng 20°.
    gk_ = 0.0
    for f in range(H.khoang(N)[0], H.khoang(N)[1] + 1):
        sc.frame_set(f); bpy.context.view_layer.update(); Pb_ = rig.pose.bones; Bn_ = rig.data.bones
        qa_ = Pb_["spine"].matrix.to_quaternion() @ Bn_["spine"].matrix_local.to_quaternion().inverted(); qb_ = Pb_["chest"].matrix.to_quaternion() @ Bn_["chest"].matrix_local.to_quaternion().inverted()
        gk_ = max(gk_, math.degrees((qa_.inverted() @ qb_).angle))
    NAM_KQ["20_lung_gap_khuc_deg"] = round(gk_, 1)
    print("nam_sam", NAM_KQ)
    for pr in clip.get("props", []): pr["theo_hai_tay"] = False
elif dc is not None and g.lenh == "mocap" and any(pr.get("qua_hai_nam") for pr in clip.get("props", [])):
    # rìu ĐI QUA hai nắm tay mocap (tay đã đặt theo số đo tam giác thân — KHÔNG giải lại tay): gốc món = nắm TRÊN (gần đầu rìu),
    # chiều cán: nắm dưới → nắm trên, đầu rìu hướng RA XA ngực; lưỡi (+X) = chiều chuyển động của đầu rìu (lưỡi đi trước)
    def sock(b):
        hb = rig.data.bones[f"hand_{b}"]; return rig.matrix_world @ rig.pose.bones[f"hand_{b}"].matrix @ hb.matrix_local.inverted() @ V(SK[f"cam_{b}"]["vi_tri"])
    dc.parent = None; dc.rotation_mode = "QUATERNION"
    DAU_NAM = {}; E_TRUOC = {}; H0 = {}; X0 = {}; NAN = {}; H_TRUOC = {}; BL_TRUOC = {}
    def dat_tay(b, Rw):   # đặt bàn tay theo xoay THẾ GIỚI Rw (giữ vị trí cổ tay)
        pb = rig.pose.bones[f"hand_{b}"]; m = (rig.matrix_world.inverted().to_3x3() @ Rw).to_4x4(); m.translation = pb.matrix.translation; pb.matrix = m; bpy.context.view_layer.update()
    def nan_nam(b, z):   # nắn NHỎ trục nắm // cán (chiều đã chốt) — trả về góc phải nắn = độ vênh giữa xoay tay nguồn và cán
        pb = rig.pose.bones[f"hand_{b}"]; hb = rig.data.bones[f"hand_{b}"]; Mh = rig.matrix_world @ pb.matrix @ hb.matrix_local.inverted()
        sa = (Mh.to_3x3() @ V(SK[f"cam_{b}"]["len"])).normalized(); dz = z * DAU_NAM.get(b, 1); g_ = math.degrees(sa.angle(dz))
        m = pb.matrix.copy(); t = m.translation.copy(); m2 = sa.rotation_difference(dz).to_matrix().to_4x4() @ m; m2.translation = t; pb.matrix = m2; bpy.context.view_layer.update()
        return round(g_, 1)
    def xoay_long(b, z, v_ra):   # BÀN TAY theo LÒNG BÀN TAY (Boss 22/10): trục nắm = cán; lòng tay PHẢI hướng RA ngoài thân, TRÁI hướng VÀO
        # (xoay cổ tay của SAM 3D vênh 75–131° với trục rìu đo từ video ⇒ không dùng được; vị trí cổ tay + trục rìu là số đo tin được)
        pb = rig.pose.bones[f"hand_{b}"]; hb = rig.data.bones[f"hand_{b}"]; Mh = rig.matrix_world @ pb.matrix @ hb.matrix_local.inverted()
        sa = (Mh.to_3x3() @ V(SK[f"cam_{b}"]["len"])).normalized()
        if b not in DAU_NAM: DAU_NAM[b] = int(os.environ.get(f"DAU_NAM_{b}", "0")) or (1 if sa.dot(z) >= 0 else -1)
        dz = z * DAU_NAM[b]
        a0 = V(SK[f"cam_{b}"]["len"]).normalized(); h0 = (hb.tail_local - hb.head_local).normalized(); a0p = (a0 - h0 * a0.dot(h0)).normalized()
        # lòng bàn tay (lúc nghỉ) ⟂ CẢ hướng bàn tay lẫn trục nắm; chiều = phía có socket nắm
        # (bản trước chỉ bỏ phần dọc trục nắm ⇒ lấy nhầm hướng bàn tay làm lòng tay ⇒ cổ tay gập 140–170° mọi khung)
        o0 = V(SK[f"cam_{b}"]["vi_tri"]) - hb.head_local; pn0 = h0.cross(a0p).normalized()
        if o0.dot(pn0) < 0: pn0 = -pn0
        pt = v_ra if b == "R" else -v_ra; pt = pt * float(os.environ.get("LONG_LAT", "1")); pt = (pt - dz * pt.dot(dz)).normalized()
        B0 = mathutils.Matrix((a0p, pn0, a0p.cross(pn0))).transposed(); B = mathutils.Matrix((dz, pt, dz.cross(pt))).transposed()
        dat_tay(b, B @ B0.transposed() @ hb.matrix_local.to_3x3())
    def xoay_nam(b, z):   # BÀN TAY: trục nắm (socket «len») = trục cán; hướng bàn tay = hướng cẳng tay bỏ phần dọc cán (cổ tay thẳng nhất)
        # (xoay ngắn nhất từ trục nắm cũ sang cán ⇒ cổ tay gập 125°, 22/10)
        pb = rig.pose.bones[f"hand_{b}"]; hb = rig.data.bones[f"hand_{b}"]; Mh = rig.matrix_world @ pb.matrix @ hb.matrix_local.inverted()
        sa = (Mh.to_3x3() @ V(SK[f"cam_{b}"]["len"])).normalized()
        fa = (W_(f"forearm_{b}", True) - W_(f"forearm_{b}")).normalized()
        if b not in DAU_NAM:   # chiều trục nắm CHỐT 1 lần/tay theo LUẬT LÒNG TAY (Boss 22/10): lòng tay PHẢI hướng ra ngoài thân, TRÁI vào trong
            # (chọn lại mỗi khung ⇒ bàn tay lật 160–180°). Lòng tay = h × dz (h = cẳng tay ⟂ cán); thử 2 chiều, giữ chiều đúng luật
            v_ra = (W_("hand_R") + W_("hand_L")) / 2 - (W_("upperarm_L") + W_("upperarm_R") + W_("thigh_L") + W_("thigh_R")) / 4
            hb_ = rig.data.bones[f"hand_{b}"]; a0 = V(SK[f"cam_{b}"]["len"]).normalized(); h0 = (hb_.tail_local - hb_.head_local).normalized()
            a0p = (a0 - h0 * a0.dot(h0)).normalized(); o0 = V(SK[f"cam_{b}"]["vi_tri"]) - hb_.head_local; pn0 = h0.cross(a0p).normalized()
            if o0.dot(pn0) < 0: pn0 = -pn0
            k_ = h0.cross(a0p).dot(pn0)   # lòng tay lúc nghỉ = k_ · (h0 × a0p)
            muon = (1 if b == "R" else -1) if os.environ.get("LUAT_LONG") else 0; DAU_NAM[b] = 1 if sa.dot(z) >= 0 else -1
            # LUẬT LÒNG TAY (ra/vào) chỉ đúng ~50–60 % khung ở MỌI chiều (lòng tay quay theo cú vung) và đẩy cổ tay gập 100–120° ⇒ tắt mặc định; chiều = trục nắm khung 0
            if os.environ.get(f"DAU_NAM_{b}"): DAU_NAM[b] = int(os.environ[f"DAU_NAM_{b}"]); muon = 0
            for sg in (1, -1):
                dz_ = z * sg; h_ = (fa - dz_ * fa.dot(dz_)).normalized(); long_ = h_.cross(dz_) * k_
                if muon and long_.dot(v_ra) * muon > 0: DAU_NAM[b] = sg
        dz = z * DAU_NAM[b]
        h = fa - dz * fa.dot(dz)
        if b in H_TRUOC: h = h + (H_TRUOC[b] - dz * H_TRUOC[b].dot(dz)) * max(0.0, 0.35 - h.length) * 3   # chỉ khi cẳng tay gần // cán (h bất định) mới kéo về khung trước; kéo luôn 0,6 ⇒ cổ tay trễ, gập 100°
        h = h.normalized() if h.length > 1e-4 else dz.orthogonal().normalized(); H_TRUOC[b] = h.copy()
        a0 = V(SK[f"cam_{b}"]["len"]).normalized(); h0 = (hb.tail_local - hb.head_local).normalized(); a0p = (a0 - h0 * a0.dot(h0)).normalized()
        B0 = mathutils.Matrix((h0, a0p, h0.cross(a0p))).transposed(); B = mathutils.Matrix((h, dz, h.cross(dz))).transposed(); R = B @ B0.transposed()
        m = (rig.matrix_world.inverted().to_3x3() @ R @ hb.matrix_local.to_3x3()).to_4x4(); m.translation = pb.matrix.translation; pb.matrix = m; bpy.context.view_layer.update()
    def keo_co_tay(b, d, zc=None):   # dời cổ tay một đoạn d (thế giới) bằng giải 2 đoạn, khuỷu giữ mặt phẳng hiện tại; bàn tay giữ hướng thế giới
        pbh = rig.pose.bones[f"hand_{b}"]; Rh = (rig.matrix_world @ pbh.matrix).to_3x3().normalized()
        S_ = W_(f"upperarm_{b}"); E0 = W_(f"forearm_{b}"); Wt = W_(f"forearm_{b}", True) + d
        Lu = rig.data.bones[f"upperarm_{b}"].length; Lf = rig.data.bones[f"forearm_{b}"].length; dv = Wt - S_; dl = min(dv.length, Lu + Lf - 1e-4); u = dv.normalized()
        a_ = (Lu * Lu - Lf * Lf + dl * dl) / (2 * dl); r_ = math.sqrt(max(0.0, Lu * Lu - a_ * a_)); C_ = S_ + u * a_; v_ = (E0 - C_) - u * (E0 - C_).dot(u)
        v_ = v_.normalized() if v_.length > 1e-6 else u.orthogonal().normalized(); E_ = C_ + v_ * r_
        if zc is not None:   # xoay khuỷu quanh trục vai–cổ tay: cẳng tay gần ⟂ cán ⇒ cổ tay lệch ngang ≤ 40° như người thật;
            # tay DUỖI HẾT (tay settler ngắn hơn người mẫu) thì xoay khuỷu vô tác dụng ⇒ cho cổ tay nhích về vai ≤ 6 cm (Codex: f12–15 cổ tay gập gắt)
            tot = None
            for rut in ((0.0, 0.02, 0.04, 0.06) if dv.length >= Lu + Lf - 0.01 else (0.0,)):
                dl2 = min(dv.length, Lu + Lf - 1e-4) - rut; a2 = (Lu * Lu - Lf * Lf + dl2 * dl2) / (2 * dl2); r2 = math.sqrt(max(0.0, Lu * Lu - a2 * a2)); C2 = S_ + u * a2
                Wn = S_ + u * dl2
                for dg in range(-150, 151, 10):
                    v2 = mathutils.Quaternion(u, math.radians(dg)) @ v_; E2 = C2 + v2 * r2
                    lech = abs(90 - math.degrees((Wn - E2).angle(zc)))
                    dc_ = max(0.0, lech - float(os.environ.get("KHUYU_LECH", "40"))) * 5 + abs(dg) * float(os.environ.get("KHUYU_PHAT", "0.4")) + max(0.0, (E2.z - S_.z) * 100) * 2 + rut * 300
                    # giữ khuỷu theo SAM (phạt xoay 0,4/°; 0,05 ⇒ khuỷu nhảy mỗi khung ⇒ tay trái vặn −90°↔+100° mỗi vòng — Boss «tay trái xoắn xoắn»)
                    if tot is None or dc_ < tot[0]: tot = (dc_, E2, dl2)
            E_ = tot[1]; dl = tot[2]
        H.ngam(rig, f"upperarm_{b}", E_ - S_); bpy.context.view_layer.update(); H.ngam(rig, f"forearm_{b}", (S_ + u * dl) - E_); bpy.context.view_layer.update()
        m = (rig.matrix_world.inverted().to_3x3() @ Rh).to_4x4(); m.translation = pbh.matrix.translation; pbh.matrix = m; bpy.context.view_layer.update()
    Z = []; G = []
    for f in range(N + 1):
        sc.frame_set(f); bpy.context.view_layer.update(); c = (W_("upperarm_L") + W_("upperarm_R") + W_("thigh_L") + W_("thigh_R")) / 4
        for _ in range(int(os.environ.get("VONG_NAM", "6"))):   # hướng cán = ngón út → ngón trỏ của bàn tay NGUỒN (SAM 3D); đường cán qua giữa 2 nắm; kéo cổ tay vào trục + xoay nắm
            pR, pL = sock("R"), sock("L"); m_ = (pR + pL) / 2
            fe = sc.frame_end + 1 if os.environ.get("CHU_KY") else N
            z = H.CAN_DIR[f if f < fe else f - fe].copy() if H.CAN_DIR else (pR - pL).normalized()
            # chiều: đầu rìu phía tay PHẢI (tay trên, thuận phải; tay trái nắm đuôi) — «ra xa thân» lật rìu chĩa đất lúc lấy đà (22/10);
            # hai nắm sát nhau (< 5 cm) ⇒ giữ chiều khung trước
            if H.CAN_NGUON and H.CAN_NGUON[f if f < fe else f - fe] == "ban_tay":   # khung lấy đà (không đo được trên ảnh): đầu rìu phía tay phải
                if (pR - pL).length > 0.05: z = z if z.dot(pR - pL) >= 0 else -z
            if os.environ.get("CHIEU_RIU") == "tay_phai":
                if (pR - pL).length > 0.05: z = z if z.dot(pR - pL) >= 0 else -z
                elif Z: z = z if z.dot(Z[-1]) >= 0 else -z
            # mặc định: KHÔNG lật — nắm cán thì phía ngón trỏ/ngón cái của CẢ hai tay quay về đầu rìu ⇒ út→trỏ đo được tự chỉ đầu rìu
            for b, pb_ in (("R", pR), ("L", pL)):
                keo_co_tay(b, (m_ + z * (pb_ - m_).dot(z)) - pb_, z)
                if os.environ.get("TAY_XOAY", "cang") == "long":
                    v_ra = m_ - c; v_ra = (v_ra - z * v_ra.dot(z)); xoay_long(b, z, v_ra.normalized() if v_ra.length > 1e-4 else z.orthogonal().normalized())
                elif os.environ.get("TAY_XOAY") == "nguon" and H.XOAY_TAY and f > 0 and b in H0 and b in H.XOAY_TAY[f if f < fe else f - fe]:
                    # xoay cổ tay SAM 3D vênh 75–131° với trục rìu đo (nhân vật hoạt hình, nắm tay không lộ ngón) ⇒ CHỈ bật khi chỉ định
                    dat_tay(b, H.XOAY_TAY[f if f < fe else f - fe][b] @ X0[b].transposed() @ H0[b]); NAN[b] = max(NAN.get(b, 0), nan_nam(b, z))
                else: xoay_nam(b, z)
        if os.environ.get("IN_LONG"):
            v_ra = m_ - c
            for b in "RL":
                hb_ = rig.data.bones[f"hand_{b}"]; Mh = (rig.matrix_world @ rig.pose.bones[f"hand_{b}"].matrix).to_3x3() @ hb_.matrix_local.to_3x3().inverted()
                a0 = V(SK[f"cam_{b}"]["len"]).normalized(); h0 = (hb_.tail_local - hb_.head_local).normalized(); a0p = (a0 - h0 * a0.dot(h0)).normalized()
                o0 = V(SK[f"cam_{b}"]["vi_tri"]) - hb_.head_local; pn0 = h0.cross(a0p).normalized(); pn0 = pn0 if o0.dot(pn0) >= 0 else -pn0
                pw = (Mh @ pn0).normalized(); print("LONG", f, b, "ra" if pw.dot(v_ra) > 0 else "vao")
        if os.environ.get("IN_GAP"):
            print("GAP", f, " ".join(f"{b}:{math.degrees((W_(f'forearm_{b}', True) - W_(f'forearm_{b}')).angle(W_(f'hand_{b}', True) - W_(f'hand_{b}'))):.0f}" for b in "RL"))
        if os.environ.get("IN_NAM"):
            pR, pL = sock("R"), sock("L"); m_ = (pR + pL) / 2
            print("NAM", f, " ".join(f"{b}: cang-can {math.degrees((W_(f'forearm_{b}', True) - W_(f'forearm_{b}')).angle(z)):.0f} gap {math.degrees((W_(f'forearm_{b}', True) - W_(f'forearm_{b}')).angle(W_(f'hand_{b}', True) - W_(f'hand_{b}'))):.0f} lech {((sock(b) - m_) - z * (sock(b) - m_).dot(z)).length * 1000:.0f}" for b in "RL"))
        for b in ("LR" if os.environ.get("BAN_LE","0")=="1" else ""): BL_TRUOC[b] = H.ban_le_khuyu(rig, b, BL_TRUOC.get(b))   # khuỷu = bản lề ⇒ xoắn bắp tay do hình học quyết định
        for b in "LR":   # CHIA ĐỘ XOẮN: cẳng tay xoắn 50 % giữa bắp tay (không xoắn) và bàn tay (đặt theo cán) — chỉ hướng ⇒ xoắn trống, giật 83°/frames
            pf = rig.pose.bones[f"forearm_{b}"]; ph = rig.pose.bones[f"hand_{b}"]; Wm = rig.matrix_world
            Mh = (Wm @ ph.matrix).copy(); Mf = (Wm @ pf.matrix).to_3x3().normalized(); Mu = (Wm @ rig.pose.bones[f"upperarm_{b}"].matrix).to_3x3().normalized()
            a_ = Mf.col[1].normalized(); xu = Mu.col[1].normalized().rotation_difference(a_) @ Mu.col[0]; xu = (xu - a_ * xu.dot(a_)).normalized()
            xh = Mh.to_3x3().normalized().col[0]; xh = (xh - a_ * xh.dot(a_)); xh = xh.normalized() if xh.length > 1e-4 else xu
            xt = (xu + xh); xt = xt.normalized() if xt.length > 1e-4 else xu
            xf = (Mf.col[0] - a_ * Mf.col[0].dot(a_)).normalized(); g_ = math.atan2(a_.dot(xf.cross(xt)), xf.dot(xt))
            m = pf.matrix.copy(); t = m.translation.copy(); m2 = mathutils.Matrix.Rotation(g_, 4, Wm.inverted().to_3x3() @ a_) @ m; m2.translation = t
            pf.matrix = m2; bpy.context.view_layer.update(); ph.matrix = Wm.inverted() @ Mh; bpy.context.view_layer.update()
        for b in "LR": E_TRUOC[b] = W_(f"forearm_{b}").copy()   # khuỷu khung này ⇒ mốc liền mạch cho khung sau
        if f == (sc.frame_end + 1 if os.environ.get("CHU_KY") else N):   # vòng lặp: khung cuối chu kỳ ≡ khung 0 (giải riêng ⇒ mối nối 15,7–25,6 mm)
            for b in "LR":
                for x in ("upperarm", "forearm", "hand"): rig.pose.bones[f"{x}_{b}"].rotation_quaternion = Q0[(x, b)]
            bpy.context.view_layer.update()
        for b in "LR":
            for x in ("upperarm", "forearm", "hand"): rig.pose.bones[f"{x}_{b}"].keyframe_insert("rotation_quaternion", frame=f)
        if f == 0:
            Q0 = {(x, b): rig.pose.bones[f"{x}_{b}"].rotation_quaternion.copy() for b in "LR" for x in ("upperarm", "forearm", "hand")}
            if H.XOAY_TAY:   # MỐC: khung 0 tay đã ôm cán ⇒ H0 (bàn tay đích) ↔ X0 (cổ tay nguồn đã đổi khung thân)
                for b in "LR":
                    if b in H.XOAY_TAY[0]: H0[b] = (rig.matrix_world @ rig.pose.bones[f"hand_{b}"].matrix).to_3x3().normalized(); X0[b] = H.XOAY_TAY[0][b]
        pR, pL = sock("R"), sock("L"); m_ = (pR + pL) / 2
        tmin = min((pR - m_).dot(z), (pL - m_).dot(z)); tren = m_ + z * (tmin + float(os.environ.get("NAM_DUOI", "0.28")))   # nắm DƯỚI ở −0,28 (cán tới −0,32)
        Z.append(z); G.append(tren)
    Zs = Z
    # LƯỠI (+X) gắn CỨNG theo bàn tay phải: hướng bàn tay (cổ tay→đốt) bỏ phần dọc cán; chiều chốt 1 lần ở khung trúng (lưỡi đi trước)
    # (lưỡi theo hướng chuyển động ⇒ rìu xoay quanh cán 119°/khung, gần 360° cả vòng — Boss 22/10)
    HR = []
    for f in range(N + 1):
        sc.frame_set(f); bpy.context.view_layer.update(); h_ = (W_("hand_R", True) - W_("hand_R")).normalized(); z = Zs[f]; hp = h_ - z * h_.dot(z)
        if HR:   # bàn tay gần // cán ⇒ hướng lưỡi bất định (giật 105°/frames) ⇒ kéo về khung trước theo độ bất định
            pr_ = HR[-1] - z * HR[-1].dot(z); hp = hp + pr_ * max(0.0, 0.5 - hp.length) * 4
            if hp.dot(pr_) < 0 and hp.length < 0.5: hp = pr_
        HR.append(hp.normalized() if hp.length > 1e-5 else HR[-1])
    fh = next((e["frame"] for e in clip.get("events", []) if e["name"] == "hit"), N // 3)
    vh = (G[fh + 1] + Zs[fh + 1] * 0.67) - (G[fh - 1] + Zs[fh - 1] * 0.67); dau_x = 1 if HR[fh].dot(vh) >= 0 else -1
    xp = None; zp = None; LIM = math.radians(float(os.environ.get("RIU_XOAY_MAX", "25")))
    for f in range(N + 1):
        z = Zs[f]; x = HR[f] * dau_x
        if xp is not None:   # VẬT LÝ: tay không vặn rìu > 25°/frames quanh cán (đỉnh lấy đà: bàn tay // cán ⇒ hướng lưỡi bất định, giật 90–102°)
            xt = zp.rotation_difference(z) @ xp; xt = (xt - z * xt.dot(z)).normalized()
            g_ = math.atan2(z.dot(xt.cross(x)), xt.dot(x)); g2 = max(-LIM, min(LIM, g_))
            x = mathutils.Quaternion(z, g2) @ xt
        x = (x - z * x.dot(z)).normalized(); xp = x.copy(); zp = z.copy()
        dc.matrix_world = M4.Translation(G[f]) @ M4((x, z.cross(x), z)).transposed().to_4x4()
        dc.keyframe_insert("location", frame=f); dc.keyframe_insert("rotation_quaternion", frame=f)
    nl, ng_, nz = 0.0, 0.0, []   # đo nắm: socket cách TRỤC cán (mm), góc trục nắm–cán (°), vị trí dọc cán (m, cán −0,32…0,73)
    for f in range(N + 1):
        sc.frame_set(f); bpy.context.view_layer.update(); M = dc.matrix_world; o = M.translation; z = (M.to_3x3() @ V((0, 0, 1))).normalized()
        for b in "LR":
            q = sock(b) - o; t_ = q.dot(z); nl = max(nl, (q - z * t_).length); nz.append(t_)
            hb = rig.data.bones[f"hand_{b}"]; Mh = rig.matrix_world @ rig.pose.bones[f"hand_{b}"].matrix @ hb.matrix_local.inverted()
            sa = (Mh.to_3x3() @ V(SK[f"cam_{b}"]["len"])).normalized(); ng_ = max(ng_, min(math.degrees(sa.angle(z)), math.degrees(sa.angle(-z))))
    NAM_KQ = dict(nam_lech_truc_mm=round(nl * 1000, 1), nam_goc_deg=round(ng_, 1), nam_doc_can_m=[round(min(nz), 2), round(max(nz), 2)],
                  tay_nguon_nan_deg=NAN)   # góc phải nắn tay-nguồn cho ôm cán (lớn ⇒ xoay cổ tay nguồn vênh với trục rìu đo)
    # ⑯ XOẮN (Boss 22/10 «cây rìu xoay 360 độ… hai cánh tay xoắn theo»): bước xoay quanh trục lớn nhất mỗi khung — rìu quanh cán, bàn tay quanh xương
    def buoc_xoan(lay):
        bmax = 0.0; prev = None
        for f in range(sc.frame_start, sc.frame_end + 2):
            sc.frame_set(f); bpy.context.view_layer.update(); a_, x_ = lay()
            if prev:
                a0, x0 = prev; xt = a0.rotation_difference(a_) @ x0; xt = (xt - a_ * xt.dot(a_)).normalized(); xx = (x_ - a_ * x_.dot(a_)).normalized()
                bmax = max(bmax, abs(math.degrees(math.atan2(a_.dot(xt.cross(xx)), xt.dot(xx)))))
            prev = (a_, x_)
        return round(bmax, 1)
    def truc_mon():
        M = dc.matrix_world.to_3x3().normalized(); return M.col[2].normalized(), M.col[0].normalized()
    def truc_xuong(n):
        def g():
            M = (rig.matrix_world @ rig.pose.bones[n].matrix).to_3x3().normalized(); return M.col[1].normalized(), M.col[0].normalized()
        return g
    NAM_KQ["16_riu_xoay_quanh_can_buoc_deg"] = buoc_xoan(truc_mon)
    NAM_KQ["16_tay_xoan_buoc_deg"] = max(buoc_xoan(truc_xuong(f"{x}_{b}")) for x in ("hand", "forearm") for b in "LR")
    print("nam", NAM_KQ)
    for pr in clip.get("props", []): pr["theo_hai_tay"] = False
elif dc is not None and g.lenh == "mocap" and any(pr.get("tay") for pr in clip.get("props", [])):   # mocap: 2 tay giải tích bám cán
    pr_ = next(pr for pr in clip["props"] if pr.get("tay"))
    if pr_.get("dung_quat_mocap"):   # rìu theo CÁNH QUẠT canh nhịp mẫu (cổ tay MP sai khi 2 tay chụm bị che)
        vn = (K["vai_L"] + K["vai_R"]) / 2; lech = []   # tâm quạt dời theo giữa hai vai của thân mocap từng khung (tâm cố định ⇒ với hụt 131 mm)
        for f in range(N + 1):
            sc.frame_set(f); bpy.context.view_layer.update(); lech.append((W_("upperarm_L") + W_("upperarm_R")) / 2 - vn)
        quat = pr_; H.riu_quat(dc, pr_["quy_dao"], N, True, lech=lech)
        if pr_.get("nam_theo_tay_mocap"):   # VỊ TRÍ nắm = giữa hai nắm tay của thân mocap (luôn trong tầm với); quạt chỉ cho HƯỚNG cán + lưỡi
            # (tâm quạt cố định độ cao ⇒ tay phải với 0,60–0,63 m > tầm 0,56 m ở lấy đà và sau trúng, 22/10)
            C_ = []
            for f in range(N + 1):
                sc.frame_set(f); bpy.context.view_layer.update(); C_.append((W_("hand_R", True) + W_("hand_L", True)) / 2)
            C_ = [(C_[(i - 1) % N] + C_[i % N] + C_[(i + 1) % N]) / 3 for i in range(N + 1)]   # làm mượt TUẦN HOÀN (khung N ≡ 0; không vòng ⇒ mối nối 116 mm)
            if pr_.get("nang_tay"):   # cổ tay MP bị che lúc lấy đà ⇒ tay ở hông thay vì ngang đầu như mẫu: nâng theo bảng {khung: m}
                nk = {float(k): dict(z=v) for k, v in pr_["nang_tay"].items()}
                C_ = [c + V((0, 0, H.noi_suy(nk, f, True, N)["z"])) for f, c in enumerate(C_)]
            for f in range(N + 1):
                sc.frame_set(f); bpy.context.view_layer.update(); M = dc.matrix_world.copy(); z_ = (M.to_3x3() @ V((0, 0, 1))).normalized()
                zm = sum(H.z_nam(zc, f) for _, zc in pr_["tay"]) / len(pr_["tay"])
                M.translation = C_[f] - z_ * zm; dc.matrix_world = M; dc.keyframe_insert("location", frame=f)
    else:
        H.riu_tu_mocap(dc, N)
    H.nam_hai_tay(rig, SK, dc, pr_["tay"], N)
    for pr in clip.get("props", []): pr["theo_hai_tay"] = False
if dc is not None and any(pr.get("theo_hai_tay") for pr in clip.get("props", [])):   # B: cán rìu đi qua HAI nắm tay
    dc.parent = None; trucx = None
    def sock(b):
        hb = rig.data.bones[f"hand_{b}"]; return rig.matrix_world @ rig.pose.bones[f"hand_{b}"].matrix @ hb.matrix_local.inverted() @ V(SK[f"cam_{b}"]["vi_tri"])
    for f in range(N + 1):
        sc.frame_set(f); bpy.context.view_layer.update()
        pR, pL = sock("R"), sock("L"); z = (pR - pL).normalized()
        x = truoc_hong(); x = (x - z * x.dot(z)).normalized()   # lưỡi quay về phía trước người
        dc.matrix_world = M4.Translation(pR) @ M4((x, z.cross(x), z)).transposed().to_4x4()
        dc.keyframe_insert("location", frame=f); dc.rotation_mode = "QUATERNION"; dc.keyframe_insert("rotation_quaternion", frame=f)

# khúc gỗ đặt xuống: khung thế giới (vai → trước ngực → đất), giữ nguyên thế giới khi đổi chủ
if go is not None and pr_go.get("che_do") == "dat":
    kk = pr_go["khung"]; f_vai = int(kk["roi_vai"] * N / 64); f_dat = int(kk["cham_dat"] * N / 64); f_bo = int(kk["buong"] * N / 64)
    Ws = []
    for f in range(0, f_vai + 1):
        sc.frame_set(f); bpy.context.view_layer.update(); Ws.append(go.matrix_world.copy())
    go.parent = None
    for f, Wm in enumerate(Ws):
        Wm = M4.Translation(V((0, 0, 0.04 * f / max(1, f_vai)))) @ Wm   # nhấc khỏi vai 4 cm
        go.matrix_world = Wm; go.keyframe_insert("location", frame=f); go.rotation_mode = "XYZ"; go.keyframe_insert("rotation_euler", frame=f)
    r = 0.09; dx, dy, _ = pr_go.get("dich", [0, -0.45, 0])
    # quỹ đạo: nhấc lên-ra trước GIỮ hướng dọc, chỉ xoay ngang khi đã cách ngực ≥ 0,5 m (bản cũ xoay sát ngực ⇒ xuyên 100 mm)
    for f, (p, rz) in ((int(21 * N / 64), (V((-0.20, -0.42, 1.58)), 0)), (int(28 * N / 64), (V((0, -0.68, 1.25)), 45)), (int(36 * N / 64), (V((0, dy, 0.50)), 90)), (int(44 * N / 64), (V((0, dy, r + 0.02)), 90)),
                       (f_dat, (V((0, dy, r)), 90)), (N, (V((0, dy, r)), 90))):
        go.location = p; go.rotation_euler = (math.radians(90), 0, math.radians(rz)); go.keyframe_insert("location", frame=f); go.keyframe_insert("rotation_euler", frame=f)

# chặt cây: đặt THÂN CÂY tại chỗ lưỡi rìu ở khung «hit» (cùng cách cho A và B)
if clip["id"].startswith("chop") and dc is not None:
    hit = next((e["frame"] for e in clip.get("events", []) if e["name"] == "hit"), N // 2)
    if g.lenh == "retarget":   # B: không có mốc khung (mocap CÓ mốc hit trong clip — dò điểm thấp nhất đặt cây sai phía, 22/10) ⇒ chém trúng = điểm THẤP NHẤT của đầu rìu sau đỉnh vung đầu tiên
        zz = []
        for f in range(N + 1):
            sc.frame_set(f); bpy.context.view_layer.update(); zz.append((dc.matrix_world @ V((0.1, 0, 0.55))).z)
        dinh = max(range(len(zz)), key=lambda i: zz[i]); hit = min(range(dinh, len(zz)), key=lambda i: zz[i]) if dinh < len(zz) - 1 else dinh
        print("B hit", hit, "đỉnh", dinh)
    sc.frame_set(hit); bpy.context.view_layer.update()
    dau = max((o for o in dc.children), key=lambda o: o.matrix_world.translation.z if False else (o.matrix_world @ V((0.15, 0, 0.55))).length)
    dau_ = next((pr.get("dau") for pr in clip.get("props", []) if pr.get("ben") == "R"), None) or [0.17, 0, 0.55]
    p = dc.matrix_world @ V(dau_); xz = (p.xy - rig.matrix_world.translation.xy)
    bpy.ops.mesh.primitive_cylinder_add(vertices=8, radius=0.20, depth=4.0, location=(p.x + xz.normalized().x * 0.18, p.y + xz.normalized().y * 0.18, 2.0))
    cay = bpy.context.object; m = bpy.data.materials.new("vo"); m.use_nodes = True; m.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.32, 0.22, 0.14, 1); cay.data.materials.append(m)

# CHÂN KHÔNG XOAY VÀO (Boss 23/10 «bàn chân phải nó cứ xoay vô»): clip DI CHUYỂN ⇒ xoay chân quanh trục hông→cổ chân, cổ chân đứng yên
# ⛔ KHÔNG sửa ở đây: rig còn IK chân ⇒ xoay đùi làm IK giải lại (thử 23/10: cổ chân 119→159°, bàn chân vặt 10→53°). Chỉ ĐO; sửa ở cảnh trên clip đã bake.
CHAN_XOAY = H.do_chan_xoay(rig, 0, N) if clip["root"].get("mode") == "root_motion" else None
kq = H.cua(rig, K, N, clip, than, dc, go)
if CHAN_XOAY is not None:
    kq["21_chan_vao_ra_deg_chua_sua"] = CHAN_XOAY   # báo cáo; cảnh dùng clip PHẢI gọi H.sua_chan_xoay (cửa ở cảnh)
kq["0_truc_giai_phau_loi"] = loi_truc; kq["dinh_khong_trong_so"] = trong
# ⑭b CỔ TAY THEO TRỤC GIẢI PHẪU (Boss 23/10 «Ko được để cổ tay gập như vầy, như vầy là sai với anatomy»): gập ≤ 80 · ngửa ≤ 70 · lệch ngang ≤ 25 ·
# xoắn TẠI cổ tay ≤ 15 (xoắn thuộc cẳng tay). Cửa ⑭ cũ chỉ đo TỔNG góc ⇒ cổ tay bẻ ngang 46° + xoắn 97° vẫn lọt (cuốc v1).
VUOT_CT = 0.0; TE_CT = None
for f in range(H.khoang(N)[0], H.khoang(N)[1] + 1):
    sc.frame_set(f); bpy.context.view_layer.update()
    for b_ in "LR":
        d_ = H.co_tay_giai_phau(rig, b_, VO_NGUOI["_long_ban_tay"][b_]["phap_tuyen"]); v_ = H.vuot_co_tay(d_)
        if v_ > VUOT_CT: VUOT_CT, TE_CT = v_, (f, b_, d_)
kq["14b_co_tay_vuot_bien_deg"] = round(VUOT_CT, 1); kq["14b_co_tay_te"] = TE_CT
if go is not None and os.environ.get("TAY_GIU_GO"):
    kq["5b_tay_xuyen_go_mm"] = H.tay_xuyen_go(rig, than, go, N); kq["12_khuyu_lat_buoc_max_deg"], kq["12_khuyu_lat_tong_deg"] = H.lat_khuyu(rig, "R", N)
    kq["dat"] = kq["dat"] and kq["5b_tay_xuyen_go_mm"] <= 3 and kq["12_khuyu_lat_buoc_max_deg"] <= 6
if quat:
    kq.update(H.do_quat(dc, quat["quy_dao"], N, quat["cua_so_chem"], quat.get("dau", (0.12, 0, 0.67))))
    kq.update(H.do_nam_can(rig, SK, dc, quat["tay"], N))
    kq["15_riu_xuyen_than_mm"], kq["15_o_khung"] = H.riu_xuyen_than(rig, than, dc, N)
    vet = []
    for f in range(N + 1):
        sc.frame_set(f); bpy.context.view_layer.update(); vet.append(list(dc.matrix_world @ V(quat.get("dau", (0.12, 0, 0.67)))))
    json.dump(dict(tam=quat["quy_dao"]["tam"], dau=vet, cua_so=quat["cua_so_chem"]), open(os.path.join(g.out, clip['id'] + '_trajectory.json'), "w"))
    kq["dat"] = kq["dat"] and kq["quat_lech_mat_mm"] <= 40 and kq["quat_ban_kinh_pct"] <= 10 and kq["quat_don_dieu"] and kq["luoi_di_truoc_cos"] >= 0.8 \
        and kq["nam_lech_mm"] <= 5 and kq["nam_goc_deg"] <= 12 and kq["15_riu_xuyen_than_mm"] <= 3
kq["dat"] = kq["dat"] and not loi_truc and trong == 0 and kq["14b_co_tay_vuot_bien_deg"] <= 0.0
# 1c CHÂN THẤP MÀ BAY (audit 23/10: ① mù với chân tự do ở +2 cm) — đo từ pose đã bake, ngưỡng tốc độ hiệu chuẩn H.CHAN_THAP_V_MAX; quãng bay sát đất ≤ 5 mm
if kq.get("1c_chan_thap_bay_mm", 0) > 5: print(f"⛔ 1c chân thấp mà bay: {kq['1c_chan_thap_bay_mm']} mm (tốc độ sát đất max {kq['1c_toc_do_thap_max_mps']} m/s > {H.CHAN_THAP_V_MAX})"); kq["dat"] = False
# HÔNG RUNG (Boss «rung rung»; audit T6): RMS sai phân bậc 2 hips.z ≤ 8 mm — đo 23/10: idle 0.03 · Kimodo bow 1.31 · walk 2.96 · lao 6.16 · hạ hông từng khung 11.34
if kq.get("hong_rung_mm", 0) > 8: print(f"⛔ hông rung: hong_rung_mm {kq['hong_rung_mm']} > 8"); kq["dat"] = False
# CHÂN LƠ LỬNG / CHÂN RUNG (Boss 24/10 xem clip lao) — đo trong H.cua từ pose bake; ngưỡng rung hiệu chuẩn H.CHAN_RUNG_MAX_MM/DEG
if kq.get("chan_lo_lung_frames", 0) > 0: print(f"⛔ chân lơ lửng: {kq['chan_lo_lung_frames']} khung {kq.get('chan_lo_lung_o')}"); kq["dat"] = False
if kq.get("chan_rung_max_mm", 0) > H.CHAN_RUNG_MAX_MM or kq.get("chan_rung_max_deg", 0) > H.CHAN_RUNG_MAX_DEG: print(f"⛔ chân rung: {kq.get('chan_rung_max_mm')} mm @{kq.get('chan_rung_max_o')} (≤ {H.CHAN_RUNG_MAX_MM}) · {kq.get('chan_rung_max_deg')}° @{kq.get('chan_rung_max_deg_o')} (≤ {H.CHAN_RUNG_MAX_DEG})"); kq["dat"] = False
# THÂN RUNG so với NGUỒN + HÔNG RUNG XY (P1-k, Boss 24/10 lần 3 «vẫn còn giật nhẹ lúc phóng lao» — cửa chân/hông-z mù với thân trên và hông XY)
if kq.get("than_rung_co_nguon") and kq.get("than_rung_max_ratio", 0) > H.THAN_RUNG_RATIO_MAX: print(f"⛔ thân rung so với nguồn: ×{kq['than_rung_max_ratio']} @{kq.get('than_rung_o')} (≤ {H.THAN_RUNG_RATIO_MAX}; vượt {kq.get('than_rung_vuot_deg')}° @{kq.get('than_rung_vuot_o')})"); kq["dat"] = False
if max(list(kq.get("hong_rung_xy_mm", {}).values()) or [0]) > H.HONG_RUNG_XY_MAX_MM: print(f"⛔ hông rung XY: {kq['hong_rung_xy_mm']} mm/khung² (≤ {H.HONG_RUNG_XY_MAX_MM} = 2 g) · nguồn {kq.get('hong_rung_xy_ng_mm')}"); kq["dat"] = False
print(f"GIAT_TOAN_THAN mean {kq.get('giat_toan_than_mm')} · max {kq.get('giat_toan_than_max_mm')} mm @{kq.get('giat_toan_than_max_o')} · than_rung ×{kq.get('than_rung_max_ratio')} @{kq.get('than_rung_o')} · hông XY {kq.get('hong_rung_xy_mm')}")
if TAY_KQ: kq.update(TAY_KQ)
if NAM_KQ and "nam_goc_vench_deg" in NAM_KQ:   # nhánh SAM thuần: chỉ báo số, không cửa nắm
    NAM_KQ["15_riu_xuyen_than_mm"], NAM_KQ["15_o_khung"] = H.riu_xuyen_than(rig, than, dc, H.khoang(N)[1]); kq.update(NAM_KQ)
    kq["dat"] = kq["dat"] and NAM_KQ["15_riu_xuyen_than_mm"] <= 3 and NAM_KQ["16_riu_xoay_quanh_can_buoc_deg"] <= 30 and NAM_KQ["16_tay_xoan_buoc_deg"] <= 60 \
        and NAM_KQ.get("17_luoi_truoc_cos_min", 1) >= 0.2 and NAM_KQ.get("18_nam_truot_doc_can_mm", 0) <= 15 and NAM_KQ.get("19_luoi_doc_max", 0) <= 0.25 and NAM_KQ.get("20_lung_gap_khuc_deg", 0) <= 20; NAM_KQ = None
if NAM_KQ:
    NAM_KQ["15_riu_xuyen_than_mm"], NAM_KQ["15_o_khung"] = H.riu_xuyen_than(rig, than, dc, H.khoang(N)[1])   # chỉ khoảng GIAO (khung 29 thừa báo 57 mm)   # ⑮ cũng cho rìu mocap (f27 lưỡi sát mặt)
if NAM_KQ: kq.update(NAM_KQ); kq["dat"] = kq["dat"] and NAM_KQ["15_riu_xuyen_than_mm"] <= 3 and NAM_KQ["nam_goc_deg"] <= 25 and -0.32 <= NAM_KQ["nam_doc_can_m"][0] \
    and NAM_KQ["16_riu_xoay_quanh_can_buoc_deg"] <= 30 and NAM_KQ["16_tay_xoan_buoc_deg"] <= 60   # ⑯ xoắn
# P0-a 23/10: KHÔNG xuất gì ở đây — mọi cửa (kể cả ㉒ ㉓) chạy xong rồi mới render/xuất ở cuối file (bản cũ xuất GLB/mp4 trước ㉒㉓ ⇒ clip rớt vẫn có GLB)
kq["truot"] = [] if kq["dat"] else ["cua_1_21"]
# cửa ㉓ BÀN CHÂN ĐỨNG PHẲNG (Boss 23/10/2026: «Sao bàn chân ko chạm đất hoàn toàn mà mũi chân chỉa lên vậy»; cửa 13b báo 0° trong khi
# mũi chân chĩa lên): khung nào cổ chân sát nền (≤ +3 cm) và gần đứng yên (< 0,35 m/s) ⇒ dốc bàn chân lệch dốc NGHỈ ≤ 6°
def _doc(v): return math.degrees(math.atan2(v.z, math.hypot(v.x, v.y)))
lech_doc = 0.0; khung_lech = None; _prev = {}
for f_ in range(0, N + 1):
    sc.frame_set(f_); bpy.context.view_layer.update(); Wm = rig.matrix_world
    for b_ in "LR":
        pf = rig.pose.bones[f"foot_{b_}"]; bf = rig.data.bones[f"foot_{b_}"]; h_ = Wm @ pf.head
        v_ = (h_ - _prev[b_]).length * H.FPS if b_ in _prev else 0.0; _prev[b_] = h_.copy()
        nghi = _doc(Wm.to_3x3() @ (bf.tail_local - bf.head_local)); hien = _doc((Wm @ pf.tail) - h_)
        if h_.z <= (Wm @ bf.head_local).z + 0.03 and v_ < 0.35 and abs(hien - nghi) > lech_doc: lech_doc = abs(hien - nghi); khung_lech = (f_, b_)
        if os.environ.get("NHON_DEBUG") and b_ == "R" and 63 <= f_ <= 82: print("CUA23", f_, "ankle_h_cm", round((h_.z - (Wm @ bf.head_local).z) * 100, 1), "v", round(v_, 2), "slope", round(hien, 1), "rest", round(nghi, 1), "dev", round(abs(hien - nghi), 1), "in_band", h_.z <= (Wm @ bf.head_local).z + 0.03 and v_ < 0.35)
kq["23_ban_chan_dung_lech_doc_nghi_deg"] = round(lech_doc, 1)
if lech_doc > 6: print(f"⛔ ㉓ bàn chân đứng không phẳng: lệch dốc nghỉ {lech_doc:.1f}° ở {khung_lech}"); kq["dat"] = False; kq["truot"].append("23_ban_chan_dung_phang")
# cửa ㉒ MẮT: body build có vật liệu mắt thì body sau animate PHẢI còn nó (đo trên object, không tin tên file)
con = [sl.material.name for sl in than.material_slots if sl.material]
mat_ok = all(m in con for m in MAT_MAT)
if not mat_ok: print(f"⛔ ㉒ mất vật liệu mắt: build có {MAT_MAT}, còn {con}"); kq["dat"] = False; kq["truot"].append("22_vat_lieu_mat")
json.dump(kq, open(os.path.join(g.out, f"{clip['id']}_gates.json"), "w"), indent=1, ensure_ascii=False)
print(clip["id"], json.dumps(kq, ensure_ascii=False))
# XUẤT SAU CÙNG, NGUYÊN TỬ (P0-a): rớt cửa ⇒ không có .glb/.mp4 trên đĩa (xoá cả bản cũ cùng tên); đạt ⇒ render/xuất ra <id>.tmp.* rồi đổi tên
MP4, GLB = os.path.join(g.out, f"{clip['id']}.mp4"), os.path.join(g.out, f"{clip['id']}.glb")
for p_ in (MP4, GLB, MP4.replace(".mp4", ".tmp.mp4"), GLB.replace(".glb", ".tmp.glb")):
    if os.path.exists(p_): os.remove(p_)
if kq["dat"] and not os.environ.get("KHONG_RENDER"):   # lặp nhanh: chỉ đo cửa
    H.render(rig, N, MP4.replace(".mp4", ".tmp.mp4"), theo=clip["root"].get("mode") == "root_motion" or g.lenh != "build")
    bpy.ops.export_scene.gltf(filepath=GLB.replace(".glb", ".tmp.glb"), export_animations=True)
    os.replace(MP4.replace(".mp4", ".tmp.mp4"), MP4); os.replace(GLB.replace(".glb", ".tmp.glb"), GLB)
if os.environ.get("XEM_THU"):   # XEM THỬ (chỉ để Boss nhìn): render <id>_xemthu.mp4 kể cả khi rớt cửa — KHÔNG xuất GLB, không đụng <id>.mp4, exit code giữ nguyên
    H.render(rig, N, MP4.replace(".mp4", "_xemthu.mp4"), theo=clip["root"].get("mode") == "root_motion" or g.lenh != "build")
print("✅ ĐẠT" if kq["dat"] else "⛔ TRƯỢT", clip["id"]); sys.exit(0 if kq["dat"] else 1)

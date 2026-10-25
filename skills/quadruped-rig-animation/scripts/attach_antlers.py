"""GẮN GẠC SÁT SỌ + CỔNG khe hở (Boss 23/10/2026: «hình như sừng nai vẫn đang còn gap rất to so với đầu»).
Đo: gạc Quaternius (bone-parent vào Head) khi nạp glTF vào Blender nằm cao hơn da đầu 17 cm (nai B cao 1,24 m ⇒ 14%), cả bản gốc
stag.glb lẫn stag_origami.glb, cả tư thế rest lẫn Idle ⇒ lỗi có từ file, mọi clip nai trước 23/10 đều dính.
Sửa: tư thế REST, lấy gốc gạc mỗi bên (2,5% đỉnh thấp nhất), điểm da đầu gần nhất ⇒ dời cả mesh gạc một vector (TB 2 bên) sao cho
gốc gạc cắm vào da CAM_MM. Ghi lại glb (giữ mọi action). Cổng: khe hở gốc gạc ↔ da sau khi sửa ≤ 1% chiều cao con vật, nếu không exit 1.
  blender -b -P attach_antlers.py -- <vao.glb> <ra.glb> [--chi-do]"""
import bpy, sys, numpy as np
from mathutils import Vector as V, Matrix as M

a_ = sys.argv[sys.argv.index("--") + 1:]; VAO, RA = a_[0], a_[1]; CHI_DO = "--chi-do" in a_; CAM_MM = 10
bpy.ops.wm.read_factory_settings(use_empty=True); bpy.ops.import_scene.gltf(filepath=VAO)
for o in list(bpy.data.objects):
    if o.name.startswith("Icosphere"): bpy.data.objects.remove(o)
arm = next(o for o in bpy.data.objects if o.type == "ARMATURE")
giu_ac = arm.animation_data.action if arm.animation_data else None
if arm.animation_data: arm.animation_data.action = None
for b in arm.pose.bones: b.matrix_basis = M.Identity(4)
bpy.context.view_layer.update(); dg = bpy.context.evaluated_depsgraph_get()


def pts(o):
    e = o.evaluated_get(dg); me = e.to_mesh(); P = np.array([tuple(e.matrix_world @ v.co) for v in me.vertices]); e.to_mesh_clear(); return P


than = next(o for o in bpy.data.objects if o.type == "MESH" and "Horn" not in o.name)
gac = next((o for o in bpy.data.objects if "Horn" in o.name), None)
if gac is None: print("KHONG_CO_GAC"); sys.exit(0)
B = pts(than); H = B[:, 2].max() - B[:, 2].min(); cx = B[:, 0].mean()


from mathutils.bvhtree import BVHTree
_e = than.evaluated_get(dg); _me = _e.to_mesh(); _mw = _e.matrix_world
BVH = BVHTree.FromPolygons([_mw @ v.co for v in _me.vertices], [tuple(p.vertices) for p in _me.polygons]); _e.to_mesh_clear()


def khe(G):
    """khoảng cách tới BỀ MẶT da (BVH), điểm nằm trong da = 0. Bản đầu đo tới ĐỈNH gần nhất ⇒ sàn ~1 cm do đỉnh low-poly thưa
    (23/10: chạm da rồi vẫn báo 1,1–1,4%)."""
    out = []
    for s in (1, -1):
        Gs = G[(G[:, 0] - cx) * s > 0]; da, dist = [], []
        for g in Gs:
            loc, nor, _i, d = BVH.find_nearest(V(g.tolist()))
            trong = (V(g.tolist()) - loc).dot(nor) < 0
            da.append(tuple(loc)); dist.append(0.0 if trong else d)
        da = np.array(da); dist = np.array(dist)
        k = max(5, len(Gs) // 40); i = np.argsort(dist)[:k]
        out.append((Gs[i], da[i], dist[i]))
    return out


G = pts(gac); k0 = khe(G); khe0 = max(float(x[2].mean()) for x in k0)
print(f"TRUOC khe gốc gạc ↔ da: {khe0 * 100:.1f} cm = {khe0 / H * 100:.1f}% cao")
if not CHI_DO:
    # lặp: điểm da gần nhất đổi sau mỗi lần dời (1 lần còn hở 2,9 cm)
    for _ in range(6):
        k_ = khe(G); v = np.mean([(da - goc).mean(0) for goc, da, _x in k_], 0)
        if max(float(x[2].mean()) for x in k_) < CAM_MM / 2000: break
        gac.matrix_world = M.Translation(V(v.tolist())) @ gac.matrix_world; bpy.context.view_layer.update(); dg = bpy.context.evaluated_depsgraph_get(); G = pts(gac)
    k_ = khe(G); v = np.mean([(da - goc).mean(0) for goc, da, _x in k_], 0); n = v / (np.linalg.norm(v) + 1e-9)
    gac.matrix_world = M.Translation(V((n * CAM_MM / 1000).tolist())) @ gac.matrix_world; bpy.context.view_layer.update()
    # bone-parent ⇒ SKIN Head trọng số 1 (bone-parent qua glTF bị importer đặt lệch lại: xuất rồi nạp còn hở 14,6 cm)
    ten_dau = next(b.name for b in arm.data.bones if b.name.lower() == "head")
    Gw = [gac.matrix_world @ v.co for v in gac.data.vertices]; Ai = arm.matrix_world.inverted()
    gac.parent = None; gac.parent = arm; gac.parent_type = "OBJECT"; gac.matrix_parent_inverse = M.Identity(4); gac.matrix_basis = M.Identity(4)
    for v, w in zip(gac.data.vertices, Gw): v.co = Ai @ w
    me = gac.data
    vg = gac.vertex_groups.new(name=ten_dau); vg.add(list(range(len(me.vertices))), 1.0, "REPLACE")
    md = gac.modifiers.new("Armature", "ARMATURE"); md.object = arm
    bpy.context.view_layer.update(); dg = bpy.context.evaluated_depsgraph_get(); G = pts(gac)
khe1 = max(float(x[2].mean()) for x in khe(G))
print(f"SAU khe: {khe1 * 100:.1f} cm = {khe1 / H * 100:.1f}% cao (cổng ≤ 1%)")
if not CHI_DO:
    if giu_ac: arm.animation_data.action = giu_ac
    bpy.ops.export_scene.gltf(filepath=RA, export_animations=True, export_animation_mode="ACTIONS")
sys.exit(0 if khe1 / H <= 0.01 else 1)

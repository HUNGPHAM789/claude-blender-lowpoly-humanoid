"""Render bộ công cụ: blender -b -P view_tools.py -- <thư mục công cụ> <nhân vật.glb> <nhân vật.json> <ảnh ra.jpg> [R=riu] [L=gio_berry]
Hàng trên: các món dựng đứng (cán theo Z). Bên phải: nhân vật LPM `--co 1` cầm đồ tại socket cam_R / cam_L
theo hợp đồng cầm: gốc món = vi_tri socket, +Z món = trục `len` của socket, +X món (phía làm việc) = tham số HUONG."""
import bpy, sys, math, json, mathutils
V = mathutils.Vector
a = sys.argv[sys.argv.index("--") + 1:]; DIR, NV, NVJ, OUT = a[:4]
if "settler" not in open(NVJ).read()[:0] + NV.lower() and "outfit" not in NV.lower():   # Boss 22/10: «use our finished settlers model»
    sys.exit("⛔ demo cầm đồ trên thân trơn bị chặn — dùng view_settler_hold.py với settler đã chốt (LPD CO=1 + tóc + đồ)")
CAM = dict(x.split("=") for x in a[4:]) or {"R": "riu", "L": "gio_berry"}
BO = ["riu", "pickaxe", "cuoc_dat", "xeng", "cung", "mui_ten", "can_cau", "binh_tuoi", "gio_berry"]
HUONG = {"riu": (0, 0, -1), "pickaxe": (0, 0, -1), "cuoc_dat": (0, 0, -1), "xeng": (0, 0, -1), "can_cau": (0, 0, 1),
         "cung": (1, 0, 0), "binh_tuoi": (0, 0, 1), "gio_berry": (0, 0, 1)}   # +X món chỉ về đâu khi cầm (thế giới, Z-up)
bpy.ops.wm.read_factory_settings(use_empty=True); sc = bpy.context.scene


def nhap(f):
    t = set(bpy.data.objects); bpy.ops.import_scene.gltf(filepath=f); moi = [o for o in bpy.data.objects if o not in t]
    g = bpy.data.objects.new("G", None); sc.collection.objects.link(g)
    for o in moi:
        if o.parent is None: o.parent = g
        if o.type == 'MESH':
            for p in o.data.polygons: p.use_smooth = False
    return g


x = 0.0
for ten in BO:                                    # hàng trưng bày, món đứng thẳng, gốc (chỗ cầm) ở cao 0,9 m
    g = nhap(f"{DIR}/{ten}.glb"); g.location = (x, 0, 0.9 if ten not in ("binh_tuoi", "gio_berry") else 0.35)
    if ten in ("binh_tuoi", "gio_berry"): g.rotation_euler = (0, math.radians(-90), 0)    # quai lên trên, thân treo dưới
    x += 0.42 if ten not in ("can_cau",) else 0.55
nv = nhap(NV); NX = x + 0.6; nv.location.x = NX
NGA = bpy.data.materials.new("nga"); NGA.use_nodes = True
NGA.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.80, 0.70, 0.58, 1)
for o in nv.children_recursive:
    if o.type == 'MESH': o.data.materials.clear(); o.data.materials.append(NGA)
sk = json.load(open(NVJ)); sk = sk.get("socket") or sk.get("sockets") or sk
for ben, ten in CAM.items():
    s = sk[f"cam_{ben}"]; z = V(s["len"]).normalized(); xw = V(HUONG[ten]); xw = (xw - z * xw.dot(z)).normalized(); y = z.cross(xw)
    g = nhap(f"{DIR}/{ten}.glb")
    g.matrix_world = mathutils.Matrix.Translation(V(s["vi_tri"]) + V((NX, 0, 0))) @ mathutils.Matrix((xw, y, z)).transposed().to_4x4()
for ten, (e, rot) in {"key": (3.2, (50, 0, -35)), "fill": (1.2, (60, 0, 60)), "rim": (1.8, (60, 0, 160))}.items():
    l = bpy.data.objects.new(ten, bpy.data.lights.new(ten, 'SUN')); sc.collection.objects.link(l); l.data.energy = e
    l.rotation_euler = [math.radians(v) for v in rot]
w = bpy.data.worlds.new("W"); sc.world = w; w.use_nodes = True; w.node_tree.nodes["Background"].inputs[0].default_value = (0.42, 0.44, 0.40, 1)
cam = bpy.data.cameras.new("c"); cam.type = 'ORTHO'; co = bpy.data.objects.new("c", cam); sc.collection.objects.link(co); sc.camera = co
sc.render.engine = "BLENDER_EEVEE"; sc.view_settings.view_transform = "Standard"; cam.clip_end = 100
tam = V((NX / 2 + 0.2, 0, 0.9)); cam.ortho_scale = NX + 1.4; sc.render.resolution_x, sc.render.resolution_y = 1800, 760
co.rotation_euler = (math.radians(80), 0, math.radians(-12)); co.location = tam + co.rotation_euler.to_matrix() @ V((0, 0, 30))
sc.render.filepath = OUT.replace(".jpg", "_a.png"); bpy.ops.render.render(write_still=True)
# cận cảnh nhân vật 3/4
cam.ortho_scale = 2.3; sc.render.resolution_x = sc.render.resolution_y = 900
co.rotation_euler = (math.radians(78), 0, math.radians(-40)); co.location = V((NX, 0, 0.95)) + co.rotation_euler.to_matrix() @ V((0, 0, 30))
sc.render.filepath = OUT.replace(".jpg", "_b.png"); bpy.ops.render.render(write_still=True)

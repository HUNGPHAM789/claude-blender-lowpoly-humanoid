"""Settler ĐÃ CHỐT (LPD + tóc + đồ) cầm công cụ: blender -b -P view_settler_hold.py -- <thư mục công cụ> <ảnh ra.png> <nhóm>...
nhóm = "<thân.glb>+<tóc.glb>+<đồ.glb>@<geometry.json>@R=riu,L=gio_berry"   (geometry.json của bản CO=1 có khoá 'socket')
Boss 22/10: «Why dont you use our finished settlers model to assembly them holding tools? We already nailed the settlers»
⇒ demo công cụ LUÔN trên settler đã chốt, không trên thân trơn.
Hợp đồng cầm: gốc món = socket vi_tri, +Z món = trục `len`, +X món theo HUONG."""
import bpy, sys, math, json, mathutils
V = mathutils.Vector
a = sys.argv[sys.argv.index("--") + 1:]; DIR, OUT, NHOM = a[0], a[1], a[2:]
HUONG = {"riu": (0, 0, -1), "pickaxe": (0, 0, -1), "cuoc_dat": (0, 0, -1), "xeng": (0, 0, -1), "can_cau": (0, 0, 1),
         "cung": (1, 0, 0), "binh_tuoi": (0, 0, 1), "gio_berry": (0, 0, 1), "mui_ten": (0, 0, 1)}
bpy.ops.wm.read_factory_settings(use_empty=True); sc = bpy.context.scene
NGA = bpy.data.materials.new("nga"); NGA.use_nodes = True
NGA.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.80, 0.66, 0.52, 1)


def nhap(f, la_than=False):
    t = set(bpy.data.objects); bpy.ops.import_scene.gltf(filepath=f); moi = [o for o in bpy.data.objects if o not in t]
    g = bpy.data.objects.new("G", None); sc.collection.objects.link(g)
    for o in moi:
        if o.parent is None: o.parent = g
        if o.type == 'MESH':
            for p in o.data.polygons: p.use_smooth = False
            for sl in o.material_slots:
                if not sl.material: continue
                sl.material.use_backface_culling = False
                if la_than and "eye" not in sl.material.name.lower() and "dark" not in sl.material.name.lower(): sl.material = NGA
    return g


for i, nhom in enumerate(NHOM):
    files, gj, cam = nhom.split("@"); X = i * 1.6   # đồ dài (cần câu 2 m, cung 1,4 m) chĩa ra trước ⇒ giãn hàng để không chồng người bên cạnh
    for f in files.split("+"):
        g = nhap(f, la_than="BODY" in f.split("/")[-1]); g.location.x = X
    sk = json.load(open(gj))["socket"]
    for muc in cam.split(","):
        ben, ten = muc.split("=")
        s = sk[f"cam_{ben}"]; z = V(s["len"]).normalized(); xw = V(HUONG.get(ten, (0, 0, -1))); xw = (xw - z * xw.dot(z)).normalized()
        g = nhap(f"{DIR}/{ten}.glb")
        g.matrix_world = mathutils.Matrix.Translation(V(s["vi_tri"]) + V((X, 0, 0))) @ mathutils.Matrix((xw, z.cross(xw), z)).transposed().to_4x4()
for ten, (e, rot) in {"key": (3.2, (45, 0, 45)), "fill": (1.2, (60, 0, 60)), "rim": (1.8, (60, 0, 160))}.items():
    l = bpy.data.objects.new(ten, bpy.data.lights.new(ten, 'SUN')); sc.collection.objects.link(l); l.data.energy = e; l.data.angle = math.radians(8); l.data.use_shadow = e >= 2.5; l.data.use_shadow_jitter = True
    l.rotation_euler = [math.radians(v) for v in rot]
w = bpy.data.worlds.new("W"); sc.world = w; w.use_nodes = True; w.node_tree.nodes["Background"].inputs[0].default_value = (0.42, 0.44, 0.40, 1)
cam = bpy.data.cameras.new("c"); cam.type = 'ORTHO'; co = bpy.data.objects.new("c", cam); sc.collection.objects.link(co); sc.camera = co
sc.render.engine = "BLENDER_EEVEE"; sc.view_settings.view_transform = "Standard"; cam.clip_end = 100
n = len(NHOM); cam.ortho_scale = max(2.4, n * 1.6 + 0.4); sc.render.resolution_x, sc.render.resolution_y = int(700 * max(n, 2.4)), 1000
for ten, rz in {"34": -35, "front": 0}.items():
    co.rotation_euler = (math.radians(80), 0, math.radians(rz))
    co.location = V(((n - 1) * 0.8, 0, 0.92)) + co.rotation_euler.to_matrix() @ V((0, 0, 30))
    sc.render.filepath = OUT.replace(".png", f"_{ten}.png"); bpy.ops.render.render(write_still=True)

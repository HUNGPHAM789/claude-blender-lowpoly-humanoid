"""Render CẬN vùng T (mặt) và mông: blender -b -P view_closeup.py -- <out.png> a.glb [b.glb]  ⇒ <out>_mat_*.png, <out>_mong_*.png"""
import bpy, sys, math, mathutils
V = mathutils.Vector
argv = sys.argv[sys.argv.index("--")+1:]; OUT, FILES = argv[0], argv[1:]
bpy.ops.wm.read_factory_settings(use_empty=True); sc = bpy.context.scene
m = bpy.data.materials.new("dat_set"); m.use_nodes = True
b = m.node_tree.nodes["Principled BSDF"]; b.inputs["Base Color"].default_value = (0.80, 0.70, 0.60, 1); b.inputs["Roughness"].default_value = 0.9
toi = bpy.data.materials.new("Eye_Dark"); toi.use_nodes = True
toi.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.05, 0.05, 0.06, 1)
for i, f in enumerate(FILES):
    t = set(bpy.data.objects); bpy.ops.import_scene.gltf(filepath=f)
    for o in bpy.data.objects:
        if o not in t:
            if o.parent is None: o.location.x += i * 0.6
            if o.type == 'MESH':
                o.data.materials.clear(); o.data.materials.append(toi if o.name.startswith("mat_") else m)
                for p in o.data.polygons: p.use_smooth = False
for ten, (e, nang, rot) in {"key": (3.4, (1, .93, .85), (40, 0, -30)), "fill": (0.9, (.8, .88, 1), (65, 0, 55)), "rim": (1.8, (1, 1, 1), (60, 0, 170))}.items():
    l = bpy.data.objects.new(ten, bpy.data.lights.new(ten, 'SUN')); sc.collection.objects.link(l)
    l.data.energy = e; l.data.color = nang; l.rotation_euler = [math.radians(x) for x in rot]
w = bpy.data.worlds.new("W"); sc.world = w; w.use_nodes = True; w.node_tree.nodes["Background"].inputs[0].default_value = (0.2, 0.21, 0.24, 1)
cam = bpy.data.cameras.new("c"); cam.type = 'ORTHO'; co = bpy.data.objects.new("c", cam); sc.collection.objects.link(co); sc.camera = co
sc.render.engine = "BLENDER_EEVEE"; sc.view_settings.view_transform = "AgX"
n = len(FILES); cx = (n - 1) * 0.3
for vung, (z, rong, goc) in {"mat": (1.69, 0.32 + 0.6*(n-1), {"truoc": (90, 0), "ba_phan_tu": (85, 35), "nghieng": (90, 90)}),
                             "mong": (0.95, 0.55 + 0.6*(n-1), {"sau": (90, 180), "sau_34": (85, 145), "nghieng": (90, 90)})}.items():
    cam.ortho_scale = rong; sc.render.resolution_x, sc.render.resolution_y = 700 * n, 700
    key = bpy.data.objects["key"]; key.rotation_euler = [math.radians(x) for x in ((40, 0, -30) if vung == "mat" else (45, 0, 215))]  # đèn chính theo phía nhìn
    for ten, (rx, rz) in goc.items():
        co.rotation_euler = (math.radians(rx), 0, math.radians(rz))
        co.location = V((cx, 0, z)) + co.rotation_euler.to_matrix() @ V((0, 0, 20)); cam.clip_end = 60
        sc.render.filepath = OUT.replace(".png", f"_{vung}_{ten}.png"); bpy.ops.render.render(write_still=True)
print("XONG")

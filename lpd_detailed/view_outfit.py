"""Render nhân vật mặc đồ: blender -b -P view_outfit.py -- <out_prefix> "NHAN=a.glb+b.glb+c.glb" ...
Thân giữ ngà (mắt tối), tóc/đồ giữ màu vật liệu glTF của chính asset. 4 góc: front, 34, side, back."""
import bpy, sys, math, mathutils
V = mathutils.Vector
argv = sys.argv[sys.argv.index("--") + 1:]; OUT = argv[0]; ITEMS = [a.split("=", 1) for a in argv[1:]]
bpy.ops.wm.read_factory_settings(use_empty=True); sc = bpy.context.scene
NGA = bpy.data.materials.new("ivory"); NGA.use_nodes = True
NGA.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.80, 0.70, 0.58, 1)
for i, (nhan, fs) in enumerate(ITEMS):
    g = bpy.data.objects.new("G_" + nhan, None); sc.collection.objects.link(g); tat = []
    for f in fs.split("+"):
        t = set(bpy.data.objects); bpy.ops.import_scene.gltf(filepath=f); moi = [o for o in bpy.data.objects if o not in t]; tat += moi
        la_than = "BODY" in f.split("/")[-1]
        for o in moi:
            if o.parent is None: o.parent = g
            if o.type == 'MESH':
                for p in o.data.polygons: p.use_smooth = False
                for sl in o.material_slots:
                    if sl.material:
                        b = next((n for n in sl.material.node_tree.nodes if n.type == 'BSDF_PRINCIPLED'), None)
                        if b: b.inputs["Roughness"].default_value = 0.9
                        if la_than and not any(k in sl.material.name.lower() for k in ("eye", "dark", "socket")): sl.material = NGA   # giữ vật liệu mặt (mắt, hốc bóng)
                sl0 = o.data.materials
                if not o.material_slots: sl0.append(NGA)
    for o in tat:   # vỏ đồ một lớp: nhìn được cả mặt trong
        if o.type == 'MESH':
            for sl in o.material_slots:
                if sl.material: sl.material.use_backface_culling = False
    g.location.x = i * 0.9
for ten, (e, nang, rot) in {"key": (3.0, (1, .93, .85), (50, 0, -35)), "fill": (1.2, (.8, .88, 1), (60, 0, 50)), "rim": (2.0, (1, 1, 1), (60, 0, 160))}.items():
    l = bpy.data.objects.new(ten, bpy.data.lights.new(ten, 'SUN')); sc.collection.objects.link(l); l.data.energy = e; l.data.color = nang; l.rotation_euler = [math.radians(x) for x in rot]
w = bpy.data.worlds.new("W"); sc.world = w; w.use_nodes = True; w.node_tree.nodes["Background"].inputs[0].default_value = (0.45, 0.46, 0.48, 1)
cam = bpy.data.cameras.new("c"); cam.type = 'ORTHO'; co = bpy.data.objects.new("c", cam); sc.collection.objects.link(co); sc.camera = co
n = len(ITEMS); cam.ortho_scale = max(2.0, 0.9 * n + 0.3) if n > 2 else 2.0; sc.render.engine = "BLENDER_EEVEE"; sc.render.resolution_x, sc.render.resolution_y = (900 if n <= 2 else 450 * n), 1000
sc.view_settings.view_transform = "Standard"; tam_x = (n - 1) * 0.45
for ten, (rx, rz) in {"front": (90, 0), "34": (82, 35), "side": (90, 90), "back": (90, 180)}.items():
    for o in bpy.data.objects:
        if o.name.startswith("G_"): o.rotation_euler.z = math.radians(-rz)
    co.rotation_euler = (math.radians(rx), 0, 0)
    co.location = V((tam_x, 0, 0.9)) + co.rotation_euler.to_matrix() @ V((0, 0, 30)); cam.clip_end = 100   # nhìn đúng tâm dù nghiêng
    sc.render.filepath = f"{OUT}_{ten}.png"; bpy.ops.render.render(write_still=True)
print("XONG")

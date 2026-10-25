"""Blender: smooth-shaded 3/4 front + 3/4 back renders of a built body (the colour panels of the reference sheet).
Run: blender -b -P render_shaded_blender.py -- <body.glb> <out.png>  ⇒ <out>_q_front.png, <out>_q_back.png"""
import bpy, sys, math, os
from mathutils import Vector
glb, out = sys.argv[sys.argv.index("--") + 1:][:2]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=glb)
objs = [o for o in bpy.context.scene.objects if o.type == "MESH"]
mat = bpy.data.materials.new("skin"); mat.use_nodes = True
b = next(n for n in mat.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
b.inputs["Base Color"].default_value = (0.80, 0.42, 0.32, 1); b.inputs["Roughness"].default_value = 0.75
USE_VC = os.environ.get("VERTEX_COLORS") == "1"      # VERTEX_COLORS=1 ⇒ show the painted colours instead of the plain skin
if USE_VC:
    mat.node_tree.nodes.new("ShaderNodeVertexColor")
    vc = next(n for n in mat.node_tree.nodes if n.type == "VERTEX_COLOR")
    mat.node_tree.links.new(vc.outputs["Color"], b.inputs["Base Color"])
KEEP = os.environ.get("KEEP_MATERIALS") == "1"     # KEEP_MATERIALS=1 ⇒ show the GLB's own materials (painted colours)
for o in objs:
    if KEEP: continue
    o.data.materials.clear(); o.data.materials.append(mat)
    for p in o.data.polygons: p.use_smooth = True
zmax = max((o.matrix_world @ Vector(v)).z for o in objs for v in o.bound_box)
sc = bpy.context.scene
for eng in ("BLENDER_EEVEE_NEXT", "BLENDER_EEVEE", "BLENDER_WORKBENCH"):
    try: sc.render.engine = eng; break
    except TypeError: pass
sc.view_settings.view_transform = "Standard"   # AgX (default) washes the flat palette out
sc.render.resolution_x, sc.render.resolution_y = 420, 900; sc.render.film_transparent = True
sun = bpy.data.objects.new("sun", bpy.data.lights.new("sun", "SUN")); sc.collection.objects.link(sun)
sun.data.energy = 3.0; sun.rotation_euler = (math.radians(55), 0, math.radians(-35))
w = bpy.data.worlds.new("w"); sc.world = w; w.use_nodes = True
bg = next(n for n in w.node_tree.nodes if n.type == "BACKGROUND"); bg.inputs[0].default_value = (1, 0.85, 0.85, 1); bg.inputs[1].default_value = 0.55
cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam")); sc.collection.objects.link(cam); sc.camera = cam
cam.data.type = "ORTHO"; cam.data.ortho_scale = zmax * 1.1
files = []
for name, yaw in (("q_front", 35), ("q_back", 215)):
    a = math.radians(yaw); d = 8
    # the GLB faces glTF +Z = Blender −Y, so the front camera sits on −Y
    cam.location = (d * math.sin(a), -d * math.cos(a), zmax * 0.52)
    cam.rotation_euler = (math.radians(90), 0, a)
    f = out.replace(".png", f"_{name}.png"); sc.render.filepath = f; bpy.ops.render.render(write_still=True); files.append(f)
print("saved", *files)   # compose with: python3 compose_panels.py <out.png> <files…> (Blender's Python has no PIL)

"""Render FRONT + SIDE with LPM's view_lpm.py camera/material/lights (ortho, ortho_scale 2.1, centre z 0.92, clay, 3 suns).
blender -b -P view_hm.py -- <out_prefix> body.glb [hair.glb]   ⇒ <out_prefix>_front.png, <out_prefix>_side.png"""
import bpy, sys, math, mathutils
V = mathutils.Vector
argv = sys.argv[sys.argv.index("--")+1:]
ZOOM = None
if argv[0] == "--zoom": ZOOM = (float(argv[1]), float(argv[2]), float(argv[3])); argv = argv[4:]   # centre x, centre z, ortho scale (close-ups only)
OUT, FILES = argv[0], argv[1:]
bpy.ops.wm.read_factory_settings(use_empty=True); sc = bpy.context.scene
dat = bpy.data.materials.new("dat_set"); dat.use_nodes = True
b = dat.node_tree.nodes["Principled BSDF"]; b.inputs["Base Color"].default_value = (0.80, 0.70, 0.60, 1); b.inputs["Roughness"].default_value = 0.9
toi = bpy.data.materials.new("Eye_Dark"); toi.use_nodes = True
toi.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.05, 0.05, 0.06, 1)
toc = bpy.data.materials.new("Hair_Charcoal"); toc.use_nodes = True
toc.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.08, 0.08, 0.09, 1); toc.node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value = 0.8
for f in FILES:                                   # all files share ONE origin (hair is fitted in place)
    t = set(bpy.data.objects); bpy.ops.import_scene.gltf(filepath=f)
    for o in bpy.data.objects:
        if o not in t and o.type == 'MESH':
            o.data.materials.clear(); o.data.materials.append(toi if o.name.startswith("mat_") else (toc if o.name.startswith("HAIR") else dat))
            for p in o.data.polygons: p.use_smooth = False
bpy.ops.mesh.primitive_plane_add(size=30); n = bpy.data.materials.new("nen"); n.use_nodes = True
n.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.35, 0.36, 0.38, 1); bpy.context.object.data.materials.append(n)
for ten, (e, nang, rot) in {"key": (3.2, (1, .93, .85), (50, 0, -35)), "fill": (1.1, (.8, .88, 1), (60, 0, 50)), "rim": (2.0, (1, 1, 1), (60, 0, 160))}.items():
    l = bpy.data.objects.new(ten, bpy.data.lights.new(ten, 'SUN')); sc.collection.objects.link(l)
    l.data.energy = e; l.data.color = nang; l.rotation_euler = [math.radians(x) for x in rot]
w = bpy.data.worlds.new("W"); sc.world = w; w.use_nodes = True; w.node_tree.nodes["Background"].inputs[0].default_value = (0.2, 0.21, 0.24, 1)
cam = bpy.data.cameras.new("c"); cam.type = 'ORTHO'; co = bpy.data.objects.new("c", cam); sc.collection.objects.link(co); sc.camera = co
tam = V((0, 0, 0.92)); cam.ortho_scale = 2.1
if ZOOM: tam = V((ZOOM[0], 0, ZOOM[1])); cam.ortho_scale = ZOOM[2]
sc.render.engine = "BLENDER_EEVEE"; sc.render.resolution_x, sc.render.resolution_y = 700, 900
sc.view_settings.view_transform = "AgX"
for ten, (rx, rz) in {"front": (90, 0), "side": (90, 90)}.items():
    co.rotation_euler = (math.radians(rx), 0, math.radians(rz))
    co.location = tam + co.rotation_euler.to_matrix() @ V((0, 0, 30)); cam.clip_end = 100
    sc.render.filepath = f"{OUT}_{ten}.png"; bpy.ops.render.render(write_still=True)
print("XONG")

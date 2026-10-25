"""Blender: the preview Boss reviews — coloured, lit with visible highlights, WHITE background, NO wireframe (Boss 25/10/2026:
«Tôi chỉ cần hình có màu, có ánh sáng phản chiếu với white background, ko cần hình mesh»).

  blender -b -P render_turnaround_blender.py -- <model.glb> <out_prefix> [--keep-materials]
  ⇒ <out_prefix>_<view>.png for front, q_front, side, q_back, back (transparent); compose with compose_white.py

Lights: key area (front-left, warm), fill area (front-right, soft), rim area (behind, cool) + soft white world.
Skin material (unless --keep-materials): theme skin colour, roughness 0.5 so the planes catch a highlight.
"""
import bpy, sys, os, math
from mathutils import Vector
a = sys.argv[sys.argv.index("--") + 1:]
glb, prefix = a[0], a[1]; keep = "--keep-materials" in a
sys.path.insert(0, os.path.expanduser("~/projects/lpm-faceless-humanoid/theme")); import theme_colors as TC
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=glb)
objs = [o for o in bpy.context.scene.objects if o.type == "MESH"]
if not keep:
    mat = bpy.data.materials.new("skin"); mat.use_nodes = True
    b = next(n for n in mat.node_tree.nodes if n.type == "BSDF_PRINCIPLED"); b.inputs["Base Color"].default_value = TC.mau(TC.DA["dat_am"])
    b.inputs["Roughness"].default_value = 0.5
    for o in objs: o.data.materials.clear(); o.data.materials.append(mat)
else:
    for o in objs:
        for m in o.data.materials:
            if m and m.use_nodes:
                b = next((n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED"), None)
# --keep-materials keeps the AUTHORED look: no roughness clamp, no forced smooth shading — the glTF importer already gives flat faces to
# flat-designed parts (split normals) and smooth ones to smooth parts (Codex audit 25/10: the global use_smooth made faceted hair/leather
# read as plastic). The plain body preview (no --keep) stays smooth.
if not keep:
    for o in objs:
        for p in o.data.polygons: p.use_smooth = True
lo = min((o.matrix_world @ Vector(v)).z for o in objs for v in o.bound_box); hi = max((o.matrix_world @ Vector(v)).z for o in objs for v in o.bound_box)
H = hi - lo; sc = bpy.context.scene
for eng in ("BLENDER_EEVEE_NEXT", "BLENDER_EEVEE"):
    try: sc.render.engine = eng; break
    except TypeError: pass
sc.view_settings.view_transform = "Standard"; sc.render.film_transparent = True
sc.render.resolution_x, sc.render.resolution_y = 600, 1100
w = bpy.data.worlds.new("w"); sc.world = w; w.use_nodes = True
bg = next(n for n in w.node_tree.nodes if n.type == "BACKGROUND"); bg.inputs[0].default_value = (1, 1, 1, 1); bg.inputs[1].default_value = 0.25


def area(name, energy, loc, color, size):
    L = bpy.data.lights.new(name, "AREA"); L.energy = energy; L.color = color; L.size = size
    ob = bpy.data.objects.new(name, L); sc.collection.objects.link(ob); ob.location = loc
    d = Vector((0, 0, lo + H * 0.55)) - Vector(loc); ob.rotation_euler = d.to_track_quat("-Z", "Y").to_euler(); return ob


# the GLB faces glTF +Z = Blender −Y: "front" lights sit on −Y
area("key", 160, (-2.2, -3.0, lo + H * 1.2), (1.0, 0.95, 0.88), 2.5)
area("fill", 55, (2.6, -2.4, lo + H * 0.7), (0.92, 0.95, 1.0), 3.0)
area("rim", 110, (0.5, 3.0, lo + H * 1.1), (0.85, 0.9, 1.0), 2.0)
cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam")); sc.collection.objects.link(cam); sc.camera = cam
cam.data.type = "ORTHO"; cam.data.ortho_scale = H * 1.12
for name, yaw in (("front", 0), ("q_front", 35), ("side", 90), ("q_back", 145), ("back", 180)):
    r = math.radians(yaw); d = 8
    cam.location = (d * math.sin(r), -d * math.cos(r), lo + H * 0.5); cam.rotation_euler = (math.radians(90), 0, r)
    sc.render.filepath = f"{prefix}_{name}.png"; bpy.ops.render.render(write_still=True)
print("rendered", prefix)

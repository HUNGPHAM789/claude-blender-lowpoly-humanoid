#!/usr/bin/env python3
"""
Render LPM Clump Origami Hair (v2.7) on LPM Base Head
"""
import bpy
import math
from mathutils import Vector

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene

# 1. Import Male Head
bpy.ops.import_scene.gltf(filepath="/tmp/ab_settler_test/lpm_base.glb")
for o in bpy.context.selected_objects:
    if o.name != "dau":
        bpy.data.objects.remove(o, do_unlink=True)
dau_m = bpy.data.objects.get("dau")
dau_m.location.x = -0.32

# Import Male Hair
bpy.ops.import_scene.gltf(filepath="/tmp/hair_origami_male.glb")
hair_m = bpy.context.selected_objects[0]
hair_m.location.x = -0.32

# 2. Import Female Head
bpy.ops.import_scene.gltf(filepath="/tmp/ab_settler_test/lpm_base.glb")
dau_f = None
for o in bpy.context.selected_objects:
    if o.name.startswith("dau"):
        dau_f = o
    else:
        bpy.data.objects.remove(o, do_unlink=True)
dau_f.location.x = 0.32

# Import Female Hair
bpy.ops.import_scene.gltf(filepath="/tmp/hair_origami_female.glb")
hair_f = bpy.context.selected_objects[0]
hair_f.location.x = 0.32

# Materials
mat_head = bpy.data.materials.new("M_Head")
mat_head.use_nodes = True
mat_head.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.80, 0.70, 0.60, 1)
mat_head.node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value = 0.9
dau_m.data.materials.clear()
dau_m.data.materials.append(mat_head)
dau_f.data.materials.clear()
dau_f.data.materials.append(mat_head)

# Ensure Flat shading
for o in bpy.data.objects:
    if o.type == 'MESH':
        for p in o.data.polygons:
            p.use_smooth = False

# Camera Close-up on heads
cam_data = bpy.data.cameras.new("HeadCam")
cam_data.type = 'ORTHO'
cam_data.ortho_scale = 1.15
cam_obj = bpy.data.objects.new("HeadCam", cam_data)
sc.collection.objects.link(cam_obj)
sc.camera = cam_obj

cam_obj.rotation_euler = (math.radians(80), 0, math.radians(25))
cam_dir = cam_obj.rotation_euler.to_matrix() @ Vector((0, 0, 5.0))
cam_obj.location = Vector((0, 0, 1.70)) + cam_dir

# Lights
lights = {
    "Key": (3.8, (1.0, 0.95, 0.88), (55, 0, 30)),
    "Fill": (1.2, (0.75, 0.85, 1.0), (60, 0, -60)),
    "Rim": (2.4, (1.0, 1.0, 1.0), (45, 0, 160))
}
for name, (energy, col, rot) in lights.items():
    l_data = bpy.data.lights.new(name, 'SUN')
    l_data.energy = energy
    l_data.color = col
    l_obj = bpy.data.objects.new(name, l_data)
    sc.collection.objects.link(l_obj)
    l_obj.rotation_euler = [math.radians(x) for x in rot]

world = bpy.data.worlds.new("W")
sc.world = world
world.use_nodes = True
world.node_tree.nodes["Background"].inputs[0].default_value = (0.12, 0.13, 0.16, 1)

sc.render.engine = "BLENDER_EEVEE"
sc.render.resolution_x = 1280
sc.render.resolution_y = 720
sc.view_settings.view_transform = "AgX"
out_img = "~/projects/lpm-faceless-humanoid/samples/v2.7_origami_hair.png"
sc.render.filepath = out_img

bpy.ops.render.render(write_still=True)
print("📸 Render complete ->", out_img)

#!/usr/bin/env python3
"""
Direct Blender Render of Male & Female Origami Clump Hair on LPM Head
High contrast materials so hair clumps and origami facets pop with extreme clarity.
"""
import bpy
import math
import os
from mathutils import Vector

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene

def create_hair_mesh(name, gioi="nam", color=(0.14, 0.08, 0.05, 1)):
    # 12-clump folded origami geometry
    N = 12
    verts = []
    faces = []
    
    # Crown apex
    verts.append([0.0, 0.005, 1.848])
    
    rx_skull = 0.088
    ry_skull = 0.098
    
    for i in range(N):
        ang = i * (2 * math.pi / N)
        cos_a = math.cos(ang)
        sin_a = math.sin(ang)
        r_base = math.hypot(rx_skull * cos_a, ry_skull * sin_a)
        
        # 1. Crown ridge (elevated outward for bold origami fold)
        r_mid = r_base + 0.026
        z_mid = 1.788
        verts.append([r_mid * cos_a, 0.005 + r_mid * sin_a, z_mid])
        
        # 2. Clump Tip
        is_front = (sin_a < -0.35)
        is_back = (sin_a > 0.35)
        
        if is_front:
            # Bangs / Mái trước
            z_tip = 1.728 if i % 2 == 0 else 1.708
            r_tip = r_base + 0.024
        elif is_back:
            if gioi == "nu":
                # Nữ tóc bob dài ngang vai
                z_tip = 1.540 if i % 2 == 0 else 1.580
                r_tip = r_base + 0.048
            else:
                # Nam tóc gáy cao
                z_tip = 1.620 if i % 2 == 0 else 1.648
                r_tip = r_base + 0.028
        else:
            # Hai bên tai
            if gioi == "nu":
                z_tip = 1.555 if i % 2 == 0 else 1.595
                r_tip = r_base + 0.042
            else:
                z_tip = 1.650 if i % 2 == 0 else 1.680
                r_tip = r_base + 0.026
                
        verts.append([r_tip * cos_a, 0.005 + r_tip * sin_a, z_tip])
        
    for i in range(N):
        nxt = (i + 1) % N
        v_mid = 1 + i * 2
        v_tip = 1 + i * 2 + 1
        v_mid_nxt = 1 + nxt * 2
        v_tip_nxt = 1 + nxt * 2 + 1
        
        # Crown triangle
        faces.append([0, v_mid, v_mid_nxt])
        # Clump facet 1
        faces.append([v_mid, v_tip, v_mid_nxt])
        # Clump facet 2 (valley)
        faces.append([v_tip, v_tip_nxt, v_mid_nxt])
        
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    
    mat = bpy.data.materials.new(f"M_{name}")
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = color
        bsdf.inputs["Roughness"].default_value = 0.85
    obj.data.materials.append(mat)
    
    for p in mesh.polygons:
        p.use_smooth = False
        
    return obj

# 1. Import Base Mesh for Male
bpy.ops.import_scene.gltf(filepath="/tmp/ab_settler_test/lpm_base.glb")
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.parent_clear(type='CLEAR_KEEP_TRANSFORM')

dau_m = bpy.data.objects.get("dau")
dau_m.name = "Head_Male"

for o in list(bpy.data.objects):
    if o.type == 'MESH' and o != dau_m:
        bpy.data.objects.remove(o, do_unlink=True)
    elif o.type == 'EMPTY':
        bpy.data.objects.remove(o, do_unlink=True)

dau_m.location.x = -0.32

# Create Male Hair (Dark Espresso)
hair_m = create_hair_mesh("Hair_Male", gioi="nam", color=(0.12, 0.08, 0.05, 1))
hair_m.location.x = -0.32

# 2. Import Base Mesh for Female
bpy.ops.import_scene.gltf(filepath="/tmp/ab_settler_test/lpm_base.glb")
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.parent_clear(type='CLEAR_KEEP_TRANSFORM')

dau_f = None
for o in list(bpy.data.objects):
    if o.name.startswith("dau") and o != dau_m:
        dau_f = o
        break

dau_f.name = "Head_Female"
for o in list(bpy.data.objects):
    if o not in [dau_m, hair_m, dau_f]:
        bpy.data.objects.remove(o, do_unlink=True)

dau_f.location.x = 0.32

# Create Female Hair (Auburn Chestnut)
hair_f = create_hair_mesh("Hair_Female", gioi="nu", color=(0.45, 0.18, 0.08, 1))
hair_f.location.x = 0.32

# High-contrast light porcelain clay skin
mat_skin = bpy.data.materials.new("M_Skin")
mat_skin.use_nodes = True
mat_skin.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.92, 0.82, 0.72, 1)
dau_m.data.materials.clear()
dau_m.data.materials.append(mat_skin)
dau_f.data.materials.clear()
dau_f.data.materials.append(mat_skin)

# Camera (Orthographic 3/4 view)
cam_data = bpy.data.cameras.new("Cam")
cam_data.type = 'ORTHO'
cam_data.ortho_scale = 1.05
cam_obj = bpy.data.objects.new("Cam", cam_data)
sc.collection.objects.link(cam_obj)
sc.camera = cam_obj

# Angle: 76 deg elevation, 25 deg azimuth
cam_obj.rotation_euler = (math.radians(76), 0, math.radians(25))
cam_dir = cam_obj.rotation_euler.to_matrix() @ Vector((0, 0, 5.0))
cam_obj.location = Vector((0, 0, 1.70)) + cam_dir

# Lights
lights = {
    "Key": (4.2, (1.0, 0.95, 0.88), (55, 0, 25)),
    "Fill": (1.4, (0.75, 0.85, 1.0), (60, 0, -60)),
    "Rim": (3.2, (1.0, 1.0, 1.0), (45, 0, 160))
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
world.node_tree.nodes["Background"].inputs[0].default_value = (0.16, 0.17, 0.20, 1)

sc.render.engine = "BLENDER_EEVEE"
sc.render.resolution_x = 1280
sc.render.resolution_y = 720
sc.view_settings.view_transform = "AgX"

out_img = "~/projects/lpm-faceless-humanoid/samples/v2.7_origami_hair.png"
sc.render.filepath = out_img
bpy.ops.render.render(write_still=True)
print("📸 Direct Hair Render Complete ->", out_img)

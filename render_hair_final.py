#!/usr/bin/env python3
"""
LPM v2.7 Faceted Origami Hair Showcase Renderer
Direct geometry generation in Blender (Zero glTF import loss).
"""
import bpy
import bmesh
import math
from mathutils import Vector

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene

# ==============================================================================
# 1. LPM Head Direct Generation (Exact Dau Vertices from lpm.py)
# ==============================================================================
def create_lpm_head(name, gioi="nam", s=1.0, color=(0.90, 0.82, 0.74, 1)):
    h = 0.92 if gioi == "nu" else 1.0
    P = [
        (0, 0.015, 1.800), (0.072, 0.005, 1.775), (-0.072, 0.005, 1.775), (0, 0.098, 1.745), (0.078, 0.07, 1.70),
        (-0.078, 0.07, 1.70), (0, -0.092, 1.725), (0.062, -0.082, 1.722), (-0.062, -0.082, 1.722),
        (0, -0.116, 1.658), (0.016, -0.100, 1.645), (-0.016, -0.100, 1.645),
        (0.070, -0.066, 1.665), (-0.070, -0.066, 1.665), (0.082, 0.0, 1.668), (-0.082, 0.0, 1.668),
        (0.088, 0.012, 1.650), (-0.088, 0.012, 1.650),
        (0.058, 0.075, 1.618), (-0.058, 0.075, 1.618),
        (0.060 * h, -0.032, 1.585), (-0.060 * h, -0.032, 1.585),
        (0, -0.083, 1.568), (0.024 * h, -0.074, 1.562), (-0.024 * h, -0.074, 1.562),
        (0, -0.086, 1.768), (0.050, -0.074, 1.764), (-0.050, -0.074, 1.764),
        (0, -0.060, 1.792), (0.040, -0.050, 1.788), (-0.040, -0.050, 1.788)
    ]
    bm = bmesh.new()
    for x, y, z in P:
        bm.verts.new((x * s, y * s, z * s))
    bm.verts.ensure_lookup_table()
    bmesh.ops.convex_hull(bm, input=bm.verts)
    
    mesh = bpy.data.meshes.new(name)
    bm.to_mesh(mesh)
    bm.free()
    
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    
    mat = bpy.data.materials.new(f"M_{name}")
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = color
        bsdf.inputs["Roughness"].default_value = 0.65
    obj.data.materials.append(mat)
    
    for p in mesh.polygons:
        p.use_smooth = False
        
    return obj

# ==============================================================================
# 2. LPM Neck Pedestal (For elegant presentation)
# ==============================================================================
def create_neck_pedestal(name, x_pos, color=(0.85, 0.77, 0.69, 1)):
    # Simple faceted cylinder neck
    bpy.ops.mesh.primitive_cylinder_add(vertices=8, radius=0.045, depth=0.12, location=(x_pos, 0.012, 1.53))
    neck = bpy.context.active_object
    neck.name = name
    for p in neck.data.polygons: p.use_smooth = False
    
    mat = bpy.data.materials.new(f"M_{name}")
    mat.use_nodes = True
    mat.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = color
    mat.node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value = 0.75
    neck.data.materials.append(mat)
    return neck

# ==============================================================================
# 3. LPM Clump Origami Hair Generator (Direct Verts & Faces)
# ==============================================================================
def create_origami_hair(name, gioi="nam", s=1.0, color=(0.14, 0.09, 0.06, 1)):
    cx, cy, cz = 0.0, 0.012 * s, 1.70 * s
    crown_z = 1.855 * s
    
    N = 12
    verts = []
    faces = []
    
    # Apex 0
    verts.append([cx, cy, crown_z])
    
    rx_skull = 0.082 * s
    ry_skull = 0.098 * s
    
    for i in range(N):
        ang = i * (2 * math.pi / N)
        cos_a = math.cos(ang)
        sin_a = math.sin(ang)
        r_base = math.hypot(rx_skull * cos_a, ry_skull * sin_a)
        
        # 1. Crown drop ring
        r_mid = r_base + 0.028 * s
        z_mid = 1.805 * s
        verts.append([cx + r_mid * cos_a, cy + r_mid * sin_a, z_mid])
        
        # 2. Clump Tip
        is_front = (sin_a < -0.35)
        is_back = (sin_a > 0.35)
        
        if is_front:
            # Bangs (staggered)
            z_tip = (1.730 if i % 2 == 0 else 1.710) * s
            r_tip = r_base + 0.024 * s
        elif is_back:
            if gioi == "nu":
                # Shoulder bob
                z_tip = (1.535 if i % 2 == 0 else 1.575) * s
                r_tip = r_base + 0.044 * s
            else:
                # High masculine nape
                z_tip = (1.620 if i % 2 == 0 else 1.645) * s
                r_tip = r_base + 0.030 * s
        else:
            # Temples / ears
            if gioi == "nu":
                z_tip = (1.550 if i % 2 == 0 else 1.590) * s
                r_tip = r_base + 0.040 * s
            else:
                z_tip = (1.655 if i % 2 == 0 else 1.680) * s
                r_tip = r_base + 0.028 * s
                
        verts.append([cx + r_tip * cos_a, cy + r_tip * sin_a, z_tip])
        
    for i in range(N):
        nxt = (i + 1) % N
        v_mid = 1 + i * 2
        v_tip = 1 + i * 2 + 1
        v_mid_nxt = 1 + nxt * 2
        v_tip_nxt = 1 + nxt * 2 + 1
        
        # 1. Crown triangle
        faces.append([0, v_mid, v_mid_nxt])
        # 2. Folded wedge facet 1
        faces.append([v_mid, v_tip, v_mid_nxt])
        # 3. Folded wedge facet 2 (serrated valley)
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

# ==============================================================================
# 4. Scene Assembly
# ==============================================================================
# Male: Left (X = -0.34)
head_m = create_lpm_head("Head_Male", gioi="nam", color=(0.94, 0.88, 0.80, 1))
head_m.location.x = -0.34
neck_m = create_neck_pedestal("Neck_Male", -0.34, color=(0.88, 0.82, 0.74, 1))
hair_m = create_origami_hair("Hair_Male", gioi="nam", color=(0.06, 0.04, 0.03, 1)) # Deep Espresso Charcoal
hair_m.location.x = -0.34

# Female: Right (X = 0.34)
head_f = create_lpm_head("Head_Female", gioi="nu", color=(0.94, 0.88, 0.80, 1))
head_f.location.x = 0.34
neck_f = create_neck_pedestal("Neck_Female", 0.34, color=(0.88, 0.82, 0.74, 1))
hair_f = create_origami_hair("Hair_Female", gioi="nu", color=(0.32, 0.08, 0.03, 1)) # Rich Deep Crimson/Auburn
hair_f.location.x = 0.34

# ==============================================================================
# 5. Framing & Camera
# ==============================================================================
cam_data = bpy.data.cameras.new("StudioCam")
cam_data.type = 'ORTHO'
cam_data.ortho_scale = 0.95
cam_obj = bpy.data.objects.new("StudioCam", cam_data)
sc.collection.objects.link(cam_obj)
sc.camera = cam_obj

# Camera at front 3/4 angle: 18 deg pitch looking slightly down, 18 deg yaw
pitch = math.radians(18)
yaw = math.radians(18)
# Look-at center: (0, 0, 1.68)
target = Vector((0.0, 0.0, 1.68))
dist = 3.5
cx = dist * math.sin(yaw) * math.cos(pitch)
cy = -dist * math.cos(yaw) * math.cos(pitch)
cz = 1.68 + dist * math.sin(pitch)
cam_obj.location = Vector((cx, cy, cz))

direction = target - cam_obj.location
rot_quat = direction.to_track_quat('-Z', 'Y')
cam_obj.rotation_euler = rot_quat.to_euler()

# ==============================================================================
# 6. High-Contrast Studio Lighting
# ==============================================================================
# Key light (Front-Right warm sun)
l_key = bpy.data.lights.new("Key", 'SUN')
l_key.energy = 4.5
l_key.color = (1.0, 0.96, 0.90)
l_key_obj = bpy.data.objects.new("Key", l_key)
sc.collection.objects.link(l_key_obj)
l_key_obj.rotation_euler = (math.radians(45), math.radians(15), math.radians(35))

# Fill light (Front-Left cool soft fill)
l_fill = bpy.data.lights.new("Fill", 'SUN')
l_fill.energy = 1.6
l_fill.color = (0.75, 0.85, 1.0)
l_fill_obj = bpy.data.objects.new("Fill", l_fill)
sc.collection.objects.link(l_fill_obj)
l_fill_obj.rotation_euler = (math.radians(50), 0, math.radians(-50))

# Rim light (Back-Top specular rim)
l_rim = bpy.data.lights.new("Rim", 'SUN')
l_rim.energy = 3.8
l_rim.color = (1.0, 1.0, 1.0)
l_rim_obj = bpy.data.objects.new("Rim", l_rim)
sc.collection.objects.link(l_rim_obj)
l_rim_obj.rotation_euler = (math.radians(-35), math.radians(20), math.radians(140))

# Dark elegant studio backdrop
world = bpy.data.worlds.new("StudioWorld")
sc.world = world
world.use_nodes = True
world.node_tree.nodes["Background"].inputs[0].default_value = (0.12, 0.13, 0.16, 1)

sc.render.engine = "BLENDER_EEVEE"
sc.render.resolution_x = 1280
sc.render.resolution_y = 720
sc.view_settings.view_transform = "AgX"

out_raw = "~/projects/lpm-faceless-humanoid/samples/v2.7_origami_hair_clean.png"
sc.render.filepath = out_raw
bpy.ops.render.render(write_still=True)
print(f"📸 Studio Render Complete -> {out_raw}")

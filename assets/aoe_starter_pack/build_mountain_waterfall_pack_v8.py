#!/usr/bin/env python3
"""
build_mountain_waterfall_pack_v8.py - MASTER v8.0 (UNIFIED MOUNTAIN COLOR & ZERO WATERFALL GAP)

Fixes applied per Boss's feedback:
1. UNIFIED MOUNTAIN COLOR:
   - Eliminated `mat_da_toi` (dark charcoal) completely.
   - All mountain cliff walls across West, Center, and East use the exact same unified rock material: `mat_da = (112, 106, 98)`.
   - All summit plateau caps use the exact same sunny grass: `mat_turf_top = (115, 155, 68)`.
   - The entire mountain range is now 100% cohesive with zero mismatched dark patches.

2. ZERO GAP BEHIND WATERFALL:
   - Built a solid stepped bedrock gorge that matches the EXACT stepped profile of the waterfall chute:
     - Top lip: Y = 21.4, Z = 8.20
     - Step 1 vertical face: Y = 20.5, Z = 8.20 -> 5.50
     - Shelf 1 horizontal terrace: Y = 20.5 -> 18.8, Z = 5.50
     - Step 2 vertical face: Y = 18.8, Z = 5.50 -> 2.90
     - Shelf 2 horizontal terrace: Y = 18.8 -> 16.8, Z = 2.90
     - Step 3 vertical face: Y = 16.8, Z = 2.90 -> 0.35
     - Plunge into sunken pond at Z = 0.18
   - The blue waterfall sheet sits flush against the rock face (+0.015m offset to prevent coplanar z-fighting).
   - Zero empty air space behind the water. From any angle, the water is solidly backed by solid cliff rock.

3. FAN-SHAPED SUNKEN POND HUGGING MOUNTAINS:
   - Water surface at Z = 0.18m recessed inside the ground (ground at Z = 0.40m), zero ground shadow.
   - Covers all green terrain at the foot of the waterfall.
"""

import bpy
import bmesh
import math
import os
from mathutils import Vector

OUT_DIR = "~/projects/lpm-faceless-humanoid/assets/aoe_starter_pack"
os.makedirs(OUT_DIR, exist_ok=True)
GLB_OUT = os.path.join(OUT_DIR, "mountain_waterfall_pack.glb")
PNG_OUT = os.path.join(OUT_DIR, "showcase_mountain_waterfall.png")

# Reset Blender
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene

def srgb_to_linear(c):
    return (c / 255.0) ** 2.2

def tt(srgb_tuple):
    return tuple(srgb_to_linear(x) for x in srgb_tuple)

def get_mat(name, srgb_color, roughness=0.9, metallic=0.0, emission_srgb=None, emission_strength=0.0):
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = (*tt(srgb_color), 1.0)
        bsdf.inputs["Roughness"].default_value = roughness
        bsdf.inputs["Metallic"].default_value = metallic
        if emission_srgb and "Emission Color" in bsdf.inputs:
            bsdf.inputs["Emission Color"].default_value = (*tt(emission_srgb), 1.0)
            bsdf.inputs["Emission Strength"].default_value = emission_strength
    return mat

# UNIFIED PALETTE (Exact same rock & grass everywhere)
mat_da        = get_mat("M_Da",        (112, 106,  98), roughness=0.92)  # Unified vertical cliff rock
mat_da_sang   = get_mat("M_DaSang",    (135, 129, 119), roughness=0.90)  # Ledge stone & stepping stones
mat_turf      = get_mat("M_Turf",      ( 92, 132,  56), roughness=0.85)  # Meadow & mountain grass
mat_turf_top  = get_mat("M_TurfTop",   (115, 155,  68), roughness=0.85)  # Sunlit plateau cap
mat_water_blue= get_mat("M_WaterBlue", ( 42, 138, 178), roughness=0.10, emission_srgb=(48, 148, 192), emission_strength=0.55)

rock_large = "~/projects/lpm-faceless-humanoid/lpms_store/rock_large/r_38f71967/rock_large.glb"
rock_small = "~/projects/lpm-faceless-humanoid/lpms_store/rock_small/r_55a2bf91/rock_small.glb"

def import_lpm_asset(filepath, name, loc, rot_z_deg=0.0, scale=1.0):
    truoc = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=filepath)
    moi = [o for o in bpy.data.objects if o not in truoc]
    parent = bpy.data.objects.new(name, None)
    bpy.context.collection.objects.link(parent)
    parent.location = Vector(loc)
    parent.rotation_euler.z = math.radians(rot_z_deg)
    parent.scale = (scale, scale, scale)
    for o in moi:
        if o.parent is None: o.parent = parent
        if o.type == 'MESH':
            for p in o.data.polygons: p.use_smooth = False
    return parent

def build_vertical_mesa_block(name, footprint_pts, z_bottom, z_top, mat_wall=mat_da, mat_cap=mat_turf_top):
    bm = bmesh.new()
    n = len(footprint_pts)
    v_bot = [bm.verts.new((x, y, z_bottom)) for x, y in footprint_pts]
    v_top = [bm.verts.new((x, y, z_top)) for x, y in footprint_pts]
    
    for i in range(n):
        i_next = (i + 1) % n
        bm.faces.new([v_bot[i], v_bot[i_next], v_top[i_next], v_top[i]])
        
    bm.faces.new(v_top)
    
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    
    obj = bpy.data.objects.new(name, me)
    bpy.context.collection.objects.link(obj)
    for p in obj.data.polygons: p.use_smooth = False
    
    obj.data.materials.append(mat_wall)
    obj.data.materials.append(mat_cap)
    
    for p in obj.data.polygons:
        if p.normal.z > 0.8:
            p.material_index = 1
        else:
            p.material_index = 0
            
    return obj

# ==============================================================================
# 1. MOUNTAINS (WEST, CENTER RIDGE, EAST) - 100% UNIFIED COLOR & ZERO GAPS
# ==============================================================================
# Center Connecting Ridge: bridges West and East across X = -3.8 to +3.8, Y = 21.2 to 24.5, Z = 0.0 to 8.2m
center_ridge_pts = [
    (-3.8, 24.5), ( 3.8, 24.5), ( 3.8, 21.2), (-3.8, 21.2)
]
build_vertical_mesa_block("Center_Connecting_Ridge", center_ridge_pts, 0.0, 8.2, mat_da, mat_turf_top)

# West Lower Terrace (Z = 0.0 to 5.2m)
w_low_pts = [
    (-13.5, 24.5), (-2.2, 24.5), (-2.2, 17.2), (-6.5, 16.5), (-13.5, 17.5)
]
build_vertical_mesa_block("West_Mesa_Lower_Terrace", w_low_pts, 0.0, 5.2, mat_da, mat_turf)

# West Summit Tabletop Mesa (Z = 5.2m to 9.8m)
w_summit_pts = [
    (-12.5, 24.5), (-2.2, 24.5), (-2.2, 19.5), (-7.5, 18.5), (-12.5, 19.5)
]
build_vertical_mesa_block("West_Mesa_Summit_Plateau", w_summit_pts, 5.2, 9.8, mat_da, mat_turf_top)

# East Lower Terrace (Z = 0.0 to 4.6m)
e_low_pts = [
    ( 2.2, 24.5), (13.5, 24.5), (13.5, 17.5), ( 6.5, 16.5), ( 2.2, 17.2)
]
build_vertical_mesa_block("East_Mesa_Lower_Terrace", e_low_pts, 0.0, 4.6, mat_da, mat_turf)

# East Summit Tabletop Mesa (Z = 4.6m to 8.4m)
e_summit_pts = [
    ( 2.2, 24.5), (12.5, 24.5), (12.5, 19.5), ( 7.5, 18.5), ( 2.2, 19.5)
]
build_vertical_mesa_block("East_Mesa_Summit_Plateau", e_summit_pts, 4.6, 8.4, mat_da, mat_turf_top)

# ==============================================================================
# 2. STEPPED BEDROCK DIRECTLY BEHIND THE WATERFALL (FLUSH STEP PROFILE)
# ==============================================================================
# The waterfall chute drops in 3 distinct rectangular steps:
# Step 1: drops at Y = 20.5 from Z = 8.20 down to 5.50
# Shelf 1: horizontal terrace Y = 20.5 -> 18.8 at Z = 5.50
# Step 2: drops at Y = 18.8 from Z = 5.50 down to 2.90
# Shelf 2: horizontal terrace Y = 18.8 -> 16.8 at Z = 2.90
# Step 3: drops at Y = 16.8 from Z = 2.90 down to 0.35
# Plunge: Y = 16.8 -> 14.8 into the sunken fan pond
#
# We build a solid mountain rock block whose front face follows this EXACT step profile!
# Width: X from -2.4 to +2.4 (bridges West and East mountain walls with 0 gap).

bm_rock_steps = bmesh.new()

# Step profile points (Y, Z) from top to ground
cliff_step_profile = [
    (21.4, 8.20),  # Top lip
    (20.5, 8.20),  # Top crest to step edge
    (20.5, 5.50),  # Drop 1
    (18.8, 5.50),  # Shelf 1
    (18.8, 2.90),  # Drop 2
    (16.8, 2.90),  # Shelf 2
    (16.8, 0.35),  # Drop 3
    (14.8, 0.00),  # Base toe at ground
]

rw_half = 2.40  # Perfectly connects to West mesa (-2.2) and East mesa (+2.2)

# Build stepped rock block with back at Y = 24.5
front_verts = []
back_verts = []

for py, pz in cliff_step_profile:
    v_fl = bm_rock_steps.verts.new((-rw_half, py, pz))
    v_fr = bm_rock_steps.verts.new(( rw_half, py, pz))
    v_bl = bm_rock_steps.verts.new((-rw_half, 24.5, pz))
    v_br = bm_rock_steps.verts.new(( rw_half, 24.5, pz))
    front_verts.append((v_fl, v_fr))
    back_verts.append((v_bl, v_br))

# Build front stepped faces & side faces
for i in range(len(cliff_step_profile) - 1):
    fl0, fr0 = front_verts[i]
    fl1, fr1 = front_verts[i+1]
    bl0, br0 = back_verts[i]
    bl1, br1 = back_verts[i+1]
    
    # Front stepped quad
    bm_rock_steps.faces.new([fl0, fr0, fr1, fl1])
    # Left side quad
    bm_rock_steps.faces.new([bl0, fl0, fl1, bl1])
    # Right side quad
    bm_rock_steps.faces.new([fr0, br0, br1, fr1])
    # Back quad
    bm_rock_steps.faces.new([br0, bl0, bl1, br1])

# Top cap
bm_rock_steps.faces.new([back_verts[0][0], back_verts[0][1], front_verts[0][1], front_verts[0][0]])
# Bottom cap
bm_rock_steps.faces.new([front_verts[-1][0], front_verts[-1][1], back_verts[-1][1], back_verts[-1][0]])

me_rock_steps = bpy.data.meshes.new("Stepped_Rock_Bedrock_Flush")
bm_rock_steps.to_mesh(me_rock_steps)
bm_rock_steps.free()

obj_rock_steps = bpy.data.objects.new("Stepped_Rock_Bedrock_Flush", me_rock_steps)
bpy.context.collection.objects.link(obj_rock_steps)
for p in obj_rock_steps.data.polygons: p.use_smooth = False
# UNIFIED MATERIAL: Same mat_da and mat_turf_top
obj_rock_steps.data.materials.append(mat_da)
obj_rock_steps.data.materials.append(mat_turf_top)
for p in obj_rock_steps.data.polygons:
    if p.normal.z > 0.8:
        p.material_index = 1
    else:
        p.material_index = 0

# Accent rocks on mountain flanks
import_lpm_asset(rock_large, "LPM_Corner_W", (-12.5, 16.8, 0.4), rot_z_deg=25, scale=1.3)
import_lpm_asset(rock_large, "LPM_Corner_E", ( 12.5, 16.8, 0.4), rot_z_deg=-30, scale=1.2)

# ==============================================================================
# 3. TOP BLUE MASK & FLUSH STEPPED WATERFALL
# ==============================================================================
# Top Mountain Blue Mask (Z = 8.22m):
top_pool_bm = bmesh.new()
tp_c = top_pool_bm.verts.new((0.0, 22.8, 8.22))
tp_rim = []
tp_n = 12
tp_rx, tp_ry = 2.4, 1.5
for i in range(tp_n):
    ang = i * (2 * math.pi / tp_n)
    vx = 0.0 + tp_rx * math.cos(ang)
    vy = 22.8 + tp_ry * math.sin(ang)
    tp_rim.append(top_pool_bm.verts.new((vx, vy, 8.22)))
for i in range(tp_n):
    i_next = (i + 1) % tp_n
    top_pool_bm.faces.new([tp_rim[i], tp_rim[i_next], tp_c])
top_pool_me = bpy.data.meshes.new("Top_Mountain_Blue_Mask")
top_pool_bm.to_mesh(top_pool_me)
top_pool_bm.free()
top_pool_obj = bpy.data.objects.new("Top_Mountain_Blue_Mask", top_pool_me)
bpy.context.collection.objects.link(top_pool_obj)
for p in top_pool_obj.data.polygons: p.use_smooth = False
top_pool_obj.data.materials.append(mat_water_blue)

# Stepped Waterfall Chute: Sits flush on top of the rock face (+0.015m offset)
# ZERO gap from top to bottom!
wf_profile = [
    # (Y, Z)
    (21.4, 8.215),  # Top lip
    (20.485, 8.215),# Top crest to step edge
    (20.485, 5.515),# Drop 1
    (18.785, 5.515),# Shelf 1
    (18.785, 2.915),# Drop 2
    (16.785, 2.915),# Shelf 2
    (16.785, 0.365),# Drop 3
    (14.800, 0.200),# Plunging directly into the sunken fan pond
]

wf_verts = []
w_half = 1.70  # Width of the blue water stream (recessed inside the rw_half=2.4 rock buttress)
for py, pz in wf_profile:
    wf_verts.append((-w_half, py, pz))
    wf_verts.append(( w_half, py, pz))

wf_faces = []
for i in range(len(wf_profile) - 1):
    i0 = i * 2
    i1 = i0 + 1
    i2 = (i + 1) * 2
    i3 = i2 + 1
    wf_faces.append([i0, i1, i3, i2])

me_wf = bpy.data.meshes.new("Flush_Waterfall_Chute")
me_wf.from_pydata(wf_verts, [], wf_faces)
me_wf.update()
obj_wf = bpy.data.objects.new("Flush_Waterfall_Chute", me_wf)
bpy.context.collection.objects.link(obj_wf)
for p in obj_wf.data.polygons: p.use_smooth = False
obj_wf.data.materials.append(mat_water_blue)

# ==============================================================================
# 4. SUNKEN FAN POND & S-CURVE RIVER OUTLET (ZERO SHADOW)
# ==============================================================================
# Ground terrain slab at Z = 0.40m with carved cavity
ground_w, ground_l = 28.0, 29.0
bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0.0, 8.5, 0.20))
ground_obj = bpy.context.active_object
ground_obj.name = "Ground_Terrain"
ground_obj.scale = (ground_w, ground_l, 0.40)
bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
for p in ground_obj.data.polygons: p.use_smooth = False
ground_obj.data.materials.append(mat_turf)

# Pond center & radius: fan shape hugging the mountains at Y = 14.5
pond_cx, pond_cy = 0.0, 14.5
pond_r = 6.20

# Carve cavity into ground using cylinder cutter
bpy.ops.mesh.primitive_cylinder_add(vertices=24, radius=pond_r, depth=0.35, location=(pond_cx, pond_cy, 0.25))
pond_cutter = bpy.context.active_object
pond_cutter.name = "Pond_Cutter"

mod_bool = ground_obj.modifiers.new("PondCavity", 'BOOLEAN')
mod_bool.operation = 'DIFFERENCE'
mod_bool.object = pond_cutter
bpy.context.view_layer.objects.active = ground_obj
bpy.ops.object.modifier_apply(modifier="PondCavity")
bpy.data.objects.remove(pond_cutter, do_unlink=True)

# Sunken water disc at Z = 0.18m (resting inside the ground cavity)
bpy.ops.mesh.primitive_cylinder_add(vertices=24, radius=pond_r, depth=0.04, location=(pond_cx, pond_cy, 0.18))
pond_water = bpy.context.active_object
pond_water.name = "Sunken_Pond_Water"
for p in pond_water.data.polygons: p.use_smooth = False
pond_water.data.materials.append(mat_water_blue)

# S-Curve River flowing south to the edge of the island
river_pts = [
    # (X_center, Y_center, width, Z_depth)
    ( 0.0, 8.5, 2.8, 0.17),
    ( 0.8, 6.0, 2.6, 0.16),
    (-0.6, 3.5, 2.5, 0.15),
    ( 0.4, 1.0, 2.4, 0.14),
    (-0.2,-1.5, 2.4, 0.13),
    ( 0.0,-4.0, 2.4, 0.12),
    ( 0.0,-6.0, 2.4, 0.11),
]

# River trench cutter
bm_cut = bmesh.new()
t_verts = []
for xc, yc, rw, rz in river_pts:
    hw = rw * 0.5
    v0 = bm_cut.verts.new((xc - hw, yc, 0.45))
    v1 = bm_cut.verts.new((xc + hw, yc, 0.45))
    v2 = bm_cut.verts.new((xc + hw, yc, 0.05))
    v3 = bm_cut.verts.new((xc - hw, yc, 0.05))
    t_verts.append((v0, v1, v2, v3))
for i in range(len(t_verts) - 1):
    c0 = t_verts[i]
    c1 = t_verts[i+1]
    bm_cut.faces.new([c0[0], c0[1], c1[1], c1[0]])
    bm_cut.faces.new([c0[3], c0[2], c1[2], c1[3]])
    bm_cut.faces.new([c0[0], c0[3], c1[3], c1[0]])
    bm_cut.faces.new([c0[1], c1[1], c1[2], c0[2]])
me_cut = bpy.data.meshes.new("River_Cutter")
bm_cut.to_mesh(me_cut)
bm_cut.free()
obj_cut = bpy.data.objects.new("River_Cutter", me_cut)
bpy.context.collection.objects.link(obj_cut)

mod_r = ground_obj.modifiers.new("RiverTrench", 'BOOLEAN')
mod_r.operation = 'DIFFERENCE'
mod_r.object = obj_cut
bpy.context.view_layer.objects.active = ground_obj
bpy.ops.object.modifier_apply(modifier="RiverTrench")
bpy.data.objects.remove(obj_cut, do_unlink=True)

# River water ribbon
bm_riv = bmesh.new()
r_rib = []
for xc, yc, rw, rz in river_pts:
    hw = rw * 0.48
    v0 = bm_riv.verts.new((xc - hw, yc, rz))
    v1 = bm_riv.verts.new((xc + hw, yc, rz))
    r_rib.append((v0, v1))
for i in range(len(r_rib) - 1):
    c0 = r_rib[i]
    c1 = r_rib[i+1]
    bm_riv.faces.new([c0[0], c0[1], c1[1], c1[0]])
me_riv = bpy.data.meshes.new("River_Water_Ribbon")
bm_riv.to_mesh(me_riv)
bm_riv.free()
obj_riv = bpy.data.objects.new("River_Water_Ribbon", me_riv)
bpy.context.collection.objects.link(obj_riv)
for p in obj_riv.data.polygons: p.use_smooth = False
obj_riv.data.materials.append(mat_water_blue)

# Stepping stones across the river at Y = 5.8m
stepping_stones = [
    (-0.7, 5.8, 0.26, 0.32),
    ( 0.1, 5.7, 0.27, 0.35),
    ( 0.9, 5.9, 0.25, 0.30),
]
for sx, sy, sz, sr in stepping_stones:
    bpy.ops.mesh.primitive_cylinder_add(vertices=7, radius=sr, depth=0.18, location=(sx, sy, sz))
    st = bpy.context.active_object
    for p in st.data.polygons: p.use_smooth = False
    st.data.materials.append(mat_da_sang)

# Natural LPM River Stones framing the southern fan rim of the sunken pond
rim_angles = [0.08, 0.22, 0.35, 0.50, 0.65, 0.78, 0.92, 1.08, 1.22, 1.35, 1.50, 1.65, 1.78, 1.92]
for i, a_mult in enumerate(rim_angles):
    ang = a_mult * math.pi
    if not (math.pi * 0.28 <= ang <= math.pi * 0.72):
        rx = pond_cx + (pond_r + 0.35) * math.cos(ang)
        ry = pond_cy + (pond_r + 0.35) * math.sin(ang)
        import_lpm_asset(rock_small, f"Pond_Fan_Stone_{i}", (rx, ry, 0.40), rot_z_deg=i*25, scale=0.92)

# ==============================================================================
# 5. CAMERA & LIGHTING (HEROIC GORGE PERSPECTIVE)
# ==============================================================================
cam_data = bpy.data.cameras.new("MountainCam")
cam_data.type = 'ORTHO'
cam_data.ortho_scale = 49.5   # Balanced margins >= 60px on all 4 sides
cam_obj = bpy.data.objects.new("MountainCam", cam_data)
sc.collection.objects.link(cam_obj)
sc.camera = cam_obj

pitch = math.radians(27)
yaw = math.radians(12)
dist = 70.0

tx, ty, tz = 0.0, 12.2, 4.2
cx = tx + dist * math.sin(yaw) * math.cos(pitch)
cy = ty - dist * math.cos(yaw) * math.cos(pitch)
cz = tz + dist * math.sin(pitch)
cam_obj.location = Vector((cx, cy, cz))

target = Vector((tx, ty, tz))
direction = target - cam_obj.location
rot_quat = direction.to_track_quat('-Z', 'Y')
cam_obj.rotation_euler = rot_quat.to_euler()

# Lights
sun = bpy.data.objects.new("Sun", bpy.data.lights.new("Sun", 'SUN'))
sc.collection.objects.link(sun)
sun.data.energy = 3.6
sun.data.color = tt((255, 246, 228)) # Warm golden sunlight
sun.rotation_euler = (math.radians(48), math.radians(12), math.radians(-32))

fill = bpy.data.objects.new("SunFill", bpy.data.lights.new("SunFill", 'SUN'))
sc.collection.objects.link(fill)
fill.data.energy = 0.65
fill.data.use_shadow = False
fill.data.color = tt((190, 218, 238)) # Soft sky fill
fill.rotation_euler = (math.radians(60), 0, math.radians(150))

rim = bpy.data.objects.new("GorgeRim", bpy.data.lights.new("GorgeRim", 'SUN'))
sc.collection.objects.link(rim)
rim.data.energy = 0.50
rim.data.use_shadow = False
rim.data.color = tt((230, 245, 255))
rim.rotation_euler = (math.radians(35), 0, math.radians(-160))

world = bpy.data.worlds.new("W")
sc.world = world
world.use_nodes = True
bg = world.node_tree.nodes["Background"]
bg.inputs[1].default_value = 0.85
bg.inputs[0].default_value = (*tt((215, 228, 238)), 1.0) # Clean studio sky

sc.render.engine = "BLENDER_EEVEE"
sc.render.resolution_x = 1920
sc.render.resolution_y = 1080
sc.render.filepath = PNG_OUT

print(f"🎬 Đang render showcase hình ảnh: {PNG_OUT}...")
bpy.ops.render.render(write_still=True)

# Export GLB Master
exportables = [
    o for o in sc.objects 
    if o.type in {'MESH', 'EMPTY'} and o != cam_obj and not o.name.startswith("Sun") and not o.name.startswith("GorgeRim")
]
for o in sc.objects: o.select_set(False)
for o in exportables: o.select_set(True)

print(f"📦 Đang xuất GLB Master: {GLB_OUT}...")
bpy.ops.export_scene.gltf(
    filepath=GLB_OUT,
    use_selection=True,
    export_format='GLB',
    export_apply=True
)
print("✨ HOÀN TẤT BUILD V8.0!")

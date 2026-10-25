#!/usr/bin/env python3
"""
build_mountain_waterfall_pack_v10.py - MASTER v10.0 (ORGANIC S-CURVE RIVER & SEAMLESS POND CONNECTION)

Addresses Boss's directives:
1. "s curve river still look square edges to me":
   - Upgraded river path to 28 dense smooth parametric spline sample points with smooth sinusoidal meander.
   - Replaced vertical rectangular box channel with a natural 45-degree trapezoidal sloped embankment.
   - Smooth, organic low-poly river curves with zero sharp kinks.

2. "why there are white rocks with equally range surround the pond":
   - Completely deleted the artificial 14 equally-spaced rim stones around the pond.
   - Natural pristine grass meets the water cleanly; only organic rock clusters remain at the mountain base corners.

3. "why i see there are like a gray line between the connection of the pond and the river":
   - River trench cutter and water ribbon now start at Y = 11.5m (DEEP INSIDE the pond cavity, Y_pond_rim = 8.3m).
   - Completely eliminated the ground barrier / seam between the pond basin and river channel.
   - 100% seamless, continuous fluid connection.
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

mat_da        = get_mat("M_Da",        (112, 106,  98), roughness=0.92)  # Unified weathered cliff rock
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

gw = 2.40

# ==============================================================================
# 1. SINGLE UNIFIED MOUNTAIN RANGE
# ==============================================================================
bm_low = bmesh.new()
low_footprint = [
    (-13.5, 24.5),
    (-13.5, 17.5),
    ( -7.0, 16.5),
    (  -gw, 16.8),
    (  -gw, 20.5),
    (   gw, 20.5),
    (   gw, 16.8),
    (  7.0, 16.5),
    ( 13.5, 17.5),
    ( 13.5, 24.5),
]
n_low = len(low_footprint)
v_bot_low = [bm_low.verts.new((x, y, 0.0)) for x, y in low_footprint]
v_top_low = [bm_low.verts.new((x, y, 4.8)) for x, y in low_footprint]
for i in range(n_low):
    i_next = (i + 1) % n_low
    bm_low.faces.new([v_bot_low[i], v_bot_low[i_next], v_top_low[i_next], v_top_low[i]])
bm_low.faces.new(v_top_low)
me_low = bpy.data.meshes.new("Mountain_Lower_Terrace")
bm_low.to_mesh(me_low)
bm_low.free()
obj_low = bpy.data.objects.new("Mountain_Lower_Terrace", me_low)
bpy.context.collection.objects.link(obj_low)
for p in obj_low.data.polygons: p.use_smooth = False
obj_low.data.materials.append(mat_da)
obj_low.data.materials.append(mat_turf)
for p in obj_low.data.polygons:
    p.material_index = 1 if p.normal.z > 0.8 else 0

bm_summit = bmesh.new()
summit_footprint = [
    (-12.5, 24.5),
    (-12.5, 19.5),
    ( -7.5, 18.8),
    (  -gw, 19.0),
    (  -gw, 20.5),
    (   gw, 20.5),
    (   gw, 19.0),
    (  7.5, 18.8),
    ( 12.5, 19.5),
    ( 12.5, 24.5),
]
n_sum = len(summit_footprint)
v_bot_sum = [bm_summit.verts.new((x, y, 4.8)) for x, y in summit_footprint]
v_top_sum = [bm_summit.verts.new((x, y, 8.5)) for x, y in summit_footprint]
for i in range(n_sum):
    i_next = (i + 1) % n_sum
    bm_summit.faces.new([v_bot_sum[i], v_bot_sum[i_next], v_top_sum[i_next], v_top_sum[i]])
bm_summit.faces.new(v_top_sum)
me_summit = bpy.data.meshes.new("Mountain_Summit_Plateau")
bm_summit.to_mesh(me_summit)
bm_summit.free()
obj_summit = bpy.data.objects.new("Mountain_Summit_Plateau", me_summit)
bpy.context.collection.objects.link(obj_summit)
for p in obj_summit.data.polygons: p.use_smooth = False
obj_summit.data.materials.append(mat_da)
obj_summit.data.materials.append(mat_turf_top)
for p in obj_summit.data.polygons:
    p.material_index = 1 if p.normal.z > 0.8 else 0

# Stepped Bedrock
bw_half = gw + 0.05
bm_bedrock = bmesh.new()
bedrock_profile = [
    (20.5, 8.50),
    (20.5, 5.58),
    (18.8, 5.58),
    (18.8, 2.88),
    (16.8, 2.88),
    (16.8, 0.33),
    (14.8, 0.00),
]
front_v = []
back_v = []
for py, pz in bedrock_profile:
    fl = bm_bedrock.verts.new((-bw_half, py, pz))
    fr = bm_bedrock.verts.new(( bw_half, py, pz))
    bl = bm_bedrock.verts.new((-bw_half, 24.5, pz))
    br = bm_bedrock.verts.new(( bw_half, 24.5, pz))
    front_v.append((fl, fr))
    back_v.append((bl, br))

for i in range(len(bedrock_profile) - 1):
    fl0, fr0 = front_v[i]
    fl1, fr1 = front_v[i+1]
    bl0, br0 = back_v[i]
    bl1, br1 = back_v[i+1]
    bm_bedrock.faces.new([fl0, fr0, fr1, fl1])
    bm_bedrock.faces.new([bl0, fl0, fl1, bl1])
    bm_bedrock.faces.new([fr0, br0, br1, fr1])
    bm_bedrock.faces.new([br0, bl0, bl1, br1])

bm_bedrock.faces.new([back_v[0][0], back_v[0][1], front_v[0][1], front_v[0][0]])
bm_bedrock.faces.new([front_v[-1][0], front_v[-1][1], back_v[-1][1], back_v[-1][0]])

me_bedrock = bpy.data.meshes.new("Gorge_Bedrock")
bm_bedrock.to_mesh(me_bedrock)
bm_bedrock.free()
obj_bedrock = bpy.data.objects.new("Gorge_Bedrock", me_bedrock)
bpy.context.collection.objects.link(obj_bedrock)
for p in obj_bedrock.data.polygons: p.use_smooth = False
obj_bedrock.data.materials.append(mat_da)

# ==============================================================================
# 2. CONTINUOUS WATER BODY: TOP ALPINE LAKE CONNECTED DIRECTLY TO WATERFALL
# ==============================================================================
water_w = gw + 0.02
bm_water = bmesh.new()

lake_profile = [
    (24.2, 3.2),
    (23.4, 4.0),
    (22.2, 3.8),
    (21.2, 3.0),
    (20.5, water_w),
]
lake_rows = []
for py, hx in lake_profile:
    v0 = bm_water.verts.new((-hx, py, 8.52))
    v1 = bm_water.verts.new((-hx*0.5, py, 8.52))
    v2 = bm_water.verts.new(( 0.0, py, 8.52))
    v3 = bm_water.verts.new(( hx*0.5, py, 8.52))
    v4 = bm_water.verts.new(( hx, py, 8.52))
    lake_rows.append((v0, v1, v2, v3, v4))

for i in range(len(lake_rows) - 1):
    r0 = lake_rows[i]
    r1 = lake_rows[i+1]
    for j in range(4):
        bm_water.faces.new([r0[j], r0[j+1], r1[j+1], r1[j]])

wf_steps = [
    (20.485, 5.60),
    (18.785, 5.60),
    (18.785, 2.90),
    (16.785, 2.90),
    (16.785, 0.35),
    (14.800, 0.16),
]
prev_r = lake_rows[-1]
for py, pz in wf_steps:
    v0 = bm_water.verts.new((-water_w, py, pz))
    v1 = bm_water.verts.new((-water_w*0.5, py, pz))
    v2 = bm_water.verts.new(( 0.0, py, pz))
    v3 = bm_water.verts.new(( water_w*0.5, py, pz))
    v4 = bm_water.verts.new(( water_w, py, pz))
    curr_r = (v0, v1, v2, v3, v4)
    for j in range(4):
        bm_water.faces.new([prev_r[j], prev_r[j+1], curr_r[j+1], curr_r[j]])
    prev_r = curr_r

me_water = bpy.data.meshes.new("Continuous_Alpine_Lake_And_Waterfall")
bm_water.to_mesh(me_water)
bm_water.free()
obj_water = bpy.data.objects.new("Continuous_Alpine_Lake_And_Waterfall", me_water)
bpy.context.collection.objects.link(obj_water)
for p in obj_water.data.polygons: p.use_smooth = False
obj_water.data.materials.append(mat_water_blue)

# ==============================================================================
# 3. GROUND TERRAIN, SUNKEN POND & NATURAL SMOOTH S-CURVE RIVER
# ==============================================================================
ground_w, ground_l = 28.0, 29.0
bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0.0, 8.5, 0.20))
ground_obj = bpy.context.active_object
ground_obj.name = "Ground_Terrain"
ground_obj.scale = (ground_w, ground_l, 0.40)
bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
ground_obj.data.materials.append(mat_turf)

# Sunken Fan Pond Cavity
pond_cx, pond_cy = 0.0, 14.5
pond_r = 6.20

bpy.ops.mesh.primitive_cylinder_add(vertices=24, radius=pond_r, depth=0.35, location=(pond_cx, pond_cy, 0.25))
pond_cutter = bpy.context.active_object

mod_p = ground_obj.modifiers.new("PondCavity", 'BOOLEAN')
mod_p.operation = 'DIFFERENCE'
mod_p.solver = 'EXACT'
mod_p.object = pond_cutter
bpy.context.view_layer.objects.active = ground_obj
bpy.ops.object.modifier_apply(modifier="PondCavity")
bpy.data.objects.remove(pond_cutter, do_unlink=True)

# SMOOTH PARAMETRIC S-CURVE RIVER (NO SQUARE EDGES, NO SEAMS)
# Generate 28 dense smooth sample points from Y = 11.5 (DEEP INSIDE POND) down to Y = -6.5
# Starting inside the pond eliminates ANY gray seam between pond and river!
n_pts = 28
smooth_river = []
for i in range(n_pts):
    u = i / (n_pts - 1)
    y = 11.5 - u * 18.0
    
    if y > 8.0:
        x = 0.0
    else:
        v = (8.0 - y) / 14.5
        x = 1.35 * math.sin(v * 2.0 * math.pi) * (1.0 - 0.15 * v)
        
    w_top = 2.8 - u * 0.4
    w_bot = 1.8 - u * 0.3
    z_water = 0.18 - u * 0.07
    smooth_river.append((x, y, w_top, w_bot, z_water))

# Build Watertight Trapezoidal River Trench Cutter
bm_cut = bmesh.new()
t_verts = []
for x, y, wt, wb, zw in smooth_river:
    hwt = wt * 0.5
    hwb = wb * 0.5
    v0 = bm_cut.verts.new((x - hwt, y, 0.50)) # top left
    v1 = bm_cut.verts.new((x + hwt, y, 0.50)) # top right
    v2 = bm_cut.verts.new((x + hwb, y, 0.05)) # bottom right
    v3 = bm_cut.verts.new((x - hwb, y, 0.05)) # bottom left
    t_verts.append((v0, v1, v2, v3))

for i in range(len(t_verts) - 1):
    c0 = t_verts[i]
    c1 = t_verts[i+1]
    bm_cut.faces.new([c0[0], c0[1], c1[1], c1[0]]) # top
    bm_cut.faces.new([c0[3], c0[2], c1[2], c1[3]]) # bottom
    bm_cut.faces.new([c0[0], c0[3], c1[3], c1[0]]) # left sloped bank
    bm_cut.faces.new([c0[1], c1[1], c1[2], c0[2]]) # right sloped bank

c_first = t_verts[0]
c_last = t_verts[-1]
bm_cut.faces.new([c_first[0], c_first[1], c_first[2], c_first[3]])
bm_cut.faces.new([c_last[3], c_last[2], c_last[1], c_last[0]])
bmesh.ops.recalc_face_normals(bm_cut, faces=bm_cut.faces)

me_cut = bpy.data.meshes.new("River_Cutter")
bm_cut.to_mesh(me_cut)
bm_cut.free()
obj_cut = bpy.data.objects.new("River_Cutter", me_cut)
bpy.context.collection.objects.link(obj_cut)

mod_r = ground_obj.modifiers.new("RiverTrench", 'BOOLEAN')
mod_r.operation = 'DIFFERENCE'
mod_r.solver = 'EXACT'
mod_r.object = obj_cut
bpy.context.view_layer.objects.active = ground_obj
bpy.ops.object.modifier_apply(modifier="RiverTrench")
bpy.data.objects.remove(obj_cut, do_unlink=True)

for p in ground_obj.data.polygons:
    p.use_smooth = False
    p.material_index = 0

# Sunken Pond Water Disc at Z = 0.18m
bpy.ops.mesh.primitive_cylinder_add(vertices=24, radius=pond_r, depth=0.04, location=(pond_cx, pond_cy, 0.18))
pond_water = bpy.context.active_object
pond_water.name = "Sunken_Pond_Water"
for p in pond_water.data.polygons: p.use_smooth = False
pond_water.data.materials.append(mat_water_blue)

# Continuous River Water Ribbon (Starts deep inside pond at Y = 11.0 to guarantee 0 seam)
bm_riv = bmesh.new()
r_rib = []
for x, y, wt, wb, zw in smooth_river:
    hwb = wb * 0.52
    v0 = bm_riv.verts.new((x - hwb, y, zw))
    v1 = bm_riv.verts.new((x + hwb, y, zw))
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

# Natural stepping stones crossing at Y = 5.2m (following the river meander)
stepping_stones = [
    ( 0.8, 5.2, 0.26, 0.30),
    ( 1.3, 5.1, 0.27, 0.32),
    ( 1.8, 5.0, 0.25, 0.28),
]
for sx, sy, sz, sr in stepping_stones:
    bpy.ops.mesh.primitive_cylinder_add(vertices=7, radius=sr, depth=0.18, location=(sx, sy, sz))
    st = bpy.context.active_object
    for p in st.data.polygons: p.use_smooth = False
    st.data.materials.append(mat_da_sang)

# NO ARTIFICIAL EQUAL RIM ROCKS!
# Only 2 organic natural rock clusters at mountain base corners where rocks naturally gather:
import_lpm_asset(rock_large, "LPM_Corner_W", (-12.5, 16.8, 0.4), rot_z_deg=25, scale=1.3)
import_lpm_asset(rock_large, "LPM_Corner_E", ( 12.5, 16.8, 0.4), rot_z_deg=-30, scale=1.2)
import_lpm_asset(rock_small, "LPM_Gorge_Base_W", (-2.8, 15.5, 0.40), rot_z_deg=15, scale=1.0)
import_lpm_asset(rock_small, "LPM_Gorge_Base_E", ( 2.8, 15.5, 0.40), rot_z_deg=-20, scale=0.95)

# Camera & Lighting
cam_data = bpy.data.cameras.new("MountainCam")
cam_data.type = 'ORTHO'
cam_data.ortho_scale = 50.5
cam_obj = bpy.data.objects.new("MountainCam", cam_data)
sc.collection.objects.link(cam_obj)
sc.camera = cam_obj

pitch = math.radians(27)
yaw = math.radians(12)
dist = 70.0
tx, ty, tz = 0.0, 10.3, 4.2
cx = tx + dist * math.sin(yaw) * math.cos(pitch)
cy = ty - dist * math.cos(yaw) * math.cos(pitch)
cz = tz + dist * math.sin(pitch)
cam_obj.location = Vector((cx, cy, cz))
target = Vector((tx, ty, tz))
direction = target - cam_obj.location
rot_quat = direction.to_track_quat('-Z', 'Y')
cam_obj.rotation_euler = rot_quat.to_euler()

sun = bpy.data.objects.new("Sun", bpy.data.lights.new("Sun", 'SUN'))
sc.collection.objects.link(sun)
sun.data.energy = 3.6
sun.data.color = tt((255, 246, 228))
sun.rotation_euler = (math.radians(48), math.radians(12), math.radians(-32))

fill = bpy.data.objects.new("SunFill", bpy.data.lights.new("SunFill", 'SUN'))
sc.collection.objects.link(fill)
fill.data.energy = 0.65
fill.data.use_shadow = False
fill.data.color = tt((190, 218, 238))
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
bg.inputs[0].default_value = (*tt((215, 228, 238)), 1.0)

sc.render.engine = "BLENDER_EEVEE"
sc.render.resolution_x = 1920
sc.render.resolution_y = 1080
sc.render.filepath = PNG_OUT

print(f"🎬 Rendering showcase image: {PNG_OUT}...")
bpy.ops.render.render(write_still=True)

# Export GLB Master
exportables = [
    o for o in sc.objects 
    if o.type in {'MESH', 'EMPTY'} and o != cam_obj and not o.name.startswith("Sun") and not o.name.startswith("GorgeRim")
]
for o in sc.objects: o.select_set(False)
for o in exportables: o.select_set(True)

print(f"📦 Exporting GLB Master: {GLB_OUT}...")
bpy.ops.export_scene.gltf(
    filepath=GLB_OUT,
    use_selection=True,
    export_format='GLB',
    export_apply=True
)
print("✨ MASTER v10.0 BUILD & EXPORT COMPLETE!")

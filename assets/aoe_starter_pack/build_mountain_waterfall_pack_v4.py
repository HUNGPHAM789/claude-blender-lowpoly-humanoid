#!/usr/bin/env python3
"""
AOE / SETTLERS — STANDALONE MOUNTAIN WATERFALL PACK (v4.0)
Strictly implementing Boss's exact feedback:
1. "dont need the white color for waterfall yet. start with blue."
   - 100% pure stylized blue water. Removed ALL white foam ribbons, chevron streaks, and mist chunks.
2. "what is the gray object in between the waterfall stream?"
   - Completely REMOVED the intermediate gray rock/boulder that sat in the middle of the stream.
   - Waterfall stream is now 100% unobstructed, clean, and continuous from top to bottom.
3. "the mountains is not connected yet in the middle."
   - Solidly connected the mountains in the middle! Built a massive central rock saddle and continuous
     connecting ridge bridging West and East bluffs. Zero gaps, zero disconnected mounds.
4. "the waterfall should just be a mask of blue on top of the mountain and square down to the ground of the big round blue first."
   - Top: A clean mask of blue water resting on the mountain crest/saddle (Z=7.5m).
   - Cascade: Clean blue chute stepping/squaring straight down the face of the mountain to the ground.
   - Ground: A big round blue pool (R=4.8m) on the ground at the base.
"""
import bpy
import bmesh
import math
import os
import random
from mathutils import Vector, Matrix

out_dir = "~/projects/lpm-faceless-humanoid/assets/aoe_starter_pack"
out_glb = os.path.join(out_dir, "mountain_waterfall_pack.glb")
out_img = os.path.join(out_dir, "showcase_mountain_waterfall.png")

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene

def tt(c):
    return tuple(((x / 255.0) / 12.92) if (x / 255.0) <= 0.04045 else (((x / 255.0) + 0.055) / 1.055) ** 2.4 for x in c)

def get_mat(name, srgb_color, roughness=0.88, metallic=0.0, emission_srgb=None, emission_strength=0.0):
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

# LPM Palette
mat_da        = get_mat("M_Da",        (112, 106,  98), roughness=0.92)  # Weathered mountain stone
mat_da_sang   = get_mat("M_DaSang",    (138, 132, 122), roughness=0.90)  # Sunlit ledge stone
mat_da_toi    = get_mat("M_DaToi",     ( 78,  72,  66), roughness=0.96)  # Canyon shadow stone
mat_turf      = get_mat("M_Turf",      ( 92, 132,  56), roughness=0.85)  # Alpine meadow grass
mat_turf_top  = get_mat("M_TurfTop",   (115, 155,  68), roughness=0.85)  # Sunlit plateau cap
# PURE BLUE WATER (No white foam)
mat_water_blue= get_mat("M_WaterBlue", ( 42, 132, 172), roughness=0.12, emission_srgb=(45, 140, 182), emission_strength=0.45)

# LPM Rock assets
rock_large = "~/projects/lpm-faceless-humanoid/lpms_store/rock_large/r_38f71967/rock_large.glb"
rock_medium = "~/projects/lpm-faceless-humanoid/lpms_store/rock_medium/r_c1ffb4d4/rock_medium.glb"
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

def make_khoi_meo(name, center, radius, mat, seed=0, meo=0.22, n=14, det=(1.0, 1.0, 1.0), flatten_bot=True):
    """Generates an authentic LPM convex-hull faceted low-poly rock chunk."""
    bm = bmesh.new()
    rng = random.Random(seed)
    cx, cy, cz = center
    dx, dy, dz = det
    for _ in range(n):
        theta = rng.uniform(0, 2 * math.pi)
        phi = math.acos(rng.uniform(-1, 1))
        r = radius * (1.0 + rng.uniform(-meo, meo))
        px = cx + r * math.sin(phi) * math.cos(theta) * dx
        py = cy + r * math.sin(phi) * math.sin(theta) * dy
        pz = cz + r * math.cos(phi) * dz
        if flatten_bot and pz < cz - radius * dz * 0.7:
            pz = cz - radius * dz * 0.7
        bm.verts.new((px, py, pz))
    
    res = bmesh.ops.convex_hull(bm, input=bm.verts)
    bmesh.ops.delete(bm, geom=res['geom_interior'], context='VERTS')
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    obj = bpy.data.objects.new(name, me)
    bpy.context.collection.objects.link(obj)
    for p in obj.data.polygons: p.use_smooth = False
    obj.data.materials.append(mat)
    return obj

def make_plateau_cap(name, center_xy, z_level, radius_x, radius_y, mat=mat_turf_top, seed=12, n=8):
    """Creates a flat alpine meadow cap on a mountain terrace."""
    bm = bmesh.new()
    rng = random.Random(seed)
    cx, cy = center_xy
    c_vert = bm.verts.new((cx, cy, z_level))
    rim = []
    for i in range(n):
        ang = i * (2 * math.pi / n)
        rx = radius_x * (1.0 + rng.uniform(-0.10, 0.10))
        ry = radius_y * (1.0 + rng.uniform(-0.10, 0.10))
        vx = cx + rx * math.cos(ang)
        vy = cy + ry * math.sin(ang)
        rim.append(bm.verts.new((vx, vy, z_level)))
    for i in range(n):
        i_next = (i + 1) % n
        bm.faces.new([rim[i], rim[i_next], c_vert])
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    obj = bpy.data.objects.new(name, me)
    bpy.context.collection.objects.link(obj)
    for p in obj.data.polygons: p.use_smooth = False
    obj.data.materials.append(mat)
    return obj

def create_mesh_obj(name, verts, faces, mat):
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], faces)
    me.update()
    obj = bpy.data.objects.new(name, me)
    bpy.context.collection.objects.link(obj)
    for p in obj.data.polygons: p.use_smooth = False
    obj.data.materials.append(mat)
    return obj

# ==============================================================================
# 1. CONTINUOUS CONNECTED MOUNTAIN MASSIF (BRIDGED IN THE MIDDLE)
# ==============================================================================
# A. Solid Central Connecting Saddle & Ridge (Bridge between West and East)
# These central blocks completely connect the mountain in the middle!
make_khoi_meo("Center_Base_Bridge",   ( 0.0, 21.0, 2.0), 5.5, mat_da, seed=50,  meo=0.18, n=15, det=(1.6, 1.2, 0.75))
make_khoi_meo("Center_Mid_Bridge",    ( 0.0, 21.5, 4.8), 4.8, mat_da, seed=51,  meo=0.18, n=14, det=(1.5, 1.1, 0.80))
make_khoi_meo("Center_High_Saddle",   ( 0.0, 22.2, 7.2), 3.8, mat_da_sang, seed=52, meo=0.16, n=13, det=(1.4, 1.0, 0.80))

# B. West Mountain Flank (Peak H=10.5m)
make_khoi_meo("W_Buttress_1", (-9.0, 21.0, 2.0), 5.2, mat_da, seed=101, meo=0.20, n=15, det=(1.3, 1.1, 0.75))
make_khoi_meo("W_Buttress_2", (-13.5, 22.0, 2.2), 4.6, mat_da_sang, seed=102, meo=0.22, n=14, det=(1.1, 1.2, 0.80))
make_khoi_meo("W_MidCliff_1", (-8.5, 21.5, 5.2), 4.4, mat_da, seed=104, meo=0.20, n=14, det=(1.2, 1.0, 0.85))
make_khoi_meo("W_MidCliff_2", (-12.2, 22.0, 5.4), 3.8, mat_da_sang, seed=105, meo=0.20, n=13, det=(1.0, 1.1, 0.85))
make_plateau_cap("W_Mid_Shelf_Grass", (-8.8, 20.2), 6.1, 3.4, 2.2, mat_turf, seed=110, n=8)

make_khoi_meo("W_Summit_1", (-8.0, 21.8, 8.4), 3.6, mat_da, seed=107, meo=0.18, n=14, det=(1.1, 1.0, 0.85))
make_khoi_meo("W_Summit_2", (-11.0, 22.2, 8.5), 3.2, mat_da_sang, seed=108, meo=0.18, n=12, det=(0.9, 1.0, 0.85))
make_plateau_cap("W_Summit_Grass", (-8.2, 21.8), 10.4, 2.8, 2.0, mat_turf_top, seed=111, n=8)

# C. East Mountain Flank (Peak H=8.8m)
make_khoi_meo("E_Buttress_1", ( 9.0, 21.2, 2.0), 4.9, mat_da, seed=201, meo=0.20, n=15, det=(1.2, 1.1, 0.75))
make_khoi_meo("E_Buttress_2", (13.2, 22.5, 2.0), 4.4, mat_da_sang, seed=202, meo=0.22, n=13, det=(1.0, 1.1, 0.80))
make_khoi_meo("E_MidCliff_1", ( 8.2, 21.6, 5.0), 4.0, mat_da, seed=204, meo=0.20, n=14, det=(1.1, 1.0, 0.85))
make_khoi_meo("E_MidCliff_2", (11.8, 22.0, 5.1), 3.4, mat_da_sang, seed=205, meo=0.20, n=12, det=(0.9, 1.0, 0.85))
make_plateau_cap("E_Mid_Shelf_Grass", ( 8.4, 20.6), 5.7, 3.0, 2.0, mat_turf, seed=210, n=8)

make_khoi_meo("E_Summit_1", ( 7.5, 21.8, 7.6), 3.1, mat_da, seed=207, meo=0.18, n=13, det=(1.0, 1.0, 0.80))
make_plateau_cap("E_Summit_Grass", ( 7.5, 21.8), 8.8, 2.4, 1.8, mat_turf_top, seed=211, n=7)

# Flanking LPM Rocks at foothills
import_lpm_asset(rock_large, "LPM_Foothill_W", (-4.6, 17.5, 0.0), rot_z_deg=20, scale=1.35)
import_lpm_asset(rock_large, "LPM_Foothill_E", ( 4.7, 17.2, 0.0), rot_z_deg=-35, scale=1.25)
import_lpm_asset(rock_medium, "LPM_Side_W",     (-13.5, 17.0, 0.0), rot_z_deg=15, scale=1.4)
import_lpm_asset(rock_medium, "LPM_Side_E",     ( 13.8, 17.5, 0.0), rot_z_deg=-45, scale=1.35)

# ==============================================================================
# 2. "MASK OF BLUE ON TOP OF THE MOUNTAIN" (MOUNTAIN SPRING POOL)
# ==============================================================================
# Sitting on top of the connected saddle at Z=7.5m:
top_pool_bm = bmesh.new()
tp_c = top_pool_bm.verts.new((0.0, 22.2, 7.50))
tp_rim = []
tp_n = 10
tp_rx, tp_ry = 2.4, 1.6
rng_tp = random.Random(77)
for i in range(tp_n):
    ang = i * (2 * math.pi / tp_n)
    vx = 0.0 + tp_rx * (1.0 + rng_tp.uniform(-0.10, 0.10)) * math.cos(ang)
    vy = 22.2 + tp_ry * (1.0 + rng_tp.uniform(-0.10, 0.10)) * math.sin(ang)
    tp_rim.append(top_pool_bm.verts.new((vx, vy, 7.50)))
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

# Framing stones around the top blue pool
import_lpm_asset(rock_small, "Top_Rock_L", (-2.2, 21.8, 7.4), rot_z_deg=35, scale=0.95)
import_lpm_asset(rock_small, "Top_Rock_R", ( 2.2, 21.8, 7.4), rot_z_deg=-40, scale=0.95)

# ==============================================================================
# 3. WATERFALL STREAM: "SQUARE DOWN TO THE GROUND" (CLEAN CONTINUOUS BLUE FLOW)
# ==============================================================================
# NO gray object in the middle! Continuous, unobstructed blue cascade sheet!
# Stepped down the face of the mountain:
wf_spine = [
    # (Left_X, Right_X, Y, Z)
    (-1.40,  1.40, 21.2, 7.45),  # Lip spilling from top blue mask
    (-1.50,  1.50, 19.8, 6.20),  # Upper chute
    (-1.65,  1.65, 18.2, 4.80),  # Upper-mid slope
    (-1.80,  1.80, 16.6, 3.40),  # Mid slope (formerly blocked by gray rock - NOW CLEAN & WIDE)
    (-2.00,  2.00, 15.0, 1.90),  # Lower plunge
    (-2.30,  2.30, 13.6, 0.48),  # Reaching the ground into the big round blue
]

wf_verts = []
for lx, rx, wy, wz in wf_spine:
    wf_verts.append((lx, wy, wz))
    wf_verts.append((rx, wy, wz))

wf_faces = []
for i in range(len(wf_spine) - 1):
    i0 = i * 2
    i1 = i0 + 1
    i2 = (i + 1) * 2
    i3 = i2 + 1
    wf_faces.append([i0, i1, i3, i2])

create_mesh_obj("Waterfall_Continuous_Blue_Stream", wf_verts, wf_faces, mat_water_blue)

# Flanking natural canyon guide walls on the sides (NOT blocking the water!)
make_khoi_meo("Canyon_Wall_Guide_L", (-3.2, 17.5, 3.2), 2.2, mat_da_toi, seed=311, meo=0.15, n=12, det=(0.8, 1.2, 1.1))
make_khoi_meo("Canyon_Wall_Guide_R", ( 3.2, 17.5, 3.2), 2.2, mat_da_toi, seed=312, meo=0.15, n=12, det=(0.8, 1.2, 1.1))

# ==============================================================================
# 4. "BIG ROUND BLUE ON THE GROUND"
# ==============================================================================
# Clean, expansive circular ground pool (R=4.6m, centered at X=0, Y=11.8m)
ground_pool_bm = bmesh.new()
gp_cx, gp_cy, gp_cz = 0.0, 11.8, 0.46
gp_c = ground_pool_bm.verts.new((gp_cx, gp_cy, gp_cz))
gp_rim = []
gp_n = 24
gp_r = 4.6
for i in range(gp_n):
    ang = i * (2 * math.pi / gp_n)
    vx = gp_cx + gp_r * math.cos(ang)
    vy = gp_cy + gp_r * math.sin(ang)
    gp_rim.append(ground_pool_bm.verts.new((vx, vy, gp_cz)))

for i in range(gp_n):
    i_next = (i + 1) % gp_n
    ground_pool_bm.faces.new([gp_rim[i], gp_rim[i_next], gp_c])

ground_pool_me = bpy.data.meshes.new("Big_Round_Blue_Pool")
ground_pool_bm.to_mesh(ground_pool_me)
ground_pool_bm.free()
ground_pool_obj = bpy.data.objects.new("Big_Round_Blue_Pool", ground_pool_me)
bpy.context.collection.objects.link(ground_pool_obj)
for p in ground_pool_obj.data.polygons: p.use_smooth = False
ground_pool_obj.data.materials.append(mat_water_blue)

# Regular LPM River Stones bounding the pool perimeter (Natural rim, no white foam)
rim_angles = [0.10, 0.25, 0.40, 0.60, 0.75, 0.90, 1.10, 1.25, 1.40, 1.60, 1.75, 1.90]
for i, a_mult in enumerate(rim_angles):
    ang = a_mult * math.pi
    rx = gp_cx + (gp_r + 0.35) * math.cos(ang)
    ry = gp_cy + (gp_r + 0.35) * math.sin(ang)
    import_lpm_asset(rock_small, f"Pool_Rim_Stone_{i}", (rx, ry, 0.0), rot_z_deg=i*30, scale=0.92)

# ==============================================================================
# 5. EXHIBITION DIORAMA PEDESTAL & GROUND GLADE
# ==============================================================================
bpy.ops.mesh.primitive_cylinder_add(vertices=48, radius=17.5, depth=0.40, location=(0.0, 16.0, -0.20))
stage = bpy.context.active_object
stage.name = "Diorama_Stage"
for p in stage.data.polygons: p.use_smooth = False
stage.data.materials.append(mat_turf)

# ==============================================================================
# 6. CAMERA & LIGHTING (HEROIC GORGE PERSPECTIVE)
# ==============================================================================
cam_data = bpy.data.cameras.new("MountainCam")
cam_data.type = 'ORTHO'
cam_data.ortho_scale = 48.0   # Balanced margins >= 60px on all 4 sides
cam_obj = bpy.data.objects.new("MountainCam", cam_data)
sc.collection.objects.link(cam_obj)
sc.camera = cam_obj

# Camera positioned in front of the gorge (Yaw = 12 deg, Pitch = 27 deg)
pitch = math.radians(27)
yaw = math.radians(12)
dist = 70.0

tx, ty, tz = 0.0, 15.5, 4.2
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

# Ambient rim light to accentuate gorge depth
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
sc.view_settings.view_transform = "AgX"

# Render Showcase PNG
sc.render.filepath = out_img
bpy.ops.render.render(write_still=True)
print(f"📸 Mountain Waterfall Showcase Rendered -> {out_img}")

# Export Standalone GLB (Unlinking diorama stage ground)
bpy.data.objects.remove(stage, do_unlink=True)
bpy.ops.export_scene.gltf(
    filepath=out_glb,
    export_format='GLB',
    use_selection=False,
    export_apply=True
)
print(f"✅ Exported Standalone Mountain Waterfall Pack GLB -> {out_glb}")

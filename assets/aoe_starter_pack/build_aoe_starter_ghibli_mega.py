#!/usr/bin/env python3
"""
AGE OF EMPIRES — MEGA TRIPLED STARTING ISLAND (100M DIAMETER) — v3.4
Conforms 100% to Boss's exact directives:
1. TREES: ALL GREEN! Removed pine_tree (pines) and tree_birch (white leaf birch).
   Exclusively using oak_tree.glb (oak trees) with rich, lush Ghibli green foliage.
2. RIVER: Organic meandering river with rich variant curves, S-bends, oxbow loops,
   and varying width (1.6m chokepoint to 6.0m ocean delta).
3. MOUNTAINS: Not pointy cones! Separately designed as two massive weathered
   terraced rock massifs (West Bluff & East Bluff) with flat/slanted ridge tops,
   enclosing a central mountain gorge.
4. WATERFALL IN THE MIDDLE: Cascades right down the central gorge between the two mountains,
   dropping in two tiers into a central mountain pool.
5. STONES: Unified regular stones only (zero weird granite caps, zero strange ore veins).
6. CAMERA: Low 28° 3/4 isometric perspective.
7. GHIBLI COLOR PALETTE & LIGHTING: Codex v2 soft, lush, natural tones.
"""
import bpy
import bmesh
import math
import os
from mathutils import Vector, Matrix

out_dir = "~/projects/lpm-faceless-humanoid/assets/aoe_starter_pack"
os.makedirs(out_dir, exist_ok=True)

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

# ==============================================================================
# GHIBLI COLOR PALETTE (Codex v2)
# ==============================================================================
mat_turf        = get_mat("M_GhibliTurf",     (72, 122, 56))      # Lush Ghibli green
mat_sand        = get_mat("M_GhibliSand",     (148, 120, 82))     # Warm earth sand
mat_cliff       = get_mat("M_GhibliCliff",    (74, 88, 50))       # Mossy cliff rock
mat_ocean       = get_mat("M_GhibliOcean",    (32, 86, 106), 0.15, 0.05)  # Deep cerulean
mat_river       = get_mat("M_GhibliRiver",    (50, 126, 140), 0.12, 0.05, (50, 126, 140), 0.4)
mat_waterfall   = get_mat("M_GhibliWaterfall",(216, 237, 245), 0.10, 0.0, (224, 240, 248), 2.2)
mat_foam        = get_mat("M_GhibliFoam",     (224, 240, 248), 0.20, 0.0, (224, 240, 248), 1.2)
mat_riverbed    = get_mat("M_GhibliRiverbed", (54, 48, 38))
mat_stone       = get_mat("M_RegularStone",   (90, 85, 78))       # Regular natural stone for all rocks & mountains
mat_fire        = get_mat("M_FireFlame",      (255, 140, 20), 0.10, 0.0, (255, 140, 20), 3.8)
mat_charcoal    = get_mat("M_Charcoal",       (32, 30, 28))
mat_bark        = get_mat("M_Bark",           (74, 53, 37))

def create_poly_mesh(name, verts, faces, mat):
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], faces)
    me.update()
    obj = bpy.data.objects.new(name, me)
    bpy.context.collection.objects.link(obj)
    for p in obj.data.polygons: p.use_smooth = False
    obj.data.materials.append(mat)
    return obj

# ==============================================================================
# IMPORT REAL LPM ASSETS HELPER & ASSET PATHS
# ==============================================================================
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
        if o.parent is None:
            o.parent = parent
        if o.type == 'MESH':
            for p in o.data.polygons:
                p.use_smooth = False
            for mat in o.data.materials:
                if mat and 'cream' in mat.name.lower():
                    bsdf = mat.node_tree.nodes.get("Principled BSDF") if mat.node_tree else None
                    if bsdf and "Base Color" in bsdf.inputs:
                        # Harmonize rabbit chest from harsh stark cream to natural warm underbelly
                        bsdf.inputs["Base Color"].default_value = (0.74, 0.66, 0.56, 1.0)
    return parent

# ==============================================================================
# 1. MEGA TRIPLED ISLAND GEOMETRY (Plateau R=32m, Beach R=38m, Water R=46m)
# ==============================================================================
bpy.ops.mesh.primitive_cylinder_add(vertices=32, radius=46.0, depth=0.50, location=(0, 0, -0.25))
water = bpy.context.active_object
water.name = "Island_Ocean"
for p in water.data.polygons: p.use_smooth = False
water.data.materials.append(mat_ocean)

bpy.ops.mesh.primitive_cylinder_add(vertices=28, radius=38.0, depth=0.60, location=(0, 0, 0.10))
sand = bpy.context.active_object
sand.name = "Island_Beach"
for p in sand.data.polygons: p.use_smooth = False
sand.data.materials.append(mat_sand)

bpy.ops.mesh.primitive_cylinder_add(vertices=24, radius=32.0, depth=0.80, location=(0, 0, 0.40))
plateau = bpy.context.active_object
plateau.name = "Island_Plateau"
for p in plateau.data.polygons: p.use_smooth = False
plateau.data.materials.append(mat_turf)

# ==============================================================================
# 2. WEATHERED TERRACED MOUNTAINS WITH WATERFALL IN THE MIDDLE
# (Not pointy cones! Two massive flanking rock massifs enclosing a central gorge)
# ==============================================================================
def build_terraced_mountain_bluff(name, center_xy, base_r, tiers, mat=mat_stone):
    # Builds stepped weathered rock tiers with flat/slanted tops (zero pointy cones)
    cx, cy = center_xy
    for i, (z_bot, z_top, r_bot, r_top, n_sides, rot_d) in enumerate(tiers):
        depth = z_top - z_bot
        mid_z = (z_bot + z_top) / 2.0
        bpy.ops.mesh.primitive_cylinder_add(
            vertices=n_sides,
            radius=r_bot,
            depth=depth,
            location=(cx, cy, mid_z)
        )
        tier_obj = bpy.context.active_object
        tier_obj.name = f"{name}_Tier_{i}"
        # Slight taper towards top
        tier_obj.scale = (1.0, 1.0, 1.0)
        tier_obj.rotation_euler.z = math.radians(rot_d)
        for p in tier_obj.data.polygons: p.use_smooth = False
        tier_obj.data.materials.append(mat)

# West Mountain Massif (Flanking West of waterfall)
west_tiers = [
    # z_bot, z_top, r_bot, r_top, n_sides, rot_deg
    (0.80,  3.50, 11.5, 10.5, 10,  15),
    (3.50,  6.20,  9.5,  8.5,  9, -30),
    (6.20,  8.60,  7.5,  6.5,  8,  45),
    (8.60, 10.50,  5.5,  4.5,  7, -10),
    (10.50, 11.60, 3.8,  3.2,  7,  25) # Weathered flat ridge top
]
build_terraced_mountain_bluff("Mountain_West_Bluff", (-12.0, 22.0), 11.5, west_tiers)

# East Mountain Massif (Flanking East of waterfall)
east_tiers = [
    (0.80,  3.20, 10.5,  9.5, 10, -20),
    (3.20,  5.80,  8.5,  7.5,  9,  35),
    (5.80,  8.20,  6.8,  5.8,  8, -40),
    (8.20,  9.80,  5.0,  4.0,  7,  15),
    (9.80, 10.80,  3.5,  2.8,  7, -30) # Weathered flat ridge top
]
build_terraced_mountain_bluff("Mountain_East_Bluff", (11.5, 22.5), 10.5, east_tiers)

# Foothill Boulders: Replaced sharp icospheres (diamond-shaped artifacts) with authentic LPM natural boulder assets
foothill_stones = [
    (rock_medium, -4.5, 18.0, 1.4, 25),
    (rock_medium,  4.8, 17.5, 1.3, -40),
    (rock_small, -7.5, 16.5, 1.5, 70),
    (rock_small,  7.8, 17.0, 1.4, -60),
    (rock_medium,-14.5, 16.0, 1.6, 15),
    (rock_medium, 15.0, 16.5, 1.5, -30)
]
for i, (stone_asset, sx, sy, s_scale, s_rot) in enumerate(foothill_stones):
    import_lpm_asset(stone_asset, f"Foothill_Stone_{i}", (sx, sy, 0.80), rot_z_deg=s_rot, scale=s_scale)

# --- WATERFALL IN THE MIDDLE (Cascading through the Central Gorge) ---
# Tier 1 (Upper chute pouring from mountain cleft between the two bluffs)
wf1_verts = [
    (-0.8, 23.0, 8.5), (0.8, 23.0, 8.5),
    ( 1.1, 20.0, 4.6), (-1.1, 20.0, 4.6)
]
create_poly_mesh("Waterfall_Tier1", wf1_verts, [[0, 1, 2, 3]], mat_waterfall)

# Mid-canyon rock shelf & basin
bpy.ops.mesh.primitive_cylinder_add(vertices=8, radius=2.5, depth=0.6, location=(0.0, 19.8, 4.5))
mid_shelf = bpy.context.active_object
for p in mid_shelf.data.polygons: p.use_smooth = False
mid_shelf.data.materials.append(mat_stone)

bpy.ops.mesh.primitive_cylinder_add(vertices=8, radius=2.0, depth=0.15, location=(0.0, 19.8, 4.8))
mid_pool = bpy.context.active_object
for p in mid_pool.data.polygons: p.use_smooth = False
mid_pool.data.materials.append(mat_waterfall)

# Tier 2 (Vertical plunge down into Central Mountain Pool)
wf2_verts = [
    (-1.0, 19.5, 4.6), (1.0, 19.5, 4.6),
    ( 1.4, 16.8, 0.95), (-1.4, 16.8, 0.95)
]
create_poly_mesh("Waterfall_Tier2", wf2_verts, [[0, 1, 2, 3]], mat_waterfall)

# Central Mountain Splash Pool at Gorge Mouth
bpy.ops.mesh.primitive_cylinder_add(vertices=14, radius=3.8, depth=0.20, location=(0.0, 16.5, 0.88))
wf_pool = bpy.context.active_object
wf_pool.name = "Waterfall_Splash_Pool"
for p in wf_pool.data.polygons: p.use_smooth = False
wf_pool.data.materials.append(mat_river)

# Foam Ring around pool
bpy.ops.mesh.primitive_cylinder_add(vertices=14, radius=4.2, depth=0.08, location=(0.0, 16.5, 0.87))
wf_foam = bpy.context.active_object
for p in wf_foam.data.polygons: p.use_smooth = False
wf_foam.data.materials.append(mat_foam)

# River Stones encasing the pool: Natural LPM river stones (rock_small), zero diamond artifacts
for i in range(12):
    ang = i * (2 * math.pi / 12)
    if ang < math.pi * 0.35 or ang > math.pi * 0.65: # leave south outlet open for river
        px = 0.0 + 4.0 * math.cos(ang)
        py = 16.5 + 4.0 * math.sin(ang)
        import_lpm_asset(rock_small, f"Pool_Stone_{i}", (px, py, 0.80), rot_z_deg=i*30, scale=0.95)

# ==============================================================================
# 3. ORGANIC MEANDERING RIVER WITH RICH VARIANT CURVES
# (Flows out of the mountain pool, through glades, past campfire, into ocean)
# ==============================================================================
# 17 waypoints with organic curvature and varied width: (x, y, z, width)
river_waypoints = [
    (  0.0,  16.0,  0.86,  2.2),  # Mountain pool outlet
    ( -1.2,  13.5,  0.86,  2.0),  # Curves gently West
    (  1.5,  11.0,  0.85,  2.6),  # Curves East into lazy bend
    (  4.5,   9.2,  0.85,  3.0),  # Wide sweeping curve near forest
    (  2.8,   6.8,  0.84,  2.2),  # Swings back South-West
    (  1.2,   4.5,  0.84,  1.6),  # Narrow chokepoint with Stepping Stones!
    ( -0.5,   2.2,  0.83,  2.5),  # Curves around Campfire glade
    ( -1.8,  -0.5,  0.82,  2.8),  # Deep oxbow bend South-West of firepit
    (  0.5,  -3.2,  0.82,  2.4),  # S-curve swinging South-East
    (  4.2,  -6.5,  0.80,  3.2),  # Wide tranquil stretch in central meadow
    (  8.5,  -9.5,  0.78,  2.6),  # Meander loop East
    ( 11.0, -13.5,  0.75,  2.8),  # Swings South
    ( 15.5, -17.5,  0.70,  2.4),  # Approaching plateau cliff
    ( 20.5, -21.5,  0.55,  2.0),  # Deep rocky canyon gorge cutting plateau
    ( 25.0, -25.5,  0.35,  3.2),  # Rapid tumbling onto sand beach
    ( 30.0, -29.0,  0.15,  4.5),  # Widening river mouth across beach
    ( 35.5, -32.5, -0.22,  6.0)   # Expansive delta into the ocean!
]

def build_organic_river(pts, width_scale=1.0, z_offset=0.0, mat=mat_river, name="River_Water"):
    verts = []
    faces = []
    N = len(pts)
    for i in range(N):
        x, y, z, w = pts[i]
        if i == 0:
            tx = pts[1][0] - x
            ty = pts[1][1] - y
        elif i == N - 1:
            tx = x - pts[i-1][0]
            ty = y - pts[i-1][1]
        else:
            tx = pts[i+1][0] - pts[i-1][0]
            ty = pts[i+1][1] - pts[i-1][1]
        mag = math.hypot(tx, ty)
        nx = -ty / mag
        ny =  tx / mag
        width = w * width_scale
        verts.append([x + nx * width / 2.0, y + ny * width / 2.0, z + z_offset])
        verts.append([x - nx * width / 2.0, y - ny * width / 2.0, z + z_offset])
    for i in range(N - 1):
        v0 = i * 2
        v1 = i * 2 + 1
        v2 = (i + 1) * 2
        v3 = (i + 1) * 2 + 1
        faces.append([v0, v1, v3, v2])
    return create_poly_mesh(name, verts, faces, mat)

# Riverbed Gravel & River Surface Ribbon
build_organic_river(river_waypoints, width_scale=1.45, z_offset=-0.08, mat=mat_riverbed, name="River_Bed")
build_organic_river(river_waypoints, width_scale=1.00, z_offset=0.0,   mat=mat_river,    name="River_Water")

# Stepping Stones at the narrow crossing (1.2, 4.5) — flat weathered low-poly river slabs
for sx_step, sy_step, srad in [(0.9, 4.5, 0.45), (1.5, 4.5, 0.42)]:
    bpy.ops.mesh.primitive_cylinder_add(vertices=7, radius=srad, depth=0.18, location=(sx_step, sy_step, 0.88))
    step_st = bpy.context.active_object
    for p in step_st.data.polygons: p.use_smooth = False
    step_st.data.materials.append(mat_stone)

# Delta Foam at ocean entry
bpy.ops.mesh.primitive_cylinder_add(vertices=12, radius=4.0, depth=0.08, location=(35.5, -32.5, -0.20))
delta_foam = bpy.context.active_object
for p in delta_foam.data.polygons: p.use_smooth = False
delta_foam.data.materials.append(mat_foam)

# ==============================================================================
# 4. CENTRAL FIREPIT & ENCAMPMENT (Location: (-2.0, -3.5, 0.80))
# ==============================================================================
fx, fy, fz = -2.0, -3.5, 0.80
bpy.ops.mesh.primitive_cylinder_add(vertices=12, radius=2.2, depth=0.15, location=(fx, fy, fz + 0.08))
charcoal = bpy.context.active_object
for p in charcoal.data.polygons: p.use_smooth = False
charcoal.data.materials.append(mat_charcoal)

# Cobblestone ring: Rounded low-poly pebbles (subdiv=2, flattened Z) — zero diamond points
for i in range(12):
    ang = i * (2 * math.pi / 12)
    sx = fx + 2.1 * math.cos(ang)
    sy = fy + 2.1 * math.sin(ang)
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2, radius=0.38, location=(sx, sy, fz + 0.22))
    stone = bpy.context.active_object
    stone.scale = (1.0, 1.0, 0.65)
    bpy.ops.object.transform_apply(scale=True)
    for p in stone.data.polygons: p.use_smooth = False
    stone.data.materials.append(mat_stone)

for rot_z in [15, -45, 75]:
    bpy.ops.mesh.primitive_cylinder_add(vertices=6, radius=0.20, depth=2.2, location=(fx, fy, fz + 0.35))
    log = bpy.context.active_object
    log.rotation_euler = (math.radians(12), math.radians(8), math.radians(rot_z))
    for p in log.data.polygons: p.use_smooth = False
    log.data.materials.append(mat_bark)

flame_verts = [
    (fx - 0.45, fy - 0.45, fz + 0.35), (fx + 0.45, fy - 0.45, fz + 0.35),
    (fx + 0.45, fy + 0.45, fz + 0.35), (fx - 0.45, fy + 0.45, fz + 0.35),
    (fx - 0.65, fy, fz + 1.15), (fx + 0.65, fy, fz + 1.15),
    (fx, fy - 0.65, fz + 1.15), (fx, fy + 0.65, fz + 1.15),
    (fx, fy, fz + 2.40)
]
flame_faces = [
    [0, 1, 5, 4], [1, 2, 7, 5], [2, 3, 4, 7], [3, 0, 6, 4],
    [4, 5, 8], [5, 7, 8], [7, 6, 8], [6, 4, 8],
    [0, 3, 2, 1]
]
create_poly_mesh("Prop_FireFlame", flame_verts, flame_faces, mat_fire)

# Storage from LPMS
import_lpm_asset("~/projects/lpm-faceless-humanoid/lpms_store/wood_storage/r_96045bad/wood_storage.glb", "LPM_KhoGo", (14.0, 1.0, 0.80), rot_z_deg=-25, scale=1.5)

# ==============================================================================
# 5. ALL-GREEN TREES & REGULAR STONES ONLY (NO pine_tree, NO tree_birch)
# ==============================================================================
tree_soi   = "~/projects/lpm-faceless-humanoid/lpms_store/oak_tree/r_4f5e6778/oak_tree.glb"
bush_berry = "~/projects/lpm-faceless-humanoid/lpms_store/berry_bush/r_6fc81fa4/berry_bush.glb"
grass_tuft = "~/projects/lpm-faceless-humanoid/lpms_store/grass_a_m/r_c01a764e/grass_a_m.glb"

fl_red   = "~/projects/GameDev/assets/downloads/cgtrader_forest/glb/Flower_bush_red.glb"
fl_blue  = "~/projects/GameDev/assets/downloads/cgtrader_forest/glb/Flower_bush_blue.glb"
mush_brn = "~/projects/GameDev/assets/downloads/cgtrader_forest/glb/Mushroom_big_group_brown.glb"
mush_yel = "~/projects/GameDev/assets/downloads/cgtrader_forest/glb/Mushroom_high_group_yellow.glb"
log_knot = "~/projects/GameDev/assets/downloads/cgtrader_forest/glb/Log_big_knotty.glb"

# ALL GREEN OAK FOREST (oak_tree exclusively)
oak_forest = [
    # North-West Ancient Woods
    (-18.0, 15.0, 1.5, 30),
    (-22.0, 11.0, 1.6, -45),
    (-15.0, 19.0, 1.4, 75),
    (-25.0, 17.0, 1.7, 15),
    (-12.0, 23.0, 1.3, -90),
    (-20.0, 23.0, 1.5, 110),
    (-27.0, 13.0, 1.4, -20),
    (-14.0, 13.0, 1.6, 40),
    (-21.0,  7.0, 1.7, -60),
    (-24.0, 21.0, 1.8, 15),
    (-17.0, 25.0, 1.5, -80),
    (-10.0, 26.0, 1.4, 105),
    (-28.0,  9.0, 1.65, 35),
    # East Woods
    ( 16.0, 13.0, 1.4, 20),
    ( 20.0, 10.0, 1.6, -45),
    ( 18.5, 15.5, 1.35, 80),
    ( 23.0, 12.0, 1.45, -70),
    ( 14.5, 17.5, 1.5, 15),
    ( 21.5, 16.0, 1.3, 50),
    ( 17.0,  8.0, 1.4, -30),
]
for i, (tx, ty, t_sc, t_rot) in enumerate(oak_forest):
    import_lpm_asset(tree_soi, f"Oak_Tree_{i}", (tx, ty, 0.80), rot_z_deg=t_rot, scale=t_sc * 1.8)

# Fallen logs in the woods
import_lpm_asset(log_knot, "Log_1", (-19.0, 13.0, 0.80), rot_z_deg=45, scale=1.4)
import_lpm_asset(log_knot, "Log_2", (-14.0, 22.0, 0.80), rot_z_deg=-60, scale=1.2)

# Mushroom colonies near waterfall and in deep woods
mushrooms = [
    (mush_brn, -13.0, 15.0, 1.3, 10),
    (mush_yel, -17.5, 17.5, 1.4, -40),
    (mush_brn, -21.0, 11.5, 1.2, 85),
    (mush_yel,  2.5,  15.5, 1.35, 120),  # near waterfall mist
    (mush_brn, -2.5,  15.5, 1.25, -15),
]
for i, (m_path, mx, my, msc, mrot) in enumerate(mushrooms):
    import_lpm_asset(m_path, f"Mushroom_{i}", (mx, my, 0.80), rot_z_deg=mrot, scale=msc * 1.2)

# --- REGULAR NATURAL STONES ONLY (NO strange granite caps, NO weird ore veins) ---
regular_stone_placements = [
    (rock_large,  18.0, 19.0, 2.2, 35),
    (rock_large,  23.0, 17.0, 2.0, -50),
    (rock_medium,  15.0, 21.0, 1.8, 80),
    (rock_medium,  20.5, 21.5, 1.7, -25),
    (rock_small,  16.5, 18.0, 1.6, 110),
    (rock_small,  22.0, 19.5, 1.5, -95),
    (rock_large,  26.0, 14.0, 2.3, 15),
    # Additional river boulders
    (rock_medium,   5.5,  8.0, 1.5, 45),
    (rock_small,  -2.5,  0.5, 1.3, -30),
    (rock_medium,  19.5,-20.0, 1.8, 65),  # canyon cliff boulder
]
for i, (r_path, rx, ry, rsc, rrot) in enumerate(regular_stone_placements):
    import_lpm_asset(r_path, f"Regular_Stone_{i}", (rx, ry, 0.80), rot_z_deg=rrot, scale=rsc * 1.3)

# --- BERRY BUSHES (South-West Meadow) ---
berry_positions = [
    (-14.0, -12.0, 1.4, 20),
    (-19.0, -10.0, 1.5, -45),
    (-11.5, -16.0, 1.35, 75),
    (-16.0, -15.5, 1.45, -80),
    (-22.0, -13.0, 1.3, 30),
    (-18.5, -19.0, 1.4, 110),
]
for i, (bx, by, bsc, brot) in enumerate(berry_positions):
    import_lpm_asset(bush_berry, f"Berry_Bush_{i}", (bx, by, 0.80), rot_z_deg=brot, scale=bsc * 1.5)

# --- WILDFLOWERS (Red & Blue flower bushes) ---
flowers = [
    (fl_red,  -12.0, -8.0,  1.3, 40),
    (fl_blue, -15.5, -6.5,  1.4, -30),
    (fl_red,  -8.0,  -11.0, 1.25, 95),
    (fl_red,   6.5,   6.0,  1.3, 25),   # along riverbank
    (fl_blue,  4.5,   9.5,  1.25, -50),
    (fl_red,   9.0,   1.5,  1.4, 80),
]
for i, (fl_path, fx, fy, fsc, frot) in enumerate(flowers):
    import_lpm_asset(fl_path, f"Flower_{i}", (fx, fy, 0.80), rot_z_deg=frot, scale=fsc * 1.4)

# --- GHIBLI GRASS TUFTS ---
grass_spots = [
    (-6.0,  6.0), (-8.5, 3.5), (-11.0, 0.0), (-4.5, -6.5), (2.0, -7.0),
    (7.0, -12.0), (12.0, -4.0), (-14.0, -4.0), (-2.0, 9.0), (10.0, 8.0),
    (-20.0, 3.0), (-7.0, 12.0), (15.0, -15.0), (-10.0, -18.0)
]
for i, (gx, gy) in enumerate(grass_spots):
    import_lpm_asset(grass_tuft, f"Grass_Tuft_{i}", (gx, gy, 0.80), rot_z_deg=i*37, scale=1.6)

# ==============================================================================
# 7. AUTHENTIC POSED ANIMALS (DEER HERD + RABBITS)
# ==============================================================================
stag_glb   = "~/projects/lpm-faceless-humanoid/assets/organic/downloads/quaternius_deer/ab/stag_origami.glb"
doe_glb    = "~/projects/lpm-faceless-humanoid/assets/organic/downloads/quaternius_deer/doe_origami.glb"
rabbit_glb = "~/projects/lpm-faceless-humanoid/assets/organic/rabbit_v1/rabbit.glb"

def spawn_static_posed_animal(filepath, name, action_name, frame, loc, yaw_deg, scale):
    truoc = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=filepath)
    moi = [o for o in bpy.data.objects if o not in truoc]
    
    for o in list(moi):
        if 'Icosphere' in o.name:
            bpy.data.objects.remove(o, do_unlink=True)
            moi.remove(o)
            
    arm = [o for o in moi if o.type == 'ARMATURE'][0]
    meshes = [o for o in moi if o.type == 'MESH']
    
    act = bpy.data.actions.get(action_name) or bpy.data.actions.get(f'AnimalArmature|{action_name}')
    if act: arm.animation_data.action = act
    bpy.context.scene.frame_set(frame)
    bpy.context.view_layer.update()
    
    dg = bpy.context.evaluated_depsgraph_get()
    min_z = 999.0
    for m in meshes:
        eval_m = m.evaluated_get(dg)
        to_m = eval_m.to_mesh()
        for v in to_m.vertices:
            w_v = m.matrix_world @ v.co
            min_z = min(min_z, w_v.z)
        eval_m.to_mesh_clear()
        
    created_objs = []
    rot_mat = Matrix.Rotation(math.radians(yaw_deg), 4, 'Z')
    for i, m in enumerate(meshes):
        eval_m = m.evaluated_get(dg)
        new_mesh_data = bpy.data.meshes.new_from_object(eval_m)
        eval_m.to_mesh_clear()
        for v in new_mesh_data.vertices:
            co_posed = m.matrix_world @ v.co
            co_zeroed = Vector((co_posed.x - arm.location.x, co_posed.y - arm.location.y, co_posed.z - min_z))
            co_final = rot_mat @ (co_zeroed * scale)
            v.co = co_final
        obj = bpy.data.objects.new(f'{name}_part_{i}', new_mesh_data)
        bpy.context.collection.objects.link(obj)
        obj.location = Vector(loc)
        for mat in m.data.materials: obj.data.materials.append(mat)
        for p in obj.data.polygons: p.use_smooth = False
        created_objs.append(obj)
        
    for o in list(moi):
        if o in bpy.data.objects.values():
            bpy.data.objects.remove(o, do_unlink=True)
    return created_objs

# WESTERN GLADE DEER PACK (Herd of 7: Stag, 3 Does, 2 Yearlings, 1 Fawn)
spawn_static_posed_animal(stag_glb, "Deer_AlphaStag",  "Idle",         0,  (-12.0,  4.0, 0.80), yaw_deg=-35, scale=1.35)
spawn_static_posed_animal(doe_glb,  "Deer_Doe_Alert",  "Idle",         0,  (-16.0,  1.5, 0.80), yaw_deg=50,  scale=1.10)
spawn_static_posed_animal(doe_glb,  "Deer_Doe_Graze1", "Eating",       50, (-14.0,  7.5, 0.80), yaw_deg=-120,scale=1.10)
spawn_static_posed_animal(doe_glb,  "Deer_Doe_Graze2", "Eating",       55, (-9.5,   9.0, 0.80), yaw_deg=70,  scale=1.05)
spawn_static_posed_animal(doe_glb,  "Deer_Yearling1",  "Eating",       50, (-18.0,  5.0, 0.80), yaw_deg=85,  scale=0.82)
spawn_static_posed_animal(doe_glb,  "Deer_Yearling2",  "Walk",         10, (-10.0, -1.5, 0.80), yaw_deg=-65, scale=0.85)
spawn_static_posed_animal(doe_glb,  "Deer_Fawn",       "Eating",       50, (-17.0, -0.5, 0.80), yaw_deg=35,  scale=0.55)

# 4 Wild Rabbits
import_lpm_asset(rabbit_glb, "Rabbit_1", (-6.0,  2.0,  0.80), rot_z_deg=45,  scale=1.8)
import_lpm_asset(rabbit_glb, "Rabbit_2", (-7.5, -4.0,  0.80), rot_z_deg=-55, scale=1.6)
import_lpm_asset(rabbit_glb, "Rabbit_3", (-13.0,-3.0,  0.80), rot_z_deg=105, scale=1.7)
import_lpm_asset(rabbit_glb, "Rabbit_4", (-15.0, 10.0, 0.80), rot_z_deg=-80, scale=1.5)

bpy.context.view_layer.update()

# ==============================================================================
# 8. CAMERA SETUP (LOWER 28° PITCH ISOMETRIC VIEW)
# ==============================================================================
cam_data = bpy.data.cameras.new("AoECam")
cam_data.type = 'ORTHO'
cam_data.ortho_scale = 118.0
cam_obj = bpy.data.objects.new("AoECam", cam_data)
sc.collection.objects.link(cam_obj)
sc.camera = cam_obj

pitch = math.radians(28)   # LOWER VIEW ANGLE (Boss: "change the view lower, currently way too on top")
yaw = math.radians(45)     # Isometric 45°
dist = 180.0

tx, ty, tz = 0.0, 4.5, 3.2
cx = tx + dist * math.sin(yaw) * math.cos(pitch)
cy = ty - dist * math.cos(yaw) * math.cos(pitch)
cz = tz + dist * math.sin(pitch)
cam_obj.location = Vector((cx, cy, cz))

target = Vector((tx, ty, tz))
direction = target - cam_obj.location
rot_quat = direction.to_track_quat('-Z', 'Y')
cam_obj.rotation_euler = rot_quat.to_euler()

# ==============================================================================
# 9. GENTLE GHIBLI LIGHTING (ZERO OVERBLOWN BLOWOUT)
# ==============================================================================
sun = bpy.data.objects.new("SunKey", bpy.data.lights.new("SunKey", 'SUN'))
sc.collection.objects.link(sun)
sun.data.energy = 3.2
sun.data.angle = math.radians(3)
sun.data.color = tt((255, 242, 218))   # Warm golden hour sunlight
sun.rotation_euler = (math.radians(46), 0, math.radians(-38))

fill = bpy.data.objects.new("SunFill", bpy.data.lights.new("SunFill", 'SUN'))
sc.collection.objects.link(fill)
fill.data.energy = 0.35
fill.data.use_shadow = False
fill.data.color = tt((202, 218, 228))  # Soft sky atmospheric fill
fill.rotation_euler = (math.radians(65), 0, math.radians(150))

# Ambient Sky World
world = bpy.data.worlds.new("W")
sc.world = world
world.use_nodes = True
bg = world.node_tree.nodes["Background"]
bg.inputs[1].default_value = 0.75
bg.inputs[0].default_value = (*tt((202, 218, 228)), 1.0)

# EEVEE & AgX Render Settings
sc.render.engine = "BLENDER_EEVEE"
sc.render.resolution_x = 1920
sc.render.resolution_y = 1080
sc.view_settings.view_transform = "AgX"
sc.view_settings.look = "AgX - Base Contrast"

# ==============================================================================
# 10. EXPORT GLB & RENDER PNG
# ==============================================================================
out_glb = os.path.join(out_dir, "aoe_starter_island_full.glb")
out_img = os.path.join(out_dir, "aoe_starter_island_isometric.png")

bpy.ops.export_scene.gltf(
    filepath=out_glb,
    export_format='GLB',
    use_selection=False,
    export_apply=True
)
print(f"✅ Exported Full Mega Tripled AoE Island GLB -> {out_glb}")

sc.render.filepath = out_img
bpy.ops.render.render(write_still=True)
print(f"📸 Mega Tripled AoE Island Isometric Render Complete -> {out_img}")

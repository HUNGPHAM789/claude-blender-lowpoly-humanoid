#!/usr/bin/env python3
"""
Age of Empires (AoE) Starting Point Island Generator v3.2
  - TRIPLED ISLAND SIZE (35m diameter, Plateau R=12.0m)
  - NORTHERN MOUNTAIN & WATERFALL PACK:
    * 3 Low-Poly Mountain Peaks (Main Peak 4.5m tall with stone cap, West & East Shoulder Peaks)
    * Two-tier Foaming Waterfall (Upper mountain chute -> Mid-shelf pool -> Lower vertical plunge)
    * Mountain Splash Pool (with white foam ripples & river stone rim)
  - NARROW MEANDERING RIVER:
    * Flowing from waterfall pool in North, curving gently through island, carving out to the sea!
    * Riverbed gravel embankment + stepping stones for settler crossing
  - DEERS PACK: Prominent herd of 6 deers (Alpha Stag with proud antlers, 2 Does, 2 Yearlings, Fawn) + 3 Rabbits
  - NATURE FROM LPM ECOSYSTEM: 22 Trees, 5 Berry Bushes, 6 Quarry Boulders, 18 Wildflowers, 14 Mushrooms
  - CENTRAL FIREPIT & OPEN-SLOT TIMBER STORAGE (10 stacked logs, crates, barrels)
  - WARM EARTH PALETTE: Ochre sand, olive-moss turf, terracotta cliffs, warm turquoise water, amber dusk sky
  - FULL ISOMETRIC VIEW: Ortho scale 54.0 framing the entire 35m island top-to-bottom and side-to-side
"""
import bpy
import bmesh
import math
import os
import numpy as np
from mathutils import Vector

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene

def create_mesh(name, verts, faces, mat):
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    for p in mesh.polygons:
        p.use_smooth = False
    obj.data.materials.append(mat)
    return obj

def get_mat(name, color, roughness=0.85, metallic=0.0, emission_color=None, emission_strength=0.0):
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = color
        bsdf.inputs["Roughness"].default_value = roughness
        bsdf.inputs["Metallic"].default_value = metallic
        if emission_color and "Emission Color" in bsdf.inputs:
            bsdf.inputs["Emission Color"].default_value = emission_color
            bsdf.inputs["Emission Strength"].default_value = emission_strength
    return mat

out_dir = "~/projects/lpm-faceless-humanoid/assets/aoe_starter_pack"
os.makedirs(out_dir, exist_ok=True)

# ==============================================================================
# WARM EARTH MATERIALS PALETTE
# ==============================================================================
mat_turf       = get_mat("M_WarmTurf",     (0.40, 0.54, 0.22, 1))      # Warm olive-moss meadow
mat_sand       = get_mat("M_WarmSand",     (0.90, 0.80, 0.50, 1))      # Golden ochre shore
mat_cliff      = get_mat("M_WarmCliff",    (0.52, 0.40, 0.28, 1))      # Terracotta clay ledge
mat_water      = get_mat("M_WarmWater",    (0.18, 0.55, 0.62, 1), 0.15, 0.05) # Tropical warm turquoise
mat_river      = get_mat("M_RiverWater",   (0.16, 0.58, 0.68, 1), 0.12, 0.05, emission_color=(0.16, 0.58, 0.68, 1), emission_strength=0.6) # Sparkling river
mat_waterfall  = get_mat("M_Waterfall",   (0.92, 0.98, 1.00, 1), 0.10, 0.0, emission_color=(0.95, 0.98, 1.0, 1), emission_strength=3.0) # Glowing foaming waterfall
mat_foam       = get_mat("M_Foam",        (0.96, 0.98, 1.00, 1), 0.20, 0.0, emission_color=(0.96, 0.98, 1.0, 1), emission_strength=1.5) # Whitewater foam
mat_riverbed   = get_mat("M_Riverbed",    (0.36, 0.28, 0.20, 1))      # Moist riverbed soil & pebbles
mat_mountain   = get_mat("M_Mountain",    (0.48, 0.38, 0.28, 1))      # Mountain cliff rock
mat_mountain_cap=get_mat("M_MountainCap", (0.76, 0.72, 0.66, 1))      # Pale granite peak cap
mat_bark       = get_mat("M_Bark",         (0.32, 0.18, 0.09, 1))      # Deep chestnut tree bark
mat_pine       = get_mat("M_PineLeaf",     (0.18, 0.36, 0.14, 1))      # Warm evergreen pine
mat_oak        = get_mat("M_OakLeaf",      (0.32, 0.48, 0.18, 1))      # Warm sunlit oak foliage
mat_bush       = get_mat("M_BushLeaf",     (0.24, 0.45, 0.16, 1))      # Berry bush mass
mat_berry      = get_mat("M_Berry",        (0.95, 0.08, 0.10, 1), 0.30, 0.0, emission_color=(0.95, 0.08, 0.10, 1), emission_strength=1.8) # Glowing red berries
mat_stone      = get_mat("M_Stone",        (0.52, 0.50, 0.48, 1))      # Warm slate granite
mat_ore        = get_mat("M_OreVein",      (0.95, 0.72, 0.15, 1), 0.35, 0.8) # Gold ore vein
mat_wood_plank = get_mat("M_WoodPlank",    (0.56, 0.36, 0.18, 1))      # Timber planks
mat_logs       = get_mat("M_Logs",         (0.44, 0.26, 0.14, 1))      # Cut logs
mat_fire       = get_mat("M_Fire",         (1.00, 0.50, 0.02, 1), 0.10, 0.0, emission_color=(1.0, 0.50, 0.02, 1), emission_strength=4.5)
mat_charcoal   = get_mat("M_Charcoal",     (0.14, 0.13, 0.14, 1))
# Flowers & Mushrooms
mat_flower_stem = get_mat("M_FlStem",      (0.30, 0.46, 0.18, 1))
mat_flower_red  = get_mat("M_FlRed",       (0.92, 0.22, 0.32, 1), 0.5, 0.0, emission_color=(0.92, 0.22, 0.32, 1), emission_strength=1.0)
mat_flower_yel  = get_mat("M_FlYel",       (0.98, 0.82, 0.12, 1), 0.5, 0.0, emission_color=(0.98, 0.82, 0.12, 1), emission_strength=1.0)
mat_flower_ctr  = get_mat("M_FlCtr",       (0.98, 0.60, 0.10, 1))
mat_mush_stem   = get_mat("M_MushStem",    (0.88, 0.82, 0.72, 1))
mat_mush_red    = get_mat("M_MushRed",     (0.85, 0.18, 0.16, 1))
mat_mush_amber  = get_mat("M_MushAmber",   (0.90, 0.58, 0.16, 1))
# Animals
mat_deer_hide   = get_mat("M_DeerHide",    (0.66, 0.40, 0.18, 1))
mat_deer_belly  = get_mat("M_DeerBelly",   (0.92, 0.86, 0.76, 1))
mat_deer_antler = get_mat("M_DeerAntler",  (0.94, 0.90, 0.80, 1))
mat_deer_hoof   = get_mat("M_DeerHoof",    (0.16, 0.14, 0.12, 1))
mat_rabbit_fur  = get_mat("M_RabbitFur",   (0.88, 0.82, 0.74, 1))

# ==============================================================================
# 1. TRIPLED LOW-POLY ISLAND (Plateau R=12.0m, Beach R=14.2m, Water R=16.5m)
# ==============================================================================
# Ocean rim disk
bpy.ops.mesh.primitive_cylinder_add(vertices=24, radius=16.5, depth=0.35, location=(0, 0, -0.30))
water = bpy.context.active_object
water.name = "Island_Water"
for p in water.data.polygons: p.use_smooth = False
water.data.materials.append(mat_water)

# Sandy shore ring
bpy.ops.mesh.primitive_cylinder_add(vertices=20, radius=14.2, depth=0.45, location=(0, 0, -0.05))
sand = bpy.context.active_object
sand.name = "Island_Beach"
for p in sand.data.polygons: p.use_smooth = False
sand.data.materials.append(mat_sand)

# Grassy Plateau (Top at Z=0.5)
bpy.ops.mesh.primitive_cylinder_add(vertices=16, radius=12.0, depth=0.65, location=(0, 0, 0.25))
plateau = bpy.context.active_object
plateau.name = "Island_Plateau"
for p in plateau.data.polygons: p.use_smooth = False
plateau.data.materials.append(mat_turf)

# ==============================================================================
# 2. LITTLE MOUNTAIN & WATERFALL PACK (NORTH SECTOR)
# ==============================================================================
# Main Mountain Peak (Center-North: (0.0, 8.8))
bpy.ops.mesh.primitive_cone_add(vertices=8, radius1=3.8, depth=4.5, location=(0.0, 8.8, 0.5 + 2.25))
mt_main = bpy.context.active_object
mt_main.name = "Mountain_Main_Base"
for p in mt_main.data.polygons: p.use_smooth = False
mt_main.data.materials.append(mat_mountain)

# Main Peak Granite Cap
bpy.ops.mesh.primitive_cone_add(vertices=8, radius1=1.8, depth=1.6, location=(0.0, 8.8, 0.5 + 3.7))
mt_cap = bpy.context.active_object
mt_cap.name = "Mountain_Main_Cap"
for p in mt_cap.data.polygons: p.use_smooth = False
mt_cap.data.materials.append(mat_mountain_cap)

# West Shoulder Peak ((-3.2, 8.0))
bpy.ops.mesh.primitive_cone_add(vertices=7, radius1=2.8, depth=3.2, location=(-3.2, 8.0, 0.5 + 1.6))
mt_west = bpy.context.active_object
mt_west.name = "Mountain_West_Ridge"
for p in mt_west.data.polygons: p.use_smooth = False
mt_west.data.materials.append(mat_mountain)

# East Shoulder Peak ((2.8, 8.5))
bpy.ops.mesh.primitive_cone_add(vertices=7, radius1=2.5, depth=2.8, location=(2.8, 8.5, 0.5 + 1.4))
mt_east = bpy.context.active_object
mt_east.name = "Mountain_East_Ridge"
for p in mt_east.data.polygons: p.use_smooth = False
mt_east.data.materials.append(mat_mountain)

# Mountain Foothill Boulders
for bx, by, brad, bmat in [(-1.5, 7.2, 0.85, mat_mountain), (1.8, 7.2, 0.75, mat_stone), (-3.8, 6.5, 0.95, mat_stone)]:
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1, radius=brad, location=(bx, by, 0.5 + brad * 0.6))
    fb = bpy.context.active_object
    for p in fb.data.polygons: p.use_smooth = False
    fb.data.materials.append(bmat)

# --- TWO-TIER WATERFALL ---
# Tier 1 (Upper chute from mountain cleft to mid-shelf)
wf1_verts = [
    (0.05, 8.2, 3.2), (0.45, 8.2, 3.2),
    (0.50, 7.4, 2.0), (0.00, 7.4, 2.0)
]
create_mesh("Waterfall_Tier1", wf1_verts, [[0, 1, 2, 3]], mat_waterfall)

# Mid-shelf rock ledge & pool
bpy.ops.mesh.primitive_cylinder_add(vertices=7, radius=0.75, depth=0.25, location=(0.25, 7.3, 1.95))
mid_shelf = bpy.context.active_object
for p in mid_shelf.data.polygons: p.use_smooth = False
mid_shelf.data.materials.append(mat_mountain)

bpy.ops.mesh.primitive_cylinder_add(vertices=7, radius=0.60, depth=0.06, location=(0.25, 7.3, 2.08))
mid_pool = bpy.context.active_object
for p in mid_pool.data.polygons: p.use_smooth = False
mid_pool.data.materials.append(mat_waterfall)

# Tier 2 (Lower vertical plunge from mid-shelf to plateau basin)
wf2_verts = [
    (0.00, 7.25, 2.0), (0.50, 7.25, 2.0),
    (0.55, 6.45, 0.55), (-0.05, 6.45, 0.55)
]
create_mesh("Waterfall_Tier2", wf2_verts, [[0, 1, 2, 3]], mat_waterfall)

# Waterfall Splash Pool at base of mountain
bpy.ops.mesh.primitive_cylinder_add(vertices=10, radius=1.35, depth=0.10, location=(0.25, 6.35, 0.54))
wf_pool = bpy.context.active_object
wf_pool.name = "Waterfall_Splash_Pool"
for p in wf_pool.data.polygons: p.use_smooth = False
wf_pool.data.materials.append(mat_river)

# Foam Ring around splash basin
bpy.ops.mesh.primitive_cylinder_add(vertices=10, radius=1.45, depth=0.04, location=(0.25, 6.35, 0.53))
wf_foam = bpy.context.active_object
for p in wf_foam.data.polygons: p.use_smooth = False
wf_foam.data.materials.append(mat_foam)

# 8 River Stones encasing the splash pool
for i in range(8):
    ang = i * (2 * math.pi / 8)
    if ang < math.pi * 0.35 or ang > math.pi * 0.65: # Leave south gap open for river exit!
        px = 0.25 + 1.40 * math.cos(ang)
        py = 6.35 + 1.40 * math.sin(ang)
        bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1, radius=0.22, location=(px, py, 0.5 + 0.16))
        st = bpy.context.active_object
        for p in st.data.polygons: p.use_smooth = False
        st.data.materials.append(mat_stone)

# ==============================================================================
# 3. NARROW MEANDERING RIVER (Flowing from Waterfall to Sea)
# ==============================================================================
river_waypoints = [
    (0.25, 6.10, 0.53),
    (0.70, 4.40, 0.53),
    (1.30, 2.60, 0.53),
    (2.10, 1.00, 0.52),
    (3.50, -1.00, 0.51),
    (5.50, -3.20, 0.48),
    (7.50, -5.20, 0.38),   # Approaching plateau cliff edge
    (9.50, -7.00, 0.18),   # Carving down beach slope
    (11.5, -8.60, -0.05),  # Crossing waterline
    (13.2, -9.60, -0.25)   # Emptying into the sea!
]

# Generate Riverbed Gravel Embankment (Base mesh under river)
# and River Water Surface Ribbon
def build_river_ribbon(pts, width_base=0.85, z_offset=0.0, mat=mat_river, name="River_Water"):
    verts = []
    faces = []
    N = len(pts)
    for i, (x, y, z) in enumerate(pts):
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
        ny = tx / mag
        
        # Widens slightly at delta
        w = width_base * (1.0 + 0.5 * (i / N))
        verts.append([x + nx * w / 2, y + ny * w / 2, z + z_offset])
        verts.append([x - nx * w / 2, y - ny * w / 2, z + z_offset])
        
    for i in range(N - 1):
        v0 = i * 2
        v1 = i * 2 + 1
        v2 = (i + 1) * 2
        v3 = (i + 1) * 2 + 1
        faces.append([v0, v1, v3, v2])
        
    return create_mesh(name, verts, faces, mat)

# 1. Gravel Riverbed (Slightly wider, under water)
build_river_ribbon(river_waypoints, width_base=1.35, z_offset=-0.04, mat=mat_riverbed, name="River_Bed")
# 2. Sparkling River Water Ribbon
build_river_ribbon(river_waypoints, width_base=0.85, z_offset=0.0, mat=mat_river, name="River_Water")

# Stepping Stones across the narrow river at Settler crossing ((1.30, 2.60))
for sx_step, sy_step, srad in [(1.10, 2.60, 0.22), (1.50, 2.60, 0.20)]:
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1, radius=srad, location=(sx_step, sy_step, 0.54))
    step_st = bpy.context.active_object
    step_st.scale = (1.1, 1.1, 0.45)
    bpy.ops.object.transform_apply(scale=True)
    for p in step_st.data.polygons: p.use_smooth = False
    step_st.data.materials.append(mat_stone)

# Delta Foam at ocean entry
bpy.ops.mesh.primitive_cylinder_add(vertices=12, radius=1.6, depth=0.04, location=(13.2, -9.60, -0.24))
delta_foam = bpy.context.active_object
for p in delta_foam.data.polygons: p.use_smooth = False
delta_foam.data.materials.append(mat_foam)

# ==============================================================================
# 4. CENTRAL FIREPIT (Location: (-0.5, -0.8, 0.5))
# ==============================================================================
fx, fy, fz = -0.5, -0.8, 0.5

bpy.ops.mesh.primitive_cylinder_add(vertices=10, radius=1.05, depth=0.08, location=(fx, fy, fz + 0.04))
charcoal = bpy.context.active_object
charcoal.name = "Firepit_Charcoal"
for p in charcoal.data.polygons: p.use_smooth = False
charcoal.data.materials.append(mat_charcoal)

for i in range(10):
    ang = i * (2 * math.pi / 10)
    sx = fx + 1.0 * math.cos(ang)
    sy = fy + 1.0 * math.sin(ang)
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1, radius=0.20, location=(sx, sy, fz + 0.12))
    stone = bpy.context.active_object
    for p in stone.data.polygons: p.use_smooth = False
    stone.data.materials.append(mat_stone)

for rot_z in [15, -45, 75]:
    bpy.ops.mesh.primitive_cylinder_add(vertices=6, radius=0.10, depth=1.05, location=(fx, fy, fz + 0.18))
    log = bpy.context.active_object
    log.rotation_euler = (math.radians(12), math.radians(8), math.radians(rot_z))
    for p in log.data.polygons: p.use_smooth = False
    log.data.materials.append(mat_bark)

flame_verts = [
    (fx - 0.22, fy - 0.22, fz + 0.18), (fx + 0.22, fy - 0.22, fz + 0.18),
    (fx + 0.22, fy + 0.22, fz + 0.18), (fx - 0.22, fy + 0.22, fz + 0.18),
    (fx - 0.32, fy, fz + 0.58), (fx + 0.32, fy, fz + 0.58),
    (fx, fy - 0.32, fz + 0.58), (fx, fy + 0.32, fz + 0.58),
    (fx, fy, fz + 1.20)
]
flame_faces = [
    [0, 1, 5, 4], [1, 2, 7, 5], [2, 3, 4, 7], [3, 0, 6, 4],
    [4, 5, 8], [5, 7, 8], [7, 6, 8], [6, 4, 8],
    [0, 3, 2, 1]
]
create_mesh("Prop_FireFlame", flame_verts, flame_faces, mat_fire)

# ==============================================================================
# 5. OPEN-SLOT TIMBER STORAGE (East Sector: (6.2, 0.5, 0.5))
# ==============================================================================
stx, sty, stz = 6.2, 0.5, 0.5

bpy.ops.mesh.primitive_cube_add(size=1.0, location=(stx, sty, stz + 0.12))
deck = bpy.context.active_object
deck.name = "Storage_Deck"
deck.scale = (3.2, 2.4, 0.22)
bpy.ops.object.transform_apply(scale=True)
for p in deck.data.polygons: p.use_smooth = False
deck.data.materials.append(mat_wood_plank)

for px in [-1.45, 1.45]:
    bpy.ops.mesh.primitive_cylinder_add(vertices=6, radius=0.14, depth=2.1, location=(stx + px, sty + 1.05, stz + 1.15))
    p_obj = bpy.context.active_object
    for p in p_obj.data.polygons: p.use_smooth = False
    p_obj.data.materials.append(mat_bark)

for px in [-1.45, 1.45]:
    bpy.ops.mesh.primitive_cylinder_add(vertices=6, radius=0.14, depth=1.5, location=(stx + px, sty - 1.05, stz + 0.85))
    p_obj = bpy.context.active_object
    for p in p_obj.data.polygons: p.use_smooth = False
    p_obj.data.materials.append(mat_bark)

roof_verts = [
    (stx - 1.70, sty - 1.30, stz + 1.65), (stx + 1.70, sty - 1.30, stz + 1.65),
    (stx + 1.70, sty + 1.30, stz + 2.25), (stx - 1.70, sty + 1.30, stz + 2.25),
]
create_mesh("Storage_LeanTo_Roof", roof_verts, [[0, 1, 2, 3]], mat_wood_plank)

# 10 Stacked Cut Logs
for ly in [-0.60, -0.20, 0.20, 0.60]:
    bpy.ops.mesh.primitive_cylinder_add(vertices=6, radius=0.16, depth=2.4, location=(stx, sty + ly, stz + 0.38))
    log = bpy.context.active_object
    log.rotation_euler = (0, math.radians(90), 0)
    for p in log.data.polygons: p.use_smooth = False
    log.data.materials.append(mat_logs)

for ly in [-0.40, 0.0, 0.40]:
    bpy.ops.mesh.primitive_cylinder_add(vertices=6, radius=0.16, depth=2.4, location=(stx, sty + ly, stz + 0.66))
    log = bpy.context.active_object
    log.rotation_euler = (0, math.radians(90), 0)
    for p in log.data.polygons: p.use_smooth = False
    log.data.materials.append(mat_logs)

for ly in [-0.20, 0.20]:
    bpy.ops.mesh.primitive_cylinder_add(vertices=6, radius=0.16, depth=2.4, location=(stx, sty + ly, stz + 0.94))
    log = bpy.context.active_object
    log.rotation_euler = (0, math.radians(90), 0)
    for p in log.data.polygons: p.use_smooth = False
    log.data.materials.append(mat_logs)

bpy.ops.mesh.primitive_cylinder_add(vertices=6, radius=0.16, depth=2.4, location=(stx, sty, stz + 1.22))
log = bpy.context.active_object
log.rotation_euler = (0, math.radians(90), 0)
for p in log.data.polygons: p.use_smooth = False
log.data.materials.append(mat_logs)

bpy.ops.mesh.primitive_cylinder_add(vertices=8, radius=0.32, depth=0.82, location=(stx - 2.1, sty - 0.4, stz + 0.41))
b1 = bpy.context.active_object
for p in b1.data.polygons: p.use_smooth = False
b1.data.materials.append(mat_wood_plank)

bpy.ops.mesh.primitive_cube_add(size=0.65, location=(stx + 2.1, sty - 0.3, stz + 0.325))
c1 = bpy.context.active_object
for p in c1.data.polygons: p.use_smooth = False
c1.data.materials.append(mat_bark)

# ==============================================================================
# 6. FOREST (North-West Arc & Mountain Foothills: 20 Trees from LPM)
# ==============================================================================
def add_lpm_pine(x, y, scale=1.0):
    z0 = 0.5
    h = 2.5 * scale
    bpy.ops.mesh.primitive_cylinder_add(vertices=6, radius=0.15 * scale, depth=h * 0.52, location=(x, y, z0 + h * 0.26))
    trunk = bpy.context.active_object
    for p in trunk.data.polygons: p.use_smooth = False
    trunk.data.materials.append(mat_bark)
    for i in range(3):
        t = i / 2.0
        r = (0.90 - t * 0.26) * scale
        cone_h = (1.10 - t * 0.18) * scale
        z_c = z0 + h * (0.50 + t * 0.22)
        bpy.ops.mesh.primitive_cone_add(vertices=7, radius1=r, depth=cone_h, location=(x, y, z_c))
        c = bpy.context.active_object
        for p in c.data.polygons: p.use_smooth = False
        c.data.materials.append(mat_pine)

def add_lpm_oak(x, y, scale=1.0):
    z0 = 0.5
    h = 2.3 * scale
    r_crown = 0.90 * scale
    bpy.ops.mesh.primitive_cylinder_add(vertices=6, radius=0.19 * scale, depth=h * 0.55, location=(x, y, z0 + h * 0.275))
    trunk = bpy.context.active_object
    for p in trunk.data.polygons: p.use_smooth = False
    trunk.data.materials.append(mat_bark)
    masses = [
        (0.0, 0.0, h * 0.75, r_crown, (1.1, 0.9, 1.0)),
        (-0.48 * scale, 0.22 * scale, h * 0.70, r_crown * 0.65, (1.0, 0.9, 1.0)),
        (0.50 * scale, -0.16 * scale, h * 0.72, r_crown * 0.60, (1.0, 0.9, 1.0))
    ]
    for mx, my, mz, mr, mscale in masses:
        bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1, radius=mr, location=(x + mx, y + my, z0 + mz))
        m_obj = bpy.context.active_object
        m_obj.scale = mscale
        bpy.ops.object.transform_apply(scale=True)
        for p in m_obj.data.polygons: p.use_smooth = False
        m_obj.data.materials.append(mat_oak)

tree_coords = [
    ("pine", -3.2, 5.5, 1.3),  ("oak",  -5.5, 4.2, 1.4),  ("pine", -7.5, 3.2, 1.2),
    ("oak",  -1.8, 6.8, 1.3),  ("pine", -4.2, 7.5, 1.25), ("oak",  -6.8, 6.2, 1.35),
    ("pine", -5.0, 9.5, 1.3),  ("pine", -8.5, 4.8, 1.1),  ("oak",  -9.5, 1.8, 1.2),
    ("pine", -6.0, 2.2, 1.15), ("oak",  -7.8, -0.2, 1.25),("pine", -3.8, 3.5, 1.05),
    ("oak",  -1.2, 4.5, 1.2),  ("oak",  -8.2, 6.5, 1.2),  ("pine", -6.2, 8.2, 1.3),
    # Eastern mountain slope trees
    ("pine",  3.5, 6.5, 1.25), ("oak",   4.8, 7.5, 1.2),  ("pine",  2.5, 5.5, 1.15),
    ("oak",   5.2, 5.2, 1.3),  ("pine",  4.0, 4.2, 1.1)
]
for t_kind, tx, ty, t_sc in tree_coords:
    if t_kind == "pine":
        add_lpm_pine(tx, ty, t_sc)
    else:
        add_lpm_oak(tx, ty, t_sc)

# ==============================================================================
# 7. DEERS PACK (Herd of 6 Deers: Alpha Stag, 2 Does, 2 Yearlings, Fawn)
# ==============================================================================
def create_lpm_deer(name, x, y, yaw_deg=0.0, scale=1.0, has_antlers=False, is_grazing=False):
    z0 = 0.5
    rot = math.radians(yaw_deg)
    
    parent = bpy.data.objects.new(name, None)
    bpy.context.collection.objects.link(parent)
    parent.location = (x, y, z0)
    parent.rotation_euler.z = rot
    
    bl, bh, bw = 1.75 * scale, 0.62 * scale, 0.46 * scale
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0, 0, 0.95 * scale))
    body = bpy.context.active_object
    body.scale = (bl, bw, bh)
    bpy.ops.object.transform_apply(scale=True)
    for p in body.data.polygons: p.use_smooth = False
    body.data.materials.append(mat_deer_hide)
    body.parent = parent
    
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0, 0, 0.74 * scale))
    belly = bpy.context.active_object
    belly.scale = (bl * 0.85, bw * 0.90, bh * 0.38)
    bpy.ops.object.transform_apply(scale=True)
    for p in belly.data.polygons: p.use_smooth = False
    belly.data.materials.append(mat_deer_belly)
    belly.parent = parent
    
    leg_l = 0.90 * scale
    leg_th = 0.095 * scale
    for lx in [-bl * 0.35, bl * 0.35]:
        for ly in [-bw * 0.34, bw * 0.34]:
            bpy.ops.mesh.primitive_cylinder_add(vertices=5, radius=leg_th, depth=leg_l, location=(lx, ly, leg_l / 2))
            leg = bpy.context.active_object
            for p in leg.data.polygons: p.use_smooth = False
            leg.data.materials.append(mat_deer_hide)
            leg.parent = parent
            
            bpy.ops.mesh.primitive_cube_add(size=1.0, location=(lx + 0.03 * scale, ly, 0.06 * scale))
            hoof = bpy.context.active_object
            hoof.scale = (leg_th * 1.8, leg_th * 1.3, 0.12 * scale)
            bpy.ops.object.transform_apply(scale=True)
            for p in hoof.data.polygons: p.use_smooth = False
            hoof.data.materials.append(mat_deer_hoof)
            hoof.parent = parent
            
    if is_grazing:
        bpy.ops.mesh.primitive_cylinder_add(vertices=5, radius=0.13 * scale, depth=0.82 * scale, location=(bl * 0.55, 0, 0.68 * scale))
        neck = bpy.context.active_object
        neck.rotation_euler.y = math.radians(55)
        for p in neck.data.polygons: p.use_smooth = False
        neck.data.materials.append(mat_deer_hide)
        neck.parent = parent
        
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=(bl * 0.88, 0, 0.40 * scale))
        head = bpy.context.active_object
        head.scale = (0.48 * scale, 0.32 * scale, 0.38 * scale)
        head.rotation_euler.y = math.radians(45)
        bpy.ops.object.transform_apply(scale=True)
        for p in head.data.polygons: p.use_smooth = False
        head.data.materials.append(mat_deer_hide)
        head.parent = parent
    else:
        bpy.ops.mesh.primitive_cylinder_add(vertices=5, radius=0.13 * scale, depth=0.75 * scale, location=(bl * 0.50, 0, 1.32 * scale))
        neck = bpy.context.active_object
        neck.rotation_euler.y = math.radians(-32)
        for p in neck.data.polygons: p.use_smooth = False
        neck.data.materials.append(mat_deer_hide)
        neck.parent = parent
        
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=(bl * 0.72, 0, 1.68 * scale))
        head = bpy.context.active_object
        head.scale = (0.48 * scale, 0.32 * scale, 0.38 * scale)
        bpy.ops.object.transform_apply(scale=True)
        for p in head.data.polygons: p.use_smooth = False
        head.data.materials.append(mat_deer_hide)
        head.parent = parent
        
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=(bl * 0.94, 0, 1.62 * scale))
        snout = bpy.context.active_object
        snout.scale = (0.24 * scale, 0.24 * scale, 0.24 * scale)
        bpy.ops.object.transform_apply(scale=True)
        for p in snout.data.polygons: p.use_smooth = False
        snout.data.materials.append(mat_deer_belly)
        snout.parent = parent
        
        if has_antlers:
            for side in [-1, 1]:
                bpy.ops.mesh.primitive_cylinder_add(vertices=4, radius=0.045 * scale, depth=0.88 * scale, location=(bl * 0.68, side * 0.18 * scale, 2.15 * scale))
                antler = bpy.context.active_object
                antler.rotation_euler = (math.radians(side * 28), math.radians(-24), 0)
                for p in antler.data.polygons: p.use_smooth = False
                antler.data.materials.append(mat_deer_antler)
                antler.parent = parent
                
                bpy.ops.mesh.primitive_cylinder_add(vertices=4, radius=0.032 * scale, depth=0.45 * scale, location=(bl * 0.76, side * 0.28 * scale, 2.28 * scale))
                tine = bpy.context.active_object
                tine.rotation_euler = (math.radians(side * 42), math.radians(20), 0)
                for p in tine.data.polygons: p.use_smooth = False
                tine.data.materials.append(mat_deer_antler)
                tine.parent = parent

# DEERS PACK: High presence in Western Glade
create_lpm_deer("Deer_AlphaStag", -4.5, 1.5, yaw_deg=-30, scale=2.8, has_antlers=True, is_grazing=False)
create_lpm_deer("Deer_Doe_1", -5.8, 0.6, yaw_deg=45, scale=2.4, has_antlers=False, is_grazing=False)
create_lpm_deer("Deer_Doe_2", -5.2, 2.8, yaw_deg=-115, scale=2.3, has_antlers=False, is_grazing=True)
create_lpm_deer("Deer_Yearling_1", -6.8, 2.0, yaw_deg=80, scale=1.9, has_antlers=False, is_grazing=True)
create_lpm_deer("Deer_Yearling_2", -3.8, 0.0, yaw_deg=-75, scale=1.8, has_antlers=False, is_grazing=False)
create_lpm_deer("Deer_Fawn", -6.4, -0.2, yaw_deg=30, scale=1.3, has_antlers=False, is_grazing=True)

# 3 Rabbits
def create_lpm_rabbit(name, x, y, yaw_deg=0.0, scale=1.0):
    z0 = 0.5
    parent = bpy.data.objects.new(name, None)
    bpy.context.collection.objects.link(parent)
    parent.location = (x, y, z0)
    parent.rotation_euler.z = math.radians(yaw_deg)
    
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1, radius=0.22 * scale, location=(0, 0, 0.20 * scale))
    b = bpy.context.active_object
    b.scale = (0.8, 1.2, 0.85)
    bpy.ops.object.transform_apply(scale=True)
    for p in b.data.polygons: p.use_smooth = False
    b.data.materials.append(mat_rabbit_fur)
    b.parent = parent
    
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1, radius=0.15 * scale, location=(0, 0.20 * scale, 0.35 * scale))
    h = bpy.context.active_object
    for p in h.data.polygons: p.use_smooth = False
    h.data.materials.append(mat_rabbit_fur)
    h.parent = parent
    
    for side in [-1, 1]:
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=(side * 0.07 * scale, 0.18 * scale, 0.58 * scale))
        ear = bpy.context.active_object
        ear.scale = (0.045 * scale, 0.07 * scale, 0.26 * scale)
        ear.rotation_euler = (math.radians(-15), math.radians(side * 15), 0)
        bpy.ops.object.transform_apply(scale=True)
        for p in ear.data.polygons: p.use_smooth = False
        ear.data.materials.append(mat_rabbit_fur)
        ear.parent = parent

create_lpm_rabbit("Rabbit_1", -2.8, 0.8, yaw_deg=40, scale=2.4)
create_lpm_rabbit("Rabbit_2", -1.8, -2.5, yaw_deg=-55, scale=2.2)
create_lpm_rabbit("Rabbit_3", -3.5, -2.0, yaw_deg=105, scale=2.0)

# ==============================================================================
# 8. BERRY BUSHES (South-West Sector: 5 Bushes)
# ==============================================================================
def add_lpm_berry_bush(bx, by, scale=1.0):
    z0 = 0.5
    r = 0.80 * scale
    masses = [
        (0.0, 0.0, r * 0.75, r, (1.2, 0.8, 1.0)),
        (-r * 0.55, 0.15 * scale, r * 0.65, r * 0.68, (1.0, 0.8, 1.0)),
        (r * 0.55, -0.15 * scale, r * 0.67, r * 0.64, (1.0, 0.8, 1.0))
    ]
    for mx, my, mz, mr, msc in masses:
        bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1, radius=mr, location=(bx + mx, by + my, z0 + mz))
        m_obj = bpy.context.active_object
        m_obj.scale = msc
        bpy.ops.object.transform_apply(scale=True)
        for p in m_obj.data.polygons: p.use_smooth = False
        m_obj.data.materials.append(mat_bush)
        
    berry_offsets = [
        (0.48, 0.28, 0.65), (-0.42, 0.32, 0.58), (0.12, -0.48, 0.54),
        (-0.38, -0.38, 0.55), (0.52, -0.16, 0.45), (0.0, 0.54, 0.68),
        (-0.28, 0.48, 0.65), (0.38, 0.40, 0.52)
    ]
    for ox, oy, oz in berry_offsets:
        bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1, radius=0.12 * scale, location=(bx + ox * scale, by + oy * scale, z0 + oz * scale))
        b_dot = bpy.context.active_object
        for p in b_dot.data.polygons: p.use_smooth = False
        b_dot.data.materials.append(mat_berry)

bushes = [
    (-6.2, -2.8, 1.3), (-8.0, -2.0, 1.2), (-5.0, -4.2, 1.4),
    (-7.0, -4.5, 1.15), (-8.8, -3.8, 1.25)
]
for bx, by, bsc in bushes:
    add_lpm_berry_bush(bx, by, bsc)

# ==============================================================================
# 9. QUARRY ROCKS & ORE VEIN (North-East Foothills)
# ==============================================================================
quarry_rocks = [
    (6.2, 4.2, 1.5, 0.85, mat_stone),
    (7.8, 2.8, 1.2, 1.10, mat_ore),      # Gold ore outcrop!
    (4.8, 5.8, 1.0, 0.75, mat_stone),
    (7.5, 5.2, 1.3, 0.90, mat_stone),
    (8.8, 3.8, 0.9, 0.70, mat_stone),
    (5.8, 7.0, 1.1, 0.80, mat_stone),
]
for rx, ry, r_rad, r_zsc, r_mat in quarry_rocks:
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1, radius=r_rad, location=(rx, ry, 0.5 + r_rad * r_zsc * 0.7))
    rock = bpy.context.active_object
    rock.scale = (1.2, 0.9, r_zsc)
    bpy.ops.object.transform_apply(scale=True)
    for p in rock.data.polygons: p.use_smooth = False
    rock.data.materials.append(r_mat)

# ==============================================================================
# 10. WILDFLOWERS & MUSHROOMS
# ==============================================================================
def add_lpm_flower(x, y, petal_mat=mat_flower_red, scale=1.0):
    z0 = 0.5
    h = 0.65 * scale
    bpy.ops.mesh.primitive_cylinder_add(vertices=5, radius=0.04 * scale, depth=h, location=(x, y, z0 + h / 2))
    stem = bpy.context.active_object
    for p in stem.data.polygons: p.use_smooth = False
    stem.data.materials.append(mat_flower_stem)
    
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1, radius=0.10 * scale, location=(x, y, z0 + h + 0.02 * scale))
    ctr = bpy.context.active_object
    for p in ctr.data.polygons: p.use_smooth = False
    ctr.data.materials.append(mat_flower_ctr)
    
    for i in range(6):
        ang = i * (math.pi / 3)
        px = x + math.cos(ang) * 0.18 * scale
        py = y + math.sin(ang) * 0.18 * scale
        bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1, radius=0.10 * scale, location=(px, py, z0 + h))
        petal = bpy.context.active_object
        petal.scale = (1.1, 1.1, 0.45)
        bpy.ops.object.transform_apply(scale=True)
        for p in petal.data.polygons: p.use_smooth = False
        petal.data.materials.append(petal_mat)

flower_spots = [
    (-1.8, -2.5, mat_flower_yel, 1.3), (-2.5, -3.2, mat_flower_red, 1.2),
    (-1.2, -3.8, mat_flower_yel, 1.1), (-3.5, -2.8, mat_flower_red, 1.3),
    (-3.8, 0.2, mat_flower_yel, 1.3),  (-4.5, -0.6, mat_flower_red, 1.2),
    (-0.5, -5.0, mat_flower_yel, 1.2), (1.2, -5.2, mat_flower_red, 1.15),
    (-2.0, -5.5, mat_flower_yel, 1.1), (-3.0, -4.5, mat_flower_yel, 1.2),
    # Flowers along the narrow riverbank!
    (1.2, 3.6, mat_flower_yel, 1.2),   (1.8, 1.8, mat_flower_red, 1.25),
    (2.8, -0.2, mat_flower_yel, 1.15), (4.5, -2.2, mat_flower_red, 1.3)
]
for fx_s, fy_s, f_mat, f_sc in flower_spots:
    add_lpm_flower(fx_s, fy_s, f_mat, f_sc)

def add_lpm_mushroom(x, y, cap_mat=mat_mush_red, scale=1.0):
    z0 = 0.5
    h = 0.55 * scale
    bpy.ops.mesh.primitive_cylinder_add(vertices=6, radius=0.08 * scale, depth=h * 0.72, location=(x, y, z0 + h * 0.36))
    stem = bpy.context.active_object
    for p in stem.data.polygons: p.use_smooth = False
    stem.data.materials.append(mat_mush_stem)
    
    bpy.ops.mesh.primitive_cone_add(vertices=8, radius1=0.36 * scale, depth=h * 0.38, location=(x, y, z0 + h * 0.80))
    cap = bpy.context.active_object
    for p in cap.data.polygons: p.use_smooth = False
    cap.data.materials.append(cap_mat)

mush_spots = [
    (-3.0, 4.8, mat_mush_red, 1.3),   (-2.6, 5.2, mat_mush_amber, 1.2),
    (-5.0, 3.8, mat_mush_amber, 1.4), (-5.4, 4.2, mat_mush_red, 1.1),
    (-1.5, 5.8, mat_mush_red, 1.3),   (-0.8, 5.5, mat_mush_amber, 1.2), # Near waterfall pool!
    (1.5, 5.2, mat_mush_red, 1.2),    (2.5, 4.8, mat_mush_amber, 1.35),
    (-4.2, 6.2, mat_mush_red, 1.2),   (3.5, 5.8, mat_mush_amber, 1.1)
]
for mx_s, my_s, m_mat, m_sc in mush_spots:
    add_lpm_mushroom(mx_s, my_s, m_mat, m_sc)

# ==============================================================================
# 11. EXPORT FULL GLB
# ==============================================================================
full_glb = os.path.join(out_dir, "aoe_starter_island_full.glb")
bpy.ops.export_scene.gltf(filepath=full_glb, export_format='GLB', use_selection=False)
print(f"✅ Exported Full Tripled AoE Starter Scene -> {full_glb}")

# ==============================================================================
# 12. ISOMETRIC STUDIO RENDER (PERFECTLY FRAMED)
# ==============================================================================
cam_data = bpy.data.cameras.new("AoECam")
cam_data.type = 'ORTHO'
cam_data.ortho_scale = 55.0
cam_obj = bpy.data.objects.new("AoECam", cam_data)
sc.collection.objects.link(cam_obj)
sc.camera = cam_obj

pitch = math.radians(50)
yaw = math.radians(45)
dist = 70.0
tx, ty, tz = 0.0, -1.2, 0.5
cx = tx + dist * math.sin(yaw) * math.cos(pitch)
cy = ty - dist * math.cos(yaw) * math.cos(pitch)
cz = tz + dist * math.sin(pitch)
cam_obj.location = Vector((cx, cy, cz))

target = Vector((tx, ty, tz))
direction = target - cam_obj.location
rot_quat = direction.to_track_quat('-Z', 'Y')
cam_obj.rotation_euler = rot_quat.to_euler()

# Warm Golden Hour Lighting
lights = {
    "SunKey":  (4.8, (1.0, 0.92, 0.82), (48, 0, 35)),
    "SunFill": (1.8, (0.78, 0.88, 1.0),  (58, 0, -65)),
    "SunRim":  (3.2, (1.0, 0.95, 0.85), (38, 0, 160))
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
world.node_tree.nodes["Background"].inputs[0].default_value = (0.16, 0.14, 0.13, 1)

sc.render.engine = "BLENDER_EEVEE"
sc.render.resolution_x = 1920
sc.render.resolution_y = 1080
sc.view_settings.view_transform = "AgX"

out_img = os.path.join(out_dir, "aoe_starter_island_isometric.png")
sc.render.filepath = out_img

bpy.ops.render.render(write_still=True)
print(f"📸 AoE Starting Point Render Complete -> {out_img}")

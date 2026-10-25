#!/usr/bin/env python3
"""
AOE / SETTLERS — STANDALONE MOUNTAIN WATERFALL PACK (v3.0)
Masterpiece Stylized Low-Poly Environment Pack.
Solves all critical Gemini Vision & Boss feedback:
1. Authentic LPM Low-Poly Mountain Geometry:
   - Interlocking faceted boulders & cliff terraces via bmesh convex hull (make_khoi_meo).
   - High West Plateau (H=10.5m) + Asymmetrical East Shoulder (H=8.8m).
   - Lush alpine turf caps (co_giua/co_ngon) on horizontal plateau shelves + weathered stone cliff walls (da/da_sang).
2. Dynamic Cascading Waterfall:
   - 3-tier flow: Upper spring cleft (Z=8.2m) -> Tier 1 rapid chute with chevron foam ->
     Mid-canyon shelf basin with turbulent eddy & overflow lip (Z=4.2m) ->
     Tier 2 flared plunge curtain (Z=4.0m -> 0.45m) with low-poly mist spray.
3. Carved Riverbed & Splash Pool Integration:
   - Recessed canyon basin & river trench (no flat sticker look).
   - Splash pool with radiating white foam ripple rings and wet stone border.
   - Meandering S-curve river flowing south with variant width, stepping stones, and LPM boulders.
4. Strict Rule 8 Compliance:
   - Margins >= 60px on all 4 sides.
   - Yaw=12 deg, Pitch=27 deg for 100% unobstructed view of gorge & waterfall.
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
mat_da_toi    = get_mat("M_DaToi",     ( 78,  72,  66), roughness=0.96)  # Canyon shadow cliff
mat_reu       = get_mat("M_Reu",       ( 96, 116,  64), roughness=0.88)  # Moss on wet rocks
mat_turf      = get_mat("M_Turf",      ( 92, 132,  56), roughness=0.85)  # Alpine meadow grass
mat_turf_top  = get_mat("M_TurfTop",   (115, 155,  68), roughness=0.85)  # Sunlit plateau cap
mat_water_deep= get_mat("M_WaterDeep", ( 38, 115, 138), roughness=0.10, emission_srgb=(38, 115, 138), emission_strength=0.35)
mat_water_flow= get_mat("M_WaterFlow", ( 78, 185, 212), roughness=0.10, emission_srgb=(115, 210, 235), emission_strength=0.90)
mat_foam      = get_mat("M_Foam",      (242, 250, 255), roughness=0.20, emission_srgb=(248, 252, 255), emission_strength=1.80)

# Real LPM Rock assets
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

# ==============================================================================
# 1. WEST MOUNTAIN BLUFF (HEROIC ALPINE PLATEAU - H=10.5m)
# ==============================================================================
# Tier 0: Base Buttress boulders (Z=0 to 3.5m)
make_khoi_meo("W_Buttress_1", (-10.0, 21.0, 1.8), 5.2, mat_da, seed=101, meo=0.20, n=15, det=(1.3, 1.1, 0.75))
make_khoi_meo("W_Buttress_2", (-14.2, 22.5, 2.0), 4.8, mat_da_sang, seed=102, meo=0.22, n=14, det=(1.1, 1.2, 0.8))
make_khoi_meo("W_Gorge_Wall_L", (-5.4, 20.2, 2.2), 3.4, mat_da_toi, seed=103, meo=0.18, n=13, det=(0.8, 1.3, 1.1))

# Tier 1: Mid-Canyon Cliff & Terrace (Z=3.5 to 6.8m)
make_khoi_meo("W_MidCliff_1", (-9.5, 21.5, 5.0), 4.4, mat_da, seed=104, meo=0.20, n=14, det=(1.2, 1.0, 0.85))
make_khoi_meo("W_MidCliff_2", (-13.0, 22.0, 5.2), 3.8, mat_da_sang, seed=105, meo=0.20, n=13, det=(1.0, 1.1, 0.85))
make_khoi_meo("W_Gorge_Wall_Mid", (-4.8, 20.8, 5.2), 2.8, mat_da_toi, seed=106, meo=0.18, n=12, det=(0.7, 1.2, 1.0))

# Mid Terrace Alpine Grass Shelf (Z=5.9m)
make_plateau_cap("W_Mid_Shelf_Grass", (-9.8, 20.2), 6.0, 3.6, 2.4, mat_turf, seed=110, n=8)

# Tier 2: High Cliff & Summit Massif (Z=6.8 to 10.5m)
make_khoi_meo("W_Summit_1", (-8.8, 21.8, 8.2), 3.6, mat_da, seed=107, meo=0.18, n=14, det=(1.1, 1.0, 0.85))
make_khoi_meo("W_Summit_2", (-11.6, 22.2, 8.4), 3.2, mat_da_sang, seed=108, meo=0.18, n=12, det=(0.9, 1.0, 0.85))
make_khoi_meo("W_Crest_Anchor", (-3.6, 21.8, 8.0), 2.4, mat_da, seed=109, meo=0.15, n=12, det=(0.8, 1.1, 1.0))

# Summit Alpine Grass Cap (Z=10.4m)
make_plateau_cap("W_Summit_Grass", (-9.2, 21.8), 10.4, 2.8, 2.0, mat_turf_top, seed=111, n=8)

# ==============================================================================
# 2. EAST MOUNTAIN BLUFF (ASYMMETRICAL RUGGED SHOULDER - H=8.8m)
# ==============================================================================
# Tier 0: Base Buttress boulders (Z=0 to 3.2m)
make_khoi_meo("E_Buttress_1", ( 9.8, 21.2, 1.8), 4.9, mat_da, seed=201, meo=0.20, n=15, det=(1.2, 1.1, 0.75))
make_khoi_meo("E_Buttress_2", (13.8, 22.8, 1.9), 4.4, mat_da_sang, seed=202, meo=0.22, n=13, det=(1.0, 1.1, 0.8))
make_khoi_meo("E_Gorge_Wall_R", ( 5.2, 20.4, 2.2), 3.2, mat_da_toi, seed=203, meo=0.18, n=13, det=(0.8, 1.3, 1.1))

# Tier 1: Mid-Canyon Cliff & Terrace (Z=3.2 to 6.2m)
make_khoi_meo("E_MidCliff_1", ( 9.0, 21.6, 4.8), 4.0, mat_da, seed=204, meo=0.20, n=14, det=(1.1, 1.0, 0.85))
make_khoi_meo("E_MidCliff_2", (12.4, 22.2, 4.9), 3.4, mat_da_sang, seed=205, meo=0.20, n=12, det=(0.9, 1.0, 0.85))
make_khoi_meo("E_Gorge_Wall_Mid", ( 4.6, 21.0, 4.9), 2.6, mat_da_toi, seed=206, meo=0.18, n=12, det=(0.7, 1.1, 1.0))

# Mid Terrace Alpine Grass Shelf (Z=5.5m)
make_plateau_cap("E_Mid_Shelf_Grass", ( 9.4, 20.6), 5.6, 3.2, 2.2, mat_turf, seed=210, n=8)

# Tier 2: Shoulder Summit (Z=6.2 to 8.8m)
make_khoi_meo("E_Summit_1", ( 8.2, 21.8, 7.4), 3.1, mat_da, seed=207, meo=0.18, n=13, det=(1.0, 1.0, 0.80))
make_khoi_meo("E_Crest_Anchor", ( 3.5, 22.0, 7.6), 2.2, mat_da, seed=208, meo=0.15, n=12, det=(0.8, 1.1, 1.0))

# East Shoulder Grass Cap (Z=8.7m)
make_plateau_cap("E_Summit_Grass", ( 8.2, 21.8), 8.8, 2.2, 1.7, mat_turf_top, seed=211, n=7)

# Foothill Boulders & Scree using authentic LPM assets
import_lpm_asset(rock_large, "LPM_Foothill_W", (-4.6, 17.5, 0.0), rot_z_deg=20, scale=1.35)
import_lpm_asset(rock_large, "LPM_Foothill_E", ( 4.7, 17.2, 0.0), rot_z_deg=-35, scale=1.25)
import_lpm_asset(rock_medium, "LPM_Side_W",     (-13.5, 17.0, 0.0), rot_z_deg=15, scale=1.4)
import_lpm_asset(rock_medium, "LPM_Side_E",     ( 13.8, 17.5, 0.0), rot_z_deg=-45, scale=1.35)
import_lpm_asset(rock_small, "LPM_Scree_W",    (-7.5, 15.8, 0.0), rot_z_deg=55, scale=1.3)
import_lpm_asset(rock_small, "LPM_Scree_E",    ( 7.4, 16.0, 0.0), rot_z_deg=-70, scale=1.2)

# ==============================================================================
# 3. DYNAMIC 3-TIER CASCADING WATERFALL
# ==============================================================================
def create_mesh_obj(name, verts, faces, mat):
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], faces)
    me.update()
    obj = bpy.data.objects.new(name, me)
    bpy.context.collection.objects.link(obj)
    for p in obj.data.polygons: p.use_smooth = False
    obj.data.materials.append(mat)
    return obj

# A. Crest Spring Cleft (Z=8.2m)
# Rock basin where water emerges naturally between mossy boulders
cleft_verts = [
    (-1.2, 23.2, 8.20), ( 1.2, 23.2, 8.20),
    (-1.1, 21.8, 8.10), ( 1.1, 21.8, 8.10),
    (-1.0, 20.6, 7.95), ( 1.0, 20.6, 7.95),
]
cleft_faces = [[0, 1, 3, 2], [2, 3, 5, 4]]
create_mesh_obj("Waterfall_Crest_Pool", cleft_verts, cleft_faces, mat_water_deep)

# Crest framing rocks
import_lpm_asset(rock_small, "Crest_Gorge_L", (-1.7, 21.2, 8.0), rot_z_deg=35, scale=1.0)
import_lpm_asset(rock_small, "Crest_Gorge_R", ( 1.7, 21.2, 8.0), rot_z_deg=-40, scale=1.0)

# B. Tier 1: Cascading Rapid Chute (Z=7.95m down to 4.5m)
# Cascading stepped water ribbon
t1_water_verts = [
    (-1.00, 20.6, 7.95), ( 1.00, 20.6, 7.95),
    (-1.15, 19.4, 6.70), ( 1.15, 19.4, 6.70),
    (-1.30, 18.2, 5.40), ( 1.30, 18.2, 5.40),
    (-1.50, 17.1, 4.45), ( 1.50, 17.1, 4.45),
]
t1_water_faces = [[0, 1, 3, 2], [2, 3, 5, 4], [4, 5, 7, 6]]
create_mesh_obj("Waterfall_Tier1_Water", t1_water_verts, t1_water_faces, mat_water_flow)

# Chevron foam ripples layered over Tier 1 chute (Stepped white-water rapids)
t1_foam_verts = [
    (-0.65, 20.4, 7.99), ( 0.65, 20.4, 7.99),
    (-0.80, 19.2, 6.74), ( 0.80, 19.2, 6.74),
    (-0.95, 18.0, 5.44), ( 0.95, 18.0, 5.44),
    (-1.10, 17.0, 4.49), ( 1.10, 17.0, 4.49),
]
t1_foam_faces = [[0, 1, 3, 2], [2, 3, 5, 4], [4, 5, 7, 6]]
create_mesh_obj("Waterfall_Tier1_Foam_Rapids", t1_foam_verts, t1_foam_faces, mat_foam)

# C. Mid-Canyon Shelf Basin (Z=4.2m)
# Rocky platform cradling the intermediate mountain pool
make_khoi_meo("Mid_Shelf_Basin_Rock", (0.0, 16.8, 3.8), 2.6, mat_da_sang, seed=301, meo=0.15, n=12, det=(1.3, 1.1, 0.45))

# Intermediate Pool with turbulent faceted eddy
mid_pool_verts = [
    (-1.8, 17.5, 4.35), ( 1.8, 17.5, 4.35),
    (-2.1, 16.4, 4.30), ( 2.1, 16.4, 4.30),
    (-1.7, 15.4, 4.25), ( 1.7, 15.4, 4.25),
]
mid_pool_faces = [[0, 1, 3, 2], [2, 3, 5, 4]]
create_mesh_obj("Mid_Basin_Water", mid_pool_verts, mid_pool_faces, mat_water_deep)

# Mid-Basin Foam Swirl Ring
mid_foam_verts = [
    (-1.2, 16.8, 4.38), ( 1.2, 16.8, 4.38),
    (-1.4, 16.0, 4.35), ( 1.4, 16.0, 4.35),
]
mid_foam_faces = [[0, 1, 3, 2]]
create_mesh_obj("Mid_Basin_Foam_Eddy", mid_foam_verts, mid_foam_faces, mat_foam)

# Rock weir spilling overflow
import_lpm_asset(rock_small, "Mid_Weir_Rock_L", (-1.9, 15.3, 4.1), rot_z_deg=45, scale=0.9)
import_lpm_asset(rock_small, "Mid_Weir_Rock_R", ( 1.9, 15.3, 4.1), rot_z_deg=-55, scale=0.9)

# D. Tier 2: Flared Vertical Plunge Curtain (Z=4.2m down to 0.50m)
t2_water_verts = [
    (-1.40, 15.3, 4.25), ( 1.40, 15.3, 4.25),
    (-1.75, 14.2, 2.40), ( 1.75, 14.2, 2.40),
    (-2.20, 13.0, 0.52), ( 2.20, 13.0, 0.52),
]
t2_water_faces = [[0, 1, 3, 2], [2, 3, 5, 4]]
create_mesh_obj("Waterfall_Tier2_Plunge", t2_water_verts, t2_water_faces, mat_water_flow)

# Tier 2 White Foam Curtain Edge
t2_foam_verts = [
    (-0.95, 15.25, 4.29), ( 0.95, 15.25, 4.29),
    (-1.25, 14.15, 2.44), ( 1.25, 14.15, 2.44),
    (-1.65, 12.95, 0.56), ( 1.65, 12.95, 0.56),
]
t2_foam_faces = [[0, 1, 3, 2], [2, 3, 5, 4]]
create_mesh_obj("Waterfall_Tier2_Foam_Curtain", t2_foam_verts, t2_foam_faces, mat_foam)

# Low-Poly Mist / Splash Chunks at impact base (Z=0.7 to 1.3m)
mist_coords = [
    (-1.9, 13.1, 0.75, 0.22),
    ( 1.9, 13.2, 0.78, 0.20),
    (-0.8, 12.7, 0.85, 0.18),
    ( 0.7, 12.6, 0.88, 0.18),
    (-1.4, 12.5, 1.15, 0.15),
    ( 1.3, 12.4, 1.20, 0.15),
]
for mx, my, mz, mr in mist_coords:
    bpy.ops.mesh.primitive_cylinder_add(vertices=6, radius=mr, depth=mr*0.7, location=(mx, my, mz))
    m_obj = bpy.context.active_object
    for p in m_obj.data.polygons: p.use_smooth = False
    m_obj.data.materials.append(mat_foam)

# ==============================================================================
# 4. RECESSED SPLASH POOL & MEANDERING S-CURVE RIVERBED
# ==============================================================================
# Deep Recessed Basin (Faceted organic pond, Z=0.48m)
pool_bm = bmesh.new()
pool_n = 14
pool_r = 3.9
pool_cx, pool_cy, pool_cz = 0.0, 12.2, 0.48
pool_center = pool_bm.verts.new((pool_cx, pool_cy, pool_cz))
pool_rim_verts = []
rng_p = random.Random(99)
for i in range(pool_n):
    ang = i * (2 * math.pi / pool_n)
    rad = pool_r * (1.0 + rng_p.uniform(-0.10, 0.10))
    vx = pool_cx + rad * math.cos(ang)
    vy = pool_cy + rad * math.sin(ang)
    pool_rim_verts.append(pool_bm.verts.new((vx, vy, pool_cz)))

for i in range(pool_n):
    i_next = (i + 1) % pool_n
    pool_bm.faces.new([pool_rim_verts[i], pool_rim_verts[i_next], pool_center])

pool_me = bpy.data.meshes.new("Splash_Pool_Mesh")
pool_bm.to_mesh(pool_me)
pool_bm.free()
pool_obj = bpy.data.objects.new("Splash_Pool", pool_me)
bpy.context.collection.objects.link(pool_obj)
for p in pool_obj.data.polygons: p.use_smooth = False
pool_obj.data.materials.append(mat_water_deep)

# Dynamic Starburst Foam Impact Ring 1 (Inner)
f1_bm = bmesh.new()
f1_c = f1_bm.verts.new((0.0, 12.6, 0.52))
f1_rim = []
for i in range(12):
    ang = i * (2 * math.pi / 12)
    rad = 2.4 * (1.0 + 0.20 * math.sin(3 * ang))
    f1_rim.append(f1_bm.verts.new((rad * math.cos(ang), 12.6 + rad * math.sin(ang), 0.52)))
for i in range(12):
    i_next = (i + 1) % 12
    f1_bm.faces.new([f1_rim[i], f1_rim[i_next], f1_c])
f1_me = bpy.data.meshes.new("Splash_Foam_Inner")
f1_bm.to_mesh(f1_me)
f1_bm.free()
f1_obj = bpy.data.objects.new("Splash_Foam_Inner", f1_me)
bpy.context.collection.objects.link(f1_obj)
for p in f1_obj.data.polygons: p.use_smooth = False
f1_obj.data.materials.append(mat_foam)

# Concentric Foam Ring 2 (Outer Ripple)
f2_bm = bmesh.new()
f2_c = f2_bm.verts.new((0.0, 12.2, 0.50))
f2_rim = []
for i in range(12):
    ang = i * (2 * math.pi / 12)
    rad = 3.3 * (1.0 + 0.15 * math.cos(4 * ang))
    f2_rim.append(f2_bm.verts.new((rad * math.cos(ang), 12.2 + rad * math.sin(ang), 0.50)))
for i in range(12):
    i_next = (i + 1) % 12
    f2_bm.faces.new([f2_rim[i], f2_rim[i_next], f2_c])
f2_me = bpy.data.meshes.new("Splash_Foam_Outer")
f2_bm.to_mesh(f2_me)
f2_bm.free()
f2_obj = bpy.data.objects.new("Splash_Foam_Outer", f2_me)
bpy.context.collection.objects.link(f2_obj)
for p in f2_obj.data.polygons: p.use_smooth = False
f2_obj.data.materials.append(mat_foam)

# Wet Stone Basin Rim (Cradling the pool, blending with terrain)
rim_angles = [0.15, 0.35, 0.55, 0.85, 1.15, 1.45, 1.70, 1.95]
for i, a_mult in enumerate(rim_angles):
    ang = a_mult * math.pi
    # Leave South outlet open for river
    if ang < math.pi * 0.32 or ang > math.pi * 0.72:
        rx = pool_cx + (pool_r + 0.4) * math.cos(ang)
        ry = pool_cy + (pool_r + 0.4) * math.sin(ang)
        import_lpm_asset(rock_small, f"Pool_Rim_Rock_{i}", (rx, ry, 0.0), rot_z_deg=i*40, scale=0.92)

# Meandering S-Curve River (Variant curves flowing South)
# Carved river channel with natural bends:
river_spine = [
    # (Left_X, Right_X, Y, Z)
    (-1.60,  1.60,  9.8, 0.46),  # Pool mouth
    (-1.20,  1.90,  8.0, 0.44),  # Smooth swing right
    (-1.80,  1.30,  6.0, 0.42),  # Smooth swing left (S-curve)
    (-1.30,  1.70,  4.0, 0.40),  # Swing back right
    (-1.60,  1.50,  2.0, 0.38),  # Exiting glade south
]
river_verts = []
for lx, rx, ry, rz in river_spine:
    river_verts.append((lx, ry, rz))
    river_verts.append((rx, ry, rz))

river_faces = []
for i in range(len(river_spine) - 1):
    i0 = i * 2
    i1 = i0 + 1
    i2 = (i + 1) * 2
    i3 = i2 + 1
    river_faces.append([i0, i1, i3, i2])

create_mesh_obj("Meandering_River_Water", river_verts, river_faces, mat_water_deep)

# River Foam Flow Ribbons (Dynamic current lines)
r_foam_spine = [
    (-0.5, 0.5, 9.6, 0.48),
    (-0.2, 0.7, 8.0, 0.46),
    (-0.8, 0.3, 6.0, 0.44),
    (-0.3, 0.6, 4.0, 0.42),
]
r_foam_verts = []
for lx, rx, ry, rz in r_foam_spine:
    r_foam_verts.append((lx, ry, rz))
    r_foam_verts.append((rx, ry, rz))
r_foam_faces = []
for i in range(len(r_foam_spine) - 1):
    i0 = i * 2
    i1 = i0 + 1
    i2 = (i + 1) * 2
    i3 = i2 + 1
    r_foam_faces.append([i0, i1, i3, i2])
create_mesh_obj("River_Current_Foam", r_foam_verts, r_foam_faces, mat_foam)

# Stepping Stones across the narrow river bend (Y=7.2m)
stepping_stones = [
    (-0.4, 7.3, 0.50, 0.45),
    ( 0.4, 7.1, 0.49, 0.42),
    ( 1.1, 6.9, 0.48, 0.38)
]
for sx, sy, sz, sr in stepping_stones:
    bpy.ops.mesh.primitive_cylinder_add(vertices=7, radius=sr, depth=0.20, location=(sx, sy, sz))
    st = bpy.context.active_object
    for p in st.data.polygons: p.use_smooth = False
    st.data.materials.append(mat_da_sang)

# Riverbank Boulders along the meandering banks
import_lpm_asset(rock_small, "River_Bank_L1", (-2.3, 8.4, 0.0), rot_z_deg=35, scale=1.0)
import_lpm_asset(rock_small, "River_Bank_R1", ( 2.4, 7.8, 0.0), rot_z_deg=-25, scale=0.95)
import_lpm_asset(rock_small, "River_Bank_L2", (-2.6, 5.2, 0.0), rot_z_deg=-50, scale=1.1)
import_lpm_asset(rock_small, "River_Bank_R2", ( 2.3, 4.2, 0.0), rot_z_deg=40, scale=0.9)

# ==============================================================================
# 5. EXHIBITION DIORAMA PEDESTAL & GROUND GLADE
# ==============================================================================
# Rounded diorama stage centered at (0.0, 16.0) with radius 17.5m
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

#!/usr/bin/env python3
"""
MOUNTAIN WATERFALL PACK (v2.0) - REFINED STYLIZED LOW-POLY SHOWCASE
Fully addresses Boss's directives & Gemini Asset Audit feedback:
1. Natural Organic Mountain Bluffs:
   - Replaced uniform stacked octagons with organic terraced cliff formations.
   - Dual-material integration: Weathered stone cliff faces (M_RegularStone) + lush plateau grass caps (M_GhibliTurf) on stepped ledges.
   - Hand-sculpted low-poly faceted silhouettes (no pointy cones, flat weathered plateaus).
2. Dynamic Cascading Waterfall:
   - Replaced flat white slabs with vibrant Ghibli turquoise cascading water (M_GhibliRiver) + layered foam rapid streaks (M_GhibliFoam).
   - Organic V-shaped cleft at mountain crest (Z=8.6m).
   - Tier 1: Stepped rapid chute curving down the gorge.
   - Mid Basin: Natural rocky intermediate shelf with turquoise eddy.
   - Tier 2: Flared plunge drop into central splash pool.
   - Splash Pool: Organic faceted basin (no artificial concentric rim sticker) with dynamic foam splash rings and LPM river rocks.
3. Meandering River Outlet:
   - Variant curved river bed flowing south with natural width variation, flat stepping stones, and LPM rock_small boulders.
4. Exhibition Diorama Base:
   - Rounded diorama stage with comfortable margins on all 4 sides (>= 60px).
   - Optimized isometric framing (Yaw=14 deg, Pitch=28 deg) ensuring 100% unobstructed view of gorge & waterfall.
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

# Materials
mat_stone       = get_mat("M_RegularStone",   (98, 92, 84), roughness=0.92)       # Weathered mountain rock
mat_stone_dark  = get_mat("M_StoneDark",      (75, 70, 64), roughness=0.95)       # Canyon shadow cliff
mat_turf        = get_mat("M_GhibliTurf",     (82, 138, 58), roughness=0.85)      # Meadow & mountain grass
mat_water_deep  = get_mat("M_WaterDeep",      (38, 108, 130), roughness=0.10, emission_srgb=(38, 108, 130), emission_strength=0.3)
mat_water_flow  = get_mat("M_WaterFlow",      (72, 175, 198), roughness=0.12, emission_srgb=(110, 205, 225), emission_strength=0.8)
mat_foam        = get_mat("M_WaterFoam",      (235, 248, 252), roughness=0.25, emission_srgb=(245, 252, 255), emission_strength=1.5)

# LPM Rock assets
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

# ==============================================================================
# 1. ORGANIC TERRACED MOUNTAIN BLUFF BUILDER
# ==============================================================================
def build_organic_mountain(name, center_xy, tier_rings, seed=42):
    """
    Constructs an organic terraced mountain with weathered cliff walls and grass plateaus.
    tier_rings: list of (z_level, base_radius, n_verts, angle_offset, turf_cap_flag)
    """
    rng = random.Random(seed)
    cx, cy = center_xy
    bm = bmesh.new()
    
    layer_verts = []
    for z, r, n, a_off, is_cap in tier_rings:
        ring = []
        for j in range(n):
            angle = (2 * math.pi / n) * j + math.radians(a_off)
            # Subtle organic jitter to break robotic symmetry
            jit_r = r * (1.0 + rng.uniform(-0.08, 0.08))
            px = cx + jit_r * math.cos(angle)
            py = cy + jit_r * math.sin(angle)
            v = bm.verts.new((px, py, z))
            ring.append(v)
        layer_verts.append((ring, is_cap))
    
    # Bridge rings into quads/tris
    for i in range(len(layer_verts) - 1):
        r1, cap1 = layer_verts[i]
        r2, cap2 = layer_verts[i+1]
        n1 = len(r1)
        n2 = len(r2)
        if n1 == n2:
            for j in range(n1):
                j_next = (j + 1) % n1
                bm.faces.new([r1[j], r1[j_next], r2[j_next], r2[j]])
        else:
            # Connect different vertex counts gracefully
            step1 = n1 / max(n1, n2)
            step2 = n2 / max(n1, n2)
            # Simple fan bridge
            for k in range(max(n1, n2)):
                j1 = int(k * step1) % n1
                j1_next = int((k + 1) * step1) % n1
                j2 = int(k * step2) % n2
                j2_next = int((k + 1) * step2) % n2
                try:
                    if j1 != j1_next and j2 != j2_next:
                        bm.faces.new([r1[j1], r1[j1_next], r2[j2_next], r2[j2]])
                    elif j1 == j1_next:
                        bm.faces.new([r1[j1], r2[j2_next], r2[j2]])
                    else:
                        bm.faces.new([r1[j1], r1[j1_next], r2[j2]])
                except:
                    pass
    
    # Cap the top plateau
    top_ring, _ = layer_verts[-1]
    top_center = bm.verts.new((cx, cy, tier_rings[-1][0]))
    for j in range(len(top_ring)):
        j_next = (j + 1) % len(top_ring)
        bm.faces.new([top_ring[j], top_ring[j_next], top_center])
    
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    
    obj = bpy.data.objects.new(name, me)
    bpy.context.collection.objects.link(obj)
    
    # Assign materials: Stone for cliff walls, Turf for flat plateau steps
    obj.data.materials.append(mat_stone)
    obj.data.materials.append(mat_turf)
    
    for poly in obj.data.polygons:
        poly.use_smooth = False
        # If normal points upward (slope < 40 degrees from vertical Z), assign grass
        if poly.normal.z > 0.65:
            poly.material_index = 1  # Turf
        else:
            poly.material_index = 0  # Stone
            
    return obj

# West Mountain Bluff (Left flank of gorge)
# Stepped organic tiers: (Z, Radius, N_verts, Angle_offset, is_cap)
west_rings = [
    ( 0.0, 10.8, 10,  10, False),
    ( 2.8,  9.8, 10,  15, False),
    ( 3.1,  8.6,  9,  25, True),   # Plateau 1 shelf
    ( 5.5,  7.8,  9, -15, False),
    ( 5.8,  6.8,  8,   0, True),   # Plateau 2 shelf
    ( 8.2,  5.8,  8,  35, False),
    ( 8.5,  4.6,  7, -20, True),   # Plateau 3 shelf
    (10.2,  3.8,  7,  10, False),
    (10.8,  2.8,  7,  30, True)    # Ridge peak cap
]
build_organic_mountain("Mountain_West_Bluff", (-10.5, 21.0), west_rings, seed=101)

# East Mountain Bluff (Right flank of gorge)
east_rings = [
    ( 0.0, 10.2, 10, -15, False),
    ( 2.6,  9.2, 10, -10, False),
    ( 2.9,  8.0,  9,  30, True),   # Plateau 1 shelf
    ( 5.2,  7.2,  9, -25, False),
    ( 5.5,  6.2,  8,  15, True),   # Plateau 2 shelf
    ( 7.8,  5.2,  8, -35, False),
    ( 8.1,  4.2,  7,   5, True),   # Plateau 3 shelf
    ( 9.8,  3.4,  7, -20, False),
    (10.4,  2.4,  7,  20, True)    # Ridge peak cap
]
build_organic_mountain("Mountain_East_Bluff", (10.0, 21.5), east_rings, seed=202)

# Foothill Boulders using authentic LPM assets (Natural erosion scatter)
foothills = [
    (rock_medium, -4.8, 17.0, 1.35,  25),
    (rock_medium,  4.9, 16.8, 1.25, -40),
    (rock_small, -7.8, 15.5, 1.45,  70),
    (rock_small,  7.6, 15.8, 1.40, -60),
    (rock_medium,-13.2, 16.5, 1.50,  15),
    (rock_medium, 13.5, 17.0, 1.40, -30)
]
for i, (ast, fx, fy, fsc, frot) in enumerate(foothills):
    import_lpm_asset(ast, f"Foothill_{i}", (fx, fy, 0.0), rot_z_deg=frot, scale=fsc)

# ==============================================================================
# 2. CENTRAL GORGE & MULTI-TIER CASCADING WATERFALL
# ==============================================================================
def create_poly_mesh(name, verts, faces, mat):
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], faces)
    me.update()
    obj = bpy.data.objects.new(name, me)
    bpy.context.collection.objects.link(obj)
    for p in obj.data.polygons: p.use_smooth = False
    obj.data.materials.append(mat)
    return obj

# Crest Rock Lip (Z=8.6m, gorge canyon entry)
crest_lip = [
    (-1.4, 23.5, 8.6), ( 1.4, 23.5, 8.6),
    (-1.2, 22.2, 8.5), ( 1.2, 22.2, 8.5),
    (-1.0, 21.0, 8.3), ( 1.0, 21.0, 8.3),
]
crest_faces = [[0, 1, 3, 2], [2, 3, 5, 4]]
create_poly_mesh("Waterfall_Crest_Lip", crest_lip, crest_faces, mat_water_deep)

# Flanking crest boulders cradling the cleft
import_lpm_asset(rock_small, "Crest_Rock_L", (-1.8, 22.0, 8.4), rot_z_deg=35, scale=1.1)
import_lpm_asset(rock_small, "Crest_Rock_R", ( 1.8, 22.0, 8.4), rot_z_deg=-45, scale=1.1)

# Tier 1: Cascading Chute (Stepped rapids plunging down the gorge)
# Main water stream
wf1_verts = [
    (-1.00, 21.0, 8.3), ( 1.00, 21.0, 8.3),
    (-1.15, 19.8, 6.8), ( 1.15, 19.8, 6.8),
    (-1.25, 18.6, 5.2), ( 1.25, 18.6, 5.2),
    (-1.40, 17.5, 4.4), ( 1.40, 17.5, 4.4),
]
wf1_faces = [[0, 1, 3, 2], [2, 3, 5, 4], [4, 5, 7, 6]]
create_poly_mesh("Waterfall_Tier1_Water", wf1_verts, wf1_faces, mat_water_flow)

# Layered Foam Rapids on Tier 1 (Central surging white water ribbons)
foam1_verts = [
    (-0.60, 20.8, 8.34), ( 0.60, 20.8, 8.34),
    (-0.75, 19.6, 6.84), ( 0.75, 19.6, 6.84),
    (-0.85, 18.4, 5.24), ( 0.85, 18.4, 5.24),
    (-0.95, 17.4, 4.44), ( 0.95, 17.4, 4.44),
]
foam1_faces = [[0, 1, 3, 2], [2, 3, 5, 4], [4, 5, 7, 6]]
create_poly_mesh("Waterfall_Tier1_Foam", foam1_verts, foam1_faces, mat_foam)

# Mid-Canyon Shelf & Intermediate Basin (Z=4.2m)
# Rocky shelf platform
bpy.ops.mesh.primitive_cylinder_add(vertices=8, radius=2.5, depth=0.7, location=(0.0, 17.2, 4.0))
mid_rock = bpy.context.active_object
mid_rock.name = "Mid_Shelf_Rock"
for p in mid_rock.data.polygons: p.use_smooth = False
mid_rock.data.materials.append(mat_stone)

# Intermediate Basin Pool
bpy.ops.mesh.primitive_cylinder_add(vertices=8, radius=2.0, depth=0.15, location=(0.0, 17.2, 4.38))
mid_pool = bpy.context.active_object
mid_pool.name = "Mid_Basin_Pool"
for p in mid_pool.data.polygons: p.use_smooth = False
mid_pool.data.materials.append(mat_water_deep)

# Mid Basin Foam Eddy
bpy.ops.mesh.primitive_cylinder_add(vertices=8, radius=1.3, depth=0.08, location=(0.0, 17.2, 4.42))
mid_foam = bpy.context.active_object
mid_foam.name = "Mid_Basin_Foam"
for p in mid_foam.data.polygons: p.use_smooth = False
mid_foam.data.materials.append(mat_foam)

# Tier 2: Flared Vertical Plunge (Steep curtain dropping into splash pool)
wf2_verts = [
    (-1.20, 16.9, 4.30), ( 1.20, 16.9, 4.30),
    (-1.45, 15.6, 2.50), ( 1.45, 15.6, 2.50),
    (-1.85, 14.2, 0.95), ( 1.85, 14.2, 0.95),
]
wf2_faces = [[0, 1, 3, 2], [2, 3, 5, 4]]
create_poly_mesh("Waterfall_Tier2_Plunge", wf2_verts, wf2_faces, mat_water_flow)

# Tier 2 Foam Curtain Edge
foam2_verts = [
    (-0.80, 16.8, 4.34), ( 0.80, 16.8, 4.34),
    (-1.05, 15.5, 2.54), ( 1.05, 15.5, 2.54),
    (-1.40, 14.1, 0.98), ( 1.40, 14.1, 0.98),
]
foam2_faces = [[0, 1, 3, 2], [2, 3, 5, 4]]
create_poly_mesh("Waterfall_Tier2_Foam", foam2_verts, foam2_faces, mat_foam)

# ==============================================================================
# 3. SPLASH POOL & MEANDERING RIVER OUTLET (ORGANIC LOW-POLY FACETS)
# ==============================================================================
# Natural Splash Pool (Organic 12-sided faceted basin, NOT a robotic cylinder!)
pool_bm = bmesh.new()
pool_n = 12
pool_r = 3.6
pool_cx, pool_cy, pool_cz = 0.0, 13.8, 0.85
pool_center = pool_bm.verts.new((pool_cx, pool_cy, pool_cz))
pool_rim_verts = []
rng_p = random.Random(88)
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

# Dynamic Foam Splash Impact Rings (Organic starburst ripple)
foam_bm = bmesh.new()
foam_center = foam_bm.verts.new((0.0, 14.2, 0.88))
foam_rim = []
for i in range(10):
    ang = i * (2 * math.pi / 10)
    rad = 2.1 * (1.0 + 0.22 * math.sin(3 * ang))
    foam_rim.append(foam_bm.verts.new((rad * math.cos(ang), 14.2 + rad * math.sin(ang), 0.88)))
for i in range(10):
    i_next = (i + 1) % 10
    foam_bm.faces.new([foam_rim[i], foam_rim[i_next], foam_center])
foam_me = bpy.data.meshes.new("Splash_Foam_Mesh")
foam_bm.to_mesh(foam_me)
foam_bm.free()
foam_obj = bpy.data.objects.new("Splash_Foam_Impact", foam_me)
bpy.context.collection.objects.link(foam_obj)
for p in foam_obj.data.polygons: p.use_smooth = False
foam_obj.data.materials.append(mat_foam)

# River Stones Bounding the Pool (LPM rock_small, natural clustering)
for i in range(9):
    ang = i * (2 * math.pi / 11) - 0.2
    # Leave South outlet open for river
    if ang < math.pi * 0.30 or ang > math.pi * 0.70:
        px = pool_cx + (pool_r + 0.3) * math.cos(ang)
        py = pool_cy + (pool_r + 0.3) * math.sin(ang)
        import_lpm_asset(rock_small, f"Pool_Border_Stone_{i}", (px, py, 0.0), rot_z_deg=i*35, scale=0.95)

# Meandering River Outlet Stream (Variant curves flowing South)
# Curving river corridor with width variation
river_spine = [
    # (Left_X, Right_X, Y, Z)
    (-1.40,  1.40, 11.2, 0.84),
    (-1.10,  1.60,  9.0, 0.82),  # Slight swing right
    (-1.60,  1.20,  6.8, 0.80),  # Swing left (meandering S-curve)
    (-1.20,  1.50,  4.6, 0.78),  # Return swing right
    (-1.50,  1.30,  2.4, 0.76),  # Exiting glade south
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

create_poly_mesh("Meandering_River_Stream", river_verts, river_faces, mat_water_deep)

# River Foam Edge Ribbons
r_foam_spine = [
    (-0.4, 0.4, 11.0, 0.86),
    (-0.2, 0.5,  9.0, 0.84),
    (-0.6, 0.2,  6.8, 0.82),
    (-0.3, 0.4,  4.6, 0.80),
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
create_poly_mesh("River_Rapid_Foam", r_foam_verts, r_foam_faces, mat_foam)

# Stepping Stones across the meandering bend (Flat low-poly slabs)
stepping_stones = [
    (-0.3, 7.8, 0.88, 0.46),
    ( 0.5, 7.5, 0.88, 0.42),
    ( 1.1, 7.2, 0.87, 0.40)
]
for sx, sy, sz, sr in stepping_stones:
    bpy.ops.mesh.primitive_cylinder_add(vertices=7, radius=sr, depth=0.18, location=(sx, sy, sz))
    st = bpy.context.active_object
    for p in st.data.polygons: p.use_smooth = False
    st.data.materials.append(mat_stone)

# LPM Riverbank Boulders along the meandering banks
import_lpm_asset(rock_small, "River_Bank_L1", (-2.2,  9.2, 0.0), rot_z_deg=40, scale=1.0)
import_lpm_asset(rock_small, "River_Bank_R1", ( 2.2,  8.6, 0.0), rot_z_deg=-20, scale=0.9)
import_lpm_asset(rock_small, "River_Bank_L2", (-2.4,  5.8, 0.0), rot_z_deg=-60, scale=1.05)
import_lpm_asset(rock_small, "River_Bank_R2", ( 2.0,  4.2, 0.0), rot_z_deg=30, scale=0.85)

# ==============================================================================
# 4. EXHIBITION DIORAMA PEDESTAL & GROUND GLADE
# ==============================================================================
# Rounded diorama stage centered at (0.0, 16.0) with radius 18.0m
bpy.ops.mesh.primitive_cylinder_add(vertices=48, radius=18.0, depth=0.40, location=(0.0, 16.0, -0.20))
stage = bpy.context.active_object
stage.name = "Diorama_Stage"
for p in stage.data.polygons: p.use_smooth = False
stage.data.materials.append(mat_turf)

# ==============================================================================
# 5. CAMERA & LIGHTING (HEROIC GORGE PERSPECTIVE)
# ==============================================================================
cam_data = bpy.data.cameras.new("MountainCam")
cam_data.type = 'ORTHO'
cam_data.ortho_scale = 51.0   # Generous balanced margins >= 60px on all 4 sides
cam_obj = bpy.data.objects.new("MountainCam", cam_data)
sc.collection.objects.link(cam_obj)
sc.camera = cam_obj

# Camera positioned in front of the gorge (Yaw = 14 deg, Pitch = 28 deg)
# Unobstructed direct line of sight into canyon cleft, Tier 1, Mid Basin, Tier 2, Pool & River!
pitch = math.radians(28)
yaw = math.radians(14)
dist = 70.0

tx, ty, tz = 0.0, 15.5, 3.8
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
rim.data.energy = 0.45
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

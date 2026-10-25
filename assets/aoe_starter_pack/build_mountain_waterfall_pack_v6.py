#!/usr/bin/env python3
"""
AOE / SETTLERS — STANDALONE MOUNTAIN WATERFALL PACK (v6.0)
Strictly implementing Boss's exact directives:
1. "moutain just look too crazy, i want more vertical line, more flat on top with some green patches on top, not too crazy with all the poking out features."
   - Replaced noisy jumbled boulders with clean, majestic Stepped Vertical Cliff Mesas.
   - Strong vertical cliff lines (sheared vertical rock facets).
   - Flat tabletop plateau tops on summits and terraces capped with lush green alpine turf (M_Turf).
   - Solid continuous mountain ridge connecting West and East seamlessly in the middle.
   - Zero crazy poking-out lumps.
2. "water pond gotta be inside the ground, i see shadow of the pond reflecting on the ground."
   - Carved recessed circular pond cavity INTO the ground terrain stage (Z_water = 0.18m inside 0.40m ground rim).
   - Zero floating pond shadow on the ground!
3. "then from the pond have curve lines of water out to the edge of the island"
   - Natural curving S-curve river channel carved into the terrain flowing south out to the island edge.
   - Pure blue water throughout (top blue mask -> stepped vertical waterfall -> sunken round pond -> curving river).
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
mat_da        = get_mat("M_Da",        (112, 106,  98), roughness=0.92)  # Weathered vertical cliff rock
mat_da_sang   = get_mat("M_DaSang",    (138, 132, 122), roughness=0.90)  # Sunlit ledge stone
mat_da_toi    = get_mat("M_DaToi",     ( 78,  72,  66), roughness=0.96)  # Chasm & riverbed rock
mat_turf      = get_mat("M_Turf",      ( 92, 132,  56), roughness=0.85)  # Meadow & mountain grass
mat_turf_top  = get_mat("M_TurfTop",   (115, 155,  68), roughness=0.85)  # Sunlit plateau cap
# PURE VIBRANT BLUE WATER (No white foam)
mat_water_blue= get_mat("M_WaterBlue", ( 42, 138, 178), roughness=0.10, emission_srgb=(48, 148, 192), emission_strength=0.55)

# LPM Rock assets
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
# 1. CLEAN VERTICAL CLIFF MESAS WITH FLAT GREEN TOPS
# ==============================================================================
def build_vertical_mesa_block(name, footprint_pts, z_bottom, z_top, mat_wall=mat_da, mat_cap=mat_turf_top):
    """
    Constructs a clean low-poly vertical cliff mesa:
    - Vertical wall faces dropping straight down (mat_wall)
    - Flat tabletop horizontal cap on top (mat_cap)
    """
    bm = bmesh.new()
    n = len(footprint_pts)
    v_bot = [bm.verts.new((x, y, z_bottom)) for x, y in footprint_pts]
    v_top = [bm.verts.new((x, y, z_top)) for x, y in footprint_pts]
    
    # Vertical wall faces
    wall_faces = []
    for i in range(n):
        i_next = (i + 1) % n
        f = bm.faces.new([v_bot[i], v_bot[i_next], v_top[i_next], v_top[i]])
        wall_faces.append(f)
        
    # Flat top cap
    cap_face = bm.faces.new(v_top)
    
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    
    obj = bpy.data.objects.new(name, me)
    bpy.context.collection.objects.link(obj)
    for p in obj.data.polygons: p.use_smooth = False
    
    obj.data.materials.append(mat_wall)
    obj.data.materials.append(mat_cap)
    
    # Assign material indices: index 1 for top cap, index 0 for walls
    for p in obj.data.polygons:
        if p.normal.z > 0.8:
            p.material_index = 1
        else:
            p.material_index = 0
            
    return obj

# A. Central Connecting Ridge & Backwall (Bridge between West and East)
# Solid rock wall spanning X = -4.0 to +4.0, Y = 21.0 to 24.5, Z = 0.0 to 8.2m
center_ridge_pts = [
    (-3.8, 24.5), ( 3.8, 24.5), ( 3.8, 21.2), (-3.8, 21.2)
]
build_vertical_mesa_block("Center_Connecting_Ridge", center_ridge_pts, 0.0, 8.2, mat_da_toi, mat_da_sang)

# B. West Mesa Bluff (High Summit H=10.0m + Mid Terrace H=5.5m)
# West Lower Terrace (Z = 0.0 to 5.2m)
w_low_pts = [
    (-13.5, 23.5), (-2.8, 23.5), (-2.8, 17.5), (-6.5, 16.5), (-13.5, 17.5)
]
build_vertical_mesa_block("West_Mesa_Lower_Terrace", w_low_pts, 0.0, 5.2, mat_da, mat_turf)

# West Summit Tabletop Mesa (Z = 5.2m to 9.8m)
w_summit_pts = [
    (-12.5, 23.5), (-2.8, 23.5), (-2.8, 19.5), (-7.5, 18.5), (-12.5, 19.5)
]
build_vertical_mesa_block("West_Mesa_Summit_Plateau", w_summit_pts, 5.2, 9.8, mat_da, mat_turf_top)

# C. East Mesa Bluff (Asymmetrical Summit H=8.4m + Mid Terrace H=4.6m)
# East Lower Terrace (Z = 0.0 to 4.6m)
e_low_pts = [
    ( 2.8, 23.5), (13.5, 23.5), (13.5, 17.5), ( 6.5, 16.5), ( 2.8, 17.5)
]
build_vertical_mesa_block("East_Mesa_Lower_Terrace", e_low_pts, 0.0, 4.6, mat_da, mat_turf)

# East Summit Tabletop Mesa (Z = 4.6m to 8.4m)
e_summit_pts = [
    ( 2.8, 23.5), (12.5, 23.5), (12.5, 19.5), ( 7.5, 18.5), ( 2.8, 19.5)
]
build_vertical_mesa_block("East_Mesa_Summit_Plateau", e_summit_pts, 4.6, 8.4, mat_da, mat_turf_top)

# Foothill Accent Stones (LPM authentic rocks framing mountain corners)
import_lpm_asset(rock_large, "LPM_Corner_W", (-12.5, 16.8, 0.4), rot_z_deg=25, scale=1.3)
import_lpm_asset(rock_large, "LPM_Corner_E", ( 12.5, 16.8, 0.4), rot_z_deg=-30, scale=1.2)
import_lpm_asset(rock_small, "LPM_Gorge_Rim_W", (-3.5, 17.8, 0.4), rot_z_deg=45, scale=1.1)
import_lpm_asset(rock_small, "LPM_Gorge_Rim_E", ( 3.5, 17.8, 0.4), rot_z_deg=-45, scale=1.1)

# ==============================================================================
# 2. "A MASK OF BLUE ON TOP OF THE MOUNTAIN" (MOUNTAIN SPRING MASK)
# ==============================================================================
# Sits cleanly on the central connecting ridge saddle at Z=8.22m:
top_pool_bm = bmesh.new()
tp_c = top_pool_bm.verts.new((0.0, 22.8, 8.22))
tp_rim = []
tp_n = 12
tp_rx, tp_ry = 2.6, 1.6
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

# ==============================================================================
# 3. WATERFALL STREAM: "SQUARE DOWN TO THE GROUND" (STEPPED VERTICAL BLUE CHUTE)
# ==============================================================================
# Clean rectangular blue chute cascading down the vertical rock face:
# Width = 3.2m (X = -1.6 to +1.6).
# Stepped down like clean square vertical/horizontal steps:
wf_profile = [
    # (Y, Z)
    (21.4, 8.22),  # Spillway lip from top blue mask
    (20.5, 8.20),  # Upper horizontal step
    (20.5, 5.60),  # Vertical drop 1
    (18.8, 5.50),  # Mid horizontal step
    (18.8, 3.00),  # Vertical drop 2
    (16.8, 2.90),  # Lower horizontal step
    (16.8, 0.40),  # Final vertical drop to ground level
    (15.2, 0.20),  # Entering the sunken ground pond
]

wf_verts = []
w_half = 1.60
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

create_mesh_obj("Waterfall_Square_Down_Stream", wf_verts, wf_faces, mat_water_blue)

# ==============================================================================
# 4. "WATER POND GOTTA BE INSIDE THE GROUND" & "CURVE LINES OF WATER OUT TO EDGE"
# ==============================================================================
# Ground Stage Terrain: Top at Z = 0.40m, Bottom at Z = -0.40m
bpy.ops.mesh.primitive_cylinder_add(vertices=64, radius=17.5, depth=0.80, location=(0.0, 16.0, 0.0))
stage = bpy.context.active_object
stage.name = "Diorama_Stage_Terrain"
for p in stage.data.polygons: p.use_smooth = False
stage.data.materials.append(mat_turf)

# Cutter 1: Circular Pond Cavity (Radius 4.6m, centered at X=0, Y=11.5, cutting Z=0.45 down to 0.05)
bpy.ops.mesh.primitive_cylinder_add(vertices=32, radius=4.6, depth=0.50, location=(0.0, 11.5, 0.25))
pond_cutter = bpy.context.active_object
pond_cutter.name = "Pond_Cutter"

# Cutter 2: Curving River Trench (S-curve trench from Y=7.0 to Y=-0.5, width 2.4m, depth 0.5m)
river_curve_pts = [
    # (Center_X, Center_Y)
    ( 0.0,  7.2),
    ( 1.1,  5.4),   # Swing right
    (-0.7,  3.2),   # Swing left (meandering S-curve)
    ( 0.0,  0.4),   # Swing back to south edge
    ( 0.0, -1.5),   # Exiting island boundary
]
rw_half = 1.25
rt_verts = []
for cx, cy in river_curve_pts:
    rt_verts.append((cx - rw_half, cy, 0.50))
    rt_verts.append((cx + rw_half, cy, 0.50))
    rt_verts.append((cx - rw_half, cy, 0.02))
    rt_verts.append((cx + rw_half, cy, 0.02))

rt_faces = []
for i in range(len(river_curve_pts) - 1):
    b0 = i * 4
    b1 = b0 + 1
    b2 = b0 + 2
    b3 = b0 + 3
    n0 = (i + 1) * 4
    n1 = n0 + 1
    n2 = n0 + 2
    n3 = n0 + 3
    # Top face
    rt_faces.append([b0, b1, n1, n0])
    # Bottom face
    rt_faces.append([b2, n2, n3, b3])
    # Left wall
    rt_faces.append([b0, n0, n2, b2])
    # Right wall
    rt_faces.append([b1, b3, n3, n1])

rt_me = bpy.data.meshes.new("River_Cutter_Mesh")
rt_me.from_pydata(rt_verts, [], rt_faces)
rt_me.update()
river_cutter = bpy.data.objects.new("River_Cutter", rt_me)
bpy.context.collection.objects.link(river_cutter)

# Apply Boolean Cutters to carve recessed pond & river trench INTO the ground terrain
for cutter in [pond_cutter, river_cutter]:
    mod = stage.modifiers.new("BoolCut", 'BOOLEAN')
    mod.object = cutter
    mod.operation = 'DIFFERENCE'
    bpy.context.view_layer.objects.active = stage
    bpy.ops.object.modifier_apply(modifier="BoolCut")
    bpy.data.objects.remove(cutter, do_unlink=True)

# Now, place the pure blue water plane INSIDE the recessed ground cavity (Z = 0.18m):
# A. Circular Sunken Pond Water Plane (R=4.58m, Z=0.18m - below ground surface Z=0.40m!)
sunken_pool_bm = bmesh.new()
sp_c = sunken_pool_bm.verts.new((0.0, 11.5, 0.18))
sp_rim = []
sp_n = 32
sp_r = 4.58
for i in range(sp_n):
    ang = i * (2 * math.pi / sp_n)
    vx = 0.0 + sp_r * math.cos(ang)
    vy = 11.5 + sp_r * math.sin(ang)
    sp_rim.append(sunken_pool_bm.verts.new((vx, vy, 0.18)))
for i in range(sp_n):
    i_next = (i + 1) % sp_n
    sunken_pool_bm.faces.new([sp_rim[i], sp_rim[i_next], sp_c])

sunken_pool_me = bpy.data.meshes.new("Sunken_Pond_Water")
sunken_pool_bm.to_mesh(sunken_pool_me)
sunken_pool_bm.free()
sunken_pool_obj = bpy.data.objects.new("Sunken_Pond_Water", sunken_pool_me)
bpy.context.collection.objects.link(sunken_pool_obj)
for p in sunken_pool_obj.data.polygons: p.use_smooth = False
sunken_pool_obj.data.materials.append(mat_water_blue)

# B. Curving River Water Plane (Z=0.16m, flowing south to island edge)
r_water_pts = [
    # (Center_X, Center_Y, Width)
    ( 0.0,  7.0, 2.3),
    ( 1.1,  5.4, 2.2),
    (-0.7,  3.2, 2.2),
    ( 0.0,  0.4, 2.3),
]
r_water_verts = []
for cx, cy, cw in r_water_pts:
    r_water_verts.append((cx - cw/2, cy, 0.16))
    r_water_verts.append((cx + cw/2, cy, 0.16))
r_water_faces = []
for i in range(len(r_water_pts) - 1):
    i0 = i * 2
    i1 = i0 + 1
    i2 = (i + 1) * 2
    i3 = i2 + 1
    r_water_faces.append([i0, i1, i3, i2])
create_mesh_obj("Curving_River_Water", r_water_verts, r_water_faces, mat_water_blue)

# Flat Stepping Stones across the narrow river curve (Y=4.2m)
stepping_stones = [
    (0.4, 4.4, 0.22, 0.44),
    (1.1, 4.2, 0.22, 0.40),
    (1.8, 4.0, 0.22, 0.38)
]
for sx, sy, sz, sr in stepping_stones:
    bpy.ops.mesh.primitive_cylinder_add(vertices=7, radius=sr, depth=0.18, location=(sx, sy, sz))
    st = bpy.context.active_object
    for p in st.data.polygons: p.use_smooth = False
    st.data.materials.append(mat_da_sang)

# Natural LPM River Stones framing the sunken pond rim bank
rim_angles = [0.10, 0.24, 0.38, 0.52, 0.66, 0.78, 0.90, 1.10, 1.24, 1.38, 1.52, 1.66, 1.78, 1.90]
for i, a_mult in enumerate(rim_angles):
    ang = a_mult * math.pi
    # Leave North entry (waterfall) and South exit (river) open
    if not (math.pi * 0.35 <= ang <= math.pi * 0.65) and not (math.pi * 1.35 <= ang <= math.pi * 1.65):
        rx = 0.0 + (sp_r + 0.35) * math.cos(ang)
        ry = 11.5 + (sp_r + 0.35) * math.sin(ang)
        import_lpm_asset(rock_small, f"Pond_Bank_Stone_{i}", (rx, ry, 0.40), rot_z_deg=i*30, scale=0.92)

# ==============================================================================
# 5. CAMERA & LIGHTING (HEROIC GORGE PERSPECTIVE)
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

tx, ty, tz = 0.0, 14.5, 4.0
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

# Export Standalone GLB (including the carved terrain stage and all elements)
bpy.ops.export_scene.gltf(
    filepath=out_glb,
    export_format='GLB',
    use_selection=False,
    export_apply=True
)
print(f"✅ Exported Standalone Mountain Waterfall Pack GLB -> {out_glb}")

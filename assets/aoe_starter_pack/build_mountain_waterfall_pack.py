#!/usr/bin/env python3
"""
STANDALONE MOUNTAINS WITH WATERFALL IN THE MIDDLE SHOWCASE
Built strictly according to SPEC_STYLED_WATERFALL.md and Boss's exact directives:
- Two flanking weathered terraced mountain bluffs (West & East, flat ridge tops, no pointy cones)
- Central gorge with 2-tier waterfall cascading right down the middle
- Upper chute ribbon pouring from cleft into mid-canyon shelf & basin
- Lower vertical plunge into central mountain splash pool with dual foam rings
- Encased in authentic LPM natural stones (rock_medium, rock_small - zero diamond artifacts)
- Exported as standalone mountain_waterfall_pack.glb & rendered separately for approval.
"""
import bpy
import bmesh
import math
import os
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

# Ghibli Materials
mat_stone       = get_mat("M_RegularStone",   (90, 85, 78))       # Weathered mountain rock
mat_turf        = get_mat("M_GhibliTurf",     (72, 122, 56))      # Meadow ground
mat_river       = get_mat("M_GhibliRiver",    (50, 126, 140), 0.12, 0.05, (50, 126, 140), 0.4)
mat_waterfall   = get_mat("M_GhibliWaterfall",(142, 209, 224), 0.10, 0.0, (232, 246, 250), 1.6) # SPEC chute
mat_foam        = get_mat("M_GhibliFoam",     (240, 248, 250), 0.20, 0.0, (240, 248, 250), 1.4) # SPEC foam

def create_poly_mesh(name, verts, faces, mat):
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], faces)
    me.update()
    obj = bpy.data.objects.new(name, me)
    bpy.context.collection.objects.link(obj)
    for p in obj.data.polygons: p.use_smooth = False
    obj.data.materials.append(mat)
    return obj

# Real LPM Rock assets
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

# Ground Stage (Green mountain glade)
bpy.ops.mesh.primitive_cylinder_add(vertices=32, radius=19.0, depth=0.3, location=(0, 18.0, -0.15))
ground = bpy.context.active_object
for p in ground.data.polygons: p.use_smooth = False
ground.data.materials.append(mat_turf)

# ==============================================================================
# 1. TWO WEATHERED TERRACED MOUNTAINS (NO POINTY CONES, FLAT RIDGE TOPS)
# ==============================================================================
def build_terraced_bluff(name, center_xy, tiers, mat=mat_stone):
    cx, cy = center_xy
    for i, (z_bot, z_top, r_bot, r_top, n_sides, rot_d) in enumerate(tiers):
        depth = z_top - z_bot
        mid_z = (z_bot + z_top) / 2.0
        bpy.ops.mesh.primitive_cylinder_add(vertices=n_sides, radius=r_bot, depth=depth, location=(cx, cy, mid_z))
        tier = bpy.context.active_object
        tier.name = f"{name}_Tier_{i}"
        tier.rotation_euler.z = math.radians(rot_d)
        for p in tier.data.polygons: p.use_smooth = False
        tier.data.materials.append(mat)

# West Mountain Bluff (Left of Waterfall)
west_tiers = [
    (0.0,  3.20, 11.0, 10.0, 10,  15),
    (3.20, 5.80,  9.0,  8.2,  9, -30),
    (5.80, 8.20,  7.2,  6.4,  8,  45),
    (8.20, 9.90,  5.2,  4.4,  7, -10),
    (9.90, 11.20, 3.6,  3.0,  7,  25) # Weathered flat top
]
build_terraced_bluff("Mountain_West_Bluff", (-12.0, 22.0), west_tiers)

# East Mountain Bluff (Right of Waterfall)
east_tiers = [
    (0.0,  3.00, 10.2,  9.2, 10, -20),
    (3.00, 5.50,  8.2,  7.4,  9,  35),
    (5.50, 7.80,  6.5,  5.6,  8, -40),
    (7.80, 9.40,  4.8,  3.8,  7,  15),
    (9.40, 10.50, 3.4,  2.6,  7, -30) # Weathered flat top
]
build_terraced_bluff("Mountain_East_Bluff", (11.5, 22.5), east_tiers)

# Foothill Boulders using authentic LPM assets (Zero diamond pokes)
foothills = [
    (rock_medium, -4.5, 18.0, 1.4, 25),
    (rock_medium,  4.8, 17.5, 1.3, -40),
    (rock_small, -7.5, 16.5, 1.5, 70),
    (rock_small,  7.8, 17.0, 1.4, -60),
    (rock_medium,-14.5, 16.0, 1.6, 15),
    (rock_medium, 15.0, 16.5, 1.5, -30)
]
for i, (ast, fx, fy, fsc, frot) in enumerate(foothills):
    import_lpm_asset(ast, f"Foothill_{i}", (fx, fy, 0.0), rot_z_deg=frot, scale=fsc)

# ==============================================================================
# 2. WATERFALL IN THE MIDDLE (Cascading down the Central Gorge)
# ==============================================================================
# Layer 1: Crest Rock Lip (Thềm nứt đỉnh kẹp giữa 2 núi tại Z=8.5m)
bpy.ops.mesh.primitive_cylinder_add(vertices=8, radius=1.8, depth=0.40, location=(0.0, 23.2, 8.4))
crest_rock = bpy.context.active_object
for p in crest_rock.data.polygons: p.use_smooth = False
crest_rock.data.materials.append(mat_stone)

# Layer 2: Tier 1 Cascading Chute (Máng thác dốc lượn sóng chữ S, 4 đốt)
wf1_verts = [
    # Top lip
    (-0.85, 23.0, 8.5), ( 0.85, 23.0, 8.5),
    # Mid-fall bend
    (-0.95, 21.5, 6.6), ( 0.95, 21.5, 6.6),
    # Lower chute entering mid basin
    (-1.15, 20.0, 4.8), ( 1.15, 20.0, 4.8),
]
wf1_faces = [[0, 1, 3, 2], [2, 3, 5, 4]]
create_poly_mesh("Waterfall_Tier1_Chute", wf1_verts, wf1_faces, mat_waterfall)

# Layer 3: Mid-Canyon Shelf & Intermediate Basin
bpy.ops.mesh.primitive_cylinder_add(vertices=8, radius=2.6, depth=0.60, location=(0.0, 19.8, 4.5))
mid_shelf = bpy.context.active_object
for p in mid_shelf.data.polygons: p.use_smooth = False
mid_shelf.data.materials.append(mat_stone)

bpy.ops.mesh.primitive_cylinder_add(vertices=8, radius=2.1, depth=0.15, location=(0.0, 19.8, 4.85))
mid_pool = bpy.context.active_object
for p in mid_pool.data.polygons: p.use_smooth = False
mid_pool.data.materials.append(mat_waterfall)

# Layer 4: Tier 2 Vertical Plunge Curtain (Màn nước xòe nan quạt)
wf2_verts = [
    (-1.10, 19.5, 4.6), ( 1.10, 19.5, 4.6),
    (-1.30, 18.2, 2.8), ( 1.30, 18.2, 2.8),
    (-1.55, 16.8, 0.95), ( 1.55, 16.8, 0.95),
]
wf2_faces = [[0, 1, 3, 2], [2, 3, 5, 4]]
create_poly_mesh("Waterfall_Tier2_Plunge", wf2_verts, wf2_faces, mat_waterfall)

# Layer 5: Central Mountain Splash Pool at Gorge Mouth (Z=0.88m)
bpy.ops.mesh.primitive_cylinder_add(vertices=16, radius=3.8, depth=0.20, location=(0.0, 16.5, 0.88))
wf_pool = bpy.context.active_object
wf_pool.name = "Waterfall_Splash_Pool"
for p in wf_pool.data.polygons: p.use_smooth = False
wf_pool.data.materials.append(mat_river)

# Dual Concentric Foam Rings (Inner & Outer bọt sóng phát quang)
bpy.ops.mesh.primitive_cylinder_add(vertices=16, radius=4.1, depth=0.08, location=(0.0, 16.5, 0.87))
foam_inner = bpy.context.active_object
for p in foam_inner.data.polygons: p.use_smooth = False
foam_inner.data.materials.append(mat_foam)

bpy.ops.mesh.primitive_cylinder_add(vertices=16, radius=4.4, depth=0.04, location=(0.0, 16.5, 0.86))
foam_outer = bpy.context.active_object
for p in foam_outer.data.polygons: p.use_smooth = False
foam_outer.data.materials.append(mat_foam)

# River Stones Encasing the Pool (LPM rock_small assets, zero diamond artifacts)
for i in range(12):
    ang = i * (2 * math.pi / 12)
    if ang < math.pi * 0.35 or ang > math.pi * 0.65: # leave south outlet open for river stream
        px = 0.0 + 4.1 * math.cos(ang)
        py = 16.5 + 4.1 * math.sin(ang)
        import_lpm_asset(rock_small, f"Pool_Stone_{i}", (px, py, 0.0), rot_z_deg=i*30, scale=0.95)

# River Outlet Stream flowing South out of the Gorge
outlet_pts = [
    (-1.2, 16.0, 0.86), ( 1.2, 16.0, 0.86),
    (-1.1, 13.5, 0.85), ( 1.1, 13.5, 0.85),
    (-1.3, 11.0, 0.84), ( 1.3, 11.0, 0.84),
]
outlet_faces = [[0, 1, 3, 2], [2, 3, 5, 4]]
create_poly_mesh("River_Outlet_Stream", outlet_pts, outlet_faces, mat_river)

# Stepping Stones across the outlet stream (Flat 7-sided river slabs)
for sx, sy, sr in [(0.8, 12.5, 0.45), (1.4, 12.5, 0.42)]:
    bpy.ops.mesh.primitive_cylinder_add(vertices=7, radius=sr, depth=0.18, location=(sx, sy, 0.88))
    st_slab = bpy.context.active_object
    for p in st_slab.data.polygons: p.use_smooth = False
    st_slab.data.materials.append(mat_stone)

# ==============================================================================
# CAMERA & LIGHTING (ISOMETRIC CLOSE-UP OF THE GORGE & WATERFALL)
# ==============================================================================
cam_data = bpy.data.cameras.new("MountainCam")
cam_data.type = 'ORTHO'
cam_data.ortho_scale = 36.0   # Perfectly frames both mountain bluffs + central gorge
cam_obj = bpy.data.objects.new("MountainCam", cam_data)
sc.collection.objects.link(cam_obj)
sc.camera = cam_obj

pitch = math.radians(24)
yaw = math.radians(45)
dist = 60.0

tx, ty, tz = 0.0, 18.5, 5.0
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
sun.data.energy = 3.3
sun.data.color = tt((255, 245, 222))
sun.rotation_euler = (math.radians(46), 0, math.radians(-38))

fill = bpy.data.objects.new("SunFill", bpy.data.lights.new("SunFill", 'SUN'))
sc.collection.objects.link(fill)
fill.data.energy = 0.40
fill.data.use_shadow = False
fill.data.color = tt((205, 220, 232))
fill.rotation_euler = (math.radians(65), 0, math.radians(145))

world = bpy.data.worlds.new("W")
sc.world = world
world.use_nodes = True
bg = world.node_tree.nodes["Background"]
bg.inputs[1].default_value = 0.80
bg.inputs[0].default_value = (*tt((210, 225, 235)), 1.0)

sc.render.engine = "BLENDER_EEVEE"
sc.render.resolution_x = 1920
sc.render.resolution_y = 1080
sc.view_settings.view_transform = "AgX"

# Render Showcase PNG
sc.render.filepath = out_img
bpy.ops.render.render(write_still=True)
print(f"📸 Mountain Waterfall Showcase Rendered -> {out_img}")

# Export Standalone GLB (Unlinking ground stage)
bpy.data.objects.remove(ground, do_unlink=True)
bpy.ops.export_scene.gltf(
    filepath=out_glb,
    export_format='GLB',
    use_selection=False,
    export_apply=True
)
print(f"✅ Exported Standalone Mountain Waterfall Pack GLB -> {out_glb}")

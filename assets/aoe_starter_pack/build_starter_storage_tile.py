#!/usr/bin/env python3
"""
STARTER STORAGE TILE — 4 SQUARES (2x2 GRID)
Standalone game asset for Age of Empires / Settlers cozy RTS.
Features:
- Flat wooden foundation tile (3.8m x 3.8m)
- Sturdy timber outer frame with 4 corner posts
- Crossed wooden divider splitting the tile into 4 equal storage slots (2x2)
- Slot 1 (North-West): Stack of 4 round timber logs (Wood stockpile)
- Slot 2 (North-East): Stack of 3 chiseled quarry stones (Stone stockpile)
- Slot 3 (South-West): Woven wicker basket with red wild berries (Food stockpile)
- Slot 4 (South-East): Empty starter slot with clean floor planks (Expansion slot ready for work)
Rendered as an independent showcase asset (NOT installed on island until approved).
"""
import bpy
import bmesh
import math
import os
from mathutils import Vector, Matrix

out_dir = "~/projects/lpm-faceless-humanoid/assets/aoe_starter_pack"
os.makedirs(out_dir, exist_ok=True)

out_glb = os.path.join(out_dir, "starter_storage_tile.glb")
out_img = os.path.join(out_dir, "showcase_starter_storage.png")

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene

def tt(c):
    return tuple(((x / 255.0) / 12.92) if (x / 255.0) <= 0.04045 else (((x / 255.0) + 0.055) / 1.055) ** 2.4 for x in c)

def get_mat(name, srgb, roughness=0.85, metallic=0.0):
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = (*tt(srgb), 1.0)
        bsdf.inputs["Roughness"].default_value = roughness
        bsdf.inputs["Metallic"].default_value = metallic
    return mat

# Materials (Ghibli / Warm Earth)
mat_timber     = get_mat("M_TimberWood",    (128, 92, 58),   0.82)
mat_wood_cut   = get_mat("M_WoodCutFace",   (180, 142, 94),  0.80)
mat_planks     = get_mat("M_FloorPlanks",   (148, 112, 74),  0.88)
mat_stone      = get_mat("M_QuarryStone",   (98, 92, 84),    0.85)
mat_stone_cut  = get_mat("M_StoneCut",      (122, 116, 108), 0.82)
mat_wicker     = get_mat("M_WickerBasket",  (196, 164, 108), 0.90)
mat_berry      = get_mat("M_RedBerry",      (180, 36, 52),   0.35)
mat_earth      = get_mat("M_PackedEarth",   (88, 70, 50),    0.95)
mat_backdrop   = get_mat("M_StudioGrass",   (72, 122, 56),   0.90)

# Studio Pedestal
bpy.ops.mesh.primitive_cylinder_add(vertices=32, radius=8.0, depth=0.20, location=(0, 0, -0.10))
pedestal = bpy.context.active_object
for p in pedestal.data.polygons: p.use_smooth = False
pedestal.data.materials.append(mat_backdrop)

# 1. Base Earth & Foundation Slab (3.8m x 3.8m x 0.12m)
bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0, 0, 0.06))
base_slab = bpy.context.active_object
base_slab.scale = (3.8, 3.8, 0.12)
bpy.ops.object.transform_apply(scale=True)
for p in base_slab.data.polygons: p.use_smooth = False
base_slab.data.materials.append(mat_earth)

# 2. Floor Planks (4 quadrants with plank grooves)
for qx in [-0.95, 0.95]:
    for qy in [-0.95, 0.95]:
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=(qx, qy, 0.13))
        quad_plank = bpy.context.active_object
        quad_plank.scale = (1.75, 1.75, 0.04)
        bpy.ops.object.transform_apply(scale=True)
        for p in quad_plank.data.polygons: p.use_smooth = False
        quad_plank.data.materials.append(mat_planks)

# 3. Outer Timber Framing & Corner Pegs
# 4 Border Beams (North, South, East, West)
borders = [
    (( 0.0,  1.85, 0.18), (3.8, 0.16, 0.16)),  # North
    (( 0.0, -1.85, 0.18), (3.8, 0.16, 0.16)),  # South
    (( 1.85,  0.0, 0.18), (0.16, 3.8, 0.16)),  # East
    ((-1.85,  0.0, 0.18), (0.16, 3.8, 0.16)),  # West
]
for loc, sc_val in borders:
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=loc)
    b_beam = bpy.context.active_object
    b_beam.scale = sc_val
    bpy.ops.object.transform_apply(scale=True)
    for p in b_beam.data.polygons: p.use_smooth = False
    b_beam.data.materials.append(mat_timber)

# 4 Corner Posts (Square Chamfered Pegs)
corners = [(-1.85, -1.85), (1.85, -1.85), (-1.85, 1.85), (1.85, 1.85)]
for cx, cy in corners:
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(cx, cy, 0.28))
    c_post = bpy.context.active_object
    c_post.scale = (0.24, 0.24, 0.36)
    bpy.ops.object.transform_apply(scale=True)
    for p in c_post.data.polygons: p.use_smooth = False
    c_post.data.materials.append(mat_timber)

# 4. Crossed Dividers (Splitting into 4 equal squares)
# X-divider (along Y=0)
bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0, 0, 0.18))
x_div = bpy.context.active_object
x_div.scale = (3.7, 0.14, 0.14)
bpy.ops.object.transform_apply(scale=True)
for p in x_div.data.polygons: p.use_smooth = False
x_div.data.materials.append(mat_timber)

# Y-divider (along X=0)
bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0, 0, 0.18))
y_div = bpy.context.active_object
y_div.scale = (0.14, 3.7, 0.14)
bpy.ops.object.transform_apply(scale=True)
for p in y_div.data.polygons: p.use_smooth = False
y_div.data.materials.append(mat_timber)

# Center Joint Pin
bpy.ops.mesh.primitive_cylinder_add(vertices=8, radius=0.14, depth=0.22, location=(0, 0, 0.20))
pin = bpy.context.active_object
for p in pin.data.polygons: p.use_smooth = False
pin.data.materials.append(mat_wood_cut)

# ==============================================================================
# QUADRANT 1: TIMBER LOGS STOCKPILE (North-West: X < 0, Y > 0)
# ==============================================================================
# 4 Stacked Round Logs (3 at base, 1 on top)
log_specs = [
    ((-1.35,  0.95, 0.27), 0.18, 1.45, 0),
    ((-0.95,  0.95, 0.27), 0.18, 1.45, 0),
    ((-0.55,  0.95, 0.27), 0.18, 1.45, 0),
    ((-0.95,  0.95, 0.58), 0.18, 1.45, 0),  # Top log
]
for (lx, ly, lz), lrad, llen, lrot in log_specs:
    bpy.ops.mesh.primitive_cylinder_add(vertices=10, radius=lrad, depth=llen, location=(lx, ly, lz))
    log_obj = bpy.context.active_object
    log_obj.rotation_euler.x = math.radians(90)
    for p in log_obj.data.polygons: p.use_smooth = False
    log_obj.data.materials.append(mat_timber)
    # End caps with lighter cut wood
    log_obj.data.materials.append(mat_wood_cut)
    # Assign end cap material to top/bottom polygon
    for i, p in enumerate(log_obj.data.polygons):
        if abs(p.normal.z) > 0.8:
            p.material_index = 1

# ==============================================================================
# QUADRANT 2: QUARRY STONE STOCKPILE (North-East: X > 0, Y > 0)
# ==============================================================================
# 3 Chiseled Stone Blocks
stone_specs = [
    ((0.65, 0.70, 0.30), (0.70, 0.55, 0.32), 12),
    ((1.25, 1.05, 0.30), (0.60, 0.65, 0.32), -8),
    ((0.85, 0.90, 0.58), (0.65, 0.60, 0.28), 25),  # Top block
]
for (sx, sy, sz), (sw, sl, sh), srot in stone_specs:
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(sx, sy, sz))
    st_obj = bpy.context.active_object
    st_obj.scale = (sw, sl, sh)
    st_obj.rotation_euler.z = math.radians(srot)
    bpy.ops.object.transform_apply(scale=True)
    for p in st_obj.data.polygons: p.use_smooth = False
    st_obj.data.materials.append(mat_stone)

# Small stone chips on floor
for cx, cy, cz in [(0.50, 1.25, 0.17), (1.35, 0.60, 0.17)]:
    bpy.ops.mesh.primitive_cube_add(size=0.12, location=(cx, cy, cz))
    chip = bpy.context.active_object
    chip.rotation_euler = (0.2, 0.3, 0.4)
    for p in chip.data.polygons: p.use_smooth = False
    chip.data.materials.append(mat_stone_cut)

# ==============================================================================
# QUADRANT 3: FOOD / BERRY STOCKPILE (South-West: X < 0, Y < 0)
# ==============================================================================
# Woven Wicker Basket with Berries
bx, by = -0.95, -0.95
# Basket outer cylinder (flared bucket)
bpy.ops.mesh.primitive_cylinder_add(vertices=12, radius=0.55, depth=0.45, location=(bx, by, 0.38))
basket = bpy.context.active_object
basket.scale = (1.0, 1.0, 1.0)
for p in basket.data.polygons: p.use_smooth = False
basket.data.materials.append(mat_wicker)

# Basket Rim Lip
bpy.ops.mesh.primitive_cylinder_add(vertices=12, radius=0.60, depth=0.08, location=(bx, by, 0.60))
basket_rim = bpy.context.active_object
for p in basket_rim.data.polygons: p.use_smooth = False
basket_rim.data.materials.append(mat_wicker)

# Mound of Red Berries in basket
bpy.ops.mesh.primitive_cylinder_add(vertices=10, radius=0.50, depth=0.12, location=(bx, by, 0.58))
berry_mound = bpy.context.active_object
for p in berry_mound.data.polygons: p.use_smooth = False
berry_mound.data.materials.append(mat_berry)

# 8 Individual juicy red berry spheres on top
berry_coords = [
    (bx - 0.20, by - 0.15, 0.66),
    (bx + 0.18, by - 0.10, 0.67),
    (bx - 0.05, by + 0.20, 0.68),
    (bx + 0.22, by + 0.15, 0.66),
    (bx,       by,        0.71),
    (bx - 0.22, by + 0.05, 0.66),
    (bx + 0.10, by - 0.25, 0.65),
    (bx - 0.12, by - 0.28, 0.65),
]
for brx, bry, brz in berry_coords:
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2, radius=0.10, location=(brx, bry, brz))
    berry_dot = bpy.context.active_object
    for p in berry_dot.data.polygons: p.use_smooth = False
    berry_dot.data.materials.append(mat_berry)

# Secondary small wooden crate beside basket
bpy.ops.mesh.primitive_cube_add(size=1.0, location=(bx + 0.45, by + 0.45, 0.28))
crate = bpy.context.active_object
crate.scale = (0.50, 0.50, 0.26)
crate.rotation_euler.z = math.radians(20)
bpy.ops.object.transform_apply(scale=True)
for p in crate.data.polygons: p.use_smooth = False
crate.data.materials.append(mat_timber)

# ==============================================================================
# QUADRANT 4: EMPTY STARTER EXPANSION SLOT (South-East: X > 0, Y < 0)
# ==============================================================================
# Clean floor planks with corner demarcation pegs, showing game readiness
# (Nothing in this quadrant — cleanly reserved for new resource intake)

# ==============================================================================
# CAMERA & LIGHTING (ISOMETRIC SHOWCASE CLOSE-UP)
# ==============================================================================
cam_data = bpy.data.cameras.new("StorageCam")
cam_data.type = 'ORTHO'
cam_data.ortho_scale = 8.5   # Comfortable framing with safe margins >80px all sides
cam_obj = bpy.data.objects.new("StorageCam", cam_data)
sc.collection.objects.link(cam_obj)
sc.camera = cam_obj

pitch = math.radians(35)
yaw = math.radians(45)
dist = 30.0

tx, ty, tz = 0.0, 0.0, 0.35
cx = tx + dist * math.sin(yaw) * math.cos(pitch)
cy = ty - dist * math.cos(yaw) * math.cos(pitch)
cz = tz + dist * math.sin(pitch)
cam_obj.location = Vector((cx, cy, cz))

target = Vector((tx, ty, tz))
direction = target - cam_obj.location
rot_quat = direction.to_track_quat('-Z', 'Y')
cam_obj.rotation_euler = rot_quat.to_euler()

# Warm Ghibli Studio Lights
sun = bpy.data.objects.new("SunKey", bpy.data.lights.new("SunKey", 'SUN'))
sc.collection.objects.link(sun)
sun.data.energy = 3.4
sun.data.color = tt((255, 245, 225))
sun.rotation_euler = (math.radians(48), 0, math.radians(-40))

fill = bpy.data.objects.new("SunFill", bpy.data.lights.new("SunFill", 'SUN'))
sc.collection.objects.link(fill)
fill.data.energy = 0.45
fill.data.use_shadow = False
fill.data.color = tt((210, 225, 235))
fill.rotation_euler = (math.radians(60), 0, math.radians(140))

world = bpy.data.worlds.new("W")
sc.world = world
world.use_nodes = True
bg = world.node_tree.nodes["Background"]
bg.inputs[1].default_value = 0.80
bg.inputs[0].default_value = (*tt((215, 228, 235)), 1.0)

sc.render.engine = "BLENDER_EEVEE"
sc.render.resolution_x = 1920
sc.render.resolution_y = 1080
sc.view_settings.view_transform = "AgX"
sc.view_settings.look = "AgX - Base Contrast"

# Export GLB & Render PNG
bpy.ops.export_scene.gltf(
    filepath=out_glb,
    export_format='GLB',
    use_selection=False,
    export_apply=True
)
print(f"✅ Exported Starter Storage Tile GLB -> {out_glb}")

sc.render.filepath = out_img
bpy.ops.render.render(write_still=True)
print(f"📸 Starter Storage Tile Showcase Rendered -> {out_img}")

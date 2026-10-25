#!/usr/bin/env python3
"""
SCALE BENCHMARK SHOWCASE: TREE VS DEER VS BERRY BUSH VS HUMAN
Directly addresses Boss's feedback: "trees are too big compare to deers and berry bush."
Compares side-by-side:
1. Adult Human Villager (1.75m reference)
2. Berry Bush (1.0m)
3. Fawn (0.70m)
4. Doe (1.30m)
5. Alpha Stag (1.75m)
6. Old Over-scaled Oak (14.5m — TOO BIG)
7. Proposed Stylized Oak (4.8m — BALANCED 1:1 RTS COZY SCALE)
"""
import bpy
import math
import os
from mathutils import Vector, Matrix

out_dir = "~/projects/lpm-faceless-humanoid/assets/aoe_starter_pack"
out_img = os.path.join(out_dir, "showcase_scale_benchmark.png")

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene

def tt(c):
    return tuple(((x / 255.0) / 12.92) if (x / 255.0) <= 0.04045 else (((x / 255.0) + 0.055) / 1.055) ** 2.4 for x in c)

# Materials
mat_grass   = bpy.data.materials.new("M_Grass")
mat_grass.use_nodes = True
mat_grass.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (*tt((72, 122, 56)), 1.0)

mat_human   = bpy.data.materials.new("M_Human")
mat_human.use_nodes = True
mat_human.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (*tt((60, 110, 175)), 1.0) # Blue tunic

mat_skin    = bpy.data.materials.new("M_Skin")
mat_skin.use_nodes = True
mat_skin.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (*tt((225, 190, 160)), 1.0)

# Studio Ground Slab
bpy.ops.mesh.primitive_cube_add(size=1.0, location=(1.5, 0, -0.15))
stage = bpy.context.active_object
stage.scale = (27.0, 6.0, 0.30)
bpy.ops.object.transform_apply(scale=True)
for p in stage.data.polygons: p.use_smooth = False
stage.data.materials.append(mat_grass)

# 1. Human Villager Reference (Height = 1.75m)
hx = -8.0
bpy.ops.mesh.primitive_cylinder_add(vertices=8, radius=0.22, depth=0.90, location=(hx, 0, 0.85))
body = bpy.context.active_object
for p in body.data.polygons: p.use_smooth = False
body.data.materials.append(mat_human)

bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1, radius=0.18, location=(hx, 0, 1.55))
head = bpy.context.active_object
for p in head.data.polygons: p.use_smooth = False
head.data.materials.append(mat_skin)

# Legs
for lx in [-0.10, 0.10]:
    bpy.ops.mesh.primitive_cylinder_add(vertices=6, radius=0.08, depth=0.80, location=(hx + lx, 0, 0.40))
    leg = bpy.context.active_object
    for p in leg.data.polygons: p.use_smooth = False
    leg.data.materials.append(mat_human)

# 2. Berry Bush (Height ~1.0m)
bush_glb = "~/projects/lpm-faceless-humanoid/lpms_store/berry_bush/r_6fc81fa4/berry_bush.glb"
bpy.ops.import_scene.gltf(filepath=bush_glb)
bush = bpy.context.active_object
# parent or move
for o in bpy.data.objects:
    if 'berry_bush' in o.name or 'goc' in o.name or 'nhanh' in o.name or 'qua' in o.name:
        if o.parent is None:
            o.location = Vector((-5.5, 0, 0))
            o.scale = (1.1, 1.1, 1.1)

# 3. Deer Pack Entities
stag_glb   = "~/projects/lpm-faceless-humanoid/assets/organic/downloads/quaternius_deer/ab/stag_origami.glb"
doe_glb    = "~/projects/lpm-faceless-humanoid/assets/organic/downloads/quaternius_deer/doe_origami.glb"

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

# Fawn (0.55x, H ~ 0.70m)
spawn_static_posed_animal(doe_glb, "Bench_Fawn", "Eating", 50, (-3.5, 0, 0), yaw_deg=20, scale=0.55)
# Doe (1.10x, H ~ 1.30m)
spawn_static_posed_animal(doe_glb, "Bench_Doe",  "Eating", 50, (-1.5, 0, 0), yaw_deg=-30, scale=1.10)
# Alpha Stag (1.35x, H ~ 1.75m with antlers)
spawn_static_posed_animal(stag_glb, "Bench_Stag", "Idle",   0,  ( 1.0, 0, 0), yaw_deg=-45, scale=1.35)

# 4. Tree Comparisons
tree_soi = "~/projects/lpm-faceless-humanoid/lpms_store/oak_tree/r_4f5e6778/oak_tree.glb"

def import_tree(filepath, name, loc, scale):
    truoc = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=filepath)
    moi = [o for o in bpy.data.objects if o not in truoc]
    parent = bpy.data.objects.new(name, None)
    bpy.context.collection.objects.link(parent)
    parent.location = Vector(loc)
    parent.scale = (scale, scale, scale)
    for o in moi:
        if o.parent is None: o.parent = parent
        if o.type == 'MESH':
            for p in o.data.polygons: p.use_smooth = False
    return parent

# Proposed Balanced Stylized Oak: scale = 0.95 -> Height = 4.8m (Balanced 3x human height)
import_tree(tree_soi, "Proposed_Balanced_Oak", (4.8, 0, 0), scale=0.95)

# Old Over-scaled Oak: scale = 2.70 -> Height = 14.5m (GIANT, dwarfs everything)
import_tree(tree_soi, "Old_Overscaled_Oak", (11.5, 0, 0), scale=2.70)

# Camera Setup (Straight side-on isometric view with ample margins)
cam_data = bpy.data.cameras.new("BenchCam")
cam_data.type = 'ORTHO'
cam_data.ortho_scale = 32.0
cam_obj = bpy.data.objects.new("BenchCam", cam_data)
sc.collection.objects.link(cam_obj)
sc.camera = cam_obj

cam_obj.location = Vector((1.5, -38.0, 7.5))
target = Vector((1.5, 0.0, 5.5))
direction = target - cam_obj.location
cam_obj.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()

# Lights
sun = bpy.data.objects.new("Sun", bpy.data.lights.new("Sun", 'SUN'))
sc.collection.objects.link(sun)
sun.data.energy = 3.2
sun.data.color = tt((255, 245, 225))
sun.rotation_euler = (math.radians(45), 0, math.radians(-35))

world = bpy.data.worlds.new("W")
sc.world = world
world.use_nodes = True
bg = world.node_tree.nodes["Background"]
bg.inputs[1].default_value = 0.85
bg.inputs[0].default_value = (*tt((215, 228, 238)), 1.0)

sc.render.engine = "BLENDER_EEVEE"
sc.render.resolution_x = 1920
sc.render.resolution_y = 1080
sc.view_settings.view_transform = "AgX"

sc.render.filepath = out_img
bpy.ops.render.render(write_still=True)
print(f"📸 Scale Benchmark Render Complete -> {out_img}")

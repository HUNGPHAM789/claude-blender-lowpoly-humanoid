#!/usr/bin/env python3
"""
Dedicated Showcase Render of the LPM Origami Deer Pack
Displays all 7 members of the herd in high detail with authentic poses:
- Alpha Stag (alert pose with proud antlers)
- 3 Does (grazing & alert)
- 2 Yearlings (grazing & walking)
- 1 Fawn (grazing baby deer)
- Ground contact at Z=0.0m on lush Ghibli meadow.
"""
import bpy
import math
import os
from mathutils import Vector, Matrix

out_path = "~/projects/lpm-faceless-humanoid/assets/aoe_starter_pack/showcase_deer_pack.png"

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene

def tt(c):
    return tuple(((x / 255.0) / 12.92) if (x / 255.0) <= 0.04045 else (((x / 255.0) + 0.055) / 1.055) ** 2.4 for x in c)

# Ground plane with Ghibli grass material
mat_grass = bpy.data.materials.new(name="M_GhibliGrass")
mat_grass.use_nodes = True
bsdf = mat_grass.node_tree.nodes.get("Principled BSDF")
bsdf.inputs["Base Color"].default_value = (*tt((72, 122, 56)), 1.0)
bsdf.inputs["Roughness"].default_value = 0.90

bpy.ops.mesh.primitive_cylinder_add(vertices=32, radius=30.0, depth=0.2, location=(0, 0, -0.10))
ground = bpy.context.active_object
for p in ground.data.polygons: p.use_smooth = False
ground.data.materials.append(mat_grass)

stag_glb = "~/projects/lpm-faceless-humanoid/assets/organic/downloads/quaternius_deer/ab/stag_origami.glb"
doe_glb  = "~/projects/lpm-faceless-humanoid/assets/organic/downloads/quaternius_deer/doe_origami.glb"
grass_tuft = "~/projects/lpm-faceless-humanoid/lpms_store/grass_a_m/r_c01a764e/grass_a_m.glb"
fl_red   = "~/projects/GameDev/assets/downloads/cgtrader_forest/glb/Flower_bush_red.glb"
fl_blue  = "~/projects/GameDev/assets/downloads/cgtrader_forest/glb/Flower_bush_blue.glb"

def import_prop(filepath, name, loc, rot_z_deg=0.0, scale=1.0):
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

def spawn_posed_deer(filepath, name, action_name, frame, loc, yaw_deg, scale):
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

# Herd of 7 deer arranged in natural glade
spawn_posed_deer(stag_glb, "Deer_AlphaStag", "Idle",    0,  ( 0.0,  0.6, 0.0), yaw_deg=-25, scale=1.35)
spawn_posed_deer(doe_glb,  "Deer_Doe_Alert", "Idle",    0,  (-2.6, -0.8, 0.0), yaw_deg=45,  scale=1.10)
spawn_posed_deer(doe_glb,  "Deer_Doe_Graze1","Eating",  50, ( 2.2,  0.2, 0.0), yaw_deg=-115,scale=1.10)
spawn_posed_deer(doe_glb,  "Deer_Doe_Graze2","Eating",  55, (-1.2,  2.2, 0.0), yaw_deg=75,  scale=1.05)
spawn_posed_deer(doe_glb,  "Deer_Yearling1", "Eating",  50, ( 3.6, -1.2, 0.0), yaw_deg=65,  scale=0.82)
spawn_posed_deer(doe_glb,  "Deer_Yearling2", "Walk",    10, (-3.8,  1.5, 0.0), yaw_deg=-65, scale=0.85)
spawn_posed_deer(doe_glb,  "Deer_Fawn",      "Eating",  50, (-2.0, -1.8, 0.0), yaw_deg=25,  scale=0.55)

# Flowers and grass tufts scattered around
for gx, gy in [(-1.5, 0.5), (1.2, -1.0), (3.0, 1.5), (-3.0, -1.0), (0.5, 2.5), (-0.5, -2.0)]:
    import_prop(grass_tuft, "Grass", (gx, gy, 0.0), rot_z_deg=gx*50, scale=1.5)

import_prop(fl_red, "Fl_1", (1.0, -1.8, 0.0), rot_z_deg=30, scale=1.2)
import_prop(fl_blue, "Fl_2", (-3.5, 0.2, 0.0), rot_z_deg=-45, scale=1.1)
import_prop(fl_red, "Fl_3", (-0.8, 3.0, 0.0), rot_z_deg=80, scale=1.2)

bpy.context.view_layer.update()

# Camera: Close 3/4 Isometric Framing
cam_data = bpy.data.cameras.new("DeerCam")
cam_data.type = 'ORTHO'
cam_data.ortho_scale = 8.5
cam_obj = bpy.data.objects.new("DeerCam", cam_data)
sc.collection.objects.link(cam_obj)
sc.camera = cam_obj

pitch = math.radians(24)
yaw = math.radians(45)
dist = 35.0
tx, ty, tz = 0.0, 0.2, 0.75
cx = tx + dist * math.sin(yaw) * math.cos(pitch)
cy = ty - dist * math.cos(yaw) * math.cos(pitch)
cz = tz + dist * math.sin(pitch)
cam_obj.location = Vector((cx, cy, cz))
target = Vector((tx, ty, tz))
cam_obj.rotation_euler = (target - cam_obj.location).to_track_quat('-Z', 'Y').to_euler()

# Ghibli Sunlight
sun = bpy.data.objects.new("SunKey", bpy.data.lights.new("SunKey", 'SUN'))
sc.collection.objects.link(sun)
sun.data.energy = 3.2
sun.data.angle = math.radians(3)
sun.data.color = tt((255, 242, 218))
sun.rotation_euler = (math.radians(46), 0, math.radians(-38))

fill = bpy.data.objects.new("SunFill", bpy.data.lights.new("SunFill", 'SUN'))
sc.collection.objects.link(fill)
fill.data.energy = 0.40
fill.data.use_shadow = False
fill.data.color = tt((202, 218, 228))
fill.rotation_euler = (math.radians(65), 0, math.radians(150))

world = bpy.data.worlds.new("W")
sc.world = world
world.use_nodes = True
bg = world.node_tree.nodes["Background"]
bg.inputs[1].default_value = 0.75
bg.inputs[0].default_value = (*tt((202, 218, 228)), 1.0)

sc.render.engine = "BLENDER_EEVEE"
sc.render.resolution_x = 1920
sc.render.resolution_y = 1080
sc.view_settings.view_transform = "AgX"
sc.view_settings.look = "AgX - Base Contrast"

sc.render.filepath = out_path
bpy.ops.render.render(write_still=True)
print(f"📸 Deer Pack Showcase Rendered -> {out_path}")

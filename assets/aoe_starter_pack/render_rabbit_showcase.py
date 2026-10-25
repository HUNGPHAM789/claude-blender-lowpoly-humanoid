#!/usr/bin/env python3
"""
Dedicated Showcase Render of the LPM Origami Rabbits
Displays the 4 rabbits up close in high detail on lush Ghibli meadow.
"""
import bpy
import math
import os
from mathutils import Vector

out_path = "~/projects/lpm-faceless-humanoid/assets/aoe_starter_pack/showcase_rabbits.png"

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

bpy.ops.mesh.primitive_cylinder_add(vertices=32, radius=25.0, depth=0.2, location=(0, 0, -0.10))
ground = bpy.context.active_object
for p in ground.data.polygons: p.use_smooth = False
ground.data.materials.append(mat_grass)

rabbit_glb = "~/projects/lpm-faceless-humanoid/assets/organic/rabbit_v1/rabbit.glb"
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
            for mat in o.data.materials:
                if mat and 'cream' in mat.name.lower():
                    bsdf = mat.node_tree.nodes.get("Principled BSDF") if mat.node_tree else None
                    if bsdf and "Base Color" in bsdf.inputs:
                        # Harmonize rabbit chest from harsh stark cream to natural warm underbelly
                        bsdf.inputs["Base Color"].default_value = (0.74, 0.66, 0.56, 1.0)
    return parent

# 4 Origami Rabbits
import_prop(rabbit_glb, "Rabbit_Alpha", ( 0.0,  0.2, 0.0), rot_z_deg=35,  scale=1.6)
import_prop(rabbit_glb, "Rabbit_Doe1",  (-1.2, -0.4, 0.0), rot_z_deg=-55, scale=1.4)
import_prop(rabbit_glb, "Rabbit_Doe2",  ( 1.3, -0.3, 0.0), rot_z_deg=105, scale=1.45)
import_prop(rabbit_glb, "Rabbit_Bunny", ( 0.4,  1.1, 0.0), rot_z_deg=-45, scale=1.05)

# Flowers and grass
import_prop(grass_tuft, "Grass_1", (-0.7, 0.6, 0.0), rot_z_deg=20, scale=1.2)
import_prop(grass_tuft, "Grass_2", (0.8, 0.5, 0.0), rot_z_deg=-40, scale=1.1)
import_prop(fl_red, "Fl_Red", (-1.8, 0.5, 0.0), rot_z_deg=50, scale=1.0)
import_prop(fl_blue, "Fl_Blue", (1.8, 0.8, 0.0), rot_z_deg=-30, scale=1.0)

bpy.context.view_layer.update()

# Camera: Close Isometric
cam_data = bpy.data.cameras.new("RabCam")
cam_data.type = 'ORTHO'
cam_data.ortho_scale = 3.6
cam_obj = bpy.data.objects.new("RabCam", cam_data)
sc.collection.objects.link(cam_obj)
sc.camera = cam_obj

pitch = math.radians(22)
yaw = math.radians(45)
dist = 20.0
tx, ty, tz = 0.1, 0.2, 0.35
cx = tx + dist * math.sin(yaw) * math.cos(pitch)
cy = ty - dist * math.cos(yaw) * math.cos(pitch)
cz = tz + dist * math.sin(pitch)
cam_obj.location = Vector((cx, cy, cz))
cam_obj.rotation_euler = (Vector((tx, ty, tz)) - cam_obj.location).to_track_quat('-Z', 'Y').to_euler()

# Ghibli Light
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
print(f"📸 Rabbit Showcase Rendered -> {out_path}")

"""Render isometric EEVEE frames of an action from rabbit_rig.blend.
blender -b rabbit_rig.blend -P render_loops.py -- <action> <outdir> [res] [frames comma list]
Isometric: azimuth 45 deg (front-right of a rabbit facing -Y), elevation 35.264 deg, orthographic.
Camera follows the root bone along world Y only (travel), floor checker period 0.18 m so a 0.36 m hop loops cleanly.
"""
import bpy, math, sys, os
from mathutils import Vector

argv = sys.argv[sys.argv.index("--") + 1:]
act_name, outdir = argv[0], argv[1]
res = int(argv[2]) if len(argv) > 2 else 640
only = [int(x) for x in argv[3].split(",")] if len(argv) > 3 else None
os.makedirs(outdir, exist_ok=True)
scn = bpy.context.scene
arm = bpy.data.objects["rabbit_rig"]
act = bpy.data.actions[act_name]
arm.animation_data.action = act
if hasattr(arm.animation_data, "action_suitable_slots") and arm.animation_data.action_slot is None:
    arm.animation_data.action_slot = arm.animation_data.action_suitable_slots[0]
f0, f1 = map(int, act.frame_range)

try:
    scn.render.engine = "BLENDER_EEVEE"
except TypeError as e:
    print(e)
scn.eevee.taa_render_samples = 16
scn.render.resolution_x = scn.render.resolution_y = res
scn.render.image_settings.file_format = "PNG"
scn.render.film_transparent = False
scn.view_settings.view_transform = "Standard"

# world
w = bpy.data.worlds.new("w"); scn.world = w; w.use_nodes = True
bg = next(n for n in w.node_tree.nodes if n.type == "BACKGROUND")
bg.inputs[0].default_value = (0.86, 0.87, 0.85, 1); bg.inputs[1].default_value = 0.45

# floor with world-space checker (period 0.18 m)
bpy.ops.mesh.primitive_plane_add(size=12, location=(0, -2, 0))
floor = bpy.context.active_object
m = bpy.data.materials.new("floor"); m.use_nodes = True; nt = m.node_tree
bsdf = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
geo = nt.nodes.new("ShaderNodeNewGeometry")
sep = nt.nodes.new("ShaderNodeSeparateXYZ"); nt.links.new(geo.outputs["Position"], sep.inputs[0])
def fl(sock):
    d = nt.nodes.new("ShaderNodeMath"); d.operation = "DIVIDE"; nt.links.new(sock, d.inputs[0]); d.inputs[1].default_value = 0.09
    f = nt.nodes.new("ShaderNodeMath"); f.operation = "FLOOR"; nt.links.new(d.outputs[0], f.inputs[0]); return f.outputs[0]
add = nt.nodes.new("ShaderNodeMath"); add.operation = "ADD"
nt.links.new(fl(sep.outputs[0]), add.inputs[0]); nt.links.new(fl(sep.outputs[1]), add.inputs[1])
mod = nt.nodes.new("ShaderNodeMath"); mod.operation = "FLOORED_MODULO"; nt.links.new(add.outputs[0], mod.inputs[0]); mod.inputs[1].default_value = 2
mix = nt.nodes.new("ShaderNodeMix"); mix.data_type = "RGBA"
nt.links.new(mod.outputs[0], mix.inputs["Factor"])
mix.inputs["A"].default_value = (0.62, 0.66, 0.58, 1); mix.inputs["B"].default_value = (0.55, 0.6, 0.5, 1)
nt.links.new(mix.outputs["Result"], bsdf.inputs["Base Color"]); bsdf.inputs["Roughness"].default_value = 0.95
floor.data.materials.append(m)

# light
sun = bpy.data.objects.new("sun", bpy.data.lights.new("sun", "SUN"))
sun.data.energy = 2.2; sun.rotation_euler = (math.radians(40), math.radians(15), math.radians(30))
scn.collection.objects.link(sun)

# isometric ortho camera
cam_data = bpy.data.cameras.new("iso"); cam_data.type = "ORTHO"; cam_data.ortho_scale = 1.55
cam = bpy.data.objects.new("iso", cam_data); scn.collection.objects.link(cam); scn.camera = cam
az, el = math.radians(45), math.radians(35.264)
target = Vector((0, -0.05, 0.42))
d = Vector((math.cos(el) * math.sin(az), -math.cos(el) * math.cos(az), math.sin(el)))  # front-right, above
cam.location = target + d * 6
cam.rotation_euler = (-d).to_track_quat("-Z", "Y").to_euler()
cam_data.clip_end = 50
c = cam.constraints.new("COPY_LOCATION"); c.target = arm; c.subtarget = "root"
c.use_x = False; c.use_z = False; c.use_offset = True

frames = only if only else list(range(f0, f1))  # last key == first key: skip it for a seamless loop
for f in frames:
    scn.frame_set(f)
    scn.render.filepath = os.path.join(outdir, f"f{f:03d}.png")
    bpy.ops.render.render(write_still=True)
print("RENDERED", act_name, len(frames))

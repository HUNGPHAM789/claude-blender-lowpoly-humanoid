"""Blender: play one action BAKED in a game GLB (bake_clips_blender.py) and render every frame — proof the exported file itself animates.

  blender -b -P play_baked_blender.py -- <game.glb> <action> <out_dir>      → <out_dir>/<f>.png (front ¾, lit, white)
"""
import bpy, sys, math, os
a = sys.argv[sys.argv.index("--") + 1:]
src, act_name, out = a[0], a[1], a[2]
os.makedirs(out, exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True); bpy.ops.import_scene.gltf(filepath=src)
sc = bpy.context.scene
rig = next(o for o in sc.objects if o.type == "ARMATURE"); rig.hide_render = True
ad = rig.animation_data
for tr in ad.nla_tracks: tr.mute = True
act = next(x for x in bpy.data.actions if x.name.split("_rig")[0] == act_name or x.name == act_name or x.name.startswith(act_name + "_"))
ad.action = act
f0, f1 = (int(round(x)) for x in act.frame_range)
for eng in ("BLENDER_EEVEE_NEXT", "BLENDER_EEVEE"):
    try: sc.render.engine = eng; break
    except TypeError: pass
sc.view_settings.view_transform = "Standard"; sc.render.resolution_x, sc.render.resolution_y = 480, 720
w = bpy.data.worlds.new("w"); sc.world = w; w.use_nodes = True
bg = next(n for n in w.node_tree.nodes if n.type == "BACKGROUND"); bg.inputs[0].default_value = (1, 1, 1, 1); bg.inputs[1].default_value = 1.0
for nm, en, rot in (("key", 3.5, (55, 0, -35)), ("fill", 1.5, (60, 0, 140)), ("rim", 1.2, (60, 0, 200))):
    L_ = bpy.data.objects.new(nm, bpy.data.lights.new(nm, "SUN")); sc.collection.objects.link(L_); L_.data.energy = en
    L_.rotation_euler = tuple(math.radians(x) for x in rot)
cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam")); sc.collection.objects.link(cam); sc.camera = cam
cam.data.type = "ORTHO"; cam.data.ortho_scale = 2.1; aa = math.radians(35)
cam.location = (6 * math.sin(aa), -6 * math.cos(aa), 0.9); cam.rotation_euler = (math.radians(90), 0, aa)
for f in range(f0, f1 + 1):
    sc.frame_set(f); sc.render.filepath = os.path.join(out, f"{f:04d}.png"); bpy.ops.render.render(write_still=True)
print(f"played {act.name} {f0}-{f1} → {out}")

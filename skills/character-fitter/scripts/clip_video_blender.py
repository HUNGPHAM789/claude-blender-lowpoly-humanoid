"""Blender: render an OLD settler clip played on a rigged, dressed character — every frame, two views (front ¾ and back ¾), lit on white —
for the Boss's eye (Boss 25/10/2026: «Gửi video stream mấy cái animation cho tôi xem»). Same retarget as clip_check_blender.py.

  blender -b -P clip_video_blender.py -- <rigged.glb> <clip.glb> <out_dir>      → <out_dir>/<view>_%04d.png
then ffmpeg hstack the two views (see character-fitter SKILL.md).
"""
import bpy, sys, math, os
from mathutils import Vector

a = sys.argv[sys.argv.index("--") + 1:]
char, clip, out = a[0], a[1], a[2]
os.makedirs(out, exist_ok=True)
SKIP = ("ik_", "pole_")
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=char)
sc = bpy.context.scene
rig = next(o for o in sc.objects if o.type == "ARMATURE")
for o in sc.objects:
    if o.type == "MESH" and o.parent != rig and not any(m.type == "ARMATURE" for m in o.modifiers): o.hide_render = True
for pb in rig.pose.bones:
    pb.rotation_mode = "QUATERNION"
    for c in pb.constraints: c.influence = 0.0
order = [b.name for b in rig.data.bones if not b.name.startswith(SKIP)]
hips_h = rig.data.bones["hips"].head_local.z
before = set(bpy.data.objects)
bpy.ops.import_scene.gltf(filepath=clip)
new = [o for o in bpy.data.objects if o not in before]
src = next(o for o in new if o.type == "ARMATURE")
for o in new:
    if o is not src: o.hide_render = True
act = src.animation_data.action if src.animation_data and src.animation_data.action else None
if act is None:
    act = next(st.action for tr in src.animation_data.nla_tracks for st in tr.strips if st.action)
    for tr in src.animation_data.nla_tracks: tr.mute = True
    src.animation_data.action = act
f0, f1 = (int(round(x)) for x in act.frame_range)
k = hips_h / max(src.data.bones["hips"].head_local.z, 1e-6)

for eng in ("BLENDER_EEVEE_NEXT", "BLENDER_EEVEE"):
    try: sc.render.engine = eng; break
    except TypeError: pass
sc.view_settings.view_transform = "Standard"; sc.render.resolution_x, sc.render.resolution_y = 480, 640; sc.render.film_transparent = False
w = bpy.data.worlds.new("w"); sc.world = w; w.use_nodes = True
bg = next(n for n in w.node_tree.nodes if n.type == "BACKGROUND"); bg.inputs[0].default_value = (1, 1, 1, 1); bg.inputs[1].default_value = 1.0
for nm, en, rot in (("key", 3.5, (55, 0, -35)), ("fill", 1.5, (60, 0, 140)), ("rim", 1.2, (60, 0, 200))):
    L_ = bpy.data.objects.new(nm, bpy.data.lights.new(nm, "SUN")); sc.collection.objects.link(L_); L_.data.energy = en
    L_.rotation_euler = tuple(math.radians(x) for x in rot)
cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam")); sc.collection.objects.link(cam); sc.camera = cam
cam.data.type = "ORTHO"; cam.data.ortho_scale = 1.25
for f in range(f0, f1 + 1):
    sc.frame_set(f)
    for pb in rig.pose.bones: pb.rotation_quaternion = (1, 0, 0, 0); pb.location = (0, 0, 0)
    bpy.context.view_layer.update()
    for n in order:
        if n not in src.pose.bones: continue
        Ps = src.pose.bones[n].matrix.to_3x3(); Rs = src.data.bones[n].matrix_local.to_3x3()
        Rc = rig.data.bones[n].matrix_local.to_3x3(); pc = rig.pose.bones[n]
        M = (Ps @ Rs.inverted() @ Rc).to_4x4(); M.translation = pc.matrix.translation
        if n == "hips":
            M.translation = rig.data.bones[n].head_local + (src.pose.bones[n].matrix.translation - src.data.bones[n].head_local) * k
            M.translation.y = rig.data.bones[n].head_local.y
        pc.matrix = M; bpy.context.view_layer.update()
    for view, yaw in (("front", 35), ("back", 215)):
        aa = math.radians(yaw); cam.location = (6 * math.sin(aa), -6 * math.cos(aa), 0.92); cam.rotation_euler = (math.radians(90), 0, aa)
        sc.render.filepath = os.path.join(out, f"{view}_{f:04d}.png"); bpy.ops.render.render(write_still=True)
print(f"rendered {f1 - f0 + 1} frames × 2 views → {out}")

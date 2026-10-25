"""Blender: bake settler clips onto a rigged, dressed character → ONE game GLB holding the character + every clip as its own action
(Boss 25/10/2026: «gom thành 1 folder toàn bộ everything để tôi nộp phiên khác làm game»). Same retarget as clip_check_blender.py.

  blender -b -P bake_clips_blender.py -- <rigged.glb> <out.glb> <name>=<clip.glb> [<name>=<clip.glb> …]

Each clip becomes an action named <name> on the character's armature (pushed to its own NLA track so the glTF exporter writes them all);
props and the source armatures are not exported.
"""
import bpy, sys

a = sys.argv[sys.argv.index("--") + 1:]
char, out = a[0], a[1]
pairs = [x.split("=", 1) for x in a[2:]]
SKIP = ("ik_", "pole_")
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=char)
sc = bpy.context.scene
rig = next(o for o in sc.objects if o.type == "ARMATURE")
for pb in rig.pose.bones:
    pb.rotation_mode = "QUATERNION"
    for c in pb.constraints: c.influence = 0.0
order = [b.name for b in rig.data.bones if not b.name.startswith(SKIP)]
hips_h = rig.data.bones["hips"].head_local.z
rig.animation_data_create()
keep_actions = []
for name, clip in pairs:
    before = set(bpy.data.objects); acts0 = set(bpy.data.actions)
    bpy.ops.import_scene.gltf(filepath=clip)
    new = [o for o in bpy.data.objects if o not in before]
    src = next(o for o in new if o.type == "ARMATURE")
    act = src.animation_data.action if src.animation_data and src.animation_data.action else None
    if act is None:
        act = next(st.action for tr in src.animation_data.nla_tracks for st in tr.strips if st.action)
        for tr in src.animation_data.nla_tracks: tr.mute = True
        src.animation_data.action = act
    f0, f1 = (int(round(x)) for x in act.frame_range)
    k = hips_h / max(src.data.bones["hips"].head_local.z, 1e-6)
    dst = bpy.data.actions.new(name); rig.animation_data.action = dst
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
        for n in order:
            pb = rig.pose.bones[n]; pb.keyframe_insert("rotation_quaternion", frame=f, group=n)
            if n == "hips": pb.keyframe_insert("location", frame=f, group=n)
    tr = rig.animation_data.nla_tracks.new(); tr.name = name
    st = tr.strips.new(name, f0, dst); st.name = name
    rig.animation_data.action = None; keep_actions.append(dst)
    for o in new: bpy.data.objects.remove(o, do_unlink=True)
    for ac in list(bpy.data.actions):
        if ac not in keep_actions: bpy.data.actions.remove(ac)
    print(f"baked {name}: frames {f0}-{f1} from {clip}")
for pb in rig.pose.bones: pb.rotation_quaternion = (1, 0, 0, 0); pb.location = (0, 0, 0)
for o in list(sc.objects):                                             # helpers that rode along in the rigged file
    if o.type == "MESH" and o.parent != rig and not any(m.type == "ARMATURE" for m in o.modifiers): bpy.data.objects.remove(o, do_unlink=True)
bpy.ops.object.select_all(action="SELECT")
bpy.ops.export_scene.gltf(filepath=out, export_format="GLB", export_skins=True, export_animations=True)
print(f"→ {out} with actions {[ac.name for ac in keep_actions]}")

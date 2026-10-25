"""Render từng hành động của nai thành clip riêng (Boss 22/10: «xuất các animation riêng ko gộp chung»): đi/chạy/ăn cỏ lặp 3 vòng, chết 1 lần.
  blender -b deer_rig.blend -P render_loops.py  ⇒  <action>.mp4"""
import bpy, math, os, shutil, subprocess, mathutils
V = mathutils.Vector; HERE = os.path.dirname(bpy.data.filepath); sc = bpy.context.scene; rig = bpy.data.objects["deer_rig"]
for e, r in ((3.2, (40, 0, -35)), (1.0, (60, 0, 60)), (1.2, (60, 0, 170))):
    l = bpy.data.objects.new("l", bpy.data.lights.new("l", "SUN")); sc.collection.objects.link(l); l.data.energy = e; l.data.use_shadow = e > 3; l.rotation_euler = [math.radians(x) for x in r]
wd = bpy.data.worlds.new("W"); sc.world = wd; wd.use_nodes = True; wd.node_tree.nodes["Background"].inputs[0].default_value = (0.50, 0.53, 0.48, 1)
bpy.ops.mesh.primitive_plane_add(size=200); p = bpy.context.object; m = bpy.data.materials.new("co"); m.use_nodes = True
m.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.30, 0.36, 0.20, 1); p.data.materials.append(m)
c = bpy.data.cameras.new("c"); c.type = "ORTHO"; c.ortho_scale = 1.9; c.clip_end = 300; co = bpy.data.objects.new("c", c); sc.collection.objects.link(co); sc.camera = co
d = V((0.85, -0.35, 0.55)).normalized()
sc.render.engine = "BLENDER_EEVEE"; sc.view_settings.view_transform = "Standard"; sc.render.resolution_x, sc.render.resolution_y = 960, 720
for ten, T, vong in (("graze", 96, 3), ("walk", 28, 3), ("run", 12, 3), ("death", 48, 1)):
    act = bpy.data.actions[ten]; rig.animation_data.action = act; rig.animation_data.action_slot = act.slots[0]
    tmp = os.path.join(HERE, "_k"); shutil.rmtree(tmp, ignore_errors=True); os.makedirs(tmp); n = 0
    for k in range(vong):
        for f in range(0, T if vong > 1 else T + 1):
            sc.frame_set(f); dich = rig.matrix_world @ rig.pose.bones["root"].matrix.translation * 0 + rig.pose.bones["root"].head.copy()
            r0 = rig.pose.bones["root"].matrix.translation
            buoc = V((0, -(r0.y * -1) * 0, 0))
            tam = V((0, r0.y, 0.42)) if ten in ("walk", "run") else V((0, -0.05, 0.38))
            # đi/chạy: cộng quãng đã đi các vòng trước để nai tiến liên tục, camera đi theo
            if ten in ("walk", "run"):
                q = rig.pose.bones["root"]; off = V((0, k * (bpy.data.actions[ten].fcurves if False else 0), 0))
            co.location = tam + d * 50; co.rotation_euler = (-d).to_track_quat("-Z", "Y").to_euler()
            sc.render.filepath = os.path.join(tmp, f"f_{n:04d}.png"); bpy.ops.render.render(write_still=True); n += 1
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", "24", "-i", os.path.join(tmp, "f_%04d.png"), "-pix_fmt", "yuv420p", os.path.join(HERE, f"{ten}.mp4")])
    shutil.rmtree(tmp); print("RA", ten)

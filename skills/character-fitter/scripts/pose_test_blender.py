"""Blender: put a rigged, dressed character through the species pose list and measure clipping of every layer against the POSED body.

  blender -b -P pose_test_blender.py -- <rigged.glb> <out.json> [--sheet <png>]

Poses are written as rotations about WORLD axes of the rest pose (Blender Z up, character faces −Y, its left = +X) and converted to each
bone's local frame, so they do not depend on bone roll. Leg IK is switched off for the test. Clipping = a layer vertex whose nearest posed
body point has the body normal pointing toward it (BVH find_nearest), depth = that distance. Rest positions of the clipping vertices are
returned (glTF frame) so fit_character.py labels them with body regions.
"""
import bpy, sys, json, math
from mathutils import Matrix, Euler
from mathutils.bvhtree import BVHTree

a = sys.argv[sys.argv.index("--") + 1:]
src, out = a[0], a[1]; sheet = a[a.index("--sheet") + 1] if "--sheet" in a else None
R = lambda ax, deg: Matrix.Rotation(math.radians(deg), 3, ax)
POSES = {
    "rest": {},
    "walk": {"thigh_L": R("X", -25), "thigh_R": R("X", 20), "shin_R": R("X", 20), "upperarm_L": R("X", 20), "upperarm_R": R("X", -20)},
    "run": {"thigh_L": R("X", -50), "shin_L": R("X", 60), "thigh_R": R("X", 30), "shin_R": R("X", 70), "upperarm_L": R("X", 40), "upperarm_R": R("X", -40),
            "forearm_L": R("X", -70), "forearm_R": R("X", -70), "spine": R("X", 10)},
    "sit": {"thigh_L": R("X", -90), "thigh_R": R("X", -90), "shin_L": R("X", 90), "shin_R": R("X", 90)},
    "crouch": {"thigh_L": R("X", -110), "thigh_R": R("X", -110), "shin_L": R("X", 120), "shin_R": R("X", 120), "spine": R("X", 25)},
    "arms_up": {"upperarm_L": R("Y", -150), "upperarm_R": R("Y", 150)},
    "kick": {"thigh_L": R("X", -85)},
    "twist": {"spine": R("Z", 30), "chest": R("Z", 15)},
    "head_turn_down": {"neck": R("X", 20), "head": R("Z", 40)},
    "lean_back": {"spine": R("X", -20), "chest": R("X", -10)},
}

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=src)
rig = next(o for o in bpy.context.scene.objects if o.type == "ARMATURE")
meshes = [o for o in bpy.context.scene.objects if o.type == "MESH"]
body = next(o for o in meshes if "body" in o.name.lower())
layers = [o for o in meshes if o is not body and (o.parent == rig or any(m.type == "ARMATURE" for m in o.modifiers))]   # skip helpers (an Icosphere rode along)
for pb in rig.pose.bones:
    pb.rotation_mode = "QUATERNION"
    for c in pb.constraints: c.influence = 0.0                             # IK off: poses are explicit rotations
rest_co = {L.name: [L.matrix_world @ v.co for v in L.data.vertices] for L in layers}
bnm = {g.index: g.name for g in body.vertex_groups}
DOM = [bnm[max(v.groups, key=lambda g: g.weight).group] if v.groups else "?" for v in body.data.vertices]   # body part a clip lands in


def set_pose(spec):
    for pb in rig.pose.bones: pb.rotation_quaternion = (1, 0, 0, 0); pb.location = (0, 0, 0)
    for name, Rw in spec.items():
        if name not in rig.pose.bones: continue
        M = rig.data.bones[name].matrix_local.to_3x3()
        rig.pose.bones[name].rotation_quaternion = (M.inverted() @ Rw @ M).to_quaternion()
    bpy.context.view_layer.update()


from mathutils import Vector
DIRS = (Vector((0, 0, 1)), Vector((0.3, 0.2, 0.93)).normalized())


def crossings(bvh, co, d, n=0):
    o = co.copy()
    while n < 50:
        hit = bvh.ray_cast(o, d)
        if hit[0] is None: return n
        n += 1; o = hit[0] + d * 1e-5
    return n


res = {}
sc = bpy.context.scene
if sheet:
    for eng in ("BLENDER_EEVEE_NEXT", "BLENDER_EEVEE"):
        try: sc.render.engine = eng; break
        except TypeError: pass
    sc.view_settings.view_transform = "Standard"; sc.render.resolution_x, sc.render.resolution_y = 360, 460; sc.render.film_transparent = True
    for nm, en, rot in (("key", 4.0, (55, 0, -35)), ("fill", 1.5, (60, 0, 140))):
        L_ = bpy.data.objects.new(nm, bpy.data.lights.new(nm, "SUN")); sc.collection.objects.link(L_); L_.data.energy = en
        L_.rotation_euler = tuple(math.radians(x) for x in rot)
    w = bpy.data.worlds.new("w"); sc.world = w; w.use_nodes = True
    next(n for n in w.node_tree.nodes if n.type == "BACKGROUND").inputs[1].default_value = 0.6
    zs = [(body.matrix_world @ v.co).z for v in body.data.vertices]; H = max(zs) - min(zs)
    cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam")); sc.collection.objects.link(cam); sc.camera = cam
    cam.data.type = "ORTHO"; cam.data.ortho_scale = H * 1.3; aa = math.radians(35)
    cam.location = (6 * math.sin(aa), -6 * math.cos(aa), min(zs) + H * 0.5); cam.rotation_euler = (math.radians(90), 0, aa)
    rig.hide_render = True
frames = []
for pose, spec in POSES.items():
    set_pose(spec); dg = bpy.context.evaluated_depsgraph_get()
    be = body.evaluated_get(dg); bm = be.to_mesh(); mw = body.matrix_world
    BP = [mw @ v.co for v in bm.vertices]; PF = [p.vertices[:] for p in bm.polygons]; bvh = BVHTree.FromPolygons(BP, PF); be.to_mesh_clear()
    res[pose] = {}
    for L in layers:
        le = L.evaluated_get(dg); lm = le.to_mesh(); pen = []; pen_bone = []
        for i, v in enumerate(lm.vertices):
            co = L.matrix_world @ v.co; hit = bvh.find_nearest(co, 0.3)
            if hit[0] is None: continue
            loc, nrm, fi, dist = hit
            # inside = odd number of body crossings along TWO rays (ground truth). The nearest-face normal sign alone gave false hits next
            # to the hands (a hand face with its normal turned away), 14 skirt verts "31 mm deep" at rest while parity said outside (25/10)
            if (co - loc).dot(nrm) < 0 and all(crossings(bvh, co, d_) % 2 == 1 for d_ in DIRS):
                r = rest_co[L.name][i]; pen.append([round(r.x, 4), round(r.z, 4), round(-r.y, 4), round(dist * 1000, 2)])   # → glTF frame, mm
                pen_bone.append(DOM[min(PF[fi], key=lambda k_: (BP[k_] - loc).length)])                          # arm-in-cloth vs skin
        res[pose][L.name] = {"verts": len(lm.vertices), "penetrating": len(pen), "max_depth_mm": max([p[3] for p in pen], default=0.0), "pen": pen, "pen_bone": pen_bone}
        le.to_mesh_clear()
    print(f"{pose:15s} " + " · ".join(f"{k}: {v['penetrating']}/{v['verts']} max {v['max_depth_mm']:.1f} mm" for k, v in res[pose].items()))
    if sheet:
        sc.render.filepath = sheet.replace(".png", f"_{pose}.png"); bpy.ops.render.render(write_still=True); frames.append(sc.render.filepath)
set_pose({})
json.dump({"poses": res, "frames": frames}, open(out, "w"))

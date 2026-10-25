"""Rig + animate the static low-poly rabbit (rabbit_v1/rabbit.glb).

Run: blender -b -P build_rig.py
Outputs (next to this script): rabbit_rig.blend, rabbit_rigged.glb, checks.json

Conventions (Blender space, Z-up, rabbit faces -Y):
  every bone is rolled so its local X == world +X. Rotation about local X (rotation_euler.x, degrees here):
  + rotates "up -> forward(-Y) -> down -> backward". So for a leg pointing down, + swings it backward;
  for the head (pointing forward), + pitches the nose down.
  root bone points straight up: pose loc.y = world up, loc.z = world forward (-Y).
"""
import bpy, bmesh, json, math, os, sys
from mathutils import Vector, Matrix

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = "~/projects/lpm-faceless-humanoid/assets/organic/rabbit_v1/rabbit.glb"
FPS = 24
S = 1.0918612913370276  # plan -> mesh scale (rabbit_report.json normalize.scale)
DZ = 0.003


def P(x, y, z):
    """plan coords (Z-up, +Y forward) -> Blender world (Z-up, -Y forward)."""
    return Vector((S * x, -S * y, S * z + DZ))


# ---------------------------------------------------------------- import + weld
bpy.ops.wm.read_factory_settings(use_empty=True)
scn = bpy.context.scene
scn.render.fps = FPS
bpy.ops.import_scene.gltf(filepath=SRC)
objs = {o.name: o for o in bpy.data.objects}
for o in list(bpy.data.objects):  # unparent from 'world' empty, keep transforms
    if o.parent:
        mw = o.matrix_world.copy(); o.parent = None; o.matrix_world = mw
bpy.data.objects.remove(objs["world"])
body_parts = [o for o in bpy.data.objects if o.name.startswith("body_")]
eyes = sorted([o for o in bpy.data.objects if o.name.startswith("eye_")], key=lambda o: o.matrix_world.translation.x)
bpy.ops.object.select_all(action="DESELECT")
for o in body_parts:
    o.select_set(True)
bpy.context.view_layer.objects.active = body_parts[0]
bpy.ops.object.join()
body = bpy.context.view_layer.objects.active
body.name = "rabbit_body"; body.data.name = "rabbit_body"
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
bm = bmesh.new(); bm.from_mesh(body.data)
bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
bm.to_mesh(body.data); bm.free()
for p in body.data.polygons:
    p.use_smooth = False
print("BODY verts", len(body.data.vertices), "tris", len(body.data.polygons))
for e in eyes:
    bpy.context.view_layer.objects.active = e
    bpy.ops.object.select_all(action="DESELECT"); e.select_set(True)
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    bm = bmesh.new(); bm.from_mesh(e.data); bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5); bm.to_mesh(e.data); bm.free()
eyes[0].name = "rabbit_eye.R"; eyes[1].name = "rabbit_eye.L"
# rabbit faces -Y, so its LEFT side is +X.  .L == +X, .R == -X.

V = [v.co.copy() for v in body.data.vertices]


# ---------------------------------------------------------------- ear landmarks from mesh
def ear_points(sign):
    side = [v for v in V if v.x * sign > 0.01 and v.z > 0.68]
    tip = max(side, key=lambda v: v.z)
    band = [v for v in side if 0.69 < v.z < 0.73]
    base = sum(band, Vector()) / len(band)
    d = (tip - base).normalized()
    root = base - d * 0.06
    mid = base + (tip - base) * 0.45
    return root, mid, tip


# ---------------------------------------------------------------- armature
arm_data = bpy.data.armatures.new("rabbit_rig")
arm = bpy.data.objects.new("rabbit_rig", arm_data)
scn.collection.objects.link(arm)
bpy.context.view_layer.objects.active = arm
bpy.ops.object.select_all(action="DESELECT"); arm.select_set(True)
bpy.ops.object.mode_set(mode="EDIT")
eb = arm_data.edit_bones
XW = Vector((1, 0, 0))


def bone(name, head, tail, parent=None, deform=True, connect=False):
    b = eb.new(name)
    b.head = head; b.tail = tail
    d = (tail - head).normalized()
    z = XW.cross(d)
    if z.length < 1e-4:
        z = Vector((0, 0, 1)).cross(d)
    b.align_roll(z.normalized())
    if parent:
        b.parent = eb[parent]; b.use_connect = connect
    b.use_deform = deform
    return b


bone("root", Vector((0, 0, 0)), Vector((0, 0, 0.15)), deform=False)
bone("pelvis", P(0, -0.22, 0.19), P(0, -0.08, 0.22), "root")
bone("spine", P(0, -0.08, 0.22), P(0, 0.05, 0.26), "pelvis", connect=True)
bone("chest", P(0, 0.05, 0.26), P(0, 0.10, 0.36), "spine", connect=True)
bone("neck", P(0, 0.10, 0.36), P(0, 0.15, 0.46), "chest", connect=True)
bone("head", P(0, 0.15, 0.46), P(0, 0.33, 0.46), "neck", connect=True)
bone("tail", P(0, -0.27, 0.14), P(0, -0.38, 0.13), "pelvis")
for side, sg in (("L", 1), ("R", -1)):
    r, m, t = ear_points(sg)
    bone(f"ear_1.{side}", r, m, "head")
    bone(f"ear_2.{side}", m, t, f"ear_1.{side}", connect=True)
    x = 0.065 * sg
    bone(f"front_upper.{side}", P(x, 0.11, 0.30), P(x, 0.16, 0.15), "chest")
    bone(f"front_lower.{side}", P(x, 0.16, 0.15), P(x, 0.20, 0.035), f"front_upper.{side}", connect=True)
    bone(f"front_paw.{side}", P(x, 0.20, 0.035), P(x, 0.265, 0.02), f"front_lower.{side}", connect=True)
    hx = 0.115 * sg
    bone(f"thigh.{side}", P(hx, -0.17, 0.21), P(hx, -0.02, 0.10), "pelvis")
    bone(f"shin.{side}", P(hx, -0.02, 0.10), P(0.13 * sg, -0.14, 0.04), f"thigh.{side}", connect=True)
    bone(f"foot.{side}", P(0.13 * sg, -0.14, 0.04), P(0.13 * sg, 0.15, 0.02), f"shin.{side}", connect=True)
bpy.ops.object.mode_set(mode="OBJECT")
BONES = [b.name for b in arm_data.bones]
print("BONES", len(BONES), BONES)

# ---------------------------------------------------------------- skinning
bpy.ops.object.select_all(action="DESELECT")
body.select_set(True); arm.select_set(True)
bpy.context.view_layer.objects.active = arm
weight_method = "heat (ARMATURE_AUTO)"
bpy.ops.object.parent_set(type="ARMATURE_AUTO")
deform_bones = [b.name for b in arm_data.bones if b.use_deform]


def weight_stats():
    gi = {g.index: g.name for g in body.vertex_groups}
    unweighted, maxinf, used = 0, 0, set()
    for v in body.data.vertices:
        ws = [(gi[g.group], g.weight) for g in v.groups if g.weight > 1e-6 and gi[g.group] in deform_bones]
        if not ws:
            unweighted += 1
        maxinf = max(maxinf, len(ws))
        used.update(n for n, _ in ws)
    return unweighted, maxinf, sorted(set(deform_bones) - used)


unw, mi, empty = weight_stats()
print("HEAT unweighted", unw, "maxinf", mi, "empty bones", empty)
if unw > 0 or empty:
    # fallback: envelope-free nearest-bone for the missing verts, then smooth
    weight_method = f"heat + nearest-bone fill for {unw} verts / bones {empty}"
    gi = {g.name: g for g in body.vertex_groups}
    segs = {b.name: (b.head_local.copy(), b.tail_local.copy()) for b in arm_data.bones if b.use_deform}

    def seg_d(p, a, b):
        ab = b - a; t = max(0, min(1, (p - a).dot(ab) / ab.length_squared)); return (a + ab * t - p).length
    for v in body.data.vertices:
        if not any(g.weight > 1e-6 for g in v.groups):
            nb = min(segs, key=lambda n: seg_d(v.co, *segs[n]))
            gi.setdefault(nb, body.vertex_groups.new(name=nb)).add([v.index], 1.0, "REPLACE")
# ---- weight cleanup: heat bleeds leg weights onto the belly and across the midline on this
# folded, low-poly mesh. Strip a limb bone's weight from verts outside its capsule, strip opposite-side
# weights, then re-fill empty verts from the nearest torso bone.
RADIUS = {"front_upper": 0.06, "front_lower": 0.05, "front_paw": 0.045,
          "thigh": 0.10, "shin": 0.09, "foot": 0.065, "tail": 0.08, "ear_1": 0.06, "ear_2": 0.06}
TORSO = ["pelvis", "spine", "chest", "neck", "head"]
segs_all = {b.name: (b.head_local.copy(), b.tail_local.copy()) for b in arm_data.bones if b.use_deform}


def seg_dist(p, a, b):
    ab = b - a; t = max(0, min(1, (p - a).dot(ab) / ab.length_squared)); return (a + ab * t - p).length


stripped = 0
vg = {g.name: g for g in body.vertex_groups}
for v in body.data.vertices:
    for g in list(v.groups):
        n = body.vertex_groups[g.group].name
        base = n.split(".")[0]
        kill = False
        if base in RADIUS and seg_dist(v.co, *segs_all[n]) > RADIUS[base]:
            kill = True
        if n.endswith(".L") and v.co.x < -0.015 or n.endswith(".R") and v.co.x > 0.015:
            kill = True
        if kill and g.weight > 0:
            vg[n].remove([v.index]); stripped += 1
    if not any(g.weight > 1e-6 for g in v.groups):
        cands = [n for n in segs_all if not (n.endswith(".L") and v.co.x < -0.015 or n.endswith(".R") and v.co.x > 0.015)]
        nb = min(cands, key=lambda n: seg_dist(v.co, *segs_all[n]))
        vg[nb].add([v.index], 1.0, "REPLACE")

# Laplacian weight smoothing (python; the operator's poll fails in background): 3 x factor 0.5
nbrs = [[] for _ in body.data.vertices]
for e in body.data.edges:
    a, b = e.vertices; nbrs[a].append(b); nbrs[b].append(a)
W = [{body.vertex_groups[g.group].name: g.weight for g in v.groups if g.weight > 0} for v in body.data.vertices]
for _ in range(3):
    W2 = []
    for i, w in enumerate(W):
        acc = {}
        for j in nbrs[i]:
            for n, x in W[j].items():
                acc[n] = acc.get(n, 0) + x / len(nbrs[i])
        keys = set(w) | set(acc)
        nw = {n: 0.5 * w.get(n, 0) + 0.5 * acc.get(n, 0) for n in keys}
        # keep the midline rule while smoothing
        co = body.data.vertices[i].co
        nw = {n: x for n, x in nw.items() if not (n.endswith(".L") and co.x < -0.015 or n.endswith(".R") and co.x > 0.015)}
        W2.append(nw)
    W = W2
for g in body.vertex_groups:
    g.remove(list(range(len(body.data.vertices))))
for i, w in enumerate(W):
    for n, x in w.items():
        if x > 1e-4:
            vg[n].add([i], x, "REPLACE")
weight_method += f"; capsule/midline cleanup stripped {stripped} limb weights, then Laplacian weight smoothing (0.5 x3)"
print("CLEANUP stripped", stripped)
# clean up: limit 4, normalize
bpy.ops.object.select_all(action="DESELECT"); body.select_set(True)
bpy.context.view_layer.objects.active = body
bpy.ops.object.vertex_group_clean(group_select_mode="ALL", limit=0.01)
bpy.ops.object.vertex_group_limit_total(group_select_mode="ALL", limit=4)
bpy.ops.object.vertex_group_normalize_all(group_select_mode="ALL", lock_active=False)
unw, mi, empty = weight_stats()
print("FINAL unweighted", unw, "maxinf", mi, "empty", empty)

# contact regions by dominant weight (hind = foot.*, front = front_paw.* / front_lower.*)
def _dom(v):
    return max(v.groups, key=lambda g: g.weight)
_names = {g.index: g.name for g in body.vertex_groups}
HIND = [v.index for v in body.data.vertices if _names[_dom(v).group].startswith("foot.")]
FRONT = [v.index for v in body.data.vertices if _names[_dom(v).group].split(".")[0] in ("front_paw", "front_lower")]
print("REGIONS hind", len(HIND), "front", len(FRONT))

# eyes: rigid bone-parent to head
for e in eyes:
    mw = e.matrix_world.copy()
    e.parent = arm; e.parent_type = "BONE"; e.parent_bone = "head"
    e.matrix_world = mw

# ---------------------------------------------------------------- animation helpers
arm.animation_data_create()
pb = arm.pose.bones
for b in pb:
    b.rotation_mode = "XYZ"


def reset_pose():
    for b in pb:
        b.location = (0, 0, 0); b.rotation_euler = (0, 0, 0); b.scale = (1, 1, 1)


def mirror(d):
    """expand 'X.LR' keys to both sides (same values, rx symmetric; ry/rz mirrored)."""
    out = {}
    for k, v in d.items():
        if k.endswith(".LR"):
            base = k[:-3]
            v = tuple(v) + (0,) * (3 - len(v))
            out[base + ".L"] = v
            out[base + ".R"] = (v[0], -v[1], -v[2])
        else:
            out[k] = tuple(v) + (0,) * (3 - len(v))
    return out


depsgraph = bpy.context.evaluated_depsgraph_get()


def eval_coords():
    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    ob = body.evaluated_get(dg)
    me = ob.to_mesh()
    co = [ob.matrix_world @ v.co for v in me.vertices]
    ob.to_mesh_clear()
    return co


def min_z():
    return min(c.z for c in eval_coords())


pitch_log = {}
clamp_log = {}


def build_action(name, length, keys, travel=None, contact=(), lift=None, scales=None, pitch_target=None):
    """keys: {frame: {bone: (rx,ry,rz) deg}}; travel: {frame: forward metres}; contact frames get root
    height solved so the lowest vertex sits on z=0; lift: {frame: metres above solved stance height}."""
    arm.animation_data.action = None  # pose freely while solving; keys written afterwards
    travel = travel or {}; lift = lift or {}; scales = scales or {}
    frames = sorted(keys)
    poses = {}
    for f in frames:
        reset_pose()
        for bn, r in mirror(keys[f]).items():
            pb[bn].rotation_euler = [math.radians(a) for a in r]
        for bn, s in scales.get(f, {}).items():
            pb[bn].scale = s
        fwd = travel.get(f, 0.0)
        pb["root"].location = (0, 0, fwd)
        region = contact.get(f, "all") if isinstance(contact, dict) else "all"
        target = pitch_target.get(f) if pitch_target else None
        if target is not None:
            # bisection on an additive pelvis pitch so (front_min_z - hind_min_z) == target
            base_rx = pb["pelvis"].rotation_euler.x
            lo, hi = math.radians(-45), math.radians(45)
            for _ in range(22):
                mid = 0.5 * (lo + hi)
                pb["pelvis"].rotation_euler.x = base_rx + mid
                co = eval_coords()
                g = min(co[i].z for i in FRONT) - min(co[i].z for i in HIND) - target
                if g > 0: lo = mid   # front too high -> more nose-down
                else: hi = mid
            pitch_log[(name, f)] = round(math.degrees(0.5 * (lo + hi)), 2)
        co = eval_coords()
        h = -min(c.z for c in co)  # height that puts lowest vertex on the floor
        if region == "hind":
            h = -min(co[i].z for i in HIND)
        elif region == "front":
            h = -min(co[i].z for i in FRONT)
        if f in contact or f in lift:
            h = h + lift.get(f, 0.0)
        else:
            h = max(h, 0.0)
        pb["root"].location = (0, h, fwd)
        poses[f] = {b.name: (tuple(b.location), tuple(b.rotation_euler), tuple(b.scale)) for b in pb}
    act = bpy.data.actions.new(name)
    act.use_fake_user = True
    arm.animation_data.action = act
    for f in frames:
        for b in pb:
            b.location, b.rotation_euler, b.scale = poses[f][b.name]
            b.keyframe_insert("rotation_euler", frame=f, group=b.name)
            b.keyframe_insert("location", frame=f, group=b.name)
            b.keyframe_insert("scale", frame=f, group=b.name)
    # floor clamp: in-between frames where FK interpolation sinks a limb get an extra root-height key
    clamp = []
    for _ in range(3):
        added = 0
        for f in range(frames[0] + 1, frames[-1]):
            if f in keys:
                continue
            scn.frame_set(f)
            mz = min(c.z for c in eval_coords())
            if mz < -0.003:
                pb["root"].location.y += -mz
                pb["root"].keyframe_insert("location", frame=f, group="root")
                clamp.append((f, round(-mz * 100, 2))); added += 1
        if not added:
            break
    print("ACTION", name, "slot", getattr(arm.animation_data, "action_slot", None), "floor-clamp keys", clamp)
    clamp_log[name] = clamp
    act.frame_range = (frames[0], frames[-1])
    act.use_frame_range = True
    for fc in iter_fcurves(act):
        for kp in fc.keyframe_points:
            kp.interpolation = "BEZIER"; kp.handle_left_type = kp.handle_right_type = "AUTO_CLAMPED"
    # make the loop seamless in slope: cyclic modifier on in-place channels only
    return act


def iter_fcurves(act):
    if hasattr(act, "layers") and len(act.layers):
        for layer in act.layers:
            for strip in layer.strips:
                for cb in strip.channelbags:
                    yield from cb.fcurves
    else:
        yield from act.fcurves


# ---------------------------------------------------------------- hop (18 frames)
HOP_LEN = 18
hop_keys = {
    0: {},
    3: {"pelvis": (-6,), "spine": (6,), "chest": (6,), "neck": (-4,), "head": (-4,),
        "ear_1.LR": (-6,), "ear_2.LR": (-4,),
        "thigh.LR": (8,), "shin.LR": (-6,), "foot.LR": (-2,),
        "front_upper.LR": (8,), "front_lower.LR": (-10,), "front_paw.LR": (2,), "tail": (-10,)},
    6: {"pelvis": (4,), "spine": (-2,), "chest": (-6,), "neck": (-6,), "head": (-8,),
        "ear_1.LR": (-18, 0, -4), "ear_2.LR": (-10,),
        "thigh.LR": (12,), "shin.LR": (-10,), "foot.LR": (38,),
        "front_upper.LR": (-18,), "front_lower.LR": (-6,), "front_paw.LR": (5,), "tail": (10,)},
    9: {"pelvis": (0,), "spine": (-4,), "chest": (-6,), "neck": (-6,), "head": (-6,),
        "ear_1.LR": (-38, 0, -6), "ear_2.LR": (-24,),
        "thigh.LR": (20,), "shin.LR": (-5,), "foot.LR": (60,),
        "front_upper.LR": (-32,), "front_lower.LR": (14,), "front_paw.LR": (25,), "tail": (18,)},
    12: {"pelvis": (18,), "spine": (6,), "chest": (4,), "neck": (-20,), "head": (-18,),
         "ear_1.LR": (-16, 0, 3), "ear_2.LR": (4,),
         "thigh.LR": (12,), "shin.LR": (-8,), "foot.LR": (18,),
         "front_upper.LR": (-12,), "front_lower.LR": (6,), "front_paw.LR": (4,), "tail": (6,)},
    15: {"pelvis": (8,), "spine": (8,), "chest": (2,), "neck": (-8,), "head": (-6,),
         "ear_1.LR": (10, 0, 2), "ear_2.LR": (8,),
         "thigh.LR": (-12,), "shin.LR": (6,), "foot.LR": (-4,),
         "front_upper.LR": (-4,), "front_lower.LR": (-6,), "front_paw.LR": (4,), "tail": (-4,)},
    18: {},
}
HOP_DIST = 0.36
hop_travel = {0: 0.0, 3: 0.0, 6: 0.05, 9: 0.18, 12: 0.30, 15: 0.34, 18: HOP_DIST}
hop_contact = {0: "all", 3: "all", 6: "hind", 12: "front", 15: "all", 18: "all"}
hop_lift = {9: 0.16}
hop_pitch = {3: 0.0, 6: 0.04, 9: -0.03, 12: -0.06, 15: 0.0}  # front-minus-hind lowest-point targets (m)
build_action("hop", HOP_LEN, hop_keys, hop_travel, hop_contact, hop_lift, pitch_target=hop_pitch)
build_action("hop_inplace", HOP_LEN, hop_keys, None, hop_contact, hop_lift, pitch_target=hop_pitch)
print("PITCH", pitch_log)

# ---------------------------------------------------------------- idle (48 frames)
idle_keys = {
    0: {},
    8: {"ear_1.LR": (-2,)},
    12: {"chest": (-2,), "neck": (1,), "head": (0, 0, 6), "ear_1.LR": (-3,)},
    20: {"head": (0, 0, 9), "neck": (0, 0, 3), "ear_1.L": (0, 0, 0), "ear_1.R": (-3,)},
    22: {"head": (0, 0, 9), "neck": (0, 0, 3), "ear_1.L": (-14, 0, -10), "ear_2.L": (-8,), "ear_1.R": (-3,)},
    24: {"head": (0, 0, 8), "neck": (0, 0, 3), "ear_1.L": (2, 0, 2), "ear_1.R": (-3,)},
    26: {"head": (0, 0, 7), "neck": (0, 0, 2), "ear_1.L": (-6, 0, -4), "ear_1.R": (-3,)},
    30: {"head": (0, 0, 2), "ear_1.LR": (-1,)},
    36: {"chest": (-2,), "neck": (1, 0, -2), "head": (-2, 0, -6), "ear_1.LR": (-3,)},
    42: {"head": (0, 0, -3), "ear_1.LR": (-1,)},
    48: {},
}
breath = {12: {"chest": (1.04, 1.0, 1.04), "spine": (1.03, 1.0, 1.03)}, 36: {"chest": (1.04, 1.0, 1.04), "spine": (1.03, 1.0, 1.03)},
          0: {}, 24: {}, 48: {}}
# scale keys only where breathing peaks/troughs; other frames reset to 1 -> add explicit troughs
for f in (0, 24, 48):
    breath[f] = {"chest": (1, 1, 1), "spine": (1, 1, 1)}
idle_scales = {f: breath.get(f, {}) for f in idle_keys}
# frames between breath keys would be forced to scale 1 by build_action; interpolate manually
def breath_at(f):
    ph = (f % 24) / 24.0
    a = 0.5 - 0.5 * math.cos(2 * math.pi * ph)
    return {"chest": (1 + 0.025 * a, 1, 1 + 0.025 * a), "spine": (1 + 0.015 * a, 1, 1 + 0.015 * a)}
idle_scales = {f: breath_at(f) for f in idle_keys}
build_action("idle", 48, idle_keys, None, tuple(idle_keys), None, idle_scales)

# ---------------------------------------------------------------- sniff (24 frames)
sniff_keys = {
    0: {},
    4: {"neck": (8,), "head": (4,), "ear_1.LR": (6,)},
    7: {"neck": (8,), "head": (8,), "ear_1.LR": (6,)},
    9: {"neck": (8,), "head": (3,), "ear_1.LR": (6,)},
    11: {"neck": (8,), "head": (8,), "ear_1.LR": (6,)},
    13: {"neck": (8,), "head": (3,), "ear_1.LR": (6,)},
    15: {"neck": (8,), "head": (8, 0, 3), "ear_1.LR": (6,)},
    19: {"neck": (3,), "head": (2,), "ear_1.LR": (2,)},
    24: {},
}
build_action("sniff", 24, sniff_keys, None, tuple(sniff_keys))

# ---------------------------------------------------------------- deformation checks
def tri_volume(co, tris):
    vol = 0.0
    for a, b, c in tris:
        vol += co[a].dot(co[b].cross(co[c]))
    return vol / 6.0


me = body.data
me.calc_loop_triangles()
tris = [tuple(t.vertices) for t in me.loop_triangles]
edges = [tuple(e.vertices) for e in me.edges]

arm.animation_data.action = None
reset_pose(); scn.frame_set(0)
rest = eval_coords()
rest_vol = tri_volume(rest, tris)
rest_len = [(rest[a] - rest[b]).length for a, b in edges]
# region masks for contact: hind foot / front paw verts (rest)
hind, front = HIND, FRONT

checks = {"rest_volume_m3": rest_vol, "body_verts": len(rest), "body_tris": len(tris), "actions": {}}
STANCE = {"hop": {0: "all", 3: "all", 6: "hind", 12: "front", 15: "all", 18: "all"},
          "hop_inplace": {0: "all", 3: "all", 6: "hind", 12: "front", 15: "all", 18: "all"},
          "idle": {0: "all", 12: "all", 24: "all", 36: "all"}, "sniff": {0: "all", 9: "all"}}
for act in [a for a in bpy.data.actions if a.name in ("hop", "hop_inplace", "idle", "sniff")]:
    arm.animation_data.action = act
    f0, f1 = map(int, act.frame_range)
    res = {"frame_range": [f0, f1], "frames": {}}
    worst_vol, worst_str, worst_shrink, nan, zero = 0, 0, 9, 0, 0
    for f in range(f0, f1 + 1):
        scn.frame_set(f)
        co = eval_coords()
        if any(any(math.isnan(x) for x in c) for c in co):
            nan += 1
        vol = tri_volume(co, tris)
        dv = (vol - rest_vol) / rest_vol * 100
        ratios = [((co[a] - co[b]).length / l) if l > 0 else 1 for (a, b), l in zip(edges, rest_len)]
        z = sum(1 for (a, b) in edges if (co[a] - co[b]).length < 1e-6)
        zero += z
        rec = {"vol_pct": round(dv, 2), "max_stretch": round(max(ratios), 3), "min_stretch": round(min(ratios), 3),
               "min_z_cm": round(min(c.z for c in co) * 100, 2),
               "hind_min_z_cm": round(min(co[i].z for i in hind) * 100, 2),
               "front_min_z_cm": round(min(co[i].z for i in front) * 100, 2)}
        res["frames"][f] = rec
        worst_vol = max(worst_vol, abs(dv)); worst_str = max(worst_str, max(ratios)); worst_shrink = min(worst_shrink, min(ratios))
    st = STANCE.get(act.name, {})
    res["stance"] = {f: {"which": w, "contact_min_z_cm": res["frames"][f][{"all": "min_z_cm", "hind": "hind_min_z_cm", "front": "front_min_z_cm"}[w]]} for f, w in st.items()}
    res.update(max_abs_vol_pct=round(worst_vol, 2), max_edge_stretch=round(worst_str, 3), min_edge_ratio=round(worst_shrink, 3),
               nan_frames=nan, zero_len_edges=zero)
    checks["actions"][act.name] = res
    print("CHECK", act.name, {k: v for k, v in res.items() if k not in ("frames",)})
checks["weights"] = {"method": weight_method, "unweighted_verts": unw, "max_influences": mi, "empty_deform_bones": empty}
checks["bones"] = BONES
checks["floor_clamp_keys_frame_cm"] = clamp_log
checks["pelvis_pitch_solve_deg"] = {f"{a}@{f}": v for (a, f), v in pitch_log.items()}
with open(os.path.join(HERE, "checks.json"), "w") as fh:
    json.dump(checks, fh, indent=1)

# ---------------------------------------------------------------- save + export
arm.animation_data.action = bpy.data.actions["idle"]
reset_pose()
scn.frame_start, scn.frame_end = 0, 47
scn.frame_set(0)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, "rabbit_rig.blend"))
bpy.ops.object.select_all(action="SELECT")
bpy.ops.export_scene.gltf(filepath=os.path.join(HERE, "rabbit_rigged.glb"), export_format="GLB",
                          export_animations=True, export_animation_mode="ACTIONS", export_skins=True,
                          export_force_sampling=True, export_yup=True, export_apply=False)
print("DONE")

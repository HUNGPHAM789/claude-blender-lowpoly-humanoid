"""Blender: keep the ARMS out of the top in an old settler clip played on a dressed character, then bake the clip for that character
(Boss 25/10/2026: «chỉnh đường đi tay trong clip vác gỗ để tay không ép vào áo, rồi gửi video»).

  blender -b -P arm_clearance_blender.py -- <rigged.glb> <clip.glb> <out_clip.glb> <report.json> [--max 50] [--step 2.5]

Per frame and side: the upper arm ABDUCTS (elbow swung away from the body about the shoulder's front–back axis) and a 2-bone IK keeps
the wrist exactly where the clip put it; the hand keeps its world orientation — so the log stays on the shoulder. The angle is the smallest that leaves
no top vertex inside that arm (vertex parity against the posed body, the body bone under the vertex = that side's clavicle / upper
arm / forearm / hand); the per-frame need is then smoothed in time on the closed loop (moving max over 5 frames, Gaussian σ 1.5) and
never allowed below the need. Report: needed / applied angle per frame, remaining clipping, wrist drift, elbow shift.
"""
import bpy, sys, json, math
import numpy as np
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree

a = sys.argv[sys.argv.index("--") + 1:]
char, clip, out_glb, rep_path = a[0], a[1], a[2], a[3]
MAXA = float(a[a.index("--max") + 1]) if "--max" in a else 50.0
STEP = float(a[a.index("--step") + 1]) if "--step" in a else 2.5
SKIP = ("ik_", "pole_")
ARM = ("clavicle", "upperarm", "forearm", "hand")

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=char)
sc = bpy.context.scene
rig = next(o for o in sc.objects if o.type == "ARMATURE")
meshes = [o for o in sc.objects if o.type == "MESH"]
body = next(o for o in meshes if o.name.lower() == "body")
tops = [o for o in meshes if o.name.startswith("outfit_upper")]
for pb in rig.pose.bones:
    pb.rotation_mode = "QUATERNION"
    for c in pb.constraints: c.influence = 0.0
order = [b.name for b in rig.data.bones if not b.name.startswith(SKIP)]
hips_h = rig.data.bones["hips"].head_local.z
bnm = {g.index: g.name for g in body.vertex_groups}
DOM = [bnm[max(v.groups, key=lambda g: g.weight).group] if v.groups else "?" for v in body.data.vertices]
DIRS = (Vector((0, 0, 1)), Vector((0.3, 0.2, 0.93)).normalized())

before = set(bpy.data.objects)
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


def retarget(f):
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
    return {n: rig.pose.bones[n].matrix.copy() for n in order}


def crossings(bvh, co, d, n=0):
    o = co.copy()
    while n < 50:
        hit = bvh.ray_cast(o, d)
        if hit[0] is None: return n
        n += 1; o = hit[0] + d * 1e-5
    return n


def arm_clip():
    """top verts inside the posed body whose nearest body vertex is an arm vertex, per side: (count, max depth mm)."""
    dg = bpy.context.evaluated_depsgraph_get()
    be = body.evaluated_get(dg); bm = be.to_mesh(); mw = body.matrix_world
    P = [mw @ v.co for v in bm.vertices]; PF = [p.vertices[:] for p in bm.polygons]; bvh = BVHTree.FromPolygons(P, PF); be.to_mesh_clear()
    out = {"L": [0, 0.0], "R": [0, 0.0]}
    for L in tops:
        le = L.evaluated_get(dg); lm = le.to_mesh()
        for v in lm.vertices:
            co = L.matrix_world @ v.co; hit = bvh.find_nearest(co, 0.3)
            if hit[0] is None: continue
            loc, nrm, fi, dist = hit
            if (co - loc).dot(nrm) < 0 and all(crossings(bvh, co, d_) % 2 == 1 for d_ in DIRS):
                bone = DOM[min(PF[fi], key=lambda k_: (P[k_] - loc).length)]
                if bone.startswith(ARM): s_ = bone[-1]; out[s_][0] += 1; out[s_][1] = max(out[s_][1], dist * 1000)
        le.to_mesh_clear()
    return out


AXES = {"front_back+": (Vector((0, 1, 0)), 1), "front_back-": (Vector((0, 1, 0)), -1), "vertical+": (Vector((0, 0, 1)), 1),
        "vertical-": (Vector((0, 0, 1)), -1), "side+": (Vector((1, 0, 0)), 1), "side-": (Vector((1, 0, 0)), -1), "shrug": (None, 1),
        "free_out": (Vector((0, 1, 0)), 1), "free_fwd": (Vector((1, 0, 0)), -1), "free_outfwd": (Vector((0, 0, 1)), 1),
        "lift": (None, 1), "free_up+": (Vector((1, 0, 0)), 1), "free_up-": (Vector((1, 0, 0)), -1),
        "free_shrug15": (None, 1), "free_shrug20": (None, 1)}   # elbow pole moved UP by ang mm/2 (wrist kept): the right upper arm lay ACROSS the band's top edge in carry_log
SIDES = a[a.index("--sides") + 1] if "--sides" in a else "LR"           # sides allowed to change
FREE = "--free" in a                                                    # allow the wrist to move (the log moves with the hand)
def swivel(base, side, ang, axis="front_back+"):
    """ABDUCT: swing the elbow away from the body by ang (deg) about the shoulder's front–back axis, then 2-bone IK so the wrist stays
    exactly where the clip put it (bone lengths kept); the hand keeps its world matrix. (A swivel about the shoulder→wrist axis could
    not clear carry_log: the hand sits on the shoulder, that axis is short and the upper arm only spun in place — 9.4 mm left at 50°.)"""
    u, fa, h, cl = f"upperarm_{side}", f"forearm_{side}", f"hand_{side}", f"clavicle_{side}"
    for n in (cl, u, fa, h):                                           # parent first, update after each (a child set before its parent
        rig.pose.bones[n].matrix = base[n]; bpy.context.view_layer.update()   # updates is stored relative to the stale parent)
    if not ang: return
    W = base[h].translation.copy()
    if axis.startswith("free_shrug"):                                  # a fixed moderate shrug, then the whole arm raised about the
        sh = float(axis[len("free_shrug"):]); C = base[cl].translation; sg_ = 1.0 if side == "R" else -1.0   # shoulder's side axis
        rig.pose.bones[cl].matrix = Matrix.Translation(C) @ Matrix.Rotation(math.radians(sh) * sg_, 4, Vector((0, 1, 0))) @ Matrix.Translation(-C) @ base[cl]
        bpy.context.view_layer.update()
        nb = {n: rig.pose.bones[n].matrix.copy() for n in (u, fa, h)}; S = nb[u].translation.copy()
        best = None
        for sgn in (1, -1):                                            # the sign that raises the elbow
            X = Matrix.Translation(S) @ Matrix.Rotation(math.radians(ang) * sgn, 4, Vector((1, 0, 0))) @ Matrix.Translation(-S)
            ez = (X @ nb[fa].translation.to_4d()).z
            if best is None or ez > best[0]: best = (ez, X)
        for n in (u, fa, h): rig.pose.bones[n].matrix = best[1] @ nb[n]; bpy.context.view_layer.update()
        return
    if axis.startswith("free"):                                        # rotate the WHOLE arm about the shoulder; hand + log follow
        S = base[u].translation.copy(); ax_, sg = AXES[axis]
        if ax_.y: sg *= (1.0 if base[fa].translation.x >= S.x else -1.0)
        if ax_.z: sg *= (1.0 if side == "L" else -1.0)
        X = Matrix.Translation(S) @ Matrix.Rotation(math.radians(ang) * sg, 4, ax_) @ Matrix.Translation(-S)
        for n in (u, fa, h): rig.pose.bones[n].matrix = X @ base[n]; bpy.context.view_layer.update()
        return
    if axis == "shrug":                                                # lift the shoulder (clavicle up about the front–back axis at its
        C = base[cl].translation; sg_ = 1.0 if side == "R" else -1.0     # root): carrying a log on the shoulder, people shrug
        Rs_ = Matrix.Rotation(math.radians(ang) * sg_, 4, Vector((0, 1, 0)))
        rig.pose.bones[cl].matrix = Matrix.Translation(C) @ Rs_ @ Matrix.Translation(-C) @ base[cl]; bpy.context.view_layer.update()
        S = rig.pose.bones[u].matrix.translation.copy(); E = rig.pose.bones[fa].matrix.translation.copy()
        bu = rig.pose.bones[u].matrix.copy(); bf = rig.pose.bones[fa].matrix.copy(); Eh = E
    else:
        S = base[u].translation.copy(); E = base[fa].translation.copy(); bu, bf = base[u], base[fa]
    lu, lf = (base[fa].translation - base[u].translation).length, (base[h].translation - base[fa].translation).length
    if axis == "lift":
        Eh = E + Vector((0, 0, ang * 0.002))                           # ang 10 ⇒ 2 cm up
    elif axis != "shrug":
        ax_, sg = AXES[axis]                                           # pole hint: the elbow turned about this axis through the shoulder
        if ax_.y: sg *= (1.0 if E.x >= S.x else -1.0)                  # front–back axis: + = away from the body on either side
        if ax_.z: sg *= (1.0 if side == "L" else -1.0)                 # vertical axis mirrored L/R
        Eh = S + Matrix.Rotation(math.radians(ang) * sg, 3, ax_) @ (E - S)
    d_ = max(min((W - S).length, lu + lf - 1e-6), abs(lu - lf) + 1e-6); uu = (W - S).normalized()
    aa = (lu * lu - lf * lf + d_ * d_) / (2 * d_); hh = math.sqrt(max(lu * lu - aa * aa, 0.0))
    pp = (Eh - S) - uu * (Eh - S).dot(uu)
    if pp.length < 1e-9: return
    E2 = S + uu * aa + pp.normalized() * hh
    def turn(M, piv, v0, v1, newpiv):
        R = v0.normalized().rotation_difference(v1.normalized()).to_matrix().to_4x4()
        return Matrix.Translation(newpiv) @ R @ Matrix.Translation(-piv) @ M
    rig.pose.bones[u].matrix = turn(bu, S, E - S, E2 - S, S); bpy.context.view_layer.update()
    rig.pose.bones[fa].matrix = turn(bf, E, W - E, W - E2, E2); bpy.context.view_layer.update()
    rig.pose.bones[h].matrix = base[h]; bpy.context.view_layer.update()


frames = list(range(f0, f1 + 1))
base, need, AX = {}, {"L": [], "R": []}, {}
for f in frames: base[f] = retarget(f)
def put(b):                                                            # the WHOLE pose of a frame, parents first (the search only touches
    for n in order: rig.pose.bones[n].matrix = b[n]; bpy.context.view_layer.update()   # the arms; the rest stayed at the last frame)
def need_at(f, side, axis):
    ang = 0.0; put(base[f])
    while True:
        for s2 in ("L", "R"): swivel(base[f], s2, 0.0)
        swivel(base[f], side, ang, axis)
        if arm_clip()[side][0] == 0 or ang >= MAXA: return ang
        ang += STEP
for side in [s_ for s_ in ("L", "R") if s_ not in SIDES]: AX[side] = "front_back+"
for side in [s_ for s_ in ("L", "R") if s_ in SIDES]:                   # ONE direction per side for the whole clip (smooth motion):
    probe = frames[::4]                                                 # the one with the smallest worst-frame need on a frame sample
    if max(need_at(f, side, "free_out" if FREE else "front_back+") for f in probe) == 0: AX[side] = "free_out" if FREE else "front_back+"; continue
    score = {ax: max(need_at(f, side, ax) for f in probe) for ax in AXES if ax.startswith("free") == FREE}
    print(f"   elbow rise per direction at the worst probe frame: (see report)")
    AX[side] = min(score, key=score.get); print(f"side {side}: worst need per direction {score} → {AX[side]}")
for f in frames:
    for side in ("L", "R"): need[side].append(need_at(f, side, AX[side]) if side in SIDES else 0.0)
    print(f"frame {f}: need L {need['L'][-1]:.1f}° R {need['R'][-1]:.1f}°")
# smooth on the closed loop: moving max (±2 frames) → Gaussian σ 1.5 → never below the need
applied = {}
for side in ("L", "R"):
    n_ = np.array(need[side]); m = len(n_)
    mx = np.array([max(n_[(i + d) % m] for d in range(-2, 3)) for i in range(m)])
    kx = np.arange(-4, 5); g = np.exp(-kx ** 2 / (2 * 1.5 ** 2)); g /= g.sum()
    sm = np.array([sum(g[j] * mx[(i + kx[j]) % m] for j in range(len(kx))) for i in range(m)])
    applied[side] = np.maximum(sm, n_)
# apply, verify, bake
rows = []
for i, f in enumerate(frames):
    retarget(f); b0 = {n: rig.pose.bones[n].matrix.copy() for n in order}
    w0 = {s_: (rig.matrix_world @ b0[f"hand_{s_}"].translation) for s_ in "LR"}; e0 = {s_: b0[f"forearm_{s_}"].translation.copy() for s_ in "LR"}
    for side in ("L", "R"): swivel(b0, side, 0.0)
    for side in ("L", "R"):
        swivel_base = {n: rig.pose.bones[n].matrix.copy() for n in order}; swivel(swivel_base, side, float(applied[side][i]), AX[side])
    for n in order:                                                     # bake: local pose of every bone at this frame
        pb = rig.pose.bones[n]; pb.keyframe_insert("rotation_quaternion", frame=f)
        if n in ("hips", "goc"): pb.keyframe_insert("location", frame=f)
    c = arm_clip()
    rows.append({"frame": f, "need": {s_: need[s_][i] for s_ in "LR"}, "applied": {s_: round(float(applied[s_][i]), 2) for s_ in "LR"},
                 "clip_after": c,
                 "wrist_drift_mm": {s_: round((rig.matrix_world @ rig.pose.bones[f"hand_{s_}"].matrix.translation - w0[s_]).length * 1000, 3) for s_ in "LR"},
                 "elbow_shift_mm": {s_: round((rig.pose.bones[f"forearm_{s_}"].matrix.translation - e0[s_]).length * 1000, 1) for s_ in "LR"}})
rig.animation_data.action.name = "carry_clear"
sc.frame_start, sc.frame_end = f0, f1
for o in new: bpy.data.objects.remove(o, do_unlink=True)
for ac in list(bpy.data.actions):                                      # export only the fixed clip (not the settler's or the log's)
    if ac is not rig.animation_data.action: bpy.data.actions.remove(ac)
bpy.ops.object.select_all(action="SELECT")
bpy.ops.export_scene.gltf(filepath=out_glb, export_format="GLB", export_skins=True, export_animations=True)
worst = {s_: max(r["clip_after"][s_][1] for r in rows) for s_ in "LR"}
json.dump({"direction": AX, "frames": rows, "max_applied": {s_: float(applied[s_].max()) for s_ in "LR"}, "worst_after_mm": worst,
           "max_wrist_drift_mm": max(max(r["wrist_drift_mm"].values()) for r in rows)}, open(rep_path, "w"), indent=1)
print(f"applied max L {applied['L'].max():.1f}° R {applied['R'].max():.1f}° · arm-in-top after: L {worst['L']:.1f} mm R {worst['R']:.1f} mm · "
      f"wrist drift ≤ {max(max(r['wrist_drift_mm'].values()) for r in rows):.3f} mm → {out_glb}")

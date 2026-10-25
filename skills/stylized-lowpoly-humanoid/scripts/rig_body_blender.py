"""Blender: rig a coloured stylized body with the SAME skeleton as the settler animation pipeline (humanoid_anim.dung_rig:
goc/hips/spine/chest/neck/head, clavicle/upperarm/forearm/hand, thigh/shin/foot + leg IK), so existing clips retarget onto it.
Boss 25/10/2026: «color và rig model … có rig giống hình rig của upgraded primal male ko?» (skills/humanoid-replaceable-assets/references/01_rig_front.png).

  blender -b -P rig_body_blender.py -- <colored.glb> <out_rigged.glb> <joints.json> [--pose-test <png>]

Joints are MEASURED on the mesh: horizontal sections at the landmark heights, points clustered along X (left arm | torso | right arm,
left leg | right leg). Weights: bone heat (Blender auto), ≤ 4 influences, normalised; hair above the neck → head only;
skirt/leather → no shin influence (it must not follow the knees); verts heat missed → copied from the nearest weighted vert.
Exit 1 if a joint cannot be found, a vertex stays unweighted, or the pose test tears the mesh (edge stretch > 2.2×).
"""
import bpy, bmesh, sys, os, json, math
import numpy as np
from mathutils import Vector as V
import mathutils

a = sys.argv[sys.argv.index("--") + 1:]
src, dst, jout = a[0], a[1], a[2]; pose_png = a[a.index("--pose-test") + 1] if "--pose-test" in a else None
sys.path.insert(0, os.path.expanduser("~/.hermes/skills/creative/humanoid-rig-animation/scripts"))
import humanoid_anim as HA

# fraction of total height (hair top = 1) where each joint is searched — from the sheet landmarks (spec/*_spec.json)
STRETCH_MAX = 3.0     # calibrated 25/10: clean rigs 1.9–2.0× (armpit/shoulder under a 50° raise); fused hand/skirt webs 20–55×
FR = {"ankle": 0.065, "knee": 0.285, "crotch": 0.40, "hip": 0.44, "navel": 0.555, "chest": 0.69, "neck": 0.805, "chin": 0.835,
      "shoulder": 0.755, "armpit": 0.675, "elbow": 0.595, "wrist": 0.49, "toe": 0.015}

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=src)
objs = [o for o in bpy.context.scene.objects if o.type == "MESH"]
# LAYERED character (assemble_layers_blender.py): one object per layer, the skin one named *body* ⇒ rig the body, then copy its
# weights onto hair/outfit layers. Otherwise (single painted mesh) join everything into one body.
layers = []
if len(objs) > 1 and any("body" in o.name for o in objs):
    body = next(o for o in objs if "body" in o.name); layers = [o for o in objs if o is not body]
    bpy.ops.object.select_all(action="DESELECT")
    for o in objs: o.select_set(True)
    bpy.context.view_layer.objects.active = body
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
else:
    bpy.ops.object.select_all(action="DESELECT")
    for o in objs: o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    if len(objs) > 1: bpy.ops.object.join()
    body = bpy.context.view_layer.objects.active
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
body.name = "body"
bm = bmesh.new(); bm.from_mesh(body.data); bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5); bm.to_mesh(body.data); bm.free()

Vt = np.array([v.co[:] for v in body.data.vertices]); E = np.array([e.vertices[:] for e in body.data.edges])
H = Vt[:, 2].max(); print(f"body {len(Vt)} verts, height {H:.3f} m, facing −Y, character left = +X")


def section(z):
    """points where mesh edges cross the plane Z = z."""
    a_, b_ = Vt[E[:, 0]], Vt[E[:, 1]]; s = (a_[:, 2] - z) * (b_[:, 2] - z) < 0
    t = (z - a_[s, 2]) / (b_[s, 2] - a_[s, 2]); return a_[s] + (b_[s] - a_[s]) * t[:, None]


def clusters(P, gap):
    """split section points into runs along X separated by gaps > gap ⇒ list of point arrays, left-to-right in X."""
    if not len(P): return []
    o = np.argsort(P[:, 0]); P = P[o]; cut = np.where(np.diff(P[:, 0]) > gap)[0] + 1
    return [c for c in np.split(P, cut) if len(c) >= 3]


fail = []
def need(cond, msg):
    if not cond: fail.append(msg)


K = {}
# legs
for nm, key in (("ankle", "co_chan"), ("knee", "goi")):
    cs = clusters(section(FR[nm] * H), 0.03 * H); need(len(cs) >= 2, f"{nm}: {len(cs)} clusters")
    if len(cs) >= 2:
        Rc = [c for c in cs if c.mean(axis=0)[0] < 0]; Lc = [c for c in cs if c.mean(axis=0)[0] > 0]
        R_ = min(Rc, key=lambda c: abs(c.mean(axis=0)[0])) if Rc else cs[0]; L_ = min(Lc, key=lambda c: abs(c.mean(axis=0)[0])) if Lc else cs[-1]   # inner runs = legs
        K[f"{key}_R"] = V(R_.mean(axis=0)); K[f"{key}_L"] = V(L_.mean(axis=0))
# hip sockets: the skirt hides the upper thighs ⇒ scan down from the crotch to the first height where two big runs appear
cs = []
for zf in np.arange(FR["crotch"] - 0.01, FR["knee"], -0.01):
    allc = clusters(section(zf * H), 0.015 * H)                    # hands hang beside the thighs: per side take the run NEAREST the midline
    Lc = [c for c in allc if c.mean(axis=0)[0] > 0 and len(c) >= 6]; Rc = [c for c in allc if c.mean(axis=0)[0] < 0 and len(c) >= 6]
    cs = [min(Rc, key=lambda c: abs(c.mean(axis=0)[0])), min(Lc, key=lambda c: abs(c.mean(axis=0)[0]))] if Lc and Rc else []
    if len(cs) == 2 and np.ptp(np.r_[cs[0][:, 0], cs[1][:, 0]]) < 0.35 * H: break
need(len(cs) == 2, f"upper thigh: {len(cs)} clusters")
if len(cs) == 2:
    cs = sorted(cs, key=lambda c: c.mean(axis=0)[0])
    for b, c in (("R", cs[0]), ("L", cs[-1])):
        m = c.mean(axis=0); K[f"hong_{b}"] = V((m[0] * 0.9, m[1], FR["hip"] * H))
for b in "LR":                                                   # toe = most forward (−Y) point of each foot near the ground
    P = section(FR["toe"] * H); P = P[(P[:, 0] > 0) if b == "L" else (P[:, 0] < 0)]
    need(len(P) > 3, f"toe {b}")
    if len(P): K[f"mui_chan_{b}"] = V((P[:, 0].mean(), P[:, 1].min(), FR["toe"] * H))
# torso centre line
def centre(z, width=0.12):
    P = section(z * H); P = P[np.abs(P[:, 0]) < width * H]; need(len(P) > 3, f"torso section at {z}")
    return V((0.0, float(P[:, 1].mean()) if len(P) else 0.0, z * H))
K["chau"] = V((0.0, (K.get("hong_L", V()).y + K.get("hong_R", V()).y) / 2, FR["hip"] * H))
K["bung"] = centre(FR["navel"]); K["nguc"] = centre(FR["chest"]); K["co"] = centre(FR["neck"], 0.05)
K["co"] = V((0.0, K["nguc"].y + 0.25 * (K["co"].y - K["nguc"].y), FR["neck"] * H))   # beard skews the neck section forward
K["dau"] = centre(FR["chin"], 0.05); K["dinh_dau"] = V((0.0, K["dau"].y, H * 0.985))
# arms: three runs (right arm | torso | left arm) between the armpit and the wrist; fit a line per arm and read the joints off it
pts = {"L": [], "R": []}; rad = {"L": [], "R": []}
for z in np.linspace(FR["wrist"], FR["armpit"] - 0.01, 12):
    cs = clusters(section(z * H), 0.012 * H)
    if len(cs) >= 3:
        for b, c in (("R", cs[0]), ("L", cs[-1])):
            pts[b].append(c.mean(axis=0)); rad[b].append(np.linalg.norm(c[:, :2] - c[:, :2].mean(axis=0), axis=1).max())
for b in "LR":
    P = np.array(pts[b]); need(len(P) >= 5, f"arm {b}: {len(P)} clean sections")
    if len(P) < 5: continue
    A = np.c_[P[:, 2], np.ones(len(P))]
    cx = np.linalg.lstsq(A, P[:, 0], rcond=None)[0]; cy = np.linalg.lstsq(A, P[:, 1], rcond=None)[0]
    at = lambda z: V((cx[0] * z + cx[1], cy[0] * z + cy[1], z))
    K[f"vai_{b}"] = at(FR["shoulder"] * H); K[f"khuyu_{b}"] = at(FR["elbow"] * H); K[f"co_tay_{b}"] = at(FR["wrist"] * H)
    s = 1 if b == "L" else -1
    K[f"xuong_don_{b}"] = V((s * 0.025 * H, K["nguc"].y, FR["shoulder"] * H - 0.01 * H))
if fail:
    for f in fail: print("⛔ joint:", f)
    sys.exit(1)
json.dump({k: [round(c, 4) for c in v] for k, v in K.items()}, open(jout, "w"), indent=1)

rig = HA.dung_rig(K)
bpy.ops.object.select_all(action="DESELECT"); body.select_set(True); rig.select_set(True); bpy.context.view_layer.objects.active = rig
bpy.ops.object.parent_set(type="ARMATURE_AUTO")
bpy.context.view_layer.objects.active = body
mats = {i: m.name for i, m in enumerate(body.data.materials)}
role = np.array([mats[p.material_index] for p in body.data.polygons]) if mats else None
vrole = {}
for p in body.data.polygons:
    for vi in p.vertices: vrole.setdefault(vi, set()).add(mats.get(p.material_index, ""))
G = {g.name: g for g in body.vertex_groups}; names = {g.index: g.name for g in body.vertex_groups}
zneck = K["co"].z
for v in body.data.vertices:
    r = vrole.get(v.index, set())
    if any("hair" in x for x in r) and v.co.z > zneck:            # hair above the neck = rigid on the head
        for n_ in [names[g.group] for g in v.groups]: body.vertex_groups[n_].remove([v.index])   # names first: removing shifts v.groups
        G["head"].add([v.index], 1.0, "REPLACE")
    elif any("leather" in x or "rope" in x for x in r):            # skirt: hips/thighs only, never the shins
        for n_ in [names[g.group] for g in v.groups]:
            if n_.startswith(("shin", "foot")): body.vertex_groups[n_].remove([v.index])
# image-to-3D fuses hands to the hips/skirt. Below the armpit, split ARM vs BODY by geometry: a vertex within ARM_R of the arm axis
# (shoulder→elbow→wrist→hand tip) belongs to the arm and listens ONLY to arm bones; every other vertex ignores arm bones.
# Faces joining the two regions are a generator web, not anatomy ⇒ cut (else raising an arm drags the skirt/hip along).
ARM_R = 0.065          # forearm/upper-arm tube radius (m)
HAND_R, HAND_LEN = 0.07, 0.11   # hand: fist ≈ 7 cm tube, wrist→fingertip ≈ 11 cm (sheet: wrist 0.49, fingertip 0.43 of height); longer/wider eats the thigh
WEB_FAR = 0.11         # body end of a web edge is ≥ 11 cm from the arm axis (hip/skirt); arm skin is closer
def seg_d(P, a_, b_):
    ab = b_ - a_; t = np.clip(((P - a_) @ ab) / max(ab @ ab, 1e-9), 0, 1); return np.linalg.norm(P - (a_ + t[:, None] * ab), axis=1)
P_ = np.array([v.co[:] for v in body.data.vertices]); region = np.array(["body"] * len(P_), dtype=object); DARM = np.full(len(P_), 9.0)
for b in "LR":
    j = [np.array(K[k][:]) for k in (f"vai_{b}", f"khuyu_{b}", f"co_tay_{b}")]; fdir = (j[2] - j[1]) / np.linalg.norm(j[2] - j[1])
    tip = j[2] + fdir * HAND_LEN
    R0 = max(ARM_R, 1.5 * float(np.median(rad[b]))) if rad[b] else ARM_R
    d = np.minimum.reduce([seg_d(P_, j[0], j[1]), seg_d(P_, j[1], j[2]), seg_d(P_, j[2], tip) * (R0 / max(HAND_R, 1.15 * R0))])   # hand: wider tube
    DARM = np.minimum(DARM, d)
    R_b = max(ARM_R, 1.5 * float(np.median(rad[b]))) if rad[b] else ARM_R        # tube = 1.5 × the measured arm radius
    region[(d < R_b) & (P_[:, 2] < (FR["armpit"] - 0.01) * H)] = "arm_" + b
    print(f"arm {b}: measured radius {np.median(rad[b]) * 100:.1f} cm → region tube {R_b * 100:.1f} cm")
# heat already says "hand/forearm" for palm verts outside the tube (hand flat on the thigh) ⇒ they are arm too
for v in body.data.vertices:
    if region[v.index] == "body" and v.groups and v.co.z < (FR["armpit"] - 0.01) * H and DARM[v.index] < 0.12:
        n_ = names[max(v.groups, key=lambda g: g.weight).group]
        if n_.startswith(("hand", "forearm")): region[v.index] = "arm_" + n_[-1]
for v in body.data.vertices:
    r = vrole.get(v.index, set())
    if any("leather" in x or "rope" in x for x in r): region[v.index] = "body"
ARMB = ("clavicle", "upperarm", "forearm", "hand")
for v in body.data.vertices:
    rg = region[v.index]
    for n_ in [names[g.group] for g in v.groups]:                 # names first: removing shifts v.groups under the iterator
        if rg == "body" and n_.startswith(ARMB) and v.co.z < (FR["armpit"] - 0.01) * H and DARM[v.index] > 0.10:   # heat bleed only
            body.vertex_groups[n_].remove([v.index])
        if rg.startswith("arm") and not (n_.startswith(ARMB) and n_.endswith(rg[-1])): body.vertex_groups[n_].remove([v.index])
    if rg.startswith("arm") and not v.groups:                      # arm vertex with no arm weight ⇒ nearest arm bone
        b = rg[-1]; cands = {f"upperarm_{b}": (K[f"vai_{b}"], K[f"khuyu_{b}"]), f"forearm_{b}": (K[f"khuyu_{b}"], K[f"co_tay_{b}"]),
                             f"hand_{b}": (K[f"co_tay_{b}"], K[f"co_tay_{b}"] + (K[f"co_tay_{b}"] - K[f"khuyu_{b}"]).normalized() * 0.13)}
        best_ = min(cands, key=lambda k: seg_d(np.array([v.co[:]]), np.array(cands[k][0][:]), np.array(cands[k][1][:]))[0])
        G[best_].add([v.index], 1.0, "REPLACE")
def islands(me):
    bm_ = bmesh.new(); bm_.from_mesh(me); seen = set(); n_ = 0
    for f in bm_.faces:
        if f.index in seen: continue
        n_ += 1; st = [f]
        while st:
            g = st.pop()
            if g.index in seen: continue
            seen.add(g.index); st += [h for e in g.edges for h in e.link_faces if h.index not in seen]
    bm_.free(); return n_
isl0 = islands(body.data)
bm = bmesh.new(); bm.from_mesh(body.data); bm.edges.ensure_lookup_table()
def is_web(e):                                                     # a real hand↔hip web: well below the armpit, and the body end
    a_, b_ = e.verts                                                 # sits far from the arm axis (not arm skin just outside the tube)
    if region[a_.index] == region[b_.index]: return False
    if max(a_.co.z, b_.co.z) > (FR["armpit"] - 0.05) * H: return False
    body_end = a_ if region[a_.index] == "body" else b_
    if DARM[body_end.index] > WEB_FAR: return True
    dv = body.data.vertices[body_end.index]                          # close to the arm but its main bone is leg/torso ⇒ hand-on-thigh contact
    return bool(dv.groups) and names[max(dv.groups, key=lambda g: g.weight).group].startswith(("thigh", "hips", "spine", "shin"))
web = [e for e in bm.edges if is_web(e)]
if os.environ.get("DEBUG_WEB"):
    def dn(v_):
        dv = body.data.vertices[v_.index]; return names[max(dv.groups, key=lambda g: g.weight).group] if dv.groups else None
    for e in web[:60]:
        a_, b_ = e.verts; print(f"  WEB z {a_.co.z:.2f}/{b_.co.z:.2f} x {a_.co.x:+.2f}/{b_.co.x:+.2f} reg {region[a_.index]}/{region[b_.index]} dom {dn(a_)}/{dn(b_)} darm {DARM[a_.index]:.2f}/{DARM[b_.index]:.2f}")
bmesh.ops.delete(bm, geom=web, context="EDGES"); bm.to_mesh(body.data); bm.free()     # removes the bridging edges AND their faces
print(f"arm region: {(region != 'body').sum()} verts · cut {len(web)} arm↔body web edges")
isl1 = islands(body.data); print(f"body pieces: {isl0} → {isl1} after the cut")
if isl1 > isl0 + 2: print("⛔ the web cut split the body into extra pieces (arm/hand torn off) — region tube too thin"); sys.exit(1)
bpy.ops.object.vertex_group_limit_total(group_select_mode="ALL", limit=4)
bpy.ops.object.vertex_group_normalize_all(lock_active=False)
empty = [v for v in body.data.vertices if not v.groups]
if empty:                                                          # heat missed (islands) ⇒ nearest weighted vertex
    for rg in set(region[v.index] for v in empty):                  # copy only from the SAME region (else body verts inherit hand weights)
        src_ = [v for v in body.data.vertices if v.groups and region[v.index] == rg]
        kd = mathutils.kdtree.KDTree(len(src_))
        for i, v in enumerate(src_): kd.insert(v.co, i)
        kd.balance()
        for v in [v for v in empty if region[v.index] == rg]:
            for e in src_[kd.find(v.co)[1]].groups: body.vertex_groups[names[e.group]].add([v.index], e.weight, "REPLACE")
    print(f"weights copied to {len(empty)} verts heat did not reach")
left = sum(1 for v in body.data.vertices if not v.groups); print(f"unweighted verts: {left}")
if left: print("⛔ unweighted verts"); sys.exit(1)

# ARMPIT / RIBCAGE / BREAST ownership (Boss 25/10: «sửa trọng số da nách của cơ thể, nhớ kiểm các clip animation cũ»; plan reviewed with
# Codex, 3 rounds). Heat gave the side of the ribcage upper-arm 0.24–0.57 + clavicle 0.2–0.6 and the breast clavicle 0.41–0.72, all
# ABOVE the measured axillary fold (the cleanup above only runs below FR armpit − 0.01 H): an arm swing dragged that skin through the top.
# Ownership: geodesic distance over the body's edges from confident TORSO seeds (below the fold inside the torso run; the sternum strip)
# and ARM seeds (arm tube below the fold; lateral to the shoulder joint); signed difference → a continuous torso-ownership blend (no
# 50/50 strip). On torso-owned skin the clavicle + upper-arm share fades with the geodesic distance from the resolved interface
# (smoothstep 0 → ARMPIT_D), the breast's clavicle is capped at BREAST_CLAV_CAP; the removed share goes to chest. Reverse THU_ARMPIT_OLD=1.
ARMPIT_D = float(os.environ.get("ARMPIT_D", 0.055)); BREAST_CLAV_CAP = float(os.environ.get("BREAST_CLAV_CAP", 0.10))
ARMPIT_BIAS = float(os.environ.get("ARMPIT_BIAS", 0.02)); ARMPIT_SMOOTH = int(os.environ.get("ARMPIT_SMOOTH", 10))   # m: moves the resolved interface toward the arm (the fused axilla dome)
def armpit_ownership():
    import heapq
    Pv = np.array([v.co[:] for v in body.data.vertices]); nv = len(Pv)
    kd_ = mathutils.kdtree.KDTree(len(P_))                             # the web cut may drop verts: map region labels by position
    for i, c in enumerate(P_): kd_.insert(c, i)
    kd_.balance(); region_ = np.array([region[kd_.find(c)[1]] for c in Pv], dtype=object)
    adj = [[] for _ in range(nv)]
    for e in body.data.edges:
        a_, b_ = e.vertices; d_ = float(np.linalg.norm(Pv[a_] - Pv[b_])); adj[a_].append((b_, d_)); adj[b_].append((a_, d_))
    def geo(seeds):
        D_ = np.full(nv, np.inf); hq = [(0.0, int(i)) for i in seeds]
        for _, i in hq: D_[i] = 0.0
        heapq.heapify(hq)
        while hq:
            d_, i = heapq.heappop(hq)
            if d_ > D_[i] or d_ > 0.25: continue
            for j, w_ in adj[i]:
                if d_ + w_ < D_[j]: D_[j] = d_ + w_; heapq.heappush(hq, (d_ + w_, j))
        return D_
    report = {}
    for b, sg in (("L", 1), ("R", -1)):
        z_fold = None; x_edge = None; miss = 0                         # highest z (scanning up) with the arm–torso gap on this side:
        for zf in np.arange(FR["armpit"] - 0.04, FR["shoulder"], 0.002):   # a gap > 1.2 % H whose inner end lies at |x| 0.08–0.15 m
            X = np.sort(sg * section(zf * H)[:, 0]); X = X[X > 0]; gp = np.diff(X)
            hit = [X[i] for i in np.where(gp > 0.012 * H)[0] if 0.08 < X[i] < 0.15]
            if hit: z_fold, x_edge, miss = zf * H, float(hit[0]), 0
            elif z_fold is not None:
                miss += 1
                if miss >= 3: break
        if z_fold is None: print(f"⛔ axillary fold {b} not found"); sys.exit(1)
        zs = K[f"vai_{b}"].z; xs = abs(K[f"vai_{b}"].x)
        sx = sg * Pv[:, 0]
        torso_seed = np.where(((Pv[:, 2] < z_fold) & (Pv[:, 2] > z_fold - 0.06) & (sx > 0) & (sx < x_edge - 0.005) & (region_ == "body")) |
                              ((sx > 0) & (sx < 0.03) & (Pv[:, 2] > z_fold) & (Pv[:, 2] < zs)))[0]
        arm_seed = np.where(((region_ == "arm_" + b) & (Pv[:, 2] < z_fold) & (Pv[:, 2] > z_fold - 0.08)) |
                            ((sx > xs + 0.01) & (Pv[:, 2] > z_fold) & (Pv[:, 2] < zs)))[0]
        dT, dA = geo(torso_seed), geo(arm_seed)
        roi = (sx > 0) & (Pv[:, 2] > z_fold - 0.04) & (Pv[:, 2] < zs) & np.isfinite(dT) & np.isfinite(dA)
        sdiff = np.where(roi, dA - dT + 2 * ARMPIT_BIAS, 0.0)          # > 0 ⇒ nearer the torso
        own = np.clip((sdiff + 0.015) / 0.03, 0, 1); own = own * own * (3 - 2 * own)
        dI = np.clip(sdiff / 2, 0, None)                               # distance from the resolved interface
        fade = np.clip(dI / ARMPIT_D, 0, 1); fade = fade * fade * (3 - 2 * fade)
        keep = 1 - own * fade                                          # arm share kept: 1 at the interface → 0 deep in the torso
        for _ in range(ARMPIT_SMOOTH):                                 # masked smoothing, boundary fixed: spreads the arm→torso transition
            nk = keep.copy()                                           # over more edges (the armpit stretched 2.7× when it sat in one band)
            for i in np.where(roi)[0]:
                nb = [j for j, _ in adj[i]]
                if nb: nk[i] = 0.5 * keep[i] + 0.5 * float(np.mean(keep[nb]))
            keep = np.where(roi, nk, keep)
        front = -Pv[:, 1]
        breast = roi & (own > 0.5) & (sx > 0.03) & (sx < x_edge + 0.02) & (front > K["nguc"].y * -1 + 0.04) & \
                 (Pv[:, 2] > FR["chest"] * H - 0.10) & (Pv[:, 2] < z_fold + 0.10)
        moved = 0
        for i in map(int, np.where(roi & (own > 0))[0]):
            v = body.data.vertices[i]; ws = {names[g.group]: g.weight for g in v.groups}; out_ = 0.0
            for n_, w_ in ws.items():
                if not n_.endswith("_" + b) or not n_.startswith(("clavicle", "upperarm")): continue
                nw = w_ * keep[i]
                if breast[i] and n_.startswith("clavicle"): nw = min(nw, BREAST_CLAV_CAP)
                if n_.startswith("upperarm") and breast[i]: nw = 0.0
                if nw < w_ - 1e-4: out_ += w_ - nw; body.vertex_groups[n_].add([i], nw, "REPLACE") if nw > 1e-4 else body.vertex_groups[n_].remove([i])
            if out_ > 0: G["chest"].add([i], ws.get("chest", 0.0) + out_, "REPLACE"); moved += 1
        report[b] = {"fold_z": round(z_fold, 3), "x_edge": round(x_edge, 3), "torso_seed": int(len(torso_seed)), "arm_seed": int(len(arm_seed)),
                     "roi": int(roi.sum()), "torso_owned": int((roi & (own > 0.5)).sum()), "breast": int(breast.sum()), "moved": moved,
                     "own": {int(i): round(float(own[i]), 3) for i in np.where(roi)[0]}, "breast_ids": [int(i) for i in np.where(breast)[0]]}
        print(f"armpit {b}: fold z {z_fold:.3f} · torso edge x {x_edge:.3f} · roi {roi.sum()} · torso-owned {(roi & (own > 0.5)).sum()} · "
              f"breast {breast.sum()} · reweighted {moved} (D {ARMPIT_D}, breast clavicle cap {BREAST_CLAV_CAP})")
    json.dump(report, open(jout.replace(".json", "_armpit.json"), "w"))
if os.environ.get("THU_ARMPIT_OLD") != "1":
    armpit_ownership()
    bpy.ops.object.vertex_group_limit_total(group_select_mode="ALL", limit=4); bpy.ops.object.vertex_group_normalize_all(lock_active=False)
# SKIRT follows the legs PER VERTEX (Boss 25/10: «khi chạy lòi da ở bụng hay đùi»; plan reviewed with Codex, 3 rounds): one tube with
# halved thigh weights could not follow a stride — belly, glutes and thigh skin came through in walk / run / carry. Now each tier keeps the
# body's own hips/spine/chest blend (thigh share folded into hips) pinned over its top WB_H; below that a vertex takes the thigh of its
# side by t (0 at the pin → 1 at the tier's hem, smoothstep) × lateralness (|sin azimuth| mapped 10°→60°, so the front/back midline stays
# hips-dominant and both thighs fade to 0 there — no crease) × SKIRT_HEM_THIGH. The ornament stays rigid: one blend for all its verts.
# Codex vetoed island-centre ownership (a 136–159° panel spans several regions). Reverse THU_SKIRT_OLD=1 (halved thigh + global smoothing).
WB_H = 0.03
# ONE field for every skirt layer (t from the belt pin down to the lowest hem of ALL skirt layers): per-tier gradients (upper 0.35, lower
# 0.9) let the tan lower tier poke through the dark upper tier in a run — overlapping layers must carry the same weights at the same spot
SKIRT_HEM_THIGH = float(os.environ.get("SKIRT_HEM_THIGH", 0.9)); SKIRT_LAT = tuple(float(x) for x in os.environ.get("SKIRT_LAT", "5,35").split(","))
SKIRT_SPAN = None   # (z_pin, z_hem) over all skirt layers, set before the layer loop
CENTRAL_MIN = float(os.environ.get("CENTRAL_MIN", 0.4))
def skirt_by_vertex(L, nm):
    nv = len(L.data.vertices); P = np.array([v.co[:] for v in L.data.vertices]); W = []
    for v in L.data.vertices:                                          # transferred weights, thigh share folded into hips
        d = {}
        for g in v.groups:
            n_ = "hips" if nm[g.group].startswith("thigh") else nm[g.group]; d[n_] = d.get(n_, 0.0) + g.weight
        W.append(d)
    if "ornament" in L.name:                                           # rigid: the mean blend
        m = {}
        for d in W:
            for k, w_ in d.items(): m[k] = m.get(k, 0.0) + w_ / nv
        W = [dict(m) for _ in range(nv)]
    elif "belt" not in L.name:
        z_pin, z_bot = SKIRT_SPAN; hem, (la, lb) = SKIRT_HEM_THIGH, SKIRT_LAT
        for i in range(nv):
            t = float(np.clip((z_pin - P[i, 2]) / max(z_pin - z_bot, 1e-6), 0, 1)); t = t * t * (3 - 2 * t)
            sa = abs(P[i, 0]) / max(np.hypot(P[i, 0], P[i, 1]), 1e-6)            # |sin azimuth|, 0 = front/back midline
            u = float(np.clip((sa - np.sin(np.radians(la))) / (np.sin(np.radians(lb)) - np.sin(np.radians(la))), 0, 1)); u = u * u * (3 - 2 * u)
            # the midline keeps CENTRAL_MIN of the thigh share, split L/R smoothly over ±4 cm: with 0 there the glutes came through the
            # back panel when she bends over (place_wood) — both thighs flex the same way and the panel stayed on the hips
            wt = hem * t * max(u, CENTRAL_MIN)
            if wt < 1e-4: continue
            cL = float(np.clip(0.5 + P[i, 0] / 0.08, 0, 1)); cL = cL * cL * (3 - 2 * cL)
            W[i] = {k: w_ * (1 - wt) for k, w_ in W[i].items()}
            if cL > 1e-3: W[i]["thigh_L"] = wt * cL
            if cL < 1 - 1e-3: W[i]["thigh_R"] = wt * (1 - cL)
    for g in L.vertex_groups: g.remove(list(range(nv)))
    for i, d in enumerate(W):
        tot = sum(d.values()) or 1.0
        for n_, w_ in d.items():
            if w_ > 1e-4: L.vertex_groups[n_].add([i], w_ / tot, "REPLACE")
    print(f"  skirt {L.name}: per-vertex thigh from the shared field, hem {SKIRT_HEM_THIGH}, lateral {SKIRT_LAT}")


# Robust Weight Transfer (Boss 25/10: «Thử plugin robust weight transfer»): LAYER_TRANSFER=rwt replaces the nearest-face Data Transfer
# for every outfit layer with the SIGGRAPH Asia 2023 inpainting transfer (rwt_transfer.py, run in ~/.venvs/rwt — libigl has no wheel for
# Blender's Python). SKIRT_MODE=rwt keeps the RWT skirt weights as they come (no shared thigh field) for the A/B.
LAYER_TRANSFER = os.environ.get("LAYER_TRANSFER", "nearest"); SKIRT_MODE = os.environ.get("SKIRT_MODE", "field")
RWT_LAYERS = os.environ.get("RWT_LAYERS", "outfit_upper")   # A/B 25/10: RWT helped the top, made the skirt worse (carry 78.6 mm, place 6.3 → 10.3 % skin)
def _arrays(o):
    me = o.data; me.calc_loop_triangles()
    Vv = np.array([v.co[:] for v in me.vertices]); Nn = np.array([v.normal[:] for v in me.vertices])
    Ff = np.array([t.vertices[:] for t in me.loop_triangles], dtype=np.int64); return Vv, Ff, Nn
_BODY_ARR = None
def rwt_weights(L):
    global _BODY_ARR
    import subprocess, tempfile
    if _BODY_ARR is None:
        V1, F1, N1 = _arrays(body); W1 = np.zeros((len(V1), len(body.vertex_groups)), np.float32)
        for v in body.data.vertices:
            for g in v.groups: W1[v.index, g.group] = g.weight
        _BODY_ARR = (V1, F1, N1, W1)
    V1, F1, N1, W1 = _BODY_ARR; V2, F2, N2 = _arrays(L)
    td = tempfile.mkdtemp(); fi, fo = os.path.join(td, "in.npz"), os.path.join(td, "out.npz")
    np.savez(fi, V1=V1, F1=F1, N1=N1, W1=W1, V2=V2, F2=F2, N2=N2)
    r = subprocess.run([os.path.expanduser("~/.venvs/rwt/bin/python"), os.path.join(os.path.dirname(os.path.abspath(__file__)), "rwt_transfer.py"), fi, fo],
                       capture_output=True, text=True)
    if r.returncode: print(r.stdout[-1500:], r.stderr[-1500:]); print(f"⛔ RWT failed on {L.name}"); sys.exit(1)
    print(f"  {L.name}: " + r.stdout.strip().splitlines()[-1])
    W2 = np.load(fo)["W2"]
    for gi, g in enumerate(body.vertex_groups):
        col = W2[:, gi]
        if not col.any(): continue
        tg = L.vertex_groups[g.name]
        for vi in np.where(col > 1e-4)[0]: tg.add([int(vi)], float(col[vi]), "REPLACE")


_sk = [L for L in layers if any(k in L.name for k in ("lower", "skirt", "lining")) and not any(k in L.name for k in ("belt", "ornament"))]
if _sk:
    _z = np.concatenate([[v.co.z for v in L.data.vertices] for L in _sk]); SKIRT_SPAN = (float(_z.max()) - WB_H, float(_z.min()))
for L in layers:                                                   # hair / outfit layers: weights from the nearest body surface
    for g in body.vertex_groups:
        if g.name not in L.vertex_groups: L.vertex_groups.new(name=g.name)
    if LAYER_TRANSFER == "rwt" and not L.name.startswith("hair") and (RWT_LAYERS == "all" or RWT_LAYERS in L.name): rwt_weights(L)
    else:
        dt = L.modifiers.new("dt", "DATA_TRANSFER"); dt.object = body; dt.use_vert_data = True
        dt.data_types_verts = {"VGROUP_WEIGHTS"}; dt.vert_mapping = "POLYINTERP_NEAREST"
        bpy.context.view_layer.objects.active = L; bpy.ops.object.datalayout_transfer(modifier="dt"); bpy.ops.object.modifier_apply(modifier="dt")
    nm = {g.index: g.name for g in L.vertex_groups}; hair = "hair" in L.name
    for v in L.data.vertices:
        gn = [nm[g.group] for g in v.groups]
        if hair and v.co.z > K["co"].z:                              # hair/beard above the neck: rigid on the head
            for n_ in gn: L.vertex_groups[n_].remove([v.index])
            L.vertex_groups["head"].add([v.index], 1.0, "REPLACE"); continue
        # a TOP at the armpit: the skin there rides clavicle / upper arm, children of CHEST — dropping that share and renormalising handed it
        # to spine, the band lagged the skin and the armpit came through it in twist / walk / run (bandeau v9, 5.7–12.5 mm, 25/10) ⇒ the
        # share goes to chest instead. Reverse THU_TOP_ARM_TO_SPINE=1.
        to_chest = "upper" in L.name and os.environ.get("THU_TOP_ARM_TO_SPINE") != "1"
        for n_ in gn:                                                # outfit / long hair: never follow arms, shins or feet
            if n_.startswith(("clavicle", "upperarm", "forearm", "hand", "shin", "foot")):
                if to_chest and n_.startswith(("clavicle", "upperarm")):
                    w_ = next(g.weight for g in v.groups if nm[g.group] == n_); L.vertex_groups["chest"].add([v.index], w_, "ADD")
                L.vertex_groups[n_].remove([v.index])
        if not v.groups: L.vertex_groups["hips" if v.co.z < K["bung"].z else "chest"].add([v.index], 1.0, "REPLACE")
    if any(k in L.name for k in ("lower", "skirt", "lining")) and SKIRT_MODE == "rwt": pass   # A/B: RWT skirt weights untouched
    elif any(k in L.name for k in ("lower", "skirt", "lining")) and os.environ.get("THU_SKIRT_OLD") != "1": skirt_by_vertex(L, nm)
    elif any(k in L.name for k in ("lower", "skirt", "lining")):               # skirt: one rigid-ish tube, not two legs — thigh weights halved into the
        hips = L.vertex_groups["hips"]                                  # hips then smoothed over the surface (both thighs at full weight tore the
        for v in L.data.vertices:                                       # front panel 4.8× in a stride, measured 25/10)
            for g in list(v.groups):
                n_ = nm[g.group]
                if n_.startswith("thigh"): w = g.weight; L.vertex_groups[n_].add([v.index], w * 0.5, "REPLACE"); hips.add([v.index], w * 0.5, "ADD")
        # smooth every group over the mesh edges (10 × half-step to the neighbour mean) — done in Python: the operator's poll fails when
        # the armature is left in pose mode
        nv = len(L.data.vertices); Eg = np.array([e.vertices[:] for e in L.data.edges]); deg = np.bincount(Eg.ravel(), minlength=nv).astype(float)
        for g in L.vertex_groups:
            w = np.zeros(nv)
            for v in L.data.vertices:
                for e in v.groups:
                    if e.group == g.index: w[v.index] = e.weight
            if not w.any(): continue
            for _ in range(10):
                acc = np.zeros(nv); np.add.at(acc, Eg[:, 0], w[Eg[:, 1]]); np.add.at(acc, Eg[:, 1], w[Eg[:, 0]])
                w = 0.5 * w + 0.5 * np.where(deg > 0, acc / np.maximum(deg, 1), w)
            for vi in range(nv):
                if w[vi] > 1e-4: g.add([vi], float(w[vi]), "REPLACE")
                else: g.remove([vi])
    bpy.ops.object.vertex_group_limit_total(group_select_mode="ALL", limit=4); bpy.ops.object.vertex_group_normalize_all(lock_active=False)
    am = L.modifiers.new("arm", "ARMATURE"); am.object = rig; L.parent = rig
    print(f"layer {L.name}: weights from body, {len(L.data.vertices)} verts")

Vt = np.array([v.co[:] for v in body.data.vertices]); E = np.array([e.vertices[:] for e in body.data.edges])
# pose test: arms up/forward, a stride; measure the worst edge stretch vs rest
def edge_len(co): return np.linalg.norm(co[E[:, 0]] - co[E[:, 1]], axis=1)
rest = edge_len(Vt)
LE = {L.name: (np.array([v.co[:] for v in L.data.vertices]), np.array([e.vertices[:] for e in L.data.edges])) for L in layers}
bpy.context.view_layer.objects.active = rig; bpy.ops.object.mode_set(mode="POSE")
pb = rig.pose.bones
from mathutils import Euler
for b, sgn in (("L", 1), ("R", -1)):
    pb[f"upperarm_{b}"].rotation_quaternion = Euler((math.radians(-50), 0, math.radians(25 * sgn))).to_quaternion()
    pb[f"forearm_{b}"].rotation_quaternion = Euler((math.radians(-40), 0, 0)).to_quaternion()
pb["ik_L"].location = (0, -0.25, 0.12); pb["spine"].rotation_quaternion = Euler((math.radians(8), 0, 0)).to_quaternion()
bpy.ops.object.mode_set(mode="OBJECT"); bpy.context.view_layer.update()
dg = bpy.context.evaluated_depsgraph_get(); ev = body.evaluated_get(dg); me = ev.to_mesh()
posed = np.array([v.co[:] for v in me.vertices]); ev.to_mesh_clear()
stretch = edge_len(posed) / np.maximum(rest, 1e-6); worst = float(np.percentile(stretch, 99.9)); mx = float(stretch.max())
for L in layers:
    ev2 = L.evaluated_get(dg); me2 = ev2.to_mesh(); P2 = np.array([v.co[:] for v in me2.vertices]); ev2.to_mesh_clear()
    R2, E2 = LE[L.name]; st2 = np.linalg.norm(P2[E2[:, 0]] - P2[E2[:, 1]], axis=1) / np.maximum(np.linalg.norm(R2[E2[:, 0]] - R2[E2[:, 1]], axis=1), 1e-6)
    print(f"  layer {L.name}: stretch p99.9 {np.percentile(st2, 99.9):.2f}× · max {st2.max():.2f}×"); worst = max(worst, float(np.percentile(st2, 99.9)))
print(f"pose test: edge stretch p99.9 {worst:.2f}× · max {mx:.2f}×")
if os.environ.get("DEBUG_STRETCH"):
    dom = lambda vi: max(body.data.vertices[vi].groups, key=lambda e: e.weight) if body.data.vertices[vi].groups else None
    for ei in np.argsort(-stretch)[:12]:
        a_, b_ = E[ei]; da_, db_ = dom(a_), dom(b_)
        print(f"  {stretch[ei]:.1f}× z {Vt[a_][2]:.2f}/{Vt[b_][2]:.2f} x {Vt[a_][0]:+.2f}/{Vt[b_][0]:+.2f} reg {region[a_] if a_ < len(region) else '?'}/{region[b_] if b_ < len(region) else '?'} "
              f"bones {names[da_.group] if da_ else None}/{names[db_.group] if db_ else None} roles {vrole.get(a_)}/{vrole.get(b_)}")
res = {"verts": len(Vt), "height_m": round(float(H), 3), "stretch_p999": round(worst, 2), "stretch_max": round(mx, 2)}
if pose_png:
    sc = bpy.context.scene
    for eng in ("BLENDER_EEVEE_NEXT", "BLENDER_EEVEE"):
        try: sc.render.engine = eng; break
        except TypeError: pass
    sc.view_settings.view_transform = "Standard"; sc.render.resolution_x, sc.render.resolution_y = 700, 900; sc.render.film_transparent = True
    sun = bpy.data.objects.new("sun", bpy.data.lights.new("sun", "SUN")); sc.collection.objects.link(sun); sun.data.energy = 3.0
    sun.rotation_euler = (math.radians(55), 0, math.radians(-35))
    w = bpy.data.worlds.new("w"); sc.world = w; w.use_nodes = True
    bg = next(n for n in w.node_tree.nodes if n.type == "BACKGROUND"); bg.inputs[1].default_value = 0.55
    cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam")); sc.collection.objects.link(cam); sc.camera = cam
    cam.data.type = "ORTHO"; cam.data.ortho_scale = H * 1.25; aa = math.radians(30)
    cam.location = (6 * math.sin(aa), -6 * math.cos(aa), H * 0.5); cam.rotation_euler = (math.radians(90), 0, aa)
    rig.show_in_front = True; rig.data.display_type = "STICK"
    sc.render.filepath = pose_png; bpy.ops.render.render(write_still=True)
# back to rest and export
bpy.context.view_layer.objects.active = rig; bpy.ops.object.mode_set(mode="POSE")
for p in rig.pose.bones: p.rotation_quaternion = (1, 0, 0, 0); p.location = (0, 0, 0)
bpy.ops.object.mode_set(mode="OBJECT")
bpy.ops.export_scene.gltf(filepath=dst, export_format="GLB", export_skins=True, export_animations=False)
json.dump(res, open(jout.replace(".json", "_rig_report.json"), "w"), indent=1)
if worst > STRETCH_MAX: print(f"⛔ pose test tears the mesh (> {STRETCH_MAX}×)"); sys.exit(1)
print(f"✅ RIGGED → {dst}")

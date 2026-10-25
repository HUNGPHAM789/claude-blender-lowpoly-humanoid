"""Blender: play OLD settler clips (same bone names) on a rigged, dressed character and measure every frame — clipping per layer (layer vertex
inside the posed body, ray parity as in pose_test_blender.py) and the body's edge stretch. Proof that a rig change did not make old clips worse
(Boss 25/10/2026: «sửa trọng số da nách của cơ thể, nhớ kiểm các clip animation cũ»).

  blender -b -P clip_check_blender.py -- <rigged.glb> <out.json> <clip.glb> [<clip.glb> …] [--sheet <prefix>] [--step 2]

Retarget = per-bone rotation DELTA in armature space (clip pose × clip rest⁻¹ applied to the character's rest), parents first; the hips
translation is copied as an offset from rest, scaled by the hips-height ratio. IK bones/constraints are ignored (clips are baked FK).
"""
import bpy, sys, json, math, os
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree

a = sys.argv[sys.argv.index("--") + 1:]
char, out = a[0], a[1]
sheet = a[a.index("--sheet") + 1] if "--sheet" in a else None
step = int(a[a.index("--step") + 1]) if "--step" in a else 2
views = [int(x) for x in a[a.index("--views") + 1].split(",")] if "--views" in a else None   # frames to render front/left/back/right
clips = [x for x in a[2:] if x.endswith(".glb") and x not in (sheet,)]
if views: step = 1
SKIP = ("ik_", "pole_")

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=char)
rig = next(o for o in bpy.context.scene.objects if o.type == "ARMATURE")
meshes = [o for o in bpy.context.scene.objects if o.type == "MESH"]
body = next(o for o in meshes if o.name.lower() == "body" or "body" in o.name.lower())
layers = [o for o in meshes if o is not body and (o.parent == rig or any(m.type == "ARMATURE" for m in o.modifiers))]
for pb in rig.pose.bones:
    pb.rotation_mode = "QUATERNION"
    for c in pb.constraints: c.influence = 0.0
rest_co = {L.name: [L.matrix_world @ v.co for v in L.data.vertices] for L in layers}
BE = [e.vertices[:] for e in body.data.edges]
B0 = [body.matrix_world @ v.co for v in body.data.vertices]
rest_len = [max((B0[i] - B0[j]).length, 1e-6) for i, j in BE]
import numpy as _np
B0n = _np.array([c[:] for c in B0]); BEn = _np.array(BE); RL = _np.array(rest_len)
def _reg(c):                                                           # Blender frame: Z up, front −Y; regions Codex asked to watch
    x, y, z = abs(c[0]), -c[1], c[2]
    if 1.08 < z < 1.26 and 0.09 < x < 0.17: return "armpit"
    if 1.05 < z < 1.25 and x < 0.12 and y > 0.06: return "breast"
    if z >= 1.22 and x >= 0.13: return "shoulder"
    if 0.62 < z < 0.95: return "hip_thigh"
    return "other"
EREG = _np.array([_reg((B0n[i] + B0n[j]) / 2) for i, j in BE])
BF = [p.vertices[:] for p in body.data.polygons]
def _area(Pa, f): return (Pa[f[1]] - Pa[f[0]]).cross(Pa[f[2]] - Pa[f[0]]).length / 2 if len(f) >= 3 else 0.0
A0 = _np.array([max(_area(B0, f), 1e-9) for f in BF])
# SKIN SHOWING THROUGH (what the eye sees; Codex: vertex parity misses skin crossing BETWEEN cloth vertices — Boss saw the glutes through
# the back panel in place_wood while the parity count said 0.5 %): body verts COVERED at rest (a ray along the vertex normal hits the
# garment group within 6 cm) and, per frame, on the OTHER side of the nearest garment surface than at rest by > 1 mm.
GROUPS = {"top": ("leather", "rope_bone"), "skirt": ("skirt_upper_tier", "skirt_lower_tier", "rope_belt", "ornament")}
def _gmesh(objs, dg=None):
    V_, F_ = [], []
    for o in objs:
        src_ = o.evaluated_get(dg) if dg else o; me_ = src_.to_mesh(); off = len(V_)
        V_ += [o.matrix_world @ v.co for v in me_.vertices]; F_ += [tuple(i + off for i in p_.vertices) for p_ in me_.polygons]; src_.to_mesh_clear()
    return V_, F_
GOBJ = {g: [L for L in layers if any(k in L.name for k in ks)] for g, ks in GROUPS.items()}
COVER = {}
for g, objs in GOBJ.items():
    if not objs: continue
    V_, F_ = _gmesh(objs); bv = BVHTree.FromPolygons(V_, F_); cov = []
    for v in body.data.vertices:
        co = body.matrix_world @ v.co; n_ = (body.matrix_world.to_3x3() @ v.normal).normalized()
        hit = bv.ray_cast(co + n_ * 1e-4, n_, 0.06)
        if hit[0] is None: continue
        loc, nrm, _, d0 = bv.find_nearest(co)
        if d0 > 0.03 or not v.groups: continue                          # the cloth sits on this skin (≤ 3 cm)
        if body.vertex_groups[max(v.groups, key=lambda g_: g_.weight).group].name.startswith(("clavicle", "upperarm", "forearm", "hand")) and g == "skirt":
            continue                                                   # a hand resting by the skirt is not skin under it
        cov.append((v.index, 1 if (co - loc).dot(nrm) > 0 else -1))
    COVER[g] = cov
print("covered skin verts:", {g: len(c) for g, c in COVER.items()})
VISIBLE = "--visible" in a
HJ = json.load(open(a[a.index("--hidden") + 1])) if "--hidden" in a else {}
HID = HJ.get("hidden_centres"); HOBJ = {k: v["hidden_centres"] for k, v in HJ.get("objects", {}).items() if k != "body"}
if VISIBLE:                                                            # emission ID render: skin hidden under cloth at rest RED, other skin
    from mathutils.kdtree import KDTree                                # BLUE, outfit/hair GREEN both sides, any BODY back-face YELLOW
    hid = set()                                                        # (= looking through a hole into the body: the cost of masking)
    if HID:
        kd = KDTree(len(body.data.polygons))
        for p_ in body.data.polygons: kd.insert(body.matrix_world @ p_.center, p_.index)
        kd.balance(); hid = {kd.find(c)[1] for c in HID if kd.find(c)[2] < 1e-4}
    ca = body.data.color_attributes.new("idc", "FLOAT_COLOR", "CORNER")
    for p_ in body.data.polygons:
        col = (1, 0, 0, 1) if p_.index in hid else (0, 0, 1, 1)
        for li in p_.loop_indices: ca.data[li].color = col
    def _emis(name, attr=None, rgb=None, back=None):
        m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; nt.nodes.clear()
        out = nt.nodes.new("ShaderNodeOutputMaterial"); em = nt.nodes.new("ShaderNodeEmission")
        if attr:
            at = nt.nodes.new("ShaderNodeAttribute"); at.attribute_name = attr; src_ = at.outputs["Color"]
        else:
            rg = nt.nodes.new("ShaderNodeRGB"); rg.outputs[0].default_value = rgb; src_ = rg.outputs[0]
        if back:
            geo = nt.nodes.new("ShaderNodeNewGeometry"); mix = nt.nodes.new("ShaderNodeMix"); mix.data_type = "RGBA"
            nt.links.new(geo.outputs["Backfacing"], mix.inputs["Factor"]); nt.links.new(src_, mix.inputs[6]); mix.inputs[7].default_value = back
            src_ = mix.outputs[2]
        nt.links.new(src_, em.inputs["Color"]); nt.links.new(em.outputs[0], out.inputs["Surface"]); return m
    mb = _emis("idbody", attr="idc", back=(1, 1, 0, 1)); mg = _emis("idcloth", rgb=(0, 1, 0, 1)); mi = _emis("idinner", attr="idc")
    body.data.materials.clear(); body.data.materials.append(mb)
    for L in layers:
        L.data.materials.clear()
        if L.name in HOBJ:                                             # inner cloth hidden at rest: MAGENTA when it shows (cloth through cloth)
            kd2 = KDTree(len(L.data.polygons))
            for p_ in L.data.polygons: kd2.insert(L.matrix_world @ p_.center, p_.index)
            kd2.balance(); hl = {kd2.find(c)[1] for c in HOBJ[L.name] if kd2.find(c)[2] < 1e-4}
            c2 = L.data.color_attributes.new("idc", "FLOAT_COLOR", "CORNER")
            for p_ in L.data.polygons:
                for li in p_.loop_indices: c2.data[li].color = (1, 0, 1, 1) if p_.index in hl else (0, 1, 0, 1)
            L.data.materials.append(mi)
        else: L.data.materials.append(mg)
    sc_ = bpy.context.scene
    for eng in ("BLENDER_EEVEE_NEXT", "BLENDER_EEVEE"):
        try: sc_.render.engine = eng; break
        except TypeError: pass
    sc_.view_settings.view_transform = "Standard"; sc_.render.filter_size = 0.0
    sc_.render.resolution_x, sc_.render.resolution_y = 240, 300; sc_.render.film_transparent = True
    vcam = bpy.data.objects.new("vcam", bpy.data.cameras.new("vcam")); sc_.collection.objects.link(vcam); sc_.camera = vcam
    vcam.data.type = "ORTHO"; vcam.data.ortho_scale = 0.95
    rig.hide_render = True
    for o in bpy.context.scene.objects:
        if o.type == "MESH" and o is not body and o not in layers: o.hide_render = True
def visible_px(tag):
    out = {"through": 0, "hole": 0, "cloth": 0}
    for vw, yaw in (("front", 0), ("left", 75), ("back", 180), ("right", -75)):
        aa_ = math.radians(yaw); vcam.location = (6 * math.sin(aa_), -6 * math.cos(aa_), 0.98); vcam.rotation_euler = (math.radians(90), 0, aa_)
        fp = f"/tmp/_vis_{os.getpid()}.png"; bpy.context.scene.render.filepath = fp; bpy.ops.render.render(write_still=True)
        im = bpy.data.images.load(fp); px = _np.array(im.pixels[:]).reshape(-1, 4); bpy.data.images.remove(im)
        vis = px[:, 3] > 0.5; r, g_, b_ = px[:, 0], px[:, 1], px[:, 2]
        out["cloth"] += int((vis & (r > 0.6) & (g_ < 0.3) & (b_ > 0.6)).sum())
        out["through"] += int((vis & (r > 0.6) & (g_ < 0.3) & (b_ < 0.3)).sum()); out["hole"] += int((vis & (r > 0.6) & (g_ > 0.6) & (b_ < 0.3)).sum())
    return out
bnm = {g.index: g.name for g in body.vertex_groups}
DOM = [bnm[max(v.groups, key=lambda g: g.weight).group] if v.groups else "?" for v in body.data.vertices]   # body part a clip lands in
ARMISH = ("clavicle", "upperarm", "forearm", "hand")
order = [b.name for b in rig.data.bones if not b.name.startswith(SKIP)]          # bones come parents-first
hips_h = rig.data.bones["hips"].head_local.z

DIRS = (Vector((0, 0, 1)), Vector((0.3, 0.2, 0.93)).normalized())
def crossings(bvh, co, d, n=0):
    o = co.copy()
    while n < 50:
        hit = bvh.ray_cast(o, d)
        if hit[0] is None: return n
        n += 1; o = hit[0] + d * 1e-5
    return n

sc = bpy.context.scene
if sheet:
    for eng in ("BLENDER_EEVEE_NEXT", "BLENDER_EEVEE"):
        try: sc.render.engine = eng; break
        except TypeError: pass
    sc.view_settings.view_transform = "Standard"; sc.render.resolution_x, sc.render.resolution_y = 360, 460
    w = bpy.data.worlds.new("w"); sc.world = w; w.use_nodes = True
    bg = next(n for n in w.node_tree.nodes if n.type == "BACKGROUND"); bg.inputs[0].default_value = (1, 1, 1, 1)
    for nm, en, rot in (("key", 3.5, (55, 0, -35)), ("fill", 1.5, (60, 0, 140))):
        L_ = bpy.data.objects.new(nm, bpy.data.lights.new(nm, "SUN")); sc.collection.objects.link(L_); L_.data.energy = en
        L_.rotation_euler = tuple(math.radians(x) for x in rot)
    cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam")); sc.collection.objects.link(cam); sc.camera = cam
    cam.data.type = "ORTHO"; cam.data.ortho_scale = 2.2; aa = math.radians(35)
    rig.hide_render = True

res = {}
for clip in clips:
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=clip)
    new = [o for o in bpy.data.objects if o not in before]
    src = next(o for o in new if o.type == "ARMATURE")
    for o in new:
        if o is not src: o.hide_render = True; o.hide_viewport = True
    act = src.animation_data.action if src.animation_data and src.animation_data.action else None
    if act is None:                                                      # NLA-only import: the armature's own strip (not the prop's)
        act = next(st.action for tr in src.animation_data.nla_tracks for st in tr.strips if st.action)
        for tr in src.animation_data.nla_tracks: tr.mute = True
        src.animation_data_create(); src.animation_data.action = act
    f0, f1 = (int(round(x)) for x in act.frame_range)
    s_hips_h = src.data.bones["hips"].head_local.z; k = hips_h / max(s_hips_h, 1e-6)
    name = clip.rsplit("/", 2)[-2] + "/" + clip.rsplit("/", 1)[-1]
    frames = []
    for f in range(f0, f1 + 1, step):
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
                M.translation.y = rig.data.bones[n].head_local.y                     # no root travel
            pc.matrix = M; bpy.context.view_layer.update()
        dg = bpy.context.evaluated_depsgraph_get()
        be = body.evaluated_get(dg); bm = be.to_mesh(); mw = body.matrix_world
        P = [mw @ v.co for v in bm.vertices]
        PF = [p.vertices[:] for p in bm.polygons]; bvh = BVHTree.FromPolygons(P, PF); be.to_mesh_clear()
        st = sorted((P[i] - P[j]).length / rest_len[e] for e, (i, j) in enumerate(BE))
        row = {"frame": f, "body_stretch_p999": round(st[int(0.999 * (len(st) - 1))], 3), "layers": {}}
        Pn = _np.array([c[:] for c in P]); ratio = _np.linalg.norm(Pn[BEn[:, 0]] - Pn[BEn[:, 1]], axis=1) / RL
        row["region"] = {rg: [round(float(_np.percentile(ratio[EREG == rg], 0.1)), 3), round(float(_np.percentile(ratio[EREG == rg], 99.9)), 3)]
                         for rg in ("armpit", "breast", "shoulder", "hip_thigh") if (EREG == rg).any()}
        row["show"] = {}
        for g, cov in COVER.items():
            V_, F_ = _gmesh(GOBJ[g], dg); bv = BVHTree.FromPolygons(V_, F_); bad = []
            for vi, sg0 in cov:
                loc, nrm, _, dist = bv.find_nearest(P[vi])
                if loc is None: continue
                if (1 if (P[vi] - loc).dot(nrm) > 0 else -1) != sg0 and 0.001 < dist < 0.04:
                    b0 = B0[vi]; bad.append([round(b0.x, 4), round(b0.z, 4), round(-b0.y, 4), round(dist * 1000, 2), DOM[vi]])
            row["show"][g] = {"n": len(bad), "frac": round(len(bad) / max(len(cov), 1), 4), "max_mm": max([b_[3] for b_ in bad], default=0.0), "verts": bad}
        if VISIBLE: row["visible_px"] = visible_px(f)
        ar = _np.array([_area(P, f_) for f_ in BF]) / A0
        row["area_min"] = round(float(ar.min()), 3); row["area_lt20"] = int((ar < 0.2).sum())
        for L in layers:
            le = L.evaluated_get(dg); lm = le.to_mesh(); pen = []
            for i, v in enumerate(lm.vertices):
                co = L.matrix_world @ v.co; hit = bvh.find_nearest(co, 0.3)
                if hit[0] is None: continue
                loc, nrm, fi, dist = hit
                if (co - loc).dot(nrm) < 0 and all(crossings(bvh, co, d_) % 2 == 1 for d_ in DIRS):
                    bone = DOM[min(PF[fi], key=lambda k_: (P[k_] - loc).length)]
                    r = rest_co[L.name][i]; pen.append([round(r.x, 4), round(r.z, 4), round(-r.y, 4), round(dist * 1000, 2), bone])
            skin = [p_ for p_ in pen if not p_[4].startswith(ARMISH)]          # torso / leg skin through the layer (arm-in-cloth reported apart)
            row["layers"][L.name] = {"n": len(pen), "frac": round(len(pen) / max(len(lm.vertices), 1), 4),
                                     "max_mm": max([p[3] for p in pen], default=0.0), "pen": pen,
                                     "skin_frac": round(len(skin) / max(len(lm.vertices), 1), 4), "skin_mm": max([p[3] for p in skin], default=0.0)}
            le.to_mesh_clear()
        frames.append(row)
        if sheet and views and f in views:                             # close-up of torso + hips from four sides
            cam.data.ortho_scale = 0.95; sc.render.resolution_x, sc.render.resolution_y = 420, 520
            for tag, yaw in (("front", 0), ("left", 75), ("back", 180), ("right", -75)):
                aa_ = math.radians(yaw); cam.location = (6 * math.sin(aa_), -6 * math.cos(aa_), 0.98); cam.rotation_euler = (math.radians(90), 0, aa_)
                sc.render.filepath = f"{sheet}_{name.replace('/', '_')[:-4]}_f{f}_{tag}.png"; bpy.ops.render.render(write_still=True)
        elif sheet and not views and f in (f0, (f0 + f1) // 2):
            cam.location = (6 * math.sin(aa), -6 * math.cos(aa), 0.95); cam.rotation_euler = (math.radians(90), 0, aa)
            sc.render.filepath = f"{sheet}_{name.replace('/', '_')[:-4]}_f{f}.png"; bpy.ops.render.render(write_still=True)
    worst = {}
    for L in layers:
        mm = max(r["layers"][L.name]["max_mm"] for r in frames); fr = max(r["layers"][L.name]["frac"] for r in frames)
        worst[L.name] = {"max_mm": mm, "max_frac": fr, "skin_mm": max(r["layers"][L.name]["skin_mm"] for r in frames),
                         "skin_frac": max(r["layers"][L.name]["skin_frac"] for r in frames)}
    res[name] = {"frames": frames, "worst": worst, "body_stretch_p999": max(r["body_stretch_p999"] for r in frames),
                 "region": {rg: [min(r["region"][rg][0] for r in frames), max(r["region"][rg][1] for r in frames)] for rg in frames[0]["region"]},
                 "area_min": min(r["area_min"] for r in frames), "area_lt20": max(r["area_lt20"] for r in frames),
                 "show": {g: {"max_frac": max(r["show"][g]["frac"] for r in frames), "max_mm": max(r["show"][g]["max_mm"] for r in frames),
                              "max_n": max(r["show"][g]["n"] for r in frames)} for g in COVER}}
    if VISIBLE:
        res[name]["visible_px"] = {g: max(r["visible_px"][g] for r in frames) for g in ("through", "hole", "cloth")}
        res[name]["visible_px_sum"] = {g: sum(r["visible_px"][g] for r in frames) for g in ("through", "hole", "cloth")}
        print(f"   {name} VISIBLE px (worst frame / all frames): skin through cloth {res[name]['visible_px']['through']} / {res[name]['visible_px_sum']['through']} · "
              f"hole into body {res[name]['visible_px']['hole']} / {res[name]['visible_px_sum']['hole']} · "
              f"inner cloth through cloth {res[name]['visible_px']['cloth']} / {res[name]['visible_px_sum']['cloth']}")
    print(f"   {name} skin through: " + " · ".join(f"{g} {v['max_n']} verts ({v['max_frac'] * 100:.1f} %) {v['max_mm']:.1f} mm" for g, v in res[name]["show"].items()))
    print(f"{name}: frames {f0}-{f1} · body stretch p99.9 {res[name]['body_stretch_p999']}× · "
          + " · ".join(f"{k_.split('__')[-1]} {v['max_mm']:.1f}mm/{v['max_frac'] * 100:.1f}%" for k_, v in worst.items() if v["max_mm"] > 0))
    for o in new:
        bpy.data.objects.remove(o, do_unlink=True)
json.dump(res, open(out, "w"))

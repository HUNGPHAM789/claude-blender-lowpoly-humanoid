"""Blender: which BODY faces are hidden under opaque clothing at rest, and (optionally) delete them — the game-industry fix for skin
showing through clothes (body masking; Boss 25/10/2026: «thử cách game hay dùng luôn»; Codex + research agent both ranked it first).

  blender -b -P hidden_skin_blender.py -- <rigged.glb> <hidden.json> [--apply <masked_rigged.glb>] [--margin 1]

HIDDEN = a body face that (1) no camera sees at rest — face-ID render (flat, no anti-aliasing, every face its own colour, outfit/hair
drawn black so they occlude) from 26 directions around the body plus 8 low/high diagonals — and (2) lies under an outfit layer
(a ray along the face normal hits an outfit layer within 6 cm). Faces within MARGIN edge-rings of a visible face are kept, so a tear or
the hem never opens a hole when the cloth moves. --apply deletes the hidden faces (and verts left without faces) and writes a new GLB
with the rig, weights and layers untouched.
"""
import bpy, bmesh, sys, json, math, os
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree

a = sys.argv[sys.argv.index("--") + 1:]
src, jout = a[0], a[1]
apply_to = a[a.index("--apply") + 1] if "--apply" in a else None
MARGIN = int(a[a.index("--margin") + 1]) if "--margin" in a else 1
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=src)
sc = bpy.context.scene
rig = next(o for o in sc.objects if o.type == "ARMATURE")
meshes = [o for o in sc.objects if o.type == "MESH"]
body = next(o for o in meshes if o.name.lower() == "body")
layers = [o for o in meshes if o is not body and (o.parent == rig or any(m.type == "ARMATURE" for m in o.modifiers))]
outfit = [o for o in layers if o.name.startswith("outfit")]
for o in meshes:
    if o is not body and o not in layers: o.hide_render = True

# (2) under an outfit layer
V_, F_ = [], []
for o in outfit:
    off = len(V_); V_ += [o.matrix_world @ v.co for v in o.data.vertices]; F_ += [tuple(i + off for i in p.vertices) for p in o.data.polygons]
bv = BVHTree.FromPolygons(V_, F_)
mw = body.matrix_world; nmat = mw.to_3x3().inverted().transposed()
under = set()
for p in body.data.polygons:
    c = mw @ p.center; n = (nmat @ p.normal).normalized()
    if bv.ray_cast(c + n * 1e-4, n, 0.06)[0] is not None: under.add(p.index)

# (1) face-ID render at rest — targets: the body + any INNER cloth layer named with --inner (Boss 25/10 «làm tiếp»: the tan skirt lining
# showed through the dark tiers at the front hem in run / place_wood; a lining face nobody sees at rest is deleted the same way)
INNER = [x for x in (a[a.index("--inner") + 1].split(",") if "--inner" in a else []) if x]
targets = [body] + [o for o in layers if any(k in o.name for k in INNER)]
offs, tot_ = {}, 0
for o in targets: offs[o.name] = tot_; tot_ += len(o.data.polygons)
for o in layers + [body]:
    c_ = o.data.color_attributes.new("fid", "FLOAT_COLOR", "CORNER")      # float + Raw view: the ID survives colour management
    for p in o.data.polygons:
        if o in targets:
            i = offs[o.name] + p.index + 1; col = ((i & 255) / 255, ((i >> 8) & 255) / 255, ((i >> 16) & 255) / 255, 1.0)
        else: col = (0, 0, 0, 1)
        for li in p.loop_indices: c_.data[li].color = col
    o.data.color_attributes.active_color = c_
sc.render.engine = "BLENDER_WORKBENCH"; sh = sc.display.shading; sh.light = "FLAT"; sh.color_type = "VERTEX"
sc.display.render_aa = "OFF"; sc.render.dither_intensity = 0.0
try: sc.view_settings.view_transform = "Raw"
except TypeError: sc.view_settings.view_transform = "Standard"
sc.render.resolution_x, sc.render.resolution_y = 640, 960; sc.render.film_transparent = True
sc.render.image_settings.file_format = "PNG"; sc.render.image_settings.color_depth = "8"
cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam")); sc.collection.objects.link(cam); sc.camera = cam
cam.data.type = "ORTHO"; cam.data.ortho_scale = 1.9; rig.hide_render = True
zs = [(mw @ v.co).z for v in body.data.vertices]; zc = (max(zs) + min(zs)) / 2
dirs = [(math.radians(az), math.radians(el)) for el in (0,) for az in range(0, 360, 15)] + \
       [(math.radians(az), math.radians(el)) for el in (-35, 35) for az in range(0, 360, 45)]
# inner cloth: the game camera never looks UP under the skirt — views below the horizon would mark the whole inside of the lining "seen"
# (173 / 236 faces) ⇒ inner layers count as seen only from views at or above the horizon; the body keeps every view
seen_g = set(); seen_hi = set()
for az, el in dirs:
    d = Vector((math.sin(az) * math.cos(el), -math.cos(az) * math.cos(el), math.sin(el)))
    cam.location = Vector((0, 0, zc)) + d * 6
    cam.rotation_euler = (-d).to_track_quat("-Z", "Y").to_euler()
    fp = f"/tmp/_fid_{os.getpid()}.png"; sc.render.filepath = fp; bpy.ops.render.render(write_still=True)
    im = bpy.data.images.load(fp); px = np.array(im.pixels[:]).reshape(-1, 4); bpy.data.images.remove(im)
    px = px[px[:, 3] > 0.5]; ids = np.rint(px[:, 0] * 255).astype(int) + (np.rint(px[:, 1] * 255).astype(int) << 8) + (np.rint(px[:, 2] * 255).astype(int) << 16)
    got = {int(i) - 1 for i in np.unique(ids) if 0 < i <= tot_}; seen_g |= got
    if el >= 0: seen_hi |= got
rep = {"views": len(dirs), "margin": MARGIN, "objects": {}}
plans = {}
for o in targets:
    n_ = len(o.data.polygons); off = offs[o.name]; omw = o.matrix_world
    seen = {i - off for i in (seen_g if o is body else seen_hi) if off <= i < off + n_}
    hidden = {i for i in (under if o is body else range(n_)) if i not in seen}
    pos_faces = {}                                                     # glTF flat shading splits every face's vertices ⇒ neighbours by
    key = lambda vi: tuple(np.round(np.array(o.data.vertices[vi].co[:]) / 1e-5).astype(int))   # shared vertex POSITION
    for p in o.data.polygons:
        for vi in p.vertices: pos_faces.setdefault(key(vi), set()).add(p.index)
    nbr = {p.index: set().union(*(pos_faces[key(vi)] for vi in p.vertices)) for p in o.data.polygons}
    keep = set(range(n_)) - hidden
    for _ in range(MARGIN):
        ring = set()
        for fi in keep: ring |= nbr[fi]
        keep |= ring
    masked = sorted(i for i in hidden if i not in keep); plans[o.name] = masked
    area = sum(o.data.polygons[i].area for i in masked); tot = sum(p.area for p in o.data.polygons) or 1.0
    rep["objects"][o.name] = {"faces": n_, "seen_at_rest": len(seen), "hidden": len(hidden), "masked": masked, "masked_area_frac": round(area / tot, 4),
                              "hidden_centres": [list(omw @ o.data.polygons[i].center) for i in sorted(hidden)]}
    print(f"hidden {o.name}: {n_} faces · " + (f"under outfit {len(under)} · " if o is body else "") +
          f"seen at rest {len(seen)} · hidden {len(hidden)} · masked after margin {MARGIN}: {len(masked)} ({area / tot * 100:.1f} % of its area)")
rep["hidden_centres"] = rep["objects"]["body"]["hidden_centres"]     # clip_check --hidden reads the body's
json.dump(rep, open(jout, "w"))
if apply_to:
    for o in layers + [body]: o.data.color_attributes.remove(o.data.color_attributes["fid"])
    for o in targets:
        bm = bmesh.new(); bm.from_mesh(o.data); bm.faces.ensure_lookup_table()
        bmesh.ops.delete(bm, geom=[bm.faces[i] for i in plans[o.name]], context="FACES_ONLY")
        loose = [v for v in bm.verts if not v.link_faces]; bmesh.ops.delete(bm, geom=loose, context="VERTS")
        bm.to_mesh(o.data); bm.free()
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.export_scene.gltf(filepath=apply_to, export_format="GLB", export_skins=True, export_animations=False)
    print(f"masked → {apply_to}")

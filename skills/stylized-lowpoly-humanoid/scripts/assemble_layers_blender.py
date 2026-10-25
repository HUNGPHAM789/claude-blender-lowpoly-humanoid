"""Blender: assemble fitted layers into one character — each layer decimated to its own budget, one game-palette material each,
kept as SEPARATE objects (swappable hair / outfit assets). Run:
  blender -b -P assemble_layers_blender.py -- <out.glb> <layer.glb>:<role>:<tris> [<layer.glb>:<role>:<tris> …]
role ∈ skin | hair | leather_dark | leather_tan | rope_bone (colours = game palette in color_mesh.GAME, loaded through the theme).
Outfit layers are pushed out of the body where they sink in (≥ 4 mm clearance), so the skin never shows through.
"""
import bpy, bmesh, sys, os, math
from mathutils import Vector
import mathutils
a = sys.argv[sys.argv.index("--") + 1:]
out, layers = a[0], [x.split(":") for x in a[1:]]
sys.path.insert(0, os.path.expanduser("~/projects/lpm-faceless-humanoid/theme")); import theme_colors as TC
GAME = {"skin": TC.DA["dat_am"], "hair": (58, 40, 28), "leather_dark": (74, 53, 37), "leather_tan": (176, 138, 92), "rope_bone": (196, 164, 108)}
bpy.ops.wm.read_factory_settings(use_empty=True)
objs = []
for path, role, tris in layers:
    before = set(bpy.data.objects); bpy.ops.import_scene.gltf(filepath=path)
    new = [o for o in bpy.data.objects if o not in before and o.type == "MESH"]
    bpy.ops.object.select_all(action="DESELECT")
    for o in new: o.select_set(True)
    bpy.context.view_layer.objects.active = new[0]
    if len(new) > 1: bpy.ops.object.join()
    ob = bpy.context.view_layer.objects.active; ob.name = os.path.basename(path).split("_fit")[0].split(".")[0]
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    start = len(ob.data.polygons)
    m = ob.modifiers.new("dec", "DECIMATE"); m.ratio = min(1.0, int(tris) / max(1, sum(len(p.vertices) - 2 for p in ob.data.polygons))); m.use_collapse_triangulate = True
    bpy.ops.object.modifier_apply(modifier="dec")
    bpy.ops.object.shade_smooth()
    try: bpy.ops.object.shade_smooth_by_angle(angle=math.radians(35))
    except Exception: pass
    mat = bpy.data.materials.new(f"M_{role}"); mat.use_nodes = True
    bsdf = next(n for n in mat.node_tree.nodes if n.type == "BSDF_PRINCIPLED"); bsdf.inputs["Base Color"].default_value = TC.mau(GAME[role]); bsdf.inputs["Roughness"].default_value = 0.85
    ob.data.materials.clear(); ob.data.materials.append(mat); ob["role"] = role
    objs.append(ob); print(f"LAYER {ob.name}: {role} · {start} → {sum(len(p.vertices) - 2 for p in ob.data.polygons)} tris")
# clearance: outfit/hair vertices inside the body are pushed out along the body normal
body = next((o for o in objs if o["role"] == "skin"), None)
if body:
    dg = bpy.context.evaluated_depsgraph_get(); bvh = mathutils.bvhtree.BVHTree.FromObject(body, dg)
    for o in objs:
        if o is body: continue
        moved = 0
        for v in o.data.vertices:
            loc, nrm, idx, dist = bvh.find_nearest(v.co)
            if loc is None: continue
            inside = (v.co - loc).dot(nrm) < 0.004
            if inside and dist < 0.06: v.co = loc + nrm * 0.004; moved += 1
        print(f"CLEARANCE {o.name}: pushed {moved}/{len(o.data.vertices)} verts out of the body")
bpy.ops.export_scene.gltf(filepath=out, export_format="GLB")
print("ASSEMBLED", out)

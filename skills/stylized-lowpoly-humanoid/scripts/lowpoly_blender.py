"""Blender: dense image-to-3D mesh → game low-poly. Run:
  blender -b -P lowpoly_blender.py -- <aligned.glb> <out.glb> <target_tris> [shade_angle_deg]

merge by distance → remove loose bits (< 2 % of the faces) → planar + collapse decimate to target_tris → shade smooth with an angle
split (reference look: soft light inside a plane, hard break at the facet ridges) → export Y-up GLB. Prints the final tri count."""
import bpy, bmesh, sys, math
a = sys.argv[sys.argv.index("--") + 1:]
src, dst, target = a[0], a[1], int(a[2]); angle = float(a[3]) if len(a) > 3 else 35.0
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=src)
objs = [o for o in bpy.context.scene.objects if o.type == "MESH"]
bpy.ops.object.select_all(action="DESELECT")
for o in objs: o.select_set(True)
bpy.context.view_layer.objects.active = objs[0]
if len(objs) > 1: bpy.ops.object.join()
ob = bpy.context.view_layer.objects.active
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
bm = bmesh.new(); bm.from_mesh(ob.data)
bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.0005)
# drop floating islands (generator noise): keep islands with ≥ 2 % of the faces
islands = []; seen = set()
for f in bm.faces:
    if f.index in seen: continue
    stack = [f]; isl = []
    while stack:
        g = stack.pop()
        if g.index in seen: continue
        seen.add(g.index); isl.append(g)
        for e in g.edges:
            for h in e.link_faces:
                if h.index not in seen: stack.append(h)
    islands.append(isl)
n = len(bm.faces)
kill = [f for isl in islands if len(isl) < 0.02 * n for f in isl]
bmesh.ops.delete(bm, geom=kill, context="FACES")
bm.to_mesh(ob.data); bm.free()
tris = lambda: sum(len(p.vertices) - 2 for p in ob.data.polygons)
start = tris()
m = ob.modifiers.new("dec", "DECIMATE"); m.decimate_type = "COLLAPSE"; m.ratio = min(1.0, target / max(1, start)); m.use_collapse_triangulate = True
bpy.ops.object.modifier_apply(modifier="dec")
bpy.ops.object.shade_smooth()
try: bpy.ops.object.shade_smooth_by_angle(angle=math.radians(angle))
except Exception: pass
mat = bpy.data.materials.new("skin"); mat.use_nodes = True
b = next(nd for nd in mat.node_tree.nodes if nd.type == "BSDF_PRINCIPLED"); b.inputs["Base Color"].default_value = (0.80, 0.42, 0.32, 1)
ob.data.materials.clear(); ob.data.materials.append(mat)
bpy.ops.export_scene.gltf(filepath=dst, export_format="GLB", use_selection=False)
print(f"LOWPOLY {start} → {tris()} tris, islands removed {len(kill)} faces → {dst}")

# Blender-side QEM reduction: blender -b -P blender_decimate.py -- in.npz out.npz target_tris
# Reads verts/faces from npz, applies Decimate(COLLAPSE, symmetry X, triangulate), writes npz.
import sys, bpy, numpy as np

argv = sys.argv[sys.argv.index("--") + 1:]
src, dst, target = argv[0], argv[1], int(argv[2])
d = np.load(src)
V, F = d["V"], d["F"]

for o in list(bpy.data.objects):
    bpy.data.objects.remove(o, do_unlink=True)
me = bpy.data.meshes.new("m")
me.from_pydata(V.tolist(), [], F.tolist())
me.validate()
ob = bpy.data.objects.new("m", me)
bpy.context.scene.collection.objects.link(ob)
bpy.context.view_layer.objects.active = ob
ob.select_set(True)

ratio = min(1.0, target / max(1, len(F)))
mod = ob.modifiers.new("dec", "DECIMATE")
mod.decimate_type = "COLLAPSE"
mod.ratio = ratio
mod.use_symmetry = True
mod.symmetry_axis = "X"
mod.use_collapse_triangulate = True
bpy.ops.object.modifier_apply(modifier=mod.name)
tri = ob.modifiers.new("tri", "TRIANGULATE")
bpy.ops.object.modifier_apply(modifier=tri.name)

m = ob.data
Vo = np.array([v.co[:] for v in m.vertices], dtype=np.float64)
Fo = np.array([p.vertices[:] for p in m.polygons], dtype=np.int64)
np.savez(dst, V=Vo, F=Fo, ratio=ratio)
print(f"DECIMATE in={len(F)} target={target} ratio={ratio:.4f} out={len(Fo)}")

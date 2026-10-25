import bpy, mathutils, math, sys, os
from mathutils.bvhtree import BVHTree
V=mathutils.Vector; sc=bpy.context.scene; out=sys.argv[-1]; os.makedirs(out, exist_ok=True)
rig=next(o for o in bpy.data.objects if o.type=="ARMATURE"); logs=[o for o in bpy.data.objects if o.name.startswith("khuc_vac")]
nguoi=[o for o in bpy.data.objects if o.type=="MESH" and o.parent is rig]
def bvh(o, dg):
    oe=o.evaluated_get(dg); me=oe.to_mesh(); M=o.matrix_world; t=BVHTree.FromPolygons([M@v.co for v in me.vertices],[tuple(p.vertices) for p in me.polygons]); oe.to_mesh_clear(); return t
F0=None
import json
moc=json.load(open(os.path.join(os.path.dirname(out.rstrip('/')),'markers.json'))) if os.path.exists(os.path.join(os.path.dirname(out.rstrip('/')),'markers.json')) else None
dem={}
for f in range(260, 330, 2):
    sc.frame_set(f); dg=bpy.context.evaluated_depsgraph_get(); B={o.name:bvh(o,dg) for o in nguoi}; n=0
    for l in logs:
        bl=bvh(l,dg)
        for k,b in B.items():
            ov=bl.overlap(b)
            if ov: dem.setdefault(k,0); dem[k]+=len(ov); n+=len(ov)
print("BVH_CHONG", dem)
for e, r in ((4.0, (45, 0, 45)), (0.6, (60, 0, 160)), (0.8, (70, 0, -60))):
    l = bpy.data.objects.new("l", bpy.data.lights.new("l", "SUN")); sc.collection.objects.link(l); l.data.energy = e; l.rotation_euler = [math.radians(x) for x in r]
w = bpy.data.worlds.new("W"); sc.world = w; w.use_nodes = True; w.node_tree.nodes["Background"].inputs[0].default_value = (0.5, 0.52, 0.48, 1)
sc.view_settings.view_transform = "Standard"
# 2 góc cận cảnh quanh bàn tay phải
for f in (270, 300):
    sc.frame_set(f); h=rig.matrix_world @ ((rig.pose.bones["hand_R"].head+rig.pose.bones["hand_R"].tail)/2)
    c0=sum((l.matrix_world.translation for l in logs), V())/len(logs); ax=(logs[0].matrix_world.to_3x3()@V((0,0,1))).normalized()
    d1=(h-c0); d1=d1-ax*d1.dot(ax); d1.normalize(); d2=ax.cross(d1).normalized()
    if d2.z < 0: d2=-d2
    for ten,d in (("tu_phia_tay",d1+ax*0.25), ("doc_truc_go",(ax if ax.dot(h-c0)>=0 else -ax)+d1*0.05)):
        c=bpy.data.cameras.new("cz"); c.lens=85; co=bpy.data.objects.new("cz",c); sc.collection.objects.link(co); sc.camera=co
        co.location=(h+d.normalized()*1.4) if ten!="doc_truc_go" else (h+d.normalized()*1.6); co.rotation_euler=(h-co.location).to_track_quat("-Z","Y").to_euler()
        sc.render.engine="BLENDER_EEVEE"; sc.render.resolution_x=sc.render.resolution_y=640; sc.render.filepath=f"{out}/{ten}_{f}.png"; bpy.ops.render.render(write_still=True)

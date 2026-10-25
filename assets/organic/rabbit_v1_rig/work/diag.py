import bpy, sys
arm=bpy.data.objects["rabbit_rig"]; body=bpy.data.objects["rabbit_body"]; scn=bpy.context.scene
gi={g.index:g.name for g in body.vertex_groups}
me=body.data
def dom(v): 
    ws=sorted(((g.weight,gi[g.group]) for g in me.vertices[v].groups),reverse=True); return [(n,round(w,2)) for w,n in ws[:3]]
def coords():
    dg=bpy.context.evaluated_depsgraph_get(); ob=body.evaluated_get(dg); m=ob.to_mesh(); c=[v.co.copy() for v in m.vertices]; ob.to_mesh_clear(); return c
arm.animation_data.action=None
for b in arm.pose.bones: b.location=(0,0,0); b.rotation_euler=(0,0,0); b.scale=(1,1,1)
scn.frame_set(0); rest=coords()
arm.animation_data.action=bpy.data.actions["hop_inplace"]
scn.frame_set(9); co=coords()
r=[]
for e in me.edges:
    a,b=e.vertices; l=(rest[a]-rest[b]).length; r.append(((co[a]-co[b]).length/l,a,b))
r.sort(reverse=True)
for s,a,b in r[:12]: print(round(s,2), [round(x,3) for x in rest[a]], dom(a), dom(b))
# per-group volume of vertex set: count verts with weight on each bone

import bpy, sys
from mathutils import Vector
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath="~/projects/lpm-faceless-humanoid/assets/organic/rabbit_v1/rabbit.glb")
for o in bpy.data.objects:
    ws=[o.matrix_world@Vector(c) for c in o.bound_box] if o.type=='MESH' else []
    if ws:
        mn=[min(v[i] for v in ws) for i in range(3)]; mx=[max(v[i] for v in ws) for i in range(3)]
        print(o.name,o.type,o.parent.name if o.parent else None,len(o.data.vertices),len(o.data.polygons),[round(x,3) for x in mn],[round(x,3) for x in mx], [m.name for m in o.data.materials], tuple(round(x,3) for x in o.location), tuple(round(x,3) for x in o.rotation_euler))
    else: print(o.name,o.type)
# nose location
b=[o for o in bpy.data.objects if o.type=='MESH' and len(o.data.vertices)>300][0]
me=b.data
for mi,m in enumerate(me.materials):
    vs=[b.matrix_world@me.vertices[v].co for p in me.polygons if p.material_index==mi for v in p.vertices]
    c=sum(vs,Vector())/len(vs); print('mat',m.name,[round(x,3) for x in c])
print(bpy.app.version_string)

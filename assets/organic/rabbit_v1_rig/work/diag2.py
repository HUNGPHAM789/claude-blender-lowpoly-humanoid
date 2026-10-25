import bpy, math
arm=bpy.data.objects["rabbit_rig"]; body=bpy.data.objects["rabbit_body"]; arm.animation_data.action=None
pb=arm.pose.bones; me=body.data; me.calc_loop_triangles(); tris=[tuple(t.vertices) for t in me.loop_triangles]
def vol():
    bpy.context.view_layer.update(); dg=bpy.context.evaluated_depsgraph_get(); ob=body.evaluated_get(dg); m=ob.to_mesh()
    co=[v.co.copy() for v in m.vertices]; ob.to_mesh_clear()
    return sum(co[a].dot(co[b].cross(co[c])) for a,b,c in tris)/6
def reset():
    for b in pb: b.location=(0,0,0); b.rotation_euler=(0,0,0); b.scale=(1,1,1)
reset(); v0=vol()
tests={"pelvis37":{"pelvis":37},"thigh26":{"thigh.L":26,"thigh.R":26},"shin-5":{"shin.L":-5,"shin.R":-5},"foot60":{"foot.L":60,"foot.R":60},
"front-32":{"front_upper.L":-32,"front_upper.R":-32},"frontlow14paw25":{"front_lower.L":14,"front_lower.R":14,"front_paw.L":25,"front_paw.R":25},
"spine-4chest-6neck-6head-6":{"spine":-4,"chest":-6,"neck":-6,"head":-6},"ears":{"ear_1.L":-38,"ear_1.R":-38,"ear_2.L":-24,"ear_2.R":-24},"tail18":{"tail":18}}
for k,d in tests.items():
    reset()
    for n,a in d.items(): pb[n].rotation_euler.x=math.radians(a)
    print("VOL",k,round((vol()-v0)/v0*100,2))

import bpy, math
arm=bpy.data.objects["rabbit_rig"]; arm.animation_data.action=None
pb=arm.pose.bones
for b in pb: b.location=(0,0,0); b.rotation_euler=(0,0,0); b.scale=(1,1,1)
bpy.context.view_layer.update()
for n in ("foot.L","pelvis","front_upper.L","thigh.L","head"):
    t0=(arm.matrix_world@pb[n].tail).copy()
    pb[n].rotation_euler.x=math.radians(30); bpy.context.view_layer.update()
    t1=arm.matrix_world@pb[n].tail
    print("AX",n,"tail",[round(x,3) for x in t0],"->",[round(x,3) for x in t1], "localX", [round(x,2) for x in arm.data.bones[n].matrix_local.col[0][:3]])
    pb[n].rotation_euler.x=0

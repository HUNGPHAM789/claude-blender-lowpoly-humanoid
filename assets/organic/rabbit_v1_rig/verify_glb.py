"""Re-import rabbit_rigged.glb into an empty scene and report actions / bones / skin.
blender -b -P verify_glb.py"""
import bpy, os, json
HERE = os.path.dirname(os.path.abspath(__file__))
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=os.path.join(HERE, "rabbit_rigged.glb"))
arms = [o for o in bpy.data.objects if o.type == "ARMATURE"]
meshes = [o for o in bpy.data.objects if o.type == "MESH"]
out = {"armatures": len(arms), "bones": len(arms[0].data.bones) if arms else 0,
       "bone_names": [b.name for b in arms[0].data.bones] if arms else [],
       "actions": {a.name: [round(x, 2) for x in a.frame_range] for a in bpy.data.actions},
       "meshes": {o.name: {"verts": len(o.data.vertices), "skinned": any(m.type == "ARMATURE" for m in o.modifiers),
                           "parent": o.parent.name if o.parent else None, "parent_type": o.parent_type,
                           "parent_bone": o.parent_bone} for o in meshes}}
print("VERIFY", json.dumps(out))
json.dump(out, open(os.path.join(HERE, "glb_reimport.json"), "w"), indent=1)

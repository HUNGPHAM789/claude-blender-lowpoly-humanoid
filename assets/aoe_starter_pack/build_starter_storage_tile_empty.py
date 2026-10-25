"""EMPTY starter storage tile (Boss 25/10/2026: «starter storage tile bộ AoE starter - storage trống và gỗ stack ở đây từ settler phải visible»).
Takes starter_storage_tile.glb and keeps only the structure: earth slab 3.8 m, 4 plank floors, border beams, corner posts, cross dividers,
centre pin. Drops the studio pedestal (r = 8 m grass disc) and every stock prop (logs, quarry stones, berry basket, crate) — the game
fills the slots itself from settler-storage/scripts/storage.py. blender -b -P build_starter_storage_tile_empty.py"""
import bpy, os
HERE = os.path.dirname(os.path.abspath(__file__))
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=os.path.join(HERE, "starter_storage_tile.glb"))
STRUCT = {"M_PackedEarth", "M_FloorPlanks", "M_TimberWood", "M_WoodCutFace"}
keep, drop = [], []
for o in list(bpy.data.objects):
    if o.type != "MESH": continue
    d = o.dimensions; mats = {m.name.split(".")[0] for m in o.data.materials if m}
    big = max(d.x, d.y) > 4.0                                   # studio pedestal
    struct = (mats & STRUCT) and (max(d.x, d.y) >= 1.7 or (d.z >= 0.3 and max(d.x, d.y) <= 0.3) or (abs(o.location.x) < 0.05 and abs(o.location.y) < 0.05))
    log = "M_TimberWood" in mats and 1.3 < max(d.x, d.y, d.z) < 1.6 and min(d.x, d.y, d.z) > 0.25   # stocked logs (r 0.18, len 1.45)
    crate = 0.4 < max(d.x, d.y) < 1.0 and d.z < 0.3                # the small crate beside the berry basket
    (keep if struct and not big and not log and not crate else drop).append(o)
for o in drop: bpy.data.objects.remove(o, do_unlink=True)
print("KEEP", len(keep), sorted({round(max(o.dimensions), 2) for o in keep}), "DROP", len(drop))
bpy.ops.export_scene.gltf(filepath=os.path.join(HERE, "starter_storage_tile_empty.glb"), export_format="GLB", export_apply=True)

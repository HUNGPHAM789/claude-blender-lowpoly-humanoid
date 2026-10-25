"""ĐỌC NGƯỢC một con thú 4 chân có rig + animation (Quaternius CC0) để rút luật làm con khác (Boss 23/10/2026: «học cách làm rig của con nai
quaternius, cách animation của nó, ghi skill, cách làm low poly của nó… dáng mũi, cách bước đi, thân mình, cổ khi ăn… ghi spec chi tiết»).
  blender -b -P analysis.py -- <model.glb> <out.json>
Mọi độ dài chia cho H = chiều cao VAI (móng trước → đỉnh vai lúc đứng nghỉ) để so được giữa các loài/cỡ."""
import bpy, bmesh, json, math, sys, mathutils
V = mathutils.Vector
a_ = sys.argv[sys.argv.index("--") + 1:]; SRC, OUT = a_[0], a_[1]
bpy.ops.wm.read_factory_settings(use_empty=True); sc = bpy.context.scene; bpy.ops.import_scene.gltf(filepath=SRC)
for o in [o for o in bpy.data.objects if o.type == "MESH" and o.name.startswith("Icosphere")]: bpy.data.objects.remove(o)
arm = next(o for o in bpy.data.objects if o.type == "ARMATURE"); ms = [o for o in bpy.data.objects if o.type == "MESH"]
W = arm.matrix_world; PB = arm.pose.bones; B = arm.data.bones
KQ = {"nguon": SRC}


def dat(ten):
    act = bpy.data.actions[ten]; arm.animation_data.action = act
    if act.slots: arm.animation_data.action_slot = act.slots[0]
    for t in list(arm.animation_data.nla_tracks): t.mute = True


def wp(b, dau="head"): return W @ (PB[b].head if dau == "head" else PB[b].tail)


# ---------------- tư thế nghỉ = khung 0 của Idle
dat("Idle"); sc.frame_set(0); bpy.context.view_layer.update()
dg = bpy.context.evaluated_depsgraph_get()
def diem_luoi():
    pts = []
    for o in ms:
        oe = o.evaluated_get(dg); me = oe.to_mesh(); pts += [o.matrix_world @ v.co for v in me.vertices]; oe.to_mesh_clear()
    return pts
P0 = diem_luoi(); zsan = min(p.z for p in P0)
dau = wp("Head", "tail"); duoi = wp("Tail3", "tail") if "Tail3" in PB else wp("Body")
truc = (dau - duoi); truc.z = 0; truc.normalize()   # hướng TRƯỚC của con vật
ben = V((0, 0, 1)).cross(truc).normalized()
# H = ĐỈNH U VAI (withers) đo trên LƯỚI: đỉnh cao nhất của thân quanh dọc vai trước (khớp xương vai nằm sâu trong ngực ⇒ thấp hơn u vai)
than0 = max(ms, key=lambda o: len(o.data.polygons)); gi0 = {g.index: g.name for g in than0.vertex_groups}
tro0 = [gi0.get(max(v.groups, key=lambda e: e.weight).group) if v.groups else "" for v in than0.data.vertices]
oe0 = than0.evaluated_get(dg); me0 = oe0.to_mesh(); PV0 = [than0.matrix_world @ v.co for v in me0.vertices]; oe0.to_mesh_clear()
x_vai = ((wp("FrontShoulder.L") + wp("FrontShoulder.R")) / 2).dot(truc); dai_t = abs(x_vai - ((wp("BackShoulder.L") + wp("BackShoulder.R")) / 2).dot(truc))
vai = max(p.z for p, n in zip(PV0, tro0) if abs(p.dot(truc) - x_vai) < 0.12 * dai_t and not n.startswith(("Neck", "Head", "Ear"))); H = vai - zsan
MUI_I = max((i for i, n in enumerate(tro0) if n.startswith("Head")), key=lambda i: PV0[i].dot(truc))   # đỉnh MÕM = đỉnh đầu xa nhất phía trước
def ch(p): d = p - V((0, 0, zsan)); return [round(d.dot(ben) / H, 3), round(d.dot(truc) / H, 3), round(d.z / H, 3)]   # (ngang, dọc trước, cao) /H
KQ["H_vai_don_vi_goc"] = round(H, 4)
KQ["truc_truoc"] = [round(x, 3) for x in truc]

# ---------------- RIG: cây xương + vị trí khớp chuẩn hoá
cay = {}
for b in B:
    cay[b.name] = {"cha": b.parent.name if b.parent else None, "deform": b.use_deform, "dau": ch(W @ b.head_local), "duoi": ch(W @ b.tail_local), "dai_H": round(b.length * W.to_scale()[0] / H, 3)}
KQ["xuong"] = cay; KQ["so_xuong"] = len(B); KQ["xuong_deform"] = sum(1 for b in B if b.use_deform)
KQ["rang_buoc"] = {pb.name: [c.type for c in pb.constraints] for pb in PB if pb.constraints}

# ---------------- MESH: tỉ lệ + mật độ mặt theo vùng (vùng = xương trọng số lớn nhất)
than = max(ms, key=lambda o: len(o.data.polygons))
gi = {g.index: g.name for g in than.vertex_groups}
tro = [gi.get(max(v.groups, key=lambda e: e.weight).group) if v.groups else None for v in than.data.vertices]
vung = lambda n: ("dau" if n and n.startswith(("Head", "Ear")) else "co" if n and n.startswith("Neck") else "chan_truoc" if n and n.startswith("Front") else
                  "chan_sau" if n and n.startswith("Back") and "Leg" in n or (n and n.startswith("BackShoulder")) else "duoi" if n and n.startswith("Tail") else "than")
dem = {}; canh = {}
bm = bmesh.new(); bm.from_mesh(than.data); bm.transform(than.matrix_world); bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-4 * H)
for f in bm.faces:
    vv = [tro[v.index] if v.index < len(tro) else None for v in f.verts]; r = vung(max(set(vv), key=vv.count))
    dem[r] = dem.get(r, 0) + len(f.verts) - 2; canh.setdefault(r, []).append(math.sqrt(f.calc_area()) / H)
bm.free()
KQ["tam_giac_theo_vung"] = dem; KQ["tam_giac_than"] = sum(dem.values())
KQ["mat_cat_trung_binh_H"] = {k: round(sum(v) / len(v), 4) for k, v in canh.items()}   # căn diện tích mặt / H ⇒ độ «to» của facet
KQ["tam_giac_tat_ca"] = sum(sum(len(p.vertices) - 2 for p in o.data.polygons) for o in ms)
KQ["vat_lieu"] = {}
for o in ms:
    for i, m in enumerate(o.data.materials):
        b_ = next((n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED"), None); n_ = sum(1 for p in o.data.polygons if p.material_index == i)
        KQ["vat_lieu"][f"{o.name}/{m.name}"] = {"mau_tuyen_tinh": [round(x, 3) for x in b_.inputs["Base Color"].default_value[:3]] if b_ else None, "mat": n_}
KQ["mem_hay_phang"] = "smooth" if any(p.use_smooth for p in than.data.polygons) else "flat"
# tỉ lệ dáng (từ khớp)
KQ["ti_le"] = {
    "dai_than_H": round((wp("Torso3" if "Torso3" in PB else "Torso").z * 0 + (wp("Neck1") - wp("Body")).dot(truc)) / H, 3),
    "cao_dau_H": round((dau.z - zsan) / H, 3), "mom_truoc_vai_H": round((dau - wp("FrontShoulder.L")).dot(truc) / H, 3),
    "dai_co_H": round((wp("Head") - wp("Neck1")).length / H, 3), "dai_dau_mom_H": round((PV0[MUI_I] - wp("Head")).length / H, 3),
    "dai_vai_vai_H": round(dai_t / H, 3), "cao_mom_nghi_H": round((PV0[MUI_I].z - zsan) / H, 3),
    "chan_truoc_doan_H": [round((wp(a) - wp(b)).length / H, 3) for a, b in (("FrontShoulder.L", "FrontUpperLeg.L"), ("FrontUpperLeg.L", "FrontLowerLeg.L"))] + [round((wp("FrontLowerLeg.L", "tail") - wp("FrontLowerLeg.L")).length / H, 3)],
    "chan_sau_doan_H": [round((wp(a) - wp(b)).length / H, 3) for a, b in (("BackShoulder.L", "BackLeg.L"), ("BackLeg.L", "BackUpperLeg.L"), ("BackUpperLeg.L", "BackLowerLeg.L"))] + [round((wp("BackLowerLeg.L", "tail") - wp("BackLowerLeg.L")).length / H, 3)],
}
# dáng MŨI: các đỉnh vùng đầu phía trước nhất (mõm) — bề ngang/cao/thon so với gốc đầu
dau_v = [than.matrix_world @ than.data.vertices[i].co for i, n in enumerate(tro) if n and n.startswith("Head")]
if dau_v:
    xa = max(p.dot(truc) for p in dau_v); gan = min(p.dot(truc) for p in dau_v); L = xa - gan
    lat = lambda t: [p for p in dau_v if abs(p.dot(truc) - (gan + t * L)) < 0.06 * L]
    def kich(t):
        s = lat(t)
        if not s: return None
        return [round((max(p.dot(ben) for p in s) - min(p.dot(ben) for p in s)) / H, 3), round((max(p.z for p in s) - min(p.z for p in s)) / H, 3)]
    KQ["mui_mat_cat_ngang_x_cao_H"] = {f"{int(t * 100)}%": kich(t) for t in (0.2, 0.4, 0.6, 0.8, 0.95)}   # từ gáy (0) → đầu mũi (100)

# ---------------- ANIMATION
MONG = {"FL": "FrontLowerLeg.L", "FR": "FrontLowerLeg.R", "HL": "BackLowerLeg.L", "HR": "BackLowerLeg.R"}
def analysis(ten):
    act = bpy.data.actions[ten]; dat(ten); T = int(act.frame_range[1])
    kq = {"khung": T, "xuong_co_key": sorted({fc.data_path.split('"')[1] for fc in getattr(act, "fcurves", []) if '"' in fc.data_path})}
    try:
        from bpy_extras import anim_utils
        cb = anim_utils.action_get_channelbag_for_slot(act, act.slots[0]); fcs = list(cb.fcurves)
    except Exception: fcs = list(getattr(act, "fcurves", []))
    kq["xuong_co_key"] = sorted({fc.data_path.split('"')[1] for fc in fcs if '"' in fc.data_path})
    kq["so_key_trung_binh"] = round(sum(len(fc.keyframe_points) for fc in fcs) / max(1, len(fcs)), 1)
    S = {k: [] for k in MONG}; goc = []; mom = []; co = []; than_ = []
    for f in range(0, T + 1):
        sc.frame_set(f); bpy.context.view_layer.update()
        for k, b in MONG.items(): S[k].append(wp(b, "tail").copy())
        goc.append(wp("Body").copy())
        oe = than0.evaluated_get(bpy.context.evaluated_depsgraph_get()); me = oe.to_mesh(); mom.append((than0.matrix_world @ me.vertices[MUI_I].co).copy()); oe.to_mesh_clear()
        n1, n3 = wp("Neck1"), wp("Neck3", "tail") if "Neck3" in PB else wp("Head")
        co.append(math.degrees(math.atan2((n3 - n1).z, (n3 - n1).dot(truc))))
        t1 = (wp("BackShoulder.L") + wp("BackShoulder.R")) / 2; t2 = (wp("FrontShoulder.L") + wp("FrontShoulder.R")) / 2
        than_.append(math.degrees(math.atan2((t2 - t1).z, (t2 - t1).dot(truc))))   # + = ngực cao hơn hông
    kq["goc_di_chuyen_H"] = round((goc[-1] - goc[0]).dot(truc) / H, 3)
    kq["than_nhun_cao_H"] = round((max(p.z for p in goc) - min(p.z for p in goc)) / H, 3)
    kq["than_nghieng_do"] = [round(min(than_), 1), round(max(than_), 1)]
    kq["co_so_ngang_do"] = [round(min(co), 1), round(max(co), 1)]
    kq["mom_cao_H"] = [round((min(p.z for p in mom) - zsan) / H, 3), round((max(p.z for p in mom) - zsan) / H, 3)]
    chan = {}
    for k, ds in S.items():
        zm = min(p.z for p in ds); cham = [p.z < zm + 0.03 * H for p in ds]
        dau_cham = [f for f in range(len(ds)) if cham[f] and not cham[f - 1]]
        truot = max([((ds[f] - ds[f - 1]) - truc * 0).to_2d().length / H for f in range(1, len(ds)) if cham[f] and cham[f - 1]] or [0])
        vt = [-(ds[f] - ds[f - 1]).dot(truc) * 24 / H for f in range(1, len(ds)) if cham[f] and cham[f - 1]]   # móng lùi lúc chạm (clip tại chỗ ⇒ = tốc độ)
        chan[k] = {"pha_cham": round(dau_cham[0] / T, 3) if dau_cham else None, "ti_le_cham": round(sum(cham) / len(cham), 3), "toc_do_H_moi_giay": round(sum(vt) / len(vt), 2) if vt else None,
                   "nhac_cao_H": round((max(p.z for p in ds) - zm) / H, 3), "sai_H": round((max(p.dot(truc) for p in ds) - min(p.dot(truc) for p in ds)) / H, 3),
                   "truot_max_H_khung": round(truot, 4)}
    kq["chan"] = chan
    return kq
KQ["animation"] = {}
for a in sorted({a.name for a in bpy.data.actions if "|" not in a.name}):
    try: KQ["animation"][a] = analysis(a)
    except Exception as ex: KQ["animation"][a] = {"loi": str(ex)}
json.dump(KQ, open(OUT, "w"), indent=1, ensure_ascii=False); print("XONG", OUT)

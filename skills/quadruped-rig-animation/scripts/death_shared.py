"""CHẾT DÙNG CHUNG cho mọi thú 4 chân (Boss 23/10/2026: «chưa có dead animation cho thỏ - và tôi nghỉ nên có universial dead animal
animation để xài chung hay như thế nào? at least 4 legs?»).

Một hàm, mọi rig: chỉ cần BẢN ĐỒ XƯƠNG (cột sống, cổ, đầu, 4 chân trên→dưới, đuôi, tai). Không có góc tay nào gắn với một con cụ thể:
  · trục ngang/trước/lên đọc từ rig (đầu − hông), chiều gập gối DÒ bằng thử (+/−: khớp giữa phải đi về phía trước ở chân trước,
    về phía sau ở chân sau), góc cúi cổ DÒ bằng chia đôi tới khi đầu chạm đất.
  · cả con đổ nghiêng = xoay OBJECT quanh trục thân qua mép đất phía ngã; mỗi khung ép điểm thấp nhất của MESH = mặt đất
    (không xuyên đất, chân gập thì thân tự hạ).
Pha (khung ở 30 fps, nhân theo `nhip`): trúng 0–5 · khuỵu 5–16 · đổ 12–30 (tăng tốc kiểu rơi, nảy 30–37) · cổ gục 16–34 ·
chân duỗi/tai đuôi rũ 28–46 · giật chân sau 56–62 · nằm yên.
Cổng (trả về dict, exit 1 ở CLI): xuyên đất ≤ 5 mm mọi khung · góc nghiêng cuối ≥ 70° · đầu chạm đất cuối (≤ 3% thân dài) ·
đứng yên 8 khung cuối (dịch < 2 mm/frames).

  blender -b -P death_shared.py -- demo <out_dir>      # nai B + thỏ, render 2 panel cạnh nhau
API: chet(arm, meshes, ban_do, f0=1, ben=+1, nhip=1.0, mat_dat=0.0) → dict cổng"""
import bpy, math, os, sys
import numpy as np
from mathutils import Vector as V, Matrix as M, Quaternion as Q


def _ease_in(u): return u * u


def _ease_io(u): return u * u * (3 - 2 * u)


def _pha(f, a, b):
    return 0.0 if f <= a else 1.0 if f >= b else (f - a) / (b - a)


def _min_z(meshes):
    dg = bpy.context.evaluated_depsgraph_get(); z = 1e9
    for o in meshes:
        e = o.evaluated_get(dg); me = e.to_mesh(); mw = e.matrix_world
        if len(me.vertices):
            co = np.empty(len(me.vertices) * 3); me.vertices.foreach_get("co", co); co = co.reshape(-1, 3)
            z = min(z, float((co @ np.array(mw.to_3x3()).T + np.array(mw.translation))[:, 2].min()))
        e.to_mesh_clear()
    return z


def _dau_min_z(meshes, ten_dau):
    """đỉnh THẤP NHẤT của vùng đầu (vertex group của xương đầu, trọng số > 0,5) — KHÔNG dùng chóp xương: nằm nghiêng thì mũi cách đất
    đúng bằng bán kính đầu (bản 1 23/10: gate báo đầu cách đất 35–53% thân trong khi hình thấy đầu nằm trên cỏ)"""
    dg = bpy.context.evaluated_depsgraph_get(); z = 1e9
    for o in meshes:
        vg = o.vertex_groups.get(ten_dau)
        if not vg: continue
        ids = [v.index for v in o.data.vertices if any(g.group == vg.index and g.weight > 0.5 for g in v.groups)]
        if not ids: continue
        e = o.evaluated_get(dg); me = e.to_mesh(); mw = e.matrix_world
        z = min(z, min((mw @ me.vertices[i].co).z for i in ids)); e.to_mesh_clear()
    return z


def chet(arm, meshes, bd, f0=1, ben=+1, nhip=1.0, mat_dat=0.0):
    sc = bpy.context.scene; pb = arm.pose.bones; MW0 = arm.matrix_world.copy()
    def F(x): return f0 + round(x * nhip)
    # khung tham chiếu trong không gian ARMATURE: trước = hông → đầu, lên = trục Z thế giới đổi về armature
    hong = pb[bd["cot_song"][0]].head; dau = pb[bd["dau"]].head
    len_ = (MW0.inverted().to_3x3() @ V((0, 0, 1))).normalized(); truoc = (dau - hong); truoc -= truoc.dot(len_) * len_; truoc.normalize()
    ngang = truoc.cross(len_).normalized()
    DAI = (MW0 @ dau - MW0 @ hong).length
    goc_bone = {b.name: b.matrix_basis.copy() for b in pb}

    def xoay(ten, goc, truc):
        """xoay xương quanh trục (không gian armature) qua đầu xương, giữ con cháu theo"""
        b = pb[ten]; h = b.head.copy()
        R = M.Translation(h) @ Q(truc, goc).to_matrix().to_4x4() @ M.Translation(-h)
        b.matrix = R @ b.matrix; bpy.context.view_layer.update()

    # dò chiều gập gối cho từng chân: khớp giữa phải đi về trước (chân trước) / về sau (chân sau)
    chieu = {}
    for k, ch in bd["chan"].items():
        if len(ch) < 2: chieu[k] = 1; continue
        giua0 = pb[ch[1]].head.copy(); xoay(ch[0], 0.3, ngang); d = (pb[ch[1]].head - giua0).dot(truoc)
        b0 = pb[ch[0]]; b0.matrix_basis = goc_bone[ch[0]]; bpy.context.view_layer.update()
        chieu[k] = (1 if d > 0 else -1) * (1 if k[0] == "T" else -1)

    # trục đổ (thế giới): trục thân; tâm xoay = dưới thân, lệch về phía ngã nửa bề ngang
    truoc_w = (MW0.to_3x3() @ truoc).normalized(); ngang_w = (MW0.to_3x3() @ ngang).normalized()
    co = [MW0 @ v for o in meshes if o.type == "MESH" for v in [vv.co for vv in o.data.vertices]] if False else None
    rong = bd.get("rong", 0.18 * DAI)
    TAM = MW0.translation + ngang_w * (ben * rong * 0.5); TAM.z = mat_dat
    dau_ra = {"xuyen_mm": 0.0, "goc_nghieng_cuoi": 0.0}
    vt_truoc = None; dich = []
    f_end = F(90)
    for f in range(f0, f_end + 1):
        x = (f - f0) / nhip
        for b in pb: b.matrix_basis = goc_bone[b.name]
        bpy.context.view_layer.update()
        # 1. trúng: cột sống co, đầu giật lên/ra sau rồi trả (0–5)
        tr = math.sin(math.pi * _pha(x, 0, 6))
        for s in bd["cot_song"]: xoay(s, -0.10 * tr / len(bd["cot_song"]), ngang)
        # 2. khuỵu: gập gối (zig-zag), chân trước sụm trước
        for k, ch in bd["chan"].items():
            g = (0.55 if k[0] == "T" else 0.40) * _ease_io(_pha(x, 5 if k[0] == "T" else 8, 16)) * (1 - 0.75 * _ease_io(_pha(x, 28, 46)))
            if len(ch) >= 2:
                xoay(ch[0], chieu[k] * g, ngang); xoay(ch[1], -chieu[k] * 2 * g, ngang)
                if len(ch) >= 3: xoay(ch[2], chieu[k] * g, ngang)
        # giật chân sau (56–62)
        for k in ("ST", "SP"):
            if k in bd["chan"]: xoay(bd["chan"][k][0], chieu[k] * 0.35 * math.sin(math.pi * _pha(x, 56, 62)), ngang)
        # tai/đuôi rũ
        ru = _ease_io(_pha(x, 20, 40))
        for tai in bd.get("tai", []):
            # tai cụp NGẢ RA SAU dọc lưng (chiều −): rũ về trước thì chóp tai chống đất, đỡ cả đầu (thỏ 23/10: đầu treo 14,7% thân)
            # (trục 'ngang' = trước × lên = −X ở rig nhìn −Y ⇒ dấu + ở đây là NGẢ RA SAU)
            for i, t in enumerate(tai): xoay(t, (1.3 if i == 0 else 0.3) * ru, ngang)
        for t in bd.get("duoi", []): xoay(t, -0.25 * ru, ngang)
        # 3. đổ: góc nghiêng tăng tốc, nảy
        u = _pha(x, 12, 30); th = math.radians(86) * _ease_in(u)
        if x > 30: th = math.radians(86) - math.radians(5) * math.sin(math.pi * _pha(x, 30, 37))
        arm.matrix_world = M.Translation(TAM) @ Q(truoc_w, -ben * th).to_matrix().to_4x4() @ M.Translation(-TAM) @ MW0
        bpy.context.view_layer.update()
        # 4. cổ gục tới đất: chia đôi góc quanh trục ⟂ (cổ, xuống)
        if bd.get("co"):
            muc = _ease_io(_pha(x, 16, 34)); Mi = arm.matrix_world.inverted()
            xuong = (Mi.to_3x3() @ V((0, 0, -1))).normalized(); co_dir = (pb[bd["dau"]].head - pb[bd["co"][0]].head).normalized()
            truc = co_dir.cross(xuong)
            if truc.length > 1e-4 and muc > 0:
                truc.normalize(); cu = {c: pb[c].matrix_basis.copy() for c in bd["cot_song"][-3:] + bd["co"] + [bd["dau"]]}
                # đốt ngực cuối + cổ + đầu cùng gục: thỏ mập (ngang = ½ cao) nằm nghiêng thì vai cao, cổ ngắn với không tới.
                # Chưa chạm ⇒ dự phòng thêm 1 đốt sống nữa (thỏ từ dáng đánh hơi: 1 đốt còn 3,7%).
                chuoi = []
                def thu(g):
                    for c in cu: pb[c].matrix_basis = cu[c]
                    bpy.context.view_layer.update()
                    for c in chuoi: xoay(c, g / len(chuoi), truc)
                    return _dau_min_z(meshes, bd["dau"]) - _min_z(meshes)
                def tim():
                    # QUÉT (không chia đôi): độ cao đầu theo góc KHÔNG đơn điệu — bẻ quá thì đầu ngóc ngược (thỏ 0,5 rad 14,6% → 1,0 rad 24%)
                    ket = [(abs(g), g, thu(g)) for g in (i * 0.1 for i in range(-22, 23))]
                    cham = [k for k in ket if k[2] <= 0.02 * DAI]
                    if cham: return min(cham)[1], min(cham)[2]
                    g0 = min(ket, key=lambda k: k[2])[1]   # quét mịn quanh góc tốt nhất
                    ket2 = [(abs(g), g, thu(g)) for g in (g0 + i * 0.01 for i in range(-10, 11))]
                    cham2 = [k for k in ket2 if k[2] <= 0.02 * DAI]
                    k_ = min(cham2) if cham2 else min(ket2, key=lambda k: k[2]); return k_[1], k_[2]
                for n_cs in (1, 2, 3):
                    chuoi[:] = bd["cot_song"][-n_cs:] + bd["co"] + [bd["dau"]]
                    g_dat, cao_ = tim()
                    if cao_ <= 0.02 * DAI: break
                if os.environ.get("DEBUG_CO") and f == f0 + int(60 * nhip):
                    print("DBG_CO", {g: round(thu(g) / DAI * 100, 1) for g in (-2.0, -1.0, -0.5, 0.0, 0.5, 1.0, 2.0)}, "g_dat", round(g_dat, 2), "truc", tuple(round(x, 2) for x in truc))
                thu(g_dat * muc)
        # 5. ép mặt đất: điểm thấp nhất mesh = mặt đất
        z = _min_z(meshes); arm.matrix_world = M.Translation((0, 0, mat_dat - z)) @ arm.matrix_world; bpy.context.view_layer.update()
        dau_ra["xuyen_mm"] = max(dau_ra["xuyen_mm"], max(0.0, (mat_dat - _min_z(meshes)) * 1000))
        arm.keyframe_insert("location", frame=f); arm.rotation_mode = "QUATERNION"; arm.keyframe_insert("rotation_quaternion", frame=f)
        for b in pb:
            b.keyframe_insert("rotation_quaternion" if b.rotation_mode == "QUATERNION" else "rotation_euler", frame=f); b.keyframe_insert("location", frame=f)
        vt = (arm.matrix_world @ pb[bd["cot_song"][-1]].head).copy()
        if vt_truoc is not None and f > f_end - 8: dich.append((vt - vt_truoc).length * 1000)
        vt_truoc = vt
    sc.frame_set(f_end)
    q = arm.matrix_world.to_quaternion(); len_now = q @ (MW0.to_quaternion().inverted() @ V((0, 0, 1)))
    dau_ra["goc_nghieng_cuoi"] = math.degrees(V((0, 0, 1)).angle((arm.matrix_world.to_3x3() @ len_).normalized()))
    dau_ra["dau_cach_dat_pct"] = (_dau_min_z(meshes, bd["dau"]) - mat_dat) / DAI * 100
    dau_ra["dich_cuoi_mm"] = max(dich) if dich else 0
    dau_ra["dat"] = dau_ra["xuyen_mm"] <= 5 and dau_ra["goc_nghieng_cuoi"] >= 70 and dau_ra["dau_cach_dat_pct"] <= 3 and dau_ra["dich_cuoi_mm"] < 2
    return dau_ra


BD_NAI_B = {"cot_song": ["Back", "Torso", "Torso2", "Torso3"], "co": ["Neck1", "Neck2", "Neck3"], "dau": "Head",
            "chan": {"TT": ["FrontUpperLeg.L", "FrontLowerLeg.L"], "TP": ["FrontUpperLeg.R", "FrontLowerLeg.R"],
                     "ST": ["BackLeg.L", "BackUpperLeg.L", "BackLowerLeg.L"], "SP": ["BackLeg.R", "BackUpperLeg.R", "BackLowerLeg.R"]},
            "duoi": ["Tail1", "Tail2"]}
BD_THO = {"cot_song": ["pelvis", "spine", "chest"], "co": ["neck"], "dau": "head",
          "chan": {"TT": ["front_upper.L", "front_lower.L", "front_paw.L"], "TP": ["front_upper.R", "front_lower.R", "front_paw.R"],
                   "ST": ["thigh.L", "shin.L", "foot.L"], "SP": ["thigh.R", "shin.R", "foot.R"]},
          "duoi": ["tail"], "tai": [["ear_1.L", "ear_2.L"], ["ear_1.R", "ear_2.R"]]}


def _nap(glb):
    tr = set(bpy.data.objects); bpy.ops.import_scene.gltf(filepath=glb); moi = [o for o in bpy.data.objects if o not in tr]
    for o in moi:
        if o.name.startswith("Icosphere"): bpy.data.objects.remove(o)
    moi = [o for o in bpy.data.objects if o not in tr]
    arm = next(o for o in moi if o.type == "ARMATURE"); arm.animation_data_clear()
    if "rabbit" in glb:
        sys.path.insert(0, os.path.expanduser("~/projects/GameDev")); from theme_colors import mau
        for o in moi:
            for sl in getattr(o, "material_slots", []):
                n = next((n for n in (sl.material.node_tree.nodes if sl.material and sl.material.use_nodes else []) if n.type == "BSDF_PRINCIPLED"), None)
                if n and not sl.material.get("da_doi_theme"):
                    c = n.inputs["Base Color"].default_value; n.inputs["Base Color"].default_value = mau(tuple(round(255 * x) for x in c[:3])); sl.material["da_doi_theme"] = 1
    for o in moi:
        if o.animation_data: o.animation_data_clear()
    return arm, [o for o in moi if o.type == "MESH"]


if __name__ == "__main__" and "demo" in sys.argv:
    import json, subprocess
    OUT = sys.argv[sys.argv.index("demo") + 1]; os.makedirs(OUT, exist_ok=True)
    G = os.path.expanduser("~/projects/lpm-faceless-humanoid/assets/organic")
    KQ = {}
    for ten, glb, bd in (("nai_B", f"{G}/downloads/quaternius_deer/ab/stag_origami.glb", BD_NAI_B), ("tho", f"{G}/rabbit_v1_rig/rabbit_rigged.glb", BD_THO)):
        bpy.ops.wm.read_factory_settings(use_empty=True); sc = bpy.context.scene
        arm, ms = _nap(glb)
        sc.frame_start, sc.frame_end = 1, 100; sc.render.fps = 30
        KQ[ten] = kq = chet(arm, ms, bd, f0=1, ben=+1); print(ten, kq)
        # dựng cảnh
        bpy.ops.mesh.primitive_plane_add(size=40); p = bpy.context.object; m = bpy.data.materials.new("dat"); m.use_nodes = True
        m.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.20, 0.24, 0.12, 1); p.data.materials.append(m)
        sc.frame_set(1); bb = [o.matrix_world @ V(c) for o in ms for c in o.bound_box]; cx = sum((v for v in bb), V()) / len(bb); H = max(v.z for v in bb)
        c = bpy.data.cameras.new("c"); c.lens = 50; co = bpy.data.objects.new("c", c); sc.collection.objects.link(co); sc.camera = co
        d = V((0.85, -0.75, 0.42)).normalized(); co.location = V((cx.x, cx.y, H * 0.35)) + d * H * 3.6; co.rotation_euler = (-d).to_track_quat("-Z", "Y").to_euler()
        for e_, rr in ((3.0, (50, 0, 30)), (1.0, (70, 0, 200))):
            l = bpy.data.objects.new("l", bpy.data.lights.new("l", "SUN")); sc.collection.objects.link(l); l.data.energy = e_; l.rotation_euler = [math.radians(x) for x in rr]
        wd = bpy.data.worlds.new("W"); sc.world = wd; wd.use_nodes = True; wd.node_tree.nodes["Background"].inputs[0].default_value = (0.55, 0.6, 0.55, 1)
        sc.render.engine = "BLENDER_EEVEE"; sc.view_settings.view_transform = "Standard"; sc.render.resolution_x, sc.render.resolution_y = 960, 720
        sc.render.image_settings.file_format = "PNG"; sc.render.filepath = f"{OUT}/{ten}_frames/"; bpy.ops.render.render(animation=True)
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-framerate", "30", "-i", f"{OUT}/{ten}_frames/%04d.png", "-c:v", "libx264", "-crf", "20", "-pix_fmt", "yuv420p", f"{OUT}/{ten}.mp4"])
        bpy.ops.wm.save_as_mainfile(filepath=f"{OUT}/{ten}.blend")
    json.dump(KQ, open(f"{OUT}/cong.json", "w"), indent=1)
    print("CONG", json.dumps(KQ))
    sys.exit(0 if all(k["dat"] for k in KQ.values()) else 1)

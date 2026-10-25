#!/usr/bin/env python3
"""LPM Studio — vòng dựng asset kiểu Kiln, bản của mình (Boss 22/10/2026: «Làm theo đề xuất của bạn chỉ lấy vài phần bên kiln»).

Lấy từ Kiln: (1) MỘT lệnh = dựng + cửa đo + ảnh nhiều góc + biên nhận JSON; (2) mỗi lần dựng là một PHIÊN BẢN bất biến r_xxxxxxxx
có cha; (3) sửa bằng THAY ĐOẠN source (neo chính xác) ⇒ phiên bản con + so trước/sau; (4) đo CẶP bộ phận (chạm / hở);
(5) danh mục hàm dựng tra được. KHÔNG lấy: màu của Kiln, QA của Kiln (nó cho qua cán sai cỡ, khối hở, lưỡi đặt sai).

Chương trình asset = file .py có META = dict(ten=..., cam=True|False, ngan_sach=600) và build() -> {tên_bộ_phận: trimesh}.
Hàm dựng: `from lpms_helpers import *` (khoi, ong, quet, dun, cau, MAU).

  lpms render <asset.py> [--cha r_x] [--cam nam:R,nu:L]   dựng → cửa → GLB + sheet.png (+ settler cầm) → in r_xxxxxxxx
  lpms edit <ref> --cu "<cũ>" --moi "<mới>" [...]       sửa neo trên source của ref → phiên bản con, so kích thước/bộ phận
  lpms pairs <ref> [A:B[:cham|:ho=5] ...] [--cam nam:R]  đo khoảng cách cặp; --cam: từng bộ phận vs THÂN+ĐỒ settler (lún = xuyên)
  lpms discover [từ]                                     tra hàm dựng
  lpms log <ten>                                         cây phiên bản
Exit 1 khi cửa trượt.
"""
import argparse, hashlib, inspect, json, math, os, shutil, subprocess, sys, time
import numpy as np, trimesh

NHA = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, NHA)
KHO = os.path.expanduser("~/projects/lpm-faceless-humanoid/lpms_store")
LPD = os.path.expanduser("~/projects/lpm-faceless-humanoid/lpd_detailed")
XEM_CAM = os.path.expanduser("~/.hermes/skills/creative/humanoid-replaceable-assets/scripts/view_settler_hold.py")
SETTLER = {"nam": ("out_male_hold", "BODY_M", "HAIR_SHORT_M", "OUTFIT_SETTLER_M"), "nu": ("out_female_hold", "BODY_F", "HAIR_BOB_F", "OUTFIT_SETTLER_F")}


# ------------------------------------------------------------------ kho phiên bản
def tim_ref(ref):
    for ten in os.listdir(KHO) if os.path.isdir(KHO) else []:
        d = os.path.join(KHO, ten, ref)
        if os.path.isdir(d): return d
    sys.exit(f"⛔ không thấy phiên bản {ref} trong {KHO}")


def chay_build(src):
    g = {"__name__": "lpms_asset"}; exec(compile(src, "<asset>", "exec"), g)
    return g["META"], g["build"]()


# ------------------------------------------------------------------ cửa đo (của mình, không phải của Kiln)
def ban_kinh_goc(parts):
    for m in parts.values():
        s = m.section(plane_origin=(0, 0, 0), plane_normal=(0, 0, 1))
        if s is not None:
            v = s.vertices[:, :2]; c = v[np.linalg.norm(v, axis=1) < 0.03]
            if len(c) and np.linalg.norm(c.mean(0)) < 0.01: return float(np.linalg.norm(c - c.mean(0), axis=1).mean())
    return None


def cua(meta, parts):
    from lpms_helpers import MAU
    kq = []; tg = sum(len(m.faces) for m in parts.values())
    ho = [k for k, m in parts.items() if not m.is_watertight]
    kq.append(("kín", not ho, "tất cả kín" if not ho else "hở: " + ", ".join(ho)))
    ns = meta.get("ngan_sach", 600); kq.append(("ngân sách", tg <= ns, f"{tg} / {ns} tam giác"))
    if meta.get("cam"):
        r = ban_kinh_goc(parts); kq.append(("cán tại gốc", r is not None and 0.013 <= r <= 0.017, f"{r * 1000:.1f} mm (13–17)" if r else "không có cán qua gốc"))
    if meta.get("dat"):
        z0 = float(min(m.vertices[:, 2].min() for m in parts.values()))
        kq.append(("chạm đất", -0.03 <= z0 <= 0.005, f"đáy z = {z0 * 1000:.0f} mm (−30…+5)"))
    tan = {k: m for k, m in parts.items() if k.startswith("tan")}
    if tan:   # TÁN LÁ (Boss 23/10 «cây có chỗ lồi ra như cái sừng… lá 2 màu… ko phải 1 vệt lồi màu đậm»)
        bt = meta.get("bao_tan")
        if not bt: kq.append(("tán không sừng", False, "thiếu META bao_tan (tâm + bán kính vỏ bao tán)"))
        else:
            c_ = np.asarray(bt["tam"], float); r_ = np.asarray(bt["ban_kinh"], float)
            e_ = {k: np.linalg.norm((m.vertices - c_) / r_, axis=1) for k, m in tan.items()}
            loi = {k: round(float(v.max()), 2) for k, v in e_.items() if v.max() > 1.10}
            kq.append(("tán không sừng", not loi, "mọi cụm trong 1,10 × vỏ bao" if not loi else "lồi: " + ", ".join(f"{k} {v}×" for k, v in loi.items())))
            dam = {k: m for k, m in tan.items() if m.visual.material.name.endswith("_toi")}
            lo = [k for k, m in dam.items() if np.any((m.vertices[:, 2] > c_[2] - 0.25 * r_[2]) & (e_[k] > 0.92))]   # đậm lộ ra vỏ chỉ ở dải ĐÁY (thấp hơn tâm ≥ 25 % bán kính đứng)
            kq.append(("màu đậm khuất dưới", not lo, "lớp đậm chỉ ở mặt dưới tán" if not lo else "lộ ở nửa trên: " + ", ".join(lo)))
            # lớp đậm không nhô NGANG ra khỏi khối sáng ở CÙNG TẦNG cao (thành «váy»/vệt): mỗi đỉnh đậm ≤ 97 % bán kính khối sáng trong ±8 cm cao
            sang = [m for k, m in tan.items() if k not in dam]
            if dam and sang:
                Ls = np.vstack([m.vertices for m in sang]); rs_ = np.linalg.norm(Ls[:, :2] - c_[:2], axis=1); vuot = 0.0
                for m in dam.values():
                    for v in m.vertices:
                        if v[2] <= Ls[:, 2].min() + 0.10: continue   # chỏm đáy: lớp đậm ĐƯỢC lộ ra (mặt dưới tán)
                        cung = rs_[np.abs(Ls[:, 2] - v[2]) <= 0.08]; rv = float(np.linalg.norm(v[:2] - c_[:2]))
                        vuot = max(vuot, rv - (0.97 * float(cung.max()) if len(cung) else 0.0))
                kq.append(("đậm không nhô ngang", vuot <= 0.0, "đậm nằm trong khối sáng ở mọi tầng" if vuot <= 0 else f"đậm nhô {vuot * 1000:.0f} mm ra ngoài khối sáng cùng tầng"))
    if callable(meta.get("soi")):   # asset-specific layout gate (e.g. meat_storage → settler-storage kho.soi_thit); fail ⇒ receipt dat=false ⇒ exit 1
        ok_, ct_ = meta["soi"](parts); kq.append(("xếp kho", ok_, ct_))
    import theme_colors as TM   # so theo THEME đang bật (lpms_helpers đã thêm đường dẫn)
    la = [k for k, m in parts.items() if not np.allclose(np.asarray(m.visual.material.baseColorFactor, float)[:3] / (255 if np.max(m.visual.material.baseColorFactor) > 1 else 1),
                                                         np.asarray(TM.mau(MAU.get(m.visual.material.name, [0, 0, 0])))[:3], atol=0.01)]
    kq.append(("màu nhà", not la, "đúng bảng MAU" if not la else "lạ: " + ", ".join(la)))
    # NATURE SPEC (Boss 25/10/2026 «từ rày về sau … cây, khoáng thạch, núi, hoa, nấm hay storage thì xài spec của bộ này»):
    # specs/NATURE_SPEC_yukekbyte.md §5. A nature-looking name without META loai fails — the spec cannot be skipped by omission.
    import re
    TU = r"tree|cay|rock|stone|pebble|cliff|mountain|nui|flower|hoa|mushroom|nam|bush|bui|storage|kho|log|stump|grass|mineral|crystal|firepit|bep"
    loai = meta.get("loai")
    if not loai and re.search(rf"(^|_)({TU})(_|$|\d)", meta.get("ten", "")):
        kq.append(("spec nature", False, "tên giống asset thiên nhiên/kho nhưng thiếu META loai — xem specs/NATURE_SPEC_yukekbyte.md"))
    elif loai:
        DAI = {"tree": (260, 1500), "bush": (80, 240), "berry_bush": (500, 900), "rock_big": (210, 260), "rock": (72, 96), "pebble": (16, 48),
               "cliff": (500, 1000), "log": (300, 600), "stump": (200, 350), "storage": (100, 1600), "mushroom": (158, 227), "flower": (310, 870),
               "grass": (84, 370), "prop": (60, 1600)}
        if loai not in DAI: kq.append(("spec nature", False, f"loai «{loai}» không có trong spec ({', '.join(DAI)})"))
        else:
            lo, hi = DAI[loai]; lo_, hi_ = int(lo * 0.6), int(hi * (1.0 if loai == "tree" else 1.4))
            la_mau = [k for k, m in parts.items() if not m.visual.material.name.startswith("yk_")]
            z0 = float(min(m.vertices[:, 2].min() for m in parts.values()))
            loi = []
            if not lo_ <= tg <= hi_: loi.append(f"{tg} tam giác ngoài {lo_}–{hi_}")
            if la_mau: loi.append("màu ngoài bảng yk_: " + ", ".join(la_mau[:4]))
            if not -0.15 <= z0 <= 0.0: loi.append(f"đáy z={z0:.3f} (−0,15…0)")
            if loai == "tree":
                Hc = float(max(m.vertices[:, 2].max() for m in parts.values())) - z0
                dt = {k: m.area for k, m in parts.items()}; la_ = sum(a for k, a in dt.items() if parts[k].visual.material.name.startswith("yk_la"))
                top = max((m.vertices[:, 2].max() for k, m in parts.items() if parts[k].visual.material.name.startswith("yk_la")), default=0) - z0
                if len(parts) < 2: loi.append("cây phải ≥ 2 khối (thân + tán)")
                if not 0.75 <= la_ / sum(dt.values()) <= 0.95: loi.append(f"lá {la_ / sum(dt.values()):.0%} diện tích (75–95 %)")
                if top < 0.9 * Hc: loi.append(f"đỉnh tán {top / Hc:.2f} H (≥ 0,9)")
            kq.append(("spec nature", not loi, f"{loai}: đúng spec yukekbyte" if not loi else "; ".join(loi)))
    return kq, tg


def xuat_glb(parts, f):
    Y = trimesh.transformations.rotation_matrix(-math.pi / 2, (1, 0, 0)); sc = trimesh.Scene()
    for k, m in parts.items():
        g = m.copy(); g.apply_transform(Y); sc.add_geometry(g, node_name=k, geom_name=k)
    sc.export(f)


SHEET = r'''
import bpy, math, sys, mathutils
V = mathutils.Vector; a = sys.argv[sys.argv.index("--") + 1:]; F, OUT = a
bpy.ops.wm.read_factory_settings(use_empty=True); sc = bpy.context.scene; bpy.ops.import_scene.gltf(filepath=F)
ms = [o for o in bpy.data.objects if o.type == "MESH"]
for o in ms:
    for p in o.data.polygons: p.use_smooth = False
pts = [o.matrix_world @ V(c) for o in ms for c in o.bound_box]; lo = V([min(p[i] for p in pts) for i in range(3)]); hi = V([max(p[i] for p in pts) for i in range(3)])
tam = (lo + hi) / 2; R = max((hi - lo).length * 0.62, 0.2)
for e, r in ((3.0, (45, 0, 45)), (1.2, (60, 0, 60)), (1.6, (60, 0, 160))):
    l = bpy.data.objects.new("l", bpy.data.lights.new("l", "SUN")); sc.collection.objects.link(l); l.data.energy = e; l.data.angle = math.radians(8); l.data.use_shadow = e >= 2.5; l.data.use_shadow_jitter = True; l.rotation_euler = [math.radians(x) for x in r]
w = bpy.data.worlds.new("W"); sc.world = w; w.use_nodes = True; w.node_tree.nodes["Background"].inputs[0].default_value = (0.42, 0.44, 0.40, 1)
c = bpy.data.cameras.new("c"); c.type = "ORTHO"; c.ortho_scale = 2 * R; c.clip_end = 100; co = bpy.data.objects.new("c", c); sc.collection.objects.link(co); sc.camera = co
sc.render.engine = "BLENDER_EEVEE"; sc.view_settings.view_transform = "Standard"; sc.render.resolution_x = sc.render.resolution_y = 600
for ten, (rx, rz) in {"truoc": (90, 0), "nghieng": (90, 90), "tren": (0, 0), "34": (65, -40)}.items():
    co.rotation_euler = (math.radians(rx), 0, math.radians(rz)); co.location = tam + co.rotation_euler.to_matrix() @ V((0, 0, 30))
    sc.render.filepath = OUT + "_" + ten + ".png"; bpy.ops.render.render(write_still=True)
'''


def ve_sheet(glb, d):
    f = os.path.join(d, "_sheet.py"); open(f, "w").write(SHEET)
    subprocess.run(["blender", "-b", "-P", f, "--", glb, os.path.join(d, "v")], capture_output=True)
    from PIL import Image, ImageDraw
    ims = [Image.open(os.path.join(d, f"v_{t}.png")).convert("RGB") for t in ("truoc", "nghieng", "tren", "34")]
    sh = Image.new("RGB", (1200, 1200))
    for i, (im, t) in enumerate(zip(ims, ("trước", "nghiêng", "trên", "3/4"))):
        sh.paste(im, ((i % 2) * 600, (i // 2) * 600)); ImageDraw.Draw(sh).text(((i % 2) * 600 + 12, (i // 2) * 600 + 10), t, fill=(255, 255, 255))
    sh.save(os.path.join(d, "sheet.png"))
    for t in ("truoc", "nghieng", "tren", "34"): os.remove(os.path.join(d, f"v_{t}.png"))
    os.remove(f)


def ve_cam(d, ten, cam):
    """settler ĐÃ CHỐT cầm món (Boss 22/10: review trên settler, không trên thân trơn)."""
    nhom = []
    for muc in cam.split(","):
        gioi, ben = muc.split(":"); o, b, h, q = SETTLER[gioi]; D = os.path.join(LPD, o)
        nhom.append(f"{D}/{b}.glb+{D}/{h}.glb+{D}/{q}.glb@{D}/geometry.json@{ben}={ten}")
    subprocess.run(["blender", "-b", "-P", XEM_CAM, "--", d, os.path.join(d, "cam.png")] + nhom, capture_output=True)


# ------------------------------------------------------------------ lệnh
def render(src_path=None, src=None, cha=None, cam=None):
    src = src if src is not None else open(src_path).read()
    meta, parts = chay_build(src); ten = meta["ten"]
    ref = "r_" + hashlib.sha256((src + open(os.path.join(NHA, "lpms_helpers.py")).read()).encode()).hexdigest()[:8]
    d = os.path.join(KHO, ten, ref); os.makedirs(d, exist_ok=True)   # ref gồm cả helper/bảng màu ⇒ đổi màu = phiên bản MỚI, không ghi đè
    open(os.path.join(d, "source.py"), "w").write(src)
    kq, tg = cua(meta, parts); glb = os.path.join(d, f"{ten}.glb"); xuat_glb(parts, glb); ve_sheet(glb, d)
    # VỎ VA CHẠM (Boss 22/10 «bất cứ vật thể nào cũng phải set boundary layer sau khi chốt xong modeling»): khối lồi từng bộ phận ⇒ shatter.json
    vo_ = {k: np.round(m.convex_hull.vertices, 5).tolist() for k, m in parts.items()}; json.dump(vo_, open(os.path.join(d, "shatter.json"), "w"))
    kq.append(("vỏ va chạm", len(vo_) == len(parts) and all(len(v) >= 4 for v in vo_.values()), f"{len(vo_)} khối lồi → shatter.json"))
    if cam: ve_cam(d, ten, cam)
    V = np.vstack([m.vertices for m in parts.values()])
    bn = dict(ref=ref, cha=cha, ten=ten, luc=time.strftime("%Y-%m-%d %H:%M"), tam_giac=tg, kich_thuoc_m=[round(float(x), 3) for x in np.ptp(V, 0)],
              bo_phan={k: hashlib.sha1(np.round(m.vertices, 5).tobytes()).hexdigest()[:10] for k, m in parts.items()},
              cua=[dict(ten=a, dat=b, do=c) for a, b, c in kq], dat=all(b for _, b, _ in kq),
              tep=sorted(os.listdir(d)))
    json.dump(bn, open(os.path.join(d, "receipt.json"), "w"), ensure_ascii=False, indent=1)
    for a, b, c in kq: print(f"  {'✅' if b else '❌'} {a}: {c}")
    print(f"{'✅' if bn['dat'] else '⛔'} {ten} {ref} · {tg} tam giác · {bn['kich_thuoc_m']} m · {d}")
    return bn, d


def edit(ref, cus, mois, cam=None):
    d = tim_ref(ref); src = open(os.path.join(d, "source.py")).read(); cu_bn = json.load(open(os.path.join(d, "receipt.json")))
    for a, b in zip(cus, mois):
        n = src.count(a)
        if n != 1: sys.exit(f"⛔ đoạn neo xuất hiện {n} lần (phải đúng 1): {a[:60]!r}")
        src = src.replace(a, b)
    bn, _ = render(src=src, cha=ref, cam=cam)
    doi = [k for k in bn["bo_phan"] if cu_bn["bo_phan"].get(k) != bn["bo_phan"][k]]
    print(f"  kích thước {cu_bn['kich_thuoc_m']} → {bn['kich_thuoc_m']} m · tam giác {cu_bn['tam_giac']} → {bn['tam_giac']}")
    print(f"  bộ phận đổi: {', '.join(doi) or 'không'} · thêm: {', '.join(set(bn['bo_phan']) - set(cu_bn['bo_phan'])) or 'không'}"
          f" · bớt: {', '.join(set(cu_bn['bo_phan']) - set(bn['bo_phan'])) or 'không'}")
    return bn


def _parts_glb(f):
    sc = trimesh.load(f); out = {}
    for node in sc.graph.nodes_geometry:
        T, g = sc.graph[node]; m = sc.geometry[g].copy(); m.apply_transform(T); m.merge_vertices(); out[node] = m
    return out


def _ben_trong(points, M):
    """parity bỏ phiếu 3 tia lệch hướng (đa số) — chép từ lpd_detailed/hair_outfit.py (hiệu chỉnh 22/10: tia đơn sai 4/8, 3 tia 0/8).
    Không cần rtree (máy không cài được, PEP 668)."""
    tri = M.triangles; e1, e2 = tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0]; phieu = np.zeros(len(points), int)
    for d in (np.array([1.0, 0.0137, 0.0071]), np.array([-0.0113, 1.0, 0.0193]), np.array([0.0171, -0.0089, 1.0])):
        d = d / np.linalg.norm(d); pv = np.cross(d, e2); det = np.einsum("ij,ij->i", e1, pv); ok = np.abs(det) > 1e-12
        inv = np.where(ok, 1 / np.where(ok, det, 1), 0)
        for s in range(0, len(points), 400):
            P = points[s:s + 400]; tv = P[:, None, :] - tri[None, :, 0]
            u = np.einsum("pij,ij->pi", tv, pv) * inv; qv = np.cross(tv, e1[None]); v = (qv @ d) * inv
            t = np.einsum("pij,ij->pi", qv, e2) * inv
            phieu[s:s + 400] += ((ok[None] & (u >= 0) & (v >= 0) & (u + v <= 1) & (t > 1e-6)).sum(1) % 2) == 1
    return phieu >= 2


def _khoang(A, B, n=3000):
    """(khe nhỏ nhất mm, lún sâu nhất mm) của A so với B: mẫu mặt A; trong/ngoài = parity 3 tia; khoảng = tới mẫu dày mặt B (sai số ≈ 1 mm)."""
    from scipy.spatial import cKDTree
    pa = trimesh.sample.sample_surface(A, n)[0]; pb = trimesh.sample.sample_surface(B, 40000)[0]
    dist = cKDTree(pb).query(pa)[0]; trong = _ben_trong(pa, B)
    return float(dist[~trong].min() * 1000) if (~trong).any() else 0.0, float(dist[trong].max() * 1000) if trong.any() else 0.0


def pairs(ref, cap, cam=None):
    d = tim_ref(ref); bn = json.load(open(os.path.join(d, "receipt.json"))); P = _parts_glb(os.path.join(d, f"{bn['ten']}.glb")); ok = True
    for c in cap:
        a, b, *loai = c.split(":"); loai = loai[0] if loai else "cham"
        khe, lun = _khoang(P[a], P[b])
        d_ok = (khe <= 2.0) if loai == "cham" else (khe >= float(loai.split("=")[1]) and lun == 0)
        ok &= d_ok; print(f"  {'✅' if d_ok else '❌'} {a} ↔ {b} ({loai}): khe {khe:.1f} mm · lún {lun:.1f} mm")
    if cam:
        Y = trimesh.transformations.rotation_matrix(math.pi / 2, (1, 0, 0))   # GLB Y-up → Z-up
        for muc in cam.split(","):
            gioi, ben = muc.split(":"); o, b, h, q = SETTLER[gioi]; D = os.path.join(LPD, o)
            s = json.load(open(f"{D}/geometry.json"))["socket"][f"cam_{ben}"]
            z = np.array(s["len"], float); z /= np.linalg.norm(z); x = np.array((0, 0, -1.0)); x -= z * x.dot(z); x /= np.linalg.norm(x)
            M = np.eye(4); M[:3, :3] = np.column_stack((x, np.cross(z, x), z)); M[:3, 3] = s["vi_tri"]
            nguoi = {}
            for f in (b, q):
                for k, m in _parts_glb(f"{D}/{f}.glb").items(): m.apply_transform(Y); nguoi[f"{f}/{k}"] = m
            for k, m in P.items():
                t = m.copy(); t.apply_transform(Y); t.apply_transform(M)
                for kn, mn in nguoi.items():
                    if not mn.is_watertight and not kn.startswith(b): continue   # vỏ áo một lớp: parity vô nghĩa
                    khe, lun = _khoang(t, mn, 1500)
                    if lun > 1.5 and not (k == "can" and kn.startswith(b)):      # cán nằm trong nắm tay là đúng
                        ok = False; print(f"  ❌ {gioi}:{ben} {k} xuyên {kn} {lun:.1f} mm")
            print(f"  {gioi}:{ben} — đã đo {len(P)} bộ phận × {len(nguoi)} khối người")
    print("✅ CẶP ĐẠT" if ok else "⛔ CẶP TRƯỢT"); return ok


def discover(tu=None):
    import lpms_helpers as H
    for ten, f in inspect.getmembers(H, inspect.isfunction):
        if ten.startswith("_") or f.__module__ != "lpms_helpers": continue
        doc = (f.__doc__ or "").strip()
        if tu and tu.lower() not in (ten + doc).lower(): continue
        print(f"{ten}{inspect.signature(f)}\n    {doc}\n")


def log(ten):
    d = os.path.join(KHO, ten); rs = [json.load(open(os.path.join(d, r, "receipt.json"))) for r in os.listdir(d) if r.startswith("r_")]
    for r in sorted(rs, key=lambda r: r["luc"]):
        print(f"  {r['ref']} ← {r['cha'] or 'gốc'} · {r['luc']} · {r['tam_giac']} tg · {'✅' if r['dat'] else '❌'}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter); sp = ap.add_subparsers(dest="lenh", required=True)
    a = sp.add_parser("render"); a.add_argument("asset"); a.add_argument("--cha"); a.add_argument("--cam")
    a = sp.add_parser("edit"); a.add_argument("ref"); a.add_argument("--cu", action="append", required=True); a.add_argument("--moi", action="append", required=True); a.add_argument("--cam")
    a = sp.add_parser("pairs"); a.add_argument("ref"); a.add_argument("cap", nargs="*"); a.add_argument("--cam")
    a = sp.add_parser("discover"); a.add_argument("tu", nargs="?")
    a = sp.add_parser("log"); a.add_argument("ten")
    g = ap.parse_args()
    if g.lenh == "render": sys.exit(0 if render(g.asset, cha=g.cha, cam=g.cam)[0]["dat"] else 1)
    if g.lenh == "edit": sys.exit(0 if edit(g.ref, g.cu, g.moi, g.cam)["dat"] else 1)
    if g.lenh == "pairs": sys.exit(0 if pairs(g.ref, g.cap, g.cam) else 1)
    if g.lenh == "discover": discover(g.tu)
    if g.lenh == "log": log(g.ten)

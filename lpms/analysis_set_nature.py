"""PHÂN TÍCH HÌNH HỌC một bộ asset thiên nhiên low-poly để ghi luật dựng cho lpms (Boss 23/10/2026: «học cách tạo các assets này thật chi
tiết về cách thể hiện hình học này kia cho PLM skill» — bộ CGTrader forest set của flamazilla; Boss cho phép AI học dù giấy phép «No AI»).
Mỗi object: tách MẢNH RỜI (khối cấu thành), mỗi mảnh: số đỉnh/mặt, kích thước, độ dẹt, số cạnh mặt cắt (đếm đỉnh trên vòng giữa),
màu (đọc pixel texture tại UV tâm mặt), góc gập trung bình giữa mặt kề (độ «gồ» facet), mặt đáy phẳng hay không.
  blender -b <bo.blend> -P analysis_set_nature.py -- <texture.png> <out.json>"""
import bpy, bmesh, json, math, sys, mathutils
V = mathutils.Vector
a_ = sys.argv[sys.argv.index("--") + 1:]; TEX, OUT = a_[0], a_[1]
img = bpy.data.images.load(TEX); W_, H_ = img.size; PX = list(img.pixels)
def mau_uv(u, v):
    x = min(W_ - 1, max(0, int(u * W_))); y = min(H_ - 1, max(0, int(v * H_))); i = (y * W_ + x) * 4
    c = PX[i:i + 3]; return tuple(round(255 * (((ch) ** (1 / 2.4)) * 1.055 - 0.055 if ch > 0.0031308 else ch * 12.92)) for ch in c)
KQ = {}
for o in [o for o in bpy.data.objects if o.type == "MESH" and o.name != "SimpleGround"]:
    bm = bmesh.new(); bm.from_mesh(o.data); bm.transform(o.matrix_world); uvl = bm.loops.layers.uv.active
    H = max(v.co.z for v in bm.verts) - min(v.co.z for v in bm.verts); zmin = min(v.co.z for v in bm.verts)
    # mảnh rời (theo cạnh)
    seen = set(); manh = []
    for v in bm.verts:
        if v.index in seen: continue
        st = [v]; c = []
        while st:
            x = st.pop()
            if x.index in seen: continue
            seen.add(x.index); c.append(x); st += [e.other_vert(x) for e in x.link_edges]
        manh.append(c)
    mm = []
    for c in manh:
        P = [v.co for v in c]; mn = V((min(p.x for p in P), min(p.y for p in P), min(p.z for p in P))); mx = V((max(p.x for p in P), max(p.y for p in P), max(p.z for p in P)))
        fs = {f for v in c for f in v.link_faces}; mau = {}
        for f in fs:
            if uvl:
                u = sum((l[uvl].uv for l in f.loops), mathutils.Vector((0, 0))) / len(f.loops); k = mau_uv(u.x, u.y); mau[k] = mau.get(k, 0) + 1
        cz = (mn.z + mx.z) / 2; vong = [p for p in P if abs(p.z - cz) < 0.08 * (mx.z - mn.z + 1e-6)]
        gap = [math.degrees(e.calc_face_angle(0)) for e in {e for f in fs for e in f.edges} if len(e.link_faces) == 2]
        mm.append({"dinh": len(c), "mat": len(fs), "tam_tuong_doi_H": [round((((mn + mx) / 2) - V((0, 0, zmin)))[i] / max(H, 1e-6), 2) for i in range(3)],
                   "kich_H": [round((mx - mn)[i] / max(H, 1e-6), 2) for i in range(3)], "dinh_vong_giua": len(vong),
                   "gap_mat_tb_do": round(sum(gap) / len(gap), 1) if gap else 0, "mau_chinh": sorted(mau.items(), key=lambda kv: -kv[1])[:3]})
    mm.sort(key=lambda m: -m["dinh"])
    day = [f for f in bm.faces if f.normal.z < -0.95 and abs(f.calc_center_median().z - zmin) < 0.02 * H]
    KQ[o.name] = {"nhom": o.users_collection[0].name, "cao": round(H, 2), "mat": len(bm.faces), "so_manh": len(manh), "day_phang_mat": len(day), "manh": mm[:12]}
    bm.free()
json.dump(KQ, open(OUT, "w"), indent=1, ensure_ascii=False); print("XONG", len(KQ))

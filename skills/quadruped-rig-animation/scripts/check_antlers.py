"""ĐO GẠC (Boss 23/10/2026: «Phong cách sừng của nai, thể hiện nhiều nét như cây, cũng đáng để học và ghi vào skill, cách mô tả hình học
cong thẳng naturally»). Trên lưới gạc (một bên): đầu mút (tine) = cực đại khoảng cách geodesic từ gốc; thân chính = đường gốc → mút xa nhất;
đo độ thon, độ «gãy khúc» (đoạn thẳng nối bằng khớp gập), góc tách nhánh, khoảng cách giữa các nhánh.
  blender -b -P check_antlers.py -- <model.glb> <out.json> [ten_luoi_gac=Horns]"""
import bpy, bmesh, json, math, sys, mathutils
import numpy as np
import heapq   # Python của Blender KHÔNG có scipy ⇒ Dijkstra tự viết


def dijkstra(ke, nguon):
    n = len(ke); D = np.full(n, np.inf); truoc = np.full(n, -1, int); D[nguon] = 0; h = [(0.0, nguon)]
    while h:
        d, u = heapq.heappop(h)
        if d > D[u]: continue
        for v, w in ke[u]:
            if d + w < D[v]: D[v] = d + w; truoc[v] = u; heapq.heappush(h, (D[v], v))
    return D, truoc
V = mathutils.Vector
a_ = sys.argv[sys.argv.index("--") + 1:]; SRC, OUT = a_[0], a_[1]; TEN = a_[2] if len(a_) > 2 else "Horn"
bpy.ops.wm.read_factory_settings(use_empty=True); bpy.ops.import_scene.gltf(filepath=SRC)
g = next(o for o in bpy.data.objects if o.type == "MESH" and TEN.lower() in o.name.lower())
bm = bmesh.new(); bm.from_mesh(g.data); bm.transform(g.matrix_world); bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-4)
P = np.array([tuple(v.co) for v in bm.verts]); ed = [(e.verts[0].index, e.verts[1].index) for e in bm.edges]
KQ = {"nguon": SRC}
for ben, sx in (("trai", 1), ("phai", -1)):
    ids = np.where(P[:, 0] * sx > 0)[0]; m = {int(i): k for k, i in enumerate(ids)}; Q = P[ids]
    ke = [[] for _ in range(len(ids))]
    for a, b in ed:
        if a in m and b in m: d = float(np.linalg.norm(P[a] - P[b])); ke[m[a]].append((m[b], d)); ke[m[b]].append((m[a], d))
    goc = int(np.argmin(Q[:, 2]))   # gốc gạc = đỉnh thấp nhất (dính sọ)
    D, pred = dijkstra(ke, goc)
    # đầu mút: D lớn nhất trong lân cận bán kính r (geodesic cục bộ ≈ Euclid) và xa gốc
    Lmax = float(D[np.isfinite(D)].max()); r = 0.18 * Lmax; mut = []   # 0,06 ⇒ 40 «mút» giả (bắt cả chỗ gồ)
    for i in np.argsort(-D):
        if not np.isfinite(D[i]) or D[i] < 0.15 * Lmax: break
        if all(np.linalg.norm(Q[i] - Q[j]) > r for j in mut): mut.append(int(i))
    # thân chính: dò ngược từ mút xa nhất về gốc theo bước giảm D
    def duong(t):
        p = [t]
        while p[-1] != goc and pred[p[-1]] >= 0: p.append(int(pred[p[-1]]))
        return p[::-1]
    than = duong(mut[0]); diem = Q[than]
    # gộp thành ~12 trạm cách đều theo chiều dài ⇒ đo hướng từng đoạn, góc gập giữa đoạn
    s = np.concatenate([[0], np.cumsum(np.linalg.norm(np.diff(diem, axis=0), axis=1))]); tram = [diem[np.searchsorted(s, t)] for t in np.linspace(0, s[-1] * 0.999, 13)]
    huong = [(tram[k + 1] - tram[k]) / max(1e-9, np.linalg.norm(tram[k + 1] - tram[k])) for k in range(12)]
    gap = [math.degrees(math.acos(max(-1, min(1, float(np.dot(huong[k], huong[k + 1])))))) for k in range(11)]
    # bán kính (độ thon): khoảng cách TB các đỉnh gần trạm tới trục
    ban_kinh = []
    for k in range(12):
        c = (tram[k] + tram[k + 1]) / 2; h = huong[k]; gan = Q[np.abs((Q - c) @ h) < 0.5 * np.linalg.norm(tram[k + 1] - tram[k])]
        dd = np.linalg.norm((gan - c) - np.outer((gan - c) @ h, h), axis=1); ban_kinh.append(float(np.percentile(dd, 60)) if len(dd) else None)
    # nhánh: với mỗi mút khác, điểm tách = đỉnh chung cuối của đường về gốc với thân chính
    tap_than = set(than); nhanh = []
    for t in mut[1:]:
        p = duong(t); tach = next((v for v in reversed(p) if v in tap_than), goc)
        st = float(s[than.index(tach)]) / s[-1] if tach in than else 0.0
        k = min(11, int(st * 12)); dv = Q[t] - Q[tach]; L = float(np.linalg.norm(dv))
        goc_tach = math.degrees(math.acos(max(-1, min(1, float(np.dot(dv / L, huong[k])))))) if L > 0 else 0
        nhanh.append({"vi_tri_tren_than": round(st, 2), "dai_so_than": round(L / s[-1], 2), "goc_tach_do": round(goc_tach, 1), "huong_len_z": round(float(dv[2] / L), 2)})
    tong = s[-1]; cao = float(diem[-1][2] - diem[0][2]); thang = float(np.linalg.norm(diem[-1] - diem[0]))
    KQ[ben] = {"so_mut": len(mut), "than_dai": round(tong, 3), "do_thang_than (day cung / chieu dai)": round(thang / tong, 3),
               "goc_gap_giua_doan_do": [round(x, 1) for x in gap], "ban_kinh_doc_than": [round(x / tong, 4) if x else None for x in ban_kinh],
               "nhanh": sorted(nhanh, key=lambda x: x["vi_tri_tren_than"]), "tam_giac_ben": int(len(ids)), "huong_than_cuoi": [round(float(x), 2) for x in huong[-1]], "huong_than_dau": [round(float(x), 2) for x in huong[0]]}
json.dump(KQ, open(OUT, "w"), indent=1, ensure_ascii=False); print("XONG", json.dumps(KQ["trai"], ensure_ascii=False)[:1500])

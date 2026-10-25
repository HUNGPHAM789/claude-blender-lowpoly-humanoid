"""LÀM MƯỢT TRỌNG SỐ DA VÙNG VAI–NÁCH (Boss 23/10/2026: «Nách bị lỏm gắt… Lỗi da hay là phải thêm vải cho áo? Sửa cái nào scalable?»).
Lỗi là DA (heat weight cắt gắt giữa bắp tay và ngực ⇒ giơ tay qua đầu da nách sụp); sửa ở dữ liệu trọng số ⇒ engine nào cũng nhận
(DQS/Preserve Volume của Blender giúp một phần nhưng mất khi xuất glTF). Laplace trên láng giềng lưới, chỉ đỉnh trong vùng, chuẩn hoá lại."""
import bpy, numpy as np


def smooth_shoulder(o, vong=8, he_so=0.6, nhom_vung=None):
    nhom_vung = nhom_vung or [f"{x}_{b}" for b in "LR" for x in ("upperarm", "clavicle")] + ["chest", "spine", "neck"]
    G = [g for g in o.vertex_groups if g.name in nhom_vung]; n = len(o.data.vertices); gi = {g.index: k for k, g in enumerate(G)}
    Wt = np.zeros((n, len(G)))
    other = np.zeros(n)
    for v in o.data.vertices:
        for e in v.groups:
            if e.group in gi: Wt[v.index, gi[e.group]] = e.weight
            else: other[v.index] += e.weight
    vung = np.where((Wt > 0.02).sum(1) >= 1)[0]
    vung = [i for i in vung if any(Wt[i, gi[g.index]] > 0.02 for g in G if g.name.startswith("upperarm"))]   # chỉ quanh bắp tay (vai + nách)
    ke = [[] for _ in range(n)]
    for e in o.data.edges: a, b = e.vertices; ke[a].append(b); ke[b].append(a)
    vung_set = set(vung)
    for _ in range(vong):
        W2 = Wt.copy()
        for i in vung:
            if not ke[i]: continue
            W2[i] = (1 - he_so) * Wt[i] + he_so * Wt[ke[i]].mean(0)
        Wt = W2
    for i in vung:   # chuẩn hoá: tổng (nhóm vùng) = 1 − trọng số nhóm khác
        s = Wt[i].sum(); tg = max(0.0, 1.0 - other[i])
        if s > 1e-9: Wt[i] *= tg / s
        for k, g in enumerate(G):
            if Wt[i, k] > 1e-4: g.add([int(i)], float(Wt[i, k]), "REPLACE")
            else: g.remove([int(i)])
    return len(vung)

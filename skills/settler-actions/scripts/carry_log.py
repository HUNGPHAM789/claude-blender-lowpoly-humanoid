"""VÁC GỖ ĐÚNG VẬT LÝ (Boss 22–23/10/2026) — tách từ anim_settler/chop_tree_scene.py để mọi cảnh vác dùng chung (kho gỗ, 2 settler…).
lap_vac(rig, go_v, F_VAC, HOA, DAI_VAC, F_END, so_khuc, kglb, out, nhap, mo, an_hien, ten="khuc_vac") → (GO, CUA)
  rig     : armature đã key tư thế vác (clip carry) · go_v: vật mang chuyển động khúc gỗ của clip carry (bị ẩn, làm khung)
  F_VAC/HOA: khung bắt đầu hoà sang vác / số khung hoà · DAI_VAC: độ dài clip vác · F_END: khung cuối cần khớp
Luật + cửa (exit ở nơi gọi nếu CUA["dat"] False): ⑧ cân vai mọi khung · ⑩ tì vai 5 mm (+BVH nâng) · ⑦ lòng tay (nhãn) áp MẶT NGOÀI bó gỗ,
cả cánh tay ngoài vỏ gỗ, khe thật −3…10 mm · ⑦b BVH 0 · ⑨ khuỷu ra ngoài · ⑥ gỗ cách đầu ≥ 0. Chi tiết: humanoid-rig-animation §CONTACT CONTRACT."""
import os, sys, math
import bpy, mathutils
V = mathutils.Vector; M4 = mathutils.Matrix
sys.path.insert(0, os.path.expanduser("~/.hermes/skills/creative/las-physics/scripts"))


def lap_vac(rig, go_v, F_VAC, HOA, DAI_VAC, F_END, so_khuc, kglb, out, nhap, mo, an_hien, ten="khuc_vac"):
    sc = bpy.context.scene
    # KHÚC GỖ VÁC 1/2/3 (Boss 22/10 «bự hơn dài hơn… 3 miếng chồng hình tam giác… setup sẵn… capacity 1/2/3»): khuc_go cũ chỉ còn làm KHUNG chuyển động
    # (ẩn); khúc mới (lpms carried_log) gắn con. Khúc dưới giữ đúng chỗ cũ (tay đang đỡ nó); khúc thêm xếp LÊN trên / RA XA đầu, đo từ tư thế vác thật.
    SO_KHUC = so_khuc; KGLB = kglb; OUT = out; CUA = {"dat": True}
    go_v.hide_render = True
    f_giua = F_VAC + DAI_VAC // 2; sc.frame_set(f_giua); bpy.context.view_layer.update()
    Mg = go_v.matrix_world.copy(); R3 = Mg.to_3x3().normalized(); zl = V((0, 0, 1))
    len_l = (R3.inverted() @ V((0, 0, 1))); len_l = (len_l - zl * len_l.dot(zl)).normalized()   # «lên» trong khung khúc gỗ
    ngang_l = zl.cross(len_l).normalized(); dau_w = rig.matrix_world @ rig.pose.bones["head"].head
    if (R3.inverted() @ (dau_w - Mg.translation)).dot(ngang_l) > 0: ngang_l = -ngang_l   # «ra» = phía xa đầu
    o_k, _ = nhap(KGLB); khuc0 = [o for o in o_k if o.type == "MESH"]
    bpy.ops.object.select_all(action="DESELECT")
    for o in khuc0: o.select_set(True)
    bpy.context.view_layer.objects.active = khuc0[0]; bpy.ops.object.join(); k0 = khuc0[0]; k0.name = ten
    rk = 0.10 if SO_KHUC == 1 else 0.085; tl_ = rk / 0.10
    # VỎ THÂN thật (las-physics shatter.py, capsule/xương fit từ skin) thay bán kính đoán (R_DAU 0,095 — vỏ đầu+tóc đo được 0,11)
    import shatter as VO
    than_ = [o for o in bpy.data.objects if o.type == "MESH" and o.parent is rig and o.vertex_groups]
    VO_N = VO.vo_nguoi(rig, than_, out=os.path.join(OUT, "body_shell.json")); DAU_CO = [b for b in VO_N if b not in ("head", "neck")]
    R_DAU = 0.0


    def kc_dau(c_w, ax_w):   # khe trục khúc gỗ → vỏ đầu/cổ (đã trừ bán kính vỏ; cộng R_DAU=0 để giữ công thức cũ)
        return VO.kc_tru(c_w, ax_w, 0.0, 1.45 * 0.95, VO.vo_the_gioi(rig, VO_N), bo_qua=DAU_CO)[0]


    # DỜI BÓ RA XA ĐẦU: khúc dưới phải cách đầu ≥ rk + R_DAU + 1 cm trên MỌI khung vác (khúc to ⇒ đâm đầu: trục cách 0,15 m, đo 22/10)
    can_ = 0.0
    for f_ in range(F_VAC + HOA - 4, F_END + 1):
        sc.frame_set(f_); bpy.context.view_layer.update(); M_ = go_v.matrix_world; R_ = M_.to_3x3().normalized()
        can_ = max(can_, rk + R_DAU + 0.01 - kc_dau(M_.translation, (R_ @ zl).normalized()))
    DOI = max(0.0, can_) * 1.1; print("KHUC_VAC dời ra xa đầu m", round(DOI, 3))
    cho = {1: [(0, 0, 1.0, 0)], 2: [(0, 0, 1.0, 0), (0, 2, 0.95, 40)], 3: [(0, 0, 1.0, 0), (2, 0, 0.95, 25), (1, 1.732, 1.04, 70)]}[SO_KHUC]
    GO = []
    for i, (ra_, len_, dai_, xoay_) in enumerate(cho):
        o = k0 if i == 0 else k0.copy()
        if i: o.data = k0.data.copy(); sc.collection.objects.link(o)
        o.parent = go_v; o.matrix_parent_inverse = M4()
        o.location = ngang_l * (ra_ * rk + DOI) + len_l * len_ * rk + zl * (0.03 * (i % 2) - 0.015)
        o.rotation_mode = "XYZ"; o.rotation_euler = (0, 0, math.radians(xoay_)); o.scale = (tl_, tl_, dai_)
        for j, mt in enumerate(o.data.materials): o.data.materials[j] = mt.copy()
        an_hien(o, F_VAC + HOA - 4, 10 ** 6); mo(o, F_VAC + HOA - 4, 8, 0.0, 1.0); GO.append(o)   # hiện khi tư thế vác đã vào (hiện lúc đang hoà ⇒ gỗ xuyên đầu)
    print("KHUC_VAC", SO_KHUC, "lên", [round(x, 2) for x in len_l], "ra", [round(x, 2) for x in ngang_l])

    # ⑧ CÂN GIỮA VAI (Boss 22/10 «plank placement phải center, hơi bị dài hơn ở phía sau, ko hợp physic, carry kiểu đó là té ngoài đời thực»):
    # trọng tâm cả bó (theo thể tích từng khúc) chiếu lên trục khúc phải nằm trên ĐIỂM TÌ VAI ⇒ dời bó dọc trục cho lệch trung bình = 0
    sys.path.insert(0, os.path.expanduser("~/.hermes/skills/creative/humanoid-rig-animation/scripts")); import humanoid_anim as H
    F_HIEN = F_VAC + HOA - 4; W_ = rig.matrix_world; P_ = rig.pose.bones
    sc.frame_set(f_giua); bpy.context.view_layer.update()
    VAI = min("LR", key=lambda b: ((W_ @ P_[f"upperarm_{b}"].head) - GO[0].matrix_world.translation).length)


    def bo_go():   # [(tâm, trục, bán kính, thể tích)] thế giới
        out = []
        for o in GO:
            M_ = o.matrix_world; ax_ = (M_.to_3x3() @ zl); dai_ = ax_.length * 1.45; r_ = 0.10 * o.matrix_world.to_3x3().col[0].length
            out.append((M_.translation.copy(), ax_.normalized(), r_, r_ * r_ * dai_))
        return out


    def lech_vai():
        b_ = bo_go(); tong = sum(x[3] for x in b_); c_ = sum((x[0] * x[3] for x in b_), V()) / tong
        return (c_ - (W_ @ P_[f"upperarm_{VAI}"].head)).dot(b_[0][1])


    # TỪNG KHUNG (clip vác cũ cho khúc gỗ trượt dọc vai ±9 cm khi đi — gỗ trượt trên vai = sai): dời khung gỗ dọc trục cho trọng tâm bó ở ngay vai
    ls_ = []
    for f_ in range(F_HIEN, F_END + 1):
        sc.frame_set(f_); bpy.context.view_layer.update(); l_ = lech_vai(); ls_.append(l_)
        go_v.matrix_world = M4.Translation(-bo_go()[0][1] * l_) @ go_v.matrix_world; go_v.keyframe_insert("location", frame=f_)
    m_ = max(map(abs, ls_))
    ls2 = []
    for f_ in range(F_HIEN, F_END + 1): sc.frame_set(f_); bpy.context.view_layer.update(); ls2.append(lech_vai())
    print("CAN_VAI vai", VAI, "lệch lớn nhất trước", round(m_ * 1000), "mm ⇒ sau", round(max(map(abs, ls2)) * 1000), "mm")
    # ⑩ GỖ TÌ LÊN VAI (đo 23/10: bó gỗ lơ lửng trên vai 27–54 mm sau khi dời xa đầu): mỗi khung hạ bó theo phương đứng tới khi
    # lưới vùng vai bên vác (xương đòn/bắp tay/ngực/cổ, cả áo) cách gỗ 5 mm. Làm TRƯỚC khi giải tay.
    VUNG_VAI = {f"clavicle_{VAI}", f"upperarm_{VAI}", "chest", "neck"}
    nguoi_m = [o for o in bpy.data.objects if o.type == "MESH" and o.parent is rig]
    IDX_VAI = {}
    for o in nguoi_m:
        nh2 = {g_.index: g_.name for g_ in o.vertex_groups}
        IDX_VAI[o.name] = [v.index for v in o.data.vertices if any(nh2.get(e.group) in VUNG_VAI and e.weight >= 0.4 for e in v.groups)]


    def khe_vai():
        dg_ = bpy.context.evaluated_depsgraph_get(); go_ = bo_go(); m_ = 9.0
        for o in nguoi_m:
            if not IDX_VAI[o.name]: continue
            oe_ = o.evaluated_get(dg_); me_ = oe_.to_mesh(); M_ = o.matrix_world
            for i in IDX_VAI[o.name]:
                p_ = M_ @ me_.vertices[i].co
                for c_, ax_, r_, _ in go_:
                    t_ = max(-0.72, min(0.72, (p_ - c_).dot(ax_))); m_ = min(m_, (p_ - (c_ + ax_ * t_)).length - r_)
            oe_.to_mesh_clear()
        return m_


    IDX_TAY = {}
    for o in nguoi_m:
        nh3 = {g_.index: g_.name for g_ in o.vertex_groups}
        IDX_TAY[o.name] = {v.index for v in o.data.vertices if any((nh3.get(e.group) or "").startswith(("upperarm_", "forearm_", "hand_")) and e.weight >= 0.3 for e in v.groups)}
    KHE_VAI = []; KHE_TI = 0.005   # 5 mm: tì 2 mm theo ĐỈNH ⇒ mặt áo low-poly cắt vào gỗ giữa 2 đỉnh (BVH 4–8 cặp/khung, 23/10)
    for f_ in range(F_HIEN, F_END + 1):
        sc.frame_set(f_); bpy.context.view_layer.update()
        for _ in range(10):   # hạ đứng chỉ giảm khe theo cos góc tiếp xúc ⇒ lặp tới hội tụ
            g_ = khe_vai()
            if abs(g_ - KHE_TI) < 0.001: break
            go_v.matrix_world = M4.Translation(V((0, 0, -(g_ - KHE_TI)))) @ go_v.matrix_world; bpy.context.view_layer.update()
        from mathutils.bvhtree import BVHTree as _BT
        def _chong():   # mặt áo/thân low-poly cắt vào gỗ giữa 2 đỉnh dù khe đỉnh 5 mm (khung 316, 23/10) ⇒ kiểm bằng BVH
            # chỉ THÂN/ÁO/ĐẦU: mặt thuộc cánh tay bỏ qua (tay còn tư thế clip cũ, giải lại sau ⇒ đếm vào sẽ đội gỗ lên 9–15 mm)
            dg_ = bpy.context.evaluated_depsgraph_get(); n_ = 0; Tg = []; Tn = []
            for o in nguoi_m + GO:
                oe_ = o.evaluated_get(dg_); me_ = oe_.to_mesh(); M_ = o.matrix_world
                F_ = [tuple(p_.vertices) for p_ in me_.polygons]; t_ = _BT.FromPolygons([M_ @ v.co for v in me_.vertices], F_); oe_.to_mesh_clear()
                (Tg if o in GO else Tn).append((o, t_, F_))
            for _, a_, _ in Tg:
                for o, b_, F_ in Tn:
                    n_ += sum(1 for i_, j_ in a_.overlap(b_) if not any(k in IDX_TAY[o.name] for k in F_[j_]))
            return n_
        for _ in range(10):
            if _chong() == 0: break
            go_v.matrix_world = M4.Translation(V((0, 0, 0.001))) @ go_v.matrix_world; bpy.context.view_layer.update()
        go_v.keyframe_insert("location", frame=f_); KHE_VAI.append(khe_vai())
    print("VAI_TI khe vai↔gỗ mm", round(min(KHE_VAI) * 1000, 1), "…", round(max(KHE_VAI) * 1000, 1))
    # ⑦ TAY KHÔNG XUYÊN GỖ — đo bằng LỚP VỎ THẬT (Boss 23/10 «Tay vẫn chưa nằm trên bề mặt, vẫn bị xuyên qua gỗ. Gỗ chưa có lớp vỏ ko thể xuyên?»).
    # Bản trước đo 1 điểm giữa xương bàn tay + bề dày đoán 2 cm ⇒ báo 0 mm trong khi 325–355 đỉnh lưới tay/cẳng nằm trong gỗ (sâu 66 mm).
    # Giờ: cánh tay = 3 capsule của vỏ thân (bắp/cẳng/bàn, bán kính đo từ skin); khúc gỗ = trụ r + dài thật. Tìm điểm đặt tay + góc khuỷu
    # sao cho CẢ cánh tay ngoài mọi khúc trên MỌI khung; trong các phương án hợp lệ chọn điểm XA VAI nhất (Boss: «đặt vào bề mặt xa nhất»),
    # khuỷu ra ngang (Boss: «cùi chỏ phải ngang với body»). Cửa cuối đo bằng ĐỈNH LƯỚI thật của cả hai cánh tay.
    TAY_GIU = VAI; KHAC = "L" if TAY_GIU == "R" else "R"
    Lu_ = rig.data.bones[f"upperarm_{TAY_GIU}"].length; Lf_ = rig.data.bones[f"forearm_{TAY_GIU}"].length; Lh_ = rig.data.bones[f"hand_{TAY_GIU}"].length
    RC = {x: VO_N[f"{x}_{TAY_GIU}"][2] for x in ("upperarm", "forearm", "hand")}
    # NHÃN LÒNG BÀN TAY đo từ lưới (vo.long_ban_tay; kiểm ở tư thế nghỉ: lòng tay hướng VÀO thân cos 0,89) — thay cho đoán trục lòng tay
    LB = VO.long_ban_tay(rig, [o for o in bpy.data.objects if o.type == "MESH" and o.parent is rig], TAY_GIU); LB_T = V(LB["tam"]); LB_N = V(LB["phap_tuyen"]).normalized()
    print("LONG_BAN_TAY", LB); HA, HB = V(VO_N[f"hand_{TAY_GIU}"][0]), V(VO_N[f"hand_{TAY_GIU}"][1])
    print("VO_TAY bán kính vỏ m", {k: round(v, 3) for k, v in RC.items()})


    def kc_tru_go(A, B, rc, go):   # khe nhỏ nhất capsule AB (bán kính rc) ↔ mọi khúc (trụ có độ dài)
        m_ = 9.0
        for c_, ax_, r_, _ in go:
            L2 = 1.45 * 0.5 * (r_ / 0.10 if False else 1.0)
            for i in range(9):
                p_ = A.lerp(B, i / 8); t_ = max(-0.72, min(0.72, (p_ - c_).dot(ax_))); m_ = min(m_, (p_ - (c_ + ax_ * t_)).length - r_ - rc)
        return m_


    def pose_tay(S_, q_, Rq, phi, ngoai):   # IK giải tích: lòng tay q_, xoay bàn Rq, khuỷu = hướng ngang xoay phi quanh trục vai→cổ tay
        Wt = q_ - (Rq @ LB_T); dv = Wt - S_   # cổ tay = tâm lòng tay (nhãn) lùi về đầu xương
        if dv.length > 0.97 * (Lu_ + Lf_): return None
        dl = dv.length; u_ = dv.normalized(); a_ = (Lu_ * Lu_ - Lf_ * Lf_ + dl * dl) / (2 * dl); r_ = math.sqrt(max(0.0, Lu_ * Lu_ - a_ * a_))
        pole = mathutils.Quaternion(u_, math.radians(phi)) @ (ngoai + V((0, 0, -0.6))); v_ = (pole - u_ * pole.dot(u_)).normalized()   # dáng chữ T ôm vào: khuỷu RA NGOÀI + XUỐNG
        E_ = S_ + u_ * a_ + v_ * r_; Mh = M4.Translation(Wt) @ Rq.to_4x4()
        return E_, Wt, [(S_, E_, RC["upperarm"]), (E_, Wt, RC["forearm"]), (Mh @ HA, Mh @ HB, RC["hand"])]


    sc.frame_set(f_giua); bpy.context.view_layer.update(); Wg = go_v.matrix_world.copy(); ph_ = rig.pose.bones[f"hand_{TAY_GIU}"]
    S0 = rig.matrix_world @ rig.pose.bones[f"upperarm_{TAY_GIU}"].head; lb0 = rig.matrix_world @ ((ph_.head + ph_.tail) / 2)
    cg_ = min(bo_go(), key=lambda x: ((lb0 - x[0]) - x[1] * (lb0 - x[0]).dot(x[1])).length)
    n0_ = ((lb0 - cg_[0]) - cg_[1] * (lb0 - cg_[0]).dot(cg_[1])).normalized(); Mh0 = (rig.matrix_world @ ph_.matrix).to_3x3().normalized()
    k_long = max((0, 2), key=lambda k: abs(Mh0.col[k].dot(-n0_))); s_long = 1 if Mh0.col[k_long].dot(-n0_) > 0 else -1


    def xoay_om(q_, n_, ax_, S_):   # Boss 23/10: lòng tay (nhãn) ÁP VÀO gỗ từ NGOÀI vào (= −n); ngón tay (trục Y xương) chĩa LÊN theo tiếp tuyến
        t_ = ax_.cross(n_).normalized()
        if t_.z < 0: t_ = -t_
        A_l = mathutils.Matrix((LB_N, V((0, 1, 0)), LB_N.cross(V((0, 1, 0))))).transposed()
        A_w = mathutils.Matrix((-n_, t_, (-n_).cross(t_))).transposed()
        return A_w @ A_l.inverted()


    # khung mẫu (mỗi 4 khung): khung gỗ, vai, hướng ngoài thân
    MS = []
    for f_ in range(F_HIEN, F_END + 1, 4):
        sc.frame_set(f_); bpy.context.view_layer.update(); W2 = rig.matrix_world; P2 = rig.pose.bones
        ng_ = (W2 @ P2[f"upperarm_{TAY_GIU}"].head) - (W2 @ P2[f"upperarm_{KHAC}"].head); ng_.z = 0
        MS.append((go_v.matrix_world.copy(), W2 @ P2[f"upperarm_{TAY_GIU}"].head, ng_.normalized(), bo_go()))
    sc.frame_set(f_giua); bpy.context.view_layer.update(); go_g = bo_go()
    truc_vai = (S0 - go_g[0][0]).dot(go_g[0][1])
    def tim_cho_tay():
        """Boss 23/10 «T shape với body - đặt 3 khúc gỗ lên - tay ôm vô lại - mặt bàn tay phải áp vào gỗ đối diện từ ngoài vào»:
        điểm khoá trên MẶT NGOÀI bó gỗ (pháp tuyến ra ngang khỏi thân, cos ≥ 0,6), tâm lòng tay cách mặt gỗ 3 mm; cả cánh tay ngoài mọi khúc
        (capsule bàn tay chỉ được chạm khúc ĐANG ÁP); mọi khung trong tầm; khuỷu ra ngoài. Chọn điểm NGOÀI NHẤT rồi góc khuỷu nhỏ nhất."""
        tot = None; thu_ = 0; ng0 = MS[len(MS) // 2][2]
        for ix_, (c_, ax_, r_, _) in enumerate(go_g):
            e1 = ax_.orthogonal().normalized(); e2 = ax_.cross(e1)
            for dt_ in (0.0, 0.10, 0.20, 0.30):
                for k_ in range(36):
                    n_ = e1 * math.cos(2 * math.pi * k_ / 36) + e2 * math.sin(2 * math.pi * k_ / 36)
                    nh_ = n_.copy(); nh_.z = 0
                    if nh_.length < 1e-3 or n_.dot(ng0) < 0.6: continue
                    for sgn in ((1,) if dt_ == 0 else (1, -1)):
                        q_ = c_ + ax_ * (truc_vai + sgn * dt_) + n_ * (r_ + 0.003)
                        if any(((q_ - c2) - a2 * (q_ - c2).dot(a2)).length < r2 + 0.003 - 1e-4 for c2, a2, r2, _ in go_g): continue
                        Rq = xoay_om(q_, n_, ax_, S0); ql = Wg.inverted() @ q_; Rl = Wg.to_3x3().normalized().inverted() @ Rq
                        for phi in (0, -20, 20, -40, 40):
                            ok_ = True; thu_ += 1
                            for Mg_, Sg_, ng_, go_ in MS:
                                r3 = pose_tay(Sg_, Mg_ @ ql, Mg_.to_3x3().normalized() @ Rl, phi, ng_)
                                if r3 is None: ok_ = False; break
                                E_, Wt_, caps = r3
                                khe_ = min(kc_tru_go(A_, B_, rc_, [g for j2, g in enumerate(go_) if not (j_ == 2 and j2 == ix_)]) for j_, (A_, B_, rc_) in enumerate(caps))
                                if khe_ < -0.002: ok_ = False; break
                                kh_ = E_ - (Sg_ + Wt_) / 2; kh_.z = 0
                                if kh_.length > 1e-3 and kh_.normalized().dot(ng_) < 0.5: ok_ = False; break
                            if ok_:
                                diem = (round(n_.dot(ng0), 2), -abs(phi))
                                if tot is None or diem > tot[0]: tot = (diem, q_, n_, Rq, phi)
                                break
        return tot, thu_


    tot, thu_ = tim_cho_tay()
    if tot is None: raise SystemExit("⛔ không có chỗ áp lòng tay lên MẶT NGOÀI bó gỗ mà cả cánh tay ngoài vỏ gỗ")
    (xa_, _), q_, n_, Rh_moi, PHI = tot
    P_KHOA = Wg.inverted() @ q_; R_KHOA = Wg.to_3x3().normalized().inverted() @ Rh_moi
    print("TAY_KHOA thử", thu_, "phương án · mặt ngoài cos", xa_, "· góc khuỷu", PHI, "°")


    def ik_tay(b, P_long, Rh, phi):
        W2 = rig.matrix_world; P2 = rig.pose.bones; pu, pf, ph = P2[f"upperarm_{b}"], P2[f"forearm_{b}"], P2[f"hand_{b}"]
        S_ = W2 @ pu.head; ngoai = (W2 @ pu.head) - (W2 @ P2[f"upperarm_{'L' if b == 'R' else 'R'}"].head); ngoai.z = 0; ngoai.normalize()
        if os.environ.get("KHUYU_THU") == "truoc": ngoai = ngoai.cross(V((0, 0, 1))) * (1 if b == "L" else -1)   # thử ngược cửa ⑨
        r3 = pose_tay(S_, P_long, Rh, phi, ngoai)
        if r3 is None:   # ngoài tầm (không nên xảy ra: đã kiểm mọi khung mẫu) ⇒ duỗi hết về phía đích
            Wt = P_long - (Rh @ LB_T); u_ = (Wt - S_).normalized(); E_ = S_ + u_ * Lu_; Wt = S_ + u_ * (Lu_ + Lf_ - 1e-4)
        else: E_, Wt, _ = r3
        for pb_, d_ in ((pu, E_ - S_), (pf, Wt - E_)):
            M0 = (W2 @ pb_.matrix).to_3x3().normalized(); qd = M0.col[1].rotation_difference(d_.normalized())
            m = (W2.inverted().to_3x3() @ (qd.to_matrix() @ M0)).to_4x4(); m.translation = pb_.matrix.translation; pb_.matrix = m; bpy.context.view_layer.update()
        mh = (W2.inverted().to_3x3() @ Rh).to_4x4(); mh.translation = ph.matrix.translation; ph.matrix = mh; bpy.context.view_layer.update()
        return E_, S_, ngoai


    def ho_tay_khac():   # tay rảnh: capsule bàn/cẳng ↔ gỗ; lún ⇒ hướng đẩy
        W2 = rig.matrix_world; P2 = rig.pose.bones; go_ = bo_go(); day_ = V(); m_ = 9.0
        for x in ("forearm", "hand"):
            pb = P2[f"{x}_{KHAC}"]; A_, B_ = W2 @ pb.head, W2 @ pb.tail; rc_ = VO_N[f"{x}_{KHAC}"][2]
            for c_, ax_, r_, _ in go_:
                for i in range(5):
                    p_ = A_.lerp(B_, i / 4); t_ = max(-0.72, min(0.72, (p_ - c_).dot(ax_))); d_ = p_ - (c_ + ax_ * t_); g_ = d_.length - r_ - rc_
                    m_ = min(m_, g_)
                    if g_ < 0: day_ += d_.normalized() * (-g_ + 0.003)
        return m_, day_


    body_ = next(o for o in rig.children if o.name.startswith("BODY")); nh_ = {g_.index: g_.name for g_ in body_.vertex_groups}
    idx_ban = [v.index for v in body_.data.vertices if any(nh_[e.group] == f"hand_{TAY_GIU}" and e.weight >= 0.5 for e in v.groups)]
    go_tx = min(range(len(go_g)), key=lambda i: ((q_ - go_g[i][0]) - go_g[i][1] * (q_ - go_g[i][0]).dot(go_g[i][1])).length)   # khúc tay đang đỡ


    def khe_ban_tay():   # khe THẬT: đỉnh lưới bàn tay ↔ mặt khúc đang đỡ (dương = hở, âm = lún)
        dg_ = bpy.context.evaluated_depsgraph_get(); be_ = body_.evaluated_get(dg_); me_ = be_.to_mesh(); Mb_ = body_.matrix_world
        c_, ax_, r_, _ = bo_go()[go_tx]; m_ = 9.0
        for i in idx_ban:
            p_ = Mb_ @ me_.vertices[i].co; t_ = max(-0.72, min(0.72, (p_ - c_).dot(ax_))); m_ = min(m_, (p_ - (c_ + ax_ * t_)).length - r_)
        be_.to_mesh_clear(); return m_


    def chay_tay():
        LK = 0.0; KH = 1.0; KHE = []
        for f_ in range(F_HIEN, F_END + 1):
            sc.frame_set(f_); bpy.context.view_layer.update(); Wg = go_v.matrix_world; ph_ = rig.pose.bones[f"hand_{TAY_GIU}"]
            Rh = Wg.to_3x3().normalized() @ R_KHOA
            for _ in range(2): E_, S_, ngoai = ik_tay(TAY_GIU, Wg @ P_KHOA, Rh, PHI)
            lb = (rig.matrix_world @ ph_.matrix) @ LB_T; LK = max(LK, ((Wg @ P_KHOA) - lb).length)
            giua_ = (S_ + (rig.matrix_world @ ph_.head)) / 2; kh_ = (E_ - giua_); kh_.z = 0
            if kh_.length > 1e-3: KH = min(KH, kh_.normalized().dot(ngoai))
            for _ in range(3):
                g_, day_ = ho_tay_khac()
                if day_.length < 1e-4: break
                H.keo_tay_giu_xoan(rig, KHAC, day_)
            for b in "LR":
                for x_ in ("upperarm", "forearm", "hand"): rig.pose.bones[f"{x_}_{b}"].keyframe_insert("rotation_quaternion", frame=f_)
            KHE.append(khe_ban_tay())
        return LK, KH, KHE


    # vòng 1: khoá theo vỏ capsule (an toàn, nhưng capsule bàn tay phân vị 95 % dày hơn tay thật ⇒ tay HỞ khỏi gỗ — Boss soi 2 góc 23/10)
    LECH_KHOA, KHUYU, KHE1 = chay_tay()
    # vòng 2: dời điểm khoá vào sát mặt gỗ theo khe THẬT nhỏ nhất của lưới bàn tay (chừa 3 mm)
    # vòng 2: lòng tay đo ở tư thế NGHỈ; khi tay biến dạng còn hở ⇒ dời điểm khoá vào theo pháp tuyến đúng bằng khe THẬT nhỏ nhất − 3 mm
    P_KHOA = P_KHOA - (Wg.inverted().to_3x3() @ (n_ * (min(KHE1) - 0.003)))
    LECH_KHOA, KHUYU, KHE2 = chay_tay()
    print("TAY_SAT khe thật lưới bàn tay↔gỗ", round(min(KHE2) * 1000, 1), "…", round(max(KHE2) * 1000, 1), "mm")
    HO_THAT = max(KHE2)
    if False:
      for f_ in range(F_HIEN, F_END + 1):
        sc.frame_set(f_); bpy.context.view_layer.update(); Wg = go_v.matrix_world; ph_ = rig.pose.bones[f"hand_{TAY_GIU}"]
        Rh = Wg.to_3x3().normalized() @ R_KHOA
        for _ in range(2): E_, S_, ngoai = ik_tay(TAY_GIU, Wg @ P_KHOA, Rh, PHI)
        lb = rig.matrix_world @ ((ph_.head + ph_.tail) / 2); LECH_KHOA = max(LECH_KHOA, ((Wg @ P_KHOA) - lb).length)
        giua_ = (S_ + (rig.matrix_world @ ph_.head)) / 2; kh_ = (E_ - giua_); kh_.z = 0
        if kh_.length > 1e-3: KHUYU = min(KHUYU, kh_.normalized().dot(ngoai))
        for _ in range(3):
            g_, day_ = ho_tay_khac()
            if day_.length < 1e-4: break
            H.keo_tay_giu_xoan(rig, KHAC, day_)
        for b in "LR":
            for x_ in ("upperarm", "forearm", "hand"): rig.pose.bones[f"{x_}_{b}"].keyframe_insert("rotation_quaternion", frame=f_)
    print("KHUYU_NGANG cos nhỏ nhất (khuỷu·ngoài thân, ngang)", round(KHUYU, 2))
    print("TAY_KHOA lệch điểm khoá lớn nhất mm", round(LECH_KHOA * 1000, 1))
    # CỬA ⑦ bằng ĐỈNH LƯỚI THẬT: mọi đỉnh lưới thân có trọng số ≥ 0,3 ở bắp/cẳng/bàn tay (cả hai tay) phải ngoài mọi khúc gỗ (trụ thật)
    body_ = next(o for o in rig.children if o.name.startswith("BODY"))
    nh_ = {g_.index: g_.name for g_ in body_.vertex_groups}
    CANH_TAY = {f"{x}_{b}" for x in ("upperarm", "forearm", "hand") for b in "LR"}
    idx_tay = [v.index for v in body_.data.vertices if any(nh_[e.group] in CANH_TAY and e.weight >= 0.3 for e in v.groups)]
    xuyen_ = 0.0; dem_max = 0; f_te = None
    for f_ in range(F_HIEN, F_END + 1):
        sc.frame_set(f_); dg_ = bpy.context.evaluated_depsgraph_get(); be_ = body_.evaluated_get(dg_); me_ = be_.to_mesh(); Mb_ = body_.matrix_world
        P_ = [Mb_ @ me_.vertices[i].co for i in idx_tay]; be_.to_mesh_clear(); dem_ = 0
        for c_, ax_, r_, _ in bo_go():
            for p_ in P_:
                t_ = (p_ - c_).dot(ax_)
                if abs(t_) > 0.72: continue
                d_ = ((p_ - c_) - ax_ * t_).length - r_
                if d_ < 0: dem_ += 1; xuyen_ = min(xuyen_, d_)
        if dem_ > dem_max: dem_max, f_te = dem_, f_
    ho_ = HO_THAT
    # ⑦b CHỒNG LẤN BỀ MẶT (BVH) mọi lưới nhân vật ↔ gỗ — bắt cả mặt cắt qua giữa 2 đỉnh (đã hiệu chỉnh: bản xuyên 23/10 = 4 661 cặp, bản sửa = 0)
    from mathutils.bvhtree import BVHTree


    def _bvh(o):
        dg_ = bpy.context.evaluated_depsgraph_get(); oe_ = o.evaluated_get(dg_); me_ = oe_.to_mesh(); M_ = o.matrix_world
        t_ = BVHTree.FromPolygons([M_ @ v.co for v in me_.vertices], [tuple(p.vertices) for p in me_.polygons]); oe_.to_mesh_clear(); return t_


    nguoi_ = [o for o in bpy.data.objects if o.type == "MESH" and o.parent is rig]; BVH_CHONG = 0
    for f_ in range(F_HIEN, F_END + 1, 2):
        sc.frame_set(f_); B_ = [_bvh(o) for o in nguoi_]
        for o in GO:
            bl_ = _bvh(o); BVH_CHONG += sum(len(bl_.overlap(b_)) for b_ in B_)
    print("TAY_BVH cặp mặt chồng lấn người↔gỗ", BVH_CHONG)
    print("TAY_GO đỉnh lưới cánh tay", len(idx_tay), "· đỉnh trong gỗ nhiều nhất", dem_max, "(khung", f_te, ") · sâu nhất mm", round(xuyen_ * 1000, 1))
    # ⑥ GỖ KHÔNG XUYÊN ĐẦU trên mọi khung gỗ đã hiện (mm, âm = xuyên)
    xd_ = 9.0
    for f_ in range(F_VAC + HOA - 4, F_END + 1):
        sc.frame_set(f_); bpy.context.view_layer.update()
        for o in GO: R_ = o.matrix_world.to_3x3(); xd_ = min(xd_, kc_dau(o.matrix_world.translation, (R_ @ zl).normalized()) - rk - R_DAU)
    CUA["6_go_cach_dau_mm"] = round(xd_ * 1000, 1); CUA["7_khe_that_ban_tay_mm"] = [round(min(KHE2) * 1000, 1), round(max(KHE2) * 1000, 1)]   # lưới bàn tay ↔ mặt gỗ: −3…10 mm (không xuyên, không lơ lửng)
    CUA["10_khe_vai_go_mm"] = [round(min(KHE_VAI) * 1000, 1), round(max(KHE_VAI) * 1000, 1)]; CUA["7b_bvh_chong_lan"] = BVH_CHONG; CUA["7_tay_xuyen_go_mm"] = round(xuyen_ * 1000, 1); CUA["7_dinh_tay_trong_go"] = dem_max; CUA["7_tay_giu_ho_go_mm"] = round(ho_ * 1000, 1)
    CUA["8_lech_vai_mm"] = round(max(map(abs, ls2)) * 1000, 1)
    CUA["9_khuyu_ngang_cos"] = round(KHUYU, 2); CUA["7_lech_diem_khoa_mm"] = round(LECH_KHOA * 1000, 1)
    CUA["dat"] = bool(xd_ >= 0 and xuyen_ >= -0.003 and min(KHE2) >= -0.003 and max(KHE2) <= 0.010 and BVH_CHONG == 0 and min(KHE_VAI) >= -0.003 and max(KHE_VAI) <= 0.008 and ho_ <= 0.04 and CUA["8_lech_vai_mm"] <= 60 and CUA["9_khuyu_ngang_cos"] >= 0.5 and CUA["7_lech_diem_khoa_mm"] <= 10); print("CUA_GO_DAU", CUA["6_go_cach_dau_mm"])
    return GO, CUA

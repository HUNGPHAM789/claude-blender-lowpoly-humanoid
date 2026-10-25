"""LAS physics (Boss 22/10/2026: «Cây ngã physics phải hay - giờ là physics skill cho project LAS»). Blender 5.2 bpy.

Công thức chung cho vật ĐỔ có bản lề (cây ngã, cột đổ, cửa sập, tủ đổ):
  pha 1  BẢN LỀ GIẢI TÍCH — tích phân RK4 đúng phương trình  I_h·θ'' = a·((c−h) × m·g)  (khối lượng/quán tính đo từ LƯỚI, mật độ theo bộ phận),
  pha 2  BULLET — tắt «animated» ở khung thả: Bullet NHẬN vận tốc của pha 1 (đo 22/10: 1,200 → 1,197 rad/s), lo va đất / nảy / lăn / dừng,
  rồi nướng ra keyframe (deterministic, mờ dần được). Cửa đo `cua_do()` — exit 1 nếu trượt.
⚠️ Bullet lấy GỐC VẬT làm TRỌNG TÂM ⇒ `dat_goc_trong_tam()` trước khi bật rigid body.
"""
import math
import bpy, mathutils, numpy as np
from mathutils.bvhtree import BVHTree

V = mathutils.Vector; M4 = mathutils.Matrix
G = np.array((0.0, 0.0, -9.81))
_C = np.array([[2, 1, 1], [1, 2, 1], [1, 1, 2]]) / 120.0


def _tam_giac(obj):
    dg = bpy.context.evaluated_depsgraph_get(); oe = obj.evaluated_get(dg); me = oe.to_mesh(); me.calc_loop_triangles()
    Mw = obj.matrix_world; P = np.array([tuple(Mw @ v.co) for v in me.vertices]); T = np.array([tuple(t.vertices) for t in me.loop_triangles])
    oe.to_mesh_clear(); return P, T


def khoi_luong(phan):
    """phan = [(obj, mật độ kg/m³), …] ⇒ (m, trọng tâm c (3,), tensor quán tính quanh c (3×3)) — tứ diện có dấu, toạ độ thế giới."""
    m = 0.0; S1 = np.zeros(3); C = np.zeros((3, 3))
    for obj, rho in phan:
        P, T = _tam_giac(obj)
        a, b, c = P[T[:, 0]], P[T[:, 1]], P[T[:, 2]]; d = np.einsum("ij,ij->i", a, np.cross(b, c))   # 6·thể tích có dấu
        m += rho * d.sum() / 6; S1 += rho * (d[:, None] * (a + b + c)).sum(0) / 24
        A = np.stack([a, b, c], axis=2)   # (n,3,3) cột = đỉnh
        C += rho * np.einsum("n,nij,jk,nlk->il", d, A, _C, A)
    c_ = S1 / m; Cc = C - m * np.outer(c_, c_)
    return m, c_, np.trace(Cc) * np.eye(3) - Cc


def dat_goc_trong_tam(obj, c):
    """dời gốc vật về trọng tâm c (thế giới), hình không đổi."""
    Mi = obj.matrix_world.inverted(); cl = Mi @ V(c); obj.data.transform(M4.Translation(-cl)); obj.matrix_world = obj.matrix_world @ M4.Translation(cl)


def rung_tat_dan(obj, tam, truc, f0, bien_do_deg, fps, tan_so=2.2, tau=0.35, so_khung=30, M0=None, pha=0.0):
    """rung tắt dần quanh trục qua `tam` (cú chặt trúng): θ(t) = A·e^(−t/τ)·sin(2πft+pha). Ghi key ma trận (giữ M0 làm gốc)."""
    M0 = M0 or obj.matrix_world.copy(); tam = V(tam); truc = V(truc).normalized(); out = []
    for k in range(so_khung + 1):
        t = k / fps; th = math.radians(bien_do_deg) * math.exp(-t / tau) * math.sin(2 * math.pi * tan_so * t + pha)
        obj.matrix_world = M4.Translation(tam) @ M4.Rotation(th, 4, truc) @ M4.Translation(-tam) @ M0
        obj.keyframe_insert("location", frame=f0 + k); obj.keyframe_insert("rotation_quaternion", frame=f0 + k); out.append(th)
    obj.matrix_world = M0; obj.keyframe_insert("location", frame=f0 + so_khung + 1); obj.keyframe_insert("rotation_quaternion", frame=f0 + so_khung + 1)
    return out


def omega_toi_thieu(m, c, I, h, a):
    """vận tốc góc nhỏ nhất để trọng tâm vượt qua đỉnh quanh bản lề (vật đang nghiêng NGƯỢC chiều đổ): ½·I_h·ω² = m·g·Δz."""
    a = np.asarray(a) / np.linalg.norm(a); r = c - h; rp = r - a * (r @ a); Ih = a @ I @ a + m * (rp @ rp)
    dz = np.linalg.norm(rp) - rp[2]   # trọng tâm lên tới thẳng đứng trên bản lề
    return math.sqrt(max(0.0, 2 * m * 9.81 * dz / Ih)), Ih


def nga_ban_le(obj, m, c, I, h, a, f0, fps, omega0, theta_tha, buoc=20, f_max=240):
    """pha 1: quay quanh bản lề h, trục a (θ>0 = đổ theo chiều a × …) — RK4, key mỗi khung tới khi θ ≥ theta_tha. Trả (khung thả, θ, ω, [θ])."""
    a = np.asarray(a, float) / np.linalg.norm(a); r0 = np.asarray(c) - np.asarray(h); rp = r0 - a * (r0 @ a); Ih = a @ I @ a + m * (rp @ rp)
    def R(th):
        K = np.array([[0, -a[2], a[1]], [a[2], 0, -a[0]], [-a[1], a[0], 0]]); return np.eye(3) + math.sin(th) * K + (1 - math.cos(th)) * K @ K
    def acc(th): return a @ np.cross(R(th) @ r0, m * G) / Ih
    M0 = obj.matrix_world.copy(); th, w = 0.0, omega0; dt = 1 / (fps * buoc); f_tha_ = None; hv = V(tuple(h)); av = V(tuple(a)); TH = []
    for k in range(f_max):
        obj.matrix_world = M4.Translation(hv) @ M4.Rotation(th, 4, av) @ M4.Translation(-hv) @ M0
        obj.keyframe_insert("location", frame=f0 + k); obj.keyframe_insert("rotation_quaternion", frame=f0 + k); TH.append(th)
        if th >= theta_tha and f_tha_ is None: f_tha_, th_tha_, w_tha_ = f0 + k, th, w
        if f_tha_ is not None and f0 + k >= f_tha_ + 2: return f_tha_, th_tha_, w_tha_, TH
        # ⚠️ key THÊM 2 khung qua khung thả: Bullet lấy vận tốc vật kinematic từ chuyển động TRONG các bước con tới khung tắt
        # (key dừng đúng khung thả ⇒ bước con đứng yên ⇒ ω tụt 0,757 → 0,179, đo 22/10)
        for _ in range(buoc):
            k1 = (w, acc(th)); k2 = (w + dt / 2 * k1[1], acc(th + dt / 2 * k1[0])); k3 = (w + dt / 2 * k2[1], acc(th + dt / 2 * k2[0])); k4 = (w + dt * k3[1], acc(th + dt * k3[0]))
            th += dt / 6 * (k1[0] + 2 * k2[0] + 2 * k3[0] + k4[0]); w += dt / 6 * (k1[1] + 2 * k2[1] + 2 * k3[1] + k4[1])
    raise RuntimeError("nga_ban_le: không tới góc thả — ω0 quá nhỏ (vật đứng lại)")


def bullet_tiep(obj, f_tha, f_het, tinh, m, ma_sat=0.8, nay=0.1, giam=(0.05, 0.12), giam_sau_cham=None):
    """pha 2: obj ACTIVE (convex hull), animated tới f_tha rồi tắt ⇒ Bullet nhận vận tốc; `tinh` = vật PASSIVE (mesh). Nướng ra keyframe."""
    sc = bpy.context.scene
    assert giam[1] < 0.95, "angular_damping ≥ 0,95 ⇒ Bullet xoá gần hết ω mỗi giây — vật không đổ (đo 22/10: ω 0)"
    if sc.rigidbody_world is None: bpy.ops.rigidbody.world_add()
    w = sc.rigidbody_world; w.point_cache.frame_start = sc.frame_start; w.point_cache.frame_end = f_het; w.substeps_per_frame = 20; w.solver_iterations = 30
    for o in tinh:
        bpy.ops.object.select_all(action="DESELECT"); o.select_set(True); bpy.context.view_layer.objects.active = o; bpy.ops.rigidbody.object_add(type="PASSIVE")
        # ⚠️ PASSIVE nhỏ (gốc cây, bậc, hộp) = CONVEX_HULL đặc; MESH = vỏ tam giác mỏng ⇒ đáy vật lún 1 chút là lọt qua (đo 22/10: cây tụt 0,6 m xuyên gốc)
        o.rigid_body.collision_shape = "MESH" if max(o.dimensions) > 20 else "CONVEX_HULL"; o.rigid_body.friction = ma_sat; o.rigid_body.restitution = nay; o.rigid_body.collision_margin = 0.002
    bpy.ops.object.select_all(action="DESELECT"); obj.select_set(True); bpy.context.view_layer.objects.active = obj; bpy.ops.rigidbody.object_add(type="ACTIVE")
    rb = obj.rigid_body; rb.collision_shape = "CONVEX_HULL"; rb.mass = m; rb.friction = ma_sat; rb.restitution = nay; rb.linear_damping, rb.angular_damping = giam
    rb.collision_margin = 0.002; rb.use_deactivation = False
    rb.kinematic = True; rb.keyframe_insert("kinematic", frame=f_tha); rb.kinematic = False; rb.keyframe_insert("kinematic", frame=f_tha + 1)
    if __import__("os").environ.get("IN_RB"):
        for o in w.collection.objects: print("RB", o.name, o.rigid_body.type, o.rigid_body.collision_shape, [round(x, 2) for x in o.dimensions], [round(x, 2) for x in o.matrix_world.translation], len(o.data.polygons))
    bpy.ops.ptcache.bake_all(bake=True)
    if giam_sau_cham:   # GIẢM CHẤN SAU CHẠM ĐẤT (23/10: tán tròn lăn 6–11 mm/khung; giảm chấn cao suốt ⇒ hụt ω nối pha 20 %): lượt 1 tìm khung chạm, lượt 2 key giảm chấn
        f_cham = None
        for f in range(f_tha, f_het + 1):
            sc.frame_set(f); P, _ = _tam_giac(obj)
            if P[:, 2].min() <= 0.03: f_cham = f; break
        if f_cham:
            bpy.ops.ptcache.free_bake_all()
            for f, (l_, a_) in ((f_cham, giam), (f_cham + 3, giam_sau_cham)):
                rb.linear_damping, rb.angular_damping = l_, a_; rb.keyframe_insert("linear_damping", frame=f); rb.keyframe_insert("angular_damping", frame=f)
            bpy.ops.ptcache.bake_all(bake=True); print("BULLET giảm chấn sau chạm đất từ khung", f_cham + 3, giam_sau_cham)
    MW = {}
    for f in range(f_tha, f_het + 1): sc.frame_set(f); MW[f] = obj.matrix_world.copy()
    bpy.ops.ptcache.free_bake_all()
    for o in tinh + [obj]:
        bpy.ops.object.select_all(action="DESELECT"); o.select_set(True); bpy.context.view_layer.objects.active = o; bpy.ops.rigidbody.object_remove()
    for f, M in MW.items():
        obj.matrix_world = M; obj.keyframe_insert("location", frame=f); obj.keyframe_insert("rotation_quaternion", frame=f)
    return MW


def cua_do(obj, f0, f_tha, f_het, huong, nguoi=None, omega_tha=None, fps=24, a=None):
    """CỬA vật lý (exit 1 ở nơi gọi nếu kq['dat'] False):
    ① lún đất ≥ −20 mm · ② đứng yên 12 khung cuối (trọng tâm < 4 mm/khung, xoay < 0,6°/frames) · ③ đổ đúng hướng (dời trọng tâm · huong ≥ 0,8)
    ④ không đè người (BVH chồng lấn = 0 khung) · ⑤ nối pha: ω Bullet 2 khung sau thả lệch ω giải tích ≤ 20 %."""
    sc = bpy.context.scene; kq = {}; zmin = 9.0; C = {}; Q = {}; cham = []
    for f in range(f0, f_het + 1):
        sc.frame_set(f); P, _ = _tam_giac(obj); zmin = min(zmin, P[:, 2].min()); C[f] = obj.matrix_world.translation.copy(); Q[f] = obj.matrix_world.to_quaternion()
        if nguoi is not None and f <= f_het:
            Pa, Ta = _tam_giac(obj); Pb, Tb = _tam_giac(nguoi)
            if BVHTree.FromPolygons([V(p) for p in Pa], [tuple(t) for t in Ta]).overlap(BVHTree.FromPolygons([V(p) for p in Pb], [tuple(t) for t in Tb])): cham.append(f)
    kq["1_lun_dat_mm"] = round(zmin * 1000, 1)
    cuoi = range(f_het - 11, f_het + 1)
    kq["2_troi_cuoi_mm"] = round(max((C[f] - C[f - 1]).length for f in cuoi) * 1000, 2)
    kq["2_xoay_cuoi_deg"] = round(max(math.degrees(Q[f - 1].rotation_difference(Q[f]).angle) for f in cuoi), 2)
    d = C[f_het] - C[f0]; d.z = 0; kq["3_huong_cos"] = round(d.normalized().dot(V(huong).normalized()), 2) if d.length > 1e-3 else 0.0
    kq["4_de_nguoi_khung"] = cham[:5]; kq["4_so_khung_de_nguoi"] = len(cham)
    if omega_tha is not None:
        w_ = math.radians(math.degrees(Q[f_tha + 1].rotation_difference(Q[f_tha + 3]).angle)) * fps / 2
        kq["5_omega_giai_tich"] = round(omega_tha, 3); kq["5_omega_bullet"] = round(w_, 3); kq["5_noi_pha_lech_pct"] = round(abs(w_ - omega_tha) / max(1e-6, omega_tha) * 100, 1)
    kq["1_lun_dat_mm"] = float(kq["1_lun_dat_mm"])
    kq["dat"] = bool(kq["1_lun_dat_mm"] >= -20 and kq["2_troi_cuoi_mm"] < 4 and kq["2_xoay_cuoi_deg"] < 0.6 and kq["3_huong_cos"] >= 0.8 \
        and kq["4_so_khung_de_nguoi"] == 0 and kq.get("5_noi_pha_lech_pct", 0) <= 20)
    return kq

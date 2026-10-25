"""Sinh 6 clip JSON (nguồn sự thật) cho settler từ bảng spec (spec/tra1.md, ChatGPT 22/10/2026).
Góc theo trục GIẢI PHẪU (xem humanoid_anim.py). Rig bind = A-pose tay dạng ~20° ⇒ dạng vai ghi = (giá trị spec − 20).
Chạy: python3 make_clips.py <thư mục clips>"""
import json, os, sys

OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(__file__), "..", "assets", "clips")
A0 = 20.0   # dạng vai của tư thế bind


def tay(S, abd, E=None, tw=0.0):   # E (khuỷu) ghi riêng ở forearm
    return {"flex": S, "abd": abd - A0, "twist": tw}


def than(yaw=0, pitch=0, roll=0, w=1.0):
    return {"yaw": yaw * w, "pitch": pitch * w, "roll": roll * w}


def chia_than(keys):
    """thân: 40 % spine, 60 % chest (spec §3)."""
    return {"spine": {f: than(*v, w=0.4) for f, v in keys.items()}, "chest": {f: than(*v, w=0.6) for f, v in keys.items()}}


def khuyu(keys): return {f: {"flex": e} for f, e in keys.items()}


def dich(keys, d, N):
    return {(f + d) % N if (f + d) % N or f + d == 0 else N: v for f, v in keys.items()} | ({N: keys[min(keys)]} if True else {})


def chu_ky(keys, N):
    """đảm bảo khoá N = khoá 0 (vòng lặp)."""
    k = {f: v for f, v in keys.items()}; k[N] = k[0]; return k


clips = {}

# ---------------- IDLE 72
N = 72
clips["idle"] = dict(id="idle", end_frame=N, loop=True, root=dict(mode="stationary"),
    gait=dict(contacts={"L": dict(on=0, off=N), "R": dict(on=0, off=N)}, swing_h_m=0.0),
    hips_drop_mm=2,
    pelvis={0: dict(x_mm=0, z_mm=0), 18: dict(x_mm=8, z_mm=3), 36: dict(x_mm=0, z_mm=0), 54: dict(x_mm=-8, z_mm=3), 72: dict(x_mm=0, z_mm=0)},
    joints={**chia_than({0: (0, 1, 0), 18: (1, 0, -0.5), 36: (0, 1, 0), 54: (-1, 0, 0.5), 72: (0, 1, 0)}),
            "head": {0: than(0, -1, 0), 20: than(-1, 0, 0.5), 38: than(0, -1, 0), 56: than(1, 0, -0.5), 72: than(0, -1, 0)},
            "upperarm_L": {0: tay(2, 7, 0), 36: tay(3, 7.5, 0), 72: tay(2, 7, 0)}, "upperarm_R": {0: tay(2, 7, 0), 36: tay(3, 7.5, 0), 72: tay(2, 7, 0)},
            "forearm_L": khuyu({0: 12, 18: 13, 36: 12, 54: 13, 72: 12}), "forearm_R": khuyu({0: 12, 18: 13, 36: 12, 54: 13, 72: 12})},
    props=[dict(asset="riu", ben="R", huong=[0, 0, -1]), dict(asset="gio_berry", ben="L", huong=[0, 0, 1])],
    events=[], requirements=dict(tay_xe_mm=15))

# ---------------- WALK 26 @ 1.2 m/s (nghiên cứu 22/10: 24 khung = 120 bước/phút quá nhanh; 26 khung ≈ 111; toe-off 62 %; nghiêng chậu ±3,5°)
N = 26
vai_L = {0: -18, 6.5: 0, 13: 22, 19.5: 0, 26: -18}; khu_L = {0: 12, 6.5: 18, 13: 28, 19.5: 18, 26: 12}
vai_R = chu_ky({(f + 13) % N: v for f, v in vai_L.items() if f != N}, N); khu_R = chu_ky({(f + 13) % N: v for f, v in khu_L.items() if f != N}, N)
clips["walk"] = dict(id="walk", end_frame=N, loop=True, root=dict(mode="root_motion", speed_mps=1.20),
    gait=dict(contacts={"L": dict(on=0, off=16, heel_rise=9), "R": dict(on=13, off=29, heel_rise=22)}, swing_h_m=0.075, toe_off_deg=22, width_extra_m=-0.022),
    hips_drop_mm=12,
    pelvis={0: dict(z_mm=0, x_mm=0, yaw=5), 2: dict(z_mm=-20, x_mm=10, yaw=3), 6.5: dict(z_mm=5, x_mm=25, yaw=0, roll=-3.5), 8: dict(z_mm=20, x_mm=22, yaw=-1),
            13: dict(z_mm=0, x_mm=0, yaw=-5), 15: dict(z_mm=-20, x_mm=-10, yaw=-3), 19.5: dict(z_mm=5, x_mm=-25, yaw=0, roll=3.5), 21: dict(z_mm=20, x_mm=-22, yaw=1),
            26: dict(z_mm=0, x_mm=0, yaw=5)},
    joints={**chia_than({0: (-8, 3, 0), 6.5: (0, 3, 1.5), 13: (8, 3, 0), 19.5: (0, 3, -1.5), 26: (-8, 3, 0)}),
            "upperarm_L": {f: tay(v, 8, 0) for f, v in vai_L.items()}, "forearm_L": khuyu(khu_L),
            "upperarm_R": {f: tay(v * 0.6, 10, 0) for f, v in vai_R.items()}, "forearm_R": khuyu({f: v + 6 for f, v in khu_R.items()}),
            "head": {0: than(4, -3, 0), 13: than(-4, -3, 0), 26: than(4, -3, 0)}},
    props=[dict(asset="riu", ben="R", huong=[0, 0, -1])], events=[dict(frame=0, name="contact_L"), dict(frame=13, name="contact_R")],
    requirements=dict(cach_dinh_tay_khung=[12, 14]))

# ---------------- RUN 18 @ 2.5 m/s (chạy chậm: chạm đất 7 khung, bay 2 khung, đỉnh ~9 mm; gối vung ~90°)
N = 18
clips["run"] = dict(id="run", end_frame=N, loop=True, root=dict(mode="root_motion", speed_mps=2.50),
    gait=dict(contacts={"L": dict(on=0, off=7, heel_rise=5), "R": dict(on=9, off=16, heel_rise=14)}, swing_h_m=0.14, toe_off_deg=30, width_extra_m=-0.032),
    hips_drop_mm=28,
    pelvis={0: dict(z_mm=0, yaw=6, x_mm=0), 2: dict(z_mm=-40, yaw=4, x_mm=10), 5: dict(z_mm=-10, yaw=1, x_mm=15), 7: dict(z_mm=6, yaw=-2, x_mm=6), 8: dict(z_mm=9, yaw=-4, x_mm=2),
            9: dict(z_mm=0, yaw=-6, x_mm=0), 11: dict(z_mm=-40, yaw=-4, x_mm=-10), 14: dict(z_mm=-10, yaw=-1, x_mm=-15), 16: dict(z_mm=6, yaw=2, x_mm=-6), 17: dict(z_mm=9, yaw=4, x_mm=-2), 18: dict(z_mm=0, yaw=6, x_mm=0)},
    joints={**chia_than({0: (-10, 9, 0), 9: (10, 9, 0), 18: (-10, 9, 0)}),
            "upperarm_L": {0: tay(-35, 10), 4.5: tay(5, 10), 9: tay(45, 10), 13.5: tay(5, 10), 18: tay(-35, 10)},
            "upperarm_R": {0: tay(45 * 0.7, 12), 4.5: tay(5, 12), 9: tay(-35 * 0.7, 12), 13.5: tay(5, 12), 18: tay(45 * 0.7, 12)},
            "forearm_L": khuyu({0: 85, 10: 100, 18: 85}), "forearm_R": khuyu({0: 95, 9: 85, 18: 95}),
            "head": {0: than(5, -6, 0), 9: than(-5, -6, 0), 18: than(5, -6, 0)}},
    props=[dict(asset="riu", ben="R", huong=[0, 0, -1])], events=[], requirements=dict(bay_khung=[1.5, 2.5]))

# ---------------- CHOP 48 (đứng yên, chân trước-sau)
N = 48
T = {0: (-5, 5, 0), 6: (-20, 2, -3), 14: (-33, -8, -3), 18: (-36, -10, -2), 21: (-10, 0, 0), 24: (20, 18, 2), 26: (24, 22, 2), 29: (18, 15, 1), 35: (5, 10, 0), 42: (-5, 5, 0), 48: (-5, 5, 0)}
R = {0: (35, 20, 65), 6: (55, 25, 85), 14: (160, 25, 70), 18: (165, 20, 75), 21: (135, 20, 60), 24: (65, 15, 25), 26: (65, 15, 30), 29: (70, 18, 40), 35: (50, 20, 70), 42: (35, 20, 65), 48: (35, 20, 65)}
L_ = {0: (0, 22, 75), 14: (10, 25, 85), 24: (-10, 30, 70), 35: (0, 25, 75), 48: (0, 22, 75)}
xd = {0: 0, 6: 5, 14: 20, 18: 22, 21: 18, 24: 5, 26: 5, 29: 8, 35: 12, 42: 3, 48: 0}   # nâng xương đòn khi vung qua đầu
clips["chop"] = dict(id="chop", end_frame=N, loop=True, root=dict(mode="stationary"),
    gait=dict(contacts={"L": dict(on=0, off=N), "R": dict(on=0, off=N)}, swing_h_m=0.0, width_extra_m=0.058, offset={"L": [0, -0.10, 0], "R": [0, 0.10, 0]}),
    hips_drop_mm=30,
    pelvis={max(0, f - 2) if f not in (0, 48) else f: dict(yaw=v[0] * 0.3, z_mm=(-15 if 21 <= f <= 29 else 0), x_mm=(-10 if f in (6, 14, 18) else 15 if f in (24, 26) else 0)) for f, v in T.items()},
    joints={**chia_than(T), "upperarm_R": {f: tay(*v[:2], 0) | {"twist": -25 if 14 <= f <= 18 else 0} for f, v in R.items()},
            "forearm_R": khuyu({f: v[2] for f, v in R.items()}), "upperarm_L": {f: tay(*v[:2]) for f, v in L_.items()}, "forearm_L": khuyu({f: v[2] for f, v in L_.items()}),
            "clavicle_R": {f: {"abd": e} for f, e in xd.items()}, "head": {f: than(-v[0] * 0.5, -v[1] * 0.4, 0) for f, v in T.items()}},
    props=[dict(asset="riu", ben="R", huong=[0, 0, -1])], events=[dict(frame=24, name="hit")], requirements=dict(riu_tren_dinh_m=0.25, dinh_truoc_hit_khung=[4, 10]))

def quat_phang(goc, tam_z=1.20, nghieng=15.0, phi=-155.0, r_tay=0.42, dai=0.67, ha=None, rr=None):
    """độ cao tay & lưỡi nằm TRÊN MỘT MẶT PHẲNG nghiêng qua tâm ngực (cao nhất ở hướng phi): z = tam_z + r·tan(nghiêng)·cos(θ−φ).
    Bản đặt độ cao tay từng khung ⇒ mặt nón, lệch phẳng 52 mm."""
    import math as m
    k = m.tan(m.radians(nghieng)); ha = ha or {}; rr = rr or {}
    # ngoài đoạn chém được HẠ tay (tư thế chờ/test về ngang hông — tay ngang ngực làm cẳng tay trái nằm ngang trước ngực)
    return {f: [t, round(tam_z + rr.get(f, r_tay) * k * m.cos(m.radians(t - phi)) + ha.get(f, 0), 3), round(tam_z + (rr.get(f, r_tay) + dai) * k * m.cos(m.radians(t - phi)) + ha.get(f, 0), 3), rr.get(f, r_tay)] for f, t in goc.items()}


# ---------------- CHOP2 48: HAI TAY, VUNG NGANG từ sau vai phải vào thân cây ngang hông (Boss 22/10: «need two hands chop from side swing in»)
# tay phải dẫn (FK), tay trái bám cán bằng IK (bam_can). Hông dẫn ngực 2 khung, tay trễ ngực 1 khung (ChatGPT vòng 3). Vặn thân lớn như B (~70° tổng).
N = 48
T2 = {0: (-12, 8, 0), 8: (-32, 6, -3), 16: (-48, 4, -6), 19: (-52, 4, -6), 21: (-28, 8, -2), 24: (25, 14, 3), 26: (35, 17, 3), 30: (30, 12, 2), 36: (8, 10, 0), 42: (-8, 8, 0), 48: (-12, 8, 0)}   # thân bám hướng rìu (θ)
R2 = {0: (45, 25, 60, 40), 8: (70, 45, 90, 30), 16: (100, 70, 110, 20), 19: (105, 72, 115, 20), 21: (85, 50, 80, -20), 24: (78, 15, 10, -72),
      26: (76, 12, 15, -72), 30: (70, 18, 40, -40), 36: (55, 22, 55, 45), 42: (45, 25, 60, 40), 48: (45, 25, 60, 40)}
tre = lambda k, d: {min(48, f + d) if f not in (0, 48) else f: v for f, v in k.items()}
clips["chop2"] = dict(id="chop2", end_frame=N, loop=True, root=dict(mode="stationary"),
    gait=dict(contacts={"L": dict(on=0, off=N), "R": dict(on=0, off=N)}, swing_h_m=0.0, width_extra_m=0.08, offset={"L": [0, -0.12, 0], "R": [0, 0.12, 0]}),
    hips_drop_mm=30,
    pelvis={max(0, f - 2) if f not in (0, 48) else f: dict(yaw=v[0] * 0.4, z_mm=(-20 if f == 24 else -30 if f == 26 else -5),
            y_mm=(40 if f in (16, 19) else -60 if f in (24, 26) else 0), x_mm=(-30 if f in (16, 19) else 40 if f in (24, 26) else 0)) for f, v in T2.items()},
    joints={**chia_than(T2), "upperarm_R": tre({f: tay(v[0], v[1]) for f, v in R2.items()}, 1), "forearm_R": tre(khuyu({f: v[2] for f, v in R2.items()}), 1),
            "hand_R": tre({f: {"flex": v[3]} for f, v in R2.items()}, 2),
            "upperarm_L": {0: tay(55, 15), 16: tay(70, 25), 24: tay(75, 10), 48: tay(55, 15)}, "forearm_L": khuyu({0: 70, 16: 100, 24: 30, 48: 70}),
            "head": {f: than(-v[0] * 0.45, -v[1] * 0.3, 0) for f, v in T2.items()}},
    # Boss 22/10 «tay cho cầm đúng vào rìu (2 tay)… rìu nằm ngược chiều lúc vung ra sau… vòng cung mũi rìu đúng hình cánh quạt»
    # ⇒ RÌU LÀ CHỦ: đầu rìu chạy trên mặt quạt quanh ngực (θ: −155° sau vai phải → +35° trước-trái), lưỡi luôn quay theo chiều chém; 2 tay IK theo cán.
    props=[dict(asset="riu_dai", ben="R", huong=[1, 0, 0], dau=[0.12, 0, 0.67], tay=[["R", 0.0], ["L", -0.24]], cua_so_chem=[19, 26],
                quy_dao=dict(tam=[0, -0.05, 1.20], r_tay=0.36, dai=0.67,
                             keys=quat_phang({0: -20, 8: -60, 16: -115, 19: -125, 21: -95, 24: -5, 26: 35, 27: 35, 29: 34.5, 35: 5, 42: -15, 48: -20}, r_tay=0.36, ha={0: -0.08, 8: -0.05, 35: -0.06, 42: -0.08, 48: -0.08}, rr={8: 0.42, 16: 0.46, 19: 0.46, 21: 0.46, 24: 0.48, 26: 0.46, 27: 0.46, 29: 0.46, 35: 0.42})))],
    events=[dict(frame=26, name="hit")], requirements=dict(hit_cao_m=[0.8, 1.35]))

# ---------------- CHOP_MOCAP 24: thân/chân từ mocap (short «Farm Folks», Boss 22/10), RÌU theo cánh quạt canh NHỊP của mẫu:
# đỉnh lấy đà f0 (qua vai phải) → trúng thân cây f6 → giữ f8 → rút, vòng về thấp → lấy đà lại f24. (Hướng cán theo cổ tay MP sai ở f0: 2 tay chụm bị che.)
clips["chop_mocap"] = dict(clips["chop2"]); clips["chop_mocap"]["id"] = "chop_mocap"; clips["chop_mocap"]["end_frame"] = 24
clips["chop_mocap"]["events"] = [dict(frame=6, name="hit")]
clips["chop_mocap"]["them_xoay_nguc"] = {0: -35, 3: -22, 5: -5, 6: 0, 12: 0, 16: -10, 20: -28, 24: -35}   # quay phải lúc lấy đà
# tay phải TRƯỢT xuống cán sát tay trái lúc chém rồi trượt lên lại khi lấy đà (như mẫu f6–f12; giữ cố định ⇒ với 0,60 m > tầm 0,56 m)
clips["chop_mocap"]["props"] = [dict(asset="riu_dai", ben="R", huong=[1, 0, 0], dau=[0.12, 0, 0.67],
    tay=[["R", {0: -0.14, 3: -0.13, 5: -0.14, 6: -0.15, 12: -0.15, 16: -0.12, 20: -0.13, 24: -0.14}], ["L", -0.24]], cua_so_chem=[1, 6], dung_quat_mocap=True, nam_theo_tay_mocap=True, nang_tay={0: 0.38, 2: 0.32, 4: 0.28, 6: 0.28, 8: 0.28, 12: 0.22, 16: 0.18, 20: 0.30, 24: 0.38},
    # mẫu chém CHÉO: đỉnh lấy đà rìu gần dựng đứng trên vai phải, trúng ngang hông trái ⇒ mặt quạt nghiêng 38°, cao nhất ở θ −80 (θ −110 sau vai: tay trái với hụt 112 mm)
    quy_dao=dict(tam=[0, -0.05, 1.42], r_tay=0.46, dai=0.67,
                 keys=quat_phang({0: -80, 3: -45, 5: 10, 6: 30, 8: 29.5, 12: 10, 16: -35, 20: -65, 24: -80}, tam_z=1.42, nghieng=38, phi=-80, r_tay=0.46,
                                 ha={12: -0.10, 16: -0.40, 20: -0.15}, rr={0: 0.44, 3: 0.46, 5: 0.48, 6: 0.48, 8: 0.48, 12: 0.46, 16: 0.46, 20: 0.44, 24: 0.44})))]

# ---------------- CHOP_GVHMR 24: TOÀN THÂN từ mocap GVHMR (SMPL-X, Boss 22/10 «use motion capture to get it and infuse in the rigged model»);
# rìu đặt theo HAI CỔ TAY bắt được (riu_tu_mocap), 2 tay giải tích bám cán — KHÔNG bảng tay/quạt tự chỉnh.
# chu kỳ đo trên dữ liệu GVHMR: đỉnh lấy đà (cổ tay cao nhất) t 0.58 → 1.75 s = 28 khung @24; trúng ≈ t 0.93 → khung 8
clips["chop_gvhmr"] = dict(id="chop_gvhmr", end_frame=28, loop=True, root=dict(mode="stationary"), gait=clips["chop2"]["gait"],
    events=[dict(frame=8, name="hit")], tiep_xuc=["hand_R", "hand_L", "forearm_R", "forearm_L"],
    props=[dict(asset="long_axe_v2", ben="R", huong=[1, 0, 0], dau=[0.19, 0, 0.45], qua_hai_nam=True, cua_so_chem=[1, 8])], doi_nhip=[[0, 0], [2, 3], [8, 6], [12, 11], [28, 28]],   # đổi nhịp: giữ đỉnh lâu hơn, vung 2→8 nén còn 3 khung (Boss 22/10 «make the swing fast… strong swing») · rìu cách điệu cỡ thật (Boss 22/10 «medium bigger axe, stylized») ⇒ RIU_TL=1 NAM_TRAI=-0.21
    requirements=dict(hit_cao_m=[0.55, 0.85], chan_lech_max_deg=35, can_ngang_max_deg=34))   # fit 3D có mốc thân cây: lúc trúng lưỡi ≈ 0,9–1,0 × cao hông (settler hông ~0,75 m), cán 21–24° (+10°)   # mũi chân mẫu xoè 33° (P) / tới 52° (T) so với hông   # đo trên mẫu: lưỡi lúc trúng = 0,55 × cao hông (khung 26–30) ⇒ settler ≈ 0,44 m ± 0,1

# ---------------- CARRY LOG 32 @ 0.75 m/s
N = 32
clips["carry"] = dict(id="carry", end_frame=N, loop=True, root=dict(mode="root_motion", speed_mps=0.75),
    gait=dict(contacts={"L": dict(on=0, off=19, heel_rise=12), "R": dict(on=16, off=35, heel_rise=28)}, swing_h_m=0.06, toe_off_deg=18, width_extra_m=0.008),
    hips_drop_mm=16,
    pelvis={0: dict(z_mm=0, x_mm=15, yaw=3), 4: dict(z_mm=-15, x_mm=25), 8: dict(z_mm=0, x_mm=35), 12: dict(z_mm=12, x_mm=25), 16: dict(z_mm=0, x_mm=15, yaw=-3),
            20: dict(z_mm=-15, x_mm=5), 24: dict(z_mm=0, x_mm=-5), 28: dict(z_mm=12, x_mm=5), 32: dict(z_mm=0, x_mm=15, yaw=3)},
    joints={**chia_than({0: (-4, 6, 5), 16: (4, 6, 5), 32: (-4, 6, 5)}), "clavicle_R": {0: {"abd": 12}, 32: {"abd": 12}},
            "upperarm_R": {0: tay(60, 45), 32: tay(60, 45)}, "forearm_R": khuyu({0: 130, 32: 130}),
            "upperarm_L": {0: tay(-10, 12), 16: tay(10, 12), 32: tay(-10, 12)}, "forearm_L": khuyu({0: 25, 16: 35, 32: 25}),
            "head": {0: than(4, -2, -3), 32: than(4, -2, -3)}},
    props=[dict(asset="khuc_go", che_do="vac")], tiep_xuc=["upperarm_R", "forearm_R", "hand_R"], events=[], requirements=dict())

# ---------------- PUT LOG DOWN 64
N = 64
pz = {0: 0, 8: -20, 16: -30, 24: -60, 36: -200, 44: -285, 48: -300, 52: -285, 60: -80, 64: 0}   # nửa ngồi (nghiên cứu: gối 90–105°, thân 40–45°)
py = {0: 0, 24: 30, 36: 100, 44: 150, 48: 160, 52: 150, 60: 40, 64: 0}
tp = {0: (0, 6, 0), 8: (-5, 8, 0), 16: (-5, 8, 0), 24: (0, 12, 0), 36: (0, 30, 0), 44: (0, 40, 0), 48: (0, 42, 0), 52: (0, 38, 0), 60: (0, 15, 0), 64: (0, 2, 0)}
aR = {0: (65, 35, 110), 8: (70, 30, 105), 16: (85, 25, 100), 24: (80, 22, 95), 36: (55, 20, 80), 44: (35, 18, 55), 48: (35, 18, 55), 52: (20, 20, 40), 60: (15, 15, 30), 64: (2, 7, 12)}
aL = {0: (0, 10, 15), 8: (75, 25, 105), 16: (85, 25, 100), 24: (80, 22, 95), 36: (55, 20, 80), 44: (35, 18, 55), 48: (35, 18, 55), 52: (20, 20, 40), 60: (15, 15, 30), 64: (2, 7, 12)}
clips["put_down"] = dict(id="put_down", end_frame=N, loop=False, root=dict(mode="stationary"),
    gait=dict(contacts={"L": dict(on=0, off=N + 1), "R": dict(on=0, off=N + 1)}, swing_h_m=0.0, width_extra_m=0.058),
    hips_drop_mm=4,
    pelvis={f: dict(z_mm=pz[f], y_mm=py.get(f, 0)) for f in pz},
    joints={**chia_than(tp), "upperarm_R": {f: tay(*v[:2]) for f, v in aR.items()}, "forearm_R": khuyu({f: v[2] for f, v in aR.items()}),
            "upperarm_L": {f: tay(*v[:2]) for f, v in aL.items()}, "forearm_L": khuyu({f: v[2] for f, v in aL.items()}),
            "clavicle_R": {0: {"abd": 12}, 24: {"abd": 4}, 64: {"abd": 0}}, "head": {f: than(0, -v[1] * 0.5, 0) for f, v in tp.items()}},
    props=[dict(asset="khuc_go", che_do="dat", khung=dict(roi_vai=16, cham_dat=48, buong=52), dich=[0, -0.62, 0])],   # xa gối (0,45 m quét qua gối khi ngồi)
    tiep_xuc=["upperarm_R", "forearm_R", "hand_R", "upperarm_L", "forearm_L", "hand_L"],
    events=[dict(frame=48, name="ground"), dict(frame=52, name="release")], requirements=dict())

os.makedirs(OUT, exist_ok=True)
for k, c in clips.items():
    c.update(version=1, rig="settler_lpd", fps=24, reference_height_m=1.75)
    json.dump(c, open(os.path.join(OUT, f"{k}.json"), "w"), indent=1)
print("✅", len(clips), "clip →", os.path.abspath(OUT))

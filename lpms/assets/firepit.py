"""BẾP LỬA trại ~1,5 m ngang (Boss 25/10: thế giới tự nhiên = bộ yukekbyte + thú + settler + firepit). Dựng theo
specs/NATURE_SPEC_yukekbyte.md: vòng 9 hòn đá kiểu «rock, small» (khối méo sắc, yk_da), 3 khúc củi tipi kiểu «log» (yk_vo, đầu cắt yk_go_cat),
nền than yk_than, lửa = 3 nón lệch tâm (yk_lua ngoài, yk_lua_vang trong). Phần lửa tên `lua_*` để game làm bập bùng."""
from lpms_helpers import *
META = dict(ten="firepit", loai="prop", dat=True, ngan_sach=900)
R_VONG = 0.68


def build():
    n = 9; o = [(math.cos(2 * math.pi * k / n), math.sin(2 * math.pi * k / n)) for k in range(n)]
    p = {"than": khoi([(0.52 * c, 0.52 * s, z) for c, s in o for z in (-0.03, 0.03)], "yk_than")}
    for k, (c, s) in enumerate(o):   # đá vòng: như rock small của bộ (dẹt, sắc, chìm 2–3 cm)
        m = khoi_meo((R_VONG * c, R_VONG * s, 0.0), 0.15, "yk_da", seed=60 + k, meo=0.22, n=10, det=(1.15, 1.0, 0.75))
        v = m.vertices.copy(); v[:, 2] = np.maximum(v[:, 2] + 0.06, -0.025); p[f"da_{k}"] = khoi(v, "yk_da")
    for k in range(3):   # củi tipi: thân yk_vo, đầu cắt (chóp trên) yk_go_cat
        a = 2 * math.pi * k / 3 + 0.4; b = (0.40 * math.cos(a), 0.40 * math.sin(a), 0.035); t = (0.06 * math.cos(a), 0.06 * math.sin(a), 0.58)
        p[f"cui_{k}"] = ong(b, t, 0.065, 0.05, "yk_vo", n=7)
        d = np.subtract(t, b); d = d / np.linalg.norm(d)
        p[f"dau_cui_{k}"] = ong(tuple(np.add(t, -0.02 * d)), tuple(np.add(t, 0.03 * d)), 0.05, 0.045, "yk_go_cat", n=7)
    for k, (dx, dy, r, h, mau) in enumerate([(0.0, 0.0, 0.25, 0.92, "yk_lua"), (0.08, -0.05, 0.17, 0.62, "yk_lua"), (-0.03, 0.05, 0.13, 0.70, "yk_lua_vang")]):
        m = non(0.03, h, r, mau, n=6, seed=70 + k, xoay=0.5 * k); m.apply_translation((dx, dy, 0.0)); p[f"lua_{k}"] = m
    return p

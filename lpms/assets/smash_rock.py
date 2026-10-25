"""Đá MỎ để đập bằng cuốc (Boss 23/10: «cảnh đập đá… pickaxe»). Thấp ~0,4 m (cú bổ Kimodo chạm thấp), mặt trên hơi phẳng cho mũi cuốc bổ vào,
khối chính + 2 khối tựa sáng/đậm. Bản vỡ cục làm sau (las-physics)."""
from lpms_helpers import *

META = dict(ten="smash_rock", dat=True, ngan_sach=300)


def build():
    def vui(m, mau):
        v = m.vertices.copy(); v[:, 2] = np.maximum(v[:, 2], -0.02); v[:, 2] = np.minimum(v[:, 2], 0.40); return khoi(v, mau)
    return {"da_chinh": vui(khoi_meo((0, 0, 0.20), 0.36, "da", seed=61, meo=0.18, n=14, det=(1.15, 0.95, 0.75)), "da"),
            "da_tua_a": vui(khoi_meo((0.30, 0.18, 0.08), 0.20, "da_sang", seed=62, meo=0.22, n=10, det=(1, 1, 0.7)), "da_sang"),
            "da_tua_b": vui(khoi_meo((-0.28, -0.20, 0.07), 0.18, "da_sang", seed=63, meo=0.22, n=10, det=(1, 1, 0.65)), "da_sang")}

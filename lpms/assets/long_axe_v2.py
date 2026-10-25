"""Rìu hai tay CÁCH ĐIỆU (Boss 22/10: «medium bigger axe, make it stylized a lil bit not just too simple»).
Hợp đồng cầm: gốc = nắm PHẢI, cán +Z, lưỡi +X (mép mỏng), gáy búa −X. Nắm TRÁI ở z = NAM_TRAI.
Cỡ thật (dùng RIU_TL=1): to hơn riu_dai×0,55 đang dùng ≈ 1,35 lần. Lưỡi trăng khuyết có râu, viền lưỡi sáng, khâu đồng, quấn cán, núm đuôi."""
import math
from lpms_helpers import *

META = dict(ten="long_axe_v2", cam=True, ngan_sach=1200)
NAM_TRAI = -0.21   # nắm trái (đặt NAM_TRAI=-0.21 khi chạy chop)
DUOI, DINH = -0.27, 0.56
ZH = 0.45          # tâm đầu rìu trên cán
R = 0.15           # bán kính cung lưỡi
TAM = (0.055, ZH)  # tâm cung lưỡi (x, z)


def build():
    p = {}
    # CÁN: thẳng đoạn hai tay nắm (hợp đồng), thon dần lên đầu, phình về đuôi; núm đuôi tối màu
    p["can_duoi"] = ong((0, 0, DUOI + 0.03), (0, 0, NAM_TRAI - 0.05), 0.019, 0.016, "go", n=8)
    p["can_giua"] = ong((0, 0, NAM_TRAI - 0.05), (0, 0, 0.30), 0.016, 0.015, "go", n=8)
    p["can_tren"] = ong((0, 0, 0.30), (0.006, 0, DINH), 0.015, 0.014, "go", n=8)
    p["num"] = khoi([(x, y, z) for z, r in ((DUOI, 0.017), (DUOI + 0.012, 0.024), (DUOI + 0.035, 0.019))
                     for x, y in [(r * math.cos(2 * math.pi * k / 8), r * math.sin(2 * math.pi * k / 8)) for k in range(8)]], "go_toi")
    # QUẤN CÁN hai chỗ nắm (da, viền nổi) — bán kính 16,5 mm ⇒ vẫn trong cửa 13–17
    for ten, z0 in (("quan_phai", 0.0), ("quan_trai", NAM_TRAI)):
        p[ten] = ong((0, 0, z0 - 0.055), (0, 0, z0 + 0.055), 0.0165, 0.0165, "go_toi", n=8)   # da quấn tối
        for k, dz in enumerate((-0.055, 0.055)):
            p[f"{ten}_vien{k}"] = ong((0, 0, z0 + dz - 0.005), (0, 0, z0 + dz + 0.005), 0.0172, 0.0172, "dong", n=8)   # vòng đồng
    # ĐẦU: khâu ôm cán (mắt rìu) + má rìu dày + gáy búa vuông
    p["khau"] = khoi([(x, y, z) for z in (ZH - 0.065, ZH + 0.065) for x in (-0.03, 0.03) for y in (-0.025, 0.025)], "sat")
    p["ma"] = khoi([(0.025, -0.022, ZH - 0.06), (0.025, 0.022, ZH - 0.06), (0.025, -0.022, ZH + 0.06), (0.025, 0.022, ZH + 0.06),
                    (0.085, -0.012, ZH - 0.045), (0.085, 0.012, ZH - 0.045), (0.085, -0.012, ZH + 0.05), (0.085, 0.012, ZH + 0.05)], "sat")
    p["gay"] = khoi([(x, y, z) for x, s in ((-0.03, 1.0), (-0.068, 0.86)) for y in (-0.027 * s, 0.027 * s) for z in (ZH - 0.045 * s, ZH + 0.045 * s)]
                    + [(-0.078, y, z) for y in (-0.016, 0.016) for z in (ZH - 0.03, ZH + 0.03)], "sat")   # gáy búa vát cạnh
    for k, dz in enumerate((-0.068, 0.068)):   # đai sắt tối trên/dưới mắt rìu
        p[f"dai_{k}"] = khoi([(x, y, ZH + dz + h) for x in (-0.034, 0.034) for y in (-0.029, 0.029) for h in (-0.008, 0.008)], "da")
    for k, (x, z) in enumerate(((0.05, ZH + 0.025), (0.05, ZH - 0.025))):   # đinh tán đồng hai má
        for s_ in (-1, 1):
            p[f"dinh_{k}_{s_ + 1}"] = khoi([(x + dx, s_ * (0.016 + h), z + dz) for dx in (-0.007, 0.007) for dz in (-0.007, 0.007) for h in (0, 0.005)], "dong")
    p["nem"] = khoi([(-0.012, -0.006, ZH + 0.065), (0.012, -0.006, ZH + 0.065), (-0.012, 0.006, ZH + 0.065), (0.012, 0.006, ZH + 0.065),
                     (0, 0, ZH + 0.095)], "dong")   # nêm đồng trên mắt rìu
    # LƯỠI TRĂNG KHUYẾT CÓ RÂU: cung mép từ +55° (sừng trên) xuống −75° (râu chúc xuống), mỗi khúc = hull (gốc ở má, 2 điểm mép)
    goc = [55, 30, 8, -15, -38, -58, -78, -92]
    mep = [(TAM[0] + R * math.cos(math.radians(a)) * (1.0 if a > -40 else 0.92 - 0.004 * (-40 - a)), TAM[1] + R * math.sin(math.radians(a))) for a in goc]
    def goc_ma(a):   # điểm gốc trên má tương ứng (râu bám thấp xuống cán)
        return (0.08, ZH + max(-0.045, min(0.05, 0.05 * math.sin(math.radians(a)) * 1.6))) if a > -40 else (0.035 + 0.035 * (a + 92) / 52, ZH - 0.05 - 0.035 * (-40 - a) / 52)
    for i in range(len(goc) - 1):
        (x0, z0), (x1, z1) = mep[i], mep[i + 1]; g0, g1 = goc_ma(goc[i]), goc_ma(goc[i + 1])
        tron = [(x0 - 0.022 * math.cos(math.radians(goc[i])), z0 - 0.022 * math.sin(math.radians(goc[i]))),
                (x1 - 0.022 * math.cos(math.radians(goc[i + 1])), z1 - 0.022 * math.sin(math.radians(goc[i + 1])))]
        p[f"luoi_{i}"] = khoi([(g[0], s * 0.011, g[1]) for g in (g0, g1) for s in (-1, 1)] +
                              [(t[0], s * 0.005, t[1]) for t in tron for s in (-1, 1)], "sat")
        # VIỀN LƯỠI mài sáng (dải mỏng ngoài cùng)
        p[f"vien_{i}"] = khoi([(t[0], s * 0.005, t[1]) for t in tron for s in (-1, 1)] +
                              [(x, s * 0.0015, z) for x, z in ((x0, z0), (x1, z1)) for s in (-1, 1)], "long")
    return p

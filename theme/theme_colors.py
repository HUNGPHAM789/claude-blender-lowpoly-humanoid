"""THEME MÀU dùng chung cho cả game settler (Boss 23/10/2026: «Theo tông màu của nai B bạn vừa mới chỉnh, thì theme đó là theme gì?
Tôi muốn apply theme đó cho game này - đặc biệt với settler và các vật dụng đã tạo trước»).

Hai theme, CÙNG bảng màu sRGB của từng asset — chỉ khác CÁCH NẠP vào glTF/Blender (baseColor là màu TUYẾN TÍNH):
  · "dat_am"  (Đất ấm, MẶC ĐỊNH từ 23/10): đổi sRGB → tuyến tính đúng chuẩn ⇒ thấy đúng màu đã chọn: đậm, ấm, đất (giống nai B).
  · "nhat_nha" (Nhạt nhà, cũ 22/10): ghi thẳng sRGB/255 vào kênh tuyến tính ⇒ mọi màu sáng bạc, pastel.
Đổi theme: file ~/projects/lpm-faceless-humanoid/theme/theme.json {"theme": "nhat_nha"} hoặc biến môi trường THEME_MAU. Rồi dựng lại (build.sh, lpms render, tools).
Mỗi nơi nạp màu PHẢI gọi mau() — cửa «màu nhà» của lpms/tools so bằng mau() chứ không so bảng thô."""
import json, os

_F = os.path.expanduser("~/projects/lpm-faceless-humanoid/theme/theme.json")


def theme():
    if os.environ.get("THEME_MAU"): return os.environ["THEME_MAU"]
    try: return json.load(open(_F)).get("theme", "dat_am")
    except Exception: return "dat_am"


def _tt(x):
    x = x / 255.0; return x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4


def mau(c):
    """c = (r, g, b[, a]) sRGB 0–255 ⇒ [r, g, b, a] float 0–1 cho baseColorFactor / Base Color theo theme."""
    a = (c[3] / 255.0) if len(c) > 3 else 1.0
    if theme() == "nhat_nha": return [c[0] / 255.0, c[1] / 255.0, c[2] / 255.0, a]
    return [_tt(c[0]), _tt(c[1]), _tt(c[2]), a]


# Da/mắt settler (trước đây ghi thẳng giá trị tuyến tính trong blender_build.py): giữ màu HIỂN THỊ cũ cho theme nhat_nha,
# màu da ấm tự nhiên cho dat_am.
DA = {"nhat_nha": (231, 220, 200), "dat_am": (222, 186, 152)}
HOC_MAT = {"nhat_nha": (151, 136, 118), "dat_am": (92, 64, 48)}

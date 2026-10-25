#!/usr/bin/env python3
"""
AGE OF EMPIRES — MEGA TRIPLED 100M ISLAND (GHIBLI PALETTE & LOW 28° ANGLE)
Adds clean floating annotations with 100% CLEAR (TRANSPARENT) BACKGROUND
Zero opaque cards obscuring the 3D scene!

Accurately pinpoints all 9 revised features:
1. All-Green Oak Forest (100% oak_tree, removed pines & birch)
2. Deer Herd (7 deers) & Wild Rabbits (4 rabbits)
3. Berry Bushes & Wildflower Meadow
4. Central Campfire & Log Seats
5. Settler Flat Expansion Ground
6. Mountain Massifs: Weathered terraced bluffs (West & East, NO pointy cones)
7. Waterfall in the Middle (Cascades between the two bluffs into splash pool)
8. Organic Meandering River with S-bends, Oxbow loop, and Stepping Stones
9. Regular Natural Stones only (LPM rock_large, rock_medium, rock_small - zero weird granite)
10. Open-slot Timber Storage (wood_storage.glb)
11. Expansive River Delta entering the Ocean
"""
from PIL import Image, ImageDraw, ImageFont
import os

img_path = "~/projects/lpm-faceless-humanoid/assets/aoe_starter_pack/aoe_starter_island_isometric.png"
out_path = "~/projects/lpm-faceless-humanoid/assets/aoe_starter_pack/aoe_starter_island_labeled.png"
img = Image.open(img_path).convert("RGBA")
draw = ImageDraw.Draw(img)

try:
    font_title = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial Bold.ttf", 34)
    font_sub = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial Bold.ttf", 19)
    font_label_bold = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial Bold.ttf", 20)
    font_label_sub = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial Bold.ttf", 15)
except Exception:
    font_title = font_sub = font_label_bold = font_label_sub = ImageFont.load_default()

def draw_shadow_text(x, y, text, fill_col, font, shadow_col=(0, 0, 0, 245), offset=2):
    for dx in [-offset, 0, offset]:
        for dy in [-offset, 0, offset]:
            if dx != 0 or dy != 0:
                draw.text((x + dx, y + dy), text, fill=shadow_col, font=font)
    draw.text((x, y), text, fill=fill_col, font=font)

# 1. Top Title (Floating with drop shadow, completely clear background)
draw_shadow_text(60, 32, "AGE OF EMPIRES — ĐẢO KHỞI ĐẦU 100M (GHIBLI PALETTE & GÓC NHÌN THẤP 28°)", (247, 201, 72, 255), font_title, offset=3)
draw_shadow_text(60, 74, "100% Cây Sồi Lá Xanh • Núi Tầng Bằng Phẳng • Thác Ở Giữa • Sông Uốn Khúc S-Bend • Đá Đồng Nhất • Đàn Hươu 7 Con & 4 Thỏ", (240, 240, 245, 255), font_sub, offset=2)

# Left Column Notes
left_notes = [
    # lx, ly, tx, ty, title, sub, color
    (60, 160, 851, 371, "🌲 RỪNG SỒI XANH THẬT LPM (TẤT CẢ LÁ XANH)", "100% Cây Sồi Xanh Mướt (Đã Gỡ Bỏ Thông & Bạch Dương)", (130, 235, 150, 255)),
    (60, 295, 793, 496, "🦌 ĐÀN HƯƠU ORIGAMI LPM (7 CON) & 4 THỎ", "Alpha Stag Gạc Lớn, 3 Hươu Mẹ, 2 Hươu Nhỡ, 1 Fawn & 4 Thỏ", (255, 210, 85, 255)),
    (60, 435, 563, 585, "🍓 BỤI DÂU & VƯỜN HOA DẠI THẬT LPM", "Bụi Dâu Trĩu Quả LPM + Hoa Đỏ Xanh & Cụm Nấm", (255, 120, 135, 255)),
    (60, 580, 845, 607, "🔥 BẾP LỬA TRUNG TÂM & GHẾ GỖ", "Vòng Đá Cuội Tự Nhiên • Than Hồng • Lửa Đỏ Cam", (255, 160, 45, 255)),
    (60, 725, 943, 669, "🌱 BÃI ĐẤT ĐỊNH CƯ MỞ RỘNG", "Đất Bằng Trống Rộng Thoáng Sẵn Sàng Xây Dựng", (140, 240, 170, 255)),
]

# Right Column Notes
right_notes = [
    # lx, ly, tx, ty, title, sub, color
    (1380, 160, 1023, 312, "🏔️ KHỐI NÚI ĐÔI TẦNG PHẲNG (KHÔNG CHÓP NHỌN)", "Khối Đá Trầm Tích Vách Bậc Thang Bằng Phẳng (Tây & Đông)", (230, 225, 205, 255)),
    (1380, 295, 1136, 434, "💦 THÁC NƯỚC Ở CHÍNH GIỮA HAI KHỐI NÚI", "Hẻm Núi Trung Tâm Đổ 2 Tầng Xuống Hồ Chân Núi", (140, 225, 255, 255)),
    (1380, 435,  974, 580, "🌊 DÒNG SÔNG UỐN LƯỢN ĐA DẠNG & ĐÁ BƯỚC", "Khúc Co S-Bends, Vòng Oxbow Quanh Bếp Lửa & Cầu Đá Bước", (120, 220, 240, 255)),
    (1380, 580, 1345, 595, "🪨 BÃI ĐÁ TỰ NHIÊN ĐỒNG NHẤT LPM", "Tảng Đá Tự Nhiên (rock_large, rock_medium, rock_small - Gỡ Bỏ Hoa Cương Lạ)", (245, 215, 130, 255)),
    (1380, 725, 1081, 666, "🪵 KHO GỖ Ô THOÁNG THẬT LPM", "Kho Gỗ Chuẩn AoE (wood_storage.glb) • Súc Gỗ Tròn", (235, 185, 120, 255)),
    (1380, 870,  943, 978, "🏖️ CỬA SÔNG ĐỔ RA BIỂN", "Cửa Sông Rộng Xẻ Vách Đất & Cát Đổ Ra Đại Dương", (140, 220, 230, 255)),
]

for lx, ly, tx, ty, title, sub, col in left_notes:
    draw.ellipse([tx - 6, ty - 6, tx + 6, ty + 6], fill=(0, 0, 0, 220), outline=(247, 201, 72, 255), width=2)
    draw.ellipse([tx - 3, ty - 3, tx + 3, ty + 3], fill=(247, 201, 72, 255))
    draw.line([(lx + 430, ly + 12), (tx, ty)], fill=col[:3] + (210,), width=2)
    draw_shadow_text(lx, ly, title, col, font_label_bold, offset=2)
    draw_shadow_text(lx, ly + 24, sub, (230, 235, 245, 255), font_label_sub, offset=2)

for lx, ly, tx, ty, title, sub, col in right_notes:
    draw.ellipse([tx - 6, ty - 6, tx + 6, ty + 6], fill=(0, 0, 0, 220), outline=(247, 201, 72, 255), width=2)
    draw.ellipse([tx - 3, ty - 3, tx + 3, ty + 3], fill=(247, 201, 72, 255))
    draw.line([(lx, ly + 12), (tx, ty)], fill=col[:3] + (210,), width=2)
    draw_shadow_text(lx, ly, title, col, font_label_bold, offset=2)
    draw_shadow_text(lx, ly + 24, sub, (230, 235, 245, 255), font_label_sub, offset=2)

# Bottom Bar Info (Clear background)
draw_shadow_text(60, 1032, "ASSET PACK: aoe_starter_island_full.glb (Tripled 100m Island • Ghibli Palette Codex v2 • Low 28° Angle • 100% Green Oaks)", (160, 225, 175, 255), font_label_sub, offset=2)

img.convert("RGB").save(out_path)
print(f"✅ Saved Clear-Background Labeled Mega AoE Island -> {out_path}")

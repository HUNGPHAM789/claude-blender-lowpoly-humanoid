#!/usr/bin/env python3
"""
Labels the Starter Storage Tile Showcase with clean clear-background annotations.
Points to all 4 storage quadrants and construction framing.
"""
from PIL import Image, ImageDraw, ImageFont
import os

img_path = "~/projects/lpm-faceless-humanoid/assets/aoe_starter_pack/showcase_starter_storage.png"
out_path = "~/projects/lpm-faceless-humanoid/assets/aoe_starter_pack/showcase_starter_storage_labeled.png"
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

# Title
draw_shadow_text(60, 35, "Ô KHO KHỞI ĐẦU 4 Ô VUÔNG — STARTER STORAGE TILE (LƯỚI 2x2)", (247, 201, 72, 255), font_title, offset=3)
draw_shadow_text(60, 78, "Mặt Bằng Đất Nện 3.8m x 3.8m • Khung Gỗ Chia 4 Ô Mở • Sẵn Sàng Lưu Trữ Gỗ, Đá, Lương Thực & Mở Rộng", (240, 240, 245, 255), font_sub, offset=2)

# Left Column (Slots 1 & 3)
left_notes = [
    # lx, ly, tx, ty, title, sub, col
    (60, 320, 830, 480, "🪵 Ô 1: KHO GỖ TRÒN (Tây-Bắc)", "4 Súc Gỗ Sồi Xếp Chồng Gọn Gàng • Vết Cắt Gỗ Sáng", (235, 185, 120, 255)),
    (60, 580, 810, 680, "🍓 Ô 3: KHO LƯƠNG THỰC (Tây-Nam)", "Giỏ Mây Đan (Wicker) Đựng Đầy Dâu Rừng Đỏ Mọng + Hòm Gỗ", (255, 130, 145, 255)),
]

# Right Column (Slots 2 & 4 + Framing)
right_notes = [
    (1380, 320, 1150, 470, "🪨 Ô 2: KHO ĐÁ MỎ THÔ (Đông-Bắc)", "3 Khối Đá Xẻ Vuông Vức + Mảnh Vụn Chân Tường", (210, 215, 220, 255)),
    (1380, 580, 1170, 670, "📦 Ô 4: Ô TRỐNG MỞ RỘNG (Đông-Nam)", "Mặt Sàn Gỗ Thoáng Sẵn Sàng Nhận Tài Nguyên Tiếp Theo", (140, 240, 175, 255)),
    (1380, 780,  990, 570, "🏗️ CHỐT GỖ TRUNG TÂM & KHUNG 2x2", "Khung Gỗ Bao 4 Cạnh • 4 Cọc Gỗ Góc • Chốt Gỗ Giữa", (245, 205, 110, 255)),
]

for lx, ly, tx, ty, title, sub, col in left_notes:
    draw.ellipse([tx - 6, ty - 6, tx + 6, ty + 6], fill=(0, 0, 0, 220), outline=(247, 201, 72, 255), width=2)
    draw.ellipse([tx - 3, ty - 3, tx + 3, ty + 3], fill=(247, 201, 72, 255))
    draw.line([(lx + 380, ly + 12), (tx, ty)], fill=col[:3] + (210,), width=2)
    draw_shadow_text(lx, ly, title, col, font_label_bold, offset=2)
    draw_shadow_text(lx, ly + 24, sub, (230, 235, 245, 255), font_label_sub, offset=2)

for lx, ly, tx, ty, title, sub, col in right_notes:
    draw.ellipse([tx - 6, ty - 6, tx + 6, ty + 6], fill=(0, 0, 0, 220), outline=(247, 201, 72, 255), width=2)
    draw.ellipse([tx - 3, ty - 3, tx + 3, ty + 3], fill=(247, 201, 72, 255))
    draw.line([(lx, ly + 12), (tx, ty)], fill=col[:3] + (210,), width=2)
    draw_shadow_text(lx, ly, title, col, font_label_bold, offset=2)
    draw_shadow_text(lx, ly + 24, sub, (230, 235, 245, 255), font_label_sub, offset=2)

# Bottom note
draw_shadow_text(60, 1030, "ASSET CONTRACT: starter_storage_tile.glb (Standalone Asset • 3.8m x 3.8m • Modular AoE Starter Stockpile)", (160, 225, 175, 255), font_label_sub, offset=2)

img.convert("RGB").save(out_path)
print(f"✅ Saved Starter Storage Labeled Showcase -> {out_path}")

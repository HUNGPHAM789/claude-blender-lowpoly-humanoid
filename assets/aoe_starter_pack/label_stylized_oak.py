#!/usr/bin/env python3
"""
Labels the Refined Stylized Oak Tree Showcase with clean clear-background annotations.
"""
from PIL import Image, ImageDraw, ImageFont

img_path = "~/projects/lpm-faceless-humanoid/assets/aoe_starter_pack/showcase_stylized_oak.png"
out_path = "~/projects/lpm-faceless-humanoid/assets/aoe_starter_pack/showcase_stylized_oak_labeled.png"
img = Image.open(img_path).convert("RGBA")
draw = ImageDraw.Draw(img)

try:
    font_title = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial Bold.ttf", 34)
    font_sub = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial Bold.ttf", 19)
    font_bold = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial Bold.ttf", 20)
    font_small = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial Bold.ttf", 15)
except Exception:
    font_title = font_sub = font_bold = font_small = ImageFont.load_default()

def draw_shadow_text(x, y, text, fill_col, font, shadow_col=(0, 0, 0, 245), offset=2):
    for dx in [-offset, 0, offset]:
        for dy in [-offset, 0, offset]:
            if dx != 0 or dy != 0:
                draw.text((x + dx, y + dy), text, fill=shadow_col, font=font)
    draw.text((x, y), text, fill=fill_col, font=font)

# Title
draw_shadow_text(60, 35, "CÂY SỒI STYLIZED NÂNG CẤP (V2.0) — 2 TÁN NHỎ TÁCH RỜI TRÊN CÀNH LỘ RÕ", (247, 201, 72, 255), font_title, offset=3)
draw_shadow_text(60, 78, "Đã Gỡ Bỏ Màu Xanh Đậm • 2 Tán Nhỏ Tách Biệt Đậu Trên Cành Gỗ Vươn Dài • Giữ Kích Thước 4.8m Boss Đã Duyệt", (240, 240, 245, 255), font_sub, offset=2)

# Left Column Notes
left_notes = [
    # lx, ly, tx, ty, title, sub, col
    (60, 320, 830, 410, "🌿 TÁN PHỤ B TÁCH RỜI (Tây-Nam)", "Khối Tán Nhỏ Độc Lập • Xanh Mướt Ghibli Thuần Nhất", (140, 240, 165, 255)),
    (60, 520, 890, 510, "🪵 CÀNH GỖ VƯƠN LỘ RÕ", "Cành Gỗ Nâng Đỡ Tán B Tách Xa Thân Chính", (235, 185, 120, 255)),
    (60, 720, 755, 780, "🧑 DÂN LÀNG (1.75m)", "Thước Đo Chuẩn • Cây Cao Gấp ~2.7x Người", (140, 210, 255, 255)),
]

# Right Column Notes
right_notes = [
    (1380, 280, 1010, 260, "🌳 TÁN CHÍNH TRUNG TÂM (4.8m)", "Khối Tán Tròn Đỉnh Vòm • Đã Xóa Bỏ Cục Lồi Kỳ Quặc", (255, 215, 90, 255)),
    (1380, 480, 1180, 430, "🌿 TÁN PHỤ A TÁCH RỜI (Đông-Bắc)", "Khối Tán Nhỏ Độc Lập Cân Đối Bên Phải", (130, 245, 175, 255)),
    (1380, 680, 1120, 530, "🪵 CÀNH GỖ VƯƠN LỘ RÕ PHẢI", "Chạc Ba Cành Gỗ Lộ Rõ Nâng Tán A", (245, 195, 110, 255)),
]

for lx, ly, tx, ty, title, sub, col in left_notes:
    draw.ellipse([tx - 6, ty - 6, tx + 6, ty + 6], fill=(0, 0, 0, 220), outline=(247, 201, 72, 255), width=2)
    draw.ellipse([tx - 3, ty - 3, tx + 3, ty + 3], fill=(247, 201, 72, 255))
    draw.line([(lx + 380, ly + 12), (tx, ty)], fill=col[:3] + (210,), width=2)
    draw_shadow_text(lx, ly, title, col, font_bold, offset=2)
    draw_shadow_text(lx, ly + 24, sub, (230, 235, 245, 255), font_small, offset=2)

for lx, ly, tx, ty, title, sub, col in right_notes:
    draw.ellipse([tx - 6, ty - 6, tx + 6, ty + 6], fill=(0, 0, 0, 220), outline=(247, 201, 72, 255), width=2)
    draw.ellipse([tx - 3, ty - 3, tx + 3, ty + 3], fill=(247, 201, 72, 255))
    draw.line([(lx, ly + 12), (tx, ty)], fill=col[:3] + (210,), width=2)
    draw_shadow_text(lx, ly, title, col, font_bold, offset=2)
    draw_shadow_text(lx, ly + 24, sub, (230, 235, 245, 255), font_small, offset=2)

# Bottom Bar
draw_shadow_text(60, 1030, "ASSET CONTRACT: stylized_oak_v2.glb (Standalone Asset • 4.8m Scale • 3 Separate Bushes • Visible Branches • Chờ Boss Duyệt)", (160, 225, 175, 255), font_sub, offset=2)

img.convert("RGB").save(out_path)
print(f"✅ Saved Refined Oak Labeled Showcase -> {out_path}")

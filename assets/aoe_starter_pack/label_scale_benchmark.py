#!/usr/bin/env python3
"""
Adds clean drop-shadow annotations for the Scale Benchmark Showcase.
Illustrates the exact height comparisons:
Human (1.75m) vs Berry Bush (1.0m) vs Fawn (0.7m) vs Doe (1.3m) vs Stag (1.75m)
vs Proposed Oak (4.8m) vs Old Overscaled Oak (14.5m).
"""
from PIL import Image, ImageDraw, ImageFont
import os

img_path = "~/projects/lpm-faceless-humanoid/assets/aoe_starter_pack/showcase_scale_benchmark.png"
out_path = "~/projects/lpm-faceless-humanoid/assets/aoe_starter_pack/showcase_scale_benchmark_labeled.png"
img = Image.open(img_path).convert("RGBA")
draw = ImageDraw.Draw(img)

try:
    font_title = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial Bold.ttf", 34)
    font_sub = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial Bold.ttf", 19)
    font_bold = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial Bold.ttf", 18)
    font_small = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial Bold.ttf", 14)
except Exception:
    font_title = font_sub = font_bold = font_small = ImageFont.load_default()

def draw_shadow_text(x, y, text, fill_col, font, shadow_col=(0, 0, 0, 245), offset=2):
    for dx in [-offset, 0, offset]:
        for dy in [-offset, 0, offset]:
            if dx != 0 or dy != 0:
                draw.text((x + dx, y + dy), text, fill=shadow_col, font=font)
    draw.text((x, y), text, fill=fill_col, font=font)

# Top Title
draw_shadow_text(60, 35, "BẢNG ĐỐI CHIẾU TỈ LỆ (SCALE BENCHMARK) — CÂY SỒI vs HƯƠU vs BỤI DÂU vs NGƯỜI", (247, 201, 72, 255), font_title, offset=3)
draw_shadow_text(60, 78, "Giải Quyết Gốc Rễ Phản Hồi Của Boss: Cây Cũ (14.5m) Quá To Nuốt Chửng Thú • Đề Xuất Cây Chuẩn RTS (4.8m)", (240, 240, 245, 255), font_sub, offset=2)

# Entities from Left to Right: (tx, ty, label, sub, color, up_offset)
entities = [
    # Human (hx = -8.0 -> screen X ~ 320)
    (320, 740, "🧑 DÂN LÀNG", "Cao: 1.75m\nThước Đo Chuẩn", (140, 210, 255, 255), -140),
    # Berry Bush (bx = -5.5 -> screen X ~ 475)
    (475, 780, "🍓 BỤI DÂU", "Cao: 1.0m\nBụi Quả Mọng", (255, 130, 150, 255), -110),
    # Fawn (fx = -3.5 -> screen X ~ 600)
    (600, 800, "🦌 HƯƠU CON", "Cao: 0.70m\nĂn Cỏ (0.55x)", (255, 210, 90, 255), -90),
    # Doe (dx = -1.5 -> screen X ~ 725)
    (725, 760, "🦌 HƯƠU MẸ", "Cao: 1.30m\nĂn Cỏ (1.10x)", (255, 200, 80, 255), -120),
    # Stag (sx = 1.0 -> screen X ~ 880)
    (880, 720, "👑 ALPHA STAG", "Cao: 1.75m\nGạc Sát Sọ (1.35x)", (247, 201, 72, 255), -145),
    # Proposed Balanced Oak (ox = 4.8 -> screen X ~ 1110)
    (1110, 560, "✅ CÂY SỒI ĐỀ XUẤT", "Cao: 4.8m (0.95x)\nChuẩn Cozy RTS\nGấp 2.7x Người", (130, 245, 160, 255), -190),
    # Old Overscaled Oak (ox = 11.5 -> screen X ~ 1520)
    (1520, 260, "❌ CÂY CŨ (QUÁ TO)", "Cao: 14.5m (2.7x)\nQuá Khổng Lồ!\nNuốt Chửng Đàn Hươu", (255, 100, 100, 255), -220),
]

for tx, ty, title, sub, col, up_off in entities:
    # Target dot
    draw.ellipse([tx - 6, ty - 6, tx + 6, ty + 6], fill=(0, 0, 0, 220), outline=(247, 201, 72, 255), width=2)
    draw.ellipse([tx - 3, ty - 3, tx + 3, ty + 3], fill=(247, 201, 72, 255))
    
    # Leader line straight up
    ly = ty + up_off
    draw.line([(tx, ty), (tx, ly + 25)], fill=col[:3] + (210,), width=2)
    
    # Center text above leader
    lines = [title] + sub.split("\n")
    cur_y = ly - len(lines) * 18
    for line in lines:
        is_first = (line == title)
        f = font_bold if is_first else font_small
        c = col if is_first else (235, 240, 245, 255)
        # Approximate center width
        t_w = len(line) * (9 if is_first else 7)
        draw_shadow_text(tx - t_w // 2, cur_y, line, c, f, offset=2)
        cur_y += 20

# Bottom Bar
draw_shadow_text(60, 1030, "ĐỀ XUẤT ÁP DỤNG: Cây sồi thu về scale 0.95x (4.8m) -> Đảo giữ trọn vẹn bóng mát nhưng đàn hươu và bụi dâu hiển thị rõ nét!", (160, 225, 175, 255), font_sub, offset=2)

img.convert("RGB").save(out_path)
print(f"✅ Saved Scale Benchmark Labeled Showcase -> {out_path}")

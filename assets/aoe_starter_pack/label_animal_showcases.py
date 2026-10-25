#!/usr/bin/env python3
"""
Adds clean drop-shadow annotations with 100% CLEAR (TRANSPARENT) BACKGROUND
for the dedicated Deer Pack Showcase and Rabbit Showcase.
"""
from PIL import Image, ImageDraw, ImageFont

def draw_shadow_text(draw, x, y, text, fill_col, font, shadow_col=(0, 0, 0, 245), offset=2):
    for dx in [-offset, 0, offset]:
        for dy in [-offset, 0, offset]:
            if dx != 0 or dy != 0:
                draw.text((x + dx, y + dy), text, fill=shadow_col, font=font)
    draw.text((x, y), text, fill=fill_col, font=font)

try:
    font_title = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial Bold.ttf", 34)
    font_sub = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial Bold.ttf", 19)
    font_label_bold = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial Bold.ttf", 20)
    font_label_sub = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial Bold.ttf", 15)
except Exception:
    font_title = font_sub = font_label_bold = font_label_sub = ImageFont.load_default()

# 1. DEER PACK SHOWCASE
img_deer = Image.open("~/projects/lpm-faceless-humanoid/assets/aoe_starter_pack/showcase_deer_pack.png").convert("RGBA")
draw_d = ImageDraw.Draw(img_deer)

draw_shadow_text(draw_d, 60, 35, "ĐÀN HƯƠU ORIGAMI CHUẨN LPM (7 CON ĐẦY ĐỦ VÓC DÁNG)", (247, 201, 72, 255), font_title, offset=3)
draw_shadow_text(draw_d, 60, 78, "Alpha Stag Gạc Lớn Cảnh Giới • 3 Hươu Mẹ Ăn Cỏ & Đứng • 2 Hươu Nhỡ • 1 Hươu Con Fawn", (240, 240, 245, 255), font_sub, offset=2)

deer_notes = [
    # lx, ly, tx, ty, title, sub, col
    (60, 220, 680, 520, "🦌 HƯƠU MẸ 1 (Alert Idle)", "Dáng đứng cảnh giới • Tai vểnh • 730 tris", (255, 215, 90, 255)),
    (60, 420, 550, 650, "🦌 HƯƠU CON (Fawn Grazing)", "Hươu con gặm cỏ • Tỉ lệ 0.55x nhỏ xinh", (255, 140, 160, 255)),
    (60, 620, 520, 380, "🦌 HƯƠU NHỠ (Walk Step)", "Dáng bước đi tự nhiên • Chân nhấc nhẹ", (140, 235, 165, 255)),
    (1400, 220, 1020, 420, "👑 ALPHA STAG (Alert Standing)", "Hươu đầu đàn • Bộ gạc lớn sát sọ • 1.163 tris", (247, 201, 72, 255)),
    (1400, 420, 1260, 520, "🌾 HƯƠU MẸ 2 (Eating Pose)", "Cổ uốn cong chữ S • Mõm chạm đất ăn cỏ", (120, 225, 255, 255)),
    (1400, 620, 1420, 660, "🌿 HƯƠU NHỠ 2 (Grazing)", "Hươu tơ gặm cỏ ven suối", (160, 220, 180, 255)),
]

for lx, ly, tx, ty, title, sub, col in deer_notes:
    draw_d.ellipse([tx - 6, ty - 6, tx + 6, ty + 6], fill=(0, 0, 0, 220), outline=(247, 201, 72, 255), width=2)
    draw_d.ellipse([tx - 3, ty - 3, tx + 3, ty + 3], fill=(247, 201, 72, 255))
    draw_d.line([(lx + (300 if lx < tx else 0), ly + 12), (tx, ty)], fill=col[:3] + (210,), width=2)
    draw_shadow_text(draw_d, lx, ly, title, col, font_label_bold, offset=2)
    draw_shadow_text(draw_d, lx, ly + 24, sub, (230, 235, 245, 255), font_label_sub, offset=2)

draw_shadow_text(draw_d, 60, 1030, "ASSET SOURCE: stag_origami.glb & doe_origami.glb (LPM Animal Skill • Ground Contact Z=0.0m)", (170, 230, 185, 255), font_label_sub, offset=2)
img_deer.convert("RGB").save("~/projects/lpm-faceless-humanoid/assets/aoe_starter_pack/showcase_deer_pack_labeled.png")
print("✅ Saved showcase_deer_pack_labeled.png")

# 2. RABBIT SHOWCASE
img_rab = Image.open("~/projects/lpm-faceless-humanoid/assets/aoe_starter_pack/showcase_rabbits.png").convert("RGBA")
draw_r = ImageDraw.Draw(img_rab)

draw_shadow_text(draw_r, 60, 35, "ĐÀN THỎ ORIGAMI CHUẨN LPM (4 CON TRÊN ĐỒNG CỎ GHIBLI)", (247, 201, 72, 255), font_title, offset=3)
draw_shadow_text(draw_r, 60, 78, "Bộ Lông Trắng Ngà & Kem • Tai Dài Cụp Mở • Bụi Cỏ & Hoa Dại Ghibli Tự Nhiên", (240, 240, 245, 255), font_sub, offset=2)

rab_notes = [
    (60, 260, 720, 470, "🐇 THỎ MẸ 1 (Alert)", "Thỏ mẹ vểnh tai lắng nghe", (255, 215, 90, 255)),
    (60, 480, 840, 660, "🐇 THỎ MẸ 2 (Sniffing)", "Dáng gặm cỏ cúi sát đất", (140, 230, 255, 255)),
    (1400, 260, 1040, 380, "🐇 THỎ ĐẦU ĐÀN (Alpha)", "Thỏ đực vóc dáng đẫy đà", (247, 201, 72, 255)),
    (1400, 480, 1140, 320, "🐰 THỎ CON (Bunny)", "Thỏ con tinh nghịch ven bụi hoa", (255, 150, 180, 255)),
]

for lx, ly, tx, ty, title, sub, col in rab_notes:
    draw_r.ellipse([tx - 6, ty - 6, tx + 6, ty + 6], fill=(0, 0, 0, 220), outline=(247, 201, 72, 255), width=2)
    draw_r.ellipse([tx - 3, ty - 3, tx + 3, ty + 3], fill=(247, 201, 72, 255))
    draw_r.line([(lx + (260 if lx < tx else 0), ly + 12), (tx, ty)], fill=col[:3] + (210,), width=2)
    draw_shadow_text(draw_r, lx, ly, title, col, font_label_bold, offset=2)
    draw_shadow_text(draw_r, lx, ly + 24, sub, (230, 235, 245, 255), font_label_sub, offset=2)

draw_shadow_text(draw_r, 60, 1030, "ASSET SOURCE: rabbit.glb (LPM Organic Animal Skill • 1.6k tris • Ground Contact Z=0.0m)", (170, 230, 185, 255), font_label_sub, offset=2)
img_rab.convert("RGB").save("~/projects/lpm-faceless-humanoid/assets/aoe_starter_pack/showcase_rabbits_labeled.png")
print("✅ Saved showcase_rabbits_labeled.png")

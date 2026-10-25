from PIL import Image, ImageDraw, ImageFont
import os

img_path = "~/projects/lpm-faceless-humanoid/assets/aoe_starter_pack/showcase_mountain_waterfall.png"
out_path = "~/projects/lpm-faceless-humanoid/assets/aoe_starter_pack/showcase_mountain_waterfall_labeled.png"

img = Image.open(img_path).convert("RGBA")
overlay = Image.new("RGBA", img.size, (255, 255, 255, 0))
draw = ImageDraw.Draw(overlay)

def get_font(size):
    font_paths = [
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
        "/Library/Fonts/Arial.ttf"
    ]
    for p in font_paths:
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, size)
            except:
                pass
    return ImageFont.load_default()

font_title = get_font(42)
font_sub = get_font(26)
font_pill = get_font(22)

# Top Banner Card
draw.rounded_rectangle([40, 36, 960, 150], radius=16, fill=(20, 24, 33, 215), outline=(245, 185, 66, 240), width=3)
draw.text((64, 50), "AOE STARTER: MOUNTAIN WATERFALL PACK (v11.0 MASTER)", fill=(245, 185, 66, 255), font=font_title)
draw.text((64, 104), "ORGANIC NON-CIRCULAR POND · SINUSOIDAL S-CURVE RIVER · UNIFIED MASSIF", fill=(235, 240, 245, 220), font=font_sub)

# Spec Badge
draw.rounded_rectangle([1340, 36, 1880, 165], radius=16, fill=(20, 24, 33, 215), outline=(78, 161, 211, 220), width=3)
draw.text((1364, 52), "SPECIFICATIONS (v11.0 MASTER)", fill=(78, 161, 211, 255), font=font_sub)
draw.text((1364, 88), "• Pond: Asymmetric organic fan basin (non-circular, 5.1-6.7m)", fill=(240, 240, 245, 220), font=font_pill)
draw.text((1364, 115), "• River: 28-pt smooth sinusoidal spline (no square cuts)", fill=(240, 240, 245, 220), font=font_pill)
draw.text((1364, 142), "• Chute: 2.42m wall-to-wall water welded to top lake", fill=(240, 240, 245, 220), font=font_pill)

# Feature Badges
badges = [
    (740, 190, "HIGH ALPINE LAKE (WELDED TO WATERFALL)", (42, 138, 178)),
    (960, 380, "WALL-TO-WALL WATER (ZERO SIDE GAPS)", (245, 185, 66)),
    (860, 580, "ORGANIC NON-CIRCULAR POND (NATURAL SHORE)", (78, 161, 211)),
    (980, 700, "SEAMLESS POND MOUTH (ZERO GRAY SEAMS)", (42, 138, 178)),
    (970, 830, "ORGANIC LOW-POLY S-CURVE RIVER", (48, 148, 192)),
    (430, 360, "UNIFIED MOUNTAIN FLANK (NO SEAMS)", (112, 106, 98)),
]

for bx, by, text, col in badges:
    bbox = draw.textbbox((bx, by), text, font=font_pill)
    pad = 8
    draw.rounded_rectangle([bbox[0]-pad, bbox[1]-pad, bbox[2]+pad, bbox[3]+pad], radius=8, fill=(15, 20, 28, 210), outline=col, width=2)
    draw.text((bx, by), text, fill=(255, 255, 255, 255), font=font_pill)

final_img = Image.alpha_composite(img, overlay).convert("RGB")
final_img.save(out_path, quality=95)
print(f"✨ Labeled showcase generated: {out_path}")

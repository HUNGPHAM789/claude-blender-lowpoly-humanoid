"""Contact sheet of 8 hop frames with labels. python3 make_sheet.py"""
from PIL import Image, ImageDraw
import os
H = os.path.dirname(os.path.abspath(__file__))
frames = [(0, "rest"), (2, "crouch"), (4, "load"), (6, "push-off"), (9, "airborne"), (11, "reach"), (13, "front land"), (15, "hind land")]
T = 400
sheet = Image.new("RGB", (T * 4, T * 2), "white")
for k, (f, lab) in enumerate(frames):
    im = Image.open(os.path.join(H, "work/frames_hop", f"f{f:03d}.png")).convert("RGB").resize((T, T), Image.LANCZOS)
    d = ImageDraw.Draw(im); d.rectangle([0, 0, 170, 26], fill=(255, 255, 255)); d.text((6, 6), f"f{f:02d}  {lab}", fill=(0, 0, 0))
    sheet.paste(im, ((k % 4) * T, (k // 4) * T))
sheet.save(os.path.join(H, "rabbit_hop_contact_sheet.png"))

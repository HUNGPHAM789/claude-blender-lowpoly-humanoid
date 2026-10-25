"""Compose turnaround renders on WHITE, one row per model (Boss 25/10/2026: coloured + lit, white background, no mesh lines).
  python3 compose_white.py <out.png> <prefix1> [<prefix2> …]   (prefix = render_turnaround_blender.py out_prefix)"""
import sys
from PIL import Image
out, prefixes = sys.argv[1], sys.argv[2:]
VIEWS = ("front", "q_front", "side", "q_back", "back")
rows = []
for p in prefixes:
    tiles = []
    for v in VIEWS:
        im = Image.open(f"{p}_{v}.png").convert("RGBA"); bg = Image.new("RGBA", im.size, (255, 255, 255, 255)); bg.alpha_composite(im)
        a = im.split()[3].getbbox() or (0, 0, im.width, im.height); pad = 20
        tiles.append(bg.convert("RGB").crop((max(0, a[0] - pad), 0, min(im.width, a[2] + pad), im.height)))
    row = Image.new("RGB", (sum(t.width for t in tiles), tiles[0].height), (255, 255, 255)); x = 0
    for t in tiles: row.paste(t, (x, 0)); x += t.width
    rows.append(row)
W = max(r.width for r in rows); sheet = Image.new("RGB", (W, sum(r.height for r in rows)), (255, 255, 255)); y = 0
for r in rows: sheet.paste(r, ((W - r.width) // 2, y)); y += r.height
sheet.save(out); print("saved", out, sheet.size)

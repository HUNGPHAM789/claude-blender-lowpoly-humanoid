"""Paste transparent renders onto the reference sheet's pastel panels, side by side.
  python3 compose_panels.py <out.png> <render1.png> [<render2.png> …] [--ref <sheet.png>]  (with --ref: reference on top)"""
import sys
from PIL import Image
COLS = [(250, 172, 150), (172, 160, 230), (236, 166, 172), (166, 160, 226), (206, 160, 212)]
a = sys.argv[1:]; ref = None
if "--ref" in a: i = a.index("--ref"); ref = a[i + 1]; a = a[:i] + a[i + 2:]
out, files = a[0], a[1:]
tiles = []
for f, c in zip(files, COLS):
    im = Image.open(f).convert("RGBA"); bg = Image.new("RGBA", im.size, c + (255,)); bg.alpha_composite(im); tiles.append(bg.convert("RGB"))
sheet = Image.new("RGB", (sum(t.width for t in tiles), max(t.height for t in tiles))); x = 0
for t in tiles: sheet.paste(t, (x, 0)); x += t.width
if ref:
    r = Image.open(ref).convert("RGB"); r = r.crop((0, 0, int(r.width * 0.40), r.height))   # the two colour panels
    r = r.resize((int(r.width * sheet.height / r.height), sheet.height))
    both = Image.new("RGB", (r.width + sheet.width + 12, sheet.height), (255, 255, 255)); both.paste(r, (0, 0)); both.paste(sheet, (r.width + 12, 0)); sheet = both
sheet.save(out); print("saved", out)

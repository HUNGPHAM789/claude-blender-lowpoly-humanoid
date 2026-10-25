"""Gate + preview: does the built body cast the same silhouette as the reference sheet? (Boss 25/10/2026)

  python3 compare_silhouette.py --sex male --glb <body>.glb --out <dir>   ⇒ <dir>/<sex>_overlay.png + exit 1 if a band fails

Front = X–Z projection, side = Y–Z (forward to the right, like the sheet), back = mirrored front. Built body is scaled so its
height-in-figure-units matches the sheet (scale_m), feet on the same baseline, centred on the ankle centre of each view.
Bands (fraction of figure height) skip hair (> 0.84) and the leather skirt (0.37–0.52) because the body is naked under them.
Overlay colours: reference only = red, build only = cyan, both = white.
"""
import argparse, json, os, sys
import numpy as np
import trimesh
from build_body import load_zup
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__)); SPEC = os.path.join(HERE, "..", "spec")
BANDS = {"lower_leg": (0.04, 0.30), "knee_thigh": (0.30, 0.37), "waist_chest": (0.52, 0.80)}
MIN_IOU = {"front": 0.80, "side": 0.75, "back": 0.80}       # calibrated on the first accepted build (see SKILL.md)


def raster(tris2d, H, W, ox, scale):
    im = Image.new("L", (W, H), 0); d = ImageDraw.Draw(im)
    for t in tris2d:
        d.polygon([(ox + x * scale, H - 1 - z * scale) for x, z in t], fill=255)
    return np.asarray(im) > 0


def ankle_centre(mask, H):
    rows = mask[int(H * 0.86):int(H * 0.89)]
    xs = np.where(rows.any(axis=0))[0]
    return (xs.min() + xs.max()) / 2 if len(xs) else mask.shape[1] / 2


def main(sex, glb, out):
    spec = json.load(open(os.path.join(SPEC, f"{sex}_spec.json"))); k = spec["scale_m"]
    mesh = load_zup(glb)
    T = mesh.vertices[mesh.faces] / k                                     # figure units
    os.makedirs(out, exist_ok=True); fails = []; tiles = []; report = {}
    for view in ("front", "side", "back"):
        ref = np.asarray(Image.open(os.path.join(SPEC, "measure", f"{sex}_{view}_mask.png")).convert("L")) > 0
        ys = np.where(ref.any(axis=1))[0]; top, bot = ys.min(), ys.max(); Hf = bot - top
        H, W = ref.shape
        if view == "front": t2 = T[:, :, [0, 2]]
        elif view == "side": t2 = T[:, :, [1, 2]]
        else: t2 = T[:, :, [0, 2]] * [-1, 1]
        ours = raster(t2, H, W, W / 2, Hf)
        # shift ours: baseline to the sheet's feet row, centre to the sheet's ankle centre
        oy = np.where(ours.any(axis=1))[0].max(); ours = np.roll(ours, bot - oy, axis=0)
        ours = np.roll(ours, int(round(ankle_centre(ref[top:bot + 1], Hf + 1) - ankle_centre(ours[top:bot + 1], Hf + 1))), axis=1)
        report[view] = {}
        for b, (lo, hi) in BANDS.items():
            r0, r1 = bot - int(hi * Hf), bot - int(lo * Hf)
            a, c = ref[r0:r1], ours[r0:r1]
            iou = (a & c).sum() / max(1, (a | c).sum()); report[view][b] = round(float(iou), 3)
            if iou < MIN_IOU[view]: fails.append(f"{view}:{b} IoU {iou:.2f} < {MIN_IOU[view]}")
        rgb = np.zeros((H, W, 3), np.uint8)
        rgb[ref & ~ours] = (230, 60, 60); rgb[ours & ~ref] = (60, 210, 230); rgb[ref & ours] = (245, 245, 245)
        for b, (lo, hi) in BANDS.items():
            for hh in (lo, hi): rgb[max(0, bot - int(hh * Hf)), :, :] = (90, 90, 90)
        tiles.append(Image.fromarray(rgb))
    Wt = sum(t.width for t in tiles) + 10 * (len(tiles) - 1); Ht = max(t.height for t in tiles)
    sheet = Image.new("RGB", (Wt, Ht), (30, 30, 30)); x = 0
    for t in tiles: sheet.paste(t, (x, 0)); x += t.width + 10
    sheet.save(os.path.join(out, f"{sex}_overlay.png"))
    json.dump(report, open(os.path.join(out, f"{sex}_silhouette_iou.json"), "w"), indent=1)
    print(json.dumps(report))
    for f in fails: print("⛔", f)
    if fails: sys.exit(1)
    print("✅ silhouette matches the reference in every band")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--sex", required=True); ap.add_argument("--glb", required=True); ap.add_argument("--out", required=True)
    a = ap.parse_args(); main(a.sex, a.glb, a.out)

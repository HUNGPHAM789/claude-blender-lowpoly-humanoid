"""Measure body silhouettes from a 5-view reference sheet (Boss 25/10/2026: official primal adult male/female).
Panels 3–5 are orthographic wireframes (front, side, back): figure = unsaturated pixels (white fill + black lines) on a
saturated pastel background. Output: per-panel mask PNG + per-row runs JSON (height-normalised, feet = 0, head top = 1)."""
import json, sys, os
import numpy as np
from PIL import Image
from scipy import ndimage

def figures(a):
    """3 wireframe figures (front, side, back) = the 3 largest unsaturated blobs right of the 2 render panels."""
    h, w, _ = a.shape
    p = a.astype(int); sat = p.max(axis=2) - p.min(axis=2)
    m = sat < 28
    top = (p.min(axis=2) > 235)[int(h * 0.05):int(h * 0.15)].mean(axis=0)
    for x in np.where(top > 0.9)[0]: m[:, max(0, x - 1):x + 2] = False      # erase white panel separators
    m = ndimage.binary_closing(m, structure=np.ones((3, 7)))               # re-join a figure cut by a separator
    holes = ndimage.binary_fill_holes(m) & ~m                              # fill mesh cells only; keep arm–torso gaps
    lab, n = ndimage.label(holes)
    if n:
        sz = ndimage.sum(holes, lab, range(1, n + 1)); m |= np.isin(lab, 1 + np.where(sz < 120)[0])
    m = ndimage.binary_opening(m, structure=np.ones((1, 5)))              # drop thin vertical lines (separators ≤ 4 px)
    m[:, : int(w * 0.37)] = False                                          # left two panels are shaded renders
    lab, n = ndimage.label(m)
    sz = ndimage.sum(m, lab, range(1, n + 1)); big = 1 + np.argsort(sz)[-3:]
    big = sorted(big, key=lambda k: np.where(lab == k)[1].mean())
    out = {}
    for v, k in zip(("front", "side", "back"), big):
        f = lab == k; xs = np.where(f.any(axis=0))[0]
        out[v] = f[:, xs.min():xs.max() + 1]
    return out


def runs(row):
    r = []; x = 0; w = len(row)
    while x < w:
        if row[x]:
            s = x
            while x < w and row[x]: x += 1
            r.append((s, x - 1))
        x += 1
    return r


def main(sheet, sex, out):
    a = np.asarray(Image.open(sheet).convert("RGB"))
    res = {"sheet": os.path.basename(sheet), "sex": sex, "views": {}}
    for v, m in figures(a).items():
        ys = np.where(m.any(axis=1))[0]; top, bot = int(ys.min()), int(ys.max())
        H = bot - top
        Image.fromarray((m * 255).astype(np.uint8)).save(os.path.join(out, f"{sex}_{v}_mask.png"))
        rows = []
        for y in range(top, bot + 1):
            rr = runs(m[y])
            rows.append({"h": round((bot - y) / H, 4), "runs": [[round((s) / H, 4), round((e) / H, 4)] for s, e in rr]})
        res["views"][v] = {"px_height": H, "top": top, "bottom": bot, "rows": rows}
    json.dump(res, open(os.path.join(out, f"{sex}_silhouette.json"), "w"))
    print(sex, {v: d["px_height"] for v, d in res["views"].items()})


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], sys.argv[3])

"""Armpit POINT gate for an upper garment, measured the way the owner sees it (Boss 25/10 ×3: «vật nhọn lòi ra nách» · «vệt nhọn nâu áo V7
bên nách trái nhìn từ phía trước» · «Phần nách vẫn còn chỗ nhọn, nhọn của dây belt»). Spec: Codex audit
`spec/audits/codex_audit_female_bandeau_armpit.md` (final spec step 8).

  python3 measure_armpit_point.py --top <bandeau.glb> --body <base_lp.glb> [--max-mm 5] [--overlay out.png]

Orthographic depth-tested renders (the whole body takes part in depth) from the front and yaw ±35°, 1.5 mm pixels, inside an anatomical
box beside each armpit (outer torso side, from 4 cm below to 3 cm above the garment's top) padded by 12 mm. Mask = pixels where the
garment (leather ∪ trim) is the nearest surface. Morphological opening with a 4.5 mm-radius disk keeps every part of the garment that
is at least 9 mm wide; what the opening removes is a narrow appendage. Score = the longest removed run: the largest distance from a
removed pixel to the opened mask. Exit 1 when any view / side scores > --max-mm. --overlay writes the masks with removed pixels in red.
"""
import argparse, sys
import numpy as np
import trimesh
from scipy import ndimage

PX = 0.0005               # m per pixel
OPEN_R = 0.0045           # m opening radius (a 16 mm binding face survives; a < 9 mm wide tip does not)
PAD = 0.012               # m box padding so cropping cannot create or hide a spur
VIEWS = {"front": 0.0, "yaw+35": 35.0, "yaw-35": -35.0}


def raster(tris, tag, d, u, y0, y1, u0, u1):
    """nearest-surface tag image for parallel rays along d (orthographic), pixel grid over (u, y)."""
    W = int(np.ceil((u1 - u0) / PX)); H = int(np.ceil((y1 - y0) / PX))
    depth = np.full((H, W), np.inf); img = np.full((H, W), -1, int)
    P2 = np.stack([tris @ u, tris[:, :, 1]], -1); Z = tris @ d             # (n, 3, 2) screen, (n, 3) depth along the view
    for t, (p, z) in enumerate(zip(P2, Z)):
        lo = np.floor((p.min(0) - [u0, y0]) / PX).astype(int); hi = np.ceil((p.max(0) - [u0, y0]) / PX).astype(int)
        lo = np.maximum(lo, 0); hi = np.minimum(hi, [W, H])
        if (hi <= lo).any(): continue
        gx, gy = np.meshgrid(np.arange(lo[0], hi[0]), np.arange(lo[1], hi[1]))
        q = np.stack([u0 + (gx + 0.5) * PX, y0 + (gy + 0.5) * PX], -1)
        a, b, c = p; v0, v1 = b - a, c - a; den = v0[0] * v1[1] - v1[0] * v0[1]
        if abs(den) < 1e-14: continue
        w = q - a; s = (w[..., 0] * v1[1] - v1[0] * w[..., 1]) / den; r = (v0[0] * w[..., 1] - w[..., 0] * v0[1]) / den
        inside = (s >= 0) & (r >= 0) & (s + r <= 1)
        if not inside.any(): continue
        zz = z[0] + s * (z[1] - z[0]) + r * (z[2] - z[0])
        yy, xx = gy[inside], gx[inside]; better = zz[inside] < depth[yy, xx]
        depth[yy[better], xx[better]] = zz[inside][better]; img[yy[better], xx[better]] = tag[t]
    return img


def measure(top_path, body_path, overlay=None):
    body = trimesh.load(body_path, force="mesh"); top = trimesh.load(top_path, force="scene")
    # each COLOUR region is its own mask: the v7 brown point was the leather corner under the tan rope's end — in a leather ∪ trim mask
    # the rope above made it wide and the opening kept it
    G = [(n, g) for n, g in top.geometry.items() if hasattr(g, "faces")]
    gar = np.concatenate([g.triangles for _, g in G]); T = np.concatenate([body.triangles, gar])
    tag = np.r_[np.zeros(len(body.faces), int)] if False else np.zeros(len(body.faces), int)
    tag = np.r_[tag, np.concatenate([np.full(len(g.faces), 1 if n.startswith("leather") else 2) for n, g in G])]
    gy = gar[:, :, 1]; ytop = gy.max(); y0, y1 = ytop - 0.04 - PAD, ytop + 0.03 + PAD
    k = int(round(OPEN_R / PX)); yy, xx = np.mgrid[-k:k + 1, -k:k + 1]; disk = xx ** 2 + yy ** 2 <= k * k
    res, tiles = {}, []
    for vn, yaw in VIEWS.items():
        a = np.radians(yaw); d = np.array([-np.sin(a), 0, -np.cos(a)]); u = np.array([np.cos(a), 0, -np.sin(a)])
        gu = (gar.reshape(-1, 3) @ u); half = np.abs(gu).max()
        for side, sg in (("left", 1), ("right", -1)):
            # outer torso side: from 45 % of the garment's half-width out to past its edge (the armpit, not the cleavage)
            ua, ub = sorted([sg * 0.45 * half, sg * (half + 0.03)])
            img = raster(T, tag, d, u, y0, y1, ua - PAD, ub + PAD)
            sc = 0.0; removed_all = np.zeros(img.shape, bool)
            core = np.zeros(img.shape, bool); p = int(PAD / PX); core[p:-p, p:-p] = True
            for role in (1, 2):
                mask = img == role; opened = ndimage.binary_opening(mask, structure=disk)
                removed = mask & ~opened
                lab, n = ndimage.label(removed); sizes = ndimage.sum(removed, lab, range(1, n + 1)) if n else []
                for i, s_ in enumerate(sizes):                             # < 1 mm² = raster noise
                    if s_ * PX * PX * 1e6 < 1.0: removed[lab == i + 1] = False
                dist = ndimage.distance_transform_edt(~opened) * PX
                if (removed & core).any(): sc = max(sc, float(dist[removed & core].max()))
                removed_all |= removed
            removed = removed_all; mask = img >= 1
            res[f"{vn}/{side}"] = round(sc * 1000, 1)
            if overlay:
                rgb = np.full(mask.shape + (3,), 255, np.uint8); rgb[img == 0] = (230, 200, 170); rgb[img == 1] = (90, 70, 50); rgb[img == 2] = (200, 170, 110)
                rgb[removed] = (230, 30, 30); tiles.append(rgb[::-1])
    if overlay:
        from PIL import Image
        h = max(t.shape[0] for t in tiles); row = np.full((h, sum(t.shape[1] + 6 for t in tiles), 3), 255, np.uint8); x = 0
        for t in tiles: row[:t.shape[0], x:x + t.shape[1]] = t; x += t.shape[1] + 6
        Image.fromarray(row).resize((row.shape[1] * 3, row.shape[0] * 3), Image.NEAREST).save(overlay)
    return res


def main(a):
    r = measure(a.top, a.body, a.overlay); worst = max(r, key=r.get)
    print(f"armpit point (longest narrow spur, mm): {r} · worst {worst} {r[worst]} (≤ {a.max_mm})")
    if r[worst] > a.max_mm: print(f"⛔ a point sticks out of the garment at the armpit ({worst}, {r[worst]} mm)"); sys.exit(1)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--top", required=True); ap.add_argument("--body", required=True)
    ap.add_argument("--max-mm", type=float, default=5.0); ap.add_argument("--overlay")
    main(ap.parse_args())

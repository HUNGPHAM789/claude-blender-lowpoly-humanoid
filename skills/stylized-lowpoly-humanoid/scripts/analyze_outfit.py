"""LEARN the torn leather outfit grammar from a sample outfit mesh (Boss 25/10/2026: «quét outfit luôn … sẽ tìm ra được belt nằm chỗ
nào, lớp lót chỗ nào thì tô màu khá dễ»). Teacher meshes only — never shipped.

  python3 analyze_outfit.py --outfit <outfit_fit.glb> --out <dir>/<name> [--kind skirt|top]
  ⇒ <name>_outfit.json · <name>_parts.png (faces coloured by part) · <name>_parts.glb (same mesh, one material per part)

Frame: glTF metres, Y up, body faces +Z. The garment is unrolled around its own vertical axis: θ (0 = front), y, ρ (radius).
  belt      = the top band (skirt) where the median radius bulges into a ring ≥ BELT_BULGE above the band just below it
  ornament  = faces at belt height, front (|θ| < 35°), standing ≥ 1.2 cm proud of the belt ring
  layers    = horizontal rays from the axis outwards on a θ×y grid: every hit pair (in/out surface) is one leather layer;
              faces hit LAST = outer layer, faces hit before = lining (the lighter strips that show under the outer edge)
  hem       = lowest y per θ bin → torn-edge signal: teeth = local minima with ≥ 1 cm prominence (count, depth, width, spread)
"""
import argparse, json, math
import numpy as np
import trimesh
from PIL import Image, ImageDraw

BELT_BULGE, THETA_BINS, Y_BINS = 1.06, 96, 48
PART_RGB = {"belt": (196, 164, 108), "ornament": (120, 116, 108), "outer": (74, 53, 37), "lining": (176, 138, 92)}


def ray_hits(tris, O, D, chunk=40):
    """Möller–Trumbore, vectorised: for each ray all hit (triangle index, distance), sorted by distance (no rtree needed)."""
    v0, e1, e2 = tris[:, 0], tris[:, 1] - tris[:, 0], tris[:, 2] - tris[:, 0]; out = []
    for s0 in range(0, len(O), chunk):
        o = O[s0:s0 + chunk, None, :]; d = D[s0:s0 + chunk, None, :]
        p = np.cross(d, e2[None]); det = np.einsum("rfk,fk->rf", p, e1)
        ok = np.abs(det) > 1e-12; inv = np.where(ok, 1.0 / np.where(ok, det, 1), 0)
        tv = o - v0[None]; u = np.einsum("rfk,rfk->rf", tv, p) * inv
        q = np.cross(tv, e1[None]); v = np.einsum("rfk,rfk->rf", d, q) * inv; t = np.einsum("rfk,fk->rf", q, e2) * inv
        hit = ok & (u >= 0) & (v >= 0) & (u + v <= 1) & (t > 1e-6)
        for r in range(hit.shape[0]):
            f = np.where(hit[r])[0]; out.append(f[np.argsort(t[r, f])])
    return out


def image_roles(raw_path, image_path, fit_json, fit_mesh):
    """colour roles per FIT face from the clean asset image: find the image camera on the raw (generator-frame) mesh, z-buffer the
    raw faces, read the median pixel colour, snap to the game leather palette, then carry the label to the fitted mesh."""
    import sys, os
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from color_mesh import view, fit, iou
    raw = trimesh.load(raw_path, force="mesh"); img = np.asarray(Image.open(image_path).convert("RGB")); mask = img.min(axis=2) < 245
    sub = trimesh.Trimesh(raw.vertices, raw.faces[np.random.default_rng(0).choice(len(raw.faces), min(8000, len(raw.faces)), replace=False)], process=False)
    _, yw, pt = max((iou(sub, mask, a, b), a, b) for a in range(-60, 61, 6) for b in (-10, 0, 10, 20))
    _, yw, pt = max((iou(sub, mask, a, b), a, b) for a in range(yw - 4, yw + 5, 2) for b in range(pt - 6, pt + 7, 3))
    P = fit(sub, mask, yw, pt); x, y, d = view(raw.vertices, yw, pt); u, v = P(x, y); F = raw.faces
    zb = Image.new("I", mask.shape[::-1], 0); dz = ImageDraw.Draw(zb)
    for i in np.argsort(d[F].mean(axis=1)): dz.polygon([(u[j], v[j]) for j in F[i]], fill=int(i) + 1)
    Z = np.asarray(zb); ok = mask & (img.min(axis=2) < 232); col = np.full((len(F), 3), np.nan)
    for fid in np.unique(Z[ok]):
        if fid: sel = (Z == fid) & ok; col[fid - 1] = np.median(img[sel], axis=0)
    seen = ~np.isnan(col[:, 0])
    pal = {"outer": (74, 53, 37), "lining": (176, 138, 92), "belt": (196, 164, 108), "ornament": (120, 116, 108)}
    names = list(pal); Pm = np.array(list(pal.values()), float)
    lab = np.full(len(F), -1); lab[seen] = np.argmin(((col[seen][:, None] - Pm[None]) ** 2).sum(-1), axis=1)
    from scipy.spatial import cKDTree
    C = raw.triangles_center; kd = cKDTree(C[seen]); _, j = kd.query(C[~seen]); lab[~seen] = lab[seen][j]   # hidden faces: nearest seen
    M = np.array(json.load(open(fit_json))["raw_to_fit"]); Cf = (np.c_[C, np.ones(len(C))] @ M.T)[:, :3]
    _, k = cKDTree(Cf).query(fit_mesh.triangles_center)
    print(f"  image camera yaw {yw} pitch {pt} · faces seen {seen.sum()}/{len(F)}")
    image_roles.seen = seen[k]                                        # per FIT face: did the image actually see it?
    return np.array([names[i] for i in lab[k]], dtype=object)


def main(path, out, kind, image=None, raw=None, fit_json=None):
    m = trimesh.load(path, force="mesh"); m = trimesh.Trimesh(m.vertices, m.faces, process=True)
    V, F = m.vertices, m.faces; C = m.triangles_center
    ax = np.array([V[:, 0].mean(), 0, V[:, 2].mean()])
    y0, y1 = V[:, 1].min(), V[:, 1].max(); Hh = y1 - y0
    th = np.degrees(np.arctan2(C[:, 0] - ax[0], C[:, 2] - ax[2])); rho = np.hypot(C[:, 0] - ax[0], C[:, 2] - ax[2])
    part = np.array(["outer"] * len(F), dtype=object)
    # ---- radial profile and belt
    yb = np.linspace(y0, y1, Y_BINS + 1); prof = []
    for i in range(Y_BINS):
        s = (C[:, 1] >= yb[i]) & (C[:, 1] < yb[i + 1]); prof.append(float(np.median(rho[s])) if s.sum() > 3 else np.nan)
    prof = np.array(prof); belt = None
    if kind == "skirt":
        top = Y_BINS - 1; cand = []
        for i in range(int(Y_BINS * 0.70), Y_BINS):                  # belt lives in the top 30 %
            below = np.nanmedian(prof[max(0, i - 6):max(1, i - 2)])
            if not np.isnan(prof[i]) and prof[i] >= BELT_BULGE * below: cand.append(i)
        if not cand: cand = list(range(int(Y_BINS * 0.86), Y_BINS))  # no clear bulge: the top 14 % band
        lo, hi = yb[min(cand)], yb[max(cand) + 1]; ring = float(np.nanmedian(prof[min(cand):max(cand) + 1]))
        part[(C[:, 1] >= lo) & (C[:, 1] <= hi)] = "belt"
        orn = (C[:, 1] >= lo - 0.02) & (C[:, 1] <= hi + 0.04) & (np.abs(th) < 35) & (rho > ring + 0.012)
        part[orn] = "ornament"
        belt = {"y_from_top_cm": [round(float(y1 - hi) * 100, 1), round(float(y1 - lo) * 100, 1)], "band_height_cm": round(float(hi - lo) * 100, 1),
                "ring_radius_cm": round(ring * 100, 1), "ornament_faces": int(orn.sum()),
                "ornament_height_cm": round(float(np.ptp(C[orn, 1])) * 100, 1) if orn.any() else 0.0,
                "ornament_proud_cm": round(float((rho[orn].max() - ring)) * 100, 1) if orn.any() else 0.0}
    # ---- layers by ray casting
    hits_last = np.zeros(len(F), int); hits_inner = np.zeros(len(F), int); layer_counts = []
    ys = np.linspace(y0 + 0.03 * Hh, (yb[int(Y_BINS * 0.70)] if kind == "skirt" else y1) - 0.01, 18)
    origins, dirs = [], []
    for y in ys:
        for t in np.linspace(-180, 180, THETA_BINS, endpoint=False):
            a = math.radians(t); origins.append([ax[0], y, ax[2]]); dirs.append([math.sin(a), 0, math.cos(a)])
    for T in ray_hits(m.triangles, np.array(origins, float), np.array(dirs, float)):
        if not len(T): continue
        layer_counts.append(len(T) / 2)
        hits_last[T[-1]] += 1
        if len(T) >= 2: hits_last[T[-2]] += 1                      # the outer layer's inner surface too
        for t_ in T[:-2]: hits_inner[t_] += 1
    lining = (hits_inner > hits_last) & (part == "outer")
    # grow lining over its connected surface patch (faces between ray samples)
    adj = {}
    for a_, b_ in m.face_adjacency: adj.setdefault(a_, []).append(b_); adj.setdefault(b_, []).append(a_)
    for _ in range(3):
        grow = lining.copy()
        for f in np.where(lining)[0]:
            for g in adj.get(f, []):
                if part[g] == "outer" and hits_last[g] == 0: grow[g] = True
        lining = grow
    part[lining] = "lining"
    if image:                                                          # colour roles from the clean asset image (layers are FUSED in
        roles = image_roles(raw, image, fit_json, m)                   # generated meshes, so the lining only exists as colour)
        part[(roles == "lining") & (part == "outer")] = "lining"
        part[(roles == "belt") & (C[:, 1] > y0 + 0.6 * Hh) & (part != "ornament")] = "belt"
        part[(roles == "ornament") & (C[:, 1] > y0 + 0.6 * Hh)] = "ornament"
    # ---- hem
    tb = np.linspace(-180, 180, THETA_BINS + 1); hem = []
    for i in range(THETA_BINS):
        s = (th >= tb[i]) & (th < tb[i + 1]); hem.append(float(C[s, 1].min()) if s.any() else np.nan)
    hem = np.array(hem); hcm = (hem - np.nanmin(hem)) * 100
    teeth = []
    for i in range(THETA_BINS):
        w = [hcm[(i + k) % THETA_BINS] for k in range(-4, 5)]
        if not np.isnan(hcm[i]) and hcm[i] == np.nanmin(w):
            prom = np.nanmax(w) - hcm[i]
            if prom >= 1.0: teeth.append((i, prom))
    widths = np.diff([t[0] for t in teeth] + [teeth[0][0] + THETA_BINS]) * 360 / THETA_BINS if len(teeth) > 1 else []
    res = {"kind": kind, "height_cm": round(float(Hh) * 100, 1), "radius_profile_cm_bottom_to_top": [None if np.isnan(p) else round(p * 100, 1) for p in prof],
           "flare_bottom_over_top": round(float(np.nanmedian(prof[:6]) / np.nanmedian(prof[-10:-4])), 2), "belt": belt,
           "layers_per_ray_p10_50_90": [round(float(np.percentile(layer_counts, p)), 1) for p in (10, 50, 90)] if layer_counts else None,
           "faces_by_part": {k: int((part == k).sum()) for k in PART_RGB},
           "hem": {"teeth": len(teeth), "tooth_depth_cm_p10_50_90": [round(float(np.percentile([t[1] for t in teeth], p)), 1) for p in (10, 50, 90)] if teeth else None,
                   "tooth_spacing_deg_p10_50_90": [round(float(np.percentile(widths, p)), 1) for p in (10, 50, 90)] if len(widths) else None,
                   "hem_spread_cm": round(float(np.nanmax(hcm)), 1)}}
    json.dump(res, open(out + "_outfit.json", "w"), indent=1)
    # ---- outputs: coloured parts GLB + picture
    sc = trimesh.Scene()
    for k, rgb in PART_RGB.items():
        s = np.where(part == k)[0]
        if not len(s): continue
        sub = trimesh.Trimesh(V, F[s], process=False); sub.remove_unreferenced_vertices(); sub.visual.face_colors = list(rgb) + [255]
        sc.add_geometry(sub, geom_name=k, node_name=k)
    sc.export(out + "_parts.glb")
    col = np.array([PART_RGB[p] for p in part]); tiles = []
    for yaw in (0, 90, 180, 270):
        a = math.radians(yaw); R = np.array([[math.cos(a), 0, math.sin(a)], [0, 1, 0], [-math.sin(a), 0, math.cos(a)]])
        W = (V - ax - [0, (y0 + y1) / 2, 0]) @ R.T; s = 300 / (1.3 * max(np.ptp(V[:, 0]), Hh)); im = Image.new("RGB", (300, 320), (245, 245, 245)); d = ImageDraw.Draw(im)
        for i in np.argsort(W[F][:, :, 2].mean(axis=1)):
            tri_ = W[F[i]]
            if np.cross(tri_[1] - tri_[0], tri_[2] - tri_[0])[2] <= 0: continue
            d.polygon([(150 + x * s, 160 - y * s) for x, y, _ in tri_], fill=tuple(int(v) for v in col[i]))
        tiles.append(im)
    sheet = Image.new("RGB", (1200, 320)); [sheet.paste(t, (300 * i, 0)) for i, t in enumerate(tiles)]; sheet.save(out + "_parts.png")
    print(json.dumps({k: v for k, v in res.items() if k != "radius_profile_cm_bottom_to_top"}, indent=1))


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--outfit", required=True); ap.add_argument("--out", required=True)
    ap.add_argument("--kind", default="skirt", choices=["skirt", "top"])
    ap.add_argument("--image"); ap.add_argument("--raw"); ap.add_argument("--fit-json")
    a = ap.parse_args(); main(a.outfit, a.out, a.kind, a.image, a.raw, a.fit_json)

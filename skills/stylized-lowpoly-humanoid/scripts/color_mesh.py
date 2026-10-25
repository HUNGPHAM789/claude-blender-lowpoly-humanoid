"""Paint a low-poly body with flat per-face colours taken from the clean input image (Boss 25/10/2026: «color và rig model»).

  python3 color_mesh.py --glb lp.glb --xform aligned.xform.json --image front_sq.png [--image back_sq.png:back] --out colored.glb [--colors 7]

1. camera of the input image = orthographic view of the generator's raw frame, turned by yaw/pitch: searched by silhouette IoU
   of the raw mesh against the image mask (the input is a 3/4 render, not a front view)
2. every final face is mapped back to the raw frame (aligned.xform.json), projected; a face-id z-buffer decides which faces the
   image actually shows; visible faces take the median image colour inside their triangle
3. hidden faces (back, under the arms) take the colour of the nearest visible face in 3D
4. colours snap to a k-means palette (default 7) ⇒ flat low-poly look, exported as one PBR material per colour (sub-meshes)
"""
import argparse, json, math, os
import numpy as np
import trimesh
from PIL import Image, ImageDraw
from scipy.spatial import cKDTree

import sys
sys.path.insert(0, os.path.expanduser("~/projects/lpm-faceless-humanoid/theme")); import theme_colors as TC   # game theme (Đất ấm)
# GAME PALETTE for characters (Boss 25/10/2026: «dùng bảng màu của game mình ghibli») — every colour already used in the game:
GAME = {"skin": TC.DA["dat_am"],                    # settler skin, theme Đất ấm
        "hair": (58, 40, 28),                       # hair_outfit MAU_TOC dark_brown
        "leather_dark": (74, 53, 37),               # Ghibli M_Bark
        "leather_tan": (176, 138, 92),              # settler outfit 'ao'
        "rope_bone": (196, 164, 108),               # tools 'may' (rope / bone belt)
        "charcoal": (32, 30, 28)}                   # Ghibli M_Charcoal (eyes, brows)
SHOULDER = 0.80      # fraction of height: hair lives above, leather below
LIGHT_W = 0.35        # weight of CIE lightness vs the colour axes when building the palette
MERGE_AB, MERGE_L = 14.0, 30.0   # same hue family ⇒ one colour (lit/shaded skin); tan leather (yellower) stays apart


def view(V, yaw, pitch):
    a, p = math.radians(yaw), math.radians(pitch)
    x = V[:, 0] * math.cos(a) + V[:, 2] * math.sin(a); z = -V[:, 0] * math.sin(a) + V[:, 2] * math.cos(a)
    y = V[:, 1] * math.cos(p) - z * math.sin(p); d = V[:, 1] * math.sin(p) + z * math.cos(p)
    return x, y, d                                    # d = towards the camera (+)


def fit(raw, mask, yaw, pitch, ref=None):
    x, y, _ = view(raw.vertices if ref is None else ref, yaw, pitch)
    ys, xs = np.where(mask); top, bot = ys.min(), ys.max(); cx = (xs.min() + xs.max()) / 2
    s = (bot - top) / (y.max() - y.min())
    return lambda X, Y: (cx + (X - (x.max() + x.min()) / 2) * s, top + (y.max() - Y) * s)


def iou(raw, mask, yaw, pitch):
    P = fit(raw, mask, yaw, pitch); x, y, _ = view(raw.vertices, yaw, pitch); u, v = P(x, y)
    im = Image.new("L", mask.shape[::-1], 0); d = ImageDraw.Draw(im)
    for t in raw.faces: d.polygon([(u[i], v[i]) for i in t], fill=255)
    m = np.asarray(im) > 0
    return (m & mask).sum() / (m | mask).sum()


def sample_view(lp, Vr, path, yaw_range, pitches=(-10, 0, 10, 20)):
    """camera search for one image + per-face colour and facing score (0 where the face is hidden)."""
    img = np.asarray(Image.open(path).convert("RGB")); mask = img.min(axis=2) < 245
    small = trimesh.Trimesh(vertices=Vr, faces=lp.faces, process=False)
    _, yw0, pt0 = max((iou(small, mask, yw, pt), yw, pt) for yw in yaw_range for pt in pitches)
    sc, yaw, pitch = max((iou(small, mask, yw, pt), yw, pt) for yw in range(yw0 - 4, yw0 + 5, 2) for pt in range(pt0 - 6, pt0 + 7, 3))
    P = fit(small, mask, yaw, pitch)
    x, y, d = view(Vr, yaw, pitch); u, v = P(x, y)
    F = lp.faces; n = len(F)
    zbuf = Image.new("I", mask.shape[::-1], 0); dz = ImageDraw.Draw(zbuf)
    for i in np.argsort(d[F].mean(axis=1)):                         # painter's order: far first ⇒ face-id z-buffer
        dz.polygon([(u[j], v[j]) for j in F[i]], fill=int(i) + 1)
    Z = np.asarray(zbuf); ok = mask & (img.min(axis=2) < 232)       # skip white background bleeding in at the edges
    col = np.zeros((n, 3)); face = np.zeros(n)
    T = np.c_[x, y, d][F]; nrm = np.cross(T[:, 1] - T[:, 0], T[:, 2] - T[:, 0]); nrm /= np.linalg.norm(nrm, axis=1, keepdims=True) + 1e-12
    ids = np.unique(Z[ok])
    for fid in ids:
        if fid == 0: continue
        sel = (Z == fid) & ok
        if sel.sum() < 3: continue
        col[fid - 1] = np.median(img[sel], axis=0); face[fid - 1] = abs(nrm[fid - 1, 2]) + 1e-3
    print(f"  {os.path.basename(path)}: camera yaw {yaw} pitch {pitch} · IoU {sc:.2f} · sees {(face > 0).sum()}/{n} faces")
    return col, face, {"image": path, "yaw": yaw, "pitch": pitch, "iou": round(float(sc), 3)}


def main(glb, xform, images, out, ncol):
    X = json.load(open(xform)); M = np.array(X["raw_to_final"]); Mi = np.linalg.inv(M)
    lp = trimesh.load(glb, force="mesh")
    Vr = (np.c_[lp.vertices, np.ones(len(lp.vertices))] @ Mi.T)[:, :3]          # final → generator (raw) frame
    F = lp.faces; n = len(F)
    views = []; front_yaw = None
    for spec in images:
        path, _, kind = spec.partition(":")
        rng_ = range(-90, 91, 6) if kind != "back" else range(front_yaw + 100, front_yaw + 261, 6)
        c, f, info = sample_view(lp, Vr, path, rng_); views.append((c, f)); info["kind"] = kind or "front"
        if kind != "back": front_yaw = info["yaw"]
        views[-1] = (c, f, info)
    best = np.argmax(np.stack([v[1] for v in views]), axis=0)        # per face: the image that looks at it most squarely
    col = np.stack([v[0] for v in views])[best, np.arange(n)]
    vis = np.stack([v[1] for v in views]).max(axis=0) > 0
    # hidden faces: grow colours over the surface (face adjacency), not through the air
    adj = [[] for _ in range(n)]
    for a, b in lp.face_adjacency: adj[a].append(b); adj[b].append(a)
    from collections import deque
    q = deque(np.where(vis)[0]); got = vis.copy()
    while q:
        i = q.popleft()
        for j in adj[i]:
            if not got[j]: col[j] = col[i]; got[j] = True; q.append(j)
    if (~got).any():
        C = lp.vertices[F].mean(axis=1); kd = cKDTree(C[got]); _, j = kd.query(C[~got]); col[~got] = col[got][j]
    # palette: cluster in CIELAB with lightness down-weighted, so lit and shaded skin are ONE colour while hue changes
    # (skin / tan leather / dark leather / hair / belt) stay apart; each colour = the median of its faces (albedo, not shading)
    def lab_(rgb):
        c = rgb / 255.0; c = np.where(c > 0.04045, ((c + 0.055) / 1.055) ** 2.4, c / 12.92)
        xyz = c @ np.array([[0.4124, 0.3576, 0.1805], [0.2126, 0.7152, 0.0722], [0.0193, 0.1192, 0.9505]]).T / [0.9505, 1.0, 1.089]
        f = np.where(xyz > 0.008856, np.cbrt(xyz), 7.787 * xyz + 16 / 116)
        return np.c_[116 * f[:, 1] - 16, 500 * (f[:, 0] - f[:, 1]), 200 * (f[:, 1] - f[:, 2])]
    feat = lab_(col) * [LIGHT_W, 1, 1]
    rng = np.random.default_rng(0); idx = rng.choice(np.where(vis)[0], ncol, replace=False); cen = feat[idx].copy()
    for _ in range(40):
        lab = np.argmin(((feat[:, None, :] - cen[None]) ** 2).sum(-1), axis=1)
        cen = np.array([feat[lab == k].mean(axis=0) if (lab == k).any() else cen[k] for k in range(ncol)])
    cen = np.array([np.median(col[(lab == k) & vis], axis=0) if ((lab == k) & vis).any() else col[lab == k].mean(axis=0) for k in range(ncol)])
    # merge palette entries of the same hue family (lit vs shaded skin): a/b distance < MERGE_AB and lightness gap < MERGE_L
    while True:
        L_ = lab_(cen); best_ = None
        for i in range(len(cen)):
            for j in range(i + 1, len(cen)):
                dab = np.hypot(*(L_[i, 1:] - L_[j, 1:])); dl = abs(L_[i, 0] - L_[j, 0])
                if dab < MERGE_AB and dl < MERGE_L and (best_ is None or dab < best_[0]): best_ = (dab, i, j)
        if best_ is None: break
        _, i, j = best_; lab[lab == j] = i; lab[lab > j] -= 1
        cen = np.delete(cen, j, axis=0); cen[i] = np.median(col[(lab == i) & vis], axis=0)
    ncol = len(cen)
    # snap every measured colour to the nearest GAME colour (CIELAB) ⇒ the character shares the world's palette
    G = np.array(list(GAME.values()), float); GL = lab_(G); CL = lab_(cen)
    role = [list(GAME)[int(np.argmin(((GL - c) ** 2).sum(1)))] for c in CL]
    cen = np.array([GAME[r] for r in role], float)
    print("  palette roles:", dict(zip(role, np.bincount(lab, minlength=ncol).tolist())))
    for _ in range(2):                                              # de-speckle: a face outvoted by its neighbours joins them
        new = lab.copy()
        for i in range(n):
            nb = lab[adj[i]]
            if len(nb):
                v_, c_ = np.unique(nb, return_counts=True)
                if c_.max() >= 2 and v_[np.argmax(c_)] != lab[i] and (nb == lab[i]).sum() == 0: new[i] = v_[np.argmax(c_)]
        lab = new
    # per-face roles; region rule: dark brown below the shoulders is leather, not hair (the two game colours are close)
    froles = np.array(role, dtype=object)[lab]
    Cz = lp.vertices[F].mean(axis=1)[:, 1]; Hm = lp.vertices[:, 1].max()           # final mesh is Y-up
    froles[(froles == "hair") & (Cz < SHOULDER * Hm)] = "leather_dark"
    # one PBR material per role (no textures): flat low-poly colours that every engine reads the same way
    scene = trimesh.Scene(); counts = {}
    for r in GAME:
        sel = np.where(froles == r)[0]
        if not len(sel): continue
        counts[r] = int(len(sel))
        sub = trimesh.Trimesh(vertices=lp.vertices, faces=F[sel], process=False); sub.remove_unreferenced_vertices()
        rgba = TC.mau(GAME[r])                                       # sRGB → linear per the active theme (⛔ raw /255 = washed «nhạt nhà»)
        sub.visual = trimesh.visual.TextureVisuals(material=trimesh.visual.material.PBRMaterial(name=f"M_{r}", baseColorFactor=rgba, roughnessFactor=0.85, metallicFactor=0.0))
        scene.add_geometry(sub, geom_name=r, node_name=r)
    scene.export(out)
    print("  faces per role:", counts)
    json.dump({"roles": counts, "views": [v[2] for v in views], "visible_faces": int(vis.sum()), "faces": n,
               "palette_rgb": cen.round().astype(int).tolist(), "faces_per_colour": np.bincount(lab, minlength=ncol).tolist()},
              open(out.replace(".glb", "") + ".color.json", "w"), indent=1)
    print(f"seen by an image {vis.sum()}/{n} faces · palette {cen.round().astype(int).tolist()} → {out}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    for k in ("--glb", "--xform", "--out"): ap.add_argument(k, required=True)
    ap.add_argument("--image", action="append", required=True, help="front image; add more as path:back for a 3/4 back view")
    ap.add_argument("--colors", type=int, default=7)
    a = ap.parse_args(); main(a.glb, a.xform, a.image, a.out, a.colors)

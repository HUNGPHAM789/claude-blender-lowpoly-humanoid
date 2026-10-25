"""Put an image-to-3D mesh (Hunyuan3D-2 GLB) into the body frame of the reference sheet.

  python3 align_to_reference.py --sex male --glb <hy3d.glb> --out <aligned.glb>

1. one mesh, feet on Z = 0, ankle centre on the Z axis
2. scale so the full height (hair top) = spec scale_m (figure units → metres, same as build_body.py)
3. yaw search (every 5°, then 1°) that maximises the summed silhouette IoU against the sheet's front + side + back masks
   (the input image is a 3/4 view, so the generator returns the body turned by an unknown angle)
Writes a Y-up GLB that faces +Z, like build_body.py.
"""
import argparse, json, math, os, sys
import numpy as np
import trimesh
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__)); SPEC = os.path.join(HERE, "..", "spec")
sys.path.insert(0, HERE)
from build_body import load_zup



def masks(sex):
    out = {}
    for v in ("front", "side", "back"):
        m = np.asarray(Image.open(os.path.join(SPEC, "measure", f"{sex}_{v}_mask.png")).convert("L")) > 0
        ys, xs = np.where(m); m = m[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
        out[v] = m
    return out


def sil(V, F, view, H):
    """silhouette of V (figure units, feet z=0, height 1) as an H-row mask, cropped to its bbox."""
    P = {"front": V[:, [0, 2]], "side": V[:, [1, 2]], "back": V[:, [0, 2]] * [-1, 1]}[view]
    s = H / max(1e-6, P[:, 1].max()); x0 = P[:, 0].min()
    W = int((P[:, 0].max() - x0) * s) + 2
    im = Image.new("L", (W, H + 2), 0); d = ImageDraw.Draw(im)
    for t in F:
        d.polygon([((P[i, 0] - x0) * s, H - P[i, 1] * s) for i in t], fill=255)
    m = np.asarray(im) > 0; ys, xs = np.where(m)
    return m[ys.min():ys.max() + 1, xs.min():xs.max() + 1]


def iou(a, b):
    H = min(a.shape[0], b.shape[0]); W = max(a.shape[1], b.shape[1])
    A = np.zeros((H, W), bool); B = np.zeros((H, W), bool)
    ra = np.asarray(Image.fromarray(a).resize((a.shape[1] * H // a.shape[0] or 1, H))) > 0
    rb = np.asarray(Image.fromarray(b).resize((b.shape[1] * H // b.shape[0] or 1, H))) > 0
    W = max(ra.shape[1], rb.shape[1]); A = np.zeros((H, W), bool); B = np.zeros((H, W), bool)
    A[:, (W - ra.shape[1]) // 2:(W - ra.shape[1]) // 2 + ra.shape[1]] = ra
    B[:, (W - rb.shape[1]) // 2:(W - rb.shape[1]) // 2 + rb.shape[1]] = rb
    return (A & B).sum() / max(1, (A | B).sum())


def main(sex, glb, out):
    spec = json.load(open(os.path.join(SPEC, f"{sex}_spec.json"))); k = spec["scale_m"]
    m = load_zup(glb); V = m.vertices.copy(); F = m.faces
    # X tracks every affine step so colour projection can map the final mesh back to the generator's (= input image's) frame
    X = np.array([[-1, 0, 0, 0], [0, 0, 1, 0], [0, 1, 0, 0], [0, 0, 0, 1.]])          # glTF raw → build axes (load_zup)
    def step(A, t=(0, 0, 0)):
        nonlocal_X[0] = np.r_[np.c_[A, t], [[0, 0, 0, 1]]] @ nonlocal_X[0]
    nonlocal_X = [X]
    z0 = V[:, 2].min(); V[:, 2] -= z0; step(np.eye(3), (0, 0, -z0)); h0 = V[:, 2].max(); V /= h0; step(np.eye(3) / h0)
    # the sheet's cast shadow comes back as a ground plate fused to the soles: drop low faces that lie away from the real
    # footprint (= the ankle/foot slice just above the plate)
    from scipy.spatial import cKDTree
    foot = V[(V[:, 2] > 0.035) & (V[:, 2] < 0.08)][:, :2]
    tri = V[F]; low = tri[:, :, 2].max(axis=1) < 0.035
    far = cKDTree(foot).query(tri[:, :, :2].mean(axis=1))[0] > 0.035
    F = F[~(low & far)]
    used = np.unique(F); remap = -np.ones(len(V), int); remap[used] = np.arange(len(used)); V = V[used]; F = remap[F]
    parts = trimesh.Trimesh(vertices=V, faces=F, process=False).split(only_watertight=False)
    big = max(parts, key=lambda p: len(p.faces)); keep = [p for p in parts if len(p.faces) > 0.02 * len(big.faces)]
    mm = trimesh.util.concatenate(keep); V = mm.vertices.copy(); F = mm.faces
    z0 = V[:, 2].min(); V[:, 2] -= z0; step(np.eye(3), (0, 0, -z0)); h0 = V[:, 2].max(); V /= h0; step(np.eye(3) / h0)
    low = V[:, 2] < 0.15; cxy = V[low][:, :2].mean(axis=0); V[:, :2] -= cxy; step(np.eye(3), (-cxy[0], -cxy[1], 0))   # ankle centre on the axis
    # facing from geometry, not from silhouettes (front/back look alike): shoulder line = widest direction at chest height,
    # forward = the side the toes stick out to (toes vs ankles)
    # lateral axis = line through the two ankles (hair over the shoulders fools a chest-width axis)
    ank_pts = V[(V[:, 2] > 0.06) & (V[:, 2] < 0.12)][:, :2]
    c = ank_pts[np.argsort(ank_pts @ np.linalg.eigh(np.cov(ank_pts.T))[1][:, -1])]
    for _ in range(10):                                            # 2-means on the ankle slice
        a0, a1 = c[: len(c) // 2].mean(axis=0), c[len(c) // 2:].mean(axis=0)
        lab = np.linalg.norm(ank_pts - a0, axis=1) > np.linalg.norm(ank_pts - a1, axis=1)
        a0, a1 = ank_pts[~lab].mean(axis=0), ank_pts[lab].mean(axis=0); c = np.r_[ank_pts[~lab], ank_pts[lab]]
    lat = (a1 - a0) / np.linalg.norm(a1 - a0); fwd = np.array([-lat[1], lat[0]])
    toes = V[V[:, 2] < 0.03][:, :2].mean(axis=0); ank = V[(V[:, 2] > 0.09) & (V[:, 2] < 0.13)][:, :2].mean(axis=0)
    if (toes - ank) @ fwd < 0: fwd = -fwd
    best = math.degrees(math.atan2(-fwd[0], fwd[1]))                  # rotate so fwd → +Y
    M = masks(sex); H = 200
    sub = F if len(F) < 20000 else F[np.random.default_rng(0).choice(len(F), 20000, replace=False)]
    def score(deg):
        a = math.radians(deg); R = np.array([[math.cos(a), -math.sin(a), 0], [math.sin(a), math.cos(a), 0], [0, 0, 1]])
        W_ = V @ R.T
        return sum(iou(sil(W_, sub, v, H), M[v]) for v in ("front", "side", "back")) / 3
    def side_score(deg):
        a = math.radians(deg); R = np.array([[math.cos(a), -math.sin(a), 0], [math.sin(a), math.cos(a), 0], [0, 0, 1]])
        return iou(sil(V @ R.T, sub, "side", H), M["side"])
    # toes can mislead (feet splayed): the side silhouette is not symmetric (face, chest/bust, glutes) ⇒ it decides front vs back
    if side_score(best + 180) > side_score(best): best += 180
    best = max([best + d for d in range(-10, 11, 2)], key=score); sc = score(best)    # small trim only
    a = math.radians(best); R = np.array([[math.cos(a), -math.sin(a), 0], [math.sin(a), math.cos(a), 0], [0, 0, 1]])
    V = (V @ R.T) * k; step(R * k)
    mesh = trimesh.Trimesh(vertices=V, faces=F, process=False)
    Y = np.array([[-1, 0, 0, 0], [0, 0, 1, 0], [0, 1, 0, 0], [0, 0, 0, 1.]])
    mesh.apply_transform(Y)   # → Y-up, faces +Z
    mesh.export(out)
    json.dump({"raw_to_final": (Y @ nonlocal_X[0]).tolist(), "raw": os.path.abspath(glb), "yaw_deg": best, "sex": sex},
              open(out.replace(".glb", "") + ".xform.json", "w"), indent=1)
    print(f"aligned yaw {best}° · mean IoU {sc:.3f} · height {k:.3f} m · {len(F)} tris → {out}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--sex", required=True); ap.add_argument("--glb", required=True); ap.add_argument("--out", required=True)
    a = ap.parse_args(); main(a.sex, a.glb, a.out)

"""Fit a separately generated layer (hair, outfit piece, base body) onto the dressed character (Boss 25/10/2026: «kêu codex nó tách
tóc riêng, quần áo riêng … như vậy là có asset tóc và outfit?»).

  python3 fit_layer.py --source <layer_raw.glb> --target <dressed_colored.glb> --roles hair[,leather_dark…] [--ymin f --ymax f] --out <layer_fit.glb>

Target points = the dressed mesh's faces whose material role is in --roles (and, optionally, inside a height band as a fraction
of the body height). Source = the generator's raw layer mesh. Init: bbox scale + centre match, then yaw candidates every 30°;
each runs ICP with uniform scale; the lowest mean distance wins. Writes a Y-up GLB in the dressed mesh's frame + a JSON report.
"""
import argparse, json, math
import numpy as np
import trimesh
from scipy.spatial import cKDTree


def role_points(target, roles, ymin, ymax):
    """points sampled on the target's faces whose geometry name (= colour role) is in roles, inside the height band."""
    sc = trimesh.load(target, force="scene"); H = None; pts = []
    allv = np.vstack([g.vertices for g in sc.dump()]); H = allv[:, 1].max() - allv[:, 1].min(); y0 = allv[:, 1].min()
    for name, g in sc.geometry.items():
        if not any(name.startswith(r) for r in roles): continue
        p, _ = trimesh.sample.sample_surface(g, max(200, len(g.faces) * 4), seed=0)
        keep = (p[:, 1] >= y0 + ymin * H) & (p[:, 1] <= y0 + ymax * H); pts.append(p[keep])
    return np.vstack(pts), H


def main(source, target, roles, ymin, ymax, out, back_heavy=False, inflate=1.0):
    T, H = role_points(target, roles, ymin, ymax)
    src = trimesh.load(source, force="mesh"); S = src.vertices
    sub = S[np.random.default_rng(0).choice(len(S), min(4000, len(S)), replace=False)]
    kd = cKDTree(T)
    best = None
    s0 = (np.ptp(T[:, 1]) / max(np.ptp(S[:, 1]), 1e-9))
    for yaw in range(0, 360, 30):
        a = math.radians(yaw); R = np.array([[math.cos(a), 0, math.sin(a)], [0, 1, 0], [-math.sin(a), 0, math.cos(a)]])
        M0 = np.eye(4); M0[:3, :3] = R * s0; M0[:3, 3] = T.mean(axis=0) - (S.mean(axis=0) @ (R * s0).T)
        try:
            M, _, cost = trimesh.registration.icp(sub, T, initial=M0, threshold=1e-6, max_iterations=60, reflection=False, scale=True)
        except Exception:
            continue
        P = (np.c_[sub, np.ones(len(sub))] @ M.T)[:, :3]
        d_src = kd.query(P)[0].mean(); d_tgt = cKDTree(P).query(T)[0].mean()      # both directions: no shrinking into a corner
        score = d_src + d_tgt
        if back_heavy:                                                  # ponytail/long hair: the lowest 30 % of the piece hangs BEHIND
            low = P[P[:, 1] < np.percentile(P[:, 1], 30)]               # the head (glTF −Z = back); penalise fits that put it in front
            if len(low) and low[:, 2].mean() > T[:, 2].mean() - 0.05: score += 1.0     # must sit ≥ 5 cm behind the hair centre
        if best is None or score < best[0]: best = (score, yaw, M, d_src, d_tgt)
    if back_heavy:                                                      # ICP spins the piece back to one minimum whatever the start, so
        best = None                                                     # for hair with a ponytail: rotation is SEARCHED (5°), never ICP-fitted;
        topT = T[T[:, 1] > np.percentile(T[:, 1], 50)]                  # scale = height ratio, position = match the crowns (upper halves)
        for yaw, k_ in ((y_, k_) for y_ in range(0, 360, 5) for k_ in (0.9, 1.0, 1.1, 1.2, 1.3, 1.4, 1.5)):   # rotation AND size searched
            a = math.radians(yaw); R = np.array([[math.cos(a), 0, math.sin(a)], [0, 1, 0], [-math.sin(a), 0, math.cos(a)]]) * s0 * k_
            P = sub @ R.T; topP = P[P[:, 1] > np.percentile(P[:, 1], 50)]
            P = P + (topT.mean(axis=0) - topP.mean(axis=0))
            d_src = kd.query(P)[0].mean(); d_tgt = cKDTree(P).query(T)[0].mean(); score = d_src + d_tgt
            low = P[P[:, 1] < np.percentile(P[:, 1], 30)]
            if low[:, 2].mean() > T[:, 2].mean() - 0.05: score += 1.0
            if best is None or score < best[0]:
                M = np.eye(4); M[:3, :3] = R; M[:3, 3] = topT.mean(axis=0) - (S[S[:, 1] > np.percentile(S[:, 1], 50)].mean(axis=0) @ R.T)
                best = (score, yaw, M, d_src, d_tgt)
    score, yaw, M, d_src, d_tgt = best
    src.apply_transform(M)
    if inflate != 1.0:                                                  # snug garments: grow about the centre of the body slice
        c = T.mean(axis=0); src.vertices = c + (src.vertices - c) * [inflate, 1.0, inflate]
    src.export(out)
    Mfull = M.copy()
    if inflate != 1.0:
        c = T.mean(axis=0); Sx = np.diag([inflate, 1.0, inflate, 1.0]); Tc = np.eye(4); Tc[:3, 3] = c; Ti = np.eye(4); Ti[:3, 3] = -c
        Mfull = Tc @ Sx @ Ti @ M
    rep = {"source": source, "roles": roles, "yaw_init": yaw, "raw_to_fit": Mfull.tolist(), "mean_dist_src_to_target_mm": round(d_src * 1000, 1),
           "mean_dist_target_to_src_mm": round(d_tgt * 1000, 1), "scale": round(float(np.cbrt(abs(np.linalg.det(M[:3, :3])))), 4), "tris": len(src.faces)}
    json.dump(rep, open(out.replace(".glb", "") + ".fit.json", "w"), indent=1)
    print(f"fit {source.split('/')[-1]} → roles {roles}: yaw0 {yaw}° · mean dist {d_src*1000:.0f}/{d_tgt*1000:.0f} mm → {out}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", required=True); ap.add_argument("--target", required=True); ap.add_argument("--roles", required=True)
    ap.add_argument("--ymin", type=float, default=0.0); ap.add_argument("--ymax", type=float, default=1.0); ap.add_argument("--out", required=True)
    ap.add_argument("--back-heavy", action="store_true", help="the piece's lowest part must hang behind (ponytail, long hair)")
    ap.add_argument("--inflate", type=float, default=1.0, help="horizontal growth for snug garments, e.g. 1.04")
    a = ap.parse_args(); main(a.source, a.target, a.roles.split(","), a.ymin, a.ymax, a.out, a.back_heavy, a.inflate)

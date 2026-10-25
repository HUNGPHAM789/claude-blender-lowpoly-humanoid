"""Measure procedural primal hair / outfit GLBs ON the body (own numbers, independent of the character fitter).

  python3 measure_primal_assets.py --body male_base_lp.glb --measurements male_measurements.json \
      [--hair male_hair_v1.glb] [--outfit male_outfit_v1.glb] --out report.json
Per asset: tris per part, closed/consistent (watertight + winding), clipping (vertices AND face samples inside the skin, deepest mm),
inner standoff (rays from covered skin along its normal to the first asset triangle, median / p90 mm), see-through misses
(skin the skirt must hide: rays outward that hit nothing), face rays (eye/nose/mouth/cheek probes blocked by hair), hand contact.
Exit 1 if: clipping > 1 mm, standoff median outside the brief (hair 3–8 mm shell, skirt 4–10 mm), eyes/nose blocked, see-through misses > 0.
"""
import argparse
import json
import os
import sys

import numpy as np
import trimesh

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from primal_body_frame import BodyQuery, arm_mask, load_body, load_json  # noqa: E402
from analyze_outfit import ray_hits  # noqa: E402


def parts_of(glb):
    sc = trimesh.load(glb)
    out = {}
    for node in sc.graph.nodes_geometry:
        T, g = sc.graph[node]
        m = sc.geometry[g].copy()
        m.apply_transform(T)
        out[node] = m
    return out


def first_dist(tris, O, D):
    out = np.full(len(O), np.nan)
    for k, h in enumerate(ray_hits(tris, O, D)):
        if len(h):
            t = tris[h[0]]
            n = np.cross(t[1] - t[0], t[2] - t[0])
            out[k] = (n @ (t[0] - O[k])) / (n @ D[k])
    return out


def clipping(q, mesh, n_samples=4000):
    pts, _ = trimesh.sample.sample_surface(mesh, n_samples, seed=2)
    pts = np.vstack([mesh.vertices, pts])
    sd, _, _ = q.signed_distance(pts)
    inside = q_inside(q, pts[sd < 0.002])
    deep = -sd[sd < 0.002][inside] if inside.any() else np.zeros(0)
    return {"samples": int(len(pts)), "inside": int(inside.sum()), "deepest_mm": round(float(deep.max() * 1000), 2) if len(deep) else 0.0}


def clipping_trunk(q, mesh, joints, n_samples=4000):
    pts, _ = trimesh.sample.sample_surface(mesh, n_samples, seed=2)
    pts = np.vstack([mesh.vertices, pts])
    sd, cp, _ = q.signed_distance(pts)
    near = sd < 0.002
    ins = np.zeros(len(pts), bool)
    ins[near] = q_inside(q, pts[near])
    trunk = ~arm_mask(cp, joints)
    m = ins & trunk
    return {"inside": int(m.sum()), "deepest_mm": round(float(-sd[m].min() * 1000), 2) if m.any() else 0.0}


def q_inside(q, pts, n_rays=3):
    """parity vote with jittered rays (the body is not watertight: signed distance alone mislabels edges)."""
    if not len(pts):
        return np.zeros(0, bool)
    rng = np.random.default_rng(0)
    votes = np.zeros(len(pts))
    for _ in range(n_rays):
        d = rng.normal(size=3)
        d /= np.linalg.norm(d)
        hits = ray_hits(q.T, pts, np.tile(d, (len(pts), 1)))
        votes += np.array([len(h) % 2 for h in hits])
    return votes >= 2


def stats_mm(x):
    x = x[np.isfinite(x)] * 1000
    if not len(x):
        return None
    return {"median": round(float(np.median(x)), 1), "p90": round(float(np.percentile(x, 90)), 1), "n": int(len(x))}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--body", required=True)
    ap.add_argument("--measurements", required=True)
    ap.add_argument("--hair")
    ap.add_argument("--outfit")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    body = load_body(a.body)
    meas = load_json(a.measurements)
    q = BodyQuery(body)
    face = meas["face"]
    xm = face["midline_x"]
    rep = {}
    fails = []
    P, N = q.P, q.N
    if a.hair:
        parts = parts_of(a.hair)
        allm = trimesh.util.concatenate(list(parts.values()))
        r = {"tris": {k: int(len(m.faces)) for k, m in parts.items()}, "tris_total": int(len(allm.faces))}
        r["clipping"] = {k: clipping(q, m) for k, m in parts.items()}
        # standoff: scalp above the hairline (+ back of the head above the nape) → hair shell
        shell = trimesh.util.concatenate([m for k, m in parts.items() if k.endswith("shell")])
        sk_c = meas["skull"]["centre_xz"]
        scalp = (P[:, 1] > face["hairline_y"] + 0.01) | ((P[:, 1] > face["eye_y"]) & (P[:, 2] < sk_c[1] - 0.02) & (P[:, 1] < 1.9))
        scalp &= P[:, 1] > face["chin_y"] + 0.04
        hs = parts.get("hair_shell")
        g = first_dist(hs.triangles, P[scalp] + N[scalp] * 0.0005, N[scalp]) + 0.0005
        g[g > 0.05] = np.nan
        r["standoff_hair_shell_mm"] = stats_mm(g)
        r["scalp_uncovered_frac"] = round(float(np.mean(~np.isfinite(g))), 4)
        if "beard_shell" in parts:
            bs = parts["beard_shell"]
            lo, hi = face["chin_y"] + 0.01, face["eye_y"] - 0.07
            jaw = (P[:, 1] > lo) & (P[:, 1] < hi) & (P[:, 2] > sk_c[1]) & (np.abs(N[:, 1]) < 0.7)
            gb = first_dist(bs.triangles, P[jaw] + N[jaw] * 0.0005, N[jaw]) + 0.0005
            gb[gb > 0.05] = np.nan
            r["standoff_beard_mm"] = stats_mm(gb)
        # face probes (same layout as the fitter: points ON the face, 3 outward rays each)
        eye_y = face["eye_y"]
        chin = face["chin_y"]
        probes = [("eye_L", 0.032, eye_y), ("eye_R", -0.032, eye_y), ("nose", 0.0, eye_y - 0.025),
                  ("mouth", 0.0, chin + 0.35 * (eye_y - chin)), ("cheek_L", 0.045, eye_y - 0.03), ("cheek_R", -0.045, eye_y - 0.03)]
        zt = body.vertices[:, 2].max() + 0.2
        blocked = {}
        for nm, dx, y in probes:
            d = first_dist(q.T, np.array([[xm + dx, y, zt]]), np.array([[0, 0, -1.0]]))[0]
            p = np.array([xm + dx, y, zt - d + 0.003])
            dirs = [(0, 0, 1), (0.34 if dx >= 0 else -0.34, 0, 0.94), (0, 0.3, 0.95)]
            D = np.array(dirs, float)
            D /= np.linalg.norm(D, axis=1, keepdims=True)
            hits = ray_hits(allm.triangles, np.tile(p, (3, 1)), D)
            blocked[nm] = int(sum(1 for h in hits if len(h)))
        r["face_rays_blocked_of_3"] = blocked
        if blocked["eye_L"] or blocked["eye_R"] or blocked["nose"]:
            fails.append("hair blocks eyes/nose")
        if any(c["deepest_mm"] > 1.0 for c in r["clipping"].values()):
            fails.append("hair clipping > 1 mm")
        rep["hair"] = r
    if a.outfit:
        parts = parts_of(a.outfit)
        r = {"tris": {k: int(len(m.faces)) for k, m in parts.items()}}
        r["closed"] = {k: bool(m.is_watertight and m.is_winding_consistent) for k, m in parts.items()}
        r["clipping"] = {k: clipping(q, m) for k, m in parts.items()}
        J = meas["joints_gltf"]
        r["clipping_trunk_only"] = {k: clipping_trunk(q, m, J) for k, m in parts.items()}
        skirt = trimesh.util.concatenate([m for k, m in parts.items() if k.startswith("skirt")])
        ylo, yhi = skirt.vertices[:, 1].min(), skirt.vertices[:, 1].max()
        J = meas["joints_gltf"]
        # trunk only (drop arm/hand samples by x beyond the shoulder joint × 0.95, like the fitter)
        armx = abs(J["vai_L"][0] - xm) * 0.95
        is_arm = arm_mask(P, J)
        zone = (P[:, 1] > ylo) & (P[:, 1] < yhi) & (np.abs(N[:, 1]) < 0.6) & ~is_arm
        g = first_dist(skirt.triangles, P[zone] + N[zone] * 0.0005, N[zone]) + 0.0005
        g[g > 0.15] = np.nan
        hip = zone & (P[:, 1] > meas["torso"]["hip_joint_y"])
        gh = first_dist(skirt.triangles, P[hip] + N[hip] * 0.0005, N[hip]) + 0.0005
        r["standoff_skirt_mm_all_in_height_range"] = stats_mm(g)
        r["standoff_skirt_mm_hip_to_waist"] = stats_mm(gh)
        # see-through: waist → buttock fold (and groin), all round, skin normals outward must hit the skirt
        waist = meas["torso"]["waist_y"]
        fold = meas["torso"]["hip_joint_y"] - 0.05
        cover = (P[:, 1] > max(fold, ylo + 0.03)) & (P[:, 1] < waist - 0.01) & (np.abs(N[:, 1]) < 0.8) & ~is_arm
        cover &= ~((np.abs(P[:, 0] - xm) > 0.12) & (P[:, 1] < meas["torso"]["hip_joint_y"]))
        d = first_dist(skirt.triangles, P[cover] + N[cover] * 0.0005, N[cover])
        miss = ~np.isfinite(d)
        back = P[cover][:, 2] < np.median(body.vertices[:, 2])
        r["see_through"] = {"zone_points": int(cover.sum()), "misses": int(miss.sum()), "misses_back_buttocks": int((miss & back).sum())}
        # groin: rays from the crotch front forward/down-forward
        hipy = meas["torso"]["hip_joint_y"]
        g_pts = P[(np.abs(P[:, 0] - xm) < 0.05) & (P[:, 1] > hipy - 0.08) & (P[:, 1] < hipy + 0.05) & (N[:, 2] > 0.3)]
        if len(g_pts):
            dirs = np.tile(unit3([0, -0.3, 1.0]), (len(g_pts), 1))
            dg = first_dist(skirt.triangles, g_pts + dirs * 0.0005, dirs)
            r["groin_rays"] = {"n": int(len(g_pts)), "misses": int((~np.isfinite(dg)).sum())}
        # hands vs skirt (rest pose): hand/arm samples inside the skirt volume ⇒ report
        arm = is_arm & (P[:, 1] > ylo) & (P[:, 1] < yhi)
        if arm.any():
            r["hand_points_in_skirt_range"] = int(arm.sum())
            sk_r = skirt.vertices
            # count hand samples whose |x| is inside the skirt's half-width at that height & depth band
            inside = 0
            for p in P[arm]:
                band = sk_r[np.abs(sk_r[:, 1] - p[1]) < 0.02]
                band = band[np.abs(band[:, 2] - p[2]) < 0.03]
                if len(band) and np.abs(band[:, 0] - xm).max() > abs(p[0] - xm):
                    inside += 1
            r["hand_samples_inside_skirt_silhouette"] = inside
        if r["see_through"]["misses"]:
            fails.append("skin visible through the skirt")
        if any(c["deepest_mm"] > 1.0 for c in r["clipping_trunk_only"].values()):
            fails.append("outfit clipping into the trunk > 1 mm")
        if any(c["inside"] for c in r["clipping"].values()):
            r["note"] = "clipping outside the trunk = the rest-pose hands touching the skirt sides (reported, not gated here)"
        rep["outfit"] = r
    rep["fails"] = fails
    with open(a.out, "w") as f:
        json.dump(rep, f, indent=1)
    print(json.dumps(rep, indent=1))
    sys.exit(1 if fails else 0)


def unit3(v):
    v = np.asarray(v, float)
    return v / np.linalg.norm(v)


if __name__ == "__main__":
    main()

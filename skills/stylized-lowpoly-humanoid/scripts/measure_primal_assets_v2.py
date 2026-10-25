"""Self-checks for the v2 procedural primal hair/beard + hide skirt (Codex audit build brief v2, steps 28–32).

  python3 measure_primal_assets_v2.py --body male_base_lp.glb --measurements male_measurements.json \
      --hair male_hair_v2.glb --outfit male_outfit_v2.glb --out male_v2_checks.json
Reports: tris by role · clump/lobe/panel/reveal counts (from the builders' _parts.json) · clipping of every part (parity-voted) ·
beard contact (area-sampled skin patch under the beard → ray along the skin normal to beard_contact: coverage, gap p50/p95/max,
penetration) · beard excursion beyond a coarse envelope (skin + 17 mm above the chin) · hair root concealment from 6 fixed
orthographic cameras (a root is exposed if the ray from it to the camera hits nothing) · tan share per camera from unlit
role ray-casts (tan / (tan + dark leather)) · skin seen through the skirt all round, waist → top of the hem teeth.
Exit 1 if: clipping of a protected part > 1 mm, contact coverage < 99 %, gap p95 > 6 / max > 8 mm, penetration > 1 mm,
eyes/nose blocked, skin visible through the skirt.
"""
import argparse
import json
import math
import os
import sys

import numpy as np
import trimesh

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from primal_body_frame import BodyQuery, arm_mask, load_body, load_json  # noqa: E402
from analyze_outfit import ray_hits  # noqa: E402
from measure_primal_assets import parts_of, first_dist  # noqa: E402

CAMS = {"front": 0, "q_front_L": 35, "side_L": 90, "q_back_L": 145, "back": 180, "side_R": -90, "q_front_R": -35}


def cam_dir(yaw):
    r = math.radians(yaw)
    return np.array([math.sin(r), 0.0, math.cos(r)])   # direction FROM the model TO the camera (front = +Z)


def clip_report(q, m, n=3000):
    pts, _ = trimesh.sample.sample_surface(m, n, seed=2)
    pts = np.vstack([m.vertices, pts])
    c = q.clearance(pts)
    ins = c < 0
    return {"inside": int(ins.sum()), "deepest_mm": round(float(-c[ins].min() * 1000), 2) if ins.any() else 0.0}


def role_raycast(scene_tris, scene_roles, yaw, y_lo, y_hi, x_half, step=0.006):
    d = -cam_dir(yaw)
    right = np.array([math.cos(math.radians(yaw)), 0, -math.sin(math.radians(yaw))])
    ys = np.arange(y_lo, y_hi, step)
    xs = np.arange(-x_half, x_half, step)
    O = np.array([right * x + np.array([0, y, 0]) - d * 2.0 for y in ys for x in xs])
    D = np.tile(d, (len(O), 1))
    counts = {}
    for h in ray_hits(scene_tris, O, D, chunk=60):
        role = scene_roles[h[0]] if len(h) else "none"
        counts[role] = counts.get(role, 0) + 1
    return counts


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--body", required=True)
    ap.add_argument("--measurements", required=True)
    ap.add_argument("--hair", required=True)
    ap.add_argument("--outfit", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    body = load_body(a.body)
    meas = load_json(a.measurements)
    q = BodyQuery(body)
    face = meas["face"]
    xm = face["midline_x"]
    P, N = q.P, q.N
    rep, fails = {}, []
    hp = parts_of(a.hair)
    op = parts_of(a.outfit)
    hinfo = load_json(os.path.splitext(a.hair)[0] + "_parts.json")
    oinfo = load_json(os.path.splitext(a.outfit)[0] + "_parts.json")
    rep["tris"] = {"hair": {k: int(len(m.faces)) for k, m in hp.items()}, "outfit": {k: int(len(m.faces)) for k, m in op.items()}}
    rep["tris"]["hair_total"] = int(sum(rep["tris"]["hair"].values()))
    rep["tris"]["skirt_total"] = int(sum(v for k, v in rep["tris"]["outfit"].items() if k.startswith("skirt")))
    rep["counts"] = {"clumps_per_region": hinfo["clumps_per_region"], "beard_lobes": hinfo["beard"]["lobes"],
                     "moustache_lobes": hinfo["beard"]["moustache_lobes"], "panels": oinfo["counts"]}
    rep["closed_before_flat_export"] = {**hinfo["closed_before_flat_export"], **oinfo["closed_before_flat_export"]}
    rep["clipping"] = {k: clip_report(q, m) for k, m in {**hp, **op}.items()}
    J = meas["joints_gltf"]
    for k, m in op.items():          # trunk-only clipping for the skirt (rest hands hang into the skirt sides: reported apart)
        pts, _ = trimesh.sample.sample_surface(m, 3000, seed=2)
        pts = np.vstack([m.vertices, pts])
        sd, cp, _ = q.signed_distance(pts)
        c = q.clearance(pts)
        trunk = ~arm_mask(cp, J)
        ins = (c < 0) & trunk
        rep["clipping"][k]["trunk_inside"] = int(ins.sum())
        rep["clipping"][k]["trunk_deepest_mm"] = round(float(-c[ins].min() * 1000), 2) if ins.any() else 0.0
    for k, r in rep["clipping"].items():
        lim = r.get("trunk_deepest_mm", r["deepest_mm"])
        if not k.endswith("__movable") and lim > 1.0:
            fails.append(f"{k} clips {lim} mm")
    # ---- beard contact: skin patch under the beard (inside the contact rows' footprint, 6 mm margin)
    rows = np.array(hinfo["beard"]["contact_rows"])          # 5 × nc × 3, top → chin
    A = np.array([xm, 0, 0.03])
    def az(p):
        return np.degrees(np.arctan2(p[..., 0] - A[0], p[..., 2] - A[2]))
    col_az = az(rows[0])
    top_y, bot_y = rows[0][:, 1], rows[-1][:, 1]
    paz = az(P)
    inside_az = (paz > col_az.min() + 6) & (paz < col_az.max() - 6) & (P[:, 2] > 0.0)
    ty = np.interp(paz, col_az, top_y)
    by = np.interp(paz, col_az, bot_y)
    patch = inside_az & (P[:, 1] < ty - 0.006) & (P[:, 1] > by + 0.004) & (P[:, 1] > face["chin_y"]) & (P[:, 1] < face["eye_y"])
    bc = hp["beard_contact__movable"]
    g = first_dist(bc.triangles, P[patch] - N[patch] * 0.002, N[patch]) - 0.002
    hit = np.isfinite(g) & (g < 0.02)
    gm = g[hit] * 1000
    rep["beard_contact"] = {"patch_points": int(patch.sum()), "coverage": round(float(hit.mean()), 4),
                            "gap_mm_p50": round(float(np.median(gm)), 2), "gap_mm_p95": round(float(np.percentile(gm, 95)), 2),
                            "gap_mm_max": round(float(gm.max()), 2), "penetration_mm": round(float(max(0, -gm.min())), 2)}
    bcr = rep["beard_contact"]
    if bcr["coverage"] < 0.99: fails.append("beard contact coverage < 99 %")
    if bcr["gap_mm_p95"] > 6 or bcr["gap_mm_max"] > 8: fails.append("beard contact gap p95 > 6 or max > 8 mm")
    if bcr["penetration_mm"] > 1: fails.append("beard penetration > 1 mm")
    # ---- beard excursion beyond the coarse envelope (skin + 17 mm), above the chin (lobe rim below the chin is designed)
    bo = hp["beard_outer"].vertices
    above = bo[:, 1] > face["chin_y"] + 0.015
    sd, _, _ = q.signed_distance(bo[above])
    rep["beard_envelope"] = {"limit_mm": 17.0, "outer_offset_mm_p50": round(float(np.median(sd) * 1000), 1),
                             "outer_offset_mm_max": round(float(sd.max() * 1000), 1),
                             "max_excursion_beyond_mm": round(float(max(0.0, sd.max() * 1000 - 17.0)), 1)}
    # ---- face rays
    eye_y, chin = face["eye_y"], face["chin_y"]
    allh = trimesh.util.concatenate(list(hp.values()))
    zt = body.vertices[:, 2].max() + 0.2
    blocked = {}
    for nm, dx, y in (("eye_L", 0.032, eye_y), ("eye_R", -0.032, eye_y), ("nose", 0.0, eye_y - 0.025),
                      ("mouth", 0.0, chin + 0.35 * (eye_y - chin)), ("cheek_L", 0.045, eye_y - 0.03), ("cheek_R", -0.045, eye_y - 0.03)):
        d = first_dist(q.T, np.array([[xm + dx, y, zt]]), np.array([[0, 0, -1.0]]))[0]
        p = np.array([xm + dx, y, zt - d + 0.003])
        D = np.array([(0, 0, 1), (0.34 if dx >= 0 else -0.34, 0, 0.94), (0, 0.3, 0.95)], float)
        D /= np.linalg.norm(D, axis=1, keepdims=True)
        blocked[nm] = int(sum(1 for h in ray_hits(allh.triangles, np.tile(p, (3, 1)), D) if len(h)))
    rep["face_rays_blocked_of_3"] = blocked
    if blocked["eye_L"] or blocked["eye_R"] or blocked["nose"]: fails.append("eyes/nose blocked")
    # ---- root concealment: root ring centre + ridge of every hair mass, ray toward each camera
    hm = next(hp[k] for k in ("hair_masses", "hair_chunks", "hair_spikes") if k in hp)
    scene = trimesh.util.concatenate([body] + list(hp.values()))
    roots = []
    hv = trimesh.load(a.hair, force=None)
    # root rings are the first 4 vertices of each wedge in builder order; re-derive from the merged-face table
    for row in hinfo["clumps"]:
        if row.get("skipped"):
            continue
        f0, f1 = row["faces"]
        tri = hm.triangles[f0:f1]
        # the root cap is the last 2 faces of each wedge: its centroid = root ring centre
        roots.append(tri[-2:].reshape(-1, 3).mean(axis=0))
    roots = np.array(roots)
    conceal = {}
    for cam, yaw in CAMS.items():
        d = cam_dir(yaw)
        facing = (roots - np.array([xm, 1.70, 0.04])) @ d > -0.02
        hits = ray_hits(scene.triangles, roots[facing] + d * 0.003, np.tile(d, (facing.sum(), 1)))
        exposed = sum(1 for h in hits if not len(h))
        conceal[cam] = {"roots_facing": int(facing.sum()), "exposed": int(exposed)}
    rep["hair_root_concealment"] = conceal
    # ---- tan share (unlit role ray-cast) per camera, skirt region
    sk_parts = [(k, m) for k, m in op.items()]
    roles = {"skirt_tan_reveals": "tan", "skirt_under_panels": "dark", "skirt_main_panels": "dark", "skirt_shell__movable": "dark",
             "rope_belt": "belt", "stone": "stone"}
    tris = [body.triangles]
    rl = ["skin"] * len(body.faces)
    for k, m in sk_parts:
        tris.append(m.triangles)
        rl += [roles.get(k, k)] * len(m.faces)
    tris = np.vstack(tris)
    tan = {}
    G_top = oinfo["belt_y"]
    for cam in ("front", "q_front_L", "q_front_R", "side_L", "back"):
        c = role_raycast(tris, rl, CAMS[cam], G_top - oinfo["G_m"] - 0.03, G_top + 0.03, 0.3)
        t, dk = c.get("tan", 0), c.get("dark", 0)
        tan[cam] = {"tan_share": round(t / max(t + dk, 1), 3), "tan_px": t, "dark_px": dk}
    rep["tan_share_unlit"] = tan
    # ---- skin seen through the skirt, all round, waist → top of the hem teeth (highest main panel tip)
    hem_top = max(p["tip_y"] for p in oinfo["panels"] if p["overlap_group"] == "main")
    protected = trimesh.util.concatenate([m for k, m in op.items() if k.startswith("skirt") and not k.endswith("__movable")])
    allsk = trimesh.util.concatenate([m for k, m in op.items() if k.startswith("skirt")])
    is_arm = arm_mask(P, J)
    zone = (P[:, 1] > hem_top) & (P[:, 1] < meas["torso"]["waist_y"] - 0.01) & (np.abs(N[:, 1]) < 0.8) & ~is_arm
    arm_faces = arm_mask(body.triangles_center, J)
    hand_mesh = trimesh.Trimesh(body.vertices, body.faces[arm_faces], process=False)
    with_hand = trimesh.util.concatenate([allsk, hand_mesh])      # skin hidden behind the body's own hand is not "seen"
    for nm, mesh in (("panels_only", protected), ("with_shell", allsk), ("with_shell_or_own_hand", with_hand)):
        d = first_dist(mesh.triangles, P[zone] + N[zone] * 0.0005, N[zone])
        miss = ~np.isfinite(d)
        rep.setdefault("see_through", {})[nm] = {"zone_points": int(zone.sum()), "misses": int(miss.sum()),
                                                 "zone_y": [round(hem_top, 3), round(meas['torso']['waist_y'] - 0.01, 3)]}
    if rep["see_through"]["panels_only"]["misses"]: fails.append("skin visible through the skirt panels")
    # ---- rest-pose hands vs every skirt part (Boss 25/10: «Tay xuyên váy»): min distance skirt surface → hand/arm skin,
    # plus skirt samples INSIDE the hand (parity vote, nearest skin point on the arm)
    from scipy.spatial import cKDTree
    arm_P = P[is_arm]
    arm_kd = cKDTree(arm_P)
    hands = {}
    for k, m in op.items():
        pts, _ = trimesh.sample.sample_surface(m, 6000, seed=3)
        pts = np.vstack([m.vertices, pts])
        d = arm_kd.query(pts)[0]
        near = d < 0.02
        inside = 0
        if near.any():
            ins = q.inside(pts[near])
            inside = int(ins.sum())
        hands[k] = {"min_clearance_mm": round(float(d.min() * 1000), 1), "samples_within_10mm": int((d < 0.010).sum()),
                    "samples_inside_hand": inside}
    rep["hands_vs_skirt"] = hands
    rep["hands_vs_skirt_min_mm"] = min(v["min_clearance_mm"] for v in hands.values())
    if any(v["samples_within_10mm"] or v["samples_inside_hand"] for v in hands.values()):
        fails.append("skirt within 10 mm of / inside the rest-pose hands")
    # ---- lateral half-width of the skirt vs the hip skin at 4 heights (trunk samples, arms excluded)
    allv = np.vstack([m.vertices for k, m in op.items() if k.startswith("skirt")])
    lat = {}
    for y in (1.05, 0.95, 0.85, 0.75):
        sb = allv[np.abs(allv[:, 1] - y) < 0.012]
        tb = P[(~is_arm) & (np.abs(P[:, 1] - y) < 0.006)]
        if len(sb) and len(tb):
            lat[str(y)] = {"skirt_half_width_cm_L": round(float((sb[:, 0] - xm).max() * 100), 1), "skin_L": round(float((tb[:, 0] - xm).max() * 100), 1),
                           "skirt_half_width_cm_R": round(float((xm - sb[:, 0]).max() * 100), 1), "skin_R": round(float((xm - tb[:, 0]).max() * 100), 1)}
    rep["lateral_half_width"] = lat
    rep["fails"] = fails
    with open(a.out, "w") as f:
        json.dump(rep, f, indent=1)
    print(json.dumps(rep, indent=1))
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()

"""LEARN the chunky-spiky hair grammar from a sample hair mesh (Boss 25/10/2026: «học từ assets tóc … cách làm chunky spikey hair,
tóc đuôi cột … học bằng cách nào? scan số liệu?»). The samples are teachers only — never shipped.

  python3 analyze_hair.py --hair <hair_fit.glb> --body <body_fit.glb> --joints <joints.json> --out <dir>/<name>
  ⇒ <name>_clumps.json (one row per clump) · <name>_summary.json (per-region statistics) · <name>_clumps.png (each clump its own colour)

Frame: glTF, metres, Y up, the body faces +Z (both inputs already fitted onto the same body).
1. scalp = ellipsoid around the head (body verts above the neck joint): centre + half-extents
2. height above scalp h(v) = (‖(v − c)/r‖ − 1) · mean(r)
3. tips = vertices that are the highest h inside a 1.5 cm ball and stand ≥ 1 cm proud of the scalp
4. clumps = steepest ascent of h over the mesh edges; every vertex climbs to a tip (watershed); tiny basins are merged
5. per clump: length, base width, tip half-angle, tilt from the scalp normal, droop (downward share of the axis), region
"""
import argparse, json, math, os
import numpy as np
import trimesh
from scipy.spatial import cKDTree
from PIL import Image, ImageDraw

TIP_BALL, TIP_MIN_H, MIN_VERTS = 0.015, 0.010, 25


def load(p):
    m = trimesh.load(p, force="mesh"); return trimesh.Trimesh(m.vertices, m.faces, process=True)


def main(hair_p, body_p, joints_p, out):
    hair, body = load(hair_p), load(body_p)
    J = json.load(open(joints_p))
    neck_y = J["co"][2]                                              # joints are Blender Z-up; glTF y = Blender z
    hv = body.vertices[body.vertices[:, 1] > J["dau"][2]]          # head = body above the chin joint (above the neck catches the traps)
    c = (hv.min(axis=0) + hv.max(axis=0)) / 2; r = (hv.max(axis=0) - hv.min(axis=0)) / 2; rm = float(r.mean())
    V = hair.vertices; n = len(V)
    q = (V - c) / r; rr = np.linalg.norm(q, axis=1); h = (rr - 1) * rm
    # tips
    kd = cKDTree(V); ball = kd.query_ball_point(V, TIP_BALL)
    is_tip = np.array([h[i] >= h[b].max() - 1e-9 and h[i] > TIP_MIN_H for i, b in enumerate(ball)])
    tips = np.where(is_tip)[0]
    # watershed by steepest ascent along mesh edges
    nb = [[] for _ in range(n)]
    for a, b in hair.edges_unique: nb[a].append(b); nb[b].append(a)
    up = np.arange(n)
    for i in range(n):
        if nb[i]:
            j = max(nb[i], key=lambda k: h[k])
            if h[j] > h[i]: up[i] = j
    root = up.copy()
    for _ in range(60): root = root[root]
    # merge adjacency maxima into the nearest real tip (within 2.5 cm), else they stay their own (small) basin
    tkd = cKDTree(V[tips]) if len(tips) else None
    lab = root.copy()
    if tkd is not None:
        u = np.unique(root); d, k = tkd.query(V[u]); m_ = dict(zip(u, np.where(d < 0.025, tips[k], u))); lab = np.array([m_[x] for x in root])
    clumps = []; cnt = np.bincount(lab, minlength=n)
    head_top = np.array([0, 1.0, 0]); front = np.array([0, 0, 1.0])
    for t in np.unique(lab):
        idx = np.where(lab == t)[0]
        if len(idx) < MIN_VERTS: continue
        P = V[idx]; H_ = h[idx]; tip = V[t]
        base = P[H_ <= np.percentile(H_, 20)]; bc = base.mean(axis=0)
        ax = tip - bc; L = float(np.linalg.norm(ax))
        if L < 0.015: continue
        a_ = ax / L
        perp = lambda X: np.linalg.norm((X - bc) - np.outer((X - bc) @ a_, a_), axis=1)
        width = float(2 * np.sqrt(np.mean(perp(base) ** 2)))
        near_tip = P[((P - bc) @ a_) > 0.75 * L]
        half = float(math.degrees(math.atan2(np.mean(perp(near_tip)) if len(near_tip) else 0.0, 0.25 * L)))
        nrm = ((bc - c) / r ** 2); nrm /= np.linalg.norm(nrm)
        tilt = float(math.degrees(math.acos(np.clip(a_ @ nrm, -1, 1))))
        dirb = (bc - c) / np.linalg.norm(bc - c)
        polar = float(math.degrees(math.acos(np.clip(dirb @ head_top, -1, 1))))
        az = float(math.degrees(math.atan2(dirb[0], dirb[2])))       # 0 = front (+Z), ±180 = back
        if bc[1] < neck_y - 0.02 and dirb[2] < -0.2: region = "tail"
        elif bc[1] < c[1] - 0.2 * r[1] and abs(az) < 70: region = "beard"
        elif polar < 35: region = "crown"
        elif abs(az) < 45: region = "fringe"
        elif abs(az) > 120: region = "back"
        else: region = "side"
        # flow = where the clump points along the scalp: 0° = straight down the head, +90° = toward the character's left (+X side
        # of its own base), ±180° = up/over; measured in the tangent plane at the base
        g = np.array([0, -1.0, 0]); e_down = g - (g @ nrm) * nrm
        e_down = e_down / np.linalg.norm(e_down) if np.linalg.norm(e_down) > 1e-6 else np.array([0, 0, -1.0])
        e_side = np.cross(nrm, e_down); at = a_ - (a_ @ nrm) * nrm
        flow = float(math.degrees(math.atan2(at @ e_side, at @ e_down))) if np.linalg.norm(at) > 1e-6 else 0.0
        outward = float(math.degrees(math.atan2(at @ np.cross(np.array([0, 1.0, 0]), nrm), at @ (dirb - (dirb @ nrm) * nrm + 1e-9))))
        # cross-section: PCA extents ⇒ flatness = thickness / width (blade ≈ 0.3, cone ≈ 1)
        ev = np.sqrt(np.maximum(np.linalg.eigvalsh(np.cov((P - P.mean(axis=0)).T)), 0))
        flat = float(ev[0] / max(ev[1], 1e-9))
        # bend: how far the clump's mid-section leaves the straight base→tip line, per unit length
        mid = P[np.abs(((P - bc) @ a_) - 0.5 * L) < 0.12 * L]
        bend = float(np.linalg.norm(mid.mean(axis=0) - (bc + 0.5 * L * a_)) / L) if len(mid) else 0.0
        base_h = float(np.percentile(H_, 20))                        # how far the clump's root sits off the scalp = its layer
        clumps.append({"tip": V[t].round(4).tolist(), "base": bc.round(4).tolist(), "verts": int(len(idx)), "region": region,
                       "flow_deg": round(flow, 1), "flatness": round(flat, 3), "bend": round(bend, 3), "root_off_scalp_cm": round(base_h * 100, 2),
                       "length_cm": round(L * 100, 2), "base_width_cm": round(width * 100, 2), "tip_half_angle_deg": round(half, 1),
                       "tilt_from_normal_deg": round(tilt, 1), "droop": round(float(-a_[1]), 3), "polar_deg": round(polar, 1), "azimuth_deg": round(az, 1),
                       "proud_cm": round(float(h[t] * 100), 2), "_idx": idx})
    # summary
    from scipy.spatial import cKDTree as _KD
    B = np.array([k["base"] for k in clumps]) if clumps else np.zeros((0, 3))
    for k_, b_ in zip(clumps, B):
        others = B[np.linalg.norm(B - b_, axis=1) > 1e-6]; k_["nn_spacing_cm"] = round(float(np.min(np.linalg.norm(others - b_, axis=1))) * 100, 2) if len(others) else None
    lowfront = [k for k in clumps if k["region"] in ("fringe",)]
    hairline = {"front_lowest_base_above_head_centre_frac": round(float((min(k["base"][1] for k in lowfront) - c[1]) / r[1]), 3) if lowfront else None,
                "nape_lowest_base_above_head_centre_frac": round(float((min(k["base"][1] for k in clumps if k["region"] == "back") - c[1]) / r[1]), 3) if any(k["region"] == "back" for k in clumps) else None}
    summ = {"hairline": hairline, "head_centre": c.round(4).tolist(), "head_half_extent_cm": (r * 100).round(2).tolist(), "verts": n, "clumps": len(clumps),
            "regions": {}}
    for reg in sorted({k["region"] for k in clumps}):
        G = [k for k in clumps if k["region"] == reg]; f = lambda key: np.array([k[key] for k in G])
        q_ = lambda a: [round(float(np.percentile(a, p)), 2) for p in (10, 50, 90)]
        summ["regions"][reg] = {"count": len(G), "length_cm_p10_50_90": q_(f("length_cm")), "base_width_cm_p10_50_90": q_(f("base_width_cm")),
                                "tip_half_angle_deg_p10_50_90": q_(f("tip_half_angle_deg")), "tilt_deg_p10_50_90": q_(f("tilt_from_normal_deg")),
                                "droop_p10_50_90": q_(f("droop")), "flow_deg_p10_50_90": q_(f("flow_deg")), "flatness_p10_50_90": q_(f("flatness")),
                                "bend_p10_50_90": q_(f("bend")), "root_off_scalp_cm_p10_50_90": q_(f("root_off_scalp_cm")),
                                "nn_spacing_cm_p10_50_90": q_(np.array([k["nn_spacing_cm"] for k in G if k["nn_spacing_cm"] is not None])), "aspect_len_over_width_median": round(float(np.median(f("length_cm") / np.maximum(f("base_width_cm"), 0.1))), 2)}
    # picture: each clump its own colour, 4 views
    col = np.full((n, 3), 200); rng = np.random.default_rng(1)
    for k in clumps: col[k["_idx"]] = rng.integers(40, 230, 3)
    F = hair.faces; tiles = []
    for yaw in (0, 90, 180, 270):
        a = math.radians(yaw); R = np.array([[math.cos(a), 0, math.sin(a)], [0, 1, 0], [-math.sin(a), 0, math.cos(a)]])
        W = (V - c) @ R.T; s = 300 / (2.4 * rm); im = Image.new("RGB", (300, 360), (245, 245, 245)); d = ImageDraw.Draw(im)
        for i in np.argsort(W[F][:, :, 2].mean(axis=1)):
            tri = W[F[i]]
            if np.cross(tri[1] - tri[0], tri[2] - tri[0])[2] <= 0: continue
            d.polygon([(150 + x * s, 190 - y * s) for x, y, _ in tri], fill=tuple(int(v) for v in col[F[i]].mean(axis=0)), outline=(30, 30, 30))
        tiles.append(im)
    sheet = Image.new("RGB", (1200, 360)); [sheet.paste(t, (300 * i, 0)) for i, t in enumerate(tiles)]; sheet.save(out + "_clumps.png")
    for k in clumps: k.pop("_idx")
    json.dump(clumps, open(out + "_clumps.json", "w"), indent=0); json.dump(summ, open(out + "_summary.json", "w"), indent=1)
    print(json.dumps(summ, indent=1))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    for k_ in ("--hair", "--body", "--joints", "--out"): ap.add_argument(k_, required=True)
    a = ap.parse_args(); main(a.hair, a.body, a.joints, a.out)

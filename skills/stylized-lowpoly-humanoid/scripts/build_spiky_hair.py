"""Procedural chunky SPIKY primal hair + beard on a measured base body (no image→3D).

  python3 build_spiky_hair.py --body male_base_lp.glb --measurements male_measurements.json --out male_hair_v1.glb [--seed 7] [--no-beard]

Spec: spec/SPEC_primal_spiky_hair.json (clump sizes per region, flow, budget) + SPEC_primal_body_anatomy.md (ear → hair-root anchors).
Frame: glTF metres, Y up, faces +Z; the GLB comes out already in place on the body.

Construction
1. SCALP SHELL: rays from the skull centre on a (azimuth, elevation) grid hit the real head; vertex = hit + normal × SHELL_GAP.
   The lowest row per column is bisected so its hit lies on the HAIRLINE curve y(|azimuth|): forehead hairline → temple →
   sideburn down to the ear-lobe in front of the ear → over the ear top → behind the ear down to the nape (ear azimuths measured
   from the ear points in the measurement JSON).
2. CLUMPS: folded locks (triangular section, flat side on the scalp, thickness ÷ width ≥ 0.55) with a mid ring and a bent tip,
   9 tris each, rooted on the shell.
   Direction = cos(flow)·down-the-scalp + sin(flow)·normal (flow from the spec: male fringe/side/back point up and out).
3. BEARD: a shell on the jaw/cheeks/chin (horizontal rays, BEARD_GAP off the skin) from under the nose / the cheek line down to the
   chin, a bib hanging below the chin, an underside back to the throat, plus down-pointing clumps and a 2-clump moustache.
4. Every clump vertex is pushed out until it stands ≥ CLUMP_MIN_GAP from the body (signed distance by closest face).
Writes <out>.glb (geometries hair_shell, hair_clumps, beard — one material 'hair') and <out>_clumps.json (one row per clump).
"""
import argparse
import json
import math
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from primal_body_frame import BodyQuery, export_roles, fix_winding_outward, load_body, load_json  # noqa: E402

SPEC_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "spec")
SHELL_GAP = 0.0035      # scalp shell vertices 3.5 mm off the skin (brief: 3–8 mm, NOT a helmet)
BEARD_GAP = 0.0035      # beard inner surface on the jaw
CLUMP_MIN_GAP = 0.003   # no clump vertex closer than 3 mm to the skin
TOP_ELEVATION = 86.0
_g = [(i / 4, j / 4) for i in range(5) for j in range(5 - i)]
BARY = np.array([[a, b, 1 - a - b] for a, b in _g if 0 < a + b <= 1 or (a, b) == (0, 0)])  # 15 points per face incl. corners


def unit(v):
    v = np.asarray(v, float)
    return v / np.linalg.norm(v, axis=-1, keepdims=True)


def az_dir(theta_deg, phi_deg):
    t, p = math.radians(theta_deg), math.radians(phi_deg)
    return np.array([math.sin(t) * math.cos(p), math.sin(p), math.cos(t) * math.cos(p)])


class HeadFrame:
    def __init__(self, body, meas):
        self.q = BodyQuery(body)
        sk = meas["skull"]
        face = meas["face"]
        self.face = face
        self.C = np.array([sk["centre_xz"][0], face["brow_y"] + 0.008, sk["centre_xz"][1]])
        ears = meas["ears"]
        az = []
        for side in ("left", "right"):
            for key in ("lobe_bottom_point", "top_point", "most_proud_point"):
                p = np.array(ears[side][key])
                az.append(abs(math.degrees(math.atan2(p[0] - self.C[0], p[2] - self.C[2]))))
        self.ear_front_az = min(az) - 5.0
        self.ear_back_az = max(az) + 12.0
        self.lobe_y = float(np.mean([ears[s]["lobe_bottom_point"][1] for s in ("left", "right")]))
        self.ear_top_y = float(np.mean([ears[s]["top_point"][1] for s in ("left", "right")]))
        self.nape_y = face["chin_y"] + 0.045
        self.max_r = 0.85 * max(sk["width_m"], sk["depth_m"], sk["height_eye_to_top_m"] * 1.6)
        hl = face["hairline_y"]
        ef, eb = self.ear_front_az, self.ear_back_az
        # hairline height y(|azimuth|): forehead → temple → sideburn (lobe, in front of the ear) → over the ear → behind → nape
        self.hairline = [(0, hl), (25, hl), (45, hl - 0.02), (60, face["brow_y"] + 0.006), (ef - 8, self.lobe_y + 0.002),
                         (ef, self.lobe_y + 0.002), (ef + 3, self.ear_top_y + 0.011), (eb, self.ear_top_y + 0.006),
                         (eb + 12, self.lobe_y - 0.005), (150, self.nape_y), (180, self.nape_y)]

    def hairline_y(self, theta):
        a = abs(((theta + 180) % 360) - 180)
        xs, ys = zip(*self.hairline)
        return float(np.interp(a, xs, ys))

    def hit(self, theta, phi):
        h, n, _ = self.q.first_hit(self.C[None], az_dir(theta, phi)[None])
        return h[0], n[0]

    def bottom_elevation(self, theta):
        target = self.hairline_y(theta)
        lo, hi = -70.0, TOP_ELEVATION
        for _ in range(28):
            mid = 0.5 * (lo + hi)
            h, _ = self.hit(theta, mid)
            far = np.isnan(h[0]) or np.linalg.norm(h - self.C) > self.max_r
            if (not far) and h[1] > target:
                hi = mid
            else:
                lo = mid
        return hi  # hi = the lowest elevation whose hit is still ON the head (the neck/trapezius jump never leaks into the hairline)

    def clear_shell(self, verts, faces, min_gap, iters=8, centre=None):
        """push shell verts out (radially) until samples on every face (centre + edge mid-points) stand ≥ min_gap off the skin:
        a low-poly chord between two 5 mm vertices cuts into the skull bulge between them."""
        v = verts.copy()
        bary = BARY
        for _ in range(iters):
            tri = v[faces]
            pts = np.einsum("bk,fkj->fbj", bary, tri).reshape(-1, 3)
            sd = self.q.clearance(pts)
            lack = (min_gap - sd).reshape(len(faces), len(bary)).max(axis=1)
            if lack.max() <= 0.0002:
                break
            push = np.zeros(len(v))
            for f, l in zip(faces, lack):
                if l > 0:
                    push[f] = np.maximum(push[f], l + 0.0005)
            c0 = self.C if centre is None else centre
            dirs = unit(v - c0)
            low = v[:, 1] < c0[1] - 0.05            # nape: radial-from-centre runs ALONG the neck, push horizontally out instead
            hz = v - c0
            hz[:, 1] = 0
            dirs[low] = unit(hz[low])
            v += dirs * push[:, None]
        return v

    def scalp_point(self, theta, phi, gap):
        h, n = self.hit(theta, phi)
        radial = unit(h - self.C)
        nn = unit(0.5 * unit(n) + 0.5 * radial)
        return h + nn * gap, nn, h


def build_scalp_shell(hf, rows_t=(0.0, 0.2, 0.42, 0.65, 0.85)):
    ef, eb = hf.ear_front_az, hf.ear_back_az
    half = sorted(set([0, 15, 30, 45, 60, 70, round(ef - 8, 1), round(ef, 1), round(ef + 3, 1), round((ef + eb) / 2, 1),
                       round(eb, 1), round(eb + 12, 1), 142, 160]))
    cols = [-a for a in reversed(half) if a > 0] + half + [180]
    cols = sorted(set(cols))
    nc = len(cols)
    phib = {c: hf.bottom_elevation(c) for c in cols}
    verts = []
    for t in rows_t:
        for c in cols:
            phi = phib[c] + t * (TOP_ELEVATION - phib[c])
            p, _, _ = hf.scalp_point(c, phi, SHELL_GAP)
            verts.append(p)
    top, _, _ = hf.scalp_point(0, 90, SHELL_GAP)
    verts.append(top)
    faces = []
    nr = len(rows_t)
    for r in range(nr - 1):
        for i in range(nc):
            j = (i + 1) % nc
            a, b, c2, d = r * nc + i, r * nc + j, (r + 1) * nc + j, (r + 1) * nc + i
            faces += [[a, b, c2], [a, c2, d]]
    pole = len(verts) - 1
    for i in range(nc):
        faces.append([(nr - 1) * nc + i, (nr - 1) * nc + (i + 1) % nc, pole])
    verts = np.array(verts)
    faces = fix_winding_outward(verts, faces, hf.C)
    verts = hf.clear_shell(verts, faces, SHELL_GAP - 0.002)
    return verts, faces, cols, phib


def blade(root, n, d, length, width, thick_ratio, rng):
    """Folded lock: triangular cross-section (flat side on the scalp, ridge out), base ring (3), mid ring (3) at 0.6 L scaled 0.8,
    bent pointed tip. 9 tris, base open (it sits in the shell). Reads as a chunky folded clump, not a paper shard."""
    d = unit(d)
    lat = unit(np.cross(n, d))
    th = unit(np.cross(d, lat))
    if np.dot(th, n) < 0:
        th = -th
    T = width * thick_ratio
    B = root - d * 0.004
    ring = lambda C, s: [C + lat * width / 2 * s - th * T / 3 * s, C + th * 2 * T / 3 * s, C - lat * width / 2 * s - th * T / 3 * s]
    bend = rng.uniform(0.12, 0.2)
    M = B + d * 0.6 * length - th * bend * 0.45 * length
    tip = B + d * length - th * bend * length
    v = np.array(ring(B, 1.0) + ring(M, 0.8) + [tip])
    f = []
    for i in range(3):
        j = (i + 1) % 3
        f += [[i, j, 3 + j], [i, 3 + j, 3 + i]]
    for i in range(3):
        f.append([3 + i, 3 + (i + 1) % 3, 6])
    f = np.array(f)
    tri = v[f]
    nrm = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0])
    cen = tri.mean(axis=1)
    axis_pt = B + np.outer(np.clip(np.einsum("ij,j->i", cen - B, d), 0, length), d) + th * T / 6
    flip = np.einsum("ij,ij->i", nrm, cen - axis_pt) < 0
    f[flip] = f[flip][:, ::-1]
    return v, f


def push_clear(q, v, n, min_gap, f=None):
    """push a whole clump out along the scalp normal until its vertices AND face samples clear the skin (an ear top pierced the
    middle of a clump face while all 7 vertices were outside — measured 25/10)."""
    for _ in range(12):
        pts = v if f is None else np.vstack([v, np.einsum("bk,fkj->fbj", BARY, v[f]).reshape(-1, 3)])
        sd = q.clearance(pts)
        lack = min_gap - sd.min()
        if lack <= 0:
            break
        v = v + n * min(lack + 0.0005, 0.01)
    return v


def sample_len(rng, p10, p50, p90):
    x = p50 * math.exp(rng.normal(0, 0.3))
    return float(np.clip(x, p10, p90))


def rotate_about(v, axis, ang):
    axis = unit(axis)
    return v * math.cos(ang) + np.cross(axis, v) * math.sin(ang) + axis * np.dot(axis, v) * (1 - math.cos(ang))


def build_hair_clumps(hf, phib_fn, spec, rng, size_scale):
    reg = spec["regions"]
    plan = []  # (region, theta, elevation offset t, flow)
    # (region, list of thetas, t)
    def ring(n, start, span, t):
        return [start + span * (k + 0.5) / n for k in range(n)], t
    rows = []
    for (n, t) in ((6, 0.03), (6, 0.3), (4, 0.55)):
        th, t = ring(n, -40, 80, t); rows.append(("fringe", th, t))
    for sgn in (1, -1):
        for (n, t) in ((5, 0.03), (4, 0.28), (3, 0.52), (3, 0.76)):
            th, t = ring(n, 44, 76, t); rows.append(("side", [sgn * x for x in th], t))
    for (n, t) in ((6, 0.03), (6, 0.17), (5, 0.36), (4, 0.58), (3, 0.8)):
        th, t = ring(n, 122, 116, t); rows.append(("back", th, t))
    rows.append(("crown", [0, 60, 120, 180, 240, 300], 0.95))
    region_key = {"fringe": "fringe", "side": "side", "back": "back", "crown": "crown"}
    verts, faces, table = [], [], []
    for region, thetas, t in rows:
        r = reg[region_key[region]]
        for th0 in thetas:
            th = th0 + rng.uniform(-4, 4)
            tt = float(np.clip(t + rng.uniform(-0.04, 0.04), 0.0, 0.98))
            phi = phib_fn(th) + tt * (TOP_ELEVATION - phib_fn(th))
            root, n, _ = hf.scalp_point(th, phi, SHELL_GAP)
            sdown = np.array([0, -1.0, 0]) - n * np.dot([0, -1.0, 0], n)
            if np.linalg.norm(sdown) < 0.15:
                sdown = np.array([0, 0, -1.0]) - n * np.dot([0, 0, -1.0], n)
            sdown = unit(sdown)
            flow = r["flow_abs_deg_median"] + rng.uniform(-12, 12)
            tilt = float(np.clip(r["tilt_deg_median"] + 6 + rng.uniform(-8, 8), 45, 78))
            if t < 0.05:
                flow, tilt = rng.uniform(20, 55), rng.uniform(55, 70)  # hairline row hangs down-and-out: tips break the shell edge
            slat = unit(np.cross(n, sdown)) * (1 if rng.random() < 0.5 else -1)
            tan = math.cos(math.radians(flow)) * sdown + math.sin(math.radians(flow)) * slat
            d = math.cos(math.radians(tilt)) * n + math.sin(math.radians(tilt)) * tan
            L = sample_len(rng, *r["length_cm_p10_50_90"]) / 100 * size_scale
            W = sample_len(rng, *r["base_width_cm_p10_50_90"]) / 100 * size_scale
            W = float(np.clip(W, L / 2.6, min(L / 1.1, 0.05)))
            v, f = blade(root, n, d, L, W, spec["thickness_over_width"], rng)
            v = push_clear(hf.q, v, n, CLUMP_MIN_GAP, f)
            faces.append(f + len(verts))
            verts.extend(v)
            table.append({"region": region, "theta": round(th, 1), "length_cm": round(L * 100, 2), "width_cm": round(W * 100, 2),
                          "flow_deg": round(flow, 1), "root": np.round(root, 4).tolist()})
    return np.array(verts), np.vstack(faces), table


def build_beard(hf, body_meas, spec, rng, size_scale):
    q = hf.q
    face = body_meas["face"]
    mid_x = face["midline_x"]
    chin_y = face["chin_y"]
    # nose bottom from the midline profile: lowest y above the mouth where the profile is still proud
    nose_bottom = face["eye_y"] - 0.05
    A_z = 0.03
    thetas = np.array([-78, -62, -46, -32, -20, -10, 0, 10, 20, 32, 46, 62, 78], float)  # denser over the chin and mouth
    def top_y(th):
        s = min(abs(th) / 70.0, 1.0)
        s = s * s * (3 - 2 * s)
        return (nose_bottom - 0.006) + (hf.lobe_y - 0.005 - (nose_bottom - 0.006)) * s
    row_fracs = [0.0, 0.25, 0.5, 0.75, 1.0]
    bottom_y = chin_y + 0.008
    grid = []
    for fr in row_fracs:
        row = []
        for th in thetas:
            y = top_y(th) + (bottom_y - top_y(th)) * fr
            o = np.array([mid_x, y, A_z])
            dr = az_dir(th, 0)
            h, n, _ = q.first_hit(o[None], dr[None])
            nn = unit(0.5 * unit(n[0]) + 0.5 * dr)
            row.append(h[0] + nn * BEARD_GAP)
        grid.append(row)
    # bib hanging below the chin
    bib = []
    for k, th in enumerate(thetas):
        c = math.cos(math.radians(th))
        p = grid[-1][k] + np.array([0, -(0.05 * c ** 4 + 0.008), 0.014 * c ** 2])
        bib.append(p)
    grid.append(bib)
    # underside back to the throat
    under = []
    for th in thetas:
        o = np.array([mid_x, chin_y + 0.05, 0.06])
        dr = unit(az_dir(th, -50))
        h, n, _ = q.first_hit(o[None], dr[None])
        under.append(h[0] + unit(n[0]) * BEARD_GAP)
    grid.append(under)
    G = np.array(grid)  # rows × cols × 3
    nr, nc = G.shape[:2]
    verts = G.reshape(-1, 3)
    faces = []
    for r in range(nr - 1):
        for i in range(nc - 1):
            a, b, c2, d = r * nc + i, r * nc + i + 1, (r + 1) * nc + i + 1, (r + 1) * nc + i
            faces += [[a, b, c2], [a, c2, d]]
    centre = np.array([mid_x, chin_y + 0.06, 0.06])
    faces = fix_winding_outward(verts, faces, centre)
    verts = hf.clear_shell(verts, faces, BEARD_GAP - 0.001, centre=centre)
    G = verts.reshape(G.shape)
    # clumps: down-pointing locks along the jaw/bib, plus a 2-clump moustache
    r = spec["regions"]["beard"]
    cverts, cfaces, table = [], [], []
    def add(root, n, d, L, W, region):
        v, f = blade(root, n, d, L, W, spec["thickness_over_width"], rng)
        v = push_clear(q, v, n, CLUMP_MIN_GAP, f)
        cfaces.append(f + len(cverts))
        cverts.extend(v)
        table.append({"region": region, "length_cm": round(L * 100, 2), "width_cm": round(W * 100, 2), "root": np.round(root, 4).tolist()})
    for k, rr in [(1, 3), (3, 3), (5, 3), (6, 3), (7, 3), (9, 3), (11, 3), (2, 1), (4, 1), (8, 1), (10, 1)]:
        th = thetas[k]
        root = 0.5 * (G[rr][k] + G[min(rr + 1, 5)][k])
        hz = root - np.array([mid_x, root[1], A_z])
        n = unit(hz)                                    # horizontal out from the jaw axis (a cross-product normal flipped down
                                                        # on the jaw angle and pushed a lock 24 cm down the chest — measured 25/10)
        sdown = unit(np.array([0, -1.0, 0]) - n * np.dot([0, -1.0, 0], n))
        flow = r["flow_abs_deg_median"] + rng.uniform(-8, 8)
        d = math.cos(math.radians(flow)) * sdown + math.sin(math.radians(flow)) * n
        c = math.cos(math.radians(th))
        L = (0.03 + 0.035 * c ** 2 + 0.01 * (rr == 3)) * size_scale * rng.uniform(0.9, 1.1)
        W = (0.026 + 0.008 * c) * size_scale
        add(root, n, d, L, W, "beard")
    # moustache: two locks from under the nose, sweeping down and out over the mouth corners
    for sgn in (-1, 1):
        k = 6 + sgn * 1
        root = G[0][k] * 0.6 + G[1][k] * 0.4
        n = unit(root - np.array([mid_x, root[1], A_z]))
        d = unit(np.array([sgn * 0.55, -0.8, 0.12]))
        add(root + n * 0.003, n, d, 0.034 * size_scale, 0.020 * size_scale, "moustache")
    return verts, np.asarray(faces), np.array(cverts), np.vstack(cfaces), table


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--body", required=True)
    ap.add_argument("--measurements", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--spec", default=os.path.join(SPEC_DIR, "SPEC_primal_spiky_hair.json"))
    ap.add_argument("--sex", default="male")
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--size-scale", type=float, default=1.0, help="clump size × this (spec teachers ran large; Boss: oversize)")
    ap.add_argument("--no-beard", action="store_true")
    a = ap.parse_args()
    spec_all = load_json(a.spec)
    spec = spec_sex(spec_all, a.sex)
    body = load_body(a.body)
    meas = load_json(a.measurements)
    rng = np.random.default_rng(a.seed)
    hf = HeadFrame(body, meas)
    sv, sf, cols, phib = build_scalp_shell(hf)
    cols_arr = np.array(cols, float)
    phib_arr = np.array([phib[c] for c in cols])
    def phib_fn(th):
        th = ((th + 180) % 360) - 180
        return float(np.interp(th, np.r_[cols_arr - 360, cols_arr, cols_arr + 360], np.r_[phib_arr, phib_arr, phib_arr]))
    cv, cf, table = build_hair_clumps(hf, phib_fn, spec, rng, a.size_scale)
    parts = [("hair_shell", "hair", sv, sf), ("hair_clumps", "hair", cv, cf)]
    if not a.no_beard:
        bv, bf, bcv, bcf, btable = build_beard(hf, meas, spec, rng, a.size_scale)
        parts += [("beard_shell", "hair", bv, bf), ("beard_clumps", "hair", bcv, bcf)]
        table += btable
    export_roles(parts, a.out)
    tris = {p[0]: int(len(p[3])) for p in parts}
    info = {"out": a.out, "tris": tris, "tris_total": int(sum(tris.values())), "clumps": table,
            "hairline": hf.hairline, "ear_front_az": hf.ear_front_az, "ear_back_az": hf.ear_back_az}
    with open(os.path.splitext(a.out)[0] + "_clumps.json", "w") as f:
        json.dump(info, f, indent=1)
    counts = {}
    for row in table:
        counts[row["region"]] = counts.get(row["region"], 0) + 1
    print(json.dumps({"tris": tris, "tris_total": info["tris_total"], "clumps_per_region": counts}))


def spec_sex(spec_all, sex):
    """Normalise the spec JSON into {regions: {name: {...}}, thickness_over_width}."""
    regs = {}
    for name, r in spec_all["regions"][sex].items():
        regs[name] = {"length_cm_p10_50_90": r["length_cm"], "base_width_cm_p10_50_90": r["base_width_cm"],
                      "flow_abs_deg_median": r["abs_flow_deg"][1], "flatness": r["flatness"][1],
                      "tilt_deg_median": r["tilt_from_normal_deg"][1]}
    flat = float(np.median([regs[k]["flatness"] for k in ("fringe", "side", "back") if k in regs]))
    return {"regions": regs, "thickness_over_width": max(flat, 0.55)}  # chunkier than the fused teachers read on a 12-tri blade


if __name__ == "__main__":
    main()

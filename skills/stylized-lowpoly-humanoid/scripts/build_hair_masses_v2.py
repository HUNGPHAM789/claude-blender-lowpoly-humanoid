"""v2 primal male HAIR + BEARD: ~30 broad overlapping wedge masses on a concealed cap, one continuous snug beard mass with broad
lobes and a returning underside, two broad moustache lobes (Codex audit 25/10 build brief v2, steps 5–17; Boss: v1 hair = «messy
shards», beard = «mask block»).

  python3 build_hair_masses_v2.py --body male_base_lp.glb --measurements male_measurements.json --out male_hair_v2.glb [--seed 11]

Units from the body: W = skull width, H = skull top → chin. Frame glTF, Y up, faces +Z; output already in place.
Geometries (one material per role, all 'hair'):
  hair_cap__movable       concealed scalp cap (fitter may deform)          ~140 tris
  hair_masses             30 wedges (protected: clears the skin by itself) 22 tris each
  beard_contact__movable  inner contact sheet 2–4 mm off the skin + underside contact
  beard_outer             outer beard surface: cheek → jaw → chin → lobed rim → returning underside (protected)
  moustache               two broad lobes (protected)
Sidecar <out>_parts.json: per-geometry face ranges per clump_id / hair_region / beard part; masks fit_movable / protect_outer.
Flat shading: protected parts are exported with unmerged vertices (one normal per face).
"""
import argparse
import json
import math
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from primal_body_frame import export_roles, fix_winding_outward, load_body, load_json  # noqa: E402
from build_spiky_hair import HeadFrame, unit, az_dir, TOP_ELEVATION  # noqa: E402

CAP_GAP = 0.0035
MASS_GAP = 0.004          # wedge underside off the skin / cap
CONTACT_GAP = 0.003       # beard contact sheet (brief: 0.01–0.02 W ≈ 2–4 mm)
_g = [(i / 4, j / 4) for i in range(5) for j in range(5 - i)]
BARY = np.array([[a, b, 1 - a - b] for a, b in _g])


def build_cap(hf, rows_t=(0.0, 0.33, 0.66), extra_cols=()):
    """extra_cols: additional |azimuth| columns (female widow's peak); default () keeps the male caps unchanged."""
    ef, eb = hf.ear_front_az, hf.ear_back_az
    half = sorted(set([0, 25, 50, 66, round(ef - 6, 1), round(ef, 1), round(ef + 3, 1), round(eb, 1), round(eb + 14, 1), 150] + list(extra_cols)))
    cols = sorted(set([-a for a in half if a > 0] + half + [180]))
    nc = len(cols)
    phib = {c: hf.bottom_elevation(c) for c in cols}
    verts = []
    for t in rows_t:
        for c in cols:
            p, _, _ = hf.scalp_point(c, phib[c] + t * (TOP_ELEVATION - phib[c]), CAP_GAP)
            verts.append(p)
    top, _, _ = hf.scalp_point(0, 90, CAP_GAP)
    verts.append(top)
    faces = []
    for r in range(len(rows_t) - 1):
        for i in range(nc):
            j = (i + 1) % nc
            a, b, c2, d = r * nc + i, r * nc + j, (r + 1) * nc + j, (r + 1) * nc + i
            faces += [[a, b, c2], [a, c2, d]]
    pole = len(verts) - 1
    last = (len(rows_t) - 1) * nc
    for i in range(nc):
        faces.append([last + i, last + (i + 1) % nc, pole])
    verts = np.array(verts)
    faces = fix_winding_outward(verts, faces, hf.C)
    verts = hf.clear_shell(verts, faces, CAP_GAP, iters=16)
    return verts, np.asarray(faces), phib, cols


def surface_frame(hf, theta, phi):
    h, n = hf.hit(theta, phi)
    if np.isnan(h[0]) or np.linalg.norm(h - hf.C) > hf.max_r:
        return None, None
    nn = unit(0.5 * unit(n) + 0.5 * unit(h - hf.C))
    return h, nn


def wedge(hf, theta0, phi0, u_theta, u_phi, length, width, thick, lift_tip, layer, stop=None):
    """one broad lock lying ON the head: a path marched over the scalp in head-angle space, diamond section
    (left edge, ridge, right edge, underside) at root/0.3/0.65, pointed lifted tip. Root ring narrow + low so it emerges from the
    cap/neighbours (root concealment). 22 tris, closed."""
    R = 0.105
    ks = [0.0, 0.3, 0.65, 1.0]
    wprof = [0.7, 1.0, 0.8, 0.0]
    tprof = [0.12, 0.42, 0.32, 0.0]
    u = np.array([u_theta, u_phi], float)
    u /= np.linalg.norm(u)
    pts, nrms = [], []
    th, ph = theta0, phi0
    s_prev = 0.0
    for k in ks:
        s = k * length
        # march in small steps so the path follows the curvature
        steps = 6
        for _ in range(steps):
            ds = (s - s_prev) / steps
            ph_c = max(min(ph, 84), -80)
            th += math.degrees(ds * u[0] / (R * max(math.cos(math.radians(ph_c)), 0.25)))
            ph += math.degrees(ds * u[1] / R)
        s_prev = s
        p, n = surface_frame(hf, th, min(ph, 88))
        if p is None or (stop is not None and k > 0 and stop(p)):
            break
        pts.append(p)
        nrms.append(n)
    if len(pts) < 3:
        return None
    m = len(pts)
    e = MASS_GAP + layer * 0.004
    rings = []
    for i in range(m - 1):
        p, n = pts[i], nrms[i]
        tang = unit(pts[min(i + 1, m - 1)] - pts[max(i - 1, 0)])
        lat = unit(np.cross(n, tang))
        w = width * wprof[i]
        t = width * thick * tprof[i] / 0.42
        rings.append([p + lat * w / 2 + n * (e + 0.002), p + n * (e + t), p - lat * w / 2 + n * (e + 0.002), p + n * e])
    last_p, last_n = pts[-1], nrms[-1]
    tip = last_p + last_n * (e + lift_tip * length)
    V = [v for ring in rings for v in ring] + [tip]
    F = []
    nr = len(rings)
    for r in range(nr - 1):
        for i in range(4):
            j = (i + 1) % 4
            F += [[4 * r + i, 4 * r + j, 4 * (r + 1) + j], [4 * r + i, 4 * (r + 1) + j, 4 * (r + 1) + i]]
    tipi = len(V) - 1
    for i in range(4):
        F.append([4 * (nr - 1) + i, 4 * (nr - 1) + (i + 1) % 4, tipi])
    F += [[0, 2, 1], [0, 3, 2]]  # root cap (closed)
    V = np.array(V)
    F = np.array(F)
    centre = V[:-1].mean(axis=0)
    # outward winding about the wedge's own centre line
    tri = V[F]
    nrm = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0])
    axis_pts = np.array([np.mean(rg, axis=0) for rg in rings] + [tip])
    cen = tri.mean(axis=1)
    near = axis_pts[np.argmin(np.linalg.norm(cen[:, None] - axis_pts[None], axis=2), axis=1)]
    flip = np.einsum("ij,ij->i", nrm, cen - near) < 0
    F[flip] = F[flip][:, ::-1]
    return V, F, np.array(nrms[:nr] + [last_n])


def clear_wedge(hf, V, F, normals_per_ring, min_gap=0.003, iters=10):
    """push only the offending vertices out along their ring normal (a whole-wedge lift would expose its root)."""
    ring_of = np.minimum(np.arange(len(V)) // 4, len(normals_per_ring) - 1)
    dirs = normals_per_ring[ring_of]
    for _ in range(iters):
        pts = np.vstack([V, np.einsum("bk,fkj->fbj", BARY, V[F]).reshape(-1, 3)])
        sd = hf.q.clearance(pts)
        lack_v = min_gap - sd[:len(V)]
        lack_f = (min_gap - sd[len(V):]).reshape(len(F), len(BARY)).max(axis=1)
        push = np.maximum(lack_v, 0)
        for f, l in zip(F, lack_f):
            if l > 0:
                push[f] = np.maximum(push[f], l)
        if push.max() < 0.0002:
            break
        V = V + dirs * (push[:, None] + 0.0003 * (push[:, None] > 0))
    return V


def layout(hf, H, W, rng):
    """(region, theta, phi, u_theta, u_phi, L, W, thick, lift, layer, stop) — flow coherent per region."""
    brow = hf.face["brow_y"]
    ef, eb, ear_top = hf.ear_front_az, hf.ear_back_az, hf.ear_top_y
    fringe_stop_y = brow + 0.06 * H
    def stop_fringe(p):
        return p[1] < fringe_stop_y + rng.uniform(-0.008, 0.008)
    def stop_side(p):
        az = abs(math.degrees(math.atan2(p[0] - hf.C[0], p[2] - hf.C[2])))
        if ef - 4 < az < eb + 4:
            return p[1] < ear_top + 0.006           # never over the most-proud ear point
        return p[1] < hf.lobe_y
    def stop_back(p):
        return p[1] < hf.nape_y - 0.012
    J = lambda a: a * rng.uniform(0.9, 1.1)
    out = []
    # crown: broad, shorter, the ONLY upward peaks; radiate from the crown whorl (behind the top)
    for th in (180, 120, 60, 0, -60, -120):
        out.append(("crown", th + rng.uniform(-8, 8), 70, 0.0, -1.0, J(0.24 * H), J(0.30 * W), 0.45, 0.42, 2, None))
    # fringe: falls DOWN onto the forehead, sweeping slightly to the figure's left, tips 0.04–0.10 H above the brow
    for th in (-42, -26, -10, 6, 22, 38):
        out.append(("fringe", th, 52 + rng.uniform(-3, 3), 0.28, -1.0, 0.4 * H, J(0.24 * W), 0.4, 0.08, 1, stop_fringe))
    # sides: down and BACK, stop above the ear (front lock may reach the sideburn)
    for sgn in (1, -1):
        for th, ph in ((58, 40), (80, 46), (102, 44), (122, 40)):
            out.append(("side", sgn * (th + rng.uniform(-4, 4)), ph, sgn * 0.75, -1.0, J(0.32 * H), J(0.24 * W), 0.38, 0.18, 1, stop_side))
    # back / nape: two rows hanging down, tips flick out a little at the nape
    for th in (128, 152, 178, -156, -132):
        out.append(("back", th + rng.uniform(-5, 5), 34, 0.0, -1.0, J(0.36 * H), J(0.27 * W), 0.4, 0.14, 1, stop_back))
    for th in (140, 165, -168, -144, -120):
        out.append(("back", th + rng.uniform(-5, 5), 6, 0.0, -1.0, J(0.30 * H), J(0.25 * W), 0.36, 0.2, 0, stop_back))
    return out


def build_beard(hf, meas, H, W, top_y_fn=None):
    """continuous cheek–jaw–chin mass. Per column a closed loop of rows:
       T (top edge) → O_mid → O_chin → LOBE rim → U_throat (underside contact) → U_jaw → I_chin → I_mid → back to T.
    Inner rows I_* / U_* = contact (CONTACT_GAP off the skin) → beard_contact__movable; O_* / LOBE / underside → beard_outer."""
    q = hf.q
    face = meas["face"]
    mid_x, chin_y = face["midline_x"], face["chin_y"]
    nose_bottom = face["eye_y"] - 0.05
    A_z = 0.03
    thetas = np.array([-75, -60, -46, -33, -22, -13, -6, 0, 6, 13, 22, 33, 46, 60, 75], float)  # ends stay in front of the ear lobe  # dense over lips/chin
    nc = len(thetas)
    def top_y(th):
        """cheek line: from under the nose it RISES toward the sideburn (sheet), never above eye − 1.5 cm"""
        xs = [0, 20, 40, 60, 80]
        ys = [nose_bottom - 0.004, nose_bottom + 0.016, nose_bottom + 0.032, face["eye_y"] - 0.014, face["eye_y"] - 0.008]  # up to the nose wings (3/4 views saw skin above the cheek line)
        return float(np.interp(abs(th), xs, ys))
    if top_y_fn is not None:                  # male v7 chin-strap: the caller decides the top edge (default keeps v2–v6 unchanged)
        top_y = top_y_fn
    def skin(y, th):
        o = np.array([mid_x, y, A_z])
        dr = az_dir(th, 0)
        h, n, _ = q.first_hit(o[None], dr[None])
        return h[0], unit(0.5 * unit(n[0]) + 0.5 * dr)
    fr = [0.0, 0.25, 0.5, 0.72, 0.88, 1.0]   # dense over the lips and chin bulge   # contact rows top → chin (dense: the sheet must follow the lip groove)
    bottom = chin_y + 0.03          # last horizontal-ray row stays ON the chin (lower rays slip under the jaw)
    rows_in, rows_n = [], []
    for f in fr:
        rr, nn = [], []
        for th in thetas:
            y = top_y(th) + (bottom - top_y(th)) * f
            h, n = skin(y, th)
            rr.append(h)
            nn.append(n)
        rows_in.append(rr)
        rows_n.append(nn)
    rows_in = np.array(rows_in)
    rows_n = np.array(rows_n)
    contact = rows_in + rows_n * CONTACT_GAP
    # underside + chin-bottom rows: rays fanned from the jaw axis at the column's own azimuth (snapped/central rays collapsed the
    # columns onto the narrow chin and folded the sheet 8 mm into it; a ray from in front of the jaw hit the neck 10–20 cm low on
    # the side columns — both measured 25/10). Elevation flattens toward the sides so they stay on the jaw line.
    def fan(el):
        out = []
        for th in thetas:
            c2_ = math.cos(math.radians(th)) ** 2
            o = np.array([mid_x, bottom - 0.004, A_z])
            dr = unit(az_dir(th, el * (0.35 + 0.65 * c2_)))
            h, n, dist = q.first_hit(o[None], dr[None])
            if not np.isfinite(dist[0]) or dist[0] > 0.075:   # the ray left through the throat and hit the chest: snap instead
                _, i = q.kd.query(o + dr * 0.05)
                h, n = q.P[i][None], q.N[i][None]
            out.append(h[0] + unit(0.5 * unit(n[0]) + 0.5 * unit(h[0] - o)) * CONTACT_GAP)
        return np.array(out)
    Cb, U1, U2 = fan(-22.0), fan(-42.0), fan(-58.0)
    # the underside must stay ABOVE the lobed rim (an underside dipping below the lobes showed as loose shards in front view and a
    # slatted slit in side view — Boss 25/10 «lủng»): lift any underside point that sits lower than the rim above it
    # outer thickness (brief: cheek 7–13 mm, jaw 9–15, chin front 11–17)
    c2 = np.cos(np.radians(thetas)) ** 2
    t_cheek = 0.008 + 0.002 * c2
    t_jaw = 0.010 + 0.003 * c2
    t_chin = 0.011 + 0.004 * c2
    K = len(fr) - 1
    def t_row(f):
        if f < 0.5:
            return t_cheek * max(0.8, f / 0.5)
        if f < 0.8:
            w = (f - 0.5) / 0.3
            return t_cheek * (1 - w) + t_jaw * w
        w = (f - 0.8) / 0.2
        return t_jaw * (1 - w) + t_chin * w
    O = [contact[r] + rows_n[r] * t_row(fr[r])[:, None] for r in range(1, K + 1)]
    O4 = O[-1]
    # lobed rim below the chin: 6 broad lobes (tips at alternate columns), centre longest (0.08–0.15 H → 0.11 H)
    ext = np.array([0.012, 0.02, 0.016, 0.03, 0.022, 0.034, 0.03, 0.036, 0.03, 0.034, 0.022, 0.03, 0.016, 0.02, 0.012])
    ext = ext * (float(os.environ.get("BEARD_LOBE_H", "0.13")) * H / 0.036)   # male v7 chin strap: 0.09
    lob = O4 + np.c_[np.zeros(nc), -ext, 0.12 * ext * c2]   # lobes hang down, not a forward-jutting plate (side view showed a slit)
    # loop order per column (outer side then back along the contact side)
    for arr, margin in ((U2, 0.006), (U1, 0.010), (Cb, 0.014)):
        for c in range(nc):
            if arr[c, 1] < lob[c, 1] + margin:
                o = np.array([mid_x, lob[c, 1] + margin, A_z])
                h, n, dist = q.first_hit(o[None], unit(az_dir(thetas[c], 0))[None])
                if np.isfinite(dist[0]):
                    arr[c] = h[0] + unit(n[0]) * CONTACT_GAP
    loop = [contact[0]] + O + [lob, U2, U1, Cb] + [contact[r] for r in range(K, 0, -1)]
    L = len(loop)
    G = np.stack(loop, axis=0)            # L × nc × 3
    V = G.reshape(-1, 3)
    idx = lambda r, c: (r % L) * nc + c
    outer_faces, contact_faces = [], []
    for r in range(L):
        for c in range(nc - 1):
            quad = [[idx(r, c), idx(r, c + 1), idx(r + 1, c + 1)], [idx(r, c), idx(r + 1, c + 1), idx(r + 1, c)]]
            (outer_faces if r < K + 2 else contact_faces).extend(quad)
    # side caps (sideburn ends): fan over each end column loop
    # strip-triangulated between the outer chain (T → O… → lobe) and the contact chain (T → contact… → Cb → U1 → U2 → lobe):
    # a fan from the centroid of this CONCAVE loop left see-through slits in side view (Boss 25/10: «thấy white background»)
    caps = []
    for c in (0, nc - 1):
        A = [idx(r, c) for r in range(0, K + 2)]                       # T, O1..OK, lobe
        B = [idx(0, c)] + [idx(r, c) for r in range(L - 1, K + 1, -1)] + [idx(K + 1, c)]   # T, contact1..K, Cb, U1, U2, lobe
        i = j = 0
        tA = np.linspace(0, 1, len(A))
        tB = np.linspace(0, 1, len(B))
        while i < len(A) - 1 or j < len(B) - 1:
            if j >= len(B) - 1 or (i < len(A) - 1 and tA[i + 1] <= tB[j + 1]):
                caps.append([A[i], A[i + 1], B[j]])
                i += 1
            else:
                caps.append([A[i], B[j + 1], B[j]])
                j += 1
    outer_faces += caps
    centre = np.array([mid_x, chin_y + 0.04, 0.05])
    allf = np.array(outer_faces + contact_faces)
    # orient: outward from the beard's own centreline (the mid point between contact and outer rows)
    tri = V[allf]
    nrm = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0])
    cen = tri.mean(axis=1)
    core_all = np.vstack([0.5 * (contact[r] + O[r - 1]) for r in range(1, K + 1)] + [0.5 * (U1 + lob)])
    near = core_all[np.argmin(np.linalg.norm(cen[:, None] - core_all[None], axis=2), axis=1)]
    flip = np.einsum("ij,ij->i", nrm, cen - near) < 0
    allf[flip] = allf[flip][:, ::-1]
    n_out = len(outer_faces)
    # snug clear: push only offending vertices along their OWN skin normal (a radial push from one centre lifted the whole contact
    # sheet 8 mm off the lips/chin — measured 25/10)
    dirs = np.zeros_like(V)
    dirs[:] = unit(V - np.array([mid_x, chin_y + 0.04, 0.0]))
    for li, r in [(0, 0)] + [(K + 5 + (K - r), r) for r in range(K, 0, -1)]:
        dirs[li * nc:(li + 1) * nc] = rows_n[r]
    for _ in range(int(os.environ.get("BEARD_CLEAR_ITERS", "50"))):   # diagnosis: BEARD_CLEAR_ITERS=0 shows the unpushed sheet
        pts = np.vstack([V, np.einsum("bk,fkj->fbj", BARY, V[allf]).reshape(-1, 3)])
        c = q.clearance(pts)
        push = np.maximum(CONTACT_GAP - 0.0005 - c[:len(V)], 0)
        lack = (CONTACT_GAP - 0.0005 - c[len(V):]).reshape(len(allf), len(BARY))
        for f, ls in zip(allf, lack):
            for b, l in zip(BARY, ls):
                if l > 0:                      # bary-weighted: lift the corner nearest the penetration, not the whole face
                    push[f] = np.maximum(push[f], l * np.clip(b * 1.6, 0, 1))
        if push.max() < 0.0002:
            break
        V = V + dirs * (np.minimum(push, 0.002)[:, None] + 0.0001 * (push[:, None] > 0))
    envelope = {"contact_rows": contact.tolist(), "outer_t_mm": {"cheek": (t_cheek * 1000).round(1).tolist(),
                "jaw": (t_jaw * 1000).round(1).tolist(), "chin": (t_chin * 1000).round(1).tolist()}, "lobe_ext_mm": (ext * 1000).round(1).tolist()}
    return V, allf[:n_out], allf[n_out:], envelope, contact, rows_n


def moustache(hf, meas, contact, rows_n):
    """two broad lobes from under the nose, down and out over the mouth corners, lying on the upper lip."""
    out = []
    mid_x = meas["face"]["midline_x"]
    nc = contact.shape[1]
    c0 = nc // 2
    for sgn in (-1, 1):
        root = contact[0][c0] * 0.85 + contact[0][c0 + sgn] * 0.15 + np.array([0, 0.011, 0.007])   # lobes overlap at the philtrum and start right under the nose (3/4 views saw philtrum skin)
        n = rows_n[0][c0 + sgn]
        d = unit(np.array([sgn * 0.85, -0.5, 0.0]) - n * np.dot(np.array([sgn * 0.85, -0.5, 0.0]), n))
        lat = unit(np.cross(n, d))
        L, Wd = 0.041, 0.036          # broad: the lobe's upper edge must weld into the cheek line (no slit beside the nose)
        V = []
        for k, (wf, tf) in enumerate(((0.8, 0.010), (1.0, 0.013), (0.7, 0.009))):
            p = root + d * L * [0.0, 0.4, 0.75][k]
            V += [p + lat * Wd * wf / 2 + n * 0.003, p + n * (0.003 + tf), p - lat * Wd * wf / 2 + n * 0.003, p + n * 0.002]
        V.append(root + d * L + n * 0.006 + np.array([0, -0.004, 0]))
        V = np.array(V)
        F = []
        for r in range(2):
            for i in range(4):
                j = (i + 1) % 4
                F += [[4 * r + i, 4 * r + j, 4 * (r + 1) + j], [4 * r + i, 4 * (r + 1) + j, 4 * (r + 1) + i]]
        for i in range(4):
            F.append([8 + i, 8 + (i + 1) % 4, 12])
        F += [[0, 2, 1], [0, 3, 2]]
        F = np.array(F)
        tri = V[F]
        nrm = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0])
        cen = tri.mean(axis=1)
        axis_pts = np.array([V[0:4].mean(0), V[4:8].mean(0), V[8:12].mean(0), V[12]])
        near = axis_pts[np.argmin(np.linalg.norm(cen[:, None] - axis_pts[None], axis=2), axis=1)]
        flip = np.einsum("ij,ij->i", nrm, cen - near) < 0
        F[flip] = F[flip][:, ::-1]
        out.append((V, F, n))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--body", required=True)
    ap.add_argument("--measurements", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--seed", type=int, default=11)
    a = ap.parse_args()
    rng = np.random.default_rng(a.seed)
    meas = load_json(a.measurements)
    body = load_body(a.body)
    hf = HeadFrame(body, meas)
    W = meas["skull"]["width_m"]
    H = float(body.vertices[:, 1].max() - meas["face"]["chin_y"])
    cap_v, cap_f, _, _ = build_cap(hf)
    mv, mf, table = [], [], []
    for (reg, th, ph, ut, up, L, Wd, thick, lift, layer, stop) in layout(hf, H, W, rng):
        res = wedge(hf, th, ph, ut, up, L, Wd, thick, lift, layer, stop)
        if res is None:
            table.append({"region": reg, "theta": round(th, 1), "skipped": True})
            continue
        V, F, nr = res
        V = clear_wedge(hf, V, F, nr)
        f0 = len(mf)
        mf.extend((F + len(mv)).tolist())
        mv.extend(V.tolist())
        table.append({"clump_id": len(table), "region": reg, "theta": round(th, 1), "length_cm": round(L * 100, 1),
                      "width_cm": round(Wd * 100, 1), "faces": [f0, len(mf)]})
    mv, mf = np.array(mv), np.array(mf)
    bv, b_out, b_con, envelope, contact, rows_n = build_beard(hf, meas, H, W)
    must = moustache(hf, meas, contact, rows_n)
    sv, sf = [], []
    for V, F, n in must:
        F2 = F + len(sv)
        sv.extend(V.tolist())
        sf.extend(F2.tolist())
    sv, sf = np.array(sv), np.array(sf)
    # beard parts share the loop vertices; split into two geometries (contact may be deformed by the fitter)
    def sub(V, F):
        used = np.unique(F)
        remap = -np.ones(len(V), int)
        remap[used] = np.arange(len(used))
        return V[used], remap[F]
    bov, bof = sub(bv, b_out)
    bcv, bcf = sub(bv, b_con)
    parts = [("hair_cap__movable", "hair", cap_v, cap_f), ("hair_masses", "hair", mv, mf),
             ("beard_contact__movable", "hair", bcv, bcf), ("beard_outer", "hair", bov, bof), ("moustache", "hair", sv, sf)]
    closed = {}
    import trimesh
    for name, _, v, f in parts:
        closed[name] = bool(trimesh.Trimesh(v, f, process=True).is_watertight)
    closed["beard_contact+outer"] = bool(trimesh.Trimesh(bv, np.vstack([b_out, b_con]), process=True).is_watertight)
    export_roles(parts, a.out, flat=[p[0] for p in parts if not p[0].endswith("__movable")])
    tris = {p[0]: int(len(p[3])) for p in parts}
    counts = {}
    for row in table:
        if not row.get("skipped"):
            counts[row["region"]] = counts.get(row["region"], 0) + 1
    info = {"out": a.out, "units": {"W_m": W, "H_m": H}, "tris": tris, "tris_total": int(sum(tris.values())),
            "clumps_per_region": counts, "clumps": table, "beard": {"lobes": 6, "moustache_lobes": 2, **envelope},
            "closed_before_flat_export": closed,
            "masks": {"fit_movable": [p[0] for p in parts if p[0].endswith("__movable")],
                      "protect_outer": [p[0] for p in parts if not p[0].endswith("__movable")]}}
    with open(os.path.splitext(a.out)[0] + "_parts.json", "w") as f:
        json.dump(info, f, indent=1)
    print(json.dumps({"tris": tris, "total": info["tris_total"], "clumps": counts, "closed": closed}))


if __name__ == "__main__":
    main()

"""Male hair v9 = male_hair_v8.glb with ONLY the beard (beard_contact__movable + beard_outer) rebuilt (Boss 25/10: «râu nam đúng hướng
rồi, cho dài ôm hai bên mặt hơn, dày hơn thêm tí nữa, râu dưới cong đúng rồi, nhưng cover thêm chút nữa chỗ da cằm môi dưới - phía
bên râu dưới bên phía trái bị một vệt hỏng nhìn thấy da»). Moustache v8, cap, masses and chunks are copied unchanged.

  python3 build_male_beard_v9.py --body male_base_lp.glb --measurements male_measurements.json --hair-v8 male_hair_v8.glb --out male_hair_v9.glb

Changes against v7/v8 (same chin-strap construction otherwise):
- top edge per column azimuth: the strap climbs up both sides to SIDEBURN_OVERLAP above the lowest sideburn hair (measured on the v8
  hair in front of each ear), so it joins the sideburn (v7/v8 stopped 2–3 cm short at the jaw corner);
- outer surface THICK_SCALE × further off the jaw;
- centre top edge at the lower-lip bottom − LIP_BAND (bare band under the lower lip ≤ 5 mm, the lip itself stays clear);
- winding made consistent over the closed surface (v8 had inward faces on the left jaw = the see-through streak).
"""
import argparse
import json
import math
import os
import sys

import numpy as np
import trimesh

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from primal_body_frame import export_roles, load_body, load_json  # noqa: E402
from build_spiky_hair import HeadFrame, unit, az_dir  # noqa: E402
from measure_primal_assets import parts_of  # noqa: E402
from build_hair_masses_v2 import CONTACT_GAP, BARY  # noqa: E402
from build_male_beard_v7 import make_top_edge, mouth_points  # noqa: E402

THICK_SCALE = float(os.environ.get("BEARD_THICK_SCALE", "1.5"))
JAW_THICK_SCALE = float(os.environ.get("BEARD_JAW_THICK_SCALE", "1.1"))
CHIN_THICK_SCALE = float(os.environ.get("BEARD_CHIN_THICK_SCALE", "1.0"))
SIDEBURN_OVERLAP = 0.020
LIP_BAND = 0.004
RAMP_FROM_DEG = 46.0
RAMP_TO_DEG = 62.0


def consistent_outward(V, F):
    m = trimesh.Trimesh(V, F, process=False)
    trimesh.repair.fix_winding(m)
    if m.volume < 0:
        m.invert()
    return np.array(m.faces)


def rewound_faces(V, F):
    """same vertices, faces re-wound consistently and outward (the v8 moustache_R tip was wound inside-out: background showed
    through it from the left side). Returns (faces, number flipped)."""
    m = trimesh.Trimesh(V, F, process=False)
    m.merge_vertices()
    trimesh.repair.fix_winding(m)
    if m.volume < 0:
        m.invert()
    n_old = np.cross(V[F[:, 1]] - V[F[:, 0]], V[F[:, 2]] - V[F[:, 0]])
    n_new = m.face_normals
    flip = np.einsum("ij,ij->i", n_old, n_new) < 0
    F2 = F.copy()
    F2[flip] = F2[flip][:, ::-1]
    return F2, int(flip.sum())


def sideburn_bottom(hair_parts, mid_x):
    """lowest scalp-hair point in front of each ear (the sideburn tip): {+1: (y, az), -1: (y, az)} — +1 = +x side"""
    hv = np.vstack([hair_parts[k].vertices for k in ("hair_cap__movable", "hair_masses", "hair_chunks")])
    out = {}
    for s in (1, -1):
        sel = hv[((hv[:, 0] - mid_x) * s > 0.055) & (hv[:, 2] > 0.0) & (hv[:, 1] < 1.70)]
        p = sel[np.argmin(sel[:, 1])]
        out[s] = (float(p[1]), float(math.degrees(math.atan2(p[0] - mid_x, p[2] - 0.03))), p.tolist())
    return out


def make_top_edge_v9(hf, meas, sb):
    top_v7, _ = make_top_edge(hf, meas)
    _, lip_corner_y, _ = mouth_points(meas)
    centre = lip_corner_y - LIP_BAND
    def top_y(th):
        s = 1 if th >= 0 else -1
        a = abs(th)
        y7 = top_v7(th)
        if a <= 8:
            return float(max(y7, centre))
        if a <= 15:
            return float(max(y7, centre + 0.002))
        if a <= RAMP_FROM_DEG:
            return float(y7)
        y_from = top_v7(s * RAMP_FROM_DEG)
        y_to = sb[s][0] + SIDEBURN_OVERLAP
        t = min(1.0, (a - RAMP_FROM_DEG) / (RAMP_TO_DEG - RAMP_FROM_DEG))
        return float(max(y7, y_from + t * (y_to - y_from)))
    return top_y


def build_beard_v9(hf, meas, H, W, top_y_fn, thick_scale):
    """continuous cheek–jaw–chin mass. Per column a closed loop of rows:
       T (top edge) → O_mid → O_chin → LOBE rim → U_throat (underside contact) → U_jaw → I_chin → I_mid → back to T.
    Inner rows I_* / U_* = contact (CONTACT_GAP off the skin) → beard_contact__movable; O_* / LOBE / underside → beard_outer."""
    q = hf.q
    face = meas["face"]
    mid_x, chin_y = face["midline_x"], face["chin_y"]
    nose_bottom = face["eye_y"] - 0.05
    A_z = 0.03
    thetas = np.array([-80, -75, -60, -46, -33, -22, -13, -6, 0, 6, 13, 22, 33, 46, 60, 75, 80], float)   # v9: ±80 = the column under the sideburn's back edge, just in front of the ear lobe (az ±82–84)  # ends stay in front of the ear lobe  # dense over lips/chin
    nc = len(thetas)
    def top_y(th):
        """cheek line: from under the nose it RISES toward the sideburn (sheet), never above eye − 1.5 cm"""
        xs = [0, 20, 40, 60, 80]
        ys = [nose_bottom - 0.004, nose_bottom + 0.016, nose_bottom + 0.032, face["eye_y"] - 0.014, face["eye_y"] - 0.008]  # up to the nose wings (3/4 views saw skin above the cheek line)
        return float(np.interp(abs(th), xs, ys))
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
    t_cheek = (0.008 + 0.002 * c2) * thick_scale       # v9: Boss «dày hơn thêm tí nữa»
    t_jaw = (0.010 + 0.003 * c2) * JAW_THICK_SCALE
    t_chin = (0.011 + 0.004 * c2) * CHIN_THICK_SCALE   # the chin front stays near v8: the fitter's «beard hugs the face» p90 ≤ 18 mm
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
    ext = np.array([0.008, 0.012, 0.02, 0.016, 0.03, 0.022, 0.034, 0.03, 0.036, 0.03, 0.034, 0.022, 0.03, 0.016, 0.02, 0.012, 0.008])
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
    # v9 orient: the nearest-core heuristic wound a run of faces INWARD on the left jaw (v8 «vệt hỏng»: those faces are culled by
    # the single-sided material, so skin showed through). The loop × column tube + strip caps is one closed surface: make the
    # winding consistent over the connectivity, then point it outward by the sign of the enclosed volume.
    allf = consistent_outward(V, np.array(outer_faces + contact_faces))
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


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--body", required=True)
    ap.add_argument("--measurements", required=True)
    ap.add_argument("--hair-v8", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--rewind-moustache", action="store_true",
                    help="variant: re-wind the v8 moustache faces outward (vertices untouched); default keeps it byte-identical")
    a = ap.parse_args()
    meas = load_json(a.measurements)
    body = load_body(a.body)
    hf = HeadFrame(body, meas)
    W = meas["skull"]["width_m"]
    H = float(body.vertices[:, 1].max() - meas["face"]["chin_y"])
    v8 = parts_of(a.hair_v8)
    sb = sideburn_bottom(v8, meas["face"]["midline_x"])
    os.environ.setdefault("BEARD_LOBE_H", "0.07")     # reproduces the v7/v8 lobe lengths (centre 21.1 mm)
    top_y = make_top_edge_v9(hf, meas, sb)
    bv, b_out, b_con, envelope, contact, rows_n = build_beard_v9(hf, meas, H, W, top_y, THICK_SCALE)
    def sub(Vv, F):
        used = np.unique(F)
        remap = -np.ones(len(Vv), int)
        remap[used] = np.arange(len(used))
        return Vv[used], remap[F]
    bov, bof = sub(bv, b_out)
    bcv, bcf = sub(bv, b_con)
    parts = []
    for name in ("hair_cap__movable", "hair_masses", "hair_chunks"):
        parts.append((name, "hair", v8[name].vertices, v8[name].faces))
    parts += [("beard_contact__movable", "hair", bcv, bcf), ("beard_outer", "hair", bov, bof)]
    rewound = {}
    for name in ("moustache_L", "moustache_R"):
        F = np.array(v8[name].faces)
        if a.rewind_moustache:
            F, rewound[name] = rewound_faces(np.array(v8[name].vertices), F)
        parts.append((name, "hair", v8[name].vertices, F))
    export_roles(parts, a.out, flat=["beard_outer"])
    tris = {p[0]: int(len(p[3])) for p in parts}
    v8info = json.load(open(os.path.splitext(a.hair_v8)[0] + "_parts.json"))
    info = {"out": a.out, "from": a.hair_v8, "tris": tris, "tris_total": int(sum(tris.values())),
            "beard": {"lobes": 6, "moustache_lobes": 2, **envelope}, "clumps": [], "clumps_per_region": {}, "closed_before_flat_export": {},
            "v9": {"thick_scale": THICK_SCALE, "jaw_thick_scale": JAW_THICK_SCALE, "chin_thick_scale": CHIN_THICK_SCALE, "sideburn_bottom": {str(k): v for k, v in sb.items()}, "sideburn_overlap_mm": SIDEBURN_OVERLAP * 1000,
                   "lip_band_mm": LIP_BAND * 1000, "moustache_faces_rewound": rewound, "top_edge_y": [round(top_y(t), 4) for t in (-80, -75, -60, -46, -33, -22, -13, -6, 0, 6, 13, 22, 33, 46, 60, 75, 80)]},
            "params": v8info.get("params")}
    with open(os.path.splitext(a.out)[0] + "_parts.json", "w") as f:
        json.dump(info, f, indent=1, default=float)
    print(json.dumps({"tris": tris, "total": info["tris_total"], "sideburn": sb, "top": info["v9"]["top_edge_y"]}))


if __name__ == "__main__":
    main()

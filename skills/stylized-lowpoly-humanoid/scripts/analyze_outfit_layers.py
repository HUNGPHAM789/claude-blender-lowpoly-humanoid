"""Layer/flap grammar of a torn leather garment from its molds (Boss 25/10/2026: «layered and torned primal outfit … muốn số liệu gì
thì cứ phân tích 2 outfit đó»). Needs segment_mesh.py outputs (<p>_molds.json + <p>_face_molds.npy) for the same fitted mesh.

  python3 analyze_outfit_layers.py --mesh <outfit_fit.glb> --molds <p> --out <dir>/<name>   ⇒ <name>_layers.json

flaps    = outer + lining molds below the belt: length (vertical span), width (arc length round the body), fill = area / (length·width)
           (triangle-ish tooth ≈ 0.5, square panel ≈ 1), tip = lowest point
rows     = flap centres sorted by height, split where the gap ≥ ROW_GAP of the garment height ⇒ count, height, flaps per row
stagger  = for each flap, angular offset to the nearest flap of the row above ÷ that row's mean spacing (0 aligned, 0.5 fully staggered)
lining   = how far each lining flap's lowest point reaches below the outer flaps around it (±20°) — positive = shows under the edge
thickness= horizontal rays: distance between the first and last surface hit (generated layers are fused ⇒ total leather thickness)
belt     = number of belt molds round the ring (rope lumps), ornament = width/height/depth of the ornament molds
"""
import argparse, json, math
import numpy as np
import trimesh

ROW_GAP = 0.12


def main(mesh_p, molds_p, out):
    m = trimesh.load(mesh_p, force="mesh"); m = trimesh.Trimesh(m.vertices, m.faces, process=True)
    M = json.load(open(molds_p + "_molds.json"))["molds"]; lab = np.load(molds_p + "_face_molds.npy")
    C = m.triangles_center; A = m.area_faces; y0, y1 = m.vertices[:, 1].min(), m.vertices[:, 1].max(); H = y1 - y0
    ax = np.array([np.average(C[:, 0], weights=A), 0, np.average(C[:, 2], weights=A)])
    th = np.degrees(np.arctan2(C[:, 0] - ax[0], C[:, 2] - ax[2])); rho = np.hypot(C[:, 0] - ax[0], C[:, 2] - ax[2])
    flaps = []
    for k in M:
        if k.get("role") not in ("outer", "lining"): continue
        f = np.where(lab == k["id"])[0]
        if len(f) < 30: continue
        tt = th[f]; c0 = math.degrees(math.atan2(np.mean(np.sin(np.radians(tt))), np.mean(np.cos(np.radians(tt)))))
        dt = (tt - c0 + 180) % 360 - 180; span = np.percentile(dt, 95) - np.percentile(dt, 5)
        width = math.radians(span) * float(np.median(rho[f])); length = float(np.percentile(C[f, 1], 97) - np.percentile(C[f, 1], 3))
        flaps.append({"id": k["id"], "role": k["role"], "theta": c0, "y": float(np.average(C[f, 1], weights=A[f])), "low": float(C[f, 1].min()),
                      "length_cm": length * 100, "width_cm": width * 100, "fill": float(A[f].sum() / max(length * width, 1e-9))})
    # rows
    F = sorted(flaps, key=lambda r: -r["y"]); rows = [[F[0]]] if F else []
    for r in F[1:]:
        if rows[-1][-1]["y"] - r["y"] >= ROW_GAP * H: rows.append([r])
        else: rows[-1].append(r)
    rows = [rw for rw in rows if len(rw) >= 2]
    stag = []
    for up_, lo_ in zip(rows, rows[1:]):
        ut = np.array([r["theta"] for r in up_]); sp = 360 / max(len(up_), 1)
        for r in lo_:
            d = np.min(np.abs((ut - r["theta"] + 180) % 360 - 180)); stag.append(d / sp)
    # lining exposure
    expo = []
    for r in flaps:
        if r["role"] != "lining": continue
        around = [o for o in flaps if o["role"] == "outer" and abs((o["theta"] - r["theta"] + 180) % 360 - 180) < 20 and o["y"] > r["y"] - 0.05]
        if around: expo.append((min(o["low"] for o in around) - r["low"]) * 100)
    # thickness by rays
    import sys, os
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from analyze_outfit import ray_hits
    O, D = [], []
    for y in np.linspace(y0 + 0.15 * H, y0 + 0.75 * H, 8):
        for t in range(0, 360, 15): O.append([ax[0], y, ax[2]]); D.append([math.sin(math.radians(t)), 0, math.cos(math.radians(t))])
    thick = []
    for (o, d_), T in zip(zip(O, D), ray_hits(m.triangles, np.array(O, float), np.array(D, float))):
        if len(T) >= 2:
            P = m.triangles[T].mean(axis=1); dd = np.linalg.norm(P - np.array(o), axis=1); thick.append((dd.max() - dd.min()) * 100)
    orn = np.where(np.isin(lab, [k["id"] for k in M if k.get("role") == "ornament"]))[0]
    q = lambda a: [round(float(np.percentile(a, p)), 2) for p in (10, 50, 90)] if len(a) else None
    res = {"garment_height_cm": round(H * 100, 1), "flaps": len(flaps), "flap_length_cm": q([r["length_cm"] for r in flaps]),
           "flap_width_cm": q([r["width_cm"] for r in flaps]), "flap_fill": q([r["fill"] for r in flaps]),
           "flap_aspect_len_over_width": q([r["length_cm"] / max(r["width_cm"], 0.1) for r in flaps]),
           "rows": len(rows), "row_height_frac_top_down": [round(float((np.mean([r["y"] for r in rw]) - y0) / H), 2) for rw in rows],
           "flaps_per_row": [len(rw) for rw in rows], "stagger_ratio": q(stag),
           "lining_flaps": sum(1 for r in flaps if r["role"] == "lining"), "lining_shows_below_outer_cm": q(expo),
           "leather_thickness_cm": q(thick), "belt_lumps": sum(1 for k in M if k.get("role") == "belt"),
           "ornament_w_h_d_cm": [round(float(np.ptp(C[orn, i])) * 100, 1) for i in (0, 1, 2)] if len(orn) else None}
    json.dump(res, open(out + "_layers.json", "w"), indent=1); print(json.dumps(res))


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--mesh", required=True); ap.add_argument("--molds", required=True); ap.add_argument("--out", required=True)
    a = ap.parse_args(); main(a.mesh, a.molds, a.out)

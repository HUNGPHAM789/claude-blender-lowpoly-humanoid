"""Beard see-through test (Boss 25/10: «Râu còn vài chỗ lủng - thấy da nếu nhìn front, thấy white background nếu nhìn side»).

  python3 measure_beard_see_through.py --body male_base_lp.glb --hair male_hair_v3.glb [--out report.json] [--step 0.002]

Per view (front, left, right, 3/4 left, 3/4 right): an orthographic grid at `step` over the beard's own FILLED silhouette mask
(projected beard + moustache triangles rasterised, interior holes filled). Every ray inside the mask must hit beard geometry
before skin or empty space. Reports see-through rays per view, split into "skin first" and "nothing hit", with their mean
position. Exit 1 if any view has a see-through ray.
"""
import argparse
import json
import math
import os
import sys

import numpy as np
from PIL import Image, ImageDraw
from scipy.ndimage import binary_fill_holes, binary_erosion
from scipy.spatial import cKDTree
import trimesh

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from primal_body_frame import load_body  # noqa: E402
from analyze_outfit import ray_hits  # noqa: E402
from measure_primal_assets import parts_of  # noqa: E402

VIEWS = {"front": 0, "left": 90, "right": -90, "q_left": 35, "q_right": -35}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--body", required=True)
    ap.add_argument("--hair", required=True)
    ap.add_argument("--out")
    ap.add_argument("--step", type=float, default=0.002)
    a = ap.parse_args()
    body = load_body(a.body)
    hp = parts_of(a.hair)
    beard_names = [k for k in hp if k.startswith("beard") or k.startswith("moustache")]
    beard_tris = np.vstack([hp[k].triangles for k in beard_names])
    hair_tris = np.vstack([hp[k].triangles for k in hp if k not in beard_names])
    allt = np.vstack([beard_tris, hair_tris, body.triangles])
    nb = len(beard_tris)
    nh = nb + len(hair_tris)          # a ray stopped by scalp hair first is occluded, not a hole
    cs = [hp[k] for k in hp if k.startswith('beard_contact')]
    cpts = np.vstack([trimesh.sample.sample_surface(m, 20000, seed=1)[0] for m in cs])
    contact_kd = cKDTree(cpts)
    info = json.load(open(os.path.splitext(a.hair)[0] + "_parts.json"))
    top_row = np.array(info["beard"]["contact_rows"])[0]
    ax_ = np.array([top_row[:, 0].mean(), 0, 0.03])
    t_az = np.degrees(np.arctan2(top_row[:, 0] - ax_[0], top_row[:, 2] - ax_[2]))
    o_ = np.argsort(t_az)
    def above_edge(p):          # bare cheek ABOVE the beard's top line (by design), not a hole in the beard
        az = math.degrees(math.atan2(p[0] - ax_[0], p[2] - ax_[2]))
        return p[1] > np.interp(az, t_az[o_], top_row[o_, 1]) - 0.002
    rep = {}
    for view, yaw in VIEWS.items():
        r = math.radians(yaw)
        to_cam = np.array([math.sin(r), 0, math.cos(r)])
        right = np.array([math.cos(r), 0, -math.sin(r)])
        up = np.array([0, 1.0, 0])
        # silhouette of the camera-facing half only (the far half projects behind the head: occluded, not a hole)
        axis = np.array([beard_tris[..., 0].mean(), 0, beard_tris[..., 2].min() - 0.03])
        cen = beard_tris.mean(axis=1) - axis
        cen[:, 1] = 0
        facing = beard_tris[(cen @ to_cam) > 0]
        full_mask_tris = beard_tris                     # background holes are checked on the FULL beard silhouette
        pts = facing.reshape(-1, 3)
        u, v = pts @ right, pts[:, 1]
        u0, v0 = u.min() - 0.004, v.min() - 0.004
        nu = int((u.max() - u0) / a.step) + 3
        nv = int((v.max() - v0) / a.step) + 3
        img = Image.new("L", (nu, nv), 0)
        dr = ImageDraw.Draw(img)
        for t in facing:
            tu, tv = (t @ right - u0) / a.step, (t[:, 1] - v0) / a.step
            dr.polygon(list(zip(tu, tv)), fill=1)
        mask = binary_erosion(binary_fill_holes(np.array(img) > 0))   # 1-cell erosion: no edge-precision rays
        img2 = Image.new("L", (nu, nv), 0)
        dr2 = ImageDraw.Draw(img2)
        for t in full_mask_tris:
            dr2.polygon(list(zip((t @ right - u0) / a.step, (t[:, 1] - v0) / a.step)), fill=1)
        full = binary_erosion(binary_fill_holes(np.array(img2) > 0))
        j2, i2 = np.nonzero(full & ~mask)
        O2 = (u0 + (i2 + 0.5) * a.step)[:, None] * right + (v0 + (j2 + 0.5) * a.step)[:, None] * up + to_cam * 1.0
        bg_holes = sum(1 for h in ray_hits(allt, O2, np.tile(-to_cam, (len(O2), 1)), chunk=80) if not len(h)) if len(O2) else 0
        jj, ii = np.nonzero(mask)
        U = u0 + (ii + 0.5) * a.step
        Vv = v0 + (jj + 0.5) * a.step
        O = U[:, None] * right + Vv[:, None] * up + to_cam * 1.0
        D = np.tile(-to_cam, (len(O), 1))
        skin_first, empty, edge_skin = [], [], []
        for k, h in enumerate(ray_hits(allt, O, D, chunk=80)):
            if not len(h):
                empty.append(O[k])
            elif h[0] >= nh:
                t = allt[h[0]]
                nrm = np.cross(t[1] - t[0], t[2] - t[0])
                hit = O[k] + D[k] * ((nrm @ (t[0] - O[k])) / (nrm @ D[k]))
                d_skin = float((hit - O[k]) @ D[k])
                beard_behind = False
                for hb in h[1:]:                    # the nose/lip occluding beard that lies just behind it is not a hole
                    if hb < nb:
                        tb = allt[hb]
                        nb_ = np.cross(tb[1] - tb[0], tb[2] - tb[0])
                        if ((nb_ @ (tb[0] - O[k])) / (nb_ @ D[k])) - d_skin < 0.03:
                            beard_behind = True
                        break
                if above_edge(hit):
                    edge_skin.append(hit)
                elif contact_kd.query(hit)[0] < 0.012 and not beard_behind:   # skin UNDER the beard seen first = a hole (skin far from the beard = the
                    skin_first.append(hit)            # head occluding the far half, not a hole)
        rep[view] = {"rays": int(len(O)), "see_through": int(len(skin_first) + len(empty) + bg_holes), "skin_first": len(skin_first),
                     "empty": len(empty) + bg_holes, "background_through_full_silhouette": int(bg_holes), "bare_cheek_above_beard_line": len(edge_skin),
                     "sample_hits": [np.round(p, 3).tolist() for p in skin_first[::8]],
                     "where_skin_first_y": [round(float(min(p[1] for p in skin_first)), 3), round(float(max(p[1] for p in skin_first)), 3)] if skin_first else None}
    print(json.dumps(rep, indent=1))
    if a.out:
        with open(a.out, "w") as f:
            json.dump(rep, f, indent=1)
    sys.exit(1 if any(r["see_through"] for r in rep.values()) else 0)


if __name__ == "__main__":
    main()

"""Beard see-through test v2 = v1 + PITCHED views (Boss 25/10 «phía bên râu dưới bên phía trái bị một vệt hỏng nhìn thấy da»: the
level-only v1 views missed a streak between the lower lobes and the underside that shows from above and from 3/4).
Views: (yaw, pitch) — pitch < 0 = camera above looking down. Same rules otherwise, plus:
- BACK-FACE CULLING like the game/preview renderer (the GLB materials are doubleSided=False): a ray passes through any triangle it
  meets from behind. The v8 left-jaw streak was a run of beard faces wound inward — invisible in the render, "solid" to v1's rays.
- a skin-first region counts as a HOLE only when it is not connected (8-neighbour, in the view's ray grid) to the moustache or to
  the bare cheek/lip above the beard line: the mouth between moustache and strap is enclosed by the FILLED silhouette in the
  pitched views but it is lip, not a hole (a slit inside the strap — the v8 streak — is enclosed by beard and still counts);
- any ray that crosses a beard/moustache BACK face before any drawn face AND then shows skin or background counts as see-through
  on its own, whatever region it is in (a closed shell is always entered through a front face; the v8 moustache_R tip was wound
  inside-out); folds whose culled layer has beard drawn right behind it do not show and are not counted;
- the same enclosure rule for background ("empty") rays, and a region touching the outside of the silhouette is the beard's edge,
  not a hole (the underside contact faces projected under the chin in the steep views);
- the "beard just behind the skin" occluder exemption only applies to skin ≥ 8 mm from the beard contact sheet (a nose), not to
  skin the contact sheet has sunk into.

v1 doc:
Beard see-through test (Boss 25/10: «Râu còn vài chỗ lủng - thấy da nếu nhìn front, thấy white background nếu nhìn side»).

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
from scipy.ndimage import binary_fill_holes, binary_erosion, binary_dilation, label
from scipy.spatial import cKDTree
import trimesh

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from primal_body_frame import load_body  # noqa: E402
from analyze_outfit import ray_hits  # noqa: E402
from measure_primal_assets import parts_of  # noqa: E402

VIEWS = {"front": (0, 0), "left": (90, 0), "right": (-90, 0), "q_left": (35, 0), "q_right": (-35, 0),
         "front_down": (0, -20), "front_down_steep": (0, -35), "q_left_down": (35, -20), "q_right_down": (-35, -20),
         "q_left_up": (35, 15), "q_right_up": (-35, 15), "front_up": (0, 15),
         "side_left_down": (70, -20), "side_right_down": (-70, -20)}


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
    off, moustache_ids = 0, set()
    for k in beard_names:
        n_ = len(hp[k].triangles)
        if k.startswith("moustache"):
            moustache_ids.update(range(off, off + n_))
        off += n_
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
    tri_n = np.cross(allt[:, 1] - allt[:, 0], allt[:, 2] - allt[:, 0])
    def cull(hits, d):
        front = (tri_n @ d) < 0                 # faces the camera; back faces are not drawn (doubleSided=False)
        return [h[front[h]] for h in hits]
    def broken(hits, d):
        """rays that cross a beard/moustache BACK face before any drawn face: entering a closed shell always crosses a front face
        first, so this ray went in through a missing or inside-out face (= see-through in the single-sided render)."""
        front = (tri_n @ d) < 0
        out = 0
        for h in hits:
            crossed = False
            for t_ in h:
                if front[t_]:
                    if crossed and t_ >= nh:          # ...and what is drawn behind it is skin: see-through
                        out += 1
                    break
                if t_ < nb:
                    crossed = True
            else:
                if crossed:                            # ...and nothing is drawn behind it: background through the beard
                    out += 1
        return out
    rep = {}
    for view, (yaw, pitch) in VIEWS.items():
        r = math.radians(yaw)
        p = math.radians(pitch)
        to_cam = np.array([math.sin(r) * math.cos(p), -math.sin(p), math.cos(r) * math.cos(p)])
        right = np.array([math.cos(r), 0, -math.sin(r)])
        up = np.cross(to_cam, right)
        depth0 = float(allt.reshape(-1, 3).mean(axis=0) @ to_cam)   # v2: ray origins 1 m in FRONT of the model along the view axis
        # (v1 started them on the plane 1 m from the world origin — fine for level views, but with pitch the head at y ≈ 1.6 m sits
        # ~0.9 m along the view axis and parts of the beard were behind the ray origins: invisible to the test)
        # silhouette of the camera-facing half only (the far half projects behind the head: occluded, not a hole)
        axis = np.array([beard_tris[..., 0].mean(), 0, beard_tris[..., 2].min() - 0.03])
        cen = beard_tris.mean(axis=1) - axis
        cen[:, 1] = 0
        bn_ = np.cross(beard_tris[:, 1] - beard_tris[:, 0], beard_tris[:, 2] - beard_tris[:, 0])
        facing = beard_tris[((cen @ to_cam) > 0) & ((bn_ @ to_cam) > 0)]   # v2: only faces the renderer DRAWS from this camera (culled
                                                                           # undersides projected onto the neck below the beard in the down views)
        full_mask_tris = beard_tris                     # background holes are checked on the FULL beard silhouette
        pts = facing.reshape(-1, 3)
        u, v = pts @ right, pts @ up
        u0, v0 = u.min() - 0.004, v.min() - 0.004
        nu = int((u.max() - u0) / a.step) + 3
        nv = int((v.max() - v0) / a.step) + 3
        img = Image.new("L", (nu, nv), 0)
        dr = ImageDraw.Draw(img)
        for t in facing:
            tu, tv = (t @ right - u0) / a.step, (t @ up - v0) / a.step
            dr.polygon(list(zip(tu, tv)), fill=1)
        mask = binary_erosion(binary_fill_holes(np.array(img) > 0))   # 1-cell erosion: no edge-precision rays
        img2 = Image.new("L", (nu, nv), 0)
        dr2 = ImageDraw.Draw(img2)
        for t in full_mask_tris:
            dr2.polygon(list(zip((t @ right - u0) / a.step, (t @ up - v0) / a.step)), fill=1)
        full = binary_erosion(binary_fill_holes(np.array(img2) > 0))
        j2, i2 = np.nonzero(full & ~mask)
        O2 = (u0 + (i2 + 0.5) * a.step)[:, None] * right + (v0 + (j2 + 0.5) * a.step)[:, None] * up + to_cam * (1.0 + depth0)
        raw2 = ray_hits(allt, O2, np.tile(-to_cam, (len(O2), 1)), chunk=80) if len(O2) else []
        bg_k = [k_ for k_, h in enumerate(cull(raw2, -to_cam)) if not len(h)]
        n_broken = broken(raw2, -to_cam)
        jj, ii = np.nonzero(mask)
        U = u0 + (ii + 0.5) * a.step
        Vv = v0 + (jj + 0.5) * a.step
        O = U[:, None] * right + Vv[:, None] * up + to_cam * (1.0 + depth0)
        D = np.tile(-to_cam, (len(O), 1))
        skin_first, empty, edge_skin = [], [], []
        cls = np.zeros(mask.shape, int)          # 0 other, 1 beard/hair, 2 moustache, 3 hole candidate, 4 lip/cheek above the line
        cand_idx, empty_idx = {}, {}
        for k_ in bg_k:                                   # background through the FULL silhouette joins the same region analysis
            cls[j2[k_], i2[k_]] = 6
            empty_idx[(j2[k_], i2[k_])] = O2[k_]
        raw = ray_hits(allt, O, D, chunk=80)
        n_broken += broken(raw, -to_cam)
        for k, h in enumerate(cull(raw, -to_cam)):
            if len(h) and h[0] < nh:
                cls[jj[k], ii[k]] = 2 if h[0] in moustache_ids else 1
            if not len(h):
                cls[jj[k], ii[k]] = 6
                empty_idx[(jj[k], ii[k])] = O[k]
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
                d_contact = contact_kd.query(hit)[0]
                if beard_behind and d_contact < 0.008:
                    beard_behind = False      # v2: skin right on the contact sheet, beard sheet just behind it = the sheet sank into the
                                              # skin (the v8 left-jaw streak hid behind this exemption); only a far occluder (nose) is exempt
                if above_edge(hit):
                    edge_skin.append(hit)
                    cls[jj[k], ii[k]] = 4
                elif d_contact < 0.012 and not beard_behind:   # skin UNDER the beard seen first = a hole (skin far from the beard = the
                    cls[jj[k], ii[k]] = 3                       # head occluding the far half, not a hole)
                    cand_idx[(jj[k], ii[k])] = hit
                else:
                    cls[jj[k], ii[k]] = 5                       # other skin (far from the sheet): joins regions, never a hole itself
        if os.environ.get("SEE_THROUGH_GRID_DIR"):           # diagnosis: per-view class grid as an image
            pal = np.array([[255, 255, 255], [60, 40, 30], [150, 80, 200], [255, 0, 0], [255, 200, 120], [240, 170, 150], [0, 160, 255]], np.uint8)
            Image.fromarray(pal[cls[::-1]]).resize((cls.shape[1] * 4, cls.shape[0] * 4), Image.NEAREST).save(
                os.path.join(os.environ["SEE_THROUGH_GRID_DIR"], f"{view}.png"))
        # a HOLE = a bare-skin / background region ENCLOSED by beard in this view (its 8-neighbour ring is beard only). A region
        # that touches the moustache or the cheek/lip above the beard line is lip (mouth between moustache and strap); one that
        # touches the outside of the silhouette is the beard's own edge seen against skin/background (not a hole).
        inside = full.copy()
        bg_holes = 0
        lab, nlab = label(np.isin(cls, (3, 4, 5, 6)), structure=np.ones((3, 3)))
        lip_connected = edge_connected = 0
        for L_ in range(1, nlab + 1):
            reg = lab == L_
            ring = binary_dilation(reg, structure=np.ones((3, 3))) & ~reg
            pts_ = [cand_idx[(a_, b_)] for a_, b_ in zip(*np.nonzero(reg & (cls == 3)))]
            emp_ = [empty_idx[(a_, b_)] for a_, b_ in zip(*np.nonzero(reg & (cls == 6)))]
            if not pts_ and not emp_:
                continue
            if (cls[ring] == 2).any() or (cls[reg] == 4).any():
                lip_connected += len(pts_) + len(emp_)
                edge_skin += pts_
            elif (~inside[ring]).any() or reg[0].any() or reg[-1].any() or reg[:, 0].any() or reg[:, -1].any():
                edge_connected += len(pts_) + len(emp_)
            else:
                skin_first += pts_
                empty += emp_
                bg_holes += int(np.sum(reg & (cls == 6) & ~mask))
        rep[view] = {"yaw_pitch": [yaw, pitch], "rays": int(len(O)), "see_through": int(len(skin_first) + len(empty) + n_broken), "through_broken_surface": int(n_broken), "skin_first": len(skin_first),
                     "empty": len(empty), "background_through_full_silhouette": int(bg_holes), "background_uv": [[round(float(o_ @ right), 4), round(float(o_ @ up), 4)] for o_ in empty], "bare_cheek_above_beard_line": len(edge_skin), "of_which_lip_connected_regions": lip_connected, "skin_or_bg_at_silhouette_edge": edge_connected,
                     "sample_hits": [np.round(p, 3).tolist() for p in skin_first[::8]], "all_hits": [np.round(p, 4).tolist() for p in skin_first], "all_empty": [np.round(p, 4).tolist() for p in empty],
                     "skin_first_mean": np.round(np.mean(skin_first, axis=0), 3).tolist() if skin_first else None,
                     "where_skin_first_y": [round(float(min(p[1] for p in skin_first)), 3), round(float(max(p[1] for p in skin_first)), 3)] if skin_first else None}
    print(json.dumps(rep, indent=1))
    if a.out:
        with open(a.out, "w") as f:
            json.dump(rep, f, indent=1)
    sys.exit(1 if any(r["see_through"] for r in rep.values()) else 0)


if __name__ == "__main__":
    main()

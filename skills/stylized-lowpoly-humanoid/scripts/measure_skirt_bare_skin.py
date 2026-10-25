"""Bare skin seen INSIDE the skirt's outline (Boss 25/10: «váy bị lộ đùi bên phải»).

  python3 measure_skirt_bare_skin.py --body female_base_lp.glb --measurements female_measurements.json --outfit female_outfit_v2.glb [--step 0.003]

Orthographic rays from the front and both 3/4 cameras over the skirt's own FILLED silhouette (skirt + lining parts projected,
interior holes filled). A ray whose first hit is body skin (not an arm/hand face — skin hidden behind the hand is not seen) counts
as bare skin inside the skirt. Exit 1 if any view has one.
"""
import argparse
import json
import math
import os
import sys

import numpy as np
from PIL import Image, ImageDraw
from scipy.ndimage import binary_fill_holes, binary_erosion

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from primal_body_frame import load_body, load_json, arm_mask  # noqa: E402
from analyze_outfit import ray_hits  # noqa: E402
from measure_primal_assets import parts_of  # noqa: E402

VIEWS = {"front": 0, "q_left": 35, "q_right": -35}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--body", required=True)
    ap.add_argument("--measurements", required=True)
    ap.add_argument("--outfit", required=True)
    ap.add_argument("--step", type=float, default=0.003)
    ap.add_argument("--out")
    ap.add_argument("--side", choices=["both", "right", "left"], default="both", help="count only bare skin on that side of the body (hit point x vs midline)")
    ap.add_argument("--min-y", type=float, default=None, help="ignore rays below this height (default: the highest hem-tooth valley = top of the torn hem)")
    a = ap.parse_args()
    body = load_body(a.body)
    meas = load_json(a.measurements)
    op = parts_of(a.outfit)
    sk = np.vstack([m.triangles for k, m in op.items() if k.startswith("skirt")])
    other = np.vstack([m.triangles for k, m in op.items() if not k.startswith("skirt")])
    is_arm = arm_mask(body.triangles_center, meas["joints_gltf"])
    allt = np.vstack([sk, other, body.triangles])
    n_sk, n_out = len(sk), len(sk) + len(other)
    arm_idx = np.where(is_arm)[0] + n_out
    arm_set = set(arm_idx.tolist())
    rep = {}
    for view, yaw in VIEWS.items():
        r = math.radians(yaw)
        to_cam = np.array([math.sin(r), 0, math.cos(r)])
        right = np.array([math.cos(r), 0, -math.sin(r)])
        u, v = sk.reshape(-1, 3) @ right, sk.reshape(-1, 3)[:, 1]
        u0, v0 = u.min() - 0.006, v.min() - 0.006
        nu, nv = int((u.max() - u0) / a.step) + 3, int((v.max() - v0) / a.step) + 3
        img = Image.new("L", (nu, nv), 0)
        dr = ImageDraw.Draw(img)
        for t in sk:
            dr.polygon(list(zip((t @ right - u0) / a.step, (t[:, 1] - v0) / a.step)), fill=1)
        mask = binary_erosion(binary_fill_holes(np.array(img) > 0))
        if a.min_y is not None:
            vy = v0 + (np.arange(mask.shape[0]) + 0.5) * a.step
            mask[vy < a.min_y, :] = False
        jj, ii = np.nonzero(mask)
        O = (u0 + (ii + 0.5) * a.step)[:, None] * right + (v0 + (jj + 0.5) * a.step)[:, None] * np.array([0, 1.0, 0]) + to_cam * 1.0
        bare = []
        for k, h in enumerate(ray_hits(allt, O, np.tile(-to_cam, (len(O), 1)), chunk=80)):
            if len(h) and h[0] >= n_out and h[0] not in arm_set:
                t = allt[h[0]]
                nrm = np.cross(t[1] - t[0], t[2] - t[0])
                hp_ = O[k] + (-to_cam) * ((nrm @ (t[0] - O[k])) / (nrm @ -to_cam))
                if a.side == "right" and hp_[0] >= meas["face"]["midline_x"]:
                    continue
                if a.side == "left" and hp_[0] < meas["face"]["midline_x"]:
                    continue
                bare.append(O[k])
        bare = np.array(bare)
        if len(bare):
            hx = np.histogram(bare @ right, bins=12)
            hy = np.histogram(bare[:, 1], bins=8)
            print(view, "x", [(round(float(e), 2), int(c)) for e, c in zip(hx[1], hx[0]) if c], "y", [(round(float(e), 2), int(c)) for e, c in zip(hy[1], hy[0]) if c], file=sys.stderr)
        rep[view] = {"rays": int(len(O)), "bare_skin_rays": int(len(bare)),
                     "where": {"x_range": [round(float(bare[:, 0].min()), 3), round(float(bare[:, 0].max()), 3)],
                               "y_range": [round(float(bare[:, 1].min()), 3), round(float(bare[:, 1].max()), 3)]} if len(bare) else None}
    print(json.dumps(rep))
    if a.out:
        json.dump(rep, open(a.out, "w"), indent=1)
    sys.exit(1 if any(v["bare_skin_rays"] for v in rep.values()) else 0)


if __name__ == "__main__":
    main()

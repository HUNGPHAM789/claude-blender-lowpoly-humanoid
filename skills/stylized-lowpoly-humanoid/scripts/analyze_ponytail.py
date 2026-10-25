"""LEARN the ponytail grammar from a sample hair mesh (Boss 25/10/2026: «cách làm tóc đuôi cột … học bằng cách nào? scan số liệu?»).

  python3 analyze_ponytail.py --hair <hair_fit.glb> --body <body_fit.glb> --joints <joints.json> --clumps <name>_clumps.json --out <dir>/<name>
  ⇒ <name>_ponytail.json

Ponytail = hair hanging BEHIND (z < centre − 0.45·r_z) and BELOW the head centre. Its main axis comes from PCA; 16 slices along
the axis give the radius profile (mean distance to the axis): the tie = the narrowest slice in the upper third, the bulge = the
widest after it, the taper = how the radius falls to the tip. Also: length, droop (angle from vertical), attach height on the head,
and how many clump tips (from analyze_hair.py) end inside the tail = lock count.
"""
import argparse, json, math
import numpy as np
import trimesh
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def main(hair_p, body_p, joints_p, clumps_p, out, molds_p=None):
    hair = trimesh.load(hair_p, force="mesh"); body = trimesh.load(body_p, force="mesh"); J = json.load(open(joints_p))
    hv = body.vertices[body.vertices[:, 1] > J["dau"][2]]
    c = (hv.min(axis=0) + hv.max(axis=0)) / 2; r = (hv.max(axis=0) - hv.min(axis=0)) / 2
    V = hair.vertices
    tail = V[(V[:, 2] < c[2] - 0.45 * r[2]) & (V[:, 1] < c[1]) & (np.abs(V[:, 0] - c[0]) < 0.5 * r[0])]   # midline only: side locks hang at the sides
    if len(tail) < 50: print("no ponytail found"); json.dump({"ponytail": None}, open(out + "_ponytail.json", "w")); return
    m = tail.mean(axis=0); w, vec = np.linalg.eigh(np.cov((tail - m).T)); ax = vec[:, -1]
    if ax[1] > 0: ax = -ax                                           # point the axis down the tail (root → tip)
    t = (tail - m) @ ax; t0, t1 = t.min(), t.max(); L = t1 - t0
    prof = []
    for k in range(16):
        sel = (t >= t0 + k * L / 16) & (t < t0 + (k + 1) * L / 16)
        P = tail[sel]
        if len(P) < 5: prof.append(None); continue
        d = np.linalg.norm((P - m) - np.outer((P - m) @ ax, ax), axis=1); prof.append(round(float(np.mean(d)) * 100, 2))
    valid = [(i, p) for i, p in enumerate(prof) if p is not None]
    upper = [x for x in valid if x[0] < 6]; tie = min(upper, key=lambda x: x[1]) if upper else valid[0]
    after = [x for x in valid if x[0] > tie[0]]; bulge = max(after, key=lambda x: x[1]) if after else tie
    tipr = valid[-1]
    droop = math.degrees(math.acos(np.clip(-ax[1], -1, 1)))         # 0 = hangs straight down
    root = m + ax * t0
    locks = 0
    try:
        CL = json.load(open(clumps_p)); TP = np.array([k["tip"] for k in CL])
        tt = (TP - m) @ ax; dd = np.linalg.norm((TP - m) - np.outer(tt, ax), axis=1)
        locks = int(((tt > t0 + 0.5 * L) & (dd < 2.5 * max(x[1] for x in valid) / 100)).sum())
    except Exception: pass
    res = {"length_cm": round(float(L) * 100, 1), "droop_from_vertical_deg": round(droop, 1),
           "root_height_on_head": round(float((root[1] - (c[1] - r[1])) / (2 * r[1])), 2), "root_behind_cm": round(float((c[2] - root[2]) * 100), 1),
           "radius_profile_cm_root_to_tip": prof, "tie_slice": tie[0], "tie_radius_cm": tie[1], "bulge_slice": bulge[0], "bulge_radius_cm": bulge[1],
           "bulge_over_tie": round(bulge[1] / max(tie[1], 0.1), 2), "tip_radius_cm": tipr[1], "tip_over_bulge": round(tipr[1] / max(bulge[1], 0.1), 2),
           "lock_tips_in_lower_half": locks}
    # tie (from segment_mesh.py --kind hair): its size and where it sits on the tail
    if molds_p:
        Mo = json.load(open(molds_p))["molds"]; ties = [k for k in Mo if k.get("role") == "tie"]
        if ties:
            hm = trimesh.load(hair_p, force="mesh"); hm = trimesh.Trimesh(hm.vertices, hm.faces, process=True)
            from segment_mesh import segment_bumps
            tc = np.array(max(ties, key=lambda k: k["faces"])["centre"])
            near = hm.vertices[np.linalg.norm(hm.vertices - tc, axis=1) < 0.06]
            tt = (near - m) @ ax; rr = np.linalg.norm((near - m) - np.outer(tt, ax), axis=1)
            res["tie"] = {"centre_along_tail_frac": round(float(((tc - m) @ ax - t0) / L), 2), "band_width_cm": round(float(np.percentile(tt, 90) - np.percentile(tt, 10)) * 100, 1),
                          "radius_cm": round(float(np.median(rr)) * 100, 1), "faces": max(ties, key=lambda k: k["faces"])["faces"]}
        else: res["tie"] = None
    # gather: back/crown clumps should point toward the tie (angle between clump axis and base→root direction)
    try:
        CL = json.load(open(clumps_p)); g_ = []
        for k in CL:
            if k["region"] in ("back", "crown"):
                b_ = np.array(k["base"]); a_ = np.array(k["tip"]) - b_; dvec = root - b_
                if np.linalg.norm(a_) > 1e-6 and np.linalg.norm(dvec) > 1e-6: g_.append(math.degrees(math.acos(np.clip(a_ @ dvec / np.linalg.norm(a_) / np.linalg.norm(dvec), -1, 1))))
        res["gather_angle_to_root_deg_p10_50_90"] = [round(float(np.percentile(g_, p)), 1) for p in (10, 50, 90)] if g_ else None
        # lock tips around the tail axis: angular spread (0 = all on one side, 360 = all round)
        TP = np.array([k["tip"] for k in CL]); tt = (TP - m) @ ax; inl = TP[(tt > t0 + 0.5 * L)]
        if len(inl) >= 3:
            u_ = np.cross(ax, [1, 0, 0]); u_ /= np.linalg.norm(u_); w_ = np.cross(ax, u_)
            ang = np.sort(np.degrees(np.arctan2((inl - m) @ w_, (inl - m) @ u_)) % 360); gaps = np.diff(np.r_[ang, ang[0] + 360])
            res["lock_tip_angular_spread_deg"] = round(float(360 - gaps.max()), 1)
    except Exception as e: res["gather_error"] = str(e)
    json.dump(res, open(out + "_ponytail.json", "w"), indent=1); print(json.dumps(res, indent=1))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    for k_ in ("--hair", "--body", "--joints", "--clumps", "--out"): ap.add_argument(k_, required=True)
    ap.add_argument("--molds", help="<name>_molds.json from segment_mesh.py --kind hair (finds the tie)")
    a = ap.parse_args(); main(a.hair, a.body, a.joints, a.clumps, a.out, a.molds)

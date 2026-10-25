"""Skin showing through / beside the skirt AS A VIEWER SEES IT (Boss 25/10 ×2: «váy bị lộ đùi bên phải» · «đùi phải vẫn lòi ra ngoài váy»).

  python3 measure_lower_views.py --dressed <name>_dressed.glb --body … --joints … --anatomy … [--max-frac 0.005] [--json out.json]

see_report() casts rays OUT of the skin and skips skin within 3 cm of a hand (so a lining is not triggered under a resting hand) — the
right-thigh strip between the skirt's side edge and the hand sat inside that 3 cm and read 0 while Boss saw it in every front view.
Here horizontal parallel rays come FROM 8 cameras round the body (front, 3/4, sides, back) over the skirt band; a ray whose first hit is
torso/leg skin (not the arm/hand faces) between the waist and the hem-tooth zone of that side is visible skin. Exit 1 when any view shows
more than --max-frac of its skirt-band rays as skin.
"""
import argparse, json, os, sys
import numpy as np
import trimesh

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fit_engine as fe  # noqa: E402

VIEWS = {"front": 0, "q_front_L": 45, "side_L": 90, "q_back_L": 135, "back": 180, "q_back_R": -135, "side_R": -90, "q_front_R": -45}
STEP = 0.004              # m ray spacing


def measure(dressed, B):
    s = trimesh.load(dressed, force="scene"); g = s.geometry
    lower = [k for k in g if k.startswith("outfit_lower")]
    skirt = trimesh.util.concatenate([g[k] for k in lower]); body = g["body"]
    occl = [g[k] for k in g if k not in lower and k != "body"]
    parts = [("body", body)] + [("skirt", skirt)] + [("other", m) for m in occl]
    T = np.concatenate([m.triangles for _, m in parts]); tag = np.concatenate([[i] * len(m.faces) for i, (_, m) in enumerate(parts)])
    arm = np.zeros(len(T), bool); arm[:len(body.faces)] = B.arm_face if len(B.arm_face) == len(body.faces) else False
    ax = np.array([B.xm, np.median(body.vertices[:, 2])]); X = skirt.vertices
    aV = np.degrees(np.arctan2(X[:, 0] - ax[0], X[:, 2] - ax[1]))
    lo_sec = {sec: X[(aV >= sec) & (aV < sec + 45), 1].min() + fe.TOOTH_ZONE for sec in range(-180, 180, 45)}
    hi = B.waist_y - 0.01; y0 = min(lo_sec.values())
    out = {}
    for name, az in VIEWS.items():
        a = np.radians(az); d = -np.array([np.sin(a), 0, np.cos(a)]); r = np.array([np.cos(a), 0, -np.sin(a)])
        span = np.abs((body.vertices - [ax[0], 0, ax[1]]) @ r).max() + 0.02
        us, ys = np.meshgrid(np.arange(-span, span, STEP), np.arange(y0, hi, STEP))
        O = np.array([ax[0], 0, ax[1]]) + us.reshape(-1, 1) * r - d * 1.0; O[:, 1] = ys.ravel()
        hits = fe.ray_hits(T, O, np.tile(d, (len(O), 1)))
        n_band = skin = 0; pts = []
        for o, h in zip(O, hits):
            if not len(h): continue
            f = h[0]; t = T[f]; nn = np.cross(t[1] - t[0], t[2] - t[0]); dist = (nn @ (t[0] - o)) / (nn @ d); p = o + d * dist
            pa = np.degrees(np.arctan2(p[0] - ax[0], p[2] - ax[1])); sec = int(np.floor((pa + 180) / 45)) * 45 - 180
            if not (lo_sec[sec] < p[1] < hi): continue
            if tag[f] == 0 and arm[f]: continue                       # the arm / hand itself in front of the skirt is fine
            n_band += 1
            if tag[f] == 0: skin += 1; pts.append(p)
        P = np.array(pts) if pts else np.zeros((0, 3))
        out[name] = {"band_rays": n_band, "skin_rays": skin, "frac": round(skin / max(n_band, 1), 4),
                     "skin_centre": P.mean(0).round(3).tolist() if len(P) else None}
    return out


def main(a):
    B = fe.Body(a.body, a.joints, a.anatomy); r = measure(a.dressed, B)
    worst = max(r, key=lambda k: r[k]["frac"]); bad = [k for k in r if r[k]["frac"] > a.max_frac]
    for k, v in r.items(): print(f"  {k:10s} skin {v['skin_rays']:4d} / {v['band_rays']:5d} = {v['frac']*100:5.2f} %  at {v['skin_centre']}")
    if a.json: json.dump(r, open(a.json, "w"), indent=1)
    if bad: print(f"⛔ skin shows beside / through the skirt in {bad} (worst {worst} {r[worst]['frac']*100:.2f} %, ≤ {a.max_frac*100:.1f} %)")
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    for k in ("--dressed", "--body", "--joints", "--anatomy"): ap.add_argument(k, required=True)
    ap.add_argument("--max-frac", type=float, default=0.005); ap.add_argument("--json")
    main(ap.parse_args())

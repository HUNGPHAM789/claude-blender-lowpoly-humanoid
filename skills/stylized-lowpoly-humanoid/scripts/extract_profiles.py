"""Turn the measured silhouettes into smooth body profiles the builder can loft (Boss 25/10/2026).

Input  spec/measure/<sex>_silhouette.json (measure_reference.py).
Output spec/<sex>_profiles.json — every value is a fraction of figure height (feet 0 → hair top 1), sampled every 0.01:
  torso_hw[h]        half width of the torso run in the FRONT view (arms excluded = the run that holds the body centre)
  side_front[h]      front-most point in the SIDE view, relative to the body axis (axis = centre of the ankle in the side view)
  side_back[h]       back-most point (negative) in the SIDE view
  leg_hw[h]          half width of one leg (mean of left/right runs) in the FRONT view, below the crotch
  leg_front/back[h]  leg extents in the SIDE view below the crotch
  arm_hw[h]          half width of one arm (mean of the outer runs) in the FRONT view, below the armpit
Rows covered by the leather skirt (crotch … skirt top) are flagged in `skirt` so the builder fills them from the spec instead.
"""
import json, sys, os
import numpy as np

STEP = 0.01


def by_h(rows):
    d = {}
    for r in rows:
        k = round(round(r["h"] / STEP) * STEP, 2)
        d.setdefault(k, []).append(r["runs"])
    return d


def smooth(y, k=3):
    y = np.array(y, float); out = y.copy()
    for i in range(len(y)):
        w = y[max(0, i - k):i + k + 1]; w = w[~np.isnan(w)]
        out[i] = np.median(w) if len(w) else np.nan
    return out


def main(sex, mdir, out):
    S = json.load(open(os.path.join(mdir, f"{sex}_silhouette.json")))["views"]
    F, Sd = by_h(S["front"]["rows"]), by_h(S["side"]["rows"])
    hs = [round(i * STEP, 2) for i in range(0, 101)]
    # front body centre = midpoint between the two ankles (h 0.10–0.16)
    ank = [r for h in hs if 0.10 <= h <= 0.16 for r in F.get(h, [[]])[0] if len(F.get(h, [[]])[0]) == 2]
    fr = [F[h][0] for h in hs if 0.10 <= h <= 0.16 and h in F and len(F[h][0]) == 2]
    cx = float(np.mean([(r[0][0] + r[1][1]) / 2 for r in fr]))
    # side axis = centre of the ankle run in the side view
    sa = [Sd[h][0] for h in hs if 0.11 <= h <= 0.15 and h in Sd]
    ax = float(np.mean([max(r, key=lambda q: q[1] - q[0])[0] / 2 + max(r, key=lambda q: q[1] - q[0])[1] / 2 for r in sa]))
    P = {k: [] for k in ("torso_hw", "side_front", "side_back", "leg_hw", "leg_front", "leg_back", "arm_hw", "front_runs")}
    for h in hs:
        fr = F.get(h, [[]])[0]; sd = Sd.get(h, [[]])[0]
        body = [r for r in fr if r[0] <= cx <= r[1]]
        P["front_runs"].append(len(fr))
        P["torso_hw"].append((body[0][1] - body[0][0]) / 2 if body else np.nan)
        main_s = max(sd, key=lambda q: q[1] - q[0]) if sd else None
        P["side_front"].append(main_s[1] - ax if main_s else np.nan)
        P["side_back"].append(main_s[0] - ax if main_s else np.nan)
        legs = [r for r in fr if not (r[0] <= cx <= r[1])]
        two = len(fr) == 2 and not body
        P["leg_hw"].append(np.mean([(r[1] - r[0]) / 2 for r in fr]) if two else np.nan)
        P["leg_front"].append(main_s[1] - ax if (two and main_s) else np.nan)
        P["leg_back"].append(main_s[0] - ax if (two and main_s) else np.nan)
        arms = [r for r in fr if not (r[0] <= cx <= r[1])] if body and len(fr) == 3 else []
        P["arm_hw"].append(np.mean([(r[1] - r[0]) / 2 for r in arms]) if arms else np.nan)
    res = {"sex": sex, "step": STEP, "h": hs, "front_centre": cx, "side_axis": ax}
    for k, v in P.items():
        res[k] = [None if (isinstance(x, float) and np.isnan(x)) else round(float(x), 4) for x in (smooth(v) if k != "front_runs" else v)]
    json.dump(res, open(os.path.join(out, f"{sex}_profiles.json"), "w"), indent=0)
    print(sex, "centre", round(cx, 3), "axis", round(ax, 3))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], sys.argv[3])

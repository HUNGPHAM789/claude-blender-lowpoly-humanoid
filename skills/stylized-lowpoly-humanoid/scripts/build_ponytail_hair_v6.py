"""Female hair v6 = v5 with the hair behind the ears rounded and curving down (Boss 25/10: «Chỗ tóc sau lỗ tai đang bị vuông góc cho nó
tròn tự nhiên cong xuống»).

  python3 build_ponytail_hair_v6.py --v5 female_hair_v5.glb --body female_base_lp.glb --joints female_joints.json \
      --anatomy female_anatomy.json --out female_hair_v6.glb
  python3 build_ponytail_hair_v6.py --check <hair.glb>        # gate only

Measured on v5: every back mass ends on ONE flat line (y 1.511 at azimuth 100–180°) and the scalp cap hangs below it to 1.43 as a
flat-bottomed slab — from 3/4 back that reads as a square block with a right-angle corner behind the ear. Here the back mass TIPS go
down an arc (high behind the ear, lowest at the nape), each pulled onto the neck at SNUG off the skin so the hair wraps round and in;
the cap's back rows are lifted under that arc so it stays hidden. Fringe, front masses, ponytail and tie are byte-identical.
Gate (also run by --check): the back contour must DESCEND toward the nape — lowest tip at the nape ≥ DROP_MIN below the tips behind
the ears; a flat cut (v5: 0 mm) exits 1.
"""
import argparse, os, sys
import numpy as np
import trimesh

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "character-fitter", "scripts"))
import fit_engine as fe  # noqa: E402

BACK = 100.0              # deg from the face: behind the ear starts here
TOP_Y, NAPE_DROP = 1.53, 0.075    # arc: tips at TOP_Y behind the ear → TOP_Y − NAPE_DROP at the nape (1 − cos ease: stays up
                                  # behind the ear, then curves down to the nape — round, no corner)
SNUG = 0.006              # m off the skin for the moved tips (the masses' own standoff is 4–10 mm)
TIP_BAND = 0.006          # m above a mass's lowest point that counts as its tip
DROP_MIN = 0.03           # gate: nape tips at least this far below the behind-the-ear tips


def az_of(V, c):
    return np.degrees(np.arctan2(V[:, 0] - c[0], V[:, 2] - c[2]))


def arc_y(az):
    t = np.clip((np.abs(az) - BACK) / (180.0 - BACK), 0, 1)
    return TOP_Y - NAPE_DROP * (1 - np.cos(t * np.pi / 2))


def contour(sc):
    c = sc.geometry["hair_cap__movable"].vertices.mean(0); V = sc.geometry["hair_masses"].vertices; a = np.abs(az_of(V, c))
    ear = V[(a >= 120) & (a < 145), 1]; nape = V[a >= 160, 1]   # 100–120° has no back masses (ear gap)
    return float(ear.min()), float(nape.min())


def check(path):
    ear, nape = contour(trimesh.load(path, force="scene")); drop = ear - nape
    print(f"back hair contour: lowest tip behind the ears y {ear:.3f} · at the nape y {nape:.3f} · drop {drop * 1000:.0f} mm (≥ {DROP_MIN * 1000:.0f})")
    if drop < DROP_MIN: print("⛔ the back hair ends on a flat cut (square corner behind the ear)"); return 1
    return 0


def main(a):
    B = fe.Body(a.body, a.joints, a.anatomy); sc = trimesh.load(a.v5, force="scene"); c = sc.geometry["hair_cap__movable"].vertices.mean(0)
    out = trimesh.Scene()
    for name, g in sc.geometry.items():
        g = g.copy(); V = g.vertices.copy(); az = az_of(V, c); back = np.abs(az) >= BACK
        if name == "hair_masses":
            low = back & (V[:, 1] < V[back, 1].min() + TIP_BAND + 0.01)   # the clamped tips (all on the flat line)
            tgt = arc_y(az[low]); X = V[low].copy(); X[:, 1] = np.minimum(X[:, 1], tgt)
            for _ in range(4):                                              # onto the neck: round in, not a slab standing off
                d, n = B.signed(X); X -= n * (d - SNUG)[:, None]; X[:, 1] = np.minimum(V[low, 1], tgt)
            V[low] = X; print(f"  masses: {int(low.sum())} tip verts moved down the arc (max {np.abs(X - g.vertices[low]).max() * 1000:.0f} mm)")
        elif name == "hair_cap__movable":
            m = back & (V[:, 1] < arc_y(az) + 0.012)                     # cap hidden 12 mm above the new tips
            V[m, 1] = arc_y(az[m]) + 0.012
            d, n = B.signed(V[m]); V[m] -= n * np.minimum(d - 0.003, 0)[:, None]
            print(f"  cap: {int(m.sum())} back verts lifted under the arc")
        g.vertices = V; out.add_geometry(g, geom_name=name, node_name=name)
    out.export(a.out); print(f"hair v6 → {a.out}")
    sys.exit(check(a.out))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--check")
    for k in ("--v5", "--body", "--joints", "--anatomy", "--out"): ap.add_argument(k)
    a = ap.parse_args()
    sys.exit(check(a.check)) if a.check else main(a)

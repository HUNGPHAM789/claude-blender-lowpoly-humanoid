"""Skirt v(N+1) = v(N) with the outward BULGES on one side pulled back to the skirt's own line (Boss 25/10 ×2: «Sao váy nữ … lòi ra bên đùi
trái» · «Bên trái váy nữ V4 đang bị lồi ra một khúc kì kì»).

  python3 build_skirt_bulge_trim.py --skirt female_outfit_v4.glb --side L --out female_outfit_v5.glb
  python3 build_skirt_bulge_trim.py --skirt <skirt.glb> --check        # gate: exit 1 on any lining lump

The left half (from v1) wraps the lining + lower tier OUT round the resting left hand: at azimuth 100–120° the lining stands 0.257 m
off the axis where its neighbours sit at 0.20–0.21 (5 cm lump). A vertex is a bulge when its radius exceeds the median radius of the same
part's vertices in the ring around it (±25° azimuth, ±3 cm height, its own ±8° excluded) by more than BULGE; it is pulled radially back
to that median + KEEP. Only --side moves; the other side, the belt and the stone stay byte-identical. Exit 1 if a bulge remains
(measure_bulges() is the gate).
"""
import argparse, json, os, sys
import numpy as np
import trimesh

BULGE = 0.015             # m beyond the ring's median radius = a lump the eye reads as «lồi ra»
KEEP = 0.006              # m kept above the ring median: the torn layers still overlap / flare a little
PARTS = ("skirt_lining",)   # only the tan lining wraps the hand; pulling either torn tier in made their faces cross (tan patches on the dark tier, holes at the back)


def ring_median(V, i, ax):
    a = np.degrees(np.arctan2(V[:, 0] - ax[0], V[:, 2] - ax[1])); r = np.hypot(V[:, 0] - ax[0], V[:, 2] - ax[1])
    da = np.abs((a - a[i] + 180) % 360 - 180)
    m = (da < 25) & (da > 8) & (np.abs(V[:, 1] - V[i, 1]) < 0.03)
    return (np.median(r[m]) if m.sum() >= 3 else None), r[i]


def measure_bulges(sc, ax, side=None):
    out = {}
    for n in PARTS:
        if n not in sc.geometry: continue
        V = sc.geometry[n].vertices; idx = []
        for i in range(len(V)):
            if side == "L" and V[i, 0] < ax[0]: continue
            if side == "R" and V[i, 0] >= ax[0]: continue
            med, r = ring_median(V, i, ax)
            if med is not None and r - med > BULGE: idx.append((i, round((r - med) * 1000, 1)))
        out[n] = idx
    return out


def main(a):
    sc = trimesh.load(a.skirt, force="scene")
    allv = np.vstack([sc.geometry[n].vertices for n in PARTS if n in sc.geometry]); ax = np.array([0.0, float(np.median(allv[:, 2]))])
    if a.check:                                                         # gate only: any lining lump on either side ⇒ exit 1
        b = {k: v for k, v in measure_bulges(sc, ax, a.side).items() if v}
        print(f"skirt bulges ({a.side or 'both sides'}): {json.dumps(b)}")
        if b: print("⛔ the skirt bulges out (a lining lump stands > 15 mm off its ring)"); sys.exit(1)
        sys.exit(0)
    before = measure_bulges(sc, ax, a.side)
    print("bulges before:", {k: v for k, v in before.items() if v})
    out = trimesh.Scene(); moved = 0
    for n, g in sc.geometry.items():
        g = g.copy()
        if n in PARTS:
            V = g.vertices.copy()
            for _ in range(8):                                          # neighbours of a lump are lumpy too: settle in a few passes
                for i, _mm in measure_bulges(trimesh.Scene({n: trimesh.Trimesh(V, g.faces, process=False)}), ax, a.side).get(n, []):
                    med, r = ring_median(V, i, ax); d = np.array([V[i, 0] - ax[0], V[i, 2] - ax[1]]) / r
                    V[i, 0], V[i, 2] = ax[0] + d[0] * (med + KEEP), ax[1] + d[1] * (med + KEEP); moved += 1
            g.vertices = V
        out.add_geometry(g, geom_name=n, node_name=n)
    out.export(a.out)
    after = measure_bulges(trimesh.load(a.out, force="scene"), ax, a.side)
    print(f"skirt bulge trim ({a.side}): {moved} vertex pulls → {a.out}; bulges after: {{k: v for k, v in after.items() if v}}".replace("{k: v for k, v in after.items() if v}", json.dumps({k: v for k, v in after.items() if v})))
    if any(after.values()): print("⛔ the skirt still bulges"); sys.exit(1)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--skirt", required=True); ap.add_argument("--out"); ap.add_argument("--check", action="store_true")
    ap.add_argument("--side", choices=("L", "R"))
    main(ap.parse_args())

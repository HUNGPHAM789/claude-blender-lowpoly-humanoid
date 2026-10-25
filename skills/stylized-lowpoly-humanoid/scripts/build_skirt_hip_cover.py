"""Skirt v(N+1) = v(N) with ONE hip side pushed back over the skin (Boss 25/10 ×2: «váy bị lộ đùi bên phải» · «đùi phải vẫn lòi ra ngoài váy»).

  python3 build_skirt_hip_cover.py --skirt female_outfit_v3.glb --body female_base_lp.glb --joints female_joints.json \
      --anatomy female_anatomy.json --side R --out female_outfit_v4.glb

compose_skirt_sides pulled the hip sides in so the hands clear the skirt; on the female's right side it went 0–1.4 cm INSIDE the outer
hip at y 0.79–0.91 (torso −0.190…−0.157 vs skirt −0.190…−0.150), so the thigh showed between the skirt and the hand. Here the
character-fitter's poke_push moves the three corners of every skirt triangle that leaves skin visible out past the skin + CLEAR, and
only on --side (the other side, the hem teeth, the belt and the stone stay byte-identical). Exit 1 if skin still shows on that side.
"""
import argparse, os, sys
import numpy as np
import trimesh

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "character-fitter", "scripts"))
import fit_engine as fe  # noqa: E402

CLEAR = 0.006             # m: what the approved left side keeps off the hip (5–6 mm)
SKIRT = ("skirt_lining", "skirt_lower_tier", "skirt_upper_tier")


def main(a):
    B = fe.Body(a.body, a.joints, a.anatomy); sc = trimesh.load(a.skirt, force="scene")
    names = [n for n in SKIRT if n in sc.geometry]; geos = [sc.geometry[n] for n in names]
    off = np.cumsum([0] + [len(g.vertices) for g in geos])
    V = np.vstack([g.vertices for g in geos]); F = np.vstack([g.faces + o for g, o in zip(geos, off[:-1])])
    side = (V[:, 0] < B.xm) if a.side == "R" else (V[:, 0] >= B.xm)
    X, disp = fe.poke_push(V, F, B, "lower", CLEAR)
    X = np.where(side[:, None], X, V)                                   # the other side never moves
    P, N, miss = fe.see_through(X, F, B, "lower"); Pm = P[miss]
    on_side = (Pm[:, 0] < B.xm) if a.side == "R" else (Pm[:, 0] >= B.xm)
    moved = np.linalg.norm(X - V, axis=1)
    out = trimesh.Scene()
    for n, g in sc.geometry.items():
        g = g.copy()
        if n in names:
            i = names.index(n); g.vertices = X[off[i]:off[i + 1]]
        out.add_geometry(g, geom_name=n, node_name=n)
    out.export(a.out)
    print(f"skirt hip cover ({a.side}): {int((moved > 1e-5).sum())} verts moved, max {moved.max()*1000:.1f} mm · skin visible {miss.mean()*100:.2f} % "
          f"of the cover zone, {int(on_side.sum())} rays on side {a.side} → {a.out}")
    if on_side.sum() > 0.002 * len(P): print(f"⛔ skin still shows on side {a.side}"); sys.exit(1)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    for k in ("--skirt", "--body", "--joints", "--anatomy", "--out"): ap.add_argument(k, required=True)
    ap.add_argument("--side", choices=("L", "R"), required=True)
    main(ap.parse_args())

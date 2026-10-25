"""Female hair v5 = v4 with the ponytail + tie moved onto the head (Boss 25/10 ×2: «nữ tóc đuôi chưa sát với đầu»).

  python3 build_ponytail_hair_v5.py --v4 female_hair_v4.glb --body female_base_lp.glb --joints female_joints.json \
      --anatomy female_anatomy.json --out female_hair_v5.glb

Only `ponytail` + `tie_rope` move, together, as one rigid translation toward the scalp centre; cap, masses and fringe stay byte-identical.
The shift is the smallest one (1 mm steps) that makes measure_tail_attachment pass with the root sunk SINK into the masses; the build
exits 1 if the gate still fails.
"""
import argparse, os, subprocess, sys
import numpy as np
import trimesh

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from measure_tail_attachment import measure  # noqa: E402
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "character-fitter", "scripts"))
import fit_engine as fe  # noqa: E402

MOVING = ("ponytail", "tie_rope")
SINK = 0.003              # m the head-facing root goes into the hair masses, so no seam shows from the side
CLEAR = 0.0015            # m skin clearance for the root end cap that now sits against the skull (hidden under the masses)


def shifted(src, d, out, body=None):
    s = trimesh.load(src, force="scene"); sc = trimesh.Scene()
    for name, g in s.geometry.items():
        g = g.copy()
        if name in MOVING: g.vertices = g.vertices + d
        if name == "ponytail" and body is not None:                   # only the root band (under the tie / masses) may be pushed off the skull
            root = g.vertices[:, 1] > g.vertices[:, 1].max() - 0.03
            g.vertices, disp = fe.fading_push(g.vertices, body, CLEAR, 0.01, movable=root)
            print(f"  root end cap pushed off the skull: {int((np.linalg.norm(disp, axis=1) > 1e-5).sum())} verts, max {np.linalg.norm(disp, axis=1).max()*1000:.1f} mm")
        sc.add_geometry(g, geom_name=name, node_name=name)
    sc.export(out)


def main(a):
    s = trimesh.load(a.v4, force="scene"); g = s.geometry
    centre = g["hair_cap__movable"].vertices.mean(0); tail = g["ponytail"].vertices
    root = tail[tail[:, 1] > tail[:, 1].max() - 0.03].mean(0)
    u = centre - root; u[1] = 0.0; u /= np.linalg.norm(u)            # horizontal, toward the skull: the tail keeps its height and hang
    tmp = a.out + ".tmp.glb"
    for mm in range(0, 121):
        shifted(a.v4, u * mm / 1000, tmp); r = measure(tmp)
        if r["root_gap_p25_mm"] <= 0.0 and r.get("tie_gap_p25_mm", 0) <= 3.0:   # head-facing quarter sunk in, tie touching
            break
    body = fe.Body(a.body, a.joints, a.anatomy)
    mm = min(mm + int(SINK * 1000), 120); shifted(a.v4, u * mm / 1000, a.out, body); os.remove(tmp)
    print(f"hair v5: ponytail + tie moved {mm} mm toward the head along {np.round(u, 3).tolist()} → {a.out}")
    rc = subprocess.call([sys.executable, os.path.join(os.path.dirname(os.path.abspath(__file__)), "measure_tail_attachment.py"), "--hair", a.out])
    sys.exit(rc)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    for k in ("--v4", "--out", "--body", "--joints", "--anatomy"): ap.add_argument(k, required=True)
    main(ap.parse_args())

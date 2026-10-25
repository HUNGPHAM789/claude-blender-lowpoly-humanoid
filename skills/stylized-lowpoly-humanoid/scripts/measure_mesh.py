"""Measure a built body directly on the 3D mesh (Boss 25/10/2026: «phân tích theo actual 3D model thì tốt và chi tiết hơn»).

  python3 measure_mesh.py --sex female --glb <body.glb> [--json out.json]   ⇒ table + gate (exit 1 on a failed check)

Cross-sections at the spec landmarks (figure units × scale_m): width (X), depth (Y), front-most point. Checks:
  height        = scale_m ± 2 %
  bust (female) = front at bust_peak − front at underbust ≥ 0.6 × the sheet's protrusion (spec bust.*)
  tris          ≤ budget (default 3500)
"""
import argparse, json, os, sys
import numpy as np
import trimesh

HERE = os.path.dirname(os.path.abspath(__file__)); SPEC = os.path.join(HERE, "..", "spec")
sys.path.insert(0, HERE)
from build_body import load_zup


def section(mesh, z):
    """contour points of the horizontal cut at height z (exact on a low-poly mesh, unlike a vertex band)."""
    p = mesh.section(plane_origin=[0, 0, z], plane_normal=[0, 0, 1])
    if p is None: return None
    pts = np.vstack([e for e in p.discrete]) if hasattr(p, "discrete") else p.vertices
    return pts


def main(sex, glb, out, budget):
    S = json.load(open(os.path.join(SPEC, f"{sex}_spec.json"))); k = S["scale_m"]
    m = load_zup(glb); V = m.vertices
    H = V[:, 2].max() - V[:, 2].min(); rows = {}; fails = []
    # torso-only section: drop arms by keeping points within the inner 60 % of the widest span at that height
    for name, h in sorted(S.get("landmarks", {}).items(), key=lambda kv: -kv[1]):
        s = section(m, h * k)
        if s is None: continue
        x = s[:, 0]; half = max(abs(x.min()), abs(x.max()))
        core = s[np.abs(x) < 0.6 * half] if name not in ("knee", "calf_peak", "ankle") else s   # body axis is x = 0 (ankle centre)
        if len(core) < 3: core = s
        rows[name] = {"h_m": round(h * k, 3), "width_cm": round((s[:, 0].max() - s[:, 0].min()) * 100, 1),
                      "depth_cm": round((core[:, 1].max() - core[:, 1].min()) * 100, 1), "front_cm": round(core[:, 1].max() * 100, 1)}
    print(f"{'landmark':12s} {'h m':>6s} {'width cm':>9s} {'depth cm':>9s} {'front cm':>9s}")
    for n, r in rows.items(): print(f"{n:12s} {r['h_m']:6.3f} {r['width_cm']:9.1f} {r['depth_cm']:9.1f} {r['front_cm']:9.1f}")
    res = {"height_m": round(float(H), 3), "tris": int(len(m.faces)), "sections": rows}
    if abs(H - k) > 0.02 * k: fails.append(f"height {H:.3f} m ≠ {k:.3f} m ± 2 %")
    if len(m.faces) > budget: fails.append(f"tris {len(m.faces)} > budget {budget}")
    if sex == "female" and "bust" in S and "bust_peak" in rows and "underbust" in rows:
        want = (S["bust"]["side_front_peak"] - S["bust"]["side_front_underbust"]) * k * 100
        got = rows["bust_peak"]["front_cm"] - rows["underbust"]["front_cm"]; res["bust_protrusion_cm"] = round(got, 1)
        print(f"bust protrusion {got:.1f} cm (sheet {want:.1f} cm, need ≥ {0.6 * want:.1f})")
        if got < 0.6 * want: fails.append(f"bust protrusion {got:.1f} cm < {0.6 * want:.1f} cm")
    print(f"height {H:.3f} m · tris {len(m.faces)}")
    if out: json.dump(res, open(out, "w"), indent=1)
    for f in fails: print("⛔", f)
    if fails: sys.exit(1)
    print("✅ mesh measurements pass")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--sex", required=True); ap.add_argument("--glb", required=True)
    ap.add_argument("--json"); ap.add_argument("--budget", type=int, default=3500)
    a = ap.parse_args(); main(a.sex, a.glb, a.json, a.budget)

"""Compose primal male hair v6 from approved parts (Boss 25/10/2026: «ý tôi là tóc V2 + chỏm V4 nhưng V4 ngắn lại gấp 70%»).

  python3 compose_hair_v6.py --v2 male_hair_v2.glb --v4 male_hair_v4.glb --whorl-json male_hair_v4_parts.json --scale 0.7 --out male_hair_v6.glb

- scalp: v2 `hair_cap__movable` + `hair_masses` (the 30 broad masses), unchanged
- crown chunks: v4 `hair_chunks` scaled about the whorl (0.7 = «ngắn lại 70%»), so roots stay at the whorl and tips come in
- beard: the sealed v4 `beard_contact__movable` + `beard_outer` + `moustache` (v2's beard had see-through holes)
Every part keeps its own name + material (the fitter writes fitted positions back per part).
"""
import argparse, json
import numpy as np
import trimesh


def main(a):
    v2 = trimesh.load(a.v2, force="scene"); v4 = trimesh.load(a.v4, force="scene")
    w = json.load(open(a.whorl_json))["whorl"]; c = np.array(w["point"] if isinstance(w, dict) else w, float)
    if not np.isfinite(c).all() or c.shape != (3,): raise SystemExit(f"⛔ whorl point unreadable: {w}")
    sc = trimesh.Scene()
    for name in ("hair_cap__movable", "hair_masses"):
        sc.add_geometry(v2.geometry[name].copy(), geom_name=name, node_name=name)
    ch = v4.geometry["hair_chunks"].copy(); ch.vertices = c + (ch.vertices - c) * a.scale
    if not np.isfinite(ch.vertices).all(): raise SystemExit("⛔ scaled chunks have non-finite vertices")
    sc.add_geometry(ch, geom_name="hair_chunks", node_name="hair_chunks")
    for name in ("beard_contact__movable", "beard_outer", "moustache"):
        sc.add_geometry(v4.geometry[name].copy(), geom_name=name, node_name=name)
    sc.export(a.out)
    tris = {k: len(g.faces) for k, g in sc.geometry.items()}
    print(f"hair v6: {sum(tris.values())} tris {tris} · chunks ×{a.scale} about the whorl {np.round(c, 4).tolist()} → {a.out}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    for k in ("--v2", "--v4", "--whorl-json", "--out"): ap.add_argument(k, required=True)
    ap.add_argument("--scale", type=float, default=0.7)
    main(ap.parse_args())

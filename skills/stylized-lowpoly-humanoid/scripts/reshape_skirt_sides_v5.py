"""v5 skirt = the v1 torn layered skirt with ONLY its hip sides pulled in so the rest-pose hands clear it
(Boss 25/10: «quần chỉ reshape bên hông cho xích vào thôi - của quần V1 bạn làm»).

  python3 reshape_skirt_sides_v5.py --body male_base_lp.glb --measurements male_measurements.json \
      --skirt male_outfit_v1.glb --out male_outfit_v5.glb [--waist-scale 0.62]

Nothing is regenerated: every v1 vertex keeps its height and azimuth (tiers, teeth, irregular hem, lining, belt, stone unchanged);
only its distance from the trunk is scaled:
  r' = r_trunk(y, a) + (r − r_trunk) · f(a, y)
  f = 1 − side_w(a) · (1 − SIDE_SCALE)            side_w = 1 inside the measured hand wedge, smooth to 0 within BLEND_DEG outside it
      · (waist band only) WAIST_SCALE where the band reads oversize
so layer order is kept (proportional). The belt moves rigidly with the skirt surface under it (its rope section is not squashed).
Then vertices / face samples still within HAND_CLEAR of the hand are pulled further in (never into the skin); faces that cannot clear
are removed — the only opening allowed, right at the hand-contact patch. Finally every part is sanitised (no edge < 0.5 mm).
"""
import argparse
import json
import math
import os
import sys

import numpy as np
from scipy.spatial import cKDTree

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from primal_body_frame import export_roles, load_body, load_json  # noqa: E402
from build_torn_outfit import BodyProfile  # noqa: E402
from build_hide_skirt_v4 import sanitize  # noqa: E402
from measure_primal_assets import parts_of  # noqa: E402

HAND_CLEAR = float(os.environ.get("HAND_CLEAR_M", "0.0105"))   # 0.5 mm margin over the 10 mm requirement (random surface samples landed at 9.5 mm)
SIDE_SCALE = 0.30
BLEND_DEG = 22.0
ROLE_OF = {"skirt_lining": "leather_tan", "skirt_lower_tier": "leather_dark", "skirt_upper_tier": "leather_dark",
           "rope_belt": "rope_bone", "ornament": "ornament_stone"}


def smooth(x):
    x = np.clip(x, 0, 1)
    return x * x * (3 - 2 * x)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--body", required=True)
    ap.add_argument("--measurements", required=True)
    ap.add_argument("--skirt", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--waist-scale", type=float, default=0.62)
    ap.add_argument("--lining-valley-drop", type=float, default=0.06, help="m; lining tooth valleys only (hidden behind the dark teeth)")
    a = ap.parse_args()
    meas = load_json(a.measurements)
    body = load_body(a.body)
    bp = BodyProfile(body, meas)
    arm_kd0 = cKDTree(bp.arm_P)
    far = arm_kd0.query(bp.P)[0] > 0.02
    hand_kd = cKDTree(np.vstack([bp.arm_P, bp.P[~far]]))     # fingertips resting on the thigh count as hand
    if os.environ.get("HAND_FROM_FITTER", "0") == "1":      # use the character fitter's own arm/hand faces (read-only import)
        sys.path.insert(0, os.path.expanduser("~/projects/lpm-faceless-humanoid/skills/character-fitter/scripts"))
        from fit_engine import Body as _FB
        jp = a.measurements.replace("_measurements.json", "_joints.json")
        an = a.measurements.replace("_measurements.json", "_anatomy.json")
        fb = _FB(a.body, jp, an)
        fb._torso_mesh()
        hand_kd = cKDTree(fb.P[fb.arm_face[fb.Pfi]])
    if os.environ.get('TRUNK_DROP_NEAR_ARM', '1') == '1':   # male v5 used 1; the female hands sit closer: radius from the FULL trunk (0)
        bp.P, bp.N = bp.P[far], bp.N[far]
        bp._cache, bp._rcache = {}, {}
    J = meas["joints_gltf"]
    hand_top = max(J["co_tay_L"][1], J["co_tay_R"][1]) + 0.06
    arm_az = np.degrees(np.arctan2(bp.arm_P[:, 0] - bp.cx, bp.arm_P[:, 2] - bp.cz))
    low = bp.arm_P[:, 1] < hand_top
    wL = (float(arm_az[low & (arm_az > 0)].min()), float(arm_az[low & (arm_az > 0)].max()))
    wR = (float(arm_az[low & (arm_az < 0)].min()), float(arm_az[low & (arm_az < 0)].max()))
    waist_lo, waist_hi = max(J["chau"][1] + 0.06, meas["torso"]["waist_y"] - float(os.environ.get("WAIST_BAND_DEPTH", "9"))), max(J["bung"][1] + 0.03, meas["torso"]["waist_y"] + float(os.environ.get("WAIST_TOP_EXTRA", "-1")))   # female: band runs up to the skirt top (WAIST_TOP_EXTRA=0.05)

    def side_w(az):
        out = np.zeros_like(az)
        for lo_, hi_ in (wL, wR):
            d = np.maximum(lo_ - az, az - hi_)          # < 0 inside the wedge
            out = np.maximum(out, 1 - smooth(d / BLEND_DEG))
        return out

    def f_of(V):
        az = np.degrees(np.arctan2(V[:, 0] - bp.cx, V[:, 2] - bp.cz))
        f = 1 - side_w(az) * (1 - SIDE_SCALE)
        band = smooth((V[:, 1] - (waist_lo - 0.04)) / 0.04) * (1 - smooth((V[:, 1] - waist_hi - 0.04) / 0.04))
        f = f * (1 - band * (1 - a.waist_scale))
        return f

    def trunk_r(V):
        r = bp.radius_at(V, band=0.008, half_deg=4.0)
        if os.environ.get("MIRROR_TRUNK_RIGHT", "0") == "1":
            # female round 3: the right hand rests ON the hip, so the hip skin there is classified as hand and the trunk radius
            # collapses (the v1 skirt sank inside the right hip → bare thigh). Read the right hip from the mirrored LEFT hip.
            az = np.degrees(np.arctan2(V[:, 0] - bp.cx, V[:, 2] - bp.cz))
            right = (az < wR[1] + BLEND_DEG) & (az > wR[0] - BLEND_DEG)
            if right.any():
                Vm = V[right].copy()
                Vm[:, 0] = 2 * bp.cx - Vm[:, 0]
                r[right] = np.maximum(r[right], bp.radius_at(Vm, band=0.008, half_deg=4.0))
        return r

    def remap(V):
        r = np.hypot(V[:, 0] - bp.cx, V[:, 2] - bp.cz)
        rt = trunk_r(V)
        off = np.maximum(r - rt, 0)
        rn = rt + np.maximum(off * f_of(V), np.minimum(off, float(os.environ.get("MIN_OFF", "0.006"))))
        rn = np.where(rt < 0.05, r, rn)     # no trunk sample in the window (between the legs): leave the vertex where it is   # never closer than 6 mm (chords between verts must not sink into the hip)
        dirv = (V - np.array([bp.cx, 0, bp.cz]))
        dirv[:, 1] = 0
        dirv /= np.linalg.norm(dirv, axis=1, keepdims=True)
        return V + dirv * (rn - r)[:, None], dirv

    src = parts_of(a.skirt)
    lin = src["skirt_lining"]
    LV = lin.vertices.copy()
    low_band = LV[:, 1] < LV[:, 1].min() + 0.12
    if a.lining_valley_drop > 0:
        # the lowest row = teeth; valleys are its HIGHER vertices: pull those down (tips untouched)
        ymin = LV[:, 1].min()
        tooth = low_band & (LV[:, 1] > ymin + 0.06)          # valleys only (tips sit within ~4.5 cm of the lowest tip)
        LV[tooth, 1] = np.maximum(LV[tooth, 1] - a.lining_valley_drop, ymin + 0.055)   # never below the lowest tip + 5.5 cm
        lin.vertices = LV
    new = {}
    upper_old = src["skirt_upper_tier"].vertices
    for name in ("skirt_lining", "skirt_lower_tier", "skirt_upper_tier"):
        m = src[name]
        V, _ = remap(m.vertices.copy())
        new[name] = (V, m.faces.copy())
    # belt / stone: move rigidly with the upper-tier surface under each vertex
    up_new = new["skirt_upper_tier"][0]
    key = lambda V: np.c_[np.degrees(np.arctan2(V[:, 0] - bp.cx, V[:, 2] - bp.cz)) * 0.004, V[:, 1]]
    kd_up = cKDTree(key(upper_old))
    for name in ("rope_belt", "ornament"):
        m = src[name]
        _, i = kd_up.query(key(m.vertices))
        new[name] = (m.vertices + (up_new[i] - upper_old[i]), m.faces.copy())
    # hand pass: pull what is still within HAND_CLEAR of the hand further in, never into the skin; remove faces that cannot clear
    from build_hair_masses_v2 import BARY
    q = bp.q
    removed = {}
    for name in ("skirt_lining", "skirt_lower_tier", "skirt_upper_tier", "rope_belt"):
        V, F = new[name]
        for it in range(int(os.environ.get('HAND_REFINE', '1')) if name in os.environ.get('REFINE_PARTS', 'skirt_lower_tier').split(',') else 0):        # refine next to the hand so a removed patch stays the size of the hand contact
            smp = np.einsum("bk,fkj->fbj", BARY, V[F])
            dmin = hand_kd.query(smp.reshape(-1, 3))[0].reshape(len(F), len(BARY)).min(axis=1)
            split = dmin < float(os.environ.get('HAND_SPLIT_M', '0.009'))
            Vl = list(V)
            nf = [f for f, sp in zip(F, split) if not sp]
            for f in F[split]:
                a_, b_, c_ = f
                m = []
                for u, v in ((a_, b_), (b_, c_), (c_, a_)):
                    Vl.append(0.5 * (Vl[u] + Vl[v]))
                    m.append(len(Vl) - 1)
                nf += [[a_, m[0], m[2]], [m[0], b_, m[1]], [m[2], m[1], c_], [m[0], m[1], m[2]]]
            V, F = np.array(Vl), np.array(nf)
        rad = V - np.array([bp.cx, 0, bp.cz])
        rad[:, 1] = 0
        rad /= np.linalg.norm(rad, axis=1, keepdims=True)
        for _ in range(14):
            pts = np.vstack([V, np.einsum("bk,fkj->fbj", BARY, V[F]).reshape(-1, 3)])
            d = hand_kd.query(pts)[0]
            need = np.maximum(HAND_CLEAR - d, 0)
            pull = need[:len(V)].copy()
            for f, ls in zip(F, need[len(V):].reshape(len(F), len(BARY))):
                for b, l in zip(BARY, ls):
                    if l > 0:
                        pull[f] = np.maximum(pull[f], l * np.clip(b * 1.6, 0, 1))
            if pull.max() < 0.0003:
                break
            Vn = V - rad * np.minimum(pull, 0.004)[:, None]
            ok = q.clearance(Vn) >= 0.003
            V = np.where(ok[:, None], Vn, V)
        if os.environ.get("OVER_HAND", "0") == "1" and name != "rope_belt":
            drape_total = np.zeros(len(V))
            # where the fingers rest ON the thigh nothing can pass between: let the leather drape OVER the fingertips instead,
            # pushed radially OUT until it clears the hand (female round 2: «váy bị lộ đùi bên phải»)
            for _ in range(20):
                smp = np.einsum("bk,fkj->fbj", BARY, V[F])
                flat = smp.reshape(-1, 3)
                dd = hand_kd.query(flat)[0]
                dmin = dd.reshape(len(F), len(BARY)).min(axis=1)
                near = dd < 0.03
                ins = np.zeros(len(flat), bool)
                if near.any():
                    ins[near] = q.inside(flat[near])           # a point deep INSIDE the hand is far from its surface: test it
                    ins[near] |= q.signed_distance(flat[near])[0] < 0.002   # the fitter's own rule (nearest skin normal) must agree
                bad = (dmin < HAND_CLEAR) | ins.reshape(len(F), len(BARY)).any(axis=1)
                if not bad.any():
                    break
                push = np.zeros(len(V))
                for f in F[bad]:
                    push[f] = 0.004
                push = np.minimum(push, np.maximum(0, float(os.environ.get("DRAPE_MAX", "0.08")) - drape_total))
                drape_total += push
                if push.max() <= 0:
                    break
                V = V + rad * push[:, None]
        smp = np.einsum("bk,fkj->fbj", BARY, V[F])
        dmin = hand_kd.query(smp.reshape(-1, 3))[0].reshape(len(F), len(BARY)).min(axis=1)
        # last refinement: split ONLY the faces about to be removed, so just the sub-faces at the contact patch go
        bad = dmin < HAND_CLEAR
        if bad.any() and name in os.environ.get("FINAL_SPLIT_PARTS", "skirt_lower_tier").split(","):
            Vl = list(V)
            nf = [f for f, b_ in zip(F, bad) if not b_]
            for f in F[bad]:
                a_, b2, c_ = f
                m = []
                for u, v in ((a_, b2), (b2, c_), (c_, a_)):
                    Vl.append(0.5 * (Vl[u] + Vl[v]))
                    m.append(len(Vl) - 1)
                nf += [[a_, m[0], m[2]], [m[0], b2, m[1]], [m[2], m[1], c_], [m[0], m[1], m[2]]]
            V, F = np.array(Vl), np.array(nf)
            # the new mid-edge points lie on chords: push any that sit in the skin back out (radially)
            radn = V - np.array([bp.cx, 0, bp.cz])
            radn[:, 1] = 0
            radn /= np.linalg.norm(radn, axis=1, keepdims=True)
            for _ in range(8):
                c_ = q.clearance(V)
                lack = np.maximum(0.003 - c_, 0)
                if lack.max() < 0.0002:
                    break
                V = V + radn * np.minimum(lack + 0.0005, 0.01)[:, None] * (lack > 0)[:, None]
            smp = np.einsum("bk,fkj->fbj", BARY, V[F])
            dmin = hand_kd.query(smp.reshape(-1, 3))[0].reshape(len(F), len(BARY)).min(axis=1)
        keep = dmin >= HAND_CLEAR
        flat = np.einsum("bk,fkj->fbj", BARY, V[F]).reshape(-1, 3)
        nearh = hand_kd.query(flat)[0] < 0.03
        if nearh.any():                            # a face whose samples sit INSIDE the hand goes too (distance alone missed them)
            insd = np.zeros(len(flat), bool)
            insd[nearh] = q.inside(flat[nearh])
            keep &= ~insd.reshape(len(F), len(BARY)).any(axis=1)
        if name == "rope_belt":                # the belt is only pulled in (female forearm passes the waist), never cut
            keep[:] = True
        removed[name] = int((~keep).sum())
        new[name] = (V, F[keep])
    # face clearance: after proportional squeezing, a face between two vertices can sink under the hip skin (a bite of bare skin
    # in front view, female v2 measured 25/10) — push such faces back out radially (never toward the hand)
    if os.environ.get("FACE_CLEAR", "1") == "1":
        for name in ("skirt_lining", "skirt_lower_tier", "skirt_upper_tier"):
            V, F = new[name]
            radn = V - np.array([bp.cx, 0, bp.cz])
            radn[:, 1] = 0
            radn /= np.linalg.norm(radn, axis=1, keepdims=True)
            for _ in range(10):
                smp = np.einsum("bk,fkj->fbj", BARY, V[F]).reshape(-1, 3)
                c = q.clearance(smp).reshape(len(F), len(BARY))
                dh = hand_kd.query(smp)[0].reshape(len(F), len(BARY)).min(axis=1)
                lack = (0.003 - c).max(axis=1)
                bad = (lack > 0.0002) & (dh > HAND_CLEAR + 0.005)
                if not bad.any():
                    break
                push = np.zeros(len(V))
                for f, l in zip(F[bad], lack[bad]):
                    push[f] = np.maximum(push[f], min(l + 0.0005, 0.008))
                V = V + radn * push[:, None]
            new[name] = (V, F)
    # last guard, the fitter's own rest rule: no vertex with a negative nearest-normal distance (2 lower-tier verts beside the hand
    # read −9 mm there while ray parity said outside)
    for name in ("skirt_lining", "skirt_lower_tier", "skirt_upper_tier"):
        V, F = new[name]
        radn = V - np.array([bp.cx, 0, bp.cz])
        radn[:, 1] = 0
        radn /= np.linalg.norm(radn, axis=1, keepdims=True)
        for _ in range(12):
            sd = q.signed_distance(V)[0]
            bad = (sd < 0.002) & (hand_kd.query(V)[0] > 0.03)    # next to the hand the drape pass owns the vertex (no push INTO the hand)
            if not bad.any():
                break
            V = V + radn * (0.003 * bad)[:, None]
        new[name] = (V, F)
    parts = []
    min_edge = {}
    for name in ("skirt_lining", "skirt_lower_tier", "skirt_upper_tier", "rope_belt", "ornament"):
        V, F = sanitize(*new[name], tol=float(os.environ.get("SANITIZE_TOL", "0.0005")))   # female: 4 mm (a 1.2 mm edge tore the rig test)
        e = np.linalg.norm(V[F[:, [1, 2, 0]]] - V[F], axis=2)
        min_edge[name] = round(float(e.min() * 1000), 2)
        parts.append((name, ROLE_OF[name], V, F))
    export_roles(parts, a.out)
    info = {"out": a.out, "source": a.skirt, "side_scale": SIDE_SCALE, "waist_scale": a.waist_scale, "blend_deg": BLEND_DEG,
            "hand_wedge_deg": {"L": [round(x, 1) for x in wL], "R": [round(x, 1) for x in wR]}, "faces_removed_at_hand": removed,
            "tris": {p[0]: int(len(p[3])) for p in parts}, "min_edge_mm": min_edge}
    with open(os.path.splitext(a.out)[0] + "_parts.json", "w") as f:
        json.dump(info, f, indent=1)
    print(json.dumps(info))


if __name__ == "__main__":
    main()

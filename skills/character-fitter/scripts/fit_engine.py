"""Universal Character Fitter — geometry engine (numpy; no Blender needed). Codex proposal forwarded by Boss 25/10/2026: one fitter for
hair + outfit (+ face, done by stylized-lowpoly-humanoid/scripts/eyebrow_fitter.py), measured, with a Fitting Report — «agent không được
tuyên bố "fit thành công" chỉ vì nhìn Front View thấy đẹp».

Only VERTEX POSITIONS move: faces, triangle count and topology of the low-poly asset are never touched (gate in fit_character.py).

kinds
  hair   orientation searched (asset files face anywhere) → per-axis scale to the skull + translation, chosen by a cost that wants the scalp
         covered, nothing inside the head and the eye band clear → ROOT-ONLY deform: verts that clip are pushed out along the body normal
         and the push fades with distance (σ 1.5 cm), so spikes / ponytail keep their shape (no whole-asset shrinkwrap)
  lower  front = +Z (asset contract); belt ring → belt line on the body; uniform scale from the ring girth; then a RADIAL scale per height
         band (only where the body pokes through, smoothed along the height) + the same fading push for what is left
  upper  same as lower, anchored on the bust / pec peak
  rigid  armour / shoes: rigid align + uniform scale + translate out, never deformed
"""
import json, math
import numpy as np
import trimesh
from scipy.spatial import cKDTree
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "stylized-lowpoly-humanoid", "scripts"))
from analyze_outfit import ray_hits          # numpy Möller–Trumbore (no rtree on this machine)


# ---------------------------------------------------------------- body + landmarks
class Body:
    def __init__(s, glb, joints_json, anatomy_json=None, n_samples=120000):
        m = trimesh.load(glb, force="mesh"); s.mesh = trimesh.Trimesh(m.vertices, m.faces, process=True)
        P, fi = trimesh.sample.sample_surface_even(s.mesh, n_samples, seed=0); s.Pfi = fi
        s.P, s.N = P, s.mesh.face_normals[fi]; s.kd = cKDTree(P)
        Jb = json.load(open(joints_json)); s.J = {k: np.array([v[0], v[2], -v[1]]) for k, v in Jb.items()}
        s.A = json.load(open(anatomy_json)) if anatomy_json else {}
        J = s.J; s.y = {k: float(J[v][1]) for k, v in {"pelvis": "chau", "belly": "bung", "chest": "nguc", "neck": "co", "chin": "dau", "top": "dinh_dau"}.items()}
        T = s.A.get("face_T_zone", {}); s.xm = T.get("midline_x_cm", 0.0) / 100
        Hd = s.y["top"] - s.y["chin"]
        s.brow_y = s.y["chin"] + T.get("brow_y_frac_of_head", 0.6) * Hd; s.eye_y = T.get("eye_y_abs", s.y["chin"] + 0.48 * Hd)
        s.hairline_y = s.brow_y + (s.brow_y - s.y["chin"]) / 2              # face thirds
        V = s.mesh.vertices; hv = V[V[:, 1] > s.eye_y]
        s.skull_c = np.array([s.xm, (hv[:, 1].min() + hv[:, 1].max()) / 2, (hv[:, 2].min() + hv[:, 2].max()) / 2])
        s.skull_size = np.ptp(hv, axis=0)                                   # width, height (eye→top), depth
        s.ears = s.A.get("ears", {})
        s.face_probes = s._face_probes()
        s.waist_y, s.armpit_y = s._waist(), s._armpit(); s.underbust_y = s._underbust()

    def _slice(s, y, h=0.006):
        return s.P[np.abs(s.P[:, 1] - y) < h]

    def loops(s, y):
        """EXACT horizontal cross-section of the body mesh at height y: closed loops in x/z (segments chained end to end), each with its
        perimeter and whether it contains the body axis. Point samples were too noisy (male girth jumped 36 → 80 cm between slices)."""
        seg = trimesh.intersections.mesh_plane(s.mesh, [0, 1, 0], [0, y, 0])[:, :, [0, 2]]
        if not len(seg): return []
        key = lambda p: (round(p[0], 5), round(p[1], 5)); nxt = {}
        for a_, b_ in seg: nxt.setdefault(key(a_), []).append(b_); nxt.setdefault(key(b_), []).append(a_)
        seen, out = set(), []
        for a_, b_ in seg:
            if key(a_) in seen: continue
            loop = [a_]; seen.add(key(a_)); cur, prev = b_, a_
            while key(cur) not in seen:
                seen.add(key(cur)); loop.append(cur)
                cand = [q for q in nxt[key(cur)] if key(q) != key(prev)]
                if not cand: break
                prev, cur = cur, cand[0]
            L = np.array(loop)
            if len(L) < 4: continue
            per = float(np.linalg.norm(np.diff(np.vstack([L, L[:1]]), axis=0), axis=1).sum())
            xz = (s.xm, float(np.median(s.mesh.vertices[:, 2]))); inside = False   # even-odd test of the body axis
            for (x1, z1), (x2, z2) in zip(L, np.roll(L, -1, axis=0)):
                if (z1 > xz[1]) != (z2 > xz[1]) and xz[0] < x1 + (xz[1] - z1) * (x2 - x1) / (z2 - z1): inside = not inside
            out.append({"perimeter": per, "cx": float(L[:, 0].mean()), "axis": inside, "xmin": float(L[:, 0].min()), "xmax": float(L[:, 0].max())})
        return out

    def _torso_mesh(s):
        """the body without its arms: a vertex belongs to an arm when it is nearer the shoulder→elbow→wrist bones than the spine line and
        within 7 cm of them. Female arms touch the bust, so a plain cross-section counted both arms into the bust girth (the top became a cape)."""
        if getattr(s, "_torso", None) is not None: return s._torso
        V = s.mesh.vertices

        def seg_d(a, b):
            ab = b - a; t = np.clip(((V - a) @ ab) / (ab @ ab), 0, 1); return np.linalg.norm(V - (a + t[:, None] * ab), axis=1)
        J = s.J; spine = seg_d(J["chau"], J["co"])
        hand = {k: J[f"co_tay_{k}"] + (J[f"co_tay_{k}"] - J[f"khuyu_{k}"]) * 0.75 for k in "LR"}     # hand ≈ ¾ forearm past the wrist
        # the upper-arm segment starts 30 % down from the shoulder joint: from the joint itself it swallowed the shoulder blade, so the
        # bandeau was cut from a torso with no scapula and the back-left skin poked over it (Boss 25/10 ×2: «nách sau trái … lòi da»)
        up0 = {k: J[f"vai_{k}"] + 0.3 * (J[f"khuyu_{k}"] - J[f"vai_{k}"]) for k in "LR"}
        arm = np.min([seg_d(up0[k], J[f"khuyu_{k}"]) for k in "LR"] + [seg_d(J[f"khuyu_{k}"], J[f"co_tay_{k}"]) for k in "LR"]
                     + [seg_d(J[f"co_tay_{k}"], hand[k]) for k in "LR"], axis=0)
        is_arm = (arm < spine) & (arm < 0.09)
        # keep only the arm candidates MESH-CONNECTED to each hand: the outer hip / thigh is nearer the hanging forearm than the spine line,
        # so its big low-poly triangles were cut out as "arm" — the skirt's cover zone skipped them and the right thigh showed beside the
        # skirt in every front view while the gate read 0 (Boss 25/10 ×2: «váy bị lộ đùi bên phải» · «đùi phải vẫn lòi ra ngoài váy»)
        if os.environ.get("THU_ARM_MASK_NO_LEGS") != "1":                 # reverse test: =1 keeps the old blind mask
            from scipy.sparse import coo_matrix
            from scipy.sparse.csgraph import connected_components
            E = s.mesh.edges_unique; e = E[is_arm[E[:, 0]] & is_arm[E[:, 1]]]
            _, lab = connected_components(coo_matrix((np.ones(len(e)), (e[:, 0], e[:, 1])), shape=(len(V), len(V))), directed=False)
            seeds = [lab[np.argmin(np.linalg.norm(V - hand[k], axis=1) + np.where(is_arm, 0, 9))] for k in "LR"]
            is_arm &= np.isin(lab, seeds)
        keep = ~is_arm[s.mesh.faces].any(axis=1); s.arm_face = ~keep
        s._torso = trimesh.Trimesh(V, s.mesh.faces[keep], process=False); return s._torso

    def girth(s, y):
        """torso girth at y = perimeter of the convex hull of the arm-less cross-section."""
        from scipy.spatial import ConvexHull
        seg = trimesh.intersections.mesh_plane(s._torso_mesh(), [0, 1, 0], [0, y, 0])
        if len(seg) < 4: return np.nan
        P2 = seg.reshape(-1, 3)[:, [0, 2]]
        try: return float(ConvexHull(P2).area)
        except Exception: return np.nan

    def _waist(s):
        """narrowest torso GIRTH (convex perimeter of the torso piece) between the hip joint and the chest joint — where a skirt / belt
        sits (Boss 25/10: «cover waist, not at butt cheek»; the old pelvis→belly rule put the belt on the buttocks)."""
        ys = np.arange(s.y["pelvis"] + 0.05, s.y["chest"], 0.005); g = np.array([s.girth(y) for y in ys])
        s.girth_profile = (ys, g); return float(ys[np.nanargmin(g)])

    def _armpit(s):
        """highest height where the cross-section has the torso loop plus one SEPARATE loop on each side (the arms) — the top of an
        under-arm garment (Boss 25/10: «The female outfit supose to be underarm not overarm»)."""
        for y in np.arange(s.y["neck"] - 0.03, s.y["belly"], -0.004):
            L = s.loops(y); t = [l for l in L if l["axis"]]
            if not t: continue
            t = max(t, key=lambda l: l["perimeter"])
            left = [l for l in L if l["xmin"] > t["xmax"]]; right = [l for l in L if l["xmax"] < t["xmin"]]
            if left and right: return float(y)
        return s.y["chest"] + 0.05

    def _underbust(s):
        """female: where the girth below the bust peak has dropped half way to the waist; male: 8 cm under the pec peak."""
        ys, g = s.girth_profile; up = ys > s.waist_y
        if not up.any(): return s.y["chest"]
        ib = int(np.nanargmax(np.where(up, g, -1))); gb, gw = g[ib], np.nanmin(g)
        for k in range(ib, 0, -1):
            if g[k] < gb - 0.5 * (gb - gw): return float(ys[k])
        return float(ys[ib] - 0.06)

    def _face_probes(s):
        """points ON the face (both eyes, nose bridge, mouth, both cheeks) + 3 outward directions each: hair that blocks one of these rays
        covers the face. Measured by rays, not by counting vertices — a low-poly ponytail over the face has almost no vertices there."""
        chin = s.y["chin"]; pts = [("eye_L", 0.032, s.eye_y), ("eye_R", -0.032, s.eye_y), ("nose", 0.0, s.eye_y - 0.025),
                                   ("mouth", 0.0, chin + 0.35 * (s.eye_y - chin)), ("cheek_L", 0.045, s.eye_y - 0.03), ("cheek_R", -0.045, s.eye_y - 0.03)]
        T = s.mesh.triangles; zt = s.mesh.vertices[:, 2].max() + 0.2; out = []
        for nm, dx, y in pts:
            d = first_hit(T, np.array([[s.xm + dx, y, zt]]), np.array([[0, 0, -1.0]]))[0]
            if not np.isfinite(d): continue
            p = np.array([s.xm + dx, y, zt - d + 0.003])
            for v in ((0, 0, 1), (0.34, 0, 0.94) if dx >= 0 else (-0.34, 0, 0.94), (0, 0.3, 0.95)):
                out.append((nm, p, np.array(v) / np.linalg.norm(v)))
        return out

    def face_blocked(s, X, faces):
        """names of the face probes whose rays hit the asset."""
        O = np.array([p for _, p, _ in s.face_probes]); D = np.array([d for _, _, d in s.face_probes])
        return sorted({nm for (nm, _, _), h in zip(s.face_probes, ray_hits(X[faces], O, D)) if len(h)})

    def face_side_balance(s, X):
        """hair in front of the ears and below the brow, left vs right, weighted by how far it stands off the skin: 0 = balanced, 1 = all on
        one side. The sheet frames the face with locks on BOTH sides; one heavy lock on one side is the «đuôi tóc đang xoay bên trái mặt»
        Boss saw (left/right mass 2.03 vs 0.03 at the chosen yaw, 25/10). Returns (imbalance, total mass)."""
        ez = np.mean([e["most_proud_point"][2] for e in s.ears.values()]) if s.ears else s.skull_c[2]
        m = (X[:, 1] < s.brow_y) & (X[:, 2] > ez - 0.02); d, _ = s.signed(X); w = np.clip(d, 0, None)
        wl, wr = w[m & (X[:, 0] > s.xm)].sum(), w[m & (X[:, 0] < s.xm)].sum()
        return float(abs(wl - wr) / (wl + wr + 0.05)), float(wl + wr)

    def hanging_in_front(s, X):
        """fraction of FREE-hanging hair (below the eyes, > 4 cm off the skin, > 7 cm off the face midline = beside the face) that sits in front of the ears. A ponytail / long lock
        belongs behind the ears (Boss 25/10: «đuôi tóc đang xoay bên trái mặt»); a beard hugs the jaw (< 4 cm) and is not counted."""
        d, _ = s.signed(X); free = (X[:, 1] < s.eye_y - 0.01) & (d > 0.04) & (np.abs(X[:, 0] - s.xm) > 0.07)    # beside the face (past the cheeks); beard / mask sides not counted
        if free.sum() < 10: return 0.0, int(free.sum())
        ez = np.mean([e["most_proud_point"][2] for e in s.ears.values()]) if s.ears else s.skull_c[2]
        return float(np.mean(X[free, 2] > ez)), int(free.sum())

    def torso_view(s):
        """the same body with the ARMS removed for distance tests — an under-arm top has to pass through the arm–torso contact (the female
        arm touches the torso along the whole bust height), where the arm hides it. Fitting against the full body pushed the band's
        ends out OVER the arms (Boss 25/10: «Nữ áo chưa ôm vào nách»)."""
        if getattr(s, "_tv", None) is not None: return s._tv
        import copy
        t = copy.copy(s); T = s._torso_mesh(); P, fi = trimesh.sample.sample_surface_even(T, 80000, seed=6)
        t.P, t.N, t.kd = P, T.face_normals[fi], cKDTree(P); t._tv = t; s._tv = t; return t

    def hidden_in_arm_contact(s, X, d):
        """inside the body, but inside an ARM and within 2 cm of the torso surface = the strip where the arm presses on the torso, hidden by
        the arm. An under-arm top must pass there (the female arm touches the torso along the whole bust height)."""
        s._torso_mesh(); _, i = s.kd.query(X); on_arm = s.arm_face[s.Pfi[i]]
        tv = s.torso_view(); dt, _ = tv.kd.query(X)
        return (d < 0) & on_arm & (dt < 0.02)

    def signed(s, X):
        """signed distance to the skin (+ outside, − inside) and the skin normal at the nearest point."""
        d, i = s.kd.query(X); n = s.N[i]; sg = np.sign(np.einsum("ij,ij->i", X - s.P[i], n)); sg[sg == 0] = 1
        return d * sg, n

    def region_hair(s, X):
        """label every hair vertex by the head landmark it sits on."""
        out = np.full(len(X), "crown", dtype=object); c = s.skull_c
        front = X[:, 2] > c[2] + 0.15 * s.skull_size[2]; dx = np.abs(X[:, 0] - s.xm)
        out[(X[:, 1] < s.y["chin"] + 0.02)] = "neck_shoulder"
        out[(X[:, 1] < s.eye_y + 0.02) & ~front & (X[:, 1] >= s.y["chin"] + 0.02)] = "nape"
        out[front & (X[:, 1] > s.brow_y) & (X[:, 1] < s.hairline_y + 0.02) & (dx < 0.05)] = "forehead"
        out[front & (X[:, 1] > s.eye_y - 0.02) & (X[:, 1] < s.hairline_y) & (dx >= 0.05)] = "temple"
        for e in s.ears.values():
            p = np.array(e["most_proud_point"]); out[np.linalg.norm(X - p, axis=1) < 0.045] = "ear"
        out[s.in_eye_band(X)] = "eye_band"
        return out

    def in_eye_band(s, X):
        return (np.abs(X[:, 1] - s.eye_y) < 0.015) & (np.abs(X[:, 0] - s.xm) < 0.05) & (X[:, 2] > s.skull_c[2])

    def region_garment(s, X):
        y = s.y; out = np.full(len(X), "waist", dtype=object); back = X[:, 2] < np.median(s.mesh.vertices[:, 2])
        armx = abs(s.J["vai_L"][0] - s.xm) * 0.95
        out[X[:, 1] < y["pelvis"] + 0.06] = "hips"
        out[(X[:, 1] < y["pelvis"] + 0.12) & (X[:, 1] > y["pelvis"] - 0.12) & back] = "glutes"
        out[(X[:, 1] < y["pelvis"] - 0.02) & (np.abs(X[:, 0] - s.xm) < 0.05) & ~back] = "groin"
        out[X[:, 1] < y["pelvis"] - 0.10] = "thigh"
        out[X[:, 1] > y["belly"] + 0.03] = "chest"
        out[(X[:, 1] > y["belly"] + 0.03) & back] = "back"
        out[(X[:, 1] > y["chest"]) & (np.abs(X[:, 0] - s.xm) > armx * 0.75)] = "underarm"
        out[np.abs(X[:, 0] - s.xm) > armx] = "hand_arm"
        return out


# ---------------------------------------------------------------- asset helpers
def load_asset(path):
    m = trimesh.load(path, force="mesh"); return trimesh.Trimesh(m.vertices, m.faces, process=False)


def load_asset_parts(path):
    """the asset as ONE mesh for the geometry maths + its named PARTS (role geometries with their own materials) so fitted positions are
    written back per part. load_asset() flattened every role into one mesh — the belt, lining and stone all came out one colour (Codex
    audit 25/10). A part whose name ends with `__movable` may be deformed; every other part is PROTECTED (never moved; it fails if it clips).
    Returns (mesh, parts=[(name, vslice, fslice, visual)], movable_mask)."""
    sc = trimesh.load(path, force="scene"); V, F, parts, off_v, off_f = [], [], [], 0, 0
    for node in sorted(sc.graph.nodes_geometry):
        T, gname = sc.graph[node]; g = sc.geometry[gname]
        if not hasattr(g, "faces"): continue
        v = trimesh.transform_points(g.vertices, T); V.append(v); F.append(g.faces + off_v)
        parts.append((node, slice(off_v, off_v + len(v)), slice(off_f, off_f + len(g.faces)), g.visual))
        off_v += len(v); off_f += len(g.faces)
    mesh = trimesh.Trimesh(np.vstack(V), np.vstack(F), process=False)
    tagged = any(n.endswith("__movable") for n, *_ in parts)
    mov = np.ones(len(mesh.vertices), bool)
    if tagged:
        mov[:] = False
        for n, vs, _, _ in parts:
            if n.endswith("__movable"): mov[vs] = True
    return mesh, parts, mov


def rot_y(deg):
    r = math.radians(deg); return np.array([[math.cos(r), 0, math.sin(r)], [0, 1, 0], [-math.sin(r), 0, math.cos(r)]])


def edge_stretch(V0, V1, E):
    l0 = np.linalg.norm(V0[E[:, 0]] - V0[E[:, 1]], axis=1); l1 = np.linalg.norm(V1[E[:, 0]] - V1[E[:, 1]], axis=1)
    return l1 / np.maximum(l0, 1e-9)


def fading_push(V, body, clearance, sigma, iters=4, movable=None):
    """push clipping verts out to `clearance` along the skin normal; the push fades with distance exp(−d²/σ²) so the rest of the asset
    keeps its form (root-only deform). Returns new verts and the per-vertex displacement."""
    V = V.copy(); total = np.zeros_like(V)
    for _ in range(iters):
        d, n = body.signed(V); need = d < clearance
        if movable is not None: need &= movable
        if not need.any(): break
        src = V[need]; push = (clearance - d[need])[:, None] * n[need]
        kd = cKDTree(src); disp = np.zeros_like(V); wsum = np.zeros(len(V))
        for i, nb in enumerate(kd.query_ball_point(V, 3 * sigma)):
            if not nb: continue
            dd = np.linalg.norm(V[i] - src[nb], axis=1); w = np.exp(-(dd / sigma) ** 2)
            k = int(np.argmax(w * np.linalg.norm(push[nb], axis=1)))          # strongest nearby push wins (no averaging-away)
            disp[i] = push[nb][k] * w[k]
        V += disp; total += disp
    return V, total


# ---------------------------------------------------------------- hair


def first_hit(tris, O, D):
    out = np.full(len(O), np.nan)
    for k, (h, o, d) in enumerate(zip(ray_hits(tris, O, D), O, D)):
        if len(h):
            t = tris[h[0]]; n = np.cross(t[1] - t[0], t[2] - t[0]); out[k] = (n @ (t[0] - o)) / (n @ d)
    return out


def standoff(X, faces, pts, nrm, max_d=0.15):
    """how far the asset's INNER surface stands off the skin: ray from each body point along its normal to the first asset triangle.
    nan = nothing there (bare skin). This is what "oversize" means (Boss 25/10: «hair, outfit is currently oversize compare to the body»)
    — penetration alone never sees a garment hanging 3 cm off the body."""
    g = first_hit(X[faces], pts + nrm * 0.001, nrm) + 0.001
    g[g > max_d] = np.nan; return g


def eye_level_opening(asset, cav, drop):
    """face direction at EYE height: `drop` = eye depth under the ceiling in asset units. The face / mask hole is open there, while lower
    down a beard closes the front and the nape is open at the back (the lower-cavity opening put a beard behind the head, 25/10)."""
    T = asset.triangles; ax = cav["axis"]; ang = np.radians(np.arange(0, 360, 10)); D = np.c_[np.cos(ang), np.zeros_like(ang), np.sin(ang)]
    r0 = cav["radius_mid"]; o = np.zeros(len(D), bool)
    for f in (0.85, 1.0, 1.15):
        y = cav["ceiling"] - f * drop; r = first_hit(T, np.tile([ax[0], y, ax[2]], (len(D), 1)), D)
        o |= (~np.isfinite(r)) | (r > 1.8 * r0)
    best, face = 0, None
    for st in range(len(o)):
        L = 0
        while L < len(o) and o[(st + L) % len(o)]: L += 1
        if L > best: best, face = L, (st + (L - 1) / 2) % len(o)
    return (float(face * 10) if face is not None and best < len(o) else None), best * 10


def hair_cavity(asset):
    """the hair asset is a SHELL: hollow head cavity under a solid crown (measured 25/10 on both teachers). Returns the cavity axis (x, z),
    its ceiling, its inner half-width / half-depth, and the FACE direction = the widest arc where horizontal rays escape the shell."""
    V = asset.vertices; T = asset.triangles; b = asset.bounds; c = V.mean(axis=0)
    ang = np.radians(np.arange(0, 360, 10)); D = np.c_[np.cos(ang), np.zeros_like(ang), np.sin(ang)]
    y_lo, y_hi = b[0, 1], b[1, 1]; ax = np.array([c[0], 0, c[2]])
    # ceiling: walk the centre column upward from the lower third until it enters the shell
    ys = np.linspace(y_lo + 0.15 * (y_hi - y_lo), y_hi, 40)
    up = first_hit(T, np.c_[np.full(len(ys), ax[0]), ys, np.full(len(ys), ax[2])], np.tile([0, 1.0, 0], (len(ys), 1)))
    ceil = float(np.nanmin(ys + up)) if np.isfinite(up).any() else y_hi
    y_mid = ceil - 0.35 * (ceil - y_lo)
    for _ in range(3):                                                      # recentre the axis on the cavity walls
        r = first_hit(T, np.tile([ax[0], y_mid, ax[2]], (len(D), 1)), D)
        ok = np.isfinite(r)
        if ok.sum() < 6: break
        P = np.c_[ax[0] + D[ok, 0] * r[ok], ax[2] + D[ok, 2] * r[ok]]; ax[0], ax[2] = (P.min(axis=0) + P.max(axis=0)) / 2
    r_mid = first_hit(T, np.tile([ax[0], y_mid, ax[2]], (len(D), 1)), D)
    # face opening: at 2 heights in the lower cavity, directions with no wall (or a far wall) — widest contiguous arc
    open_ = np.zeros(len(D))
    for f in (0.55, 0.7):
        y = ceil - f * (ceil - y_lo); r = first_hit(T, np.tile([ax[0], y, ax[2]], (len(D), 1)), D)
        open_ += (~np.isfinite(r)) | (r > 1.6 * np.nanmedian(r_mid))
    o = open_ > 0; best, face = 0, None
    for st in range(len(o)):
        L = 0
        while L < len(o) and o[(st + L) % len(o)]: L += 1
        if L > best: best, face = L, (st + (L - 1) / 2) % len(o)
    face_deg = float(np.degrees(ang[0]) + face * 10) if face is not None else 90.0
    half_w = np.nanmedian(r_mid) if np.isfinite(r_mid).any() else 0.5 * np.ptp(V[:, 0])
    return {"axis": ax, "ceiling": ceil, "bottom": y_lo, "radius_mid": float(half_w), "face_dir_deg": face_deg, "open_arc_deg": best * 10}


def head_frame(skin_V, eye_y=None):
    """skull width / depth / top from skin verts above the eye line (or the top 12 % of the figure when no eye line is known)."""
    top = skin_V[:, 1].max(); ey = eye_y if eye_y is not None else top - 0.12 * np.ptp(skin_V[:, 1])
    hv = skin_V[skin_V[:, 1] > ey]
    return {"top": float(top), "width": float(np.ptp(np.percentile(hv[:, 0], [2, 98]))), "depth": float(np.ptp(np.percentile(hv[:, 2], [2, 98]))),
            "height": float(top - ey), "cx": float(np.median(hv[:, 0])), "cz": float(np.median(hv[:, 2]))}


def hair_extent(V, head):
    """hair size in units of the skull it sits on: width / depth over skull width / depth, lift of the top over the skull top / skull
    height, drop of the lowest hair below the skull top / skull height."""
    lo, hi = np.percentile(V, 2, axis=0), np.percentile(V, 98, axis=0)
    return {"width": float((hi[0] - lo[0]) / head["width"]), "depth": float((hi[2] - lo[2]) / head["depth"]),
            "top_lift": float((hi[1] - head["top"]) / head["height"]), "drop": float((head["top"] - lo[1]) / head["height"])}


def reference_hair(dressed_glb):
    """the OFFICIAL sheet character (coloured, one geometry per role): its hair size relative to its own skull = the size target.
    Boss 25/10: «The hair, the outfit is currently oversize compare to the body»."""
    sc = trimesh.load(dressed_glb, force="scene"); g = sc.geometry
    skin = g["skin"].vertices; hair = g["hair"].vertices
    head = head_frame(skin); e = hair_extent(hair, head)
    # the sheet hair in skull units — fit_hair maps it onto the body's skull and matches SHAPE + ORIENTATION to it (a beard-and-mask hair
    # rotated 180° leaves the face rays clear too; only the reference shows which side is the front)
    e["pts_skull"] = np.c_[(hair[:, 0] - head["cx"]) / head["width"], (hair[:, 1] - head["top"]) / head["height"], (hair[:, 2] - head["cz"]) / head["depth"]]
    return e


BACK_DEG, MASS_TOL = 180.0, 60.0   # main hair mass behind the head, ± 60°


def mass_direction(X, body):
    """direction (deg, 0 = front +Z, 90 = character's left +X) of the hair's most protruding mass — the 20 % of verts farthest from the skin
    (a ponytail, a bun, long locks) — seen from above, from the skull centre."""
    X = X[~beard_zone(X, body)]                                             # a beard is not "the main hair mass" (it put a short male cut at −25°)
    if len(X) < 20: return 0.0, 0.0
    d, _ = body.signed(X); far = d >= np.percentile(d, 80); v = X[far][:, [0, 2]].mean(axis=0) - np.array([body.skull_c[0], body.skull_c[2]])
    return float(np.degrees(np.arctan2(v[0], v[1]))), float(np.linalg.norm(v))


def fit_placed(asset, body, kind, clearance, movable=None):
    """the asset is ALREADY built in place on this body (procedural builders): never re-anchor, rotate or rescale it — only clear clipping,
    squeeze the beard, and push skin-through-a-triangle out. Re-placing a placed outfit opened 2.4 % skin it did not show (agent run 25/10)."""
    X = asset.vertices.copy(); Xr = X.copy(); disp = np.zeros_like(X); info = {"placed": True, "height_scale": 1.0}
    if kind == "hair":
        P_, N_ = body.P, body.N
        jaw = (P_[:, 1] > body.y["chin"] - 0.03) & (P_[:, 1] < body.eye_y - 0.035) & (P_[:, 2] > body.skull_c[2]) & (np.abs(P_[:, 0] - body.xm) < 0.075)
        ji = np.where(jaw)[0]; ji = ji[np.random.default_rng(3).choice(len(ji), min(300, len(ji)), replace=False)]
        X, pl = root_pull(X, asset.faces, body, P_[ji], N_[ji], clearance + 0.003)        # beard inner shell onto the jaw
        X, sq = beard_squeeze(X, body); X, d1 = fading_push(X, body, clearance, sigma=0.008); disp += pl + sq + d1
        body._pulled = np.linalg.norm(pl, axis=1) > 0.001
        md, ml = mass_direction(X, body)
        info.update({"face_side_imbalance": list(body.face_side_balance(X)), "mass_dir_deg": round(md, 1), "mass_offset_cm": round(ml * 100, 1),
                     "reference_mass_dir_deg": BACK_DEG, "beard_squeeze_max_mm": round(float(np.linalg.norm(sq, axis=1).max() * 1000), 1)})
    else:
        for _ in range(3):
            X, d1 = fading_push(X, body, clearance, sigma=0.02); X, d2 = poke_push(X, asset.faces, body, kind, clearance); disp += d1 + d2
            if not np.abs(d1).any() and not np.abs(d2).any(): break
    if movable is not None and not movable.all():                           # PROTECTED parts never move (the outer design is the artist's)
        X[~movable] = Xr[~movable]; disp[~movable] = 0.0
        info["protected_verts"] = int((~movable).sum())
    return X, info, Xr, disp


def angle_diff(a, b):
    return abs(((a - b) + 180) % 360 - 180)


def root_pull(X, faces, body, sc_p, sc_n, target, sigma=0.01, iters=2):
    """pull the hair's INNER shell onto the scalp: every scalp ray that meets the hair farther than `target` drags the vertices of the
    triangle it hit inward by the excess; the drag fades over σ among inner-shell vertices only — the outer spikes never move."""
    X = X.copy(); total = np.zeros_like(X)
    for _ in range(iters):
        T = X[faces]; hits = ray_hits(T, sc_p + sc_n * 0.001, sc_n); src, push = [], []
        for h, p, n in zip(hits, sc_p, sc_n):
            if not len(h): continue
            t = T[h[0]]; nn = np.cross(t[1] - t[0], t[2] - t[0]); g = (nn @ (t[0] - p)) / (nn @ n)
            if g > target + 0.002 and g < 0.15:
                for vi in faces[h[0]]: src.append(vi); push.append(-n * (g - target))
        if not src: break
        src = np.array(src); push = np.array(push); inner = np.unique(src)
        kd = cKDTree(X[src]); disp = np.zeros_like(X)
        cand = np.unique(np.r_[inner, np.concatenate(cKDTree(X).query_ball_point(X[inner], 2 * sigma))]).astype(int)
        for i in cand:
            nb = kd.query_ball_point(X[i], 2 * sigma)
            if not nb: continue
            dd = np.linalg.norm(X[i] - X[src[nb]], axis=1); w = np.exp(-(dd / sigma) ** 2); k = int(np.argmax(w))
            # only verts at least as close to the head as the pulled ones (inner side) follow — the outer surface stays as drawn
            if body.signed(X[i:i + 1])[0][0] <= body.signed(X[src[nb][k]:src[nb][k] + 1])[0][0] + 0.01: disp[i] = push[nb][k] * w[k]
        X += disp; total += disp
    return X, total


BEARD_CAP = 0.015   # m: a beard stands at most ~1.5 cm off the jaw (the sheet's beard hugs the face)


def beard_zone(X, body):
    """hair on the lower face: below the nose, in front of the ears, within the jaw width."""
    ez = np.mean([e["most_proud_point"][2] for e in body.ears.values()]) if body.ears else body.skull_c[2]
    return (X[:, 1] < body.eye_y - 0.03) & (X[:, 1] > body.y["chin"] - 0.08) & (X[:, 2] > ez) & (np.abs(X[:, 0] - body.xm) < 0.085)


def beard_thickness(X, body):
    """p90 distance of beard verts from the skin (mm) — how far the beard stands off the face. The jaw-ray standoff only saw its INNER
    surface (5 mm) while the side view showed it jutting out (Boss 25/10 ×2: «râu chưa sát vào mặt»)."""
    bz = beard_zone(X, body)
    if bz.sum() < 10: return None, int(bz.sum())
    d, _ = body.signed(X[bz]); return float(np.percentile(d, 90) * 1000), int(bz.sum())


BEARD_VIEWS = {"front": (0, 0), "front_down": (0, -20), "q_left": (40, -10), "q_right": (-40, -10), "left": (90, 0), "right": (-90, 0)}


def beard_see_through(X, faces, body, part_mask=None, cell=0.002):
    """holes in the beard (Boss 25/10 ×2: «Râu còn vài chỗ lủng» → «râu dưới bên phía trái bị một vệt hỏng nhìn thấy da»): in 6 views
    (front, front-down −20°, 3/4 L/R at chin height, sides) shoot a 2 mm orthographic grid over the beard's OWN silhouette; a ray that meets
    skin or nothing before the beard is a hole. The mouth is not inside the beard silhouette, so it is never counted.
    part_mask: faces that belong to the beard (+ moustache); default = faces in the lower-face beard zone."""
    from PIL import Image, ImageDraw
    if part_mask is None:
        fc = X[faces].mean(axis=1); part_mask = beard_zone(fc, body)
    BF = faces[part_mask]
    if len(BF) < 10: return None
    T_b = X[BF]; T_s = body.mesh.triangles; out = {}
    for name, (yaw, pitch) in BEARD_VIEWS.items():
        ya, pa = np.radians(yaw), np.radians(pitch)
        d = -np.array([np.sin(ya) * np.cos(pa), np.sin(pa), np.cos(ya) * np.cos(pa)])      # ray direction (camera looks along d)
        u = np.cross([0, 1.0, 0], d); u /= np.linalg.norm(u); v = np.cross(d, u)
        P2 = np.c_[X[BF].reshape(-1, 3) @ u, X[BF].reshape(-1, 3) @ v]; lo = P2.min(axis=0); hi = P2.max(axis=0)
        W, H = int((hi[0] - lo[0]) / cell) + 2, int((hi[1] - lo[1]) / cell) + 2
        img = Image.new("L", (W, H), 0); dr = ImageDraw.Draw(img)
        for t in P2.reshape(-1, 3, 2):
            dr.polygon([tuple((q - lo) / cell) for q in t], fill=255)
        m = np.array(img) > 0
        from scipy.ndimage import binary_erosion
        m = binary_erosion(m, iterations=1)                                  # edge cells only graze the silhouette (false holes)
        iy, ix = np.where(m)
        if not len(ix): continue
        pts2 = lo + np.c_[ix + 0.5, iy + 0.5] * cell
        O = pts2[:, :1] * u + pts2[:, 1:] * v - d * 1.0                     # 1 m in front, along −d
        Dd = np.tile(d, (len(O), 1))
        hb = first_hit(T_b, O, Dd); hs = first_hit(T_s, O, Dd)
        # a hole is (a) background through the beard silhouette (nothing hit at all) or (b) skin hit first AT a spot the beard covers
        # (skin point within 1.5 cm of the beard). Skin hit first far from the beard is the near cheek hiding the far-side beard, not a hole.
        bg = ~np.isfinite(hb) & ~np.isfinite(hs)
        skin_first = np.isfinite(hs) & (~np.isfinite(hb) | (hs < hb - 1e-4))
        if skin_first.any():
            sp = O[skin_first] + Dd[skin_first] * hs[skin_first][:, None]
            near = cKDTree(X[np.unique(BF)]).query(sp)[0] < 0.015
            skin_hole = np.zeros(len(O), bool); skin_hole[np.where(skin_first)[0][near]] = True
        else: skin_hole = np.zeros(len(O), bool)
        out[name] = {"rays": int(len(O)), "holes": int((bg | skin_hole).sum()), "background": int(bg.sum()), "skin": int(skin_hole.sum())}
    return out


def beard_squeeze(X, body, cap=BEARD_CAP):
    """squeeze the beard onto the face: each beard vertex's distance off the skin d → cap·(1 − e^(−d/cap)) along the skin normal (close
    verts barely move, far ones land just under `cap`); faded over 1 cm at the zone edge so the hair above is untouched."""
    if os.environ.get("THU_NO_BEARD_SQUEEZE"): return X, np.zeros_like(X)   # reverse test only
    bz = beard_zone(X, body); disp = np.zeros_like(X)
    if bz.sum() < 10: return X, disp
    d, n = body.signed(X); dn = cap * (1 - np.exp(-np.clip(d, 0, None) / cap)); move = np.where(d > 0, dn - d, 0.0)
    w = np.ones(len(X)); ez = np.mean([e["most_proud_point"][2] for e in body.ears.values()]) if body.ears else body.skull_c[2]
    w *= np.clip((body.eye_y - 0.03 - X[:, 1]) / 0.01, 0, 1) * np.clip((X[:, 2] - ez) / 0.01, 0, 1)
    disp[bz] = (move * w)[bz, None] * n[bz]
    return X + disp, disp


def fit_hair(asset, body, clearance, ref=None, yaw_hint=None):
    cav = hair_cavity(asset); c = body.skull_c; W, Hh, D = body.skull_size
    # rotate so the face opening points at +Z (glTF front): direction (cos a, sin a) in x/z → yaw that maps it to +z
    s_guess = (0.5 * np.mean([W, D * 0.85]) + clearance) / cav["radius_mid"]
    eye_dir, eye_arc = eye_level_opening(asset, cav, (body.y["top"] - body.eye_y) / s_guess)
    face_dir = eye_dir if eye_dir is not None else cav["face_dir_deg"]
    # GENERATOR CONTRACT: image→3D (Hunyuan3D-2) output faces +Z — measured on both base bodies (2°, 8°). The geometric openings are only
    # reported: Hunyuan fills a beard-hair's face as a mask with eye slits and leaves the back of the head open, so "open side = face" put the
    # male beard behind the head (25/10). Override per asset with yaw_hint when an asset was drawn turned.
    yaw0 = 0.0 if yaw_hint is None else float(yaw_hint)
    V0 = asset.vertices - np.array([cav["axis"][0], cav["ceiling"], cav["axis"][2]])
    skull_r = 0.5 * np.mean([W, D * 0.85])                                  # depth includes the nose
    s0 = (skull_r + clearance) / cav["radius_mid"]
    scalp = body.P[(body.P[:, 1] > body.hairline_y - 0.01) | ((body.P[:, 1] > body.eye_y) & (body.P[:, 2] < c[2]))]
    pick = np.random.default_rng(0).choice(len(scalp), min(1500, len(scalp)), replace=False); scalp = scalp[pick]
    mask = (body.P[:, 1] > body.hairline_y - 0.01) | ((body.P[:, 1] > body.eye_y) & (body.P[:, 2] < c[2]))
    sel = np.where(mask)[0][np.random.default_rng(1).choice(mask.sum(), min(220, mask.sum()), replace=False)]
    sc_p, sc_n = body.P[sel], body.N[sel]; target = clearance + 0.003

    def place(yaw, s, dy, k=(1, 1, 1)):
        X = (V0 @ rot_y(yaw).T) * s * np.array(k); X[:, 0] += c[0]; X[:, 2] += c[2]; X[:, 1] += body.y["top"] + clearance + dy
        return X
    bhead = head_frame(body.mesh.vertices, body.eye_y)
    ref_pts = None; ref_dir = BACK_DEG
    if ref is not None and "pts_skull" in ref:
        q = np.asarray(ref["pts_skull"]); ref_pts = np.c_[bhead["cx"] + q[:, 0] * bhead["width"], bhead["top"] + q[:, 1] * bhead["height"], bhead["cz"] + q[:, 2] * bhead["depth"]]
    # where the ponytail / long hair goes: BEHIND the head — official sheets 25/10 (female ponytail centre back, male long hair at the back).
    # Not read from the coloured sheet mesh: its "hair" role is mislabelled and put the mass at 96° (her left) — exactly Boss's complaint
    # «đuôi tóc đang xoay bên trái mặt».

    F = asset.faces

    def cost(X):
        d, _ = body.signed(X); inside = np.mean(d < -0.002)
        g = standoff(X, F, sc_p, sc_n); bare = np.mean(~np.isfinite(g)); gap = np.nanmedian(g) if np.isfinite(g).any() else 0.15
        blocked = body.face_blocked(X, F); crit = sum(b.startswith(("eye", "nose")) for b in blocked)
        # snug: inner shell ≈ clearance + 3 mm off the scalp; bare scalp and clipping cost; a blocked eye/nose costs more than any fit gain
        size = 0.0
        if ref is not None and ref_pts is not None:
            sub = X[::max(1, len(X) // 600)]
            cham = 0.5 * (cKDTree(ref_pts).query(sub)[0].mean() + cKDTree(sub).query(ref_pts)[0].mean())
        else: cham = 0.0
        if ref is not None:                                               # outer size vs the official sheet (log ratios, width/depth/lift)
            e = hair_extent(X, bhead); size = sum(abs(math.log(max(e[k_], 1e-3) / max(ref[k_], 1e-3))) for k_ in ("width", "depth")) + abs(e["top_lift"] - ref["top_lift"])
            md, mlen = mass_direction(X, body); imb, tot = body.face_side_balance(X)
            hang = body.hanging_in_front(X)[0] + (max(0.0, angle_diff(md, ref_dir) - MASS_TOL) / 180 if mlen > 0.02 else 0.0) + (imb if tot > 0.2 else 0.0)
            return 0.3 * size + 2.0 * cham + 0.1 * bare + 0.5 * inside + 1.0 * crit + 1.0 * hang, gap, inside   # cham: 2 cm off the sheet ≈ 0.04
        return abs(gap - target) + 0.1 * bare + 0.5 * inside + 1.0 * crit + 0.05 * (len(blocked) - crit) + 1.0 * body.hanging_in_front(X)[0], gap, inside
    best = None
    # the cavity's opening is only a HINT (a ponytail or long side hair also leaves "openings"): every yaw is tried, the face rays decide
    prior = lambda yw: 0.5 * abs(((yw - yaw0) + 180) % 360 - 180) / 180    # asset front = +Z (contract); turning it to the back costs 0.5
    # never more than 75° from the generator's front (a 3/4-view drawing): an asset that only "passes" turned around fails its gates instead
    # (Boss 25/10: «Male hair is backward» — the mask-beard escaped its blocked nose by facing the nape)
    yaws = yaw0 + np.arange(-75, 76, 15)
    if os.environ.get("THU_HAIR_YAW_FIXED"): yaws = [float(os.environ["THU_HAIR_YAW_FIXED"])]   # reverse test only: pin the bad facing
    for yaw in yaws:
        for sk in (0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 1.1):
            for dy in (-0.01, 0.0, 0.01, 0.02):
                cst = cost(place(yaw, s0 * sk, dy))[0] + prior(yaw)
                if best is None or cst < best[0]: best = (cst, yaw, s0 * sk, dy, (1, 1, 1))
    _, yaw, s, dy, k = best
    for kx in (0.92, 1.0, 1.08):                                            # per-axis: skull width / height / depth
        for ky in (0.92, 1.0, 1.08):
            for kz in (0.92, 1.0, 1.08):
                cst = cost(place(yaw, s, dy, (kx, ky, kz)))[0] + prior(yaw)
                if cst < best[0]: best = (cst, yaw, s, dy, (kx, ky, kz))
    _, yaw, s, dy, k = best; X = place(yaw, s, dy, k); X_rigid = X.copy()
    # beard: the jaw / cheeks / chin (front of the face under the cheekbones, to the ears) pull the beard's inner shell onto the skin too
    # (Boss 25/10: «Male: râu chưa sát vào mặt»); with no beard these rays meet no hair and nothing moves
    P_, N_ = body.P, body.N
    jaw = (P_[:, 1] > body.y["chin"] - 0.03) & (P_[:, 1] < body.eye_y - 0.035) & (P_[:, 2] > c[2]) & (np.abs(P_[:, 0] - body.xm) < 0.075)
    ji = np.where(jaw)[0]; ji = ji[np.random.default_rng(3).choice(len(ji), min(250, len(ji)), replace=False)]
    pull_p, pull_n = np.r_[sc_p, P_[ji]], np.r_[sc_n, N_[ji]]
    X, pull = root_pull(X, F, body, pull_p, pull_n, target)                 # inner shell down onto the scalp AND the jaw
    X, squeeze = beard_squeeze(X, body); pull = pull + squeeze
    X, disp = fading_push(X, body, clearance, sigma=0.008)                  # ROOTS only: σ 8 mm, spikes stay as drawn
    _, cover, inside = cost(X); body._pulled = np.linalg.norm(pull, axis=1) > 0.001   # inner shell: stretch there is intended
    disp = disp + pull
    return X, {"yaw_prior_deg": yaw0, "geometric_opening_deg": round(face_dir, 1), "eye_level_open_arc_deg": eye_arc, "yaw_deg": round(float(yaw), 1),
               "scale": round(float(s), 4), "axis_scale_xyz": list(k), "lift_cm": round(dy * 100, 1),
               "scalp_standoff_median_mm": round(float(cover * 1000), 1),
               "extent_vs_skull": {k_: round(v_, 3) for k_, v_ in hair_extent(X, bhead).items()},
               "reference_extent": {k_: round(v_, 3) for k_, v_ in (ref or {}).items() if k_ != "pts_skull"},
               "face_side_imbalance": [round(v_, 3) for v_ in body.face_side_balance(X)], "mass_dir_deg": round(mass_direction(X, body)[0], 1), "mass_offset_cm": round(mass_direction(X, body)[1] * 100, 1), "reference_mass_dir_deg": ref_dir,
               "chamfer_to_sheet_mm": round(float(0.5 * (cKDTree(ref_pts).query(X)[0].mean() + cKDTree(X).query(ref_pts)[0].mean()) * 1000), 1) if ref_pts is not None else None}, X_rigid, disp


# ---------------------------------------------------------------- garments
def fit_garment(asset, body, kind, clearance, anchor_frac=0.6, yaw=0.0):
    full = body
    V0 = asset.vertices @ rot_y(yaw).T; y = body.y; ax = np.array([body.xm, 0, np.median(body.mesh.vertices[:, 2])])
    hgt = np.ptp(V0[:, 1])
    ky = 1.0
    if kind == "lower":                                                     # belt line ON the waist (narrowest girth), measured
        band = V0[:, 1] > V0[:, 1].max() - 0.08 * hgt; target_y = body.waist_y + 0.01; ref = "top"
    else:                                                                   # UNDER the arms: top edge 2 cm below the armpit, bottom on the under-bust fold
        band = np.abs(V0[:, 1] - np.median(V0[:, 1])) < 0.1 * hgt
        # calibrated on the official sheet (female top spans 1.11–1.27 m on the 1.66 m body): bottom on the under-bust fold, top as far
        # above the bust peak as the fold is below it; girth from the TORSO loop only, so the arms stay outside
        peak = body.y["chest"] + body.A.get("chest", {}).get("peak_y_above_chest_joint_cm", 3.0) / 100
        bot_y = min(body.underbust_y, peak - 0.03); top_y = peak + 0.9 * (peak - bot_y); target_y = (top_y + bot_y) / 2; ref = "mid"
    ctr = V0[band].mean(axis=0); ring_r = np.percentile(np.hypot(V0[band, 0] - ctr[0], V0[band, 2] - ctr[2]), 25)   # INNER ring (knot/ornament stick out)
    # body girth at the anchor: mean radius of the skin around the body axis in a 2 cm slice
    anchor_y = target_y if ref == "top" else bot_y + 0.3 * (top_y - bot_y)
    g_ = body.girth(anchor_y)                                               # exact torso loop; arms are separate loops ⇒ never counted
    body_r = g_ / (2 * np.pi) if np.isfinite(g_) else 0.15
    s = (body_r + clearance) / max(ring_r, 1e-6)
    if kind == "upper": ky = (top_y - bot_y) / max(hgt * s, 1e-6)          # its height comes from armpit → under-bust, not from its girth
    hem_target = None
    if kind == "lower":
        # the hem must reach at least MID-THIGH (Boss 25/10: «increase the size of the skirt a lil bit so it can go down a lil bit more»):
        # a short asset is scaled up uniformly about its belt line; a longer one is left as drawn. The waist band is pulled snug again below.
        knee = np.mean([body.J["goi_L"][1], body.J["goi_R"][1]]); hip = np.mean([body.J["hong_L"][1], body.J["hong_R"][1]])
        hem_target = hip - 0.5 * (hip - knee); length = hgt * s
        if target_y - length > hem_target: s *= (target_y - hem_target) / length
    X = (V0 - ctr) * s; X[:, 1] *= ky; X[:, 0] += ax[0]; X[:, 2] += ax[2]
    X[:, 1] += target_y - (X[band, 1].max() if ref == "top" else (X[:, 1].max() + X[:, 1].min()) / 2)
    X_rigid = X.copy()
    # radial scale per 2 cm height band, BOTH ways: measured standoff of the inner surface (body point → along its normal → asset) pulled to
    # clearance + 2 mm; where the skin pokes through the band grows. Below the hip widest (lower) the band keeps the hip's scale so the hem
    # keeps its flare and teeth; smoothed along the height.
    target = clearance + 0.002; edges = np.arange(X[:, 1].min(), X[:, 1].max() + 0.02, 0.02); kband = np.ones(len(edges))
    torso = np.abs(body.P[:, 0] - ax[0]) < 0.8 * abs(body.J["vai_L"][0] - body.xm)
    hip_y = y["pelvis"] - 0.03 if kind == "lower" else -1e9; ktot = np.ones(len(edges))
    for it in range(3):
        d, _ = body.signed(X)
        for i, e in enumerate(edges):
            if e < hip_y: continue
            m = (X[:, 1] >= e - 0.01) & (X[:, 1] < e + 0.01)
            bp = torso & (np.abs(body.P[:, 1] - e) < 0.01) & (np.abs(body.N[:, 1]) < 0.6)
            if not m.any() or bp.sum() < 10: continue
            bi = np.where(bp)[0]; bi = bi[np.random.default_rng(i).choice(len(bi), min(80, len(bi)), replace=False)]
            g = standoff(X, asset.faces, body.P[bi], body.N[bi]); r = np.median(np.hypot(X[m, 0] - ax[0], X[m, 2] - ax[2]))
            k = 1.0
            if np.isfinite(g).mean() > 0.5: k = 1 - (np.nanmedian(g) - target) / max(r, 0.05)
            # a few clipping verts (belt knot, a hem tooth) are the fading push's job — letting them scale the whole band undid the snug fit
            if (d[m] < clearance).mean() > 0.25: k = max(k, 1.0)
            kband[i] *= float(np.clip(k, 0.7, 1.35))
            if os.environ.get("DEBUG_FIT"): print(f"  it{it} y {e:.3f} gap {np.nanmedian(g)*1000 if np.isfinite(g).any() else -1:.0f} mm hit {np.isfinite(g).mean():.2f} r {r*100:.1f} cm pen {(d[m] < clearance).sum()} k {kband[i]:.3f}")
        if kind == "lower":
            hi = np.searchsorted(edges, hip_y); kband[:hi] = kband[min(hi, len(kband) - 1)]
        ks = np.convolve(np.r_[kband[0], kband, kband[-1]], [0.25, 0.5, 0.25], mode="valid")
        X_ = X.copy(); X_[:, 0] = ax[0] + (X[:, 0] - ax[0]) * np.interp(X[:, 1], edges, ks); X_[:, 2] = ax[2] + (X[:, 2] - ax[2]) * np.interp(X[:, 1], edges, ks)
        X = X_; ktot *= ks; kband = np.ones(len(edges))
    X_rigid = X.copy()                                                      # deform risk is judged on the local push, not on the intended band scale
    disp = np.zeros_like(X)
    # hug: pull the INNER shell onto the skin it covers (top: all of it — under the arms, the sides, the back; skirt: the waist band
    # only, below the hips it keeps its flare). Boss 25/10: «Nữ áo chưa ôm vào nách» — a band scale alone left the sides 24 mm off.
    # (a "wing clamp" pulling the band's ends past the torso width back onto it was tried 25/10 on the Hunyuan top: stretch 7×, shards —
    # that asset is the wrong garment, the shape gate says so; a proper bandeau is built to the torso instead)
    # (skirt: not pulled — on the fused Hunyuan shells the pull flipped triangles and 21 % of the skin showed through, measured 25/10)
    if kind == "upper":
        zp, zn = cover_zone(body, kind, X)
        if len(zp):
            pick = np.random.default_rng(5).choice(len(zp), min(500, len(zp)), replace=False)
            X, pull = root_pull(X, asset.faces, body, zp[pick], zn[pick], clearance + 0.002, sigma=0.012, iters=1); disp += pull
    for _ in range(3):                                                      # vertex clipping and skin-through-a-triangle, until both are clean
        mov = None
        if kind == "upper": dd_, _ = body.signed(X); mov = ~body.hidden_in_arm_contact(X, dd_)   # leave the band in the arm–torso strip
        X, d1 = fading_push(X, body, clearance, sigma=0.02, movable=mov); X, d2 = poke_push(X, asset.faces, body, kind, clearance); disp += d1 + d2
        if not np.abs(d1).any() and not np.abs(d2).any(): break
    return X, {"yaw_deg": yaw, "scale": round(float(s), 4), "height_scale": round(float(ky), 3), "hem_target_y": round(float(hem_target), 4) if hem_target else None,
               "hem_y": round(float(X[:, 1].min()), 4), "anchor_y": round(float(target_y), 4),
               "waist_y": round(body.waist_y, 4), "armpit_y": round(body.armpit_y, 4), "underbust_y": round(float(body.underbust_y), 4), "body_radius_cm": round(float(body_r * 100), 1),
               "radial_scale_range": [round(float(ktot.min()), 3), round(float(ktot.max()), 3)]}, X_rigid, disp


def fit_rigid(asset, body, clearance, anchor):
    V0 = asset.vertices - asset.vertices.mean(axis=0); X = V0 + anchor; d, n = body.signed(X)
    if (d < clearance).any():
        X += np.mean(n[d < clearance], axis=0) * (clearance - d.min())
    return X, {"translate_out_mm": round(float(max(0, clearance - d.min()) * 1000), 1)}, X, X - (V0 + anchor)


TOOTH_ZONE = 0.07   # m above the lowest edge: the spec's hem teeth are 4–8 cm deep (median 6.6)


def cover_zone(body, kind, X):
    """skin the garment MUST hide: lower = waist line down to the top of its hem teeth (lowest edge + 7 cm), all round (legs included, arms not);
    upper = under-bust to 2 cm under its top edge. Arms are excluded (torso mesh)."""
    T = body._torso_mesh(); P, fi = trimesh.sample.sample_surface_even(T, 30000, seed=4); N = T.face_normals[fi]
    if kind == "lower":
        # ALL ROUND and down to 3 cm above the garment's own lowest edge in each 45° sector, outer thighs included (Boss 25/10: «Quần nam vẫn
        # còn lòi da 3 mặt còn lại» — the old zone stopped at the buttock fold and skipped the sides: it read 0.4 % while the sides showed 21–43 %)
        ax = np.array([body.xm, np.median(body.mesh.vertices[:, 2])])
        aP = np.degrees(np.arctan2(P[:, 0] - ax[0], P[:, 2] - ax[1])); aV = np.degrees(np.arctan2(X[:, 0] - ax[0], X[:, 2] - ax[1]))
        lo = np.full(len(P), np.inf)
        for sec in range(-180, 180, 45):
            mv = (aV >= sec) & (aV < sec + 45)
            if mv.any(): lo[(aP >= sec) & (aP < sec + 45)] = X[mv, 1].min() + TOOTH_ZONE   # gaps between hem teeth are the design
        hi = body.waist_y - 0.01; legs = np.zeros(len(P), bool)
    else:
        # up to 4 mm under the garment's top: the old «top − 2 cm» left the skin just under the bandeau's rope unmeasured — it read 0 while
        # Boss saw back skin poking through there (25/10, 2nd time: «chỗ áo nách sau trái của nữ bị lòi da sửa chưa?»)
        lo, hi = body.underbust_y + 0.01, X[:, 1].max() - 0.004; legs = np.zeros(len(P), bool)
    # skin within 3 cm of an arm / hand is hidden by the hand itself: it must not trigger a lining (male v2: 45 of the 1.2 % "visible"
    # points sat under the rest-pose hands and the auto lining then broke the skirt budget, 25/10)
    body._torso_mesh(); arm_pts = body.P[body.arm_face[body.Pfi]]
    near_hand = cKDTree(arm_pts).query(P)[0] < 0.03 if len(arm_pts) else np.zeros(len(P), bool)
    m = (P[:, 1] > lo) & (P[:, 1] < hi) & (np.abs(N[:, 1]) < 0.8) & ~legs & ~near_hand
    # look HORIZONTALLY, the way a viewer sees a body from the side: under the hip bulge the skin normal tilts down and its ray slipped out
    # under a flared hem — 22 % "visible" skin on the female skirt that nobody can see (25/10)
    Nh = N[m].copy(); Nh[:, 1] = 0; Nh /= np.maximum(np.linalg.norm(Nh, axis=1, keepdims=True), 1e-9)
    return P[m], Nh


def make_lining(body, X, clearance=0.004, angles=20, rows=4, thick=0.003):
    """a light leather LINING tube under a torn lower garment: from the waist to 2 cm above the garment's hem in each direction, its
    radius the convex hull of the hip / thigh cross-section (both legs bridged) + clearance. The outfit spec has a lining that peeks out
    in the lower tier; here it also hides the skin between the torn flaps (Boss 25/10 «Quần nam vẫn còn lòi da»)."""
    from scipy.spatial import ConvexHull
    T = body._torso_mesh(); ax = np.array([body.xm, np.median(body.mesh.vertices[:, 2])])
    ang = np.linspace(0, 2 * np.pi, angles, endpoint=False); aV = np.arctan2(X[:, 0] - ax[0], X[:, 2] - ax[1])
    bot = np.array([X[np.abs(((aV - a + np.pi) % (2 * np.pi)) - np.pi) < np.pi / angles * 1.5, 1].min() + 0.02 for a in ang])
    top = body.waist_y - 0.005; V = []
    for ri in range(rows):
        for side, off in ((0, clearance), (1, clearance + thick)):
            for a, yb in zip(ang, bot):
                y = top + (yb - top) * ri / (rows - 1); seg = trimesh.intersections.mesh_plane(T, [0, 1, 0], [0, y, 0])
                Q = seg.reshape(-1, 3)[:, [0, 2]]; H = Q[ConvexHull(Q).vertices]; d = np.array([np.sin(a), np.cos(a)]); r = 0.0
                for p_, q_ in zip(H, np.roll(H, -1, axis=0)):
                    e = q_ - p_; M = np.array([d, -e]).T
                    if abs(np.linalg.det(M)) < 1e-12: continue
                    t, u = np.linalg.solve(M, p_ - ax)
                    if t > 0 and 0 <= u <= 1: r = max(r, t)
                V.append([ax[0] + d[0] * (r + off), y, ax[1] + d[1] * (r + off)])
    k = lambda ri, side, j: (ri * 2 + side) * angles + (j % angles); F = []
    for ri in range(rows - 1):
        for j in range(angles):
            for side, flip in ((1, False), (0, True)):
                a_, b_, c_, d_ = k(ri, side, j), k(ri, side, j + 1), k(ri + 1, side, j + 1), k(ri + 1, side, j)
                F += [(a_, c_, b_), (a_, d_, c_)] if not flip else [(a_, b_, c_), (a_, c_, d_)]
    for ri, flip in ((0, False), (rows - 1, True)):
        for j in range(angles):
            a_, b_, c_, d_ = k(ri, 0, j), k(ri, 0, j + 1), k(ri, 1, j + 1), k(ri, 1, j)
            F += [(a_, b_, c_), (a_, c_, d_)] if not flip else [(a_, c_, b_), (a_, d_, c_)]
    m = trimesh.Trimesh(np.array(V), np.array(F), process=False); m.fix_normals(); return m


def see_through(X, faces, body, kind):
    """rays from the skin the garment must hide, outward along the skin normal: a miss = skin visible (Boss 25/10: «Quần lòi da ở mông»).
    Vertex-only clipping checks never saw it: the body pokes through the middle of a big low-poly triangle, not at a vertex."""
    P, N = cover_zone(body, kind, X)
    if not len(P): return P, N, np.zeros(0, bool)
    out = first_hit(X[faces], P + N * 0.001, N); return P, N, ~np.isfinite(out)


def poke_push(X, faces, body, kind, clearance, iters=8, sigma=0.012):
    """where skin shows because the garment surface lies UNDER the skin (an inward ray meets it within 6 cm), push the three corners of THAT
    triangle out along the skin normal past the skin + clearance (low-poly triangles are 5–10 cm: pushing "nearby verts" missed their
    corners), fading a little to the neighbours. A miss with nothing under the skin is a HOLE in the asset (reported, never patched here)."""
    X = X.copy(); total = np.zeros_like(X)
    for _ in range(iters):
        P, N, miss = see_through(X, faces, body, kind)
        if not miss.any(): break
        Pm, Nm = P[miss], N[miss]; T = X[faces]; hits = ray_hits(T, Pm + Nm * 0.001, -Nm)
        src, push = [], []
        for h, p_, n_ in zip(hits, Pm, Nm):
            if not len(h): continue
            t = T[h[0]]; nn = np.cross(t[1] - t[0], t[2] - t[0]); d = (nn @ (t[0] - p_)) / (nn @ -n_)
            if d >= 0.06: continue
            for vi in faces[h[0]]: src.append(vi); push.append(n_ * (d + clearance))
        if not src: break
        src = np.array(src); push = np.array(push); disp = np.zeros_like(X)
        for vi, pv in zip(src, push):                                       # the hit corners: strongest push wins
            if np.linalg.norm(pv) > np.linalg.norm(disp[vi]): disp[vi] = pv
        hard = np.unique(src); kd = cKDTree(X[hard])
        for i, nb in enumerate(kd.query_ball_point(X, 2 * sigma)):         # soften the step into the neighbours
            if not nb or i in set(hard): continue
            dd = np.linalg.norm(X[i] - X[hard[nb]], axis=1); w = np.exp(-(dd / sigma) ** 2); k = int(np.argmax(w))
            disp[i] = disp[hard[nb][k]] * w[k]
        X += disp; total += disp
    return X, total


# ---------------------------------------------------------------- report
def see_report(kind, asset, X, body):
    if kind not in ("lower", "upper"): return None
    P, N, miss = see_through(X, asset.faces, body, kind)
    if not len(P): return {"zone_points": 0}
    under = first_hit(X[asset.faces], P[miss] + N[miss] * 0.001, -N[miss]) if miss.any() else np.zeros(0)
    reg = body.region_garment(P[miss]) if miss.any() else []
    return {"zone_points": int(len(P)), "skin_visible_frac": round(float(miss.mean()), 4), "holes": int((~np.isfinite(under) | (under >= 0.06)).sum()),
            "garment_under_skin": int((np.isfinite(under) & (under < 0.06)).sum()), "by_region": {r_: int((np.asarray(reg) == r_).sum()) for r_ in sorted(set(reg))}}


def rest_report(kind, asset, X, X_rigid, disp, body):
    d, _ = body.signed(X); E = asset.edges_unique
    if kind == "upper": d = np.where(body.hidden_in_arm_contact(X, d), 0.0, d)   # the arm–torso contact strip is hidden, not clipping
    regions = body.region_hair(X) if kind == "hair" else body.region_garment(X)
    pen = d < 0; contact = d < 0.03
    per_region = {}
    for r in sorted(set(regions)):
        m = regions == r
        per_region[r] = {"verts": int(m.sum()), "penetrating": int((pen & m).sum()), "max_depth_mm": round(float(max(0, -d[m].min()) * 1000), 2),
                         "mean_clearance_mm": round(float(d[m & contact].mean() * 1000), 2) if (m & contact).any() else None}
    st = edge_stretch(X_rigid, X, E); moved = np.linalg.norm(disp, axis=1)
    pulled = getattr(body, "_pulled", None) if kind == "hair" else None; body._pulled = None
    inner_note = None
    if pulled is not None and pulled.any():                                 # judge the OUTER form only; the pulled inner shell is reported
        keep = ~(pulled[E[:, 0]] | pulled[E[:, 1]]); inner_note = {"inner_shell_verts_pulled": int(pulled.sum()), "inner_edge_stretch_max": round(float(st[~keep].max()), 2)}
        st = st[keep]
    # standoff of the inner surface over the skin it covers (oversize check) — body points in the asset's height range, rays along normals
    if kind == "hair":
        bm = (body.P[:, 1] > body.hairline_y - 0.01) | ((body.P[:, 1] > body.eye_y) & (body.P[:, 2] < body.skull_c[2]))
    else:
        bm = (body.P[:, 1] > X[:, 1].min()) & (body.P[:, 1] < X[:, 1].max()) & (np.abs(body.N[:, 1]) < 0.6) & \
             (np.abs(body.P[:, 0] - body.xm) < 0.8 * abs(body.J["vai_L"][0] - body.xm))
    bi = np.where(bm)[0]; bi = bi[np.random.default_rng(2).choice(len(bi), min(600, len(bi)), replace=False)]
    g = standoff(X, asset.faces, body.P[bi], body.N[bi]); gr = body.region_hair(body.P[bi]) if kind == "hair" else body.region_garment(body.P[bi])
    if kind == "hair":                                                       # beard: gap from jaw / cheeks / chin to the beard's inner surface
        P_, N_ = body.P, body.N
        jaw = (P_[:, 1] > body.y["chin"] - 0.03) & (P_[:, 1] < body.eye_y - 0.035) & (P_[:, 2] > body.skull_c[2]) & (np.abs(P_[:, 0] - body.xm) < 0.075)
        gj = standoff(X, asset.faces, P_[jaw][::3], N_[jaw][::3], max_d=0.05)
        beard = {"jaw_points_under_hair": int(np.isfinite(gj).sum()), "median_mm": round(float(np.nanmedian(gj) * 1000), 1) if np.isfinite(gj).any() else None,
                 "p90_mm": round(float(np.nanpercentile(gj, 90) * 1000), 1) if np.isfinite(gj).any() else None}
    else: beard = None
    so = {"median_mm": round(float(np.nanmedian(g) * 1000), 1) if np.isfinite(g).any() else None, "beard": beard,
          "p90_mm": round(float(np.nanpercentile(g, 90) * 1000), 1) if np.isfinite(g).any() else None, "covered_frac": round(float(np.isfinite(g).mean()), 2),
          "by_region_median_mm": {r_: round(float(np.nanmedian(g[gr == r_]) * 1000), 1) for r_ in sorted(set(gr)) if np.isfinite(g[gr == r_]).any()}}
    Xm = X.copy(); Xm[:, 0] = 2 * body.xm - Xm[:, 0]; sym = float(np.mean(cKDTree(X).query(Xm)[0]) * 1000)
    return {"verts": int(len(X)), "tris": int(len(asset.faces)), "penetrating_verts": int(pen.sum()),
            "max_depth_mm": round(float(max(0, -d.min()) * 1000), 2), "mean_clearance_mm": round(float(d[contact].mean() * 1000), 2) if contact.any() else None,
            "regions": per_region, "failing_regions": [r for r, v in per_region.items() if v["penetrating"]],
            "hanging_in_front": dict(zip(("frac", "free_verts"), body.hanging_in_front(X))) if kind == "hair" else None,
            "beard_thickness": dict(zip(("p90_mm", "verts"), beard_thickness(X, body))) if kind == "hair" else None,
            "beard_see_through": beard_see_through(X, asset.faces, body) if kind == "hair" else None,
            "eye_band_verts": int(body.in_eye_band(X).sum()), "face_blocked": body.face_blocked(X, asset.faces) if kind == "hair" else [],
            "symmetry_mirror_mean_mm": round(sym, 1), "standoff": so, "see_through": see_report(kind, asset, X, body),
            "deform": {"verts_moved_over_5mm": int((moved > 0.005).sum()), "max_move_mm": round(float(moved.max() * 1000), 1),
                       "edge_stretch_p99": round(float(np.percentile(st, 99)), 3), "edge_stretch_max": round(float(st.max()), 3),
                       "edge_shrink_min": round(float(st.min()), 3), "inner": inner_note}}

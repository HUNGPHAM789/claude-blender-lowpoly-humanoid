"""Shared helpers for procedural primal assets (hair, beard, torn outfit) built ON a measured base body.

Frame: glTF metres, Y up, body faces +Z. Every builder reads the body GLB + measurement JSON, never hard-coded body numbers.
"""
import json
import numpy as np
import trimesh
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

ROLE_COLOURS = {  # game palette (spec §5 hair, outfit spec §4)
    "hair": (58, 40, 28),
    "leather_dark": (74, 53, 37),
    "leather_tan": (176, 138, 92),
    "rope_bone": (196, 164, 108),
    "ornament_stone": (120, 116, 108),
}


def load_body(body_glb):
    mesh = trimesh.load(body_glb, force="mesh")
    mesh.fix_normals() if mesh.is_watertight else None
    return mesh


def load_json(path):
    with open(path) as f:
        return json.load(f)


class BodyQuery:
    """Ray casts (numpy Möller–Trumbore, no rtree on this machine) + signed distance against the low-poly body.
    Signed distance = nearest dense surface sample and its face normal (+ outside), the same rule the character fitter uses."""

    def __init__(self, mesh, samples=60000):
        from scipy.spatial import cKDTree
        from analyze_outfit import ray_hits
        self._ray_hits = ray_hits
        self.mesh = mesh
        self.T = mesh.triangles
        P, fi = trimesh.sample.sample_surface_even(mesh, samples, seed=1)
        self.P, self.N = P, mesh.face_normals[fi]
        self.kd = cKDTree(P)

    def _hits(self, origins, dirs):
        origins = np.atleast_2d(origins).astype(float)
        dirs = np.atleast_2d(dirs).astype(float)
        dirs = dirs / np.linalg.norm(dirs, axis=1, keepdims=True)
        return origins, dirs, self._ray_hits(self.T, origins, dirs)

    def _pick(self, origins, dirs, hits, which):
        n = len(origins)
        hit = np.full((n, 3), np.nan)
        nrm = np.full((n, 3), np.nan)
        dist = np.full(n, np.nan)
        for r, h in enumerate(hits):
            if not len(h):
                continue
            f = h[which]
            t = self.T[f]
            fn = np.cross(t[1] - t[0], t[2] - t[0])
            d = (fn @ (t[0] - origins[r])) / (fn @ dirs[r])
            hit[r] = origins[r] + dirs[r] * d
            nrm[r] = self.mesh.face_normals[f]
            dist[r] = d
        return hit, nrm, dist

    def first_hit(self, origins, dirs):
        o, d, h = self._hits(origins, dirs)
        return self._pick(o, d, h, 0)

    def last_hit(self, origins, dirs):
        o, d, h = self._hits(origins, dirs)
        return self._pick(o, d, h, -1)

    def inside(self, pts, n_rays=3):
        """parity vote with jittered rays (the low-poly body is not watertight; a nearest-normal sign alone mislabels ears/necks)."""
        pts = np.atleast_2d(pts)
        if not len(pts):
            return np.zeros(0, bool)
        rng = np.random.default_rng(0)
        votes = np.zeros(len(pts))
        for _ in range(n_rays):
            d = rng.normal(size=3)
            d /= np.linalg.norm(d)
            hits = self._ray_hits(self.T, pts, np.tile(d, (len(pts), 1)))
            votes += np.array([len(h) % 2 for h in hits])
        return votes >= 2

    def clearance(self, pts):
        """signed distance, forced negative where the parity test says the point is inside the body."""
        sd, _, _ = self.signed_distance(pts)
        near = sd < 0.01
        if near.any():
            ins = self.inside(pts[near])
            idx = np.where(near)[0][ins]
            sd[idx] = -np.abs(sd[idx]) - 0.001
        return sd

    def signed_distance(self, pts):
        pts = np.atleast_2d(pts)
        d, i = self.kd.query(pts)
        sg = np.sign(np.einsum("ij,ij->i", pts - self.P[i], self.N[i]))
        sg[sg == 0] = 1
        return d * sg, self.P[i], self.N[i]


def role_mesh(vertices, faces, role):
    mesh = trimesh.Trimesh(vertices=np.asarray(vertices), faces=np.asarray(faces), process=False)
    sys.path.insert(0, os.path.expanduser("~/projects/lpm-faceless-humanoid/theme"))
    import theme_colors
    rgba = np.clip(theme_colors.mau(ROLE_COLOURS[role]), 0, 1).astype(np.float64)  # sRGB 0–255 → linear baseColorFactor (theme rule)
    mat = trimesh.visual.material.PBRMaterial(
        name=role, baseColorFactor=rgba, metallicFactor=0.0, roughnessFactor=0.9, doubleSided=False)
    mesh.visual = trimesh.visual.TextureVisuals(material=mat)
    return mesh


def export_roles(parts, out_glb, flat=()):
    """parts: list of (name, role, vertices, faces). One node + geometry per part, named by role.
    Parts named in `flat` are exported with unmerged vertices so every face keeps its own normal (flat-designed planes)."""
    scene = trimesh.Scene()
    for name, role, v, f in parts:
        m = role_mesh(v, f, role)
        if name in flat:
            m.unmerge_vertices()
        scene.add_geometry(m, geom_name=name, node_name=name)
    scene.export(out_glb)
    return scene


def fix_winding_outward(vertices, faces, centre):
    """Flip faces whose normal points toward `centre` (for star-shaped shells)."""
    v = np.asarray(vertices)
    f = np.asarray(faces).copy()
    tri = v[f]
    n = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0])
    c = tri.mean(axis=1)
    flip = np.einsum("ij,ij->i", n, c - centre) < 0
    f[flip] = f[flip][:, ::-1]
    return f


def seg_dist(P, a, b):
    ab = b - a
    t = np.clip(((P - a) @ ab) / (ab @ ab), 0, 1)
    return np.linalg.norm(P - (a + t[:, None] * ab), axis=1)


def arm_mask(P, joints_gltf):
    """True for arm/hand skin: nearest bone by SURFACE distance (segment distance − bone radius). The hand hangs 8 cm from the hip skin
    but 15 cm from the narrow hip joint, so a plain nearest-segment rule handed the hip side to the arm."""
    J = {k: np.asarray(v, float) for k, v in joints_gltf.items()}
    keep = [("chau", "bung", 0.13), ("bung", "nguc", 0.14), ("nguc", "co", 0.13), ("chau", "hong_L", 0.13), ("chau", "hong_R", 0.13),
            ("hong_L", "goi_L", 0.08), ("hong_R", "goi_R", 0.08), ("goi_L", "co_chan_L", 0.05), ("goi_R", "co_chan_R", 0.05)]
    arm = []
    for s in ("L", "R"):
        hand_end = J[f"co_tay_{s}"] + (J[f"co_tay_{s}"] - J[f"khuyu_{s}"]) * 0.8
        arm += [(J[f"vai_{s}"], J[f"khuyu_{s}"], 0.05), (J[f"khuyu_{s}"], J[f"co_tay_{s}"], 0.04), (J[f"co_tay_{s}"], hand_end, 0.035)]
    dk = np.min([seg_dist(P, J[a], J[b]) - r for a, b, r in keep], axis=0)
    da = np.min([seg_dist(P, a, b) - r for a, b, r in arm], axis=0)
    return da < dk

"""Render a built body like the reference sheet: 3/4 front + 3/4 back (flat-shaded skin) and front / side / back wireframes
(white faces, black edges) on the same pastel panels. Pure Python (orthographic, painter's sort) — no Blender needed.

  python3 render_views.py <body.glb> <out.png> [--ref <reference_sheet.png>]   ⇒ out.png (and out_vs_ref.png: reference on top, build below)
"""
import sys, math
import numpy as np
import trimesh
from build_body import load_zup
from PIL import Image, ImageDraw

PANELS = [("q_front", -35, False, (250, 172, 150)), ("q_back", 145, False, (172, 160, 230)),
          ("front", 0, True, (236, 166, 172)), ("side", -90, True, (166, 160, 226)), ("back", 180, True, (206, 160, 212))]
SKIN = np.array([222, 150, 125.]); LIGHT = np.array([-0.45, -0.75, 0.5]); LIGHT /= np.linalg.norm(LIGHT)


def render(mesh, yaw, wire, bg, W=224, H=560):
    a = math.radians(yaw + 180)                                    # body faces +Y; camera sits at −Y ⇒ turn it to face us
    R = np.array([[math.cos(a), math.sin(a), 0], [-math.sin(a), math.cos(a), 0], [0, 0, 1]])   # turn the body, camera looks along +Y
    V = mesh.vertices @ R.T; F = mesh.faces
    zmax = V[:, 2].max(); s = H * 0.80 / zmax; ox, oy = W / 2, H * 0.92
    T = V[F]; n = np.cross(T[:, 1] - T[:, 0], T[:, 2] - T[:, 0]); n /= np.linalg.norm(n, axis=1, keepdims=True) + 1e-12
    vis = n[:, 1] < 0                                              # faces looking at the camera (camera at −Y)
    order = np.argsort(-T[:, :, 1].mean(axis=1))                   # far (large y) first
    im = Image.new("RGB", (W, H), bg); d = ImageDraw.Draw(im)
    nl = n @ LIGHT                                                 # light fixed to the camera, like a studio key
    for i in order:
        if not vis[i]: continue
        pts = [(ox + x * s, oy - z * s) for x, _, z in T[i]]
        if wire: d.polygon(pts, fill=(246, 246, 246), outline=(20, 20, 20))
        else:
            k = 0.42 + 0.58 * max(0.0, nl[i]); c = tuple(int(v) for v in np.clip(SKIN * k + 18, 0, 255))
            d.polygon(pts, fill=c, outline=c)
    return im


def main(glb, out, ref=None):
    mesh = load_zup(glb)
    tiles = [render(mesh, yaw, wire, bg) for _, yaw, wire, bg in PANELS]
    sheet = Image.new("RGB", (sum(t.width for t in tiles), tiles[0].height)); x = 0
    for t in tiles: sheet.paste(t, (x, 0)); x += t.width
    sheet.save(out)
    if ref:
        r = Image.open(ref).convert("RGB"); r = r.resize((sheet.width, int(r.height * sheet.width / r.width)))
        both = Image.new("RGB", (sheet.width, r.height + sheet.height), (255, 255, 255)); both.paste(r, (0, 0)); both.paste(sheet, (0, r.height))
        both.save(out.replace(".png", "_vs_ref.png"))
    print("saved", out)


if __name__ == "__main__":
    a = sys.argv[1:]; ref = a[a.index("--ref") + 1] if "--ref" in a else None
    main(a[0], a[1], ref)

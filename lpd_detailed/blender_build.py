"""blender -b -P blender_build.py -- geometry.json outdir
Builds BODY_M + HAIR_SHORT_01 (+ HAIR_SOCKET), measures counts FROM MESH DATA, exports GLB, renders."""
import bpy, bmesh, json, sys, os, math
from mathutils import Vector

argv = sys.argv[sys.argv.index('--') + 1:]
import os as _os
TEN = 'BODY_F' if _os.environ.get('GIOI') == 'nu' else 'BODY_M'
G = json.load(open(argv[0])); OUT = argv[1]
os.makedirs(OUT + '/renders', exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene


def mat(name, rgb, rough):
    m = bpy.data.materials.new(name); m.use_nodes = True
    b = next(n for n in m.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
    b.inputs['Base Color'].default_value = (*rgb, 1); b.inputs['Roughness'].default_value = rough
    b.inputs['Metallic'].default_value = 0.0
    return m


sys.path.insert(0, os.path.expanduser('~/projects/lpm-faceless-humanoid/theme')); import theme_colors as TM   # Boss 23/10: theme «Đất ấm» ⇒ da ấm; nhat_nha giữ ngà cũ
_DA = (0.80, 0.72, 0.58) if TM.theme() == 'nhat_nha' else tuple(TM.mau(TM.DA['dat_am'])[:3])
M = [mat('Body_Ivory', _DA, 0.85), mat('Eye_Dark', (0.035, 0.035, 0.04), 0.8),
     mat('Hair_Charcoal', (0.045, 0.045, 0.05), 0.80), mat('Socket_Shade', (0.12, 0.09, 0.07), 0.9)]   # hốc mắt bản B2: nâu-da tối (≈0,38 sRGB, giả bóng đọng), KHÔNG đen (đen = 0,035)


def build(name, D, mats):
    me = bpy.data.meshes.new(name)
    me.from_pydata([tuple(v) for v in D['V']], [], [tuple(f[0]) for f in D['F']])
    me.update()
    regs = sorted(set(f[1] for f in D['F']))
    attr = me.attributes.new('region', 'INT', 'FACE')
    for p, f in zip(me.polygons, D['F']):
        attr.data[p.index].value = regs.index(f[1]); p.material_index = mats.index(f[2]) if f[2] in mats else 0
        p.use_smooth = False
    for mi in mats: me.materials.append(M[mi])
    ob = bpy.data.objects.new(name, me); sc.collection.objects.link(ob)
    bm = bmesh.new(); bm.from_mesh(me)
    loose = [v for v in bm.verts if not v.link_faces]
    bmesh.ops.delete(bm, geom=loose, context='VERTS')
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(me); bm.free()
    return ob, regs, len(loose)


body, bregs, loose_b = build(TEN, G['body'], [0, 1, 3])
hair, hregs, loose_h = build('HAIR_SHORT_01', G['hair'], [2])

# socket: parented to the body (static model has no head bone; spec item 2 fallback)
sock = bpy.data.objects.new('HAIR_SOCKET', None); sc.collection.objects.link(sock)
sock.empty_display_type = 'ARROWS'; sock.empty_display_size = 0.05
sock.parent = body; sock.location = Vector(G['hair']['socket'])
hair.parent = sock; hair.location = (0, 0, 0)


# ---------------------------------------------------------------- measurements from mesh data
def counts(ob, regs):
    me = ob.data; a = me.attributes['region']
    out = {r: [0, 0] for r in regs}
    for p in me.polygons:
        r = regs[a.data[p.index].value]
        if len(p.vertices) == 4: out[r][0] += 1
        elif len(p.vertices) == 3: out[r][1] += 1
        else: out[r].append(('ngon', len(p.vertices)))
    return out


def topo(ob):
    bm = bmesh.new(); bm.from_mesh(ob.data); bm.edges.ensure_lookup_table()
    nonman = sum(1 for e in bm.edges if len(e.link_faces) > 2)
    boundary = sum(1 for e in bm.edges if len(e.link_faces) == 1)
    # duplicate faces (same vertex set)
    seen = set(); dup = 0
    for f in bm.faces:
        k = tuple(sorted(v.index for v in f.verts))
        dup += k in seen; seen.add(k)
    # non-planar quads (max dev / diag)
    npq = 0; worst = 0
    for f in bm.faces:
        if len(f.verts) == 4:
            c = f.calc_center_median(); n = f.normal
            dev = max(abs((v.co - c).dot(n)) for v in f.verts) / max(1e-9, (f.verts[0].co - f.verts[2].co).length)
            worst = max(worst, dev); npq += dev > 0.05
    # inconsistent winding: an interior edge whose two faces traverse it in the same direction
    bad = 0
    for e in bm.edges:
        if len(e.link_faces) == 2:
            d = []
            for f in e.link_faces:
                for l in f.loops:
                    if l.edge == e: d.append(l.vert == e.verts[0])
            bad += d[0] == d[1]
    shells = 0; seenv = set()
    for v in bm.verts:
        if v.index in seenv: continue
        shells += 1; st = [v]
        while st:
            x = st.pop()
            if x.index in seenv: continue
            seenv.add(x.index); st += [e.other_vert(x) for e in x.link_edges]
    tris = sum(len(f.verts) - 2 for f in bm.faces)
    r = dict(verts=len(bm.verts), faces=len(bm.faces), render_tris=tris, nonmanifold_edges=nonman,
             boundary_edges=boundary, duplicate_faces=dup, winding_conflicts=bad, shells=shells,
             nonplanar_quads_gt5pct=npq, worst_quad_nonplanarity=round(worst, 3))
    bm.free(); return r


# volume sign check (outward normals) on the body's main shell
def signed_volume(ob):
    me = ob.data; vol = 0
    for p in me.polygons:
        vs = [me.vertices[i].co for i in p.vertices]
        for k in range(1, len(vs) - 1):
            vol += vs[0].dot(vs[k].cross(vs[k + 1])) / 6
    return vol


rep = dict(body=dict(counts=counts(body, bregs), topo=topo(body), loose_removed=loose_b,
                     signed_volume=signed_volume(body)),
           hair=dict(counts=counts(hair, hregs), topo=topo(hair)))
# bbox
zs = [v.co.z for v in body.data.vertices]; xs = [v.co.x for v in body.data.vertices]
rep['body']['height'] = max(zs) - min(zs); rep['body']['span_x'] = max(xs) - min(xs)
# hair fit: min distance hair-rim to scalp (sample)
from mathutils.bvhtree import BVHTree
dg = bpy.context.evaluated_depsgraph_get(); bpy.context.view_layer.update()
bv = BVHTree.FromObject(body, dg)
hw = hair.matrix_world
inside = 0; dmin = 9; dists = []
for v in hair.data.vertices:
    p = hw @ v.co
    loc, nrm, idx, d = bv.find_nearest(p)
    if loc is None: continue
    s = (p - loc).dot(nrm)
    dists.append(s); inside += s < 0
rep['hair']['fit'] = dict(verts_inside_body=inside, min_signed_dist_mm=round(min(dists) * 1000, 2),
                          head_height_m=G['hair']['head_h'], target_offset_mm=round(G['hair']['off'] * 1000, 2))
json.dump(rep, open(OUT + '/counts_measured.json', 'w'), indent=1)
print(json.dumps(rep, indent=1))

# ---------------------------------------------------------------- export (glTF exporter converts Z-up -> Y-up)
def export(objs, path):
    bpy.ops.object.select_all(action='DESELECT')
    for o in objs: o.select_set(True)
    bpy.ops.export_scene.gltf(filepath=path, use_selection=True, export_yup=True, export_apply=False,
                              export_extras=True)


export([body, sock], OUT + f'/{TEN}.glb')
# hair alone, in socket space (vertices authored relative to HAIR_SOCKET)
mw = hair.matrix_world.copy(); hair.parent = None; hair.matrix_world = __import__('mathutils').Matrix.Identity(4)
export([hair], OUT + '/HAIR_SHORT_01.glb')
hair.parent = sock; hair.matrix_parent_inverse.identity(); hair.location = (0, 0, 0)
export([body, sock, hair], OUT + f'/{TEN}_with_HAIR_SHORT_01_fitted.glb')
bpy.ops.wm.save_as_mainfile(filepath=OUT + ('/lpd_female.blend' if TEN == 'BODY_F' else '/lpd_male.blend'))

# ---------------------------------------------------------------- render
for eng in ('BLENDER_EEVEE', 'BLENDER_EEVEE_NEXT'):
    try: sc.render.engine = eng; break
    except TypeError: pass
sc.render.resolution_x = 900; sc.render.resolution_y = 1200; sc.render.film_transparent = False
w = bpy.data.worlds.new('W'); sc.world = w; w.use_nodes = True
bg = next(n for n in w.node_tree.nodes if n.type == 'BACKGROUND')
bg.inputs[0].default_value = (0.78, 0.77, 0.75, 1); bg.inputs[1].default_value = 0.6
try: sc.view_settings.view_transform = 'Standard'
except Exception: pass
sun = bpy.data.objects.new('key', bpy.data.lights.new('key', 'SUN')); sc.collection.objects.link(sun)
sun.data.energy = 3.2; sun.rotation_euler = (math.radians(50), math.radians(10), math.radians(-35))
fill = bpy.data.objects.new('fill', bpy.data.lights.new('fill', 'SUN')); sc.collection.objects.link(fill)
fill.data.energy = 1.0; fill.rotation_euler = (math.radians(70), 0, math.radians(150))
cam = bpy.data.objects.new('cam', bpy.data.cameras.new('cam')); sc.collection.objects.link(cam); sc.camera = cam
cam.data.type = 'ORTHO'


def shot(name, target, yaw_deg, pitch_deg, ortho, res=(900, 1200), hair_on=False):
    hair.hide_render = not hair_on
    sc.render.resolution_x, sc.render.resolution_y = res
    t = Vector(target); yaw = math.radians(yaw_deg); pitch = math.radians(pitch_deg)
    d = Vector((math.sin(yaw) * math.cos(pitch), -math.cos(yaw) * math.cos(pitch), math.sin(pitch)))
    cam.location = t + d * 5
    cam.rotation_euler = (-d).to_track_quat('-Z', 'Y').to_euler()
    cam.data.ortho_scale = ortho
    sc.render.filepath = f'{OUT}/renders/{name}.png'
    bpy.ops.render.render(write_still=True)


shot('01_full_front', (0, 0, 0.88), 0, 0, 1.95)
shot('02_full_34', (0, 0, 0.88), 35, 5, 1.95)
shot('03_full_back', (0, 0, 0.88), 180, 0, 1.95)
shot('04_full_front_hair', (0, 0, 0.88), 20, 3, 1.95, hair_on=True)
shot('05_face_front', (0, -0.01, 1.64), 0, 0, 0.30, (900, 900))
shot('06_face_side', (0, -0.01, 1.64), 90, 0, 0.30, (900, 900))
shot('07_face_34_hair', (0, -0.01, 1.66), 35, 8, 0.34, (900, 900), hair_on=True)
shot('08_hair_back', (0, -0.01, 1.66), 160, 10, 0.34, (900, 900), hair_on=True)
# left hand (at +x): wrist centre approx from mesh
ra = body.data.attributes['region']; hi = bregs.index('hands')
hv = [body.data.vertices[i].co for p in body.data.polygons if ra.data[p.index].value == hi for i in p.vertices
      if body.data.vertices[i].co.x > 0]
hc = sum(hv, Vector()) / len(hv)
shot('09_hand_palm', hc, -19, 0, 0.24, (900, 900))
shot('10_hand_back', hc, 161, 0, 0.24, (900, 900))
shot('11_rear_pelvis', (0, 0.0, 0.84), 180, 0, 0.62, (900, 900))
shot('12_rear_pelvis_side', (0, 0.0, 0.84), 90, 0, 0.62, (900, 900))
# underside of hair cap (detached)
body.hide_render = True
shot('13_hair_underside', hair.matrix_world @ Vector((0, 0, 0)), 30, -55, 0.30, (900, 900), hair_on=True)
body.hide_render = False
print('DONE')

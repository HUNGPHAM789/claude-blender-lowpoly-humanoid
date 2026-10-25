---
name: humanoid-replaceable-assets
description: Layer assets that ATTACH to the low-poly humanoid base (hair, hats, shoes, gloves, clothes, backpacks) via its sockets/contract. Open before building any hair/shoe/garment for LPM or the combined humanoid. Hair recipe proven 22/10/2026; hair STYLIZATION still under development.
version: 0.5.1
metadata:
  hermes:
    tags: [humanoid, replaceable-assets, hair, low-poly, sockets]
    related_skills: [low-poly-origami-character]
---

# Replaceable humanoid assets (layer skill)

Base body contract = the humanoid skill (`low-poly-origami-character`, §4): named parts + `SOCKET_*` (dau, ban_tay_*, cam_*, ban_chan_*, lung, hong_*).
Rule: an asset is its own mesh/GLB, authored in the socket's space, never merged into the body.

## Hair — recipe that WORKS (test 22/10/2026, simplified-spec agent)
- ✅ Build the hair cap ON THE HEAD'S OWN VERTEX RINGS above the brow line, then scale it about `HAIR_SOCKET` by **k ≈ 1.032** (≈3 % out).
  Result: 0 / 4,000 sample points inside the head, no floating; median gap 3.9 mm.
- ⛔ An independently modeled cap with a fixed 6 mm offset: **106 / 4,000** samples ended inside the faceted head — a large-facet cap can't follow a faceted scalp.
- Detailed-spec agent also fitted its short hair at 0 verts inside (min gap 0.94 mm) by authoring in socket space against the actual head.
- `HAIR_SOCKET`: skull centre at brow height (≈ chin + 0.12 m for a 1.65 m body); hair parented to it at identity.
- Cap underside stays OPEN (seats over the scalp); hair is a separate node; swapping hair keeps the socket transform.

## Hair — NOT solved yet (Boss 22/10: «làm tóc vẫn chưa ra stylized cần phát triển thêm»)
Both test hairs read as a helmet/cap, not stylized folded clumps. Next development:
- clump grammar: N sectors around the head × crown rows; hanging rows only at sides/back; fringe stops above the brow; each clump = folded wedge with a pointed tip, alternating lengths;
- silhouette gate: % of hairline perimeter broken by clump tips; tip count per 90° sector; no clipping (keep the 4,000-sample inside test).

## Shoes / gloves / garments
- Shoes: remove `ban_chan_*` and place the shoe at `SOCKET_ban_chan_*` (the shin is closed, no hole).
- Garments: reuse the body section table (`THAN`) scaled outward 1–2 cm over the garment's z-range (shirt = torso rings × 1.03–1.05).
- Hand-held props: align the handle with `cam_*` (Ø32 mm grip axis) and build the body with `--co 1`.

## v0.2 (22/10/2026) — simple hair + settler outfits for the DETAILED humanoid (built, gated)
Boss: «Giờ tóc đơn giản cho nam và nữ. Đồ đơn giản cho nam và nữ — đồ thời nào là dễ làm RTS settler nhất? Giống GodUs?»
Era chosen: EARLY VILLAGE SETTLER (tribal → early medieval peasant) — garments are offset shells of the body tables, no buttons/collars; readable at isometric size by colour (Godus-like).
Code: `~/projects/GameDev/lpd_detailed/hair_outfit.py` (`GIOI=nam|nu python3 hair_outfit.py out_<g>`) → HAIR_SHORT_M / HAIR_BOB_F + OUTFIT_SETTLER_M (ao_than, ao_vat, quan, that_lung, giay) / OUTFIT_SETTLER_F (vay_than, vay_duoi, that_lung, giay). Render: `view_outfit.py`.
- HAIR: grid on the head's 16 columns; place every vertex by RAY-CASTING the real head mesh (incl. ears) from HAIR_SOCKET + gap 11 mm (+4 mm in the drop zone, +6 mm on columns next to the fringe). ⛔ Don't place hair on the interpolated scalp envelope: the real crown sits 8 mm behind it ⇒ 147/4000 clipping. ⛔ Gap 4 mm: the face between two hair vertices is a chord and cuts into bulges. Fringe hem above the brow; male hem above the ears until the 130° column (earlier switch ⇒ the slanted face crosses the ear back); bob = horizontal rays at ear level, slight puff, jagged hem.
- GARMENTS: shell = body faces of chosen regions offset along vertex normals (torso 10–11 mm, legs 8, feet 7); tunic hem / skirt = 16-sided tube whose radius per direction = farthest DENSE SURFACE SAMPLE of torso+legs at that z + gap, flaring down. ⛔ Measure from surface samples, not vertices (gap between thigh ring 0.765 and hip ring 0.865 ⇒ tube shrank inside body, 755/2000 clipping). Tunic hem must stay above the fingertips (0.716 m) or hands pierce it.
- GATE (in hair_outfit.py, exit 1): hair 0/4000 samples inside body; each garment ≤2 % of 2000 samples inside. Inside test = parity with 3 jittered rays, majority vote — a single +X ray runs along ring planes, hits edges, and mis-reported 4/8 known-inside points (calibrated 0/56 outside, 0/8 inside after the fix).
- Result: hair 368 tris; male outfit 1,329 tris; female 953 tris; all gates pass. Hair still reads simple (not folded-clump stylized).


## v0.3 (22/10/2026) — hand tools for settlers (Boss: berry · bow for deer · axe · pickaxe · hoe · shovel · watering can · fishing rod)
- Build: `python3 scripts/tools.py <dir>` → one GLB per tool + `tools.json`; gate runs at the end, exit 1 on fail.
  Output v1: `~/projects/GameDev/assets/tools/settler_v1/` (axe 40 tris … basket 268; all ≤600).
- Route: convex-hull primitives (`khoi`, `ong` prism, `hop`) — hard objects, NOT the organic skill (that makes clay blobs).
- **Grip contract**: origin = centre of the grip; handle axis = local +Z; working side (blade/spout/head) = local +X.
  Matches LPM `--co 1` socket `cam_L/cam_R` (`vi_tri`, `len` = cylinder axis, Ø32 mm).
  To attach: origin → `vi_tri`, +Z → `len`, +X → chosen world direction (axe/pick/hoe/shovel blade DOWN; can/basket body hangs, so +X = UP).
- Gates (measured on the mesh, not read from code): every part watertight · ≤600 tris · handle radius at the origin
  13–17 mm via a plane section at z=0. Reverse test 22/10: fishing rod tapered to 12.8 mm → rc=1; fixed to 14.5 → rc=0.
- Render: `blender -b -P scripts/view_tools.py -- <dir> <lpm.glb> <lpm.json> <out.jpg> R=riu L=binh_tuoi` (lineup + 3/4 figure).
- Traps: watering can / basket hang on −X, so the spout must rise toward +X (first version pointed it at the ground);
  a hoe blade facing the camera reads as a hook — make it big (~17 cm) and angled ~70°.
- Not done: two-handed poses (bow draw, hoe swing) need a second socket on the tool + IK; no clipping check vs body yet.
- **Review on the APPROVED settler** (Boss 22/10 «use our finished settlers model»): `CO=1 bash lpd_detailed/build.sh nam|nu`
  (grip hands, gate check_hold.py) then `scripts/view_settler_hold.py`. view_tools.py refuses a bare body.
- v0.4 (Boss 22/10): colours stay raw sRGB (house pale palette) — Boss tried Kiln's warm linear colours, then «tôi thích màu bên mình hơn».
  Pickaxe = crescent head. Rod = 6 segments × 4°; gate ⑦ fails any joint > 8° (old 25° kink → blocked).

## Hanging a tool on a peg / rack (Boss 23/10/2026: «Physics ko đúng»)
Grip on top of the peg, grip axis along the peg, body hanging straight down (centre of mass under the grip, ≤ 3 cm sideways). Never place a
hung tool by yaw only. Reference implementation + gate: `~/projects/GameDev/lpms/assets/weapon_rack.py` (weapon rack, LPMS README §Hanging).

---

## v0.5 — Curated Primal Human (8-view) + Procedural Stone/Bone Axe — 2026-10-24

### Mandatory design scope

The 8 user-provided reference screenshots depict a **detailed bearded primal man** with brows/eyes/nose, chunky hair, layered scarf, belt, asymmetric leather kilt, forearm bracer and fur-cuff boots. This is an **opt-in archetype profile `primal-detailed-settler`**, NOT a change to the canonical LPM *faceless humanoid* mesh or head triangle gates. Never replace `lpm.py`'s faceless face specification with this external-looking detailed sculpt. Preserve the canonical socket contract for compatible apparel/tools.

- **[Full curated eight-view anatomy, outfit and rig specification](PRIMAL_HUMAN_REFERENCE_SPEC_2026-10-24.md)**: per-image front/side/back anatomy observations; >40 numerical targets with confidence; front pixel calibration, facial clumps, tapered arms/legs, collar, braids, boots, optional individual digits, skeleton weights/limits and visualization gates. Only screen-estimates and proposed game dimensions are known—**actual source 3D mesh/bind weights not available**.
- **[Machine-readable calibrated landmark contract](SKELETON_LANDMARKS_8VIEW.json)**: R01 joint-dot pixels, R04 silhouette boxes, meter scaling flag and missing source measurements.
- **[Eight original reference images, the axe reference and provenance README](references/README.md)**: screenshots saved as-supplied, with uncertain copyright attribution; these images **are not automatically relicensed under this repo's MIT code license**.
- **[Original procedural primal axe builder](scripts/build_primal_axe.py)**: emits original faceted geometry by code (Trimesh/SciPy), **not** generated image or CGTrader asset reuse.
- **[Primal stone axe GLB](assets/primal_stone_axe.glb)**, **[Primal bone axe GLB](assets/primal_bone_axe.glb)**: physically modeled, tested GLB binary game assets, not mere mockups. Source reference visually uses dark stone; bone is the game-era ivory variant.

### Axe assembly contract and actual validated construction

1. **Curved shaft:** 8 longitudinal station rings, each with 9 side vertices, smooth longitudinal bend, tapered radius; grip station at authoring Z=0 has radius **0.016m**, matching the LPM Ø32mm socket cylinder. Wood material is flat warm ochre.
2. **Stone head:** asymmetric 16-vertex perimeter × two beveled face layers on both sides, triangle-faceted black/dark-slate geometry; chopping side is **local +X**. Stone is slightly BEHIND the handle in local depth so the wooden shaft and X-leather lashing remain visible, like the user's supplied photo.
3. **Bone head:** same attachment silhouette for compatibility, but warm pale ivory/ochre chipped-bone faceted material. Its color and survival progression are deliberately distinct from the dark *stone* reference.
4. **Leather fastening:** two wide diagonal X bands on visible front, two rear bands, additional circumferential winding around upper handle. Each short band is a CLOSED watertight faceted solid so it remains physically visible in GLB.
5. **Rendering optimization:** 58 individually tested small watertight components are merged by material into **4 render batches**. Both GLBs have **944 triangles** at this revision and are ~24 KB each. Tool-part provenance and gameplay parameters live in JSON generated by builder.
6. **Export frame:** construct Z-up, +Z handle, +X cutting face; export GLB in Y-up once. The grip center is tool local origin; after export, handle direction is local +Y. Attach GLB +Y to LPM socket `SOCKET_cam_L/R` axis and orient +X away from torso. Never apply the Z-up→Y-up transform twice.
7. **Durability gameplay:** example `durability_max=55`, decrement 1/chop, destroy at 0 and release worker/tool reservation; this is **a tunable prototype default**, not yet a confirmed balance decision.

Usage (requires `numpy scipy trimesh`):

```bash
python3 skills/humanoid-replaceable-assets/scripts/build_primal_axe.py \
  --out /tmp/primal_axes --variant both
# -> primal_stone_axe.glb/.obj/.json
# -> primal_bone_axe.glb/.obj/.json
```

### Mandatory acceptance tests for all future primal props

- Real GLB exists and can be reimported as a scene. All components and combined scene watertight; 0 NaN vertices and 0 degenerate triangles.
- Flat readable silhouette from front, side and isometric; blade not accidentally centered or mirrored, shaft slightly curved and tapering.
- Lashing must be visibly **in front of** head and wood under fixed game camera, with X readable at pixel scale (do not accept a hidden skin-deep ribbon).
- Ø32mm tool socket calibration exactly at grip origin; keep `SOCKET_cam_*` aligned and avoid grip penetrations; test hand animation in **humanoid-rig-animation** separately.
- For game use, 4 or fewer material groups for this asset, <=3,000 triangles, and use LOD/instancing for groups of tools displayed on racks.
- Correlate stone/chipped-bone fracture orientation, edge thickness and lashing paths rather than perturbing every vertex with independent randomness.
- Record generated part bounds, triangle budgets, Y-up transform and gameplay tool type in JSON manifest.

**Still pending:** posed rig/hand IK audit on the finished Settler, image-to-GLB silhouette comparison with consistent renderer/lighting and close-range leather collision audit. A render mockup is NOT a substitute for the GLB mesh.


## v0.5.1 (2026-10-24) — Upgraded primal gender variant taxonomy

Canonical game visual references are separated by **archetype**, not treated as interchangeable with the LPM faceless base body:
- `UPGRADED_MALE_PRIMAL`: 8 previously stored rig/weights/wireframe/render references `references/01_*.png`–`08_*.png`. Bearded male body with cloak/kilt and boots; refer to `PRIMAL_HUMAN_REFERENCE_SPEC_2026-10-24.md`.
- `UPGRADED_FEMALE_PRIMAL`: new five-panel collage, original dimensions 1122×1402, shaded front/back three-quarter + wireframe front/side/back. Dark angular tied hair, diagonal shawl, separate bust wrap, midriff, asymmetric skirt, fur-cuff boots. Refer to `references/UPGRADED_PRIMAL_VARIANTS_2026-10-24.md` for anatomy proportions, garment mesh groups, sockets, provenance and five separate evidence interpretations.
- Female visual reference is a **user-provided attachment**. The model source geometry and permission to redistribute images are unknown. Do not treat screenshot-estimated proportions as verified original mesh dimensions.
- For generated humanoid bodies, preserve the exact LPM base's socket and mesh naming contract; use separate hair/wardrobe/gear layers per archetype and retain both original author and license attribution once known.

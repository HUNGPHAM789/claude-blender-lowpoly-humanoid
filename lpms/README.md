# LPM Studio (lpms) — Kiln-style loop, our own geometry and gates (22/10/2026)
Boss: «Làm theo đề xuất của bạn chỉ lấy vài phần bên kiln». Taken from Kiln: one-call render receipt, immutable revisions with parent,
anchored edits with before/after diff, part-pair measurement, helper discovery, sweep/extrude ideas.
NOT taken: Kiln QA. COLOURS: Boss 23/10 overturned the pale palette ⇒ theme «Đất ấm» via `~/projects/GameDev/theme_colors.py` (true sRGB→linear; switch in theme.json), Kiln QA (passed wrong grip size, open parts, misplaced blade).

    python3 lpms.py render assets/<x>.py [--cam nam:R,nu:L]   # gates: watertight, budget, grip 13–17 mm, house colours; sheet.png 4 views; settler holding it
    python3 lpms.py edit r_xxxxxxxx --cu "<old>" --moi "<new>"  # child revision + size/parts diff
    python3 lpms.py pairs r_xxxxxxxx A:B[:cham|:ho=5] --cam nam:R  # gaps/penetration; --cam = every part vs settler BODY (reverse test: 100 mm → caught)
    python3 lpms.py discover [word] · python3 lpms.py log <name>
Store: ~/projects/GameDev/lpms_store/<name>/r_<sha8>/{source.py, <name>.glb, sheet.png, cam_*.png, receipt.json}
Asset program: META = dict(ten, cam, ngan_sach) + build() -> {part: trimesh}; helpers in lpms_helpers.py.

## Boundary layer (Boss 22/10/2026)
Every render writes `shatter.json` (convex hull per part) + gate «vỏ va chạm»; contact gates use it. Characters: las-physics `shatter.py` (capsule per bone, auto in animate.py).

## New asset from a concept (Boss 23/10/2026: «kêu codex vẽ… và viết spec… để cùng với skill bạn code được 90% giống hình concept»)
Codex via `~/bin/anchor-gen <mo_ta.txt> <refs…>` with refs = current renders (settler, an approved asset sheet) ⇒ concept PNG + `SPEC.md` written in OUR primitives (khoi/ong/khoi_meo/cau/non/quet), metres, Z up, MAU palette only, part table, ratios, state rules, slot layout, interaction points, likeness checklist. Template prompt: `~/projects/GameDev/concept/food/mo_ta.txt` (berry bush + food storage, 23/10).
- Built from that SPEC 23/10: `assets/berry_bush.py` (r_4bc25a58, 1100 tris; fruit parts `qua_<cluster>_<k>`, harvested = hide `qua_*`, harvest order 6,7,8,4,5,3,1,2,0) and `assets/food_storage.py` (r_4d8ae98e, 2920 tris; stock parts `dau_<slot>_<k>`, slot i shows clamp(Q−6i,0,6)). Deliberate SPEC deviation: lobes are geodesic (icosphere subdiv 1) because the SPEC's 14-point hull reads as pointy diamonds, not the concept's round lobes. Machine has no `rtree` ⇒ trimesh ray casts fail; use the numpy Möller–Trumbore `tia()` in berry_bush.py. Showcase render at the SPEC camera: `concept/food/ship.py`.

## ⭐ NATURE SPEC (25/10/2026) — supersedes the flamazilla rules below for trees, rocks, mountains, flowers, mushrooms, bushes, storage
Boss: «xài spec của bộ này để làm». Read `../specs/NATURE_SPEC_yukekbyte.md`; set META `loai` (tree, bush, rock_big, rock, pebble, cliff, log, stump, storage, mushroom, flower, grass, prop); colours only `yk_*`. Gate «spec nature» exits 1 otherwise.

## Nature-set geometry rules (learned 23/10/2026 from CGTrader «Low-Poly Forest Nature Set Free Trial», flamazilla)
Source + licence: `assets/downloads/cgtrader_forest/` (37 glb, `inventory.txt`, measured by `analysis_set_nature.py` → `analysis.json`). Licence «Royalty Free, No AI»; Boss 23/10: «dùng trong game và cho AI học luôn». Sizes below are ÷ object height H.
- **Built from loose convex pieces, never one welded blob.** Tree = trunk piece + 3 canopy pieces; bush = 1–3 blobs + 3–5 stick stubs; flower bush = 3 heads + leaf fans. Pieces overlap ~10–20%; nothing is booleaned.
- **Face budget by role**: stone 88 · stump 65–105 · log 57–104 · bare branch 54 · spruce 166–198 · small tree 155 · big tree 678 · bush 256–698 · grass tuft 143 · flower bush 238 · mushroom 72–86. Hero tree ≈ 700, everything else ≤ 250.
- **Canopy/bush blob** = icosphere-like 97 verts / 180 tris, squashed to ~1.0 : 1.05 : 0.85 (wide > tall), random vertex jitter so mean dihedral is **29–35°** (soft, lumpy). Deciduous canopy = 3 blobs of 0.5–0.7 H wide clustered at 0.55–0.85 H, each slightly different size.
- **Spruce** = 8-sided trunk (0.16 H wide, full height) + 3–4 stacked 8-sided cones (32 verts each, ring-split once) at 0.36 / 0.54 / 0.68 H, widths 0.58 / 0.42 / 0.33 H, + top cone 0.23 H. Cone facets sharp: dihedral **~62°**. Tiers overlap so no trunk shows between them.
- **Trunks/logs/stumps**: 6–8 sided rings (logs up to 21-vertex ring for knots), dihedral 45–50°; stumps have a root flare (bottom ring 1.3–1.5× top) and 9 flat bottom faces; hollow stump = open ring with inner wall.
- **Stones**: one piece 50 verts / 88 tris, wide-flat 2.0 × 2.5 × 1.0, **flat bottom (~14 faces)**, low dihedral 22–27° (smooth pebble). Mossy = same stone + extra cap faces (89 verts) coloured moss only on up-facing faces (normal.z > 0.5). Groups = 2 big + 1 chip (0.25 H).
- **Grass tuft** = 9 blade fans of 13 verts / 13 tris, each tapered strip folded once, splayed outward 20–45°, dihedral ~67–74°. Low tuft = same blades flattened (H ÷ 2.5).
- **Mushroom**: cap + stem one piece 68–74 verts, flat bottom; groups = 3 sizes 1.0 / 0.8 / 0.55.
- **Colour = palette atlas**: ONE material, UVs collapsed into colour cells of a 256² texture (`texture_gradient.png` = top-to-bottom gradient per cell for fake AO; `texture_solid.png` flat). Cells: greens 183,206,125 · 122,167,60 · 74,124,25; bark 185,146,110 · 153,105,44 · 119,71,46; stone 155 grey; flowers yellow/orange/red/blue/magenta. Our house rule stays: colours through `theme_colors.mau()`; their greens are brighter than «Đất ấm» ⇒ when mixing, darken their cells ~15% or keep both in separate scenes.
- **Shading**: flat (faceted) normals everywhere, no bevel, no subdivision; silhouette comes from piece count, not from vertex count.

## Hanging / displaying real props on storage (Boss 23/10/2026: «làm sao cái giỏ lại nằm ngang kiểu đó được? Physics ko đúng, trong skill ko có ghi điều đó?»)
- A hung item rests its GRIP on the TOP of the peg and hangs FREE: centre of mass directly BELOW the support point (horizontal offset ≤ 3 cm).
  With the tool contract (origin = grip, +Z = grip axis, +X = working side, body on −X): grip axis along the peg (local Z → ±peg axis),
  body down (local X → world +Z); origin = peg top + peg radius + handle radius. Rotating about Z only (what v1 did) leaves the basket sideways.
- Standing long tools: foot on a trough/cup, handle captured between peg pairs; heads face out so head width lies along slot depth.
- Gate pattern (see `assets/weapon_rack.py` soi): penetration vs every other part's convex hull ≤ 5 mm · every item rests or hangs ·
  hung items pass the centre-of-mass test (reverse test: Z-only rotation ⇒ 16–26 cm off, rc=1). Displayed real tools keep their own palette
  names; `da` from tools.py is imported as `da_lua`.

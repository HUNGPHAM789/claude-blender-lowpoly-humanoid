# LPM — Faceless Low-Poly Humanoid (origami style)

> 🗺 Full map of this asset factory (skills, library, packs): [MAP.md](MAP.md)

Procedural **faceless low-poly human base mesh** (male / female) in pure Python, built for games, Blender, Godot 4, and three.js.
Flat planar facets, a continuous lofted torso, separate convex limbs, detachable head/hands/feet with named **sockets**,
**grippable hands** (mitten + thumb, 5 hinged parts) controlled by one parameter, and **v2.7 Origami Hair Clump Grammar** with automated silhouette gating.


## Quick start
```bash
pip install numpy scipy trimesh
python3 lpm.py --out out/male --gioi nam            # open hands
python3 lpm.py --out out/female --gioi nu --co 1    # fist around a Ø32 mm grip
python3 hair_origami.py                              # generates male & female origami hair clumps
python3 check_hair.py samples/hair_origami_male.glb     # Gate ⑯ silhouette audit
blender -b -P view_lpm.py -- out/sheet.png out/male.glb out/female.glb   # 4-view render
```
Every build writes `.glb` (Y-up glTF, one node per body part + `SOCKET_*` empties), `.obj`, `.json` (sockets, hinge axes),
then **auto-runs `check_lpm.py`** — 15 measured gates (+ Gate ⑯ for hair); the build exits **1** if any fails.

## What the gates check (measured on the exported file)
watertight parts · triangle budget · height & feet on ground · body volume · continuous torso (no stacked boxes) ·
part/socket contract · L/R symmetry · waist taper · faceless head density · slight buttocks · forehead profile ·
no «skirt hem» at the pelvis · hand grips a Ø32 mm cylinder (≥75 % wrap, ≤1.5 mm penetration) ·
**Gate ⑯ Origami Hair Clump Grammar**: budget ≤450 tris, silhouette toothiness ≥15 mm, zero skull penetration (0/4000 samples).

## Sub-Skills & Ecosystem Architecture
This repository contains two first-class integrated sub-skills located under `skills/`:
1. [`skills/humanoid-replaceable-assets`](skills/humanoid-replaceable-assets/SKILL.md):
   - Modular layer assets attaching via LPM sockets (`SOCKET_dau`, `SOCKET_cam_*`, `SOCKET_ban_chan_*`, `SOCKET_lung`).
   - Origami hair clump grammar (`hair_origami.py`), early settler outfits (`hair_outfit.py`), and low-poly hand tools (`tools.py`).
2. [`skills/procedural-low-poly-world`](skills/procedural-low-poly-world/SKILL.md):
   - Procedural 3D low-poly world building, island generation, terrain dioramas, and stylized biome assets for Three.js & Godot 4.
   - **World Scale Hierarchy (Rule for Size)**: Strict scaling proportions pegged to LPM Humanoid base ($1.80\text{m}$): Stylized Oak ($5.8-6.5\text{m}$), Pine ($6.5-7.5\text{m}$), Deer Family (Stag $1.5\text{m}$/antlers $2.1\text{m}$, Hind $1.3\text{m}$, Fawn $0.85\text{m}$), Rabbit ($0.45\text{m}$), Berry Bush ($0.9-1.1\text{m}$), Storage Tile ($4\times 4\text{m}$).
   - **Master Asset Blueprints**: Mountain & Waterfall Pack Master v11.0 (unified massif, flush bedrock, wall-to-wall chute, welded alpine lake, organic non-circular pond basin, 28-pt sinusoidal S-curve river), Stylized Oak v2, Deer Family Pack, and Clean Low-Poly Rabbit.

## Nature World — procedural reference and examples (2026-10-24)

The `procedural-low-poly-world` sub-skill now includes:
- [Nature upgrade comparison manifest](skills/procedural-low-poly-world/NATURE_UPGRADE_MANIFEST_2026-10-24.md), covering **every publicly listed category** in a CGTrader reference pack (trees, bushes, flowers, mushrooms, stones, ground plants, clouds, logs/trunk, bridge, cliff, scene groupings). This is a **catalogue/spec comparison**, not direct proprietary mesh inspection.
- [Original procedural asset examples](skills/procedural-low-poly-world/scripts/nature_asset_examples.mjs) (**46 seeded mesh variants + 12 grouping examples**), with an adapter for Three.js.
- [Node tests](skills/procedural-low-poly-world/scripts/test_nature_asset_examples.mjs) and [interactive gallery](skills/procedural-low-poly-world/examples/nature_gallery.html).
- [Pure Python curve grammar](skills/procedural-low-poly-world/scripts/nature_curve_grammar.py), for independent swept/Bézier trunk meshes.

Run `node skills/procedural-low-poly-world/scripts/test_nature_asset_examples.mjs` and serve `skills/procedural-low-poly-world/` over local HTTP to view the gallery. **No third-party nature model binaries or textures are redistributed in this MIT repository.**

## Bi-Directional Pointer: GameDev Companion Workspace
This repository works in close harmony with the companion local workspace:
- **Local Path**: [`../GameDev/`](../GameDev/) (`~/projects/GameDev`)
- **Role & Boundary**:
  - `lpm-faceless-humanoid` is the **Canonical Humanoid Base Mesh & Layer Contract Authority** (base bodies, sockets, origami hair, validation gates).
  - `GameDev` is the **Game Asset Factory, Animation Testbed & Procedural World Engine**:
    - **Engine Primitives**: `lpms/lpms_helpers.py` providing `khoi()`, `khoi_meo()`, `quet()`, `dun()`, `la_gap()`.
    - **Unified Color Theme**: `theme_colors.py` (sRGB color mapping across all assets).
    - **Asset Store**: `lpms_store/` containing 34 production-ready low-poly props, furniture, and environmental pieces.
    - **Starter Packs**: `assets/aoe_starter_pack/` including the approved Mountain & Waterfall Pack Master v11.0, Starter 4-Square Storage, and Stylized Oak Tree v2.
    - **Animation Testbed**: `anim_settler/` (motion clips retargeted onto the LPM rig, Godot 4 export pipeline).

## Design rules (learned the hard way — see `SKILL.md` §9 upgrade log)
- Change body shape by editing the **section tables** (`THAN`), never by inserting blocks.
- Keep facet density uniform; this skill is deliberately **faceless** (detailed faces were tried and rejected; code kept in `history/`).
- Hand curl angles come from a **grid search** (`SKILL.md`), not from eyeballing.
- Hair clumps must follow the **Origami Clump Grammar** with automated silhouette gates (`check_hair.py`), never smooth helmet shells.
- A gate that passes while the render looks wrong is a broken gate — measure what the viewer sees.

Docs are in Vietnamese (`SKILL.md`); code identifiers are Vietnamese (e.g. `than` = torso, `tay` = hand, `co` = curl).


## SURVIVAL JOURNEY — executable prototype game logic specs (2026-10-25)

- **[Prototype Game Logic Spec V1](docs/survival-journey/PROTOTYPE_GAME_LOGIC_SPEC_V1.md)** — 2 settlers, island, autonomous jobs, food/firepit, tools, wildlife conservation, milestone crafting, day/night, player-approved construction, physical inventory and 40 acceptance tests. **One-person hauling only in V1**.
- **[Wood Gathering V1](docs/survival-journey/WOOD_GATHERING_V1_SPEC.md)** — one settler uses Bone Axe, chops tree → Wood ×5, carries ×3 then ×2, deposits in Starter Storage D; 16 specialized test cases.

These files describe the **approved design/implementation contract**, not a claim that the browser game has already been implemented. Q32 advanced warehouse design, cooperative carrying and island outward-expansion remain outside the first-house vertical slice.

## SURVIVAL JOURNEY — primal-human reference and real 3D primal axes

The 24 October 2026 curated reference expansion includes the **[detailed 8-view human specification](skills/humanoid-replaceable-assets/PRIMAL_HUMAN_REFERENCE_SPEC_2026-10-24.md)**, [rig coordinate annotations](skills/humanoid-replaceable-assets/SKELETON_LANDMARKS_8VIEW.json), and [nine supplied visual references](skills/humanoid-replaceable-assets/references/README.md) (8 primal views + source stone axe). Note: these images' original model authorship/licensing is unverified, and is **not** covered by the MIT code license.

**Real generated meshes** (not generated illustrations):
- [Stone axe GLB](skills/humanoid-replaceable-assets/assets/primal_stone_axe.glb) — dark chipped stone, curved wooden handle and X-bound leather straps.
- [Bone axe GLB](skills/humanoid-replaceable-assets/assets/primal_bone_axe.glb) — pale bone-age alternative on the same grip.
- [Reproducible Trimesh source](skills/humanoid-replaceable-assets/scripts/build_primal_axe.py) — rebuild both; 944 triangles each, 4 merged material render groups, 32mm grip compatibility.

The bearded detailed primal-human image set is a **new character archetype** and does not change the canonical *faceless* LPM base.


## Credits
v1 by Antigravity & Hermes · v2 rewritten by Claude (Anthropic) with Hung Pham, Oct 2026. MIT licensed.

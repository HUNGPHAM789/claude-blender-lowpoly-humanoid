---
name: character-fitter
description: Universal Character Fitter — fit hair + outfit (+ face via eyebrow_fitter) onto a base body, keep the low-poly topology, copy the body's rig weights, test 10 poses, and write a measured Fitting Report (exit 1 on a failed gate). Use before claiming any hair/outfit "fits".
---

# Universal Character Fitter (v0.1, 25/10/2026)

Codex proposal forwarded by Boss 25/10 (one engine, not three tools; a Fitting Report so the agent never says "fit" from a front view).
Boss corrections built in:
- «hair, outfit … oversize»
- «female outfit supose to be underarm not overarm - and cover waist, not at butt cheek»
- «increase the size of the skirt a lil bit»
- «Male hair is backward»

```bash
python3 scripts/fit_character.py --species humanoid --body <base_lp.glb> --joints <joints.json> --anatomy <anatomy.json> \
  --hair <hair.glb> --reference <sheet_coloured.glb> --outfit <skirt.glb>:lower --outfit <top.glb>:upper --out <dir> --name <id>
```
Output in `<dir>`:
- `<id>_fit_report.{json,md}`: the Fitting Report
- `<id>_dressed.glb`, `<id>_rigged.glb`
- `<id>_rest_*.png`: lit, white background
- `<id>_pose_*.png`: one frame per test pose

Exit 1 if any gate fails.

## Engine (`scripts/fit_engine.py`): only vertex positions move; faces and triangle count are gated unchanged

### Body landmarks (all measured on the mesh)
| landmark | how it is measured |
|---|---|
| face midline | from the anatomy data |
| eye / brow | from the anatomy data |
| hairline | face thirds: brow + (brow − chin) / 2 |
| skull frame | from the head vertices |
| waist | narrowest TORSO girth: exact cross-section, arms cut away by nearest bone |
| under-bust | girth half way from the bust down to the waist |
| face probes | eyes, nose, mouth, cheeks; 3 rays each |

### Hair
1. **Facing — generator contract:** image→3D output faces +Z (measured on both bodies: 2°, 8°); `--hair-yaw` overrides.
   - Geometric openings are only reported. Hunyuan fills a beard-hair's face as a mask and leaves the nape open, so "open = front" put the male beard at the back.
2. **Size — the official sheet:** width, depth and top lift relative to the skull, plus chamfer distance to the sheet's hair.
3. **Inner shell:** pulled onto the scalp, fading only among inner verts (`root_pull`). Clipping roots are pushed out with σ 8 mm.
4. The outer spikes are never shrinkwrapped.

### Garments
| step | lower (skirt) | upper (top) |
|---|---|---|
| vertical anchor | belt ring on the WAIST | under-bust → above the bust, so the top sits UNDER the arms |
| length / height | hem ≥ mid-thigh (a short asset is scaled up about the belt) | height from those landmarks; 0.7–1.4× gate, beyond that the asset is the wrong garment |

Then, for both:
- **Radial scale per 2 cm band**, in both directions, from the measured inner standoff. Below the hip widest point the skirt keeps its flare.
- **Fading push** for whatever still clips.

### Rigid
Armour and shoes: align + translate out only. **Untested.**

## Fitting Report (per layer)
- penetrating vertices and the deepest one (mm)
- inner **standoff** (median / p90, by region) — the oversize measure
- face rays blocked by hair
- symmetry
- deform risk: edge stretch on the outer form only
- per-pose clipping by region, with required poses marked

## Gates (`species/humanoid.json`)
| gate | limit |
|---|---|
| topology | unchanged |
| rest clipping | ≤ 1 mm |
| standoff | hair ≤ 12 mm, skirt ≤ 12 mm, top ≤ 8 mm |
| eyes and nose | clear (mouth/cheek reported: beards cover them) |
| edge stretch | p99 ≤ 1.3 |
| required poses | ≤ 1 % of verts and ≤ 6 mm deep |

Skirts in sit, crouch, kick and run are **report-only**: no fitter makes a rigid skirt follow a 90° thigh; that needs cloth bones.

## Single-rule gates (ledger seals) — `scripts/check_fit_gate.py`
These run one rule with its own exit code, because a full run on the Hunyuan fixtures still has other red gates.

| gate | rule |
|---|---|
| `--gate hair_facing` | Boss «Male hair is backward» · «đuôi tóc đang xoay bên trái mặt». Hair beside the face (in front of the ears, below the brow) is balanced left/right: imbalance ≤ 0.5. Free-hanging locks stay behind the ears. Eyes and nose stay clear. |
| `--gate beard_snug` | Boss «râu chưa sát vào mặt» ×2. Beard inner surface ≤ 6 mm off the jaw and the beard ≤ 18 mm thick (p90 off the skin). Fitting squeezes the beard onto the face; `THU_NO_BEARD_SQUEEZE=1` turns that off for the reverse test (33 mm ⇒ rc=1). |
| `--gate top_underarm` | Boss «underarm not overarm» · «Nữ áo chưa ôm vào nách» · «nách sau trái … lòi da» (×2). Skin showing ≤ 1 % up to 4 mm under the top edge; the torso's upper-arm segment starts 30 % down from the shoulder, so the shoulder blade counts as torso. Standoff ≤ 8 mm under the arms and on the back. Nothing inside the body except the hidden arm–torso strip. Height scaled 0.7–1.4×. |

Reverse tests:
- `THU_HAIR_YAW_FIXED=0` pins the facing Boss saw; balance 0.92 ⇒ rc=1.
- The Hunyuan cape top ⇒ rc=1.

Proper bandeau: `stylized-lowpoly-humanoid/scripts/build_bandeau.py` builds it from the arm-less torso sections, 360 tris.

## Placed assets (`--placed`)
Use for procedurally built assets that are already in place on the body (`build_spiky_hair.py`, `build_torn_outfit.py`, `build_bandeau.py`).
- The fitter never re-anchors, rotates or rescales them. It only clears clipping, pulls the beard onto the jaw, squeezes it, and pushes out skin that shows through a triangle.
- Re-placing an already-placed outfit opened 2.4 % skin that it did not show as built.
- The lower-garment budget is 1110 tris: skirt 900 + belt 150 + ornament 60.
- The skin-showing zone runs all round, legs included, down to the top of the hem teeth (lowest edge + 7 cm). Boss «Quần nam vẫn còn lòi da 3 mặt còn lại»: the old zone skipped the sides, which showed 21–43 % skin.
- A see-through lower garment gets an automatic lining tube (`make_lining`, ~320 tris, tan).

## Role parts, protection, final budget (Codex audit 25/10)
- `load_asset_parts`: every named geometry of an asset is a role part.
  - Fitted positions are written back per part, each keeping its own material. Before this, the belt, lining and stone came out as one colour.
  - Gate: «role parts kept», checked on the reimported delivered GLB.
- Parts whose name ends in `__movable` may be deformed. Every other part of a tagged asset is PROTECTED: it never moves, and it fails the clipping gates if it clips.
- «final budget» gates count the DELIVERED assembly by role, automatic lining included: hair 1,200 · skirt 900 · belt 150 · stone 60 · top 450.
- Pose results from several parts of one layer are summed.
- Still to do (Codex round 2): replace the beard gates with area-sampled contact coverage ≥ 99 %, gap p95 ≤ 6 / max ≤ 8 mm, a regional outer envelope and a maximum spike excursion. That needs the builder's `contact_inner` patch tags.

## Species
- `humanoid`: implemented.
- `quadruped_{deer,wolf,rabbit}`: profiles with planned regions and poses. They refuse to run until their landmarks are measured on a real mesh.

## Status on the primal teachers (Hunyuan test assets Boss set aside — fixtures only)
- Rest pose: hair, skirt and top are proportionate.
- Male hair faces the right way (generator contract).
- Beard inner surface: 5.1 mm off the jaw. It was 18 mm before the jaw rays joined the pull.
- Male skirt: skin visible in its zone is 0.37 %. The 11 visible points are holes in the asset; the 62 points where the skirt lay under the skin are fixed by the triangle-corner push.
- Pose test: uses ray parity since 25/10. The nearest-normal sign had flagged skirt verts beside the hands as "31 mm inside".

**Still red:**
- Female top asset is the wrong shape (0.395× height).
- A female hair lock covers the left eye.
- Male skirt clips the stepping thigh in walk (6.6 %).
- Male beard hits the chest when the head turns down.
- Outer edge stretch on skirts is about 2.2×.
- The Hunyuan beard mask juts out of the face in the side view. The beard metric only sees jaw rays that hit the beard; extend it.


## Gate `skirt_cover` (Boss 25/10 ×2 «đùi phải vẫn lòi ra ngoài váy»)
`python3 scripts/check_fit_gate.py --gate skirt_cover --body … --joints … --anatomy … --asset <skirt.glb>` exit 1 when > 1 % of the waist→hem-teeth skin shows. The arm mask (`Body._torso_mesh`) keeps only arm candidates MESH-CONNECTED to a hand — the outer hips used to be cut out as "arm", so a side slit read 0.9 % (reverse: `THU_ARM_MASK_NO_LEGS=1`). Female skirt v3 → 7.15 % rc 1; v4 (v3 left + v2 right, `compose_skirt_sides.py`) → 0.87 % rc 0. View-based diagnostic: `scripts/measure_lower_views.py --dressed <name>_dressed.glb …` (8 cameras).

## Old clips, skin through cloth, body masking (Boss 25/10: «sửa trọng số da nách … nhớ kiểm các clip animation cũ», «Gửi video stream», «Thử plugin robust weight transfer, thử cách game hay dùng luôn»)
Plan reviewed with Codex in 4 rounds (session 01a171c9-92cb-7602-bd8f-67a0b0ff231f) + a web-research agent.
- **Old clips on a dressed rig**: `scripts/clip_check_blender.py -- <rigged.glb> <out.json> <clip.glb>… [--visible --hidden <hidden.json>]`
  plays the settler clips (`~/projects/GameDev/anim_settler/A_male/{idle,walk,run,carry_log,place_wood}.glb`, same bone names; per-bone
  armature-space rotation delta, hips offset × height ratio, no root travel, IK skipped; NLA-only clips use the rig's own strip). Per frame:
  layer-vertex clipping tagged by the body bone it lands in (arm-in-cloth vs skin), regional stretch/compression (armpit, breast, shoulder,
  hip_thigh), triangle-area collapse. ⚠️ Vertex parity is BLIND to skin crossing BETWEEN cloth vertices (Boss saw the glutes through the
  back panel while it said 0.5 %) ⇒ the eye metric is `--visible`: emission ID render, 4 views, every frame — skin HIDDEN at rest that shows
  = RED («skin through cloth»), any body back-face = YELLOW («hole into body», ≈ 980 px baseline at idle from the arm–hip web cut).
- **Videos for the Boss**: `scripts/clip_video_blender.py -- <rigged.glb> <clip.glb> <dir>` (front ¾ + back ¾, lit, white) → ffmpeg hstack →
  `~/projects/GameDev/anim_settler/tools/preview_compare.py --src old.mp4 --result new.mp4 --label-src TRƯỚC --label-res SAU`.
- **Body masking** (game standard, ranked first by Codex + research): `scripts/hidden_skin_blender.py -- <rigged.glb> <hidden.json> --margin 0
  --apply <masked.glb>` — a face is HIDDEN when no camera sees it at rest (face-ID render from 40 directions, outfit/hair occluding) AND an
  outfit layer lies on it (normal ray ≤ 6 cm); deletes those faces. Female v10: 275 / 2369 faces (14.2 % of the skin) ⇒ skin through cloth
  0 px in all 5 clips (run was 9 819, place_wood 33 835 summed px), holes not above the unmasked rig. Margin 1 keeps only 60 faces (the
  covered band is one face thick on this low-poly body) and leaves 2–13 k px. Keep the UNMASKED rig for diagnostics (Codex).
- **Robust Weight Transfer** (SIGGRAPH Asia 2023; addon cloned at `~/tools/robust-weight-transfer`, deps in `~/.venvs/rwt` — libigl 2.5.1 has
  no wheel for Blender's Python 3.13): `LAYER_TRANSFER=rwt` in `rig_body_blender.py` (layers matching `RWT_LAYERS`, default `outfit_upper`).
  A/B 25/10: on the skirt it tore the rig 3.14× (pure) or worsened carry/place (with the shared field); on the top it was marginal and mixed
  ⇒ opt-in, not default. Voxel Heat Diffuse Skinning ($30) not bought — it re-binds, it does not stop cloth/skin crossing (Codex).
- **Inner cloth layers too** (`--inner skirt_lining`): the tan was the LINING (lower/upper tiers are the same dark brown). An inner-layer face
  counts as seen only from views at or above the horizon (the game camera never looks up under the skirt; with the low views 173/236
  lining faces were "seen"); 100 lining faces (34 %) masked ⇒ `--visible` «inner cloth through cloth» (MAGENTA) 0 px in all 5 clips
  (was ≤ 154 px/frame). The tan swirl at the left hip is a TEAR of the approved skirt v5, visible at rest — not a bug.
- **Arm path in a clip** (Boss 25/10 «chỉnh đường đi tay trong clip vác gỗ để tay không ép vào áo»): `scripts/arm_clearance_blender.py --
  <rigged.glb> <clip.glb> <out_clip.glb> <report.json> [--free] [--sides L|R|LR] [--max deg]` — per side ONE direction for the whole clip
  (smallest worst-frame need over 6 elbow-pole directions with 2-bone IK keeping the wrist, a shoulder shrug + IK, or with `--free` the
  whole arm turned about the shoulder so the hand moves); per frame the smallest angle that leaves no top vertex inside that arm, smoothed
  on the loop (moving max ±2, Gaussian σ 1.5, never below the need); bakes a clip for THIS character. carry_log: LEFT arm 5° out+forward,
  hand ≤ 17 mm → 0 mm; RIGHT arm cannot be cleared by any path (wrist fixed, or whole arm ±40°): the band's front-armpit edge sits in
  upper-arm-owned skin (front axillary fold, x −0.14 z 0.10–0.14 y 1.21) that rides the raised arm wherever it goes ⇒ a weights problem.
  Bugs met: set a child pose matrix only after its parent updated; restore the WHOLE frame pose before measuring a search step.
  RIGHT arm (Boss «sửa … để tay phải vác gỗ hết đè áo»): a bone-coloured close-up showed the upper arm lying ACROSS the band's top edge
  (male clip, no bust). With the wrist fixed the elbow only moves on a circle about shoulder→wrist ⇒ no pole/lift clears it; only moving
  the shoulder does: A = shrug 52.5° + IK (log stays; armpit stretch 1.84 → 2.34, breast 1.07 → 1.35, collapsed tris 3 → 12) ·
  B = shrug 20° + whole arm raised 22.5° (hand/log moves ≤ 88 mm; armpit 2.53, collapsed tris stay 3). Both: top clean. Boss picks by eye.
- Still open: the arm
  physically entering the top in carry_log (the clip's arm path — fix the pose/contact, not weights).

---
name: stylized-lowpoly-humanoid
description: Stylized low-poly MUSCULAR humanoid (primal adult male/female of the Settler game) — image → Hunyuan3D-2 (local, free) → code aligns, decimates and MEASURES on the 3D mesh. Different from the origami LPM. Status 25/10/2026: draft v1 m/f built, untextured, single mesh (body+hair+clothes), awaiting Boss's eye.
---

# Stylized low-poly humanoid

Boss 25/10/2026: «spec chi tiết từng bộ phận, các đường cong … phần torso ở dưới, chỗ lòi ra của ngực … các muscle — một skill
stylized low poly, khác với low poly origami» · «làm tay như vầy … bạn ko biết làm các khúc pointy» ⇒ generate the shape from the image,
measure with code · «phân tích theo actual 3D model thì tốt và chi tiết hơn» · «kêu codex làm nét ảnh và xoá background».
Official reference: `references/primal_starter_official_2026-10-25/` (5-view sheets + Codex-cleaned colour panels `*_clean_codex.png`).

## Pipeline (what worked, 25/10/2026)
| step | command | notes |
|---|---|---|
| 1 clean the image | `ANCHOR_CWD=<dir> ~/bin/anchor-gen brief.txt <panel.png>…` (Codex imagegen) | same design/pose, pure white bg, NO cast shadow, nothing behind armpits/between legs, sharper. ⛔ rembg/u2net/isnet: skin ≈ pink bg ⇒ washed skin or lost shins; ⛔ shadow ⇒ ground plate in the mesh |
| 2 square pad | white square 1024² | |
| 3 image → mesh | `~/bin/hy3d <img> --quality medium --seed 42 --output raw.glb` | ComfyUI :8188 with `~/image-gen-venv` (`python main.py --port 8188`), weights `~/ComfyUI/models/diffusion_models/hy3dgen/hunyuan3d-dit-v2-0-fp16.safetensors` (4.9 GB). ≈ 80 s. Shape only (texture nodes are Windows-only) |
| 4 align | `python3 scripts/align_to_reference.py --sex m\|f --glb raw.glb --out aligned.glb` | feet z=0, height = spec `scale_m` (incl. hair), drops shadow plate away from the footprint; facing = line through the two ankles (⛔ chest width: hair fools it), front/back by the SIDE silhouette (face/bust/glutes), ±10° IoU trim |
| 5 low poly | `blender -b -P scripts/lowpoly_blender.py -- aligned.glb lp.glb 3000` | collapse decimate, smooth-by-angle 35° (reference look: soft light, hard silhouette), Y-up GLB facing +Z |
| 6 measure (gate) | `python3 scripts/measure_mesh.py --sex m\|f --glb lp.glb` | exact plane sections at the landmarks (cm); height ± 2 %, tris ≤ 3500, female bust protrusion ≥ 0.6 × sheet (sheet 4.1 cm) ⇒ exit 1 |
| 7 silhouette | `python3 scripts/compare_silhouette.py --sex m\|f --glb lp.glb --out <dir>` | overlay vs sheet masks (red sheet only / cyan build only), band IoU (thresholds still draft) |
| 8 preview for Boss | `blender -b -P scripts/render_shaded_blender.py -- lp.glb <out.png>` + `python3 scripts/render_views.py lp.glb <wire.png>` | sheet on top, build below (`previews/<sex>_hy3d_v1_vs_reference.png`) |

Sheet measurement (`measure_reference.py`, `extract_profiles.py`) feeds the spec landmarks + silhouette masks. `build_body.py` +
`spec/male_spec.json` = the earlier hand ring-loft (kept as a fallback / for the `load_zup` helper; it reads as a mannequin — don't use for art).

## Results v1 (25/10/2026)
- male: 1.866 m incl. hair, 3000 tris, silhouette IoU front 0.66–0.78 · side 0.65–0.87 · back 0.70–0.83
- female: 1.776 m, 3000 tris, bust protrusion 5.1 cm (sheet 4.1), IoU front 0.64–0.72 · side 0.69–0.75 · back 0.71–0.85
- files: `assets/characters/primal_adult_{male,female}_draft_v1.glb`

## Open
- female ponytail missing (single front image ⇒ the back is guessed) → try Hunyuan3D-2mv (node `Hy3DGenerateMeshMultiView`, weights not downloaded) with Codex-made front/side/back colour views
- one mesh = body + hair + clothes; the game needs layers (body, hair, outfit sockets as in `humanoid-replaceable-assets`)
- no colour yet (vertex colours projected from the clean image, or per-part materials)
- rig: not started (GameDev animation pipeline expects the LPD rig profile)
- best input for next time: orthographic front / 90° side / back, A-pose, naked base + separate hair/outfit sheets, ≥ 1000 px per view

## LEARN from teacher meshes (25/10/2026) — hair, ponytail, torn outfit
Boss: «Thôi ko lấy assets này, học từ assets tóc và outfit này … chunky spikey hair, tóc đuôi cột, quần rách · học bằng cách nào? scan số liệu?»
· «quét ra từng khuôn màu … là thấy được dây cột tóc · áp dụng cho quần có belt để tìm chính xác vùng belt và tô màu».
Teachers = Hunyuan3D meshes from Codex asset images drawn LARGE (≈85 % of a 1024² frame — small crops come out lumpy). Never shipped.

| step | command | finds |
|---|---|---|
| hair clumps | `scripts/analyze_hair.py --hair <fit> --body <body_fit> --joints <j> --out <p>` | tips (highest proud point in a 1.5 cm ball), clumps by watershed of height-above-scalp; per region length / base width / tip half-angle / tilt / droop (stable: 84–85 clumps for ball 1–2 cm) |
| ponytail | `scripts/analyze_ponytail.py …` | midline hanging hair: PCA axis, 16-slice radius profile, length, droop, root height, lock tips |
| outfit | `scripts/analyze_outfit.py --outfit <fit> --out <p> --kind skirt\|top` | radius profile + flare, belt band (radius bulge in the top 30 %), ornament (proud front blob), hem teeth (count/depth/spacing). Ray layers find nothing: generated layers are FUSED ⇒ lining exists only as colour |
| molds («khuôn») | `scripts/segment_mesh.py --kind skirt\|hair --mesh <fit> --out <p> --image <asset png> --raw <raw> --fit-json <fit.json>` | convex bumps between concave valleys (smooth meshes have no sharp creases); one role per mold from the image (seen faces only) gated by geometry: belt = top 12 % band, ornament = proud front blob, unseen ⇒ outer; hair: light-voted mold = the hair TIE |
| pool | `scripts/aggregate_hair.py --out spec/hair_grammar_learned.json …` · outfit pooled into `spec/outfit_grammar_learned.json` | p10/p50/p90 per sex × region / garment × role |

Learned (spec files hold the full ranges): male side locks 29–32 × 6.4 cm (w 3.1, L/W 2.2), fringe 3.3 cm, back 5.3 cm; female locks longer/thinner
(back 45–52 × 6.9 cm, L/W 3.1; fringe 9.5 cm); ponytail 19–25 cm, droop 36–44°, root at 0.56 head height, 12–13 cm behind, max r ≈ 4.3 cm,
13–15 lock tips, tie = one ring mold at the root. Skirts: 8–10 hem teeth, depth 4–11 cm, spacing 30–45°, flare 1.23–1.32; outer ≈ 71–73 % area,
lining 12–15 % (lower 40 %), belt band top 0–7 cm, ornament 5.5 cm tall standing 6–9 cm proud at the front. Top: 6 teeth 2 cm, light trim on the upper rim.

## SPECS (v1.0, 25/10/2026) — what a builder must reproduce
| spec | file | gates |
|---|---|---|
| chunky primal spiky hair | `spec/SPEC_primal_spiky_hair.md` + `.json` | analyze_hair.py stats inside learned ranges, flow, blade, coverage, budget |
| chunky primal ponytail | `spec/SPEC_primal_ponytail_hair.md` + `.json` | analyze_ponytail.py, taper, one tie mold at 0.2–0.4, behind the head |
| ⛔ ponytail ON the head (Boss 25/10 ×2 «nữ tóc đuôi chưa sát với đầu») | `scripts/measure_tail_attachment.py --hair <glb>` exit 1 when the tail root (head-facing quarter) or the tie floats > 3 mm off the hair; `build_ponytail_hair_v5.py` moves tail + tie as one piece toward the skull until it passes and runs the gate as its last step (rc) | v4 = 17.7 mm gap → rc 1; v5 = 0 mm → rc 0 |
| primal body anatomy (T zone, ears → hair roots, crotch concavity m≠f, lower pec, breast, glutes, trapezius, clavicle, spine, forearm→wrist, calves) | `spec/SPEC_primal_body_anatomy.md` + `.json` — `analyze_anatomy.py`, eyebrows `eyebrow_fitter.py` (7 control pts → raycast + surface-normal offset, each side cast on its own half; report json) | brow CENTRE on the socket rim, skin gap ≤ 1.5 mm between sections, 0 buried, both sides gated (rc=1) |
| layered torn primal outfit | `spec/SPEC_primal_torn_layered_outfit.md` + `.json` | hem, two tiers + lining in the lower tier, belt ring + ornament, role areas, clearance |
Previews for Boss: `render_turnaround_blender.py` + `compose_white.py` (coloured, lit, WHITE background, no wireframe — Boss 25/10).

## Look vs gates (Codex audit 25/10/2026, `spec/audits/`)
- Statistics from generated teachers never override the official sheet. Sheet overlays and IoU are diagnostic only, never a gate.
- Boss accepts the look by eye on lit, white-background turnarounds with head and skirt crops. Machine gates prove fit only: budget, contact, clipping, roles, skin showing.
- Every procedural asset is exported as named role geometries with their own materials. Parts the fitter may bend end in `__movable`.
- Previews keep authored shading: `render_turnaround_blender.py --keep-materials` no longer forces smooth shading or clamps roughness.


## ⛔ Skirt side lumps (Boss 25/10 ×2 «lòi ra bên đùi trái» · «Bên trái váy nữ V4 đang bị lồi ra một khúc kì kì»)
`python3 scripts/build_skirt_bulge_trim.py --skirt <skirt.glb> --side L --check` exit 1 when a lining vertex stands > 15 mm beyond the median radius of its ring (±25°, ±3 cm). Fix = same script without `--check` (+ `--out`): pulls only the LINING back to ring median + 6 mm on that side; never the torn tiers (pulling them in crossed their faces: tan patches on the dark tier, holes at the back). Female v4 → rc 1, v5 → rc 0. The right half (from v2) still reports hidden lining lumps — not visible in the turnaround, left as is.


## Female bandeau rope + back hair contour (Boss 25/10)
- «Dây belt áo của nữ cho nhỏ size lại … lòi ra ngoài từ chỗ nách ra tới vai»: `scripts/build_bandeau.py` rope 7–10 mm, 16 stations, laid on the REAL skin section outside the front (the convex hull bridged the armpit 3.3 cm off the skin); builder exits 1 when the rope's inner side stands > 10 mm off the skin (reverse `THU_FAT_ROPE=1` → 2.3 cm, rc 1). v6.
- «Chỗ tóc sau lỗ tai đang bị vuông góc cho nó tròn tự nhiên cong xuống»: `scripts/build_ponytail_hair_v6.py` (back mass tips down a 1−cos arc onto the neck, cap lifted under it); `--check <hair.glb>` exits 1 when the nape tips are < 30 mm below the tips behind the ears (v5 flat cut 1 mm → rc 1; v6 54 mm → rc 0).
- «vệt tà áo trên đang nhô ra bất bình thường nó phải ôm vào ngực chứ - chỗ 2 bên nách» (×2 with the rope): `build_bandeau.py` bridges only between the breast apexes and hugs the real skin section from each apex round to the back; the vertex-containment step pushes only the NEARER row (raising both rows pushed the top 1.7–2.8 cm out). Builder exits 1 when the top row stands > 13 mm off the skin between 30° and 120° (reverse `THU_RAISE_BOTH_ROWS=1 THU_HULL_BRIDGE=1` → 23.7 mm rc 1; v7 11.9 mm rc 0).
- «vẫn còn một vệt nhọn nâu áo V7 bên nách trái nhìn từ phía trước» (×2 with «vật nhọn lòi ra nách»): under the arm the arm-less section has no skin, so the hull bridged 1–2 cm wider than the neighbours. `build_bandeau.py` now blends band rows (ARM_GAP_PAD 4 mm) and rope stations (ROPE_GAP_PAD 15 mm, keeps the underarm skin covered) across that gap; builder exits 1 when the FRONT-view outline forms a point > 5 mm past the outline 1.6 cm above/below (reverse `THU_ARM_GAP_HULL=1` → 8 mm rc 1; v8 4 mm rc 0).
- v9 flat strap (Boss 25/10 «dây dẹp v9 ổn, sửa tiếp chỗ lọt dưới nách khi cử động»): the 2.2 cm spike was the BREASTS (containment raised one station) → per-row constrained least-squares bridge after containment (≥ contained radius, ≤ 6 mm over neighbours, side stations ×10 cost); reverse `THU_NO_BRIDGE=1` → 2.2 cm rc 1. Motion: `rig_body_blender.py` hands an upper layer's clavicle/upper-arm share to CHEST (their parent) instead of renormalising onto spine — twist 12.5 → 0 mm, lean_back 7.3 → 0.3 mm; reverse `THU_TOP_ARM_TO_SPINE=1`. Still open: walk 5.75 mm / 3.2 %, run 12.3 mm (same for v8, whose rig never reached the pose test) — the body's own armpit skin rides the upper arm down to y 1.17; tried and rejected: keeping arm weights on the top (v8 got worse, strap tore 6.4×), weight smoothing (twist back to 5 mm), gap room 6–12 mm (more clipping).
- Body weights + skirt (Boss 25/10 «sửa trọng số da nách của cơ thể … khi chạy lòi da ở bụng hay đùi»; Codex 4 rounds): `rig_body_blender.py` `armpit_ownership()` — the old cleanup only ran BELOW FR armpit − 0.01 H while the fold measures 1.127 m (arm–torso gap closes there) and every bad vert sat 2.5–9.5 cm above it; geodesic torso/arm seeds → continuous ownership, interface bias 2 cm, clavicle+upper-arm share fades over 5.5 cm with 10 masked smoothing passes, breast clavicle ≤ 0.10, removed share → chest (reverse `THU_ARMPIT_OLD=1`). `skirt_by_vertex()` — ONE thigh field shared by every skirt layer (per-tier gradients let the tan tier poke through), hem 0.9, lateral 5°→35°, midline keeps 0.4 split L/R over ±4 cm, ornament rigid (reverse `THU_SKIRT_OLD=1`). Check with character-fitter `clip_check_blender.py` + videos; final asset = body masking (character-fitter SKILL §Old clips).

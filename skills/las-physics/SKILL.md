---
name: las-physics
description: Physics for LAS / settler scenes in Blender 5.2: things that FALL or TOPPLE (tree felling, posts, doors, crates) with a believable hinge phase plus Bullet rigid body for landing, bounce and settle, baked to keyframes, with machine gates. Read BEFORE animating anything that falls, breaks or collapses.
---

# LAS physics (Boss 22/10/2026: «Cây ngã physics phải hay - giờ là physics skill cho project LAS»)

Module: `scripts/vat_ly.py` (import with `sys.path.insert(0, ~/.hermes/skills/creative/las-physics/scripts)`).
Worked example: `~/projects/GameDev/anim_settler/chop_tree_scene.py` (5 chops → tree breaks → physics fall → fade → carry log).

## Recipe: an object that topples about a hinge
1. **Mass from the mesh**: `khoi_luong([(obj, density), …])` uses signed tetrahedra and returns (m, COM, inertia about the COM).
   Use a density per part: green wood 650 kg/m³, canopy/leaf mass ~60 kg/m³ (mostly air).
2. **Origin at the COM**: call `dat_goc_trong_tam(obj, c)`. Bullet treats the object ORIGIN as the centre of mass.
3. **Hinge phase, solved analytically**: `nga_ban_le(...)` integrates I_h·θ'' = a·((c−h)×m·g) with RK4.
   - The initial push is ω0 = 1.35 × `omega_toi_thieu()`, the minimum ω that lifts the COM over the hinge.
   - The hinge sits on the REAL edge of the support, measured from the mesh. A tapered trunk has r = 0.181 at the cut, not R = 0.20. A hinge 15 mm off the edge digs the butt 6 mm into the stump at release, and Bullet kicks it back.
   - Release at ~58°. That is where hinge wood snaps in real felling. Releasing at 24° makes the butt slip backward toward the chopper (real kickback, μ too low).
   - The phase keys 2 frames PAST the release frame. Bullet reads a kinematic body's velocity from motion inside the substeps up to the switch; if the keys stop at the release frame, ω dropped from 0.757 to 0.179.
4. **Bullet phase**: `bullet_tiep(obj, f_tha, f_end, [ground, support], m)`.
   - The object is ACTIVE with a CONVEX_HULL shape; `animated` is turned off at the release frame.
   - A small PASSIVE (stump, step) must be CONVEX_HULL. MESH is a zero-thickness shell; the tree fell 0.6 m straight through the stump.
   - Damping (0.4, 0.8) stands in for leaves and branches dragging on the ground. A round canopy otherwise keeps rolling.
   - The result is baked to keyframes, so it is deterministic and can fade.
5. **Gates**: `cua_do()`. The scene script exits 1 if they fail.

   | gate | what it checks | threshold |
   |---|---|---|
   | ① | ground penetration | ≥ −20 mm |
   | ② | settled over the last 12 frames | < 4 mm/frame and < 0.6°/frame |
   | ③ | falls the right way | cos ≥ 0.8 |
   | ④ | never overlaps the character | BVH overlap in 0 frames |
   | ⑤ | phase hand-off | ω jump ≤ 20 % |

   Measured caught failures: cos −0.41, hand-off 76 %, drift 94 mm/frame. Pass, v2–v4: 0 mm, 1.5 mm/frame, cos 1.0, 0 frames, 15.6 %.

## Other helpers
- `rung_tat_dan(obj, pivot, axis, f, A_deg, fps, f=2.0 Hz, tau=0.4 s)`: damped shake on a non-final hit (hits 1–4 of a tree).
- Wood chips (ballistic, land and stay) are in `chop_tree_scene.py`.

## Breakable look (tree)
- The notch deepens 25/45/62/78 % R. It is cut with an EXACT boolean wedge (`material_mode=TRANSFER`) facing the chopper; the top slopes 40°, the bottom 12°.
- Cut faces, as Boss asked «màu ở trong ruột»:
  - sapwood: cream (196,164,108);
  - heartwood: a coaxial 0.45R core, deep orange-brown (150,88,48) converted sRGB→linear, otherwise it washes into the sapwood;
  - bark rim: brown;
  - bright splinters on the hinge side.
- ⚠️ `obj.copy()` SHARES the action. Hide/show keys on the stump leaked onto the notch-4 trunk (its core reappeared as a pole after the break). Call `animation_data_clear()` on every copy.

## Sound
Real Mixkit only, never synthesized; sources are listed in `anim_settler/sfx/mk/SOURCE.txt`.
- Every chop uses ONE sound, `nhat_4` (Boss 22/10: «Tiếng chặt thứ hai nghe giống có máy cưa… xài 1 tiếng thôi… Tiếng thứ 4 xài chung»; Mixkit 796 has a chainsaw bed).
- Break = crack 2943. The trunk creaks with 178 pitched down ×0.78. Landing = 3141 + leaves 751.
- `merge_audio.py <scene dir>` reads `markers.json` (hit / break / landing frames).

## BOUNDARY LAYER for every finished asset (Boss 22/10/2026: «Toàn bộ body của nhân vật hay bất cứ vật thể nào cũng phải set boundary layer sau khi chốt xong modeling finished của vật thể đó»)
Once an asset's modeling is final, it ships with a collision shell, and every contact/penetration gate measures against that shell.
Never use hand-typed radii: the guessed head radius was 0.095 m, the measured head+hair shell is 0.110 m.
- **Characters**: `scripts/shatter.py::vo_nguoi(rig, meshes)` fits one capsule per deform bone from skin weights ≥ 0.5 (body + outfit + hair)
  at rest, stored in bone space. It is generated automatically in `animate.py` right after skinning (`<out>/body_shell.json`; print `VO_NGUOI`).
  At any pose `vo_the_gioi()` gives world capsules; `kc()` / `kc_tru()` give the signed gap (negative = penetration).
  - Known coarse spots: the tunic flares the thigh capsules (0.14 m) and the open fist inflates hand capsules (0.064 m). Read them as conservative.
- **Static props (lpms)**: `lpms.py render` writes `shatter.json` (one convex hull per part) and gate «vỏ va chạm». No shell = the asset is not finished.
- **Scene use**: `chop_tree_scene.py` head clearance ⑥ now uses the body shell (gap 14.7 mm with 3 logs).

## Recipe: rock / brittle object SHATTERS after N hits (built 23/10/2026, `~/projects/GameDev/anim_settler/smash_rock_scene.py`)
- Reuse the approved tool loop through an NLA strip (`repeat=N`, `extrapolation=HOLD`, `frame_end`=one cycle) — never re-key the motion.
- Fracture = bmesh `bisect_plane` + `holes_fill` along planes THROUGH THE IMPACT POINT (2 vertical + 1 horizontal ⇒ 4–8 convex chunks); fill faces get a lighter "inside" material.
- Cracks for hits 1..N-1 = the SAME bisect lines (crack where it will break), revealed by radius from the impact point, offset 4 mm out of the surface.
- Each hit: sparks (emissive, ~8 frames), chips (ballistic, clamp to the ground by the REAL radius after jitter — nominal radius sank 14.7 mm), dust (smooth ico subdiv 3, GROUND colour, alpha 0.3→0 over 18 f; white dust reads as solid cotton balls).
- Final hit: chunks get kinematic velocity keys from F-3 to F+2, `kinematic` off at F+1, Bullet convex hull, passive support rocks, bake → keys.
- Gates (exit 1): chunk ground ≥ −20 mm · last-12-frame drift < 4 mm · BVH 0 against the person · chips ≥ −5 mm · ≥3 chunks.
- Sound: `merge_audio_rock.py` — one `cuoc_da` per hit, + `vo_da` on the break, + `lan_da` on landing.

## Soft attachment that must not pass through the body (straps, belts, ropes, cloth bands) — Boss 23/10/2026: «Tại sao thân người vẫn chưa set là vỏ ko thể xuyên thủng để dây ôm vào tự nhiên hơn?»
Measuring with the boundary shell is not enough — ENFORCE it: skin the attachment to the body (Armature), then Shrinkwrap `wrap_mode="OUTSIDE"` (only pushes vertices that are inside) with offset 6 mm onto every outer body layer, limited by a vertex group so the ends stay attached to their anchor. Sample the curve finely (segments ≈ 1.5 cm) so faces do not bridge low-poly ridges. Gate on signed penetration depth, not triangle-pair counts (pairs also count harmless edge crossings). Example: `anim_settler/basket_storage_scene.py`.

## Gate-writing traps found 23/10/2026
- Signed distance by nearest-face normal is unreliable inside concave creases (pec fold, armpit): a point outside can read "inside". Cross-check with a close-up render before trusting a small depth.
- Blender `Matrix.Rotation(+θ, 4, "X")` turns +Z toward −Y. Write the sign in the comment and test it by sweeping (basket tilt was backwards: top gap 119→169 mm when "fixing" it).
- Debris/chips: clamp to the ground by the REAL mesh radius after jitter; give dust the ground colour (white dust = solid cotton balls); gate "every effect object has a material".

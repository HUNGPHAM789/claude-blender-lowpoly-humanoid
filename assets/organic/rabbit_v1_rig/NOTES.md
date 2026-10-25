# rabbit_v1_rig: rigged and animated low-poly rabbit

Source: `../rabbit_v1/rabbit.glb` (read only, never modified). Built 22/10/2026 with Blender 5.2.2 LTS, slotted actions.
To rebuild everything: `blender -b -P build_rig.py`, then `blender -b -P verify_glb.py`. Renders: see "Reuse" below.

## Files
| file | what |
|---|---|
| `rabbit_rigged.glb` | skinned mesh, 2 bone-parented eyes, 23 joints, 4 glTF animations (Y-up) |
| `rabbit_rig.blend` | armature `rabbit_rig`, mesh `rabbit_body`, eyes `rabbit_eye.L/.R`, 4 actions (fake user) |
| `rabbit_hop.gif` / `rabbit_idle.gif` | 640 px isometric EEVEE loops at 24 fps (1.6 MB / 1.2 MB) |
| `rabbit_hop_contact_sheet.png` | 8 hop frames (f0, 2, 4, 6, 9, 11, 13, 15), labelled |
| `checks.json` | per-frame deformation numbers for every action, weight stats, solver logs |
| `glb_reimport.json` | what came back when the GLB was re-imported |
| `build_rig.py` / `render_loops.py` / `make_sheet.py` / `verify_glb.py` | the pipeline |
| `work/` | rendered frames, the diagnosis scripts (`diag.py` = most stretched edges, `diag2.py` = volume per bone, `axis.py` = rotation-sign check) |

`scripts/probe.py` was already in this folder before this run started (05:16). Not mine, left alone.

## Mesh prep
The GLB body arrives as 4 per-material pieces with unwelded per-face verts (4,650 verts). They are joined and welded (`remove_doubles` 1e-5), which gives back the 852-vert / 1,700-tri closed mesh with the 4 materials kept. Flat shading. Eyes get transforms applied, then are **bone-parented to `head`** (rigid, no skin). Blender space: Z up, the rabbit faces −Y, its left is +X (so `.L` = +X).

## Bones (23; 22 deform + `root`)
`root` (non-deform, at the floor origin, points +Z) → `pelvis` → `spine` → `chest` → `neck` → `head` → `ear_1.L/R` → `ear_2.L/R`
`chest` → `front_upper.L/R` → `front_lower.L/R` → `front_paw.L/R`
`pelvis` → `thigh.L/R` → `shin.L/R` → `foot.L/R` (long foot, hock to toes); `pelvis` → `tail`

The joint positions come from `plan_rabbit.json` masses mapped to mesh space (scale 1.09186, the normalise factor in `rabbit_report.json`; plan +Y → Blender −Y). The ear roots and tips are measured from the mesh (top vertex on each side). The thigh runs from the hip down and forward to a knee inside the haunch. The shin runs back to the hock, and the foot runs forward along the floor.

**Roll convention:** every bone's local X equals world +X. So `rotation_euler.x` (degrees in the scripts) has one meaning on every bone: + turns up → forward(−Y) → down → backward. A leg pointing down swings backward, and the head pitches nose-down. I checked this numerically with `work/axis.py`. `root` pose loc.y = world up and loc.z = world forward.

## Weighting
1. Automatic weights (heat, `ARMATURE_AUTO`) **worked** with no failures: 0 unweighted verts and every deform bone used. But heat bled leg weights onto the belly and across the midline (for example, `front_upper.R` weights on +X belly verts). That produced 5–23× edge stretch.
2. Cleanup: a limb bone's weight is removed from verts outside its capsule. Radii are front 0.045–0.06, thigh 0.10, shin 0.09, foot 0.065, tail 0.08 and ear 0.06 m. `.L` weights are removed from x < −1.5 cm and `.R` from x > +1.5 cm. Verts left empty go to the nearest same-side bone. This stripped 498 weights.
3. Laplacian weight smoothing in Python (0.5 × 3 passes; `vertex_group_smooth` fails its poll in background mode), keeping the midline rule.
4. `vertex_group_clean` 0.01 → `limit_total` 4 → `normalize_all`.
**Result: 852/852 verts weighted (≥1 influence), max influences = 4, normalized.**

## Actions (24 fps; the last key equals the first, so play `[start, end)` or let the engine treat end == start)
| action | frames | content |
|---|---|---|
| `hop` | 0–18 | rest → crouch (3) → push-off, hind on floor (6) → airborne +16 cm, ears trailing, hind feet trailing (9) → front-paw landing, nose down (12) → hind feet land (15) → recover (18). **Root travels 0.36 m forward (−Y)**, so the cycle repeats seamlessly with root motion |
| `hop_inplace` | 0–18 | the same poses with no forward root travel (vertical root motion kept) |
| `idle` | 0–48 | 2 breaths (chest/spine scale +2.5 % / +1.5 %, period 24), left-ear twitch f20–26, head turn +9° then −6° yaw |
| `sniff` | 0–24 | neck forward, 4 fast nose bobs, ears perk |

Two automatic solvers in `build_action`:
- **Contact / pelvis-pitch solver.** Each hop key gets an extra pelvis pitch from bisection so that the lowest front-paw vert minus the lowest hind-foot vert hits a target. Targets: f3 0, f6 +4 cm, f9 −3 cm, f12 −6 cm, f15 0. Contact regions are taken from dominant weights (148 hind-foot verts, 86 front verts). Then the root height is set so that the named contact region sits at z = 0.
- **Floor clamp.** In-between frames where FK interpolation pushes a limb under the floor get an extra root-height key: hop f4 +2.4 cm, f5 +5.6 cm, f13 +6.8 cm, f14 +0.3 cm.

## Measured deformation (evaluated mesh, every frame; `checks.json`)
| action | max abs volume change vs rest | max edge stretch | min edge ratio | NaN frames | zero-length edges |
|---|---|---|---|---|---|
| hop / hop_inplace | **11.3 %** (f9, airborne) | 5.41 (f9) | 0.22 | 0 | 0 |
| idle | 2.83 % (breath peak) | 1.69 | 0.83 | 0 | 0 |
| sniff | 0.08 % | 1.26 | 0.81 | 0 | 0 |

Rest volume is 0.07253 m³, the same as the source report. **Ground contact at stance frames (lowest vert of the named region, cm):** hop f0 0.0 · f3 0.0 · f6 (hind) 0.0 · f12 (front) 0.0 · f15 0.0 · f18 0.0. Idle f0/12/24/36 all 0.0, and sniff f0/9 0.0. All are within ±1 cm.

Which bones add volume (`work/diag2.py`, f9 values one at a time): thigh +4.4 %, front_upper +2.9 %, foot +2.4 %, shin +1.3 %. Pelvis pitch, spine, ears and tail add about 0 %.

## GLB round trip (`verify_glb.py` → `glb_reimport.json`)
Re-import gives 1 armature, **23 bones**, and **4 actions: hop 0–18, hop_inplace 0–18, idle 0–48, sniff 0–24**. `rabbit_body` is skinned (5,098 verts after the glTF split by material and flat normals). The eyes come back BONE-parented to `head`. The extra `Icosphere` object is the importer's bone-display shape and is not part of the asset.

## Known problems
- **Edge stretch up to 5.4× in the airborne pose.** It sits in the crease between the folded hind foot and the haunch, and between the foreleg and the haunch. The mesh was built seated: those folds are short edges that have to open when the legs extend. It shows as a spiky trailing heel at f8–10. Smaller leg swings would remove it, but the hop would read weaker. A real fix is to remodel the leg in an extended rest pose, or add corrective shape keys.
- **The hop is stylized**, not a measured rabbit gait. The pitch solver tilts the body nose-down by 29–40° at f6/f9/f12, so the hop reads as a forward "dive".
- **Small foot slide.** Feet slide about 4 cm during push-off (root 0→0.05 m while the hind feet are planted), and the hind feet hover up to about 7 cm on the floor-clamp frames f13–14. There is no IK: everything is FK plus a root-height solver.
- The volume aim (≤12 %) is met with only 0.7 % to spare. Any bigger hind-leg swing pushes it over.
- The renders use a camera that follows the root's Y position, on a checker floor with a 0.18 m period, so the hop GIF loops without a jump.

## Reuse
- **Game engine:** import `rabbit_rigged.glb` and use `hop` with root motion (root bone `root`, forward −Y in Blender = +Z in glTF), or `hop_inplace` with your own mover. Loop clips as `[0, end)`.
- **New action:** add a `build_action("name", length, {frame: {"bone.LR": (rx, ry, rz)}}, travel, contact, lift, scales, pitch_target)` call in `build_rig.py`. `.LR` mirrors to both sides. Then rerun the build; checks and export are automatic.
- **Render:** `blender -b rabbit_rig.blend -P render_loops.py -- <action> <outdir> 640 [f1,f2,..]`. Then run ffmpeg palettegen/paletteuse to make the GIF (the command is in this session's history: `-framerate 24 -i f%03d.png ... -loop 0`), and `python3 make_sheet.py` for the contact sheet.

# LPM Primal Human — Eight-View Curated Reference Specification v1.0

**Date:** 2026-10-24. **Source:** eight user-supplied reference PNGs, ordered below. **Status:** photographed-screen reference analysis, NOT a 3D mesh audit. **Use:** a NEW `primal-detailed-settler` profile for SURVIVAL JOURNEY, not a replacement for the canonical LPM `faceless-humanoid` v2.7. License/author of pictured reference model not established: do not redistribute the images or clone exact mesh topology commercially without authorization. Numbers are estimates or proposed recreation targets until original mesh measurements exist.

## Reference images and evidence type

| ID | Image | Mode/view | Shows / can reliably constrain |
|---|---|---|---|
| R01 | `01_rig_front.png` | Front, partly transparent body, joint dots/skeleton | Bone ordering, projected joint heights and symmetry; **not** skin topology |
| R02 | `02_rig_side.png` | Side, partly transparent body, joint dots/skeleton | Head/neck alignment, torso and knee/ankle chains, posture, forward lean |
| R03 | `03_skin_weights.png` | Front, RGB weights | Smooth skin-bound deform regions; NOT true bone names or per-bone numeric weights |
| R04 | `04_wire_front.png` | Front wireframe, clothing and head | Body/garment contours, loop spacing and high-density areas |
| R05 | `05_wire_side.png` | Side wireframe | Chest/belly/glute/face projection, boot toe and garment thickness |
| R06 | `06_wire_back.png` | Back wireframe | Shoulder blade and spine meshes, back mantle, hem, cuffs |
| R07 | `07_render_front_3quarter.png` | Color game-model preview | Hair/clothing palette, beard, eyes, earrings? visible no reliable jewelry, skin colors, shadows |
| R08 | `08_render_back_3quarter.png` | Color game-model preview | Mantle and skirt overlap, boot and hair silhouette, rear seams |

All eight screenshot PNGs have now been committed to the public LPM repository at `references/01_...` through `references/08_...`, preserving their original uploaded bytes. An extra screenshot of the axe is `references/09_primal_axe_reference.png`. They are user-provided reference images of **unverified third-party authorship/license**, and must NOT be inferred to have become MIT-licensed by residing near MIT code. The original model/rig source files were never supplied.

## Calibration and uncertainty

- Chosen gameplay height: **H = 1.80 m**, matching the canonical LPM human anchor. User images have **no physical scale marker**; all metric measurements below are **proposed output dimensions** derived from proportions, not recovered world-space units.
- R04 front-wire silhouette: near top **y≈19 px**, soles **y≈798 px**, total projected **779 px** at 426×820 PNG. This implies approx **433 pixels per meter** *only at the chosen 1.80m normalization*, under near-orthographic projection.
- R04 front pelvis/limb overlap, hair spikes, ankle cuffs, and facial beard occlusion add **±7–20 px** visual uncertainty. Perspective foreshortening, clothing thickness and off-axis camera cause further uncertainty; do not infer hidden volumes from one photo.
- All screenshot X positions use left image edge as 0; Y increases downward. Orthographic proportions from R01/R04/R06 can be compared relatively. R02/R05 side projection cannot recover torso width; R03 heat maps show influences but do not yield exact numeric weights.

### Image-space guide: R04 `04_wire_front.png` (426×820)

| Landmark/visible envelope | Approx pixels X or XY | Fraction of stature | Metric *design target* | Confidence |
|---|---|---:|---:|---|
| Hair peak to soles | y 19 to 798 | 1.000 | 1.80m | High pixel / chosen scale |
| Hair crown → lowest beard | y 19–163 | 0.185 | 0.33m incl beard/hair | Med; hair/cloak overlap |
| Skull/hair maximum width | x 164–281 | 0.150 | 0.27m incl silhouette | Med |
| Neck/collar span | x 164–287, y 147–198 | 0.158 width | collared garment max 0.28m | Low; scarf included |
| Overall upper shoulder envelope | x 98–356, y 180–251 | 0.331 width | 0.60m incl deltoid/garment | Med |
| Ribcage/chest width | x 119–345, y 240–315 | 0.290 width | 0.52m incl arms overlap | Low |
| Natural waist/upper belt | x 141–311, y 374–416 | 0.218 width | 0.39m garment/belt region | Med |
| Hip/skirt upper silhouette | x 117–343, y 438–507 | 0.290 width | 0.52m cloth skirt incl motion | Low |
| Crotch / skirt hem split | y≈561 | 0.695 from top | 0.55m above soles | Med, partly garment |
| Elbow envelope | left x~79,y~334; right x~362,y~335 | 0.405 down | target elbow 1.08–1.18m high | Med |
| Wrist cuff | left x~48,y~439; right x~388,y~438 | 0.539 down | target wrist 0.80–0.90m high | Med |
| Left/right knee cuffs | x~151/288,y~650 | 0.810 down | target knees 0.35–0.50m high | Med, cuff not joint center |
| Heel/toe lower silhouette | left x~68–171; right x~271–351,y~738–798 | foot length projected | boot length 0.30–0.33m | Low |

**Important:** Some X envelopes include overlapping sleeves, skirt and accessories. They are not naked-body widths. No topology polygon count is inferable from a screenshot; counts below are **budgets for recreation**.

## Coordinate and socket authority

- Sculpt / assembly: **Z up**, meters, feet on **Z=0**, forward is local **−Y** (current LPM convention), left/right use unmodified LPM `L/R` names.
- glTF export: **Y up**, exactly one Z-up→Y-up transform; test file has vertical human after import.
- World origin pelvis/root at horizontal center, ground origin under feet. A skeleton root `ROOT_WORLD` at ground and `hips` joint at proposed Z≈0.97m.
- Existing LPM sockets retained for compatibility: `SOCKET_dau`, `SOCKET_cam_L/R`, `SOCKET_ban_tay_L/R`, `SOCKET_ban_chan_L/R`, `SOCKET_lung`, `SOCKET_hong_L/R`; add `SOCKET_headHair`, `SOCKET_beard`, `SOCKET_scarfFront`, `SOCKET_clothWaist`. New sockets **must not** break old names.
- Canonical base remains faceless. This detailed-body line may introduce eyes, beard, nasal forms and separate digits with new gate/budget profile, using opt-in `profile: primal-detailed-settler`. The old LPM head faceless gate must **not** be weakened to accommodate this different asset.

## Complete build targets by body part (all dimensions proposal, 1.80m avatar)

### 1. Head and facial construction

- **Skull:** top Z 1.78–1.81; lower jaw/neck transition Z 1.53–1.58. Cranial width 0.195–0.225m; skull depth (nose excluded) 0.205–0.235m. Side silhouette R05 projects a high forehead, strong nasal wedge and jaw that tapers into beard. Human eyes look in forward −Y, center Z≈1.68–1.72m; brow ridge gives readable shadow at game distance.
- **Eyes:** two shallow sockets and dark eye surfaces, not cartoon spherical eyeballs; each eye width ~0.028–0.034m, spaced ~0.055–0.070m center-to-center. Keep eyes as separate flat-colour surfaces; screenshot does not prove eyelashes/pupil geometry.
- **Nose:** faceted wedge connecting nasal bridge to projecting nose tip, projection ≈0.025–0.045m beyond facial plane; 3–5 major facets, avoid a single smooth bulb. Nose base Z≈1.61–1.66m. Wire front R04 demonstrates faceted nose/tip and geometric moustache beneath.
- **Ears:** side ear spans 0.045–0.065m high, offset 0.010–0.025m from skull; can be partly covered by long hair. Use 5–9 facets/ear, soft pink inner patch at most 2–3 triangles.
- **Beard/moustache:** dense dark brown wedge beard under chin, projection 0.04–0.075m from jaw; tip near Z 1.50–1.55m; layered 3–7 angular clumps with front and side profile. Mustache consists of two angled lobes shielding upper lip but never covering both eyes or full nose. R07 shows a prominent hanging beard and eyebrows.
- **Hair:** black/dark espresso rugged hairstyle, ~12–20 asymmetric pointed clumps, with thick sideburns and crown spikes. Hair projects ≈0.025–0.06m above skull; back reaches upper neck. **Different from v2.7 canonical helmet-like origami hair**, keep hair a replaceable layer. R07/R08 confirm large jagged readable silhouette, no hair helmet.
- **Face palette proposals:** skin base `#E9AA9F`, shadow `#C9857C`; beard/hair `#302627`–`#47312F`; eyes/brow darker. Sample in screenshot is light-dependent; do not treat these as measured texture RGB.

### 2. Cervical spine, scarf, upper back

- **Neck:** center vertical Z≈1.49–1.61m; diameter ~0.13–0.15m; chin/beard overlap head-front; trapezius transitions shoulder collar without abrupt block geometry.
- **Scarf/primitive mantle collar:** garment as 2–3 broad connected faceted loops around collarbones and rear neck. Front opening exposes upper pectorals, back forms triangular drape to mid scapula. Collar outer thickness 0.022–0.045m; dark charcoal/brown. R06/R08 rear drape extends from base-of-neck Z≈1.55 to middle of upper back Z≈1.24–1.31; tip should not float away from back >0.02m (unless physically simulated).
- **Scapular silhouette:** R06 has clear descending V-back cloth panel and a straight line on spine; shoulder joints separate from collar attachment to prevent cloth deformation spikes.

### 3. Thorax, abdomen, waist, hips

- **Shoulder-to-shoulder bare body width:** 0.51–0.57m; garment/sleeves could expand to 0.60m. Broad muscular but non-bodybuilder proportions.
- **Upper torso Z:** shoulder/clavicle ~1.48–1.56; chest line 1.30–1.45; waist at 1.00–1.12; pelvis crest 0.92–1.03. Torso depth at chest 0.255–0.320m, at waist 0.205–0.275m. Maintain continuous stomach side curve rather than separated convex blocks.
- **Torso profile:** R05 side silhouette: chest projects 0.02–0.045m in front of tummy; abdomen slightly forward vs waist, upper back bows into shoulder blades. Build with oval/rounded-square cross-sectional rings, 8–12 points per ring, 9–12 vertical rings. Ribcage tapers to navel then widens at iliac crest; no 'three stacked boxes'.
- **Upper chest emblem:** front sternum has a small faceted dark hanging pendant, ~0.055–0.07m long, 0.03–0.05m wide, below mantle collar; R07 shows one central diamond-ish polygon. Keep a separate replaceable prop/socket; do not sculpt it into torso.
- **Belt:** thick rough pale bone/rope ring at Z≈0.95–1.02m, circumference follows waist/hip section not a perfect circle. 3–5 small irregular knots/segments and a central hanging dark flap. Band thickness ~0.04–0.065m.
- **Pelvis:** hip joint centers at Z≈0.92–0.97; femoral-head x offset ±0.105–0.145m. The screenshot does not reveal naked buttocks; defer to LPM canonical body reference for posterior musculature under cloth.

### 4. Arms and hands

- **Deltoids:** angular shoulder cap from clavicle ~1.50 to upper arm 1.40m; arm attaches at x≈±0.26–0.29m, Z≈1.45–1.50. Deltoid sphere-like block is NOT separately isolated from skin surface in render.
- **Humerus:** shoulder-to-elbow approx 0.28–0.33m, with a gentle taper; upper-arm max diameter approx 0.14–0.17m. Screenshot arms rest 8–15 degrees abducted, hands near the thigh.
- **Elbows:** Z≈1.06–1.16m neutral pose; bending must preserve a tapered wedge on posterior elbow, no disconnected shell.
- **Forearms:** elbow-to-wrist 0.25–0.31m, strong upper forearm taper toward wrist; diameter at proximal end 0.12–0.15m, at distal end 0.075–0.10m.
- **Wrists:** Z≈0.76–0.86 in rest pose; transition supports interchangeable wrist bracer. R07 one large dark bracer on screen-left arm, game character's right if orientation standard; avoid hardcoding anatomical side until source rig labels confirmed.
- **Hands:** palm length 0.095–0.115m, width 0.075–0.095m; separate thumb plus four finger digits or visually separated groups unlike canonical LPM mittens. Finger tip to wrist ≈0.17–0.21m. R04 close wireframe shows distinct finger sections; R07 render simplifies at distance. For game LOD1 may merge four fingers, but LOD0 needs two-hand tool pose/IK contact. Palm/finger loops near wrist/knuckles rather than uniform segments.
- **Grip compatibility:** map new detailed hand grasp to Ø32mm LPM tool handle at `SOCKET_cam_*`. Derive grip rotation from actual posed hand; keep contact ≤2mm penetration for clasp, <=0.010m non-grip clearances.

### 5. Legs, thighs, calves and feet

- **Femoral hip to knee:** 0.39–0.46m along limb; quad silhouette under garment broad near upper thigh, narrowing into knee. Pair x center ±0.14–0.17m.
- **Knee joint target:** Z≈0.43–0.53m; Screenshot R04 knee *fur cuff* visually near y≈650, not equal anatomical center! Distinguish actual knee pivot (likely immediately above top of boot shaft) from cuff center.
- **Lower leg:** knee to ankle length ~0.37–0.44m; calf thickness ~0.12–0.16m max, taper to ankle under high boots.
- **Boots:** thick dark leather, chunky low-poly toes and slightly raised heel. Boot total shaft rises to just under the knee (Z≈0.45–0.54m), opening ring cuff width ~0.20–0.24m and ankle width ~0.105–0.15m. Foot length ~0.28–0.34m and max toe width 0.12–0.16m; toe not a perfect rectangular cube. On R05 toe projects well forward of shin; in rear R08 shoes show compact heel and broad cuff.
- **Cuffs:** pale warm-gray fur/cloth ring at top of boots with irregular 8–12 angular facets; height ~0.055–0.090m. R04 wire rings have triangulated folds and layered lip. Keep ring centered on shin axis and seated onto boot mesh (no visible air gap).

### 6. Tunic/skirt, bracer and layered cloth

- **Lower kilt/skirt:** dark brown coarse cloth wrapping hips, falling from belt at Z≈1.00 to hem Z≈0.68–0.76. Two or more overlapping irregular fabric panels, unhemmed jagged corner silhouette. Front has center-left diagonal overlap and asymmetrical cut. R04 front and R06 back show broad planar polygons with more loops near waist and drape bottom.
- **Side/back drape:** R05 side view shows rear cloth trailing from waist to roughly upper thigh, and a forward strip separate from thigh contour. R08 rear skirt falls longer than front at one side. Cloth should hang with directional gravity; do not attach one rigid ring to thigh joints.
- **Wrist bracer:** dark leather cuff wraps forearm length ~0.15–0.20m, thickness ~0.01–0.025m. Bracer follows forearm bone, not hand bone; silhouette reads broad at proximal forearm.
- **Fabric profile:** matte nearly black-brown `#493F3D`; scarf `#5A4A49`; pale waist rope `#B9A58E`; dark boots `#453631`. Values are STYLE TARGETS, not eyedropper-certified source material.

## Rig / animation reconstruction

### Bone chain graph and approximate world-space joint Z (m)

```
ROOT_WORLD (0.00)
 └─ hips (0.96) ┬─ spineA (1.12) ─ spineB (1.29) ─ chest (1.41) ─ neck (1.54) ─ head (1.65)
                │                  ├─ clavicle.L/R ─ upperArm.L/R ─ lowerArm.L/R ─ hand.L/R ─ fingers (5 digits optional)
                │                  └─ optional scarf/mantle bones, from chest, NOT pelvis
                ├─ upperLeg.L (0.95) ─ lowerLeg.L (0.48) ─ foot.L (0.10) ─ toe.L (0.055)
                └─ upperLeg.R (0.95) ─ lowerLeg.R (0.48) ─ foot.R (0.10) ─ toe.R (0.055)
```

Caution: names above are new **semantic contract proposal**; 8 screenshots do not prove actual source file bone names. R01 shows pelvis root/hip center, two hip sockets, knee/ankle and symmetrical clavicle chains. R02 shows cervical alignment and shoulder depth, including a separate wrist/ankle articulation. R03 shows red/purple/green blended skin weights but does not expose exact channels; do not claim exact skin weights or paint colors map unambiguously to bone names.

### Practical skinning proposal with gates

- 4 influences maximum per vertex, weights ≥0 and sum to 1 ± 1e-4; unweighted verts count = 0.
- 80–100% weight on joint center for rigid bony props; skin shoulders use clavicle/upperArm/chest mix, elbow blend upperArm/lowerArm, knee blend upperLeg/lowerLeg, waist cloth pelvis/spine.
- Avoid extreme 180-degree rotations during skin test; check shoulder abduction 90°, elbow flexion 110°, knee flexion 90°, head yaw ±50°, full walking stride ±35°.
- Hair/beard separate mesh layers, parent to head bone. Scarf parent to upper thorax with supplementary cloth bones only if animated. Kilt weighted predominantly hips/spine, NOT knees; avoid pelvis fabric clipping at knee lift.
- Wrist/tool `SOCKET_cam_*` must follow hand joint and match 32mm cylindrical grip; left/right symmetry of the rig but intentionally asymmetrical outfits.

## Measured-look, budget and geometry gates (proposal)

| Gate | Method | Acceptance target |
|---|---|---|
| P01 scale | Imported GLB bounds and screenshot ratio | 1.80m ±1%, heels on Z=0 (authoring) / Y=0 (GLB) |
| P02 silhouette | front/side/rear renders side-by-side with R04/05/06 | no missing beard, boot cuff, skirt asymmetry or back mantle |
| P03 body volume | torso cross sections and ray intersection | one continuous main torso skin; no hard stacked torso blocks; no floating sleeves |
| P04 hair/beard | hard-edge visible clumps, penetrations | 12–20 hair clumps, beard 3–7 clumps, each visually detached from eyes/nose |
| P05 hands | closed grip with cylinder Ø32 mm | hand grips ≥75% circumference, solid collision tolerance ~2mm |
| P06 rig hierarchy | bone parent tests | stable pelvis-spine-head, two arm chains, two leg chains; no orphan bones |
| P07 skin weights | numeric vertex influences | all sums ≈1, max 4 joints, orphan vertices 0 |
| P08 deformation | prescribed animation poses | no inverted faces, folded elbow skin or neck clipping |
| P09 tools | prop sockets + full walk/axe/spear poses | handle stays in grip, head points away from body, tool collision checked |
| P10 art palette | same camera/light reference grid | skin/hair/leather/fur readable at isometric 150px avatar height |
| P11 topology/LOD | compare actual triangle counts from GLB, not screenshot | proposed LOD0 ≤4,500 tris; LOD1 ≤2,300; LOD2 ≤800 |
| P12 source traceability | per-reference ID and confidence labels | every dimension tagged image-estimated vs parameter-chosen vs actual mesh-measured |

## Differences from the existing LPM skill and implementation plan

| Area | Current canonical faceless LPM | This photo reference / new optional profile | Reusable lesson |
|---|---|---|---|
| Head | ≤80-triangle faceless gemstone | Full forehead/brow/eyes/nose/lips/beard | Keep faceless LPM locked; introduce `primal-detailed-settler` separately |
| Hands | Mitten with opposed thumb and grip gate | Individually separated fingertips visible in wire | Optional independent fingers at LOD0, mitten fallback LOD2 |
| Hair | Origami clumps above skull | Jagged chunky locks on brow/side/back | Add curve and silhouette/contact gates to hair subskill |
| Body | Continuous torso and separate convex limbs | Sculpted continuous wireframe shoulders/chest/abdomen | Retain section-table loft, extend shoulder blend profiles |
| Clothing | Simple shell tunic/dress | Asymmetric scarf, pendant, kilt panels, belt rope, forearm bracer, fur boot cuffs | Layer grammar with cloth hems and bone props |
| Rig | Socket-ready body; animation elsewhere | Full joint/weight views | Standardized humanoid joint map and deformation acceptance suite |
| Animation | Clips externally authored/tested | Weight map gives general influence hints | Validate mesh *while posed* and physical held-tool contact |

## Missing evidence / caveat

The eight reference pictures are **screenshots**, not a downloadable rigged model. Therefore this document does NOT know actual topology vertex count, triangle count, joint roll angles, bone names, bind matrices, accurate body depth in meters, or true per-vertex weights. Those require original FBX/BLEND/GLB and Blender inspection. Numeric proposals are actionable game-authoring defaults, not falsely claimed measured source data.

## Related asset study — user's primal axe

The requested axe reference features a curved blond timber handle (≈0.95m proposed), a dark asymmetrical chipped stone head (visual reference actually looks like **stone**, not ivory bone), and wide crossed brown leather lashings. The new source generator and GLB include a stone reference variant and also supplies a *bone axe* gameplay variant with the same canonical grip contract. Required gates: single-face-source primitive meshes, manifold solid parts, flat material semantics, ≤3k triangles, shaft Ø≈32–70 mm locally and LPM 32 mm grip, 4 or fewer material draw batches. Do not claim bone where visual reference clearly depicts dark stone.


## Per-view silhouette and rig annotation study (additional QA sheet)

This section expands the per-reference inventory above; each description is derived from the user-provided PNG, NOT an original rig scene export.

### R01 — semi-transparent front rig (481×820 px)

Approximate visible colored rig marker centers: head line `(233,88)→(233,154)→(235,195)`, paired shoulder dots `(141,222)/(330,217)`, paired upper-chest dots `(212,243)/(256,244)`, spine `(235,278)→(235,372)→(235,450)`, elbows `(115,342)/(353,340)`, wrists `(77,449)/(388,445)`, left/right hips `(193,457)/(277,456)`, knees `(168,583)/(307,586)`, ankles `(165,736)/(323,741)` in image pixels. Positions are approximate ±6–15 px; rig screenshot dots and skin overlap, and knee-dot colors may lie under skin.

Rig graph observations: a central neck/chest/abdomen/pelvis chain, two clavicle-to-shoulder links, upper-arm/lower-arm links, lateral pelvis-to-hip links and hip→knee→ankle chains. The colored keypoints indicate distinct pivots. The screenshot does **not** prove actual imported bone names, exact joint rolls or weight counts.

### R02 — semi-transparent side rig (400×814 px)

Visible neck head forward of shoulder, central spine slightly S-shaped, and knee/ankle joints relatively aligned in standing pose. Chest and abdomen are naturally rounded, not cubic. The arms project in front of the torso, wrists near anterior thigh. Two legs overlap in side projection; do **not** infer one bone is absent. Side rig screenshot shows a detached thin vertical object near lower shin; do not mistakenly add this as anatomy without cross-view confirmation.

### R03 — painted skin-weight visualization (444×820 px)

High saturation gradients cover chest, left/right forearm, pelvis, thighs and shins. Left/right weight zones appear deliberately distinct, confirming skin influences change across bilateral limbs. White narrow triangles are likely rig overlays/debug guides rather than holes in the mesh. Infer qualitative blend zones at shoulders, elbows, hips, knees and wrists; quantitative weights are **unavailable** from screenshots. Target game profile: max 4 influences, sums 1 ±0.0001; test animation extremes before approval.

### R04 — wireframe front (426×820 px)

Front hair line spiky and separately triangulated. Strong neck/collar V, clavicle folds and a central pendant. Upper arms/forearms have multiple width-changing edge loops; torso front has rectangular-ish ring grid transitioning into hip skirt; belt is a separate braided/notched band; two skew skirt flaps converge toward asymmetrically raised hem; low-poly finger separations can be counted qualitatively, not reliably reconstructed as source topology. Knee cuffs are triangulated fan/wedge-like, boot toes cubic but rounded by a few edges. Reference body face is present and detailed, therefore incompatible with forced faceless head gate.

### R05 — wireframe side (376×837 px)

Pronounced brow/nose/beard profile, hair spikes backward at crown, separate outer collar and hanging back mantle. The forearm and hand silhouette follow a relaxed bend; chest projects further forward than stomach, pelvis/hips carry fabric thickness behind thigh. Outer boot toe extends forward from shin by approximately its own ankle diameter (perspective-dependent). Mid-calf boot upper cuff is a faceted toroidal band; toe has 2–3 radial rings. Hair and scarf need side silhouette gates, not front-only vertex budgets.

### R06 — wireframe back (465×796 px)

Rear hair shell visible with faceted strips; a near-triangular upper-back scarf panel drops toward mid-back. Upper torso surface spans shoulder blades in connected segments without a horizontal box seam. Belt forms nonuniform braided rhythm; back skirt split and 2–3 draping irregular fabric panels. Gloves/palms separate from wrist cuffs. Leg boot cuffs match left/right silhouette but some folds differ. Rig skin should not hard-paint the scarf into the spine mesh.

### R07 — colored 3/4 view (≈376×837 px)

Material layer separation: light salmon skin; extremely dark reddish-brown chunky hair and beard; charcoal scarf; small dark stone/symbol pendant; grayish-brown asymmetric cloth skirt; pale rope/bone waist fastening; one dark forearm bracer; warm pale fur boot cuffs, dark brown boot shaft. See separate palette proposals earlier. Skin shading is soft but polygon edge changes remain present at elbows/shoulders. Face eyes are distinctly visible; do not use faceless canonical head here.

### R08 — colored rear 3/4 view (≈465×796 px)

Mantle/scarf overhang is a large dark trapezoid tapering to a central point above belt, with a long hanging dark patch on right back. Hair descends to nape. Kilt rear silhouette broad and relatively flat with two offset hem lengths; belt and boot fur cuffs visually brighter than skirt and shoes. Axial centerline of torso curves slightly; boot toes are more prominent from side. Neck and hair head-socket attachment must keep mantle free from rear hair clipping.

### Missing exact inputs required for production-ready reconstruction

A real side-by-side mesh audit would require original rigged `.blend`, `.fbx` or `.glb`, bind poses, material/UV texture maps, and a designated source model height. Those are **not** contained in the eight images. Precise polygon counts, normal maps, vertex weights and underlying body geometry are intentionally left *unmeasured*.
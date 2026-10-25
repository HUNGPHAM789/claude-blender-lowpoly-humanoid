# Origami Humanoid — Male & Female — Modeling Specification v1

## Status and counting rules

This is a proposed modeling specification accompanying an AI-generated concept image. No 3D mesh has been built or counted. All polygon numbers below are authoring targets, not measurements of the image and not established industry standards.

- A face is one polygon in the editable source mesh.
- Use exactly two polygon shapes: triangles (T, three vertices) and planar convex quadrilaterals (Q, four vertices).
- Target render triangle count = 2 × Q + T.
- All visible surfaces are flat facets. Do not use subdivision or NURBS surfaces.
- A material change is not an additional face. A functional surface group is a design classification, not a new polygon shape.
- Keep a quad coplanar if it is intended to read as one paper plane. A noncoplanar quad needs an intentional diagonal and must be counted as two triangles.
- The budgets refer to the neutral bind pose. Rigging may bend planes between poses.
- The concept image illustrates silhouette, features, material and detachable hair. The written specification governs counts.

## Overall form

Two adult base characters: one male and one female. Plain warm-ivory mannequin bodies, bald base heads, bare hands and feet, no outfit or accessories. Simplify chest and groin into clean mannequin surfaces. Use balanced rear pelvic volumes with a shallow central transition.

Suggested working heights: male 1.75 m, female 1.65 m; approximately seven heads tall. Heights are design choices and can be uniformly rescaled. Male: moderately wider shoulders and straighter waist. Female: moderately wider pelvis and softer taper through the waist. Avoid exaggerated musculature or curves.

Relaxed A-pose: arms about 20 degrees away from the torso, elbows slightly relaxed, hands open with separated digits, feet under the hips. Preserve bilateral topology symmetry in the source mesh.

Use broad, deliberate facets over the torso and limbs; concentrate smaller planes around facial landmarks and finger joints. The result should resemble a folded-paper sculpture rather than a randomly decimated smooth human. Origami describes the visual style; physical single-sheet foldability is not specified.

## Main polygon budget — per character

Male and female share the same body topology budget. Hands are included twice; the buttocks row includes both sides.

| Region | Quads Q | Triangles T | Source faces Q+T | Render triangles 2Q+T |
| --- | ---: | ---: | ---: | ---: |
| Facial region | 64 | 32 | 96 | 160 |
| Remaining skull/scalp | 32 | 16 | 48 | 80 |
| Both ears | 16 | 8 | 24 | 40 |
| Neck | 24 | 8 | 32 | 56 |
| Torso/pelvis excluding rear gluteal patch | 160 | 48 | 208 | 368 |
| Both arms, excluding hands | 160 | 32 | 192 | 352 |
| Both hands | 276 | 60 | 336 | 612 |
| Rear gluteal patch, both sides | 48 | 16 | 64 | 112 |
| Both legs, excluding feet | 224 | 32 | 256 | 480 |
| Both feet | 64 | 32 | 96 | 160 |
| **Base body total** | **1,068** | **284** | **1,352** | **2,420** |

Assign each polygon to exactly one region to avoid double counting. Facial region excludes ears, rear skull and neck. Hands include wrists; arm counts stop at the hand boundary. Rear gluteal patch starts below the sacral transition and ends at the upper-thigh transition; it is excluded from the torso and leg rows.

## Face — 96 faces, 8 functional surface groups

This is the facial region of ONE head, across both left and right sides. It is not the complete head count. Male and female retain identical counts with different vertex positions.

| Functional surface group | Q | T | Faces |
| --- | ---: | ---: | ---: |
| Forehead planes | 8 | 4 | 12 |
| Temple planes, both sides | 8 | 4 | 12 |
| Brow ridges and eye sockets, both eyes | 12 | 8 | 20 |
| Cheek and cheekbone planes, both sides | 12 | 4 | 16 |
| Nose bridge, sidewalls and tip | 8 | 4 | 12 |
| Mouth and lip planes | 6 | 2 | 8 |
| Chin planes | 6 | 2 | 8 |
| Jaw planes, both sides | 4 | 4 | 8 |
| **Total** | **64** | **32** | **96** |

Shape requirements:
- Forehead: broad central planes and clear changes at the temples; avoid a fractured, crystalline appearance.
- Eyes: shallow inset polygonal openings with readable upper lids. Use dark material patches on included socket faces; separate eyeballs are outside this budget.
- Nose: an actual projecting folded bridge, two sidewalls and a small tip, rather than a painted triangle.
- Mouth: a short closed crease between simplified upper/lower lip planes; no mouth cavity or teeth.
- Male: slightly broader jaw, clearer brow ridge and more angular chin.
- Female: slightly narrower jaw, softer cheek taper and subtler brow ridge.
- Ears: 12 source faces per ear from the separate ear allocation; simplified outer rim and one recessed inner plane group.
- No added eyebrow hair mesh in the base budget. Eyebrow shape may be suggested by the brow ridge or material assignment.

## Hand — 168 faces per hand, 7 functional surface groups

Exactly five separated digits: four fingers and one opposed thumb. Left hand mirrors the right. Use six-sided finger cross-sections, with taper toward the tips.

| Functional surface group | Q | T | Faces |
| --- | ---: | ---: | ---: |
| Palm planes | 12 | 0 | 12 |
| Back-of-hand planes | 12 | 0 | 12 |
| Palm sidewalls and heel transitions | 12 | 0 | 12 |
| Wrist connection | 6 | 0 | 6 |
| Knuckle bases and finger-web transitions | 12 | 0 | 12 |
| Four fingers together | 72 | 24 | 96 |
| Thumb | 12 | 6 | 18 |
| **One hand total** | **138** | **30** | **168** |

Finger construction:
- Each of the four fingers: three longitudinal segments × six side faces = 18 Q; tip cap = 6 T; total 24 faces.
- Thumb: two longitudinal segments × six side faces = 12 Q; tip cap = 6 T; total 18 faces.
- Root ends remain connected to the palm/web region, with no overlapping internal caps.
- The thumb base points diagonally out of the palm and opposes the other fingers.
- Fingers have distinct lengths and a slight relaxed curl. Show joint-plane changes rather than wrinkles.
- Nails are optional material patches on existing distal faces; separate nail geometry is outside this budget.
- Avoid fused fingers, mitten silhouettes, razor-thin fingers and spherical knuckles.
- This is a compact hand for neutral poses and simple gestures. If full-range gripping or close-up finger animation requires extra loops, revise the budget and document the new counts.

Both hands together: 336 source faces = 276 Q + 60 T = 612 render triangles.

## Buttocks / rear pelvis — 64 faces total, 5 functional surface groups

Counts cover BOTH sides of the rear gluteal patch. Per side: 32 source faces, including half of the shared central transition.

| Functional surface group | Q | T | Faces |
| --- | ---: | ---: | ---: |
| Upper gluteal slopes | 8 | 4 | 12 |
| Main posterior gluteal planes | 16 | 4 | 20 |
| Outer lateral transitions to hips | 8 | 4 | 12 |
| Lower gluteal transitions to upper thighs | 8 | 4 | 12 |
| Central sacral/medial transition | 8 | 0 | 8 |
| **Both sides total** | **48** | **16** | **64** |

Shape requirements:
- Create volume in side view through a controlled projection from the pelvis; a flat rear with a drawn crease is insufficient.
- Use a readable upper slope, main rear volume, side transition and lower return into the thighs.
- Central separation is shallow and formed through adjacent planes, not a deep cut or black line.
- Male: slightly narrower, flatter lateral outline. Female: moderately wider lateral outline. Keep the same count and topology layout.
- Preserve a clean pelvis-to-thigh connection. The buttocks are part of the body mesh, not detachable spheres.
- Keep the base neutral; account for sitting or hip flexion during later rigging tests before locking production topology.

## Hair — two separate digital plug-in assets

Base bodies stay bald. Hair assets are displayed beside the characters and delivered separately from the body.

| Asset | Q | T | Source faces | Render triangles | Functional surface groups |
| --- | ---: | ---: | ---: | ---: | ---: |
| Male short swept hair | 48 | 32 | 80 | 128 | 4 |
| Female shoulder-length bob | 96 | 48 | 144 | 240 | 4 |

Male hair breakdown:

| Group | Q | T | Faces |
| --- | ---: | ---: | ---: |
| Crown shell | 16 | 8 | 24 |
| Side and rear shell | 16 | 8 | 24 |
| Front swept clump planes | 12 | 12 | 24 |
| Underside attachment rim | 4 | 4 | 8 |
| **Total** | **48** | **32** | **80** |

Female hair breakdown:

| Group | Q | T | Faces |
| --- | ---: | ---: | ---: |
| Crown shell | 16 | 8 | 24 |
| Side and rear panels | 40 | 16 | 56 |
| Fringe planes | 16 | 8 | 24 |
| Lower perimeter and underside rim | 24 | 16 | 40 |
| **Total** | **96** | **48** | **144** |

Hair form:
- Short asset: about eight primary folded clump groups, swept gently to one side.
- Bob asset: about twelve primary folded clump/panel groups, with a coherent crown and distinct lower silhouette.
- Solid geometric clumps; no individual strands, transparency cards, hair simulation or fur.
- Matte charcoal finish, readable changes between planes, no wet or metallic sheen.
- Each style is one independently selectable mesh object; folded clump groups connect to its cap.
- Cap underside stays open to seat over the scalp. This is a digital accessory, not a watertight printable hair part.

Digital attachment interface:
1. Name the body meshes BODY_M and BODY_F. Name the assets HAIR_SHORT_01 and HAIR_BOB_01.
2. Provide a HAIR_SOCKET transform attached to the head bone. In a static model, parent it to the head object's transform.
3. Author both hair assets against one shared normalized SCALP_REFERENCE envelope. Use that same envelope for both base heads above the hairline; facial shapes below it may differ.
4. Match each asset's attachment transform to HAIR_SOCKET in the neutral pose. Derive fit/scale from the shared scalp reference, not from arbitrary viewport alignment.
5. Offset the cap just above the scalp by approximately 0.5–1.0% of head height, then adjust for clean contact without visible floating or intersections.
6. Keep the actual body scalp continuous. No visible peg, screw, hole or connector is required.
7. Hair follows the head transform. Do not merge it into the body mesh. Swapping hair should preserve its socket alignment.
8. Test frontal, profile and rear views, looking for scalp clipping, ear collisions and a floating hairline. Validate the bob during head turns if animation is later added.
9. In the reference layout, offset hair for presentation only. Keep a separate fitted transform for attachment.

## Materials and shading

Three material roles across the asset set:
1. Body_Ivory — matte warm ivory; roughness about 0.85; metallic 0.
2. Eye_Dark — dark charcoal for existing eye/socket face patches.
3. Hair_Charcoal — matte dark charcoal; roughness about 0.80; metallic 0.

Material parameters are design starting values, not measurements of the rendered concept. Use flat face normals to reveal origami planes. No subdivision and no geometry bevel in the base budget. If bevel geometry, separate eyes, teeth, nails or physical mounting hardware are added, count them as explicit budget revisions.

## Combined budget

| Configuration | Source faces | Render triangles |
| --- | ---: | ---: |
| One base body, bald | 1,352 | 2,420 |
| Base body + short hair | 1,432 | 2,548 |
| Base body + bob hair | 1,496 | 2,660 |
| Both bodies + both hair assets, each counted once | 2,928 | 5,208 |

## Acceptance checklist for the eventual 3D mesh

- Source polygon counts are reported from actual mesh data, per region and per asset.
- Counts match this target or deviations are listed with reasons; do not estimate counts from a render.
- Five separated digits per hand and a clearly opposed thumb.
- Readable nose projection, eye sockets, jaw and chin in front and side views.
- Rear pelvic volume is integrated into the torso and thigh topology.
- No duplicate/internal faces at connected region boundaries; coherent outward normals.
- Hair is a separate asset that can attach through HAIR_SOCKET and be swapped.
- Front, side and rear silhouettes match the intended adult proportions.
- Render triangle count is verified after intentional triangulation.
- Neutral-pose and basic deformation checks are completed before calling an asset production-ready.
- This document supplies targets and a concept prompt; it does not supply a rigged model or certify an existing mesh.

## Concept image generation prompt

The reference image was produced with the built-in image-generation tool. The prompt intentionally omits numeric topology annotations because image generation does not verify mesh counts.

Use case: stylized-concept.
Create ONE premium high-resolution wide landscape 3D character design reference sheet of TWO ADULT LOW-POLY ORIGAMI HUMANOID BASE MODELS, male and female, plus separate detachable hair assets. This is a visual concept reference, not an exact topology diagram; do NOT include polygon counts, dimension lines, a wireframe, or claims of measured geometry.
STYLE: beautifully designed folded-paper sculptural miniatures, unmistakably low-poly, medium-size clean planar facets, purposeful angular folds, elegant stylized adult faces, balanced attractive adult proportions approximately seven heads tall. Matte warm ivory unpainted body material, subtle paper grain, crisp plane changes, soft studio ambient occlusion and restrained soft shadows. A premium handcrafted origami 3D render. Keep forehead, nose, cheek, jaw, palms, five fingers, pelvis and rear gluteal volume clearly readable from the facets. No dense crystalline triangulation, no smooth clay look, no blocky Minecraft limbs.
LAYOUT: uncluttered editorial concept board on a pale warm-gray background. Main upper two-thirds: a large full-body bald adult male on the left and a large full-body bald adult female at center-right, each in a relaxed neutral A-pose facing a slight three-quarter front angle, palms slightly forward, entire heads and bare feet visible. Equal visual prominence. Male moderate shoulders and straight waist, female moderate shoulders and gently wider pelvis. Both visibly adult. Small matching full-body rear-view studies beside their corresponding large figure, to clarify the complete rear silhouette and buttocks. No clothing, no jewelry, no body hair, no nipples or genital detail; smooth abstract mannequin chest/groin; anatomically simplified and entirely nonsexual.
HAIR ASSETS: display a detached charcoal-black short swept origami hair cap at the far left near the male head, and a detached charcoal-black shoulder-length geometric bob hair cap at the far right near the female head. Both assets float separately with a generous visible gap from the bald heads; hair is NOT worn by either main model. Each hair piece is a coherent faceted shell made from solid folded clumps, not individual strands. Include a small underside three-quarter view of each cap beside it to show the open concave underside that seats over the scalp; clean removable digital attachment design, no physical hardware required.
BOTTOM DETAIL BAND: three spacious detail groups, separated by generous blank space. Left group: paired large head closeups of the same adult male and female, no hair, expressive but neutral, simple dark recessed polygonal eyes, folded nose bridge, subtle mouth crease, crisp chin and jaw. Middle group: two large closeups of the SAME right hand, one palm view and one back-of-hand view, exactly five separated fingers including a clearly opposed thumb, simplified joint planes, same ivory material; fingers are slender proportionate tapered polygonal digits, not mittens. Right group: paired cropped rear pelvis studies of male and female from waist to upper thighs, neutral anatomical mannequin study, showing angular upper glute slopes, back planes, side planes and transitions to thighs; modest stylization and balanced shape, no exaggerated buttocks or deep cleft.
TYPOGRAPHY: only small elegant readable English labels: "MALE", "FEMALE", "HAIR ASSETS", "FACE", "HAND", "REAR PELVIS". Absolutely no numeric annotation or tables. Strong hierarchy with main full-body figures larger than detail studies. Every closeup must visibly match the corresponding model. No props, no scenery, no decorative graphics, no logo, no watermark. Render as a beautiful useful sculptural design concept sheet, with attention to facial design and hands.


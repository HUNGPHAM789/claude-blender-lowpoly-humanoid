# SURVIVAL JOURNEY — Starter Humanoids v1.0
2026-10-24 | Curated image-first rebuild spec. See original starter female/male five-panel concept collages in Google Drive concept images (link in starter manifest).
**Do not conflate starter with UPGRADED_MALE_PRIMAL and UPGRADED_FEMALE_PRIMAL.**

## Global numeric convention
Y up, +Z character facing, ground at Y0. H = character height including hair. Proposed starter render height female 1.68m, male 1.80m; these are production targets inferred from image, NOT measurements of unprovided source model. Individual dimensions specified as fractions H. Animation/rest pose standing relaxed near A-pose, hands by outer hips. Shared interchangeable base LPM rig and SO​CKET names, with costume assembled separately.

| Region | Female proportions H | Male proportions H | Geometry specification |
|---|---|---|---|
| Head+hair top | .16–.18 | .16–.18 | cap follows skull; angular hair blade silhouette |
| Eye horizontal line from ground | .89–.92 | .88–.91 | paired narrow dark sculpt/geometry slots |
| Jaw/neck | .85–.90 | .84–.90 | neck 6–8 sides and chin support |
| Shoulders Y | .79–.84 | .79–.84 | full shoulders width .22–.25H female / .25–.29H male |
| Upper chest/pectoral | .73–.81 | .72–.81 | female strap top/bandeau separate; male bare chest 2 distinct pectoral planes |
| Natural waist | .58–.66 | .58–.66 | female frontal width .12–.15H; male .14–.17H |
| Iliac hip/pelvis | .51–.59 | .51–.59 | female width .18–.22H; male .17–.20H |
| Crotch Y | .50–.53 | .50–.53 | proper groin deformation; cloth skirt overlays thighs |
| Knee Y | .24–.28 | .24–.28 | use 3+ rings for flexion |
| Ankles Y | .05–.09 | .05–.09 | narrow calf taper -> ankle |
| Foot length forward | .13–.16H | .14–.17H | bare toes and separate instep planar surface |
| Hand length | .09–.11H | .09–.11H | thumb opposition + individual digits silhouettes |

## Starter Female — exact visual audit
Reference is first starter 5-panel board: colored front 3/4, rear 3/4, wire front, wire side, wire back.
- **Head:** short simple face mask, dark brows wedge approx brow width 1/4 eye-to-ear, small nose plane, eyes subdued, ears under hair. Face should remain readable at 64px.
- **Hair:** dark charcoal angular cap + 10–16 forward/side clumps, crown peaks, rear tied ponytail with 6–10 long faceted tapered locks. Longer locks hang beside both cheeks, asymmetrically. Keep separate HAIR_* nodes; hair roots trace actual skull rings with collision clearance.
- **Neck/traps:** slim neck, collarbone silhouette; neck emerges from visible bare shoulders. No thick neck scarf.
- **Chest:** strapless jagged brown bandeau cloth covering fitted chest; 2 bulged geometric forms but no single smooth cylinder. Zigzag uneven top hem with pale tooth-leaf trim. Torso exposed from bandeau to belt.
- **Abdomen:** waist narrowed and planar oblique lines. Avoid high-frequency sculpt detail. Side outline concave above hips.
- **Shoulder/upper arms:** moderate smooth biceps volume, elbow narrow; lower arms angle slightly outward, hands by thigh. Fingers a grouped palm fan with thumb and 3–4 discernible tips.
- **Belt:** broad primitive twisted rope/bone belt at high hips; central elongated teardrop/leaf pendant. Material light taupe vs main dark skirt.
- **Skirt:** 7–11 leaf-pointed garment panels as discrete low-poly shells, mixed dark brown + 2–4 light-tan accents. Front layered and asymmetric, with center tip near upper thighs; back panel partially covering upper thigh, sides slits. Do not glue garment vertices directly onto thigh skin.
- **Legs:** thighs taper through knees; calves broaden then ankle narrows. Bare feet five indicated toes with toe seam/groove and separate dark nail color only if readable.
- **Back:** hair tied behind crown, bare shoulder blades; slim waist; belt and skirt visible from rear; ponytail covers upper back but no shoulder scarf.
- **LOD0 suggestion:** 1800–3200 triangles including hair/outfit; LOD1 <1600; LOD2 <800.
- **Materials:** skin-peach, shadow-peach, hair-charcoal, leather-dark, leather-light, belt-bone.

## Starter Male — exact visual audit
Second five-panel board: shaded front 3/4 + rear 3/4 + front/side/rear wires.
- **Head/face:** wider jaw and neck, thick dark eyebrows, protruding geometric nose, eyes under heavier brow ridge. Full charcoal beard with triangular chin/cheek spikes and separated moustache tuft, to be separate from head skin.
- **Hair:** dark angular cropped medium mane of 9–15 uneven polygon clumps, pointed hairline, rear head locks low to ear; no ponytail on starter male.
- **Torso:** broad shoulder, planar pectoral volumes and trapezius slope; simplified abdomen with clean quadrilateral/triangles; 2–3 torso rings for spine deformations.
- **Arms:** upper arms slightly larger than female, forearm tapers to wrist, fingers visible and graspable. No metal bracers, no sleeves.
- **Waist:** pale twisted rope/bone belt around pelvis with central dark hanging elongated bone ornament.
- **Skirt:** asymmetric dark leather/kilt panels over hips with 2–3 lighter tan dagger-shaped leaves on front/side; bare calves. No leg armor or boots in **starter** variant.
- **Legs:** thick thighs and large stylized calf, ankle taper. Wide barefoot foundation with low-poly toes. Side view heel-to-toe projection important.
- **Back:** broad bare trapezius/shoulder blades, waist concave, kilt rear triangular layered silhouette, belt above buttock.
- **LOD0 suggestion:** 1800–3000 triangles; LOD1 <1500; LOD2 <750.
- **Materials:** skin, hair-charcoal, beard-charcoal, leather-main, leather-light, bone-ornament.

## Rig, sockets, animation
- Shared root/pelvis/spine_01/spine_02/chest/neck/head, clavicle L/R, upperarm L/R, forearm L/R, hand L/R, thigh L/R, calf L/R, foot L/R and toe L/R.
- Socket aliases MUST match repo's `cam_L`, `cam_R`, `dau`, `lung`, `hong_*` etc. See LPM base SKILL; 32mm grip compatible with physical Tool Rack.
- Mesh groups BODY, HEAD, HAIR, BEARD, TOP, BELT, ORNAMENT, SKIRT, HANDS, FEET; detachable skinned geometry, no irreversible boolean union.
- Functional tests: naked body animation, hair/scarf self-penetration, tool reach, barefoot ground contact, skirt swaying during walking, visually matching front/back/side reference.
- Difference from upgraded characters: upgraded female wears diagonal shawl, structured upper garment, wrist bracer, boots; upgraded male wears scarf/boots; starter versions wear minimal clothes and **bare feet**.

## Strict visual gates
H01 silhouette image 3/4 color and 3 wire views matched under same camera.
H02 planar face not overly smooth; hair and beard clearly separated from face at game scale.
H03 exact group names sockets/rig compliance and props can be reserved/carried.
H04 all garment shell clearances >0 in neutral, moving limbs skirt gap checked.
H05 toe width, large feet and stance read in orthographic isometric at 64 pixels.
H06 every numeric dimension labeled `proposed` until original 3D mesh obtained.

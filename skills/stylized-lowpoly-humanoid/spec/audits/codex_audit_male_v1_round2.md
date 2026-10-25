**I would revise round 1: the owner’s “snug” requirement remains correct. My proposed 25–40 mm chin offset was insufficiently supported, and ≥0.90 silhouette IoU should not be a hard gate against these images.** The useful distinction is attachment gap versus beard shape—not permission to make the beard stand farther from the face.

**1. Beard: satisfy snug attachment and a solid chin**

**1.1 What the images actually establish**

In image 1’s side wireframe, the beard follows the face into the jaw, then forms a compact forward/downward chin mass. It does not form a separate mask floating ahead of the jaw. Image 2 makes the continuous cheek–jaw connection clearer, but is three-quarter, not side.

Using **W = bare skull width** and **H = bare skull top-to-chin height**:

| Region | Defensible visual reading | What cannot be measured from these images |
|---|---|---|
| **Cheek** | Beard begins directly at the visible skin boundary. No visible air slit. Broad surfaces lie along the cheek rather than projecting sideways. | Thickness over the concealed cheek. |
| **Jaw corner** | Sideburn and beard form one connected angular strip. The lower boundary turns forward/down toward the chin; there is no lateral fan of spikes. | Exact underlying jaw position and normal offset. |
| **Chin front** | A broad, blunt faceted mass. In the side panel, its leading contour is approximately aligned with the nose tip or slightly ahead—roughly **0–0.05H** in projected horizontal difference. | Beard-to-bare-chin distance: the bare chin is hidden. |
| **Under chin** | Beard returns upward/back toward the jaw/upper neck as a continuous underside. It is not a fringe of isolated long needles. | Exact downward extension below the anatomical chin, which is hidden. |

That **0–0.05H is a rough projected landmark comparison**, not a recovered 3D thickness. H itself requires an estimated concealed skull/chin frame. I would not gate that range directly.

I cannot defend a precise cheek, jaw or chin **skin-offset** measurement from the sheet. Giving four precise offsets would repeat the mistake in round 1.

**1.2 Concrete revised starting dimensions**

These are **construction proposals on our measurable body**, not claimed sheet measurements:

| Region | Initial construction limit |
|---|---|
| Contact surface on cheek/jaw/chin | Target gap **0.01–0.02W**, approximately **2–4 mm** on this body. |
| Outer cheek surface | Start within **0.03–0.06W**, approximately **7–13 mm**, measured along registered cheek normals. |
| Outer jaw corner | Start within **0.04–0.07W**, approximately **9–15 mm**; no isolated lateral tips outside that envelope. |
| Chin front | Start at **0.05–0.08W**, approximately **11–17 mm**, forward of the registered bare-chin profile. **No mandatory minimum volume gate yet.** |
| Bottom of central beard | Trial extension **0.08–0.15H**, approximately **22–41 mm**, below the bare chin; close the underside back toward the submental attachment. |

A solid chin comes from **broad joined planes, a substantial cross-section, and a closed-looking underside**. It does not require a 40 mm forward offset. First build the lower end of these ranges, then let the owner judge the side and three-quarter views.

**1.3 Replace the single p90 rule with four separate measurements**

A vertex-distance percentile mixes attachment, thickness, downward extension and tessellation density. It can also overlook a small but ugly spike.

Use named regions and authored surface roles: `contact_inner`, `cheek_outer`, `jaw_outer`, `chin_outer`, `underside`, plus corresponding body patches.

1. **Contact coverage and gap — replaces “beard on the face.”**
   - Sample the designated body attachment patches uniformly by area.
   - Cast outward along registered body normals into `contact_inner`.
   - Require **≥99% valid coverage**, excluding explicitly designated open boundaries.
   - Require gap **p95 ≤6 mm**, **maximum ≤8 mm**, and penetration **≤1 mm**.
   - Treat missed rays as failures, not samples to omit.
   
   This rejects the old 18 mm floating mask even if its outer shape is otherwise attractive.

2. **Regional outer envelope — replaces “beard hugs the face.”**
   - Measure cheek/jaw thickness along the same registered normals.
   - Measure chin-front extension along the face’s forward axis.
   - Measure below-chin extension along the vertical axis.
   - Report these separately against the provisional ranges above; freeze hard shape limits only after owner approval.

   Do not use nearest distance to arbitrary neck/chest skin as “chin thickness.”

3. **Attachment visibility and continuity — adds what gap statistics miss.**
   - In fixed front, left/right side and three-quarter cameras, test for background visible between designated beard attachment edges and the face.
   - Permit **zero exposed attachment slit**, with a stated raster tolerance.
   - Check that intended adjoining beard patches overlap or connect; an isolated blade is not acceptable merely because its root is close.

4. **No jutting spikes — maximum excursion, not percentile.**
   - Author a coarse, independently defined cheek/jaw/chin envelope.
   - Sample every outer triangle, including tips.
   - Require maximum protrusion beyond that envelope **≤0.015W**, about **3 mm**, excluding approved moustache endpoints.
   
   The envelope must be approved or fixed by design; deriving it from the same spiky mesh would make this test meaningless.

**Do not simply disable squeezing on arbitrary v0 geometry.** A floating mask must fail contact/shape gates. For authored v2 geometry, fit the contact surface and preserve the intended outer mass; if both cannot coexist without distortion, report a failed fit rather than silently flattening it.

**2. Which targets can actually be machine gates?**

**2.1 Sheet silhouette IoU: diagnostic only**

A hard **IoU ≥0.90 against the sheet is not reliable here**. Camera perspective, pose, painted contours, hidden landmarks and differences between the cleaned image and original sheet all affect it. A camera optimization can also compensate for incorrect geometry.

Use sheet overlays to locate disagreements, report alignment assumptions, and show them to the owner. After approval, **our own v2 mesh and fixed cameras** can become reliable regression references.

**2.2 Machine-checkable measurements**

| Target | Robust implementation | Appropriate status |
|---|---|---|
| Triangle counts | Count final exported primitives by role, including additions and instances as applicable. | Hard gate now. |
| Material roles | Preserve role IDs and face assignments; compare material parameters before/after export. | Hard gate now. |
| Clump/panel counts | Count authored IDs and verify each owns geometry. Do not infer counts from noisy curvature segmentation. | Hard construction gate once the chosen recipe is accepted. |
| Length/width | Measure in each component’s authored local frame or along its centreline; avoid ambiguous world-axis bounding boxes. | Machine-checkable; initial ranges remain design proposals. |
| Overlap percentage | Define a root-band surface and measure the area covered by its designated neighbour through local projection/raycasting. | Robust **after that definition**; “25% overlap” alone is underspecified. |
| Root concealment | Render component/root IDs with fixed cameras; visible root pixels divided by projected root pixels in an isolated-root render. | Hard gate within the specified camera set, not a claim about every possible view. |
| Facet dimensions | Measure triangle area/edge length and, separately, connected coplanar or equal-normal patches. | Geometry gate; thresholds need tuning. |
| Colour-role area | Unlit material-ID renders: visible tan pixels divided by visible tan + dark-leather pixels. Exclude belt, stone and background. | Repeatable render metric; target percentage initially advisory. |
| Fitter shape preservation | Compare corresponding protected vertices and pre/post depth/silhouette renders under identical cameras. | Hard regression gate. |
| Beard contact | Area-sampled registered contact patches, with misses counted. | Hard gate. |

A measurable number does not automatically become a justified artistic acceptance threshold. **Thirty clumps can be counted perfectly and still look wrong.**

**2.3 Keep owner-reviewed**

The following remain visual decisions until an approved v2 baseline exists:

- Whether clumps feel broad, coherent and appropriately irregular.
- Whether the beard looks snug and substantial rather than mask-like.
- Whether the skirt’s diagonal overlaps resemble the official design.
- Whether colour placement—not merely colour percentage—is right.
- Whether planes read attractively at game scale.
- Whether the total silhouette matches the official character.

**3. Minimal fitter changes, in priority order**

**3.1 Preserve geometry roles and materials end to end**

The loss begins earlier than I identified in round 1:

- [fit_engine.py:211](~/projects/lpm-faceless-humanoid/skills/character-fitter/scripts/fit_engine.py:211): `load_asset()` flattens the asset and returns a new geometry-only mesh.
- [fit_character.py:60](~/projects/lpm-faceless-humanoid/skills/character-fitter/scripts/fit_character.py:60): fitted output is again reconstructed without visuals.
- [fit_character.py:75](~/projects/lpm-faceless-humanoid/skills/character-fitter/scripts/fit_character.py:75): one material replaces all sub-geometry roles.

**Minimal change:** retain the source scene and a stable sub-geometry/vertex/face mapping; use a concatenated geometry view for collision calculations, then write fitted positions back to the original role meshes.

**Gate effect:** strengthen existing **topology** to check per-role face ownership, and add **material-role preservation**. The current topology gate at line 104 cannot detect lost colours or merged semantic roles.

**3.2 Replace blanket beard squeeze with contact fitting and protected outer geometry**

Relevant locations:

- [fit_engine.py:350](~/projects/lpm-faceless-humanoid/skills/character-fitter/scripts/fit_engine.py:350): placed-hair path calls root pull, beard squeeze and fading push.
- [fit_engine.py:375](~/projects/lpm-faceless-humanoid/skills/character-fitter/scripts/fit_engine.py:375): root selection currently relies on geometry/proximity rather than explicit authored roles.
- [fit_engine.py:417](~/projects/lpm-faceless-humanoid/skills/character-fitter/scripts/fit_engine.py:417): blanket squeeze implementation.
- `fit_engine.py:504`: the non-placed path also calls squeezing.

**Minimal change:** add explicit movable-contact and protected-outer masks. Restrict contact correction to designated surfaces and transition vertices. Fail if resolving contact/collision would require unacceptable outer deformation. Retain the legacy corrective path for untagged fixtures until they receive proper region definitions.

**Gate effect:**

- Replace **beard hugs the face**, [fit_character.py:121](~/projects/lpm-faceless-humanoid/skills/character-fitter/scripts/fit_character.py:121), with regional envelope checks.
- Strengthen **beard on the face**, line 124, with coverage, p95 and maximum gap.
- Add protected-shape displacement to **deform**, line 106. Edge stretch alone cannot detect a rigidly displaced patch.
- Keep rest-clipping, face-clear and required-pose gates.

The current `>20` sample conditions can silently skip beard gates. A declared beard should fail when its required measurement coverage is insufficient.

**3.3 Gate the final assembly budget, including automatic lining**

- [fit_character.py:44](~/projects/lpm-faceless-humanoid/skills/character-fitter/scripts/fit_character.py:44): current budget handling is an input decimation trigger with **5% tolerance**.
- [fit_character.py:62](~/projects/lpm-faceless-humanoid/skills/character-fitter/scripts/fit_character.py:62): automatic lining is added afterward.
- Lines 99–142 contain no explicit final triangle-budget gate.

**Minimal change:** recount the exported assembly and enforce independently:

- Hair + beard **≤1,200**.
- Skirt + every lining **≤900**.
- Belt **≤150**.
- Ornament **≤60**.

**Gate effect:** add an actual **final budget** gate; there is no existing final gate to amend. Keep **no skin showing**, but insufficient budget for its automatic fix must cause failure. Also give added lining its own applicable rest/pose checks rather than merely appending geometry.

**3.4 Preserve authored normals and roughness in previews**

- [render_turnaround_blender.py:28](~/projects/lpm-faceless-humanoid/skills/stylized-lowpoly-humanoid/scripts/render_turnaround_blender.py:28): roughness is clamped.
- Line 30: every polygon is forced smooth.

**Minimal change:** remove both global overrides. Preserve authored normals; explicitly use flat planes for the v2 hair/beard/leather groups where specified. Do not globally flatten the body.

**Gate effect:** none of the existing fitter gates verifies this. Add a **render/export shading-contract** check. For flat regions, corner normals must agree with the intended face/plane normal; validate after reimport. The final rendered beauty still requires visual review.

**4. Corrections to round 1**

1. **Withdraw the 25–40 mm chin-front recommendation.** The sheet hides the underlying chin, so it does not support that claimed offset.
2. **Withdraw ≥0.90 sheet IoU as a hard gate.** Keep it diagnostic; use identical-camera comparisons for pipeline regression.
3. **Downgrade my clump counts, lining percentages and facet-size ranges to provisional design targets.** They were not measured from the official mesh.
4. **Separate rendered facets from triangles.** Two coplanar triangles may form one visible plane; small triangles do not necessarily create noisy shading.
5. **Do not attribute the entire thin-beard appearance to squeezing.** The builder already creates narrow blades. Squeezing is a plausible additional distortion; its exact contribution requires a pre/post geometry comparison.
6. **Correct the material-loss location:** it starts at `load_asset()`, not only during final material assignment.
7. **Do not protect an unapproved outline blindly.** Preservation applies to a deliberately authored v2 shape; it must not preserve v0’s floating mask or sideways spikes.

All inspection remained read-only.
---
name: build-stylized-organic-model
description: ORGANIC SUBJECTS ONLY (animals, trees, rocks, plants, creatures) — NOT humans (use the humanoid skill). Create code-generated stylized organic 3D models from short prompts such as "create a rabbit model", without asking the user to supply a per-species mesh specification. Use for low-poly origami humans, vertebrate animals and simple imaginary creatures, semantic anatomy planning, convex/concave forms, bulges, creases, seamless organic volume unions, static OBJ/GLB export, and multi-view visual iteration.
---

# Build Stylized Organic Models

> **Scope (Boss 22/10/2026): organic subjects only — animals, trees, rocks, plants, simple creatures.** Its humanoid test came out as a smooth clay sculpt, not origami; humans go to the humanoid skill (LPM / combined). Rabbit test: excellent — saved as asset `~/projects/GameDev/assets/organic/rabbit_v1/`.
>
> The bundled files were missing when handed over; they were REBUILT from this document on 22/10 and now live here: `scripts/organic_pipeline.py` (masses → smooth union → marching cubes → report/previews), `scripts/blender_decimate.py` (QEM via Blender Decimate collapse, X symmetry), `references/rabbit-calibration.json` (the working rabbit plan), `references/humanoid-example.json`, `references/TEST_REPORT_2026-10-22.md`. Field names in the plans were invented by the rebuild — treat the JSON files as the schema.

## Execute from a short prompt

Infer a complete internal model plan from the subject, available references and the user's requested purpose. Do not ask the user to write an anatomy specification. Resolve ordinary design choices using the defaults below and state consequential assumptions briefly.

Distinguish three sources of knowledge:
1. Infer species identity, anatomy and proportions through your own semantic reasoning.
2. Apply this skill's reusable geometry grammar and art direction.
3. Execute the bundled code, inspect its outputs and correct the model.

The scripts accept a JSON plan; they do not interpret natural language. You are responsible for turning "rabbit" into that plan. Never claim that a fixed rabbit template is a universal species recognizer.

Represent fur/plumage color patches as surface materials using color_regions, not as raised overlay volumes. A penguin's white bib belongs on the existing body surface. Use extra geometry only for real volume, such as an eyeball, nose or removable shell.

Use [form-grammar.md](references/form-grammar.md) to translate shape intent into geometry, [anatomy-and-style.md](references/anatomy-and-style.md) to infer a part graph, and [implementation.md](references/implementation.md) for the exact executable schema and limitations. Read those references before generating a new species.

## Apply consistent defaults

Unless overridden, build one recognizable static adult animal or adult humanoid in a neutral, balanced pose:
- Style: attractive low-poly origami, large deliberate facets, clean silhouette, modest stylization.
- Palette: a restrained matte species-appropriate palette with charcoal eye accents; use ivory for plain/mannequin base studies. User-requested colors take priority.
- Composition: full body; orthographic isometric camera, 45-degree azimuth and 35.264-degree elevation.
- Construction: Z up, Y forward, X right; bilateral symmetry across X = 0 where appropriate.
- Scale: normalize the finished asset to height 1.0 meter as an authoring convention, not a biological measurement.
- Anatomy: integrate body, limbs and anatomical appendages. Keep eyes, removable hair and equipment separate only when their roles require it.
- Humanoids: abstract mannequin chest/groin, no clothing unless requested.
- Output: actual indexed geometry, static GLB, OBJ, plan, topology report and multi-view previews.
- Rigging: do not add a rig unless the task calls for animation. Do not describe a static triangular mesh as animation-ready.

Use a soft initial total budget: about 1,000–3,000 triangles for a simple animal, 2,000–5,000 for a more articulated animal/humanoid. Choose the budget from silhouette complexity and game-view size; never reuse the old fixed 676-face humanoid allocation for every subject.

Treat these budgets as design starting points. Preserve identity and valid topology before hitting a round number. Count source triangles and exported split vertices separately.

## 1. Infer a semantic part graph

Determine:
- Subject/archetype and pose: biped, quadruped, seated compact mammal, bird, fish or an explicit hybrid.
- Primary masses: head, chest, abdomen/pelvis and support limbs.
- Three to five identity cues that must survive at small size.
- Part relationships: continuation, branch, attached swelling, thin appendage, recess or detachable asset.
- Relative dimensions, local axes, anatomical landmarks and contact areas.
- Material roles, bilateral relationships and intended floor contact.
- Any required articulation and its consequences for the modeling route.

Write the resulting plan yourself. If identity is unfamiliar or a provided reference is essential, inspect that reference or use authoritative visual/anatomical sources; do not replace the animal with a generic human skeleton.

For a rabbit, infer long ears, a compact muzzle, large folded hindquarters, smaller forelimbs, long hind feet and a short tail. For a fox, infer a longer muzzle, pointed ears, a quadruped stance and a long bushy tail. Do not transfer rabbit proportions to the fox.

## 2. Design the silhouette before details

Arrange primary masses first, then inspect front, side and game-view outlines. Give the support limbs readable negative space, place the center of mass over the support area and make the head direction apparent.

Encode primary form before secondary form:
1. Proportion, pose and identity.
2. Large convex volumes and major concave transitions.
3. Ear/limb thickness, root connections and important creases.
4. Eyes, nose and restrained tertiary detail.

Use local frames for all deformations. A thigh bulge follows the thigh axis, regardless of the character's orientation. Separate geometric hardness from material gloss and physical stiffness.

Represent curvature through changing section radii and face orientations. Flat shading cannot repair an incorrect silhouette. Do not fill the mesh with arbitrary small triangles as a substitute for intentional form.

## 3. Choose a construction route

### Static organic model: implicit union, then simplify

Use this bundled route for a first static body:
1. Encode anatomy as oriented ellipsoid/superellipsoid masses and capsules.
2. Apply taper, bend, twist, localized bulge/dent, curve ridge/groove and boolean operations as needed.
3. Overlap intended anatomical roots and use a controlled smooth union.
4. Sample the final volume and extract one shared-edge mesh.
5. Check connectedness and manifold topology before simplification.
6. Reduce with conservative QEM, inspect silhouettes and raise the budget if important features disappear.

Use this route for fused static surfaces. It creates triangles and does not supply animation edge loops, a rig or a certified origami plane layout.

### Controlled planes or animation: section-based control mesh

Use the bundled ellipsoid and transported-frame loft routines as starting geometry, then implement semantic shared boundary loops for the requested model:
- Reuse position indices at coincident interfaces.
- Remove internal caps before attaching an appendage.
- Bridge real gaps with nondegenerate faces; do not bridge coincident rings.
- Adapt ring densities with explicit transitions, never T-junctions.
- Put support loops around the requested joints and test actual poses.
- Preserve separate per-corner normals rather than separating body surfaces to obtain flat shading.

The loft function builds one tube; it does not automatically join that tube to a torso. Implement and validate the junction explicitly. Retopologize an implicit draft when the requested rig needs purposeful edge flow.

If Blender is available, use its installed version's documented mesh, remesh and export APIs. If it is unavailable, the static bundled pipeline still works with NumPy and Pillow. Report any unexecuted Blender/rig/engine checks.

## 4. Build using the bundled pipeline

Use the active Python environment; verify NumPy and Pillow are installed before running. Do not install dependencies without need.

Create a task-specific plan JSON outside this skill directory. Then execute:
~~~bash
python /absolute/path/to/this-skill/scripts/build_model.py plan.json --out output/model
~~~

Resolve the skill's real directory from the loaded resource; do not hardcode a cache path.

For a smoke test only, run [rabbit-calibration.json](references/rabbit-calibration.json). Treat it as a working starting example, not as the correct anatomy for every new request. Adapt proportions, pose and palette to the actual subject.

Inspect the emitted files:
- model.obj: indexed Z-up source triangles, flat shading, no rig.
- model.glb: static Y-up geometry with explicit flat normals and materials.
- previews.png: front, side, back and isometric depth-rendered views.
- isometric_96px.png: small-size readability diagnostic.
- plan.json: the exact authored input.
- report.json: actual counts and the checks the scripts performed.

A successful script run establishes the reported topology checks, not visual quality, absence of self-intersections, animation quality or target-engine compatibility.

## 5. Evaluate and revise visibly

Open the preview sheet using the available image-inspection tool. Evaluate:
- Identity: do the three to five key cues survive at small size?
- Silhouette: are pose, head direction and appendages unambiguous?
- Proportion: are primary masses intentional and balanced?
- Connections: are roots attached without an accidental collar, seam, pinched waist or melted blob?
- Convexity/concavity: do bulges and recesses support anatomy?
- Facets: are important planes legible without dense visual noise or sliver triangles?
- Contacts: do feet/support surfaces meet the floor without arbitrary sinking?
- Details: are eyes/nose placed on the intended surface rather than floating?
- Symmetry: are paired volumes balanced despite unconstrained QEM triangulation?

Revise the plan and rebuild when any major category fails. Fix proportions and overlap before changing polygon budgets. Increase sampling resolution when features were never captured; increase target triangles when simplification erased an already captured feature. These are different controls.

Use the small-size render as a diagnostic, not a marketing preview. Use the requested engine or Blender for final lighting/presentation when available. If views remain noisy after a reasonable adjustment, switch to a more controlled plane/loft construction instead of repeatedly adding triangles.

Perform another multi-view inspection after substantive changes. Record meaningful revisions and the remaining limitations; do not claim a beauty score that was never assessed.

## 6. Validate honestly

Require one connected, closed source body surface unless the design explicitly calls for an opening or multiple bodies. Validate anatomical appendages as part of that body; tag eye overlays and removable accessories separately.

The bundled checks cover:
- Finite vertices and valid indices.
- Source vertex and triangle counts.
- Boundary/nonmanifold edges, winding consistency and closed vertex links.
- Degenerate and duplicate faces, loose vertices, component count, Euler characteristic and positive signed volume.
- Topology-preserving local collapse conditions and face-flip rejection during reduction.

They do not establish:
- Absence of self-intersections or cross-object clipping.
- Anatomical correctness or attractive design.
- Rigging, collision, motion, skin weights or actual engine import.
- A Blender-native quad layout or exact bilateral symmetry after QEM.
- Preservation of every thin feature under arbitrary sampling/reduction.

Keep those statuses explicit. If requested, add the relevant real checks and tests rather than changing an unchecked status to passed.

Treat topological connectedness, positional continuity, visual smoothness, flat normal breaks and skeletal continuity as different properties. A connected object may still have disconnected surfaces; matching coordinates may still have duplicate unwelded vertices; a UV/normal split may still represent one welded source surface.

## 7. Extend rather than overpromise

Support new organic subjects by composing the same geometric operators and inferring a new part graph. Do not require a separate user-authored specification for every animal.

For machinery, architecture, advanced cloth/fur, photoreal anatomy or a production facial rig, preserve useful form rules but choose an appropriate specialized workflow. Do not advertise this static organic kernel as a universal solution for every 3D modeling discipline.

When handing off, name the subject, actual files, triangle count, construction route, visual-review status and any material untested requirement. Keep technical detail proportional to the user's request.

Run [test_geometry.py](scripts/test_geometry.py) after changing the bundled code.

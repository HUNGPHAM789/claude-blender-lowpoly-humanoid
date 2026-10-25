---
name: procedural-low-poly-world
description: Production standard for building procedural 3D low-poly worlds, village builders, animals, trees, and environmental diorama props in Three.js and Blender/Godot with flat shading and zero asset dependencies.
version: 1.2.0
author: Hermes & Antigravity
license: MIT
metadata:
  hermes:
    tags: [3d-graphics, threejs, blender, godot4, procedural-modeling, low-poly, diorama, webgl]
    related_skills: [low-poly-origami-character, humanoid-replaceable-assets]
---

# Core Philosophy
This system is dedicated to creating highly stylized, low-polygon dioramas and game environments entirely procedurally. The goal is visual fidelity through geometric simplicity, clean silhouette readability, unified palette harmony, and strict proportional scaling across all entities (settlers, wildlife, vegetation, and terrain).

---

# World Scale Hierarchy & Proportional Budget (Rule for Size)
All environmental props, vegetation, and wildlife MUST be strictly proportioned against the canonical Humanoid Settler baseline ($H = 1.80\text{m}$). Never eyeball arbitrary scales.

| Entity | Height / Size | Proportional Ratio | Role & Silhouette Rule |
|---|---|---|---|
| **Humanoid Settler** (LPM Base) | **$1.80\text{m}$** | **$1.00\times$ (Anchor)** | Canonical reference standard for all world assets. |
| **Stylized Oak Tree v2** | $5.80\text{m} - 6.50\text{m}$ | $3.2\times - 3.6\times$ settler | Main temperate canopy; trunk $\varnothing \approx 0.75\text{m}$, spread $\approx 5.5\text{m}$. Scaled down from old 12m giants to maintain balanced diorama framing. |
| **Pine Tree** | $6.50\text{m} - 7.50\text{m}$ | $3.6\times - 4.2\times$ settler | Tapered 3-tier conic needle canopy. |
| **Birch Tree** | $5.00\text{m} - 6.00\text{m}$ | $2.8\times - 3.3\times$ settler | Slender trunk with light green foliage. |
| **Berry Bush** | $0.90\text{m} - 1.10\text{m}$ | $0.50\times - 0.60\times$ settler | Foraging node; waist-height to settler, lower than deer shoulder. |
| **Deer — Stag (Huơu Đực)** | $1.50\text{m}$ shoulder / $2.10\text{m}$ antlers | $0.83\times$ shoulder / $1.17\times$ tip | Majestic multi-tine procedural branching bone-white antlers. |
| **Deer — Hind (Hươu Mẹ)** | $1.30\text{m}$ shoulder | $0.72\times$ settler | Slender graceful neck, no antlers, cream belly inset. |
| **Deer — Fawn (Hươu Con)** | $0.85\text{m}$ shoulder | $0.47\times$ settler | Compact proportions, large ears, cute profile. |
| **Rabbit (Thỏ)** | $0.45\text{m}$ height | $0.25\times$ settler | Small wildlife; knee-height to settler. Clean chest without artifact stickers. |
| **Storage Tile (Starter 4-Sq)** | $4.00\text{m} \times 4.00\text{m} \times 0.25\text{m}$ | $2.22\times$ settler width | 4 modular $2.0\text{m} \times 2.0\text{m}$ storage cells with wooden corner posts. |
| **Mountain Cliffs & Gorge** | $8.50\text{m} - 9.00\text{m}$ summit | $4.7\times - 5.0\times$ settler | Continuous 2-tier massif; lower terrace $4.8\text{m}$, summit $8.5\text{m}$. |

---

# Technical Directives

## 1. The Material Isolation Rule (CRITICAL)
**NEVER** mutate shared materials. When multiple meshes share a single material instance, changing one property (like `color`) corrupts all meshes using that instance.
*   **Rule:** Always instantiate distinct materials for every unique component part (e.g., `deerBodyMat`, `deerBellyMat`, `deerAntlerMat`).

## 2. Ground-Up Stacking Rule
All characters and creatures must be constructed and positioned relative to a definitive vertical baseline ($z=0$ or $y=0$).
*   **Sequence:** Hooves/Feet $\to$ Legs $\to$ Torso $\to$ Neck $\to$ Head $\to$ Accessories.

## 3. Lighting & Palette Standard
*   **Sky:** Soft atmospheric studio background (`#dbeafe` or `#b0c4de`).
*   **Key Light:** Warm Directional Sun (`#fff6e4`, Intensity 3.6), Pitch $48^\circ$, Yaw $12^\circ$.
*   **Fill Light:** Cool Sky Fill (`#bedeee`, Intensity 0.65, shadowless).
*   **Gorge Rim:** Subtle backlight (`#e6f5ff`, Intensity 0.50).
*   **Unified Color Palette (sRGB)**:
    - Weathered Cliff Rock: `(112, 106, 98)` (`#706a62`)
    - Meadow Turf: `(92, 132, 56)` (`#5c8438`)
    - Sunlit Plateau Cap: `(115, 155, 68)` (`#739b44`)
    - Vibrant Blue Water: `(42, 138, 178)` (`#2a8ab2`), emission `(48, 148, 192)`
    - Light Ledge / Stepping Stone: `(135, 129, 119)` (`#878177`)
    - Wood Trunk / Bark: `(88, 62, 44)` (`#583e2c`)

---

# Master Asset Blueprints

## 1. Stylized Oak Tree v2 (Master Blueprint)
*   **Trunk & Branches:** Tapered 7-sided cylinder base ($\varnothing = 0.85\text{m}$ at ground, tapering to $0.45\text{m}$ at $Z = 3.2\text{m}$). Two distinct structural branches fork outward at $Z = 3.4\text{m}$ to visibly support independent canopy canopies.
*   **Foliage Clusters:** Built from 3 to 4 distinct convex low-poly foliage clusters (main crown + 2 side secondary clusters).
*   **Color Uniformity:** Use unified leaf tones (`#4e8a36`, `#5c9c40`). NEVER place random darker green blob clumps sticking out unnaturally from the main crown.

## 2. Low-Poly Deer Pack Family (Stag, Hind, Fawn)
*   **Stag (Hươu Đực):**
    - Body: Angular faceted torso ($\#934b1f$ Warm Russet) + Cream Belly Inset ($\#f6ede0$).
    - Antlers: Procedural branching using bone-white material ($\#ede4d3$), main beam backward-curved with 3 pointed brow/bay/tray tines per antler.
    - Shoulder Height: $1.50\text{m}$; Antler Tip: $2.10\text{m}$.
*   **Hind (Hươu Mẹ):**
    - Slender, graceful neck, smaller head, NO antlers.
    - Softened russet tone ($\#9e5324$), cream chest and belly.
    - Shoulder Height: $1.30\text{m}$.
*   **Fawn (Hươu Con):**
    - Compact rounded proportions: shorter body, large alert ears, stubby legs.
    - Golden brown hue ($\#b45309$), soft cream spots along the spine.
    - Shoulder Height: $0.85\text{m}$.

## 3. Clean Low-Poly Rabbit (Thỏ)
*   **Body & Head:** Smooth low-poly organic mesh ($0.45\text{m}$ height).
*   **Clean Chest Rule:** The chest and belly must use seamless organic vertex coloring or unified geometry. NEVER apply square UV planar stickers or mismatched chest badges.
*   **Ears:** Dual-tone faceted ears (outer pelt `#e2d9cc`, inner ear pink inset `#e8a598`).

## 4. Starter 4-Square Storage Tile
*   **Footprint:** $4.00\text{m} \times 4.00\text{m} \times 0.25\text{m}$ elevated platform divided into 4 equal $2.00\text{m} \times 2.00\text{m}$ storage cells.
*   **Structure:** 4 carved corner wooden posts ($\varnothing = 0.28\text{m}$, height $0.60\text{m}$) with notched perimeter curbs framing the cells.
*   **Material:** Weathered timber planks (`#7a583e`) with recessed stone paving.

## 5. Mountain & Waterfall Pack (Master v11.0 Specification)
*   **Unified Mountain Massif:** The mountain is ONE continuous solid rock massif spanning $X \in [-13.5, +13.5]$ with a 2-tier step (Lower Terrace $Z = 4.8\text{m}$, Summit Plateau $Z = 8.5\text{m}$). NEVER create a separate "middle chunk" or sunken plug between left and right flanks.
*   **Flush Stepped Bedrock Chute:** The rock directly behind the waterfall chute has the EXACT stepped profile matching the chute (drops at $Y = 20.5, 18.8, 16.8$). Zero air gap behind the water from top to bottom.
*   **Wall-to-Wall Water Chute:** The water chute ($W = 4.84\text{m}$) spans the entire width of the gorge ($W = 4.80\text{m}$), embedding $2\text{cm}$ into the rock walls on both sides. Zero side gaps or exposed rock ledges along the stream.
*   **Contiguous Top Alpine Lake:** High mountain lake ($Z = 8.52\text{m}$) sits on the summit plateau and is WELDED DIRECTLY to the waterfall lip at $Y = 20.5$. 100% continuous fluid flow.
*   **Organic Non-Circular Plunge Pond:** Sunken pond basin at $Z = 0.18\text{m}$ inside ground cavity ($Z = 0.40\text{m}$). Must be an asymmetric organic fan-shaped polygon ($r \in [5.1\text{m}, 6.7\text{m}]$), NEVER a perfect geometric circle.
*   **Smooth Sinusoidal S-Curve River:** 28-point smooth parametric spline with $45^\circ$ sloped trapezoidal banks. Enters deep into the pond cavity at $Y = 11.5\text{m}$ to guarantee ZERO gray barrier line between pond and river.
*   **Clean Shoreline:** Pristine meadow grass meeting the water. NEVER place an artificial necklace of equally-spaced stones around the pond rim.

---

# Verification & Inspection Protocol (Rule 8)
1. **Visual Self-Audit Before Transmitting:** Every asset showcase must be rendered and visually inspected before delivery.
2. **Margin Standard:** Framing must maintain balanced margins $\ge 60\text{px}$ on all four edges.
3. **Contrast Standard:** Foreground entities must maintain distinct contrast ($\Delta E > 30$) against the background.
4. **Zero-Grayscreen Rule:** Blank canvases, washed-out tones, missing components, or inverted boolean normals are strictly rejected.

---

# 6. Procedural Nature Grammar v1.2 (2026-10-24)

**Authority:** `NATURE_UPGRADE_MANIFEST_2026-10-24.md` records reference-pack provenance, baseline comparison, numeric defaults, tests and licensing. Its figures are **proposed internal generation rules, not reverse-engineered measurements of the third-party pack**.

## 6a. Natural curves, NOT stacked rigid cylinders

Represent each growing stem/trunk/branch/root/log by one deterministic **cubic Bézier centerline**:

`P(t) = (1-t)^3 P0 + 3(1-t)^2 t P1 + 3(1-t)t^2 P2 + t^3 P3, t∈[0,1]`

Evaluate at 8–12 longitudinal sample rings. Each ring has 6–9 points around the local tangent. Compute stable frame by projecting the previous ring's normal into the plane perpendicular to the new tangent (parallel transport). Do NOT rotate independent rings by arbitrary Euler angles. Adjacent primary trunk tangents should turn <=22°, otherwise increase sampling or lower the bend. Position centerline in Z-up authoring space, export to Y-up glTF once.

Radius: `r(t)=baseRadius * (1-t*(1-tipRatio)) * (1+rootFlare*(max(0,1-t/0.18))^2)`. Use `tipRatio=0.18..0.30`, `rootFlare=0.15..0.40`. Radius must be >0 everywhere; cap the tube ends for closed solid geometry. This formula is a reusable starting point, not a botanical universal law.

Derived assets: mature/sapling trees, curved branches, exposed roots, stumps, wind-bent reeds, fallen logs and driftwood. To make a stump or log, **reuse the parent trunk's seed and measured cut radius**; do not generate an unrelated straight cylinder.

## 6b. Organic differentiation by *correlated* patterns

- **Broadleaf oak:** branch trunk at 0.36–0.78 normalized height, 2–5 primary branches with varied angle and height; branch base touches/penetrates parent tube, radius 0.35–0.70 of its parent radius at join. Crown comprises 3–6 **asymmetric** intersecting faceted lobes, attached to branch tips; preserve small negative spaces in silhouette.
- **Pine:** 4–7 partially-overlapping whorls; vary tier spacing, tilt and missing lower boughs. Never produce an exact stack of identical cones.
- **Birch:** slimmer trunk, off-axis sway, pale bark, fine branching; distinguish from oak by silhouette and material segmentation, not uniform scaling.
- **Rocks:** build with 6–10-sided angular ring profiles and 2–4 elevation bands. Apply spatially correlated radial deformation (do not jitter every vertex independently); flatten ground-contact surface, widen lower section; vary fracture orientation by rock family.
- **Bushes:** multiple rooted stems plus asymmetric crowns; fruit density controlled by harvest availability and season. Berry collection needs **no knife**. Woven berry basket is an optional carrying-capacity item, not job eligibility.
- **Grass / reeds / flowers:** 3–9 bent tapered blades/stems from rooted clumps. Reeds follow water proximity; grass blade length and lean share a local wind direction. Avoid rigid radial starburst and random floating tips.
- **Riverbanks/shorelines:** preserve the v1.1 continuous S-curve/pond/waterfall constraints. Scatter reeds along wet bank gradients; loose stones cluster below cliffs; mushrooms appear in damp shade. Use clustered distributions with minimum distances, never uniformly spaced rings of decoration.

Every random choice must use a **seeded generator** with independent named streams (`trunk`, `branches`, `foliage`, `scatter`) so changing foliage count does not change the whole trunk. Variation operates on a coherent family template, not on unbounded white noise.

## 6c. Asset factory contract

Input recipe: `LPM.NatureGrammar.v1`: `{species,seed,growthStage,season,heightM,trunk:{type,controlPointsNormalized,sides,radialSamples,baseRadiusM,tipRadiusRatio,rootFlare},branch:{levels,primaryCount,radiusRatioRange},foliage:{clumps,silhouette},palette,lod}`. Use the full example in the manifest.

Output:
- stable pivot at root contact with ground, meters, named mesh groups (TRUNK, BRANCH_*, FOLIAGE_*, ROOT_*, ROCK_*, etc);
- GLB Y-up once; optional Blender Z-up and THREE.BufferGeometry implementation;
- mesh/GLB summary for seed, bounds, part count, triangle count, materials, LOD and validation gates;
- a reference 1.80m settler placed adjacent in preview for scale.

Palette may be a shared atlas for batching. **Material isolation** (§1) still applies for *mutable* meshes: never recolor a shared THREE material behind another object's back. Read-only palette/instanced color attributes may be shared intentionally.

Suggested game LOD budgets: tree 900 / 350 / 90 triangles (LOD0/1/2), rock <=180, bush <=180, grass tuft <=90. Inspect actual GLB triangle and draw calls, not source polygon labels. Place high-detail LOD primarily near game camera; update seasonal instance variants without per-object material mutation.

## 6d. Required quantitative and visual gates

- **G1 Determinism:** same recipe+seed ⇒ identical vertex/index arrays; seed variants must differ yet stay within dimensions.
- **G2 Natural profile:** strictly positive radius, tapered overall envelope, root flare near base, nonzero controlled centerline curvature where specified.
- **G3 Surface quality:** no NaNs, collapsed triangles, flipped/zero-area faces or nongrounded roots; close solid components; attach all branches and lobes to supporting structures.
- **G4 Species & lifecycle:** oak/pine/birch silhouettes distinct; growth stages, felled log and stump maintain same seed/scale; seasonal fruit/leaf changes consistent with economy.
- **G5 Composition:** no equally spaced decoration, no systematic overlapping paths/buildings; random seeds tested in groups, with four seasons.
- **G6 Render & perf:** four orthographic views + isometric in-world screenshot, compare against 1.80m settler and target references; budget triangles/draw calls at worst camera.

Reusable **pure-Python, no-dependency** centerline+meshing reference and tests: `scripts/nature_curve_grammar.py`. Keep existing oak/waterfall production meshes until the new generated assets pass these gates and visual comparison.

## 6e. Attribution and third-party boundary

The CGTrader yukekbyte “Low Poly Nature Environment with Trees - Rocks - Plants” is a **design benchmark**, not a vendored dependency. Listing indicates royalty-free **No AI** licensing. Do **not** copy/distribute its raw 3D meshes or palette texture into this MIT repository, use it for AI model training, or describe inferred curve values as observed measurements. Gameplay use requires lawful acquisition and license compliance. For actual geometric A/B verification, obtain the files lawfully and compare in a local Blender scene; current benchmark is listing-level only.

---

# 7. Runnable Example Catalogue — All Nature Categories (v1.2 supplement)

This sub-skill now includes an **original procedural example factory** and a **category-level comparison manifest** covering all categories publicly listed by yukekbyte's CGTrader nature pack. The original CGTrader mesh binaries were **not** inspected or copied.

- [Full comparison manifest and geometry/growth specs](NATURE_UPGRADE_MANIFEST_2026-10-24.md) — coverage matrix for trees (6), bushes (7), flowers (2), mushrooms (4), rocks (12), plants (6), clouds (3), wood items, cliff, bridge, and 12 grouping recipes. Distinguishes what is observed on the public listing vs design targets.
- [Procedural JavaScript example generator](scripts/nature_asset_examples.mjs) — 46 independent parametric variants, 12 scene groupings, `makeAsset`, `toThree`, `audit`, `toOBJ`; all authored in Three.js Y-up meters, with seeded variation and semantic palette.
- [Runtime Node test](scripts/test_nature_asset_examples.mjs) — procedural reproducibility, finite/non-degenerate triangles, OBJ output, category traversal.
- [Interactive Three.js gallery](examples/nature_gallery.html) — inspect category, variant, seed and 1.8m settler scale next to the generated asset.
- [Existing Python curve generator](scripts/nature_curve_grammar.py) — swept Bézier trunk with proper transported ring frames.

Quick-start from this skill directory:

```bash
node scripts/test_nature_asset_examples.mjs
python3 scripts/nature_curve_grammar.py --test
python3 -m http.server 8000
# Open http://localhost:8000/examples/nature_gallery.html
```

Three.js embedding:

```js
import * as THREE from 'three';
import { makeAsset, toThree, audit } from './scripts/nature_asset_examples.mjs';
const oak = makeAsset('tree', 0, 29);
const flower = makeAsset('flower', 1, 42);
console.log(audit(oak)); // geometry size and material metrics
scene.add(toThree(THREE, oak));
scene.add(toThree(THREE, flower));
```

**Do not conflate public pack inventory with validated geometric similarity.** The example generator is a new baseline with approximate, consciously authored silhouettes. A genuine one-by-one accuracy comparison requires lawful access to CGTrader's original files, followed by Blender metric captures and equal-camera renders. Do not treat the included third-party license as MIT.

**CI status:** GitHub Actions nature-grammar run [40106501651](https://github.com/HUNGPHAM789/lpm-faceless-humanoid/actions/runs/40106501651) completed the Node nature asset example tests and Python curved-trunk checks successfully (2026-10-24).

**Known work remaining:** browser/gallery QA, real-engine load and profiling, external binary A/B analysis, production-ready biome masks and grouping/path collision, seasonal mesh morphs, real GLB exporter, visual LOD, and proper shared atlas UVs. The example uses simple per-face semantics and is not a drop-in replacement for the currently approved island scene assets.

# Nature World Upgrade Manifest — 2026-10-24

Status: SPEC-LEVEL BENCHMARK (not binary/model audit) | Target skill: procedural-low-poly-world v1.2 | Owner: SURVIVAL JOURNEY

## Reference / provenance

- Reference pack: **Low Poly Nature Environment with Trees - Rocks - Plants**, yukekbyte, CGTrader, model #4801050.
- URL: https://www.cgtrader.com/free-3d-models/various/various-models/low-poly-nature-models
- Listing checked: 2026-10-24.
- Listing states: ~50 assets, 6 trees, 7 bushes, 2 flowers, 4 mushrooms, 12 stones, 6 plants, 3 clouds, a log, trunk, log pile, cliff, bridge, demo scene, and 12 grouped arrangements; .blend/.fbx/.obj/.stl + a shared palette PNG; consistent origins/scales. FBX files intentionally do not duplicate the shared material. The creator states each model is under 999 polygons / 2099 vertices.
- License displayed on the listing: **Royalty Free License (No AI)**. Under CGTrader license 21B, **No AI** prohibits model use for machine learning/training, including generative AI models. Do not assume free == public domain or MIT. Source files must not be added to this public MIT repo. Any later game incorporation requires the actual asset acquisition under the seller's license and distribution as an incorporated product under applicable terms.
- **Evidence boundary:** this analysis uses the publicly accessible listing and the CURRENT LPM skill spec; no licensed binary model, scene files, mesh topology, textures, or side-by-side renders were retrieved/inspected. Curve radii/angles below are **new internal design targets**, not measurements claimed from yukekbyte's meshes. A true geometric A/B analysis is still pending possession of the original pack.

## Baseline: currently documented LPM nature assets (skill v1.1)

| Current item | Existing strength | Gap / action |
| --- | --- | --- |
| Oak v2 | 7-sided tapered trunk, forked branches, 3–4 convex canopy clumps, measured 5.8–6.5m height | Only base-to-top taper and prescribed forks; add bent centerline, transported radial frames, root flare, repeated seed variants, growth stages, silhouette tests. |
| Pine | 3 conical canopy tiers and 6.5–7.5m scale | Replace uniformly repeated cone-stack outline with offset whorls, tier taper, asymmetric sag and dead/bare variants. |
| Birch | Height and slenderness defined | Add species-specific off-axis lean, fine fork density, pale trunk segmentation; avoid generic scaled oak. |
| Rock / gorge | One massive contiguous waterfall mountain and organic pond/river shape already specified | Add reusable individual pebble / boulder / slab / cliff-face facet grammars, stratification and fracture families. Preserve waterfall's continuous topology rules. |
| Berry bush / plants | Fixed berry-bush scale and game role | Add multi-stem bush structure, leaves, seasonal berries, foraging stages, flowers, mushrooms, grass and reeds. |
| Nature set composition | Fixed palette and explicit world reference scale | Add shared palette atlas option, pivot/naming contracts, 12-style grouping templates, correlated spatial distribution and LOD budgets. |
| Environment validation | Strong framing / silhouette / no-gap checks | Add numerical curvature, taper, root/branch connection, manifold-per-part, seed reproducibility, distinct variation, and LOD checks. |

## 8 transferable nature grammars (new; not copied from third-party meshes)

1. **Curved grown wood:** cubic Bézier or cardinal centerline; parallel-transport tube rings, 6–9 sides, smoothly tapering radius plus localized buttress/root flare. Tree trunks, limbs, roots, fallen logs, driftwood, reeds, winding wooden rails share this grammar.
2. **Hierarchical branching:** deterministic recursion with parent-attachment points and nonuniform phyllotaxis; child radius <=0.70 parent local radius; tree species choose branch angle, sag, tropism and taper rather than duplicating cylinders randomly.
3. **Clustered foliage:** 3–7 intersecting asymmetric faceted volumes, attached to branches, crown negative spaces visible; apply coherent whole-cluster color variation, not uncontrolled vertex noise.
4. **Angular fractured stone:** 6–12-sided irregular profiles, flattened base, displaced middle bands, oriented fracture planes; boulders, pebbles, cliff chunks and stone slabs use different width/height ratios and facet direction.
5. **Vegetation tufts:** central root point with 3–9 bent tapered blades, curved stem arcs and per-blade silhouette variation; reeds favor vertical tropism; grasses fan outward; flowers terminate in flat radial petals.
6. **Organic scatter pattern:** Poisson-like blue-noise for minimum spacing, environmental masks, clusters via several parents + child offsets; no square/equidistant decoration. E.g. mushrooms in damp shade, reeds near bank, rock talus below cliff.
7. **Weathering / lifecycle:** young/mature/dead/felled variants share species seed; canopy density and colors change by season; felled log retains trunk's curvature and bark, stump carries matching cut radius, foraging depletion affects fruit volume only.
8. **Single-palette batching:** constrained semantic palette (bark, sapwood, foliage light/shade, earth, stone, moss), optional one shared atlas; keep per-mesh material isolation when recoloring individual instances, but permit read-only material sharing and instancing for static identical hues.

## Procedural numeric profile (PROPOSED defaults; meters, 1.80m settler anchor)

- Coordinate authority: procedural authoring Z-up, ground at Z=0. Export glTF/GLB with Y-up transform **exactly once**, not twice.
- Broadleaf adult: height 5.8–6.5m; basal radius 0.36–0.46m; lean at crown 0.06–0.16 of height; 7-sided trunk; 8–12 longitudinal centerline samples; taper tip/base radius 0.18–0.30; buttress amplification 1.15–1.40 limited to first 0.18 normalized height.
- Smooth centerline: adjacent tube tangents <=22 degrees for primary trunk; fork sharper only at branch junction. Never make each ring choose an unrelated random radial offset.
- Branching: 2–5 primary branches; origins at normalized trunk height 0.36–0.78; child radius 0.35–0.70 times parent *local* radius; crown open-space target 12–30% of projected crown bbox (style/QA review, not computable simply by triangle count).
- Canopy: 3–6 major clumps for oak; main clump broad, side lobes at differing heights; center offset each lobe by 0.10–0.45 its own radius; overlapping lobes should read as one crown, but not as 3 identical green balls.
- Pine: 4–7 partially overlapping radial whorls, tapered height hierarchy, angle jitter <=15 degrees per tier; several lower branch gaps. Keep canonical height 6.5–7.5m.
- Rock: 6–10 radial sides, 2–4 irregular height bands, top flattening, base wider than crown; local correlated displacement amplitude 0.04–0.16 of width and constrained hue variation.
- Mushroom: stem visibly supports cap, 5–8-sided cap, no floating faces; low-height clusters at 0.08–0.30m.
- Grass/flowers: grouped blade lengths, coherent wind bias, nonuniform spacing; avoid repeated identical radial starburst.
- Asset LOD targets (game **triangle** counts, not the reference's claimed polygons): hero tree LOD0 <=900, LOD1 <=350, LOD2 <=90; rock LOD0 <=180; shrubs LOD0 <=180; individual grass tuft LOD0 <=90. These are targets to benchmark, not guarantees.
- Mesh parity: valid winding, finite vertices, zero-area faces 0, watertight closed solid *components* where appropriate (open cut planes/plants may be intentionally open), no unparented floaters, all roots visibly seated at ground.

## Golden tests / gates

G1 seed reproducibility: same species, seed and parameters emit byte-for-byte equivalent numerical geometry.
G2 variation: seeds 3/11/29 differ in centerline and canopy silhouette but preserve species proportions.
G3 curved trunk: main-axis displacement between bottom and crown exceeds 0.05H on the curved sample, without teleporting between centerline samples.
G4 tapered trunk: radius decreases in overall envelope from ground to top, except deliberate root buttress; no negative radii / zero-area triangles.
G5 branch contact: branch base is inside or touching its parent tube; no visually disconnected twig, canopy must be supported.
G6 anti-uniformity: no equally spaced trunk fork attachments, equal-sized foliage blobs, or identical rotations among near neighbors.
G7 scene: tree+stump+log share matching radius; terrain follows shoreline slope; no gaps in river/waterfall; saplings/canopies do not overlap gameplay buildings or paths.
G8 perf: each exported GLB logs triangle count, material groups and approximate draw-call count per distance band; test worst camera and 4 seasons.
G9 preview: render 4 isolated rotations plus isometric island placement; compare 1.80m humanoid anchor and benchmark references visually.
G10 licensing: only original procedural assets/code in repo; external model binaries stay in separately licensed game assets once acquired properly.

## API/data contract for re-creation

```json
{
  "schema": "LPM.NatureGrammar.v1",
  "species": "oak",
  "seed": 29,
  "growthStage": "mature",
  "season": "autumn",
  "heightM": 6.2,
  "trunk": {
    "type": "cubic_bezier_tube",
    "controlPointsNormalized": [[0,0,0],[0.02,-0.02,0.31],[0.13,0.0,0.71],[0.09,0.05,1.0]],
    "sides": 7,
    "radialSamples": 10,
    "baseRadiusM": 0.41,
    "tipRadiusRatio": 0.23,
    "rootFlare": 0.28
  },
  "branch": {"levels": 1, "primaryCount": 4, "radiusRatioRange": [0.35,0.65]},
  "foliage": {"clumps": 4, "silhouette": "lobed"},
  "palette": "warm_earth_v1",
  "lod": 0
}
```

The recipe is independent of target rendering engine; geometry adapters implement THREE.BufferGeometry and Blender mesh or glTF. The same centerline/tube tool can create roots, branches, fallen logs, reeds, vines and riverbank driftwood.

## Next actions once original downloadable files are obtained lawfully

1. Import purchased/downloaded .blend/.obj in Blender (local workspace, not public repo); record object count, pivots, bounds, topology, triangle counts and atlas resolution.
2. Produce side-by-side 3/4 and silhouette renders under **identical** camera, light and scale; measure actual centerline bend distribution, trunk-to-crown ratios and canopy volumes.
3. Replace provisional numeric defaults only if measurement or visual QA justifies it; attach audit values rather than claiming hypothetical matches.
4. Integrate the actual licensed pack into the GAME build only as applicable under the seller's redistribution terms; never push its raw binaries to LPM MIT repo.

Related:
- `skills/procedural-low-poly-world/SKILL.md` (master skill, v1.2)
- `skills/procedural-low-poly-world/scripts/nature_curve_grammar.py` (original proof-of-concept geometry)
- https://www.cgtrader.com/pages/terms-and-conditions (§21A/§21B)


---

## 2026-10-24 coverage supplement — flowers and *all* publicly listed pack categories

This is a **catalogue-to-capability** comparison, **not** a vertex-level comparison of the downloaded CGTrader meshes. The public CGTrader listing explicitly enumerates:
6 trees, 7 bushes, 2 flowers, 4 mushrooms, 12 stones, 6 plants, 3 clouds, 1 log, 1 treetrunk, 1 pile of logs, 1 cliff, 1 bridge and 12 groupings. They use one color-palette texture, consistent origins/scales, and the listing claims each source asset is below 999 polygons and 2,099 vertices. The listed Unity water shader, waterfall particles, and demo Unity project are NOT included. See: https://www.cgtrader.com/free-3d-models/various/various-models/low-poly-nature-models

### Coverage matrix: present LPM v1.1 versus original generator examples

| CGTrader listing item | Source count | Older LPM nature spec | New independent LPM code example (`scripts/nature_asset_examples.mjs`) | Reusable geometric grammar & improvement |
|---|---:|---|---|---|
| Trees | 6 | Oak v2 with 7-sided taper, pine 3 cones, birch height only | 6 variants: broadleaf, pine, birch, wide-crown, bare/dead, young | Curved Bézier sweep trunk, coherent ring frames, trunk taper/root flare, branch forks, variable lobes, missing/offset pine whorls |
| Bushes | 7 | Berry bush height, role and broad concept | 7 seeded shrub silhouettes: berry/dense/sparse/flowering/broad/young/dry | Rooted multiple branch tips, asymmetric foliage, season-dependent fruit and harvest metadata *still to integrate* |
| Flower meshes | 2 | No flower geometry blueprint | 2: 6-petal radial wildflower and downward bell blossom (each makes 3 flower stems) | Stem sweep + elliptical radial petals or drooping asymmetric bell; central disk; reproducible petal ring and variable bloom timing |
| Mushrooms | 4 | Basic environment mentions mushrooms | 4 styles: rounded red cap, tall brown bell, low flat gold cap, small cluster | Organic cap profile with a grounded stem; multiple stem groups, supporting cap junction and safe forest scatter |
| Stone models | 12 | Cliff and mountain/waterfall master, generic faceted rock | 12 scale/shape/family variants incl. rock clusters, pillar, wide boulder and moss | Radial irregular faceted volume, correlated radius noise, base-contact and cliff-fall family |
| Plant models | 6 | Berry bush only; no code grammar | 6: grass fan, fern, reed, broadleaf herb, cattail, small tuft | Leaning tapered blades, 3D stems, fern leaflets, reed seedheads, species-ground masks |
| Clouds | 3 | Sky/lighting but no cloud mesh recipe | 3 layered lobe clusters | Soft asymmetry via grouped low-sided volumes; sun silhouette and distance LOD |
| Fallen log | 1 | Tree trunk dimensions, no fallen lifecycle code | 1 bent log asset with seed variation | Horizontal swept tube from Bézier; cut-end proportions; pair with parent-tree seed in game later |
| Treetrunk | 1 | Tree trunk embedded in standing oak | 1 bare trunk with trimmed branches distinct from stump | Branch-supported trunk without canopy, fracture/cut stage |
| Log pile | 1 | No log pile generator | 1 five-log stack | Repeated seed-varying curved logs, grounded pile, stable load silhouette |
| Cliff | 1 | Strong one-piece gorge topology + waterfall specs | 1 procedural grouped faceted cliff example | Connected/fitted terrain rock slabs; individual example is NOT a replacement for validated v11 waterfall master |
| Bridge | 1 | No generic bridge grammar | 1 simple plank-and-post bridge | Rhythmic plank assembly with small coherent warp; would need collision and shoreline foundations for production |
| Scene groupings | 12 | One scenic composition / biome rules | 12 deterministic scene recipes (positions & asset metadata) | Clustered ecology with positive/negative space, no regular repeating rings |
| **Bonus: stump** | not separately listed | No stand-alone stump code | 1 rooted cut stump | Trunk taper and visible sapwood/cut surface; for logging gameplay |

**Count of supplied ORIGINAL generator examples: 46 parametric asset variants plus 12 grouping recipes = 58 demonstrable cases.** They deliberately provide catalogue breadth rather than replicating the reference artist's mesh shapes, UV coordinates, material colors or exact counts.

### Code layout and runnable examples

- `scripts/nature_curve_grammar.py` — pure Python curved Bézier tube, mesh verification example, Z-up authoring.
- `scripts/nature_asset_examples.mjs` — zero-dependency ES module for procedural assets, Three.js-compatible **Y-up** in meters. Exposes `makeAsset(kind,variant,seed)`, `toThree(THREE,mesh)`, `audit(mesh)`, `grouping(index,seed)`, `toOBJ(mesh)`, and `catalogue()`.
- `scripts/test_nature_asset_examples.mjs` — Node test: loops all 46 meshes and 12 groupings; asserts triangle sanity, finite/area data via `audit`, deterministic seed and OBJ face presence. Run `node scripts/test_nature_asset_examples.mjs`.
- `examples/nature_gallery.html` — browser demo using Three.js CDN. Run from the skill directory `python3 -m http.server 8000`, open `http://localhost:8000/examples/nature_gallery.html`; use selectors for type, variant, seed. This is a gallery of *our generated meshes*, not licensed CGTrader asset screenshots.

Minimal ES module:

```js
import * as THREE from "three";
import {makeAsset, toThree, audit} from "./scripts/nature_asset_examples.mjs";
const flower = makeAsset("flower", 0, 29); // wildflower
const mushroom = makeAsset("mushroom", 3, 29); // small cluster
const stone = makeAsset("stone", 10, 29); // large boulder
console.log(audit(flower)); // triangle/material/bounds summary
scene.add(toThree(THREE, flower));
```

Examples can be freely altered by species recipe and seed, but **new code has not been validated by Blender render, compared against the licensed pack's actual mesh files, or guaranteed production-ready**. Each generated category needs visual acceptance under the same camera and lighting conditions.

### Style specs proposed for flowers, fungi, plant groups and small decorations

- **Flowers:** low-poly petals converge on a visible head; 5–7 distinct leaf blades/petals per radial species; bell species point down; 1–3 stems in patch; stem diameter stays visibly thinner than flower diameter, no disconnected flower heads. Example default stem length 0.45–0.70m.
- **Mushrooms:** proportion defined by cap-to-stem width (example 2.2–5.0x), cap volume type (bell/convex/flat) and stem angle. Cap underside contacts stem, red/earth tones from semantic palette, clusters overlap ground but not each other excessively. Example height 0.18–0.35m.
- **Grass / reeds:** 3–9 curved blades with several height groups; align broad tilt to wind + local noise, not independent random spikes; reeds/cattails prefer riparian mask, herbs in pasture, fern and mushroom in shade. Example grass 0.20–0.45m, reed up to 0.85m.
- **Stones:** choose small pebbles, medium boulders, tall pillars and large slabs via aspect ratios before vertex displacement; avoid same perfect sphere scaled everywhere; moss as separate palette region only where moisture/lighting justify.
- **Clouds:** cloud clusters are not placed at island ground level in production; the geometry is authored around its local pivot then translated to cloud height by scene composer.
- **Bridge:** direct primitive planks are for shape prototyping only; bridge collision, slope connections and physical logistics remain game-specific extensions.

### Checklist for the NEXT quantitative comparison with actual reference binaries

- Obtain the pack legally, and handle its No-AI terms; **do not ingest its models into model-training, copy meshes into this MIT repo, or silently redistribute its texture**.
- Blender audit per exact source asset: name, type, vertex/triangle count, bounding box, pivot, UV coverage, material atlas use, scale, branch/crown centerline profiles, silhouette and color palette.
- Compute matching metrics on **our own** asset; use side-by-side silhouettes at identical 1.80m settler scale with same camera and lighting. Record measured deltas.
- Revise only those new internal grammar parameters supported by actual audit; do not falsely describe provisional numeric defaults as observed characteristics of the seller's mesh.

### Code-check status at commit time

- JS authoring-time audit evaluated all originally implemented variants through deterministic seeded meshing, geometry/triangle summary and hard polygon budget; no geometry exceptions reported.
- The Node script and Python Bézier tube test were **executed successfully** by GitHub Actions (nature-grammar.yml), run [40106501651](https://github.com/HUNGPHAM789/lpm-faceless-humanoid/actions/runs/40106501651) on 2026-10-24; both job steps concluded SUCCESS. The browser Three.js gallery, rendered imagery, Blender topology analysis and any comparison against actual CGTrader mesh binaries have **not** been executed/verified.

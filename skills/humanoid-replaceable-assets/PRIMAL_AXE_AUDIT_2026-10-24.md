# LPM Procedural Primal Axe — Visual-to-Mesh Audit / Missing Skill Logic

**Reference**: user-provided 297×541 PNG `references/09_primal_axe_reference.png`, not a mesh. The displayed object has a **dark chipped-stone** axe head, beige wooden handle and dark leathery X lash. This is **not visibly an ivory/bone head**. To satisfy both the requested reference and the Bone Age gameplay, we generate TWO distinctive variants using the SAME mesh contract: stone and bone.

## Comparison values (reference vs code)

| Feature | Reference pixel observation | Generated 3D metric / decision | Status |
|---|---|---|---|
| Overall height | Approx y=26..514 in 541px; H≈488px | GLB Y bounds −0.426 to +0.600 m, H=1.026m | Chosen 3D scale, not recovered from screenshot |
| Overall chopping-side width | Approx x=45..255, W≈210px ⇒ W/H≈0.430 | GLB X bounds −0.1105 to +0.3261m ⇒ W=0.4366m, W/H≈**0.426** | MATCHES 2D proportion within screenshot-estimation tolerance |
| Head orientation | Large mass extends to camera-right, small hammer stub left | +X is blade/chopping side, −X back stub; asymmetrical faceted perimeter | MATCH |
| Stone material | Almost-black cool slate, chipped irregular broadside, nonmetallic | 16-point rough head outline, 2 bevel layers front/back, face-color jitter, dark slate | PASS structural, visual likeness needs game renderer |
| Shaft | Pale warm tan natural wood, subtly bowed and rounded at butt/tip | 8 curved ring stations × 9 radial sides; taper radius grip .016m; wood-based material | PASS geometric; wood grain is suggested by facets, not texture |
| Head connection | Stone at upper end with exposed wood tip above head | Head offset behind shaft at local depth +0.070m; upper wood tip reaches +0.600m | PASS mechanically layered look |
| Leather X | Two diagonal wide brown leather strips on both faces of wood; multiple circular bands | 4 3D diagonal strips, 4 spiral/circular segmented bindings; each ribbon is watertight convex strip | PASS structure; physical friction/tension not simulated |
| LPM hand grip | Not measurable from photo; LPM skill needs Ø32mm grip | EXACT authored tool origin `(0,0,0)` with `.016m` wood radius; GLB up +Y, blade +X | PASS procedural construction, posed IK check pending |
| Asset budget | Reference screenshot has no polygon information | **944 triangles**, 58 individual watertight segments merged into **4 scene geometry batches**, 23,964 byte GLB | MEASURED from generated GLB |
| Prototype lifecycle | Tool is used repeatedly and eventually wears out | JSON defaults `durability_max=55`, `durability_loss_per_chop=1`, discard at 0 | Example only, gameplay balance not confirmed |

**Source ratio caution:** photo includes perspective and studio cropping; the 0.430 ratio is a rough silhouette measurement not proof of source mesh dimensions. Code numbers are measured from the exported GLB using Trimesh.

## What the existing tools skill lacked; new production directives

1. **Curved shaft grammar:** A linearly tapered cylinder still looks synthetic. Author 6–10 axial cross-section stations, interpolate a coherent arc and wood thickness to follow growth grain. Keep one explicit grip station at exactly required LPM socket radius.
2. **Organic + engineered junctions:** Haft is one naturally curved wooden solid; stone is a CLOSED irregular flint solid behind the shaft; leather straps are their OWN volumes over both. Do not fuse stone and wood into one hull or decorate with flat coplanar lines.
3. **Chipped stone geometry:** Bias silhouette extension toward the cutting side; generate an uneven near-convex perimeter, inset a bevel ring and fan broad planar faces with color facets. Distinguish blade edge from back stub by wedge thickness and length.
4. **Binding grammar:** Calculate 3D ribbon centerlines and extrude narrow thickness; front/rear X cross, circumferential windings, varying overlap; prevent intersecting wood where possible. A twist can be modeled but needs physical collision/visible-depth audit.
5. **Physical socket contract:** Author handle +Z along shaft with origin grip and blade +X; **export Y-up once** (then handle +Y). No loose auto-centering or automatic rescaling on import because both invalidate socket alignment.
6. **Render cost:** Each fastening segment is an auditable solid, but joining by material reduces scene groups from 58 to 4. Future Tool Rack requires instance batching and rack attachment pivots; 58 draw calls per axe is unacceptable.
7. **Reference-first silhouette metric:** compare source image ratio `W/H` against re-exported GLB orthographic projection before declaring similarity. Initial prototype head was W/H≈0.61, visibly too broad; revised output ratio≈0.426.
8. **Variants:** same attachment, length and grip can support stone dark-slate and bone ivory alternative; gameplay durability/crafting recipes vary without re-rigging the worker.
9. **Animation/contact audit:** hold tool through swing, sprint and idle transitions; confirm palm wraps correct Ø32mm section, blade points outward and wrist axis does not flip. No claim of acceptance until an actual posed settler is tested.
10. **Quality gates:** numeric triangles, manifold integrity, all finite vertices, GLB Y up, blade axis, front/back strap visibility, isometric camera preview, and deterministic generator rebuild.

## Generator/output and test


defaults: `python scripts/build_primal_axe.py --out ./out/primal_axes --variant both`

Output: `primal_stone_axe.glb/.obj/.json` and `primal_bone_axe.glb/.obj/.json`. Source build is pure procedural Python with `numpy`, `scipy` and `trimesh`; no external 3D meshes/UVs/material maps used. The locally exported GLBs were checked for finite coordinates, mesh watertightness, triangle count and Y-up bounds. Compare both generated GLBs with repo-committed GLBs using the **Primal LPM geometry gates** GitHub workflow.

## Open audit blockers

- No original source `.blend`/`.fbx`/`.obj` for the photographed axe; can only compare visual evidence, not replicate exact topology.
- Lashings are geometric closed volumes but have not been collision-simulated as tensioned leather; after animation, check interpenetration and rack-hang center of mass.
- Source screenshot lighting/material maps are unknown; faceted vertex colors are an original stylization, not a copy of any source texture.
- No Blender/OpenGL 4-view render sign-off; Matplotlib mock view is illustrative and not a full in-engine shading test.
- Bone variant is a gameplay design extension, not a claim that the photographic axe head is bone.
**The biggest problem is the shape grammar, not the triangle budget.** The reference has broad, interlocking hair masses, a solid sculpted beard, and overlapping hide panels. V1 has small blades attached to a cap, a beard shell covered with teeth, and stacked toothed tubes.

I audited the supplied images and files read-only. Below, observations are visual; proposed v2 dimensions are **starting targets to validate against the images**, not measurements of an unavailable official mesh. Image 1 should control the multi-view silhouette; image 2 clarifies surfaces and colour.

**1. A — Ranked visual differences**

Ranks indicate impact on resemblance, highest first. The B entries below use the same numbers.

| Rank / part | Official reference | V1 |
|---|---|---|
| **1 — Hair mass and clump scale** | Broad, overlapping wedges form a coherent, substantial hairstyle. Relatively few large shapes dominate. | Many small, narrow spikes create a bristly, fragmented surface. The cap remains readable beneath them, especially at the back. |
| **2 — Skirt construction and layers** | Large, irregular hide panels overlap diagonally. Their outlines continue well up the garment. | Two continuous horizontal bands with serrated lower edges. Reads as stacked skirts rather than overlapping hides. |
| **3 — Beard volume and outline** | A continuous, chunky cheek–jaw–chin mass, tapering into a broad angular chin. Sideburns connect convincingly to it. | Thin face-hugging shell with separate downward teeth. The lower outline is stringy; fitted close-ups show especially thin projections and interrupted-looking surfaces. |
| **4 — Hair silhouette and flow** | Broad fringe falls onto the forehead; crown peaks are selective; side/back locks sweep outward and downward into a substantial nape. | High, comparatively open forehead; numerous upward/outward ticks; smaller scattered side/back projections. Crown and perimeter feel uniformly busy. |
| **5 — Skirt silhouette and hanging shape** | Uneven, directional hem; panels hang from the waist and overlap over the hips. Large pointed ends create the silhouette. | Strong waist-to-hip cone, then a bulky lower band. Horizontal ledges and repeated teeth dominate. Front/back are too regular and similar. |
| **6 — Lining and colour composition** | Broad tan areas interrupt the dark leather, including substantial diagonal reveals extending upward between dark panels. | Tan mostly appears as a narrow row of bottom teeth. The fitted version loses still more of the intended role separation. |
| **7 — Facet/shading language** | Broad, readable planes under soft lighting. Hair, beard and leather look angular but solid and matte. | Smooth gradients across skirt tubes, with tiny bright/dark fragments on hair and beard. The scale of surface detail is inconsistent. |
| **8 — Moustache and cheek boundary** | Wide, thick moustache under the nose, with two clear lobes; cheek coverage rises toward the sideburns and descends toward the chin. | Moustache merges into a narrow horizontal beard band. The broad reference moustache and purposeful cheek outline are weak. |
| **9 — Belt** | Thick, irregular, pale rope-like band seated against the hide, with visible bends and lobes. | A comparatively straight, level hoop that projects at the sides. In image 4 it becomes dark, losing a major identifying colour accent. |
| **10 — Ornament** | Prominent elongated stone pendant extending downward over the leather. | Tiny diamond-like bead. Too short and visually subordinate to the belt. |
| **11 — Overlap and attachment** | Clump roots disappear under neighbouring masses; hide panels visibly overlap without looking detached. | Individual hair blades often look pasted on. Skirt overlap becomes a circumferential ridge rather than local panel layering. |
| **12 — Triangle/detail distribution** | Larger planes on broad surfaces, smaller ones where curvature and outlines need them. | Many tiny hair facets beside large smooth garment spans. Repetitive narrow triangles and tooth tips consume detail without improving the main shapes. |

Colour comparisons have a lighting limitation: the images use different lighting and backgrounds. **The fitted belt/material loss, however, is confirmed in code**, not inferred from lighting.

**2. B — Root causes, mapped to A**

For compact references, `H` means `build_spiky_hair.py`, `O` means `build_torn_outfit.py`, and both are under `skills/stylized-lowpoly-humanoid/scripts/`.

1. **Small hair clumps — wrong statistical target and construction.**  
   The hair spec’s `regions.male.*.clumps_per_sample_min_med_max` targets teacher-mesh segmentation counts, not visually authored locks. Its own source is generated Hunyuan meshes, not the original topology. V1 actually creates **76 scalp clumps: 16 fringe, 30 side, 24 back, 6 crown**.

   [H:224](~/projects/lpm-faceless-humanoid/skills/stylized-lowpoly-humanoid/scripts/build_spiky_hair.py:224) hardcodes those rows. H:163–183 makes each lock the same nine-triangle triangular-section blade; H:254 caps width at 5 cm and forces length/width between approximately 1.1 and 2.6. This excludes the particularly broad crown masses allowed by the spec’s own crown median L/W of 0.82.

2. **Horizontal skirt bands — wrong construction method, explicitly encouraged by the spec.**  
   [Outfit spec:47](~/projects/lpm-faceless-humanoid/skills/stylized-lowpoly-humanoid/spec/SPEC_primal_torn_layered_outfit.md:47) says: **“the two TIERS replace rows.”**  
   O:137–155 constructs complete rings with only the final ring serrated. O:197–224 closes those rings into sheets. No individual flap has its own root, longitudinal edge, diagonal overlap or drape.

   The spec’s `flaps.length_cm`, `width_cm`, and aspect statistics therefore do not meaningfully control the visible panel construction.

3. **Thin/toothed beard — wrong shape model, compounded by fitting.**  
   H:277–315 constructs a closely offset jaw shell and hanging bib; H:326 adds **11 beard blades**, rather than a small number of broad sculpted lobes. `BEARD_GAP = 0.0035` controls contact but supplies no outer-volume design.

   [Fitter engine:400](~/projects/lpm-faceless-humanoid/skills/character-fitter/scripts/fit_engine.py:400) sets `BEARD_CAP = 0.015`. Lines 417–426 compress selected beard vertices using  
   `d → cap × (1 − exp(−d/cap))`.  
   This also acts on outer beard geometry, rather than only its attachment surface. The fitted report confirms a beard p90 distance of **14 mm**. Exact per-vertex visual damage would require comparing the pre/post meshes, but the volume-reducing mechanism is explicit.

4. **Wrong hairline/flow — wrong anchor plus insufficient directional rules.**  
   `male_measurements.json` gives `hairline_y = 1.7765` and `head_top_y = 1.7973`: the front anchor is only **20.8 mm below the skull top**. H:73 uses that directly. The resulting short forehead fringe is visible in v1.

   The hair spec’s `flow_rule` broadly prescribes male up/out flow. H:245–251 adds random lateral direction and jitter, with only the lowest row switched downward. There is no authored fringe sweep, crown parting or coherent nape flow.

5. **Bulky, regular skirt envelope — wrong hanging rule and repeated hem layout.**  
   [O:121](~/projects/lpm-faceless-humanoid/skills/stylized-lowpoly-humanoid/scripts/build_torn_outfit.py:121) says the radius **“never shrinks”** below the widest hip; it accumulates per-column maximum radii and adds flare. This carries a local body bulge downward into the whole garment.

   O:36 fixes 24 columns, with eight regularly spaced teeth per tier. O:143 changes heights through small random jitter, not designed asymmetry. O:333–359 anchors entire tier edges at common heights. Clearance pushes can further inflate the envelope; they do not create hanging panels.

6. **Weak lining reveal — wrong reveal rule; fitted materials are destroyed.**  
   The outfit spec restricts lining chiefly to the lower region and specifies teeth just **1–3 cm longer**. O:347 implements a bottom lining band with tips 3.5 cm longer, rather than broad diagonal reveals.

   More seriously, [fit_character.py:60](~/projects/lpm-faceless-humanoid/skills/character-fitter/scripts/fit_character.py:60) rebuilds the fitted asset as a mesh without preserving its role materials. Lines 75–76 assign **one material per fitted layer**. Thus dark leather, tan lining, pale belt and stone inside the lower-garment asset lose their individual colours.

7. **Smooth/plastic appearance — renderer overrides the authored look.**  
   [render_turnaround_blender.py:28](~/projects/lpm-faceless-humanoid/skills/stylized-lowpoly-humanoid/scripts/render_turnaround_blender.py:28) reduces roughness to at most 0.6; line 30 sets **every polygon’s `use_smooth = True`**.

   `primal_body_frame.py:108–115` creates materials but establishes no explicit facet-normal contract. The main skill also recommends smooth-by-angle 35° for its earlier body pipeline, without defining separate hair/leather shading rules.

8. **Weak moustache — wrong dimensions and missing independent specification.**  
   H:339–345 uses two blades only **3.4 cm long × 2 cm wide**, directed mostly downward. There is no moustache-specific width, thickness, central separation or lip relationship in the hair spec. It inherits the generic blade construction and is subject to beard squeezing.

9. **Hoop belt — insufficient centreline design; colour loss in fitter.**  
   O:262 constructs a **14-segment, five-sided tube**, with radius randomized from 16–22 mm. Its section thickness is not grossly inadequate; the more important problems are the near-level path, placement over the already expanded skirt, and lack of deliberate front bends. The fitted dark belt is caused by the material replacement in B6.

10. **Tiny ornament — wrong number.**  
    The outfit spec explicitly calls for about **5.5 cm height**, inherited from teacher segmentation. [O:299](~/projects/lpm-faceless-humanoid/skills/stylized-lowpoly-humanoid/scripts/build_torn_outfit.py:299) implements `h=0.055, w=0.034, t=0.018`. The official pendant occupies a substantially larger fraction of the belt-to-hem distance.

    The spec also inconsistently recommends 6–9 cm “proud” despite warning that teacher bounds are inflated. Size and front projection need separate reference-derived targets.

11. **Exposed roots and artificial overlaps — missing adjacency rules.**  
    H:194–204 translates an entire blade outward until it clears the body. It does not subsequently ensure that its root still disappears into the cap or neighbouring clump. The hair spec describes layer order but has no overlap/visible-root metric.

    The outfit spec specifies tier staggering, but O uses a one-column shift between tooth classes—**one-third of a tooth**, not the stated half-tooth stagger—and never establishes panel-to-panel overlap.

12. **Uneven detail scale — missing regional allocation and quality gates.**  
    The specs constrain total triangles and broad statistics, but not projected facet size, triangle aspect ratio, dominant-plane size or silhouette contribution. Repeated primitives consume the budget automatically.

    The recorded v1 budgets are already:
    - Hair + beard: **1,197 tris**.
    - Skirt: **864**, belt: **140**, ornament: **24**.

    This leaves almost no room to solve the problem by adding geometry. Geometry must be redistributed.

The [v1 fitting report](~/projects/lpm-faceless-humanoid/skills/character-fitter/previews/male_v1_fit_report.md) is explicitly **FAIL**. It records skirt standoff, deformation and pose failures. It also includes an added `outfit_lining`; that extra geometry must count toward the final garment budget. “Topology unchanged” currently checks the fitted source layer, not necessarily the whole delivered assembly after automatic additions.

**3. C — Missing measurable rules for the next builder**

Use normalized dimensions first:

- **W** = measured skull width, currently 21.75 cm.
- **H** = skull top minus chin, currently 27.37 cm.
- **G** = belt centre to lowest intended skirt tip.

These targets should replace teacher-derived counts where they conflict with the official silhouette.

| Rule | Proposed v2 acceptance target |
|---|---|
| **Hair clump count** | **26–34 dominant scalp clumps**: fringe 5–7; crown 5–7; each side 4–5; back/nape 8–10. Count authored masses, not every triangulation bump. |
| **Clump proportions** | Main width **0.18–0.32W**; length **0.22–0.40H**; L/W generally **1.1–2.0**, with broader crown masses allowed. Thickness **0.3–0.5 of width**. |
| **Clump overlap** | Adjacent roots overlap **25–45% of local width**. First **20–30% of each lock’s length** concealed by cap/adjacent hair. No visible floating root from the four review views. |
| **Hair direction** | Fringe down/diagonally across forehead; side/nape predominantly down/back; upward peaks concentrated on crown. Adjacent major locks normally differ by **≤25°**, with deliberate exceptions. |
| **Hair silhouette** | Initial envelope: crown lift **0.08–0.15H**, lateral expansion **0.08–0.16W per side**. Trace the official front/side/back outlines; target silhouette IoU **≥0.90**, with local boundary error **≤0.04W** after camera alignment. |
| **Fringe placement** | Lowest main tips finish roughly **0.04–0.10H above the brow**, with a deliberately irregular edge. Do not derive the visible fringe solely from the current high `hairline_y`. |
| **Beard mass** | **5–7 broad connected lobes**, not eleven dangling blades. Inner attachment gap **2–6 mm**; separate outer-envelope targets: cheeks **10–20 mm**, chin/front **25–40 mm**, bottom **0.15–0.23H below chin**. Validate in side view. |
| **Moustache** | Two broad lobes spanning **0.45–0.60W** overall; visible height **0.10–0.15H**; projection **10–20 mm**. Preserve a readable junction under the nose and separation from the chin mass. |
| **Skirt panel grammar** | Two **overlap groups**, not two level bands: **7–9 main outer panels**, **6–8 lower/underlapping panels**, with **3–5 substantial tan reveals** around the garment. |
| **Panel size** | Main visible panels **0.45–0.75G long** and **0.20–0.35G wide**; lower panels **0.25–0.45G long**. Vary widths deliberately by about **±20%**. |
| **Panel overlap and hem** | Width overlap **20–35%**; roots concealed by **0.08–0.15G**. Main tip heights vary across a **0.12–0.22G** range. Include diagonal edges, unequal notches and broad points. |
| **Hanging envelope** | Fit at waist/upper hip; below hip, use panel-specific gravity-led paths. Initial allowance: lateral growth below hip **≤0.04G per side**, unless the traced reference requires more. Avoid continuous tier ledges. |
| **Lining reveal** | In matched front/three-quarter renders, tan occupies initially **20–30% of visible leather area**, excluding belt/stone. At least two broad reveals rise **0.30–0.50G above the lowest hem**. Measure projected colour masks, not total hidden mesh area. |
| **Belt** | Visible diameter **0.06–0.08G**, centreline vertical variation **0.02–0.04G**, local 2–5 mm seating gap to leather. Preserve pale material through fitting/export. |
| **Pendant** | Height **0.20–0.25G**, width **0.07–0.10G**, thickness **0.025–0.04G**; elongated angular outline, visibly resting over the front panels. |
| **Facet scale** | Hair main visible edges roughly **20–45 mm**; beard **15–30 mm**; leather **35–70 mm**; belt **15–30 mm**. Smaller geometry reserved for tips, overlaps and attachment edges. |
| **Triangle quality** | Within each region, aim for **p90/p10 triangle-area ratio ≤8**, excluding intentional tip/edge triangles; non-tip aspect ratio generally **≤5:1**. Uniform size across different regions is neither necessary nor desirable. |
| **Normals/materials** | Flat normals on designed hair, beard, stone and leather planes; smoothing only within explicitly chosen curved patches. No global smooth override. Preserve role materials and authored roughness, initially **0.8–0.95** for hair/leather. |

Additional pipeline requirements:

1. **Separate contact from volume.** Inner beard fit must not imply a cap on outer beard thickness. Protect silhouette vertices from automatic squeezing.
2. **Gate fitter damage.** Compare pre/post silhouettes and colour masks. Proposed limit: protected-outline movement **≤3 mm**, except explicitly reviewed collision fixes.
3. **Preserve nodes/material roles and socket conventions.** Keep the replaceable-assets contract, but do not treat its scalp-offset recipe as the hairstyle itself.
4. **Make beauty checks mandatory.** Review aligned front, three-quarter, side and back views, plus head/skirt crops, using identical lighting. Collision success cannot substitute for resemblance.
5. **Count the final assembly.** Include lining, undersides, belt and ornament after fitting; automatic lining must not silently exceed the budget.

**4. D — Short v2 construction recipe and budget**

1. **Build hair from the silhouette inward.**  
   Trace the major peaks, fringe, side locks and nape from image 1. Make a low-resolution concealed cap against the actual skull. Place approximately **30 broad, asymmetrical wedge masses**, each with a few designed planes and a bent/blunt-pointed end. Establish overlap before adding small secondary tips.

2. **Sculpt beard and moustache as volumes.**  
   Build a continuous cheek–jaw–chin envelope with 5–7 broad lobes; add two substantial moustache lobes. Fit only the inner contact surface. Preserve the outer envelope through the fitter.

   | Hair component | Tri allocation |
   |---|---:|
   | Concealed cap | 160 |
   | 30 main clumps × approximately 18 | 540 |
   | Beard mass and lobes | 240 |
   | Moustache | 60 |
   | Junctions/undersides | 80 |
   | **Total** | **1,080 / 1,200** |

3. **Build the skirt as overlapping hide panels.**  
   Start with a lightweight concealed coverage shell. Add eight main dark panels and seven underlapping panels with unequal lengths and diagonal seams. Shape tan reveals deliberately between dark panels. Use thickness primarily at visible edges rather than duplicating every hidden surface. Keep the lower silhouette close to the reference instead of accumulating maximum body radii downward.

   | Skirt component | Tri allocation |
   |---|---:|
   | Concealed coverage shell | 120 |
   | 8 main panels × approximately 36 | 288 |
   | 7 underlapping panels × approximately 28 | 196 |
   | Tan reveal geometry | 120 |
   | Visible rims/closures | 96 |
   | **Total** | **820 / 900** |

4. **Add the identifying accents.**  
   Use an irregular seated belt with **12 stations × five section vertices = 120 tris**, leaving 30 for localized shaping. Make a larger elongated stone in approximately **36 tris**, within the 60-triangle limit.

5. **Validate the delivered result.**  
   Preserve material assignments and facet normals, run collision/pose checks, then compare the final rendered assembly against the official views. Spend the remaining triangles only on mismatched silhouettes or missing major planes—not additional surface spikes.
# Codex audit — female bandeau armpit point (25/10/2026, 3 rounds, session 01a17186-7e37-75f0-8789-b856fa78fcae)

Boss: «Phần nách vẫn còn chỗ nhọn, nhọn của dây belt - hay là làm thành dây dẹp vẫn giữ texture xoắn đó?»

## Round 1 — brief
You are reviewing a procedural low-poly garment for a game character. Read-only. I (Claude) built it; the owner judges by eye only.
Answer in English, concrete and implementable, no generalities. We will go 2–3 rounds; push back on me where I'm wrong.

## The asset
Female primal "bandeau" (strapless chest wrap) built in code by
`skills/stylized-lowpoly-humanoid/scripts/build_bandeau.py` (read it). Body: `assets/characters/primal_female_base/female_base_lp.glb`
(~2400 tris, arms hanging at the sides, upper arm touching the torso side under the armpit). Current output `female_bandeau_v8.glb`
(448 tris, budget 450): a dark leather band (rows `[bottom, peak, mid, top]`, 20 angles, torn bottom teeth) + a "rope" top trim
(`rope_bone`, 16 stations × 4-sided twisted tube, radius 7–10 mm, copied in spirit from the skirt's rope belt).

Image 1: front view crop of the character's LEFT armpit, v7 (left half) vs v8 (right half).
Image 2: full front view of v8 on the body.

## Owner's complaints so far (in order)
1. «áo nữ đang bị vật nhọn lòi ra nách» — a pointed thing sticks out at the armpit.
2. «Dây belt áo … nhỏ size lại vì nó đang lòi ra ngoài từ chỗ nách ra tới vai» — rope too thick, sticks out armpit → shoulder.
3. «vệt tà áo trên đang nhô ra … phải ôm vào ngực … chỗ 2 bên nách» — top edge must hug the chest beside the armpits.
4. «vẫn còn một vệt nhọn nâu … bên nách trái nhìn từ phía trước» — brown (leather) point at the left armpit, front view.
5. NOW: «Phần nách vẫn còn chỗ nhọn, nhọn của dây belt — hay là làm thành dây dẹp vẫn giữ texture xoắn đó?»
   = the armpit still has a point, now from the ROPE. Should the rope become a FLAT strap that keeps the twisted texture?

## How I build it now (and why)
- Each row radius per angle = convex hull of the ARM-LESS torso cross-section (arm faces removed by nearest-bone test, kept only if
  mesh-connected to a hand). Between the two breast apexes the band bridges the cleavage (hull); outside the apexes it follows the REAL
  (non-convex) section radius.
- Under the arm (~80–110° azimuth from front) the arm-less section has NO skin (the arm faces were cut away), so there is no radius;
  v8 blends the radius across that gap from the hugged neighbours (+4 mm band, +15 mm rope). Without the +15 mm on the rope the underarm
  skin shows (skin-visible gate 1.14 % > 1 %).
- Every torso vertex between two rows must be inside the band (linear blend between rows; the nearer row takes the push).
- Gates in the builder: torn-edge evenness, spike clamp (≤ 12 mm over neighbour mean), rope inner side ≤ 10 mm off skin outside the
  front, top row ≤ 13 mm off skin at 30–120°, front-view outline point ≤ 5 mm. Fitter gate: skin visible ≤ 1 %, no visible clipping.
- The rope is a closed loop around the torso at the top row height; under the arm it passes INTO the upper arm (hidden inside it).

## My diagnosis of the remaining rope point
In front view the rope loop must enter the upper arm somewhere between the breast side and the armpit. Where it enters, the 4-sided tube
(radius ~8.5 mm, chord between stations 22.5° apart ≈ 6 cm long) tapers visually into the arm silhouette → reads as a tan spike.
It is the INTERSECTION line of a round tube with the arm, seen edge-on; making the rope thinner shrinks it but cannot remove it.

## My current position (attack it)
A. A flat strap (e.g. 14–18 mm tall × 3–4 mm thick ribbon lying ON the band's top edge, normal = band normal), with the twist kept as
   alternating diagonal facets / a sawtooth top silhouette, would show no point: entering the arm it is a thin sheet tangent to the
   torso, so its intersection with the arm is a short vertical line, not a cone tip.
B. Alternatively stop the rope BEFORE the arm on each side (two open arcs, front and back, ending in a knot/fray cap) — honest
   design, no intersection at all; but the owner might read a gap under the arm as "missing".
C. I distrust "push the rope outward around the arm" — that is exactly complaint 2.

## Questions
1. Is my diagnosis right? Look at the images and the code — what EXACTLY produces the visible point (rope taper, band corner, the
   +15 mm rope pad under the arm, chord length, the twist phase)? If you see a different cause, say which lines.
2. Flat strap vs round rope vs open arcs: which one, and why, for THIS body (arm touching the torso)? Give a spec: cross-section
   (vertices, w × t in mm), where it sits relative to the band edge (offset along band normal / up), station count, how to keep the
   "twisted rope" read on a flat strap within ~120 tris, and how it must behave where it meets the arm.
3. What should happen under the arm (80–110°) for both band and trim so the underarm skin stays covered (≤ 1 % visible) without any
   outward bridge?
4. Propose ONE machine gate that would have caught complaints 1, 4 and 5 (what the owner sees: a point at the armpit in front /
   3/4 view), with a threshold rationale, so I can reverse-test it on v7 (fail) and on the fixed version (pass).

## Round 1 — Codex
**Choose a flat binding, but reject A’s guarantee that a flat sheet cannot form a point.** An oblique arm intersection can clip a ribbon into a triangle too. The fix needs both a flatter section and controlled disappearance behind the arm.

I read the builder and coverage implementation. These conclusions use the supplied images and code; I haven’t rendered geometry ablations.

**1. What produces this point**

In Image 1, v8’s remaining tan projection is a shallow wedge extending beyond the leather’s upper corner. Your intersection diagnosis is plausible, but “a round tube inevitably tapers into a spike” is too strong. This is a **twisted square tube on a sparsely sampled, independently offset path**.

The relevant code is in [build_bandeau.py](~/projects/lpm-faceless-humanoid/skills/stylized-lowpoly-humanoid/scripts/build_bandeau.py):

- **Lines 206–208:** the center sits approximately `skin + 9 mm + 0.6r`. Its outermost extent can reach `skin + 9 mm + 1.6r`, or **20–25 mm**, before considering the gap handling. That is substantial for this trim.
- **Line 216:** `ROPE_GAP_PAD = 15 mm` permits an outward bulge relative to the neighbouring centers. It does **not necessarily add 15 mm**: this is a `min()` cap. Log the uncapped and capped values before blaming the entire pad.
- **Lines 222–230:** rotating four vertices creates diagonal ridges and triangular faces. The arm can hide most of one face while leaving its pointed end visible. Twist phase affects which ridge survives.
- **Line 205:** rounding 16 rope stations onto 20 leather stations introduces angular mismatch of up to 9°. The rope is not consistently attached to the actual band edge.
- **Lines 219–223:** the section uses radial/up axes rather than a frame perpendicular to the path tangent. On a sharply turning underarm path, that further distorts the nominal tube.

Long chords amplify the problem by giving the intersection a long planar facet to cut across. They do not, by themselves, prove an outward spike.

Two additional corrections:

- **Lines 174–179 can undo the spike clamp:** you clamp `rings`, then take `maximum(r, top_r)` with freshly computed, unclamped radii. The later spike gate checks `rings`, not that final geometry.
- Your current outline gate explicitly excludes `rope_bone` at **line 268**. Complaint 5 cannot fail it.

**2. Concrete replacement**

Use a **closed, flattened rope binding**, continuous beneath the arm. Avoid exposed knots or frays at the armpits: they introduce another potential pointed feature exactly where the owner objects.

| Property | Implementation |
|---|---|
| Cross-section | Four vertices forming a rectangle: **16 mm tall × 3 mm thick** |
| Orientation | Width axis follows the band surface upward; thickness axis is the local band normal |
| Placement | Inner face **0.5 mm outside the final leather outer surface** |
| Height | Center **6 mm below the leather top edge**, giving approximately 2 mm above and 14 mm below |
| Stations | **20 nonuniform stations**, shared with the band’s angular layout |
| Underarm sampling | On each side, place stations at approximately **65°, 80°, 95°, 110°, 125°**; distribute the remaining ten around front/back |
| Geometry budget | Outer face + upper/lower thickness faces: **6 triangles per span × 20 = 120 triangles** |
| Hidden face | Omit the inward face against the leather; verify backface behaviour in the target renderer |
| Total | Existing 320-triangle leather + 120-triangle trim = **440 triangles** |

Keep the rectangle’s orientation stable. **Do not twist the entire rectangular section, and do not add a sawtooth outline.** Both recreate silhouette points.

For the rope read, put diagonal alternating light/dark bands in the base-color texture, at roughly **20–25 mm pitch**, with a narrow shaded groove beside each light ridge. This requires no additional triangles. Fade the contrast beneath the arm. Your present material assignment at lines 235–239 supplies a uniform color; the current “texture” is geometric shading.

At the arm, the visible binding should retain approximately its full height until occluded. Move the continuation inward beneath the arm over the last two spans; do not narrow it to an exposed tip. Judge that transition in front and both three-quarter views. Flat geometry alone does not guarantee this.

**3. Underarm coverage**

The missing arm-less section is **missing data**, not evidence that the garment needs an outward pad.

For 80–110°:

1. Connect the last trustworthy front and back torso attachment points with a **Cartesian chord**, separately for each leather row. Interpolating polar radii does not produce that chord and can preserve an outward bow.
2. Use zero blanket gap pad initially. Keep the hidden continuation beneath the arm; attach the trim directly to this final leather surface.
3. If exposed torso skin remains at the front/back ends, adjust those local leather faces against the retained torso surface. Add or redistribute a station there instead of moving the whole gap outward.
4. Make the leather provide coverage. The decorative trim should not be necessary to get under 1%.

There is an important flaw in your justification for `+15 mm`: [see_through()](~/projects/lpm-faceless-humanoid/skills/character-fitter/scripts/fit_engine.py:753) casts rays along skin normals and checks garment intersections. **It does not test whether the arm hides that skin from the camera.** Consequently, “1.14% skin visible” is not necessarily 1.14% visibly exposed skin.

Inspect those failing samples with full-body depth occlusion. Preserve the existing metric as a diagnostic, but use camera-visible, intended-to-be-covered torso skin for the owner-facing ≤1% requirement. Otherwise you may keep creating visible protrusions to cover invisible samples.

**4. One gate: visible armpit spur length**

Use a depth-tested garment-mask gate:

1. Render orthographic front and yaw **±30°, ±45°**, with the complete body participating in depth.
2. Produce a binary mask of **visible leather plus trim**. Evaluate only fixed anatomical armpit regions, excluding the torn bottom edge.
3. At **0.5 mm/pixel**, perform a morphological opening with a **4 mm-radius disk** on the full mask, before cropping to the regions.
4. For pixels removed by the opening, measure distance to the opened mask. The gate score is the maximum distance within either armpit region, across all views.
5. **Fail above 5 mm.** Ignore isolated raster components smaller than 1 mm².

This detects a narrow appendage extending from the visible garment, including a tan wedge against skin; it does not depend on the character’s outer silhouette. The 8 mm opening diameter preserves a 16 mm binding face while removing narrow tips; the 5 mm limit allows small low-poly corners but rejects a conspicuous extension.

Reverse-test it on actual v7 and v8 renders, saving the removed pixels as a red overlay. **I would expect v7’s brown point and v8’s tan point to score poorly, but cannot claim either fails until measured.** Freeze the threshold after checking those overlays, then test the replacement unchanged.
## Round 2 — Claude pushback
Round 2 — I accept most of it, but I push back on three points. Answer each, then give the final spec.

ACCEPTED (will implement): flat 4-vertex rectangular binding, inner face 0.5 mm off the final leather, centre 6 mm below the top edge,
20 stations SHARED with the leather angles (no 16→20 rounding), section frame from the band surface (up along band, normal = band
normal), no whole-section twist, no knots/frays at the armpit; Cartesian chord per row across the 80–110° arm gap with zero blanket pad;
fix lines 174–179 so the spike clamp is not undone by max(r, top_r); the outline gate must include the trim.

PUSHBACK 1 — "keep the twist in the base-colour texture". This project has NO textures/UVs: every asset is flat-shaded low-poly with
per-part PBR baseColorFactor from a shared palette (`theme/theme_colors`). The owner explicitly asked to KEEP "texture xoắn" = the
twisted look he sees now, which is GEOMETRIC (facets catching light). A painted texture would be the only textured part of the whole
character. My counter-proposal: keep it geometric but inside the strap's own envelope — a 3-row section (top edge, a middle ridge row,
bottom edge) where the middle ridge vertex alternates up/down between stations (zig-zag diagonal crease) and sits +1.5 mm proud of the
strap face. Silhouette stays a smooth band (ridge never crosses the top/bottom edges), but light breaks into alternating diagonal facets
= reads as twisted rope. Cost: outer face becomes 4 tris/span → 4 + 4 (top/bottom thickness) = 8/span × 20 = 160 tris; leather 320
→ 480 > 450 budget. Options: drop the bottom thickness faces (hidden against the leather) → 6/span = 120; or drop leather to 16 angles.
Is the zig-zag crease a sound way to read "twisted" without points? Which budget option, and what ridge amplitude/pitch (every station or
every 2nd)?

PUSHBACK 2 — "see_through ignores arm occlusion". cover_zone() already samples only the ARM-LESS torso and drops skin within 3 cm of any
arm face (fit_engine.py ~698–702), so samples hidden by the arm are mostly excluded. The 1.14 % that appeared when the rope stopped
bridging were "underarm" region samples at the front/back ENDS of the arm gap. Do you still think the metric is wrong there, or that
those few samples are truly visible from a 3/4 camera? If the latter, your step 3 ("adjust local leather faces at the gap ends") is the
fix — give me the rule (which faces, how far, bounded how) so it cannot create the point again.

PUSHBACK 3 — the gate. Rendering to a 0.5 mm/pixel mask with full depth test across 5 views in pure numpy ray casting (my per-ray loop) is
~2 M rays: too slow for a builder gate (I need < ~30 s). I propose: 1.5 mm grid only inside the two armpit boxes (anatomical: x from the
breast apex to the arm's outer silhouette, y from 4 cm below to 3 cm above the top edge), 3 views (front, ±35°), opening radius 3 px
(4.5 mm), fail if any removed pixel lies > 5 mm from the opened mask. Is the lower resolution / box restriction still discriminative for
a 6–10 mm point? Any simpler equivalent (e.g. per-scanline run-length: a garment run that narrows to < 4 mm and extends > 5 mm beyond the
neighbour scanlines)?

Then FINAL SPEC: one numbered list I can implement directly (geometry numbers, under-arm rule, budget, gate + threshold + reverse test).

## Round 2 — Codex (FINAL SPEC 1–9)
**1. Geometric twist: agreed, with one budget change.**

My texture proposal was wrong for this project. Your zigzag ridge is a sound way to retain alternating facets without rotating the binding’s outline. It should read as flattened, twisted cord, although the final lighting render must confirm that read.

Use ridge displacement **±3 mm vertically**, alternating **every station**, and **1.5 mm outward relief**. Every second station would produce long, nearly horizontal ridge segments and a less consistent twist rhythm. With nonuniform station spacing, the physical pitch will vary; that is acceptable here.

However, **the bottom thickness face is not automatically hidden against the leather**. With the inner face offset 0.5 mm and the outer face another 3 mm out, removing that face leaves an exposed underside.

Keep both thickness faces. Instead, remove the leather’s **uppermost inner-facing row of quads**: 20 spans × 2 triangles = **40 triangles saved**. Those faces sit against the torso in this fitted asset. Keep the leather’s top cap and verify that the omitted inner faces are never exposed in the review views.

That gives **280 leather + 160 binding = 440 triangles**, preserves 20 shared stations, and closes the visible binding edges.

**2. Coverage: your correction is valid; visibility remains unproven.**

I checked `cover_zone()`. It excludes samples within 3 cm of sampled arm faces, and its rays are **horizontalized normals**, not the original surface normals. My earlier description missed both details.

The exclusion makes your gap-end explanation credible. It does not establish camera visibility: distance from an arm is not an occlusion test. Treat these as coverage defects to investigate, rather than dismissing them or declaring them definitely visible.

Also fix a comparison confound: coverage currently ends at `X[:,1].max() - 4 mm`. Changing rope height changes the measured skin region. **Freeze the coverage ceiling to the intended leather top height minus 4 mm** for old/new comparisons.

For local repair, target the leather triangle found by an inward ray from each failing gap-end sample. Move only its eligible vertices, along torso normals, using the smallest displacement that puts the outer leather **3 mm beyond the sample**. Bound cumulative displacement to **4 mm per vertex**, and final outer-surface standoff to **10 mm from trustworthy torso skin**. Keep gap-interior vertices constrained to the Cartesian continuation. If those bounds cannot cover the sample, redistribute a station or row; do not increase the pad.

**3. Gate: your cheaper version is useful, but 6 mm is borderline.**

At 1.5 mm/pixel, a 6 mm point is only four pixels long. A 5 mm threshold lies between three and four pixels, so grid alignment can flip the result. An 8–10 mm point should be much more reliably detected.

Use your coarse gate, followed by **local 0.5 mm refinement only for candidate spurs scoring ≥3 mm**. That avoids rendering all boxes at high resolution. A strict runtime guarantee still needs timing against your ray caster.

Pad each rendered box by **12 mm**, perform opening on the padded mask, then score only the original box. Otherwise cropping can manufacture spurs or remove their supporting garment region.

Do not replace opening with the proposed scanline rule. Diagonal tips and arm-clipped edges can move between scanlines without satisfying a fixed narrow-run condition.

**Final implementation spec**

1. **Shared sampling:** retain 20 leather/binding stations. Include approximately 65°, 80°, 95°, 110°, 125° on each side; distribute the remaining ten around front/back. Replace uniform-angle indexing and nearest-bin rounding wherever necessary with lookup against the actual station angles.

2. **Binding envelope:** 16 mm tall, 3 mm base thickness. Inner face 0.5 mm outside the final leather outer surface; center 6 mm below its top edge. Use the band surface’s upward tangent and outward normal. No whole-section twist or silhouette teeth.

3. **Facet ridge:** add one outer middle vertex per station, displaced vertically by alternating **+3/−3 mm** and outward **1.5 mm beyond the base outer face**. Connect top–ridge and ridge–bottom with two triangles each per span. Flat shading; existing palette material. Maximum relief from the leather is therefore **5 mm**, not 3.5 mm.

4. **Arm transition:** fade ridge relief and vertical zigzag amplitude to zero over the last two spans before the binding disappears behind the arm. Keep the top/bottom edges separated by 16 mm; do not taper the visible strip to a tip. Carry its hidden continuation inward with the leather. Confirm disappearance in front and ±35° views.

5. **Gap construction:** for each leather row, connect trustworthy front/back torso endpoints across the missing section by a Cartesian chord, with **zero blanket outward pad**. Attach the binding to the resulting final leather surface. Apply spike constraints to the final emitted geometry; do not restore unclamped radii afterward.

6. **Gap-end repair:** freeze coverage samples and ceiling across comparisons. For failing samples within **20 mm of a gap endpoint**, identify the supporting leather triangle by inward ray. Solve for minimal outward normal displacement giving **3 mm clearance** at those samples, with **4 mm cumulative vertex movement** and **10 mm final skin standoff** limits. Recompute adjacent gap chords and binding after repair. If infeasible, redistribute existing stations/rows and retry; never widen the entire gap.

7. **Budget:** binding outer face 80 triangles, upper/lower thickness faces 80: **160 total**. Omit the leather’s uppermost inner-facing strip, saving 40: **280 leather + 160 binding = 440**. Keep the binding underside and leather top cap. Reject this omission if review views expose the missing inner strip.

8. **Point gate:** render full-body-depth-tested, visible **leather ∪ binding** masks in anatomical armpit boxes at front and ±35°. Use 1.5 mm/pixel, 12 mm box padding, and disk opening radius **4.5 mm**. Score removed pixels by distance to the opened mask. Refine candidates scoring **≥3 mm** in small padded crops at 0.5 mm/pixel, using the same physical opening radius. **Fail if refined spur length exceeds 5 mm.** If a nontrivial candidate component disappears completely under opening, flag it rather than silently dropping it.

9. **Reverse test:** run identical cameras, boxes, scale, and thresholds on **v7, v8, and the replacement**. Save mask overlays showing removed pixels and the worst-scoring location. Require v7’s brown point and v8’s tan point to fail at their actual locations, and the replacement to pass. If either old point escapes, fix candidate detection or box placement before accepting the gate; do not claim success from a numeric pass alone.
## Round 3
Round 3 (last). I'll implement your final spec 1–9. Two simplifications — accept or reject each in one line with the reason:
(a) Gate step 8: if the coarse 1.5 mm pass already separates v7 (brown point), v8 (tan point) and the replacement by ≥ 3 mm margin on the saved overlays, I ship the coarse gate and add the 0.5 mm refinement only if a later case lands within 3–7 mm.
(b) Spec 6 gap-end repair: implement it only if the frozen-ceiling coverage of the new geometry is > 1 % (it may pass without it, since the Cartesian chord sits inside the old polar blend and the leather, not the trim, now must cover).
Also: anything in spec 1–9 you consider the MOST likely to recreate a point if I get it slightly wrong? Name it and the check.

(a) **Accept**, provided the ≥3 mm margin is from the **5 mm threshold**: both old points score ≥8 mm and the replacement ≤2 mm at the correct locations. Refine future scores in the 3–7 mm range.

(b) **Accept**—run repair only if frozen-ceiling coverage exceeds 1%; still inspect gap-end overlays, because a small localized hole can pass the aggregate metric. An inward chord does not itself improve coverage.

**Most likely recurrence: step 4’s arm transition.** Moving the binding inward too early can leave a long triangular sliver where the arm occludes it, even with zero ridge relief. Check depth-tested trim masks in front and ±35°: reject a visible tip extending >5 mm beyond the opened mask. Fade the ridge, not the strip’s height, and adjust the entry path if that wedge remains.
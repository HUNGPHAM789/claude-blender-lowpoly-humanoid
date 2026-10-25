## PART 1 — BUILD BRIEF v2

1. **Scope:** rebuild hair + beard and skirt + belt + stone; preserve the body and replaceable-asset contract. Spend approximately 60 minutes, then submit for owner review.
2. **Reference:** image 1 controls front/side/back silhouette; image 2 clarifies broad planes and colour placement. Sheet overlays are diagnostic, not an IoU pass/fail test.
3. **Units:** W = bare skull width; H = bare skull-top-to-chin height; G = belt-centre-to-lowest-skirt-tip distance. All shape ranges below are provisional.
4. **Timebox:** 5 min silhouette blockout; 20 min hair/beard; 20 min outfit; 10 min checks/renders; 5 min corrections.
5. **Hair:** build a concealed scalp cap, then approximately 30 broad, irregular overlapping wedges with authored ridges, intermediate sections and bent/blunt-pointed ends.
6. Use approximately 6 fringe, 6 crown, 4 per side and 10 back/nape masses; prioritize silhouette and coherent flow over exact counts.
7. Main clump width 0.18–0.32W; length 0.22–0.40H; thickness 0.3–0.5 × width. Allow broader, shorter crown masses.
8. Direct fringe down/across the forehead, sides and nape down/back; reserve upward peaks for the crown. Place visible fringe tips approximately 0.04–0.10H above the brow.
9. Conceal each clump’s first 20–30% of length beneath cap/neighbours; start with 25–45% root-width overlap, then check actual concealment.
10. **Do NOT use repeated nine-triangle blades, random lateral flow, or derive the visible fringe from `hairline_y` alone.**
11. **Beard:** construct one continuous cheek–jaw–chin mass with 5–7 broad connected lobes and an underside returning toward the submental attachment; add two broad moustache lobes.
12. Keep contact gap near 0.01–0.02W. Start outer cheek offset at 0.03–0.06W, jaw at 0.04–0.07W, chin-front extension at 0.05–0.08W.
13. Trial below-chin extension: 0.08–0.15H. Start modestly; broad joined planes provide solidity. These outer dimensions are proposals, not measurements recovered from the sheet.
14. **Do NOT add eleven dangling beard blades, floating mask geometry, lateral needle spikes, or a blanket outer-beard squeeze.**
15. Hair/beard tags: `cap_contact`, `clump_id`, `hair_region`, `root_band`, `contact_inner`, `cheek_outer`, `jaw_outer`, `chin_outer`, `underside`, `moustache_L/R`.
16. Add explicit vertex masks `fit_movable` and `protect_outer`, plus corresponding body attachment-patch IDs; preserve these through export or a stable sidecar mapping.
17. **Hair budget:** cap 160; main clumps 540; beard 240; moustache 60; junctions/undersides 80 = target 1,080; **final total ≤1,200 tris**.
18. **Skirt:** make a lightweight concealed coverage shell, then eight main dark hide panels and seven underlapping panels with separate roots, diagonal edges and unequal lengths.
19. Main panels: length 0.45–0.75G, width 0.20–0.35G; lower panels: length 0.25–0.45G. Begin with 20–35% panel-width overlap.
20. Conceal panel roots; vary main tip heights across approximately 0.12–0.22G. Fit upper attachments, then shape each panel’s hanging path independently.
21. Create 3–5 broad tan reveals between dark panels, including reveals extending upward; target initially 20–30% tan of visible leather in fixed front/three-quarter role renders.
22. **Do NOT build rings plus serrated hems, two level toothed tubes, or a skirt whose maximum hip radius is carried downward.**
23. Garment tags: `panel_id`, `overlap_group`, `root_band`, `contact_inner`, `protect_outer`, `leather_dark`, `lining_reveal_id`, `leather_tan`, `coverage_shell`.
24. **Skirt budget:** shell 120; main panels 288; underlapping panels 196; tan reveals 120; rims/closures 96 = target 820; **all skirt/lining geometry ≤900 tris**.
25. **Belt:** build a seated, irregular centreline with 12 stations and five section vertices; target 120 tris, **≤150**. Diameter initially 0.06–0.08G; vertical variation 0.02–0.04G.
26. **Stone:** build an elongated faceted pendant, height 0.20–0.25G, width 0.07–0.10G; target 36 tris, **≤60**. Tag belt `belt`, pendant `stone`.
27. Preserve sub-geometry material roles. Use explicit flat normals on designed hair/beard/leather/stone planes; no global smooth-shading or roughness override.
28. **Report counts/budget:** authored clumps by region, beard lobes, panels/reveals, and final exported triangles by role, including every automatic addition.
29. **Report contact:** area-sample registered beard attachment patches; require ≥99% ray-hit coverage, gap p95 ≤6 mm, max ≤8 mm, penetration ≤1 mm; count misses as failures.
30. **Report spikes:** maximum sampled outer-surface excursion beyond a separately authored coarse beard envelope; provisional limit 0.015W, excluding designated moustache endpoints.
31. **Report root concealment:** visible root pixels / isolated-root projected pixels in fixed front, back, left/right side and three-quarter cameras; target zero exposed attachment roots.
32. **Report tan share:** use unlit material-ID renders; tan / (tan + dark leather), excluding belt, stone and background. Report each camera separately.
33. Report protected-vertex displacement before/after fitting, clipping and required-pose results; fail unresolved conflicts instead of silently flattening or inflating the design.
34. Deliver matching pre/post-fit turnarounds, head/skirt close-ups, role renders and the check report. **The owner decides resemblance and attractiveness by eye.**

## PART 2 — SKILL/SPEC AMENDMENTS

1. **OWNER-EYE — `skills/stylized-lowpoly-humanoid/spec/SPEC_primal_spiky_hair.md`, §§1–3:**  
   “Male primal hair uses broad overlapping masses with coherent regional flow; teacher-segmentation counts are descriptive evidence, not mandatory authored-clump counts. Start near 30 masses and obtain owner review.”

2. **OWNER-EYE — same file, §4 Placement:**  
   “Author fringe, crown, side and nape silhouettes from the official views; `hairline_y` anchors contact only. Reject repeated nine-triangle blades and uniformly randomized spike directions.”

3. **HARD GATE (machine) — same file, new ‘Authored structure’ section:**  
   “Export stable clump/region IDs, root bands, body-contact correspondences and movable/protected vertex masks; report counts and root visibility under the fixed review-camera set.”

4. **OWNER-EYE — same file, new ‘Beard construction’ section:**  
   “Build a continuous snug cheek–jaw–chin mass with broad lobes, two moustache lobes and a returning underside. Reject floating masks, eleven-blade fringes and sideways needle spikes; outer dimensions remain provisional until approved.”

5. **HARD GATE (machine) — same file, §6 Gates:**  
   “Beard contact uses area-sampled registered attachment patches: coverage ≥99%, gap p95 ≤6 mm, max ≤8 mm, penetration ≤1 mm. Missing intersections count as failures; insufficient measurement coverage cannot skip the gate.”

6. **HARD GATE (machine) — same file, §§5–6 Budget/Envelope:**  
   “Hair plus beard must total ≤1,200 final exported triangles. Report maximum excursion beyond an independently authored beard envelope; provisional limit 0.015W, excluding explicitly tagged moustache endpoints.”

7. **OWNER-EYE — `skills/stylized-lowpoly-humanoid/spec/SPEC_primal_torn_layered_outfit.md`, §§1,3,5:**  
   “Two overlap groups mean individually shaped hide panels, not two continuous serrated tubes. Use diagonal overlaps, unequal lengths and panel-specific hanging paths; prohibit carrying maximum hip radius down the garment.”

8. **HARD GATE (machine) — same file, new ‘Panel contract’ section:**  
   “Export panel IDs, overlap groups, root bands, protected outer masks and distinct dark-leather, tan-reveal, coverage-shell, belt and stone roles. Define overlap on designated root bands before reporting percentages.”

9. **OWNER-EYE — same file, §4 Colour composition:**  
   “Start with broad tan reveals occupying approximately 20–30% of visible leather in fixed front/three-quarter views; placement and visual resemblance require owner approval, not percentage alone.”

10. **HARD GATE (machine) — same file, §§6–7:**  
    “Count the final assembly: skirt including every lining ≤900, belt ≤150, stone ≤60 triangles. Report tan share using unlit role masks with denominator tan + dark leather; preserve role assignments through fitting.”

11. **OWNER-EYE — `skills/stylized-lowpoly-humanoid/SKILL.md`, ‘SPECS’ and preview workflow:**  
    “Generated-teacher statistics do not override the official design. Sheet overlays and IoU are diagnostic only; require owner review of matched turnarounds and head/skirt crops before declaring visual acceptance.”

12. **HARD GATE (machine) — same file, pipeline/export contract:**  
    “Every procedural asset carries semantic roles, stable geometry mappings and authored shading intent. Report final budgets and fit checks separately from owner visual acceptance.”

13. **HARD GATE (machine) — `skills/character-fitter/SKILL.md`, ‘Placed assets’ and ‘Fitting Report’:**  
    “Preserve sub-geometry, face-role assignments, materials and metadata through loading, deformation and export. Extend topology validation with role/material preservation and final-assembly budget checks, including automatic lining.”

14. **HARD GATE (machine) — same file, ‘Hair’ and `beard_snug`:**  
    “Replace pooled outer-vertex p90 distance with contact coverage/gap plus regional outer-envelope measurements. Fit tagged contact surfaces; preserve tagged outer geometry and fail conflicts rather than applying blanket beard squeezing.”

15. **HARD GATE (machine) — same file, ‘Gates’:**  
    “Report protected-shape displacement alongside edge stretch; provisional maximum 3 mm. Added lining receives applicable rest/pose checks, and every declared beard must produce valid contact measurements.”

16. **HARD GATE (machine) — `skills/stylized-lowpoly-humanoid/scripts/render_turnaround_blender.py`, lines 23–30 material/normal handling:**  
    “Remove global roughness clamping and `use_smooth=True`; preserve authored materials and normals. Verify flat-design regions after reimport without globally flattening the body.”
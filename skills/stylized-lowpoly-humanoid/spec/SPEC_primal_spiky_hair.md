# SPEC — chunky primal spiky hair (v1.0, 25/10/2026)

Boss: «học được và có spec cho chunky primal hair … chưa?» → «1 và 3». Numbers: `SPEC_primal_spiky_hair.json` (machine-readable, same values).
Source: 6 Hunyuan3D-2 teacher meshes (male/female × seeds 42/7/123) from Codex-cleaned large asset images of the official primal sheets.
Teachers are measured, never shipped. Units: cm at body scale (male scalp 1.80 m, female ≈ 1.70 m). Ranges = p10 / p50 / p90.

## 1. What the hair is
A cap of **flat, blade-like clumps** (not round cones) planted on the scalp in 4–5 regions. Each clump: a root on the scalp, a straight-ish
blade that tapers to a point, slightly bent. Male = **spiky**: clumps point UP/OUT. Female = **long locks** that hang DOWN, with a spiky
crest on the crown/fringe.

## 2. Clump shape (all regions)
| property | male | female | how measured |
|---|---|---|---|
| cross-section thickness / width | 0.41–0.51 (blade) | 0.56–0.66 | PCA extents of the clump |
| bend (mid-point off the straight line ÷ length) | 0.13–0.23 | 0.10–0.18 | |
| tip half-angle | 37–51° | 28–40° | cone fitted to the last 25 % |
| facets per clump | ≈ budget ÷ clumps ≈ 18 tris | ≈ 18 tris | design rule from the tri budget |

## 3. Regions (counts per head = min / median / max)
| sex | region | clumps | length | base width | len ÷ width | flow \|°\| (0 = down the scalp) | root spacing |
|---|---|---|---|---|---|---|---|
| male | fringe | 10 / 16 / 22 | 2.2 / 3.3 / 7.8 | 1.2 / 2.3 / 4.2 | 1.7 | 132 (up/out) | 1.7 |
| male | side | 29 / 31 / 32 | 3.5 / 6.4 / 10.5 | 1.1 / 3.1 / 5.1 | 2.2 | 128 (up/out) | 2.8 |
| male | back | 18 / 23 / 24 | 2.7 / 5.3 / 9.8 | 1.2 / 3.0 / 6.3 | 1.9 | 150 (up/out) | 3.8 |
| male | crown ⚠ | 3 / 4 / 9 | 2.7 / 5.6 / 9.5 | 1.1 / 5.6 / 15.1 | 0.8 | 125 | 4.6 |
| male | beard | 4 / 7 / 9 | 1.9 / 5.0 / 10.3 | 0.7 / 3.0 / 4.4 | 2.6 | 28 (down) | 2.6 |
| female | fringe | 4 / 11 / 11 | 3.8 / 9.5 / 11.5 | 1.3 / 2.0 / 3.1 | 3.8 | 155 (crest up) | 2.2 |
| female | crown | 20 / 22 / 27 | 2.1 / 5.8 / 10.1 | 0.9 / 2.2 / 5.0 | 2.5 | 33 (down) | 2.9 |
| female | side | 7 / 8 / 11 | 3.1 / 6.1 / 9.3 | 1.2 / 2.7 / 4.1 | 1.9 | 46 | 3.2 |
| female | back | 45 / 48 / 52 | 3.3 / 6.9 / 11.5 | 1.1 / 2.4 / 4.6 | 3.1 | 33 (down) | 3.0 |

Tilt from the scalp normal ≈ 31–68° (median per region in the JSON). ⚠ male crown = LOW confidence (short crowded spikes merge into broad patches).

## 4. Placement and layering
- **Hairline:** male front roots down to 0.18 of the head half-height BELOW the head centre (brow line), nape 0.29 below; female front 0.11,
  hair falls to 0.95 below (neck).
- **Spacing:** roots 1.7–3.8 cm apart (nearest neighbour); no scalp may show from any view above the hairline.
- **Layers:** rank clumps by how far their root sits off the scalp — outer layer = larger offset, drawn last; absolute offsets are biased
  by the fit, use rank only.
- **Flow field:** male side/fringe/back point up and outward (spikes); female back/crown/side hang down; female fringe crest points up.

## 5. Colour and budget
One material, game palette `hair (58, 40, 28)` loaded through `theme_colors.mau()` (theme Đất ấm). Tris: male ≤ 1400, female ≤ 1600.

## 6. Gates (the builder's output must pass — measured with the same tools)
1. `analyze_hair.py` on the built mesh: clumps per region within [0.8 × min, 1.2 × max].
2. Per region medians of length / base width / tip angle inside the learned [p10, p90].
3. Flow: male ≥ 60 % of side/fringe/back clumps |flow| > 90°; female back ≥ 60 % |flow| < 60°.
4. Blade: median flatness ≤ learned p90.
5. Coverage: no scalp visible in the white-background turnaround above the hairline.
6. Budget: tris ≤ budget.

## 7. Re-measure
`analyze_hair.py` → `aggregate_hair.py` (skill §LEARN). Add samples by drawing new large asset images with Codex and running `~/bin/hy3d`.

## v2 rules — Codex audit of male v1, 25/10/2026 (`audits/codex_audit_male_v1_round*.md`)
Boss on v1: messy shards, the beard read as a mask. These rules OVERRIDE the teacher-segmentation counts above: those counts are evidence about the generated teachers, not targets.

**Look (Boss judges by eye):**
- **Masses:** about 30 broad, overlapping, irregular wedges.
  - Fringe ~6, crown ~6, sides ~4 each, back/nape ~10.
  - Width 0.18–0.32 W, length 0.22–0.40 H, thickness 0.3–0.5 × width (W = skull width, H = skull top → chin).
  - Never repeated 9-triangle blades.
- **Flow:** coherent per region.
  - Fringe down / across the forehead, ending 0.04–0.10 H above the brow.
  - Upward peaks only on the crown.
  - Sides and nape down / back.
  - Adjacent masses within about 25° of each other.
  - `hairline_y` anchors CONTACT only, never the visible fringe.
- **Roots:** the first 20–30 % of each mass hides under the cap or a neighbour; no floating root in the 4 review views.
- **Beard:** one continuous cheek–jaw–chin mass made of 5–7 broad lobes, with an underside returning to the throat, plus 2 broad moustache lobes. Never dangling blades, a floating mask, or sideways needles. Starting outer offsets: cheek 7–13 mm, jaw 9–15, chin front 11–17.

**Machine gates:**
- Contact gap 2–4 mm (`character-fitter` `beard_snug`).
- Hair + beard ≤ 1,200 tris in the delivered assembly.
- Every part exported as its own role geometry. Deformable parts are named `*__movable`; everything else is protected.
- Flat normals on designed planes.

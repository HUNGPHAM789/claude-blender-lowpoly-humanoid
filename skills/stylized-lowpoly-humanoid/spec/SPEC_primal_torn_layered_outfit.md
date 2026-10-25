# SPEC — layered, torn primal outfit (v1.0, 25/10/2026)

Boss: «layered and torned primal outfit» · «2 outfit đó là đủ số liệu rồi, muốn số liệu gì thì cứ phân tích 2 outfit đó».
Numbers: `SPEC_primal_torn_layered_outfit.json`. Source: 2 outfits — male skirt; female skirt + bandeau top (Hunyuan3D-2 teachers from
Codex-cleaned large asset images). Molds = `segment_mesh.py --mode bumps`; roles = image votes on SEEN faces, gated by geometry.

## 1. What it is
Leather made of **pointed flaps in two overlapping tiers**, dark outer leather with **light lining** peeking out mainly in the lower tier,
a **rope belt** round the top with **one stone/bone ornament** at the front. The bandeau top uses the same grammar, shorter, no lining,
light trim on the upper rim.

## 2. Garments
| property | male skirt | female skirt | female top |
|---|---|---|---|
| height | 57.2 cm | 49.1 cm | 20.4 cm |
| flare (bottom radius ÷ top) | 1.32 | 1.23 | 0.78 |
| hem teeth round the body | 8 | 10 | 6 |
| tooth depth p10/p50/p90 | 4.1 / 6.6 / 7.7 | 6.3 / 8.2 / 11.0 | 1.9 / 2.2 / 2.4 |
| tooth spacing | 30 / 39 / 63° | 30 / 36 / 45° | 51 / 62 / 68° |
| flap length | 5.0 / 8.3 / 13.7 | 4.3 / 8.9 / 14.2 | 2.6 / 4.6 / 7.1 |
| flap width (round the body) | 4.6 / 7.6 / 14.6 | 3.1 / 5.3 / 12.0 | 2.7 / 4.4 / 6.3 |
| flap length ÷ width | 0.6 / 1.1 / 1.8 | 0.8 / 1.4 / 2.6 | 0.7 / 1.0 / 1.6 |
| belt band (from the top edge) | 3.6–6.0 cm, ring r 16.5 | 0–7.2 cm, ring r 12.2 | light trim on the rim |
| belt lumps round the ring | 14 | 10 | 8 (trim) |
| ornament | 5.6 cm tall, 6.0 cm proud, front | 5.5 cm tall, 8.7 cm proud, front | — |

## 3. Layering (tiers, bottom up)
| | lower tier tips | lining share (lower) | upper tier tips | lining share (upper) |
|---|---|---|---|---|
| male skirt | 14.7 % of height (8.4 cm above the hem) | 0.25 | 35.8 % (20.5 cm) | 0.08 |
| female skirt | 13.1 % (6.4 cm) | 0.22 | 37.5 % (18.4 cm) | 0.17 |
| female top | 14.5 % (2.9 cm) | 0 | 35.3 % (7.2 cm) | 0 |

Rule: two overlapping tiers; the upper tier's flaps cover the roots of the lower tier; the lining shows in the lower tier.

## 4. Area by role (molds)
| role | male skirt | female skirt | female top | colour |
|---|---|---|---|---|
| outer leather | 73 % | 71 % | 87 % | `(74, 53, 37)` |
| lining | 12 % (lower 40 %) | 15 % | 7 % (rim) | `(176, 138, 92)` |
| belt / trim | 12 % (top 10 %) | 8 % | 5 % | `(196, 164, 108)` |
| ornament | 3 % | 7 % | — | `(120, 116, 108)` |

## 5. Design rules (NOT measurable from the teachers — generated layers are fused into one shell)
- Lining sheet sits 0.6–1.0 cm inside the outer sheet; where it shows, its teeth are 1–3 cm longer than the outer ones above it.
- Leather is ONE sheet 0.4–0.8 cm thick (fused-volume thickness measured 2–8 cm is fill, not leather).
- Rows/stagger are not recoverable (the molds form one continuous band) — the two TIERS replace rows; stagger tier 2 by half a tooth.
- Ornament bounding sizes from molds are inflated — use height 5.5 cm, proud 6–9 cm.

## 6. Budget, fit, rig
Tris: skirt ≤ 900, top ≤ 450, belt ≤ 150, ornament ≤ 60. Fit on the base body with ≥ 4 mm clearance (`assemble_layers_blender.py`); weights
copied from the body, never arm/shin/foot bones (`rig_body_blender.py`).

## 7. Gates
1. `analyze_outfit.py` on the built garment: teeth within learned ± 2; depth and spacing medians inside the learned [p10, p90].
2. Two flap-tip tiers: lower at 0.10–0.18, upper at 0.32–0.42 of the height; lining visible on ≥ 15 % of the lower tier's flaps (skirts).
3. `segment_mesh.py` finds a belt ring (ring-ness ≥ 0.6) in the top 12 % and one ornament mold at the front.
4. Role area shares within ± 50 % of §4.
5. Clearance ≤ 20 % of verts pushed; rig pose test stretch ≤ 3× on the garment.
6. Tris ≤ budget.

## 8. Confidence
Measured: tiers (both skirts agree), hem, belt band, ornament position, role areas. One sample per garment ⇒ treat p10/p90 as wide.
Design rules: lining offset, thickness, stagger.

## v2 rules — Codex audit of male v1, 25/10/2026 (`audits/`)
**OVERTURNED:** §5's «the two TIERS replace rows». Tiers built as rings with a serrated hem read as a stiff barrel (Boss on v1).

**Look (Boss judges by eye):**
- **Panels:** individually shaped hide panels.
  - 8 main dark panels, length 0.45–0.75 G, width 0.20–0.35 G (G = belt → lowest tip).
  - 7 underlapping panels, length 0.25–0.45 G.
  - Each panel has its own root, diagonal edges and unequal lengths (main tips spread over 0.12–0.22 G), and overlaps its neighbours by 20–35 %.
- **Never** carry the widest-hip radius down the garment. Below the hip each panel hangs on its own path.
- **Lining:** 3–5 broad tan reveals rising between the panels, about 20–30 % of the visible leather in front and 3/4 role renders. Not a strip of teeth at the hem.
- **Belt:** an irregular seated rope, diameter 0.06–0.08 G, its centreline rising and falling 0.02–0.04 G, pale `rope_bone`.
- **Stone:** an elongated faceted pendant, 0.20–0.25 G tall, 0.07–0.10 G wide.

**Machine gates:**
- Delivered assembly: skirt + every lining ≤ 900, belt ≤ 150, stone ≤ 60 tris. Automatic lining counts.
- Role parts keep their own materials through fitting.
- Skin-showing all round, down to the top of the hem teeth.
- Flat normals on panels and stone.

## Bandeau (female top) — `scripts/build_bandeau.py` (25/10/2026)
Boss: «underarm not overarm» · «các nét rách của tà áo hơi bị đều» · «tà áo phía trên hơi đều chưa tự nhiên» · «nách trái phía sau - áo bị lộ da».

**Construction:**
- Cut from the ARM-LESS torso sections. Rows sit at the under-bust fold, ON the bust peak, halfway up, and at the top rim (20 angles × 4 rows = 400 tris).
- The radius is widened by any full-body skin within 2.5 cm outside the hull, so it wraps the arm–back junction at the armpit.

**Torn edges:** seeded, irregular teeth on the bottom (6) AND on the top rim (9). Each tooth has its own centre, depth and width, and sits at its own height.

**Gates:**
- **Evenness:** ≥ 2 of 3 must hold: depth CV ≥ 0.25, spacing CV ≥ 0.25, width CV ≥ 0.25. Reverse: `THU_EVEN_HEM=1` ⇒ rc=1.
- **Skin showing:** ≤ 1 %. v2 measures 0.18 %.
- **`check_fit_gate.py --gate top_underarm`:** standoff ≤ 8 mm.


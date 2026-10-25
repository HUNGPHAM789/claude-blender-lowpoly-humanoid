# SPEC — chunky primal ponytail hair (v1.0, 25/10/2026)

Numbers: `SPEC_primal_ponytail_hair.json`. Source: 3 female Hunyuan3D-2 teacher meshes (seeds 42/7/123), Codex asset image drawn 3/4 side-back
so the tail is visible. The head part follows `SPEC_primal_spiky_hair` (female regions); this spec adds the TAIL and the TIE.

## 1. What it is
Female spiky hair gathered at the back of the head by one light rope tie; below the tie a thick bundle of blade locks hangs down and
backwards, swells, then tapers to a fan of 13–15 pointed lock tips.

## 2. Tail (p10 / p50 / p90)
| property | value | how measured |
|---|---|---|
| length root → tip | 18.7 / 19.8 / 24.7 cm | PCA axis of the midline hair behind and below the head centre |
| droop from vertical | 36 / 40 / 44° | |
| root height on the head (0 = chin, 1 = top) | 0.55 / 0.56 / 0.57 | |
| root behind the head centre | 11.7 / 13.1 / 13.4 cm | |
| max radius | 4.1 / 4.3 / 4.6 cm | 16 slices along the axis |
| radius ÷ max, root → tip (median of 16 slices) | 0.74 0.87 0.74 0.57 0.67 0.61 0.73 0.81 **1.0** 0.67 0.78 0.76 0.62 0.74 0.45 0.36 | swell at ≈ 55 % of the length, tip ≈ 0.36 |
| lock tips in the lower half | 13 / 14 / 15 | clump tips from `analyze_hair.py` |
| lock tips spread round the axis | 222 / 238 / 289° | locks fan round most of the tail, not one side |

## 3. Tie
| property | value |
|---|---|
| found | 2 / 3 samples (one ring mold, light-voted, `segment_mesh.py --kind hair`) |
| position along the tail from the root | 0.30 (0.28–0.31) |
| band width | ≤ 6.4–7.6 cm measured (includes touching hair) ⇒ **design rule: 2–3 cm band** |
| radius | 4.7–8.3 cm measured (upper bound) ⇒ design rule: tail radius at that point + 0.5 cm |
| colour | rope `(196, 164, 108)` |

## 4. Gather (design choice)
In the teachers the back/crown clumps hang loose — their axis points 114–131° away from the tail root, they do NOT converge on the tie.
The builder SHOULD pull back/crown clumps toward the root (that is what reads as a ponytail in game); keep the female side/fringe free.

## 5. Colour and budget
Hair `(58, 40, 28)`, tie `(196, 164, 108)` via `theme_colors.mau()`. Tris: tail ≤ 500, tie ≤ 60 (plus the head cap from the hair spec).

## 6. Gates
1. `analyze_ponytail.py` on the built mesh: length, droop, root height within the learned [p10, p90] ± 10 %.
2. Taper: tip radius ≤ 0.5 × max radius; max radius within the learned range.
3. Tie: `segment_mesh.py --kind hair` finds exactly one tie mold at 0.2–0.4 of the tail from the root.
4. Behind: tail centre ≥ 8 cm behind the head centre, never in front of the ears.
5. Rig: tail weighted to head/neck only (no arm/shoulder bones); pose test stretch ≤ 3×.

# HM combined humanoid — build + test notes (22/10/2026)

## 1. What was built
- `hm.py` (builder) · `hm_check.py` (gates, auto-run, exit 1 on any red) · `hand.py` (LPM grip hand, copied unchanged) ·
  `view_hm.py` (Blender 5.2 front/side render, the same ortho camera, clay material, lights and 2.1 ortho scale as LPM `view_lpm.py`) ·
  `build_all.sh` · `SKILL.md`.
- 5 test builds in `out/` (GLB + JSON + HAIR GLB + gate log), all rc=0. Renders in `renders/<tier>_<gioi>[_faceless]_<front|side>.png`
  (faced models are rendered wearing their hair: nam = short, nu = bob). `counts.json` = counts measured from the exported meshes.
- 3 build→render→fix rounds were used: (1) budget/arm-length/inside-test fixes, (2) arm roots sunk into the shoulder + thinner thigh tops,
  (3) grip-hand scale fix (female --co 1 penetration 3.1 mm → 0.4 mm).

| model | body tris | hair tris | shoulder→tip | fingertip | worst twist | rc |
|---|---:|---:|---:|---:|---:|---:|
| rut_gon_nam | 1,156 | 48 (short) | 0.435 H | 0.409 H | 0.65° | 0 |
| rut_gon_nu | 1,156 | 50 (bob) | 0.439 H | 0.407 H | 0.65° | 0 |
| rut_gon_nam_faceless | 1,024 | — | 0.435 H | 0.409 H | 0.65° | 0 |
| chi_tiet_nam | 2,368 | 77 (short) | 0.426 H | 0.415 H | 0.52° | 0 |
| chi_tiet_nu | 2,368 | 88 (bob) | 0.425 H | 0.417 H | 0.52° | 0 |
Grip pose: rut_gon nam --co 1 wrap 80 % / 1.0 mm, nu 75 % / 0.4 mm (rc=0). chi_tiet --co 1 builds (rc=0) but grip is not gated.

## 2. Reverse tests (all run; rc from the command)
| gate | input | result | rc |
|---|---|---|---|
| ⑯ twist | `test_spec/simplified/BODY_F.glb` | legs 22.5° (8-gon, 7 rings), arms 30.0° (6-gon, 6 rings) | 1 |
| ⑯ twist | own `simplified_female.glb` | worst 0.7° over 10 limbs | 0 |
| ⑯ twist | own build with alternating ring phase (mutation) | 22.5° legs / 30° arms | 1 |
| ⑯ twist | `test_spec/detailed/BODY_M.glb` | no limb shell isolable (one connected mesh) ⇒ "nothing measured" ⇒ fail | 1 (not a twist finding) |
| ⑰ arm | `test_spec/detailed/BODY_M.glb` | L/H 0.425 (in band) · fingertip 0.369 H (< 0.38) | 1 |
| ⑰ arm | own `detailed_male.glb` | 0.426 H · tip 0.415 H | 0 |
| ⑰ arm | own build with +12 % arm segments | 0.472 H · tip 0.378 H | 1 |
| ⑰ arm | `test_spec/simplified/BODY_F.glb` | 0.399 H (short) | 1 |
| ⑱ hair | own chi_tiet_nu bob at k = 0.97 | 1,851 / 4,000 inside | 1 |
| ⑱ hair | same at k = 1.032 | 0 / 4,000, gap min 2.5 / median 3.2 mm | 0 |
| ② budget | faceless rut_gon before ring additions | 908 (< 950) | 1 (round 1, real failure) |

Honest caveats:
- On the detailed model the arm gate fails on fingertip height, not on L/H: its shoulder corner lands on the upper arm (its shoulders are low and narrow), so L/H alone would have let it through.
- ⑲ landmarks is weak: the shoulder-top ring is placed FROM the table, so Δ0 is close to tautological; head top/chin are real measurements.
- ⑨ faced-head density ceiling (3.5×) was set after measuring the C head (3.3×); it guards against regressions and does not prove "uniform density".

## 3. Visible open issues (from the renders)
- Front view: a horizontal ledge where the torso's crotch rim meets the thigh tops, and a seam at the knee (separate thigh and shin parts, LPM contract).
- rut_gon face (C): long, pointed chin; eyes are flat 1-quad dark patches. chi_tiet face (B) reads «tạm ổn» as before (blocky jaw).
- Hair is a cap made of scalp facets plus vertical panels: it reads as a helmet/bob, with no stylised clumps (stylisation was not required).
- rut_gon arms are thin. Glutes pass ⑩ (nam 53 mm, nu 72 mm projection) but they are subtle in the side render at this scale.
- The chi_tiet 5-finger hand has no grip solver: `--co` only curls the fingers 8°→83°. Feet are 128 tris against the 160 in spec B.
- There is no rig or deformation test, same as all three sources.

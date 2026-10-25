# deer_v1_rig — rigged + animated low-poly deer (23/10/2026)
Boss: «Rồi giờ tới săn nai. Animation cho nai - ăn cỏ idle, đi bộ, chạy, chết - có dùng kimodo ko?»
**Kimodo: NO** — its skeletons are human only (somaskel30/77, smplx22) + the G1 humanoid robot; no quadruped. Everything here is code.

Run: `blender -b -P build_rig.py` (rig + 4 actions + gates, exit 1) then `blender -b deer_rig.blend -P render_loops.py` (one mp4 per action).
Built on the rabbit_v1_rig recipe: bones from plan masses (scale 0.857, plan +Y → Blender −Y), heat weights → capsule + midline cleanup, antler verts 100% head, eyes bone-parented to head. Every bone rolled so local X = world +X ⇒ rotation about local X = pitch.

| action | frames | how |
|---|---|---|
| graze | 0–96 loop | body pitched 10° + hips dropped 3 cm, legs IK back to their hoof spots; neck STRETCHED ×1.5 (mesh neck too short: base 0.53 m vs neck+head 0.37 m) and pitched by a SCAN (not bisection — muzzle height is non-monotonic past ~95°); head counter-pitched −0.1× (same-sign curls the face into the chest); grass-pull bob every 12 f, tail flick, ear twitch, look-up 54–80 |
| walk | 0–28 loop | 4-beat lateral walk HL→FL→HR→FR, 0.45 m/s, stance 62 %, hooves LOCKED by 2-bone IK during stance (front carpus pole forward, hind hock pole back), body lowered 3.5 cm so the stance ends stay in reach |
| run | 0–12 loop | rotary gallop HL 0 · HR .08 · FL .42 · FR .52, 2.3 m/s, stance 25 %, spine flex ±9°, pitch ±4°, body lowered 6 cm |
| death | 0–48 | flinch → front legs buckle → hind sink → roll 86° onto the side → head drops; per-frame floor clamp (lowest vertex = 0) |

Gates (checks.json): ground penetration ≥ −10 mm · volume change ≤ 18 % · stance hoof slip ≤ 10 mm/frame · loop seam ≤ 0.02 rad · graze muzzle ≤ 40 mm at the bottom of each bob.
Results 23/10: walk slip 0 · run 8.1 mm · graze muzzle 30 mm, ground −3.7 mm · death ground 0.
Traps paid: stride must match leg length (~0.40 m) — 1.1 m/s walk / 5 m/s run slipped 33 / 108 mm; neck sign/curl found by test, not assumed.
Scale: this deer is ~1.0 m tall incl. antlers (shoulder ~0.6) vs settler 1.75 m — scale ~1.5× in the hunting scene.

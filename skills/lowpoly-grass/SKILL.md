---
name: lowpoly-grass
description: Low-poly grass for the settler game (Blender 5.2 bpy) — tuft geometry in CGTrader nature-set style, scatter with density falloff, loopable wind (tip-weighted sway + travelling gust wave), measured performance of shader vs geometry-nodes wind. Use before building any grass/meadow, answering "does grass wind make the game heavy?", or rendering a grass field clip.
---
# lowpoly-grass (v1, 23/10/2026)
Boss 23/10/2026: «học skill tạo grass này https://www.youtube.com/watch?v=p-xOxa5nL1Q - mà grass movement như vầy có làm nặng game ko?» then «develop cỏ».
Code: `~/projects/GameDev/grass/` (grass_lib.py · bench_perf.py · grass_field.py). Video notes: `grass/learn/gemini.json`, `spoken.txt`.

## 1. What the video teaches (3Dan, «Ghibli style grass with Blender's Geometry nodes (4.5+)», 26 min)
Pipeline (GN, all real-time, no cache):
1. **Few guide curves**: Distribute Points on Faces, **Poisson disk**, one `density` knob drives Density Max = density·4 and Distance Min = sqrt(0.3/density) ⇒ even coverage. Curves made with **Interpolate Curves** (points + one Curve Line as guide) instead of Instance on Points + Realize (1.3 ms vs 1.6 ms; 23 vs 27 ms at high density). Store `mesh_normal`, `mesh_position` on points. Align to surface: Set Position + Vector Rotate (Euler) around **Curve Root** position + Align Rotation to Vector. Resample count **6**.
2. **Wind only on the guide curves** (cheap): Vector Rotate around root, axis = wind direction rotated 90° on Z (swap X/Y, negate one), angle = **Spline Parameter factor × noise**; noise input = position − windDir·SceneTime·speed (noise scrolls downwind), not normalized (blades swing back too), + constant offset = lean (Multiply-Add 0.5 / strength). **Trim Curve (length = height)** so bending doesn't stretch blades. Defaults on screen: initial density 10, child density 75, resolution 8, width 0.1 m, height 1 m, wind speed 0.05, strength 0.75.
3. **Camera culling** (4.5 Camera Info node, from Cartesian Caramel): point → inverse camera matrix → divide by −z → max(|x|,|y|) < padding **1.4** ⇒ Separate Geometry. Then a 2nd Interpolate Curves spawns the dense child curves inheriting the wind.
4. **Mesh as camera-facing cards**: Curve to Mesh with Curve **Line** profile (85k tris) not Curve Circle (345k tris, 8 fps). Set Curve Normal (Free) = cross(cross(camPos−P, tangent), tangent), flipped.
5. **Shader**: diffuse BSDF whose **Normal = stored mesh_normal** (grass lit like the ground ⇒ painterly), blade shape from captured UV (spline parameter across/along) through 2 Float Curves + color-burn ⇒ Mix with Transparent (alpha cut). Colour = noise(mesh_position) → Brightness/Contrast 0.7 → Color Ramp #10103B · #275B24 · #5A8B3F · #96B245. No self-shadow: Mix Transparent by Light Path *Is Camera Ray* (EEVEE Next). Soft (no Greater-Than) falloff = fluffier painterly look.
Verdict for OUR game: the cards+alpha+camera-facing tricks are Blender-render tricks for anime look; our low-poly style uses opaque folded blade tufts (no alpha overdraw), and wind as ONE formula usable in a game vertex shader.

## 2. Measured cost (23/10/2026, M4 Max, Blender 5.2.2 EEVEE, 1280×720, 4 samples, 20×20 m patch, tufts of 9 blades = 126 tris)
`blender -b --factory-startup -P grass/bench_perf.py -- <none|shader|gn> <blades> [verify]` → `BENCH {...}`
| blades | tris | no wind render | shader wind render | GN wind render | GN eval CPU/frame |
|---|---|---|---|---|---|
| 5k | 70k | 60 ms | 61 ms | 65 ms | 1.9 ms |
| 50k | 0.70M | 91 ms | 100 ms | 121 ms | 14 ms |
| 200k | 2.8M | 182 ms | 204 ms | 289 ms | 53 ms |
`verify` proved both winds move pixels (mean |f1−f46| 0.025 both, 0 for none) — the shader number is real, not a no-op.
Reading: **GPU vertex wind ≈ +0–12 %** (instances stay instanced). **CPU/GN wind = realize every instance every frame**: +60 % render AND 53 ms CPU at 200k (= the whole 16 ms budget ×3). Rule: wind belongs in the vertex shader, never in CPU-side deformation.
Game-engine budget (reasoned, not web-sourced): cost = blade count × verts × (1 + shadow cascades) + overdraw. Keep grass ≤ ~0.5–1M tris on screen for mid GPUs (≈ 4–8k tufts visible), GPU-instanced per chunk; **grass casts no shadows** (video also kills self-shadow); fade/scale tufts to 0 at 20–30 m, swap to low tuft at ~12 m; opaque blades (no alpha cards ⇒ no overdraw sorting); frustum-cull per chunk (the video's 1.4 padding idea).

## 3. Our asset (grass_lib.py)
- Blade = V-folded tapered strip (crease ~70°), 4 levels + tip = **13 verts / 14 tris**; tuft = 9 blades splayed 20–45° + curl → **117 verts / 126 tris** (CGTrader tuft 143). Low tuft = H ÷ 2.5, wider + more splay.
- Attribute `h` (0 root → 1 tip) + colour attribute `Col` gradient C_BASE (52,66,30) → C_MID (84,106,42) → C_TIP (146,150,72)/(122,142,58), all through `theme_colors.mau()`. Flat shading.
- Wind (both GN and shader use `wind_offset`): s = P·d; gust = Σ sin(k s + phase·noise − n ω t), n = 2,3,5, ω = 2π/6 s ⇒ **exact 6 s loop**; bend = h²·(LEAN + AMP·gust); z drops by 0.35·bend²/H. In shader: Value node driven `frame/30` → Vector Displacement (World) → Material Output Displacement, material `displacement_method = DISPLACEMENT`.
- Scatter (scatter_group): Distribute RANDOM, Density field = density × ground attribute `dens` (meadow blobs, path, clearing r 0.35 m at settler feet, edge fade) → Instance on Points (pick random of 4 tufts, random yaw/tilt 0.12, scale 0.7–1.3).

## 4. Run
- Field + loop: `blender -b --factory-startup -P grass/grass_field.py -- --wind shader --samples 16` (≈ 1 min for 180 frames at 1080p), then `ffmpeg -framerate 30 -i grass/out/frames/%04d.png -c:v libx264 -pix_fmt yuv420p -crf 18 grass/out/grass_wind_6s.mp4`, then delete frames (180 PNG = 750 MB). `--still --res 50` = preview. Exports tufts `grass/out/co_bui_{cao_1,cao_2,cao_3,thap}.glb`.
- Loop check: mean |f180 − f1| = 2.8 vs |f90 − f1| = 14.5 (seam = one normal frame step).

## 5. Traps (paid for 23/10)
- Blender 5.2 Random Value: ONE output `Value`, inputs Min/Max/ID/Seed only (index 0/1) — old `outputs[2]` code crashes.
- Distribute Points RANDOM has no `Density Factor` (Poisson only) — RANDOM `Density` is a field: multiply attribute in.
- Shader nodes have no Scene Time ⇒ driver `frame/fps` on a Value node (works in `-b`).
- `view_layer.objects` may yield None right after linking a new collection ⇒ `view_layer.update()` + skip None before selecting for glTF export.
- Bench camera only sees part of the patch; render ms is for that view, eval ms is whole patch.
- Bald settler (grass_field): root cause found 23/10 — `HAIR_SHORT_M_dark_brown.glb` has ALL faces pointing inward (trimesh volume −0.0017, 0 % outward) and `doubleSided: false` ⇒ Blender's glTF importer turns backface culling ON ⇒ the hair shell is culled from outside. Fix at import: `bmesh.ops.recalc_face_normals` on the hair mesh (done in `cozy/scene.py`). Real fix belongs upstream in the hair export (hair_outfit) — same family as `feedback_quan_ao_phap_tuyen`.

## 6. Cozy house style — Boss 23/10 rejected realistic carpet
Boss 23/10/2026 on `grass/out/grass_wind_6s.mp4`: «cỏ này xấu nha, ko hợp cozy atmostphere we have. nếu dựa vào skill, tự tạo cỏ, tự animation nhẹ thì sao?»
⇒ 9-blade dense tufts + saturated greens + wall-to-wall carpet = WRONG for this game. sections 1–3 stay only as perf reference (wind cost).
- Grass is an **lpms asset** like rocks/trees: `lpms/assets/grass_a.py`, `grass_b.py`, `grass_c.py` (`BIEN = S|M|L`), built by `grass/cozy/build_bush.py` (lpms render ⇒ receipt + sheet + gates, 9 glbs → `grass/cozy/glb/`). Helper `la_gap()` in `lpms_helpers.py` = origami folded blade, 2 convex closed pieces, 12 tris.
- Palette (in `MAU`, through `theme_colors.mau()`): `co_goc` 66,92,48 · `co_giua` 98,128,62 · `co_ngon` 148,158,86 · flowers `hoa_kem` 236,222,182 · `hoa_vang` 226,188,96 · `hoa_hong` 206,140,128. 2–3 FLAT colour bands = separate parts/material slots, no gradient texture.
- Styles (tris S/M/L): **A** origami folded wide leaves 3–6 per tuft (36/60/72) · **B** soft low-poly mound + dark skirt + light cap + 2–4 leaf tips (40/54/58) · **C** sparse tall thin folded blades + 1–2 flower stems with octahedron heads (40/52/80). Budget per tuft 20–80 (gate `ngan_sach=80`).
- Scatter = `grass/cozy/scatter_clumps.py` (pure numpy, game-reusable): 5 clusters per patch, acceptance (1−d²/R²)^1.3, L in the centre → S at the rim, min distance 0.72·(r_i+r_j), no-grass discs round feet/rock/bush, ~6 lone stragglers; GROUND MUST SHOW between patches. Ground = faceted warm earth (150,124,92 ±5) with a faint moss tint under patches — keep tint contrast low or the checker facets get busy.
- Wind: each patch is ONE static joined mesh + GN Set Position modifier (per-vertex = vertex shader in game, never realize per frame): bend = z²·(0.09 + 0.31·gust), gust harmonics 2/3/5 of 2π/6 s (0.33/0.5/0.83 Hz) ⇒ exact 6 s loop; 0.4 m tip leans 1.4 cm ± 5 cm; roots fixed (z = rest height above ground, no extra attribute needed).
- Review render: `blender -b -P grass/cozy/scene.py -- still <png>` then `python3 grass/cozy/nhan.py <png> grass/cozy/ABC.png`; video `-- video <frames_dir>` → `nhan.py <dir> <dir2>` → ffmpeg ⇒ `ABC_wind.mp4` (EEVEE ≈ 1–2 s/frame at 720p). Settler + berry bush + rock_medium in every patch for scale. Awaiting Boss's pick A/B/C.


## 7. GRASS FLOOR / lawn (Boss 23/10/2026: «like golf course grass so we can do wind effect… square blade thin, 2-3 color of green… feather blur»)
Script `GameDev/grass/grass_field/grass_field.py` (env `KIEU` vuong|xien|nhon|cg, `CAO` m, `MAT_DO` clumps/m², `FSTOP`); A/B runner `grass_field/ab3.sh`.
- Blade = thin strip (6 mm, ×1.4 when tall), 2–3 segments, flat; tips: `vuong` square · `xien` slanted (one edge 22% lower) · `nhon` single apex. Clump = 6–8 blades, 3 clump variants, GN instancing (no realize) — 1.3–3.4 M tris rendered fine in EEVEE.
- Colour in the shader (all through `mau()`): 3 greens as LARGE noise patches (scale 0.22) + per-clump ±7% (Object Info Random); root = soil-under-grass colour (that is the "feather": blades melt into the ground), tip lighter by h^p. Ground under grass is DARK GREEN so gaps still read as grass. Path edge = density AND scale fall off with `mat_do` (soft border). Camera DOF f/2.2.
- Wind = `grass_lib.wind_offset` as shader displacement on instances, period LOOP 6 s.
- ⛔ Traps paid 23/10: (1) `ShaderNodeVectorDisplacement` Scale defaults to 0.01 ⇒ wind ×100 too small, grass frozen — set 1.0. (2) a GN modifier that outputs only `Instance on Points` deletes the ground mesh ⇒ Join Geometry with the input. (3) bmesh loop colour «Col» did not read in EEVEE ⇒ drive ground colour from the float point attribute. (4) Loop seam measured on mp4 is dominated by H.264 error on grass (1.3–2.2 grey levels vs real seam 0.74) ⇒ gate `GameDev/grass/check_wind.py` runs on the PNG frames (20 warm-up frames dropped), exit 1 if motion < 0.5 or seam > 3× one-frame step; encode crf 12 `-tune grain`.
- A/B 23/10 (sent): A slanted ×4 (14 cm) bright tips · B pointed ×4 · C CGTrader Grass_bush_low/high scattered 5/m² · D golf 3.5 cm. Boss picks.

## 8. GHIBLI floor (Boss chose B 23/10; Codex 2 rounds) — `GameDev/grass/ghibli/grass_ghibli.py` GH=0..4 cumulative
GH4 = current: blades 7 cm median (N(7,1.1) cm + 7% accents 9.5–11.5), 9 mm wide, apex at height, 6/clump fanned (72% shared azimuth ±25°), 300 clumps/m²;
light normal = 70% up + 30% blade (sign: −1 if z<0 else +1 — SIGN(0) zeroes vertical faces); base-only occlusion ×(1−.25(1−smoothstep(0,.3,u)));
palette ramp #365D32/#659337/#9FBB48 @ .2/.5/.8, tip #CDD66A ≤45% from u .65 × sun-facing mask; colour field anchored at CLUMP ROOT (Object Info Location) shared with the ground;
dark pockets (noise 1.6, ~20%, 42% toward #365D32); light pools (noise 0.32, −20%); sun #FFF0D5 3.4, fill #CADAE4 0.35, AgX Base Contrast.
Wind: shared gust step 1.2 m + per-blade phase sway (mesh attribute «pha», integer harmonics 2 and 3 of 1/6 s ⇒ still loops), lateral component too.
⛔ Trap: Codex v1 numbers (L* 55–65, crop std ≤5) all passed while the field looked foggy/flat — always add chroma (C*ab 35–50), 1 m-scale P90−P10 L* (10–18) and dark-mass fraction (15–25%) before trusting a look gate.

### ✅ LOCKED grass floor (Boss 23/10/2026 «Chốt bản này làm cỏ nền chuẩn»)
`GH=4 CAO=0.10 HOA=1 TOI=1 blender -b -P GameDev/grass/ghibli/grass_ghibli.py -- <out>` (defaults TUI_NG 0.63, VUNG_NG 0.57, HOA_NGUONG 0.55, HOA_DO 14):
10 cm pointed blades, GH4 colour/normals/wind (gust 1.2 m + per-blade sway), few dark pockets/cloud pools, low-poly flowers in pockets
(heads 36–48 mm #FFF6DC/#F2C14E/#F4B6C2, ~2.2/m², sway with the grass). Reference render: grass/ghibli/FLOWER2/image.png + wind.mp4.

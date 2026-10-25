---
name: quadruped-rig-animation
description: Spec + recipe for low-poly FOUR-LEGGED animals (deer, stag, horse, dog, boar…) — rig topology, body proportions, gait timing (walk / gallop), grazing, hit-react, death — reverse-engineered from Quaternius CC0 deer/stag (measured, not guessed), plus how to turn a downloaded animal into our "origami" house style. Read BEFORE building or animating any quadruped. Kimodo cannot do this (human-only skeletons).
---

# Quadrupeds (Boss 23/10/2026)
Boss: «Nail quaterus is good use that - should we low poly origami it for our own version? Test AB» · «học cách làm rig của con nai quaternius,
cách animation của nó, ghi skill, cách làm low poly của nó… dáng mũi, cách bước đi, thân mình, cổ khi ăn… ghi spec chi tiết để có thể làm con khác sau này».

## 0. Decision order for a new animal
1. **Look for a CC0 rigged+animated one first** (Quaternius on poly.pizza: `curl -sL https://poly.pizza/m/<id> | grep -oE 'https://static.poly.pizza/[^"]*\.glb'`). Ask Boss before downloading. Keep downloads in their own folder + `SOURCE.txt`.
2. If found → convert to house style (§5). If not → build with this spec (§1–4) using `~/projects/GameDev/assets/organic/deer_v1_rig/build_rig.py` as the code base.
3. ⛔ Kimodo: human (somaskel30/77, smplx22) + G1 robot only.

Measure any reference with `scripts/analysis.py <model.glb> <out.json>` (all lengths ÷ H).
**H = withers height** (top of the back above the front legs, measured on the MESH — the shoulder JOINT sits deep in the chest and is lower).

## 1. Rig topology (Quaternius "AnimalArmature", same for stag & deer)
```
Body → Back → Torso → Torso2 → Torso3 → Neck1 → Neck2 → Neck3 → Head (→ Ear1..4 .L/.R on deer)
Torso3 → FrontShoulder.X → FrontUpperLeg.X → FrontLowerLeg.X          (3 bones: scapula, upper, cannon+hoof)
Body/Back → BackShoulder.X → BackLeg.X → BackUpperLeg.X → BackLowerLeg.X  (4 bones: pelvis-side, thigh, gaskin, cannon+hoof)
Back → Tail1 → Tail2 → Tail3
helpers (non-skinned in practice): IKFrontLeg.X, IKBackLeg.X, PoleTarget.X, PoleTargetBack.X, FF.X, FFB.X
```
- Stag 38 bones, deer 46 (ears 4 bones each side). glTF carries NO constraints: every action is **baked on every frame** (keys = frames + 1) on every bone. In Blender the IK bones drive the legs; export bakes FK.
- **Spine = 5 bones** (Body, Back, Torso, Torso2, Torso3) ⇒ smooth back flex in gallop/death; ours had 3 (pelvis, spine, chest) — use ≥4.
- **Hind leg = 4 bones** (true dog-leg: stifle forward, hock backward); front = 3 (carpus). Our deer used 2+hoof per leg ⇒ stiff hocks.
- **Neck = 3 bones** ⇒ the neck curves (S-shape when grazing) instead of rotating as one stick.

## 2. Proportions (÷ H; stag / deer)
| measure | stag | deer | ours v1 (problem) |
|---|---|---|---|
| neck length (Neck1 head → Head head) | 0.445 | 0.455 | ≈0.37 incl. head ⇒ could not reach grass |
| head length (Head joint → muzzle tip) | 0.28 | 0.29 | — |
| shoulder-joint ↔ hip-joint distance | 0.65 | 0.62 | |
| head joint height at rest | 1.16 | 1.23 | |
| muzzle tip height at rest | 1.08 | 1.19 | |
| muzzle ahead of front shoulder joint | 0.32 | 0.26 | |
| front leg: upper → cannon (joint spacing) | 0.30 | 0.29 | |
| hind leg: thigh 0.23 · gaskin 0.35 | 0.23 / 0.35 | 0.22 / 0.33 | |
**Rule:** neck + head ≥ 0.70 H, else the animal cannot graze with straight legs.

**Nose / head shape** (cross-section width × height ÷ H, from back of skull 0% → nose tip 100%):
stag 20% 0.28×0.22 · 40% 0.22×0.22 · 60% 0.17×0.17 · 80% 0.11×0.12 · 95% 0.10×0.08 — a **wedge that tapers ~3× from skull to nose, almost square in section**, nose slightly flatter than wide; deer is narrower (95%: 0.08×0.09).

**Mesh style:** 2.1k (deer) – 3.7k (stag, 1.6k of it antlers) tris, smooth-shaded in the source (the facets come from geometry). Tris by region (stag body): head 815 · body 432 · neck 239 · front legs 225 · hind legs 205 · tail 133 — **the head gets the most detail** (eyes, muzzle, ears). Facet size (√face area ÷ H) ≈ 0.04–0.055 everywhere, legs/tail finest (0.037). Colours: 2 body tones (back darker, belly/neck/face cream) + near-black hooves/nose + black eyes.

## 3. Gaits (in-place cycles: root does NOT travel; the game moves the object)
Contact = hoof within 3 % H of its lowest point. Phases are first-contact / cycle.
**Walk — 28 frames @24 (1.17 s)**
| leg | deer phase | duty | hoof lift ÷H | fore-aft swing ÷H |
|---|---|---|---|---|
| HL | 0.18 | ~0.21 | 0.18 | 0.36 |
| FR | 0.29 | ~0.28 | 0.17 | 0.24 |
| HR | 0.64 | ~0.24 | 0.18 | 0.38 |
| FL | 0.75 | ~0.35 | 0.16 | 0.26 |
Order **HL → FR → HR → FL** (each hind followed ~0.11 cycle later by the OPPOSITE fore = diagonal-sequence walk; ours used lateral HL→FL). Hind legs swing ~1.5× further than fore. Body bob 0.025 H, body pitch varies only ±2°, neck nods 5° (55→58°).
(The duty numbers are lower than biology because the threshold is tight; use 0.55–0.65 when building with hoof locking.)

**Gallop — 12 frames (0.5 s)**: HR 0.42 → HL 0.50 → FR 0.83–0.92 → FL 1.00 (= 0). Same lead side in both pairs ⇒ **transverse gallop**; one long suspension after FL (~0.4 cycle with no hoof down). Hind hooves lift 0.37–0.49 H (tuck high under the belly), fore 0.20 H; hind reach 0.46–0.53 H. Body bob 0.055 H; **body pitch swings 16°** (rocking horse: −19° → −3°); neck swings 20° (34→54°) counter to the body.

## 4. Behaviours
- **Eating** (stag 290 f / deer 144 f, loop): legs straight, body pitch changes only 2° (−13 → −15), **all the reach comes from the neck: +57° (up) → −44° (down) ≈ 100° travel through the 3 neck bones**, head pitches so the muzzle points at the ground. Muzzle bottoms at 0.12–0.21 H (nose in the grass, mouth at ground level). Long idle chewing at the bottom, occasional lift.
- **Idle**: 80 f loop, body bob ≤ 0.01 H, neck ±0.5° (breathing only). Idle_2 / Idle_Headlow variants.
- **Hit react** (Left/Right, 11–12 f): neck snaps UP +10°, body pitch +7° (front rises), body bobs 0.05 H, muzzle rises 0.15–0.25 H, then back to idle. Use for the arrow impact before death.
- **Death** (stag 26 f ≈ 1.1 s, deer 20 f): fast. Body drops 0.11–0.12 H, body pitch −14° → +5°, neck goes from +79° to −24° (head swings down to the ground), muzzle ends AT the ground (0.008 H). No long roll — a quick collapse to the side.

## 5. Convert a downloaded animal to our ORIGAMI house style (A/B 23/10)
Script: `~/projects/GameDev/assets/organic/downloads/quaternius_deer/ab_origami.py <in.glb> <out_dir> [ratio=0.35]` → `stag_origami.glb` + A/B renders + gates.
1. **Weld first** (`remove_doubles` 1e-4): source meshes are split at every material/UV seam (stag body: 4,203 open edges before welding, 12 after). Decimating unwelded ⇒ the mesh TEARS into islands (seen in B v1).
2. Decimate COLLAPSE (ratio 0.35, antlers 0.28) as the FIRST modifier and apply it on the rest pose, BEFORE the Armature modifier ⇒ vertex groups are interpolated and kept (0 unweighted verts). Stag 3,667 → 1,163 tris.
3. Flat shading; colours by ORIGINAL base colour (re-imported materials get renamed, so never map by name): fur → (170,130,84), cream → (225,220,205), dark/hooves → (96,70,50), eyes → (40,36,32), antlers → (214,208,196), sRGB written straight (house look).
4. Gates (exit 1): open edges ≤ the welded source's own count; 0 unweighted verts; all actions present; lowest hoof point differs from the original ≤ 2 cm on every 4th frame of every action (measured 2.8 mm).
5. Scale to real size: stag with antlers ≈ 1.7 m next to the 1.75 m settler.

## 6. Traps paid for (23/10)
- Stride must match leg length: our deer at 1.1 m/s walk / 5 m/s run slipped 33 / 108 mm per frame.
- Neck too short ⇒ we had to pitch the body / stretch the neck to graze. Fix the proportion (§2 rule), not the animation.
- Neck/head rotation sign: find by test. Same-sign head pitch curls the face into the chest.
- Bisection on a non-monotonic quantity (muzzle height vs neck angle) picks wrong answers — scan.
- Analysis traps: the Quaternius Head bone points UP (its tail is not the muzzle — track the frontmost head vertex); bone `length` × object scale gave nonsense — measure joint positions in world space.

## 6b. UNIVERSAL DEATH + antler attach (23/10/2026)
- Boss: «có universial dead animal animation để xài chung… at least 4 legs?» ⇒ `scripts/death_shared.py` `chet(arm, meshes, ban_do, f0, ben, nhip)`. Works on ANY 4-leg rig from a bone map (spine, neck, head, 4 legs top→bottom, tail, ears); nothing hand-tuned per animal: lateral/forward/up read from the rig, knee fold direction found by trial (±), neck+head (+ last spine bone) drop angle found by SCANNING (height vs angle is not monotonic — bisection failed on the rabbit). Body roll = object rotation about the body axis; every frame the lowest mesh vertex is clamped to the ground. Ready maps: `BD_NAI_B`, `BD_THO`. Demo: `blender -b -P death_shared.py -- demo <out>`; gates exit 1: penetration ≤ 5 mm, final roll ≥ 70°, head-region lowest vertex ≤ 3% body length above ground, last 8 frames still.
- Traps: measure the head by its LOWEST MESH VERTEX (head-bone vertex group), not the bone tip (on its side the nose is a head-radius up). Ears must lay BACK along the neck — drooping forward they prop the head up. Antlers touching first is fine (real stags lie on them).
- ⛔ Antlers: Quaternius horns are bone-parented to `Head`; through glTF import they sit 17 cm ABOVE the skull (12–15% of height) in rest AND in actions — every deer clip before 23/10 had it (Boss: «sừng nai vẫn đang còn gap rất to so với đầu»). Fix + gate: `scripts/attach_antlers.py <in.glb> <out.glb>` (moves antler bases onto the skin by BVH surface distance, converts to SKIN on Head weight 1 so it survives export; gate gap ≤ 1% height, exit 1). Wired into `ab_origami.py`. Measure distance to the SURFACE, not the nearest vertex (low-poly vertices are cm apart ⇒ fake 1.1–1.4% floor).

## 7. SOURCE LOG — where assets came from / can come from (Boss 23/10/2026: «Các source trước giờ mình sử dụng nhớ log lại cho skill này luôn - ghi chi tiết nguồn nào có gì đặc biệt để sau này còn vào tải thêm»)
| source | what it has | licence / cost | how to get | used for |
|---|---|---|---|---|
| **Quaternius via poly.pizza** (`poly.pizza/m/tQdzbZ1Cmw` Stag, `poly.pizza/m/T6Cs7tmMHJ` Deer) | rigged low-poly animals, **13 actions each** (Eating, Walk, Gallop, Gallop_Jump, Idle ×3, HitReact L/R, Jump_toIdle, Death, Attack_Headbutt, Attack_Kick), flat colours, no textures, 2–3.7k tris; same "AnimalArmature" on all animals of the pack | **CC0**, free | page HTML has `https://static.poly.pizza/<uuid>.glb` (curl grep); ~1 MB each | ⭐ our deer (A/B, origami B) — `assets/organic/downloads/quaternius_deer/` + SOURCE.txt |
| Quaternius "Ultimate Animated Animal Pack" (quaternius.com/packs/ultimateanimatedanimals.html) | 12 animals, >12 actions each, FBX/OBJ/Blend/glTF | CC0 | site download buttons (not fetched yet); itch.io "LowPoly Animated Animals" = older 6-animal pack (no deer) | next animals (horse, wolf, fox, cow…) |
| **Envato Elements** — author **Rajibcou** (`elements.envato.com/user/Rajibcou/stock-video?searchTerm=Deer`), 2,556 items | **stock VIDEOS** of realistic 3D deer with **alpha channel**: grazing (`/deer-eat-XBU7HDY`, `/deer-eat-VWY38QG`), walking loop (`/fawn-deer-walk-J4TTPUV`, `/deer-walk-9WUQHSA`), lying/chewing (`/deer-stag-sit-idle-and-chew-UKGGDJS`) — motion REFERENCE, not 3D files | Envato subscription | needs Boss signed in to Envato in the browser (shows "Subscribe to download" when not) | animation reference (grazing timing/poses). Boss: «Envato has a lot of sfx and 3D model and animation» — search there for SFX/3D too |
| Sketchfab — Fabian Orrego (Xunulu) "Fantasy Deer – Locomotion Animations" (YouTube 3TCP_tKJgQY) | faceted low-poly deer, 4 locomotion clips, 2.7k tris | **not downloadable, no licence** | — | STYLE reference only |
| kag3d.itch.io "Red deer 3D animated animal" | Gazing, Idle, Run1, Run2, Walk; GLB 12 MB + FBX | ≥ $5, licence not stated | itch.io purchase | not used |
| Fab "Low World Forest Animals Kit" | deer + stag: Idle, Walk, Run, Sleep; GLB/glTF/USDZ | licence not stated | Fab | not used (no death/eat) |
| Superhive (Blender Market) stag/reindeer/fawn | Eating, Gallop, Walk, Idle, Death…, GLB | paid | — | not used |
| Mixkit (mixkit.co) | free SFX (chop, rock hits, debris, footsteps) | Mixkit free licence | direct download | settler SFX: `anim_settler/sfx/mk*/SOURCE.txt` |
| NVIDIA Kimodo (local, `~/projects/GameDev/kimodo`) | text→motion for HUMANS only | local | `kimodo_gen` (sinh_*.sh) | settler walk/carry/chop/pickaxe/bow; ⛔ animals |
| Codex imagegen (`~/bin/anchor-gen`) | concept art + build SPEC in our primitives | our quota | — | berry bush, food storage (`concept/food/`) |

## 8. Colour themes (keep both; switch by table)
- **A — Quaternius original** (no textures; glTF `metallicFactor 0.4`, `roughnessFactor 0.415` ⇒ slightly glossy; SMOOTH shading). Stag: fur linear (0.192,0.112,0.047) ≈ sRGB 121,94,61 · cream (0.382,0.319,0.233) ≈ 166,153,133 · dark (0.07,0.042,0.019) ≈ 75,58,37 · hooves/antlers (0.028,0.021,0.013) ≈ 47,40,30 · eyes ≈ 20,20,20. Deer (doe): Main ≈ 134,89,61 · Main_Light ≈ 166,153,133 · Main_Dark ≈ 104,69,47 · Hooves ≈ 68,58,56 · Eye_Lighter ≈ 158,105,72 · Eye_Black 20 · Eye_White 200.
- **B — our origami** (Boss 23/10 «Cho nai của mình màu đậm hơn và sừng màu nâu đen»): FLAT shading, roughness 0.9, metallic 0, colours given as the DISPLAY sRGB and converted to linear (`tt()` in ab_origami.py): fur 124,88,58 · cream 190,172,142 · dark 78,58,42 · hooves 52,42,34 · eyes 24,22,20 · **antlers 48,38,30**. ⚠️ The house habit of writing sRGB straight into the linear slot BRIGHTENS colours (62,48,36 showed as ~135,118,100 ⇒ antlers grey-brown) — fine for pale props, wrong for dark animals.

## 9. ANTLERS / branching that reads "natural" (Boss 23/10/2026: «Phong cách sừng của nai, thể hiện nhiều nét như cây, cũng đáng để học và ghi vào skill, cách mô tả hình học cong thẳng naturally»)
Measured on the Quaternius stag with `scripts/check_antlers.py <model.glb> <out.json> Horn` (geodesic tips + beam path; pure Python Dijkstra because Blender's Python has no scipy). Renders: one connected welded mesh per side, 409 verts / 808 tris, low-poly tubes of ~6–8 sides.
**Main beam**
- Built as **straight segments joined by kinks**, NOT a smooth spline: 12 segments, kink 8–33° between neighbours (mean ~17°), chord/length = **0.89**. The eye reads the kinks as a natural curve; a perfect arc looks plastic.
- Sweeps BACK then UP: first segment direction ≈ (side 0.18, back 0.63, up 0.75) → last ≈ (0.05, 0.31, 0.95). Overall a rising arc that ends near-vertical.
- **Taper ~3×**: radius 0.05 L at the base → 0.017 L at the tip, with **knuckle bulges** 0.10–0.19 L where a tine leaves (forks are fatter than the shafts).
**Tines (9 per side)**
- All grow from the FRONT/UPPER side of the beam and point UP (vertical component 0.25–0.92); each tine also bends up toward its tip.
- Lengths 0.09–0.48 of the beam; the **longest are at the base** (brow/bez tines 0.33–0.48) and they get shorter upward.
- Angle off the beam: low tines open WIDE (45–85°), upper tines close in (6–28°) ⇒ the top ends in a near-parallel crown fork.
- Spacing widens upward: three tines clustered at 0–0.21 of the beam, then 0.35, 0.58, 0.71.
**Generative recipe (also for tree branches)**: polyline beam of N straight segments, each turned 8–30° (random sign within a plane that rotates slowly) so chord/length ≈ 0.85–0.9; radius tapers ~3× base→tip with +60–100 % bulges at forks; children spawn from the convex/upper side, length ∝ (1 − position)^0.8, opening angle ∝ (1 − position) (wide low, narrow high), and every child is itself a 2–4 segment kinked polyline curving toward "up". Mirror for the other side with small random differences.


- **CGTrader — Low-Poly Forest Nature Set Free Trial (flamazilla)** · 23/10/2026 · 37 nature props (trees, spruce, bushes, stones, stumps, logs, grass, flowers, mushrooms), one palette-atlas material. Licence «Royalty Free, No AI» — Boss allowed game + AI learning. Local: `GameDev/assets/downloads/cgtrader_forest/`. Geometry rules extracted → `GameDev/lpms/README.md` §Nature-set. Same author sells the full set (more trees/props) — check before modelling scenery by hand.
## 10. PROCEDURAL HERD RECIPE (Boss 24/10/2026: «The way you make huou me and huou con is good. Note that, and if that is new method then note down that recipe»)
When populating wildlife or farm animals in a game level/scene, NEVER place identical duplicated T-pose or idle meshes. Use this exact procedural method to generate a lifelike, cohesive family herd from a single base rigged asset (e.g. `doe_origami.glb` & `stag_origami.glb`):

```python
def spawn_static_posed_animal(filepath, name, action_name, frame, loc, yaw_deg, scale):
    """
    Bakes a specific animation keyframe into a static, zeroed, ground-locked mesh
    with procedural scale hierarchy (Fawn, Yearling, Doe, Stag).
    """
    truoc = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=filepath)
    moi = [o for o in bpy.data.objects if o not in truoc]
    
    # 1. Clean extraneous primitives
    for o in list(moi):
        if 'Icosphere' in o.name:
            bpy.data.objects.remove(o, do_unlink=True)
            moi.remove(o)
            
    arm = [o for o in moi if o.type == 'ARMATURE'][0]
    meshes = [o for o in moi if o.type == 'MESH']
    
    # 2. Bind action and jump to keyframe
    act = bpy.data.actions.get(action_name) or bpy.data.actions.get(f'AnimalArmature|{action_name}')
    if act: arm.animation_data.action = act
    bpy.context.scene.frame_set(frame)
    bpy.context.view_layer.update()
    
    # 3. Evaluate deformed mesh & compute lowest hoof Z (Ground Locking)
    dg = bpy.context.evaluated_depsgraph_get()
    min_z = 999.0
    for m in meshes:
        eval_m = m.evaluated_get(dg)
        to_m = eval_m.to_mesh()
        for v in to_m.vertices:
            w_v = m.matrix_world @ v.co
            min_z = min(min_z, w_v.z)
        eval_m.to_mesh_clear()
        
    # 4. Bake posed mesh into world space, zero feet at Z=0.0m, apply yaw & scale
    created_objs = []
    rot_mat = Matrix.Rotation(math.radians(yaw_deg), 4, 'Z')
    for i, m in enumerate(meshes):
        eval_m = m.evaluated_get(dg)
        new_mesh_data = bpy.data.meshes.new_from_object(eval_m)
        eval_m.to_mesh_clear()
        for v in new_mesh_data.vertices:
            co_posed = m.matrix_world @ v.co
            co_zeroed = Vector((co_posed.x - arm.location.x, co_posed.y - arm.location.y, co_posed.z - min_z))
            co_final = rot_mat @ (co_zeroed * scale)
            v.co = co_final
        obj = bpy.data.objects.new(f'{name}_part_{i}', new_mesh_data)
        bpy.context.collection.objects.link(obj)
        obj.location = Vector(loc)
        for mat in m.data.materials: obj.data.materials.append(mat)
        for p in obj.data.polygons: p.use_smooth = False
        created_objs.append(obj)
        
    # 5. Clean up temporary imported armature and raw meshes
    for o in list(moi):
        if o in bpy.data.objects.values():
            bpy.data.objects.remove(o, do_unlink=True)
    return created_objs
```

### Standard Herd Ratios & Keyframes
| Role in Herd | Base Model | Action | Keyframe | Scale | Pose Description |
|---|---|---|---|---|---|
| **Alpha Stag** | `stag_origami.glb` | `Idle` | Frame 0 | **1.35×** | Head held high, majestic antlers, sentry scanning |
| **Alert Doe** | `doe_origami.glb` | `Idle` | Frame 0 | **1.10×** | Upright vigilant stance, ears forward guarding young |
| **Grazing Doe 1** | `doe_origami.glb` | `Eating` | Frame 50 | **1.10×** | Neck in full S-curve, muzzle touching ground ($Z \approx 0.15 H$) |
| **Grazing Doe 2** | `doe_origami.glb` | `Eating` | Frame 55 | **1.05×** | Secondary grazing posture with slight head tilt |
| **Yearling 1** | `doe_origami.glb` | `Eating` | Frame 50 | **0.82×** | Sub-adult juvenile feeding beside mother |
| **Yearling 2** | `doe_origami.glb` | `Walk` | Frame 10 | **0.85×** | Front left leg lifted mid-stride, moving across glade |
| **Fawn** | `doe_origami.glb` | `Eating` | Frame 50 | **0.55×** | Cute tiny baby deer feeding close to mother |

### Critical Golden Rules
1. **Never scale down antlers for fawns**: Fawns must be derived from `doe_origami.glb` (antlerless).
2. **Zero Foot Sliding / Ground Lock**: Always calculate `min_z` across all four hooves and subtract it from the baked vertices so the lowest hoof vertices sit exactly on $Z=0.0\text{m}$ (terrain plane).
3. **No Modifier Apply Crash**: Never call `bpy.ops.object.modifier_apply` on an armature mesh. Always use `evaluated_depsgraph_get()` and `bpy.data.meshes.new_from_object()` to extract bone-deformed vertices safely.



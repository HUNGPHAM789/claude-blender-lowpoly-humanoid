---
name: humanoid-rig-animation
description: PARENT skill — rig + animate a low-poly humanoid in Blender from code (bpy). Rig from joint landmarks, heat skin + weight transfer to clothes, anatomical-axis adapter, leg IK with world-fixed stance contacts, prop attachment, BVH retarget (Kimodo/SOMA), 10 machine gates, render + GLB export. Child skills (e.g. settler-actions) supply clip JSON + rig profile and must NOT reimplement the solver.
version: 0.1 (22/10/2026)
---

> ⛔ RETIRED 24/10/2026 — Boss: «no longer needed - i don't develop them no more». Deleted: ~/projects/GameDev/hymotion, ~/mocap. Scripts/paths there are GONE — do not run or restore them.

# humanoid-rig-animation (parent)

Boss 22/10/2026: «vậy là bạn phải có 3D animation spec … rig animation skill cho humanoid body và sub skill for humanoid settlers actions».
Spec source: ChatGPT 2 rounds (`~/projects/GameDev/anim_settler/spec/tra1.md`, `tra2.md`) + web research agent
(`spec/web_research.md`, ~30 citations: gait cadence, run duty factor, load carriage, chop timing, squat placement).

## Run
```
blender -b -P scripts/animate.py -- build    --profile <rig-profile.json> --gioi nam|nu --toc den|dark_brown|hat_de --clip <clip.json> --out <dir>
blender -b -P scripts/animate.py -- retarget --profile ... --clip <clip.json> --bvh <kimodo.bvh> --out <dir>
KHONG_RENDER=1 …   # gates only (fast iteration)
```
Out: `<id>.mp4` (iso camera following root), `<id>.glb` (rig + action), `<id>_gates.json`. Exit 1 when any gate fails.

## Conventions (do not re-derive)
- Z up, character faces −Y, LEFT = +X. Metres, degrees. 24 fps, keys 0…N, loop plays [0,N).
- Anatomical axes in character rest space: torso yaw +Z · pitch(forward) +X · roll(left) +Y; hip & shoulder flexion −X;
  knee flexion +X; elbow flexion −X; abduction L −Y / R +Y; clavicle elevation = «abd»; twist = bone Y.
- `B_i = Π Q(R_i⁻¹·axis, θ)` in order: torso yaw→pitch→roll; hip/shoulder flex→abd→twist; elbow flex→twist; knee flex only.
- Bind pose is an A-pose: shoulder abduction values in clips are (spec value − 20°).
- Rest knees are pre-bent ~5° (knee joint moved 2 cm forward in the rig) — a straight rest leg is an IK singularity
  (heel sank 18–26 mm before this fix).
- Root motion: bone `goc` owns travel; hips own bob/sway. Strides/speeds from spec are scaled by s = leg length / 0.86 m
  (settler leg 0.715 m — unscaled spec strides made the trailing leg reach 125–130 %).
- Stance foot lands half a step AHEAD of the pelvis (`−L/4`), held world-fixed; heel-rise pivots around the toe.

## Skinning
Body: weld duplicates (glTF flat shading splits vertices ⇒ heat weights fail 5108/5108) → `ARMATURE_AUTO` →
limit 4 influences → normalise. Clothes: DATA_TRANSFER nearest-face-interpolated from body. Hair: rigid to `head`.
Materials of clothes AND hair: backface culling OFF (hair otherwise renders as an outline = looks bald).
Props attach at REST POSE, before any keys (attaching after keys bakes the parent inverse at the last frame ⇒ props float behind).

## Gates (on bones, integer frames — Blender IK at sub-frames gives garbage, −175 mm seen at 31.5)
⓪ anatomical axis self-test (IK muted) · ① stance foot slip ≤ 5 mm · ② ground penetration ≥ −3 mm · ③ knee ≤ 140°, elbow ≥ −2°
· ⑤ prop–body penetration ≤ 3 mm (ray-parity inside test, 3 jittered rays; nearest-normal test gave a false 715 mm;
calibrated 12/12 known points; clip `tiep_xuc` lists intended contact bones whose faces are excluded) · ⑥ loop seam ≤ 1.5 mm
· ⑧ root travel = speed·s·T within 0.5 % · ⑩ chop: axe-head top ≥ head-top + 0.25 m (measure mesh bbox, NOT part origins = grip).
Plus: 0 unweighted vertices.

## Retarget (Kimodo SOMA BVH → this rig)
Import BVH with axis_up Y (cm → m). Limbs: rotate target segment so its direction matches the source joint segment (after the
parent is posed). Torso/head: 2-vector frame (segment up + left-right) delta `F_s(t)·F_s0⁻¹` applied to target rest.
Hips height absolute: `src_hips_z · k + offset`, k = leg-length ratio. Bones are not connected: reset child `location` to 0 after
assigning `pose_bone.matrix`. Foot lock: low (≤ 2 cm) & slow (< 0.15 m/s) ≥ 2 frames ⇒ median anchor, solved by the leg IK.
Mute all constraints while copying FK, unmute before keying IK targets.

## Known limits
No toe bone (rigid foot pivot); props are rigid children (log in put-down is a keyed world track, timing tied to the A clip);
B clips from Kimodo are not cyclic — loop extraction not implemented.

## Second hand on a tool (A) / props from the source pose (B)
- `bam_can(rig, SK, axe, "L", z)`: forearm IK to the wrist position that puts socket cam_L on the handle at z, then hand rotation =
  rotation taking the rest grip axis onto the handle axis; baked per frame.
- Retarget: `GO_B=kep` = log centred in the triangle shoulder–elbow–wrist (akimbo arm, «inside the arms and hip»), 2.5 cm outward,
  radius ×0.72; `GO_B=vai_B` = 16 cm over the right shoulder; both along the hips' forward axis, front up 5°. Two-hand axe: handle =
  line R fist → L fist, blade toward the hips' forward axis.

## Video mocap (Boss 22/10: «use motion capture… infuse in the rigged model»; hands «no guessing… triangle gap measurement»)
Tools in `~/mocap` (Mac, no CUDA): GVHMR pip fork `gv_venv` (SMPL-X from the `lithiumice/models_hub` mirror that ComfyUI-MotionCapture
auto-downloads) = BODY + world trajectory; SAM 3D Body `sam-3d-body/.venv` (HF gated, access granted; patched `.cuda()` → model device,
no EGL on darwin; ~30–45 s/frame CPU) = best ARMS/HANDS; DWPose/RTMW3D `op_venv` = 2D/3D wholebody check.
```
gv_venv/bin/gvhmr demo vao/<clip>.mp4 -s -o ra_gvhmr ; gv_venv/bin/python scripts/smplx_sang_mp.py ra_gvhmr/<clip>/hmr4d_results.pt <out>.json 30
op_venv/bin/python scripts/chay_dwpose.py vao/<clip>.mp4 ra_dwpose        # bbox source for SAM 3D
cd sam-3d-body && .venv/bin/python ../scripts/chay_sam3d.py ../vao/<clip>.mp4 ../ra_dwpose/dwpose.json ../ra_sam3d <t0> <t1> cpu
TAY_TU=~/mocap/ra_sam3d/sam3d_mp.json CHU_KY=0,<T> blender -b -P animate.py -- mocap --mp <gvhmr json> --tu <t0> --den <t1+0.05> ...
```
- Cycle = measured from data (wrist-above-shoulder peaks), never by eye (eyeballed 0.67–1.73 s was wrong; GVHMR peaks 0.58/1.75/2.92 s).
- `tay_theo_nguon`: wrist POSITION in the torso triangle (shoulders + hip mid) × target torso height, elbow toward the source elbow
  (2-bone solve), hand from index/pinky. Copying arm angles only left wrists 18 % off (arm/torso proportions differ). Reports
  `tay_lech_than_pct` (8.9 % on 4JKeYagLMFk, reach-limited at f17) + per-frame table `TAY_BANG` (hand gap within 2 %).
- `CAM_Z`/`CAM_X` env set the render camera (CAM_Z 10 ≈ front like the source video).
- AXE from mocap (`qua_hai_nam` prop): handle passes through both fists; wrists pulled onto the axis with a 2-bone solve + elbow
  swivel (wrist ≤ 40° deviation; reach-limited arms may pull ≤ 6 cm); fist axis = handle; lower fist at −0.28. Handle DIRECTION is
  measured, never guessed: `~/mocap/scripts/do_riu.py` tracks axe pixels (light, outside the SAM body mask and static tree) → blade
  point → camera ray ∩ sphere(grip, L); trusted only when the axe shows ≥ 72 % of its length (windup blade over hair = 17–43 %);
  gaps ≤ 4 source frames interpolated; elsewhere the SAM knuckle axis (pinky→index; head on the right-hand side). Knuckles alone
  matched the real axe in only 3/8 key frames. Codex round 3 (22/10): grips OK; remaining notes = source style (no impact hold).
- TWIST (Boss 22/10 «cây rìu xoay 360 độ… hai cánh tay xoắn theo»): direction-only retarget leaves bone ROLL free ⇒ flips. Fixes now in
  `qua_hai_nam`: fist-axis sign LOCKED per hand (re-choosing per frame flipped hands 160–180°); blade +X from the right hand, roll limited
  25°/frame; forearm gets 50 % of hand twist; axe depth root by Viterbi over the whole clip with physics (no axe through head, blade near the
  measured 3D tree at the hit — tree base = lowest static-pole pixel ∩ ankle ground plane). SAM2 tracks the axe head in all frames
  (`~/mocap/scripts/bam_riu_sam2.py`, env sam2_venv). SAM 3D wrist ROTATIONS (pred_global_rots, MHR frame = F·coords, F = diag(1,−1,−1))
  disagreed with the measured axe by 75–131° on this cartoon clip ⇒ `TAY_XOAY=nguon` only on request. Palm "out/in" rule held in only
  ~50–60 % of frames (palms rotate with the swing) ⇒ not used as an absolute target.
  Gate ⑯ (animate.py, mocap axe): axe roll step ≤ 30°/frame, hand/forearm twist step ≤ 60°/frame; reverse-tested (limit off ⇒ rc=1, 102°).
  Gate ⑮ now also on mocap axe (delivered range only). Result 4JKeYagLMFk v3: Codex PASS, Telegram 5260–5263.

## SAM 3D Body FULL-ROTATION transfer (Boss 22/10 «Redo from original whole thing from SAM 3D… rig matching incl. hand… dont twist arm and adjusting»)
`animate.py -- sam --mp ~/mocap/ra_sam3d_xoay --tu <t0> --den <t1> ...` → `H.retarget_sam`. Needs in the dir: m_*.npz (R = pred_global_rots,
J = pred_joint_coords), khop_mhr.json (127 MHR joint names/parents), mhr_bind_G/P.npy (bind = FK of joint_prerotations xyzw + offsets),
trong_luc.json (gravity in camera frame from GVHMR global_orient·incam⁻¹ — source camera pitched 15°; without it the settler hunches).
- Map `SAM_MAP`: hips←root, spine←c_spine1, chest←c_spine3, neck/head, clavicle/uparm/lowarm/wrist, upleg/lowleg/transversetarsal.
- Conventions verified on data: MHR rotation frame = F·J with F = diag(1,−1,−1) (0.0°), child−parent = R_parent·offset (≤ 0.07°).
- Per bone once: M_match = swing(rest dir → bind segment dir)·Rest; per frame M = Y·(CQ·R(t)·Cᵀ)·(C·G_bind·Cᵀ)ᵀ·M_match. Forearm takes 50 % of the
  lowarm→wrist_twist twist RELATIVE TO BIND (global slerp added the bind offset: forearm +40–62°).
- Proportions: copying angles separates the hands (settler shoulders 38–41 cm vs 25–30 scaled source) ⇒ wrist target = shoulder-mid + source
  vector × arm-length ratio, 2-bone with elbow plane from SAM, bones swung minimally (twist kept). Wrist gap then matches source exactly.
- Axe (`qua_hai_nam`, sam branch): handle through both sockets (no hand edits); blade from right hand, roll ≤ 25°/frame; gates ⑮ ⑯ apply.
  Pulling fists onto the video-measured axe (up to 150 mm) re-introduced twist/flip (upperarm 163°) ⇒ off by default (`KEO_LEN_CAN`).
- Result v5 (Telegram 5273–5276): all gates pass, Codex: no candy-wrap; open = left shoulder pinch f8–12 (skinning), axe dir f4/f12 vs video.

## GVHMR rig → settler (Boss 22/10: «Làm lại bằng phiên bản GVHMR: get the rig… same rig… apply… adjust only hands and axe»)
`gv_venv/bin/python ~/mocap/scripts/gvhmr_sang_rig.py hmr4d_results.pt ~/mocap/ra_gvhmr_rig` exports SMPL-X (55 + 7 alias joints, global
rotations by FK of body_pose/global_orient, rest = identity frames) in the SAME folder format as SAM (joint names aliased to MHR names), so
`animate.py -- sam --mp ~/mocap/ra_gvhmr_rig` + `SAM_TAY_TL=0` (no arm edits) applies it. Convention check child−parent = G_parent·rest offset: ≤ 0.02°.
Video axe axis brought into GVHMR world with global_orient·incam⁻¹ (ra_gvhmr_rig/sam3d_mp.json). With arms frozen, fists sit 76–99 mm off the
video axe ⇒ hand roll alone cannot reach it (wrist 107°); default = handle through both fists, hands rotate to grip (fist–handle 6.5°).
Result v6 (Telegram 5277–5279): no visible twist (Codex), hands on handle; open: hit handle 52° vs reference 27°, wrist 50.7° (gate 50).

## MEASURED AXE drives the grip (Boss 22/10: «Allow minimal arm IK (wrist position only, keep elbow direction and twist from GVHMR), measured axe drives it»; Codex 3 rounds in anim_settler/hoi/)
1. `sam2_venv/bin/python ~/mocap/scripts/bam_riu2.py` — SAM2 grows both prompts to the WHOLE axe ⇒ split head/handle geometrically in the fit.
2. `~/pose-venv/bin/python ~/mocap/scripts/fit_riu.py <video> <ra_sam3d_xoay>` — sequence least-squares (head centre + handle dir per frame,
   global length bounded 0.4–0.9): reprojection head/butt/handle line, weak wrist prior, smoothness, and the DEPTH ANCHOR = tree contact at
   impact (tree base = lowest static-pole pixel ray ∩ ground plane ⟂ GVHMR gravity through the ankles). Without the tree anchor the depth branch
   was wrong (blade 0.3 m BEHIND the body ⇒ "axe too low"); with it: impact blade ≈ 0.9–1.0 × hip, handle 21–24°, reprojection 3–6 px median.
3. `RIU3D=riu3d.json SAM_KP=sam3d_mp.json animate.py -- sam --mp ~/mocap/ra_gvhmr_rig` — source frames are DUPLICATED (cartoon on twos) ⇒ dedupe
   + interpolate; grips = source wrists projected on the axe line, mapped through the torso triangle (× arm-length ratio); wrists pulled by
   `keo_tay_giu_xoan` (same-frame GVHMR elbow plane, swing-only, twist kept), hand = fist axis on handle (straight wrist, sign locked),
   capsule clearance pushes the axe out of thighs/torso. Fixed bugs: restoring the hand matrix WITH its old translation detached the hand.
4. Our `riu_dai` is ~2× the source axe relative to the body ⇒ same angle puts the blade lower; `RIU_TL=0.55` matches the source (impact
   blade/hip 0.83–0.91). Open: wrist bend up to 109° at the downswing start (f3–f5).
Delivery: `bash anim_settler/send_build.sh <clip.mp4> <soi_dir> "<label>"` (3 videos).
- Grip lock (Boss 22/10 «left hand not attach… twisting or hold and unhold» + «blade… always pointing toward the front»): right grip from the
  measured wrist, LEFT grip FIXED at −0.28 on the handle (following the source wrist slid it −0.07…−0.54, off the −0.32 butt); hands rotate
  RIGIDLY with the axe (one grip transform per hand, roll about the handle chosen to minimise the clip's p95 wrist bend); blade +X = hips
  forward projected ⟂ handle (continuity near-parallel). Result v8 (Telegram 5290–5293): grip 0 mm along/around the handle except reach-
  limited frames; open: left wrist bend p95 ~94°, max 130° (GVHMR forearm nearly along the handle) — only elbow swivel would fix it.
- ⭐ LESSON (Boss 22/10 «chỉ cần nắm cố định là xong, mà nãy giờ sửa tới sửa lui là do bạn ko set tay nắm cố định axe»): for ANY two-hand prop,
  lock each hand to the prop FIRST (constant hand→prop transform + fixed slot on the handle), then drive the prop; never re-solve hand roll /
  grip slot per frame. Gate ⑱ `18_nam_truot_doc_can_mm` ≤ 15 (socket travel along the handle over the delivered range).
- Blade side (Boss 22/10 «Lưỡi axe đang quay ngược về sau»): `riu_dai` mesh +X = thin EDGE (0.006 thick), −X = poll (0.044). v8 flipped XR by the
  hit-motion sign `dx` ⇒ blade backward AND axe 180° off the gripping hands. With RIU3D, dx = 1. Gate ⑰ `17_luoi_truoc_cos_min` ≥ 0.2
  (blade·hips-forward, reverse-tested: correct 0.45 / flipped −1.0).
- Elbow swivel (Boss 22/10 «Xoay khuỷu tay thử»): `XOAY_KHUYU=90` (default) rotates upper+fore arm about shoulder→wrist (wrist fixed) chosen
  by Viterbi over the clip (bend + 0.5·pole jump + 0.1·|φ|; greedy per-frame flipped the elbow 147°/frame); grip roll θ searched jointly.
  v9 (Telegram 5294–5297): twist step 49.6°, left wrist still 111–113° at frames 9–11 (after impact) — even free ±180° swivel only reaches 93°,
  so the rest needs a grip slot/roll change, not more elbow.
- Stylized axe (Boss 22/10 «medium bigger axe, make it stylized a lil bit»): `long_axe_v2` built in lpms (`~/projects/GameDev/lpms/assets/long_axe_v2.py`,
  rev r_a504ddab, 586 tris, 0.84 m, bearded crescent + bright edge strip, brass rivets/wedge, leather wraps at both grips, butt knob), modelled at REAL
  size ⇒ run chop with `RIU_TL=1 NAM_TRAI=-0.21` (clip `chop_gvhmr` asset long_axe_v2, dau [0.19,0,0.45]). v10 Telegram 5298–5302.
- Horizontal blade (Boss 22/10 «the blade is pointing upward, supose to be horizontol»): forward-projected-⟂-handle tilts up whenever the
  handle tilts (measured vertical 0.5–0.86 in the windup). Now blade = the unique horizontal ⟂ handle (handle × Z), sign by CONTINUITY
  (transported previous blade) with a 30°/frame roll clamp, then one global sign = most forward over the clip (`LUOI_NGANG=1` default).
  Under RIU3D the axe follows XR exactly (no separate 25° clamp ⇒ it drifted from the gripping hands). Gate ⑲ `19_luoi_doc_max` ≤ 0.25
  (frames with |handle z| ≤ 0.65; reverse-tested: horizontal 0.22 / old 0.86). ⑰ now only inside the swing window `cua_so_chem`.
- Retime / strong swing (Boss 22/10 «make the swing fast at the swing frame»): clip field `doi_nhip` [[src,dst],…] (or env DOI_NHIP="a:b;…")
  remaps EVERY keyframe (rig + axe, Blender 5 channelbag API), loop ends fixed, events/cua_so_chem moved. chop_gvhmr: 0:0 2:3 8:6 12:11 28:28
  (hold top, swing ×2, hit 8→6). After retime the axe is re-keyed per integer frame RIGIDLY from hand_R @ CN⁻¹ (fractional-key interpolation
  had drifted grip 21.5°). ⑯ divides each step by local speed-up so intentional speed is not called jitter. v11 Telegram 5304–5307.
- TORSO CALIBRATION (Boss 22/10 «lúc chặt cây cái lưng của settler bị cong dữ vậy»): retarget_sam aligned each settler torso bone to its
  own source segment at bind; SMPL-X spine2→spine3 is only 5.2 cm and tilted 30° at rest ⇒ lower back locked +30° forward, chest
  −36…−41° back (S-hunch; source chest-vs-spine 2–13°). Now hips/spine/chest are calibrated to the WHOLE trunk axis root→neck
  (`THAN_THEO_TRUC=1` default) since the settler spine rests straight. Gate ⑳ `20_lung_gap_khuc_deg` ≤ 20 (spine→chest rotation minus rest;
  reverse-tested 12.2 fixed / 41.0 old). Rule: never calibrate a long target bone to a short source segment (< ~1/3 its length) — use the
  chain axis. After retime the LEFT hand is also re-keyed rigidly to the axe (interpolation had opened a 23.5° grip gap).
- Joint range limits in Blender exist (bone constraint LIMIT_ROTATION; IK panel lock/limit/stiffness) but our scripts write pose
  matrices directly, so the binding check is the gate set (⓪ anatomical axes, ⑭ wrist, ⑳ back kink), not constraints.

## CONTACT CONTRACT — hand ↔ object (Boss 22/10/2026: «khi tương tác với vật thể - phải cố định tay ở trên bề mặt vật thể, xem hình coi có bị xuyên qua ko - luôn luôn setup vật thể đã xong là boundary layer unthroughable»)
Applies to every frame where a hand touches a prop, tool or load (axe, logs, basket, door, another character).
1. **Shell first.** Before animating, give the object a contact shell = its collision surface offset outward by the hand's
   half-thickness (settler fist: 20 mm). The shell is the only place a palm may sit; the object's interior is out of bounds.
2. **Lock, then drive.** Pick the contact point(s) on the shell once at a reference frame (reject points that fall inside another
   part), store palm position AND hand orientation in the OBJECT's local frame, and keep them fixed for the whole interaction. Each frame,
   move the object, then solve wrist IK (elbow plane kept, twist kept) to the locked point. Never key a contacting hand independently.
3. **Prove it numerically.** On every frame: palm-to-shell distance −3 mm … +40 mm (no penetration, no floating), object never inside
   the body or head (clearance ≥ 0), carried loads balanced over their support (COM offset along the load axis ≤ 60 mm).
   Gates live in the build script and exit 1. A gate that did not run is "not run", never "passed".
4. **Prove it visually.** Render close-ups at the worst-margin frames reported by the gates (smallest clearance, largest IK correction)
   and inspect for intersections before delivery.
4b. **Hugging a load — PALM ON THE OUTER FACE** (Boss 23/10 «Tay đang nằm dưới gỗ chứ ko phải lật ngửa bàn tay - T shape với body -
   đặt 3 khúc gỗ lên - tay ôm vô lại - mặt bàn tay phải áp vào gỗ đối diện từ ngoài vào»; overturns 22/10 «farthest from the shoulder»
   which put the hand UNDER the logs palm-up): think T-pose → load placed on the shoulder → arm folds back in. Contact point = the OUTER
   face of the load (surface normal points horizontally away from the body, cos ≥ 0.6, pick the most outward); the PALM (palm label, see
   below) presses inward against it, fingers pointing up along the surface; upper arm out to the side, elbow pole = outward + down.
   Every frame: wrist reachable, whole arm (capsules) outside every piece except the hand on the piece it presses. Gate ⑨ elbow·outward ≥ 0.5.
   **Palm label**: `las-physics/scripts/shatter.py::long_ban_tay()` measures palm centre + palm normal in the hand-bone frame from the mesh
   (fingertips curl toward the palm); verified at rest: palm faces the body cos 0.89. Stored in `body_shell.json["_long_ban_tay"]` by animate.py.
   Never guess the palm axis from a clip pose again.
4c. **Measure with the REAL mesh, never a proxy point** (Boss 23/10 «Tay vẫn chưa nằm trên bề mặt, vẫn bị xuyên qua gỗ… Zoom lại thật
   gần soi 2 angles»): the old gate tested ONE point (hand-bone midpoint) + a guessed 2 cm thickness and reported 0 mm while 325–355
   arm-mesh vertices were inside the logs (−66 mm). Required checks: (a) every arm-mesh vertex (weight ≥ 0.3, both arms) outside every
   piece; (b) BVH face overlap between all character meshes and the load = 0 (calibrated: old bad build 4 661 overlaps, fixed 0);
   (c) TRUE palm gap = hand-mesh vertices → contact surface within −3…+10 mm (no penetration AND no floating).
   Search the placement with the whole arm as capsules (upperarm/forearm/hand radii from the body shell) on every frame, then a
   2nd pass with the hand's MEASURED thickness (bone axis → palm surface 31 mm vs capsule 62 mm — capsule-only left the hand floating 34 mm).
   Visual proof: `las-physics/scripts/check_contact.py` renders (1) from the hand side and (2) ALONG the load axis (end-on shows the
   cross-sections + the hand; a side view can fake a gap when a nearer piece covers the contact).
5. **Re-fit on change.** Any change to the object (size, count, shape, scale) or to the motion invalidates the contacts: redo 1–4.
   Contacts are never inherited from the previous object.
Reference implementations: axe two-hand grip (`animate.py` RIU3D block, gates ⑮⑯⑱), log bundle carry (`anim_settler/chop_tree_scene.py`,
gates ⑥⑦⑧). Blender has no "never intersect" switch for keyframed characters (rigid body only affects simulated objects; Limit Distance /
Floor / Shrinkwrap constraints guard one bone vs one target and fight IK) — the contract above is how we guarantee it.

## TWO-HAND TOOL ON A KIMODO CLIP — pickaxe (Boss 23/10/2026 «C it is, only from beginning until the impact - then loop… loop smoothly…
use skill and all manifest debug knowledge to attach the pickaxe… slow-fast-slow»). Scene `~/projects/GameDev/anim_settler/hoe_scene.py`.
- **Impact frame** = the sudden stop of the wrist midpoint after the first overhead peak (C: drop 74 → 23 mm/frame at src 52).
  **Cycle** = src [raise start 14 → impact 52] + an INTERPOLATED recovery (impact pose → start pose). Never use the generated motion after the impact.
- **Slow-fast-slow** (out frames): raise 0→24 (eased) · hold at the top to 27 · strike 27→35 with src time ∝ u^1.6, accelerating into
  the impact · recovery 35→48 (eased). Frame 48 ≡ 0: loop seam 0 mm.
- **Never build the handle through Kimodo's two hands.** Measured: the hands sit SIDE BY SIDE (left–right, 10–44 cm apart), so the
  "handle" came out horizontal across the body (wrist 150°, handle through the torso).
  - The handle lies in the swing plane (sagittal) at angle θ(t): rest → lags behind while raising → ~215° at the top (behind the head) → wrist snap.
  - θ at impact is SOLVED so the pick tip reaches the rock top.
  - The pick point is ⟂ the handle, pointing down at impact.
  - Grips are fixed on the handle (upper +0.03 / lower −0.11) at the Kimodo hand midpoint.
- **Reach.**
  1. Clamp the grip centre into both shoulders' reach.
  2. Solve the hands.
  3. Re-measure the REAL socket error and shift the whole tool by the short hand's error (95 mm → 2.7 mm in 1 pass).
- **Body clearance.** Lift θ in 2° steps until the tool BVH (excluding hand/forearm faces) misses the body; smooth the lift over ±4 frames,
  circularly, otherwise the loop seam jumps 116 mm.
- **Feet.** Plant both feet from frame 0 (leg 2-bone IK, knee plane kept, foot rotation frozen); raise to shoe bottom = 0. Kimodo raw: slip 30 mm, sink 35 mm → 0.
- **Gates (exit 1).**
  - Grip ≤ 8 mm.
  - Wrist ≤ 70° (physiological ROM; C bottoms at 68.6° in the strike for every rest angle tried).
  - Tool-in-body BVH 0, body-in-rock 0.
  - Tip embed 0–30 mm at impact.
  - Back kink ≤ 20°.
  - Hand rotation step ≤ 60°/frame, measured as min(a, 360 − a) since q ≡ −q (the naive measure read 357°).
  - Loop seam ≤ 2 mm.

## WRIST = ANATOMY PER AXIS, NOT A TOTAL ANGLE (Boss 23/10/2026: «Ko được để cổ tay gập như vầy, như vầy là sai với anatomy»)
The old gate ⑭ measured only the TOTAL forearm↔hand angle (≤ 50/70°), so a wrist bent SIDEWAYS 46° and twisted 97° passed (pickaxe v1).
- **Measure.** `humanoid_anim.co_tay_giai_phau(rig, b, palm_normal)` splits the hand motion relative to the forearm, from the REST pose
  (neutral wrist), into flex/ext (about the palm's lateral axis), deviation (about the palm normal, from the palm label `vo.long_ban_tay`)
  and twist (about the forearm). Calibrated: rest = 0/0/0; walk ≤ 12/20/1.
- **Limits** `CO_TAY_ROM`: flexion 80 · extension 70 · deviation 25 (radial 20 / ulnar 30; no thumb label yet ⇒ 25 both sides) ·
  twist AT the wrist 15.
- **Rule: twist belongs to the FOREARM** (pronation/supination). Rotate the forearm about its own axis by the wrist's signed twist, cap
  the forearm at ±85°, and leave the remainder at the wrist (≤ 15).
- **Gates.** `animate.py` ⑭b `14b_co_tay_vuot_bien_deg` must be 0 for every clip. `hoe_scene.py` adds forearm twist ≤ 90°.
  - Reverse tests: pickaxe v1 81.8 ⇒ caught; the GVHMR chop clip shows 180° twist at the left wrist ⇒ caught (still to fix).
- **Fixing a two-hand tool.**
  1. Choose a tool-angle offset δ (±45°, Viterbi smooth, impact frames locked so the tip still hits) and an elbow swivel φ (±60°).
  2. Re-choose the fixed grip roll by anatomical cost.
  3. Run measured local refinement (smooth δ/φ bumps over ±4 frames, keep only collision-free).
  4. Pull the tool into wrist reach using the exact wrist position (hand orientation + socket offset), per frame shoulders.
  Pickaxe v2: wrist excess 0, forearm twist 85, grip 0 mm, no body/rock penetration.

## ARMPIT + POWER-PHASE WRIST (Boss 23/10/2026: «Nách bị lỏm gắt» · «Lỗi da hay là phải thêm vải cho áo? Sửa cái nào scalable?» · «Cổ tay khi
chuẩn bị impact mạnh… thẳng với cánh tay… phải thẳng hoặc cong vô nhẹ so với cánh tay»)
- **Armpit is a SKIN problem**, not cloth: measured on BODY faces; the outfit copies body weights.
  - Gauge `scripts/measure_armpit.py`: area ratio of armpit faces (upperarm + torso weights) versus rest, on a FIXED face set taken from the original weights.
    Walk: p10 0.82. Arms overhead pickaxe v2: p10 0.17–0.38, worst face 1.5 %.
- **Scalable fix, exportable to glTF:**
  - Helper bone `nach_<b>` (child of the clavicle, at the shoulder) with blended skin weights (`them_xuong_nach`), turned per frame halfway
    between clavicle-rigid and upperarm-rigid (`nuong_xuong_nach`).
  - Plus scapular rhythm: clavicle lifts (elevation − 60°)/4, cap 20°. 1/3 with cap 35° looks shrugged; with no clavicle lift the shoulder edge is the harshest.
  - Result: p10 0.37/0.37, worst face 0.14/0.19.
  - Rejected: DQS (Preserve Volume, 0.45/0.48 but lost in glTF export); Laplacian weight smoothing (worse); extra cloth (only hides it).
  - Thresholds BY POSE: arms low (elevation < 90°) p10 ≥ 0.60, worst ≥ 0.15 (walk 0.82). Arms OVERHEAD p10 ≥ 0.35, worst ≥ 0.12, anchored to
    pickaxe v3 which Boss APPROVED 23/10 («Tốt hơn rồi. Chốt»: 0.37 / 0.14). Do not lower further to pass.
- **Wrist deviation is now SIGNED.** Thumb side comes from the standard rest pose: palms face the thighs (cos 0.89), so thumbs point forward (−Y).
  Known-answer test: tilt toward thumb −14°, toward pinky +14°.
  - General ROM: radial 20, ulnar 30.
  - **Power phase** (top of swing → impact) `CO_TAY_BO`: extension ≤ 10 · flexion ≤ 25 · ulnar ≤ 25 · radial ≤ 10.
  - Forearm pronation/supination cap 88°, then wrist twist ≤ 15°.
- **Solver order that reached 0 excess (pickaxe v3):**
  1. Analytic δ/φ Viterbi.
  2. MEASURED grip-roll search per hand: −40…40 step 10, then fine ±8 step 2. The analytic estimate was off by ~15° in the strike.
  3. Wide local bumps (±4 frames).
  4. Narrow bumps (±2 frames, 1–15°).
  5. Re-search the rest handle angle with the new gate (+10 → 0).

## FEET MUST NOT TOE IN (Boss 23/10/2026: «lúc đi bộ, bàn chân phải nó cứ xoay vô, kiểu khó chịu lắm»)
Kimodo walk measured: right foot up to 74.7° toe-in during swing, 9.2° average. Fix = `humanoid_anim.sua_chan_xoay(rig, f0, f1)`: rotates the whole leg about the hip→ankle axis (hip internal/external rotation), so the ankle does not move (measured 0.0 mm) and the knee follows. Target toe-out 6°. Returns the gate {L/R: (toe-in max, toe-out max)}: toe-in ≤ 2°, toe-out ≤ 18°. After the fix: toe-in 0°, toe-out 6.5–11.2°. Called in `basket_storage_scene.py`; call it in every walk-based scene ON THE BAKED/IMPORTED clip. ⛔ Not inside animate.py: the rig still has leg IK there, so swivelling the thigh makes IK re-solve (tested 23/10: ankle 119→159°, foot twist 10→53°). animate.py only REPORTS `21_chan_vao_ra_deg_chua_sua`. Note: the Kimodo walk clip already fails gate ⑧ (sai quãng 71%) — pre-existing.

## Two-bone arm IK to a held point (hands on straps/handles) — debug 23/10/2026
- Target the HAND CENTRE (hand bone 55% + 12 mm toward the palm), not the palm label `vo.long_ban_tay.tam`: that label sits ~73 mm off the bone axis, so solving for it oscillated (fixed-point iteration 50–250 mm off) or diverged (Newton 705 mm).
- Closed form that always works: elbow = intersection of sphere(shoulder, upperarm length) and sphere(target, forearm + hand-centre distance); pick the point on that circle nearest the pole (elbow down/out). Forearm Y = elbow→target, roll chosen so the palm faces the intended way; hand = forearm × rest relation (neutral wrist ⇒ gate ⑭b = 0).
- Facing the palm flat onto the chest right under the shoulder is unreachable without the forearm entering the chest — grip like a fist around the strap (palm medial + back).
- Pole that looks natural for strap grip: (side·0.3, +0.12 back, −1 down).

## Feedback 23/10/2026 on the basket clip v2 — «Sao animation này chân bị rung / Đùi sau có vệt trắng là gì? / Vai bị gãy»
- JITTER came from my own toe-in fix v1 (per-frame angle with trial sign flips): thigh angular acceleration 44°/frame² vs 11 in the source. Rewritten `sua_chan_xoay`: measure on the ORIGINAL pose (slope by ±2° probe), only correct frames outside [3°, 14°] toe-out, interpolate, Gaussian ±2 frames, clamp ±45°, keep quaternions continuous, apply once. Gate: thigh accel ≤ source + 3 (`CHAN_RUNG_THEM`), toe-in ≤ 8°, toe-out ≤ 22°. Measure jitter with min(a, 360−a) — q and −q read as 356°.
- WHITE STREAK = body skin poking through the pants at the buttock/thigh crease when the leg extends back (present in the source clip). Fix = game-standard body masking: `humanoid_anim.an_da_duoi_do(body)` deletes body faces fully owned by thigh/shin/foot when pants + shoes cover them (716 faces).
- BROKEN SHOULDER = IK with the grip fixed high on the chest: the "elbow down" pole got cancelled by projection and the elbow flew back at shoulder height (upper-arm elevation 68°). Fix: put the upper arm in a HANGING pose first (down, 12° out, 17° forward), then slide the grip up/down the strap until forearm + hand reach fits. Gate: upper-arm elevation from the spine-down axis ≤ 45° (now 41°).

## Procedural picking / reaching low objects (berry harvest, 23/10/2026)
- Kimodo text-to-motion gave no usable picking (4 seeds: standing, waving hands at the waist; wrist excess 4–32°) ⇒ build reach cycles by IK on top of a standing base clip.
- Reaching anything below the hip needs HIP DROP (bend knees, leg IK with ankles fixed, knee pole forward) + HIP HINGE (hips 55% / spine 20% / chest 25%), not just spine bend (spine-only pivot ~1.0 m moves the shoulder ~10 cm).
- Turn the torso toward targets on the OPPOSITE side of the reaching hand; for same-side targets turning moves that shoulder AWAY — turn little.
- Keying on top of an NLA base: snapshot the base pose per frame first and reset to it every frame, otherwise lean/head offsets ACCUMULATE frame to frame (bent ~70° instead of 28°).
- glTF-imported props carry baked keys: `animation_data_clear()` before reparenting, else they snap back every frame. After reparenting call `view_layer.update()` before reading children world positions. Compute "top/mouth" points in WORLD space when the object was rotated upright.
- Scene: `~/projects/GameDev/anim_settler/harvest_berry_scene.py` (basket hooked on the left forearm, right hand picks, cluster hides on grasp, berries appear in the basket on drop). Gates: grasp ≤ 40 mm, drop ≤ 40 mm, wrist ⑭b, foot slip ≤ 10 mm, body (not hand/forearm) vs foliage = 0.

## Quadrupeds (deer, rabbit) — NOT Kimodo (human-only skeletons) — 23/10/2026
Recipe + gates: `~/projects/GameDev/assets/organic/deer_v1_rig/NOTES.md` (build_rig.py: rig from plan masses, walk/run with hoof locking by 2-bone IK, graze, death with floor clamp). Rabbit: `assets/organic/rabbit_v1_rig/NOTES.md`.


## TEXT → MOTION: HY-Motion 1.0 on the Mac (Boss 23/10/2026: «tải CLIP ViT-L/14 và chạy thử HY-Motion bắn cung (hunting) + phóng lao (hunting)»)
Tencent HY-Motion 1.0 Lite (DiT, SMPL-H output, licence tencent-hunyuan-community: free < 1 M MAU, NOT valid in EU/UK/South Korea).
Install: `~/projects/GameDev/hymotion/` — code `code/HY-Motion-1.0` (git), venv py3.11 (`req_mac.txt`: no bitsandbytes/fbxsdkpy, + torchdiffeq,
gguf, accelerate latest, transformers 5.x), ckpts: `tencent/HY-Motion-1.0-Lite` (1.7 GB), `GGUF/Qwen3-8B-Q4_K_M.gguf` (4.7 GB), `clip-vit-large-patch14` (1.6 GB).
Run: `venv/bin/python run_hy.py <ABS out_dir> "<prompt>" <sec> <seeds>` — own runner (T2MRuntime picks CUDA else CPU): pipeline → MPS,
Qwen via `gguf_file=` (dequantised bf16 ≈16 GB RAM), `get_module_device` patched (returned CPU for MPS modules ⇒ device mismatch),
no prompt rewriter. Load 141 s, generate 4 s clip in 9 s. Output npz (Rh, poses 52×3, trans, betas16) y-up.
→ `~/mocap/gv_venv/bin/python ~/mocap/scripts/hy_sang_rig.py <npz> <rig_dir>` (SMPL-H 22 body + 30 hand joints = SMPL-X order) →
`animate.py -- sam --mp <rig_dir>` (same as GVHMR). Open: wrists exceed anatomy (74° on first sample) — hand/finger data not yet clamped.

## LTX VIDEO → SETTLER + PROPS (Boss 23/10: «gắn 2 animation LTX vào settler, gắn cung và cây lao»)
LTX i2v clip (ref_motion/ltx_2026-10-23/*_s2.mp4) → `gvhmr demo <mp4> -s` → `gvhmr_sang_rig.py` → `animate.py -- sam` (KHONG_DAO_CU=1)
→ `GameDev/anim_settler/attach_prop_ltx.py --glb <settler glb> --mon cung|lao`: prop POSITION = socket cam_* per frame, prop DIRECTION
steered by the target (GVHMR has no fingers ⇒ wrist rotation unreliable for a bow/spear axis); release frame MEASURED (bow: fastest
hand separation after full draw; spear: peak right-hand speed, 10 m/s on LTX seed 2), then ballistic flight. Spear tool = `tools.py lao`
(1.7 m shaft, grip at balance point, knapped leaf head, 128 tris, gates pass).
⛔ GVHMR needs SMPL-X/SMPL body models: symlink from ~/.cache/huggingface lithiumice/models_hub 4_SMPLhub into
gv_venv/.../inputs/checkpoints/body_models/{smplx,smpl} (registration-gated otherwise).

## 23/10 fixes in the sam/GVHMR/HY path
- Eyes: body materials Body_Ivory + Socket_Shade are KEPT (old code overwrote Socket_Shade ⇒ no eyes); gate ㉒ in animate.py.
- Feet (`retarget_sam`): contact-run pinning + source foot direction + flat mid-contact (see memory feedback_animate_mat_chan). Spear: steps and stance change now transfer.
- HY prompts: follow the official guide — English < 60 words, ONLY limb/torso actions, NO objects/scene/camera (no "bow", "spear", "deer", "grass"). Defaults: CFG 5.0, 50 Euler steps, 30 fps, max 12 s.
- Text2MotionPrompter official = Qwen3-30B-A3B MoE 56.9 GB (does not fit) ⇒ community Q4_K_M GGUF 17.3 GB via Ollama, run sequentially with HY (RAM).
- Standing feet = REST slope (not 0°) — gate ㉓ (≤ 6°). HY bow: trim the long aim hold with `hy_cat_khung.py <in> <out> <from> <to>` (source 30 fps) so the release lands ~2 s.

### HY model choice (Boss 23/10/2026: «Bỏ prompter ra đi, animation thì mượt và thật hơn»)
Use the FULL HY-Motion-1.0 (1.0B, now the default in run_hy.py) with a hand-written hunting-style prompt («A hunter sneaks… draws a bow… aims at a deer…»). Do NOT run Text2MotionPrompter in the loop. Raw preview of travelling clips: `BAM=1 blender -b -P hy_ve_goc.py -- ve …` (follow camera).

## CHAINING CLIPS (idle → walk → action → idle) — `~/mocap/scripts/noi_rig.py` (Boss 23/10/2026: «nối cho nó vào pose cầm lao hơi khom người»)
Join at the RIG-FOLDER level (before `animate.py -- sam`), never by stitching rendered clips: `gv_venv/bin/python noi_rig.py <out> <dir:t0:t1[:speed]> … [--tron 12]`.
Per segment: gravity normalised (trong_luc.json, same formula as retarget_sam), lowest foot = 0, yaw-rotated so hip facing matches the previous segment's end, root translated to continue, then N-frame smoothstep crossfade (slerp global rotations, lerp joints). Writes noi.json with segment start times (to place the arrow/spear release). Arrow hidden before nocking: `TEN_TU=<frame> blender -b -P attach_prop_ltx.py …`.
Universal crouch source = HY full, no weapon words in the prompt (see memory project_settler_hunting).
- Bow hand is NOT fixed (Boss 23/10: «holding bow in the wrong hand»): attach_prop_ltx.py picks the hand FARTHER from the head at the draw hold as the bow hand (TAY_CUNG to force). Carry = limb axis along forearm pointing down, belly forward; aim pose only between nock and release. Mirror a source segment in noi_rig.py with field 5 «g». End a combo on its own first frame (`<dir>:0:0.1:0.06` = held pose) so it loops.
- Gates added 23/10 (Boss feedback on hunting combos): noi_rig.py «chân lên trời» OPT-IN `--sua-chan` (ankle ≥10 cm below knee, patches leg joints; Boss reverted it on the spear combo 23/10) · attach_prop_ltx.py bow carry wrist (straight ≤5°, back of hand forward ≥0.8) · spear head clearance ≥14 cm · release time TEN_GIAY. Bow string: bow.glb's built-in straight string is deleted (drawn string only).
- MATCH THE ORIGINAL VIDEO (Boss 23/10 «match độ vertical … và độ tiến tới»): track the source video with `lego-movie-studio/scripts/ref/pose_track.py`, correct the GVHMR rig folder with `~/mocap/scripts/khop_video.py` (hip height + travel per frame), gate with `anim_settler/compare_trajectory.py`. Never fix floating feet by moving the hips per frame (it makes the body bob); GVHMR feet are noisy ±10 cm, its root is not. Use NEN_PCT=25 in retarget.

## PREVENTION RULES — audited 23/10/2026 (Boss: «manifest … tại sao nó lại phải adjust … cách nào để prevent next time»; ChatGPT critical audit)
Full record: `~/projects/GameDev/anim_settler/MANIFEST_ADJUSTMENTS_2026-10-23.md` (every Boss correction: intention, measured cause, fix,
barrier) + audit synthesis at its end; private mirror repo `HUNGPHAM789/settler-anim-audit`.
1. Contracts at every boundary (axes, units, fps, handedness, event semantics, provenance) — enforce known conventions (HY = y-up).
2. Validate against an independent reference (original video / approved clip), not the estimator's own output.
3. Fix at the right stage: reconstruction → retarget → contact solve → props → render. Never move the hips per frame to fix feet.
4. Events by onset with a declared spec (release = hand starts to open; `TEN_GIAY` is mandatory for the bow).
5. Temporal consistency; seams need longer blends for stance changes (field 6 in noi_rig).
6. Gates fail closed and are coverage-aware ("no contact" = FAIL, gate ① `1_phu_cham_pct`); `set -o pipefail` around gates.
7. Never tune a threshold on the failing clip alone; record old/new + why next to the number.
8. Pose/orientation feedback: render ONE still of the interpretation first; change only the DOF Boss names.
Pipeline defaults now: video → `~/mocap/scripts/video_sang_rig.sh` (GVHMR + MediaPipe + khop_video); `retarget_sam` REFUSES GVHMR rigs
without `khop_video.json` (override `BO_KHOP_VIDEO=1`); ground = 25th percentile (`NEN_PCT`); noi_rig flag `d` removed.
DONE 23–24/10 (P0/P1, plan `~/projects/GameDev/SETTLER_PLAN_2026-10-23.md`): gates run BEFORE export (failed clip ⇒ no GLB/mp4, `attach_prop_ltx.py`
refuses dat:false); contact solver = source-glitch repair → hysteresis stance + entry-frame anchor → windowed pelvis (cap `hong.ha_toi_da_m`)
→ ankle/wrist ROM post-pass → entry/exit relaxation; thresholds in `assets/motion_profile.json` (versioned, reverse flags `THU_*`).
9. A gate must never share its state with the solver it judges (① was blind: solver lifted free feet 2 cm, gate counted ≤ 1 cm) — measure
   from the BAKED pose with its own threshold calibrated on known-good clips: `1c_chan_thap_bay_mm` (low-foot flight), `chan_lo_lung_frames`
   (foot hovering 3–20 cm, slow, other foot planted, hips calm ⇒ Boss «chân khỏi mặt đất một nhịp»), `chan_rung_max_mm/deg` (per-foot 2nd
   difference ⇒ Boss «giựt giựt»), `hong_rung_mm`. Boss judges BY EYE on a source|result video, never on these numbers.
10. Executable failure registry: `~/projects/GameDev/anim_settler/test_spec/regression.sh --nhanh` (29 fixtures, ~30 s) runs BEFORE any
   change to humanoid_anim.py / animate.py / thresholds; `run_fixture_raw.sh <id>` = one fixture, raw rc (ledger evolve proofs). First
   video→rig clip that passes every gate: `pos_sam_ltx_spear_video` (24/10).
11. Final-timeline gate in scene scripts (`film_build.py::cua_timeline`, before render): hips step ≥ −30 mm, ≤ 3× median, |hips−root| ≤ 0.5 m —
   loop seams must blend toward the start pose advanced by one loop of travel (Boss «giựt lùi» at every crouch-walk loop).
LICENCE (game is sold): GVHMR + SMPL-X are non-commercial ⇒ P2 switches video mocap to DWPose → SAM 3D Body (MHR) or Kimodo; see plan §1b.

## EVENT-ANCHORED TIMING (Boss 24/10/2026 «làm các đề xuất bạn nói»; answers «có công thức tuyệt đối hay … ăn may?»)
1. Mark the event ONCE on the SOURCE rig: `~/mocap/gv_venv/bin/python ~/mocap/scripts/release_events.py <rig_dir> [--window a:b] --write`
   → `<rig_dir>/events.json` {release_s, draw_hand, hold_len_s, peak_mps, confidence, confirmed}. Rule: longest wrist-separation hold
   (|ḋ| < 0.10 m/s) → release = first frame ḋ ≥ 25 % of that burst's own peak (relative onset; robustness sweep 24/10: 285/360 within ±1
   frame vs 248/360 for absolute thresholds). Low confidence (no flat hold, e.g. HY seed 000) ⇒ inspect the curve before trusting;
   set confirmed:true only after looking.
2. Place it: `noi_rig.py … --event release@<T>` (absolute s) or `release@+<T>` (after that segment's start) [:<seg>] ⇒ t0 solved
   analytically, T snapped to the 24 fps grid; noi_rig re-detects on the joined data and exits 1 if off by > 1/24 s.
   First use: combo bow t0 = 0.5297 s in ONE pass (manual retries had found 0.56), measured 4.400 vs 4.417 s (17 ms).
   Limit: the gate uses the same detector as the labelling ⇒ catches bad metadata/solver errors, not a wrong rule — that is what
   `confirmed` (eye check) is for. HY-Motion fingers are static (curl 53° constant) ⇒ no finger-based ground truth.

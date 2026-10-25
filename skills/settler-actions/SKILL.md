---
name: settler-actions
description: CHILD of humanoid-rig-animation — the 6 settler action clips (idle, walk, run, chop tree, carry log on shoulder, put log down) for the approved LPD settler (male/female, 3 hair colours), as clip JSON generated from spec tables, plus the rig profile. Use to (re)build or extend settler animations; load the parent skill and run its animate.py.
version: 0.1 (22/10/2026)
---

# settler-actions (child)

Source of truth: `scripts/make_clips.py` → `assets/clips/*.json` (never hand-edit the JSON). Rig profile: `assets/rig-profile.json`
(LPD `out_<gioi>_cam` = grip hands + sockets + joint landmarks `khop` in geometry.json; tools `assets/tools/settler_v1`).

```
python3 scripts/make_clips.py
S=~/.hermes/skills/creative; blender -b -P $S/humanoid-rig-animation/scripts/animate.py -- build \
  --profile $S/settler-actions/assets/rig-profile.json --gioi nam --toc dark_brown --clip $S/settler-actions/assets/clips/walk.json --out <dir>
```

| clip | frames | root | notes (spec + web research corrections 22/10) |
|---|---|---|---|
| idle | 72 loop | 0 | weight shift ±8 mm, breathing 3 mm, axe R + berry basket L |
| walk | 26 loop | 1.2 m/s·s | 26 not 24 frames (≈111 steps/min), toe-off 62 %, pelvis roll ±3.5°, elbow lags shoulder |
| run | 18 loop | 2.5 m/s·s | jog: 7 contact + 2 flight frames, apex ~9 mm, trunk 9°, elbows 85–100° |
| chop | 48 loop | 0 | long windup 0–18, strike 18–24 (3:1), pelvis leads chest 2 frames, trunk twist −36°, axe ≥0.25 m over head; trunk placed where the blade is at `hit` |
| carry | 32 loop | 0.75 m/s·s | log 1.2 m on RIGHT clavicle (not chest: raised shoulder pierced it), front end raised 5° (X 85°, 95° tips it into the chest), yawed out 8°, +18 cm over shoulder |
| chop2 | 48 loop | 0 | Boss 22/10 «two hands chop from side swing in»: long axe `riu_dai` (handle 1.05 m), R hand FK leads, L hand grips handle at z −0.24 via `bam_can` IK; windup behind right shoulder, horizontal strike at frame 26: blade 0.94 m high, handle 2° from horizontal (gate «hit_cao_m»). Wrist must EXTEND (negative) when the arm is raised — flexion tilts the handle up |
| put_down | 64 | 0 | semi-squat (pelvis −300 mm, trunk 40°), log lifted forward BEFORE turning crosswise (turning near the chest pierced it), lands 0.62 m in front |

Clip fields used by the parent: `joints` (anatomical channels per frame), `pelvis`, `gait.contacts` (on/off/heel_rise per foot),
`gait.swing_h_m`, `toe_off_deg`, `width_extra_m`, `offset`, `hips_drop_mm` (keep small: near-straight legs bend a lot per mm),
`props` (asset/ben/huong or khuc_go che_do vac|dat), `tiep_xuc` (contact bones excluded from gate ⑤), `events`.

A/B 22/10 (same rig, same gates): A (this skill) 6/6 gates pass; B (Kimodo-SOMA-RP-v1.2 → retarget) 0/6 — see
`~/projects/GameDev/anim_settler/AB.md`.

## Boss verdict 22/10 (A/B round 1)
«idle, walk, and run B win. chop neither win, need two hands chop from side swing in. carry B win, you just place the wood plank wrong,
place it inside the arms and hip of version B. or regen with prompt that say carrying wood on shoulder, and walk normal, not tired.»
⇒ idle/walk/run: use Kimodo (B) body motion. Props for B are placed from B's OWN pose (env `GO_B=kep|vai_B` in retarget; two-hand axe
follows the line through both fists) — never reuse A's prop attachment for B.

## SPEC — chop2: two-handed horizontal side swing (Boss 22/10: «skill này bạn thắng»)
Feedback chain: «chop neither win, need two hands chop from side swing in» → «tay cho cầm đúng vào rìu (2 tay)… rìu nằm ngược chiều lúc vung
ra sau – đo vòng cung của mũi rìu có đi đúng hình cánh quạt ko?»
1. AXE IS MASTER (`props[].quy_dao`): the axe-head moves on a TILTED PLANE fan around the chest pivot `tam` [0,−0.05,1.20]:
   θ (0 = forward −Y, + = left) keys 0:−20 · 8:−70 · 16:−140 · 19:−155 (top of windup, behind right shoulder) · 21:−115 · 24:−5 ·
   26:+35 (HIT, front-left) · 29:+33 (arrested) · 35:+5 · 42:−15 · 48:−20. Heights from `quat_phang` (plane tilt 15°, highest toward
   θ=−155): z = tam_z + r·tan15°·cos(θ+155). Setting heights per key made a cone (52 mm off-plane) — never do that.
2. Handle points RADIALLY outward from the pivot (right fist at r 0.36 m, head 0.67 m further); blade (+X of the axe) = tangent in the
   strike direction ALWAYS (fixes «axe reversed on the backswing»).
3. Both hands are IK to the handle (`bam_can`): R socket at z 0, L at z −0.24, fist axis = handle axis. The torso turns with θ
   (ready yaw −12° with θ −20°; ready θ +10° put the right hand at 131 % reach).
4. Timing: windup 0→19 (long), strike 19→26 (fast), hold 26→29, recover →48. Pelvis leads chest by 2 frames.
5. Gates (`do_quat`, `do_nam_can`, «hit_cao_m»): off-plane ≤ 40 mm (got 12), radius spread ≤ 10 % (1.2), θ monotonic over the strike,
   blade leads motion cos ≥ 0.8 (0.95), grip error ≤ 5 mm (3.5) and ≤ 12° (0), blade height at hit 0.8–1.35 m (0.93),
   handle ≤ 35° from horizontal (15). Trajectory plot: `anim_settler/A4/chop2_trajectory.png`.

## Walk + carry (chosen 22/10)
- Walk = Kimodo `B/walk.bvh` (seed 1, prompt «walks forward … holding a small axe in his right hand»), axe removed (`KHONG_DAO_CU=1`),
  right arm = MIRROR of the left arm shifted half a stride (`TAY_GUONG=R`, `guong_tay`: S·M·S in the hips frame — an extra X-flip
  twisted the shoulder), one stride cut 39→67 (`CHU_KY`, seam blended 4 frames, pose seam 0 mm).
- Carry = the SAME walk + log 15 cm over the right shoulder (5 cm outward) + right fist IK-held on top of the log (`TAY_GIU_GO=1`)
  (Boss: «lấy walking animation mình mới chốt – sửa lại để tay trên vai không move»).
- Deliver every clip as its own file looped ×3 (`anim_settler/export_separate.sh`) — Boss reviews repetition per clip.

## Chốt 22/10 (Boss): idle = Kimodo (auto cycle 40→70). Run v2 and carry v2 — see memory feedback_retarget_huong_va_vac_vai.
Defaults now in animate.py: GO_VAI_T 0.75, TAY_GIU_GO_Z 0.22, TAY_NHAC −0.03, TAY_NGANG_THEM 0.07, DAU_NE 8°, KEP_MUI_CHAN 8°.
- Delivery (Boss 22/10 «Always send video»): `bash ~/projects/GameDev/anim_settler/send_build.sh <clip.mp4> <soi_dir> "<label>"` → loop ×3 + vs source + slow close-up.

## CARRYING A LOAD (Boss 22/10/2026 — chop scene → carry logs, capacity 1/2/3)
Rules, all gated in `~/projects/GameDev/anim_settler/chop_tree_scene.py` (exit 1):
- ⑧ BALANCE — «plank placement phải center… carry kiểu đó là té ngoài đời thực»: the load's centre of mass (volume-weighted over all
  pieces) projected on the load axis sits on the SUPPORT point (shoulder joint) on EVERY frame. The old carry clip let the log slide
  ±116 mm along the shoulder while walking ⇒ re-key the load frame per frame. Gate `8_lech_vai_mm` ≤ 60 (fixed: 0).
- ⑦ HAND ON A CONTACT SURFACE — «boundary layer surface… cố định tay cũng dễ hơn»: the load's outer shell = each piece radius + half
  hand thickness (2 cm); pick the shell point nearest the palm (sample 24 points around every piece, reject points inside another piece),
  LOCK palm position + hand rotation in the load's frame, IK only the wrist each frame (same lesson as the axe: lock grip to prop first).
  The free hand is only pushed out if it sinks. Pushing the holding hand out per frame failed (−43 mm). Gates `7_tay_xuyen_go_mm` ≥ −3,
  `7_tay_giu_ho_go_mm` ≤ 40 (fixed: 0 / 0).
- ⑥ HEAD CLEARANCE: bigger/more pieces ⇒ shift the bundle away from the head by the measured shortfall (axis-to-head ≥ r + 9.5 cm),
  reveal the load only after the carry pose has blended in. Gate `6_go_cach_dau_mm` ≥ 0.
- Capacity system: `--khuc 1|2|3` (1 = r 0.10 × 1.45 m; 2 = stacked; 3 = triangle 2 bottom + 1 top, r 0.085), asset lpms `carried_log`.
- Blender has no "never intersect" switch for keyframed characters: rigid-body collision works only for simulated objects; constraints
  (Limit Distance «outside», Floor, Shrinkwrap) can keep ONE bone off ONE target but fight IK and are invisible to our gates. We solve
  contacts explicitly (locked contact point + IK) and prove them with gates.
- ⑨ HUG ARC (Boss 22/10): holding arm hugs the load — palm on the farthest reachable shell point, elbow out to the side; see humanoid-rig-animation §CONTACT CONTRACT 4b.

## BOW — full body (Boss 23/10/2026: «animation bắn cung, toàn bộ body phải move - áp dụng luật physics và anatomy từ chặt gỗ, đập đá - nâng cấp animation bắn cung xem, khom người, giơ cung, kéo ra rồi bắn nhanh»)
Script `GameDev/anim_settler/hunt_scene.py` (`--con nai|tho`). Per shot 46 frames @24: nock 0–8 (bow canted 40° down, body crouched) · raise 8–14 (half rise) · DRAW 14–22 (fast) · aim 22–25 · RELEASE 25 · follow-through 25–31 (draw hand flies 15 cm back past the ear, torso recoils 4°) · recover to crouch 31–46.
Body layer `khom(ha, nghieng, xoay_hong)`: hip drop 10 cm crouch / 5.5 cm shooting, hip hinge 16°→9° split hips 55 / spine 20 / chest 25, leg IK with ankles pinned (knees forward), pelvis yaw leads the chest by 2 frames (chop rule), chest opens +6° during the draw.
Gates (exit 1): every shot hips travel ≥ 3 cm AND trunk pitch range ≥ 5° (measured on bones), foot slide ≤ 5 mm, wrists 0 over anatomy, arrow tip within 120 mm of the surface at hit and after 20 frames.
Trap: Child Of on a scaled target — rabbit (0.3) needs scale channels off AND a scale-free inverse; the deer rig (object scale 29.8) must keep the full inverse (scale-free made arrows land 8 m away).

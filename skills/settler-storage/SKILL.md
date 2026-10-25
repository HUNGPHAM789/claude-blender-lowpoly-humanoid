---
name: settler-storage
description: Open storage (visible stock) for settler games/clips — log pile 5-4-3-2-1, deposit (carry → bare-hand walk + item fades into next slot) and withdraw (top-down fade-out). Read BEFORE building any stockpile/storage, depositing or taking items, or animating settlers bringing resources.
---

# Settler open storage (Boss 23/10/2026)
Boss: «dùng skill tạo open storage (visible what are being stored)… carry đi tới gần storage switch lại pose đi bộ bare hand - gỗ appear fade
in fast nằm trong storage… 2 settler mỗi người carry 1 khúc… gỗ stack 5 layers 5-4-3-2-1… khi bị lấy đi… disappear from top to bottom fade out fast».
No put-down animation.

## One source of truth: `scripts/storage.py`
- `o_chua()` lists the slots in FILL order: bottom layer left→right, then up. 5-4-3-2-1 = 15 logs.
  Each upper log sits in the groove between two lower ones: x offset r, height +√3·r. Logs lie along the storage Y axis.
- `thu_tu_lay(n)` gives the withdraw order, the reverse of fill (top first).
- `MO_NHANH` = 6 frames (0.25 s) for the fast fade in/out.
- `soi_kho()` gates the layout:
  - no two logs overlap;
  - every upper log rests on exactly 2 logs;
  - the bottom layer rests on the sleepers;
  - the edge stakes never pierce a log.
  - Reverse test: stakes moved inward → caught.
- The asset (lpms `assets/wood_storage.py`, r_e81cdffc, 116 tris) and the scenes import these numbers. Never re-type them.

## Scene: `~/projects/GameDev/anim_settler/storage_scene.py`
Usage: `--nguoi 1|2 [--co-san 7]`, or `--demo` (fill 15, then withdraw top-down).

1. **Walking in with the load.** Carry and walk (Kimodo) share the same hip trajectory, so switching carry→walk at the same frame is seamless.
   - The switch happens when the hips pass the storage centre line.
   - The carried log fades out in 6 frames, and the next slot fades in during the same 6 frames.
   - The arms blend from the locked carry grip to the walk pose over 10 frames.
2. **Carrying rules.** They come from `settler-actions/scripts/carry_log.py` (shared with the chop scene): shoulder balance, shoulder seat,
   palm on the outer face, whole arm outside the load, BVH 0.
   - Two settlers = two separate imports. Each body is looked up from `rig.children`, never by name.
3. **Gates (exit 1).**
   - Layout (`soi_kho`).
   - ⑫ every stored log parallel to the storage axis (≤ 2°) and exactly in its slot (≤ 5 mm).
   - ⑪ BVH overlap between every person and the storage + stored logs = 0.
   - Each settler's carry gates.

## Traps paid for (23/10)
- glTF imports use QUATERNION rotation mode, so setting `rotation_euler` is silently ignored and all 15 logs stood upright.
  Set `rotation_mode = "XYZ"` first. ⑫ reverse test: upright 1.0 ⇒ caught.
- With XYZ order, a "spin" put on Z after X becomes a yaw: the logs splay ±14° into X shapes.
  Spin about the log's own axis is the Y component after the 90° X rotation. ⑫ reverse test: 14° ⇒ caught.

## Rock / loose-goods slot + back basket (Boss 23/10/2026: «nó cũng stack và stack đc nhìu hơn ở storage đúng ko? Per slot»)
- `kho.o_chua_dong()`: square pyramid 4×4-3×3-2×2-1 = 30 units per slot (logs: 15). Change capacity = change `LOP_DA`. `soi_dong()` gates it (no overlap, 4 supports, inside the bin wall; reverse test: wall 0.24 ⇒ caught).
- Assets: lpms `pebble` (1 unit), `stone_storage` (open bin, walls lower than the pile), `back_basket` (woven back basket, open top).
- Scene `~/projects/GameDev/anim_settler/basket_storage_scene.py`: walk + basket on the back + both hands gripping the straps; passing the bin ⇒ basket contents fade out, next `DA_MOI_CHUYEN` slots fade in, basket stays on the back.
- Basket placement = binary search of the back offset over EVERY frame (no torso hit) + tilt that follows the spine (`GIO_NGHIENG` −7°); gate: back gap per height ≤ 35 mm (Boss «chỗ cổ và đầu còn gap»).
- Basket contents must look FULL with a heap above the rim (Boss «stone stack còn thưa quá»): rings against the inner wall, radius from the REAL rock bounding radius measured on the mesh.
- Straps: skinned to the body (weights copied from the nearest body vertex, verts moved to rest pose) + Shrinkwrap mode OUTSIDE onto BODY + shirt (⛔ OUTSIDE_SURFACE glues every vertex to the surface; ⛔ the waist flap mesh drags the strap down). Gate = signed penetration depth ≤ 2 mm (reverse test: Shrinkwrap off ⇒ rc=1).
- Hands on straps: closed-form elbow (sphere ∩ sphere, pick the point nearest "elbow down"), hand straight along the forearm (neutral wrist). Gates: wrist ⑭b, hand-to-strap gap ≤ 12 mm.

- Clip-level lesson: the basket scene and storage clips use `anim_settler/SEPARATE/tmp/walk.glb`; every scene that uses it must call `humanoid_anim.sua_chan_xoay` (toe-in fix) — see humanoid-rig-animation §FEET.

## Meat storage «kho thịt» (Boss 23/10/2026: «Storage stacking display thịt»)
- Unit: lpms `meat_piece` (smoked haunch + twine + bone, 120 tris, 0.33 m; flat bottom, top plateau `kho.THIT_CAO`) · small variant `meat_piece_small` (slab + fat strip, 76 tris).
- Asset `meat_storage` (r_4acd6ca5, 4202 tris incl. full stock, 1.84 × 1.26 × 1.90 m): roofed smoking rack, 8 hooks over a fire ring + slatted table with 2 brick piles 4-3-2-1. Capacity 10/pile × 2 + 8 hooks = **28**.
- `kho.o_chua_thit()` = slots in FILL order (table piles layer by layer, both piles together → hooks centre-out); each has `vi_tri`, `ry`, `rz`; cut transform `kho.ma_tran_thit(o)`. Withdraw = reverse (`thu_tu_lay`). Stock parts `thit_<NN>_*`: storage with Q cuts shows NN < Q (scenes hide/fade the others, same fast fade `MO_NHANH`).
- Gate `kho.soi_thit(parts)` on the REAL meshes: no penetration > 5 mm, every cut rests (CoM inside its bottom contacts) or hangs plumb on a `moc_*`. Runs inside `lpms render` via `META["soi"]` (fail ⇒ exit 1) and standalone `python3 storage.py thit --nguoc` (reverse tests: spacing 0.10 / layer gap 2 cm / wrong tie point ⇒ all caught).
- Review render: `blender -b -P ~/projects/GameDev/concept/meat/review_meat_storage.py -- kho <out.png> 14 28` (empty/half/full + male settler) or `-- can <out.png>` (close-up).

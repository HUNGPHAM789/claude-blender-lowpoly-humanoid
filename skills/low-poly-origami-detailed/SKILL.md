---
name: low-poly-origami-detailed
description: LPD — DETAILED low-poly origami humanoid (male/female, ~2,400 render tris per body, 5-finger hands, faceted face with eye openings, detachable hair). SPEC ONLY — nothing built yet. Open when Boss asks for the detailed/high-facet origami human set, NOT for the simple LPM base mesh.
version: 0.3.0 (in development)
author: Boss (spec + concept image, 22/10/2026)
---

# LPD — detailed low-poly origami humanoid (IN DEVELOPMENT)

**Status 22/10/2026:** Boss picked this formula to develop: «công thức bên phiên bản chi tiết nhìn kỹ lại khá ok. Giờ develop với phiên bản chi tiết. Cho tôi base model nữ nữa».
- Code: `~/projects/GameDev/lpd_detailed/` — `GIOI=nam|nu python3 geometry.py out/geometry.json` then `GIOI=nam|nu blender -b -P blender_build.py -- out/geometry.json out/` (counts measured from mesh, GLB, .blend, 13 renders).
- Male 1.75 m / female 1.65 m share ONE topology: 1,354 faces = 2,420 render tris, exact per region except hands 274Q+64T (render total exact). Female = different section tables (TOR, NECK, HR, FEAT, arm/leg profiles) + uniform scale 1.65/1.752.
- Clean mesh: 0 non-manifold, 0 duplicate faces, 0 winding conflicts; 12 open edges = embedded ear bases.
- Build + gate in one command: `bash build.sh nam|nu` → runs geometry.py, Blender, then `check_lpd.py` (exit 1 on failure).
- v0.3 (22/10) Boss: «Sửa tay ngắn lại tí. Còn nữ thì chưa thấy ngực - sao vậy ta? Chưa có spec ngực? Hay model ko biết?»
  · Arms: `TAY_K=0.86` (arm/forearm length) ⇒ fingertip 0.369·H → 0.409·H. Gate ②: 0.39–0.44·H.
  · Bust: the spec only says «simplify chest… clean mannequin surfaces» — no bust spec. v0.2 pushed the WHOLE chest ring forward 8 mm ⇒ thicker chest, no mounds (bust vs sternum −1 mm). Fix: push ONLY ring vertices at ±22.5°/±45° on rows z 1.20–1.30 forward (24/19/7 mm) and tuck the under-bust row; sternum stays ⇒ bust 19 mm in front of sternum, 31 mm in front of under-bust. Gate ③: female ≥15/≥15 mm, male ≤10/≤10.
  · Reverse tests: TAY_K=1.0 ⇒ ② rc=1 · male torso measured as female ⇒ ③ rc=1 · real builds rc=0.
- Known open items: knee seam, hair = short only (bob not built), no rig.
- Spec problems found by the first test: `~/projects/GameDev/test_spec/detailed/REPORT.md`.

Boss 22/10/2026: «save bộ này riêng — cũng low poly nhưng dạng chi tiết — chưa đụng tới gì hết».
⛔ Not implemented. Do NOT merge into LPM (`low-poly-origami-character`), which is the simple ~600-tri base mesh with uniform low facet density.

Files:
- `Origami_Humanoid_Spec_v1.md` — Boss's spec verbatim: per-region Q/T budgets (body 1,352 source faces / 2,420 render tris), face 96 faces in 8 groups, hand 168 faces/hand, rear pelvis 64 faces, two hair assets (short 80 faces, bob 144), HAIR_SOCKET + SCALP_REFERENCE attachment, 3 materials (Body_Ivory, Eye_Dark, Hair_Charcoal), acceptance checklist.
- `concept_sheet.webp` — concept board (male/female front + rear, hair assets with undersides, face/hand/rear-pelvis closeups).

When starting it: read the spec, reuse LPM's continuous-ring torso + gates where possible, report counts from real mesh data per region (spec §Acceptance), keep the detachable-part contract compatible with LPM sockets.

## EYES = SUNKEN SOCKET + SKIN SHADE, no black square (Boss 23/10/2026 chose C from an A/B/C test: «C somehow có cheek đẹp hơn, lông mày ok hơn… Lấy design mặt C»)
- Default in `~/projects/GameDev/lpd_detailed/geometry.py`: `MAT_LOM` defaults to "2" ⇒ socket verts (rows 4–5, cols 1/2/14/15) pushed 16–27 mm in, the 2 eye faces get material `Socket_Shade` (linear 0.12, 0.09, 0.07 ≈ sRGB 0.38 — dark skin, not black). Old variants: `MAT_LOM=0` black square (A), `1` socket only (B — too faint at distance).
- Why C reads better: the deeper socket also moves the brow ridge and cheek planes, so they catch light — a geometry effect, not a skill/preload effect.
- Gate ④ in `check_lpd.py` (runs in build.sh): BODY glb must have `Socket_Shade` and no `Eye_Dark` ⇒ rc=1 (reverse test MAT_LOM=0 ⇒ caught).
- Material colours are LINEAR: 0.30 looks pale (≈0.58 sRGB); check by eye, not by number.
- A/B renders: `HAU_TO=<tag> CO=1 bash build.sh nam` + `view_outfit.py` with several items (keeps eye/dark/socket materials; frame widens with item count).
- Consumers: rig-profile.json and lpms.py read `out_*_cam` ⇒ new exports get C automatically; old clips in `anim_settler/SEPARATE/tmp` still have the old eyes until re-exported.

## Male outfit: HIGH BOOTS + pants cover the back of the thighs (Boss 23/10/2026: «Hình như ko phải vệt mà là cái quần hay high boot…» · «phía trước nó cover cao quá so với phía sau chỉ cao hơn đầu gối một tí»)
- Body region "glute" runs down the BACK of the thigh to near the knee. Old `hair_outfit.py` built the tunic from torso+glute ⇒ a tunic "tail" behind the thighs whose lower edge looked like a boot cuff, and the gap between the two flaps flashed as a pale streak when walking. Pants were built from "legs" only.
- Now: tunic takes glute only above the hem (z ≥ 0.88); pants = legs + glute below 0.90; male boots = every non-arm face below `CO_UNG` 0.56 (just above the knee), outer layer 10 mm, vertices clamped flat at the cuff (no shapely ⇒ trimesh slice_plane fails). The inner-thigh crotch triangle cannot carry the boot (clamping it makes a web between the legs).
- Gates in `hair_outfit.py` (exit 1 via build.sh): ⑤ tunic bottom z ≥ 0.85; ⑥ boot cuff height spread on the OPEN BOUNDARY vertices ≤ 25 mm (reverse test: slanted cuff ⇒ 137 mm caught). Measuring by 30° arcs gave false 86 mm (empty arcs picked knee vertices).
- Female ears are separate mesh islands ⇒ Blender bone-heat leaves 28 vertices unweighted; `humanoid_anim.da` now copies weights from the nearest weighted vertex and still reports the count.

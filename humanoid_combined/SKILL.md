---
name: humanoid-combined
description: HM — COMBINED low-poly origami humanoid base mesh (male/female) in TWO tiers, rut_gon (isometric game, ~1.1–1.3K tris) and chi_tiet (~2.3–2.5K tris). Merges three specs: LPM (ours: construction, contract, gates), the DETAILED spec (budgets, face, 5-finger hand) and the SIMPLIFIED concept (body form, glutes, simple face). Open for any new low-poly humanoid body that needs a face or a game budget; the faceless LPM base is still available via --faceless.
version: 1.0.0 (22/10/2026)
---

# HM — combined low-poly origami humanoid

Boss 22/10/2026: «gộp 3 spec: của mình, chi tiết, và rút gọn» · «nên combine spec của mình, spec chi tiết, và spec rút gọn
(mỗi cái thiếu dư một tí nên combine là tốt nhất) - nhưng vẫn ghi rõ 2 phiên bản chi tiết và rút gọn».

```
python3 hm.py --tier rut_gon|chi_tiet --gioi nam|nu --out <dir>/<name> [--faceless] [--co 0..1] [--hair none|short|bob]
blender -b -P view_hm.py -- renders/<name> <dir>/<name>.glb [<dir>/<name>_HAIR.glb]     # FRONT + SIDE, LPM camera
./build_all.sh                                                                          # the 5 test variants
```
Outputs `<name>.glb` (body, Y-up, one node per part + `SOCKET_*` empties + dark `mat_L/R` eye patches),
`<name>.json` (contract, landmarks, per-region counts), `<name>_HAIR.glb` (separate asset). The build runs
`hm_check.py` itself; **any red gate ⇒ exit 1**.

## 1. What came from where
| piece | A = LPM (ours) | B = detailed spec | C = simplified concept |
|---|---|---|---|
| construction | ✅ continuous torso lofted from a SECTION TABLE; separate closed limb parts; sockets + .json; Y-up GLB | | |
| gates | ✅ ①③④⑤⑥⑦⑧⑨⑩⑪⑫⑮ ported | | |
| torso table | ✅ male rows; chi_tiet = LPM rows densified to 12 | | ✅ rut_gon female table (glute + glute_low rows), male gets the same 8-row layout |
| glutes | ✅ light glutes, W-shaped crotch rim, no skirt hem | | ✅ «mông chuẩn» pushes (150°/165°) |
| budgets | | ✅ chi_tiet = 2,420 table | ✅ rut_gon ≈ ½ detailed (test-derived) |
| face | ✅ --faceless gem head + forehead (48 tris) | ✅ chi_tiet head: 16 columns × 8 rings + feature offsets | ✅ rut_gon head: 10 columns × 8 rings, eye quads |
| hand | ✅ rut_gon: 5-block grip hand (hand.py, --co, Ø32 grip) | ✅ chi_tiet: 5 separated digits, 6-sided fingers, opposed thumb | |
| heights | | ✅ male 1.75 / female 1.65 | |
| hair | ✅ HAIR_SOCKET joins the socket contract | (rim too small, no recipe) | ✅ recipe: build on the head's own facets, scale 1.032 about HAIR_SOCKET |
| fixes over the tests | | arms too long ⇒ landmark table + gate ⑰ | twisted-meat legs ⇒ one ring frame per limb + gate ⑯ |

## 2. The two tiers (read these numbers, not adjectives)
| region (render tris, measured) | rut_gon | rut_gon --faceless | chi_tiet | detailed spec |
|---|---:|---:|---:|---:|
| head (face+skull+ears) | 180 | 48 | 296 | 280 |
| neck | 24 | 24 | 48 | 56 |
| torso incl. glutes | 252 | 252 | 480 | 480 |
| arms (both) | 192 | 192 | 352 | 352 |
| hands (both) | 148 | 148 | 584 | 612 |
| legs (both) | 288 | 288 | 480 | 480 |
| feet (both) | 72 | 72 | 128 | 160 |
| **body total** | **1,156** | **1,024** | **2,368** | 2,420 |
| gate ② window | 1,100–1,300 | 950–1,200 | 2,300–2,500 | |
| eye patches (`mat_*`, not counted) | 8 | — | 8 | |
| hair short / bob | 48 / 50 | — | 77 / 88 | 128 / 240 |
Per-region gate: each region within ±30 % of `TIER[...]["regions"]` in hm.py.

### Ring / loop table (vertices per ring × rings; all lofts use ONE frame per limb ⇒ phase aligned)
| region | rut_gon | chi_tiet |
|---|---|---|
| torso | 14 × 9 rows (angles 0·30·60·90·120·150·165·180 ±) | 20 × 12 rows (0·20·…·140·152·165·180 ±) |
| neck | 6 × 2 | 8 × 3 |
| upper arm / forearm | 6 × 4 / 6 × 4 | 8 × 6 / 8 × 5 |
| thigh / shin | 8 × 5 / 8 × 4 | 10 × 6 / 10 × 6 |
| foot (heel→toe) | 6 × 3 | 8 × 4 |
| head | 10 × 8 + crown + chin cap (C) | 16 × 8 + pole + jaw cap (B) |
| hand | LPM 5 convex blocks, ~74 tris | palm 8 × 4; fingers 6 × 4 (3 segments); thumb 6 × 3 |
Torso pushes are 15°-wide bumps, so the 14-vertex ring reproduces LPM exactly and the 20-vertex ring gets the same shape.

### Landmark table (metres, at working height; source of every joint/socket)
| landmark | nam 1.75 | nu 1.65 |
|---|---:|---:|
| head top (`dinh`) | 1.750 | 1.650 |
| chin (`cam`) | 1.515 | 1.428 |
| neck base | 1.463 | 1.380 |
| shoulder top (torso `vai` ring) | 1.415 | 1.334 |
| shoulder joint (x, y, z) | 0.172, 0.008, 1.380 | 0.150, 0.007, 1.302 |
| upper arm / forearm length (along limb, A-pose 25°) | 0.292 / 0.258 | 0.282 / 0.246 |
| hip joint (x, y, z) | 0.089, 0.010, 0.875 | 0.090, 0.013, 0.830 |
| crotch (`day_chau`) | 0.817 | 0.775 |
| knee | 0.486 | 0.458 |
| ankle | 0.083 | 0.078 |
| fingertip (measured) | 0.409 H (rut_gon) · 0.415 H (chi_tiet) | 0.407 H · 0.417 H |
| shoulder→fingertip (measured) | 0.435 H · 0.426 H | 0.439 H · 0.425 H |
Head is fitted uniformly so chin→top equals the table (7.4–7.7 heads); female heads 4 % narrower.

## 3. Contract (parts + sockets)
Parts: `than co dau canh_tay_L/R cang_tay_L/R dui_L/R cang_chan_L/R ban_chan_L/R ban_tay_L/R` +
rut_gon `ngon1 ngon2 cai1 cai2 _L/R` (LPM hand) · chi_tiet `ngon_cai ngon_tro ngon_giua ngon_ap ngon_ut _L/R` ·
faced: `tai_L/R` (ears) + `mat_L/R` (dark eye patches, open, not counted).
Sockets: LPM set (`dau ban_tay_* cam_* ban_chan_* lung hong_*`) **+ `HAIR`** (skull centre at 0.55 of chin→top).

## 4. Hair (replaceable-assets recipe, `build_hair`)
1. Take the head's OWN facets whose centroid is above a hairline: front 0.80, sides 0.60 (short) / 0.62 (bob), back 0.47 of chin→top.
2. Scale them about `SOCKET_HAIR` by `HAIR_K = 1.032` (parallel copies of the scalp ⇒ cannot clip a star-shaped head).
3. bob: boundary edges more than 55° from the face are extruded to 3.5 cm below the chin, 18 mm outward.
4. Separate GLB `<name>_HAIR.glb`, node `HAIR_SHORT|HAIR_BOB`, parented at identity to `SOCKET_HAIR`; underside open.
Gate ⑱: 0 of 4,000 surface samples inside the head (ray parity). Stylised clumps are NOT done (not required yet).

## 5. Gates (`hm_check.py`, run by every build; manual `python3 hm_check.py <out>`)
Ported from LPM: ① watertight parts ③ height ±1 %, floor −5…+10 mm ④ volume ⑤ continuous torso (1 cm slices, step ≤ 20 mm)
⑥ contract ⑦ L/R symmetry < 3 % ⑧ waist ≤ 0.93 × min(chest, hip) ⑨ head facet density (faceless ≤ 80 tris & ≤ 1.5× torso;
faced ≤ 3.5×, measured 3.3× rut_gon / 2.1× chi_tiet) ⑩ glutes (projection 30–60 / 40–80 mm, cleft 5–20, no sag)
⑪ forehead recedes ≤ 25 mm behind the brow ⑫ «W» crotch rim, no skirt ⑮ grip (rut_gon: wrap ≥ 75 % at co ≥ 0.95, penetration ≤ 1.5 mm).
New:
- ② **per-tier budget** (window above) + per-region ±30 %.
- ⑯ **ring twist** — every elongated loft (arms, legs, feet): rings found from the mesh by axial clustering, angle about the
  ring centroid (normalised by ring spread), mean nearest-vertex angle between consecutive rings ≤ 8°.
  `python3 hm_check.py --xoan <any.glb>` works on foreign files (splits merged meshes into shells).
- ⑰ **arm length** (open hand only): shoulder = upper-lateral corner of the front silhouette (max x+z, z < 0.86 H);
  fingertip = lowest vertex with x > 0.14 H. Shoulder→fingertip 0.42–0.45 H **and** fingertip height 0.38–0.47 H.
  `python3 hm_check.py --tay <any.glb>`.
- ⑱ hair inside head 0 / 4,000. ⑲ landmarks (head top, chin, shoulder-top ring) within 15 mm of the table.

Reverse tests (22/10, run, rc shown): see NOTES.md §2. Summary: simplified BODY_F legs/arms twist 22.5°/30° → rc=1;
detailed BODY_M arm → rc=1 (fingertip 0.369 H); own model with alternating ring phase → rc=1; own +12 % arms → rc=1
(0.472 H); hair at k=0.97 → 1,851/4,000 inside, rc=1; all 5 own builds rc=0.

## 6. Traps
- Ring phase: never offset alternate rings (the simplified test did π/n per ring ⇒ spiral «twisted meat»). `chi()` builds
  every ring of a limb with the SAME frame. Gate ⑯ catches regressions.
- Grip hand scale: LPM grip angles were solved at hand scale 1.0 with an unscaled Ø32 cylinder; scaling the hand by H/1.80
  gave 3.1 mm penetration on the 1.65 m female. The rut_gon hand is built at scale 1.0.
- Arm length must be judged where the viewer looks: the detailed test's L/H read 0.425 (inside the band) because its low,
  narrow shoulders moved the corner onto the upper arm; it is the fingertip height (0.369 H) that shows «tay hơi dài».
- `trimesh.contains` / `signed_distance` need rtree (not installed) — gates use numpy ray casting.

## 7. Changelog
| ver | date | Boss said | change | measured | gate |
|---|---|---|---|---|---|
| 1.0 | 22/10/2026 | «gộp 3 spec: của mình, chi tiết, và rút gọn»; simplified: «tốt cho isometric game - tuy nhiên sao cái chân nó nhìn giống như bị xoắn thịt. body form đẹp, với mông chuẩn»; detailed: «nhìn cũng mướt nhưng tay hơi dài - tuy nhiên có mặt nhưng là tạm ổn»; «nên combine spec của mình, spec chi tiết, và spec rút gọn (mỗi cái thiếu dư một tí nên combine là tốt nhất) - nhưng vẫn ghi rõ 2 phiên bản chi tiết và rút gọn» | one builder, 2 tiers; LPM backbone; C body/glutes; B face/hand/budgets; phase-aligned limb rings; landmark table; hair recipe | rut_gon 1,156 (faceless 1,024) · chi_tiet 2,368 · twist ≤ 0.7° · arm 0.425–0.439 H · hair 0/4,000 | ② ⑯ ⑰ ⑱ ⑲ new |

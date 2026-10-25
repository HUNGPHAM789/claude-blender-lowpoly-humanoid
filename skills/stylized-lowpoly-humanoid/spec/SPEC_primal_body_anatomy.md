# SPEC — primal base body anatomy (v1.1, 25/10/2026)

Boss: «Xác định vùng T shape của khuôn mặt và gắn lông mày dày vào · Học cách làm lồi ra của phần dưới ngực nam · Cách đường cong các cơ bắp ·
bắp tay trước hóp vào chỗ cổ tay rồi lại cong ra chỗ cơ ngón cái · Đường cong của mông và đường đi vào · Đường cong của ngực nữ · Cơ cổ vai ·
Xương quai xanh · Lưng hỏm chỗ spine». Numbers: `SPEC_primal_body_anatomy.json`. Tool: `scripts/analyze_anatomy.py` (exact z-buffer depth maps
front/back at 2.5 mm + limb slices perpendicular to each bone, every vertex owned by its nearest bone). Teachers: the Hunyuan base bodies.

## Measured (male · female)
| feature | how it is found | male | female |
|---|---|---|---|
| **T zone — nose** | centre column standing proud of ±3 cm | tip 4.1 cm proud, at 0.10 of the head height | ⚠ 8.2 cm (picked the chin) |
| **T zone — brow ridge** | first bump above the eye-socket dip, per column 1–6 cm off centre | at 0.63 of the head, 2.0 cm over the socket | at 0.59, 1.8 cm |
| **lower pec (male) / breast (female)** | front profile at x = 8.5 / 7.5 cm: peak, fold below, slopes | peak 7.6 cm above the chest joint, **1.9 cm proud of the fold 6 cm below**, underside 52° | peak 3.3 cm above, 7.7 cm proud ⚠ fold 13 cm below (too low), upper slope 34°, underside 62° |
| **trapezius** | top silhouette neck → acromion vs the straight chord | drops 5.2 cm, slope 14°, **bulges 3.1 cm** over the chord | 3.8 cm, 16°, 1.4 cm |
| **clavicle** | ridge in the band 1–12 cm under the neck joint | 1.2 cm proud of the hollow below, 6.8 cm under the neck | 2.8 cm, 7.0 cm (outer ends only) |
| **spine groove** | back map: centre vs ±3.5 cm, waist → neck | 0.9 cm median, **1.5 cm max at 0.71** of pelvis→neck | 0.8 cm median, 1.1 cm max |
| **glutes** | back profile at x = 7.5 / 8.5 cm: most-back point, crease below, hollow above | peak 10 cm above the pelvis joint, **5.3 cm proud of the fold 14 cm below**, lower-back hollow **6.4 cm** deep 16 cm above | peak 9.3 cm, 3.6 cm over the fold 14 cm below, hollow **7.8 cm** deep 15 cm above |
| **upper arm** | radius along shoulder → elbow | belly at 0.23, 1.64 × the ends | flatter (1.14) |
| **forearm → wrist → hand** | radius along elbow → wrist → +14 cm | belly 7.0 cm at 3 cm from the elbow → **wrist 4.4 cm (0.63 ×)** at 13 cm → hand swells 2.7 × the wrist | belly 9.0 → **wrist 3.5 (0.38 ×)** → hand 2.6 × |
| **thigh / calf** | radius along hip → knee / knee → ankle | thigh widest at the root (1.59 ×), **calf belly at 0.40 of the shin, 2.07 ×** the ankle | calf at 0.32, 1.71 × |

## Rules for a builder (what the numbers mean)
- **Lower pec (male):** the pec is a shelf — its lower edge stands ≈ 2 cm proud, the underside turns steep (≈ 50°) into a fold ≈ 6 cm below.
- **Glutes + "đường đi vào":** an S-curve on the back — lower-back hollow 6–8 cm deep, glute peak ≈ 10 cm above the pelvis joint, crease ≈ 14 cm below.
- **Forearm:** fat near the elbow, pinched at the wrist (male 0.63 ×, female 0.38 × of the forearm belly), then the hand/thumb mass swells again.
- **Trapezius:** the neck–shoulder line is not straight — it bulges ≈ 3 cm (male) above the chord.
- **Spine:** a shallow groove 1–1.5 cm, deepest between the shoulder blades and the waist (male) / low back (female).
- **Calves:** strong belly high on the shin (0.3–0.4 of its length), ≈ 2 × the ankle.

## Face T zone + eyebrows (v1.1)
Boss 25/10: «chân mày đang bị lệch qua phải … sóng mũi nó có một khoảng ngang» → «Lông mày nam đang bị để ở chỗ lõm mắt · Lông mày nữ cũng chưa
dán đúng chỗ lồi nhất của T shape, hay vùng liền vào chỗ sóng mũi với mặt».
| | male | female |
|---|---|---|
| face midline (body axis = ankle centre) | −1.19 cm | +0.90 cm |
| nose-bridge half width (at the socket rows) | 0.95 cm | 0.95 cm |
| eye socket floor (of head height) | 0.50 | 0.47 |
| brow ridge = socket rim (of head height) | 0.62, stands 2.1 cm over the socket | 0.57, 1.7 cm |

Tool: **`scripts/eyebrow_fitter.py`**, the Eyebrow Fitter from the Codex review of 25/10. `add_eyebrows.py` forwards to it.

Steps:
1. Landmarks come from `face_T_zone`: the FACE midline, the bridge half width measured at the socket rows, and the eye-socket row.
2. 7 control points per brow: head, inner body, inner peak, peak, outer peak, outer body, tail.
   - At each point the ridge is re-measured with front→back rays.
   - The ridge is the socket rim: the first row within 1 mm of the peak above the socket. The female forehead is a flat plateau, so the bare peak wanders.
   - Left and right votes are averaged into one shape. That shape gets a robust line (tilt ≤ 15°), a CURVE arch, and an inner "frown".
3. The 7 points set the shape. The strip is resampled into 13 cross-sections, and both edges of each one are **raycast onto the head**, then pushed out along the **smoothed surface normal**.
   - The base sits 1 mm under the skin.
   - The lower front stands out by the thickness, the upper front by 0.6 × that.
   - The brow therefore follows the brow bone round to the temple, with nothing sunk in or floating off in the 3/4 and side views.
   - With only 7 sections, the straight chords left a 1.6–2 mm gap.
4. **Each side is cast on its own half of the face** with the same shape. A geometric mirror sank the female right brow, because the generated face is not symmetric.
5. Male: hairy bar 2.6 → 1.4 cm tall, with 6 flat spikes in the tangent plane pointing up and out. Female: slim arch 1.3 → 0.6 cm.
6. Parameters: `--width --angle --curve --thickness --surface-offset`.
7. Report `<out>.report.json`: per control point, the ridge row, the deviation and the normal.

Gates (exit 1). All measured on the mesh, on both sides:

| gate | limit | reverse test |
|---|---|---|
| ridge | brow centre within 0.8 cm of the ridge, judged only where the face looks forward (\|n_z\| ≥ 0.5) | `THU_BROW_DROP=0.025` ⇒ rc=1 |
| skin contact | ≤ 1.5 mm, sampled BETWEEN sections along the normal | `--surface-offset 0.004` ⇒ rc=1 |
| front vertices inside the head | 0 | `--surface-offset -0.004` ⇒ rc=1 |
| L/R asymmetry | ≤ 0.3 cm | — |

Measured on the teachers:

| | ridge deviation | skin gap |
|---|---|---|
| male | 0.28 cm | 1.1 mm |
| female | 0.50 cm | 0.7 mm |

## Ears → hair-root anchors
Found as a lateral bump (> 6 mm) on the side depth maps.
| | male | female |
|---|---|---|
| ear height | 7.2–7.5 cm | 6.2 cm |
| protrusion | 1.4 cm | 1.4 cm |
| lobe bottom (of head height) | 0.41 | 0.38 |
| ear top (of head height) | 0.68 | 0.63 |

Hair roots:
- Sideburn runs down in front of the ear to lobe height.
- The hairline wraps over the ear top, then goes behind the ear down to the nape.
- Hair never covers the most-proud point of the ear unless the style says so.

## Region between the legs — concavity (male ≠ female)
Boss 25/10: «cách làm vùng giữa 2 chân của nam và nữ khác nhau - đo độ lõm».
- **Apex** = where the thighs split, seen from the front.
- **Notch** = the gap between the thighs below the apex.
- **Front** = the midline compared with the thigh fronts and the groin creases either side.

| | male | female |
|---|---|---|
| apex below the pelvis joint | 0.7 cm | 7.3 cm |
| thigh gap 1 / 4 / 10 cm under the apex | 2.2 / 3.8 / 7.0 cm | 4.8 / 6.8 / 10.2 cm |
| front midline vs thigh fronts | **filled**: −7.8 cm for the first 4 cm, then rises to level (+0.3 cm) by 8.5 cm (bulge) | **recessed**: −6 to −7.6 cm for the first 13 cm (a valley between the thighs), level only ~19 cm up |
| groin crease | 1.7 cm deep, 2.3 cm off the midline, 6.5 cm above the apex (short V either side of the bulge) | 4.9 cm deep, 2.0 cm off the midline, running along the inner thighs |
| gluteal cleft (back) | 12 cm deep at the apex | 4.6 cm |

Rule:
- **Male:** a short, filled front with a bulge, a high apex and a narrow gap.
- **Female:** a recessed V valley, a low apex, a wider gap, and long creases down the inner thighs.

Both teachers wear modelled briefs: the waistband and leg line are raised geometry, so the numbers include the cloth.

## Confidence
Good: brow ridge, nose (male), lower pec, glutes and lower-back hollow, spine groove, trapezius, forearm → wrist. Doubtful (female): nose tip, underbust
fold, brow tilt. Clavicle: only the outer ends are found (teacher ridge too flat near the sternum). `hand_max` includes the fingers.

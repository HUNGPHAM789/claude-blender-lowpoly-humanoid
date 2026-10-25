# Asset: rabbit_v1 (stylized low-poly, static)
- Made 22/10/2026 by the organic skill (`build-stylized-organic-model`) — Boss: «spec organic làm động vật xuất sắc … thỏ này save lại thành asset».
- rabbit.glb (Y-up, height 1.0 m, materials: fur brown, bib cream, inner ear pink, nose, charcoal eyes) · rabbit.obj (Z-up) · plan_rabbit.json (rebuild input) · rabbit_report.json (1,700 body tris + 2×80 eye tris, 1 component, 0 boundary/nonmanifold, Euler 2).
- Rebuild: `python3 ~/.hermes/skills/creative/build-stylized-organic-model/scripts/organic_pipeline.py plan_rabbit.json …` (see skill).
- Known weak points: belly/bib patch is blocky; nose only 3 faces.
- Rigged/animated version: ../rabbit_v1_rig/ — rabbit_rigged.glb (23 bones, actions hop / hop_inplace / idle / sniff @24 fps), rabbit_rig.blend, GIFs, NOTES.md. Known: up to 5.4× edge stretch in airborne hop (model built sitting), feet slide ~4 cm (no IK).

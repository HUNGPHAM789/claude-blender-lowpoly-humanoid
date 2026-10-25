"""One fitter rule as its own exit code (ledger seals: the full fit_character run still has other red gates on the Hunyuan fixtures).

  python3 check_fit_gate.py --gate hair_facing  --body … --joints … --anatomy … --asset <hair.glb> [--reference <sheet.glb>] [--hair-yaw D]
  python3 check_fit_gate.py --gate top_underarm --body … --joints … --anatomy … --asset <top.glb>

hair_facing (Boss 25/10 «Male hair is backward» · «đuôi tóc đang xoay bên trái mặt»): free-hanging hair beside the face must be behind the
  ears (≤ 15 %) and the eyes/nose rays clear.
skirt_cover (Boss 25/10 ×2 «đùi phải vẫn lòi ra ngoài váy»): a placed lower garment leaves ≤ 1 % of the waist→hem-teeth skin visible.
top_underarm (Boss 25/10 «female outfit supose to be underarm not overarm» · «Nữ áo chưa ôm vào nách»): the top hugs the torso — inner
  standoff median ≤ 8 mm under the arms and on the back, nothing inside the body outside the hidden arm–torso strip, and its height
  scaled 0.7–1.4× (a cape squashed into a band is the wrong garment).
"""
import argparse, os, sys
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fit_engine as fe


def main(a):
    B = fe.Body(a.body, a.joints, a.anatomy); asset = fe.load_asset(a.asset); bad = []
    if a.gate == "hair_facing":
        ref = fe.reference_hair(a.reference) if a.reference else None
        X, info, Xr, disp = fe.fit_hair(asset, B, 0.003, ref, a.hair_yaw)
        hf, n = B.hanging_in_front(X); crit = [b for b in B.face_blocked(X, asset.faces) if b.startswith(("eye", "nose"))]
        print(f"hair_facing: yaw {info['yaw_deg']}° · free hair beside the face in front of the ears {hf*100:.0f} % of {n} · eyes/nose blocked {crit}")
        if hf > 0.15: bad.append("long hair / ponytail hangs beside the face (in front of the ears)")
        if info.get("reference_mass_dir_deg") is not None:
            dd = fe.angle_diff(info["mass_dir_deg"], info["reference_mass_dir_deg"])
            print(f"  hair mass points {info['mass_dir_deg']}° vs the sheet's {info['reference_mass_dir_deg']}° (Δ {dd:.0f}°, ≤ 60; offset {info['mass_offset_cm']} cm)")
            if dd > fe.MASS_TOL and info["mass_offset_cm"] > 2: bad.append("the ponytail / main hair mass is not behind the head (official sheet)")
        imb, tot = info["face_side_imbalance"]
        print(f"  face-side hair left/right imbalance {imb:.2f} (mass {tot:.2f}; ≤ 0.5 when mass > 0.2)")
        if tot > 0.2 and imb > 0.5: bad.append("hair beside the face is piled on one side (a tail / lock turned onto one cheek)")
        if crit: bad.append(f"hair covers {crit}")
    elif a.gate == "beard_snug":
        # Boss 25/10 ×2 «râu chưa sát vào mặt»: beard inner surface on the jaw (median ≤ 6 mm) AND the beard ≤ 18 mm thick (p90 off the skin)
        X, info, Xr, disp = fe.fit_placed(asset, B, "hair", 0.003) if a.placed else fe.fit_hair(asset, B, 0.003, None, a.hair_yaw)
        th, n = fe.beard_thickness(X, B); r = fe.rest_report("hair", asset, X, Xr, disp, B); jaw = r["standoff"]["beard"]
        print(f"beard_snug: {n} beard verts · thickness p90 {th} mm · inner surface off the jaw median {jaw['median_mm']} mm (p90 {jaw['p90_mm']})")
        if th is None or n < 20: bad.append("no beard found in front of the jaw")
        else:
            if th > 18: bad.append(f"beard stands {th:.0f} mm off the face (≤ 18)")
            if (jaw["median_mm"] or 99) > 6: bad.append(f"beard inner surface {jaw['median_mm']} mm off the jaw (≤ 6)")
    elif a.gate == "skirt_cover":
        # Boss 25/10 ×2 «váy bị lộ đùi bên phải» · «đùi phải vẫn lòi ra ngoài váy»: no skin between the waist and the hem teeth, all round,
        # the outer hips included (the old arm mask cut them out as "arm", so a side slit read 0.9 % while every front view showed thigh)
        asset, _, mov = fe.load_asset_parts(a.asset); X, info, Xr, disp = fe.fit_placed(asset, B, "lower", 0.003, mov)
        st = fe.see_report("lower", asset, X, B)
        print(f"skirt_cover: skin showing {st['skin_visible_frac']*100:.2f} % (≤ 1 %) of {st['zone_points']} · holes {st['holes']} · by region {st['by_region']}")
        if st["skin_visible_frac"] > 0.01: bad.append(f"skin shows beside / through the skirt ({st['skin_visible_frac']*100:.1f} %, mostly {max(st['by_region'], key=st['by_region'].get)})")
    else:
        if a.placed:                                                        # a designed top is judged as built, never re-placed
            asset, _, mov = fe.load_asset_parts(a.asset); X, info, Xr, disp = fe.fit_placed(asset, B, "upper", 0.003, mov)
        else: X, info, Xr, disp = fe.fit_garment(asset, B, "upper", 0.003)
        r = fe.rest_report("upper", asset, X, Xr, disp, B); so = r["standoff"]["by_region_median_mm"]
        d, _ = B.signed(X); vis = int(((d < -0.001) & ~B.hidden_in_arm_contact(X, d)).sum()); hs = info["height_scale"]
        print(f"top_underarm: standoff underarm {so.get('underarm')} mm · back {so.get('back')} mm · chest {so.get('chest')} mm · visible clipping {vis} verts · height ×{hs}")
        if (so.get("underarm") or 99) > 8 or (so.get("back") or 99) > 8: bad.append("top does not hug the torso under the arms / on the back")
        if vis: bad.append(f"{vis} top verts inside the body outside the hidden arm strip")
        st = fe.see_report("upper", asset, X, B)                           # Boss 25/10 ×2: «nách sau trái … lòi da»
        print(f"  skin showing {st['skin_visible_frac']*100:.2f} % (≤ 1 %) by region {st['by_region']}")
        if st["skin_visible_frac"] > 0.01: bad.append(f"skin shows through the top ({st['skin_visible_frac']*100:.1f} %, mostly {max(st['by_region'], key=st['by_region'].get) if st['by_region'] else '-'})")
        if not 0.7 <= hs <= 1.4: bad.append(f"height scaled ×{hs}: wrong garment for an under-arm top")
    for b in bad: print("⛔", b)
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--gate", choices=("hair_facing", "top_underarm", "beard_snug", "skirt_cover"), required=True)
    ap.add_argument("--placed", action="store_true")
    for k in ("--body", "--joints", "--anatomy", "--asset"): ap.add_argument(k, required=True)
    ap.add_argument("--reference"); ap.add_argument("--hair-yaw", type=float)
    main(ap.parse_args())

"""Pool the per-sample measurements into the LEARNED hair grammar (ranges, not one sample's numbers — Boss 25/10/2026: learn,
don't copy the teacher assets).

  python3 aggregate_hair.py --out spec/hair_grammar_learned.json <dir>/<sample>_clumps.json …   (ponytail files are picked up beside them)

Per sex × region: clump count per sample (min/median/max) and pooled p10/p50/p90 of length, base width, tip half-angle, tilt from
the scalp normal and droop; ponytail: pooled length, droop, root height, radius profile normalised to the bulge.
"""
import argparse, json, os, re
import numpy as np


def main(files, out):
    pooled = {}; counts = {}; tails = {}
    hl = {}
    for f in files:
        sm = f.replace("_clumps.json", "_summary.json")
        if os.path.exists(sm): hl.setdefault("female" if "female" in os.path.basename(f) else "male", []).append(json.load(open(sm)).get("hairline", {}))
    for f in files:
        sex = "female" if "female" in os.path.basename(f) else "male"; sample = re.sub(r"_clumps\.json$", "", os.path.basename(f))
        C = json.load(open(f))
        for k in C:
            pooled.setdefault((sex, k["region"]), []).append(k)
        for reg in {k["region"] for k in C}:
            counts.setdefault((sex, reg), []).append(sum(1 for k in C if k["region"] == reg))
        pt = f.replace("_clumps.json", "_ponytail.json")
        if os.path.exists(pt):
            d = json.load(open(pt))
            if d.get("length_cm"): tails.setdefault(sex, []).append(d)
    q = lambda a: [round(float(np.percentile(a, p)), 2) for p in (10, 50, 90)]
    G = {"_doc": "Learned from Hunyuan3D teacher meshes of the official primal sheets (25/10/2026). Lengths in cm at body scale "
                 "(male 1.80 m, female ~1.70 m scalp). p10/p50/p90 pooled over all samples; counts = clumps per sample (min/median/max).",
         "samples": [os.path.basename(f) for f in files], "regions": {}, "ponytail": {}}
    for (sex, reg), K in sorted(pooled.items()):
        f_ = lambda key: np.array([k[key] for k in K])
        cn = counts[(sex, reg)]
        G["regions"].setdefault(sex, {})[reg] = {
            "clumps_per_sample_min_med_max": [int(min(cn)), float(np.median(cn)), int(max(cn))],
            "length_cm": q(f_("length_cm")), "base_width_cm": q(f_("base_width_cm")), "tip_half_angle_deg": q(f_("tip_half_angle_deg")),
            "tilt_from_normal_deg": q(f_("tilt_from_normal_deg")), "droop": q(f_("droop")), "proud_cm": q(f_("proud_cm")),
            "length_over_width": q(f_("length_cm") / np.maximum(f_("base_width_cm"), 0.1)),
            "flow_deg": q(f_("flow_deg")), "abs_flow_deg": q(np.abs(f_("flow_deg"))), "flatness": q(f_("flatness")), "bend": q(f_("bend")),
            "root_off_scalp_cm": q(f_("root_off_scalp_cm")), "nn_spacing_cm": q(np.array([k["nn_spacing_cm"] for k in K if k.get("nn_spacing_cm") is not None]))}
    for sex, T in tails.items():
        prof = np.array([[p if p is not None else np.nan for p in t["radius_profile_cm_root_to_tip"]] for t in T])
        norm = prof / np.nanmax(prof, axis=1, keepdims=True)
        G["ponytail"][sex] = {"samples": len(T), "length_cm": q([t["length_cm"] for t in T]), "droop_from_vertical_deg": q([t["droop_from_vertical_deg"] for t in T]),
                              "root_height_on_head": q([t["root_height_on_head"] for t in T]), "root_behind_cm": q([t["root_behind_cm"] for t in T]),
                              "radius_profile_over_max_median": [round(float(x), 2) for x in np.nanmedian(norm, axis=0)],
                              "max_radius_cm": q(np.nanmax(prof, axis=1)), "lock_tips": q([t["lock_tips_in_lower_half"] for t in T])}
    G["hairline"] = {sx: {k: q([h[k] for h in H if h.get(k) is not None]) for k in ("front_lowest_base_above_head_centre_frac", "nape_lowest_base_above_head_centre_frac")} for sx, H in hl.items()}
    json.dump(G, open(out, "w"), indent=1); print(f"learned grammar → {out}")
    for sex, R in G["regions"].items():
        for reg, v in R.items():
            print(f"{sex:6s} {reg:7s} n {v['clumps_per_sample_min_med_max']} · flow|°| {v['abs_flow_deg']} · flat {v['flatness']} · bend {v['bend']} · root {v['root_off_scalp_cm']} · gap {v['nn_spacing_cm']}")
    for sex, v in G["ponytail"].items(): print(f"{sex} ponytail: {v}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--out", required=True); ap.add_argument("files", nargs="+")
    a = ap.parse_args(); main(a.files, a.out)

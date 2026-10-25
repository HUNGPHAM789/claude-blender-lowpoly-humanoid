"""Universal Character Fitter — one command: fit hair + outfit pieces to a base body, keep the low-poly topology, rig with the body's
weights, test 10 poses, write a Fitting Report. Exit 1 when a gate fails — «agent không được tuyên bố "fit thành công" chỉ vì nhìn Front
View thấy đẹp» (Codex proposal forwarded by Boss 25/10/2026).

  python3 fit_character.py --species humanoid --body <base_lp.glb> --joints <joints.json> --anatomy <anatomy.json> \
      --hair <hair.glb> [--reference <sheet_coloured.glb>] --outfit <skirt.glb>:lower --outfit <top.glb>:upper --out <dir> --name <id> [--no-poses] [--yaw-outfit DEG]

Steps (each one measured, numbers in <dir>/<id>_fit_report.json + .md):
 1 species profile (species/<species>.json) — landmarks rules, clearances, budgets, regions, poses, gates; quadrupeds refuse until measured
 2 decimate an asset only if it is over the species budget (lowpoly_blender.py) — fitting never changes faces afterwards
 3 fit_engine: hair (cavity → skull, root-only push) · lower / upper (belt ring / bust anchor, radial scale per height, fading push) · rigid
 4 rest report per layer: penetrating verts, deepest mm, mean clearance, per-region table, eye band, symmetry, edge stretch / shrink
 5 assemble body + layers (game palette) → rig_body_blender.py (body weights copied to layers) → pose_test_blender.py (10 poses)
 6 gates from the species profile; preview = lit, white background, rest turnaround + pose sheet
"""
import argparse, json, os, subprocess, sys
import numpy as np
import trimesh

HERE = os.path.dirname(os.path.abspath(__file__))
SKILLS = os.path.join(HERE, "..", "..")
SHL = os.path.join(SKILLS, "stylized-lowpoly-humanoid", "scripts")
sys.path.insert(0, HERE)
from fit_engine import Body, load_asset, load_asset_parts, fit_hair, fit_garment, fit_rigid, fit_placed, rest_report, reference_hair, make_lining, see_report

COLOURS = {"face": (58, 40, 28), "hair": (58, 40, 28), "lower": (74, 53, 37), "upper": (74, 53, 37), "rigid": (120, 116, 108), "lining": (176, 138, 92)}


def blender(script, *args):
    r = subprocess.run(["blender", "-b", "--python-exit-code", "1", "-P", script, "--", *map(str, args)], capture_output=True, text=True)
    return r.returncode, r.stdout + r.stderr


def main(a):
    sp = json.load(open(os.path.join(HERE, "..", "species", f"{a.species}.json")))
    if sp.get("status") != "implemented":
        print(f"⛔ species {a.species}: {sp.get('status')} — {sp.get('note', '')}"); sys.exit(1)
    os.makedirs(a.out, exist_ok=True); P = lambda s: os.path.join(a.out, f"{a.name}_{s}")
    body = Body(a.body, a.joints, a.anatomy); G = sp["gates"]
    items = ([("hair", a.hair)] if a.hair else []) + [(k, p) for p, k in (o.rsplit(":", 1) for o in a.outfit or [])]
    rep = {"species": a.species, "body": a.body, "layers": {}, "poses": {}, "gates": [], "preview": {}}
    fitted = []
    for kind, path in items:
        asset, parts, movable = load_asset_parts(path); budget = sp["budget_tris"][kind]
        # step 2: over budget ⇒ decimate ONCE, before fitting — never a --placed (designed) asset: decimation merged male v5's six hair parts
        # into one 698-tri lump and the gates then scored that instead (25/10); over-budget designed assets fail the final budget gate
        if len(asset.faces) > budget * 1.05 and not a.placed:
            lp = P(f"{kind}_lp.glb"); rc, log = blender(os.path.join(SHL, "lowpoly_blender.py"), path, lp, budget)
            if rc: print(log[-1500:]); sys.exit(1)
            asset, parts, movable = load_asset_parts(lp)
        faces_in = asset.faces.copy(); clr = sp["clearance_mm"][kind] / 1000
        if kind == "face":                                                  # brows etc. from eyebrow_fitter: already on the skin, never moved
            X = asset.vertices.copy(); Xr = X.copy(); disp = np.zeros_like(X); info = {"placed": True, "height_scale": 1.0}
        elif a.placed: X, info, Xr, disp = fit_placed(asset, body, kind, clr, movable)
        elif kind == "hair": X, info, Xr, disp = fit_hair(asset, body, clr, reference_hair(a.reference) if a.reference else None, a.hair_yaw)
        elif kind in ("lower", "upper"): X, info, Xr, disp = fit_garment(asset, body, kind, clr, yaw=a.yaw_outfit)
        else: X, info, Xr, disp = fit_rigid(asset, body, clr, body.skull_c)
        r = rest_report(kind, asset, X, Xr, disp, body); r["fit"] = info; r["source"] = path
        if kind == "upper":                                                 # arms: only clipping that is NOT hidden in the arm–torso contact counts
            dfull, _ = body.signed(X); vis = (dfull < -0.001) & ~body.hidden_in_arm_contact(X, dfull)
            r["arm_clipping_visible"] = {"verts": int(vis.sum()), "max_mm": round(float(-dfull[vis].min() * 1000), 1) if vis.any() else 0.0}
        r["topology_kept"] = bool(np.array_equal(faces_in, asset.faces) and len(X) == len(asset.vertices))
        name = "hair" if kind == "hair" else "hair_brows" if kind == "face" else f"outfit_{kind}"   # "hair*" ⇒ the rig pins it to the head
        rep["layers"][name] = r; fitted.append((name, kind, trimesh.Trimesh(X, asset.faces, process=False), parts))
        r["parts"] = [p_[0] for p_ in parts]; r["protected_verts"] = int((~movable).sum())
        st_ = r.get("see_through") or {}
        # never on a --placed (designed) asset: its coverage is the builder's job; an added tube broke the skirt budget and tore in the rig
        if kind == "lower" and st_.get("skin_visible_frac", 0) > G["see_through_max_frac"] and not a.no_lining and not a.placed:
            lin = make_lining(body, X)                                       # torn flaps leave skin showing ⇒ light lining underneath (spec)
            both = trimesh.util.concatenate([trimesh.Trimesh(X, asset.faces, process=False), lin])
            r["see_through_without_lining"] = st_; r["see_through"] = see_report("lower", both, both.vertices, body)
            r["lining_tris"] = int(len(lin.faces)); fitted.append(("outfit_lining", "lining", lin, None))
            print(f"  + lining {len(lin.faces)} tris: skin visible {st_['skin_visible_frac']*100:.1f} % → {r['see_through']['skin_visible_frac']*100:.1f} %")
        print(f"{name:14s} {len(asset.faces)} tris · penetrating {r['penetrating_verts']} · deepest {r['max_depth_mm']} mm · clearance {r['mean_clearance_mm']} mm · "
              f"face blocked {r['face_blocked']} · standoff {r['standoff']['median_mm']} mm · stretch p99 {r['deform']['edge_stretch_p99']} · failing {r['failing_regions']}")
    # step 5: assemble (one material per layer, game palette through the theme) → rig → poses
    sys.path.insert(0, os.path.join(SKILLS, "..", "theme")); import theme_colors as TC
    sc = trimesh.Scene(); b = body.mesh.copy()
    b.visual = trimesh.visual.TextureVisuals(material=trimesh.visual.material.PBRMaterial(name="M_skin", baseColorFactor=TC.mau(TC.DA["dat_am"]), roughnessFactor=0.5, metallicFactor=0.0))
    sc.add_geometry(b, geom_name="body", node_name="body")
    def part_mesh(m, vs, fs):
        return trimesh.Trimesh(m.vertices[vs], m.faces[fs] - vs.start, process=False)
    for name, kind, m, parts_ in fitted:
        plain = trimesh.visual.TextureVisuals(material=trimesh.visual.material.PBRMaterial(name=f"M_{name}", baseColorFactor=TC.mau(COLOURS[kind]), roughnessFactor=0.85, metallicFactor=0.0))
        if not parts_ or len(parts_) < 2:                                   # one-part asset (image→3D): game palette by kind
            m.visual = plain; sc.add_geometry(m, geom_name=name, node_name=name); continue
        for pn, vs, fs, vis in parts_:                                      # write fitted positions back PER ROLE PART, keeping its material
            pm = part_mesh(m, vs, fs); mat = getattr(vis, "material", None)
            pm.visual = trimesh.visual.TextureVisuals(material=mat) if mat is not None else plain
            sc.add_geometry(pm, geom_name=f"{name}__{pn}", node_name=f"{name}__{pn}")
    sc.export(P("dressed.glb"))
    rc, log = blender(os.path.join(SHL, "render_turnaround_blender.py"), P("dressed.glb"), P("rest"), "--keep-materials"); rep["preview"]["rest"] = P("rest")
    if not a.no_poses:
        rc, log = blender(os.path.join(SHL, "rig_body_blender.py"), P("dressed.glb"), P("rigged.glb"), P("rig_joints.json"))
        rep["rig_ok"] = rc == 0
        if rc: print(log[-2000:]); rep["gates"].append({"gate": "rig", "ok": False, "why": "rig_body_blender failed (stretch / unweighted)"})
        else:
            rc, log = blender(os.path.join(HERE, "pose_test_blender.py"), P("rigged.glb"), P("poses.json"), "--sheet", P("pose.png"))
            if rc: print(log[-2000:]); sys.exit(1)
            PT = json.load(open(P("poses.json"))); rep["preview"]["pose_frames"] = PT["frames"]
            for pose, layers in PT["poses"].items():
                rep["poses"][pose] = {}
                for lname, v in layers.items():
                    cand = [n for n, *_ in fitted if lname.startswith(n)]       # LONGEST prefix: "hair_brows" is not "hair"
                    key = max(cand, key=len) if cand else lname; kind = next((k for n, k, *_ in fitted if n == key), "hair")
                    pen = np.array(v["pen"]).reshape(-1, 4)
                    regs = (body.region_hair(pen[:, :3]) if kind == "hair" else body.region_garment(pen[:, :3])) if len(pen) else []
                    by = {}
                    for rg, dpt in zip(regs, pen[:, 3] if len(pen) else []): by.setdefault(rg, []).append(dpt)
                    prev = rep["poses"][pose].get(key)                   # a role-split layer has several parts: add them up
                    if prev:
                        v = {"penetrating": v["penetrating"] + prev["penetrating"], "verts": v["verts"] + prev["verts"],
                             "max_depth_mm": max(v["max_depth_mm"], prev["max_depth_mm"])}
                        for rg_, dd_ in prev["regions"].items(): by.setdefault(rg_, []).extend([dd_["max_mm"]] * dd_["verts"])
                    rep["poses"][pose][key] = {"penetrating": v["penetrating"], "verts": v["verts"], "frac": round(v["penetrating"] / max(v["verts"], 1), 4),
                                               "max_depth_mm": v["max_depth_mm"], "regions": {k: {"verts": len(d), "max_mm": round(max(d), 1)} for k, d in by.items()},
                                               "required": pose in sp["required_poses"].get(kind, [])}
    # step 6: gates
    def gate(name, ok, why): rep["gates"].append({"gate": name, "ok": bool(ok), "why": why})
    for name, kind, *_ in fitted:
        if name not in rep["layers"]: continue
        r = rep["layers"][name]
        gate(f"{name}: topology", r["topology_kept"], "faces / vertex count unchanged by fitting")
        if kind == "face": continue                                         # brows: gated by eyebrow_fitter itself (skin gap, buried, ridge, socket, symmetry)
        gate(f"{name}: rest clipping", r["max_depth_mm"] <= G["rest_max_depth_mm"], f"deepest {r['max_depth_mm']} mm (≤ {G['rest_max_depth_mm']})")
        gate(f"{name}: deform", r["deform"]["edge_stretch_p99"] <= 1.3, f"edge stretch p99 {r['deform']['edge_stretch_p99']}× (≤ 1.3); max {r['deform']['edge_stretch_max']}× reported")
        so = r["standoff"]["median_mm"]; so_max = G["standoff_max_mm"][kind]
        if kind == "lower":                                                 # a skirt hangs free over the thighs / between the legs: judge the snug band
            band = [v for k_, v in r["standoff"]["by_region_median_mm"].items() if k_ in ("waist", "back", "chest")]
            so = round(float(np.median(band)), 1) if band else so
        gate(f"{name}: size (not oversize)", so is not None and so <= so_max, f"inner surface stands {so} mm off the skin it covers (median{' of the waist band' if kind == 'lower' else ''}; ≤ {so_max}), p90 {r['standoff']['p90_mm']} mm, by region {r['standoff']['by_region_median_mm']}")
        if kind in ("lower", "upper"):
            st_ = r["see_through"] or {}
            gate(f"{name}: no skin showing", st_.get("skin_visible_frac", 1) <= G["see_through_max_frac"],
                 f"{st_.get('skin_visible_frac', 0)*100:.1f} % of the skin it must hide is visible (≤ {G['see_through_max_frac']*100:.0f} %): {st_.get('garment_under_skin')} garment-under-skin, {st_.get('holes')} holes in the asset, by region {st_.get('by_region')}")
            if kind == "upper":
                ac = r["arm_clipping_visible"]
                gate(f"{name}: no visible arm clipping", ac["verts"] == 0, f"{ac['verts']} verts inside the body outside the hidden arm–torso strip, deepest {ac['max_mm']} mm; the arm–torso contact strip is allowed (hidden)")
            hs = r["fit"].get("height_scale", 1.0)
            gate(f"{name}: asset shape fits the slot", 0.7 <= hs <= 1.4, f"height had to be scaled {hs}× to span its landmarks — outside 0.7–1.4 the asset is the wrong garment for this slot (remake it), not a fitting problem")
        bt = r.get("beard_thickness") or {}
        if kind == "hair" and bt.get("p90_mm") is not None and bt.get("verts", 0) > 20:
            gate(f"{name}: beard hugs the face", bt["p90_mm"] <= G["beard_thickness_max_mm"], f"beard stands {bt['p90_mm']:.0f} mm off the skin (p90 of {bt['verts']} beard verts; ≤ {G['beard_thickness_max_mm']})")
        bst = r.get("beard_see_through")
        if kind == "hair" and bst and G.get("beard_holes_gate_live"):           # report-only until calibrated on a known-good closed beard
            tot = sum(v_["holes"] for v_ in bst.values())
            gate(f"{name}: beard has no holes", tot <= G["beard_holes_max"], f"see-through rays inside the beard silhouette: {tot} ({', '.join(k_ + ' ' + str(v_['holes']) for k_, v_ in bst.items())}; ≤ {G['beard_holes_max']})")
        if kind == "hair" and (r["standoff"].get("beard") or {}).get("jaw_points_under_hair", 0) > 20:
            bd = r["standoff"]["beard"]
            gate(f"{name}: beard on the face", bd["median_mm"] <= G["beard_standoff_max_mm"], f"beard inner surface {bd['median_mm']} mm off the jaw/cheeks (median, p90 {bd['p90_mm']}; ≤ {G['beard_standoff_max_mm']})")
        if kind == "hair":
            if r["fit"].get("reference_mass_dir_deg") is not None:
                from fit_engine import angle_diff
                dd = angle_diff(r["fit"]["mass_dir_deg"], r["fit"]["reference_mass_dir_deg"])
                gate(f"{name}: hair mass behind the head", dd <= 60 or r["fit"]["mass_offset_cm"] <= 2, f"ponytail / main mass points {r['fit']['mass_dir_deg']}° ({r['fit']['mass_offset_cm']} cm off the skull centre), must be behind the head 180° ± 60 (0 = front, 90 = her left)")
            imb, tot = r["fit"]["face_side_imbalance"]
            gate(f"{name}: face-side hair balanced", tot <= 0.2 or imb <= 0.5, f"hair in front of the ears below the brow: left/right imbalance {imb:.2f} (≤ 0.5), mass {tot:.2f}")
            hf = r["hanging_in_front"]
            gate(f"{name}: long hair behind the ears", hf["frac"] <= G["hair_hanging_front_max_frac"], f"{hf['frac']*100:.0f} % of the free-hanging hair ({hf['free_verts']} verts > 4 cm off the skin, below the eyes) is in front of the ears (≤ {G['hair_hanging_front_max_frac']*100:.0f} %)")
            crit = [b for b in r["face_blocked"] if b.startswith(("eye", "nose"))]
            gate(f"{name}: face clear", not crit, f"eye/nose rays blocked by hair: {crit or 'none'}; mouth/cheeks (beard allowed): {[b for b in r['face_blocked'] if b not in crit] or 'none'}")
        for pose, v in rep["poses"].items():
            if name in v and v[name]["required"]:
                ok = v[name]["frac"] <= G["pose_max_penetrating_frac"] and v[name]["max_depth_mm"] <= G["pose_max_depth_mm"]
                gate(f"{name}: pose {pose}", ok, f"{v[name]['penetrating']} verts ({v[name]['frac']*100:.1f} %), deepest {v[name]['max_depth_mm']} mm, regions {list(v[name]['regions'])}")
    # FINAL ASSEMBLY budget by role, automatic lining included (Codex audit 25/10: the lining was appended after the budget check)
    tri = {"hair": 0, "brows": 0, "skirt": 0, "belt": 0, "stone": 0, "upper": 0}
    for name, kind, m, parts_ in fitted:
        if kind == "hair": tri["hair"] += len(m.faces)
        elif kind == "face": tri["brows"] += len(m.faces)
        elif kind == "upper": tri["upper"] += len(m.faces)
        elif kind in ("lower", "lining"):
            for pn, vs, fs, _ in (parts_ or [(name, None, slice(0, len(m.faces)), None)]):
                n_ = fs.stop - fs.start; k_ = "belt" if ("belt" in pn or "rope" in pn) else "stone" if ("stone" in pn or "ornament" in pn) else "skirt"
                tri[k_] += n_
    lim = {"hair": sp["budget_tris"]["hair"], "brows": 300, "skirt": 900, "belt": 150, "stone": 60, "upper": 450}; rep["final_tris"] = tri
    for k_, n_ in tri.items():
        if n_: gate(f"final budget {k_}", n_ <= lim[k_], f"{n_} tris in the delivered assembly (≤ {lim[k_]}), automatic additions included")
    # role parts + materials survive into the delivered GLB
    out = trimesh.load(P("dressed.glb"), force="scene"); names = set(out.geometry.keys())
    for name, kind, m, parts_ in fitted:
        if parts_ and len(parts_) >= 2:
            missing = [pn for pn, *_ in parts_ if f"{name}__{pn}" not in names]
            gate(f"{name}: role parts kept", not missing, f"{len(parts_) - len(missing)}/{len(parts_)} role parts with their own material in the delivered GLB" + (f"; missing {missing}" if missing else ""))
    rep["passed"] = all(g["ok"] for g in rep["gates"])
    json.dump(rep, open(P("fit_report.json"), "w"), indent=1, default=lambda o: o.tolist() if hasattr(o, "tolist") else str(o))
    md = [f"# Fitting report — {a.name} ({a.species})", "", f"**{'PASS' if rep['passed'] else 'FAIL'}** · body `{os.path.basename(a.body)}`", "",
          "| layer | tris | penetrating | deepest mm | standoff median / p90 mm | face blocked | stretch p99 / max | failing regions |", "|---|---|---|---|---|---|---|---|"]
    for n, r in rep["layers"].items():
        md.append(f"| {n} | {r['tris']} | {r['penetrating_verts']} | {r['max_depth_mm']} | {r['standoff']['median_mm']} / {r['standoff']['p90_mm']} | {', '.join(r['face_blocked']) or '—'} | "
                  f"{r['deform']['edge_stretch_p99']} / {r['deform']['edge_stretch_max']} | {', '.join(r['failing_regions']) or '—'} |")
    if rep["poses"]:
        md += ["", "| pose | " + " | ".join(n for n, *_ in fitted) + " |", "|---|" + "---|" * len(fitted)]
        for pose, v in rep["poses"].items():
            md.append(f"| {pose} | " + " | ".join((f"{v[n]['penetrating']} ({v[n]['max_depth_mm']} mm){'' if v[n]['required'] else ' ·report'}"
                                                    + (f" {', '.join(v[n]['regions'])}" if v[n]['regions'] else "")) if n in v else "—" for n, *_ in fitted) + " |")
    md += ["", "| gate | ok | why |", "|---|---|---|"] + [f"| {g['gate']} | {'✅' if g['ok'] else '⛔'} | {g['why']} |" for g in rep["gates"]]
    open(P("fit_report.md"), "w").write("\n".join(md) + "\n")
    print(("✅ FIT PASSED" if rep["passed"] else "⛔ FIT FAILED") + f" → {P('fit_report.md')}")
    for g in rep["gates"]:
        if not g["ok"]: print("  ⛔", g["gate"], "—", g["why"])
    sys.exit(0 if rep["passed"] else 1)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--species", default="humanoid"); ap.add_argument("--body", required=True); ap.add_argument("--joints", required=True)
    ap.add_argument("--anatomy"); ap.add_argument("--hair"); ap.add_argument("--reference", help="official-sheet character, coloured by role (hair size target)"); ap.add_argument("--outfit", action="append"); ap.add_argument("--out", required=True)
    ap.add_argument("--name", required=True); ap.add_argument("--no-poses", action="store_true"); ap.add_argument("--yaw-outfit", type=float, default=0.0)
    ap.add_argument("--hair-yaw", type=float, help="the hair asset's front, if it was NOT generated facing +Z")
    ap.add_argument("--no-lining", action="store_true", help="never add the lining tube under a see-through lower garment")
    ap.add_argument("--placed", action="store_true", help="assets are already built in place on this body: only clear clipping / squeeze, never re-place")
    main(ap.parse_args())

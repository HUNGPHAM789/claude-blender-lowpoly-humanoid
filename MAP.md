# LPM — map of the asset factory (25/10/2026)

Boss 25/10/2026: «gom về hết trong LPM … GameDev chủ yếu là game system và trỏ về LPM cho assets library và skills».
This repo = everything that MAKES game assets (specs, builders, gates, the asset library, animation skills).
`~/projects/GameDev` = the game system (engine, economy, scenes, animation production runs) and points here.

Old paths still work: every moved folder left a symlink behind
(`~/.hermes/skills/creative/<skill>` → `skills/<skill>`, `~/projects/GameDev/<dir>` → `<dir>` here).

## Folders

| folder | what | entry point |
|---|---|---|
| `/` (root) | LPM faceless low-poly origami humanoid (skill `low-poly-origami-character`), origami hair `hair_origami.py` | `lpm.py --out <dir>/<name> --gioi nam\|nu` |
| `lpd_detailed/` | LPD detailed humanoid with face + hair/outfit colours `hair_outfit.py` | `bash lpd_detailed/build.sh nam\|nu` |
| `humanoid_combined/` | combined humanoid draft (tiers rut_gon / chi_tiet) | `humanoid_combined/hm.py --tier …` |
| `lpms/` | asset engine (Kiln-style loop: render, edit, pairs, receipts) | `python3 lpms/lpms.py render\|edit\|pairs\|discover\|log` |
| `lpms_store/` | **asset library** — every built asset with its revisions `r_xxx` | read by `lpms.py` |
| `assets/aoe_starter_pack/` | world pack (mountain + waterfall v11, oak, storage tile, scale benchmark) | `build_mountain_waterfall_pack_v11.py` |
| `assets/organic/` | animals (deer_v1, rabbit_v1 + rigs; Quaternius CC0 sources) | skill `build-stylized-organic-model` |
| `assets/tools/` | settler hand tools renders + `settler_v1` | skill `humanoid-replaceable-assets` |
| `starter-pack/` | cave-age starter presets (humans, animals) + playable `game/index.html` | `starter-pack/README.md` |
| `miniature_kit/` | **MINIATURE STYLE (Boss 25/10, current standard)**: every world asset, the chibi settler and the animals built + animated IN CODE (three.js); `palette.js` only colour source, `toon.js` pieces/outline/x-ray, `nature.js` `props.js` `settler.js` `animals.js`; imported by GameDev/prototype as `@kit` | `specs/MINIATURE_STYLE_SPEC_V2.md` |
| `specs/` | **NATURE_SPEC_yukekbyte.md** — house spec for every new tree / rock-mineral / mountain / flower / mushroom / bush / storage (Boss 25/10); enforced by lpms gate «spec nature» | `specs/NATURE_SPEC_yukekbyte.md` |
| `theme/` | shared colour theme for all assets (`theme_colors.py`, `theme.json`) | env `THEME_MAU` |
| `skills/` | all asset + animation skills (below) | each `SKILL.md` |

## Skills (`skills/`, symlinked into `~/.hermes/skills/creative/`)

| skill | what |
|---|---|
| `humanoid-replaceable-assets` | hair, shoes, garments, hand tools (`tools.py`, `hair_outfit.py`), sockets |
| `low-poly-origami-detailed` / `low-poly-origami-simplified` | detailed / simplified humanoid with face |
| `procedural-low-poly-world` | terrain, mountains, water, world scale hierarchy |
| `lowpoly-grass` | grass + wind in vertex shader |
| `build-stylized-organic-model` | animals, trees, rocks (masses → marching cubes → decimate) |
| `settler-storage` | storage, baskets, straps |
| `humanoid-rig-animation` | `animate.py` / `humanoid_anim.py` retarget + gates, `motion_profile.json` |
| `settler-actions` | settler clip library (idle, walk, run, chop, carry…) |
| `quadruped-rig-animation` | 4-legged rigs, gaits, death |
| `las-physics` | falling / breaking (Bullet) |
| `stylized-lowpoly-humanoid` | muscular stylized primal adult m/f: Codex-cleaned sheet image → Hunyuan3D-2 (local) → align/decimate/measure on the mesh; drafts in `assets/characters/` |
| `character-fitter` | Universal Character Fitter: hair / outfit onto any base body (topology kept, rig weights copied, 10-pose test, Fitting Report, exit 1); species profiles (humanoid live, quadrupeds planned) |

## Stays in GameDev (not here)
- `anim_settler/` production runs + regression suite, `mocap_recovery/`, `kimodo/`, `hymotion/` (31 GB models), `grass/` research, `scenes/`, `zombie-rts/`.
- `assets/downloads/`, `assets/raw/` — third-party downloads (Sketchfab CC BY, CGTrader no-redistribution). ⛔ never copy in (licences forbid redistribution; repo is PRIVATE since 25/10/2026).

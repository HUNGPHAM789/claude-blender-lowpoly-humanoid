# LPM — asset factory for the Settler game — rules for Claude

Auto-loaded when a session opens in this folder. Boss 25/10/2026: «gom về hết trong LPM … GameDev chủ yếu là game system và trỏ về
LPM cho assets library và skills».

- **Map first:** [`MAP.md`](MAP.md) — every folder (humanoids, `lpms` engine, `lpms_store` asset library, world/animal/tool packs,
  `theme/`) and every skill in `skills/` (symlinked into `~/.hermes/skills/creative/`).
- **Game system lives elsewhere:** `~/projects/GameDev` (engine, economy, `anim_settler/` animation runs + regression suite).
  Its rules: `~/projects/GameDev/CLAUDE.md`, status `~/projects/GameDev/PROGRESS.md`. Anything that MAKES assets goes here, not there.
- **English names only** for every file, folder, function, flag (Boss 23–25/10, ledger #111). Remaining Vietnamese names:
  `python3 ~/bin/rename_to_english.py scan .` (rc=1 if any).
- **Private repo** (GitHub HUNGPHAM789/lpm-faceless-humanoid). ⛔ Never copy third-party downloads in (licences forbid redistribution);
  they stay in `GameDev/assets/downloads`, `assets/raw`.
- **Boss accepts by eye** (preview images/video), never by numbers — measure, decide, show.
- Commit + push after a change lands; keep `MAP.md` current when a folder or skill is added.

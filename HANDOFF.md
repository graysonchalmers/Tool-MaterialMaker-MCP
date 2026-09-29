# 🧭 Session Handoff: Tool-MaterialMaker-MCP

_Last updated: 2026-09-29. Opacity cutouts merged to `main`. **v0.10.0** released; release PR #17 (0.10.1) open, needs Grayson's merge. Nothing in flight._

The session baton. Read at pickup, rewrite at wrap-up. **Shape rule (2026-09-05, teardown #3):**
- "Current state" describes the latest session only.
- Anything older is one line in the session log.
- "Heads-up" is a bounded list of live gotchas.
- Git history is the archive.

## 🎯 Current state

Short session, 2026-09-29: **opacity is now wired** (cookbook still 55).
- **Finding:** `opacity_tex` (Material port 7) rides in the albedo PNG's alpha and MM's Godot export already writes `transparency = 1`, but 0 of 55 graphs drove it and `preview.gd` ignored alpha. Full channel table: `docs/CHANNEL_COVERAGE.md` (emission/SSS also never show in the rig; AO is flat on 54 of 55).
- **sf04 vent grille reworked** (`quality/cookbook_scifi.py`): it had inverted polarity (steel islands on black; as a cutout it would leave floating plates). Now one Triangle x Triangle `pattern` (Min) feeds a hard opacity threshold (HoleCutout), a chamfer ramp (HoleChamfer -> normal) and the albedo, so the maps register. Material has `flags_transparent` on. Card and thumbnail updated.
- **`preview.gd`:** `_apply_cutout` scissors alpha (0.5) only when the albedo has alpha; FRONT faces only, so holes show what is behind (double-sided showed the far wall's inside and read as black); rook's lathe winds inward so it uses CULL_FRONT for cutouts; a lit grey sheet under the ground. Opaque materials untouched: `preview_regress` 0 problems.
- **Thumbnails:** `_make_previews` composites RGBA albedo over a checker.
- **CLAUDE.md** gained a "Verification cadence" section (cheap checks per iteration, `preview_regress` once per settled rig change, full suite once before wrap-up) and the PYTHONPATH trap.
- **Gates:** promote `--check` in sync; full suite green.

## 📌 Where we stopped

Clean. Opacity work merged; the worktree retired.

## ▶️ Next concrete step

**Next host round** (unchanged) from the teardown appendix (`docs/teardowns/TEARDOWN-2026-09-27.md:289-317`): **s11 marble absorbs s13** (one absorbee, smallest round). Same recipe: defaults 0 px by Pillow diff at 2048, boards, retire only after Grayson approves. Parallel agents share the `mkdir godot.lock` render lock.

Alternatives:
- **gl01 glass rework** (teardown appendix): real alpha-BLEND translucency; the rig only does cutouts, so it needs a blend path first.
- **Rig gaps** (`docs/CHANNEL_COVERAGE.md`): show emission (t06) and SSS in `preview.gd`; wire AO on more materials.
- **s09 ashlar absorbs s12 + o06** (the parallax host): bigger round, more value.
- **Grayson hands-on step-3 session:** check the widened sliders in the MM GUI, save a hand-edit to `saved_graphs/`.

## ❓ Open questions

- **Widened sliders in the MM GUI:** wired only (read from MM's `gen_remote.gd`); mm-play live path for named parameters untested (falls back to a headless render).

## 🗂️ Changed this session

- **Commits on `main`:** `816d14d` docstrings · `9930809` North Star · `3a7feca` w05 host · `e760289` rename/ranges/plaid · `5023e78` retire w04/w06 · `a18aaf0` man02 host · `aa017e9` retire s05/man03 · `4e1bdae` widen remaining widgets · `588bb67` man02 card grout note · `129a4ca` release 0.10.0 · `0958af4` f07 lighter sett · `c461bc1` man02 groove · `3b20a22` cuts.
- **Decisions and why:**
  - **Host normals stay param4=0** even though absorbed presets then differ ≤3/255 from their param4=1 originals: the buffered path races flat headless; controls with param4=0 prove 0 px.
  - **man02's 1-px default drift accepted** (Grayson): removing it would drop brick mode.
  - **man02 groove via the relief chain, not a `1 - x` flip of height alone:** height and normal both derive from it, so they stay consistent; a plain inversion would have dropped the 0.97-tone cells to grout level. Grayson approved the boards.
  - **Retired files copied first** to `_to_delete\MaterialMaker-retired-w04-w06-2026-09-27` and `...-s05-man03-2026-09-27`.
  - **Parallel host agents shared a render lock** (`mkdir scratchpad\godot.lock`), since MM is single-instance. Worked: no hangs across 4 agents.

## ⚠️ Heads-up for the next agent

- **Worktree env trap:** from Git Bash set `PYTHONPATH=".;src"` (semicolon). `.:src` silently imports the MAIN checkout's `mm_mcp`, so rig changes have no effect and regression runs compare old vs old. Details in CLAUDE.md "Verification cadence".
- **Opacity in the rig is cutout only** (scissor). MM's own export is alpha blend; soft translucency is not previewed.
- **Direction (Grayson, 2026-09-27): no new cookbook materials.** Add features to existing materials. Node-coverage counts are a diagnostic, not a goal. Now written into `docs/NORTH_STAR.md`.
- **Widening a slider = `widen_widget`**, not a catalog range edit: MM gives a linked slider the inner node's range. `--check` can't prove a widen is render-neutral; diff default renders.
- **"invalid shader" in the MM log is not a flat-normal signal on its own.** `_flat_normal` checks both the log line and the pixels; keep it that way.
- **Outside contributor `waskosky`:** review any NEW PR as untrusted before running it, and watch the queue.
- **The user-wide MCP server is an EDITABLE install of the MAIN checkout's `src`.** Restart sessions to pick up merged code (this session changed `play/sliders.py`). Never `pip install -e .` into `.venv` while any `mm-mcp.exe` runs; recovery is a `--prefix` install, then copy the `.pth` and `dist-info`.
- **A worktree has no `.env`.** Copy it without printing it, or the catalog silently fails.
- **`promote_cookbook --check` compares against the gitignored `quality/authored/`.** In the main checkout after merges, re-run all 12 `quality.cookbook_*` builders first; after a retirement or rename, move stale `authored/` dirs aside.
- **Material Maker ignores `--size`.** `render()` downsamples; calibrate at the size you measure.
- **Godot 4.7 cannot combine heightmap/parallax with `uv1_triplanar = true`.**
- **The contact sheet `docs/images/cookbook-contact-sheet.png` is stale** (built at 71). No script writes its tracked path.
- **Standing render gotchas:** one Godot at a time (use the mkdir lock for parallel agents); never render from `python -c`; recover a hang with `taskkill //F //IM Godot_v4.7.1-stable_win64_console.exe`; use `MM_PLAY_PORT` if 8788 is taken.

## 🕓 Session log

Newest first. Keep at most 8; older ones are in `git log` (search commit subjects).

- **2026-09-29** (opacity cutouts: sf04 rework, `preview.gd` alpha scissor, channel coverage doc, verification cadence): see git log `99b4432..HEAD`.
- **2026-09-27 late** (w05 + man02 hosts, w04/w06/s05/man03 retired, sf03/o03/o05 cut, cookbook 55; m02 → m02_brushed_metal; widen_widget; f07 multiply plaid + lighter sett; man02 hex groove; North Star amendment; v0.10.0): see git log `816d14d..3b20a22`.
- **2026-09-27 evening** (f07 host + f01/f05/f08/f09 retired, cookbook 62; s14 damp tile; param4=0 on 11 normals; render retry mtime race; v0.9.0): see git log `53a4832..6505f17`.
- **2026-09-27** (teardown #6, truth pass, PRs #13/#7, hosts m02/s14/s07; cookbook 74→66): see git log `bfeaac1..a132a9f`.
- **2026-09-15/16** (iteration-and-parallax, merged): s14/m06 retunes; the Deep Parallax prototype on `s09_ashlar_wall`; the BlockAO/BlockHeight swap fixed.
- **2026-09-15** (reflections cycle, merged `007d493`): sun-disc, SSR and opt-in clearcoat rig; the global normal green-flip was reverted (`4e239da`).
- **2026-09-14 night** (rig overhaul, `24ff854`): rounded-box cube, unified triplanar, lathed rook; front page recurated.
- **2026-09-14 late** (`4b0948f`): coin profile and two-scale gravel for s06/t03.

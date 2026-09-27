# 🧭 Session Handoff: Tool-MaterialMaker-MCP

_Last updated: 2026-09-27 18:25 CDT. `main` @ `129a4ca` + wrap-up, pushed. Release PR #16 merged as **v0.10.0** (release job was queued at wrap-up). Nothing in flight._

The session baton. Read at pickup, rewrite at wrap-up. **Shape rule (2026-09-05, teardown #3):**
- "Current state" describes the latest session only.
- Anything older is one line in the session log.
- "Heads-up" is a bounded list of live gotchas.
- Git history is the archive.

## 🎯 Current state

Late-evening session, 2026-09-27 (four subagent worktrees, all merged, pushed, retired). **Cookbook 62 → 58.**
- **w05 wood host** absorbs w04 + w06: w04 is a preset (ramps only); w06's `SwirlField`+`BurlSwirl(warp2)` chained after `RingWarp` (either warp at 0 passes the other through). Exposed: Ring figure, Burl swirl (default 0), Burl size. Default 0 px; presets 0 px albedo/ORM, normal ≤3/255 (their param4=1 only; 0 px vs param4=0 controls). **w04, w06 retired.**
- **man02 tile host** absorbs s05 + man03: Layout switch (hex / skewed bricks), Tone switch (clean / per-cell stone via a twin stone-tone chain), Surface Grain (default off). Default: 1 normal px at 1/255 (NormalMix's presence; accepted by Grayson), else 0 px. man03 preset 0 px; s05 preset 0 px except normal ≤3/255 (its param4=1). **s05, man03 retired.** No param4=1 graph remains except o03 (an approved cut).
- **m02 renamed `m02_brushed_metal`** (byte-identical graph, no alias: `load_example("m02_brushed_aluminum")` is now not-found).
- **Slider ranges:** new `widen_widget` helper (`quality/author_helpers.py`) converts an exposed slider to a named parameter with its own range; `play/sliders.py` reads it. Applied to s07/s14/f07/man02/gl01/m02/m06/pm01/pm02/pm05/s02/s12/t03/l06; a test now asserts every shipped value is inside its range. All default renders 0 px before vs after.
- **f07 Plaid Overlay** now multiplies (blend_type 2). Defaults/presets 0 px; plaid on reads much darker (sett × tweed).
- **North Star** adopts "Library shape: depth over breadth" (`9930809`). t01/s09 stale docstrings fixed.
- **Gates:** promote `--check` in sync; fast suite 1187; CI green on `588bb67`.

## 📌 Where we stopped

Clean. Every branch merged, every session worktree retired, v0.10.0 release PR merged.

## ▶️ Next concrete step

**Execute the three approved cuts** from the teardown appendix (`docs/teardowns/TEARDOWN-2026-09-27.md:289-317`): sf03 circuit board, o03 tree bark (it is also the LAST param4=1 graph), o05 coral. Copy to `_to_delete\` first, `git rm`, drop builders, fix cross-refs, recount README/STATUS. Cheap and needs no boards.

Alternatives:
- **Next host round:** s11 marble absorbs s13 (one absorbee, small), or s09 ashlar absorbs s12 + o06. Same recipe: defaults 0 px by Pillow diff at 2048, boards, retire only after Grayson approves.
- **Grayson hands-on step-3 session:** open a host in MM, check the widened sliders show in the GUI (only headless-verified), save a hand-edit to `saved_graphs/`.

## ❓ Open questions

- **man02 hex grout is a raised ridge** (measured: grout height ~208 vs faces ~88, height and normal agree; brick mode has recessed mortar). Invert the hex relief so grout recesses? Changes the hex normal too, needs boards.
- **f07 plaid under multiply reads dark.** Retune the sett to lighter colours?
- **Widened sliders in the MM GUI:** wired only (read from MM's `gen_remote.gd`); mm-play live path for named parameters untested (falls back to a headless render).

## 🗂️ Changed this session

- **Commits on `main`:** `816d14d` docstrings · `9930809` North Star · `3a7feca` w05 host · `e760289` rename/ranges/plaid · `5023e78` retire w04/w06 · `a18aaf0` man02 host · `aa017e9` retire s05/man03 · `4e1bdae` widen remaining widgets · `588bb67` man02 card grout note · `129a4ca` release 0.10.0.
- **Decisions and why:**
  - **Host normals stay param4=0** even though absorbed presets then differ ≤3/255 from their param4=1 originals: the buffered path races flat headless; controls with param4=0 prove 0 px.
  - **man02's 1-px default drift accepted** (Grayson): removing it would drop brick mode.
  - **man02 heightmap NOT flipped:** flipping height alone would contradict the normal. Card corrected instead; inversion is an open question.
  - **Retired files copied first** to `_to_delete\MaterialMaker-retired-w04-w06-2026-09-27` and `...-s05-man03-2026-09-27`.
  - **Parallel host agents shared a render lock** (`mkdir scratchpad\godot.lock`), since MM is single-instance. Worked: no hangs across 4 agents.

## ⚠️ Heads-up for the next agent

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

- **2026-09-27 late** (w05 + man02 hosts, w04/w06/s05/man03 retired, cookbook 58; m02 → m02_brushed_metal; widen_widget; f07 multiply plaid; North Star amendment; v0.10.0): see git log `816d14d..129a4ca`.
- **2026-09-27 evening** (f07 host + f01/f05/f08/f09 retired, cookbook 62; s14 damp tile; param4=0 on 11 normals; render retry mtime race; v0.9.0): see git log `53a4832..6505f17`.
- **2026-09-27** (teardown #6, truth pass, PRs #13/#7, hosts m02/s14/s07; cookbook 74→66): see git log `bfeaac1..a132a9f`.
- **2026-09-15/16** (iteration-and-parallax, merged): s14/m06 retunes; the Deep Parallax prototype on `s09_ashlar_wall`; the BlockAO/BlockHeight swap fixed.
- **2026-09-15** (reflections cycle, merged `007d493`): sun-disc, SSR and opt-in clearcoat rig; the global normal green-flip was reverted (`4e239da`).
- **2026-09-14 night** (rig overhaul, `24ff854`): rounded-box cube, unified triplanar, lathed rook; front page recurated.
- **2026-09-14 late** (`4b0948f`): coin profile and two-scale gravel for s06/t03.
- **2026-09-14 evening** (merged): `normal_albedo_audit.py` and `_make_showcase.py`; 5 normal-registration fixes.

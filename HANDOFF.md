# 🧭 Session Handoff: Tool-MaterialMaker-MCP

_Last updated: 2026-09-14 (preview lighting rig overhaul: soft distance
shadows, boosted shadow-casting rim, sky bounce, SSAO, precession-default
sweep; merged to `main` `6ce84c6`, NOT pushed) CT (America/Chicago)_

The session baton. Read at pickup, rewrite at wrap-up. **Shape rule (2026-09-05,
teardown #3):** "Current state" describes the latest session only; anything
older is one line in the session log. "Heads-up" is a bounded list of live
gotchas (drop an entry once a mechanism makes it moot). Git history is the
archive; there is no separate archive file.

## 🎯 Current state

**The `render_preview` 3D lighting rig was overhauled and merged to `main`
(`6ce84c6`, not pushed).** A long live visual-iteration session with Grayson:
prototyped every lighting option in a throwaway scratchpad Godot project
(`scratchpad/preview_variant/` + an interactive slider lab `scratchpad/lighting_lab/`,
run via `lab.bat`), sending rendered PNG/GIF comparisons each pass, and only
touched production once the look was approved. Final rig in
`src/mm_mcp/preview_project/preview.gd`:

- **Key** gets a distance-based soft shadow (`light_angular_distance = 5.0`,
  `SHADOW_QUALITY_SOFT_ULTRA`): crisp at the object base, blurring as it falls
  away.
- **Rim/kick** boosted 0.55 -> 2.0, repositioned behind `(-20,-150,0)`, and it
  DELIBERATELY casts a soft shadow (`light_angular_distance = 4.0`) -- that cast
  is load-bearing, it blocks the rim's own spill from washing out the SSAO
  contact grounding. Do NOT "fix" it to non-casting (a code comment says so).
- **Fill:** new low cool bounce directional (0.35).
- **Env:** procedural-sky ambient + reflections (never drawn, dark backdrop
  kept) replaces the flat constant ambient -- this is the soft bounce AND the
  fix for metals reading dead-black. Plus SSAO for crisp contacts.
- **`render_preview_sweep`** default sweep changed from the azimuth 360 orbit
  (its backlit third read dark) to a **precession**: the key stays aimed at the
  object, its aim traces a small cone (default 18 deg, rim/fill held still), so
  highlights circle the relief without going backlit. `sweep_kind="azimuth"`
  still reachable; `cone` tunable. New `sweep_kind`/`cone` params plumbed through
  `preview.py` and the `server.py` tool wrapper.

TDD on the two test changes; fast suite 1112 passed, preview integration 4
passed (the motion test now exercises precession and still clears its >3.0
per-frame movement floor, verified empirically). Verified end-to-end:
cobblestone matches Grayson's approved pick, out-of-category frosted glass
renders clean through the production rig, final GIF generated via the real
`render_preview_sweep` tool.

**The planned "regenerate 65 cookbook previews" step turned out unnecessary.**
The tracked `docs/images/cookbook-*/*.png` thumbnails are flat ALBEDO downscales
(`quality/_make_previews.py`), not lit 3D renders. The lit rig is only used by
the on-demand `render_preview` / `render_preview_sweep` MCP tools, whose output
is never committed. So the lighting change touches nothing tracked and needs no
regeneration; commit `6ce84c6` is the whole feature.

## 📌 Where we stopped

Feature complete and merged to `main` (`6ce84c6`, fast-forward from the branch
`claude/godot-lighting-improvements-d0efc9`). **Not pushed** (Grayson said merge,
not push). The scratchpad prototype + slider lab are untracked, still on disk.

## ▶️ Next concrete step

Push `main` if wanted (`git push`; then confirm `git rev-list --left-right
--count origin/main...HEAD` reads `0  0`). Alternatives: promote the throwaway
slider lab (`scratchpad/lighting_lab/`) to a real repo dev tool if it'll be
reused; or move on to the queued noise-vocabulary round 3 (plan committed
`75571b6`, its own worktree `noise-vocabulary-round-3` exists and is locked).

## ❓ Open questions

- PyPI vs GitHub-clone-only (leaning GitHub-only); macOS/Linux never run.
  release-please will open the next PR on the pushed commits.
- NORTH_STAR treats UE4's export path as a lesser tier; never confirmed.
- Whether `project-setup` should register MCP servers user-wide is open.
- Two parked overlay-builder findings (2026-08-28): no rollback if `copytree`
  fails partway; staleness check hashes only the addon.
- `m01_weathered_copper` ships without a normal map (content gap surfaced by
  the render baseline).
- Promote the interactive lighting slider lab to a tracked dev tool, or leave
  it as throwaway scratchpad? (Grayson to decide.)

## ⚠️ Heads-up for the next agent

- **The preview rig's rim light CASTS a shadow on purpose** (it restores contact
  grounding under objects by blocking its own spill). There is a code comment
  saying so in `preview.gd`; do not "fix" it to the usual non-casting rim.
- **Tracked cookbook thumbnails are flat ALBEDO downscales, not lit 3D renders**
  (`docs/images/cookbook-*/*.png` via `quality/_make_previews.py`). A change to
  the `render_preview` lighting rig touches nothing tracked and needs NO
  thumbnail regeneration -- do not plan one.
- **Godot launcher hangs** when the console binary is run through a raw bash pipe
  (`... | grep`) or with a GDScript parse error (no pipe EOF / scene never loads
  -> `get_tree().quit` never fires, idles to timeout). Redirect output to a file
  (`> log 2>&1`) and run `--check-only --script` before rendering. `var x := a
  and b` where `b` is a Variant comparison fails GDScript type inference;
  annotate `var x: bool = ...`.
- **An out-of-range enum INDEX is now a hard `error`** (was a warning), so it
  fails `test_cookbook_gate` and makes `render_tracked` SKIP that graph. Latent
  only: the cookbook has zero out-of-range enums today.
- **Buffer/compute-shader nodes do NOT render headless** under `--export-material`
  (`shader_compile_spirv_from_source` on null -> all-black). Use
  `directional_warp`/`warp2` for distortion instead.
- **`truchet` output is a smooth distance field, range ~0.5-0.95** (not 0/1).
  Threshold/gradient INSIDE that range; diagnose any unknown node's real range
  with `quality/pngread.py` on its swatch before tuning against it.
- **Controller render tools for material self-screen:** `python -m
  quality.render_one <label> <case> [size]` renders the promoted flat maps
  (absolute paths, ~10-30s at 512), then MCP `render_preview` composites the 3D
  preview. One Godot at a time.
- **Run quality scripts as `python -m quality.<module>` from the repo root**
  (`pip install -e .` prerequisite). Never launch a Godot render from `python
  -c`. **Pass `render()` an absolute `outdir`** (relative -> GUI opens -> 180s
  timeout, empty log).
- **Subagents lose long Godot runs.** Run `render_tracked` per category; stone
  and terrain compares take 6 to 9 minutes. Tell implementers to poll the output
  file rather than return.
- **In the Git Bash tool, `taskkill /F` is rewritten to `F:/`.** Use `taskkill
  //F //IM Godot_v4.7.1-stable_win64_console.exe` (and the GUI exe). Recovery
  from a stuck/orphaned Godot = kill both exes, then re-render clean.
- **Every Claude Code session spawns its own `mm-mcp.exe`** (user-scope
  registration); a server idle for `MM_IDLE_EXIT_MINUTES` (120) exits and is not
  auto-restarted (reconnect via `/mcp`). The install is EDITABLE, so on-disk
  source == what the server imports; a code change only needs a restart of a
  server that was already running, never a reinstall.
- **A `blend` shows port-1 where its port-2 mask is 0 and port-0 where it is 1**;
  put the majority layer on port-1. Opacity = amount x mask. `normal_map`
  `param4=0` is the flat-normal fix. Voronoi output port 2 is the per-cell
  random source. **Verify metallic/roughness/AO fixes by reading the exported
  ORM channel** (`quality/pngread.py`), not by eye.
- **Node names never affect renders** (MM seeds from node position); a rename
  pass is render-identical. Never rename a subgraph node (`mm-play` slider ids).
- **Edit cookbook materials by changing the builder and re-promoting**, never the
  tracked `.ptex` by hand; `promote_cookbook --check` flags both (compares
  against gitignored `quality/authored/`, so regenerate the category first).
  Godot is not byte-deterministic: a re-render of an unchanged graph once
  measured 21.89 mean abs diff -- a single compare failure is a rerender first, a
  regression second.
- **Bumping the Material Maker pin** means `MM_UPSTREAM_PIN` in
  `src/mm_mcp/__init__.py` AND `MM_PIN` in `.github/workflows/test.yml`, then the
  local checkout, then regenerate every category and `--check`.
- **`.mcp.json` and `.env` are gitignored; never echo `.env`.**
- **A second Claude session may be active on this machine and its `Push-Repo`
  runs `git add -A`** (it has swept this session's commons log into its own
  commit before). `git fetch` and re-read before editing shared files; search
  the commons by filename, not `git log --grep`.

## 🕓 Session log

Newest first. Keep at most 8 entries; older ones are in `git log` (search the
commit subjects, every session ends with a `docs:` wrap-up commit).

### 2026-09-14 (preview lighting overhaul, MERGED `6ce84c6`, NOT pushed): `pickup` on the lighting worktree; a long live visual-iteration session (advisor-guided, no formal brainstorm per the "show me options" ask). Prototyped soft-shadow/bounce/AO/precession options in a throwaway scratchpad Godot project + an interactive slider lab (`lab.bat`), sending PNG/GIF comparisons each pass; Grayson converged over ~10 rounds to: soft distance key shadow (angular 5.0), boosted rim (2.0) casting a soft shadow (load-bearing for contact grounding), cool bounce fill, procedural-sky ambient+reflections (fixes dark metals), SSAO contacts, and a precession-default sweep (cone 18, rim still). Landed into production `preview.gd` + `preview.py` + `server.py` + `tests/test_preview.py` (TDD on the sweep-flag tests; motion test now exercises precession, clears its floor empirically). Fast suite 1112, preview integration 4. The planned 65-preview regen was found MOOT (tracked thumbnails are flat albedo, not lit renders). Merged `--ff-only` to `main`. Gotchas hit: Godot launcher hangs on raw-pipe/parse-error (redirect to file, `--check-only` first); `var x := a and b` Variant-inference failure.
### 2026-09-14 (pickup, render_preview_sweep verified): ran the sweep tool for real through the live MCP tool surface (`render_graph` on cookbook's `f01_woven_denim`, piped into `render_preview_sweep`), sent Grayson the resulting GIF, he confirmed it read fine. Promoted `render_preview_sweep` 🔌 -> ✅ in STATUS.md. (This session's precession overhaul supersedes the sweep's default behavior.)
### 2026-09-14 (noise-vocabulary round 2, MERGED to `main`): `pickup` resumed at Task 5's pending approval; `subagent-driven-development` drove Tasks 5-11 to completion (cookbook 59 -> 65 across 12 categories, README/AUTHORING count integration). Task 8 found + parked a real pre-existing bug (shared `wood` donor bleeds GrainMask into Material's metallic port, w04/w05/w06); a follow-up session fixed w04/w05, then w06 was fixed on this round's branch before merging. Merged with HANDOFF.md's session log hand-reconciled.
### 2026-09-14 (rotating-key-light preview mode, `render_preview_sweep`, MERGED `58e35ab`): brainstorming -> TDD. `preview.gd` azimuth sweep mode (one Godot process, N frames, 360 key-light rotation) + `render_preview_sweep()` (Pillow GIF assembly, runtime dep) + 11th MCP tool. Advisor review caught a thin test and the verified/wired state mismatch; added a real frames-differ assertion, measured a real brightness curve. Merged same session.
### 2026-09-13 (enum-index validation enforcement, MERGED to main): `pickup`; the hole was ENFORCEMENT (out-of-range enum was a `warning`). Fix: out-of-range enum index -> `error` with an intended-index hint; ratchet test. TDD red->green, fast suite 1039->1045. A sibling branch fixing the same thing was folded in.
### 2026-09-13 (noise/distortion vocabulary + core toolbox, MERGED `0169446`): `subagent-driven-development`, all 14 tasks. Shipped 6 proof materials on unused bases (cookbook 53->59), 19 diagnostic swatches, README "Core toolbox" section, AUTHORING distortion note. Fast suite 1039.
### 2026-09-06 (backup-ops wake-lock, cross-project): root-caused the 09-05 nightly truncation as idle-sleep mid-run; added a `SetThreadExecutionState` wake-lock to `backup-ops\Backup-All.ps1`. Commit `f7e809d`. No MM-MCP code changed.
### 2026-09-06 (idle-exit watchdog): `MM_IDLE_EXIT_MINUTES` opt-in idle exit, 17/17 tools touch it; merged `--no-ff` as `f669f8c`, suite 989; registration set to 120. (Older entries: see `git log`.)

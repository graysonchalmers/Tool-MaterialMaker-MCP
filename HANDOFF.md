# 🧭 Session Handoff: Tool-MaterialMaker-MCP

_Last updated: 2026-09-14 18:51 CT (America/Chicago) -- the round-3 follow-up
(`task_73027cd8`) landed on `claude/nervous-mahavira-e778a5`, pushed. `main`
itself is also now confirmed pushed (a concurrent session fast-forwarded it
mid-session; the prior "not pushed" note below was stale the moment it was
written)._

The session baton. Read at pickup, rewrite at wrap-up. **Shape rule (2026-09-05,
teardown #3):** "Current state" describes the latest session only; anything
older is one line in the session log. "Heads-up" is a bounded list of live
gotchas (drop an entry once a mechanism makes it moot). Git history is the
archive; there is no separate archive file.

## 🎯 Current state

**The `task_73027cd8` follow-up (compound-node param `default` accuracy) is
fixed, tested, and pushed** on branch `claude/nervous-mahavira-e778a5`
(commit `948a8e7`), not yet merged to `main` or opened as a PR. Round 3 and
the preview lighting overhaul (prior session, detailed in the log below)
are already on `main`, which this session confirmed is itself pushed.

Bug: `_parse_generic_node` in `catalog_builder.py` sourced a resolved
compound param's `default` from whichever inner node its widget's
`linked_widgets` pointed at (e.g. `crystal.param0` resolved against
`voronoi.scale_x`, default 4) instead of the compound node's own
`remote`/`gen_parameters` block, which declares the real default (16 for
`crystal`). This is only reproducible on top of round-3's type-referenced-
link resolution (`aca9939`/`60e2700`), which at session start was still
sitting on the unmerged `worktree-noise-vocabulary-round-3` branch, not
`main` -- the very first RED attempt against plain `main` came back
`None == 16` (unreproducible) rather than `4 == 16`; merging round-3's
branch in locally was required to reproduce it at all. Mid-session, a
concurrent session/Grayson fast-forwarded `main`/`origin/main` to include
round-3, so the branch was rebuilt as one clean commit on top of the
now-current `main` rather than carrying a redundant merge commit.

Fix: prefer the remote node's own `parameters[pname]` for `default` when
present, sourced from the raw file data (not catalog state) so the
existing fixpoint-resolution pass stays idempotent/order-independent.
Also corrected `normal_map.param1`'s pinned test default (was asserting
the inner `edge_detect_1.amount` default of 0.5; the real default, from
`normal_map`'s own remote node, is 1) -- same bug, different node. Added a
`clouds_noise`-based regression test verified (against a copy of the
pre-fix file) to genuinely fail `None == 0` without the fix. Fast suite:
1165 passed, zero regressions.

## 📌 Where we stopped

Fix is committed (`948a8e7`) and pushed to
`origin/claude/nervous-mahavira-e778a5`. Not merged to `main`, no PR
opened yet. `main`/`origin/main` confirmed in sync at `825c9fa`.

## ▶️ Next concrete step

Open a PR for `claude/nervous-mahavira-e778a5` (or have Grayson merge it
directly) to land the `task_73027cd8` fix on `main`. Alternatives, either
of which Grayson can pick up instead:
- Promote the interactive lighting slider lab (`scratchpad/lighting_lab/`) to a tracked dev tool, or leave it as throwaway scratchpad.
- Audit the broader compound-default flaw class beyond the two nodes tested here (crystal, normal_map, clouds_noise) -- not exhaustively checked.

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
- `f11_corduroy`'s underlying `directional_noise` field is genuinely more
  irregular than real corduroy's evenly-spaced wales (measured, disclosed
  in its recipe card); it was chosen as the best of the node's three
  internal modes, not a claim of a photo-real corduroy read. Revisit if a
  future session finds a way to regularize the banding further.
- `task_73027cd8` (catalog `default`-field accuracy) is fixed this session
  but not yet merged to `main` -- open a PR / merge `claude/nervous-mahavira-e778a5`.
  The broader 44/61-parameter compound-default flaw class beyond the two
  nodes tested (crystal, normal_map, clouds_noise) has not been audited
  exhaustively; may be worth a follow-up sweep.

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
- **A compound (`graph`-type) node's exposed numeric parameter can be a
  `named_parameter` widget** (min/max/step/default live directly on the widget,
  no `linked_widgets` at all -- `directional_noise.n_scale`, `dirt.d_scale`) OR
  a `linked_control` widget chasing an inner node that may itself be a plain
  TYPE REFERENCE (not an inline `shader_model`) needing a full-catalog lookup,
  possibly through another compound node (`catalog_builder.py`'s `build_catalog`
  now does a bounded fixpoint pass for this, fixed 2026-09-14). If a new
  material's exposed slider ever fails `test_play_sliders.py` with "missing
  numeric range," check which of these two widget shapes it is before assuming
  the node just lacks catalog data. The resolved parameter's `default` field
  now comes from the remote node's own `parameters` block, not the linked
  inner node -- fixed 2026-09-14 (`task_73027cd8`, commit `948a8e7`).
- **A compositing node like `splatter` needs a real pattern wired into its
  input** (its `in` port has a literal `"0.0"` shader default, so leaving it
  unconnected renders blank) -- retype the from-scratch skeleton's placeholder
  generator to a `shape` node instead of the true target, `add_node` the real
  compositing node, wire shape-output into its `in` port, then `rewire()` the
  skeleton's downstream albedo/normal chain onto the compositing node's output.
  `shape`'s own bare `radius=1` default fills the whole tile, which some
  compositing nodes (like `splatter`) treat as one giant instance rather than a
  small discrete one -- shrink the shape's radius and check with an isolated
  render before trusting a "reasonable-sounding" default.
- **Material authoring flow, refined in round 3:** implementer authors builder +
  validates + registers in `BUILDERS` ONLY, plus any isolated single-node
  verification renders needed to pick between a compound node's internal modes
  or confirm a gradient's histogram (this IS in scope for the implementer -- it's
  a technical check, not the approval gate); the implementer never runs the full
  `render_preview` composite, writes the recipe card, or runs `promote_cookbook`.
  Controller renders all materials, self-screens for gross misses and variety
  collisions, batches them into one `SendUserFile`, waits for Grayson's real
  approval, then writes the recipe cards and runs `promote_cookbook` per
  category -- only the controller has the chat channel for approval. A "new
  base" material can still drift into an existing look (t09 clay -> voronoi
  plates; s12 -> wood; round 3's corduroy read as wood-grain) so actively
  differentiate and flag it in the self-screen even if you ship anyway.
- **An out-of-range enum INDEX is now a hard `error`** (was a warning), so it
  fails `test_cookbook_gate` and makes `render_tracked` SKIP that graph. Latent
  only: the cookbook has zero out-of-range enums today.
- **Buffer/compute-shader nodes do NOT render headless** under `--export-material`
  (`shader_compile_spirv_from_source` on null -> all-black). Use
  `directional_warp`/`warp2` for distortion instead.
- **`truchet` output is a smooth distance field, range ~0.5-0.95** (not 0/1).
  Threshold/gradient INSIDE that range; diagnose any unknown node's real range
  with `quality/pngread.py` on its swatch before tuning against it.
- **The 3D preview scene can render METALS dark** depending on the lighting
  variant in play; judge metals by the pattern/relief, or read the ORM, rather
  than by overall brightness.
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

### 2026-09-14 (`task_73027cd8` catalog default-field fix, pushed, not yet merged): dispatched task with an exact fix location and a pre-diagnosed bug. First RED attempt against plain `main` came back unreproducible (`None == 16`, not `4 == 16`) because the bug only exists once round-3's type-referenced-link resolution is present, and round-3 was still sitting on its own unmerged worktree branch -- merged `worktree-noise-vocabulary-round-3` in locally to reproduce it for real (confirmed via `advisor`). Fix: `_parse_generic_node` now prefers the remote node's own `parameters[pname]` for `default` over the linked inner node's. Corrected `normal_map.param1`'s pinned test default (0.5 -> 1, same bug). Added a `clouds_noise`-based test empirically verified (against a pre-fix copy of the file) to fail without the change. Mid-session a concurrent session fast-forwarded `main`/`origin/main` to include round-3, so rebuilt the branch as one clean commit (`948a8e7`) on the new `main` instead of carrying a redundant merge. Fast suite 1165 passed. Pushed `origin/claude/nervous-mahavira-e778a5`; not merged to `main`, no PR yet.
### 2026-09-14 (noise-vocabulary round 3 + catalog fix, MERGED to `main`): `pickup` -> `writing-plans` -> `subagent-driven-development` for a 6-material round Grayson approved (scope-corrected before dispatch: `custom_tiles` swapped for `skewed_bricks`). Refined the implementer/controller split: implementer authors + validates + isolated verification renders only; controller renders all six, self-screens, batches one `SendUserFile`, gets Grayson's real approval before writing cards/promoting. All 6 materials + 2 README/AUTHORING tasks landed, only Task 2 (`f11_corduroy`) needed a fix round (an overstated "clean ribbing" claim caught by the task reviewer). Task 8 surfaced a real pre-existing `catalog_builder.py` bug (compound-node param range resolution) fixed as its own TDD'd task, itself needing one fix round (a fixpoint loop replacing an order-dependent two-pass sweep). Final whole-branch review (opus) came back "ready to merge with fixes": one fix wave (a fabricated-numbers card fix matching Task 2's own error class, catalog dead-code cleanup, an aliasing fix, a card tidy), re-reviewed clean. One finding spawned as a follow-up instead of fixed (`task_73027cd8`: catalog default-field accuracy for 17 params). Cookbook 65 -> 71 materials, 12 categories. Merged `main` into this branch first (a concurrent session had landed `6ce84c6`/`6051eed` on `main` after this branch forked), hand-reconciling HANDOFF.md/STATUS.md conflicts; then merged this branch into `main`. Full suite 1161+ passed throughout.
### 2026-09-14 (preview lighting overhaul, MERGED `6ce84c6`, NOT pushed): `pickup` on the lighting worktree; a long live visual-iteration session (advisor-guided). Prototyped soft-shadow/bounce/AO/precession options in a throwaway scratchpad Godot project + an interactive slider lab (`lab.bat`), sending PNG/GIF comparisons each pass; Grayson converged over ~10 rounds to: soft distance key shadow (angular 5.0), boosted rim (2.0) casting a soft shadow (load-bearing for contact grounding), cool bounce fill, procedural-sky ambient+reflections (fixes dark metals), SSAO contacts, and a precession-default sweep (cone 18, rim still). Landed into production `preview.gd` + `preview.py` + `server.py` + `tests/test_preview.py`. Fast suite 1112, preview integration 4. The planned 65-preview regen was found MOOT (tracked thumbnails are flat albedo, not lit renders). Merged `--ff-only` to `main`. Gotchas hit: Godot launcher hangs on raw-pipe/parse-error; `var x := a and b` Variant-inference failure.
### 2026-09-14 (pickup, render_preview_sweep verified): ran the sweep tool for real through the live MCP tool surface (`render_graph` on cookbook's `f01_woven_denim`, piped into `render_preview_sweep`), sent Grayson the resulting GIF, he confirmed it read fine. Promoted `render_preview_sweep` 🔌 -> ✅ in STATUS.md.
### 2026-09-14 (noise-vocabulary round 2, MERGED to `main`): `pickup` resumed at Task 5's pending approval; `subagent-driven-development` drove Tasks 5-11 to completion (cookbook 59 -> 65 across 12 categories, README/AUTHORING count integration). Task 8 found + parked a real pre-existing bug (shared `wood` donor bleeds GrainMask into Material's metallic port, w04/w05/w06); a follow-up session fixed w04/w05, then w06 was fixed on this round's branch before merging. Merged with HANDOFF.md's session log hand-reconciled.
### 2026-09-14 (rotating-key-light preview mode, `render_preview_sweep`, MERGED `58e35ab`): brainstorming -> TDD. `preview.gd` azimuth sweep mode (one Godot process, N frames, 360 key-light rotation) + `render_preview_sweep()` (Pillow GIF assembly, runtime dep) + 11th MCP tool. Advisor review caught a thin test and the verified/wired state mismatch; added a real frames-differ assertion, measured a real brightness curve. Merged same session.
### 2026-09-13 (enum-index validation enforcement, MERGED to main): `pickup`; the hole was ENFORCEMENT (out-of-range enum was a `warning`). Fix: out-of-range enum index -> `error` with an intended-index hint; ratchet test. TDD red->green, fast suite 1039->1045. A sibling branch fixing the same thing was folded in.
### 2026-09-13 (noise/distortion vocabulary + core toolbox, MERGED `0169446`): `subagent-driven-development`, all 14 tasks. Shipped 6 proof materials on unused bases (cookbook 53->59), 19 diagnostic swatches, README "Core toolbox" section, AUTHORING distortion note. Fast suite 1039.

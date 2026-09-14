# 🧭 Session Handoff: Tool-MaterialMaker-MCP

_Last updated: 2026-09-14 (two sessions landed today: the rotating-key-light
preview mode `render_preview_sweep` merged via `58e35ab`, then the
noise-vocabulary round-2 expansion's 11 tasks merged to `main`, both
pushed) CT (America/Chicago)_

The session baton. Read at pickup, rewrite at wrap-up. **Shape rule (2026-09-05,
teardown #3):** "Current state" describes the latest session only; anything
older is one line in the session log. "Heads-up" is a bounded list of live
gotchas (drop an entry once a mechanism makes it moot). Git history is the
archive; there is no separate archive file.

## 🎯 Current state

**Two sessions landed on `main` today.** First, the optional rotating-key-light
preview mode Grayson asked to have noted as a follow-up (2026-09-13,
noise-vocabulary-round-2 kickoff session: reviewing f09_plaid_flannel's
static preview, he couldn't judge relief/bump depth from one fixed light
angle). New `render_preview_sweep()` tool:

- `preview_project/preview.gd` gained a second output mode alongside the
  existing static one, same sphere/cube/cutaway/ground rig either way:
  `--sweep-outdir=<dir> --sweep-frames=<N>` sweeps the key light through a
  full 360-degree azimuth rotation (rim light fixed), writing `frame_NNN.png`
  per step, all inside ONE Godot process -- a fresh process per frame would
  pay the project-load cost N times over, and one process trivially respects
  the one-Godot-at-a-time constraint.
- `src/mm_mcp/preview.py`: `render_preview_sweep()` runs it, then Pillow
  stitches the frames into a looping GIF (`_frames_to_gif`); frame dir cleaned
  up on success, left in place on failure for debugging. New `PreviewSweepResult`
  dataclass. Pillow is now a real runtime dependency (`pyproject.toml`,
  `requirements.txt`) -- previously dev-only for `quality/_make_previews.py`.
- Registered as an 11th MCP batch tool (`server.py`, mirrors `render_preview`'s
  wrapper: same path-bounding, same error-as-data shape).
- TDD: unit tests for `_build_sweep_command` and `_frames_to_gif` (the GIF
  assembly is pure and tested with synthetic PNGs, no Godot needed) written
  first, watched RED (ImportError), then implementation, then GREEN. Added a
  discriminating integration test after advisor review: frame-count + valid-GIF
  alone don't prove the light moved, so `test_render_preview_sweep_light_actually_moves_between_frames`
  asserts adjacent/opposite frames differ by a real pixel-diff floor. Proved the
  test has teeth by dropping the per-step settle-frame wait to 0 (real RED --
  Pillow's GIF encoder deduplicated the now-identical frames down below the
  requested count) before settling on 6 waits per step (matches the static
  path's own settle count; cost is negligible inside one process).
- Sampled real per-frame brightness across a 24-frame sweep (`f01_woven_denim`):
  66 (front-lit) down to 40 (backlit, roughly a third of the sweep), not black.
  Expected for a single rotating key light against a fixed camera -- ambient +
  rim keep the backlit stretch from going dead, but relief reads weaker there
  than in the static preview's front-lit frame. Not adjusted (e.g. restricting
  the arc) without Grayson's read first, since a full 360 circle was the literal
  ask.
- Ran it via direct Python calls and real Godot renders (not through the MCP
  tool surface at the time) and sent Grayson the GIF. Per this project's own
  convention (see `mm-play`'s history), that is 🔌 wired, not ✅ verified,
  until Grayson runs it himself; STATUS.md reflects that. Full suite (fast +
  integration) 1083 passed / 1 known live-overlay flake (passes alone).
  README/STATUS batch-tool counts bumped 10 -> 11. Merged to `main` via
  `58e35ab`, pushed. Fast suite re-verified green on `main` post-merge (1051
  passed / 33 deselected). Branch `claude/vigorous-kepler-8c0148` can be
  deleted, local and remote, when convenient.

Second, and most recently: **round 2 of the noise-vocabulary expansion,
now MERGED to `main`.** This session
resumed at Task 5's pending approval (the prior session had paused mid-task
awaiting Grayson's reply) and drove `subagent-driven-development` through
to the end of the plan: Tasks 5-11 all complete, reviewed clean, and
committed. Plan at
`docs/superpowers/plans/2026-09-13-noise-vocabulary-round-2.md`, SDD ledger
at `.superpowers/sdd/2026-09-13-noise-vocabulary-round-2/progress.md` (the
authoritative task-by-task record).

Landed and reviewed clean this session:
- **Task 5** `f10_boucle_upholstery` (fbm Cellular 5, fabrics): Grayson
  approved the carried-over preview with no iteration ("go"); resumed from
  the prior session's WIP checkpoint (`a3728df`) to finish the recipe card,
  promote, and gates as a new commit `094da06`.
- **Task 6** `sf05_circuit_maze_panel` (truchet Line, scifi): truchet's
  real output range measured fresh (0.498-1.000, thresholded at the
  statistical midpoint 0.73-0.77) rather than assumed from the Circle-mode
  precedent; approved first pass, committed `d5f0319`.
- **Task 7** `gl03_shattered_crystal` (shard_fbm pushed crystalline, glass):
  two shard_fbm-specific gotchas fixed (single output port vs the donor's
  port-1 wire; its broad-bell field needed an S-curve, not the gl01/gl02
  near-zero threshold convention); approved first pass, committed `27f824f`.
- **Task 8** `w06_burled_wood` (warp2 burl figure, wood): donor's dead
  voronoi ring chain removed, low-freq perlin displacement + `warp2`
  (mode 0, amount 0.65) for swirling knotted burl, visually distinct from
  w05's straight grain; approved first pass, committed `f4fe79e`. Review
  found a real bug (below, parked, not fixed in this task).
- **Task 9** README material counts 59 -> 65 + regenerated contact sheet,
  committed `75a7d4f`.
- **Task 10** AUTHORING.md names all six round-2 materials and refreshes the
  live coverage line 13 -> 14 of 52 (only `shard_fbm` is a genuinely new
  node type this round), committed `af3e687`.
- **Task 11** (this wrap): fast suite 1103 passed, `promote_cookbook --check`
  and `naming --cookbook` both clean, em-dash scan of the six new recipe
  cards + README + AUTHORING.md clean (AUTHORING.md's two pre-existing
  em dashes at lines 48/65 are legacy, out of this round's scope per Task
  10's reviewer), HANDOFF/STATUS updated, wrap-up commit made.

All six materials this round got a rendered 3D preview sent to Grayson via
SendUserFile and his live "go" approval before being finished (matching
round 1's pattern); none needed an iteration this round (unlike Task 4's
relief fix, done in the prior session before the pause). Cookbook is now 65
materials across 12 categories, up from 59 at the start of round 2.

**One finding was deliberately parked at Task 8's review, then closed before
merge.** Task 8 found the shared `wood` donor (used by w04, w05, and the new
w06) wires its GrainMask blend straight into Material's metallic port,
producing a spatially-varying metallic channel (~0.04-0.58) instead of
near-zero, identical and pre-existing in already-shipped w04/w05. Fixing
only w06 there would have left w04/w05 inconsistent, so it was ruled out of
Task 8's scope and a follow-up was spawned (`task_21359777`). That follow-up
ran in a separate session and landed on its own branch
(`claude/heuristic-bhaskara-551ae1`, commit `a984312`), fixing w04/w05 on
`main`. Before merging this branch, the identical fix was applied to w06
here too (commit `0997d6d`, verified via the exported ORM's metallic
channel reading flat 0, not by eye), so all three wood materials are
consistent and the issue is fully closed, not just deferred.

Both sessions are now merged to `main`: all 11 round-2 tasks landed with
clean per-task reviews, full suite and cookbook gates green, the
wood-metallic fix applied on top before merging, and the sweep-preview
feature merged earlier the same day.

## 📌 Where we stopped

Nothing in flight. Both features are on `main` and pushed: `noise-vocabulary-round-2`
merged with Grayson's explicit go-ahead (`--no-ff`, this file's own conflict
hand-resolved rather than taken from one side). Fast suite re-verified green
on the merged result (1110 passed), `promote_cookbook --check` and
`naming --cookbook` (65/65) both clean. The three now-merged branches
(`claude/vigorous-kepler-8c0148`, `claude/heuristic-bhaskara-551ae1`,
`noise-vocabulary-round-2`) are deleted, local and remote (the first had
no remote ref left to delete, already cleaned up earlier).

## ▶️ Next concrete step

No pressing next step queued; pick up general project work. If looking for
one: Grayson running `render_preview_sweep` himself through the live MCP
tool surface (see Open questions) is the one still-open loose end from
today's two sessions.

## ❓ Open questions

- PyPI vs GitHub-clone-only (leaning GitHub-only); macOS/Linux never run.
  release-please will open the next PR on the pushed commits.
- NORTH_STAR treats UE4's export path as a lesser tier; never confirmed.
- `.mcp.json` question resolved in practice: user-scope registration is the
  wiring; `.mcp.json` stays for this repo's own dev sessions. Whether
  `project-setup` should register MCP servers user-wide is open.
- Two parked overlay-builder findings (2026-08-28): no rollback if `copytree`
  fails partway; staleness check hashes only the addon.
- `m01_weathered_copper` ships without a normal map (content gap surfaced by
  the render baseline).
- `render_preview_sweep`'s sweep tuning (frame count 18, 80ms/frame, 6
  settle-frames per step) is a first guess, confirmed on one material
  (`f01_woven_denim`) so far -- revisit if the GIF reads too choppy/slow
  once Grayson has used it on a few more.

## ⚠️ Heads-up for the next agent

- **An out-of-range enum INDEX is now a hard `error`** (was a warning), so it
  fails `test_cookbook_gate` and makes `render_tracked` SKIP that graph (records
  a problem) instead of rendering-with-warning. Latent only: the cookbook has
  zero out-of-range enums today. `validate` names the intended index when the
  bad value matches a known literal (via the new catalog `value_literals`).
  A string-stored literal (`"-3"`) is still skipped by the
  `isinstance(pval,(int,float))` guard: deliberately left, t09's value was an int.
- **Buffer/compute-shader nodes do NOT render headless** under `--export-material`
  (`shader_compile_spirv_from_source` on null -> all-black). This kills
  `slope_blur` and the whole `warp_dilation` family for cookbook materials even
  though they validate. `normal_map` only survives because its `switch` bypasses
  its internal buffer when `param4=0`. Use `directional_warp`/`warp2` for
  distortion instead (they render).
- **`truchet` output is a smooth distance field, range ~0.5-0.95** (not 0/1),
  shaped like interlocking tubes. Threshold/gradient INSIDE that range, and feed
  the raw field into `normal_map` for rounded tube relief. Diagnose any unknown
  node's real value range by rendering its noise-gallery/debug swatch and
  sampling with `quality/pngread.py` before tuning a builder against it.
- **The 3D preview scene renders METALS dark** (dark environment, metals reflect
  it). m01/m02/m03 all look dark with bright highlights; that is the scene, not a
  broken material. Judge metals by the pattern/relief, or read the ORM.
- **Controller render tools for material self-screen:** `python -m
  quality.render_one <label> <case> [size]` renders the promoted flat maps to
  `quality/cookbook/<label>/<case>/` (absolute paths, ~10-30s at 512), then the
  MCP `render_preview` tool (or `quality/_make_previews`) composites the 3D
  sphere/cube preview. One Godot at a time. (The old `scratchpad/preview_material.py`
  was a per-session scratch file and does not persist.)
- **Material authoring flow (this plan):** implementer authors builder + validates
  + promotes (NO Godot); controller renders + self-screens for gross misses and
  variety collisions, then Grayson is the visual judge. A "new base" material can
  still drift into an existing look (t09 clay -> voronoi plates; s12 -> wood) so
  actively differentiate.
- **The 2026-09-05 nightly backup truncation is FIXED (2026-09-06).** The cause
  was NOT the `git diff HEAD --binary` `NativeCommandError` at
  `Backup.Common.ps1:229` (that is a benign CRLF warning already handled by the
  EAP relax at lines 217-232). The powershell process was idle-slept mid-run
  before the top-level `finally { Stop-Transcript }`. `Backup-All.ps1` now holds
  a `SetThreadExecutionState(ES_SYSTEM_REQUIRED)` wake-lock for the run's
  duration (commit `f7e809d`, push pending). The true truncation signature is a
  missing `transcript end` footer, not the git error. A forced sleep (lid close)
  or `StopIfGoingOnBatteries` can still truncate, far more rarely.
- **Run quality scripts as `python -m quality.<module>` from the repo root**
  (`pip install -e .` is a prerequisite; running from inside `quality/`
  breaks `.env` lookup). Never launch a Godot render from `python -c`.
  Renders are one Godot at a time.
- **Pass `render()` an absolute `outdir`.** Godot runs with the Material Maker
  checkout as its cwd, so a relative outdir is never found, Material Maker
  opens its GUI instead, and the render idles to the 180 s timeout with an
  empty log (cost two implementer runs on 2026-09-06).
  `quality/render_tracked.py` resolves its own paths; `src/mm_mcp/render.py`
  still accepts a relative one.
- **Subagents lose long Godot runs.** Run `render_tracked` per category; the
  stone and terrain compares take 6 to 9 minutes because `quality/pngread.py`
  decodes 2048x2048 normal maps in pure Python. Tell implementers to poll the
  output file rather than return. One re-render of an unchanged graph once
  measured 21.89 mean abs diff and 0.0 on two reruns: a single compare
  failure is a rerender first, a regression second.
- **In the Git Bash tool, `taskkill /F` is rewritten to `F:/`.** Use
  `taskkill //F //IM Godot_v4.7.1-stable_win64_console.exe` (and the GUI exe).
- **Every Claude Code session on this machine spawns its own `mm-mcp.exe`**
  (user-scope registration). Since `f669f8c` a server with no tool call for
  `MM_IDLE_EXIT_MINUTES` (120 in Grayson's registration) closes its live
  session and exits on its own. Claude Code does NOT restart an exited stdio
  server: a tab idle for two hours loses its Material Maker tools until it
  reconnects (`/mcp`) or the session restarts. Servers started before the
  change keep running without the timer.
- **Node names never affect renders** (Material Maker seeds from node
  position), so a rename pass is render-identical by construction; add
  materials through a builder that ends with `rename_nodes(g, {...})` after
  grouping, and never rename a subgraph node (`mm-play` slider ids).
- **Edit cookbook materials by changing the builder and re-promoting**, never
  the tracked `.ptex` or the generated card table by hand;
  `promote_cookbook --check` flags both. `--check` compares against the
  gitignored `quality/authored/`, so regenerate the category first. Godot is
  not byte-deterministic: do not regenerate thumbnails for a name-only change.
- **`group_into_subgraph` fails silently on a mistyped member name.**
- **A `blend` shows port-1 where its port-2 mask is 0 and port-0 where it is 1**;
  put the majority layer on port-1. Opacity = amount x mask. `normal_map`
  `param4=0` is the flat-normal fix. Voronoi output port 2 is the per-cell
  random source.
- **Verify metallic/roughness/AO fixes by reading the exported ORM channel**
  (`quality/pngread.py`), not by eye.
- **`take_variant(builder, label, keep_n)`** returns one variant and deletes
  the files it wrote; the caller re-saves as v1.
- **Bumping the Material Maker pin** means `MM_UPSTREAM_PIN` in
  `src/mm_mcp/__init__.py` AND `MM_PIN` in `.github/workflows/test.yml`,
  then the local checkout, then regenerate every category and `--check`.
- **Stale mm-play on 8788 is a startup error with the PID.**
- **The SPIRV `SCRIPT ERROR` at `parse_args.gd:59` prints on every successful
  export.** Red herring.
- **`ambientcg.com` redirected to scareware (2026-09-03).** Use Wikimedia.
- **Donors load from `quality/donors/`** (tracked); vendor new donors there.
- **release-please has `bump-minor-pre-major: true`**; do not remove it.
- **`.mcp.json` and `.env` are gitignored; never echo `.env`.** The user-scope
  registration in `~/.claude.json` carries the same paths.
- **A second Claude session is active on this machine and its `Push-Repo`
  runs `git add -A`.** On 2026-09-06 it swept this session's untracked
  `_agent-commons` log into its own commit (`f94c240`, subject "vibecheck
  s102...") and pushed it. Content is intact, but the log is not findable by
  commit subject: search the commons by filename, not `git log --grep`. It
  also committed a `docs:` correction (`868d16a`) to THIS file. `git fetch`
  and re-read before editing shared files.
- **The user-scope `mm-mcp.exe` is an EDITABLE install** (`pip show mm-mcp` ->
  `Editable project location: C:\Projects-local\Tool-MaterialMaker-MCP`), so
  on-disk source == what the server imports; no reinstall is ever needed for a
  code change. Only a server process already running from BEFORE a change holds
  stale code in memory. Fix = restart that process (idle-exit retires it, or
  `/mcp` reconnect, or session restart), not `pip install`. Verified 2026-09-06:
  the `577592f` subgraph-descent fix is live in the MCP `validate` tool this
  session (probe returned `where: sub1/inner`).

## 🕓 Session log

Newest first. Keep at most 8 entries; older ones are in `git log` (search the
commit subjects, every session ends with a `docs:` wrap-up commit).

### 2026-09-14 (pickup, render_preview_sweep verified): ran the sweep tool for real through the live MCP tool surface (`render_graph` on cookbook's `f01_woven_denim`, piped into `render_preview_sweep`), sent Grayson the resulting GIF, he confirmed it read fine. Promoted `render_preview_sweep` 🔌 -> ✅ in STATUS.md, dropped the now-resolved open question from this file. Kicking off round 3 of the noise-vocabulary expansion next.
### 2026-09-14 (noise-vocabulary round 2, MERGED to `main`): `pickup` resumed at Task 5's pending approval (prior session paused mid-task). Grayson approved four previews with no iterations needed this session (f10_boucle_upholstery, carried over from the paused prior session, plus sf05_circuit_maze_panel, gl03_shattered_crystal, and w06_burled_wood) before `subagent-driven-development` drove Tasks 5-11 through to completion: cookbook 59 -> 65 materials across 12 categories, README/AUTHORING count integration, and a wrap commit. A final whole-branch review (opus) came back "ready to merge with fixes": one fix wave landed an AUTHORING.md clarity clause, a `_NOISE_PATTERN_NODES` catalog-subset guard test plus the missing `directional_noise` entry (52 -> 53), a softened w06 docstring, and two baton nits, all re-reviewed clean. Task 8's review had also found and parked a real pre-existing bug (the shared `wood` donor bleeds GrainMask into Material's metallic port, identical in w04/w05/w06) with a spawned follow-up (`task_21359777`); before merging, that follow-up's own session landed a fix for w04/w05 on a separate branch (`claude/heuristic-bhaskara-551ae1`), which was merged to `main` first, then the identical fix was applied to w06 on this branch (verified via the ORM's metallic channel, flat 0) so the issue closed fully rather than half-fixed. Merged to `main` with Grayson's explicit go-ahead, HANDOFF.md's conflicting session-log entries hand-reconciled (both this session and the same-day `render_preview_sweep` session's entries preserved) rather than resolved naively.
### 2026-09-14 (rotating-key-light preview mode, `render_preview_sweep`, MERGED `58e35ab`, still 🔌 not ✅ pending Grayson's own run): brainstorming (bounded path) -> TDD. Follow-up from the noise-vocabulary-round-2 session (f09_plaid_flannel's static preview couldn't show relief depth). `preview.gd` sweep mode (one Godot process, N frames, full 360-degree key-light rotation) + `render_preview_sweep()` (Pillow GIF assembly, now a runtime dep) + 11th MCP tool. Advisor review caught a thin test (frame count alone doesn't prove the light moved) and the verified/wired state mismatch (implementer-run, not Grayson-run); added a real frames-differ assertion (proved it has teeth by watching it catch settle=0) and measured a real brightness curve (66 front-lit -> 40 backlit across a 24-frame sweep, not black -- flagged for Grayson, not silently fixed). Sent Grayson the GIF (`f01_woven_denim`); he confirmed it looked fine. Full suite 1083 passed / 1 known live-overlay flake (passes alone). Committed, pushed, merged to `main` same session.
### 2026-09-14 (noise-vocabulary round 2 kickoff, IN PROGRESS): `pickup` answered Grayson's two questions (README current, tool usage still shallow: 9 of the catalog's noise/warp bases in use across 59 materials), brainstorm -> `writing-plans` -> `subagent-driven-development` for a round-2 scope Grayson approved (6 more materials + a reusable `quality/node_usage_audit.py` audit script). Phase A landed clean (13/52 curated noise nodes now live-tracked). `l07_pebbled_leather` and `f09_plaid_flannel` landed and approved (f09 took one relief-strength iteration on Grayson's feedback). Caught and corrected a dispatch bug mid-session: an implementer subagent was wrongly told to SendUserFile-and-wait-for-approval itself, when only the controller session has a live chat channel to Grayson; fixed for all subsequent material dispatches. Session ended mid-Task-5 (`f10_boucle_upholstery`): preview sent, no reply yet, builder committed as an explicit WIP checkpoint (`a3728df`) so nothing is lost. Grayson also asked about a rotating-light preview GIF; deferred to a spawn_task follow-up rather than scope-creeping this round. Tasks 6-11 not started.
### 2026-09-13 (enum-index validation enforcement, MERGED to main): `pickup` (caught baton drift: noise branch already merged `0169446`/pushed, baton said unmerged), Grayson picked the deferred enum follow-up. Advisor-prompted investigation flipped the premise: detection already worked (`validate_graph` flags t09's `type=-3` int, even in-subgraph); the hole was ENFORCEMENT (out-of-range enum was a `warning`, all gates filter to errors / promote never validates). Fix: out-of-range enum index -> `error`; message explains the clamp and either names the intended index via `_enum_literal_hint` (literal match) or lists all valid options; `catalog_builder` captures `value_literals` for numeric index-mismatched enums only; ratchet test in `test_cookbook_gate`. Wrap-up surfaced a sibling branch `claude/zealous-ritchie-cb051a` (2 commits, unmerged) fixing the same thing as a warning-with-options-list; Grayson said reconcile, so its options-list message + wavelet range-pin test were folded into this branch (sibling now superseded). TDD red->green, fast suite 1039->1045. Ruled out: string-literal guard hole (left; t09 was int) and the stale gitignored `catalog/catalog.json` artifact (not a bug). Commons log written.
### 2026-09-13 (noise/distortion vocabulary + core toolbox, MERGED `0169446` + pushed): `pickup` -> `subagent-driven-development` resumed at Task 8, finished the plan (all 14 tasks, per-task + final opus review clean). Shipped 6 proof materials on unused bases (s13 marble/fbm, m03 titanium/anisotropic, sf07 conduit/truchet, s12 sandstone/directional_warp, t09 wet sand/wavelet, gl02 cut gem/voronoi_triangle; cookbook 53->59), 19 diagnostic swatches, README un-collapse + count-gated "Core toolbox" section, AUTHORING distortion note. Fast suite 1039; final fix `4905d37` (gl02 card node count). Merged next session; a follow-up t09 enum fix `4d1187f` landed post-merge.
### 2026-09-06 (backup-ops wake-lock, cross-project): `pickup` here, Grayson picked next-step #2. Root-caused the 09-05 nightly truncation as idle-sleep mid-run (the git `NativeCommandError` is a handled CRLF warning; true signature is a missing `transcript end` footer, not a code bug), and added a `SetThreadExecutionState` wake-lock to `backup-ops\Backup-All.ps1` (acquire in try, release in finally). Verified compile + parse; commit `f7e809d` local, PUSH PENDING (ssh-agent not loaded this session). Commons log written. No MM-MCP code changed.
### 2026-09-06 (idle-exit watchdog): `MM_IDLE_EXIT_MINUTES` opt-in idle exit, 17/17 tools touch it, live session closed on exit; review found and fixed the two untouched tools and the atexit skip; merged `--no-ff` as `f669f8c`, suite 989; registration set to 120.
### 2026-09-06 (validate subgraph descent + crate round-trip prep)
- `pickup`; Grayson picked options 1 + 2 ("automate most of 1 for me").
- Option 2 TDD: `validate_graph` recurses into subgraph nodes, inner
  problems path-prefixed; 5 new tests; `577592f` pushed. Closes the prior
  session's dogfooding bug.
- Option 1: Unity crate wiring verified from disk; 3D preview rendered and
  sent. Hand-edit left to Grayson (use-session one).
- Full suite 993 passed / 1 flake (live-overlay test, Godot contention;
  passes alone). A concurrent session's `Push-Repo` swept this session's
  commons log into its `f94c240` and pushed it. (Older entries: see
  `git log`, search commit subjects, every session ends with a `docs:`
  wrap-up commit.)

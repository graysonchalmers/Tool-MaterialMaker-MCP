# 🧭 Session Handoff: Tool-MaterialMaker-MCP

_Last updated: 2026-09-14 (noise-vocabulary round 3: six more cookbook
materials, all Grayson-approved, plus a real catalog_builder infra fix
found along the way, on branch `worktree-noise-vocabulary-round-3`,
final whole-branch review pending) CT (America/Chicago)_

The session baton. Read at pickup, rewrite at wrap-up. **Shape rule (2026-09-05,
teardown #3):** "Current state" describes the latest session only; anything
older is one line in the session log. "Heads-up" is a bounded list of live
gotchas (drop an entry once a mechanism makes it moot). Git history is the
archive; there is no separate archive file.

## 🎯 Current state

**Round 3 of the noise-vocabulary expansion, on branch
`worktree-noise-vocabulary-round-3`, ready for final review.** Started
from a `pickup` that verified `render_preview_sweep` for real (see prior
session, below) and answered "what's next?" by kicking off round 3.
`subagent-driven-development` drove all 6 material tasks plus the 2
README/AUTHORING integration tasks through to completion; every task
reviewed clean on the first pass except Task 2 (one fix round). Plan at
`docs/superpowers/plans/2026-09-14-noise-vocabulary-round-3.md`, SDD
ledger at `.superpowers/sdd/2026-09-14-noise-vocabulary-round-3/progress.md`.

**Scope correction found during planning, before any code was written:**
the originally-discussed sixth target, `custom_tiles`, needs an
`sdf2d`-typed shape input that only the out-of-scope SDF family can
produce (verified via `describe_node`). Swapped for `skewed_bricks`
(all three inputs are genuinely optional `f` maps, so it works
standalone) before Task 6 was ever dispatched.

Six materials landed, one per unused catalog node, each authored by an
implementer (builder + validate + isolated verification render only,
no full preview/promote) then rendered, self-screened, and sent to
Grayson as a batch by the controller (only the controller has the chat
channel for approval):

- **Task 1** `m04_scratched_steel` (`scratches`, metal): discrete
  layered scratch marks, distinct from `m02`/`m03`'s continuous brushed
  streaks. Reviewed clean, no fix round. Commit `fb436af`.
- **Task 2** `f11_corduroy` (`directional_noise`, fabrics): the one
  task needing a fix round. First pass claimed the retyped node's
  render showed "clean parallel ribbing" when the pixels actually
  showed irregular anisotropic streaking -- caught by the task reviewer
  opening the actual PNG. Fix rendered and compared all three internal
  modes with a measured band-regularity metric (coefficient of
  variation) rather than trusting the first render; kept mode 0 as
  genuinely the best of three, with the docstring rewritten to describe
  the real pixels, not an idealized look. Commits `d029c7e`, `41d1b36`.
- **Task 3** `t10_packed_dirt` (`dirt`, terrain): a new irregular
  blotchy-patch topology this category never had. Implementer's own
  self-review (with advisor) caught a gradient-stop/histogram mismatch
  before it ever reached task review and fixed it in the same commit.
  Reviewed clean. Commit `fef670e`.
- **Task 4** `gl04_raw_crystal_cluster` (`crystal`, glass): a fourth
  glass topology (two-voronoi composite reading as a raw crystal
  cluster), distinct from the category's existing crack-network/
  faceted/fracture-field siblings. Reviewed clean. Commit `9638930`.
- **Task 5** `pm06_splatter_finish` (`splatter`, painted-metal): the
  only task needing real multi-node wiring rather than a bare retype
  (`splatter` needs a real pattern feeding its `in` port, so a `shape`
  node is spliced in front of it). The brief's literal `shape` defaults
  produced 3-4 tile-filling overlapping blobs; diagnosed against
  `splatter.mmg`'s actual shader and fixed by shrinking the shape's
  radius. Reviewed clean, wiring independently re-verified against the
  saved graph's actual connections. Commit `40ea494`.
- **Task 6** `man03_mosaic_tile` (`skewed_bricks`, ceramic): per-tile
  positional jitter distinguishes it from `man02`'s perfectly regular
  hex grid. Reused `man02`'s face-vs-grout roughness-inversion
  technique rather than a flat roughness constant. Reviewed clean.
  Commit `1c15120`.

All six got a rendered 3D preview batched into one `SendUserFile` and
Grayson's live "approved" with zero iteration requested (including the
corduroy one the controller's self-screen specifically flagged as
reading more like wood grain than fabric). Recipe cards written,
`promote_cookbook` run per category, `promote_cookbook --check` and
`naming --cookbook` both clean at 71/71. Cookbook is now 71 materials
across 12 categories, up from 65. Commit `0e14c4d`.

**A real, pre-existing infra bug surfaced during Task 8, unrelated to
any of the six materials' own correctness, fixed as its own dispatched
task.** Running the full suite for the first time after promotion (no
earlier task had reason to) surfaced 3 `test_play_sliders.py` failures:
`f11_corduroy`, `gl04_raw_crystal_cluster`, and `t10_packed_dirt` all
came back "missing numeric range" on an exposed slider. Root cause,
diagnosed directly: `src/mm_mcp/catalog_builder.py::_resolve_widget_range`
had two real gaps that this round's compound-node retype choices were
simply the first to exercise -- it required `linked_widgets` to exist at
all (missing the `named_parameter`-style widgets `directional_noise.n_scale`
and `dirt.d_scale` use, which carry their own min/max directly), and it
only followed a link to an inner node with an INLINE `shader_model`
(missing `crystal.param0`/`param1`'s links to plain TYPE-REFERENCE nodes
like `voronoi`). Dispatched as its own fix task with full TDD. First
pass (commit `aca9939`) fixed both gaps but introduced a subtler one:
its two-pass `build_catalog` restructuring ran pass 2 as a single sweep,
which is order-dependent for a compound node linking to ANOTHER compound
node that itself only resolves in pass 2 -- the opus reviewer reproduced
this concretely (`binary_smooth.smooth` -> `fast_blur.param1` resolves
differently under forward vs. reversed glob order) and prototyped the
fix. One fix round (commit `60e2700`) replaced the single sweep with a
bounded fixpoint loop (converges in 2-3 rounds against a cap of 10,
warns loudly rather than silently half-resolving if the cap is hit),
plus a committed order-independence regression test exercising the real
compound-to-compound chain. Re-review independently re-derived the old
buggy behavior from scratch to confirm the fix's necessity, then
confirmed the fix's entire blast radius is exactly the one entry that
was actually broken. Full suite 1161 passed, zero regressions. Three
Minor findings (a hardcoded `"type": "float"` on the named_parameter
path, a shallow-copy aliasing risk on an enum's `values` list, dead
`full_catalog` parameter plumbing) deferred to the final whole-branch
review, not required for this fix.

## 📌 Where we stopped

All 8 plan tasks plus the unplanned catalog fix task are complete and
reviewed clean (Task 2 and the catalog fix each took one fix round; every
other task passed review on the first try). Full suite 1161 passed,
`promote_cookbook --check` and `naming --cookbook` both clean (71/71).
Still on the isolated worktree branch (`worktree-noise-vocabulary-round-3`)
-- the final whole-branch review (`superpowers:requesting-code-review`,
most capable model) has not run yet, so this has not merged to `main` or
pushed. The three deferred Minor findings from the catalog fix's review
are queued for that final review to triage.

## ▶️ Next concrete step

Run the final whole-branch review on `worktree-noise-vocabulary-round-3`
against its merge-base with `main`, address any findings in one fix wave,
then `superpowers:finishing-a-development-branch` to merge and push. No
other pressing next step queued after that.

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
- `f11_corduroy`'s underlying `directional_noise` field is genuinely more
  irregular than real corduroy's evenly-spaced wales (measured, disclosed
  in its recipe card); it was chosen as the best of the node's three
  internal modes, not a claim of a photo-real corduroy read. Revisit if a
  future session finds a way to regularize the banding further.
- Three Minor findings deferred from the catalog_builder fix's review,
  queued for the final whole-branch review to triage: a hardcoded
  `"type": "float"` on the `named_parameter` resolution path (safe today,
  latent if MM ever ships a non-float `named_parameter`); `dict(p)`
  shallow-copies an enum's `values` list in `_resolve_widget_range`,
  aliasing it between a compound entry and its referenced leaf entry
  (harmless only because nothing mutates the catalog today,
  `copy.deepcopy` would close it); dead `full_catalog` parameter plumbing
  on `_parse_node_data` that no caller passes non-`None`.

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
- **A compound (`graph`-type) node's exposed numeric parameter can be a
  `named_parameter` widget** (min/max/step/default live directly on the widget,
  no `linked_widgets` at all -- `directional_noise.n_scale`, `dirt.d_scale`) OR
  a `linked_control` widget chasing an inner node that may itself be a plain
  TYPE REFERENCE (not an inline `shader_model`) needing a full-catalog lookup,
  possibly through another compound node (`catalog_builder.py`'s `build_catalog`
  now does a bounded fixpoint pass for this, fixed 2026-09-14). If a new
  material's exposed slider ever fails `test_play_sliders.py` with "missing
  numeric range," check which of these two widget shapes it is before assuming
  the node just lacks catalog data.
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

### 2026-09-14 (noise-vocabulary round 3 + catalog fix, ready for final review): `pickup` -> `writing-plans` -> `subagent-driven-development` for a 6-material round Grayson approved (scope-corrected before dispatch: `custom_tiles` swapped for `skewed_bricks`, the former needs an out-of-scope `sdf2d` input). Refined the implementer/controller split further: implementer authors + validates + does isolated verification renders only (including comparing a compound node's internal modes with a measured regularity metric, not trusting the first render); controller renders all six, self-screens, batches one `SendUserFile`, gets Grayson's real approval before writing cards/promoting. All 6 materials + 2 README/AUTHORING tasks landed, only Task 2 (`f11_corduroy`) needed a fix round (an overstated "clean ribbing" claim caught by the task reviewer opening the actual render). Task 8 surfaced a real pre-existing `catalog_builder.py` bug (compound-node param range resolution failing for `named_parameter` widgets and type-referenced `linked_control` links) unrelated to any task's own correctness; fixed as its own TDD'd task, itself needing one fix round after the opus reviewer found the first pass's two-pass restructuring was order-dependent for compound-to-compound chains (concretely reproduced with `binary_smooth`/`fast_blur`) -- replaced with a bounded fixpoint loop, re-review independently re-derived the old bug to confirm the fix. Full suite 1161 passed, gates clean 71/71. Still on `worktree-noise-vocabulary-round-3`, final whole-branch review not yet run.
### 2026-09-14 (pickup, render_preview_sweep verified): ran the sweep tool for real through the live MCP tool surface (`render_graph` on cookbook's `f01_woven_denim`, piped into `render_preview_sweep`), sent Grayson the resulting GIF, he confirmed it read fine. Promoted `render_preview_sweep` 🔌 -> ✅ in STATUS.md, dropped the now-resolved open question from this file. Kicking off round 3 of the noise-vocabulary expansion next.
### 2026-09-14 (noise-vocabulary round 2, MERGED to `main`): `pickup` resumed at Task 5's pending approval (prior session paused mid-task). Grayson approved four previews with no iterations needed this session (f10_boucle_upholstery, carried over from the paused prior session, plus sf05_circuit_maze_panel, gl03_shattered_crystal, and w06_burled_wood) before `subagent-driven-development` drove Tasks 5-11 through to completion: cookbook 59 -> 65 materials across 12 categories, README/AUTHORING count integration, and a wrap commit. A final whole-branch review (opus) came back "ready to merge with fixes": one fix wave landed an AUTHORING.md clarity clause, a `_NOISE_PATTERN_NODES` catalog-subset guard test plus the missing `directional_noise` entry (52 -> 53), a softened w06 docstring, and two baton nits, all re-reviewed clean. Task 8's review had also found and parked a real pre-existing bug (the shared `wood` donor bleeds GrainMask into Material's metallic port, identical in w04/w05/w06) with a spawned follow-up (`task_21359777`); before merging, that follow-up's own session landed a fix for w04/w05 on a separate branch (`claude/heuristic-bhaskara-551ae1`), which was merged to `main` first, then the identical fix was applied to w06 on this branch (verified via the ORM's metallic channel, flat 0) so the issue closed fully rather than half-fixed. Merged to `main` with Grayson's explicit go-ahead, HANDOFF.md's conflicting session-log entries hand-reconciled (both this session and the same-day `render_preview_sweep` session's entries preserved) rather than resolved naively.
### 2026-09-14 (rotating-key-light preview mode, `render_preview_sweep`, MERGED `58e35ab`, still 🔌 not ✅ pending Grayson's own run): brainstorming (bounded path) -> TDD. Follow-up from the noise-vocabulary-round-2 session (f09_plaid_flannel's static preview couldn't show relief depth). `preview.gd` sweep mode (one Godot process, N frames, full 360-degree key-light rotation) + `render_preview_sweep()` (Pillow GIF assembly, now a runtime dep) + 11th MCP tool. Advisor review caught a thin test (frame count alone doesn't prove the light moved) and the verified/wired state mismatch (implementer-run, not Grayson-run); added a real frames-differ assertion (proved it has teeth by watching it catch settle=0) and measured a real brightness curve (66 front-lit -> 40 backlit across a 24-frame sweep, not black -- flagged for Grayson, not silently fixed). Sent Grayson the GIF (`f01_woven_denim`); he confirmed it looked fine. Full suite 1083 passed / 1 known live-overlay flake (passes alone). Committed, pushed, merged to `main` same session.
### 2026-09-14 (noise-vocabulary round 2 kickoff, IN PROGRESS): `pickup` answered Grayson's two questions (README current, tool usage still shallow: 9 of the catalog's noise/warp bases in use across 59 materials), brainstorm -> `writing-plans` -> `subagent-driven-development` for a round-2 scope Grayson approved (6 more materials + a reusable `quality/node_usage_audit.py` audit script). Phase A landed clean (13/52 curated noise nodes now live-tracked). `l07_pebbled_leather` and `f09_plaid_flannel` landed and approved (f09 took one relief-strength iteration on Grayson's feedback). Caught and corrected a dispatch bug mid-session: an implementer subagent was wrongly told to SendUserFile-and-wait-for-approval itself, when only the controller session has a live chat channel to Grayson; fixed for all subsequent material dispatches. Session ended mid-Task-5 (`f10_boucle_upholstery`): preview sent, no reply yet, builder committed as an explicit WIP checkpoint (`a3728df`) so nothing is lost. Grayson also asked about a rotating-light preview GIF; deferred to a spawn_task follow-up rather than scope-creeping this round. Tasks 6-11 not started.
### 2026-09-13 (enum-index validation enforcement, MERGED to main): `pickup` (caught baton drift: noise branch already merged `0169446`/pushed, baton said unmerged), Grayson picked the deferred enum follow-up. Advisor-prompted investigation flipped the premise: detection already worked (`validate_graph` flags t09's `type=-3` int, even in-subgraph); the hole was ENFORCEMENT (out-of-range enum was a `warning`, all gates filter to errors / promote never validates). Fix: out-of-range enum index -> `error`; message explains the clamp and either names the intended index via `_enum_literal_hint` (literal match) or lists all valid options; `catalog_builder` captures `value_literals` for numeric index-mismatched enums only; ratchet test in `test_cookbook_gate`. Wrap-up surfaced a sibling branch `claude/zealous-ritchie-cb051a` (2 commits, unmerged) fixing the same thing as a warning-with-options-list; Grayson said reconcile, so its options-list message + wavelet range-pin test were folded into this branch (sibling now superseded). TDD red->green, fast suite 1039->1045. Ruled out: string-literal guard hole (left; t09 was int) and the stale gitignored `catalog/catalog.json` artifact (not a bug). Commons log written.
### 2026-09-13 (noise/distortion vocabulary + core toolbox, MERGED `0169446` + pushed): `pickup` -> `subagent-driven-development` resumed at Task 8, finished the plan (all 14 tasks, per-task + final opus review clean). Shipped 6 proof materials on unused bases (s13 marble/fbm, m03 titanium/anisotropic, sf07 conduit/truchet, s12 sandstone/directional_warp, t09 wet sand/wavelet, gl02 cut gem/voronoi_triangle; cookbook 53->59), 19 diagnostic swatches, README un-collapse + count-gated "Core toolbox" section, AUTHORING distortion note. Fast suite 1039; final fix `4905d37` (gl02 card node count). Merged next session; a follow-up t09 enum fix `4d1187f` landed post-merge.
### 2026-09-06 (backup-ops wake-lock, cross-project): `pickup` here, Grayson picked next-step #2. Root-caused the 09-05 nightly truncation as idle-sleep mid-run (the git `NativeCommandError` is a handled CRLF warning; true signature is a missing `transcript end` footer, not a code bug), and added a `SetThreadExecutionState` wake-lock to `backup-ops\Backup-All.ps1` (acquire in try, release in finally). Verified compile + parse; commit `f7e809d` local, PUSH PENDING (ssh-agent not loaded this session). Commons log written. No MM-MCP code changed.

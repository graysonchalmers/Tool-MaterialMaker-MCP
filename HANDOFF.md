# 🧭 Session Handoff: Tool-MaterialMaker-MCP

_Last updated: 2026-09-14 21:15 CT (round 3 of the noise-vocabulary expansion
merged to `main` and pushed to `origin`; the preview lighting rig overhaul
merged earlier the same day from a concurrent session, `6ce84c6`, pushed
along with it) (America/Chicago)_

The session baton. Read at pickup, rewrite at wrap-up. **Shape rule (2026-09-05,
teardown #3):** "Current state" describes the latest session only; anything
older is one line in the session log. "Heads-up" is a bounded list of live
gotchas (drop an entry once a mechanism makes it moot). Git history is the
archive; there is no separate archive file.

## 🎯 Current state

**Round 3 of the noise-vocabulary expansion, MERGED to `main`.** Started
from a `pickup` that verified `render_preview_sweep` for real and answered
"what's next?" by kicking off round 3. `subagent-driven-development` drove
all 6 material tasks plus the 2 README/AUTHORING integration tasks through
to completion; every task reviewed clean on the first pass except Task 2
(one fix round). Plan at
`docs/superpowers/plans/2026-09-14-noise-vocabulary-round-3.md`, SDD ledger
at `.superpowers/sdd/2026-09-14-noise-vocabulary-round-3/progress.md`.

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
across 12 categories, up from 65.

**A real, pre-existing infra bug surfaced during Task 8, unrelated to
any of the six materials' own correctness, fixed as its own dispatched
task.** Running the full suite for the first time after promotion
surfaced 3 `test_play_sliders.py` failures: `f11_corduroy`,
`gl04_raw_crystal_cluster`, and `t10_packed_dirt` all came back "missing
numeric range" on an exposed slider. Root cause: `src/mm_mcp/catalog_builder.py`'s
`_resolve_widget_range` had two real gaps this round's compound-node
retype choices were simply the first to exercise -- it required
`linked_widgets` to exist at all (missing the `named_parameter`-style
widgets `directional_noise.n_scale` and `dirt.d_scale` use, which carry
their own min/max directly), and it only followed a link to an inner
node with an INLINE `shader_model` (missing `crystal.param0`/`param1`'s
links to plain TYPE-REFERENCE nodes like `voronoi`). Dispatched as its
own fix task with full TDD. First pass fixed both gaps but introduced a
subtler one: its two-pass `build_catalog` restructuring ran pass 2 as a
single sweep, which is order-dependent for a compound node linking to
ANOTHER compound node that itself only resolves in pass 2 -- the opus
reviewer reproduced this concretely (`binary_smooth.smooth` ->
`fast_blur.param1` resolves differently under forward vs. reversed glob
order). One fix round replaced the single sweep with a bounded fixpoint
loop (converges in 2-3 rounds against a cap of 10, warns loudly rather
than silently half-resolving if the cap is hit), plus a committed
order-independence regression test. Re-review independently re-derived
the old buggy behavior from scratch to confirm the fix's necessity.

**Final whole-branch review (opus) came back "ready to merge with
fixes."** Independently rebuilt the catalog under base vs. HEAD and
diffed every entry (34 entries/22 node types resolved, zero
regressions); independently re-verified every material's sibling
numeric cross-references against the real graphs (all correct except
one). One fix wave: `t10_packed_dirt`'s card and docstring had fabricated,
self-contradictory sibling relief numbers (the same error class that
cost Task 2 its fix round) -- fixed, prose-only, no re-render needed.
Also included in the same wave since already touching the file: removed
dead `full_catalog` parameter plumbing plus a now-false docstring claim
in `catalog_builder.py`, closed a shallow-copy aliasing hazard on
resolved enum params (`copy.deepcopy` instead of `dict()`), and fixed
`gl04`'s card mischaracterizing a sibling as "turbulent." Re-review
confirmed all four addressed, zero new breakage. One finding was
explicitly ruled NOT a merge blocker and spawned as a follow-up instead
(`task_73027cd8`): the catalog fix's `default` field is resolved from
the wrong (inner leaf) node for 17 parameters including `crystal`
(reports 4, real default is 16) -- an amplification of a pre-existing
flaw (44 -> 61 wrong compound defaults), not a new defect class.

**Merged to `main` while `main` had moved.** A concurrent session (the
preview lighting rig overhaul, below) landed two commits on `main`
after this branch had already forked from it. Merging `main` into this
branch surfaced conflicts in exactly `HANDOFF.md` and `STATUS.md` (no
code conflicts -- the two sessions touched entirely disjoint files
otherwise); hand-reconciled preserving both sessions' content, matching
this project's established precedent for concurrent-session baton
conflicts. Full suite re-verified green post-merge before the final
merge to `main`.

Below, compressed to one entry each in the session log: the preview
lighting rig overhaul (a separate concurrent session, merged to `main`
earlier the same day as `6ce84c6`) reworked `render_preview`'s 3D
lighting -- soft distance key shadow, a boosted rim light that
deliberately casts its own shadow for contact grounding, a cool bounce
fill, procedural-sky ambient/reflections (fixes metals reading
dead-black), SSAO, and changed `render_preview_sweep`'s default motion
from a full 360 azimuth orbit to a precession (key aim wobbles in an
18-degree cone, rim/fill held still) so highlights circle relief without
ever going backlit. Verified end-to-end on cobblestone (Grayson's
approved pick) plus an out-of-category glass render. No tracked
thumbnail regeneration was needed (`docs/images/cookbook-*/*.png` are
flat albedo downscales, not lit 3D renders, so the lighting change
touches nothing tracked).

## 📌 Where we stopped

Both sessions' work is on `main` AND pushed to `origin` (confirmed synced,
`git rev-list --left-right --count origin/main...HEAD` reads `0  0`): round
3's six materials plus the catalog_builder fix, and the preview lighting rig
overhaul. Full suite 1163 passed in the primary checkout post-merge,
`promote_cookbook --check` and `naming --cookbook` both clean (71/71). The
scratchpad lighting prototype (`scratchpad/preview_variant/`,
`scratchpad/lighting_lab/`) is untracked, still on disk. The merged-away
worktree (`worktree-noise-vocabulary-round-3`) hit a Windows file-lock on
`git worktree remove`; a follow-up (`task_86ba47bd`) was spawned to retry
the cleanup once nothing has it locked.

## ▶️ Next concrete step

No pressing next MM-MCP step queued. Open items, any of which Grayson
can pick up next:
- The spawned follow-up (`task_73027cd8`, already running as of this
  writing): fix the catalog's resolved `default` field for compound-node
  parameters.
- The spawned worktree-cleanup follow-up (`task_86ba47bd`).
- Promote the interactive lighting slider lab (`scratchpad/lighting_lab/`) to a tracked dev tool, or leave it as throwaway scratchpad.

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
- Follow-up spawned (`task_73027cd8`): the catalog_builder fix's `default`
  field is resolved from the wrong node for 17 compound-node parameters
  (see Current state); not a merge blocker, worth fixing properly later.

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
  the node just lacks catalog data. Known remaining gap: the resolved
  parameter's `default` field can still be wrong (taken from the inner node,
  not the compound node's own declared default) -- see the spawned follow-up.
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

### 2026-09-14 (noise-vocabulary round 3 + catalog fix, MERGED to `main`): `pickup` -> `writing-plans` -> `subagent-driven-development` for a 6-material round Grayson approved (scope-corrected before dispatch: `custom_tiles` swapped for `skewed_bricks`). Refined the implementer/controller split: implementer authors + validates + isolated verification renders only; controller renders all six, self-screens, batches one `SendUserFile`, gets Grayson's real approval before writing cards/promoting. All 6 materials + 2 README/AUTHORING tasks landed, only Task 2 (`f11_corduroy`) needed a fix round (an overstated "clean ribbing" claim caught by the task reviewer). Task 8 surfaced a real pre-existing `catalog_builder.py` bug (compound-node param range resolution) fixed as its own TDD'd task, itself needing one fix round (a fixpoint loop replacing an order-dependent two-pass sweep). Final whole-branch review (opus) came back "ready to merge with fixes": one fix wave (a fabricated-numbers card fix matching Task 2's own error class, catalog dead-code cleanup, an aliasing fix, a card tidy), re-reviewed clean. One finding spawned as a follow-up instead of fixed (`task_73027cd8`: catalog default-field accuracy for 17 params). Cookbook 65 -> 71 materials, 12 categories. Merged `main` into this branch first (a concurrent session had landed `6ce84c6`/`6051eed` on `main` after this branch forked), hand-reconciling HANDOFF.md/STATUS.md conflicts; then merged this branch into `main`. Full suite 1161+ passed throughout.
### 2026-09-14 (preview lighting overhaul, MERGED `6ce84c6`, pushed with round 3): `pickup` on the lighting worktree; a long live visual-iteration session (advisor-guided). Prototyped soft-shadow/bounce/AO/precession options in a throwaway scratchpad Godot project + an interactive slider lab (`lab.bat`), sending PNG/GIF comparisons each pass; Grayson converged over ~10 rounds to: soft distance key shadow (angular 5.0), boosted rim (2.0) casting a soft shadow (load-bearing for contact grounding), cool bounce fill, procedural-sky ambient+reflections (fixes dark metals), SSAO contacts, and a precession-default sweep (cone 18, rim still). Landed into production `preview.gd` + `preview.py` + `server.py` + `tests/test_preview.py`. Fast suite 1112, preview integration 4. The planned 65-preview regen was found MOOT (tracked thumbnails are flat albedo, not lit renders). Merged `--ff-only` to `main`. Gotchas hit: Godot launcher hangs on raw-pipe/parse-error; `var x := a and b` Variant-inference failure.
### 2026-09-14 (pickup, render_preview_sweep verified): ran the sweep tool for real through the live MCP tool surface (`render_graph` on cookbook's `f01_woven_denim`, piped into `render_preview_sweep`), sent Grayson the resulting GIF, he confirmed it read fine. Promoted `render_preview_sweep` 🔌 -> ✅ in STATUS.md.
### 2026-09-14 (noise-vocabulary round 2, MERGED to `main`): `pickup` resumed at Task 5's pending approval; `subagent-driven-development` drove Tasks 5-11 to completion (cookbook 59 -> 65 across 12 categories, README/AUTHORING count integration). Task 8 found + parked a real pre-existing bug (shared `wood` donor bleeds GrainMask into Material's metallic port, w04/w05/w06); a follow-up session fixed w04/w05, then w06 was fixed on this round's branch before merging. Merged with HANDOFF.md's session log hand-reconciled.
### 2026-09-14 (rotating-key-light preview mode, `render_preview_sweep`, MERGED `58e35ab`): brainstorming -> TDD. `preview.gd` azimuth sweep mode (one Godot process, N frames, 360 key-light rotation) + `render_preview_sweep()` (Pillow GIF assembly, runtime dep) + 11th MCP tool. Advisor review caught a thin test and the verified/wired state mismatch; added a real frames-differ assertion, measured a real brightness curve. Merged same session.
### 2026-09-13 (enum-index validation enforcement, MERGED to main): `pickup`; the hole was ENFORCEMENT (out-of-range enum was a `warning`). Fix: out-of-range enum index -> `error` with an intended-index hint; ratchet test. TDD red->green, fast suite 1039->1045. A sibling branch fixing the same thing was folded in.
### 2026-09-13 (noise/distortion vocabulary + core toolbox, MERGED `0169446`): `subagent-driven-development`, all 14 tasks. Shipped 6 proof materials on unused bases (cookbook 53->59), 19 diagnostic swatches, README "Core toolbox" section, AUTHORING distortion note. Fast suite 1039.
### 2026-09-06 (backup-ops wake-lock, cross-project): root-caused the 09-05 nightly truncation as idle-sleep mid-run; added a `SetThreadExecutionState` wake-lock to `backup-ops\Backup-All.ps1`. Commit `f7e809d`. No MM-MCP code changed.

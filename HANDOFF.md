# 🧭 Session Handoff: Tool-MaterialMaker-MCP

_Last updated: 2026-09-04 (leather + terrain bug fixes) CT (America/Chicago)_

The session baton. Read at pickup, rewrite at wrap-up.

## 🎯 Current state

**The three cookbook bugs the subgraph retrofit surfaced are all fixed,
verified, promoted, committed, and pushed.** `main` is at `5cd9e0b`, in sync
with origin. Fast suite 505 passed, `promote_cookbook.py --check` in sync, no
incidental render-sweep churn.
- **t01_sand_dunes (terrain):** the `wood` donor wired `blend_0` (the master
  ripple pattern) into Material's metallic port, and Material's metallic
  scalar defaults to 1, so parts of the sand read as metal. Fixed by dropping
  the wire AND `set_param(Material, metallic, 0)`. Verified by reading the
  exported ORM's metallic (B) channel directly: flat 0.
- **l02_distressed_two_tone (leather):** swapped port0/port1 on both blends so
  the dark saddle base is the majority and the lighter worn rubs are the
  scattered minority (was reversed). Before/after render confirmed the flip.
  Bonus: the exposed "Wear blend strength" param now controls the wear layer
  as its label claims.
- **l05_quilted_leather (leather):** swapped port0/port1 on `blend_alb_q` so
  the dark seam_shade lands in the recessed seams instead of on the pad
  centers. The `sin*sin` pattern makes compact round peaks, so the result
  reads as round grain pads on a dark seam grid; Grayson reviewed before/after
  and chose the swap over relabeling (documented honestly in the card).
- Recipe cards for all three rewritten to describe the fixed behavior (they
  had previously asserted the broken behavior as intentional).

**Before this (2026-09-04), all 46 existing cookbook materials were
retrofitted to use Material Maker's native subgraph mechanism.**
Opening any cookbook material now shows a handful of friendly, labeled
nodes instead of a wall of raw ones (524 -> 179 top-level nodes across the
cookbook, 66% fewer, average 11.4 -> 3.9 per material), purely
organizational, zero materials failed to reduce, zero regressions.
- Picked up Grayson's backlog idea ("Material Maker for dummies" -- a raw
  node graph "scared the shit out of" a non-technical viewer he showed it
  to) via `pickup` -> `brainstorming`. Investigating a dead-end lead
  ("generic parameters") surfaced the real answer: Material Maker already
  has a native subgraph mechanism (`Ctrl+G` groups nodes into one collapsed
  node exposing a curated, named set of parameters), the same shape its own
  50 bundled compound nodes (`normal_map`, `occlusion`) already use. No new
  infrastructure needed.
- Decomposed into two sequenced sub-projects: (1) a subgraph
  authoring/retrofit lever (this session), (2) a later live web companion
  that will read its slider definitions from (1)'s exposed parameters
  (deferred, unscoped). Grayson chose to retrofit all 46 existing
  materials, not just apply the lever going forward, which upgraded
  sub-project 1 from bounded to architectural.
- Spec + 12-task plan -> `subagent-driven-development` on branch
  `cookbook-subgraph-retrofit`. Task 1 built `group_into_subgraph` (a new
  primitive in `quality/author_helpers.py`, pure JSON graph surgery, no
  Godot dependency) plus a tolerance-based render comparison utility
  (`quality/render_compare.py`, since Godot's render isn't perfectly
  deterministic run to run). A pilot task proved the whole process on
  `glass` (1 material) before fanning out to the other 9 categories, one
  dispatch per category, largest last (`stone` 8, `terrain` 8). A final
  task added a permanent regression gate: every cookbook material must
  carry at least one subgraph node, `pytest`-enforced across all 46.
- Every task hit an exact `grid_mean_abs_diff == 0.0` render match (not
  merely under tolerance). The final whole-branch review went further:
  it built an independent flatten-diff harness (resolves every subgraph's
  boundary threading back to a flat graph, diffs node types/params/
  connections against pre-branch `main`) across all 46 materials in all 13
  commits. 45/46 matched byte-for-byte; the one exception
  (`f04_wool_knit`) was an incidental, disclosed correction of an
  already-stale tracked artifact (its committed `.ptex` predated a 2026-08
  builder/card fix and had never been re-promoted), not a retrofit-caused
  change -- fixed by correcting the recipe card's parity claim, not the
  artifact (already correct).
- Two real, pre-existing, unrelated bugs surfaced during the retrofit and
  correctly left unfixed per each task's organizational-only scope
  (documented in their own recipe cards): `l02_distressed_two_tone` and
  `l05_quilted_leather`'s visible composite layers are reversed from what
  their own names/docstrings describe; `t01_sand_dunes`'s wood-donor wires
  a `blend_0` node directly to the Material's metallic port. **All three
  FIXED 2026-09-04 in the next session (`5cd9e0b`); see this doc's top
  Current-state section.**
- Fast suite 453 -> 505 (Task 1's +6, Task 12's +46 parametrized gate
  cases). Merged `--no-ff` (`034aeaf`), pushed, feature branch deleted.

**Before this, plastics (new category) and a second, differently-flecked
tweed both landed in the cookbook: `p01_glossy_plastic` and
`f08_donegal_tweed`.** Cookbook grew to 46 materials across ten categories
(was 44/nine).
- Picked up on the two smallest open backlog items from the prior session's
  briefing (plastics, two-color tweed). Scoped via `brainstorming` (bounded
  path): plastics differentiates through the ABSENCE of visible
  micro-pattern (every other category so far uses one), so it's the first
  cookbook material built from scratch via `_from_scratch_noise_material`
  rather than cloned from a donor. Tweed differentiates through color
  (flecks) rather than weave geometry (f07's chevron).
- `p01_glossy_plastic`: narrow near-single-color saturated red albedo, low
  roughness (glossy), non-metallic, normal relief kept just above zero
  (`param1=0.04`, `param4=0`). Hit the same scalar-roughness ORM gap
  `gl01_frosted_glass` did; fixed the same way, a flat `rough_const`
  texture wired into `Material` port 2.
- `f08_donegal_tweed`: plain `weave2` base (`stitch=1`) plus a SEPARATE
  `voronoi` node purely for flecks (retyping the base loses its own
  rand3 output), hard-thresholded to the top ~20% of cells for sparse
  coverage, cream/rust two-tone color. First pass was too sparse (~4
  flecks per crop, sent to Grayson, revised); second pass approved.
  Composited via `blend` (`blend_type=0`, base on majority port 1, flecks
  on minority port 0, mask on port 2).
- Both promoted through `promote_cookbook.py`, carded, thumbnailed
  (`_make_previews.py`). README counts updated (44/nine -> 46/ten).
  **Real gotcha hit and worked around:** re-rendering a whole
  `cookbook-<category>` label for one new entry re-renders and
  re-thumbnails every case in it; `f04_wool_knit`'s thumbnail came out
  byte-different (render non-determinism, not a content change) and had
  to be reverted before committing. Fast suite 447 -> 453.

**Before this, the "image-to-material decomposition" backlog idea closed: a
reference-photo authoring workflow is documented and proven with a real
cookbook material.**
- Scoped via `brainstorming`: the decomposition reasoning happens in
  Claude's own vision during a chat session, no new server code, no new MCP
  tool, no new dependency, which downgraded the task from architectural to
  bounded (a documented workflow, not a subsystem).
- New "Authoring from a reference photo" section in `docs/AUTHORING.md`,
  extends the existing step-1 workflow with a decomposition rubric
  (color/tone, pattern topology, scale, roughness, relief cues), reusing
  the noise vocabulary and cross-material lessons already documented rather
  than inventing new taxonomy.
- Proved it out end to end: sourced a real CC-BY-SA 4.0 macro photo of
  sandblasted glass (Wikimedia Commons), decomposed it, and authored
  `cookbook/glass/gl01_frosted_glass`, cloning `dry_earth`'s connected-
  crack-network topology at a much finer scale, judged in the 3D preview,
  promoted through the normal `promote_cookbook.py` path. First entry in a
  new `glass` category, closes half of the glass/plastics backlog gap.
  Fast suite 444 -> 447.
- Also cleared a pre-existing stale local build artifact
  (`quality/authored/cookbook-fabrics/f04_wool_knit/`, gitignored, left
  over from the 2026-09-01 wool-knit exploration) that was making
  `promote_cookbook.py --check` report false drift.

Older write-ups/log beyond the cap live in
[docs/HANDOFF_ARCHIVE.md](docs/HANDOFF_ARCHIVE.md).

## 📌 Where we stopped

`main` at `5cd9e0b`, pushed and in sync. All three retrofit-surfaced cookbook
bugs (t01 metallic, l02 reversed layers, l05 seam polarity) fixed, promoted,
carded, committed as one bug-fix commit and pushed. Natural stopping point, no
open decision blocking the next session.

## ▶️ Next concrete step

Nothing is blocking on Grayson right now.
1. **l05's `blend_h_q` height weighting: DONE (2026-09-04, `6d460c4`).** Bumped
   `amount` from 0.35 to 0.85 so the quilt pads drive the relief instead of the
   crocodile grain overpowering them; confirmed in a 3D preview (puffy padded
   bumps with recessed channels). Only optional remainder here: swapping the
   `pattern` node to a Bounce wave for broad diamond pads instead of `sin*sin`'s
   compact round ones (a larger redesign, still deferred, not needed).
2. **Sub-project 2 of the "Material Maker for dummies" idea: the live web
   companion.** Now unblocked (sub-project 1, this session's retrofit, is
   the prerequisite). A local server bundled with `mm-mcp`, opened in a
   real browser, driving Phase 5's existing live-control tools
   (`live_apply`/`live_render`/`set_param`), with slider definitions read
   directly from each graph's exposed subgraph parameters rather than a
   separate curation step. Needs its own `brainstorming` session to nail
   down the UI shape before building (was explicitly deferred pending
   sub-project 1's completion, see the 2026-09-04 session log entry).
3. **This session's tool list showed `mcp__unreal-engine__*` tools
   connected** (see the drift note an earlier pickup briefing surfaced).
   **Unreal UE5 export verification** has been blocked for multiple
   sessions on "needs a live Unreal Editor with the MCP bridge connected" —
   worth a live check now that the bridge appears to be up, before assuming
   it's still blocked.
4. **More cookbook categories/materials** remain an open-ended, no
   specific quick-win flagged right now. New materials land in `cookbook/`
   via `promote_cookbook.py`, then get a card at `cookbook/<category>/<id>.md`
   — and should call `group_into_subgraph` before `save_variant` returns
   from now on (see `docs/AUTHORING.md`'s "Grouping into subgraphs"
   section), so future categories don't need a second retrofit pass.

The older open backlog, unchanged unless noted:
- **2 findings ruled out, not fixed** (deliberate): #8 (`_cmd_clear_graph`'s
  guard is correct, `new_material()` creates the generator, doesn't read
  one) and #10 (`generic_size or 1` coercion is safer than passing an
  explicit 0). Both annotated in-code. Findings 3-7 and 9 are fixed.
- **`list_node_types` tool decision — KEEP.** ~5KB name list vs the ~260KB
  full `catalog://nodes` resource, so it's the cheap discovery lever, not
  redundant with the resource + `describe_node`.
- **B. More cookbook categories** — fabrics, organics, sci-fi, terrain, wood,
  stone, leather, painted-metal, glass, and plastics are all represented
  (ten categories, 46 materials); terrain includes the natural-surface set
  (ice/lava/forest floor/pebbles). No specific remaining gap flagged right
  now. All 46 now grouped into subgraphs (see 2026-09-04 below).
- **K. Cookbook subgraph retrofit — DONE, 2026-09-04.** All 46 existing
  materials grouped into Material Maker's native subgraph mechanism; new
  materials should do the same at authoring time going forward (see
  `docs/AUTHORING.md`).
- **L. "Material Maker for dummies" — sub-project 1 DONE (this session),
  sub-project 2 open.** Decomposed into subgraph retrofit (done) + a live
  web companion (open, see Next concrete step above).
- **C. True cobblestone — DONE.** `s07_cobblestone` closed this; the `s05`
  hex-grid partial is superseded.
- **D. Wool loop-knit — CLOSED as unreachable.** No bundled generator makes
  upright-V stockinette; `f04` stays the honest coarse-weave stand-in and
  `f07_herringbone_tweed` shipped as the closing probe's byproduct.
- **E. Image-to-material decomposition — CLOSED, 2026-09-03.** Shipped as
  the "Authoring from a reference photo" section in `docs/AUTHORING.md`
  plus `cookbook/glass/gl01_frosted_glass` as the worked proof. Scoped to
  Claude's own vision doing the decomposition in-session, no new server
  code or MCP tool.
- **F. PyPI publish** (on hold; GitHub-clone is the current route).
- **J. Load an existing `.ptex` into a live session.** No `live_load`
  equivalent exists. Lowest priority of the remaining live-mode gaps.

## ❓ Open questions

- **New 2026-09-03:** `quality/README.md`'s "Cookbook growth" section was
  corrected this session (it still said helpers were "imported from
  `author.py`"), but hasn't been re-read end to end for other drift since
  the split. Worth a skim next time that file is touched.
- **New 2026-09-03 (parked, not fixed, no downstream dependency):**
  `tests/test_donors.py`'s module-level `build_catalog(cfg.nodes_dir)` call
  means a missing `MM_PROJECT_PATH` fails all 20 donor tests together
  (including the 10 that don't actually need the catalog), not just the 9
  catalog-validation ones. Low blast-radius issue, not a correctness bug;
  worth a `pytest.fixture` split only if it ever actually bites.
- Still open, unchanged: does `backup-ops` exclude the ~1GB of regenerable
  renders under `output/`, `quality/cookbook/`, `quality/runs/` (plus the
  266MB `mm_live_overlay/`)? Flagged by an earlier teardown, not verified.
- Still open, unchanged, deferred minors from the cookbook-as-data reviews
  (all small): `tests/test_config.py`'s default-dir test reads the real
  machine env (pre-existing pattern); `_default_cookbook_dir()`'s empty
  branch is untested; `server.py`'s source-validation error string is
  near-duplicated between the two example tools; the contact sheet adds a
  5MB blob per regeneration.
- Still open, unchanged: the cross-engine North Star wording treats UE4's
  export path (PNGs + manual in-editor assembly) as a lesser tier, not a
  real target, Grayson said "sounds good" generally but never explicitly
  confirmed that specific framing. Worth a quick check before it drives real
  scope decisions.
- Still open, unchanged: is `.mcp.json` the right long-term wiring, or
  should it fold into `project-setup`'s standard kit? Not decided.
- Still open, unchanged: PyPI vs. GitHub-clone-only (leaning GitHub-only);
  cross-platform (macOS/Linux) verification, still untested, no machine
  available; two parked-not-fixed overlay-builder findings from a much
  earlier session (staleness marker, `_append_autoload`'s first-occurrence
  match, both verified low-priority).

## 🗂️ Changed this session (leather + terrain bug fixes)

- **`quality/cookbook_terrain.py`** (`build_t01_sand_dunes`): drop the
  `blend_0 -> Material:1` metallic wire (`drop_conn(g, "Material", 1)`) and
  `set_param(g, "Material", "metallic", 0)`. The `wood` donor pipes its master
  ripple pattern into the metallic port and Material's metallic scalar defaults
  to 1, so sand read partly metallic. Doing both edits is correct under every
  Material-node port/scalar semantic. Verified by reading the exported ORM's
  metallic (B) channel: flat 0 (`min=max=mean=0`). Albedo/normal unaffected.
- **`quality/cookbook_leather.py`** (`build_l02_distressed_two_tone`): swap
  port0/port1 on both `blend_alb` and `blend_rgh`. `colorize_wm`'s mask is 1
  only in the small high-perlin patches, so the worn tone (minority) belongs on
  port0 and the dark saddle base (majority) on port1; the original wiring was
  reversed. Before/after render confirmed the field flipped from mostly-light
  to mostly-dark-saddle with lighter worn rubs scattered through it. In-code
  port trace updated.
- **`quality/cookbook_leather.py`** (`build_l05_quilted_leather`): swap
  port0/port1 on `blend_alb_q` so the dark `seam_shade` lands where the mask is
  1 (the recessed seams) instead of on the pad centers. The `sin*sin` `pattern`
  makes compact round peaks with broad valleys, so the fixed result reads as
  round grain pads on a dark seam grid (round/small pads, not big puffy
  diamonds). Grayson reviewed the before/after and chose the swap over
  relabeling the material; the geometry limitation is documented honestly in
  the card.
- **Recipe cards** `cookbook/terrain/t01_sand_dunes.md`,
  `cookbook/leather/l02_distressed_two_tone.md`,
  `cookbook/leather/l05_quilted_leather.md` rewritten: each had asserted the
  broken behavior as intentional/documented, now they describe the fix and its
  reasoning. Thumbnails regenerated for l02 and l05 (t01's albedo is unchanged).
- **Process:** `pickup` (`+ fix the leather and terrain bugs`) then a single
  advisor consult before editing, which confirmed the t01/l02 fixes, flagged
  the whole-label render-sweep hazard, re-promotion (non-zero diffs are the
  goal this time, inverse of the retrofit), and the card rewrites. Worked
  directly on `main` (this repo's cookbook convention), builder-only edits,
  `render_one.py` for just the fixed case each time to avoid the sweep. Fast
  suite 505 passed, `promote --check` in sync, `git status` showed only the
  three intended materials changed. Committed as one bug-fix commit (`5cd9e0b`)
  and pushed on Grayson's "push it and wrap up."
- **Decisions (+ why):** do both the wire-drop and the scalar-zero on t01 (so
  the fix is correct regardless of MM's port/scalar semantics); verify metallic
  by reading the ORM channel, not by eye (metallic is near-invisible on tan
  diffuse); ship the l05 swap rather than relabel (it matches the material's
  name and stated intent, round pads accepted as a minor stylization); leave
  l05's `blend_h_q` 35% height weighting as a separate follow-up rather than
  fold it in.

## 🗂️ Changed this session (cookbook subgraph retrofit)

- **`quality/author_helpers.py`**: new `group_into_subgraph(graph, member_names,
  name, label, exposed, catalog)` primitive. Pure JSON graph surgery, no Godot
  dependency: partitions a group's connections into internal/incoming/outgoing/
  untouched, builds `ios`-type `gen_inputs`/`gen_outputs` nodes (port types looked
  up from the catalog), a `remote`-type `gen_parameters` node whose `widgets`
  expose a curated subset of internal parameters under friendly labels, and
  collapses the named nodes into one `type: "graph"` node, the exact shape
  Material Maker's own `Ctrl+G` grouping produces and the same shape its 50
  bundled compound nodes (`normal_map`, `occlusion`) already use.
- **`quality/render_compare.py`** (new): `grid_mean_abs_diff`/`renders_match`,
  a 16x16-sample tolerance comparison (default 3.0) between two rendered PNGs,
  using the existing pure-stdlib `pngread.py` (no Pillow). Needed since Godot's
  render isn't perfectly deterministic run to run; the regression bar for this
  retrofit was "renders the same," not byte-identical.
- **All 46 existing cookbook materials retrofitted**, one dispatch per category
  (glass pilot, then plastics, wood, organics, sci-fi, painted-metal, fabrics,
  leather, stone, terrain): every `quality/cookbook_<category>.py` builder now
  ends its `build_*` functions with `group_into_subgraph` calls before
  `save_variant`. 524 -> 179 top-level nodes across the cookbook (66% fewer,
  11.4 -> 3.9 average per material), zero materials failed to reduce. Every
  category-level render check hit an exact `grid_mean_abs_diff == 0.0`.
  Category-specific cautions all held: `sf03_circuit_board`'s blend/opacity
  mask wiring (documented history of a real bleed-through bug), `stone`'s
  `warp_0`-sensitive materials (kept ungrouped-from-consumer, never exposed),
  `f08_donegal_tweed`'s fleck voronoi kept separate from the base weave,
  `t06_cooled_lava`'s emission glow chain kept as one unit -- all independently
  re-verified by task-level review, none regressed.
- **`tests/test_cookbook_subgraph_gate.py`** (new): parametrized across all 46
  cookbook entries via `mm_mcp.cookbook.list_cookbook`, asserts every material
  has at least one top-level `type: "graph"` node -- a permanent floor against
  future drift.
- **`docs/AUTHORING.md`**: new "Grouping into subgraphs" section (added
  alongside the glass pilot) documenting the lever for future materials.
  **`quality/README.md`**: one-line pointer added at the end of the retrofit.
- **Real bug found, disclosed, left unfixed (organizational-only task scope):**
  the final whole-branch review built an independent flatten-diff harness
  (resolves every subgraph's boundary threading back to a flat graph, diffs
  against pre-branch `main`) across all 46 materials. 45/46 matched
  byte-for-byte; `f04_wool_knit` didn't -- its tracked `.ptex` was a stale
  promotion (predating this series, from the 2026-09-01 wool-knit exploration)
  that disagreed with its own already-`weave`-based builder and card. The
  retrofit's rebuild-from-builder step incidentally corrected it as a side
  effect. Fixed via disclosure, not an artifact change: corrected
  `f04_wool_knit.md`'s parity claim to state what the `0.0` comparison does and
  does not prove (commit `73cf8d0`).
- **Two other real, pre-existing, unrelated bugs surfaced and correctly left
  unfixed** (each task's scope was organizational only): `l02_distressed_two_tone`
  and `l05_quilted_leather`'s visible composite layers are reversed from what
  their names describe (traced against `blend.mmg`'s shader model in each
  card); `t01_sand_dunes`'s wood donor wires `blend_0` directly to the
  Material's metallic port.
- **Process:** `pickup` -> `brainstorming` (architectural: a new interaction
  surface, no existing flow to extend). Investigating a dead-end lead ("generic
  parameters," which turned out to be an unrelated variadic-port mechanism)
  surfaced the real, already-native answer (subgraphs). Decomposed into two
  sequenced sub-projects; Grayson chose the larger retrofit scope (all 46
  existing materials, not just going forward), upgrading sub-project 1 from
  bounded to architectural. Spec + 12-task plan (pilot-first, smallest category
  before largest) -> `subagent-driven-development` on branch
  `cookbook-subgraph-retrofit`. One task-level fix round (Task 7/painted-metal:
  a commit message gave a factually-backwards explanation for a real thumbnail
  file-size change; the reviewer independently found the true, benign cause --
  old thumbnails were un-downscaled 2048x2048, new ones correctly 512x512 --
  fixed via a new documentation commit, not an amend). Final whole-branch
  review (opus) found 1 Important (the f04 disclosure gap above) + several
  Minor (boundary-port duplication in the primitive, builder-signature
  inconsistency across categories, exposed-parameter label drift); one fix
  wave addressed the Important finding, scoped re-review clean. Merged
  `--no-ff` to `main` (`034aeaf`), pushed, branch deleted, SDD workspace
  removed. Fast suite 453 -> 505.

## 🗂️ Changed this session (plastics category + Donegal tweed)

- **`quality/cookbook_plastics.py`** (new file): `build_p01_glossy_plastic`,
  the first cookbook material built from scratch via
  `_from_scratch_noise_material` rather than cloned from a donor. Narrow
  near-single-color red albedo, non-metallic, low roughness (`0.18`),
  near-zero normal relief (`param1=0.04`, `param4=0` since the fix still
  applies to a directly-fed perlin). Added a `rough_const` flat-roughness
  texture into `Material` port 2 so ORM exports (same gap
  `gl01_frosted_glass` hit).
- **`quality/cookbook_fabrics.py`**: new `build_f08_donegal_tweed`. Plain
  `weave2` base (`stitch=1`, distinct from f07's herringbone `stitch=3`)
  recolored heather gray-brown. A separate `voronoi_fleck` node (not the
  base generator, which loses its rand3 output once retyped) feeds a
  hard-threshold mask (top ~20% of cells) and a cream/rust two-tone color
  layer, composited via `blend` (`blend_type=0`, base weave on majority
  port 1, flecks on minority port 0, mask on port 2). First pass was too
  sparse (~4 flecks visible per 2048px crop, sent to Grayson); revised the
  threshold and added the second fleck tone, approved on the second pass.
- **`cookbook/plastics/p01_glossy_plastic.{ptex,md}`**,
  **`cookbook/fabrics/f08_donegal_tweed.{ptex,md}`**: promoted via
  `promote_cookbook.py`, recipe cards written, gallery thumbnails
  generated (`_make_previews.py`). `README.md` counts bumped 44/nine to
  46/ten, contact-sheet caption updated (not regenerated, same deliberate
  deferral as glass).
- **Gotcha hit and fixed:** `_make_previews.py cookbook-fabrics` (and
  `render_cookbook.py` before it) regenerate every case in the label, not
  just the new one. `f04_wool_knit`'s thumbnail came back byte-different
  (render non-determinism, the graph itself is unchanged) and was reverted
  before committing to keep the diff scoped to the real work.
- **Process:** `pickup` chained straight into `brainstorming` (bounded
  path, no plan doc) since the prior session's briefing already scoped both
  items into concrete numbered options. Two clarifying questions (plastics
  look, tweed's distinguishing lever vs. f07) then a short in-chat design,
  approved. Each material: build, render, 3D-preview, send to Grayson,
  wait for a look, promote. Fast suite 447 -> 453 (2 new gate tests per
  material: recipe-card parity + thumbnail presence, already existed as a
  parametrized test, just gained 2 more cases). Committed (`68c51dc`) and
  pushed to `main` on Grayson's explicit go-ahead (design approval and push
  approval given separately).

> 📦 **26 older "Changed this session" write-ups archived**, newest first the
> 2026-09-03 reference-photo authoring + glass cookbook session, then the
> 2026-09-03 v0.6.0 release + author.py split + donor vendoring session, then the
> 2026-09-04 v0.5.0 release + AUTHORING split + hygiene session, then the
> 2026-09-03 teardown #2 + cookbook-as-data session, then through
> 2026-09-01, incl. the wool-knit closure/f07/terrain session, the blend-opacity
> debug swatches, the painted-metal cookbook, and the v0.4.0 release-unblock
> + README gallery session --
> the pre-release audit/teardown/doc-fix pass,
> render_node_output/live_render_node_output (item H), saved_graphs/
> round-trip, Unity export proof, wood/stone cookbooks, the overlay
> read-only `rmtree` fix, Phase 5 hands-on verification + `live_clear`, the
> `connect_or_launch` readiness race, and the Phase 5 MCP tool surface --
> moved to [docs/HANDOFF_ARCHIVE.md](docs/HANDOFF_ARCHIVE.md) per the trim
> convention (see the note above the Session log below).

## ⚠️ Heads-up for the next agent

- **Every cookbook material now uses subgraphs (`group_into_subgraph` in
  `quality/author_helpers.py`); a new material should too, from the start.**
  Call it before `save_variant` returns, following `docs/AUTHORING.md`'s
  "Grouping into subgraphs" section, so it doesn't need a second retrofit
  pass later. `tests/test_cookbook_subgraph_gate.py` enforces this
  permanently (every cookbook material must carry >=1 `type: "graph"` node).
- **`quality/render_compare.py`'s `renders_match`/`grid_mean_abs_diff` proves
  builder-output-before matches builder-output-after -- it does NOT prove the
  tracked `.ptex` on disk matches what was there before your change.** If a
  builder's own graph is already stale/wrong before you touch it (as
  `f04_wool_knit`'s was), the comparison will still report a clean `0.0` even
  though the tracked artifact changes. If you're not sure whether a material
  was already stale, diff the tracked `.ptex` against a fresh build from the
  current builder BEFORE making any other change.
- **Run `quality/*.py` scripts from the repo root, not from inside
  `quality/`.** Running from inside `quality/` breaks `.env` lookup and
  produces spurious "unknown node type" errors.
- **`quality/cookbook_wood.py`/`cookbook_glass.py`/`cookbook_plastics.py`
  still build the catalog inside each builder function** (pre-dating the
  "build once, thread through" convention the other 7 categories use). Not
  broken, just inconsistent; wood is the natural first cleanup target (3
  rebuilds per run).
- **`group_into_subgraph` fails silently on a mistyped `member_names`
  entry** -- the intended node just stays top-level, no error raised. Double
  check member names against the actual node list before calling it.
- **`render_cookbook.py <label>` and `_make_previews.py <label>` operate on
  the WHOLE label, not just the case you're adding.** Adding one material to
  an existing category (e.g. `f08_donegal_tweed` to `cookbook-fabrics`) and
  running these regenerates and re-thumbnails every other case in that
  category too. Godot's own render is not perfectly deterministic run to
  run, so an unrelated case's thumbnail can come back byte-different with
  zero content change. Always `git status` after these before committing,
  and revert anything that changed only because it got swept up in the same
  label's regen.
- **`ambientcg.com` redirected to a malicious scareware page during this
  session** (a fake "McAfee Security" page at `securesweep.pro`, hit via
  the in-app Browser pane's `navigate`). Closed the tab immediately without
  interacting; switched to Wikimedia Commons for reference photos instead,
  which worked cleanly. Worth avoiding `ambientcg.com` until/unless
  verified safe again.
- **`docs/AUTHORING.md` now has an "Authoring from a reference photo"
  section** right after the main workflow list. If a future session is
  asked to build a material from an attached photo, read that section
  first, it's a decomposition rubric that plugs into the existing donor/
  topology vocabulary, not a separate pipeline.
- **`quality/author.py` is now a builders-only file; graph-surgery helpers
  live in `quality/author_helpers.py`.** If you're adding a new cookbook
  category or debug swatch, `from author_helpers import ...` the helpers
  (`load_example`, `node`, `set_gradient`, `set_param`, `save_variant`,
  `rewire`, `drop_conn`, `add_node`, `retype`, `_grad`), not `from author
  import ...`, that module now only exports the 12 Phase-3 `build_*`
  functions, `BUILDERS`, and `main()`.
- **Donor graphs (`beehive`, `crocodile_skin`, `dry_earth`, `metal_pattern_2`,
  `rock`, `rusted_metal`, `stone_wall`, `wood`, `wooden_floor`) load from
  `quality/donors/`, a tracked directory in this repo, not the external
  Material Maker checkout anymore.** If you add a 10th donor to any builder,
  vendor its `.ptex` into `quality/donors/` too (copy from
  `<MM_PROJECT_PATH>/material_maker/examples/<name>.ptex`), `load_example()`
  won't find it in the external checkout's path anymore. Browsing all 43 of
  Material Maker's bundled examples over MCP (`list_examples(source=
  "material_maker")`) and the Phase 1 gate test are unaffected by any of
  this, they still read live from the external checkout.
- **`list_examples` / `load_example` changed shape 2026-09-03.** `list_examples`
  returns `{"ok": True, "examples": [{"name", "source", "category"}]}` (not a list
  of names); `load_example` returns `{"ok": False, "error": ...}` for unknown
  names instead of raising, and tries `cookbook/` before Material Maker's bundled
  examples. Cookbook materials are edited by rebuilding with
  `quality/cookbook_<category>.py` then `quality/promote_cookbook.py`; edit the
  builder, never the tracked `.ptex` by hand (`--check` would flag it).
- **The 2026-08-29 8-angle code review found 10 verified correctness bugs.
  As of a prior cleanup session: 7 are fixed (findings 1-7 and 9), and 2 are
  ruled out as deliberate non-changes (#8, #10) with in-code reasons. That
  leaves none outstanding.** Recorded here so they aren't tribal knowledge
  living only in a conversation transcript. Ranked most severe first:
  1. **✅ FIXED.** `server.py` (`live_render_node_output`): the restore-original-wiring
     call after a preview wasn't checked for success — a failed restore used
     to report overall success while the live graph stayed wired to the
     temporary preview connection. Now checked; a failed restore reports
     `ok=False` with a message naming the live graph's actual state (still
     wired to the preview), while still attaching the render's own image if
     the render itself succeeded. New tests:
     `test_live_render_node_output_reports_a_failed_reconnect_restore`,
     `..._reports_a_failed_disconnect_restore`,
     `..._combines_render_and_restore_failures`.
  2. **✅ FIXED.** `server.py` (`live_apply`): only caught `(KeyError, TypeError)`
     from op handlers; a malformed op (e.g. a list where a parameters dict
     is expected) could raise an uncaught `AttributeError` from deep inside
     `validate_graph`'s `.items()` call, discarding the batch's
     already-succeeded results. `AttributeError` added to the caught tuple.
     New test: `test_live_apply_reports_a_malformed_op_field_as_data_not_a_raised_exception`.
  3. **✅ FIXED.** `server.py`: no atexit handler called `_live_session.close()`,
     orphaning a launched Godot process on unclean exit. Added
     `_close_live_session_atexit` + `atexit.register`; verified it fires at
     real interpreter shutdown (the `close()`→`_terminate` it calls was
     already integration-proven).
  4. **✅ FIXED.** `validator.py`: port-range validation only checked the
     upper bound. Now rejects a negative `from_port`/`to_port` too; message
     names the valid range (`0..N-1`).
  5. **✅ FIXED.** `overlay.py` (`ensure_overlay`): a rebuild that failed
     partway left an ambiguous marker-less partial. Now removes the
     half-built overlay and re-raises (unambiguous: complete overlay or
     none). Cleanup is best-effort, can't mask the original error.
  6. **✅ FIXED (docstring).** `live.py` (`render`) always returns an empty
     `log_tail` on the live path (live Godot output goes to `mm_live.log`,
     whole-process). Docstrings in `live.render`/`live_render_node_output`
     corrected to say so and point at `mm_live.log`, rather than populating
     `log_tail` from a possibly-stale, misleading whole-process tail.
  7. **✅ FIXED.** `live.py`: the five mutation ops now default to a 30s
     socket timeout (was 5s), so a cold-launch shader compile doesn't
     spuriously time out. 30s is a ceiling, half `render()`'s proven 60s;
     read-only one-shots (`ping`/`get_graph`/`clear_graph`) stay 5s.
     PLAUSIBLE, not reproduced.
  8. **⛔ RULED OUT (non-bug).** `_cmd_clear_graph`'s `graph_edit==null`-only
     guard is CORRECT, not a missing `generator==null` check. `new_material()`
     CREATES a fresh generator (`clear_material()`→`create_gen`); it doesn't
     read one like the mutating siblings. Adding the guard would refuse to
     clear exactly the graph-less state a clear recovers. Confirmed against
     Material Maker's `graph_edit.gd:690-724`. Annotated in-code.
  9. **✅ FIXED.** `live.py` (`_launch_overlay`): the parent's `mm_live.log`
     handle is now closed (try/finally) after Popen dups the fd, was leaking
     one fd per launch.
  10. **⛔ RULED OUT (deliberate).** `catalog_builder.py`'s `generic_size or 1`
      coercion is intentional: an explicit `0` would build an input-less
      (broken) node, so treating a falsy value as the default 1 is safer than
      passing 0 through. No bundled `.mmg` triggers it. Annotated in-code.
      PLAUSIBLE.
  The full teardown also found real cleanup/duplication issues (a dead
  `Graph` class in `graph.py`, three byte-for-byte-duplicated helper pairs,
  an unused `list_node_types` tool) — see the delivered teardown file for
  those; they were ranked below correctness bugs and not re-verified
  individually here.
- **`ensure_overlay`'s rebuild path now clears read-only file attributes
  before `rmtree` -- fixed a prior session, real and load-bearing, not
  theoretical.** The overlay is a full copy of the real git checkout at
  `z-Git\material-maker`; git marks `.git/objects/pack/*.idx` read-only,
  and `shutil.rmtree` can't delete a read-only file on Windows without
  help. Fixed via a `_clear_readonly()` helper in `overlay.py`, called right
  before `rmtree`. If `live_start`/`connect_or_launch` ever fails again with
  a bare, detail-free MCP error, reproduce directly via
  `.venv\Scripts\python.exe -c "from mm_mcp import live; live.connect_or_launch()"`
  rather than trusting the MCP tool's error message -- it swallows
  exception detail on a raise; the real traceback only shows up outside it.
- **`ping`'s response has a `has_graph` field alongside `ready`, and they
  mean different things -- don't conflate them.** `ready` is purely
  "main_window resolved." `has_graph` is "a graph tab actually exists"
  (`get_current_graph_edit()`/`.generator` non-null). `connect_or_launch`
  requires both before declaring a session usable.
- **`server.py` has four live MCP tools consuming `live.py`:**
  `live_start`/`live_get_graph`/`live_apply`/`live_render`, all going through
  a shared `_ensure_live_session(cfg, launch_timeout=60.0)` helper that
  calls `live.connect_or_launch` fresh every time. **Do not read
  `server._live_session` directly** to check on a launched process --
  always call `_ensure_live_session(cfg)` yourself, the module global is
  internal bookkeeping, not a public handle.
- **`live_apply(ops)` dispatches via `_LIVE_OP_HANDLERS`, a dict keyed by
  `op["op"]`** (`"add_node"`/`"connect_nodes"`/`"set_param"`), stops at the
  first failing op, and reports a malformed op as a data-shaped error rather
  than raising. If you add a fourth op kind, add its handler to that dict
  and nowhere else.
- **Run tests with `.venv\Scripts\python.exe`** (or activate the venv).
  Fast suite: `pytest -q -m "not integration"` (444 passed, 23 deselected).
  `pytest -q` adds the Godot-launching integration tests.
- **`mm-mcp --check`** is the setup doctor (green/red preflight); `--version`,
  `--help` also work. Build/release tooling lives in the `release` extra
  (`pip install -e .[release]` -> build, twine).
- All Phase 1-2 render gotchas still hold (see CLAUDE.md): `--export-material`,
  `_console.exe`, no `--headless`, `steam_appid.txt`.
- `normal_map` is a compound node; real params `param0` (size), `param1`
  (strength), `param2`, `param4` (0 = real relief for analytic generators,
  1 = flat) -- NOT `amount`/`size`. Voronoi **output port 2** = `rand3`
  random-per-cell (the fleck/speckle source); ports 0/1 are distance fields.
- **Cookbook growth pattern** (`quality/cookbook_<category>.py` +
  `render_cookbook.py` + `_make_previews.py`) is separate from the frozen
  Phase 3 test set on purpose, copy it for the next category rather than
  touching `test_set.json`/`run_case.py`/`author.py`'s `BUILDERS` dict. See
  `quality/README.md` for the short version and `docs/AUTHORING.md` for every
  recipe + the levers that didn't pan out.

---

## 🕓 Session log

> 📦 **Trim convention (adopted 2026-08-29):** this doc keeps at most the 3
> most recent "Changed this session" write-ups and the 5 most recent
> session-log entries below. When a new wrap-up entry would push either
> section past that cap, the oldest entry moves out verbatim (no
> summarizing) into [docs/HANDOFF_ARCHIVE.md](docs/HANDOFF_ARCHIVE.md)
> instead of letting this doc grow unbounded -- flagged as a real pickup
> cost by the 2026-08-29 teardown (Maintainer lens). **33 older entries are
> now archived there**, from the 2026-09-04 v0.5.0 release + AUTHORING split
> session back through the project's Phase 1-2 kickoff on 2026-08-25.


### 2026-09-04 (leather + terrain bug fixes): the three bugs the retrofit left behind, closed
- `pickup` reconciled clean (`main` at `8cf496a`); Grayson's command was
  `+ fix the leather and terrain bugs`, the three pre-existing bugs the
  subgraph retrofit surfaced and correctly left unfixed.
- Read the three recipe cards + both builders + the `wood` donor wiring, then
  one advisor consult before editing. Advisor confirmed t01/l02, flagged the
  whole-label render-sweep hazard, re-promotion (non-zero diffs on purpose this
  time), and rewriting the three now-wrong cards.
- **t01_sand_dunes:** dropped the `blend_0 -> Material:1` metallic wire and set
  `Material.metallic = 0` (donor scalar defaults to 1). Verified the ORM
  metallic channel reads flat 0.
- **l02_distressed_two_tone:** swapped port0/port1 on both blends; before/after
  render confirmed the field flipped to mostly-dark-saddle with lighter worn
  rubs. Bonus: the exposed wear-strength param now controls the wear layer.
- **l05_quilted_leather:** swapped port0/port1 on `blend_alb_q` (dark now in the
  seams). Sent Grayson before/after; the `sin*sin` geometry makes round pads on
  a dark grid, and he chose the swap (option 1) over relabeling. Documented the
  geometry limitation and the deferred `blend_h_q` 35% height-weighting question.
- Builder-only edits, `render_one.py` per fixed case to dodge the sweep, three
  cards rewritten, fast suite 505 passed, `promote --check` in sync, `git status`
  clean of incidental churn. One commit (`5cd9e0b`), pushed on "push it and wrap
  up." Then this wrap-up.

### 2026-09-04 (cookbook subgraph retrofit): the node graph stops scaring people, one Ctrl+G at a time
- `pickup` reconciled clean (`main` at `c3cc3f2`). Grayson picked backlog item
  #2 from the briefing, "scope Material Maker for dummies."
- `brainstorming` classified it architectural (a new interaction surface, no
  existing flow to extend). A dead-end investigation ("generic parameters,"
  which turned out to be Material Maker's unrelated variadic-port mechanism)
  surfaced the real answer: a native subgraph/`Ctrl+G` mechanism already used
  by 50 of Material Maker's own bundled compound nodes. Decomposed into two
  sequenced sub-projects (a subgraph authoring lever now, a live web companion
  later that reads its slider definitions from the first). Grayson chose to
  retrofit all 46 existing materials, not just apply the lever going forward,
  upgrading sub-project 1 from bounded to architectural.
- Spec + 12-task plan -> `subagent-driven-development` on branch
  `cookbook-subgraph-retrofit` (feature branch in the main checkout, not a
  worktree, same editable-`.venv` reason as prior sessions). Task 1 built
  `group_into_subgraph` + a tolerance-based render comparison utility. A
  pilot task proved the whole process on `glass` before fanning out to the
  other 9 categories, smallest first, `stone`/`terrain` (8 materials each)
  last. Every category hit an exact `0.0` render match; every category's
  named risk (sf03's blend mask, stone's `warp_0` sensitivity, f08's fleck
  separation, t06's glow chain) was independently re-verified by task review
  and held.
- One task-level fix round (Task 7/painted-metal): a commit message claimed
  a real thumbnail file-size change was explained by a stale pre-fix render;
  the reviewer found the chronology was backwards and traced the actual,
  benign cause (old thumbnails were un-downscaled 2048x2048, new ones
  correctly 512x512). Fixed via a new documentation commit, not an amend.
- Final whole-branch review (opus) built an independent flatten-diff harness
  across all 46 materials in all 13 commits: 45/46 matched pre-branch `main`
  byte-for-byte; `f04_wool_knit` didn't, but the change was a real, incidental
  correction of an already-stale tracked artifact, not a regression -- fixed
  via disclosure (a corrected recipe-card parity claim), not an artifact
  change. Two other real, pre-existing, unrelated bugs surfaced during the
  retrofit and correctly left unfixed (leather's l02/l05 reversed composite
  layers, terrain's t01 wood-donor metallic wiring) -- flagged in this
  handoff's Next-step section so they don't only live in a recipe card.
- Merged `--no-ff` (`034aeaf`), pushed, branch deleted, SDD workspace
  removed. Fast suite 453 -> 505. Then this wrap-up.

### 2026-09-03 (plastics category + Donegal tweed): a smooth surface and a fleck lever, both closing out the same backlog batch
- `pickup` reconciled clean (`main` at `5239283`). Grayson picked "1 + 4"
  from the briefing's numbered options: the plastics cookbook entry and
  two-color tweed.
- `brainstorming` (bounded path, no plan doc): two clarifying questions
  settled the specifics (glossy vs. matte vs. textured plastic; flecked
  Donegal-style vs. two-tone herringbone for the tweed), then a short
  in-chat design, approved.
- `p01_glossy_plastic`: built from scratch (no donor fits a "smooth,
  patternless" surface), narrow near-single-color red albedo, low
  roughness, near-zero relief. Hit and fixed the same scalar-roughness ORM
  gap `gl01_frosted_glass` did. Preview sent, approved first try.
- `f08_donegal_tweed`: plain-weave base plus a separate voronoi node for
  sparse cream/rust flecks via the port-2 rand3 lever, composited with
  `blend`. First preview read too sparse (~4 flecks per crop); revised the
  mask threshold and added a second fleck tone, second preview approved.
- Both promoted, carded, thumbnailed, README counts updated (44/nine to
  46/ten). Reverted an unrelated `f04_wool_knit` thumbnail regeneration
  (render non-determinism, not a real change) before committing. Fast
  suite 447 -> 453. Committed (`68c51dc`) and pushed on explicit
  instruction ("push it + wrap"). Then this wrap-up.

### 2026-09-03 (reference-photo authoring workflow + glass cookbook): the assistant learns to read a photo, not just a sentence
- `pickup` reconciled clean (`main` at `692057b`). Grayson picked backlog
  item #4, "image-to-material decomposition," from the briefing's numbered
  options.
- `brainstorming` classified it architectural at first (a new subsystem),
  then a scoping question collapsed it to bounded: the decomposition
  reasoning happens in Claude's own vision during the chat session itself,
  not a new server-side vision tool, so the real deliverable is a
  documented workflow addition to `docs/AUTHORING.md`, not a subsystem.
  Grayson also chose to include a worked proof (not guidance-only) and to
  commit the proof as a real cookbook entry (not throwaway).
- Sourced a CC-BY-SA 4.0 reference photo. An early attempt to browse
  `ambientcg.com` hit a malicious ad redirect to a fake "McAfee Security"
  scareware page (`securesweep.pro`); closed the tab immediately without
  interacting and switched to Wikimedia Commons, which worked cleanly.
- Wrote the "Authoring from a reference photo" section, then authored
  `cookbook/glass/gl01_frosted_glass` end to end from the photo: decomposed
  it against the new rubric, matched it to `dry_earth`'s connected-crack-
  network topology at a much finer scale, built and rendered the graph,
  judged it in the 3D preview (sent to Grayson for a look), promoted it
  through `promote_cookbook.py`. Fast suite 444 -> 447. Committed and
  pushed to `main` (`9a02a8d`) on Grayson's explicit go-ahead.
- Wrote the session's commons log entry, then Grayson asked for one more
  fix: a stale gitignored build artifact (`f04_wool_knit`, unrelated to
  this session) was making `promote_cookbook.py --check` report false
  drift. Cleared it, confirmed clean, then this wrap-up.

### 2026-09-03 (v0.6.0 release + author.py split + donor vendoring): the pipeline stops depending on the external checkout
- `pickup` reconciled clean (`main` at `677f852`), then merged release-please
  PR #3 straight away (0.6.0, pure metadata bump) since it was the standing
  next step. Grayson picked options 1 + 2 from the briefing: decide the two
  deferred hygiene items, and scope the `author.py` refactor.
- Asked Grayson directly: fold `examples/` into the cookbook (chosen), keep
  `docs/HANDOFF_ARCHIVE.md` (chosen, no longer an open item). `brainstorming`
  on both remaining tasks surfaced the scope correction: "examples/" meant
  `cfg.examples_dir` (Material Maker's 43 bundled demos in the external
  checkout), not this repo's own `examples/` folder. Auditing every
  `load_example()` call site found only 9 of 43 are load-bearing donors.
  Grayson chose to vendor just those 9 and keep browsing/the gate live
  against the external checkout.
- Spec written and approved
  (`docs/superpowers/specs/2026-09-03-vendor-donor-examples-design.md`),
  4-task plan (`docs/superpowers/plans/2026-09-03-author-helpers-donor-vendor.md`)
  -> `subagent-driven-development` on branch `author-helpers-donor-vendor`
  (feature branch in the main checkout, not a worktree, same editable-`.venv`
  reason as the AUTHORING split). Task 1 extracted the helpers into
  `author_helpers.py` (the implementer caught and fixed a real gap in my own
  brief: it omitted `_grad`/`_ROOT`, which `author.py`'s own remaining code
  still needs). Task 2 repointed 10 consumer files. Task 3 vendored the 9
  donors (one fix round: a required test file was created but never
  committed, because the plan's own commit command omitted it, fixed with a
  follow-up commit). Task 4 repointed `load_example()`, proved byte-identical
  builder output before/after via a real before/after hash comparison.
- Final whole-branch review (opus): "with fixes" -- 1 Important + 6 Minor,
  all stale "author.py" doc references left over from the split (e.g.
  `quality/README.md`'s Cookbook-growth section). One fix wave, scoped
  re-review clean. Fast-forward-merged to `main` (`54693fb`), pushed, branch
  deleted, SDD workspace removed. Fast suite 424 -> 444.
- Then this wrap-up (HANDOFF baton, memory, commons log).

_(Older entries continue in [docs/HANDOFF_ARCHIVE.md](docs/HANDOFF_ARCHIVE.md).)_

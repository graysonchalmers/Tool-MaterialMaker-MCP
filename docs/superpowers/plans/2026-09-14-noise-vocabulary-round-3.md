# Noise Vocabulary Round 3 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship six more cookbook proof materials on catalog noise/pattern nodes the cookbook has never used, continuing round 1 (`docs/superpowers/plans/2026-09-06-noise-vocabulary-and-core-toolbox.md`, merged `0169446`) and round 2 (`docs/superpowers/plans/2026-09-13-noise-vocabulary-round-2.md`, merged `282a834`). Raises live coverage from 14/53 to 20/53 curated noise/pattern generator types.

**Architecture:** Everything reuses existing infrastructure; no new subsystem. Unlike round 2 (which mostly retyped a donor's existing base generator), all six targets here are used via the from-scratch skeleton `quality/author_helpers.py::_from_scratch_noise_material` + `retype()`, the same pattern `t09_rippled_wet_sand` (`quality/cookbook_terrain.py`) and `m03_brushed_titanium` (`quality/cookbook_metal.py`) already established for nodes with no natural donor to clone. Each builder lands in the category's existing `quality/cookbook_<category>.py` file (registered in its `BUILDERS` dict), following the established clone/retype-or-build-from-scratch -> `group_into_subgraph` -> `rename_nodes` -> `save_variant` -> `promote_cookbook` pipeline. Design approved in chat 2026-09-14 (bounded scope, no separate spec file, same "surface-and-expand, not architectural-new" ruling as rounds 1-2).

**Tech Stack:** Python 3.13, Material Maker node-graph JSON (`.ptex`), Godot 4.7.1 headless render, pytest.

**Spec:** Approved in chat 2026-09-14 (this plan is the durable record). Supporting evidence gathered during brainstorming (real node parameter defaults, not fabricated):
- `mcp__material-maker__describe_node` output for `scratches`, `splatter`, `skewed_bricks`, `shape` (full catalog parameter specs).
- `z-Git/material-maker/addons/material_maker/nodes/{directional_noise,dirt,crystal}.mmg` (these three describe as opaque `param0`/`param1`/`n_scale`/`d_scale` in the catalog because they are compound `graph`-type nodes; their real defaults come from each file's own `gen_parameters` remote-node block).
- `quality/cookbook_terrain.py::build_t09_rippled_wet_sand` (the from-scratch + retype + two-subgraph-group template every task below follows).
- `quality/cookbook_metal.py::build_m03_brushed_titanium` (a second from-scratch precedent, single-group variant).
- `cookbook/glass/gl03_shattered_crystal.md` (recipe-card prose/structure template).

**A scope correction found during research:** the originally-discussed sixth target, `custom_tiles`, requires an `sdf2d`-typed `shape` input (verified via `describe_node`) that only the SDF node family can produce, and `docs/AUTHORING.md` rules the entire SDF family out of scope. Swapped for `skewed_bricks` (verified standalone-usable via `describe_node`: all three of its inputs -- `mortar_map`, `bevel_map`, `round_map` -- are optional `f` maps with function defaults, not required `sdf2d`). This was flagged to Grayson in chat before finalizing scope.

## Global Constraints

- **Render mechanics:** one Godot process at a time; pass `render()`/`render_tracked` an ABSOLUTE outdir; never launch a render from `python -c`; in the Git Bash tool `taskkill //F //IM Godot_v4.7.1-stable_win64_console.exe` (and the GUI exe) is the recovery. Subagents lose long Godot runs: poll the output file rather than blocking on return.
- **Quality scripts run as `python -m quality.<module>` from the repo root** with `pip install -e .` already done; running from inside `quality/` breaks `.env` lookup.
- **Godot is not byte-deterministic.** A single render_compare failure on an unchanged graph is a re-render first, a regression second.
- **`blend` semantics:** shows port-1 where its port-2 mask is 0 and port-0 where it is 1; put the majority layer on port-1. Opacity = amount x mask. `normal_map` `param4=0` is the flat-normal fix (needed on EVERY task here: `_from_scratch_noise_material`'s skeleton defaults `param4=1`, which renders flat for a directly-fed analytic generator); `param1` is relief strength.
- **Verify metallic/roughness/AO by reading the exported ORM channel** with `quality/pngread.py`, not by eye.
- **Node names never affect renders** (MM seeds from node position); every cookbook node must be role-named (`quality/naming.py` gate); never rename a subgraph (`type=="graph"`) node.
- **A compound `graph`-type node (like `directional_noise`, `dirt`, `crystal`) can still be the target of `retype()`** as long as its output port 0 type matches what the old node fed (all three expose exactly one `f` output on port 0, same as `perlin`'s port 0, so the swap is connection-safe against `_from_scratch_noise_material`'s skeleton).
- **`splatter` and `skewed_bricks` are compositing/pattern nodes with input ports**, not bare generators: `splatter` requires an actual pattern wired into its `in` port (leaving it unconnected renders a blank field, per its shader's literal `"0.0"` fallback); `skewed_bricks`'s three inputs are genuinely optional (function defaults), so it works unconnected. See Task 5 for the exact wiring `splatter` needs.
- **Diagnose any unknown node's real output range before tuning against it** if a first render looks wrong -- these six are catalog-verified for parameter shape but not yet render-tested at material scale; treat the given starting params as a verified starting point, not a guarantee of the final look.
- **Grayson is the visual judge.** No material task self-certifies its look. Each returns rendered 3D previews (`render_preview`, and optionally `render_preview_sweep` now that it is ✅ verified) that get sent to Grayson via SendUserFile; he approves or redirects before that material is committed. The implementer subagent has no chat channel to Grayson -- it stops after authoring + promoting; the controller session renders, self-screens, and handles the SendUserFile/approval round-trip.
- **`.env` is gitignored, never echo it.** Donors load from `quality/donors/` (tracked); these six tasks do not need a donor (from-scratch skeleton).
- **Copy rule:** README/AUTHORING state all counts in digits; a test recomputes them from the tree. Change the tree, then the number, never the reverse.
- **No em dashes in any doc or commit message.**

---

## Phase A: Six proof materials

Each material is one task. Shared shape for every material task (do not restate per task):

1. In the category's `quality/cookbook_<category>.py`, add `build_<id>(catalog: dict) -> str`. Start from `_from_scratch_noise_material(perlin_params, albedo_points, metallic=..., roughness=..., normal_amount=...)` (import from `quality.author_helpers`), then `retype(g, "perlin_0", "<target_type>", <verified_starting_params>)` to swap in the target node (or, for Task 5's `splatter`, follow that task's extra wiring steps). Immediately `set_param(g, "normal_map_0", "param4", 0)` (the flat-normal fix).
2. Add a flat roughness texture so an ORM map exports (the from-scratch skeleton only sets `Material`'s roughness as a scalar): `add_node(g, "rough_const", "colorize", {"gradient": _grad([(0.0, R, R, R), (1.0, R, R, R)])})`, wire the target node's output into it, then `g["connections"].append({"from": "rough_const", "from_port": 0, "to": "Material", "to_port": 2})` (same as `t09_rippled_wet_sand`).
3. `group_into_subgraph` twice (color group: generator + albedo colorize; finish group: normal_map + rough_const), per each task's grouping list below; `rename_nodes(g, <TASK>_NAMES)`; `save_variant(g, _LABEL, "<id>", 1)`.
4. Register the builder in the category file's `BUILDERS` dict.
5. Run `python -m quality.cookbook_<category> <id>` to write `quality/authored/cookbook-<category>/<id>/v1.ptex`.
6. Validate (the `mm-mcp` `validate` tool, or a pure `validate_graph` call -- `python -c` is banned for renders but fine for a pure validate) and confirm ZERO errors.
7. Render with an ABSOLUTE outdir (`render_graph` or `render_tracked`) and build a `render_preview` composite (controller does this, not the implementer -- see the note above).
8. Controller: self-screen for gross misses/variety collisions, then SendUserFile the preview to Grayson and WAIT for approval or redirect (iterate the builder on his feedback, re-render).
9. Once approved: write the prose recipe card `cookbook/<category>/<id>.md` (technique, gotchas found, how it differs from category siblings, honest limitation, "See also" -- see `cookbook/glass/gl03_shattered_crystal.md` for the shape).
10. `python -m quality.promote_cookbook cookbook-<category>` to copy the `.ptex` and generate the card's node table.
11. Confirm `python -m quality.promote_cookbook --check` and `python -m quality.naming --cookbook <category>` are clean.
12. Commit.

Exact gradient/palette values are tuned by render-and-look, not fabricated here; each task gives the technique, the verified starting node params (from `describe_node` or the node's own `.mmg` source), the category, and the gates.

### Task 1: `m04_scratched_steel` (scratches, metal)

**Files:**
- Modify: `quality/cookbook_metal.py`
- Create: `cookbook/metal/m04_scratched_steel.{md,ptex}` (the `.ptex` via promote)

**Technique:** From-scratch skeleton, `retype(g, "perlin_0", "scratches", {"length": 0.25, "width": 0.5, "layers": 4, "waviness": 0.5, "angle": 0, "randomness": 0.5})` -- these are `scratches`'s own catalog defaults (verified via `describe_node`), a standalone generator (no inputs) with `length`/`width`/`layers`/`waviness`/`angle`/`randomness` all real, independently tunable float params. This is a genuinely different technique from `m02_brushed_aluminum` (continuous parallel streaks from a stretched `perlin`) and `m03_brushed_titanium` (continuous streaks from `noise_anisotropic`): `scratches` composes discrete, individually-angled, wavy scratch marks in layers, reading as scuffed/scored metal rather than a uniform brushed finish. Cool gray steel palette (slightly darker/less uniform than m02's aluminum or m03's titanium, since scored steel is rougher-looking than a brushed finish), metallic=1.0 scalar (uniform metal, same reasoning as m02/m03: no paint layer to mask off), moderate-to-high roughness (scored metal is not glossy), and push `layers`/`randomness` up during iteration if the first render reads too clean/regular -- start from the verified defaults above, not a guess past them.

**Grouping:** `("scratch_finish", "Scratch Finish", [generator, albedo colorize])`, `("surface_detail", "Surface Detail", [normal_map, rough_const])`.

- [ ] **Step 1-12:** Shared material shape above, category `metal`. Commit `feat(cookbook): m04_scratched_steel (scratches node)`.

### Task 2: `f11_corduroy` (directional_noise, fabrics)

**Files:**
- Modify: `quality/cookbook_fabrics.py`
- Create: `cookbook/fabrics/f11_corduroy.{md,ptex}`

**Technique:** From-scratch skeleton, `retype(g, "perlin_0", "directional_noise", {"param0": 0, "n_scale": 1, "param1": 11})` -- these are `directional_noise`'s own defaults read from `directional_noise.mmg`'s `gen_parameters` block (`param0` selects one of three internal composite sub-networks via a `switch`, default 0 = "Noise 1"; `n_scale` is an overall scale multiplier, default 1, range 1-8; `param1` is output resolution, default 11, matching the skeleton's own buffer size). "Noise 1" internally composites several `fbm2` layers with strongly asymmetric x/y scales (e.g. one branch is `scale_x=4*n_scale, scale_y=72*n_scale`), which is exactly the kind of tight parallel-ribbing corduroy needs -- a genuinely different structural family from every other fabric in this category (weave-based `f01`/`f03`/`f07`/`f08`, cellular-`fbm`-based `f09`/`f10`, smooth-pile `f06`). If "Noise 1" at these defaults reads too irregular/blotchy rather than as clean parallel ribs, try `param0=1` or `param0=2` ("Noise 2"/"Noise 3", the other two internal sub-networks) before tuning `n_scale` -- render each in isolation first (a `render_node_output` on just this retyped node) rather than guessing blind. Warm tan or burgundy corduroy palette, soft matte roughness, moderate `normal_map param1` for the characteristic raised-rib relief (stronger than f09's soft flannel nap, since corduroy ribs are a real physical ridge).

**Grouping:** `("corduroy_rib", "Corduroy Rib", [generator, albedo colorize])`, `("corduroy_finish", "Corduroy Finish", [normal_map, rough_const])`.

- [ ] **Step 1-12:** Shared material shape above, category `fabrics`. Commit `feat(cookbook): f11_corduroy (directional_noise ribbing)`.

### Task 3: `t10_packed_dirt` (dirt, terrain)

**Files:**
- Modify: `quality/cookbook_terrain.py`
- Create: `cookbook/terrain/t10_packed_dirt.{md,ptex}`

**Technique:** From-scratch skeleton, `retype(g, "perlin_0", "dirt", {"param0": 0, "d_scale": 1, "param1": 11})` -- `dirt`'s own defaults read from `dirt.mmg`'s `gen_parameters` block (`param0` selects one of three internal composite sub-networks via a `switch`, default 0 = "Dirt 1"; `d_scale` is an overall scale multiplier, default 1, range 1-8; `param1` is output resolution, default 11). "Dirt 1" internally composites a hexagonal `shape` field with an `fbm2` noise layer through a tiler, producing irregular soft-edged blotchy patches -- a genuinely new terrain topology this category has never shipped: `t01`/`t05`/`t06`/`t08` are the connected-crack/packed-cell voronoi-plate family (per project memory's topology-first authoring lesson), `t02`/`t04` are broad isotropic perlin rolls, `t09` is anisotropic banding. Irregular blotchy patches is none of those. Muted brown/tan packed-earth palette, high matte roughness (bare dirt, not the wet-sheen low roughness `t09` uses), moderate `normal_map param1` for a worn, slightly uneven ground relief (not the hard crack relief of the voronoi-plate family). If "Dirt 1" reads too regular/hexagonal at these defaults, try `param0=1`/`param0=2` before tuning further.

**Grouping:** `("dirt_pattern", "Dirt Pattern", [generator, albedo colorize])`, `("dirt_finish", "Dirt Finish", [normal_map, rough_const])`.

- [ ] **Step 1-12:** Shared material shape above, category `terrain`. Commit `feat(cookbook): t10_packed_dirt (dirt node)`.

### Task 4: `gl04_raw_crystal_cluster` (crystal, glass)

**Files:**
- Modify: `quality/cookbook_glass.py`
- Create: `cookbook/glass/gl04_raw_crystal_cluster.{md,ptex}`

**Technique:** From-scratch skeleton, `retype(g, "perlin_0", "crystal", {"param0": 16, "param1": 16})` -- `crystal`'s own defaults read from `crystal.mmg`'s `gen_parameters` block (`param0`/`param1` are Scale X/Scale Y, both defaulting to 16, feeding two independently-seeded internal `voronoi` fields at `scale_x=scale_y=16, stretch=0.85` combined via math ops into one crystalline cell pattern). This is a fourth, distinct glass topology: `gl01_frosted_glass` is a connected sandblast crack network off plain `voronoi` (soft, diffuse), `gl02_cut_gem` is faceted `voronoi_triangle` cells (flat, uniform, crisp edges, no cracks), `gl03_shattered_crystal` is a dense continuous `shard_fbm` fracture field. `crystal`'s two-voronoi composite should read as a raw, natural crystal-cluster formation (like an amethyst geode or raw quartz cluster) rather than any of those three cut/faceted/fractured looks -- distinguish it during iteration by keeping cell boundaries irregular and clustered rather than uniform-grid-like. Jewel-tone (amethyst purple, or clear/smoky quartz) or icy translucent-white palette, low roughness (glossy crystal faces), sharp `normal_map param1` for real crystalline facet relief.

**Grouping:** `("crystal_pattern", "Crystal Pattern", [generator, albedo colorize])`, `("crystal_finish", "Crystal Finish", [normal_map, rough_const])`.

- [ ] **Step 1-12:** Shared material shape above, category `glass`. Commit `feat(cookbook): gl04_raw_crystal_cluster (crystal node)`.

### Task 5: `pm06_splatter_finish` (splatter, painted-metal)

**Files:**
- Modify: `quality/cookbook_painted_metal.py`
- Create: `cookbook/painted-metal/pm06_splatter_finish.{md,ptex}`

**Technique:** `splatter` is NOT a bare generator -- it requires a real pattern wired into its `in` port (an unconnected `in` renders as a blank field, per its shader's literal `"0.0"` fallback default, verified via `describe_node`'s input list). Build from the skeleton, but retype `perlin_0` to a `shape` node instead of the target directly: `retype(g, "perlin_0", "shape", {"shape": 0, "radius": 1, "edge": 0.2})` (a Circle, `shape`'s own catalog defaults). Then `add_node(g, "splatter_0", "splatter", {"count": 24, "inputs": 0, "scale_x": 1, "scale_y": 1, "rotate": 180, "scale": 0.4, "value": 0.6, "variations": true})` (pushed up from `splatter`'s bare catalog defaults of `count=10, rotate=0, scale=0, value=0.5, variations=false` -- a real industrial spray-splatter finish needs randomized rotation/scale/value per splat, which the bare defaults do not provide) and wire it in: `g["connections"].append({"from": "perlin_0", "from_port": 0, "to": "splatter_0", "to_port": 0})` (feeds the Circle shape into `splatter`'s `in` port), then `rewire(g, "colorize_0", 0, "splatter_0", 0)` and `rewire(g, "normal_map_0", 0, "splatter_0", 0)` (repoint the skeleton's downstream albedo/normal chain from the shape onto the splatter output). Leave `splatter`'s `mask` port (`to_port` 1) unconnected -- its literal `"1.0"` default means "no masking," which is correct here (splatter everywhere across the panel). This produces randomly placed, scaled, and rotated circular splats -- a genuine spray-splatter industrial finish, distinct from every existing painted-metal material (`pm01` powder-coat orange-peel, `pm02` automotive enamel, `pm03` chipped paint, `pm04` hammertone, `pm05` scuffed panel -- none use a discrete-splat compositing technique). Two-tone palette (base coat color + a contrasting splatter color, e.g. dark base with light paint-splatter flecks or vice versa), semi-gloss roughness, subtle `normal_map param1` for the splat droplets' slight build-up relief (not flat, but not hard either -- paint droplets are a thin raised texture).

**Grouping:** `("splatter_pattern", "Splatter Pattern", [`shape`-retyped node, `splatter_0`, albedo colorize])`, `("splatter_finish", "Splatter Finish", [normal_map, rough_const])`.

- [ ] **Step 1-12:** Shared material shape above (with this task's extra wiring in step 1), category `painted-metal`. Commit `feat(cookbook): pm06_splatter_finish (splatter node)`.

### Task 6: `man03_mosaic_tile` (skewed_bricks, ceramic)

**Files:**
- Modify: `quality/cookbook_ceramic.py`
- Create: `cookbook/ceramic/man03_mosaic_tile.{md,ptex}`

**Technique:** From-scratch skeleton, `retype(g, "perlin_0", "skewed_bricks", {"rows": 6, "columns": 3, "offset": 0.5, "randomness": 1, "mortar": 0.1, "bevel": 0.1, "round": 0, "corner": 0.3})` -- `skewed_bricks`'s own catalog defaults (verified via `describe_node`). Unlike `custom_tiles` (dropped from scope, see the plan header), `skewed_bricks`'s three inputs (`mortar_map`, `bevel_map`, `round_map`) are all genuinely optional `f` maps with function defaults, so it works standalone. `skewed_bricks`'s `randomness` param (default 1, per-tile positional jitter) is the key differentiator from the category's existing `man02_ceramic_hex_tiles` (perfectly regular hex grid, zero jitter): pushed toward its default of 1, courses of rectangular tiles sit slightly offset/skewed from a perfect grid, reading as a hand-set or reclaimed mosaic rather than a machine-uniform hex tile. White or earth-tone tile palette with a distinct dark mortar/grout line (mortar param controls grout width), low roughness on tile faces vs. higher roughness in the grout (same face-vs-grout roughness-inversion technique `man02` already uses), moderate `normal_map param1` for recessed-grout relief.

**Grouping:** `("mosaic_pattern", "Mosaic Pattern", [generator, albedo colorize])`, `("mosaic_finish", "Mosaic Finish", [normal_map, rough_const])`.

- [ ] **Step 1-12:** Shared material shape above, category `ceramic`. Commit `feat(cookbook): man03_mosaic_tile (skewed_bricks node)`.

---

## Phase B: README/AUTHORING integration

### Task 7: Update README counts and regenerate the contact sheet

**Files:**
- Modify: `README.md` (the three count sentences)
- Modify: `docs/images/cookbook-contact-sheet.png` (regenerate)

**Interfaces:**
- Consumes: the six new materials from Phase A (count is now 71; category count stays 12).

- [ ] **Step 1: Regenerate the contact sheet**

Run `python -m quality.contact_sheet` (confirm the exact entrypoint by reading the module first, per rounds 1-2's Task 9/10). It must include all 71 materials. Save as 8-bit palette PNG (pinned lesson from teardown #3).

- [ ] **Step 2: Update the three README count strings**

`README.md`: `"The cookbook is 65 materials across 12 categories"` -> 71; `"**The full cookbook (65 materials:"` -> 71; `"a gallery of the 65"` -> 71.

- [ ] **Step 3: Run the count gate**

Run: `python -m pytest tests/test_readme_counts.py -v`
Expected: all pass.

- [ ] **Step 4: Commit**

```bash
git add README.md docs/images/cookbook-contact-sheet.png
git commit -m "docs(readme): 71-material counts + regenerated contact sheet"
```

### Task 8: AUTHORING.md names the six new materials + coverage numbers rise

**Files:**
- Modify: `docs/AUTHORING.md` ("Noise vocabulary" section: the live-coverage paragraph, and a new sentence naming the round-3 materials, mirroring the round-2 sentence style)

**Interfaces:**
- Consumes: Phase A's six materials; `quality.node_usage_audit.audit()`'s live numbers.

- [ ] **Step 1: Re-run the audit and update the coverage line's digits**

Run: `python -m quality.node_usage_audit`. Update the live-coverage paragraph's digits (`N of M curated noise/pattern generator types`) to the new live `N` (should be 20, since all six of this round's targets -- `scratches`, `directional_noise`, `dirt`, `crystal`, `splatter`, `skewed_bricks` -- are genuinely new top-level node types, unlike round 2 where most were new enum modes of already-counted types; confirm against the real `noise_used` list, do not assume).

- [ ] **Step 2: Name the six round-3 materials**

Add a new sentence naming the six: `m04_scratched_steel` (scratches), `f11_corduroy` (directional_noise), `t10_packed_dirt` (dirt), `gl04_raw_crystal_cluster` (crystal), `pm06_splatter_finish` (splatter), and `man03_mosaic_tile` (skewed_bricks). Note inline that `custom_tiles` was scoped out (requires an `sdf2d` shape input, which the SDF family's existing out-of-scope ruling covers) and `skewed_bricks` substituted instead, so a future reader does not wonder why `custom_tiles` is still unused despite this round's work.

- [ ] **Step 3: Run the coverage test**

Run: `python -m pytest tests/test_authoring_counts.py -v`
Expected: PASS with the new digits.

- [ ] **Step 4: Commit**

```bash
git add docs/AUTHORING.md
git commit -m "docs(authoring): name round-3 materials, refresh live coverage numbers"
```

---

## Phase C: Wrap

### Task 9: Full-suite green

- [ ] **Step 1: Run the fast suite**

Run: `python -m pytest -q -m "not integration"`
Expected: all pass (six new materials add cookbook-gate rows; README/AUTHORING count tests pass).

- [ ] **Step 2: Run the cookbook regression gates**

Run: `python -m quality.promote_cookbook --check` and `python -m quality.naming --cookbook`
Expected: both clean.

- [ ] **Step 3: Scan new/changed docs for em dashes**

Run a search for `—` across `docs/AUTHORING.md`, `README.md`, and any new `cookbook/*/*.md` recipe cards touched this round; fix any found (this project's standing no-em-dash rule).

- [ ] **Step 4: Update HANDOFF.md and STATUS.md per this project's baton shape rules**

Follow `CLAUDE.md`'s baton conventions (Current state describes this session only; STATUS cells get state + one line + evidence pointer). Commit as the session's `docs:` wrap-up commit.

---

## Self-Review

**Spec coverage (against the approved chat design):**
- Six proof materials on unused nodes (scratches, directional_noise, dirt, crystal, splatter, skewed_bricks): Tasks 1-6. Covered.
- README/AUTHORING integration: Tasks 7-8. Covered.
- The `custom_tiles` -> `skewed_bricks` scope correction is documented in the plan header and cross-referenced in Task 8 so it is not silently lost.

**Placeholder scan:** Material tasks (1-6) intentionally do not fabricate final gradient/palette values (render-judged by Grayson); each gives the exact starting node params verified from `describe_node` or the node's own `.mmg` source, the technique, the grouping, and the gates -- the same deliberate property rounds 1-2's plans used, not a placeholder. Task 5 (`splatter`) gives the full concrete wiring (not just a starting-param dict) because it is a compositing node, not a bare generator, and the wiring itself (not just parameter tuning) is the part that could otherwise be ambiguous.

**Type/name consistency:** Material ids (`m04_scratched_steel`, `f11_corduroy`, `t10_packed_dirt`, `gl04_raw_crystal_cluster`, `pm06_splatter_finish`, `man03_mosaic_tile`) are used consistently across their tasks and Phase B's 65->71 count. All six retype targets are confirmed members of `_NOISE_PATTERN_NODES` already (no new entries needed in `node_usage_audit.py`, unlike round 2's `directional_noise` addition).

**Sequencing:** Tasks 1-6 are independent of each other (different categories, different files) and can run in parallel. Phase B (Tasks 7-8) depends on all of Phase A being promoted (for the count and the audit numbers). Phase C is the final gate.

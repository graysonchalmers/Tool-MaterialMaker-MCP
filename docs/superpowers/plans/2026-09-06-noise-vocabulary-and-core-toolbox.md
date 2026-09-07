# Noise Vocabulary + Core Toolbox Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Cash the already-mapped noise/distortion gap by shipping six proof materials on zero-use base nodes, expand the pixel-tested debug swatches to cover the gap families, and surface the existing single-node infrastructure (swatches + noise gallery) as one visible "Core toolbox" README section with the cookbook contact sheet no longer collapsed.

**Architecture:** Everything reuses existing infrastructure; no new subsystem. Materials follow the established `quality/cookbook_<category>.py` builder pattern (clone a donor from `quality/donors/`, retune, `group_into_subgraph`, `rename_nodes`, promote). Swatches follow `quality/debug_swatches.py`'s single-node-into-a-Material pattern with `tests/test_debug_swatches.py`-style pixel assertions. README work is edits plus the count-gate tests in `tests/test_readme_counts.py`. Design approved in chat (session 2026-09-06); no separate spec file, per the brainstorming ruling that a surface-and-expand job of existing artifacts is not architectural-new.

**Tech Stack:** Python 3.13, Material Maker node-graph JSON (`.ptex`), Godot 4.7.1 headless render, pytest.

**Spec:** Approved in chat 2026-09-06 (this plan is the durable record). Supporting evidence: the coverage histogram in the session, `quality/noise_gallery.py` (exact starting node params for the gap bases), `docs/AUTHORING.md` "Noise vocabulary" section, `docs/DEBUG_SWATCHES.md`.

## Global Constraints

- **Render mechanics (verified, from HANDOFF heads-up):** one Godot process at a time; pass `render()`/`render_tracked` an ABSOLUTE outdir (a relative one makes Godot open its GUI and idle to the 180s timeout with an empty log); never launch a render from `python -c`; in the Git Bash tool `taskkill //F //IM Godot_v4.7.1-stable_win64_console.exe` (and the GUI exe) is the recovery. Subagents lose long Godot runs: poll the output file rather than blocking on return. Stone/terrain compares take 6-9 minutes.
- **Quality scripts run as `python -m quality.<module>` from the repo root** with `pip install -e .` already done; running from inside `quality/` breaks `.env` lookup.
- **Godot is not byte-deterministic.** A single render_compare failure on an unchanged graph is a re-render first, a regression second (one measured 21.89 mean-abs-diff then 0.0 on rerun).
- **`blend` semantics:** shows port-1 where its port-2 mask is 0 and port-0 where it is 1; put the majority layer on port-1. Opacity = amount x mask. `normal_map` `param4=0` is the flat-normal fix; `param1` is relief strength.
- **Verify metallic/roughness/AO by reading the exported ORM channel** with `quality/pngread.py`, not by eye.
- **Node names never affect renders** (MM seeds from node position); every cookbook node must be role-named (`quality/naming.py` gate); never rename a subgraph (`type=="graph"`) node.
- **Grayson is the visual judge.** No material task self-certifies its look. Each returns rendered 3D previews (`render_preview`) that get sent to Grayson via SendUserFile; he approves or redirects before that material is committed. This is the visual half of the between-task review.
- **`.env` is gitignored, never echo it.** Donors load from `quality/donors/` (tracked).
- **Copy rule:** README states all counts in digits; `tests/test_readme_counts.py` recomputes them from the tree. Change the tree, then the number, never the reverse.

---

## Phase A: Swatch expansion (independent of material count, TDD)

### Task 1: Warp / distortion diagnostic swatches

**Files:**
- Modify: `quality/debug_swatches.py` (add builders + register them in the module's build list)
- Modify: `tests/test_debug_swatches.py` (add pixel assertions)
- Modify: `docs/DEBUG_SWATCHES.md` (add legend lines)

**Interfaces:**
- Consumes: `quality.author_helpers._grad`, `save_variant`; the `_material()`, `_graph()` helpers already in `debug_swatches.py`; `quality.pngread.read_png`, `Sampler` (from the test).
- Produces: new swatch builder functions (`build_swatch_warp`, `build_swatch_warp2`, `build_swatch_directional_warp`, `build_swatch_slope_blur`) each returning the saved `.ptex` path under `quality/authored/debug-swatches/<swatch>/v1.ptex`, and registered so `python -m quality.debug_swatches` writes them.

The diagnostic principle: warp/distort nodes are assertable because they DISPLACE a KNOWN reference field. Feed each distortion node a hard-edged reference (a `pattern` or `shape` node making a sharp vertical bar or checker), then assert that a pixel which was black in the undistorted reference is now non-black (or vice versa) at a chosen coordinate, proving the displacement happened. This is a real known-answer, unlike raw noise.

- [ ] **Step 1: Read the existing swatch pattern**

Read `quality/debug_swatches.py` in full and `tests/test_debug_swatches.py` in full to match the exact `_material()`/`_graph()` skeleton, the `_AUTHORED` path convention, the `save_variant(graph, _LABEL, case, 1)` call, and the render-and-sample assertion shape. Match it; do not invent a new plumbing.

- [ ] **Step 2: Write a failing pixel assertion for the `warp` swatch**

In `tests/test_debug_swatches.py`, add an integration test (marked the same way the existing render-assert tests are) that renders the `warp` swatch at a small size and asserts the reference edge moved. Concretely: build a reference that is black on the left half and white on the right half (a `pattern` node or a steep `colorize` on a horizontal gradient), warp it, and assert `Sampler.at(x, y)` at a coordinate straddling the original boundary now reads the opposite side's value. Use the exact same `render(...)` + `read_png` + `Sampler` calls the existing tests use.

- [ ] **Step 3: Run it to confirm it fails**

Run: `python -m pytest tests/test_debug_swatches.py -k warp -v`
Expected: FAIL (builder/swatch not defined yet).

- [ ] **Step 4: Implement the `warp` swatch builder**

Add `build_swatch_warp` to `debug_swatches.py`: reference field -> `warp` (type `warp`, a visible `amount`, e.g. 0.3, fed a `perlin` as its displacement input on the warp node's second input port per `describe_node("warp")`) -> Material albedo. Confirm the warp node's real input ports with `describe_node` before wiring. Register it in the module's build list.

- [ ] **Step 5: Run the test to confirm it passes**

Run: `python -m quality.debug_swatches` then `python -m pytest tests/test_debug_swatches.py -k warp -v`
Expected: PASS.

- [ ] **Step 6: Repeat Steps 2-5 for `warp2`, `directional_warp`, and `slope_blur`**

One swatch each, one assertion each. `slope_blur`'s known-answer: it smears along the slope of its input, so a sharp edge becomes a gradient ramp; assert a mid-boundary pixel is now an intermediate value (neither 0 nor 255) where the un-blurred reference was hard. Confirm each node's input ports with `describe_node` first (distortion nodes take an input to distort plus a control/displacement input).

- [ ] **Step 7: Add legend lines to `docs/DEBUG_SWATCHES.md`**

One line per new swatch describing its known-correct appearance (what a correct render looks like), matching the existing legend format.

- [ ] **Step 8: Run the full swatch suite**

Run: `python -m pytest tests/test_debug_swatches.py -v`
Expected: all pass (existing 13 + the 4 new).

- [ ] **Step 9: Commit**

```bash
git add quality/debug_swatches.py tests/test_debug_swatches.py docs/DEBUG_SWATCHES.md
git commit -m "feat(swatches): warp/warp2/directional_warp/slope_blur diagnostics"
```

### Task 2: Colorize / normal_map / pattern baseline swatches

**Files:**
- Modify: `quality/debug_swatches.py`
- Modify: `tests/test_debug_swatches.py`
- Modify: `docs/DEBUG_SWATCHES.md`

**Interfaces:**
- Consumes: same helpers as Task 1.
- Produces: `build_swatch_colorize`, `build_swatch_normal_map`, `build_swatch_pattern`, registered in the build list.

These round out the "baseline toolbox": the three workhorse nodes every material uses. Each has a clean known-answer.

- [ ] **Step 1: Write a failing assertion for `colorize`**

Feed a known horizontal ramp (0 on the left, 1 on the right) into a `colorize` whose gradient maps 0->red, 1->blue. Assert `Sampler.at(0.05, 0.5)` is red-dominant and `Sampler.at(0.95, 0.5)` is blue-dominant. Run to confirm FAIL.

- [ ] **Step 2: Implement `build_swatch_colorize`, run to PASS**

Reference ramp -> `colorize` (red-to-blue `_grad`) -> Material albedo. Run `python -m quality.debug_swatches` then the `-k colorize` test.

- [ ] **Step 3: `normal_map` swatch (assert flat vs. relief)**

Build two-node comparison in one swatch is not needed; instead assert the `param4`/`param1` behavior: feed a bumpy `perlin` into `normal_map` with `param1=0.6` and assert the rendered normal map (Material port 4 output) is NOT the flat-normal constant (0.5, 0.5, 1.0 in the normal channel) at a sloped pixel. This memorializes the `normal_map` compound-node gotcha (`param1`=strength, `param4`=0 flat fix). Confirm FAIL, implement, PASS.

- [ ] **Step 4: `pattern` swatch**

`pattern` node (a `sin*sin` or Bounce shape per `describe_node("pattern")`) -> Material albedo; assert a peak pixel is bright and a valley pixel is dark at known coordinates. Confirm FAIL, implement, PASS.

- [ ] **Step 5: Legend lines + full suite**

Add three legend lines to `docs/DEBUG_SWATCHES.md`. Run `python -m pytest tests/test_debug_swatches.py -v`; all pass.

- [ ] **Step 6: Commit**

```bash
git add quality/debug_swatches.py tests/test_debug_swatches.py docs/DEBUG_SWATCHES.md
git commit -m "feat(swatches): colorize/normal_map/pattern baseline diagnostics"
```

### Task 3: Fix the stale `debug_swatches.py` docstring

**Files:**
- Modify: `quality/debug_swatches.py:1-23` (the module docstring)

- [ ] **Step 1: Correct the Phase 2 wording**

The docstring says Phase 2 pixel assertions are "deferred" and "Not built yet." They are built and green (`tests/test_debug_swatches.py` renders each swatch and asserts known-answer pixels). Rewrite lines 16-19 to state the assertions exist and point at the test file, and note the swatch set now covers the warp/distort and colorize/normal_map/pattern families (Tasks 1-2). No em dashes.

- [ ] **Step 2: Commit**

```bash
git add quality/debug_swatches.py
git commit -m "docs(swatches): docstring reflects built pixel assertions + widened coverage"
```

---

## Phase B: Six proof materials

Each material is one task. Shared shape for every material task (do not restate per task): add a builder to the named `quality/cookbook_<category>.py` (register it in that file's `BUILDERS` dict); run `python -m quality.cookbook_<category> <id>` to write `quality/authored/cookbook-<category>/<id>/v1.ptex`; validate it (`mm-mcp` `validate` or `python -c` is banned for renders but fine for a pure validate via the validator module) and confirm ZERO errors; render it with an ABSOLUTE outdir and build a `render_preview` composite; SendUserFile the preview to Grayson and WAIT for approval or redirect (iterate the builder on his feedback, re-render); once he approves, write the prose recipe card `cookbook/<category>/<id>.md` (the human recipe above the auto-generated node table); `python -m quality.promote_cookbook cookbook-<category>` to copy the `.ptex` and generate the card node-table; confirm `python -m quality.promote_cookbook --check` and `python -m quality.naming --cookbook <category>` are clean; commit. The exact gradient/param values are tuned by render-and-look, not fabricated here; each task gives the technique, the starting node params, the donor, and the target look.

### Task 4: `t09_parched_clay` (fbm Cellular, terrain)

**Files:**
- Modify: `quality/cookbook_terrain.py`
- Create: `cookbook/terrain/t09_parched_clay.md`, `cookbook/terrain/t09_parched_clay.ptex` (via promote)

**Technique:** Distinct from `t07_forest_floor` (which uses fbm Cellular 4 for scattered clumps): here use an fbm Cellular base tuned for a CONNECTED crack-network at a coarse scale to read as sun-baked cracked clay, a look voronoi's single-octave cells cannot give. Starting node (from `quality/noise_gallery.py` `_FBM_BASES`): `{"type":"fbm","parameters":{"noise":5,"scale_x":4,"scale_y":4,"folds":0,"iterations":3,"persistence":0.5}}` (Cellular 4); sweep `noise` across 3-6 during iteration to pick the crack character. Warm ochre/tan palette, high matte roughness, `normal_map param4=0` with medium `param1` for cracked relief. Follow `build_t07_forest_floor`'s `retype`+`group_into_subgraph`+`rename_nodes` structure.

- [ ] **Step 1:** Author `build_t09_parched_clay(catalog)` in `cookbook_terrain.py`, register in `BUILDERS`.
- [ ] **Step 2:** `python -m quality.cookbook_terrain t09_parched_clay`; validate, 0 errors.
- [ ] **Step 3:** Render (absolute outdir) + `render_preview`; SendUserFile to Grayson; iterate to his approval.
- [ ] **Step 4:** Write `cookbook/terrain/t09_parched_clay.md` prose recipe.
- [ ] **Step 5:** `python -m quality.promote_cookbook cookbook-terrain`; then `--check` and `naming --cookbook terrain` clean.
- [ ] **Step 6:** Commit `feat(cookbook): t09_parched_clay (fbm Cellular crack network)`.

### Task 5: `m03_brushed_titanium` (noise_anisotropic, metal)

**Files:**
- Modify: `quality/cookbook_metal.py`
- Create: `cookbook/metal/m03_brushed_titanium.{md,ptex}`

**Technique:** Directional hairline finish that `m02_brushed_aluminum` (warp-stretched) cannot match natively. Starting node (from `noise_gallery.py` cross-family row): `{"type":"noise_anisotropic","parameters":{"scale_x":4,"scale_y":48,"smoothness":1,"interpolation":1}}` (the high `scale_y`:`scale_x` ratio is the directional stretch). Cool gray titanium albedo with a faint warm tint, metallic is a paint-vs-metal decision (here: metallic surface, so `metallic=1` on the metal region), moderate roughness with anisotropic streaks feeding the normal for the brushed grooves. Read the exported ORM metallic channel with `quality/pngread.py` to confirm metallic, not by eye.

- [ ] **Step 1-6:** Shared material shape above, category `metal`. Commit `feat(cookbook): m03_brushed_titanium (noise_anisotropic hairline)`.

### Task 6: `sf07_conduit_panel` (truchet, scifi)

**Files:**
- Modify: `quality/cookbook_scifi.py`
- Create: `cookbook/scifi/sf07_conduit_panel.{md,ptex}`

**Technique:** Interlocking pipe/conduit topology that voronoi/perlin cannot make. Starting node (from `noise_gallery.py`): `{"type":"truchet","parameters":{"shape":1,"size":4}}` (Circle = interlocking curved pipes; try `shape:0` Line for a maze/circuit alternative during iteration). Feed the truchet field into an albedo colorize (dark panel, bright conduit) and into the normal for raised pipes. Recall the pinned sf03 lesson: a `blend`'s opacity is amount x port-2 mask, so drive any conduit-over-panel composite with a HARD 0/1 mask, never a mid-value albedo colorize.

- [ ] **Step 1-6:** Shared material shape, category `scifi`. Commit `feat(cookbook): sf07_conduit_panel (truchet interlocking pipes)`.

### Task 7: `s12_eroded_sandstone` (slope_blur, stone)

**Files:**
- Modify: `quality/cookbook_stone.py`
- Create: `cookbook/stone/s12_eroded_sandstone.{md,ptex}`

**Technique:** Water-eroded sedimentary streaking, the one distortion the cookbook has never used. `slope_blur` (from Task 1's swatch, now proven wired) smears a layered noise along its slope to give directional erosion runs. Base: a horizontally-banded sediment (a `colorize` on a vertical gradient, or perlin with high `scale_y`), then `slope_blur` to erode. Warm sandstone palette (tan/ochre/rust bands), matte-to-slightly-rough. Confirm `slope_blur` input ports with `describe_node` (input to blur plus a slope/control input).

- [ ] **Step 1-6:** Shared material shape, category `stone`. Commit `feat(cookbook): s12_eroded_sandstone (slope_blur erosion)`.

### Task 8: `t10_rippled_wet_sand` (wavelet_noise, terrain)

**Files:**
- Modify: `quality/cookbook_terrain.py`
- Create: `cookbook/terrain/t10_rippled_wet_sand.{md,ptex}`

**Technique:** Interference/ripple banding for wet sand ripples, distinct from `t01_sand_dunes` (broad perlin rolls). Starting node (from `noise_gallery.py`): `{"type":"wavelet_noise","parameters":{"type":4,"scale_x":4,"scale_y":4,"iterations":3,"persistence":0.5,"frequency":1,"offset":0}}`; tune `frequency`/`scale` for tight ripples. Damp sand palette (darker, cooler than dry dunes), LOW roughness for a wet sheen (feed a roughness texture so an ORM map exports, per the `_dry_earth_plates` lesson), ripple field into the normal for the corrugation.

- [ ] **Step 1-6:** Shared material shape, category `terrain`. Commit `feat(cookbook): t10_rippled_wet_sand (wavelet_noise ripples)`.

### Task 9: `gl02_cut_gem` (voronoi_triangle, glass)

**Files:**
- Modify: `quality/cookbook_glass.py`
- Create: `cookbook/glass/gl02_cut_gem.{md,ptex}`

**Technique:** Faceted crystal, the triangular-cell character voronoi's square cells cannot produce. Starting node (from `noise_gallery.py`): `{"type":"voronoi_triangle","parameters":{"scale_x":4,"scale_y":4,"stretch_x":1,"stretch_y":1,"randomness":0.85}}`. Use the per-facet random (confirm which output port carries per-cell random via `describe_node`, analogous to voronoi port 2) to tint each facet, sharp facet edges into the normal for hard crystalline relief, low roughness + a jewel-tone palette. Distinct from `gl01_frosted_glass` (connected-crack sandblast).

- [ ] **Step 1-6:** Shared material shape, category `glass`. Commit `feat(cookbook): gl02_cut_gem (voronoi_triangle facets)`.

---

## Phase C: README integration (depends on A and B being done)

### Task 10: Update all cookbook counts and regenerate the contact sheet

**Files:**
- Modify: `README.md` (the three count sentences)
- Modify: `docs/images/cookbook-contact-sheet.png` (regenerate)

**Interfaces:**
- Consumes: the six new materials from Phase B (count is now 59; category count stays 12).

- [ ] **Step 1: Regenerate the contact sheet**

Run `python -m quality.contact_sheet` (read the module first for the exact entrypoint and args). It must include all 59 materials. Save as 8-bit palette PNG (pinned lesson from teardown #3).

- [ ] **Step 2: Update the three README count strings**

`README.md`: "cookbook is 53 materials across 12 categories" -> 59; the contact-sheet `<summary>` "(53 materials:" -> 59 (this string moves in Task 11, keep the count correct wherever it lands); "gallery of the 53 cookbook materials" -> 59.

- [ ] **Step 3: Run the count gate**

Run: `python -m pytest tests/test_readme_counts.py -v`
Expected: all pass.

- [ ] **Step 4: Commit**

```bash
git add README.md docs/images/cookbook-contact-sheet.png
git commit -m "docs(readme): 59-material counts + regenerated contact sheet"
```

### Task 11: Un-collapse the cookbook contact sheet

**Files:**
- Modify: `README.md:81-88` (remove the `<details>`/`<summary>` wrapper)
- Modify: `tests/test_readme_counts.py:30-33` (`test_readme_contact_sheet_summary_count_matches_tree` regex)

**Interfaces:**
- Consumes: Task 10's corrected counts.

The trap: the count test currently requires the literal `Show the cookbook contact sheet</b> (59 materials:` inside the `<summary>`. Removing the wrapper deletes that string, so the test and the caption change together.

- [ ] **Step 1: Write the new always-visible caption**

Replace the `<details>`/`<summary>`/`</details>` block with a plain always-visible caption line + the `<p align="center"><img ...></p>`. The caption keeps a count-bearing phrase, e.g. `**The full cookbook (59 materials:** ceramic, fabrics, ...)`. Decide the exact wording, then set the test regex to match it.

- [ ] **Step 2: Update the regex to match the new caption**

In `tests/test_readme_counts.py`, change `test_readme_contact_sheet_summary_count_matches_tree`'s regex from the `<summary>`-specific pattern to one that matches the new always-visible caption and still captures the digit count. Keep the assertion `== len(ENTRIES)`.

- [ ] **Step 3: Run the count gate**

Run: `python -m pytest tests/test_readme_counts.py -v`
Expected: all pass (the un-collapse did not break the count enforcement).

- [ ] **Step 4: Commit**

```bash
git add README.md tests/test_readme_counts.py
git commit -m "docs(readme): cookbook contact sheet always visible, count gate follows"
```

### Task 12: Generate the swatch contact sheet + reuse the noise-gallery renders

**Files:**
- Modify: `quality/contact_sheet.py` (or add a small sibling) to emit a swatch sheet
- Create: `docs/images/core-toolbox/swatches.png`
- Confirm present: `docs/images/noise-gallery/` renders (from `quality/noise_gallery.py`)

- [ ] **Step 1: Read `quality/contact_sheet.py`**

Determine whether it can target the `debug-swatches` label or needs a small parameter. Prefer reusing it over a new module.

- [ ] **Step 2: Render the swatches if not already rendered**

Run `python -m quality.debug_swatches` then `python -m quality.render_cookbook debug-swatches` (absolute outdir constraints apply). Confirm the noise-gallery images exist under `docs/images/noise-gallery/`; if not, `python -m quality.noise_gallery` then `python -m quality.render_cookbook noise-gallery`.

- [ ] **Step 3: Build `docs/images/core-toolbox/swatches.png`**

A contact sheet of the (now ~19) debug swatches, 8-bit palette PNG.

- [ ] **Step 4: Commit**

```bash
git add quality/contact_sheet.py docs/images/core-toolbox/swatches.png
git commit -m "docs(core-toolbox): swatch contact sheet"
```

### Task 13: Add the "Core toolbox" README section with count enforcement

**Files:**
- Modify: `README.md` (new section after "Material cookbook")
- Modify: `tests/test_readme_counts.py` (add a swatch-count test)

**Interfaces:**
- Consumes: Task 12's images; the swatch count from `quality/debug_swatches.py`'s build list.

- [ ] **Step 1: Write the section**

A visible "Core toolbox" section framing the single-node artifacts as the baseline building blocks: the debug swatches (each isolates one node so you see its raw behavior, AND each is a live pixel-assertion regression test) and the noise-vocabulary gallery (fbm's 8 bases + cross-family characters). Embed `docs/images/core-toolbox/swatches.png` and a noise-gallery image; link `docs/DEBUG_SWATCHES.md` and AUTHORING's "Noise vocabulary" section. State the swatch count in digits.

- [ ] **Step 2: Write a failing swatch-count test**

Add `test_readme_core_toolbox_swatch_count_matches_build` to `tests/test_readme_counts.py`: import the swatch build list from `quality.debug_swatches`, count it, and regex the README's "N single-node ..." phrase. Confirm FAIL if the number is wrong, then set the README number right so it PASSES.

- [ ] **Step 3: Run the full README + swatch suite**

Run: `python -m pytest tests/test_readme_counts.py tests/test_debug_swatches.py -v`
Expected: all pass.

- [ ] **Step 4: Commit**

```bash
git add README.md tests/test_readme_counts.py
git commit -m "docs(readme): Core toolbox section (swatches + noise gallery), count-gated"
```

---

## Phase D: Wrap

### Task 14: Full-suite green + coverage-note doc

**Files:**
- Modify: `docs/AUTHORING.md` (a short "distortion vocabulary" note; optional SDF out-of-scope ruling)

- [ ] **Step 1: Run the fast suite**

Run: `python -m pytest -q -m "not integration"`
Expected: all pass (the six new materials add cookbook-gate rows; the new swatch tests' fast portions pass; README counts pass).

- [ ] **Step 2: Run the cookbook regression gates**

Run: `python -m quality.promote_cookbook --check` and `python -m quality.naming --cookbook`
Expected: both clean.

- [ ] **Step 3: Add the AUTHORING distortion note (+ optional SDF ruling)**

In `docs/AUTHORING.md`, add a short "Distortion vocabulary" paragraph mirroring the "Noise vocabulary" one: `warp` is the workhorse but `warp2`/`directional_warp`/`slope_blur` give displacement characters it cannot, with the swatch names as the reference. Optionally add a one-line ruling that the SDF family (43 nodes, 0 use) is out of scope as shape-SDL, not texture authoring. No em dashes.

- [ ] **Step 4: Commit**

```bash
git add docs/AUTHORING.md
git commit -m "docs(authoring): distortion vocabulary note; SDF out-of-scope ruling"
```

---

## Self-Review

**Spec coverage (against the approved chat design):**
- Six proof materials on zero-use bases: Tasks 4-9 (fbm Cellular, noise_anisotropic, truchet, slope_blur, wavelet_noise, voronoi_triangle). Covered.
- Expand debug swatches to warp/distort + colorize/normal_map/pattern: Tasks 1-2. Covered.
- Un-collapse cookbook in README + fix count gate: Task 11. Covered.
- New "Core toolbox" README section unifying swatches + noise gallery: Tasks 12-13. Covered.
- Fix stale docstring: Task 3. Covered.
- Distortion audit (#2) + family coverage (#3): completed in-session pre-plan; the durable output is the AUTHORING distortion note (Task 14) and the SDF ruling. Covered.

**Placeholder scan:** Material tasks intentionally do not fabricate final gradient/param values (those are render-judged by Grayson); each gives the donor, the exact starting node params from `noise_gallery.py`, the technique, and the gates. This is a deliberate property of visual authoring, not a placeholder. Swatch and README tasks carry exact assertions, commands, and regex targets.

**Type/name consistency:** Material ids (`t09_parched_clay`, `m03_brushed_titanium`, `sf07_conduit_panel`, `s12_eroded_sandstone`, `t10_rippled_wet_sand`, `gl02_cut_gem`) are used consistently across their tasks and Phase C counts (53 -> 59). Swatch builder names (`build_swatch_*`) and the count-test names are consistent between Phase A and Task 13.

**Sequencing:** Phase A (swatches) and Phase B (materials) are independent and can run in either order or interleaved; Phase C depends on both (counts + swatch images). Phase D is the final gate.

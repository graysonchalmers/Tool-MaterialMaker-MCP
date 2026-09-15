# Noise Vocabulary Round 2 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship a reusable node-usage-audit script so "are we using X" stops needing a manual recount, then cash six more proof materials on noise/distortion nodes the cookbook has never used, on top of round 1's six (`docs/superpowers/plans/2026-09-06-noise-vocabulary-and-core-toolbox.md`, merged `0169446`).

**Architecture:** Everything reuses existing infrastructure; no new subsystem. The audit script is a small, pure-Python reporting module following `quality/debug_swatches.py`'s existing pattern of exposing a build-list-shaped constant that a README/AUTHORING count-test can import (`tests/test_readme_counts.py::test_readme_core_toolbox_swatch_count_matches_build` is the model). Materials follow the established `quality/cookbook_<category>.py` builder pattern (clone a donor from `quality/donors/` or build from scratch, retype/tune, `group_into_subgraph`, `rename_nodes`, promote). Design approved in chat 2026-09-13; no separate spec file, same "surface-and-expand, not architectural-new" ruling as round 1.

**Tech Stack:** Python 3.13, Material Maker node-graph JSON (`.ptex`), Godot 4.7.1 headless render, pytest.

**Spec:** Approved in chat 2026-09-13 (this plan is the durable record). Supporting evidence: `quality/noise_gallery.py` (exact starting node params for the round-2 target bases), `quality/debug_swatches.py`'s `build_swatch_warp2` (warp2 wiring/ports), `quality/cookbook_scifi.py::build_sf07_conduit_panel` (truchet from-scratch pattern + the real-output-range-measurement lesson), `docs/AUTHORING.md`'s "Noise vocabulary" and "Distortion vocabulary" sections.

## Global Constraints

- **Render mechanics (verified, from HANDOFF heads-up):** one Godot process at a time; pass `render()`/`render_tracked` an ABSOLUTE outdir (a relative one makes Godot open its GUI and idle to the 180s timeout with an empty log); never launch a render from `python -c`; in the Git Bash tool `taskkill //F //IM Godot_v4.7.1-stable_win64_console.exe` (and the GUI exe) is the recovery. Subagents lose long Godot runs: poll the output file rather than blocking on return.
- **Quality scripts run as `python -m quality.<module>` from the repo root** with `pip install -e .` already done; running from inside `quality/` breaks `.env` lookup.
- **Godot is not byte-deterministic.** A single render_compare failure on an unchanged graph is a re-render first, a regression second.
- **`blend` semantics:** shows port-1 where its port-2 mask is 0 and port-0 where it is 1; put the majority layer on port-1. Opacity = amount x mask. `normal_map` `param4=0` is the flat-normal fix; `param1` is relief strength.
- **Verify metallic/roughness/AO by reading the exported ORM channel** with `quality/pngread.py`, not by eye.
- **Node names never affect renders** (MM seeds from node position); every cookbook node must be role-named (`quality/naming.py` gate); never rename a subgraph (`type=="graph"`) node.
- **`buffer`-type compound nodes do not render headless** (`slope_blur`, `warp_dilation` family) -- not used in this round, noted only so no task reaches for one.
- **Diagnose any unknown node's real output range before tuning against it.** `truchet`'s Circle mode measured 0.50-0.95 (not 0/1); its Line mode's real range is UNKNOWN and must be measured the same way (render the noise-gallery `truchet_line` case, sample with `quality/pngread.py`) before setting any threshold against it -- do not assume it matches Circle's range.
- **Grayson is the visual judge.** No material task self-certifies its look. Each returns rendered 3D previews (`render_preview`) that get sent to Grayson via SendUserFile; he approves or redirects before that material is committed.
- **`.env` is gitignored, never echo it.** Donors load from `quality/donors/` (tracked).
- **Copy rule:** README/AUTHORING state all counts in digits; a test recomputes them from the tree. Change the tree, then the number, never the reverse.
- **No em dashes in any doc or commit message.**

---

## Phase A: Node-usage-audit script (TDD)

### Task 1: `quality/node_usage_audit.py` + tests

**Files:**
- Create: `quality/node_usage_audit.py`
- Create: `tests/test_node_usage_audit.py`

**Interfaces:**
- Consumes: `mm_mcp.config.load_config().cookbook_dir`; `mm_mcp.cookbook.list_cookbook(cookbook_dir) -> list[CookbookEntry]` (each entry has `.name`, `.category`, `.path`).
- Produces: `audit(cookbook_dir: str | None = None) -> dict` with keys `"counts"` (`Counter[str, int]`, node type -> total instance count across the cookbook), `"materials_by_type"` (`dict[str, list[str]]`, node type -> sorted list of material ids using it), `"noise_used"` (sorted list of `_NOISE_PATTERN_NODES` members with count > 0), `"noise_unused"` (sorted list of the rest). Also `_NOISE_PATTERN_NODES: frozenset[str]`, importable by Task 2's test.

Material Maker's `.mmg` node files carry no machine-readable category field (verified against the pinned checkout at `z-Git/material-maker/addons/material_maker/nodes/*.mmg` -- no `category`/`tree_item` key on the leaf files; `material_maker/library/base.json`'s `tree_item` taxonomy only covers a curated UI-convenience subset and does not 1:1 match raw node type names). So `_NOISE_PATTERN_NODES` is a hand-curated constant, documented inline, matching the scope of AUTHORING.md's "Noise vocabulary" section: organic/procedural scalar-field generators, excluding the separate "Distortion vocabulary" family (`warp`/`warp2`/`directional_warp`/etc.) and excluding the SDF family (already ruled out of scope in AUTHORING.md) and excluding symbolic/glyph generators (`roman_numerals*`, `seven_segment*`, `sixteen_segment`, `runes`, `iching`, `japanese_glyphs*`, `cairo` -- decorative tile-text, not noise).

- [ ] **Step 1: Write the failing tests**

```python
"""quality.node_usage_audit must run clean against the real cookbook and
produce sane, well-typed output. This is a reporting tool, not a graph --
see quality/noise_gallery.py's docstring for why noise coverage isn't
pixel-testable, so there is no render/pixel assertion here."""
from quality.node_usage_audit import audit, _NOISE_PATTERN_NODES


def test_audit_partitions_noise_pattern_nodes_used_vs_unused():
    report = audit()
    used = set(report["noise_used"])
    unused = set(report["noise_unused"])
    assert used | unused == _NOISE_PATTERN_NODES
    assert used.isdisjoint(unused)


def test_perlin_and_voronoi_are_used():
    # The two base generators every early cookbook material leaned on
    # (2026-09-01 finding); a regression here means the subgraph recursion
    # broke, since both generators now live one level inside a group.
    report = audit()
    assert "perlin" in report["noise_used"]
    assert "voronoi" in report["noise_used"]


def test_materials_by_type_lists_real_cookbook_ids():
    report = audit()
    assert len(report["materials_by_type"]["perlin"]) > 0
    for material_id in report["materials_by_type"]["perlin"]:
        assert isinstance(material_id, str) and material_id
```

Save as `tests/test_node_usage_audit.py`.

- [ ] **Step 2: Run it to confirm it fails**

Run: `python -m pytest tests/test_node_usage_audit.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'quality.node_usage_audit'`.

- [ ] **Step 3: Implement the module**

```python
"""Audit which Material Maker generator nodes the cookbook actually uses,
recursing into the subgraph wrappers every cookbook material is grouped
into (quality.author_helpers.group_into_subgraph), so role-named nodes one
level down are counted correctly -- the same descent src/mm_mcp/validator.py
uses to check subgraph internals.

Why this exists: the 2026-09-01 "everything looks similar" histogram (see
docs/AUTHORING.md's Noise vocabulary section) was a one-time manual grep
against 38 builders. By the 2026-09-13 pickup session it was already stale
(59 materials existed by then, then 65 after this round) and had to be
re-derived by hand from a live recursive walk. This script makes that
number live: run it any time to see exactly which noise/pattern generators
the CURRENT cookbook uses and which are still untouched.

_NOISE_PATTERN_NODES is a curated list of Material Maker's scalar-field
noise/pattern GENERATOR node type names, matching the scope of
AUTHORING.md's "Noise vocabulary" section. It deliberately excludes:
distortion/warp nodes (AUTHORING.md's separate "Distortion vocabulary"
section covers those), the SDF family (ruled out of scope entirely, see
AUTHORING.md), and symbolic/glyph generators (roman_numerals, seven_segment,
sixteen_segment, runes, iching, japanese_glyphs, cairo -- decorative
tile-text nodes, not noise). Material Maker's .mmg node files carry no
machine-readable category field (verified against the pinned MM checkout),
so this list is maintained by hand here, the same way the SDF-family count
in AUTHORING.md is a manual tally. Update it if the MM node set changes.

Run: python -m quality.node_usage_audit
"""
import json
from collections import Counter, defaultdict

from mm_mcp.config import load_config
from mm_mcp.cookbook import list_cookbook

_NOISE_PATTERN_NODES = frozenset({
    "beehive", "beehive2",
    "bricks", "bricks_nontileable", "bricks_uneven", "bricks_uneven2",
    "bricks_uneven2_2", "bricks_uneven3", "bricks_uneven3_2", "bricks_uneven4",
    "bricks2", "bricks3",
    "circle_splatter", "circle_splatter_color",
    "clouds_noise", "color_noise", "crystal", "custom_tiles",
    "diagonal_weave", "dirt",
    "fbm", "fbm_variations", "fbm2", "fbm3", "fbm4",
    "noise", "noise_anisotropic", "noise_color", "noise_white", "noise2",
    "pattern",
    "perlin", "perlin_color",
    "scratches", "scratches2",
    "shard_fbm", "sine_wave",
    "skewed_bricks", "skewed_uneven_bricks",
    "spiral_gradient",
    "splatter", "splatter_color",
    "truchet", "truchet_generic",
    "voronoi", "voronoi_triangle", "voronoi2",
    "wavelet_noise", "wavelet_noise2",
    "weave", "weave2", "weave_random",
})


def _walk(nodes: list, counts: Counter) -> None:
    for n in nodes:
        t = n.get("type")
        if t:
            counts[t] += 1
        if t == "graph" and "nodes" in n:
            _walk(n["nodes"], counts)


def audit(cookbook_dir: str | None = None) -> dict:
    cookbook_dir = cookbook_dir or load_config().cookbook_dir
    counts: Counter = Counter()
    materials_by_type: "defaultdict[str, list]" = defaultdict(list)
    for entry in list_cookbook(cookbook_dir):
        with open(entry.path, encoding="utf-8") as fh:
            graph = json.load(fh)
        per_material: Counter = Counter()
        _walk(graph.get("nodes", []), per_material)
        for t, n in per_material.items():
            counts[t] += n
            materials_by_type[t].append(entry.name)
    for t in materials_by_type:
        materials_by_type[t].sort()
    used = {t for t in counts if t in _NOISE_PATTERN_NODES}
    return {
        "counts": counts,
        "materials_by_type": dict(materials_by_type),
        "noise_used": sorted(used),
        "noise_unused": sorted(_NOISE_PATTERN_NODES - used),
    }


def main() -> int:
    report = audit()
    used = report["noise_used"]
    print(f"Noise/pattern generators in use: {len(used)} of {len(_NOISE_PATTERN_NODES)}")
    for t in used:
        mats = report["materials_by_type"][t]
        print(f"  {t}: {report['counts'][t]} instance(s) across {len(mats)} material(s) ({', '.join(mats)})")
    print(f"\nStill unused ({len(report['noise_unused'])}):")
    for t in report["noise_unused"]:
        print(f"  {t}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

Save as `quality/node_usage_audit.py`.

- [ ] **Step 4: Run the tests to confirm they pass**

Run: `python -m pytest tests/test_node_usage_audit.py -v`
Expected: PASS (3 tests).

- [ ] **Step 5: Run it for real and read the report**

Run: `python -m quality.node_usage_audit`
Confirm the output is sane (perlin/voronoi/warp heavily used; the round-1 six show up once each; the round-2 targets -- `fbm` Cellular variants, `truchet` Line, `shard_fbm` -- are still in `noise_unused` at this point, before Phase B ships them).

- [ ] **Step 6: Commit**

```bash
git add quality/node_usage_audit.py tests/test_node_usage_audit.py
git commit -m "feat(quality): node-usage-audit script, live noise/pattern coverage"
```

### Task 2: AUTHORING.md live-coverage line + test

**Files:**
- Modify: `docs/AUTHORING.md` (the "Noise vocabulary" section, after "The fix is a wider base-noise vocabulary, not more recolors.")
- Create: `tests/test_authoring_counts.py`

**Interfaces:**
- Consumes: `quality.node_usage_audit.audit()`, `_NOISE_PATTERN_NODES`.

The 2026-09-01 histogram paragraph stays as-is (it is a dated historical finding, correct to leave as history). Add a new paragraph directly after it that a test keeps honest going forward, the same convention `tests/test_readme_counts.py` uses for README.

- [ ] **Step 1: Write the failing test**

```python
"""AUTHORING.md's live noise-coverage line must match quality.node_usage_audit's
real output, the same convention tests/test_readme_counts.py uses for README.md."""
import os
import re

from quality.node_usage_audit import audit, _NOISE_PATTERN_NODES

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
with open(os.path.join(_ROOT, "docs", "AUTHORING.md"), encoding="utf-8") as fh:
    AUTHORING = fh.read()


def test_authoring_noise_coverage_line_matches_live_audit():
    m = re.search(
        r"as of this writing the cookbook uses (\d+) of (\d+) curated "
        r"noise/pattern generator types",
        AUTHORING,
    )
    assert m, (
        "AUTHORING.md's Noise vocabulary section must state "
        "'as of this writing the cookbook uses <N> of <M> curated "
        "noise/pattern generator types'"
    )
    report = audit()
    assert int(m.group(1)) == len(report["noise_used"])
    assert int(m.group(2)) == len(_NOISE_PATTERN_NODES)
```

Save as `tests/test_authoring_counts.py`.

- [ ] **Step 2: Run it to confirm it fails**

Run: `python -m pytest tests/test_authoring_counts.py -v`
Expected: FAIL (AUTHORING.md does not yet contain the sentence).

- [ ] **Step 3: Add the paragraph to AUTHORING.md**

Insert after the existing "The fix is a wider base-noise vocabulary, not more recolors." sentence:

```markdown
**Live coverage.** `python -m quality.node_usage_audit` recounts this from
the current cookbook instead of relying on a stale manual tally: as of this
writing the cookbook uses N of M curated noise/pattern generator types (see
the module's `_NOISE_PATTERN_NODES` list and its scope notes for exactly
what counts, and what is deliberately excluded -- distortion nodes, the
SDF family, and symbolic/glyph generators each have their own scope
ruling).
```

Run `python -m quality.node_usage_audit` and fill in the real N (`len(noise_used)`, still round-1's count at this point in the plan -- Task 10 will raise it once Phase B ships) and M (`len(_NOISE_PATTERN_NODES)`, 52 for the set above -- confirm with `python -c "from quality.node_usage_audit import _NOISE_PATTERN_NODES; print(len(_NOISE_PATTERN_NODES))"` rather than trusting this count by eye) in place of the placeholders.

- [ ] **Step 4: Run the test to confirm it passes**

Run: `python -m pytest tests/test_authoring_counts.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add docs/AUTHORING.md tests/test_authoring_counts.py
git commit -m "docs(authoring): live noise-coverage line, test-enforced"
```

---

## Phase B: Six proof materials

Each material is one task. Shared shape for every material task (do not restate per task): add a builder to the named `quality/cookbook_<category>.py` (register it in that file's `BUILDERS` dict); run `python -m quality.cookbook_<category> <id>` to write `quality/authored/cookbook-<category>/<id>/v1.ptex`; validate it (`mm-mcp` `validate` tool, or a pure `validate_graph` call via the validator module -- `python -c` is banned for renders but fine for a pure validate) and confirm ZERO errors; render it with an ABSOLUTE outdir and build a `render_preview` composite; SendUserFile the preview to Grayson and WAIT for approval or redirect (iterate the builder on his feedback, re-render); once he approves, write the prose recipe card `cookbook/<category>/<id>.md`; `python -m quality.promote_cookbook cookbook-<category>` to copy the `.ptex` and generate the card node-table; confirm `python -m quality.promote_cookbook --check` and `python -m quality.naming --cookbook <category>` are clean; commit. Exact gradient/param values are tuned by render-and-look, not fabricated here; each task gives the technique, the starting node params (from `quality/noise_gallery.py` or `quality/debug_swatches.py`), the donor, and the gates.

### Task 3: `l07_pebbled_leather` (fbm Cellular 1, leather)

**Files:**
- Modify: `quality/cookbook_leather.py`
- Create: `cookbook/leather/l07_pebbled_leather.{md,ptex}` (the `.ptex` via promote)

**Technique:** Clone `crocodile_skin` (the leather category's standard donor, per `l01`/`l02`/`l04`/`l05`/`l06`) and retype its base generator `voronoi_0` to `fbm` with the Cellular 1 basis, instead of the raw voronoi cells the existing crocodile/reptile variants use. Starting node (from `quality/noise_gallery.py` `_FBM_BASES`): `{"type":"fbm","parameters":{"noise":2,"scale_x":4,"scale_y":4,"folds":0,"iterations":3,"persistence":0.5}}` (Cellular 1: worley cells, dark centers -- reads as pores/stippling per AUTHORING.md's noise-vocabulary table). That is a softer, rounder pore pattern than voronoi's hard cell edges, closer to a pebbled/Saffiano leather grain than the sharp-scaled reptile look `l04` already covers. Keep the existing `colorize_1`/`colorize_3`/`normal_map_0` fan-out (albedo/roughness/height) wired to the retyped node's port 0 output, same as the donor's working chain. Tan or oxblood pebbled-leather palette, matte-to-semigloss roughness, moderate `normal_map param1` for the pore relief with `param4=0`.

- [ ] **Step 1-6:** Shared material shape above, category `leather`. Commit `feat(cookbook): l07_pebbled_leather (fbm Cellular 1 pores)`.

### Task 4: `f09_plaid_flannel` (fbm Cellular 3, fabrics)

**Files:**
- Modify: `quality/cookbook_fabrics.py`
- Create: `cookbook/fabrics/f09_plaid_flannel.{md,ptex}`

**Technique:** Clone `crocodile_skin` (the fabrics category's standard donor, per `f03`-`f08`) and retype `voronoi_0` to `fbm` with the Cellular 3 basis. Starting node: `{"type":"fbm","parameters":{"noise":4,"scale_x":4,"scale_y":4,"folds":0,"iterations":3,"persistence":0.5}}` (Cellular 3: woven crosshatch grid -- reads as plaid/coarse fabric per AUTHORING.md's table). This is a genuinely different structural family from `f07_herringbone_tweed`/`f08_donegal_tweed` (which use `weave2`/independent voronoi flecks, per project memory): the crosshatch grid IS the plaid pattern, not a woven simulation. Muted plaid palette (2-3 colors crossing at the grid lines), soft matte roughness, `normal_map param4=0` with LOW `param1` (flannel has a soft nap, not sharp relief).

- [ ] **Step 1-6:** Shared material shape, category `fabrics`. Commit `feat(cookbook): f09_plaid_flannel (fbm Cellular 3 crosshatch)`.

### Task 5: `f10_boucle_upholstery` (fbm Cellular 5, fabrics)

**Files:**
- Modify: `quality/cookbook_fabrics.py`
- Create: `cookbook/fabrics/f10_boucle_upholstery.{md,ptex}`

**Technique:** Same donor/retype approach as Task 4, different Cellular index: `{"type":"fbm","parameters":{"noise":6,"scale_x":4,"scale_y":4,"folds":0,"iterations":3,"persistence":0.5}}` (Cellular 5: soft diagonal weave -- reads as brushed cloth/quilted softness per AUTHORING.md's table). Tune scale up (smaller cells, finer scale_x/scale_y) during iteration to read as bouclé's characteristic tight nubby loops rather than a coarse weave. Cream or heathered-gray palette, high matte roughness, LOW `normal_map param1` for a soft nubby bump rather than hard relief. Distinct from `f06_velvet` (smooth pile, no cell structure) and `f09` above (hard crosshatch grid vs this soft diagonal cell pattern).

- [ ] **Step 1-6:** Shared material shape, category `fabrics`. Commit `feat(cookbook): f10_boucle_upholstery (fbm Cellular 5 nubby weave)`.

### Task 6: `sf05_circuit_maze_panel` (truchet Line mode, scifi)

**Files:**
- Modify: `quality/cookbook_scifi.py`
- Create: `cookbook/scifi/sf05_circuit_maze_panel.{md,ptex}`

**Technique:** Build from scratch (no donor), following `build_sf07_conduit_panel`'s exact from-scratch pattern (a single `truchet` node fanning out to `colorize_albedo`, `colorize_rgh`, and `normal_map_0`, then grouped into two subgraphs). Starting node: `{"type":"truchet","parameters":{"shape":0,"size":4}}` (Line mode -- bold maze/chevron/circuit lines, per AUTHORING.md's table, distinct from `sf07`'s Circle-mode interlocking pipes and from `sf03`'s flat etched-trace `pattern` Square wave). **Measure Line mode's real output range before setting any threshold**, the same way `sf07` had to be fixed on 2026-09-13: Circle mode measured 0.50-0.95, not the assumed 0/1 binary; Line mode's range is unverified and may differ. Render the noise-gallery `truchet_line` case (`quality/noise_gallery.py`'s `build_crossfamily_row`) in isolation and sample it with `quality/pngread.py` before choosing `colorize_albedo`'s threshold band and deciding whether `normal_map_0` should take the raw field directly (as `sf07` does) or needs an intermediate threshold node. Dark recessed panel / bright etched-line palette, moderate metallic for the line channel, raised or engraved relief per the measured range.

- [ ] **Step 1-6:** Shared material shape, category `scifi`. Commit `feat(cookbook): sf05_circuit_maze_panel (truchet Line maze)`.

### Task 7: `gl03_shattered_crystal` (shard_fbm, glass)

**Files:**
- Modify: `quality/cookbook_glass.py`
- Create: `cookbook/glass/gl03_shattered_crystal.{md,ptex}`

**Technique:** Clone `dry_earth` (the glass category's standard donor, per `gl01`/`gl02`) and retype its base generator to `shard_fbm`. Starting node (from `quality/noise_gallery.py` `build_crossfamily_row`): `{"type":"shard_fbm","parameters":{"sharp":0.7,"sx":7,"sy":7,"folds":0,"iter":4,"per":0.5,"off":0}}`, but push further during iteration -- AUTHORING.md's pinned finding is that `shard_fbm` reads as a soft turbulent cloud AT these defaults, NOT the crystalline shatter the name implies, and only becomes angular/crystalline with `sharp` raised well above 0.7 and `folds` pushed above 0. Iterate toward a sharp-edged shattered-glass crack network, distinct from `gl01`'s connected sandblast crack network (voronoi-plate family, soft/diffuse) and `gl02`'s faceted `voronoi_triangle` gem cuts (uniform hex-ish cells). Jewel-tone or clear-glass palette, low roughness, sharp `normal_map param1` for hard crystalline relief with `param4=0`.

- [ ] **Step 1-6:** Shared material shape, category `glass`. Commit `feat(cookbook): gl03_shattered_crystal (shard_fbm pushed crystalline)`.

### Task 8: `w06_burled_wood` (warp2, wood)

**Files:**
- Modify: `quality/cookbook_wood.py`
- Create: `cookbook/wood/w06_burled_wood.{md,ptex}`

**Technique:** Clone `wood` (the donor `w04`/`w05` already use) and retype one of its two chained `warp` nodes (`warp_0` or `warp_1`, inside the `wood_grain` chain feeding `blend_0`) to `warp2`. Starting node ports (from `quality/debug_swatches.py::build_swatch_warp2`): `warp2` takes the field to distort on input port 0 and a displacement/height map on input port 1, with `{"parameters":{"mode":0,"amount":0.3}}` as the swatch's verified starting point -- push `amount` up and feed a lower-frequency `perlin`/`fbm` as the displacement map (rather than the donor's existing high-frequency grain map) to get broad swirling figure/burl distortion instead of `warp`'s straight-grain stretch, which is what `w05_dark_walnut`'s unmodified chain already produces. This belongs to AUTHORING.md's separate "Distortion vocabulary" section, not the noise-audit's `_NOISE_PATTERN_NODES` list (it is a Transform-category node, per the MM library's own `tree_item` taxonomy: `"warp" -> "Transform/Warp"`), so Task 2/10's coverage numbers do not count it -- note this distinction in the recipe card so a future reader does not expect the audit script to show it. Rich burl-figure palette (walnut or maple burl), semi-gloss finish like `w05`, swirled grain into the normal for the burl relief.

- [ ] **Step 1-6:** Shared material shape, category `wood`. Commit `feat(cookbook): w06_burled_wood (warp2 burl figure)`.

---

## Phase C: README/AUTHORING integration

### Task 9: Update README counts and regenerate the contact sheet

**Files:**
- Modify: `README.md` (the three count sentences)
- Modify: `docs/images/cookbook-contact-sheet.png` (regenerate)

**Interfaces:**
- Consumes: the six new materials from Phase B (count is now 65; category count stays 12).

- [ ] **Step 1: Regenerate the contact sheet**

Run `python -m quality.contact_sheet` (confirm the exact entrypoint by reading the module first, per round 1's Task 10). It must include all 65 materials. Save as 8-bit palette PNG (pinned lesson from teardown #3).

- [ ] **Step 2: Update the three README count strings**

`README.md`: `"cookbook is 59 materials across 12 categories"` -> 65; `"The full cookbook (59 materials:"` -> 65; `"gallery of the 59 cookbook materials"` -> 65.

- [ ] **Step 3: Run the count gate**

Run: `python -m pytest tests/test_readme_counts.py -v`
Expected: all pass.

- [ ] **Step 4: Commit**

```bash
git add README.md docs/images/cookbook-contact-sheet.png
git commit -m "docs(readme): 65-material counts + regenerated contact sheet"
```

### Task 10: AUTHORING.md names the six new materials + coverage numbers rise

**Files:**
- Modify: `docs/AUTHORING.md` ("Noise vocabulary" section: the Task 2 live-coverage paragraph, and a short addition naming the round-2 materials, mirroring the round-1 sentence "Six cookbook proof materials shipped on previously-zero-use bases this session, including...")

**Interfaces:**
- Consumes: Phase B's six materials; `quality.node_usage_audit.audit()`'s live numbers.

- [ ] **Step 1: Re-run the audit and update the coverage line's digits**

Run: `python -m quality.node_usage_audit`. Update Task 2's paragraph digits (`N of M curated noise/pattern generator types`) to the new live `N` (now includes `fbm` Cellular 1/3/5 and `truchet`, plus `shard_fbm` if it lands as a top-level type name rather than folded into an existing count -- confirm against the real `noise_used` list, do not assume).

- [ ] **Step 2: Name the six round-2 materials**

Add a sentence naming the six: `l07_pebbled_leather` (fbm Cellular 1), `f09_plaid_flannel` (fbm Cellular 3), `f10_boucle_upholstery` (fbm Cellular 5), `sf05_circuit_maze_panel` (truchet Line), `gl03_shattered_crystal` (shard_fbm), and `w06_burled_wood` (warp2, filed under Distortion vocabulary instead, per Task 8's note -- cross-reference that section rather than duplicating the explanation).

- [ ] **Step 3: Run the coverage test**

Run: `python -m pytest tests/test_authoring_counts.py -v`
Expected: PASS with the new digits.

- [ ] **Step 4: Commit**

```bash
git add docs/AUTHORING.md
git commit -m "docs(authoring): name round-2 materials, refresh live coverage numbers"
```

---

## Phase D: Wrap

### Task 11: Full-suite green

- [ ] **Step 1: Run the fast suite**

Run: `python -m pytest -q -m "not integration"`
Expected: all pass (six new materials add cookbook-gate rows; the new audit + AUTHORING tests pass; README counts pass).

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
- Reusable node-usage-audit script: Task 1. Covered.
- AUTHORING.md's stale coverage line replaced with a test-enforced live one: Task 2, refreshed by Task 10. Covered.
- Six proof materials on unused nodes (fbm Cellular x3, truchet Line, shard_fbm, warp2): Tasks 3-8. Covered.
- README/AUTHORING integration: Tasks 9-10. Covered.

**Placeholder scan:** Material tasks (3-8) intentionally do not fabricate final gradient/param values (render-judged by Grayson); each gives the donor, the exact starting node params from `noise_gallery.py`/`debug_swatches.py`, the technique, and the gates -- the same deliberate property round 1's plan used, not a placeholder. Task 1/2's code and tests are fully concrete, no TBDs. Task 6 explicitly flags an unmeasured value range as a required in-task measurement step (mirroring the real `sf07` bug fix), not a placeholder -- it names the exact tool (`pngread.py`) and exact case (`truchet_line`) to use.

**Type/name consistency:** Material ids (`l07_pebbled_leather`, `f09_plaid_flannel`, `f10_boucle_upholstery`, `sf05_circuit_maze_panel`, `gl03_shattered_crystal`, `w06_burled_wood`) are used consistently across their tasks and Phase C's 59->65 count. `audit()`'s return keys (`counts`, `materials_by_type`, `noise_used`, `noise_unused`) are used identically in Task 1's tests, Task 2's test, and Task 10's step 1.

**Sequencing:** Task 1 must complete before Task 2 (Task 2 imports Task 1's module). Tasks 3-8 are independent of each other and of Phase A; they can run in parallel. Phase C (Tasks 9-10) depends on all of Phase B being promoted (for the count) and Task 1 (for the audit numbers). Task 10 additionally depends on Task 2 (extends its paragraph). Phase D is the final gate.

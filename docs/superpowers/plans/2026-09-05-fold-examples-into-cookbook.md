# Fold `examples/` into the cookbook + play-server port diagnostic

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Retire the second material library (`examples/`, 8 ungrouped Phase-3 hero graphs that the README front page links to) by folding its 7 authored materials into `cookbook/` as first-class, subgraph-grouped, carded, gated materials; make the README's counts self-checking; and make `mm-play` explain a port collision instead of silently serving from a stale process.

**Architecture:** Each hero already has a builder in `quality/author.py` (frozen Phase-3 infra, called but never edited). A small `take_variant` helper runs that builder under the target cookbook label, keeps the one variant that matches the shipped example, and hands the graph to a per-category cookbook builder, which groups it with `group_into_subgraph` and saves `v1.ptex` for `promote_cookbook.py`. A verify script renders the ungrouped original and the grouped result and asserts they match (grouping is organizational). Thumbnails are copied from `examples/images/` (render-identical), cards are written from the builder docstrings, and a new `tests/test_readme_counts.py` ties README numbers to the tree. Separately, `play/server.py` probes the port with a plain socket before binding, because on Windows `HTTPServer`'s `SO_REUSEADDR` lets a second bind silently succeed against a live listener.

**Tech Stack:** Python 3.13, pytest, Material Maker `.ptex` JSON, Godot 4.7.1 headless render (`mm_mcp.render`), Pillow (dev-only, for the contact sheet), stdlib `socket`/`subprocess`.

**Spec:** teardown #3 report (`C:\Users\Grayson\AppData\Local\Temp\claude\C--Projects-local-Tool-MaterialMaker-MCP\b42fe840-2428-4cc0-b7bf-403ddfb57d2c\scratchpad\teardown-2026-09-05-Tool-MaterialMaker-MCP.md`), section "The one change worth making first" and the verdict-table rows for `examples/`, README counts, and the play surface.

## Global Constraints

- Windows, PowerShell 5.1. Python is `.venv\Scripts\python.exe`. Run every `quality/*.py` script from the repo root (`C:\Projects-local\Tool-MaterialMaker-MCP`), never from inside `quality/` (breaks `.env` lookup).
- Never launch a Godot render from `python -c`; use a script file. Renders run one at a time (single Godot).
- Do NOT edit `quality/author.py`, `quality/test_set.json`, `quality/runs/`, `quality/scorecards/`, or `quality/authored/iter1/`. They are frozen Phase-3 evidence.
- Do NOT re-render whole cookbook labels (`render_cookbook.py <label>`, `_make_previews.py <label>`); Godot's render is not byte-deterministic and it churns unrelated thumbnails. Thumbnails for the 7 heroes are COPIED from `examples/images/`.
- Every new cookbook material must: validate with zero hard errors, have >= 1 top-level `"type": "graph"` node, have a `.md` card > 200 bytes beside it, have `docs/images/cookbook-<category>/<id>.png`, and pass `promote_cookbook.py --check`.
- `examples/` is copied to `C:\Projects-local\_to_delete\Tool-MaterialMaker-MCP-examples-2026-09-05` BEFORE `git rm`. Nothing on this machine is deleted outright.
- No em dashes in any prose written to disk (cards, docstrings, README). Use a colon, comma, or spaced hyphen.
- Fast suite baseline: `pytest -q -m "not integration"` = 590 passed. It must stay green after every task.
- Branch `fold-examples-into-cookbook` off `main`; conventional commits; merge `--no-ff` to `main` and push at the end.

## Verified facts the tasks rely on

Variant map (the shipped `examples/<id>/<id>.ptex` is JSON-equal to):

| id | author.py builder | matching variant | target category / label |
|---|---|---|---|
| `s02_gray_granite` | `build_s02_gray_granite` | v2 | stone / `cookbook-stone` |
| `f01_woven_denim` | `build_f01_woven_denim` | v1 | fabrics / `cookbook-fabrics` |
| `o01_mossy_forest_floor` | `build_o01_mossy_forest_floor` | v1 | organics / `cookbook-organics` |
| `combo01_rusted_painted_steel` | `build_combo01_rusted_painted_steel` | v1 | painted-metal / `cookbook-painted-metal` |
| `m01_weathered_copper` | `build_m01_weathered_copper` | v1 | metal (NEW) / `cookbook-metal` |
| `m02_brushed_aluminum` | `build_m02_brushed_aluminum` | v2 | metal (NEW) / `cookbook-metal` |
| `man02_ceramic_hex_tiles` | `build_man02_ceramic_hex_tiles` | v1 | ceramic (NEW) / `cookbook-ceramic` |

`s01_red_brick_wall` is a verbatim copy of Material Maker's bundled `bricks` example (no builder); it is dropped, not folded. `author.build_X(label)` writes `quality/authored/<label>/<id>/v1.ptex` and `v2.ptex` and returns their paths in order. `promote_cookbook.py` promotes only `v1.ptex`. `group_into_subgraph(graph, member_names, name, label, exposed, catalog)` is in `quality/author_helpers.py`; `exposed` is a list of `(internal_node, internal_param, slot_id, friendly_label)`.

---

### Task 1: `take_variant` helper + `verify_hero_fold.py` render check

**Files:**
- Modify: `quality/author_helpers.py` (append after `save_variant`)
- Create: `quality/verify_hero_fold.py`
- Test: `tests/test_author_helpers.py` (append)

**Interfaces:**
- Produces: `take_variant(builder: Callable[[str], list[str]], label: str, keep_n: int) -> dict`. Calls `builder(label)`, loads the returned path whose filename is `v{keep_n}.ptex`, deletes every other returned path, returns the graph dict. Raises `FileNotFoundError` if no returned path is `v{keep_n}.ptex`.
- Produces: `python quality/verify_hero_fold.py <label> <id>` renders `examples/<id>/<id>.ptex` and `quality/authored/<label>/<id>/v1.ptex` sequentially into `quality/cookbook/<label>/_foldcheck/<id>/{before,after}/` and exits 0 when `render_compare.renders_match` holds on the albedo maps, 1 otherwise, printing the `grid_mean_abs_diff`.

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_author_helpers.py`:

```python
import json
import os
import pytest

from author_helpers import take_variant


def _fake_builder(tmp_path):
    def builder(label):
        paths = []
        for n, marker in ((1, "one"), (2, "two")):
            p = tmp_path / label / f"v{n}.ptex"
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(json.dumps({"nodes": [], "connections": [], "marker": marker}),
                         encoding="utf-8")
            paths.append(str(p))
        return paths
    return builder


def test_take_variant_returns_requested_variant_and_removes_the_rest(tmp_path):
    g = take_variant(_fake_builder(tmp_path), "lbl", 2)
    assert g["marker"] == "two"
    assert not os.path.exists(tmp_path / "lbl" / "v1.ptex")
    assert os.path.exists(tmp_path / "lbl" / "v2.ptex")


def test_take_variant_raises_when_variant_missing(tmp_path):
    with pytest.raises(FileNotFoundError):
        take_variant(_fake_builder(tmp_path), "lbl", 3)
```

(Check the top of `tests/test_author_helpers.py` for how it already imports from `quality/`; reuse the same `sys.path` setup rather than adding a second one.)

- [ ] **Step 2: Run to verify it fails**

Run: `.venv\Scripts\python.exe -m pytest tests/test_author_helpers.py -q -k take_variant`
Expected: FAIL, `ImportError: cannot import name 'take_variant'`.

- [ ] **Step 3: Implement `take_variant`**

Append to `quality/author_helpers.py` right after `save_variant`:

```python
def take_variant(builder, label: str, keep_n: int) -> dict:
    """Run a Phase-3 `author.py` builder under a cookbook label and keep ONE of
    its variants. `builder(label)` writes v1.ptex, v2.ptex, ... under
    quality/authored/<label>/<case>/ and returns their paths; this loads the
    `v{keep_n}.ptex` one, deletes the others (promote_cookbook.py only ever
    promotes v1.ptex, so leftovers would be misleading), and returns the graph
    so the caller can group_into_subgraph it and re-save it as v1."""
    paths = builder(label)
    wanted = f"v{keep_n}.ptex"
    keep = next((p for p in paths if os.path.basename(p) == wanted), None)
    if keep is None:
        raise FileNotFoundError(f"{builder.__name__}({label!r}) produced no {wanted}: {paths}")
    with open(keep, encoding="utf-8") as fh:
        graph = json.load(fh)
    for p in paths:
        if p != keep and os.path.exists(p):
            os.remove(p)
    return graph
```

Add `import os` at the top of `author_helpers.py` if it is not already imported.

- [ ] **Step 4: Run to verify it passes**

Run: `.venv\Scripts\python.exe -m pytest tests/test_author_helpers.py -q`
Expected: all pass, including the 2 new ones.

- [ ] **Step 5: Create `quality/verify_hero_fold.py`**

```python
"""Render regression check for folding an examples/ hero into the cookbook.

    python quality/verify_hero_fold.py <label> <id>
    e.g. python quality/verify_hero_fold.py cookbook-stone s02_gray_granite

Renders the UNGROUPED original (examples/<id>/<id>.ptex) and the GROUPED
cookbook candidate (quality/authored/<label>/<id>/v1.ptex), one Godot at a
time, into quality/cookbook/<label>/_foldcheck/<id>/{before,after}/, then
compares the albedo maps with render_compare.renders_match. Grouping into
subgraphs is organizational, so the expected diff is ~0.0 (tolerance 3.0).
Exit 0 on match, 1 on mismatch or render failure.

Run from the repo root as a script FILE, never via `python -c` (Godot's
console launcher does not exit cleanly from -c; see quality/render_one.py).
"""
import json
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT / "src"))
sys.path.insert(0, str(_ROOT / "quality"))

from mm_mcp.config import load_config
from mm_mcp.render import render
from render_compare import grid_mean_abs_diff, renders_match


def _render_to(ptex_path: Path, outdir: Path, basename: str, cfg) -> Path:
    with open(ptex_path, encoding="utf-8") as fh:
        ptex = json.load(fh)
    outdir.mkdir(parents=True, exist_ok=True)
    result = render(ptex, size=512, outdir=str(outdir), basename=basename, cfg=cfg)
    if not result.ok:
        print(f"RENDER FAILED for {ptex_path}: {result.error}\n{result.log_tail}")
        sys.exit(1)
    albedo = outdir / f"{basename}_albedo.png"
    if not albedo.is_file():
        print(f"no albedo produced at {albedo}")
        sys.exit(1)
    return albedo


def main() -> int:
    if len(sys.argv) != 3:
        print(__doc__)
        return 2
    label, case_id = sys.argv[1], sys.argv[2]
    before_src = _ROOT / "examples" / case_id / f"{case_id}.ptex"
    after_src = _ROOT / "quality" / "authored" / label / case_id / "v1.ptex"
    for p in (before_src, after_src):
        if not p.is_file():
            print(f"missing input: {p}")
            return 1
    cfg = load_config()
    check_root = _ROOT / "quality" / "cookbook" / label / "_foldcheck" / case_id
    before = _render_to(before_src, check_root / "before", case_id, cfg)
    after = _render_to(after_src, check_root / "after", case_id, cfg)
    diff = grid_mean_abs_diff(str(before), str(after))
    ok = renders_match(str(before), str(after))
    print(f"{case_id}: grid_mean_abs_diff={diff:.3f} -> {'MATCH' if ok else 'MISMATCH'}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 6: Smoke the script's argument handling (no render)**

Run: `.venv\Scripts\python.exe quality\verify_hero_fold.py`
Expected: prints the docstring, exit code 2.

Run: `.venv\Scripts\python.exe quality\verify_hero_fold.py cookbook-stone nope`
Expected: `missing input: ...examples\nope\nope.ptex`, exit code 1.

- [ ] **Step 7: Commit**

```
git add quality/author_helpers.py quality/verify_hero_fold.py tests/test_author_helpers.py
git commit -m "feat(quality): take_variant helper + verify_hero_fold render check for folding examples/ heroes"
```

---

### Task 2: Pilot fold: `s02_gray_granite` into stone

**Files:**
- Modify: `quality/cookbook_stone.py` (add import, builder, BUILDERS entry)
- Create: `cookbook/stone/s02_gray_granite.md`
- Create: `docs/images/cookbook-stone/s02_gray_granite.png` (copied)
- Generated: `cookbook/stone/s02_gray_granite.ptex` (via promote)

**Interfaces:**
- Consumes: `take_variant` (Task 1), `group_into_subgraph`, `save_variant` from `author_helpers`; `author.build_s02_gray_granite`.
- Produces: the pattern every later hero task repeats exactly.

The graph (`iter1/v2`, 11 nodes) wires: `voronoi_0` port 2 -> `colorize_0` -> Material albedo (port 0); `voronoi_0` ports 0,1 + `perlin_0` -> `blend_0` (dead output in v2, kept); `perlin_0` -> `colorize_1` -> Material metallic (1); `perlin_0` -> `colorize_2` -> Material roughness (2); `voronoi_1` port 1 + `perlin_1` -> `warp_0` -> `normal_map_0` -> Material normal (4).

- [ ] **Step 1: Add the builder to `quality/cookbook_stone.py`**

Add to the imports block (the file already imports from `author_helpers`):

```python
import author  # frozen Phase-3 builders; called, never edited
from author_helpers import take_variant
```

Add the builder above `BUILDERS`:

```python
def build_s02_gray_granite(catalog: dict) -> str:
    """Polished gray granite, folded in from the Phase-3 hero set (was
    examples/s02_gray_granite, iter1 variant 2). The graph itself is
    author.build_s02_gray_granite's v2 unchanged: a `rock` clone whose albedo
    colorize is fed straight from voronoi_0's per-cell random output (port 2)
    at a fine cell scale, so each cell is a flat random gray fleck, with the
    normal_map param4=0 fix for real polished-stone micro-relief. This
    builder only GROUPS it: three named subgraphs so a person opening it sees
    fleck color, surface finish, and relief instead of 11 raw nodes.
    perlin_0 stays top-level because it feeds both the color group (blend_0)
    and the finish group (colorize_1, colorize_2)."""
    g = take_variant(author.build_s02_gray_granite, _LABEL, 2)
    group_into_subgraph(
        g, ["voronoi_0", "blend_0", "colorize_0"],
        "fleck_color", "Fleck Color",
        [("voronoi_0", "scale_x", "param0", "Fleck density"),
         ("colorize_0", "gradient", "param1", "Fleck colors")],
        catalog,
    )
    group_into_subgraph(
        g, ["colorize_1", "colorize_2"],
        "surface_finish", "Surface Finish",
        [("colorize_2", "gradient", "param0", "Polish (roughness)")],
        catalog,
    )
    group_into_subgraph(
        g, ["voronoi_1", "perlin_1", "warp_0", "normal_map_0"],
        "stone_relief", "Stone Relief",
        [("voronoi_1", "scale_x", "param0", "Relief cell size"),
         ("normal_map_0", "param1", "param1", "Relief strength")],
        catalog,
    )
    return save_variant(g, _LABEL, "s02_gray_granite", 1)
```

Add `"s02_gray_granite": build_s02_gray_granite,` as the FIRST entry of `BUILDERS` (ids sort before s04).

- [ ] **Step 2: Build only this material**

Run: `.venv\Scripts\python.exe quality\cookbook_stone.py s02_gray_granite`
Expected: prints `s02_gray_granite: ...quality\authored\cookbook-stone\s02_gray_granite\v1.ptex`. Confirm `v2.ptex` does NOT exist in that folder (take_variant removed it).

- [ ] **Step 3: Verify the grouped graph renders identically**

Run: `.venv\Scripts\python.exe quality\verify_hero_fold.py cookbook-stone s02_gray_granite`
Expected: `s02_gray_granite: grid_mean_abs_diff=0.000 -> MATCH` (anything under 3.0 is a pass; investigate anything above 0.5 before continuing, it means a wire was lost in grouping).

- [ ] **Step 4: Copy the thumbnail**

```
Copy-Item examples\images\s02_gray_granite.png docs\images\cookbook-stone\s02_gray_granite.png
```

- [ ] **Step 5: Write the recipe card `cookbook/stone/s02_gray_granite.md`**

```markdown
# s02_gray_granite - Polished gray granite

_Category: stone. Open the graph: `cookbook/stone/s02_gray_granite.ptex`._

Prompt: "polished gray granite". One of the Phase-3 hero materials (the frozen
15-case test set that took authoring quality from 3/15 to 15/15); folded into
the cookbook 2026-09-05 so it carries the same gates, card, and subgraph
grouping as every other material instead of living in a separate `examples/`
folder.

## Recipe

Clone `rock`. Granite's signature is a peppery spread of light and dark
mineral flecks, so the albedo voronoi (`voronoi_0`) is pushed to a fine cell
scale (44) with `randomness=1`, and the albedo colorize (`colorize_0`) is fed
straight from voronoi port 2, the per-cell random output, so each fine cell
becomes one flat random gray fleck (the earlier attempt blended a coarse
voronoi with smooth fbm and read as low-frequency fog). The ramp runs dark
biotite through mid feldspar to light quartz. Metallic is forced to zero
(`colorize_1`), roughness is low and narrow (`colorize_2`) for a polished slab.

Relief: `rock`'s normal chain (`voronoi_1` -> `warp_0` -> `normal_map_0`) is a
directly-fed analytic generator, so the default `param4=1` (buffered
edge_detect) renders flat. `param4=0` edge-detects the raw warped voronoi and
gives real polished-stone micro-relief; strength (`param1`) is kept at 0.35 so
it reads as a subtle speckle, not craggy rock. See the `param4=0` fix in the
guide (`guide://authoring`).

## Subgraph structure

Grouped per the "Grouping into subgraphs" lever in `docs/AUTHORING.md`.
Opening the graph shows 5 top-level nodes (one shared noise source, three
groups, `Material`) instead of the raw 11:

- **Fleck Color** (`voronoi_0`, `blend_0`, `colorize_0`). Exposed: `Fleck
  density` (voronoi scale), `Fleck colors` (the gray ramp). `blend_0` is the
  donor's original albedo blend, left in place but unconnected downstream in
  this variant.
- **Surface Finish** (`colorize_1`, `colorize_2`). Exposed: `Polish
  (roughness)`.
- **Stone Relief** (`voronoi_1`, `perlin_1`, `warp_0`, `normal_map_0`).
  Exposed: `Relief cell size`, `Relief strength`.

`perlin_0` stays top-level: it feeds both the color group and the finish
group, so folding it into either would just add a boundary port.

## See also

The invariant guide (`guide://authoring` or `docs/AUTHORING.md`) for the
rubric, the noise vocabulary, and the `param4=0` flat-normal fix. The frozen
scorecard this material was judged on is `quality/scorecards/2026-08-26-iter1.md`.
```

- [ ] **Step 6: Promote and gate**

Run: `.venv\Scripts\python.exe quality\promote_cookbook.py cookbook-stone`
Expected: `cookbook/ is updated`; `git status` shows exactly one new `.ptex` (`cookbook/stone/s02_gray_granite.ptex`) and no modified `.ptex` (if another stone `.ptex` shows modified, the stone builders drifted; STOP and report rather than committing it).

Run: `.venv\Scripts\python.exe quality\promote_cookbook.py --check`
Expected: `cookbook/ is in sync with quality/authored/`.

Run: `.venv\Scripts\python.exe -m pytest tests/test_cookbook_gate.py tests/test_cookbook_subgraph_gate.py -q`
Expected: all pass (47 entries now).

- [ ] **Step 7: Commit**

```
git add quality/cookbook_stone.py cookbook/stone/s02_gray_granite.ptex cookbook/stone/s02_gray_granite.md docs/images/cookbook-stone/s02_gray_granite.png
git commit -m "feat(cookbook): fold s02_gray_granite hero into stone (grouped, carded, gated)"
```

---

### Task 3: Fold `f01_woven_denim` (fabrics), `o01_mossy_forest_floor` (organics), `combo01_rusted_painted_steel` (painted-metal)

**Files:**
- Modify: `quality/cookbook_fabrics.py`, `quality/cookbook_organics.py`, `quality/cookbook_painted_metal.py`
- Create: `cookbook/fabrics/f01_woven_denim.md`, `cookbook/organics/o01_mossy_forest_floor.md`, `cookbook/painted-metal/combo01_rusted_painted_steel.md`
- Create (copied): `docs/images/cookbook-fabrics/f01_woven_denim.png`, `docs/images/cookbook-organics/o01_mossy_forest_floor.png`, `docs/images/cookbook-painted-metal/combo01_rusted_painted_steel.png`
- Generated: the three `cookbook/<category>/<id>.ptex`

**Interfaces:**
- Consumes: `take_variant`, `group_into_subgraph`, `save_variant`, `author.build_*`. Same pattern as Task 2.

In each of the three builder files add to the imports:

```python
import author  # frozen Phase-3 builders; called, never edited
from author_helpers import take_variant
```

- [ ] **Step 1: fabrics builder**

Graph (`iter1/v1`, 7 nodes): `voronoi_0` is a `diagonal_weave` (retyped). `voronoi_0` -> `colorize_0` -> `normal_map_0` -> Material 4; `voronoi_0` -> `colorize_1` -> Material 0 (albedo); `voronoi_0` -> `colorize_3` -> Material 2 (roughness); `uniform_0` -> Material 1 (metallic, black).

Add to `quality/cookbook_fabrics.py` above `BUILDERS`:

```python
def build_f01_woven_denim(catalog: dict) -> str:
    """Blue denim, folded in from the Phase-3 hero set (was
    examples/f01_woven_denim, iter1 variant 1). Graph unchanged from
    author.build_f01_woven_denim v1: `crocodile_skin` with its voronoi
    generator retyped to `diagonal_weave` so the twill drives albedo,
    roughness, and the normal, recolored indigo and matte, with the
    normal_map param4=0 fix that first unblocked flat normals project-wide.
    This builder only GROUPS it. `uniform_0` (the black metallic constant)
    stays top-level, the same convention the other crocodile_skin-derived
    materials use."""
    g = take_variant(author.build_f01_woven_denim, _LABEL, 1)
    group_into_subgraph(
        g, ["voronoi_0", "colorize_1", "colorize_3"],
        "twill_weave", "Twill Weave",
        [("voronoi_0", "size", "param0", "Weave size"),
         ("colorize_1", "gradient", "param1", "Thread color"),
         ("colorize_3", "gradient", "param2", "Cloth roughness")],
        catalog,
    )
    group_into_subgraph(
        g, ["colorize_0", "normal_map_0"],
        "weave_relief", "Weave Relief",
        [("normal_map_0", "param1", "param0", "Relief strength")],
        catalog,
    )
    return save_variant(g, _LABEL, "f01_woven_denim", 1)
```

Add `"f01_woven_denim": build_f01_woven_denim,` as the first `BUILDERS` entry.

Run: `.venv\Scripts\python.exe quality\cookbook_fabrics.py f01_woven_denim`
Run: `.venv\Scripts\python.exe quality\verify_hero_fold.py cookbook-fabrics f01_woven_denim`
Expected: MATCH.

- [ ] **Step 2: organics builder**

Graph (`iter1/v1`, 13 nodes, `dry_earth` clone): `voronoi_0` port 1 -> `colorize_1` -> `warp_0` (with `perlin_1` on port 1) -> `blend_0` port 0; `perlin_0` -> `colorize_0` -> `blend_0` port 1; `blend_0` -> Material 0. `perlin_1` -> `colorize_3` -> Material 1. `warp_0` -> `colorize_4` -> `blend_1` port 1; `perlin_0` -> `blend_1` port 0; `blend_1` -> `colorize` -> `normal_map_0` -> Material 4; `blend_1` -> Material 6 (height).

Add to `quality/cookbook_organics.py` above `BUILDERS`:

```python
def build_o01_mossy_forest_floor(catalog: dict) -> str:
    """Mossy forest floor, folded in from the Phase-3 hero set (was
    examples/o01_mossy_forest_floor, iter1 variant 1). Graph unchanged from
    author.build_o01_mossy_forest_floor v1: `dry_earth`'s cracked-plate
    ground with its earth ramp recolored dark soil -> green moss so plate
    tops read as moss and crack floors as soil. This builder only GROUPS it,
    the same two-group split as the other dry_earth-derived materials
    (gl01_frosted_glass, the terrain plates): a Ground Color group and a
    Ground Relief group, with the two shared perlin sources left top-level
    because each feeds both groups."""
    g = take_variant(author.build_o01_mossy_forest_floor, _LABEL, 1)
    group_into_subgraph(
        g, ["voronoi_0", "colorize_1", "warp_0", "colorize_0", "blend_0", "colorize_3"],
        "ground_color", "Ground Color",
        [("voronoi_0", "scale_x", "param0", "Plate size"),
         ("colorize_0", "gradient", "param1", "Moss and soil colors"),
         ("blend_0", "amount", "param2", "Crack contrast"),
         ("warp_0", "amount", "param3", "Plate warp")],
        catalog,
    )
    group_into_subgraph(
        g, ["colorize_4", "blend_1", "colorize", "normal_map_0"],
        "ground_relief", "Ground Relief",
        [("normal_map_0", "param1", "param0", "Relief strength")],
        catalog,
    )
    return save_variant(g, _LABEL, "o01_mossy_forest_floor", 1)
```

Add `"o01_mossy_forest_floor": build_o01_mossy_forest_floor,` as the first `BUILDERS` entry.

Run: `.venv\Scripts\python.exe quality\cookbook_organics.py o01_mossy_forest_floor`
Run: `.venv\Scripts\python.exe quality\verify_hero_fold.py cookbook-organics o01_mossy_forest_floor`
Expected: MATCH.

- [ ] **Step 3: painted-metal builder**

Graph (`iter1/v1`, 17 nodes, `rusted_metal` clone + a paint coat): rust layer is `perlin_0`->`colorize_0`->`blend_1` port 1; `perlin_1`->`colorize_1`->`blend_0` port 1 and `perlin_1`->`colorize_2`->`blend_0` port 0; `perlin_2`->`colorize_3`->`blend_0` port 2, `colorize_3`->Material 1 (metallic), `colorize_3`->`colorize_4`->`blend_1` port 0. Paint layer: `perlin_pm`->`colorize_pm` (peel mask), `perlin_pm`->`paint_alb`, `perlin_pm`->`paint_rgh`; `blend_alb`(port 0 `blend_0`, port 1 `paint_alb`, port 2 `colorize_pm`)->Material 0; `blend_rgh`(port 0 `blend_1`, port 1 `paint_rgh`, port 2 `colorize_pm`)->Material 2.

Add to `quality/cookbook_painted_metal.py` above `BUILDERS`:

```python
def build_combo01_rusted_painted_steel(catalog: dict) -> str:
    """Rusted painted steel, paint peeling to bare metal, folded in from the
    Phase-3 hero set (was examples/combo01_rusted_painted_steel, iter1
    variant 1). Graph unchanged from author.build_combo01_rusted_painted_steel
    v1: `rusted_metal` (rust albedo = blend_0, rust roughness = blend_1) with
    a flat paint coat composited OVER it through an irregular perlin-threshold
    peel mask, for both albedo and roughness. This builder only GROUPS it into
    the two layers the composite is made of, so the paint-over-rust idea is
    visible as two nodes feeding Material."""
    g = take_variant(author.build_combo01_rusted_painted_steel, _LABEL, 1)
    group_into_subgraph(
        g, ["perlin_0", "perlin_1", "perlin_2", "colorize_0", "colorize_1",
            "colorize_2", "colorize_3", "colorize_4", "blend_0", "blend_1"],
        "rust_layer", "Rust Layer",
        [("colorize_2", "gradient", "param0", "Bare metal color"),
         ("colorize_1", "gradient", "param1", "Rust color"),
         ("perlin_2", "scale_x", "param2", "Rust patch size")],
        catalog,
    )
    group_into_subgraph(
        g, ["perlin_pm", "colorize_pm", "paint_alb", "paint_rgh", "blend_alb", "blend_rgh"],
        "paint_coat", "Paint Coat",
        [("paint_alb", "gradient", "param0", "Paint color"),
         ("colorize_pm", "gradient", "param1", "Peel amount"),
         ("perlin_pm", "scale_x", "param2", "Peel patch size")],
        catalog,
    )
    return save_variant(g, _LABEL, "combo01_rusted_painted_steel", 1)
```

Add `"combo01_rusted_painted_steel": build_combo01_rusted_painted_steel,` as the first `BUILDERS` entry.

Run: `.venv\Scripts\python.exe quality\cookbook_painted_metal.py combo01_rusted_painted_steel`
Run: `.venv\Scripts\python.exe quality\verify_hero_fold.py cookbook-painted-metal combo01_rusted_painted_steel`
Expected: MATCH.

- [ ] **Step 4: Copy the three thumbnails**

```
Copy-Item examples\images\f01_woven_denim.png docs\images\cookbook-fabrics\f01_woven_denim.png
Copy-Item examples\images\o01_mossy_forest_floor.png docs\images\cookbook-organics\o01_mossy_forest_floor.png
Copy-Item examples\images\combo01_rusted_painted_steel.png docs\images\cookbook-painted-metal\combo01_rusted_painted_steel.png
```

- [ ] **Step 5: Write the three cards**

`cookbook/fabrics/f01_woven_denim.md`:

```markdown
# f01_woven_denim - Woven denim

_Category: fabrics. Open the graph: `cookbook/fabrics/f01_woven_denim.ptex`._

Prompt: "blue denim fabric". A Phase-3 hero material (frozen 15-case test
set), folded into the cookbook 2026-09-05 so it carries the same gates, card,
and subgraph grouping as every other material.

## Recipe

No bundled example uses Material Maker's weave nodes, so this GRAFTS one in:
clone `crocodile_skin` and retype its `voronoi_0` generator to
`diagonal_weave` (size 22), so the same generator -> colorize -> normal_map
chain that made scales now makes twill. `colorize_1` recolors the threads to
a narrow indigo range, `colorize_3` sets a high matte roughness, `uniform_0`
stays black so the cloth is non-metallic.

This was the material that surfaced the project-wide flat-normal blocker:
`normal_map` is a compound (input -> buffer -> switch(param4) -> edge_detect)
and its default `param4=1` runs edge_detect on a pre-rendered buffer that
comes back flat for a directly-fed analytic generator. `param4=0` routes the
raw weave into edge_detect and the twill appears in the normal map. Every
later analytic-generator material reuses that fix.

## Subgraph structure

Opening the graph shows 4 top-level nodes instead of 7:

- **Twill Weave** (`voronoi_0` as `diagonal_weave`, `colorize_1`,
  `colorize_3`). Exposed: `Weave size`, `Thread color`, `Cloth roughness`.
- **Weave Relief** (`colorize_0`, `normal_map_0`). Exposed: `Relief strength`.

`uniform_0` (the metallic constant) stays top-level, the same convention the
other crocodile_skin-derived materials follow for a single donor-default
constant feeding one port.

## See also

`guide://authoring` (or `docs/AUTHORING.md`) for the `param4=0` fix and the
weave family notes; `quality/scorecards/2026-08-26-iter1.md` for the frozen
verdict.
```

`cookbook/organics/o01_mossy_forest_floor.md`:

```markdown
# o01_mossy_forest_floor - Mossy forest floor

_Category: organics. Open the graph: `cookbook/organics/o01_mossy_forest_floor.ptex`._

Prompt: "mossy forest floor". A Phase-3 hero material (frozen 15-case test
set), folded into the cookbook 2026-09-05 so it carries the same gates, card,
and subgraph grouping as every other material.

## Recipe

Clone `dry_earth`, whose cracked-plate ground already has a working
crack-and-plate relief chain, and recolor only its earth albedo ramp
(`colorize_0`): plate tops become moss green, crack floors become dark soil,
so the same plate topology reads as a mossy floor instead of dried mud. The
lesson that later became the terrain set's rule ("pick the base by topology,
not by donor name"): a connected crack network is the right base for anything
that grows in patches between low seams.

## Subgraph structure

Same two-group split as the other dry_earth-derived materials
(`gl01_frosted_glass`, the terrain plates). Opening the graph shows 5
top-level nodes instead of 13:

- **Ground Color** (`voronoi_0`, `colorize_1`, `warp_0`, `colorize_0`,
  `blend_0`, `colorize_3`). Exposed: `Plate size`, `Moss and soil colors`,
  `Crack contrast`, `Plate warp`.
- **Ground Relief** (`colorize_4`, `blend_1`, `colorize`, `normal_map_0`).
  Exposed: `Relief strength`.

`perlin_0` and `perlin_1` stay top-level: each feeds both groups, so folding
either in would only relabel the sharing as an extra boundary port.

## See also

`guide://authoring` (or `docs/AUTHORING.md`), "Cross-material lessons" for
the topology-not-donor rule; `quality/scorecards/2026-08-26-iter1.md`.
```

`cookbook/painted-metal/combo01_rusted_painted_steel.md`:

```markdown
# combo01_rusted_painted_steel - Rusted painted steel

_Category: painted-metal. Open the graph: `cookbook/painted-metal/combo01_rusted_painted_steel.ptex`._

Prompt: "rusted painted steel, paint peeling to bare metal". A Phase-3 hero
material (frozen 15-case test set, the one "combo" case that required
compositing two materials), folded into the cookbook 2026-09-05 so it
carries the same gates, card, and subgraph grouping as every other material.

## Recipe

Clone `rusted_metal` (rust albedo comes out of `blend_0`, rust roughness out
of `blend_1`, patch-driven metallic out of `colorize_3`), then composite a
flat paint coat OVER it:

- peel mask: `perlin_pm` thresholded by `colorize_pm`, a hard-ish irregular
  edge;
- paint: `paint_alb` (flat color) and `paint_rgh` (flat low roughness), each a
  two-stop colorize with identical stops fed by the mask perlin so they are
  valid constant sources;
- `blend_alb` and `blend_rgh` put paint over rust with the mask as opacity.

Where the mask is high the paint shows (smooth, colored); where it is low the
rust and bare metal show through. This is the paint-over-rust peel composite
that the later painted-metal set (`pm03_chipped_paint`) generalized, and it
predates the pinned blend port convention, so read its port order from the
graph rather than assuming majority-on-port-1.

## Subgraph structure

Opening the graph shows 3 top-level nodes instead of 17, and the composite
reads as exactly what it is, two layers feeding Material:

- **Rust Layer** (all of the `rusted_metal` donor: `perlin_0/1/2`,
  `colorize_0..4`, `blend_0`, `blend_1`). Exposed: `Bare metal color`, `Rust
  color`, `Rust patch size`.
- **Paint Coat** (`perlin_pm`, `colorize_pm`, `paint_alb`, `paint_rgh`,
  `blend_alb`, `blend_rgh`). Exposed: `Paint color`, `Peel amount`, `Peel
  patch size`.

## See also

`guide://authoring` (or `docs/AUTHORING.md`) for the blend mask and opacity
notes in "Cross-material lessons"; `quality/scorecards/2026-08-26-iter1.md`.
```

- [ ] **Step 6: Promote, check, gate**

Run: `.venv\Scripts\python.exe quality\promote_cookbook.py cookbook-fabrics cookbook-organics cookbook-painted-metal`
Expected: `cookbook/ is updated`; `git status` shows exactly three new `.ptex` files and no modified `.ptex`. (A modified pre-existing `.ptex` means that category's builders drifted; STOP and report.)

Run: `.venv\Scripts\python.exe quality\promote_cookbook.py --check`
Expected: in sync.

Run: `.venv\Scripts\python.exe -m pytest tests/test_cookbook_gate.py tests/test_cookbook_subgraph_gate.py -q`
Expected: all pass (50 entries).

- [ ] **Step 7: Commit**

```
git add quality/cookbook_fabrics.py quality/cookbook_organics.py quality/cookbook_painted_metal.py cookbook/fabrics/f01_woven_denim.* cookbook/organics/o01_mossy_forest_floor.* cookbook/painted-metal/combo01_rusted_painted_steel.* docs/images/cookbook-fabrics/f01_woven_denim.png docs/images/cookbook-organics/o01_mossy_forest_floor.png docs/images/cookbook-painted-metal/combo01_rusted_painted_steel.png
git commit -m "feat(cookbook): fold denim, mossy floor, and rusted painted steel heroes into their categories"
```

---

### Task 4: New categories: `metal` (m01, m02) and `ceramic` (man02)

**Files:**
- Create: `quality/cookbook_metal.py`, `quality/cookbook_ceramic.py`
- Create: `cookbook/metal/m01_weathered_copper.md`, `cookbook/metal/m02_brushed_aluminum.md`, `cookbook/ceramic/man02_ceramic_hex_tiles.md`
- Create (copied): `docs/images/cookbook-metal/m01_weathered_copper.png`, `docs/images/cookbook-metal/m02_brushed_aluminum.png`, `docs/images/cookbook-ceramic/man02_ceramic_hex_tiles.png`
- Generated: `cookbook/metal/*.ptex`, `cookbook/ceramic/*.ptex`

**Interfaces:**
- Consumes: same helpers as Tasks 2 and 3.
- Produces: two new category labels `cookbook-metal`, `cookbook-ceramic` that `promote_cookbook.py` maps to `cookbook/metal/` and `cookbook/ceramic/` automatically (category = label minus the `cookbook-` prefix).

- [ ] **Step 1: Create `quality/cookbook_metal.py`**

`m01` graph (`iter1/v1`, 11 nodes, `rusted_metal` clone): `perlin_1`->`colorize_2`->`blend_0` port 0 (base copper); `perlin_1`->`colorize_1`->`blend_0` port 1 (verdigris); `perlin_2`->`colorize_3`->`blend_0` port 2 (patch mask), `colorize_3`->Material 1 (metallic), `colorize_3`->`colorize_4`->`blend_1` port 0; `perlin_0`->`colorize_0`->`blend_1` port 1; `blend_0`->Material 0; `blend_1`->Material 2.

`m02` graph (`iter1/v2`, 12 nodes, `wood` clone straightened): live chain is `perlin_2`->`blend_0` ports 0 and 1; `blend_0`->`normal_map_0`->Material 4; `blend_0`->`colorize_0`->Material 2; `blend_0`->`colorize_2`->Material 0. Dead chain (wood's knot warp, disconnected by the straightening rewire, output unused): `perlin_0`, `perlin_1`->`warp_0`; `voronoi_0`->`colorize_1`; `warp_0` + `colorize_1` -> `warp_1` (goes nowhere). Material metallic port 1 is unconnected on purpose (scalar metallic=1 applies).

```python
"""Cookbook: bare-metal category. Both materials are Phase-3 heroes folded in
from the retired examples/ folder (2026-09-05): the graphs come unchanged
from quality/author.py's frozen builders via take_variant; these builders
only group them into named subgraphs. Outputs land under
quality/authored/cookbook-metal/<case>/v1.ptex.

Run: python quality/cookbook_metal.py
Then: python quality/promote_cookbook.py cookbook-metal
"""
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
import author  # frozen Phase-3 builders; called, never edited
from author_helpers import save_variant, take_variant, group_into_subgraph

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from mm_mcp.catalog_builder import build_catalog
from mm_mcp.config import load_config

_LABEL = "cookbook-metal"


def build_m01_weathered_copper(catalog: dict) -> str:
    """Weathered copper (was examples/m01_weathered_copper, iter1 variant 1):
    `rusted_metal`'s two-layer blend recolored, base gray -> copper, patches
    orange rust -> green verdigris, patch mask unchanged. Grouped into the
    three ideas the donor is built from: where the patches are, what the two
    metals look like, and how rough each is."""
    g = take_variant(author.build_m01_weathered_copper, _LABEL, 1)
    group_into_subgraph(
        g, ["perlin_2", "colorize_3", "colorize_4"],
        "patina_pattern", "Patina Pattern",
        [("perlin_2", "scale_x", "param0", "Patch size"),
         ("colorize_3", "gradient", "param1", "Patina coverage")],
        catalog,
    )
    group_into_subgraph(
        g, ["perlin_1", "colorize_2", "colorize_1", "blend_0"],
        "copper_color", "Copper Color",
        [("colorize_2", "gradient", "param0", "Copper color"),
         ("colorize_1", "gradient", "param1", "Verdigris color")],
        catalog,
    )
    group_into_subgraph(
        g, ["perlin_0", "colorize_0", "blend_1"],
        "surface_finish", "Surface Finish",
        [("colorize_0", "gradient", "param0", "Roughness")],
        catalog,
    )
    return save_variant(g, _LABEL, "m01_weathered_copper", 1)


def build_m02_brushed_aluminum(catalog: dict) -> str:
    """Brushed aluminum (was examples/m02_brushed_aluminum, iter1 variant 2):
    `wood` clone with the grain straightened (blend_0's second input fed from
    the straight perlin_2 instead of the knot warp), finer longer streaks,
    neutral gray albedo, uniform metallic (the grain-driven metallic wire is
    dropped so the scalar 1 applies), low anisotropic roughness, and shallow
    brush-scratch relief via normal_map param4=0. The straightening leaves
    wood's knot-warp chain (perlin_0, perlin_1, warp_0, voronoi_0, colorize_1,
    warp_1) connected to nothing downstream; it is grouped separately and
    labeled as the unused donor leftover rather than deleted, so the graph
    still tells the "wood grain became brushed metal" story."""
    g = take_variant(author.build_m02_brushed_aluminum, _LABEL, 2)
    group_into_subgraph(
        g, ["perlin_2", "blend_0", "colorize_2", "colorize_0", "normal_map_0"],
        "brushed_finish", "Brushed Finish",
        [("perlin_2", "scale_x", "param0", "Streak length"),
         ("perlin_2", "scale_y", "param1", "Streak density"),
         ("colorize_2", "gradient", "param2", "Aluminum color"),
         ("colorize_0", "gradient", "param3", "Roughness"),
         ("normal_map_0", "param1", "param4", "Scratch depth")],
        catalog,
    )
    group_into_subgraph(
        g, ["perlin_0", "perlin_1", "warp_0", "voronoi_0", "colorize_1", "warp_1"],
        "wood_knot_leftover", "Wood Donor Leftover (unused)",
        [],
        catalog,
    )
    return save_variant(g, _LABEL, "m02_brushed_aluminum", 1)


BUILDERS = {
    "m01_weathered_copper": build_m01_weathered_copper,
    "m02_brushed_aluminum": build_m02_brushed_aluminum,
}


def main() -> int:
    targets = sys.argv[1:] or list(BUILDERS.keys())
    catalog = build_catalog(load_config().nodes_dir)  # once per run, threaded through
    for case in targets:
        path = BUILDERS[case](catalog)
        print(f"{case}: {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

Note on the empty `exposed` list for the leftover group: `group_into_subgraph` builds `widgets=[]` and `params={}` from it, which is a valid collapsed node with no remote widgets. If `group_into_subgraph` rejects an empty list at runtime, expose one harmless parameter instead: `[("voronoi_0", "scale_x", "param0", "Knot scale (unused)")]`.

Run: `.venv\Scripts\python.exe quality\cookbook_metal.py`
Run: `.venv\Scripts\python.exe quality\verify_hero_fold.py cookbook-metal m01_weathered_copper`
Run: `.venv\Scripts\python.exe quality\verify_hero_fold.py cookbook-metal m02_brushed_aluminum`
Expected: MATCH for both.

- [ ] **Step 2: Create `quality/cookbook_ceramic.py`**

`man02` graph (`iter1/v1`, 10 nodes, `beehive` clone): `beehive_2` port 0 -> `colorize_2`, `colorize_5` (albedo -> Material 0), `colorize_4` (roughness -> Material 2); `beehive_2` port 1 -> `colorize`; `colorize_2` + `colorize` -> `blend` -> `normal_map` -> Material 4; `blend` -> `colorize_3` -> Material 6 (height); `uniform_greyscale` -> Material 1 (metallic 0). Note these node names have NO numeric suffix (`colorize`, `blend`, `normal_map`).

```python
"""Cookbook: ceramic category. Phase-3 hero folded in from the retired
examples/ folder (2026-09-05): the graph comes unchanged from
quality/author.py's frozen builder via take_variant; this builder only groups
it. Outputs land under quality/authored/cookbook-ceramic/<case>/v1.ptex.

Run: python quality/cookbook_ceramic.py
Then: python quality/promote_cookbook.py cookbook-ceramic
"""
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
import author  # frozen Phase-3 builders; called, never edited
from author_helpers import save_variant, take_variant, group_into_subgraph

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from mm_mcp.catalog_builder import build_catalog
from mm_mcp.config import load_config

_LABEL = "cookbook-ceramic"


def build_man02_ceramic_hex_tiles(catalog: dict) -> str:
    """White ceramic hexagon tiles (was examples/man02_ceramic_hex_tiles,
    iter1 variant 1): `beehive` clone, non-metallic, faces recolored white
    with a thin dark grout band, roughness inverted (glazed faces, rough
    grout), hex relief kept so grout reads recessed. Grouped into the tile
    pattern (what you see) and the tile relief (what you feel);
    `uniform_greyscale` (metallic 0) stays top-level as a single
    donor-default constant."""
    g = take_variant(author.build_man02_ceramic_hex_tiles, _LABEL, 1)
    group_into_subgraph(
        g, ["beehive_2", "colorize_5", "colorize_4"],
        "tile_pattern", "Tile Pattern",
        [("beehive_2", "sx", "param0", "Tiles across"),
         ("beehive_2", "sy", "param1", "Tiles down"),
         ("colorize_5", "gradient", "param2", "Tile and grout color"),
         ("colorize_4", "gradient", "param3", "Glaze roughness")],
        catalog,
    )
    group_into_subgraph(
        g, ["colorize_2", "colorize", "blend", "normal_map", "colorize_3"],
        "tile_relief", "Tile Relief",
        [("normal_map", "param1", "param0", "Grout depth"),
         ("blend", "amount", "param1", "Edge softness")],
        catalog,
    )
    return save_variant(g, _LABEL, "man02_ceramic_hex_tiles", 1)


BUILDERS = {
    "man02_ceramic_hex_tiles": build_man02_ceramic_hex_tiles,
}


def main() -> int:
    targets = sys.argv[1:] or list(BUILDERS.keys())
    catalog = build_catalog(load_config().nodes_dir)
    for case in targets:
        path = BUILDERS[case](catalog)
        print(f"{case}: {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

Run: `.venv\Scripts\python.exe quality\cookbook_ceramic.py`
Run: `.venv\Scripts\python.exe quality\verify_hero_fold.py cookbook-ceramic man02_ceramic_hex_tiles`
Expected: MATCH.

- [ ] **Step 3: Copy thumbnails into the two new image folders**

```
New-Item -ItemType Directory -Force docs\images\cookbook-metal, docs\images\cookbook-ceramic | Out-Null
Copy-Item examples\images\m01_weathered_copper.png docs\images\cookbook-metal\m01_weathered_copper.png
Copy-Item examples\images\m02_brushed_aluminum.png docs\images\cookbook-metal\m02_brushed_aluminum.png
Copy-Item examples\images\man02_ceramic_hex_tiles.png docs\images\cookbook-ceramic\man02_ceramic_hex_tiles.png
```

- [ ] **Step 4: Write the three cards**

`cookbook/metal/m01_weathered_copper.md`:

```markdown
# m01_weathered_copper - Weathered copper

_Category: metal. Open the graph: `cookbook/metal/m01_weathered_copper.ptex`._

Prompt: "weathered copper". A Phase-3 hero material (frozen 15-case test
set), folded into the cookbook 2026-09-05 as one of the two founding members
of the bare-metal category.

## Recipe

Clone `rusted_metal`, which is already a two-layer metal: a base metal
(`colorize_2`) with weathered patches (`colorize_1`) masked in by a perlin
threshold (`colorize_3`), plus a roughness blend that follows the same mask.
Recolor only: base gray -> warm copper, patches orange rust -> green
verdigris. The patch mask still drives metallic, so the verdigris reads as a
dull crust and the exposed copper stays metallic. The lesson this hero
taught: a donor that already has the right LAYER STRUCTURE only needs its
ramps changed; look for two-layer donors before building composites.

## Subgraph structure

Opening the graph shows 4 top-level nodes instead of 11:

- **Patina Pattern** (`perlin_2`, `colorize_3`, `colorize_4`). Exposed:
  `Patch size`, `Patina coverage`. Its output also drives Material's metallic.
- **Copper Color** (`perlin_1`, `colorize_2`, `colorize_1`, `blend_0`).
  Exposed: `Copper color`, `Verdigris color`.
- **Surface Finish** (`perlin_0`, `colorize_0`, `blend_1`). Exposed:
  `Roughness`.

## See also

`guide://authoring` (or `docs/AUTHORING.md`), the recolor lever and the
masked two-layer blend; `quality/scorecards/2026-08-26-iter1.md`.
```

`cookbook/metal/m02_brushed_aluminum.md`:

```markdown
# m02_brushed_aluminum - Brushed aluminum

_Category: metal. Open the graph: `cookbook/metal/m02_brushed_aluminum.ptex`._

Prompt: "brushed aluminum". A Phase-3 hero material (frozen 15-case test
set), folded into the cookbook 2026-09-05 as one of the two founding members
of the bare-metal category.

## Recipe

The first attempt cloned `rock` and stretched its perlin; the streaks were
soft and the normal rendered flat. The structural insight that fixed it:
brushed metal is directional streaks WITH relief, which is exactly what wood
grain is. So clone `wood`, whose `perlin_2` (scale 32 x 4) is a directional
generator already feeding a working normal chain, and:

- straighten the grain: feed `blend_0`'s second input from the straight
  `perlin_2` instead of the knot warp, so streaks run parallel;
- finer, longer streaks (raise `scale_x`, drop `scale_y`, 8 iterations);
- neutralize albedo to aluminum gray (`colorize_2`), no wood tint;
- force uniform full metallic by dropping the grain-driven metallic wire so
  Material's scalar metallic=1 applies;
- low brushed roughness with streak-driven anisotropy (`colorize_0`);
- shallow scratch relief: `normal_map_0` with the `param4=0` fix at low
  strength.

## Subgraph structure

Opening the graph shows 3 top-level nodes instead of 12:

- **Brushed Finish** (`perlin_2`, `blend_0`, `colorize_2`, `colorize_0`,
  `normal_map_0`). Exposed: `Streak length`, `Streak density`, `Aluminum
  color`, `Roughness`, `Scratch depth`.
- **Wood Donor Leftover (unused)** (`perlin_0`, `perlin_1`, `warp_0`,
  `voronoi_0`, `colorize_1`, `warp_1`). Wood's knot-warp chain, disconnected
  by the straightening rewire; it feeds nothing. Kept and labeled rather than
  deleted so the graph still shows how a wood grain became a brushed finish.
  Delete it freely if you are editing this material for real.

## See also

`guide://authoring` (or `docs/AUTHORING.md`) for the `param4=0` fix and the
"pick the base by topology" lesson; `quality/scorecards/2026-08-26-iter1.md`.
```

`cookbook/ceramic/man02_ceramic_hex_tiles.md`:

```markdown
# man02_ceramic_hex_tiles - White ceramic hexagon tiles

_Category: ceramic. Open the graph: `cookbook/ceramic/man02_ceramic_hex_tiles.ptex`._

Prompt: "white ceramic hexagon tiles". A Phase-3 hero material (frozen
15-case test set), folded into the cookbook 2026-09-05 as the founding member
of the ceramic category.

## Recipe

Clone `beehive`, Material Maker's bundled hex field. `beehive_2`'s port 0
peaks at each cell center and falls to a narrow low band at the edges, so
one ramp does both jobs: `colorize_5` maps the low band to a thin dark grout
line and everything above 0.20 to white tile, and `colorize_4` inverts that
for roughness (grout rough, glazed faces near-mirror). The metallic constant
(`uniform_greyscale`) is set to 0. The hex relief from the donor's blend ->
normal_map chain is kept so the grout reads recessed; height (port 6) comes
from the same blend.

The lesson: when a bundled example already has the exact pattern topology
(regular hex cells), the whole material is two gradient ramps and one
constant. Tile density is `sx`/`sy` on the beehive (20 x 12 here).

## Subgraph structure

Opening the graph shows 4 top-level nodes instead of 10:

- **Tile Pattern** (`beehive_2`, `colorize_5`, `colorize_4`). Exposed:
  `Tiles across`, `Tiles down`, `Tile and grout color`, `Glaze roughness`.
- **Tile Relief** (`colorize_2`, `colorize`, `blend`, `normal_map`,
  `colorize_3`). Exposed: `Grout depth`, `Edge softness`.

`uniform_greyscale` (metallic 0) stays top-level as a single donor-default
constant feeding one port.

## See also

`guide://authoring` (or `docs/AUTHORING.md`), the `pattern`/`beehive` notes;
`quality/scorecards/2026-08-26-iter1.md`.
```

- [ ] **Step 5: Promote, check, gate**

Run: `.venv\Scripts\python.exe quality\promote_cookbook.py cookbook-metal cookbook-ceramic`
Expected: `cookbook/ is updated`; new folders `cookbook/metal/` and `cookbook/ceramic/` with 2 + 1 `.ptex`.

Run: `.venv\Scripts\python.exe quality\promote_cookbook.py --check`
Expected: in sync.

Run: `.venv\Scripts\python.exe -m pytest tests/test_cookbook_gate.py tests/test_cookbook_subgraph_gate.py -q`
Expected: all pass (53 entries).

- [ ] **Step 6: Commit**

```
git add quality/cookbook_metal.py quality/cookbook_ceramic.py cookbook/metal cookbook/ceramic docs/images/cookbook-metal docs/images/cookbook-ceramic
git commit -m "feat(cookbook): new metal and ceramic categories from the copper, aluminum, and hex-tile heroes"
```

---

### Task 5: Retire `examples/`, repoint README, self-checking counts, contact sheet

**Files:**
- Delete (git rm, after copying to `_to_delete`): `examples/`
- Modify: `README.md` (lines 53, 62-83, 226, 273), `tests/test_cookbook_gate.py:26`
- Create: `tests/test_readme_counts.py`
- Regenerate: `docs/images/cookbook-contact-sheet.png`

**Interfaces:**
- Consumes: `mm_mcp.cookbook.list_cookbook(cookbook_dir) -> list[CookbookEntry]` with `.name` and `.category`; `mm_mcp.server` module attributes `live_start`, `live_get_graph`, `live_clear`, `live_apply`, `live_render_node_output`, `live_render`, `live_load`.
- Produces: README wording in digits so the counts test can parse it: `53 materials across 12 categories`, `plus 7 more in Live mode`.

- [ ] **Step 1: Write the failing counts test `tests/test_readme_counts.py`**

```python
"""README numbers must match the tree. Teardowns #1 and #3 both found
hand-typed counts that had drifted (11/15 vs 15/15; six live tools vs seven;
46 materials vs a 43-material contact sheet). This closes the drift class:
the README states counts in digits and this test recomputes them."""
import inspect
import os
import re

from mm_mcp import server
from mm_mcp.cookbook import list_cookbook

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
README = open(os.path.join(_ROOT, "README.md"), encoding="utf-8").read()
ENTRIES = list_cookbook(os.path.join(_ROOT, "cookbook"))


def _live_tool_count() -> int:
    return len([name for name, obj in vars(server).items()
                if name.startswith("live_") and inspect.isfunction(obj)])


def test_readme_cookbook_material_count_matches_tree():
    m = re.search(r"cookbook is (\d+) materials across (\d+) categories", README)
    assert m, "README 'Material cookbook' sentence must read '<N> materials across <M> categories'"
    assert int(m.group(1)) == len(ENTRIES)
    assert int(m.group(2)) == len({e.category for e in ENTRIES})


def test_readme_contact_sheet_summary_count_matches_tree():
    m = re.search(r"Show the cookbook contact sheet</b> \((\d+) materials:", README)
    assert m, "contact-sheet <summary> must state '(<N> materials:'"
    assert int(m.group(1)) == len(ENTRIES)


def test_readme_play_surface_count_matches_tree():
    m = re.search(r"gallery of the (\d+)\s+cookbook materials", README)
    assert m, "Play surface paragraph must read 'gallery of the <N> cookbook materials'"
    assert int(m.group(1)) == len(ENTRIES)


def test_readme_live_tool_count_matches_server():
    m = re.search(r"plus (\d+) more in Live mode", README)
    assert m, "Tools sentence must read 'plus <N> more in Live mode'"
    assert int(m.group(1)) == _live_tool_count()


def test_readme_live_tool_table_lists_every_live_tool():
    rows = set(re.findall(r"^\| `(live_\w+)` \|", README, flags=re.M))
    expected = {name for name, obj in vars(server).items()
                if name.startswith("live_") and inspect.isfunction(obj)}
    assert rows == expected
```

- [ ] **Step 2: Run to verify it fails**

Run: `.venv\Scripts\python.exe -m pytest tests/test_readme_counts.py -q`
Expected: 4 failures (the words "ten"/"six" and "46 more materials" do not match the digit regexes; the live table test may already pass since the README lists all 7 rows).

- [ ] **Step 3: Edit README.md**

Line 53 (Gallery paragraph): replace

```
graphs and flat swatches are in [`examples/`](examples/).
```

with

```
graphs live in the cookbook below (`s02_gray_granite`, `f01_woven_denim`,
`man02_ceramic_hex_tiles`, `m02_brushed_aluminum`, `o01_mossy_forest_floor`,
`o03_tree_bark`, `w05_dark_walnut`); the hand-finished one is
[`saved_graphs/bricks_grayson_edit.ptex`](saved_graphs/bricks_grayson_edit.ptex).
```

Lines 64-65: replace `Beyond the frozen gallery above, the cookbook is 46 more materials across\nten categories,` with `The cookbook is 53 materials across 12 categories (the gallery above is drawn from it),`. Keep the rest of that sentence.

Line 76 `<summary>`: `(53 materials: ceramic, fabrics, glass, leather, metal, organics, painted metal, plastics, sci-fi, stone, terrain, wood)`.

Line 79 alt text: `alt="Contact sheet of all 53 cookbook materials across 12 categories"`.

Lines 81-82 (the italic "_Not yet regenerated..._" paragraph): delete it entirely.

Line 226: `The server exposes 10 batch-mode tools and two resources (plus 7 more in Live mode, below):`

Line 273: `tweak a cookbook material without touching a node graph: a gallery of the 53` (keep the line break and `cookbook materials` on the next line as-is).

- [ ] **Step 4: Tighten the cookbook gate floor**

In `tests/test_cookbook_gate.py`, change

```python
    assert len(ENTRIES) >= 43, f"expected the 43 promoted graphs, found {len(ENTRIES)}"
```

to

```python
    assert len(ENTRIES) >= 53, f"expected at least the 53 promoted graphs, found {len(ENTRIES)}"
```

- [ ] **Step 5: Regenerate the contact sheet**

Run: `.venv\Scripts\python.exe quality\contact_sheet.py`
This tiles every `docs/images/cookbook-*/` folder (12 now) into `docs/images/contact-sheet-<labels>.png`. Read the script's final `print` for the exact output filename, then:

```
Move-Item -Force docs\images\contact-sheet-*.png docs\images\cookbook-contact-sheet.png
```

Open it (Read tool) and confirm 53 tiles with labels including `metal/m01_weathered_copper` and `ceramic/man02_ceramic_hex_tiles`. If Pillow is missing: `.venv\Scripts\python.exe -m pip install pillow` (dev-only, not a project dependency).

- [ ] **Step 6: Retire `examples/`**

```
Copy-Item -Recurse examples C:\Projects-local\_to_delete\Tool-MaterialMaker-MCP-examples-2026-09-05
git rm -r -q examples
```

Confirm `Test-Path C:\Projects-local\_to_delete\Tool-MaterialMaker-MCP-examples-2026-09-05\README.md` is True and `Test-Path examples` is False.

- [ ] **Step 7: Run the counts test and the full fast suite**

Run: `.venv\Scripts\python.exe -m pytest tests/test_readme_counts.py -q`
Expected: 5 passed.

Run: `.venv\Scripts\python.exe -m pytest -q -m "not integration"`
Expected: all pass (590 + Task 1's 2 + 7 new cookbook entries x 3 gates + 5 counts tests = 618).

Run: `git status --short` and confirm nothing outside this task's file list is modified (in particular no pre-existing `docs/images/cookbook-*/*.png` changed; the contact sheet is the only regenerated image).

- [ ] **Step 8: Commit**

```
git add README.md tests/test_readme_counts.py tests/test_cookbook_gate.py docs/images/cookbook-contact-sheet.png
git commit -m "feat!: retire examples/ (folded into cookbook), README counts are now test-enforced

The 8 Phase-3 hero graphs the README gallery linked to lived outside the
cookbook, ungrouped and ungated. Seven are now cookbook materials (Tasks 2-4);
s01_red_brick_wall was a verbatim copy of the bundled bricks example and is
dropped. examples/ is copied to _to_delete before removal. README counts are
stated in digits and tests/test_readme_counts.py recomputes them from the tree."
```

(The `git rm` from Step 6 is already staged; the commit picks it up. The `feat!` marks the removal of a top-level folder people may have linked to; release-please has `bump-minor-pre-major` so it cuts 0.x, not 1.0.)

---

### Task 6: `mm-play` port-collision diagnostic

**Files:**
- Modify: `src/mm_mcp/play/server.py` (`serve()` plus two new helpers)
- Test: `tests/test_play_server.py` (append)

**Interfaces:**
- Produces: `port_in_use(port: int) -> bool` (plain-socket connect probe on `127.0.0.1`), `describe_port_owner(port: int) -> str | None` (Windows: `"PID 1234 (python.exe)"`; elsewhere or on any parse failure: `None`). `serve()` returns `None` after printing a message that contains the port number, the owner when known, and both fixes.

Why a probe and not just catching the bind error: `http.server.HTTPServer` sets `allow_reuse_address = 1`, which on Windows sets `SO_REUSEADDR`, and Windows then lets a second process bind the same port while the first is still listening. That is exactly how a stale play-server on 8788 kept receiving the browser's requests while a freshly started server believed it had bound fine (see HANDOFF "Heads-up"). So the check has to be a connect probe before binding, and the bind itself is made strict as a backstop.

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_play_server.py`:

```python
import os
import socket


def test_serve_reports_port_in_use_with_owner(capsys):
    # A stale mm-play (or any process) already listening on the play port
    # must produce an actionable startup message naming the port, not a
    # server that silently binds beside the squatter (Windows SO_REUSEADDR
    # quirk) or a bare OSError traceback.
    squatter = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    squatter.bind(("127.0.0.1", 0))
    squatter.listen(1)
    port = squatter.getsockname()[1]
    try:
        cfg = replace(load_config(), play_port=port)
        result = server.serve(cfg=cfg, open_browser=False)
    finally:
        squatter.close()
    assert result is None
    out = capsys.readouterr().out
    assert f"port {port}" in out
    assert "MM_PLAY_PORT" in out
    if os.name == "nt":
        assert "PID" in out and "Stop-Process" in out


def test_port_in_use_probe():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(("127.0.0.1", 0))
    s.listen(1)
    port = s.getsockname()[1]
    try:
        assert server.port_in_use(port) is True
    finally:
        s.close()
    assert server.port_in_use(port) is False


def test_describe_port_owner_names_this_process_on_windows():
    if os.name != "nt":
        pytest.skip("netstat/tasklist parsing is Windows-only")
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(("127.0.0.1", 0))
    s.listen(1)
    port = s.getsockname()[1]
    try:
        owner = server.describe_port_owner(port)
    finally:
        s.close()
    assert owner is not None
    assert f"PID {os.getpid()}" in owner
```

- [ ] **Step 2: Run to verify they fail**

Run: `.venv\Scripts\python.exe -m pytest tests/test_play_server.py -q -k "port"`
Expected: FAIL with `AttributeError: module ... has no attribute 'port_in_use'` (and the serve test either raises `OSError` or, on Windows, hangs in `serve_forever`; if it hangs, Ctrl+C is not available to a subagent, so run the two helper tests first with `-k "probe or owner"`, implement, then run the serve test).

- [ ] **Step 3: Implement**

In `src/mm_mcp/play/server.py` add imports `csv`, `socket`, `subprocess` next to the existing stdlib imports, then add above `serve()`:

```python
def port_in_use(port: int, host: str = "127.0.0.1") -> bool:
    """True when something accepts TCP connections on host:port. A connect
    probe, not a bind attempt: HTTPServer sets SO_REUSEADDR, and on Windows
    that lets a second bind to a LISTENING port succeed silently, which is
    how a stale mm-play kept answering the browser while a new one believed
    it had started fine."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
        probe.settimeout(0.5)
        return probe.connect_ex((host, port)) == 0


def describe_port_owner(port: int) -> str | None:
    """Windows only: 'PID <n> (<image name>)' for the process LISTENING on
    127.0.0.1:<port>, from `netstat -ano` + `tasklist`. None off-Windows, or
    when either command fails or the port is not found."""
    if os.name != "nt":
        return None
    try:
        out = subprocess.run(["netstat", "-ano", "-p", "tcp"], capture_output=True,
                             text=True, timeout=10, check=False).stdout
    except (OSError, subprocess.SubprocessError):
        return None
    pid = None
    for line in out.splitlines():
        parts = line.split()
        if (len(parts) >= 5 and parts[0].upper() == "TCP"
                and parts[1].endswith(f":{port}") and parts[3].upper() == "LISTENING"):
            pid = parts[4]
            break
    if not pid:
        return None
    name = None
    try:
        out = subprocess.run(["tasklist", "/FI", f"PID eq {pid}", "/FO", "CSV", "/NH"],
                             capture_output=True, text=True, timeout=10, check=False).stdout
        first = next((ln for ln in out.splitlines() if ln.strip().startswith('"')), "")
        row = next(csv.reader([first])) if first else []
        if len(row) >= 2 and row[1] == pid:
            name = row[0]
    except (OSError, subprocess.SubprocessError, StopIteration):
        pass
    return f"PID {pid}" + (f" ({name})" if name else "")


class _StrictThreadingHTTPServer(ThreadingHTTPServer):
    # Backstop for the probe above: never bind beside an existing listener.
    allow_reuse_address = False
```

Then change `serve()`:

```python
def serve(cfg=None, open_browser=False):
    cfg = cfg or load_config()
    try:
        require_valid(cfg)
    except FileNotFoundError as exc:
        print(f"Cannot start Material Maker Play: {exc}")
        return None
    if port_in_use(cfg.play_port):
        owner = describe_port_owner(cfg.play_port)
        who = f" by {owner}" if owner else ""
        print(f"Cannot start Material Maker Play: port {cfg.play_port} is already in use{who}.")
        print("  Most likely a stale mm-play from an earlier session is still running.")
        if owner and owner.startswith("PID "):
            pid = owner.split()[1]
            print(f"  Stop it:   Stop-Process -Id {pid}")
        print("  Or use another port: set MM_PLAY_PORT in .env and relaunch.")
        return None
    catalog = build_catalog(cfg.nodes_dir)
    outdir = os.path.join(cfg.output_dir, "play")
    os.makedirs(outdir, exist_ok=True)
    handler = make_handler(cfg, catalog, outdir, STATIC_DIR)
    try:
        httpd = _StrictThreadingHTTPServer(("127.0.0.1", cfg.play_port), handler)
    except OSError as exc:
        print(f"Cannot start Material Maker Play: could not bind port {cfg.play_port} ({exc}).")
        print("  Set MM_PLAY_PORT in .env to use another port.")
        return None
    url = f"http://127.0.0.1:{cfg.play_port}/"
    print(f"Material Maker Play running at {url}  (Ctrl+C to stop)")
    if open_browser:
        webbrowser.open(url)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        httpd.shutdown()
    return None
```

- [ ] **Step 4: Run the tests**

Run: `.venv\Scripts\python.exe -m pytest tests/test_play_server.py -q`
Expected: all pass, including the 3 new tests (the pre-existing `running_server` fixture is unaffected because it constructs `HTTPServer` directly, not via `serve()`).

- [ ] **Step 5: Manual sanity (optional, no browser needed)**

In one PowerShell: `.venv\Scripts\python.exe -m mm_mcp.play.server` (leave running). In a second: the same command. Expected second output names port 8788, the first process's PID and `python.exe`, and the `Stop-Process` line. Ctrl+C the first.

- [ ] **Step 6: Commit**

```
git add src/mm_mcp/play/server.py tests/test_play_server.py
git commit -m "fix(play): refuse to start beside a stale listener, name the PID holding the port

HTTPServer's SO_REUSEADDR lets a second bind succeed on Windows while a
stale mm-play still owns the port, so requests kept hitting old code with
no error (the 2026-09-04 false 'GPU dead' blocker). Probe with a plain
connect first, report the owner via netstat/tasklist, and bind strictly."
```

---

### Task 7: Merge and push

**Files:** none new.

- [ ] **Step 1: Full verification on the branch**

Run: `.venv\Scripts\python.exe -m pytest -q -m "not integration"`
Expected: all pass (618 + 3 from Task 6 = 621).

Run: `.venv\Scripts\python.exe quality\promote_cookbook.py --check`
Expected: in sync.

Run: `.venv\Scripts\python.exe -m mm_mcp.doctor --check` (or `mm-mcp --check`)
Expected: the cookbook line reports 53 materials.

Run: `git status --short`
Expected: clean.

- [ ] **Step 2: Merge to main and push**

```
git checkout main
git merge --no-ff fold-examples-into-cookbook -m "merge: fold examples/ into the cookbook + mm-play port diagnostic (teardown #3 items 1 and 4)"
git push origin main
git branch -d fold-examples-into-cookbook
```

- [ ] **Step 3: Confirm CI**

Run: `gh run list --limit 1`
Expected: a `tests` run on `main` for the merge commit; wait for it and confirm `completed success`. If it fails, read the log (`gh run view --log-failed`) before touching anything: the likeliest cause is the CI clone of Material Maker lacking a node type a hero graph uses, which would mean the catalog fixture needs the same fix the existing 46 already pass through.

---

## Self-review notes

- Spec coverage: examples/ folded (Tasks 2-4), README repointed and counts enforced (Task 5), contact sheet regenerated with alt text fixed (Task 5), `examples/` copied then removed (Task 5), cookbook gate floor raised (Task 5), port diagnostic with PID (Task 6), merge/push (Task 7). The teardown's "baton diet" and `.env.example` items are deliberately NOT in this plan (separate item 2).
- No re-render of whole labels anywhere; the only Godot runs are the 7 paired `verify_hero_fold.py` checks.
- Type consistency: `take_variant(builder, label, keep_n)` is used with the same signature in Tasks 2-4; `group_into_subgraph` argument order `(g, members, name, label, exposed, catalog)` matches `author_helpers.py`; `list_cookbook` entries expose `.name`/`.category` as used in Task 5.
- Risk flagged inline: `group_into_subgraph` with an empty `exposed` list (Task 4, m02 leftover group) has a stated fallback.

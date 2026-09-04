# Cookbook Subgraph Retrofit Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Group the nodes in all 46 existing cookbook materials into Material Maker's
native subgraph mechanism (`type: "graph"` nodes with a curated, named set of exposed
parameters) so opening any cookbook `.ptex` shows a handful of friendly nodes instead of a
wall of raw ones, with the underlying recipe and rendered output unchanged.

**Architecture:** One new pure-JSON graph-surgery primitive, `group_into_subgraph`, added
to `quality/author_helpers.py` alongside the existing `rewire`/`retype`/`drop_conn`/
`add_node` family. Ten follow-on tasks, one per cookbook category, call it from each
category's `quality/cookbook_<category>.py` builder and re-promote through the existing
`promote_cookbook.py` pipeline. A new tolerance-based render comparison utility
(`quality/render_compare.py`) backs the regression gate, since Godot's render is already
known to be non-deterministic run to run.

**Tech Stack:** Python 3.13, pure-stdlib JSON graph manipulation (no Godot dependency in
the primitive itself), pytest, the project's existing `pngread.py` PNG decoder (no Pillow).

**Spec:** [docs/superpowers/specs/2026-09-04-cookbook-subgraph-retrofit-design.md](../specs/2026-09-04-cookbook-subgraph-retrofit-design.md)

## Global Constraints

- This is an organizational change only. A retrofitted material must render the same as it
  does today; only the top-level graph's shape changes.
- No new MCP tool, no live-control change, no new runtime dependency (Pillow stays out).
- Edit builders (`quality/cookbook_<category>.py`), never a tracked `.ptex` by hand.
- `group_into_subgraph` is pure JSON surgery: no Godot, no MCP server, testable in
  isolation.
- Run `pytest -q -m "not integration"` (the fast suite) after every task and confirm it is
  green before committing.

---

## Task 1: `group_into_subgraph` primitive + render comparison utility

**Files:**
- Modify: `quality/author_helpers.py` (add `group_into_subgraph`)
- Create: `quality/render_compare.py`
- Test: `tests/test_author_helpers.py` (add test cases)
- Test: `tests/test_render_compare.py` (new)

**Interfaces:**
- Produces: `group_into_subgraph(graph: dict, member_names: list[str], name: str,
  label: str, exposed: list[tuple[str, str, str, str]], catalog: dict) -> None`. Mutates
  `graph` in place: removes the named member nodes and any connections fully between them
  or crossing their boundary, and appends one new `type: "graph"` node named `name` in
  their place. `exposed` entries are `(internal_node_name, internal_param_name, slot_id,
  friendly_label)`.
- Produces: `quality/render_compare.py`'s `renders_match(path_a: str, path_b: str,
  tolerance: float = 3.0, n: int = 16) -> bool` and `grid_mean_abs_diff(path_a: str,
  path_b: str, n: int = 16) -> float`. Later tasks (2-12) import these to verify a
  retrofitted material renders the same as before.

- [ ] **Step 1: Write the failing tests for `group_into_subgraph`**

Add to `tests/test_author_helpers.py`. The file already imports `node` from
`author_helpers` at the top (`from author_helpers import rewire, drop_conn, node,
add_node`); extend that same import line to also bring in `group_into_subgraph` rather
than adding a second import line:

```python
from author_helpers import rewire, drop_conn, node, add_node, group_into_subgraph  # noqa: E402

_FAKE_CATALOG = {
    "perlin": {"inputs": [], "outputs": [{"type": "f"}], "parameters": []},
    "colorize": {
        "inputs": [{"name": "in", "type": "f", "desc": ""}],
        "outputs": [{"type": "rgba"}], "parameters": [],
    },
    "material": {
        "inputs": [{"name": "albedo", "type": "rgb", "desc": ""}],
        "outputs": [], "parameters": [],
    },
}


def _simple_graph():
    return {
        "nodes": [
            {"name": "perlin_0", "type": "perlin",
             "node_position": {"x": 0, "y": 0},
             "parameters": {"scale": 4}},
            {"name": "colorize_0", "type": "colorize",
             "node_position": {"x": 200, "y": 0},
             "parameters": {"amount": 1}},
            {"name": "Material", "type": "material",
             "node_position": {"x": 400, "y": 0},
             "parameters": {}},
        ],
        "connections": [
            {"from": "perlin_0", "from_port": 0, "to": "colorize_0", "to_port": 0},
            {"from": "colorize_0", "from_port": 0, "to": "Material", "to_port": 0},
        ],
    }


def test_group_into_subgraph_collapses_named_nodes():
    g = _simple_graph()
    group_into_subgraph(
        g, ["perlin_0"], "base_noise", "Base Noise",
        [("perlin_0", "scale", "param0", "Scale")], _FAKE_CATALOG,
    )
    names = {n["name"] for n in g["nodes"]}
    assert "perlin_0" not in names
    assert "base_noise" in names
    assert "colorize_0" in names and "Material" in names


def test_group_into_subgraph_new_node_is_type_graph_with_exposed_param():
    g = _simple_graph()
    group_into_subgraph(
        g, ["perlin_0"], "base_noise", "Base Noise",
        [("perlin_0", "scale", "param0", "Scale")], _FAKE_CATALOG,
    )
    collapsed = node(g, "base_noise")
    assert collapsed["type"] == "graph"
    assert collapsed["label"] == "Base Noise"
    assert collapsed["parameters"]["param0"] == 4
    remote = next(n for n in collapsed["nodes"] if n["type"] == "remote")
    widget = remote["widgets"][0]
    assert widget["name"] == "param0"
    assert widget["shortdesc"] == "Scale"
    assert widget["linked_widgets"] == [{"node": "perlin_0", "widget": "scale"}]


def test_group_into_subgraph_preserves_outer_wiring():
    g = _simple_graph()
    group_into_subgraph(
        g, ["perlin_0"], "base_noise", "Base Noise",
        [("perlin_0", "scale", "param0", "Scale")], _FAKE_CATALOG,
    )
    # perlin_0 -> colorize_0 becomes base_noise -> colorize_0
    outer = [c for c in g["connections"] if c["to"] == "colorize_0"]
    assert outer == [{"from": "base_noise", "from_port": 0,
                       "to": "colorize_0", "to_port": 0}]
    # colorize_0 -> Material is untouched (neither endpoint was grouped)
    untouched = [c for c in g["connections"] if c["to"] == "Material"]
    assert untouched == [{"from": "colorize_0", "from_port": 0,
                           "to": "Material", "to_port": 0}]


def test_group_into_subgraph_handles_incoming_and_outgoing_boundary():
    g = _simple_graph()
    group_into_subgraph(
        g, ["colorize_0"], "recolor", "Recolor", [], _FAKE_CATALOG,
    )
    collapsed = node(g, "recolor")
    gen_inputs = next(n for n in collapsed["nodes"] if n["name"] == "gen_inputs")
    gen_outputs = next(n for n in collapsed["nodes"] if n["name"] == "gen_outputs")
    assert len(gen_inputs["ports"]) == 1
    assert gen_inputs["ports"][0]["type"] == "f"       # perlin_0's output type
    assert len(gen_outputs["ports"]) == 1
    assert gen_outputs["ports"][0]["type"] == "rgba"   # colorize_0's output type
    # parent-level connections now point at "recolor" instead of "colorize_0"
    assert {"from": "perlin_0", "from_port": 0,
            "to": "recolor", "to_port": 0} in g["connections"]
    assert {"from": "recolor", "from_port": 0,
            "to": "Material", "to_port": 0} in g["connections"]
    # the internal connection is rehomed onto gen_inputs/gen_outputs
    inner = collapsed["connections"]
    assert {"from": "gen_inputs", "from_port": 0,
            "to": "colorize_0", "to_port": 0} in inner
    assert {"from": "colorize_0", "from_port": 0,
            "to": "gen_outputs", "to_port": 0} in inner
```

- [ ] **Step 2: Run the tests to verify they fail**

Run (from the repo root): `.venv\Scripts\python.exe -m pytest tests/test_author_helpers.py -k group_into_subgraph -v`
Expected: FAIL with `ImportError: cannot import name 'group_into_subgraph'`

- [ ] **Step 3: Implement `group_into_subgraph`**

Add to `quality/author_helpers.py`:

```python
def _boundary_port_type(catalog: dict, node_type: str, port: int, *, is_input: bool) -> str:
    entry = catalog.get(node_type, {})
    ports = entry.get("inputs" if is_input else "outputs", [])
    if port < len(ports):
        return ports[port].get("type") or "f"
    return "f"


def group_into_subgraph(graph: dict, member_names: list, name: str, label: str,
                         exposed: list, catalog: dict) -> None:
    """Collapse `member_names` (and the connections between them) into one
    node of type "graph", replacing them in `graph` in place. `exposed` is a
    list of (internal_node_name, internal_param_name, slot_id, friendly_label)
    tuples; each becomes one widget on the collapsed node's Parameters remote."""
    member_set = set(member_names)
    all_conns = graph["connections"]
    internal = [c for c in all_conns
                if c["from"] in member_set and c["to"] in member_set]
    incoming = [c for c in all_conns
                if c["to"] in member_set and c["from"] not in member_set]
    outgoing = [c for c in all_conns
                if c["from"] in member_set and c["to"] not in member_set]
    untouched = [c for c in all_conns
                 if c["from"] not in member_set and c["to"] not in member_set]
    member_nodes = [n for n in graph["nodes"] if n["name"] in member_set]

    inner_conns = list(internal)
    gen_inputs_ports, outer_incoming = [], []
    for i, c in enumerate(incoming):
        target = node(graph, c["to"])
        port_type = _boundary_port_type(catalog, target["type"], c["to_port"], is_input=True)
        gen_inputs_ports.append({"name": f"in{i}", "type": port_type, "group_size": 0})
        inner_conns.append({"from": "gen_inputs", "from_port": i,
                             "to": c["to"], "to_port": c["to_port"]})
        outer_incoming.append({"from": c["from"], "from_port": c["from_port"],
                                "to": name, "to_port": i})

    gen_outputs_ports, outer_outgoing = [], []
    for o, c in enumerate(outgoing):
        source = node(graph, c["from"])
        port_type = _boundary_port_type(catalog, source["type"], c["from_port"], is_input=False)
        gen_outputs_ports.append({"name": f"out{o}", "type": port_type, "group_size": 0})
        inner_conns.append({"from": c["from"], "from_port": c["from_port"],
                             "to": "gen_outputs", "to_port": o})
        outer_outgoing.append({"from": name, "from_port": o,
                                "to": c["to"], "to_port": c["to_port"]})

    widgets, params = [], {}
    for internal_node_name, internal_param_name, slot_id, friendly_label in exposed:
        inode = node(graph, internal_node_name)
        params[slot_id] = inode.get("parameters", {}).get(internal_param_name)
        widgets.append({
            "name": slot_id, "shortdesc": friendly_label, "label": "",
            "type": "linked_control",
            "linked_widgets": [{"node": internal_node_name, "widget": internal_param_name}],
        })

    xs = [n["node_position"]["x"] for n in member_nodes] or [0]
    ys = [n["node_position"]["y"] for n in member_nodes] or [0]
    centroid = {"x": sum(xs) / len(xs), "y": sum(ys) / len(ys)}

    collapsed = {
        "name": name, "label": label, "type": "graph",
        "node_position": centroid, "parameters": dict(params), "seed_int": 0,
        "nodes": [
            {"name": "gen_inputs", "type": "ios",
             "node_position": {"x": centroid["x"] - 400, "y": centroid["y"]},
             "parameters": {}, "ports": gen_inputs_ports, "seed": 0, "seed_locked": True},
            {"name": "gen_outputs", "type": "ios",
             "node_position": {"x": centroid["x"] + 400, "y": centroid["y"]},
             "parameters": {}, "ports": gen_outputs_ports, "seed": 0},
            {"name": "gen_parameters", "type": "remote",
             "node_position": {"x": centroid["x"] - 400, "y": centroid["y"] + 200},
             "parameters": dict(params), "seed": 0, "widgets": widgets},
            *member_nodes,
        ],
        "connections": inner_conns,
    }

    graph["nodes"] = [n for n in graph["nodes"] if n["name"] not in member_set] + [collapsed]
    graph["connections"] = untouched + outer_incoming + outer_outgoing
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `.venv\Scripts\python.exe -m pytest tests/test_author_helpers.py -k group_into_subgraph -v`
Expected: PASS (4 tests)

- [ ] **Step 5: Write the failing test for the render comparison utility**

Create `tests/test_render_compare.py`. Cookbook thumbnails live under
`docs/images/cookbook-<category>/<name>.png` (not next to the `.ptex` files, confirmed by
reading `tests/test_cookbook_gate.py`'s own `test_cookbook_graph_has_thumbnail`). Use two
already-committed thumbnails: the same file against itself for the "matches" case, and two
thumbnails from different categories for the "does not match" case:

```python
import os
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(_ROOT, "quality"))
from render_compare import grid_mean_abs_diff, renders_match

_GLASS_THUMB = os.path.join(_ROOT, "docs", "images", "cookbook-glass",
                             "gl01_frosted_glass.png")
_WOOD_THUMB = os.path.join(_ROOT, "docs", "images", "cookbook-wood",
                            "w03_painted_wood_siding.png")


def test_identical_file_matches_itself():
    assert renders_match(_GLASS_THUMB, _GLASS_THUMB)
    assert grid_mean_abs_diff(_GLASS_THUMB, _GLASS_THUMB) == 0.0


def test_different_materials_do_not_match():
    assert not renders_match(_GLASS_THUMB, _WOOD_THUMB, tolerance=3.0)
```

- [ ] **Step 6: Run the test to verify it fails**

Run: `.venv\Scripts\python.exe -m pytest tests/test_render_compare.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'render_compare'`

- [ ] **Step 7: Implement `quality/render_compare.py`**

```python
"""Tolerance-based render comparison for the subgraph retrofit's regression
gate. Godot's headless render is not perfectly deterministic run to run (see
the render-orphan-contention history in this project's memory/HANDOFF), so
the gate is a small mean-absolute-difference tolerance, not byte-identity.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from pngread import Sampler

# Empirically, unrelated re-renders of an unchanged graph differ by a mean
# per-channel delta well under 1.0 (out of 255). A real content change
# (a different pattern or color) produces a mean delta well above this.
TOLERANCE = 3.0


def grid_mean_abs_diff(path_a: str, path_b: str, n: int = 16) -> float:
    sa, sb = Sampler.load(path_a), Sampler.load(path_b)
    samples_a, samples_b = sa.grid(n), sb.grid(n)
    total = sum(abs(ca - cb)
                for pa, pb in zip(samples_a, samples_b)
                for ca, cb in zip(pa, pb))
    return total / (len(samples_a) * 3)


def renders_match(path_a: str, path_b: str, tolerance: float = TOLERANCE,
                   n: int = 16) -> bool:
    return grid_mean_abs_diff(path_a, path_b, n) <= tolerance
```

- [ ] **Step 8: Run the test to verify it passes**

Run: `.venv\Scripts\python.exe -m pytest tests/test_render_compare.py tests/test_author_helpers.py -v`
Expected: PASS

- [ ] **Step 9: Run the full fast suite**

Run: `.venv\Scripts\python.exe -m pytest -q -m "not integration"`
Expected: PASS, count up from the current baseline (453)

- [ ] **Step 10: Commit**

```bash
git add quality/author_helpers.py quality/render_compare.py tests/test_author_helpers.py tests/test_render_compare.py
git commit -m "feat(quality): add group_into_subgraph and a tolerance-based render comparison utility"
```

---

## Task 2: Pilot retrofit — glass (1 material)

Use this task as the proof that the whole process (grouping, re-promotion, tolerance
check) works end to end before fanning out to the other nine categories. Do not skip the
manual render comparison step even though it is the smallest category.

**Files:**
- Modify: `quality/cookbook_glass.py`
- Modify: `cookbook/glass/gl01_frosted_glass.ptex`, `cookbook/glass/gl01_frosted_glass.md`
  (regenerated via `promote_cookbook.py`, not hand-edited)
- Modify: `docs/AUTHORING.md` (do this once, here, so later category tasks don't each try
  to add the same section — see Step 6)

**Interfaces:**
- Consumes: `group_into_subgraph(graph, member_names, name, label, exposed, catalog)` from
  Task 1. Load `catalog` the same way `promote_cookbook.py`/the test suite already does:
  `from mm_mcp.catalog_builder import build_catalog; from mm_mcp.config import
  load_config; catalog = build_catalog(load_config().nodes_dir)`.
- Consumes: `renders_match(path_a, path_b)` from `quality/render_compare.py` (Task 1).

- [ ] **Step 1: Render and save the current (pre-retrofit) output as a baseline**

```bash
cd quality
python render_cookbook.py cookbook-glass
```

This writes `quality/cookbook/cookbook-glass/gl01_frosted_glass/gl01_frosted_glass_albedo.png`.
Copy it to a temp path outside the repo (e.g. `%TEMP%\gl01_before_albedo.png`) so it
survives the re-render in Step 4.

- [ ] **Step 2: Decide the grouping**

Read `quality/cookbook_glass.py`'s `build_gl01_frosted_glass`. It builds a `dry_earth`-derived
graph: a voronoi-driven crack pattern feeding two colorize layers (base color, crack
color) blended together, plus a normal map and a flat-roughness constant. Group it into 2
to 3 subgraphs that map to what a viewer would actually think about, for example:

- `"base_color"`: the voronoi and its albedo colorize node, exposing the crack scale and
  base color's key gradient stop as friendly params (e.g. `"Facet size"`, `"Base color"`).
- `"surface_detail"`: the crack-color colorize, the blend, and the roughness constant,
  exposing roughness as a friendly param (e.g. `"Roughness"`).

Use your own judgment on the exact split. The bar: opening the retrofitted `.ptex` should
show noticeably fewer top-level nodes than today (`dry_earth`-derived graphs run to
roughly 8 to 10 raw nodes), each with a plain-language label, with 1 to 3 exposed
parameters per group.

- [ ] **Step 3: Implement the grouping in the builder**

At the end of `build_gl01_frosted_glass`, before `return save_variant(...)`, add the
`group_into_subgraph` calls implementing the decision from Step 2. Import
`group_into_subgraph` and the catalog loader at the top of `quality/cookbook_glass.py`
alongside the existing `author_helpers` import.

- [ ] **Step 4: Rebuild and re-render, confirming validation passes**

```bash
cd quality
python cookbook_glass.py
python render_cookbook.py cookbook-glass
```

`render_cookbook.py` runs `validate_graph` internally and prints `ERROR:` lines for any
problem before skipping the render; confirm the console output for `gl01_frosted_glass`
shows no `ERROR:` lines and ends with `ok: gl01_frosted_glass_albedo.png` (and the other
three maps).

- [ ] **Step 5: Compare the new render against the baseline**

Output lands at
`quality/cookbook/cookbook-glass/gl01_frosted_glass/gl01_frosted_glass_albedo.png`.
Compare it against the Step 1 baseline:

```python
import sys
sys.path.insert(0, "quality")
from render_compare import renders_match, grid_mean_abs_diff

before = r"%TEMP%\gl01_before_albedo.png"  # the path you saved in Step 1
after = "quality/cookbook/cookbook-glass/gl01_frosted_glass/gl01_frosted_glass_albedo.png"
print(grid_mean_abs_diff(before, after))
assert renders_match(before, after)
```

Expected: `renders_match` returns `True`. If it returns `False`, the retrofit changed the
recipe, not just its organization. Diff the before/after `.ptex` node parameters and fix
the grouping so no parameter value changed, then re-render and re-check.

- [ ] **Step 6: Add the new lever to `docs/AUTHORING.md`**

Add a new subsection (near the other structural levers, not the color/pattern levers)
titled "Grouping into subgraphs" describing: what a subgraph is (Material Maker's native
`Ctrl+G` mechanism), why the cookbook uses it (opening a graph shows fewer, friendlier
nodes), and a one-paragraph pointer at `group_into_subgraph` in `author_helpers.py` with
its signature, so a future session adding a new cookbook material knows to use it from the
start rather than needing a later retrofit.

- [ ] **Step 7: Promote and update the recipe card**

```bash
cd quality
python promote_cookbook.py cookbook-glass
python _make_previews.py cookbook-glass
```

Check `git status` afterward. If any file outside `cookbook/glass/` changed (the known
whole-label-regen gotcha), diff it; if the change is only render noise on an unrelated
category (there is only one material in `glass`, so this should not happen here, but
verify), revert it.

Update `cookbook/glass/gl01_frosted_glass.md`'s recipe card with a short note on the new
subgraph structure (what the 2-3 named groups are), following the card's existing format.

- [ ] **Step 8: Run the full fast suite**

Run: `.venv\Scripts\python.exe -m pytest -q -m "not integration"`
Expected: PASS

- [ ] **Step 9: Commit**

```bash
git add quality/cookbook_glass.py cookbook/glass/ docs/AUTHORING.md
git commit -m "feat(cookbook): retrofit glass category with subgraph grouping"
```

---

## Task 3: Retrofit plastics (1 material)

Same process as Task 2, applied to `quality/cookbook_plastics.py` /
`cookbook/plastics/p01_glossy_plastic`. Skip Step 6 (the `AUTHORING.md` addition), already
done in Task 2.

- [ ] Render and save the current output as a baseline (Task 2 Step 1 pattern)
- [ ] Decide a 2 to 3 subgraph grouping for `build_p01_glossy_plastic` (a from-scratch
      noise material: perlin, colorize, normal_map, a flat-roughness constant, Material).
      A reasonable split: `"surface_color"` (perlin + colorize, exposing color/scale) and
      `"surface_finish"` (normal_map + roughness constant, exposing roughness/relief
      strength).
- [ ] Implement the grouping in `quality/cookbook_plastics.py` (Task 2 Step 3 pattern)
- [ ] Validate against the catalog (Task 2 Step 4 pattern)
- [ ] Re-render and confirm `renders_match` against the baseline (Task 2 Step 5 pattern)
- [ ] Promote, regenerate the thumbnail, update the recipe card, check `git status` for
      unrelated changes (Task 2 Step 7 pattern)
- [ ] Run the full fast suite: `.venv\Scripts\python.exe -m pytest -q -m "not integration"`
- [ ] Commit:

```bash
git add quality/cookbook_plastics.py cookbook/plastics/
git commit -m "feat(cookbook): retrofit plastics category with subgraph grouping"
```

---

## Task 4: Retrofit wood (3 materials)

Same process as Task 2 (skip the `AUTHORING.md` step), applied to
`quality/cookbook_wood.py` and all `build_*` functions in it (`w03_painted_wood_siding`,
`w04_driftwood_gray`, `w05_dark_walnut` per `cookbook/wood/*.ptex`; there is no `w01`/`w02`
on disk, retrofit exactly the three ids that exist). Render, decide a grouping, implement,
validate, re-render, compare
against a saved baseline, and promote **one material at a time** rather than all three at
once, so a `renders_match` failure on one material doesn't block confirming the other two
are fine.

- [ ] For each of the 3 materials: render baseline, decide grouping, implement, validate
      against the catalog, re-render, confirm `renders_match`
- [ ] Promote the whole category once all 3 are retrofitted and confirmed:
      `python promote_cookbook.py cookbook-wood`, `python _make_previews.py cookbook-wood`
- [ ] Check `git status`; revert any thumbnail change for a material you did not touch in
      this task (there should be none, since this task touches the whole category, but
      verify no other category's files were swept in)
- [ ] Update each retrofitted material's recipe card with its subgraph structure
- [ ] Run the full fast suite: `.venv\Scripts\python.exe -m pytest -q -m "not integration"`
- [ ] Commit:

```bash
git add quality/cookbook_wood.py cookbook/wood/
git commit -m "feat(cookbook): retrofit wood category with subgraph grouping"
```

---

## Task 5: Retrofit organics (4 materials)

Same process as Task 4, applied to `quality/cookbook_organics.py` and its 4 `build_*`
functions (`o03_tree_bark`, `o04_snake_scales`, `o05_coral`, `o06_lichen_crusted_rock` per
`cookbook/organics/*.ptex`; there is no `o01`/`o02` on disk).

- [ ] For each of the 4 materials: render baseline, decide grouping, implement, validate,
      re-render, confirm `renders_match`
- [ ] Promote the category, regenerate thumbnails, check `git status` for unrelated sweep-in
- [ ] Update each recipe card
- [ ] Run the full fast suite
- [ ] Commit:

```bash
git add quality/cookbook_organics.py cookbook/organics/
git commit -m "feat(cookbook): retrofit organics category with subgraph grouping"
```

---

## Task 6: Retrofit sci-fi (4 materials)

Same process, applied to `quality/cookbook_scifi.py` and its 4 `build_*` functions
(`sf01_hull_plating`, `sf02_hazard_stripe_panel`, `sf03_circuit_board`,
`sf04_vent_grille_panel` per `cookbook/scifi/*.ptex`). This category includes `sf03`, the
circuit-board
material with the previously-fixed blend-opacity gotcha (memorialized in
`docs/AUTHORING.md` and the `blend_opacity_ramp` debug swatch); when grouping its nodes,
keep the `blend` node's mask input wired exactly as-is, do not fold the mask-producing
colorize into the same subgraph as the blend without verifying `renders_match` carefully,
since this is the one material in the cookbook with documented history of a subtle
opacity-masking bug.

- [ ] For each of the 4 materials: render baseline, decide grouping, implement, validate,
      re-render, confirm `renders_match` (extra scrutiny on `sf03`)
- [ ] Promote the category, regenerate thumbnails, check `git status` for unrelated sweep-in
- [ ] Update each recipe card
- [ ] Run the full fast suite
- [ ] Commit:

```bash
git add quality/cookbook_scifi.py cookbook/scifi/
git commit -m "feat(cookbook): retrofit sci-fi category with subgraph grouping"
```

---

## Task 7: Retrofit painted-metal (5 materials)

Same process, applied to `quality/cookbook_painted_metal.py` and its 5 `build_*` functions
(`pm01_powder_coat`, `pm02_automotive_enamel`, `pm03_chipped_paint`, `pm04_hammertone`,
`pm05_scuffed_panel` per `cookbook/painted-metal/*.ptex`). Per this project's documented
lesson,
a `blend` node shows port-1 where its port-2 mask is 0 and port-0 where it's 1: when a
subgraph groups a `blend` together with only one of its two content inputs, double-check
`renders_match` since collapsing the wrong side of a blend's boundary is an easy way to
accidentally change which layer is "on top."

- [ ] For each of the 5 materials: render baseline, decide grouping, implement, validate,
      re-render, confirm `renders_match`
- [ ] Promote the category, regenerate thumbnails, check `git status` for unrelated sweep-in
- [ ] Update each recipe card
- [ ] Run the full fast suite
- [ ] Commit:

```bash
git add quality/cookbook_painted_metal.py cookbook/painted-metal/
git commit -m "feat(cookbook): retrofit painted-metal category with subgraph grouping"
```

---

## Task 8: Retrofit fabrics (6 materials)

Same process, applied to `quality/cookbook_fabrics.py` and its 6 `build_*` functions
(`f03_canvas_burlap`, `f04_wool_knit`, `f05_silk_satin`, `f06_velvet`,
`f07_herringbone_tweed`, `f08_donegal_tweed` per `cookbook/fabrics/*.ptex`; there is no
`f01`/`f02` on disk). `f08`
(Donegal tweed) uses a separate voronoi-fleck node composited via `blend`; keep the
fleck-mask voronoi and the base weave in separate subgraphs so the exposed "fleck density"
parameter stays meaningfully tunable on its own.

- [ ] For each material present in `cookbook/fabrics/`: render baseline, decide grouping,
      implement, validate, re-render, confirm `renders_match`
- [ ] Promote the category, regenerate thumbnails, check `git status` for unrelated sweep-in
- [ ] Update each recipe card
- [ ] Run the full fast suite
- [ ] Commit:

```bash
git add quality/cookbook_fabrics.py cookbook/fabrics/
git commit -m "feat(cookbook): retrofit fabrics category with subgraph grouping"
```

---

## Task 9: Retrofit leather (6 materials)

Same process, applied to `quality/cookbook_leather.py` and its 6 `build_*` functions
(`l01_black_oiled_leather`, `l02_distressed_two_tone`, `l03_suede`, `l04_reptile_exotic`,
`l05_quilted_leather`, `l06_topstitched_leather` per `cookbook/leather/*.ptex`).

- [ ] For each material present in `cookbook/leather/`: render baseline, decide grouping,
      implement, validate, re-render, confirm `renders_match`
- [ ] Promote the category, regenerate thumbnails, check `git status` for unrelated sweep-in
- [ ] Update each recipe card
- [ ] Run the full fast suite
- [ ] Commit:

```bash
git add quality/cookbook_leather.py cookbook/leather/
git commit -m "feat(cookbook): retrofit leather category with subgraph grouping"
```

---

## Task 10: Retrofit stone (8 materials)

Same process, applied to `quality/cookbook_stone.py` and its 8 `build_*` functions
(`s04_scattered_river_stones`, `s05_hex_stone_tile`, `s06_river_pebbles`,
`s07_cobblestone`, `s08_dry_stone_wall`, `s09_ashlar_wall`, `s10_flagstone`, `s11_marble`
per `cookbook/stone/*.ptex`; there is no `s01`-`s03` on disk). This is the masonry-heavy
category; several of these clone the `dry_earth` voronoi-plate family
where `warp_0.amount` is a deliberately tuned, sensitive parameter (documented as cutting
both ways depending on the material). Keep `warp_0` in the same subgraph as whatever it
directly feeds, do not expose it as a friendly parameter unless you re-verify the render
matches, since it is the single most render-sensitive parameter in this category.

- [ ] For each material present in `cookbook/stone/`: render baseline, decide grouping,
      implement, validate, re-render, confirm `renders_match`
- [ ] Promote the category, regenerate thumbnails, check `git status` for unrelated sweep-in
- [ ] Update each recipe card
- [ ] Run the full fast suite
- [ ] Commit:

```bash
git add quality/cookbook_stone.py cookbook/stone/
git commit -m "feat(cookbook): retrofit stone category with subgraph grouping"
```

---

## Task 11: Retrofit terrain (8 materials)

Same process, applied to `quality/cookbook_terrain.py` and its 8 `build_*` functions
(`t01_sand_dunes`, `t02_fresh_snow`, `t03_gravel`, `t04_grass_field`, `t05_cracked_ice`,
`t06_cooled_lava`, `t07_forest_floor`, `t08_riverbed_pebbles` per
`cookbook/terrain/*.ptex`). The lava material (`t06`) emission glow is wired from `warp_0`'s crack signal through
a `colorize` into the Material node's emission port; keep that whole chain (`warp_0` through
the emission `colorize`) inside one subgraph rather than splitting it, since it is a single
conceptual "glow" effect a viewer should be able to reason about as one unit.

- [ ] For each material present in `cookbook/terrain/`: render baseline, decide grouping,
      implement, validate, re-render, confirm `renders_match`
- [ ] Promote the category, regenerate thumbnails, check `git status` for unrelated sweep-in
- [ ] Update each recipe card
- [ ] Run the full fast suite
- [ ] Commit:

```bash
git add quality/cookbook_terrain.py cookbook/terrain/
git commit -m "feat(cookbook): retrofit terrain category with subgraph grouping"
```

---

## Task 12: Final gate test, docs polish, and whole-branch verification

**Files:**
- Create: `tests/test_cookbook_subgraph_gate.py`
- Modify: `quality/README.md`

**Interfaces:**
- Consumes: `mm_mcp.cookbook.list_cookbook(cookbook_dir)`, the same enumeration helper
  `tests/test_cookbook_gate.py` already uses, returning entries with `.name`, `.category`,
  `.path`.

- [ ] **Step 1: Write the failing gate test**

Add `tests/test_cookbook_subgraph_gate.py`, matching `tests/test_cookbook_gate.py`'s own
setup pattern exactly:

```python
import json
import os

import pytest
from mm_mcp.cookbook import list_cookbook

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
COOKBOOK_DIR = os.path.join(_ROOT, "cookbook")
ENTRIES = list_cookbook(COOKBOOK_DIR)


@pytest.mark.parametrize("entry", ENTRIES, ids=[e.name for e in ENTRIES])
def test_cookbook_material_uses_at_least_one_subgraph(entry):
    with open(entry.path, encoding="utf-8") as fh:
        graph = json.load(fh)
    top_level_types = {n["type"] for n in graph["nodes"]}
    assert "graph" in top_level_types, (
        f"{entry.name} has no top-level subgraph node; "
        "expected at least one from the subgraph retrofit"
    )
```

- [ ] **Step 2: Run it to verify it fails for any not-yet-retrofitted material**

Run: `.venv\Scripts\python.exe -m pytest tests/test_cookbook_subgraph_gate.py -v`
Expected: PASS for every material, since Tasks 2 through 11 already retrofitted all 46.
If anything fails here, go back and retrofit whatever category was missed before
continuing.

- [ ] **Step 3: Update `quality/README.md`'s cookbook-growth section**

Add one line noting that a new cookbook material should call `group_into_subgraph` before
`save_variant` returns, pointing at the "Grouping into subgraphs" section of
`docs/AUTHORING.md` added in Task 2, so future categories don't need a second retrofit
pass.

- [ ] **Step 4: Run the full fast suite one more time**

Run: `.venv\Scripts\python.exe -m pytest -q -m "not integration"`
Expected: PASS, full count up from the Task 1 baseline (one new gate test per material,
46 more than before Task 1)

- [ ] **Step 5: Commit**

```bash
git add tests/test_cookbook_subgraph_gate.py quality/README.md
git commit -m "test(cookbook): add subgraph-presence gate across the whole cookbook"
```

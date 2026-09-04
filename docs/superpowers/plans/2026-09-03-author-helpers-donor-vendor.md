# author.py Split + Donor Vendoring Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Split `quality/author.py`'s pure graph-surgery helpers into their own module, then vendor the 9 donor `.ptex` graphs the authoring pipeline actually depends on so it no longer needs the external Material Maker checkout to run.

**Architecture:** Task 1-2 are a pure code move (helpers out of `author.py` into a new `author_helpers.py`, 9 consumer files repointed to the new module) with zero behavior change. Task 3-4 add a new tracked `quality/donors/` directory holding the 9 `.ptex` files the pipeline actually reads, and repoint `load_example()` at it instead of the external checkout. Every other consumer of the external checkout (`list_examples(source="material_maker")`, the setup doctor, the Phase 1 gate test, the render/preview smoke tests) is explicitly untouched.

**Tech Stack:** Python 3.13, pytest. No new dependencies.

**Spec:** [docs/superpowers/specs/2026-09-03-vendor-donor-examples-design.md](../specs/2026-09-03-vendor-donor-examples-design.md)

## Global Constraints

- No behavior change to any `build_*` function's output. Every task that touches shared code must leave generated `.ptex` output byte/JSON-identical to before the task.
- `config.py`, `doctor.py`, `server.py`'s `list_examples`/`load_example` MCP tools, `tests/test_examples_gate.py`, `tests/test_render.py`, `tests/test_preview.py`, and `tests/test_config.py` are out of scope. Do not modify them.
- No recipe cards, no `promote_cookbook.py`-style `--check` tool for the vendored donors. They are static vendored copies, not authored cookbook content.
- Run tests with `.venv\Scripts\python.exe` (or an activated venv). Fast suite: `pytest -q -m "not integration"`.
- This is a Windows-only project. Shell examples in this plan use PowerShell (`;` to sequence, no `&&`).

---

## Task 1: Extract graph-surgery helpers into `quality/author_helpers.py`

**Files:**
- Create: `quality/author_helpers.py`
- Modify: `quality/author.py`
- Modify: `tests/test_author_helpers.py`

**Interfaces:**
- Produces: `quality/author_helpers.py` exposing `load_example(name: str) -> dict`, `node(graph: dict, name: str) -> dict`, `set_gradient(graph: dict, node_name: str, colors: list) -> None`, `set_param(graph: dict, node_name: str, key: str, value) -> None`, `save_variant(graph: dict, iter_label: str, case_id: str, n: int) -> str`, `rewire(graph: dict, to_node: str, to_port: int, from_node: str, from_port: int) -> None`, `drop_conn(graph: dict, to_node: str, to_port: int) -> None`, `add_node(graph: dict, name: str, ntype: str, params: dict) -> None`, `retype(graph: dict, node_name: str, new_type: str, params: dict) -> None`, `_grad(points) -> dict`, `_from_scratch_noise_material(perlin_params, albedo_points, *, metallic=0.0, roughness=0.5, normal_amount=0.3) -> dict`. Same signatures as today; this task only moves them, it does not change any of them.
- Consumes: nothing new. `quality/author.py`'s existing `build_*` functions consume the helpers above by name, unchanged.

- [ ] **Step 1: Point the existing helper test at the not-yet-created module**

Edit `tests/test_author_helpers.py`. Change line 15 from:

```python
from author import rewire, drop_conn, node, add_node  # noqa: E402
```

to:

```python
from author_helpers import rewire, drop_conn, node, add_node  # noqa: E402
```

Also update the module docstring's first line (currently `"""Unit tests for quality/author.py's graph-surgery helpers (rewire, drop_conn).`) to read `"""Unit tests for quality/author_helpers.py's graph-surgery helpers (rewire, drop_conn).` so the docstring names the file it actually tests. Leave the rest of the docstring and every test function body unchanged.

- [ ] **Step 2: Run the test to verify it fails**

Run: `.venv\Scripts\python.exe -m pytest tests/test_author_helpers.py -v`
Expected: FAIL/ERROR, `ModuleNotFoundError: No module named 'author_helpers'` (the module doesn't exist yet).

- [ ] **Step 3: Create `quality/author_helpers.py` with the moved helpers**

Create `quality/author_helpers.py` with this exact content:

```python
"""Pure graph-surgery helpers for Phase 3 authoring and cookbook growth.

Everything here is pure graph-JSON surgery against the catalog vocabulary; no
Godot. Split out of quality/author.py (2026-09-03) so the ~10 helpers below
have one home shared by author.py's own Phase 3 builders and every
quality/cookbook_<category>.py / debug_swatches.py / noise_gallery.py
consumer, instead of living inside author.py alongside Phase-3-specific
material builders that only author.py itself uses.
"""
import copy
import json
import os
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT / "src"))
from mm_mcp.config import load_config

_CFG = load_config()
_EX = Path(_CFG.examples_dir)


def load_example(name: str) -> dict:
    with open(_EX / f"{name}.ptex", encoding="utf-8") as fh:
        return json.load(fh)


def node(graph: dict, name: str) -> dict:
    for n in graph["nodes"]:
        if n["name"] == name:
            return n
    raise KeyError(f"node {name!r} not in graph")


def set_gradient(graph: dict, node_name: str, colors: list) -> None:
    """Replace a colorize node's gradient points.

    colors: list of (pos, r, g, b) with 0..1 floats. Alpha forced to 1.
    """
    pts = [{"a": 1, "r": r, "g": g, "b": b, "pos": pos}
           for (pos, r, g, b) in colors]
    node(graph, node_name)["parameters"]["gradient"] = {
        "interpolation": 1, "points": pts, "type": "Gradient",
    }


def set_param(graph: dict, node_name: str, key: str, value) -> None:
    node(graph, node_name).setdefault("parameters", {})[key] = value


def save_variant(graph: dict, iter_label: str, case_id: str, n: int) -> str:
    out = _ROOT / "quality" / "authored" / iter_label / case_id
    out.mkdir(parents=True, exist_ok=True)
    path = out / f"v{n}.ptex"
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(graph, fh, indent=1)
    return str(path)


def _grad(points):
    return {"interpolation": 1, "type": "Gradient",
            "points": [{"a": 1, "r": r, "g": g, "b": b, "pos": p}
                       for (p, r, g, b) in points]}


def _from_scratch_noise_material(perlin_params, albedo_points, *,
                                 metallic=0.0, roughness=0.5, normal_amount=0.3):
    """A minimal, valid noise->colorize->material graph:
    perlin -> colorize(albedo) -> Material.albedo, perlin -> normal_map ->
    Material.normal (so the normal isn't flat), with scalar metallic/roughness.
    Node skeletons match the shapes Godot's loader expects (verified vs
    rusted_metal / wooden_floor)."""
    nodes = [
        {"name": "perlin_0", "type": "perlin",
         "node_position": {"x": 0, "y": 0}, "parameters": dict(perlin_params)},
        {"name": "colorize_0", "type": "colorize",
         "node_position": {"x": 300, "y": -60},
         "parameters": {"gradient": _grad(albedo_points)}},
        # normal_map is a COMPOUND node: its real params are param0 (buffer
        # size 2^n), param1 (STRENGTH, default 1 — this is what drives relief),
        # param2, param4. Earlier stray keys (amount/size/param3) were ignored,
        # and param1=0.2 rendered a near-flat normal. Map relief -> param1.
        {"name": "normal_map_0", "type": "normal_map",
         "node_position": {"x": 300, "y": 160},
         "parameters": {"param0": 10, "param1": normal_amount,
                        "param2": 0, "param4": 1}},
        {"name": "Material", "type": "material",
         "node_position": {"x": 620, "y": 40},
         "export_paths": {},
         "parameters": {
             "albedo_color": {"a": 1, "r": 1, "g": 1, "b": 1, "type": "Color"},
             "ao": 1, "depth_scale": 1, "emission_energy": 1,
             "metallic": metallic, "normal": 1, "roughness": roughness,
             "size": 11, "sss": 0}},
    ]
    connections = [
        {"from": "perlin_0", "from_port": 0, "to": "colorize_0", "to_port": 0},
        {"from": "perlin_0", "from_port": 0, "to": "normal_map_0", "to_port": 0},
        {"from": "colorize_0", "from_port": 0, "to": "Material", "to_port": 0},
        {"from": "normal_map_0", "from_port": 0, "to": "Material", "to_port": 4},
    ]
    return {"connections": connections, "nodes": nodes}


def rewire(graph: dict, to_node: str, to_port: int, from_node: str,
           from_port: int) -> None:
    """Repoint the connection feeding (to_node, to_port) to a new source."""
    for c in graph["connections"]:
        if c["to"] == to_node and c["to_port"] == to_port:
            c["from"] = from_node
            c["from_port"] = from_port
            return
    graph["connections"].append(
        {"from": from_node, "from_port": from_port,
         "to": to_node, "to_port": to_port})


def drop_conn(graph: dict, to_node: str, to_port: int) -> None:
    """Remove the connection feeding (to_node, to_port), if any."""
    graph["connections"] = [
        c for c in graph["connections"]
        if not (c["to"] == to_node and c["to_port"] == to_port)]


def retype(graph: dict, node_name: str, new_type: str, params: dict) -> None:
    """Swap a node's type and replace its parameters. Connections that
    reference it keep working as long as the new type's output port 0 is
    compatible with what the old one fed."""
    nd = node(graph, node_name)
    nd["type"] = new_type
    nd["parameters"] = dict(params)


def add_node(graph: dict, name: str, ntype: str, params: dict) -> None:
    graph["nodes"].append({"name": name, "type": ntype,
                           "node_position": {"x": 0, "y": 0},
                           "parameters": dict(params)})
```

Note: `copy` is imported but unused by the helpers moved here (it was unused in the original `author.py` too — several `build_*` functions do `g = load_example(...)` per variant instead of deep-copying a shared graph). Keep the import as-is; removing unused imports is not part of this task's scope.

- [ ] **Step 4: Trim `quality/author.py` down to builders + registry + CLI**

Edit `quality/author.py`. Replace lines 1-59 (the module docstring through the `# ---- iteration 1 builders ----` comment) with the block below. The blank line and `def build_f02_brown_leather(iter_label: str) -> list[str]:` that originally followed at lines 60-61 are left in place after this replacement, unchanged:

```python
"""Phase 3C authoring case builders: transform bundled example graphs toward
a prompt.

Each build_* function codifies the kind of remixing a live authoring session
does (recolor a ramp, swap a generator, blend two layers) so each variant is
reproducible and auditable. The graph-surgery primitives these builders call
(load_example, node, set_gradient, rewire, ...) live in author_helpers.py,
shared with quality/cookbook_<category>.py and friends. Author variants land
under quality/authored/<iter>/<case>/vN.ptex.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from author_helpers import (
    load_example, node, set_gradient, set_param, save_variant,
    rewire, drop_conn, add_node, retype,
)


# ---- iteration 1 builders -------------------------------------------------
```

Then, in the same file, delete the now-duplicated `_grad` function definition (originally at lines 193-196, right before `_from_scratch_noise_material`) and the `_from_scratch_noise_material` function definition (originally lines 199-235) — both now live only in `author_helpers.py`. Delete the `rewire` function definition (originally lines 238-248, right after `_from_scratch_noise_material`). Delete the `drop_conn` function definition (originally lines 333-337, between `build_o01_mossy_forest_floor` and `build_m02_brushed_aluminum`). Delete the `retype` function definition (originally lines 453-459, between `build_man02_ceramic_hex_tiles` and `build_f01_woven_denim`). Delete the `add_node` function definition (originally lines 493-496, between `build_f01_woven_denim` and `build_combo01_rusted_painted_steel`).

Every `build_*` function body, the `BUILDERS` dict, and `main()`/`if __name__ == "__main__":` stay exactly as they were — only the module header and the 6 relocated helper definitions are removed. When done, `quality/author.py` should contain (in order): the new header shown above, `build_f02_brown_leather`, `build_w02_barn_wood`, `build_m01_weathered_copper`, `build_s03_cracked_concrete`, `build_w01_oak_planks`, `build_s02_gray_granite`, `build_o01_mossy_forest_floor`, `build_m02_brushed_aluminum`, `build_man01_metal_grating`, `build_man02_ceramic_hex_tiles`, `build_f01_woven_denim`, `build_combo01_rusted_painted_steel`, `BUILDERS`, `main()`, `if __name__ == "__main__":`.

- [ ] **Step 5: Run the test to verify it passes**

Run: `.venv\Scripts\python.exe -m pytest tests/test_author_helpers.py -v`
Expected: PASS, all 10 tests green.

- [ ] **Step 6: Verify the full builder output is byte-identical to before this task**

Run, from the repo root:

```powershell
.venv\Scripts\python.exe quality\author.py iter1-verify
```

Expected: exits 0, prints 12 lines (one per `BUILDERS` entry) each showing `<case>: 2 variants` (2 variants for every case except this doesn't apply here — check the actual counts match what `main()` prints; every entry in `BUILDERS` produces the count its own `build_*` function returns). Then diff the new `quality/authored/iter1-verify/` tree's `.ptex` contents against the existing `quality/authored/iter1/` tree (from a prior run) for the same case ids — every file must be byte-identical. If `quality/authored/iter1/` isn't present locally (it's gitignored), instead run `python quality\author.py iter1-verify` twice in a row and confirm the two runs produce identical output; this proves the refactor changed nothing about generation, independent of whether an old baseline exists on disk. Delete the `quality/authored/iter1-verify/` scratch output afterward (gitignored, safe to remove).

- [ ] **Step 7: Run the fast suite**

Run: `.venv\Scripts\python.exe -m pytest -q -m "not integration"`
Expected: PASS, same count as before this task (424, per the last recorded fast-suite count in STATUS.md) plus no new failures.

- [ ] **Step 8: Commit**

```bash
git add quality/author.py quality/author_helpers.py tests/test_author_helpers.py
git commit -m "refactor(quality): extract graph-surgery helpers into author_helpers.py"
```

---

## Task 2: Repoint the 9 cookbook/gallery/swatch scripts at `author_helpers`

**Files:**
- Modify: `quality/cookbook_fabrics.py`
- Modify: `quality/cookbook_stone.py`
- Modify: `quality/cookbook_scifi.py`
- Modify: `quality/cookbook_painted_metal.py`
- Modify: `quality/cookbook_organics.py`
- Modify: `quality/cookbook_leather.py`
- Modify: `quality/cookbook_wood.py`
- Modify: `quality/cookbook_terrain.py`
- Modify: `quality/debug_swatches.py`
- Modify: `quality/noise_gallery.py`

**Interfaces:**
- Consumes: `author_helpers.py`'s exports from Task 1 (unchanged signatures).
- Produces: nothing new for later tasks; this task only repoints existing imports.

- [ ] **Step 1: Change each file's import line from `author` to `author_helpers`**

Each file already does `sys.path.insert(0, os.path.dirname(__file__))` (or the equivalent, pointing at the `quality/` directory) before its `from author import ...` line — that insert is unchanged, since `author_helpers.py` lives in the same `quality/` directory. Only the module name in the `from ... import ...` line changes. Apply these exact edits (current line → new line):

`quality/cookbook_fabrics.py`:
```
from author import load_example, node, set_gradient, set_param, retype, rewire, add_node, save_variant
```
→
```
from author_helpers import load_example, node, set_gradient, set_param, retype, rewire, add_node, save_variant
```

`quality/cookbook_stone.py`:
```
from author import load_example, set_gradient, set_param, save_variant, add_node, rewire, _grad
```
→
```
from author_helpers import load_example, set_gradient, set_param, save_variant, add_node, rewire, _grad
```

`quality/cookbook_scifi.py`:
```
from author import load_example, node, set_gradient, set_param, add_node, rewire, save_variant
```
→
```
from author_helpers import load_example, node, set_gradient, set_param, add_node, rewire, save_variant
```

`quality/cookbook_painted_metal.py` (lines 36-37, multi-line import — only the module name on the first line changes, the continuation line is untouched):
```
from author import (load_example, set_gradient, set_param, save_variant,
                    add_node, rewire, drop_conn, node, _grad)
```
→
```
from author_helpers import (load_example, set_gradient, set_param, save_variant,
                    add_node, rewire, drop_conn, node, _grad)
```

`quality/cookbook_organics.py` (lines 14-15):
```
from author import (load_example, node, set_gradient, set_param, retype,
                     rewire, drop_conn, add_node, save_variant)
```
→
```
from author_helpers import (load_example, node, set_gradient, set_param, retype,
                     rewire, drop_conn, add_node, save_variant)
```

`quality/cookbook_leather.py` (lines 26-27):
```
from author import (load_example, node, set_gradient, set_param, retype,
                    rewire, add_node, save_variant, _grad)
```
→
```
from author_helpers import (load_example, node, set_gradient, set_param, retype,
                    rewire, add_node, save_variant, _grad)
```

`quality/cookbook_wood.py`:
```
from author import load_example, set_gradient, set_param, add_node, rewire, save_variant, _grad
```
→
```
from author_helpers import load_example, set_gradient, set_param, add_node, rewire, save_variant, _grad
```

`quality/cookbook_terrain.py` (lines 14-15):
```
from author import (load_example, node, set_gradient, set_param, retype,
                     rewire, drop_conn, add_node, save_variant, _grad)
```
→
```
from author_helpers import (load_example, node, set_gradient, set_param, retype,
                     rewire, drop_conn, add_node, save_variant, _grad)
```

`quality/debug_swatches.py`:
```
from author import _grad, save_variant
```
→
```
from author_helpers import _grad, save_variant
```

`quality/noise_gallery.py`:
```
from author import _grad, save_variant
```
→
```
from author_helpers import _grad, save_variant
```

- [ ] **Step 2: Verify every file still imports cleanly**

Run each of the following and confirm none raises `ImportError`/`ModuleNotFoundError` (exit code 0, no traceback):

```powershell
.venv\Scripts\python.exe -c "import sys; sys.path.insert(0, 'quality'); import cookbook_fabrics"
.venv\Scripts\python.exe -c "import sys; sys.path.insert(0, 'quality'); import cookbook_stone"
.venv\Scripts\python.exe -c "import sys; sys.path.insert(0, 'quality'); import cookbook_scifi"
.venv\Scripts\python.exe -c "import sys; sys.path.insert(0, 'quality'); import cookbook_painted_metal"
.venv\Scripts\python.exe -c "import sys; sys.path.insert(0, 'quality'); import cookbook_organics"
.venv\Scripts\python.exe -c "import sys; sys.path.insert(0, 'quality'); import cookbook_leather"
.venv\Scripts\python.exe -c "import sys; sys.path.insert(0, 'quality'); import cookbook_wood"
.venv\Scripts\python.exe -c "import sys; sys.path.insert(0, 'quality'); import cookbook_terrain"
.venv\Scripts\python.exe -c "import sys; sys.path.insert(0, 'quality'); import debug_swatches"
.venv\Scripts\python.exe -c "import sys; sys.path.insert(0, 'quality'); import noise_gallery"
```

- [ ] **Step 3: Run each builder script for real and confirm clean output**

Each of the 8 `cookbook_*.py` files defines its own `build_*` function(s) and is meant to be run directly (per `quality/README.md`'s "Cookbook growth" section). Run each and confirm exit 0 with no traceback:

```powershell
.venv\Scripts\python.exe quality\cookbook_fabrics.py
.venv\Scripts\python.exe quality\cookbook_stone.py
.venv\Scripts\python.exe quality\cookbook_scifi.py
.venv\Scripts\python.exe quality\cookbook_painted_metal.py
.venv\Scripts\python.exe quality\cookbook_organics.py
.venv\Scripts\python.exe quality\cookbook_leather.py
.venv\Scripts\python.exe quality\cookbook_wood.py
.venv\Scripts\python.exe quality\cookbook_terrain.py
```

This writes into gitignored `quality/authored/cookbook-<category>/`, same as any normal cookbook-growth run — it does not touch the tracked `cookbook/` tree (that only happens via `promote_cookbook.py`, not part of this task). `debug_swatches.py` and `noise_gallery.py` are not run here since they drive real Godot renders (out of scope for this quick import-smoke check); their import already passed in Step 2, which is what this task's import-repointing actually risks breaking.

- [ ] **Step 4: Run the fast suite**

Run: `.venv\Scripts\python.exe -m pytest -q -m "not integration"`
Expected: PASS, no new failures.

- [ ] **Step 5: Commit**

```bash
git add quality/cookbook_fabrics.py quality/cookbook_stone.py quality/cookbook_scifi.py quality/cookbook_painted_metal.py quality/cookbook_organics.py quality/cookbook_leather.py quality/cookbook_wood.py quality/cookbook_terrain.py quality/debug_swatches.py quality/noise_gallery.py
git commit -m "refactor(quality): repoint cookbook/gallery/swatch scripts at author_helpers"
```

---

## Task 3: Vendor the 9 load-bearing donor examples into `quality/donors/`

**Files:**
- Create: `quality/donors/beehive.ptex`
- Create: `quality/donors/crocodile_skin.ptex`
- Create: `quality/donors/dry_earth.ptex`
- Create: `quality/donors/metal_pattern_2.ptex`
- Create: `quality/donors/rock.ptex`
- Create: `quality/donors/rusted_metal.ptex`
- Create: `quality/donors/stone_wall.ptex`
- Create: `quality/donors/wood.ptex`
- Create: `quality/donors/wooden_floor.ptex`
- Create: `quality/donors/README.md`
- Test: `tests/test_donors.py`

**Interfaces:**
- Consumes: nothing from earlier tasks.
- Produces: 9 tracked `.ptex` files under `quality/donors/` that Task 4's `load_example()` change will read from. `tests/test_donors.py` is the regression check that they stay present and valid.

- [ ] **Step 1: Write the failing test**

Create `tests/test_donors.py`:

```python
"""Vendored donor examples: the 9 Material Maker bundled graphs the Phase 3
authoring pipeline actually reads via author_helpers.load_example(). Vendored
2026-09-03 so the pipeline doesn't depend on the external Material Maker
checkout (cfg.examples_dir) being present. Mirrors tests/test_examples_gate.py
and tests/test_cookbook_gate.py, scoped to this tracked 9-file set instead of
the live external checkout's 43."""
import json
import os
import pytest
from mm_mcp.catalog_builder import build_catalog
from mm_mcp.config import load_config
from mm_mcp.validator import validate_graph

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DONORS_DIR = os.path.join(_ROOT, "quality", "donors")
DONOR_NAMES = [
    "beehive", "crocodile_skin", "dry_earth", "metal_pattern_2", "rock",
    "rusted_metal", "stone_wall", "wood", "wooden_floor",
]
cfg = load_config()
CATALOG = build_catalog(cfg.nodes_dir)


def _all_graphs(node):
    """Yield the node itself and every nested subgraph (has a 'nodes' list)."""
    if isinstance(node, dict) and "nodes" in node:
        yield node
        for child in node["nodes"]:
            yield from _all_graphs(child)


def test_all_nine_donor_files_are_present():
    missing = [n for n in DONOR_NAMES
               if not os.path.isfile(os.path.join(DONORS_DIR, f"{n}.ptex"))]
    assert missing == [], f"missing donor files: {missing}"


@pytest.mark.parametrize("name", DONOR_NAMES)
def test_donor_file_is_valid_json_graph(name):
    path = os.path.join(DONORS_DIR, f"{name}.ptex")
    with open(path, encoding="utf-8") as fh:
        graph = json.load(fh)
    assert "nodes" in graph
    assert "connections" in graph


@pytest.mark.parametrize("name", DONOR_NAMES)
def test_donor_graph_has_no_type_or_connection_errors(name):
    path = os.path.join(DONORS_DIR, f"{name}.ptex")
    with open(path, encoding="utf-8") as fh:
        root = json.load(fh)
    hard_errors = []
    for g in _all_graphs(root):
        for p in validate_graph(g, CATALOG):
            if p["severity"] == "error":
                hard_errors.append(p["message"])
    assert hard_errors == [], f"{name}: {hard_errors}"
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `.venv\Scripts\python.exe -m pytest tests/test_donors.py -v`
Expected: FAIL, `test_all_nine_donor_files_are_present` fails listing all 9 names missing (the parametrized tests will also error/fail since `quality/donors/` doesn't exist yet).

- [ ] **Step 3: Copy the 9 donor files from the external checkout**

Run (adjust the source path if your `MM_PROJECT_PATH` differs from `.env`'s value):

```powershell
New-Item -ItemType Directory -Force -Path "quality\donors" | Out-Null
$src = "C:\Projects-local\z-Git\material-maker\material_maker\examples"
$names = @("beehive", "crocodile_skin", "dry_earth", "metal_pattern_2", "rock", "rusted_metal", "stone_wall", "wood", "wooden_floor")
foreach ($n in $names) {
    Copy-Item -Path "$src\$n.ptex" -Destination "quality\donors\$n.ptex"
}
Get-ChildItem quality\donors\*.ptex | Measure-Object | Select-Object -ExpandProperty Count
```

Expected: prints `9`.

- [ ] **Step 4: Add the provenance README**

Create `quality/donors/README.md`:

```markdown
# quality/donors/

Vendored copies of 9 Material Maker bundled example graphs, copied
byte-for-byte from `<MM_PROJECT_PATH>/material_maker/examples/*.ptex`
(the external Material Maker checkout, not part of this repo).

These are upstream Material Maker content, not first-party recipes. They
have no recipe cards and are not part of `cookbook/`. They exist because
`quality/author.py`'s Phase 3 case builders and `quality/cookbook_<category>.py`
use them as starting graphs (`author_helpers.load_example(name)`), and
vendoring them removes the authoring pipeline's dependency on the external
checkout being present at a specific path.

Files: `beehive.ptex`, `crocodile_skin.ptex`, `dry_earth.ptex`,
`metal_pattern_2.ptex`, `rock.ptex`, `rusted_metal.ptex`, `stone_wall.ptex`,
`wood.ptex`, `wooden_floor.ptex`.

Browsing Material Maker's full bundled example library (all 43, not just
these 9) is unaffected by this folder: `list_examples(source="material_maker")`
and the Phase 1 gate test (`tests/test_examples_gate.py`) still read live from
the external checkout's `cfg.examples_dir`, unchanged.
```

- [ ] **Step 5: Run the test to verify it passes**

Run: `.venv\Scripts\python.exe -m pytest tests/test_donors.py -v`
Expected: PASS, all tests green (1 presence test + 9 JSON-validity tests + 9 catalog-validation tests = 19 passed).

- [ ] **Step 6: Confirm `quality/donors/` is tracked, not gitignored**

Run: `git status --short quality/donors/`
Expected: lists all 10 new files (9 `.ptex` + `README.md`) as untracked (`??`), not silently absent. If any file is missing from this output, check `.gitignore` for a rule matching `quality/donors/` before proceeding — none is expected (the existing `quality/`-scoped ignore rules are `quality/runs/`, `quality/authored/`, and `quality/cookbook/` only).

- [ ] **Step 7: Commit**

```bash
git add quality/donors/
git commit -m "feat(quality): vendor the 9 load-bearing donor examples"
```

---

## Task 4: Repoint `load_example()` at the vendored donors

**Files:**
- Modify: `quality/author_helpers.py`
- Modify: `tests/test_donors.py`

**Interfaces:**
- Consumes: `quality/donors/*.ptex` and `tests/test_donors.py`'s `DONORS_DIR` constant from Task 3.
- Produces: `load_example(name: str) -> dict` now reads from `quality/donors/` instead of `cfg.examples_dir`. Same signature and return shape as before; every caller (`author.py`'s `build_*` functions, all 8 `cookbook_<category>.py` files) is unaffected by this task.

- [ ] **Step 1: Write a test that pins the new source directory**

Add this test to `tests/test_donors.py`, appended after the existing tests:

```python
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "quality"))


def test_load_example_reads_from_the_vendored_donors_dir():
    import author_helpers
    assert Path(author_helpers._EX) == Path(DONORS_DIR)
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `.venv\Scripts\python.exe -m pytest tests/test_donors.py::test_load_example_reads_from_the_vendored_donors_dir -v`
Expected: FAIL, `author_helpers._EX` still equals `cfg.examples_dir` (the external checkout), not `quality/donors/`.

- [ ] **Step 3: Capture a pre-change baseline**

Before editing `_EX`, run this once (at this point `load_example()` still reads from the external checkout, same as it has all along):

```powershell
.venv\Scripts\python.exe quality\author.py verify-before
```

Expected: exits 0, writes 12 cases under `quality/authored/verify-before/`. Do not delete this output yet, Step 6 diffs against it.

- [ ] **Step 4: Repoint `_EX` in `author_helpers.py`**

Edit `quality/author_helpers.py`. Change:

```python
_CFG = load_config()
_EX = Path(_CFG.examples_dir)
```

to:

```python
_CFG = load_config()
_EX = _ROOT / "quality" / "donors"
```

`_CFG` stays defined and imported exactly as before — nothing else in the file uses `_CFG.examples_dir` (only `_EX` did), and `_CFG` is not otherwise referenced elsewhere in `author_helpers.py`, so leaving the `load_config()` call in place is intentional here: `_ROOT` was already computed from `Path(__file__)`, matching the style used for `save_variant`'s output path (`_ROOT / "quality" / "authored" / ...`) two lines below.

- [ ] **Step 5: Run the test to verify it passes**

Run: `.venv\Scripts\python.exe -m pytest tests/test_donors.py -v`
Expected: PASS, all 20 tests green (the 19 from Task 3 plus this new one).

- [ ] **Step 6: Diff the post-change output against the Step 3 baseline**

Run:

```powershell
.venv\Scripts\python.exe quality\author.py verify-after
```

Expected: exits 0, writes the same 12 cases under `quality/authored/verify-after/`. Then confirm every file is byte-identical to its Step 3 counterpart:

```powershell
$cases = Get-ChildItem quality\authored\verify-before | Select-Object -ExpandProperty Name
$diffs = 0
foreach ($case in $cases) {
    Get-ChildItem "quality\authored\verify-before\$case" -Filter "v*.ptex" | ForEach-Object {
        $before = $_.FullName
        $after = "quality\authored\verify-after\$case\$($_.Name)"
        if ((Get-FileHash $before).Hash -ne (Get-FileHash $after).Hash) {
            Write-Host "DIFF: $case\$($_.Name)"
            $diffs++
        }
    }
}
Write-Host "total diffs: $diffs"
```

Expected: `total diffs: 0`. This proves the source switch changed *where* graphs load from, not *what* loads, exactly as the spec requires. Delete `quality/authored/verify-before/` and `quality/authored/verify-after/` afterward (gitignored scratch output).

Also run each of the 8 `cookbook_<category>.py` scripts once more (same command list as Task 2 Step 3) and confirm exit 0 with no traceback, now reading donors from the vendored copy instead of the external checkout.

- [ ] **Step 7: Run the full fast suite**

Run: `.venv\Scripts\python.exe -m pytest -q -m "not integration"`
Expected: PASS, no new failures. Note the new total test count (was 424 before this plan; Task 3-4 add 20 new tests in `tests/test_donors.py`).

- [ ] **Step 8: Commit**

```bash
git add quality/author_helpers.py tests/test_donors.py
git commit -m "refactor(quality): read donor examples from quality/donors/, not the external checkout"
```

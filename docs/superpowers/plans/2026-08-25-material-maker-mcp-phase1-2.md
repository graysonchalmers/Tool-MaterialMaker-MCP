# Material Maker MCP (Phases 1-2) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the node catalog and the batch-render MCP server so Claude can author a Material Maker graph, validate it, render it headlessly, and save the editable `.ptex`.

**Architecture:** Four isolated Python units. `catalog_builder` turns the ~392 `.mmg` node definitions into a machine-readable `catalog.json`. `graph` builds and validates `.ptex` JSON against that catalog. `render` wraps Godot's `--export-material` CLI. `server` exposes them as MCP tools. Logic lives in the first three modules; `server.py` is thin wiring so it needs almost no tests of its own.

**Tech Stack:** Python 3.13, `mcp` (FastMCP) SDK, `python-dotenv`, `pytest`. Godot 4.7.1 console binary drives rendering. No changes to the Material Maker Godot source in these phases.

**Spec:** `docs/superpowers/specs/2026-08-25-material-maker-mcp-design.md`

## Global Constraints

- Python interpreter: `C:\Program Files\Python313\python.exe` (Python 3.13).
- Shell is PowerShell 5.1: sequence with `;`, use `Push-Location`/`Pop-Location`, invoke quoted exes with `& "..."`. `&&` is a parse error.
- Godot binary (from `.env` `MM_GODOT_BINARY`): `C:\Users\Grayson\AppData\Local\Godot\Godot_v4.7.1-stable_win64.exe`. The runner MUST prefer the sibling `_console.exe` for output capture.
- Material Maker project (from `.env` `MM_PROJECT_PATH`): `C:\Projects-local\z-Git\material-maker`. Treat as read-only; never modify it.
- Render command shape (VERIFIED): `<console_exe> --path <MM_PROJECT> --export-material <file.ptex> -t "Godot/Godot 4 Standard" -o <outdir> --size <n>`. Never use `--export` (engine-reserved), never pass `parse_args.tscn`, never use `--headless`.
- A node's authorable `type` string equals its `.mmg` filename stem (e.g. `blend.mmg` -> `"blend"`).
- Connection port indices are positions in the node's `shader_model.inputs` / `.outputs` arrays.
- Special built-in types with NO `.mmg` file, which the validator must accept without strict port/param checks: `graph`, `comment`, `remote`, `shader`, `buffer`, `image`, `switch`, `debug`.
- All file I/O uses `encoding="utf-8"`.
- Never print the contents of `.env`.

---

## Task 1: Python environment, deps, and config module

**Files:**
- Create: `pyproject.toml`
- Create: `requirements.txt`
- Create: `src/mm_mcp/config.py`
- Create: `tests/__init__.py` (empty)
- Create: `tests/test_config.py`
- Create: `.env` (local only, gitignored — copy of `.env.example`)

**Interfaces:**
- Produces: `mm_mcp.config.load_config() -> Config`; `Config` is a dataclass with `godot_binary: str`, `console_binary: str`, `project_path: str`, `output_dir: str`, `nodes_dir: str`, `examples_dir: str`. `console_binary` is `godot_binary` with `.exe` swapped to `_console.exe` when that file exists, else equal to `godot_binary`.

- [ ] **Step 1: Create the venv and install deps**

Run:
```
Push-Location C:\Projects-local\Tool-MaterialMaker-MCP; & "C:\Program Files\Python313\python.exe" -m venv .venv; .\.venv\Scripts\python.exe -m pip install -U pip; Pop-Location
```

Create `requirements.txt`:
```
mcp>=1.2.0
python-dotenv>=1.0.0
pytest>=8.0.0
```

Create `pyproject.toml`:
```toml
[project]
name = "mm-mcp"
version = "0.0.1"
description = "MCP server for authoring and rendering Material Maker graphs"
requires-python = ">=3.13"

[tool.pytest.ini_options]
pythonpath = ["src"]
testpaths = ["tests"]
markers = [
    "integration: tests that launch Godot (slow)",
]
```

Then install:
```
Push-Location C:\Projects-local\Tool-MaterialMaker-MCP; .\.venv\Scripts\python.exe -m pip install -r requirements.txt; Pop-Location
```

- [ ] **Step 2: Create `.env` from the example**

Run:
```
Copy-Item C:\Projects-local\Tool-MaterialMaker-MCP\.env.example C:\Projects-local\Tool-MaterialMaker-MCP\.env
```
(`.env` is gitignored; it holds the machine paths so tests and the runner work.)

- [ ] **Step 3: Write the failing test**

Create `tests/test_config.py`:
```python
import os
from mm_mcp.config import load_config


def test_config_loads_paths():
    cfg = load_config()
    assert cfg.project_path
    assert cfg.nodes_dir.endswith("nodes")
    assert cfg.examples_dir.endswith("examples")


def test_console_binary_resolves(tmp_path):
    gui = tmp_path / "Godot_win64.exe"
    gui.write_text("x")
    console = tmp_path / "Godot_win64_console.exe"
    console.write_text("x")
    cfg = load_config(overrides={"MM_GODOT_BINARY": str(gui)})
    assert cfg.console_binary == str(console)


def test_console_binary_falls_back_when_absent(tmp_path):
    gui = tmp_path / "OnlyGui.exe"
    gui.write_text("x")
    cfg = load_config(overrides={"MM_GODOT_BINARY": str(gui)})
    assert cfg.console_binary == str(gui)
```

- [ ] **Step 4: Run test to verify it fails**

Run:
```
Push-Location C:\Projects-local\Tool-MaterialMaker-MCP; .\.venv\Scripts\python.exe -m pytest tests/test_config.py -v; Pop-Location
```
Expected: FAIL with `ModuleNotFoundError: No module named 'mm_mcp.config'`.

- [ ] **Step 5: Write minimal implementation**

Create `src/mm_mcp/config.py`:
```python
import os
from dataclasses import dataclass
from dotenv import dotenv_values

_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

_DEFAULTS = {
    "MM_GODOT_BINARY": r"C:\Users\Grayson\AppData\Local\Godot\Godot_v4.7.1-stable_win64.exe",
    "MM_PROJECT_PATH": r"C:\Projects-local\z-Git\material-maker",
    "MM_OUTPUT_DIR": os.path.join(_PROJECT_ROOT, "output"),
}


@dataclass
class Config:
    godot_binary: str
    console_binary: str
    project_path: str
    output_dir: str
    nodes_dir: str
    examples_dir: str


def _resolve_console(godot_binary: str) -> str:
    if godot_binary.lower().endswith(".exe"):
        candidate = godot_binary[:-4] + "_console.exe"
        if os.path.exists(candidate):
            return candidate
    return godot_binary


def load_config(overrides: dict | None = None) -> Config:
    env = dict(_DEFAULTS)
    dotenv_path = os.path.join(_PROJECT_ROOT, ".env")
    env.update({k: v for k, v in dotenv_values(dotenv_path).items() if v})
    env.update({k: v for k, v in os.environ.items() if k.startswith("MM_")})
    if overrides:
        env.update(overrides)
    project_path = env["MM_PROJECT_PATH"]
    return Config(
        godot_binary=env["MM_GODOT_BINARY"],
        console_binary=_resolve_console(env["MM_GODOT_BINARY"]),
        project_path=project_path,
        output_dir=env["MM_OUTPUT_DIR"],
        nodes_dir=os.path.join(project_path, "addons", "material_maker", "nodes"),
        examples_dir=os.path.join(project_path, "material_maker", "examples"),
    )
```

- [ ] **Step 6: Run test to verify it passes**

Run:
```
Push-Location C:\Projects-local\Tool-MaterialMaker-MCP; .\.venv\Scripts\python.exe -m pytest tests/test_config.py -v; Pop-Location
```
Expected: PASS (3 passed).

- [ ] **Step 7: Commit**

```
git add pyproject.toml requirements.txt src/mm_mcp/config.py tests/__init__.py tests/test_config.py
git commit -m "feat: python env, deps, and config module"
```

---

## Task 2: Catalog builder — parse a single node definition

**Files:**
- Create: `src/mm_mcp/catalog_builder.py`
- Create: `tests/test_catalog_parse.py`

**Interfaces:**
- Consumes: nothing from other tasks.
- Produces: `mm_mcp.catalog_builder.parse_node(mmg_path: str) -> dict | None`. Returns `None` when the file has no `shader_model` (not an authorable procedural node). On success returns:
  `{"type": str, "inputs": [{"name","type","desc"}], "outputs": [{"type"}], "parameters": [ParamDef]}` where `ParamDef` is `{"name","type","default","desc"}` plus, for `enum`, `"values": [str]` and `"min":0`, `"max":len-1`; for numeric types, `"min","max","step"` when present.

- [ ] **Step 1: Write the failing test**

Create `tests/test_catalog_parse.py`:
```python
import os
from mm_mcp.catalog_builder import parse_node
from mm_mcp.config import load_config

cfg = load_config()


def _mmg(name):
    return os.path.join(cfg.nodes_dir, name + ".mmg")


def test_parse_blend_inputs_and_ports():
    node = parse_node(_mmg("blend"))
    assert node["type"] == "blend"
    names = [i["name"] for i in node["inputs"]]
    assert names == ["s1", "s2", "a"]  # port order matters
    assert node["outputs"][0]["type"] == "rgba"


def test_parse_blend_enum_param():
    node = parse_node(_mmg("blend"))
    params = {p["name"]: p for p in node["parameters"]}
    bt = params["blend_type"]
    assert bt["type"] == "enum"
    assert len(bt["values"]) == 15
    assert bt["min"] == 0 and bt["max"] == 14
    amount = params["amount"]
    assert amount["type"] == "float"
    assert amount["min"] == 0 and amount["max"] == 1
```

- [ ] **Step 2: Run test to verify it fails**

Run:
```
Push-Location C:\Projects-local\Tool-MaterialMaker-MCP; .\.venv\Scripts\python.exe -m pytest tests/test_catalog_parse.py -v; Pop-Location
```
Expected: FAIL with `ModuleNotFoundError: No module named 'mm_mcp.catalog_builder'`.

- [ ] **Step 3: Write minimal implementation**

Create `src/mm_mcp/catalog_builder.py`:
```python
import json
import os


def _parse_param(p: dict) -> dict:
    out = {
        "name": p.get("name"),
        "type": p.get("type"),
        "default": p.get("default"),
        "desc": p.get("shortdesc") or p.get("longdesc") or "",
    }
    if p.get("type") == "enum":
        values = [v.get("name") for v in p.get("values", [])]
        out["values"] = values
        out["min"] = 0
        out["max"] = max(len(values) - 1, 0)
    else:
        for k in ("min", "max", "step"):
            if k in p:
                out[k] = p[k]
    return out


def parse_node(mmg_path: str) -> dict | None:
    with open(mmg_path, encoding="utf-8") as fh:
        data = json.load(fh)
    sm = data.get("shader_model")
    if not sm:
        return None
    type_name = os.path.splitext(os.path.basename(mmg_path))[0]
    inputs = [
        {"name": i.get("name"), "type": i.get("type"),
         "desc": i.get("shortdesc") or i.get("longdesc") or ""}
        for i in sm.get("inputs", [])
    ]
    outputs = [{"type": o.get("type")} for o in sm.get("outputs", [])]
    parameters = [_parse_param(p) for p in sm.get("parameters", [])]
    return {"type": type_name, "inputs": inputs,
            "outputs": outputs, "parameters": parameters}
```

- [ ] **Step 4: Run test to verify it passes**

Run:
```
Push-Location C:\Projects-local\Tool-MaterialMaker-MCP; .\.venv\Scripts\python.exe -m pytest tests/test_catalog_parse.py -v; Pop-Location
```
Expected: PASS (2 passed).

- [ ] **Step 5: Commit**

```
git add src/mm_mcp/catalog_builder.py tests/test_catalog_parse.py
git commit -m "feat: parse a single .mmg node definition into a catalog entry"
```

---

## Task 3: Catalog builder — full catalog + CLI

**Files:**
- Modify: `src/mm_mcp/catalog_builder.py`
- Create: `tests/test_catalog_build.py`

**Interfaces:**
- Consumes: `parse_node` (Task 2), `load_config` (Task 1).
- Produces:
  - `mm_mcp.catalog_builder.SPECIAL_TYPES: set[str]` = `{"graph","comment","remote","shader","buffer","image","switch","debug"}`.
  - `mm_mcp.catalog_builder.build_catalog(nodes_dir: str) -> dict` mapping `type -> node dict` (from `parse_node`), skipping files that return `None`.
  - `mm_mcp.catalog_builder.write_catalog(nodes_dir: str, out_path: str) -> int` writes JSON, returns entry count.
  - CLI: `python -m mm_mcp.catalog_builder` writes `catalog/catalog.json` using `load_config()`.

- [ ] **Step 1: Write the failing test**

Create `tests/test_catalog_build.py`:
```python
from mm_mcp.catalog_builder import build_catalog, SPECIAL_TYPES
from mm_mcp.config import load_config

cfg = load_config()


def test_catalog_has_core_nodes():
    cat = build_catalog(cfg.nodes_dir)
    assert len(cat) > 300
    for t in ("blend", "colorize", "perlin", "material"):
        assert t in cat


def test_material_node_has_texture_inputs():
    cat = build_catalog(cfg.nodes_dir)
    mat = cat["material"]
    names = [i["name"] for i in mat["inputs"]]
    assert names[0] == "albedo_tex"
    assert "roughness_tex" in names


def test_special_types_present():
    assert "graph" in SPECIAL_TYPES
    assert "comment" in SPECIAL_TYPES
```

- [ ] **Step 2: Run test to verify it fails**

Run:
```
Push-Location C:\Projects-local\Tool-MaterialMaker-MCP; .\.venv\Scripts\python.exe -m pytest tests/test_catalog_build.py -v; Pop-Location
```
Expected: FAIL with `ImportError: cannot import name 'build_catalog'`.

- [ ] **Step 3: Write minimal implementation**

Append to `src/mm_mcp/catalog_builder.py`:
```python
import glob

SPECIAL_TYPES = {"graph", "comment", "remote", "shader",
                 "buffer", "image", "switch", "debug"}


def build_catalog(nodes_dir: str) -> dict:
    catalog = {}
    for path in glob.glob(os.path.join(nodes_dir, "*.mmg")):
        try:
            node = parse_node(path)
        except (ValueError, KeyError):
            node = None
        if node:
            catalog[node["type"]] = node
    return catalog


def write_catalog(nodes_dir: str, out_path: str) -> int:
    catalog = build_catalog(nodes_dir)
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as fh:
        json.dump(catalog, fh, indent=1)
    return len(catalog)


if __name__ == "__main__":
    from mm_mcp.config import load_config
    cfg = load_config()
    out = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
        "catalog", "catalog.json",
    )
    count = write_catalog(cfg.nodes_dir, out)
    print(f"Wrote {count} node types to {out}")
```

- [ ] **Step 4: Run test to verify it passes**

Run:
```
Push-Location C:\Projects-local\Tool-MaterialMaker-MCP; .\.venv\Scripts\python.exe -m pytest tests/test_catalog_build.py -v; Pop-Location
```
Expected: PASS (3 passed).

- [ ] **Step 5: Generate the catalog artifact**

Run:
```
Push-Location C:\Projects-local\Tool-MaterialMaker-MCP; .\.venv\Scripts\python.exe -m mm_mcp.catalog_builder; Pop-Location
```
Expected: prints `Wrote <N> node types` with N > 300. (`catalog/catalog.json` is gitignored; it is a generated artifact, not committed.)

- [ ] **Step 6: Commit**

```
git add src/mm_mcp/catalog_builder.py tests/test_catalog_build.py
git commit -m "feat: build full node catalog + CLI writer"
```

---

## Task 4: Graph model and .ptex serialization

**Files:**
- Create: `src/mm_mcp/graph.py`
- Create: `tests/test_graph.py`

**Interfaces:**
- Consumes: nothing from other tasks (pure data).
- Produces: `mm_mcp.graph.Graph` with:
  - `add_node(name: str, type: str, parameters: dict | None = None, x: float = 0, y: float = 0) -> None`
  - `connect(from_node: str, from_port: int, to_node: str, to_port: int) -> None`
  - `to_ptex() -> dict` returning `{"type":"graph","name":"graph","label":"Graph","node_position":{"x":0,"y":0},"parameters":{},"connections":[...],"nodes":[...]}` where each node is `{"name","type","node_position":{"x","y"},"parameters":{}}` and each connection is `{"from","from_port","to","to_port"}`.
  - `Graph.from_ptex(d: dict) -> Graph` classmethod (reads `nodes` + `connections`).

- [ ] **Step 1: Write the failing test**

Create `tests/test_graph.py`:
```python
from mm_mcp.graph import Graph


def test_build_minimal_graph_to_ptex():
    g = Graph()
    g.add_node("perlin_0", "perlin", {"scale_x": 4, "scale_y": 4}, x=0, y=0)
    g.add_node("colorize_0", "colorize", {}, x=300, y=0)
    g.add_node("Material", "material", {}, x=600, y=0)
    g.connect("perlin_0", 0, "colorize_0", 0)
    g.connect("colorize_0", 0, "Material", 0)
    ptex = g.to_ptex()
    assert ptex["type"] == "graph"
    assert len(ptex["nodes"]) == 3
    assert len(ptex["connections"]) == 2
    names = {n["name"] for n in ptex["nodes"]}
    assert names == {"perlin_0", "colorize_0", "Material"}
    c0 = ptex["connections"][0]
    assert c0 == {"from": "perlin_0", "from_port": 0,
                  "to": "colorize_0", "to_port": 0}


def test_roundtrip_from_ptex():
    g = Graph()
    g.add_node("a", "perlin", {}, 0, 0)
    d = g.to_ptex()
    g2 = Graph.from_ptex(d)
    assert g2.to_ptex()["nodes"][0]["type"] == "perlin"
```

- [ ] **Step 2: Run test to verify it fails**

Run:
```
Push-Location C:\Projects-local\Tool-MaterialMaker-MCP; .\.venv\Scripts\python.exe -m pytest tests/test_graph.py -v; Pop-Location
```
Expected: FAIL with `ModuleNotFoundError: No module named 'mm_mcp.graph'`.

- [ ] **Step 3: Write minimal implementation**

Create `src/mm_mcp/graph.py`:
```python
class Graph:
    def __init__(self):
        self._nodes = []
        self._connections = []

    def add_node(self, name, type, parameters=None, x=0, y=0):
        self._nodes.append({
            "name": name,
            "type": type,
            "node_position": {"x": x, "y": y},
            "parameters": dict(parameters or {}),
        })

    def connect(self, from_node, from_port, to_node, to_port):
        self._connections.append({
            "from": from_node, "from_port": from_port,
            "to": to_node, "to_port": to_port,
        })

    def to_ptex(self):
        return {
            "type": "graph",
            "name": "graph",
            "label": "Graph",
            "node_position": {"x": 0, "y": 0},
            "parameters": {},
            "connections": list(self._connections),
            "nodes": list(self._nodes),
        }

    @classmethod
    def from_ptex(cls, d):
        g = cls()
        for n in d.get("nodes", []):
            pos = n.get("node_position", {"x": 0, "y": 0})
            g.add_node(n["name"], n["type"], n.get("parameters", {}),
                       pos.get("x", 0), pos.get("y", 0))
        for c in d.get("connections", []):
            g.connect(c["from"], c["from_port"], c["to"], c["to_port"])
        return g
```

- [ ] **Step 4: Run test to verify it passes**

Run:
```
Push-Location C:\Projects-local\Tool-MaterialMaker-MCP; .\.venv\Scripts\python.exe -m pytest tests/test_graph.py -v; Pop-Location
```
Expected: PASS (2 passed).

- [ ] **Step 5: Commit**

```
git add src/mm_mcp/graph.py tests/test_graph.py
git commit -m "feat: graph model and .ptex serialization"
```

---

## Task 5: Graph validator

**Files:**
- Create: `src/mm_mcp/validator.py`
- Create: `tests/test_validator.py`

**Interfaces:**
- Consumes: catalog dict (Task 3), `SPECIAL_TYPES` (Task 3), `.ptex` dict (Task 4).
- Produces: `mm_mcp.validator.validate_graph(ptex: dict, catalog: dict) -> list[dict]`. Each problem is `{"severity": "error"|"warning", "where": str, "message": str}`. Rules:
  - error: a node `type` is neither in `catalog` nor `SPECIAL_TYPES`.
  - error: a connection `from`/`to` names a node not present in `nodes`.
  - error: `to_port` >= number of inputs for a catalog-typed target node (skip for `SPECIAL_TYPES`); same for `from_port` vs outputs.
  - error: a parameter name not declared for a catalog-typed node.
  - warning: a numeric parameter value outside `[min, max]`; an enum value outside `[0, max]`.

- [ ] **Step 1: Write the failing test**

Create `tests/test_validator.py`:
```python
from mm_mcp.validator import validate_graph

CATALOG = {
    "perlin": {"type": "perlin", "inputs": [], "outputs": [{"type": "f"}],
               "parameters": [{"name": "scale_x", "type": "float",
                               "min": 1, "max": 32, "default": 4}]},
    "blend": {"type": "blend",
              "inputs": [{"name": "s1"}, {"name": "s2"}, {"name": "a"}],
              "outputs": [{"type": "rgba"}],
              "parameters": [{"name": "blend_type", "type": "enum",
                              "values": ["normal", "multiply"],
                              "min": 0, "max": 1, "default": 0}]},
}


def _good():
    return {"type": "graph", "nodes": [
        {"name": "p", "type": "perlin", "parameters": {"scale_x": 4}},
        {"name": "b", "type": "blend", "parameters": {"blend_type": 1}},
    ], "connections": [
        {"from": "p", "from_port": 0, "to": "b", "to_port": 0},
    ]}


def test_good_graph_has_no_errors():
    problems = validate_graph(_good(), CATALOG)
    assert [p for p in problems if p["severity"] == "error"] == []


def test_unknown_node_type_is_error():
    g = _good()
    g["nodes"][0]["type"] = "nope"
    errs = [p for p in validate_graph(g, CATALOG) if p["severity"] == "error"]
    assert any("nope" in e["message"] for e in errs)


def test_dangling_connection_is_error():
    g = _good()
    g["connections"][0]["to"] = "missing"
    errs = [p for p in validate_graph(g, CATALOG) if p["severity"] == "error"]
    assert any("missing" in e["message"] for e in errs)


def test_port_out_of_range_is_error():
    g = _good()
    g["connections"][0]["to_port"] = 9
    errs = [p for p in validate_graph(g, CATALOG) if p["severity"] == "error"]
    assert any("port" in e["message"].lower() for e in errs)


def test_unknown_param_is_error():
    g = _good()
    g["nodes"][0]["parameters"] = {"bogus": 1}
    errs = [p for p in validate_graph(g, CATALOG) if p["severity"] == "error"]
    assert any("bogus" in e["message"] for e in errs)


def test_param_out_of_range_is_warning():
    g = _good()
    g["nodes"][0]["parameters"] = {"scale_x": 999}
    warns = [p for p in validate_graph(g, CATALOG) if p["severity"] == "warning"]
    assert any("scale_x" in w["message"] for w in warns)


def test_special_type_is_accepted():
    g = _good()
    g["nodes"].append({"name": "c", "type": "comment", "parameters": {}})
    errs = [p for p in validate_graph(g, CATALOG) if p["severity"] == "error"]
    assert errs == []
```

- [ ] **Step 2: Run test to verify it fails**

Run:
```
Push-Location C:\Projects-local\Tool-MaterialMaker-MCP; .\.venv\Scripts\python.exe -m pytest tests/test_validator.py -v; Pop-Location
```
Expected: FAIL with `ModuleNotFoundError: No module named 'mm_mcp.validator'`.

- [ ] **Step 3: Write minimal implementation**

Create `src/mm_mcp/validator.py`:
```python
from mm_mcp.catalog_builder import SPECIAL_TYPES


def validate_graph(ptex: dict, catalog: dict) -> list[dict]:
    problems = []
    nodes = ptex.get("nodes", [])
    by_name = {n["name"]: n for n in nodes}

    for n in nodes:
        t = n.get("type")
        if t in SPECIAL_TYPES:
            continue
        node_def = catalog.get(t)
        if node_def is None:
            problems.append({"severity": "error", "where": n.get("name", "?"),
                             "message": f"unknown node type '{t}'"})
            continue
        declared = {p["name"]: p for p in node_def["parameters"]}
        for pname, pval in (n.get("parameters") or {}).items():
            if pname not in declared:
                problems.append({"severity": "error", "where": n["name"],
                                 "message": f"unknown parameter '{pname}' for '{t}'"})
                continue
            spec = declared[pname]
            if isinstance(pval, (int, float)) and "min" in spec and "max" in spec:
                if pval < spec["min"] or pval > spec["max"]:
                    problems.append({"severity": "warning", "where": n["name"],
                                     "message": f"parameter '{pname}'={pval} outside "
                                                f"[{spec['min']}, {spec['max']}]"})

    for c in ptex.get("connections", []):
        for end in ("from", "to"):
            if c.get(end) not in by_name and c.get(end) not in ("graph",):
                problems.append({"severity": "error", "where": str(c),
                                 "message": f"connection references missing node '{c.get(end)}'"})
        src = by_name.get(c.get("from"))
        if src and src["type"] in catalog:
            n_out = len(catalog[src["type"]]["outputs"])
            if c.get("from_port", 0) >= n_out:
                problems.append({"severity": "error", "where": src["name"],
                                 "message": f"from_port {c['from_port']} out of range "
                                            f"(node has {n_out} outputs)"})
        dst = by_name.get(c.get("to"))
        if dst and dst["type"] in catalog:
            n_in = len(catalog[dst["type"]]["inputs"])
            if c.get("to_port", 0) >= n_in:
                problems.append({"severity": "error", "where": dst["name"],
                                 "message": f"to_port {c['to_port']} out of range "
                                            f"(node has {n_in} inputs)"})
    return problems
```

- [ ] **Step 4: Run test to verify it passes**

Run:
```
Push-Location C:\Projects-local\Tool-MaterialMaker-MCP; .\.venv\Scripts\python.exe -m pytest tests/test_validator.py -v; Pop-Location
```
Expected: PASS (7 passed).

- [ ] **Step 5: Commit**

```
git add src/mm_mcp/validator.py tests/test_validator.py
git commit -m "feat: graph validator against catalog"
```

---

## Task 6: Validate all bundled examples (Phase 1 GATE)

**Files:**
- Create: `tests/test_examples_gate.py`

**Interfaces:**
- Consumes: `build_catalog` (Task 3), `validate_graph` (Task 5), `load_config` (Task 1).

This is the Phase 1 gate: every bundled example's node types are recognized and no connection dangles. Parameter range warnings are allowed; unknown-type and dangling-connection ERRORS are not. Examples nest subgraphs, so the test recurses into any node that itself has a `nodes` list.

- [ ] **Step 1: Write the failing test**

Create `tests/test_examples_gate.py`:
```python
import glob
import json
import os
import pytest
from mm_mcp.catalog_builder import build_catalog
from mm_mcp.config import load_config
from mm_mcp.validator import validate_graph

cfg = load_config()
CATALOG = build_catalog(cfg.nodes_dir)
EXAMPLES = sorted(glob.glob(os.path.join(cfg.examples_dir, "*.ptex")))


def _all_graphs(node):
    """Yield the node itself and every nested subgraph (has a 'nodes' list)."""
    if isinstance(node, dict) and "nodes" in node:
        yield node
        for child in node["nodes"]:
            yield from _all_graphs(child)


@pytest.mark.parametrize("path", EXAMPLES, ids=[os.path.basename(p) for p in EXAMPLES])
def test_example_has_no_type_or_connection_errors(path):
    with open(path, encoding="utf-8") as fh:
        root = json.load(fh)
    hard_errors = []
    for g in _all_graphs(root):
        for p in validate_graph(g, CATALOG):
            if p["severity"] == "error":
                hard_errors.append(p["message"])
    assert hard_errors == [], f"{os.path.basename(path)}: {hard_errors[:5]}"
```

- [ ] **Step 2: Run test to verify current state**

Run:
```
Push-Location C:\Projects-local\Tool-MaterialMaker-MCP; .\.venv\Scripts\python.exe -m pytest tests/test_examples_gate.py -v; Pop-Location
```
Expected: some examples may FAIL initially, revealing node types the catalog or `SPECIAL_TYPES` does not yet cover (e.g. custom inline `shader` nodes, or additional structural types).

- [ ] **Step 3: Close the gaps the failures reveal**

For each unrecognized type reported:
- If it is a structural/built-in type with no `.mmg` (confirm by checking the file does not exist under `cfg.nodes_dir`), add it to `SPECIAL_TYPES` in `src/mm_mcp/catalog_builder.py`.
- If it is a real `.mmg` node being skipped, investigate why `parse_node` returned `None` (missing `shader_model`) and handle that node family.

Re-run after each change until the gate is green. Do not weaken the test to pass; fix the coverage.

- [ ] **Step 4: Run test to verify it passes**

Run:
```
Push-Location C:\Projects-local\Tool-MaterialMaker-MCP; .\.venv\Scripts\python.exe -m pytest tests/test_examples_gate.py -q; Pop-Location
```
Expected: PASS (all examples). This is the Phase 1 gate.

- [ ] **Step 5: Record the gate in STATUS.md**

Set the Phase 1 row in `STATUS.md` to `✅` with evidence: `all <N> bundled examples validate with zero type/connection errors`.

- [ ] **Step 6: Commit**

```
git add tests/test_examples_gate.py src/mm_mcp/catalog_builder.py STATUS.md
git commit -m "test: Phase 1 gate - all bundled examples validate"
```

---

## Task 7: Render runner

**Files:**
- Create: `src/mm_mcp/render.py`
- Create: `tests/test_render.py`

**Interfaces:**
- Consumes: `load_config` (Task 1).
- Produces: `mm_mcp.render.RenderResult` dataclass `{ok: bool, images: list[str], log_tail: str, error: str | None}` and `mm_mcp.render.render(ptex: dict, size: int = 512, outdir: str | None = None, basename: str = "material", cfg: Config | None = None) -> RenderResult`. It writes `ptex` to `<outdir>/<basename>.ptex`, runs the console Godot with `--export-material`, captures the log, and collects `<basename>*.png` files that are non-empty.

- [ ] **Step 1: Write the failing test**

Create `tests/test_render.py`:
```python
import json
import os
import pytest
from mm_mcp.config import load_config
from mm_mcp.render import render

cfg = load_config()


@pytest.mark.integration
def test_render_bundled_example_produces_pngs(tmp_path):
    src = os.path.join(cfg.examples_dir, "bricks.ptex")
    with open(src, encoding="utf-8") as fh:
        ptex = json.load(fh)
    result = render(ptex, size=256, outdir=str(tmp_path), basename="bricks")
    assert result.ok, result.error or result.log_tail
    assert len(result.images) >= 1
    for img in result.images:
        assert os.path.getsize(img) > 0
```

- [ ] **Step 2: Run test to verify it fails**

Run:
```
Push-Location C:\Projects-local\Tool-MaterialMaker-MCP; .\.venv\Scripts\python.exe -m pytest tests/test_render.py -v; Pop-Location
```
Expected: FAIL with `ModuleNotFoundError: No module named 'mm_mcp.render'`.

- [ ] **Step 3: Write minimal implementation**

Create `src/mm_mcp/render.py`:
```python
import json
import os
import subprocess
from dataclasses import dataclass, field
from mm_mcp.config import Config, load_config


@dataclass
class RenderResult:
    ok: bool
    images: list = field(default_factory=list)
    log_tail: str = ""
    error: str | None = None


def render(ptex: dict, size: int = 512, outdir: str | None = None,
           basename: str = "material", cfg: Config | None = None) -> RenderResult:
    cfg = cfg or load_config()
    outdir = outdir or cfg.output_dir
    os.makedirs(outdir, exist_ok=True)

    ptex_path = os.path.join(outdir, basename + ".ptex")
    with open(ptex_path, "w", encoding="utf-8") as fh:
        json.dump(ptex, fh)

    cmd = [
        cfg.console_binary, "--path", cfg.project_path,
        "--export-material", ptex_path,
        "-t", "Godot/Godot 4 Standard",
        "-o", outdir, "--size", str(size),
    ]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
    except subprocess.TimeoutExpired:
        return RenderResult(ok=False, error="Godot render timed out after 180s")

    log = (proc.stdout or "") + (proc.stderr or "")
    log_tail = "\n".join(log.splitlines()[-20:])

    prefix = basename
    images = []
    for fn in sorted(os.listdir(outdir)):
        if fn.startswith(prefix) and fn.lower().endswith(".png"):
            full = os.path.join(outdir, fn)
            if os.path.getsize(full) > 0:
                images.append(full)

    if proc.returncode != 0 and not images:
        return RenderResult(ok=False, log_tail=log_tail,
                            error=f"Godot exited {proc.returncode}")
    if not images:
        return RenderResult(ok=False, log_tail=log_tail,
                            error="no PNG output produced")
    return RenderResult(ok=True, images=images, log_tail=log_tail)
```

- [ ] **Step 4: Run test to verify it passes**

Run:
```
Push-Location C:\Projects-local\Tool-MaterialMaker-MCP; .\.venv\Scripts\python.exe -m pytest tests/test_render.py -v -m integration; Pop-Location
```
Expected: PASS (1 passed) after Godot renders. Takes several seconds.

- [ ] **Step 5: Commit**

```
git add src/mm_mcp/render.py tests/test_render.py
git commit -m "feat: headless render runner via --export-material"
```

---

## Task 8: MCP server

**Files:**
- Create: `src/mm_mcp/server.py`
- Create: `tests/test_server_tools.py`

**Interfaces:**
- Consumes: all prior modules.
- Produces: a FastMCP server object `mcp` plus plain module-level functions (the tools wrap these so they are unit-testable without a client):
  - `list_node_types(category: str = "") -> list[str]`
  - `describe_node(node_type: str) -> dict`
  - `validate(ptex: dict) -> list[dict]`
  - `render_graph(ptex: dict, size: int = 512, basename: str = "material") -> dict` (returns `{"ok","images","error","log_tail"}`)
  - `save_graph(ptex: dict, path: str) -> str`
  - `list_examples() -> list[str]`
  - `load_example(name: str) -> dict`
  - Catalog cached at import via `build_catalog`.

- [ ] **Step 1: Write the failing test**

Create `tests/test_server_tools.py`:
```python
import json
import os
from mm_mcp import server
from mm_mcp.config import load_config

cfg = load_config()


def test_list_node_types_includes_blend():
    assert "blend" in server.list_node_types()


def test_describe_node_returns_ports():
    d = server.describe_node("blend")
    assert [i["name"] for i in d["inputs"]] == ["s1", "s2", "a"]


def test_validate_flags_unknown_type():
    ptex = {"type": "graph", "nodes": [{"name": "x", "type": "nope", "parameters": {}}],
            "connections": []}
    errs = [p for p in server.validate(ptex) if p["severity"] == "error"]
    assert errs


def test_list_and_load_example():
    names = server.list_examples()
    assert "bricks" in names
    d = server.load_example("bricks")
    assert d["type"] == "graph"


def test_save_graph_writes_file(tmp_path):
    ptex = {"type": "graph", "nodes": [], "connections": []}
    out = os.path.join(str(tmp_path), "mat.ptex")
    server.save_graph(ptex, out)
    assert os.path.exists(out)
    with open(out, encoding="utf-8") as fh:
        assert json.load(fh)["type"] == "graph"
```

- [ ] **Step 2: Run test to verify it fails**

Run:
```
Push-Location C:\Projects-local\Tool-MaterialMaker-MCP; .\.venv\Scripts\python.exe -m pytest tests/test_server_tools.py -v; Pop-Location
```
Expected: FAIL with `ModuleNotFoundError: No module named 'mm_mcp.server'`.

- [ ] **Step 3: Write minimal implementation**

Create `src/mm_mcp/server.py`:
```python
import glob
import json
import os
from mcp.server.fastmcp import FastMCP
from mm_mcp.config import load_config
from mm_mcp.catalog_builder import build_catalog
from mm_mcp.validator import validate_graph
from mm_mcp.render import render

_cfg = load_config()
_CATALOG = build_catalog(_cfg.nodes_dir)

mcp = FastMCP("material-maker")


def list_node_types(category: str = "") -> list:
    names = sorted(_CATALOG.keys())
    if category:
        names = [n for n in names if category in n]
    return names


def describe_node(node_type: str) -> dict:
    if node_type not in _CATALOG:
        return {"error": f"unknown node type '{node_type}'"}
    return _CATALOG[node_type]


def validate(ptex: dict) -> list:
    return validate_graph(ptex, _CATALOG)


def render_graph(ptex: dict, size: int = 512, basename: str = "material") -> dict:
    problems = validate_graph(ptex, _CATALOG)
    errors = [p for p in problems if p["severity"] == "error"]
    if errors:
        return {"ok": False, "images": [], "error": "validation failed",
                "problems": errors}
    result = render(ptex, size=size, basename=basename, cfg=_cfg)
    return {"ok": result.ok, "images": result.images,
            "error": result.error, "log_tail": result.log_tail}


def save_graph(ptex: dict, path: str) -> str:
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(ptex, fh, indent=1)
    return path


def list_examples() -> list:
    return sorted(os.path.splitext(os.path.basename(p))[0]
                  for p in glob.glob(os.path.join(_cfg.examples_dir, "*.ptex")))


def load_example(name: str) -> dict:
    path = os.path.join(_cfg.examples_dir, name + ".ptex")
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


# Register the plain functions as MCP tools.
mcp.tool()(list_node_types)
mcp.tool()(describe_node)
mcp.tool()(validate)
mcp.tool()(render_graph)
mcp.tool()(save_graph)
mcp.tool()(list_examples)
mcp.tool()(load_example)


@mcp.resource("catalog://nodes")
def catalog_resource() -> str:
    return json.dumps(_CATALOG, indent=1)


if __name__ == "__main__":
    mcp.run()
```

- [ ] **Step 4: Run test to verify it passes**

Run:
```
Push-Location C:\Projects-local\Tool-MaterialMaker-MCP; .\.venv\Scripts\python.exe -m pytest tests/test_server_tools.py -v; Pop-Location
```
Expected: PASS (5 passed).

- [ ] **Step 5: Commit**

```
git add src/mm_mcp/server.py tests/test_server_tools.py
git commit -m "feat: MCP server exposing catalog, validate, render, examples"
```

---

## Task 9: End-to-end MCP render smoke + Phase 2 gate

**Files:**
- Create: `smoke/smoke_mcp.py`
- Modify: `STATUS.md`
- Modify: `HANDOFF.md`
- Modify: `README.md`

**Interfaces:**
- Consumes: `mm_mcp.server` (Task 8).

Phase 2 gate: an MCP `render_graph` call on a loaded example returns image paths.

- [ ] **Step 1: Write the end-to-end smoke script**

Create `smoke/smoke_mcp.py`:
```python
"""Phase 2 smoke: load a bundled example through the MCP layer and render it."""
import sys
from mm_mcp import server


def main() -> int:
    ptex = server.load_example("bricks")
    problems = [p for p in server.validate(ptex) if p["severity"] == "error"]
    if problems:
        print("VALIDATION ERRORS:", problems[:5])
        return 1
    result = server.render_graph(ptex, size=256, basename="smoke_bricks")
    if not result["ok"]:
        print("RENDER FAILED:", result.get("error"))
        print(result.get("log_tail", ""))
        return 1
    print(f"SMOKE PASS: rendered {len(result['images'])} image(s):")
    for img in result["images"]:
        print("  ", img)
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 2: Run the end-to-end smoke**

Run:
```
Push-Location C:\Projects-local\Tool-MaterialMaker-MCP; .\.venv\Scripts\python.exe smoke\smoke_mcp.py; Pop-Location
```
Expected: `SMOKE PASS: rendered N image(s)` and exit 0.

- [ ] **Step 3: Run the full test suite (non-integration + integration)**

Run:
```
Push-Location C:\Projects-local\Tool-MaterialMaker-MCP; .\.venv\Scripts\python.exe -m pytest -v; Pop-Location
```
Expected: all pass.

- [ ] **Step 4: Update the docs and ledger**

- In `STATUS.md`, set Phase 2 to `✅` with evidence `smoke_mcp.py renders a loaded example via render_graph`; set the four component rows (`catalog_builder`, `graph`, `render`, `server`) to `✅`.
- In `HANDOFF.md`, update "Where things stand" to Phase 2 complete, next step Phase 3 (authoring quality) plus the two open knobs (Phase 3 hit-rate target; whether to add variant generation).
- In `README.md`, add an "MCP server" section: run with `.\.venv\Scripts\python.exe -m mm_mcp.server`, and note the catalog must be present (built by `python -m mm_mcp.catalog_builder`).

- [ ] **Step 5: Commit**

```
git add smoke/smoke_mcp.py STATUS.md HANDOFF.md README.md
git commit -m "test: Phase 2 end-to-end MCP render smoke + docs"
```

---

## Out of scope for this plan (later phases)

- **Phase 3 — Authoring quality.** Prompt-to-graph on a material test set, tuning catalog descriptions and authoring guidance. This is an iterative tuning loop, not bite-sized TDD; it gets its own plan once Phase 2 is green. Open knobs to settle then: the usable-hit-rate target, and whether to add multi-variant generation.
- **Phase 4 — Public packaging.** Config-driven paths, cross-platform, binary auto-detect, install docs.
- **Phase 5 — Live-control.** In-app GDScript plugin over a socket for interactive, watchable building (requires forking the Material Maker source).

## Self-review notes

- **Spec coverage:** catalog builder (Task 2-3), graph builder + validator (Task 4-5), render runner (Task 7), MCP server + all seven tools (Task 8), catalog-as-resource (Task 8), Phase 1 gate = examples validate (Task 6), Phase 2 gate = MCP render (Task 9). Error-handling requirements (validation as data, render failure surfaced, missing config) covered in Tasks 5, 7, 1. Phase 3-5 explicitly deferred.
- **Type consistency:** `RenderResult`, `validate_graph`, `build_catalog`, `SPECIAL_TYPES`, `Graph.to_ptex`/`from_ptex`, and `load_config`/`Config` names are used identically across the tasks that produce and consume them.

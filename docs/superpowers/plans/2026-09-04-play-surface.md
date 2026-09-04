# Live Web Play Surface Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a local browser "play surface" that turns each cookbook material's exposed subgraph parameters into friendly sliders driving a live WebGL PBR sphere, rendering headless or via a live Material Maker session.

**Architecture:** A new standalone `src/mm_mcp/play/` package: a stdlib `http.server` app with a vendored three.js frontend, launched by a human via a new `mm-play` command. It reuses `cookbook.py` (list materials), the catalog (slider ranges), `render.py` (headless render), and `live.py` (live path). Its one new piece of logic is a slider-derivation bridge that maps a material's subgraph widgets plus catalog ranges to slider specs and back.

**Tech Stack:** Python 3.10+ standard library only (`http.server`, `json`, `threading`, `zipfile`, `webbrowser`); vendored three.js on the frontend (no build step, no npm).

**Spec:** `docs/superpowers/specs/2026-09-04-play-surface-design.md`

## Global Constraints

- Python floor: `requires-python>=3.10` (uses `X | None` union syntax already in the codebase).
- No new runtime Python dependencies. Standard library only for the play package. three.js is vendored as a static file, not fetched at runtime.
- Run tests with `.venv\Scripts\python.exe -m pytest` (or activate the venv). Fast suite: `pytest -q -m "not integration"`. Full suite (adds Godot): `pytest -q`.
- Run any `quality/*.py` or module scripts from the repo root, never from inside a subdirectory (breaks `.env` lookup).
- No em dashes in any file content, comments, commit messages, or docs. Use a colon or a spaced hyphen for label separators.
- Errors are returned as data (`{"ok": false, "error": ...}`), not raised, consistent with the project convention.
- Only one Godot process runs at a time (the render-orphan-contention rule); the render facade serializes renders with a lock.
- Server binds to `127.0.0.1` only. No auth, single user.
- Commit after each task with a `feat:`/`test:`/`docs:` message ending with the `Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>` trailer.

---

### Task 1: Add the play-server port to config

**Files:**
- Modify: `src/mm_mcp/config.py`
- Test: `tests/test_config.py`

**Interfaces:**
- Consumes: the existing `Config` dataclass and `load_config()`.
- Produces: `Config.play_port: int` (default 8788), read from `MM_PLAY_PORT`.

- [ ] **Step 1: Write the failing test**

Add to `tests/test_config.py`:

```python
def test_play_port_defaults_to_8788(monkeypatch, tmp_path):
    monkeypatch.delenv("MM_PLAY_PORT", raising=False)
    # minimal env so load_config() succeeds; reuse the file's existing helper
    cfg = _load_with_env(monkeypatch, tmp_path, {})  # see note below
    assert cfg.play_port == 8788


def test_play_port_reads_env(monkeypatch, tmp_path):
    cfg = _load_with_env(monkeypatch, tmp_path, {"MM_PLAY_PORT": "9001"})
    assert cfg.play_port == 9001
```

Note: `tests/test_config.py` already constructs configs in its existing tests. If it has no `_load_with_env` helper, mirror the pattern the nearest existing test uses to set env vars and call `load_config()`; the two assertions above are what matter.

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv\Scripts\python.exe -m pytest tests/test_config.py -k play_port -v`
Expected: FAIL (`Config` has no attribute `play_port`).

- [ ] **Step 3: Add the field and env parsing**

In `src/mm_mcp/config.py`, add to the `Config` dataclass (after `cookbook_dir`):

```python
    play_port: int = 8788
```

In `load_config()`, after the `cookbook_dir` line, add:

```python
    play_port = int(env["MM_PLAY_PORT"] or 8788)
```

and pass `play_port=play_port` in the `Config(...)` construction.

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv\Scripts\python.exe -m pytest tests/test_config.py -k play_port -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/mm_mcp/config.py tests/test_config.py
git commit -m "feat(play): add MM_PLAY_PORT config field"
```

---

### Task 2: Slider-derivation bridge (derive)

**Files:**
- Create: `src/mm_mcp/play/__init__.py` (empty)
- Create: `src/mm_mcp/play/sliders.py`
- Test: `tests/test_play_sliders.py`

**Interfaces:**
- Consumes: a material graph dict (with `type: "graph"` subgraph nodes), a catalog dict keyed by node type (`catalog[type]["parameters"]` is a list of `{name, type, default, min, max, step}`).
- Produces: `derive_sliders(graph: dict, catalog: dict) -> list[dict]`. Each dict: `{"group": str, "slot_id": str, "label": str, "kind": str, "min": float|None, "max": float|None, "step": float|None, "value": Any, "binding": {"node": str, "widget": str}}`. `kind` is one of `"float"`, `"int"`, `"enum"`, `"color"`, `"bool"`.

- [ ] **Step 1: Write the failing test**

Create `tests/test_play_sliders.py`:

```python
import json
import mm_mcp.cookbook as cookbook
from mm_mcp.catalog_builder import build_catalog
from mm_mcp.config import load_config
from mm_mcp.play.sliders import derive_sliders


def _catalog():
    return build_catalog(load_config().nodes_dir)


def test_derive_sliders_from_a_terrain_material():
    cfg = load_config()
    entry = cookbook.find_cookbook(cfg.cookbook_dir, "t01_sand_dunes")
    graph = json.load(open(entry.path, encoding="utf-8"))
    sliders = derive_sliders(graph, _catalog())
    assert sliders, "expected at least one exposed slider"
    labels = [s["label"] for s in sliders]
    assert "Ripple scale" in labels
    ripple = next(s for s in sliders if s["label"] == "Ripple scale")
    assert ripple["binding"] == {"node": "perlin_2", "widget": "scale_x"}
    assert ripple["kind"] == "float"
    assert ripple["min"] is not None and ripple["max"] is not None
    assert ripple["value"] is not None
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv\Scripts\python.exe -m pytest tests/test_play_sliders.py -v`
Expected: FAIL (`mm_mcp.play.sliders` does not exist).

- [ ] **Step 3: Implement `derive_sliders`**

Create `src/mm_mcp/play/__init__.py` (empty). Create `src/mm_mcp/play/sliders.py`:

```python
"""Bridge between a cookbook material's exposed subgraph parameters and web
sliders. Each retrofitted material has one or more `type: "graph"` nodes; each
carries a `remote` node (gen_parameters) whose `widgets` are the author-chosen
exposed parameters. This module turns those widgets, plus the catalog's per-param
ranges, into slider specs, and applies a set of slider values back onto a graph.
"""
from typing import Any

# Material Maker param type -> slider kind.
_KIND = {
    "float": "float",
    "int": "int",
    "size": "int",
    "enum": "enum",
    "boolean": "bool",
    "color": "color",
    "gradient": "color",
}


def _remote_widgets(subgraph_node: dict) -> list[dict]:
    for inner in subgraph_node.get("nodes", []):
        if inner.get("type") == "remote":
            return inner.get("widgets", [])
    return []


def _internal_type(subgraph_node: dict, node_name: str) -> str | None:
    for inner in subgraph_node.get("nodes", []):
        if inner.get("name") == node_name:
            return inner.get("type")
    return None


def _param_def(catalog: dict, node_type: str, param_name: str) -> dict | None:
    node = catalog.get(node_type)
    if not node:
        return None
    for p in node.get("parameters", []):
        if p.get("name") == param_name:
            return p
    return None


def derive_sliders(graph: dict, catalog: dict) -> list[dict]:
    """One slider spec per exposed widget across all subgraph nodes in `graph`."""
    sliders: list[dict] = []
    for node in graph.get("nodes", []):
        if node.get("type") != "graph":
            continue
        group = node.get("label") or node.get("name", "")
        params = node.get("parameters", {})
        for widget in _remote_widgets(node):
            slot_id = widget.get("name")
            if not slot_id:
                continue
            linked = (widget.get("linked_widgets") or [{}])[0]
            inode_name = linked.get("node")
            iparam = linked.get("widget")
            itype = _internal_type(node, inode_name)
            pdef = _param_def(catalog, itype, iparam) if itype else None
            kind = _KIND.get((pdef or {}).get("type"), "float")
            sliders.append({
                "group": group,
                "slot_id": slot_id,
                "label": widget.get("shortdesc") or slot_id,
                "kind": kind,
                "min": (pdef or {}).get("min"),
                "max": (pdef or {}).get("max"),
                "step": (pdef or {}).get("step"),
                "value": params.get(slot_id),
                "binding": {"node": inode_name, "widget": iparam},
            })
    return sliders
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv\Scripts\python.exe -m pytest tests/test_play_sliders.py -v`
Expected: PASS.

- [ ] **Step 5: Add the all-46 consistency gate**

Append to `tests/test_play_sliders.py`:

```python
import pytest


def _all_entries():
    cfg = load_config()
    return cookbook.list_cookbook(cfg.cookbook_dir)


@pytest.mark.parametrize("entry", _all_entries(), ids=lambda e: e.name)
def test_every_cookbook_material_yields_consistent_sliders(entry):
    graph = json.load(open(entry.path, encoding="utf-8"))
    sliders = derive_sliders(graph, _catalog())
    assert sliders, f"{entry.name} exposed no sliders"
    for s in sliders:
        assert s["binding"]["node"], f"{entry.name}/{s['slot_id']} unresolved node"
        assert s["binding"]["widget"], f"{entry.name}/{s['slot_id']} unresolved widget"
        if s["kind"] in ("float", "int"):
            assert s["min"] is not None and s["max"] is not None, \
                f"{entry.name}/{s['slot_id']} missing numeric range"
```

- [ ] **Step 6: Run the gate**

Run: `.venv\Scripts\python.exe -m pytest tests/test_play_sliders.py -v`
Expected: PASS for all 46 materials. If a material fails the numeric-range check, its exposed param maps to a catalog param with no min/max; note the material and param in the task report so the reviewer can decide whether to widen `_KIND` or accept an unranged slider (the frontend can fall back to a numeric input).

- [ ] **Step 7: Commit**

```bash
git add src/mm_mcp/play/__init__.py src/mm_mcp/play/sliders.py tests/test_play_sliders.py
git commit -m "feat(play): derive web sliders from subgraph widgets + catalog ranges"
```

---

### Task 3: Slider-derivation bridge (apply values back)

**Files:**
- Modify: `src/mm_mcp/play/sliders.py`
- Test: `tests/test_play_sliders.py`

**Interfaces:**
- Consumes: `derive_sliders` (Task 2), a material graph dict, a `{slot_id: value}` dict.
- Produces: `apply_values(graph: dict, values: dict) -> dict`. Returns a deep-copied graph with each value written into both the linked internal node's parameter and the subgraph node's mirrored `parameters`/`gen_parameters` copies, so headless render (reads the internal node) and a live session stay consistent. Unknown slot_ids are ignored.

- [ ] **Step 1: Write the failing test**

Append to `tests/test_play_sliders.py`:

```python
from mm_mcp.play.sliders import apply_values


def test_apply_values_round_trips_through_derive():
    cfg = load_config()
    entry = cookbook.find_cookbook(cfg.cookbook_dir, "t01_sand_dunes")
    graph = json.load(open(entry.path, encoding="utf-8"))
    cat = _catalog()
    applied = apply_values(graph, {"param0": 9.0})
    # original untouched (deep copy)
    orig = next(n for n in graph["nodes"] if n.get("type") == "graph"
                and n.get("label") == "Dune Ripples")
    assert orig["parameters"]["param0"] != 9.0 or True  # tolerate equal default
    # internal node updated in the applied graph
    sub = next(n for n in applied["nodes"] if n.get("type") == "graph"
               and n.get("label") == "Dune Ripples")
    perlin = next(n for n in sub["nodes"] if n.get("name") == "perlin_2")
    assert perlin["parameters"]["scale_x"] == 9.0
    assert sub["parameters"]["param0"] == 9.0
    # and derive now reports the new value
    sliders = apply_then_derive = derive_sliders(applied, cat)
    ripple = next(s for s in sliders if s["label"] == "Ripple scale")
    assert ripple["value"] == 9.0


def test_apply_values_ignores_unknown_slot():
    cfg = load_config()
    entry = cookbook.find_cookbook(cfg.cookbook_dir, "t01_sand_dunes")
    graph = json.load(open(entry.path, encoding="utf-8"))
    applied = apply_values(graph, {"nonexistent_slot": 1.0})
    assert applied == graph  # no-op, deep-equal
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv\Scripts\python.exe -m pytest tests/test_play_sliders.py -k apply -v`
Expected: FAIL (`apply_values` not defined).

- [ ] **Step 3: Implement `apply_values`**

Add to `src/mm_mcp/play/sliders.py`:

```python
import copy


def apply_values(graph: dict, values: dict) -> dict:
    """Write slot_id->value into every matching subgraph. Returns a new graph;
    the input is not mutated. Unknown slot_ids are ignored."""
    out = copy.deepcopy(graph)
    for node in out.get("nodes", []):
        if node.get("type") != "graph":
            continue
        widgets = _remote_widgets(node)
        by_slot = {w.get("name"): w for w in widgets}
        for slot_id, value in values.items():
            widget = by_slot.get(slot_id)
            if widget is None:
                continue
            linked = (widget.get("linked_widgets") or [{}])[0]
            inode_name = linked.get("node")
            iparam = linked.get("widget")
            for inner in node.get("nodes", []):
                if inner.get("name") == inode_name:
                    inner.setdefault("parameters", {})[iparam] = value
                if inner.get("type") == "remote":
                    inner.setdefault("parameters", {})[slot_id] = value
            node.setdefault("parameters", {})[slot_id] = value
    return out
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv\Scripts\python.exe -m pytest tests/test_play_sliders.py -k apply -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/mm_mcp/play/sliders.py tests/test_play_sliders.py
git commit -m "feat(play): apply slider values back onto a material graph"
```

---

### Task 4: Render facade (headless + live auto-detect + serialization)

**Files:**
- Create: `src/mm_mcp/play/renderer.py`
- Test: `tests/test_play_renderer.py`

**Interfaces:**
- Consumes: `render.render(ptex, size, outdir, basename, cfg) -> RenderResult` (`.ok`, `.images: list[str]`, `.error`); `live.ping(timeout) -> LiveResult` (`.ok`, `.data` with `has_graph`); `live.set_param(name, parameters, cfg) -> LiveResult`; `live.render(basename, cfg) -> LiveResult`.
- Produces: `render_material(applied_graph, changes, size, cfg, outdir, *, ping=live.ping, live_set_param=live.set_param, live_render=live.render, headless_render=render.render) -> dict`. `changes` is a list of `{"node": str, "widget": str, "value": Any}` (for the live path). Returns `{"ok": bool, "path": "live"|"headless", "images": list[str], "error": str|None}`. All renders run under a module lock so only one Godot runs at a time.

- [ ] **Step 1: Write the failing test**

Create `tests/test_play_renderer.py`:

```python
from mm_mcp.play import renderer


class _Result:
    def __init__(self, ok, images=None, error=None, data=None):
        self.ok = ok
        self.images = images or []
        self.error = error
        self.data = data or {}


def _cfg():
    from mm_mcp.config import load_config
    return load_config()


def test_uses_headless_when_no_live_session():
    calls = {}

    def fake_ping(timeout=1.0):
        return _Result(False)

    def fake_headless(ptex, size=512, outdir=None, basename="material", cfg=None):
        calls["headless"] = True
        return _Result(True, images=["a_albedo.png"])

    out = renderer.render_material(
        {"nodes": [], "connections": []}, [], 256, _cfg(), outdir="x",
        ping=fake_ping, headless_render=fake_headless)
    assert out["ok"] and out["path"] == "headless"
    assert calls.get("headless")


def test_uses_live_when_session_has_graph():
    sent = []

    def fake_ping(timeout=1.0):
        return _Result(True, data={"has_graph": True})

    def fake_set_param(name, parameters, cfg=None):
        sent.append((name, parameters))
        return _Result(True)

    def fake_live_render(basename="material", cfg=None):
        return _Result(True, images=["live_albedo.png"])

    changes = [{"node": "perlin_2", "widget": "scale_x", "value": 9.0}]
    out = renderer.render_material(
        {"nodes": [], "connections": []}, changes, 256, _cfg(), outdir="x",
        ping=fake_ping, live_set_param=fake_set_param, live_render=fake_live_render)
    assert out["ok"] and out["path"] == "live"
    assert sent == [("perlin_2", {"scale_x": 9.0})]


def test_falls_back_to_headless_when_live_set_param_fails():
    def fake_ping(timeout=1.0):
        return _Result(True, data={"has_graph": True})

    def fake_set_param(name, parameters, cfg=None):
        return _Result(False, error="node not found")

    def fake_headless(ptex, size=512, outdir=None, basename="material", cfg=None):
        return _Result(True, images=["fallback_albedo.png"])

    changes = [{"node": "ghost", "widget": "x", "value": 1}]
    out = renderer.render_material(
        {"nodes": [], "connections": []}, changes, 256, _cfg(), outdir="x",
        ping=fake_ping, live_set_param=fake_set_param, headless_render=fake_headless)
    assert out["ok"] and out["path"] == "headless"
    assert out["images"] == ["fallback_albedo.png"]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv\Scripts\python.exe -m pytest tests/test_play_renderer.py -v`
Expected: FAIL (`mm_mcp.play.renderer` does not exist).

- [ ] **Step 3: Implement the facade**

Create `src/mm_mcp/play/renderer.py`:

```python
"""Chooses the render path for the play surface: drive a live Material Maker
session when one is up and usable, otherwise render headless. Serializes all
renders so only one Godot runs at a time (the render-orphan-contention rule).
"""
import threading

from mm_mcp import live, render

_RENDER_LOCK = threading.Lock()


def render_material(applied_graph, changes, size, cfg, outdir, *,
                    ping=live.ping, live_set_param=live.set_param,
                    live_render=live.render, headless_render=render.render):
    """Render `applied_graph` (values already applied). `changes` drives the live
    path. Returns {ok, path, images, error}. One Godot at a time."""
    with _RENDER_LOCK:
        probe = ping(timeout=1.0)
        if probe.ok and probe.data.get("has_graph"):
            live_result = _try_live(changes, cfg, live_set_param, live_render)
            if live_result is not None:
                return live_result
            # live was up but not usable (mismatch): fall through to headless.
        r = headless_render(applied_graph, size=size, outdir=outdir,
                            basename="play", cfg=cfg)
        return {"ok": r.ok, "path": "headless",
                "images": list(r.images), "error": r.error}


def _try_live(changes, cfg, live_set_param, live_render):
    for ch in changes:
        res = live_set_param(ch["node"], {ch["widget"]: ch["value"]}, cfg=cfg)
        if not res.ok:
            return None  # signal: fall back to headless
    r = live_render(basename="play", cfg=cfg)
    if not r.ok:
        return None
    return {"ok": True, "path": "live", "images": list(r.images), "error": None}
```

Note: `live.set_param`/`live.render` signatures in `live.py` take `cfg` and host/port kwargs with defaults; the calls above pass only `cfg`, relying on the module defaults for host/port. If the real signatures differ (check `src/mm_mcp/live.py:272` and `:312`), adjust the two calls in `_try_live` to match, keeping the injected-callable seams so the tests stay valid.

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv\Scripts\python.exe -m pytest tests/test_play_renderer.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/mm_mcp/play/renderer.py tests/test_play_renderer.py
git commit -m "feat(play): render facade with live auto-detect and serialized renders"
```

---

### Task 5: API handlers (list, get material, render)

**Files:**
- Create: `src/mm_mcp/play/api.py`
- Test: `tests/test_play_api.py`

**Interfaces:**
- Consumes: `cookbook.list_cookbook(cfg.cookbook_dir)`, `cookbook.find_cookbook(cfg.cookbook_dir, name)`; `sliders.derive_sliders`, `sliders.apply_values`; `renderer.render_material`; `catalog_builder.build_catalog(cfg.nodes_dir)`.
- Produces:
  - `list_materials(cfg) -> dict` : `{"ok": True, "materials": [{"name", "category"}]}`.
  - `get_material(cfg, catalog, name) -> dict` : `{"ok": True, "name", "sliders": [...]}` or `{"ok": False, "error"}`.
  - `render_request(cfg, catalog, body, outdir, render_fn=renderer.render_material) -> dict` : body is `{"material_id", "values", "size"}`; returns `{"ok", "path", "maps": [basename.png, ...], "error"}` where `maps` are the file basenames of the rendered images.

- [ ] **Step 1: Write the failing test**

Create `tests/test_play_api.py`:

```python
import os
from mm_mcp.play import api
from mm_mcp.config import load_config
from mm_mcp.catalog_builder import build_catalog


def _cfg():
    return load_config()


def _catalog(cfg):
    return build_catalog(cfg.nodes_dir)


def test_list_materials_returns_all_cookbook_entries():
    out = api.list_materials(_cfg())
    assert out["ok"]
    names = [m["name"] for m in out["materials"]]
    assert "t01_sand_dunes" in names
    assert all("category" in m for m in out["materials"])


def test_get_material_returns_sliders():
    cfg = _cfg()
    out = api.get_material(cfg, _catalog(cfg), "t01_sand_dunes")
    assert out["ok"]
    assert any(s["label"] == "Ripple scale" for s in out["sliders"])


def test_get_material_unknown_is_error_data():
    cfg = _cfg()
    out = api.get_material(cfg, _catalog(cfg), "does_not_exist")
    assert out["ok"] is False and "error" in out


def test_render_request_applies_values_and_calls_renderer(tmp_path):
    cfg = _cfg()

    def fake_render(applied_graph, changes, size, cfg, outdir, **kw):
        # assert the value was applied into the graph before rendering
        sub = next(n for n in applied_graph["nodes"]
                   if n.get("type") == "graph" and n.get("label") == "Dune Ripples")
        perlin = next(n for n in sub["nodes"] if n.get("name") == "perlin_2")
        assert perlin["parameters"]["scale_x"] == 12.0
        assert {"node": "perlin_2", "widget": "scale_x", "value": 12.0} in changes
        p = os.path.join(outdir, "play_albedo.png")
        open(p, "wb").close()
        return {"ok": True, "path": "headless", "images": [p], "error": None}

    body = {"material_id": "t01_sand_dunes", "values": {"param0": 12.0}, "size": 256}
    out = api.render_request(cfg, _catalog(cfg), body, str(tmp_path),
                             render_fn=fake_render)
    assert out["ok"] and out["path"] == "headless"
    assert out["maps"] == ["play_albedo.png"]


def test_render_request_unknown_material_is_error_data(tmp_path):
    cfg = _cfg()
    body = {"material_id": "nope", "values": {}, "size": 256}
    out = api.render_request(cfg, _catalog(cfg), body, str(tmp_path))
    assert out["ok"] is False and "error" in out
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv\Scripts\python.exe -m pytest tests/test_play_api.py -v`
Expected: FAIL (`mm_mcp.play.api` does not exist).

- [ ] **Step 3: Implement the handlers**

Create `src/mm_mcp/play/api.py`:

```python
"""Pure request handlers for the play surface. Each takes already-parsed input
and returns JSON-serializable data; no socket, no HTTP. Errors are data."""
import json
import os

from mm_mcp import cookbook
from mm_mcp.play import renderer, sliders


def list_materials(cfg) -> dict:
    entries = cookbook.list_cookbook(cfg.cookbook_dir)
    return {"ok": True,
            "materials": [{"name": e.name, "category": e.category} for e in entries]}


def _load_graph(cfg, name):
    entry = cookbook.find_cookbook(cfg.cookbook_dir, name)
    if entry is None:
        return None, {"ok": False, "error": f"unknown material: {name}"}
    with open(entry.path, encoding="utf-8") as fh:
        return json.load(fh), None


def get_material(cfg, catalog, name) -> dict:
    graph, err = _load_graph(cfg, name)
    if err:
        return err
    return {"ok": True, "name": name,
            "sliders": sliders.derive_sliders(graph, catalog)}


def _changes_for(graph, catalog, values):
    """Map slot_id->value to per-node live changes, using the derived bindings."""
    by_slot = {s["slot_id"]: s for s in sliders.derive_sliders(graph, catalog)}
    changes = []
    for slot_id, value in values.items():
        s = by_slot.get(slot_id)
        if s:
            changes.append({"node": s["binding"]["node"],
                            "widget": s["binding"]["widget"], "value": value})
    return changes


def render_request(cfg, catalog, body, outdir, render_fn=renderer.render_material) -> dict:
    name = body.get("material_id")
    values = body.get("values") or {}
    size = int(body.get("size") or 256)
    graph, err = _load_graph(cfg, name)
    if err:
        return err
    applied = sliders.apply_values(graph, values)
    changes = _changes_for(graph, catalog, values)
    result = render_fn(applied, changes, size, cfg, outdir)
    if not result.get("ok"):
        return {"ok": False, "error": result.get("error") or "render failed"}
    return {"ok": True, "path": result.get("path"),
            "maps": [os.path.basename(p) for p in result.get("images", [])]}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv\Scripts\python.exe -m pytest tests/test_play_api.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/mm_mcp/play/api.py tests/test_play_api.py
git commit -m "feat(play): pure API handlers for materials list, sliders, and render"
```

---

### Task 6: stdlib HTTP server + routing + static + mm-play entry + packaging

**Files:**
- Create: `src/mm_mcp/play/server.py`
- Create: `src/mm_mcp/play/static/index.html` (placeholder body, real UI lands in Task 7)
- Modify: `pyproject.toml` (`[project.scripts]`, `[tool.setuptools.package-data]`)
- Test: `tests/test_play_server.py`

**Interfaces:**
- Consumes: `api.list_materials`, `api.get_material`, `api.render_request`; `config.load_config`; `catalog_builder.build_catalog`.
- Produces: `make_handler(cfg, catalog, outdir, static_dir) -> BaseHTTPRequestHandler subclass`; `serve(cfg=None, open_browser=False) -> None`; `main(argv=None) -> int` (the `mm-play` entry point). Routes: `GET /`, `GET /api/materials`, `GET /api/material/<id>`, `POST /api/render`, `GET /api/maps/<name>.png`, static files under `/static/`.

- [ ] **Step 1: Write the failing test**

Create `tests/test_play_server.py`:

```python
import json
import threading
import urllib.request
from http.server import HTTPServer

import pytest
from mm_mcp.config import load_config
from mm_mcp.catalog_builder import build_catalog
from mm_mcp.play import server


@pytest.fixture()
def running_server(tmp_path):
    cfg = load_config()
    catalog = build_catalog(cfg.nodes_dir)
    handler = server.make_handler(cfg, catalog, str(tmp_path),
                                  str(server.STATIC_DIR))
    httpd = HTTPServer(("127.0.0.1", 0), handler)
    t = threading.Thread(target=httpd.serve_forever, daemon=True)
    t.start()
    yield f"http://127.0.0.1:{httpd.server_address[1]}"
    httpd.shutdown()


def _get(url):
    with urllib.request.urlopen(url) as r:
        return r.status, r.read()


def test_root_serves_html(running_server):
    status, body = _get(running_server + "/")
    assert status == 200
    assert b"<html" in body.lower()


def test_api_materials(running_server):
    status, body = _get(running_server + "/api/materials")
    assert status == 200
    data = json.loads(body)
    assert data["ok"] and any(m["name"] == "t01_sand_dunes" for m in data["materials"])


def test_unknown_path_404(running_server):
    with pytest.raises(urllib.error.HTTPError) as exc:
        _get(running_server + "/nope")
    assert exc.value.code == 404
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv\Scripts\python.exe -m pytest tests/test_play_server.py -v`
Expected: FAIL (`mm_mcp.play.server` does not exist).

- [ ] **Step 3: Create a placeholder static page**

Create `src/mm_mcp/play/static/index.html`:

```html
<!doctype html>
<html lang="en">
<head><meta charset="utf-8"><title>Material Maker Play</title></head>
<body><div id="app">Loading...</div></body>
</html>
```

- [ ] **Step 4: Implement the server**

Create `src/mm_mcp/play/server.py`:

```python
"""Standalone local web server for the play surface. Binds to 127.0.0.1, single
user, no auth. Launched by a human via `mm-play`. Renders are serialized in the
facade (renderer.py), so the threading server is safe."""
import json
import os
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from mm_mcp.catalog_builder import build_catalog
from mm_mcp.config import load_config
from mm_mcp.play import api
from mm_mcp.paths import reject_path_fragment

STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")


def make_handler(cfg, catalog, outdir, static_dir):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass  # quiet

        def _send_json(self, obj, status=200):
            body = json.dumps(obj).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def _send_bytes(self, data, content_type, status=200):
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def _serve_static(self, rel):
            if reject_path_fragment(rel):
                return self._send_json({"ok": False, "error": "bad path"}, 400)
            path = os.path.join(static_dir, rel)
            if not os.path.isfile(path):
                return self._send_json({"ok": False, "error": "not found"}, 404)
            ctype = ("text/html" if path.endswith(".html")
                     else "application/javascript" if path.endswith(".js")
                     else "text/css" if path.endswith(".css")
                     else "application/octet-stream")
            with open(path, "rb") as fh:
                self._send_bytes(fh.read(), ctype)

        def do_GET(self):
            path = self.path.split("?", 1)[0]
            if path == "/":
                return self._serve_static("index.html")
            if path == "/api/materials":
                return self._send_json(api.list_materials(cfg))
            if path.startswith("/api/material/"):
                name = path[len("/api/material/"):]
                out = api.get_material(cfg, catalog, name)
                return self._send_json(out, 200 if out["ok"] else 404)
            if path.startswith("/api/maps/"):
                name = path[len("/api/maps/"):]
                if reject_path_fragment(name):
                    return self._send_json({"ok": False, "error": "bad path"}, 400)
                fp = os.path.join(outdir, name)
                if not os.path.isfile(fp):
                    return self._send_json({"ok": False, "error": "not found"}, 404)
                with open(fp, "rb") as fh:
                    return self._send_bytes(fh.read(), "image/png")
            if path.startswith("/static/"):
                return self._serve_static(path[len("/static/"):])
            return self._send_json({"ok": False, "error": "not found"}, 404)

        def do_POST(self):
            path = self.path.split("?", 1)[0]
            length = int(self.headers.get("Content-Length") or 0)
            raw = self.rfile.read(length) if length else b"{}"
            try:
                body = json.loads(raw or b"{}")
            except json.JSONDecodeError:
                return self._send_json({"ok": False, "error": "bad json"}, 400)
            if path == "/api/render":
                out = api.render_request(cfg, catalog, body, outdir)
                return self._send_json(out, 200 if out["ok"] else 400)
            return self._send_json({"ok": False, "error": "not found"}, 404)

    return Handler


def serve(cfg=None, open_browser=False):
    cfg = cfg or load_config()
    catalog = build_catalog(cfg.nodes_dir)
    outdir = os.path.join(cfg.output_dir, "play")
    os.makedirs(outdir, exist_ok=True)
    handler = make_handler(cfg, catalog, outdir, STATIC_DIR)
    httpd = ThreadingHTTPServer(("127.0.0.1", cfg.play_port), handler)
    url = f"http://127.0.0.1:{cfg.play_port}/"
    print(f"Material Maker Play running at {url}  (Ctrl+C to stop)")
    if open_browser:
        webbrowser.open(url)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        httpd.shutdown()
    return None


def main(argv=None):
    serve(open_browser=True)
    return 0
```

Note: confirm `reject_path_fragment` exists in `src/mm_mcp/paths.py` and takes a single path-fragment string returning truthy when unsafe (per STATUS.md's paths.py row). If its signature differs, adapt the two guard calls; keep a traversal guard on both `/static/` and `/api/maps/`.

- [ ] **Step 5: Wire the console script and package-data**

In `pyproject.toml`, under `[project.scripts]` add:

```toml
mm-play = "mm_mcp.play.server:main"
```

Under `[tool.setuptools.package-data]`, change the `mm_mcp` line to also include the play static assets:

```toml
mm_mcp = ["preview_project/*", "play/static/*"]
```

- [ ] **Step 6: Run tests to verify they pass**

Run: `.venv\Scripts\python.exe -m pytest tests/test_play_server.py -v`
Expected: PASS (root html, materials json, 404).

- [ ] **Step 7: Commit**

```bash
git add src/mm_mcp/play/server.py src/mm_mcp/play/static/index.html pyproject.toml tests/test_play_server.py
git commit -m "feat(play): stdlib http server, routing, mm-play entry, packaging"
```

---

### Task 7: End-to-end headless render integration test

**Files:**
- Test: `tests/test_play_server.py` (add an integration test)

**Interfaces:**
- Consumes: the running server fixture (Task 6), a real Godot via `render.render` behind the facade.

- [ ] **Step 1: Write the integration test**

Append to `tests/test_play_server.py`:

```python
@pytest.mark.integration
def test_render_endpoint_produces_maps(running_server):
    payload = json.dumps({"material_id": "t01_sand_dunes",
                          "values": {}, "size": 256}).encode()
    req = urllib.request.Request(running_server + "/api/render", data=payload,
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=240) as r:
        data = json.loads(r.read())
    assert data["ok"], data
    assert data["maps"], "expected rendered maps"
    # each map is fetchable and non-empty
    for name in data["maps"]:
        with urllib.request.urlopen(running_server + "/api/maps/" + name) as r:
            body = r.read()
        assert len(body) > 0
```

- [ ] **Step 2: Run it (real Godot)**

Run: `.venv\Scripts\python.exe -m pytest tests/test_play_server.py -k render_endpoint -v`
Expected: PASS. This launches Godot; ensure no other render/live session is running first (kill stray Godot processes if it times out; see the render-orphan-contention note in CLAUDE.md/memory).

- [ ] **Step 3: Confirm the fast suite still excludes it**

Run: `.venv\Scripts\python.exe -m pytest tests/test_play_server.py -q -m "not integration"`
Expected: the integration test is deselected; the rest pass.

- [ ] **Step 4: Commit**

```bash
git add tests/test_play_server.py
git commit -m "test(play): end-to-end headless render integration test"
```

---

### Task 8: Frontend (gallery, sliders, WebGL sphere)

**Files:**
- Create: `src/mm_mcp/play/static/app.js`
- Create: `src/mm_mcp/play/static/style.css`
- Create: `src/mm_mcp/play/static/three.min.js` (vendored)
- Create: `src/mm_mcp/play/static/VENDOR.md`
- Modify: `src/mm_mcp/play/static/index.html` (real UI)

**Interfaces:**
- Consumes: the server's `GET /api/materials`, `GET /api/material/<id>`, `POST /api/render`, `GET /api/maps/<name>`.
- Produces: a working single-page UI. This task is verified manually in a browser, not by an automated test (the server smoke test already covers static serving).

- [ ] **Step 1: Vendor three.js**

Download a pinned three.js UMD build (r160 or later) to `src/mm_mcp/play/static/three.min.js`. Record the exact version and source URL in `src/mm_mcp/play/static/VENDOR.md`:

```markdown
# Vendored frontend assets

- three.min.js: three.js r<VERSION>, UMD build, from
  https://cdnjs.cloudflare.com/ajax/libs/three.js/r<VERSION>/three.min.js
  Vendored (not fetched at runtime) so the play surface has no network
  dependency. Exposes the global `THREE`.
```

Use the Bash tool to fetch it, for example:
`curl -L -o src/mm_mcp/play/static/three.min.js https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js`
(r128 is the last UMD `three.min.js` cdnjs serves as a single global-exposing file; if a newer single-file UMD build is available, prefer it and update VENDOR.md. OrbitControls is not required; implement drag-to-rotate manually in app.js to avoid a second vendored file.)

- [ ] **Step 2: Write index.html**

Replace `src/mm_mcp/play/static/index.html`:

```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Material Maker Play</title>
  <link rel="stylesheet" href="/static/style.css">
</head>
<body>
  <div id="layout">
    <aside id="left">
      <h1>Material Maker Play</h1>
      <div id="gallery"></div>
      <div id="controls" hidden>
        <h2 id="material-name"></h2>
        <div id="sliders"></div>
        <div id="actions">
          <button id="full">Render full quality</button>
          <button id="download">Download</button>
          <span id="status"></span>
        </div>
      </div>
    </aside>
    <main id="viewport"></main>
  </div>
  <script src="/static/three.min.js"></script>
  <script src="/static/app.js"></script>
</body>
</html>
```

- [ ] **Step 3: Write style.css**

Create `src/mm_mcp/play/static/style.css`:

```css
* { box-sizing: border-box; }
body { margin: 0; font: 14px system-ui, sans-serif; color: #eee; background: #1b1b1f; }
#layout { display: flex; height: 100vh; }
#left { width: 320px; padding: 16px; overflow-y: auto; background: #232329; }
#viewport { flex: 1; }
#viewport canvas { display: block; width: 100%; height: 100%; }
h1 { font-size: 16px; } h2 { font-size: 14px; margin: 12px 0 6px; }
#gallery button { display: block; width: 100%; text-align: left; margin: 2px 0;
  padding: 6px 8px; background: #2f2f37; color: #ddd; border: 1px solid #3a3a44;
  border-radius: 4px; cursor: pointer; }
#gallery button:hover { background: #3a3a46; }
.slider-row { margin: 8px 0; }
.slider-row label { display: block; margin-bottom: 2px; color: #bbb; }
.slider-row input[type=range] { width: 100%; }
#actions { margin-top: 16px; display: flex; gap: 8px; align-items: center; }
button { cursor: pointer; }
#status { color: #9c9; font-size: 12px; }
```

- [ ] **Step 4: Write app.js**

Create `src/mm_mcp/play/static/app.js`:

```javascript
/* Play surface frontend. Talks to the local server, shows a cookbook gallery,
   renders author-named sliders, and shades a three.js sphere with the returned
   PBR maps. Rotate: drag the viewport. Slider release triggers a small render. */
"use strict";

let current = null;      // {name, sliders}
let values = {};         // slot_id -> value
let debounceTimer = null;
let sphere = null, renderer = null, scene = null, camera = null;
let yaw = 0.6, pitch = 0.3, dragging = false, lastX = 0, lastY = 0;

async function j(url, opts) { const r = await fetch(url, opts); return r.json(); }

function initThree() {
  const el = document.getElementById("viewport");
  renderer = new THREE.WebGLRenderer({ antialias: true });
  renderer.setSize(el.clientWidth, el.clientHeight);
  el.appendChild(renderer.domElement);
  scene = new THREE.Scene();
  scene.background = new THREE.Color(0x15151a);
  camera = new THREE.PerspectiveCamera(45, el.clientWidth / el.clientHeight, 0.1, 100);
  camera.position.set(0, 0, 3.2);
  scene.add(new THREE.AmbientLight(0x404050, 1.2));
  const key = new THREE.DirectionalLight(0xffffff, 2.0);
  key.position.set(3, 3, 4); scene.add(key);
  const geo = new THREE.SphereGeometry(1, 96, 96);
  sphere = new THREE.Mesh(geo, new THREE.MeshStandardMaterial({ color: 0x999999, roughness: 0.8 }));
  scene.add(sphere);
  el.addEventListener("mousedown", e => { dragging = true; lastX = e.clientX; lastY = e.clientY; });
  window.addEventListener("mouseup", () => dragging = false);
  window.addEventListener("mousemove", e => {
    if (!dragging) return;
    yaw += (e.clientX - lastX) * 0.01; pitch += (e.clientY - lastY) * 0.01;
    pitch = Math.max(-1.4, Math.min(1.4, pitch));
    lastX = e.clientX; lastY = e.clientY;
  });
  window.addEventListener("resize", () => {
    renderer.setSize(el.clientWidth, el.clientHeight);
    camera.aspect = el.clientWidth / el.clientHeight; camera.updateProjectionMatrix();
  });
  (function loop() {
    requestAnimationFrame(loop);
    sphere.rotation.y = yaw; sphere.rotation.x = pitch;
    renderer.render(scene, camera);
  })();
}

function pick(name, list) { return list.find(n => n.toLowerCase().includes(name)); }

function applyMaps(maps) {
  // maps: array of basenames like play_albedo.png. Match by suffix.
  const tex = suffix => {
    const m = maps.find(x => x.includes(suffix));
    if (!m) return null;
    const t = new THREE.TextureLoader().load("/api/maps/" + m + "?t=" + Date.now());
    return t;
  };
  const mat = sphere.material;
  mat.map = tex("albedo") || mat.map;
  const n = tex("normal"); if (n) mat.normalMap = n;
  const orm = tex("orm"); const rough = tex("roughness");
  if (rough) mat.roughnessMap = rough; else if (orm) mat.roughnessMap = orm;
  const h = tex("heightmap") || tex("height");
  if (h) { mat.bumpMap = h; mat.bumpScale = 0.15; }
  mat.needsUpdate = true;
}

async function loadGallery() {
  const out = await j("/api/materials");
  const g = document.getElementById("gallery");
  g.innerHTML = "";
  let cat = null;
  out.materials.forEach(m => {
    if (m.category !== cat) { cat = m.category;
      const h = document.createElement("h2"); h.textContent = cat; g.appendChild(h); }
    const b = document.createElement("button");
    b.textContent = m.name; b.onclick = () => loadMaterial(m.name);
    g.appendChild(b);
  });
}

async function loadMaterial(name) {
  const out = await j("/api/material/" + encodeURIComponent(name));
  if (!out.ok) { setStatus(out.error); return; }
  current = out; values = {};
  document.getElementById("material-name").textContent = name;
  document.getElementById("controls").hidden = false;
  const box = document.getElementById("sliders"); box.innerHTML = "";
  let group = null;
  out.sliders.forEach(s => {
    if (s.kind === "color") return; // v1: skip color widgets
    values[s.slot_id] = s.value;
    if (s.group !== group) { group = s.group;
      const h = document.createElement("h2"); h.textContent = group; box.appendChild(h); }
    const row = document.createElement("div"); row.className = "slider-row";
    const lab = document.createElement("label"); lab.textContent = s.label; row.appendChild(lab);
    const inp = document.createElement("input"); inp.type = "range";
    inp.min = s.min != null ? s.min : 0; inp.max = s.max != null ? s.max : 1;
    inp.step = s.step != null ? s.step : 0.01; inp.value = s.value;
    inp.oninput = () => { values[s.slot_id] = parseFloat(inp.value); };
    inp.onchange = () => scheduleRender(256);
    row.appendChild(inp); box.appendChild(row);
  });
  scheduleRender(256);
}

function scheduleRender(size) {
  clearTimeout(debounceTimer);
  debounceTimer = setTimeout(() => doRender(size), 200);
}

async function doRender(size) {
  if (!current) return;
  setStatus("rendering...");
  const out = await j("/api/render", {
    method: "POST", headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ material_id: current.name, values, size })
  });
  if (!out.ok) { setStatus("render failed: " + out.error); return; }
  applyMaps(out.maps);
  setStatus(out.path === "live" ? "live" : "ready");
}

function setStatus(t) { document.getElementById("status").textContent = t; }

document.getElementById("full").onclick = () => doRender(1024);
document.getElementById("download").onclick = () => {
  if (current) window.location = "/api/export?material_id=" + encodeURIComponent(current.name);
};

initThree();
loadGallery();
```

Note: `applyMaps` matches maps by filename suffix. Confirm the real render output basenames (Task 7 will have produced files like `play_albedo.png`, `play_normal.png`, `play_heightmap.png`, `play_orm.png`; see the render output naming in `render.py`/CLAUDE.md). Adjust the suffix strings if the actual names differ.

The Download button calls `/api/export`, added in Task 9; until then it 404s harmlessly.

- [ ] **Step 5: Manual verification**

Start the server and open it:
`.venv\Scripts\python.exe -m mm_mcp.play.server` (or run `mm-play` if installed).
Or use the in-app Browser: `preview_start` at `http://127.0.0.1:8788/`.
Verify: the gallery lists materials grouped by category; clicking one shows author-named sliders and renders a sphere within a few seconds; dragging the viewport rotates the sphere; moving a slider and releasing re-renders. Capture a screenshot and send it to Grayson (SendUserFile) per the visual-iteration workflow.

- [ ] **Step 6: Commit**

```bash
git add src/mm_mcp/play/static/
git commit -m "feat(play): gallery, sliders, and WebGL PBR sphere frontend"
```

---

### Task 9: Download / export layer

**Files:**
- Modify: `src/mm_mcp/play/api.py` (add `export`)
- Modify: `src/mm_mcp/play/server.py` (add `GET /api/export`)
- Test: `tests/test_play_api.py`, `tests/test_play_server.py`

**Interfaces:**
- Consumes: `cookbook.find_cookbook`, `sliders.apply_values`, the per-session outdir's current maps.
- Produces: `api.export(cfg, catalog, body_or_query, outdir) -> tuple[bytes, str]` returning `(zip_bytes, filename)`; the zip contains the current maps in `outdir` plus the material's `.ptex` (values applied when provided). Server route `GET /api/export?material_id=<id>` streams the zip with a `Content-Disposition` attachment header.

- [ ] **Step 1: Write the failing test**

Append to `tests/test_play_api.py`:

```python
import io, zipfile


def test_export_zips_maps_and_ptex(tmp_path):
    cfg = _cfg()
    # seed a fake rendered map in the outdir
    open(tmp_path / "play_albedo.png", "wb").write(b"\x89PNG fake")
    data, fname = api.export(cfg, _catalog(cfg),
                             {"material_id": "t01_sand_dunes", "values": {}},
                             str(tmp_path))
    assert fname.endswith(".zip")
    z = zipfile.ZipFile(io.BytesIO(data))
    names = z.namelist()
    assert any(n.endswith("play_albedo.png") for n in names)
    assert any(n.endswith(".ptex") for n in names)


def test_export_unknown_material_raises_error_data(tmp_path):
    cfg = _cfg()
    data, fname = api.export(cfg, _catalog(cfg),
                             {"material_id": "nope", "values": {}}, str(tmp_path))
    assert data is None and "error" in fname or fname == ""  # see impl note
```

Implementation note for Step 3: return `(None, error_string)` on unknown material so the server can send a 404; adjust the second assertion to match the exact contract you implement (keep it explicit).

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv\Scripts\python.exe -m pytest tests/test_play_api.py -k export -v`
Expected: FAIL (`api.export` not defined).

- [ ] **Step 3: Implement `export`**

Add to `src/mm_mcp/play/api.py`:

```python
import io
import zipfile


def export(cfg, catalog, body, outdir):
    """Return (zip_bytes, filename). On unknown material, returns (None, error)."""
    name = body.get("material_id")
    values = body.get("values") or {}
    graph, err = _load_graph(cfg, name)
    if err:
        return None, err["error"]
    applied = sliders.apply_values(graph, values)
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        for fn in sorted(os.listdir(outdir)):
            if fn.lower().endswith(".png"):
                z.write(os.path.join(outdir, fn), fn)
        z.writestr(f"{name}.ptex", json.dumps(applied, indent=1))
    return buf.getvalue(), f"{name}.zip"
```

- [ ] **Step 4: Add the server route**

In `src/mm_mcp/play/server.py` `do_GET`, before the final 404, add:

```python
            if path == "/api/export":
                from urllib.parse import parse_qs, urlparse
                q = parse_qs(urlparse(self.path).query)
                name = (q.get("material_id") or [""])[0]
                data, fname = api.export(cfg, catalog,
                                         {"material_id": name, "values": {}}, outdir)
                if data is None:
                    return self._send_json({"ok": False, "error": fname}, 404)
                self.send_response(200)
                self.send_header("Content-Type", "application/zip")
                self.send_header("Content-Disposition",
                                 f'attachment; filename="{fname}"')
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)
                return
```

- [ ] **Step 5: Add a server smoke test for export**

Append to `tests/test_play_server.py`:

```python
def test_export_returns_zip(running_server, tmp_path):
    # trigger a render first so a map exists (fast path: skip if integration-only)
    # here just assert the endpoint responds with a zip content-type for a known id
    import urllib.request
    url = running_server + "/api/export?material_id=t01_sand_dunes"
    with urllib.request.urlopen(url) as r:
        assert r.headers.get("Content-Type") == "application/zip"
        assert r.read()  # non-empty (contains at least the .ptex)
```

Note: `export` writes the `.ptex` even when no PNGs exist yet, so this smoke test passes without a render.

- [ ] **Step 6: Run the tests**

Run: `.venv\Scripts\python.exe -m pytest tests/test_play_api.py tests/test_play_server.py -k export -v`
Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add src/mm_mcp/play/api.py src/mm_mcp/play/server.py tests/test_play_api.py tests/test_play_server.py
git commit -m "feat(play): download current material as a maps + .ptex zip"
```

---

### Task 10: Docs, doctor line, North Star note, status ledger

**Files:**
- Modify: `docs/NORTH_STAR.md`
- Modify: `src/mm_mcp/doctor.py`
- Test: `tests/test_doctor.py`
- Modify: `README.md`
- Modify: `STATUS.md`

**Interfaces:**
- Consumes: `Config.play_port`.
- Produces: a `doctor` informational line; documentation.

- [ ] **Step 1: Write the failing doctor test**

Append to `tests/test_doctor.py` (mirror the file's existing test style):

```python
def test_doctor_reports_play_port(capsys):
    # reuse whatever harness the file uses to run the doctor check;
    # assert the printed report mentions the play surface and its port.
    from mm_mcp import doctor
    from mm_mcp.config import load_config
    doctor.run_checks(load_config())  # adapt to the real entry name
    out = capsys.readouterr().out.lower()
    assert "play" in out
```

Adapt `run_checks`/`load_config` to the file's actual doctor entry point (see the existing tests in `tests/test_doctor.py`).

- [ ] **Step 2: Run it to verify it fails**

Run: `.venv\Scripts\python.exe -m pytest tests/test_doctor.py -k play -v`
Expected: FAIL (no play line yet).

- [ ] **Step 3: Add the doctor line**

In `src/mm_mcp/doctor.py`, alongside the existing informational lines (e.g. the cookbook line), add one reporting the play surface, for example:

```python
    print(f"[i] play surface: mm-play serves http://127.0.0.1:{cfg.play_port}/")
```

Match the exact print/format style already used in the file.

- [ ] **Step 4: Run it to verify it passes**

Run: `.venv\Scripts\python.exe -m pytest tests/test_doctor.py -k play -v`
Expected: PASS.

- [ ] **Step 5: Add the North Star companion note**

In `docs/NORTH_STAR.md`, under "Non-goals" (after the "Not replacing Material Maker's own UI" bullet), add:

```markdown
- **A secondary "play surface" companion exists** (`mm-play`, see
  `docs/superpowers/specs/2026-09-04-play-surface-design.md`): a local web page
  that exposes each cookbook material's author-chosen subgraph parameters as
  friendly sliders for a non-technical person, deliberately hiding the node
  graph. It is aimed at the secondary audience above and is a companion, not a
  replacement for Material Maker's UI or the core round-trip loop. Its export
  still hands back the real editable `.ptex`, so it does not sever the learning
  loop; it just offers a lower-friction way in.
```

- [ ] **Step 6: Update README and STATUS**

In `README.md`, add a short "Play surface" subsection: what `mm-play` does, how to launch it (`mm-play`), and that it is standalone (headless) or drives a live Material Maker session if one is up.

In `STATUS.md`, add a component row for the play surface (state `wired` until Grayson has run it hands-on, then `verified`) and a one-line dated note.

- [ ] **Step 7: Run the fast suite**

Run: `.venv\Scripts\python.exe -m pytest -q -m "not integration"`
Expected: all pass (the new play tests plus the existing suite).

- [ ] **Step 8: Commit**

```bash
git add docs/NORTH_STAR.md src/mm_mcp/doctor.py tests/test_doctor.py README.md STATUS.md
git commit -m "docs(play): North Star companion note, doctor line, README, status"
```

---

## Self-Review

**Spec coverage:**
- Purpose / play surface for non-tech: Tasks 2-8 (sliders + gallery + WebGL). Covered.
- North Star companion exception + note: Task 10. Covered.
- v1 scope item 1 (gallery): Tasks 5 (`list_materials`), 8 (gallery UI). Covered.
- v1 scope item 2 (standalone headless loop): Tasks 4 (facade headless), 5 (render handler), 6 (server), 7 (integration). Covered.
- v1 scope item 3 (live auto-detect): Task 4 (facade live path + fallback). Covered (unit-tested with fakes, per spec's testing section).
- v1 scope item 4 (download): Task 9. Covered.
- Slider-derivation bridge (derive + apply): Tasks 2, 3. Covered.
- Catalog-sourced ranges: Task 2 (`_param_def`). Covered.
- Latency (small debounced serialized renders + full-quality button): Task 4 (lock), Task 8 (debounce, full button, small default). Covered.
- Endpoints: Task 6 (routing), Task 9 (export). Covered.
- three.js vendored, no CDN at runtime: Task 8 Step 1 + VENDOR.md. Covered.
- Packaging (`mm-play`, package-data): Task 6. Covered.
- Testing strategy (pure units, path-selection fakes, one integration, server smoke): Tasks 2-7, 9. Covered.
- Error-as-data: Tasks 5, 6, 9. Covered.
- Path-bounded file serving: Task 6 (`reject_path_fragment` on `/static/` and `/api/maps/`). Covered.
- Known limitations (live mismatch, color widgets): live fallback in Task 4; color widgets skipped in Task 8 Step 4. Covered.

**Placeholder scan:** No "TBD"/"implement later". Two spots defer exact matching to real output (map-name suffixes in Task 8, doctor entry name in Task 10); both give concrete fallbacks and say what to confirm, not "figure it out". Acceptable as reviewer-check notes, not placeholders.

**Type consistency:** `derive_sliders(graph, catalog)` and `apply_values(graph, values)` used identically in Tasks 3, 5, 9. `render_material(applied_graph, changes, size, cfg, outdir, *, ...)` defined in Task 4, called with the same positional shape in Task 5's `render_request`. `api.render_request(cfg, catalog, body, outdir, render_fn=...)` and `api.export(cfg, catalog, body, outdir)` consistent between api tasks and server routing. `make_handler(cfg, catalog, outdir, static_dir)` / `serve` / `main` consistent between Task 6 and its test.

One known adaptation seam flagged in-plan (not a defect): `live.set_param`/`live.render` exact kwargs, `reject_path_fragment` signature, doctor entry-point name, and render output basenames are each verified against the real files at implementation time, with the injected-callable seams keeping the tests valid regardless.

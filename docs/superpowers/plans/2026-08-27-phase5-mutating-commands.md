# Phase 5 Build Step 3: Mutating Commands Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add `add_node`/`connect_nodes`/`set_param`/`render` to the live-control
addon (`addons/mm_live/live_server.gd`) and to its Python client
(`src/mm_mcp/live.py`), so a scripted sequence of live calls can build a
two-node graph in a real running Material Maker window, wire it, tweak a
parameter, and render it — matching batch-rendered output.

**Architecture:** Same split as step 2 (`ping`/`get_graph`): the GDScript
addon stays deliberately thin (no validation, just "do what you're told"
against the live scene tree), while `live.py` runs every mutating call
through `graph.py`'s `validate_graph` against the current live graph state
*before* anything reaches the socket, exactly like the batch `render_graph`
tool already does. `render`'s freshness-detection reuses `render.py`'s own
`_collect_fresh_images` rather than reimplementing it.

**Tech Stack:** GDScript (Godot 4.7.1), Python 3.13, pytest.

**Spec:** [docs/superpowers/specs/2026-08-26-live-control-addon-design.md](../specs/2026-08-26-live-control-addon-design.md)
(see "Phases and gates," step 3, and "Feasibility verified" / "Still-open"
for the constraints this plan must respect).

## Global Constraints

- No source fork; the `z-Git\material-maker` checkout stays pristine forever.
- Turn-based collaboration only — no concurrency conflict resolution in v1.
- Single active tab — live tools always operate on whatever graph is
  currently focused in the GUI.
- `LIVE_PORT = 8765` is a hardcoded literal on both the GDScript and Python
  sides, no shared-constant mechanism — keep both in sync by hand (already
  established in step 2).
- The addon stays deliberately thin: **no validation logic in GDScript.**
  Every mutating call is validated Python-side via `graph.py`'s
  `validate_graph` before it is ever sent over the socket.
- `mm_globals.main_window` and `get_current_graph_edit()` must be resolved
  fresh inside every command handler, never cached (autoloads start before
  the main scene).
- Windows-only, like the rest of this project (STATUS.md Phase 4).
- No target date for Phase 5 (Grayson's explicit call in brainstorming).

## Verified against Material Maker source this session (new findings)

These are hard-won, source-grounded facts this plan depends on — not
assumptions carried over from the design spec's spike:

- **`create_nodes(data, position)` on `MMGraphEdit`** (`panels/graph_edit/graph_edit.gd:751`)
  is `await`-based, wraps a single `{type, parameters}` dict into
  `{nodes:[data], connections:[]}` internally, and returns an `Array` of the
  created `GraphNode`s (empty array on failure — e.g. an unknown type).
- **Node names can be silently renamed on creation.** `MMGenGraph.add_generator`
  (`addons/material_maker/engine/nodes/gen_graph.gd:196`) assigns
  `type+"_1"` when no name was given, and appends/increments a numeric
  suffix on any collision (`has_node(NodePath(name))` loop). The addon must
  **read back** the real name from the created node's `.generator.name`
  after `create_nodes` returns — never assume the caller's requested name
  (there usually isn't one) survived.
- **`do_connect_node(from, from_slot, to, to_slot)`** (`graph_edit.gd:464`)
  addresses **GraphNode names in the GraphEdit's own scene tree**, which are
  `"node_" + generator_name` (see `update_graph`, `graph_edit.gd:703`), NOT
  the plain generator name used everywhere else (`.ptex`, `get_graph`'s
  serialized shape, `set_node_parameters`). The addon must prefix `"node_"`
  when calling it and use the plain name in the wire protocol.
- **`set_node_parameters(node, parameters)`** (`graph_edit.gd:1429`) despite
  its parameter name actually takes a **generator** (`MMGenBase`), not a
  GraphNode — confirmed because it calls `node.get_hier_name()` /
  `node.get_parameter()` / `node.set_parameter()`, all defined on
  `MMGenBase` (`gen_base.gd:237,331,362`), and the GraphNode wrapper class
  (`MMGraphNodeMinimal`, `nodes/minimal.gd`) defines none of them. Resolve
  the generator via `graph_edit.generator.get_node(NodePath(name))` (the
  `generator` tree is addressed by plain names, confirmed by
  `loader.gd:235`'s identical `gen_graph.get_node(NodePath(c.from))`).
- **CORRECTED during Task 6's integration test (this citation was wrong as
  originally written; see the plan's SDD ledger for the full trail):**
  `main_window.export_material(prefix, profile)` (`material_maker/main_window.gd:517`)
  is NOT safely awaitable from a script. Its own body has no `await` at all,
  it calls `project.export_material(export_prefix, profile)` (a real coroutine,
  `graph_edit.gd:921`) WITHOUT awaiting it, so `main_window.export_material`
  itself is not a coroutine. Awaiting it resolves same-frame while the real
  file-writing work keeps running in the background on its own schedule,
  confirmed empirically (a render reported failure immediately, then the
  expected PNG appeared on disk about 10 seconds later, unobserved).
  **The correct entry point is `graph_edit.get_material_node()`
  (`graph_edit.gd:915-919`) then `material_node.export_material(prefix, profile,
  0, true)`.** This is `gen_material.gd:650` directly, the function
  `graph_edit.export_material` itself awaits first, so awaiting it ourselves is
  a real wait. The 4th param `command_line=true` also matters: it gates an
  interactive overwrite-confirmation dialog (`gen_material.gd:683`) that would
  otherwise await user input forever inside a socket-driven command,
  `command_line=true` is the same flag the already-proven `--export-material`
  CLI path uses. Output naming (`<prefix>_albedo.png` etc., confirmed via
  `gen_material.gd:657-659`'s `$(path_prefix)`/`$(file_prefix)` substitution)
  matches `render.py`'s own CLI export convention exactly, so `render.py`'s
  `_collect_fresh_images` can be reused verbatim.
- **`export_material` has no failure signal the addon can check.** It's a
  `void`-returning coroutine with no return value and no exception on a bad
  profile/export step. The addon can only report "I awaited it, nothing
  crashed" — real success is Python's job to verify, by checking for fresh
  files on disk exactly like `render.py` already does for the batch path.
  Documenting this honestly rather than pretending the addon can detect
  export failure.

## Task 1: GDScript addon — async dispatch + `add_node`

**Files:**
- Modify: `addons/mm_live/live_server.gd`

**Interfaces:**
- Consumes: `mm_globals.main_window` (existing, from step 2), `MMGraphEdit.create_nodes(data: Dictionary, position: Vector2) -> Array` (real MM API, verified above).
- Produces: wire command `{"cmd": "add_node", "type": <String>, "parameters": <Dictionary>, "x": <float>, "y": <float>}` → `{"ok": true, "name": <String>}` or `{"ok": false, "error": <String>}`. Task 4's Python client depends on the `"name"` key being the authoritative post-creation generator name.

There is no automated GDScript test harness in this repo (true for steps 1
and 2 too — see HANDOFF.md). This handler is verified end-to-end by Task 6's
integration test. The steps below are still bite-sized and independently
committable.

- [ ] **Step 1: Add the `_cmd_add_node` handler**

Add this function to `addons/mm_live/live_server.gd` (anywhere after
`_cmd_get_graph`):

```gdscript
func _cmd_add_node(cmd: Dictionary) -> Dictionary:
	if mm_globals.main_window == null:
		return {"ok": false, "error": "main_window not ready"}
	var graph_edit: MMGraphEdit = mm_globals.main_window.get_current_graph_edit()
	if graph_edit == null or graph_edit.generator == null:
		return {"ok": false, "error": "no active graph"}
	var node_type = cmd.get("type")
	if typeof(node_type) != TYPE_STRING or node_type.is_empty():
		return {"ok": false, "error": "add_node requires a non-empty 'type' string"}
	var position := Vector2(float(cmd.get("x", 0)), float(cmd.get("y", 0)))
	var data := {"type": node_type, "parameters": cmd.get("parameters", {})}
	var created: Array = await graph_edit.create_nodes(data, position)
	if created.is_empty():
		return {"ok": false, "error": "Material Maker rejected node type '%s'" % node_type}
	# create_nodes may rename the node on a collision (see gen_graph.gd's
	# add_generator -- it uniquifies the name), so the authoritative name is
	# read back off the created node's generator, never assumed to match
	# the caller's request (there usually isn't a requested name at all).
	return {"ok": true, "name": created[0].generator.name}
```

- [ ] **Step 2: Wire it into `_dispatch`**

In `_dispatch`'s `match parsed["cmd"]:` block, add a case (this makes
`_dispatch` itself a coroutine — Godot allows calling it without `await`
from `_process()`, same as before: it runs until the first suspension
point, then resumes and writes the response later, without blocking
`_process()`'s per-frame loop):

```gdscript
			"add_node":
				response = await _cmd_add_node(parsed)
```

- [ ] **Step 3: Update the file header comment**

Change the comment block at the top of the file from:

```gdscript
## This step only implements "ping" and "get_graph". Mutating commands
## (add_node/connect_nodes/set_param/render) are Phase 5 build step 3.
```

to:

```gdscript
## Mutating commands (add_node/connect_nodes/set_param/render) were added in
## Phase 5 build step 3. See docs/superpowers/plans/2026-08-27-phase5-mutating-commands.md
## for the source citations behind each handler's Godot API calls.
```

- [ ] **Step 4: Manual sanity check (optional, no automated harness)**

If you want an earlier signal than Task 6's integration test, you can drive
this by hand from a Python REPL in the repo root (adjust the path if your
venv differs):

```bash
.venv\Scripts\python.exe -c "from mm_mcp.live import connect_or_launch, _send_command; s = connect_or_launch(); print(_send_command({'cmd': 'add_node', 'type': 'perlin', 'parameters': {}, 'x': 0, 'y': 0})); s.close()"
```

Expected: `LiveResult(ok=True, data={'ok': True, 'name': 'perlin_1'}, error=None)`
and a new Perlin node visibly appears in the launched Material Maker window.
This is a manual check, not a plan step to automate — skip it if you'd
rather rely on Task 6 alone.

- [ ] **Step 5: Commit**

```bash
git add addons/mm_live/live_server.gd
git commit -m "feat(live): add async add_node command to the live-control addon"
```

## Task 2: GDScript addon — `connect_nodes` + `set_param`

**Files:**
- Modify: `addons/mm_live/live_server.gd`

**Interfaces:**
- Consumes: `MMGraphEdit.do_connect_node(from: String, from_slot: int, to: String, to_slot: int) -> bool` and `MMGraphEdit.set_node_parameters(node, parameters: Dictionary) -> void` (both real MM API, verified above; `node` here is a generator, not a GraphNode).
- Produces: wire commands `{"cmd": "connect_nodes", "from": <String>, "from_port": <int>, "to": <String>, "to_port": <int>}` → `{"ok": true}` / `{"ok": false, "error": ...}`; `{"cmd": "set_param", "name": <String>, "parameters": <Dictionary>}` → `{"ok": true}` / `{"ok": false, "error": ...}`. Both `from`/`to`/`name` are plain generator names, matching `get_graph`'s serialized shape — the handlers do the `"node_"` prefixing internally for `do_connect_node`.

Both handlers are synchronous (no `await` needed — neither `do_connect_node`
nor `set_node_parameters` is coroutine-based), unlike Task 1's `add_node`.

- [ ] **Step 1: Add the `_cmd_connect_nodes` and `_cmd_set_param` handlers**

```gdscript
func _cmd_connect_nodes(cmd: Dictionary) -> Dictionary:
	if mm_globals.main_window == null:
		return {"ok": false, "error": "main_window not ready"}
	var graph_edit: MMGraphEdit = mm_globals.main_window.get_current_graph_edit()
	if graph_edit == null or graph_edit.generator == null:
		return {"ok": false, "error": "no active graph"}
	var from_name = str(cmd.get("from"))
	var to_name = str(cmd.get("to"))
	var from_node_name := "node_" + from_name
	var to_node_name := "node_" + to_name
	if not graph_edit.has_node(from_node_name):
		return {"ok": false, "error": "no node named '%s' in the live graph" % from_name}
	if not graph_edit.has_node(to_node_name):
		return {"ok": false, "error": "no node named '%s' in the live graph" % to_name}
	var connected: bool = graph_edit.do_connect_node(
			from_node_name, int(cmd.get("from_port", 0)),
			to_node_name, int(cmd.get("to_port", 0)))
	if not connected:
		return {"ok": false, "error": "Material Maker refused the connection (incompatible ports?)"}
	return {"ok": true}


func _cmd_set_param(cmd: Dictionary) -> Dictionary:
	if mm_globals.main_window == null:
		return {"ok": false, "error": "main_window not ready"}
	var graph_edit: MMGraphEdit = mm_globals.main_window.get_current_graph_edit()
	if graph_edit == null or graph_edit.generator == null:
		return {"ok": false, "error": "no active graph"}
	var node_name := str(cmd.get("name"))
	var node_path := NodePath(node_name)
	if not graph_edit.generator.has_node(node_path):
		return {"ok": false, "error": "no node named '%s' in the live graph" % node_name}
	var target = graph_edit.generator.get_node(node_path)
	graph_edit.set_node_parameters(target, cmd.get("parameters", {}))
	return {"ok": true}
```

- [ ] **Step 2: Wire both into `_dispatch`**

```gdscript
			"connect_nodes":
				response = _cmd_connect_nodes(parsed)
			"set_param":
				response = _cmd_set_param(parsed)
```

- [ ] **Step 3: Manual sanity check (optional)**

Same pattern as Task 1's Step 4, e.g. after adding two nodes by hand:

```bash
.venv\Scripts\python.exe -c "from mm_mcp.live import _send_command; print(_send_command({'cmd': 'connect_nodes', 'from': 'perlin_1', 'from_port': 0, 'to': 'warp_1', 'to_port': 0}))"
```

- [ ] **Step 4: Commit**

```bash
git add addons/mm_live/live_server.gd
git commit -m "feat(live): add connect_nodes and set_param commands to the live-control addon"
```

## Task 3: GDScript addon — `render`

**Files:**
- Modify: `addons/mm_live/live_server.gd`

**Interfaces:**
- Consumes: `graph_edit.get_material_node()` (`graph_edit.gd:915-919`) then `material_node.export_material(prefix, profile, 0, true)` (`gen_material.gd:650`) — genuinely `await`-based (unlike `main_window.export_material`, see the AMENDMENT below and the corrected citation above); no failure signal.
- Produces: wire command `{"cmd": "render", "prefix": <String>, "profile": <String>}` → `{"ok": true}` / `{"ok": false, "error": ...}`. `{"ok": true}` here means only "the export coroutine completed without a null-graph guard tripping" — Task 5's Python client is responsible for verifying files actually appeared, per the "no failure signal" finding above.

- [ ] **Step 1: Add the `_cmd_render` handler**

```gdscript
func _cmd_render(cmd: Dictionary) -> Dictionary:
	if mm_globals.main_window == null:
		return {"ok": false, "error": "main_window not ready"}
	var graph_edit: MMGraphEdit = mm_globals.main_window.get_current_graph_edit()
	if graph_edit == null or graph_edit.generator == null:
		return {"ok": false, "error": "no active graph"}
	var prefix := str(cmd.get("prefix", ""))
	var profile := str(cmd.get("profile", "Godot/Godot 4 Standard"))
	if prefix.is_empty():
		return {"ok": false, "error": "render requires a non-empty 'prefix'"}
	# main_window.export_material awaits graph_edit.export_material internally
	# (main_window.gd:517 -> graph_edit.gd:921), which itself awaits the
	# material node's own export_material (gen_material.gd:650) -- awaiting
	# here is required, or this handler replies before Godot finishes
	# writing the PNGs. export_material has no failure return value; Python
	# verifies success by checking for fresh files on disk.
	await mm_globals.main_window.export_material(prefix, profile)
	return {"ok": true}
```

- [ ] **Step 2: Wire it into `_dispatch`**

```gdscript
			"render":
				response = await _cmd_render(parsed)
```

- [ ] **Step 3: Manual sanity check (optional)**

```bash
.venv\Scripts\python.exe -c "from mm_mcp.live import _send_command; print(_send_command({'cmd': 'render', 'prefix': 'C:/temp/live_smoke', 'profile': 'Godot/Godot 4 Standard'}, timeout=30.0))"
```

Expected: `{"ok": true}` plus `C:\temp\live_smoke_albedo.png` (etc.) appearing
on disk within a few seconds.

- [ ] **Step 4: Commit**

```bash
git add addons/mm_live/live_server.gd
git commit -m "feat(live): add render command to the live-control addon"
```

### AMENDMENT (found during Task 6's integration test, fixed via a Task 6 fix round)

The `_cmd_render` above shipped and passed task review, but `main_window.export_material`
turned out not to be safely awaitable (see "Verified against Material Maker
source" above, corrected entry). It reports `{"ok": true}` before the real
file-writing coroutine has actually run, confirmed empirically: a render
reported failure, then the expected PNG appeared on disk about 10 seconds
later. The fix, applied and verified against a real Godot launch:

```gdscript
func _cmd_render(cmd: Dictionary) -> Dictionary:
	if mm_globals.main_window == null:
		return {"ok": false, "error": "main_window not ready"}
	var graph_edit: MMGraphEdit = mm_globals.main_window.get_current_graph_edit()
	if graph_edit == null or graph_edit.generator == null:
		return {"ok": false, "error": "no active graph"}
	var prefix := str(cmd.get("prefix", ""))
	var profile := str(cmd.get("profile", "Godot/Godot 4 Standard"))
	if prefix.is_empty():
		return {"ok": false, "error": "render requires a non-empty 'prefix'"}
	var material_node = graph_edit.get_material_node()
	if material_node == null:
		return {"ok": false, "error": "no material node in the active graph"}
	# Call the material node's own export_material directly (gen_material.gd:650)
	# rather than main_window.export_material, which forwards to
	# graph_edit.export_material WITHOUT awaiting it -- so awaiting THAT call
	# resolves same-frame while the real file-writing coroutine keeps running
	# in the background, unobserved (confirmed empirically). command_line=true
	# (gen_material.gd's 4th param) skips the interactive overwrite dialog,
	# which would otherwise await user input forever inside this socket-driven
	# command -- the same flag the proven --export-material CLI path uses.
	await material_node.export_material(prefix, profile, 0, true)
	return {"ok": true}
```

## Task 4: `live.py` — `add_node` / `connect_nodes` / `set_param` client methods

**Files:**
- Modify: `src/mm_mcp/live.py`
- Test: `tests/test_live.py`

**Interfaces:**
- Consumes: `_send_command` (existing), `get_graph` (existing), `mm_mcp.catalog_builder.build_catalog(nodes_dir: str) -> dict`, `mm_mcp.validator.validate_graph(ptex: dict, catalog: dict) -> list[dict]` (both existing, unmodified).
- Produces: `add_node(node_type: str, parameters: dict | None = None, x: float = 0.0, y: float = 0.0, cfg=None, host=LIVE_HOST, port=LIVE_PORT, timeout=5.0) -> LiveResult` (success `data={"name": <str>}`); `connect_nodes(from_name: str, from_port: int, to_name: str, to_port: int, cfg=None, host=..., port=..., timeout=5.0) -> LiveResult`; `set_param(name: str, parameters: dict, cfg=None, host=..., port=..., timeout=5.0) -> LiveResult`. On validation failure, all three return `LiveResult(ok=False, error="validation failed", data={"problems": [...]})` **without contacting the socket**. Task 6 depends on `add_node`'s `data["name"]` and on all three accepting `cfg=` to target an isolated overlay.

A brand-new node has no connections yet, so `add_node` validates the new
node's type/parameters in isolation rather than merging into the fetched
live graph (there's nothing `validate_graph` checks about a lone,
unconnected node that the live graph's other nodes would affect).
`connect_nodes`/`set_param` do need the live graph, since connection and
parameter validation depend on the referenced nodes' real types.

- [ ] **Step 1: Write the failing tests**

Add to `tests/test_live.py` (after the existing `ping`/`get_graph` tests, before the `_FakeProcess` section — keep the fake-server style already established in this file):

```python
_FAKE_CATALOG = {
    "perlin": {"type": "perlin", "inputs": [], "outputs": [{"type": "f"}],
               "parameters": [{"name": "scale_x", "type": "float",
                               "min": 1, "max": 32, "default": 4}]},
    "warp": {"type": "warp", "inputs": [{"name": "in"}, {"name": "deform"}],
             "outputs": [{"type": "f"}], "parameters": []},
}


def test_add_node_sends_command_when_type_is_valid(monkeypatch):
    monkeypatch.setattr(live, "_ensure_catalog", lambda cfg: _FAKE_CATALOG)
    received = {}

    def responder(cmd):
        received.update(cmd)
        return {"ok": True, "name": "perlin_1"}

    server = _FakeLiveServer(responder)
    try:
        result = live.add_node("perlin", {"scale_x": 8}, x=10, y=20,
                                cfg=cfg, host="127.0.0.1", port=server.port)
        assert result.ok
        assert result.data["name"] == "perlin_1"
        assert received == {"cmd": "add_node", "type": "perlin",
                             "parameters": {"scale_x": 8}, "x": 10, "y": 20}
    finally:
        server.stop()


def test_add_node_rejects_unknown_type_without_contacting_server(monkeypatch):
    monkeypatch.setattr(live, "_ensure_catalog", lambda cfg: _FAKE_CATALOG)
    contacted = {"called": False}

    def responder(cmd):
        contacted["called"] = True
        return {"ok": True}

    server = _FakeLiveServer(responder)
    try:
        result = live.add_node("totally_bogus_type", {}, cfg=cfg,
                                host="127.0.0.1", port=server.port)
        assert not result.ok
        assert result.error == "validation failed"
        assert result.data["problems"]
        assert contacted["called"] is False
    finally:
        server.stop()


def test_connect_nodes_sends_command_when_ports_are_compatible(monkeypatch):
    monkeypatch.setattr(live, "_ensure_catalog", lambda cfg: _FAKE_CATALOG)
    fake_graph = {"nodes": [
        {"name": "perlin_1", "type": "perlin", "node_position": {"x": 0, "y": 0}, "parameters": {}},
        {"name": "warp_1", "type": "warp", "node_position": {"x": 0, "y": 0}, "parameters": {}},
    ], "connections": []}
    received = {}

    def responder(cmd):
        if cmd["cmd"] == "get_graph":
            return {"ok": True, "graph": fake_graph}
        received.update(cmd)
        return {"ok": True}

    server = _FakeLiveServer(responder)
    try:
        result = live.connect_nodes("perlin_1", 0, "warp_1", 0,
                                     cfg=cfg, host="127.0.0.1", port=server.port)
        assert result.ok
        assert received == {"cmd": "connect_nodes", "from": "perlin_1", "from_port": 0,
                             "to": "warp_1", "to_port": 0}
    finally:
        server.stop()


def test_connect_nodes_rejects_out_of_range_port_without_contacting_server(monkeypatch):
    monkeypatch.setattr(live, "_ensure_catalog", lambda cfg: _FAKE_CATALOG)
    fake_graph = {"nodes": [
        {"name": "perlin_1", "type": "perlin", "node_position": {"x": 0, "y": 0}, "parameters": {}},
        {"name": "warp_1", "type": "warp", "node_position": {"x": 0, "y": 0}, "parameters": {}},
    ], "connections": []}
    calls = []

    def responder(cmd):
        calls.append(cmd["cmd"])
        return {"ok": True, "graph": fake_graph}

    server = _FakeLiveServer(responder)
    try:
        result = live.connect_nodes("perlin_1", 0, "warp_1", 5,  # warp only has 2 inputs
                                     cfg=cfg, host="127.0.0.1", port=server.port)
        assert not result.ok
        assert result.error == "validation failed"
        assert calls == ["get_graph"]  # connect_nodes was never sent
    finally:
        server.stop()


def test_set_param_sends_command_for_existing_node(monkeypatch):
    monkeypatch.setattr(live, "_ensure_catalog", lambda cfg: _FAKE_CATALOG)
    fake_graph = {"nodes": [
        {"name": "perlin_1", "type": "perlin", "node_position": {"x": 0, "y": 0},
         "parameters": {"scale_x": 4}},
    ], "connections": []}
    received = {}

    def responder(cmd):
        if cmd["cmd"] == "get_graph":
            return {"ok": True, "graph": fake_graph}
        received.update(cmd)
        return {"ok": True}

    server = _FakeLiveServer(responder)
    try:
        result = live.set_param("perlin_1", {"scale_x": 16},
                                 cfg=cfg, host="127.0.0.1", port=server.port)
        assert result.ok
        assert received == {"cmd": "set_param", "name": "perlin_1", "parameters": {"scale_x": 16}}
    finally:
        server.stop()


def test_set_param_reports_missing_node_without_contacting_server(monkeypatch):
    monkeypatch.setattr(live, "_ensure_catalog", lambda cfg: _FAKE_CATALOG)
    fake_graph = {"nodes": [], "connections": []}
    calls = []

    def responder(cmd):
        calls.append(cmd["cmd"])
        return {"ok": True, "graph": fake_graph}

    server = _FakeLiveServer(responder)
    try:
        result = live.set_param("does_not_exist", {"scale_x": 16},
                                 cfg=cfg, host="127.0.0.1", port=server.port)
        assert not result.ok
        assert "does_not_exist" in result.error
        assert calls == ["get_graph"]
    finally:
        server.stop()
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv\Scripts\python.exe -m pytest tests/test_live.py -k "add_node or connect_nodes or set_param" -v`
Expected: FAIL with `AttributeError: module 'mm_mcp.live' has no attribute 'add_node'` (and similarly for the others) — none of these functions exist yet.

- [ ] **Step 3: Implement `add_node`/`connect_nodes`/`set_param`**

Add to `src/mm_mcp/live.py`. First, add two new imports at the top of the
file alongside the existing ones:

```python
from mm_mcp.catalog_builder import build_catalog
from mm_mcp.validator import validate_graph
```

Then add this module-level cache and helper, plus the three client
functions, after the existing `get_graph` function:

```python
_catalog_cache: dict[str, dict] = {}


def _ensure_catalog(cfg: Config) -> dict:
    catalog = _catalog_cache.get(cfg.nodes_dir)
    if catalog is None:
        catalog = build_catalog(cfg.nodes_dir)
        _catalog_cache[cfg.nodes_dir] = catalog
    return catalog


def _validation_errors(ptex: dict, cfg: Config) -> list[dict]:
    problems = validate_graph(ptex, _ensure_catalog(cfg))
    return [p for p in problems if p["severity"] == "error"]


def add_node(node_type: str, parameters: dict | None = None, x: float = 0.0, y: float = 0.0,
             cfg: Config | None = None, host: str = LIVE_HOST, port: int = LIVE_PORT,
             timeout: float = 5.0) -> LiveResult:
    """Validate node_type/parameters against the catalog in isolation (a
    brand-new, unconnected node has no effect on the rest of the live
    graph), then send add_node if valid. On success, LiveResult.data["name"]
    is the node's real post-creation name -- Material Maker may rename it
    on a collision, so never assume it matches node_type."""
    cfg = cfg or load_config()
    parameters = parameters or {}
    proposed = {"nodes": [{"name": "_new", "type": node_type,
                            "node_position": {"x": x, "y": y}, "parameters": parameters}],
                "connections": []}
    errors = _validation_errors(proposed, cfg)
    if errors:
        return LiveResult(ok=False, error="validation failed", data={"problems": errors})
    return _send_command({"cmd": "add_node", "type": node_type, "parameters": parameters,
                           "x": x, "y": y}, host, port, timeout)


def connect_nodes(from_name: str, from_port: int, to_name: str, to_port: int,
                   cfg: Config | None = None, host: str = LIVE_HOST, port: int = LIVE_PORT,
                   timeout: float = 5.0) -> LiveResult:
    """Fetch the current live graph, validate the proposed connection
    against it, and only send connect_nodes if that validation is clean."""
    cfg = cfg or load_config()
    current = get_graph(host, port, timeout)
    if not current.ok:
        return current
    graph = current.data["graph"]
    proposed = {"nodes": graph.get("nodes", []),
                "connections": graph.get("connections", []) +
                               [{"from": from_name, "from_port": from_port,
                                 "to": to_name, "to_port": to_port}]}
    errors = _validation_errors(proposed, cfg)
    if errors:
        return LiveResult(ok=False, error="validation failed", data={"problems": errors})
    return _send_command({"cmd": "connect_nodes", "from": from_name, "from_port": from_port,
                           "to": to_name, "to_port": to_port}, host, port, timeout)


def set_param(name: str, parameters: dict, cfg: Config | None = None, host: str = LIVE_HOST,
              port: int = LIVE_PORT, timeout: float = 5.0) -> LiveResult:
    """Fetch the current live graph, confirm the target node exists, merge
    the proposed parameters into a copy of its current ones, validate that,
    and only send set_param if clean."""
    cfg = cfg or load_config()
    current = get_graph(host, port, timeout)
    if not current.ok:
        return current
    graph = current.data["graph"]
    nodes = graph.get("nodes", [])
    target = next((n for n in nodes if n.get("name") == name), None)
    if target is None:
        return LiveResult(ok=False, error=f"no node named '{name}' in the current live graph")
    merged_nodes = [
        {**n, "parameters": {**n.get("parameters", {}), **parameters}} if n is target else n
        for n in nodes
    ]
    proposed = {"nodes": merged_nodes, "connections": graph.get("connections", [])}
    errors = _validation_errors(proposed, cfg)
    if errors:
        return LiveResult(ok=False, error="validation failed", data={"problems": errors})
    return _send_command({"cmd": "set_param", "name": name, "parameters": parameters},
                          host, port, timeout)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `.venv\Scripts\python.exe -m pytest tests/test_live.py -k "add_node or connect_nodes or set_param" -v`
Expected: PASS (6 tests).

- [ ] **Step 5: Run the full fast suite to check for regressions**

Run: `.venv\Scripts\python.exe -m pytest -q -m "not integration"`
Expected: all pass (148 + 6 new = 154).

- [ ] **Step 6: Commit**

```bash
git add src/mm_mcp/live.py tests/test_live.py
git commit -m "feat(live): add validated add_node/connect_nodes/set_param to the live.py client"
```

## Task 5: `live.py` — `render` client method

**Files:**
- Modify: `src/mm_mcp/live.py`
- Test: `tests/test_live.py`

**Interfaces:**
- Consumes: `_send_command` (existing), `mm_mcp.render.RenderResult` and `mm_mcp.render._collect_fresh_images` (both existing, unmodified — reused rather than reimplemented, matching this codebase's DRY convention).
- Produces: `render(basename: str = "material", profile: str = "Godot/Godot 4 Standard", cfg=None, host=..., port=..., timeout=60.0) -> RenderResult`. Task 6 depends on `.ok` and `.images` (a list of absolute PNG paths).

No validation step here — `render` doesn't mutate the graph, it exports
whatever is currently there. `timeout` defaults higher than the other
mutating calls (5.0) since an export can legitimately take longer than a
`ping`; this is a pragmatic default for this step, not a tuned value — if
real renders prove slower, raise it, a known/deferred risk, not a bug.

- [ ] **Step 1: Write the failing tests**

Add to `tests/test_live.py`:

```python
def test_render_returns_fresh_images_on_success(tmp_path):
    isolated_cfg = replace(cfg, output_dir=str(tmp_path))

    def responder(cmd):
        assert cmd["cmd"] == "render"
        # Simulate Godot writing the exported PNGs before the addon replies.
        (tmp_path / "material_albedo.png").write_bytes(b"fake png bytes")
        (tmp_path / "material_normal.png").write_bytes(b"fake png bytes")
        return {"ok": True}

    server = _FakeLiveServer(responder)
    try:
        result = live.render(basename="material", cfg=isolated_cfg,
                              host="127.0.0.1", port=server.port)
        assert result.ok
        assert len(result.images) == 2
    finally:
        server.stop()


def test_render_reports_no_output_when_no_files_appear(tmp_path):
    isolated_cfg = replace(cfg, output_dir=str(tmp_path))
    server = _FakeLiveServer(lambda cmd: {"ok": True})
    try:
        result = live.render(basename="material", cfg=isolated_cfg,
                              host="127.0.0.1", port=server.port)
        assert not result.ok
        assert "no png" in result.error.lower()
    finally:
        server.stop()


def test_render_propagates_server_side_failure(tmp_path):
    isolated_cfg = replace(cfg, output_dir=str(tmp_path))
    server = _FakeLiveServer(lambda cmd: {"ok": False, "error": "main_window not ready"})
    try:
        result = live.render(basename="material", cfg=isolated_cfg,
                              host="127.0.0.1", port=server.port)
        assert not result.ok
        assert result.error == "main_window not ready"
    finally:
        server.stop()
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv\Scripts\python.exe -m pytest tests/test_live.py -k render -v`
Expected: FAIL with `AttributeError: module 'mm_mcp.live' has no attribute 'render'`.

- [ ] **Step 3: Implement `render`**

Add this import to `src/mm_mcp/live.py`'s top-of-file imports:

```python
from mm_mcp.render import RenderResult, _collect_fresh_images
```

Then add the function after `set_param`:

```python
def render(basename: str = "material", profile: str = "Godot/Godot 4 Standard",
           cfg: Config | None = None, host: str = LIVE_HOST, port: int = LIVE_PORT,
           timeout: float = 60.0) -> RenderResult:
    """Trigger a live-window export via the addon's render command, then
    verify success the same way render.py's batch path does: by checking
    for fresh <basename>_*.png files on disk, since export_material has no
    failure signal of its own to report over the socket."""
    cfg = cfg or load_config()
    outdir = cfg.output_dir
    os.makedirs(outdir, exist_ok=True)
    before = {}
    for fn in os.listdir(outdir):
        if fn.startswith(basename + "_") and fn.lower().endswith(".png"):
            full = os.path.join(outdir, fn)
            try:
                before[fn] = os.path.getmtime(full)
            except (OSError, FileNotFoundError):
                pass
    prefix = os.path.join(outdir, basename)
    result = _send_command({"cmd": "render", "prefix": prefix, "profile": profile},
                            host, port, timeout)
    if not result.ok:
        return RenderResult(ok=False, error=result.error)
    images = _collect_fresh_images(outdir, basename, before)
    if not images:
        return RenderResult(ok=False, error="no PNG output produced by live render")
    return RenderResult(ok=True, images=images)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `.venv\Scripts\python.exe -m pytest tests/test_live.py -k render -v`
Expected: PASS (3 tests).

- [ ] **Step 5: Run the full fast suite to check for regressions**

Run: `.venv\Scripts\python.exe -m pytest -q -m "not integration"`
Expected: all pass (154 + 3 new = 157).

- [ ] **Step 6: Commit**

```bash
git add src/mm_mcp/live.py tests/test_live.py
git commit -m "feat(live): add render to the live.py client, reusing render.py's freshness check"
```

## Task 6: Real integration test — scripted build-and-render sequence

**Files:**
- Test: `tests/test_live.py`

**Interfaces:**
- Consumes: everything from Tasks 1-5 (`connect_or_launch`, `add_node`, `connect_nodes`, `set_param`, `get_graph`, `render`), plus the existing `connect_or_launch` from step 2.
- Produces: nothing new — this is the plan's own gate, verbatim from the spec: "a scripted sequence of live ops visibly builds a simple graph in a real running window and renders it."

This launches a real, visible Godot window (like the existing
`test_connect_or_launch_gets_real_graph_from_default_new_material`), so it's
marked `@pytest.mark.integration` and excluded from the fast suite.

- [ ] **Step 1: Write the integration test**

Add to `tests/test_live.py`, after the existing integration test:

```python
@pytest.mark.integration
def test_live_ops_build_and_render_a_simple_graph(tmp_path):
    # Isolated overlay + output dirs so this test never collides with (or
    # clobbers) a manual session's overlay or output files.
    isolated_cfg = replace(cfg, live_overlay_dir=str(tmp_path / "mm_live_overlay"),
                            output_dir=str(tmp_path / "output"))
    session = live.connect_or_launch(cfg=isolated_cfg, launch_timeout=90.0)
    try:
        assert session.ok, session.error
        assert session.process is not None, (
            "attached to a pre-existing instance on port 8765 -- close it and rerun; "
            "this test must launch its own overlay to prove the committed addon works"
        )

        added_source = live.add_node("perlin", {}, x=0, y=0, cfg=isolated_cfg)
        assert added_source.ok, added_source.error
        source_name = added_source.data["name"]

        # colorize, not warp: colorize's input port 0 (type f) matches
        # perlin's output (type f) exactly, and its output (type rgba) is a
        # safe, standard fit for Material's albedo_tex (type rgb). warp's
        # input port 0 is type rgba, an f->rgba mismatch that validate_graph
        # and Godot's connect_children() both accept (neither checks port
        # *type* compatibility, only index range) but that silently breaks
        # export once the edge is actually evaluated -- confirmed empirically
        # in this same task's first fix round (see the plan's ledger).
        added_sink = live.add_node("colorize", {}, x=200, y=0, cfg=isolated_cfg)
        assert added_sink.ok, added_sink.error
        sink_name = added_sink.data["name"]

        connected = live.connect_nodes(source_name, 0, sink_name, 0, cfg=isolated_cfg)
        assert connected.ok, connected.error

        # Wire the chain into the default new-material graph's pre-existing
        # "Material" node (its literal name, per graph_edit.gd:714's
        # new_material() default) so the export profile's per-file
        # `conditions: "$(connected:albedo_tex)"` gate (material.mmg,
        # gen_material.gd:667-676) actually evaluates true -- an unconnected
        # chain produces zero PNGs no matter how correct render() is.
        # albedo_tex is input port 0 on "material" (material.mmg's
        # shader_model.inputs[0]).
        wired = live.connect_nodes(sink_name, 0, "Material", 0, cfg=isolated_cfg)
        assert wired.ok, wired.error

        param_result = live.set_param(source_name, {"scale_x": 16}, cfg=isolated_cfg)
        assert param_result.ok, param_result.error

        graph_after = live.get_graph()
        assert graph_after.ok, graph_after.error
        node_names = {n["name"] for n in graph_after.data["graph"]["nodes"]}
        assert {source_name, sink_name} <= node_names, (
            f"expected {source_name!r} and {sink_name!r} in {node_names}"
        )
        connections = graph_after.data["graph"]["connections"]
        assert any(c["from"] == source_name and c["to"] == sink_name for c in connections), (
            f"expected a connection {source_name}->{sink_name}, got {connections}"
        )

        rendered = live.render(basename="live_test", cfg=isolated_cfg)
        assert rendered.ok, rendered.error
        assert rendered.images, "render reported ok but produced no image paths"
        for path in rendered.images:
            assert os.path.getsize(path) > 0
    finally:
        session.close()
```

- [ ] **Step 2: Run it**

Run: `.venv\Scripts\python.exe -m pytest tests/test_live.py -k build_and_render -v`
Expected: PASS. A Material Maker window will visibly open, a Perlin and a
Colorize node will appear and connect, and PNGs will appear under
`<tmp_path>/output/`. If a node type or parameter name in this test doesn't
match the real bundled catalog exactly, this is the point where that
surfaces — adjust the type/parameter names and rerun, same as any other
TDD red-green cycle.

- [ ] **Step 3: Run the full suite (including integration) to confirm no regressions**

Run: `.venv\Scripts\python.exe -m pytest -q`
Expected: all pass (157 fast + this new integration test + the 4 existing integration tests).

- [ ] **Step 4: Commit**

```bash
git add tests/test_live.py
git commit -m "test(live): integration-verify a scripted add/connect/set_param/render sequence"
```

## Self-Review

**Spec coverage:** All four commands from the spec's step-3 gate
(`add_node`/`connect_nodes`/`set_param`/`render`) are implemented on both
the GDScript and Python sides (Tasks 1-3, 4-5) and exercised together by
the gate's own scripted sequence (Task 6). The spec's "validate before
send" requirement is implemented for all three mutating ops (Task 4). The
render handler's "still-open" status from the spec is retired by this
plan's source verification and Task 3/5's implementation. The two
await-based constraints from the spec's "Feasibility verified" section
(`create_nodes` await, lazy `main_window` resolution) are respected in
Tasks 1 and throughout. `server.py` MCP tool wiring (`live_start`/
`live_apply`/etc.) is step 4, explicitly out of scope for this plan.

**Placeholder scan:** No TBD/TODO markers; every step has literal code or a
literal command to run.

**Type consistency:** `LiveResult.data["name"]` (Task 1/4) is consumed
consistently in Task 6. `LiveResult.data["problems"]` (Task 4) matches the
list-of-dicts shape `validate_graph` already returns elsewhere in this
codebase (`server.py`'s `render_graph`). `RenderResult` (Task 5) is the
same dataclass `render.py` already defines, imported not redefined.

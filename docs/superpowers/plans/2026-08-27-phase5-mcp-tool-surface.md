# Phase 5 Step 4: MCP Tool Surface Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Wire `live_start`/`live_get_graph`/`live_apply`/`live_render` into
`server.py` as real MCP tools, exposing everything `src/mm_mcp/live.py`
already does (steps 1-3 of this sub-plan), and along the way harden
`connect_or_launch` against the squatted/dying-port race the last session's
integration test reproduced deterministically.

**Architecture:** Four thin wrapper functions in `server.py`, each following
the existing tool pattern (plain function, `mcp.tool()(fn)` registration,
error-as-data return shape) rather than a new abstraction. All four share one
new helper, `_ensure_live_session`, which calls `live.connect_or_launch` on
every call -- cheap (one ping round-trip) when a session is already up,
matching the spec's "a live tool call launches it rather than erroring out"
scope decision. `live_apply` is a small dispatch table over the three
existing mutating client functions (`add_node`/`connect_nodes`/`set_param`),
not new mutation logic. Before any of that, `connect_or_launch` itself gets
hardened: a short grace period distinguishes a port that's genuinely booting
from one squatted by an unresponsive process, so the MCP tools built on top
of it don't inherit the "burn the whole timeout on a corpse" failure mode.

**Tech Stack:** Python 3.13, pytest, the existing `mm_mcp.live` client module,
`mcp.server.mcpserver.MCPServer`.

**Spec:**
[docs/superpowers/specs/2026-08-26-live-control-addon-design.md](../specs/2026-08-26-live-control-addon-design.md)
(see "Phases and gates," step 4, and "New MCP tools (`server.py`)"). The
port-race hardening item is tracked in [HANDOFF.md](../../../HANDOFF.md)'s
Open questions from the step-3 session, not in the original spec (it's a
hardening gap discovered during step 3's own integration test, folded into
this plan at Grayson's request rather than deferred again).

## Global Constraints

- No source fork; the addon and overlay from steps 1-3 are unchanged by this
  plan (spec: "No source fork").
- Turn-based collaboration, no concurrent-write conflict resolution (spec:
  "Turn-based collaboration, not real-time sync").
- Single active tab; live tools always operate on whatever graph is
  currently focused in the GUI (spec: "Single active tab").
- A live tool call launches Material Maker if nothing is listening on the
  known port, rather than erroring out (spec: "Claude can launch Material
  Maker").
- Socket errors are explicit, never a silent hang -- every live tool
  surfaces `ok: false` plus a clear `error` string, matching `render.py`'s
  existing "never silently succeed" philosophy (spec: "Error handling").
- `LIVE_HOST`/`LIVE_PORT` stay the hardcoded literals already defined in
  `live.py` -- no host/port parameters are added to the new MCP tool
  signatures (matches the spec's "known port" framing; Claude doesn't need
  to reason about sockets).
- **Explicitly out of scope for this plan** (carried over, still deferred,
  not silently dropped): the two-instance launch race and the
  unauthenticated-local-channel question, both flagged in prior sessions'
  final reviews. Only the squatted/dying-port grace-period gap gets fixed
  here.

---

## Task 1: Harden `connect_or_launch` against a squatted/dying port

**Files:**
- Modify: `src/mm_mcp/live.py:18-19` (add a constant near the existing
  `LIVE_HOST`/`LIVE_PORT` literals), `src/mm_mcp/live.py:256-310`
  (`connect_or_launch`, replace the top of the function; the try/except
  launch-and-poll block below stays unchanged).
- Test: `tests/test_live.py` (append two new tests after
  `test_connect_or_launch_returns_immediately_when_process_exits_early`, i.e.
  right before the `@pytest.mark.integration` tests at line 469).

**Interfaces:**
- Consumes: `ping(host, port) -> LiveResult` (line 76), `_is_listening(host,
  port) -> bool` (line 224), `_launch_overlay(cfg) -> subprocess.Popen`
  (line 245), `LiveSession` (line 210-221), `_terminate` (line 232) -- all
  already defined in `live.py`, unchanged.
- Produces: a new module constant `_SQUATTED_PORT_GRACE: float` (default
  `5.0`) and a new function `_wait_for_ready_or_give_up(host: str, port:
  int, deadline: float) -> tuple[bool, str]`. Neither is consumed by later
  tasks in this plan, but both are monkeypatchable the same way
  `_launch_overlay` already is, for anyone hardening this further later.
  `connect_or_launch`'s own signature and return type (`LiveSession`) are
  unchanged, so Tasks 2-7 need no awareness of this task beyond "it's more
  robust now."

- [ ] **Step 1: Write the two failing tests**

Append to `tests/test_live.py`, directly before the
`@pytest.mark.integration` tests (i.e. before the blank line at line 468):

```python
def test_connect_or_launch_fails_fast_when_port_is_occupied_by_an_unresponsive_process(monkeypatch):
    monkeypatch.setattr(live, "_SQUATTED_PORT_GRACE", 1.0)
    server = _FakeLiveServer(lambda cmd: {"ok": True, "ready": False})  # never becomes ready
    launched = {"called": False}

    def _no_launch(passed_cfg):
        launched["called"] = True
        return _FakeProcess()

    monkeypatch.setattr(live, "_launch_overlay", _no_launch)
    try:
        started = time.monotonic()
        session = live.connect_or_launch(cfg=cfg, host="127.0.0.1", port=server.port,
                                          launch_timeout=30.0)
        elapsed = time.monotonic() - started
        assert not session.ok
        assert elapsed < 10.0, "should fail fast on the grace period, not wait out launch_timeout"
        assert "occupied" in session.error.lower()
        assert launched["called"] is False
    finally:
        server.stop()


def test_connect_or_launch_relaunches_when_a_squatting_process_stops_listening_during_grace(monkeypatch):
    monkeypatch.setattr(live, "_SQUATTED_PORT_GRACE", 2.0)
    picked_port = _free_port()
    stale_server = _FakeLiveServer(lambda cmd: {"ok": True, "ready": False}, port=picked_port)

    def _stop_stale_soon():
        time.sleep(0.3)
        stale_server.stop()

    threading.Thread(target=_stop_stale_soon, daemon=True).start()

    fake_process = _FakeProcess()
    started_server = {"server": None}

    def _fake_launch(passed_cfg):
        def _start_late():
            time.sleep(0.3)  # simulate Godot booting before the addon listens
            started_server["server"] = _FakeLiveServer(
                lambda cmd: {"ok": True, "ready": True}, port=picked_port)
        threading.Thread(target=_start_late, daemon=True).start()
        return fake_process

    monkeypatch.setattr(live, "_launch_overlay", _fake_launch)
    try:
        session = live.connect_or_launch(cfg=cfg, host="127.0.0.1", port=picked_port,
                                          launch_timeout=5.0)
        assert session.ok, session.error
        assert session.process is fake_process
    finally:
        if started_server["server"] is not None:
            started_server["server"].stop()
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `.venv\Scripts\python.exe -m pytest tests/test_live.py -k "occupied or relaunches" -v`
Expected: both FAIL. The first fails because the current code waits out the
full 30s `launch_timeout` instead of failing within 10s. The second fails
because the current code never re-checks whether the port freed up, so
`session.ok` stays `False`.

- [ ] **Step 3: Add the grace-period constant and helper**

In `src/mm_mcp/live.py`, right after the existing `LIVE_HOST`/`LIVE_PORT`
constants (after line 19):

```python
# How long connect_or_launch will wait for an already-listening port to
# either become ready or stop listening, before deciding it's occupied by an
# unresponsive process rather than one that's still booting. Much shorter
# than launch_timeout on purpose -- see connect_or_launch's docstring.
_SQUATTED_PORT_GRACE = 5.0
```

Then, right before `def add_node(...)` (i.e. after the `ping`/`get_graph`
functions, before line 84's `_catalog_cache`), add:

```python
def _wait_for_ready_or_give_up(host: str, port: int, deadline: float) -> tuple[bool, str]:
    """Poll ping() until it reports ready, or `deadline` (a time.monotonic()
    value) passes. Returns (ready, last_error) -- last_error is always a
    string, even on success (harmless: callers only read it on failure)."""
    last_error = "timed out waiting for a response"
    while time.monotonic() < deadline:
        result = ping(host, port)
        if result.ok and result.data.get("ready"):
            return True, last_error
        if not result.ok:
            last_error = result.error
        time.sleep(0.5)
    return False, last_error
```

- [ ] **Step 4: Rewrite the top of `connect_or_launch`**

Replace lines 256-271 of `src/mm_mcp/live.py` (the function signature,
docstring, and the original two-line "probe, launch if silent" body) with:

```python
def connect_or_launch(cfg: Config | None = None, host: str = LIVE_HOST,
                       port: int = LIVE_PORT, launch_timeout: float = 60.0) -> LiveSession:
    """Probe (host, port); if nothing answers, rebuild the overlay if stale
    and launch Material Maker against it. Either way, poll ping() until the
    addon reports main_window is wired -- never assume the first successful
    ping means the GUI has finished loading (see the spec's "lazy
    main_window resolution" constraint) -- or give up after launch_timeout.

    A port that's already listening gets a short grace period
    (_SQUATTED_PORT_GRACE, much shorter than launch_timeout) to either
    become ready or stop listening, before this function commits to
    attaching. This is what lets a genuinely-booting instance attach
    normally while also recovering from a dying instance (e.g. a previous
    test's Material Maker process that's still closing its socket) instead
    of burning the entire launch_timeout on a corpse that will never
    answer. If the port is still listening and still unresponsive after the
    grace period, that's treated as a squatted port: connect_or_launch fails
    fast with a diagnostic error rather than continuing to wait, since it
    can't safely bind its own listener there anyway.

    Attaching to an already-running instance never launches a process, so
    the returned session's close() is a no-op for that case: we only own the
    lifecycle of a process we started ourselves.
    """
    cfg = cfg or load_config()
    process = None
    still_listening = _is_listening(host, port)

    if still_listening:
        grace_deadline = time.monotonic() + min(_SQUATTED_PORT_GRACE, launch_timeout)
        ready, grace_error = _wait_for_ready_or_give_up(host, port, grace_deadline)
        if ready:
            return LiveSession(ok=True, process=None)
        still_listening = _is_listening(host, port)
        if still_listening:
            return LiveSession(
                ok=False,
                error=(
                    f"port {port} is occupied by a process that never answered as the live "
                    f"server after waiting {_SQUATTED_PORT_GRACE:.0f}s ({grace_error}). If a "
                    "previous Material Maker/Godot process is stuck on this port, close it "
                    "(or taskkill the Godot console binary) and retry."
                ),
            )
        # The occupant stopped listening during the grace period -- the port
        # is free now, so fall through and launch normally.

    if not still_listening:
        process = _launch_overlay(cfg)
```

Everything from the original line 273 comment (`# The launch-and-poll span
below is wrapped...`) through the end of the function (line 310) stays
exactly as-is -- only the lines above it are replaced.

- [ ] **Step 5: Run the tests to verify they pass**

Run: `.venv\Scripts\python.exe -m pytest tests/test_live.py -k "occupied or relaunches" -v`
Expected: both PASS.

- [ ] **Step 6: Run the full fast `test_live.py` suite to confirm no regressions**

Run: `.venv\Scripts\python.exe -m pytest tests/test_live.py -m "not integration" -v`
Expected: PASS, including the four pre-existing `connect_or_launch` tests
(`attaches_when_already_listening`, `launches_when_not_listening`,
`terminates_process_on_timeout`, `returns_immediately_when_process_exits_early`)
still green with no changes needed to them.

- [ ] **Step 7: Commit**

```bash
git add src/mm_mcp/live.py tests/test_live.py
git commit -m "fix(live): harden connect_or_launch against a squatted/dying port"
```

---

## Task 2: `_ensure_live_session` helper + `live_start` MCP tool

**Files:**
- Modify: `src/mm_mcp/server.py:6` (add an import), after line 116 (add new
  module state + function), `src/mm_mcp/server.py:126` (register the tool).
- Test: Create `tests/test_server_live.py`.

**Interfaces:**
- Consumes: `live.connect_or_launch(cfg, launch_timeout) -> LiveSession`
  (Task 1's hardened version), `server._ensure_ready() -> (Config, dict)`
  (already exists, line 22).
- Produces: `server._ensure_live_session(cfg: Config, launch_timeout: float
  = 60.0) -> live.LiveSession` (consumed by Tasks 3-5), `server.live_start(
  launch_timeout: float = 60.0) -> dict` returning `{"ok": bool, "launched":
  bool, "error": str | None}`.

- [ ] **Step 1: Write the failing tests**

Create `tests/test_server_live.py`:

```python
# tests/test_server_live.py
from dataclasses import dataclass
from mm_mcp import server, live
from mm_mcp.config import load_config

cfg = load_config()


@dataclass
class _FakeSession:
    ok: bool
    process: object | None = None
    error: str | None = None


def test_live_start_reports_attach_when_already_running(monkeypatch):
    monkeypatch.setattr(server, "_ensure_ready", lambda: (cfg, {}))
    monkeypatch.setattr(live, "connect_or_launch",
                         lambda cfg, launch_timeout=60.0: _FakeSession(ok=True, process=None))
    result = server.live_start()
    assert result == {"ok": True, "launched": False, "error": None}


def test_live_start_reports_launched_when_a_new_process_was_spawned(monkeypatch):
    monkeypatch.setattr(server, "_ensure_ready", lambda: (cfg, {}))
    monkeypatch.setattr(live, "connect_or_launch",
                         lambda cfg, launch_timeout=60.0: _FakeSession(ok=True, process=object()))
    result = server.live_start()
    assert result == {"ok": True, "launched": True, "error": None}


def test_live_start_surfaces_launch_failure(monkeypatch):
    monkeypatch.setattr(server, "_ensure_ready", lambda: (cfg, {}))
    monkeypatch.setattr(live, "connect_or_launch",
                         lambda cfg, launch_timeout=60.0: _FakeSession(ok=False, error="boom"))
    result = server.live_start()
    assert result == {"ok": False, "launched": False, "error": "boom"}
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv\Scripts\python.exe -m pytest tests/test_server_live.py -v`
Expected: FAIL with `AttributeError: module 'mm_mcp.server' has no attribute 'live_start'`.

- [ ] **Step 3: Add the import, helper, and tool function**

In `src/mm_mcp/server.py`, change line 6 from:

```python
from mm_mcp import __version__
```

to:

```python
from mm_mcp import __version__, live
```

After `load_example` (which ends at line 116, right before the `# Register
the plain functions as MCP tools.` comment on line 118), insert:

```python
_live_session: live.LiveSession | None = None


def _ensure_live_session(cfg, launch_timeout: float = 60.0) -> live.LiveSession:
    """Every live_* tool call goes through this first: probes (or launches)
    Material Maker via live.connect_or_launch, per the design spec's "a live
    tool call launches it rather than erroring out" scope decision. Cheap
    when a session is already up and ready (one ping round-trip); only slow
    the first time, when nothing is listening yet."""
    global _live_session
    _live_session = live.connect_or_launch(cfg=cfg, launch_timeout=launch_timeout)
    return _live_session


def live_start(launch_timeout: float = 60.0) -> dict:
    """Connect to an already-open Material Maker, or launch it against the
    disposable live overlay if nothing's listening on the known port. Not
    required before the other live_* tools -- they each do this same
    connect-or-launch check themselves -- but useful to call first to
    surface a launch failure (or confirm attach) before issuing real ops."""
    cfg, _ = _ensure_ready()
    session = _ensure_live_session(cfg, launch_timeout=launch_timeout)
    return {"ok": session.ok, "launched": session.process is not None,
            "error": session.error}
```

- [ ] **Step 4: Register the tool**

After line 126 (`mcp.tool()(load_example)`), add:

```python
mcp.tool()(live_start)
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `.venv\Scripts\python.exe -m pytest tests/test_server_live.py -v`
Expected: PASS (3 passed).

- [ ] **Step 6: Commit**

```bash
git add src/mm_mcp/server.py tests/test_server_live.py
git commit -m "feat(server): add live_start MCP tool"
```

---

## Task 3: `live_get_graph` MCP tool

**Files:**
- Modify: `src/mm_mcp/server.py` (add function after `live_start`, register).
- Test: `tests/test_server_live.py` (append).

**Interfaces:**
- Consumes: `server._ensure_live_session` (Task 2), `live.get_graph() ->
  LiveResult`.
- Produces: `server.live_get_graph() -> dict` returning `{"ok": bool,
  "graph": dict | None, "error": str | None}`.

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_server_live.py`:

```python
def test_live_get_graph_returns_graph_on_success(monkeypatch):
    monkeypatch.setattr(server, "_ensure_ready", lambda: (cfg, {}))
    monkeypatch.setattr(live, "connect_or_launch",
                         lambda cfg, launch_timeout=60.0: _FakeSession(ok=True))
    fake_graph = {"nodes": [], "connections": []}
    monkeypatch.setattr(live, "get_graph",
                         lambda: live.LiveResult(ok=True, data={"graph": fake_graph}))
    result = server.live_get_graph()
    assert result == {"ok": True, "graph": fake_graph, "error": None}


def test_live_get_graph_reports_session_failure_without_calling_get_graph(monkeypatch):
    monkeypatch.setattr(server, "_ensure_ready", lambda: (cfg, {}))
    monkeypatch.setattr(live, "connect_or_launch",
                         lambda cfg, launch_timeout=60.0: _FakeSession(ok=False, error="no server"))
    called = {"yes": False}

    def _boom():
        called["yes"] = True
        raise AssertionError("get_graph should not be called when the session failed")

    monkeypatch.setattr(live, "get_graph", _boom)
    result = server.live_get_graph()
    assert result == {"ok": False, "graph": None, "error": "no server"}
    assert called["yes"] is False
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv\Scripts\python.exe -m pytest tests/test_server_live.py -k live_get_graph -v`
Expected: FAIL with `AttributeError: module 'mm_mcp.server' has no attribute 'live_get_graph'`.

- [ ] **Step 3: Implement `live_get_graph`**

Add after `live_start` in `src/mm_mcp/server.py`:

```python
def live_get_graph() -> dict:
    """Fetch the graph currently on Material Maker's active tab, in the same
    {nodes, connections} shape as a .ptex file."""
    cfg, _ = _ensure_ready()
    session = _ensure_live_session(cfg)
    if not session.ok:
        return {"ok": False, "graph": None, "error": session.error}
    result = live.get_graph()
    return {"ok": result.ok, "graph": result.data.get("graph") if result.ok else None,
            "error": result.error}
```

- [ ] **Step 4: Register the tool**

After `mcp.tool()(live_start)`, add:

```python
mcp.tool()(live_get_graph)
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `.venv\Scripts\python.exe -m pytest tests/test_server_live.py -k live_get_graph -v`
Expected: PASS (2 passed).

- [ ] **Step 6: Commit**

```bash
git add src/mm_mcp/server.py tests/test_server_live.py
git commit -m "feat(server): add live_get_graph MCP tool"
```

---

## Task 4: `live_apply` MCP tool

**Files:**
- Modify: `src/mm_mcp/server.py` (add dispatch table + function after
  `live_get_graph`, register).
- Test: `tests/test_server_live.py` (append).

**Interfaces:**
- Consumes: `server._ensure_live_session`, `live.add_node(node_type,
  parameters, x, y, cfg) -> LiveResult`, `live.connect_nodes(from_name,
  from_port, to_name, to_port, cfg) -> LiveResult`, `live.set_param(name,
  parameters, cfg) -> LiveResult`.
- Produces: `server.live_apply(ops: list[dict]) -> dict` returning `{"ok":
  bool, "results": list[dict], "error": str | None}`. Each item of `ops` is
  one of:
  - `{"op": "add_node", "node_type": str, "parameters": dict, "x": float,
    "y": float}` (`parameters`/`x`/`y` optional)
  - `{"op": "connect_nodes", "from_name": str, "from_port": int, "to_name":
    str, "to_port": int}`
  - `{"op": "set_param", "name": str, "parameters": dict}`

  Each item of `results` is `{"index": int, "op": str, "ok": bool, "data":
  dict | None, "error": str | None}`. This exact op schema is consumed by
  Task 7's integration test.

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_server_live.py`:

```python
def test_live_apply_runs_ops_in_order_and_stops_at_first_failure(monkeypatch):
    monkeypatch.setattr(server, "_ensure_ready", lambda: (cfg, {}))
    monkeypatch.setattr(live, "connect_or_launch",
                         lambda cfg, launch_timeout=60.0: _FakeSession(ok=True))
    calls = []

    def _fake_add_node(node_type, parameters, x=0.0, y=0.0, cfg=None):
        calls.append(("add_node", node_type))
        return live.LiveResult(ok=True, data={"name": "perlin_1"})

    def _fake_connect_nodes(from_name, from_port, to_name, to_port, cfg=None):
        calls.append(("connect_nodes", from_name, to_name))
        return live.LiveResult(ok=False, error="bad port")

    monkeypatch.setattr(live, "add_node", _fake_add_node)
    monkeypatch.setattr(live, "connect_nodes", _fake_connect_nodes)

    ops = [
        {"op": "add_node", "node_type": "perlin", "parameters": {}, "x": 0, "y": 0},
        {"op": "connect_nodes", "from_name": "perlin_1", "from_port": 0,
         "to_name": "does_not_exist", "to_port": 0},
        {"op": "add_node", "node_type": "colorize", "parameters": {}},
    ]
    result = server.live_apply(ops)
    assert result["ok"] is False
    assert len(result["results"]) == 2  # third op never ran
    assert calls == [("add_node", "perlin"), ("connect_nodes", "perlin_1", "does_not_exist")]
    assert "op 1" in result["error"]


def test_live_apply_runs_all_ops_when_every_one_succeeds(monkeypatch):
    monkeypatch.setattr(server, "_ensure_ready", lambda: (cfg, {}))
    monkeypatch.setattr(live, "connect_or_launch",
                         lambda cfg, launch_timeout=60.0: _FakeSession(ok=True))
    monkeypatch.setattr(live, "set_param",
                         lambda name, parameters, cfg=None: live.LiveResult(ok=True))
    result = server.live_apply([{"op": "set_param", "name": "perlin_1",
                                  "parameters": {"scale_x": 16}}])
    assert result["ok"] is True
    assert result["results"] == [{"index": 0, "op": "set_param", "ok": True,
                                   "data": None, "error": None}]


def test_live_apply_rejects_unrecognized_op_without_contacting_the_server(monkeypatch):
    monkeypatch.setattr(server, "_ensure_ready", lambda: (cfg, {}))
    monkeypatch.setattr(live, "connect_or_launch",
                         lambda cfg, launch_timeout=60.0: _FakeSession(ok=True))
    result = server.live_apply([{"op": "delete_everything"}])
    assert result["ok"] is False
    assert "delete_everything" in result["error"]
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv\Scripts\python.exe -m pytest tests/test_server_live.py -k live_apply -v`
Expected: FAIL with `AttributeError: module 'mm_mcp.server' has no attribute 'live_apply'`.

- [ ] **Step 3: Implement `live_apply`**

Add after `live_get_graph` in `src/mm_mcp/server.py`:

```python
_LIVE_OP_HANDLERS = {
    "add_node": lambda op, cfg: live.add_node(
        op["node_type"], op.get("parameters"), x=op.get("x", 0.0), y=op.get("y", 0.0), cfg=cfg),
    "connect_nodes": lambda op, cfg: live.connect_nodes(
        op["from_name"], op["from_port"], op["to_name"], op["to_port"], cfg=cfg),
    "set_param": lambda op, cfg: live.set_param(op["name"], op["parameters"], cfg=cfg),
}


def live_apply(ops: list) -> dict:
    """Apply a batch of mutations to the live graph in order, each validated
    against the catalog before it reaches the socket (same validation
    live.py's add_node/connect_nodes/set_param already do). Stops at the
    first failing op rather than continuing: a later op in the same batch
    may assume an earlier one already applied (e.g. connecting a node
    add_node just created), so there's nothing safe to do with the rest of
    the batch once one op fails. Each op is a dict:
    {"op": "add_node", "node_type": ..., "parameters": {...}, "x": ..., "y": ...} |
    {"op": "connect_nodes", "from_name": ..., "from_port": ..., "to_name": ..., "to_port": ...} |
    {"op": "set_param", "name": ..., "parameters": {...}}.
    """
    cfg, _ = _ensure_ready()
    session = _ensure_live_session(cfg)
    if not session.ok:
        return {"ok": False, "results": [], "error": session.error}
    results = []
    for i, op in enumerate(ops):
        kind = op.get("op")
        handler = _LIVE_OP_HANDLERS.get(kind)
        if handler is None:
            error = f"op {i} has an unrecognized 'op' value: {kind!r}"
            results.append({"index": i, "op": kind, "ok": False, "data": None, "error": error})
            return {"ok": False, "results": results, "error": error}
        result = handler(op, cfg)
        results.append({"index": i, "op": kind, "ok": result.ok,
                         "data": result.data, "error": result.error})
        if not result.ok:
            return {"ok": False, "results": results,
                    "error": f"op {i} ({kind}) failed: {result.error}"}
    return {"ok": True, "results": results, "error": None}
```

- [ ] **Step 4: Register the tool**

After `mcp.tool()(live_get_graph)`, add:

```python
mcp.tool()(live_apply)
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `.venv\Scripts\python.exe -m pytest tests/test_server_live.py -k live_apply -v`
Expected: PASS (3 passed).

- [ ] **Step 6: Commit**

```bash
git add src/mm_mcp/server.py tests/test_server_live.py
git commit -m "feat(server): add live_apply MCP tool"
```

---

## Task 5: `live_render` MCP tool

**Files:**
- Modify: `src/mm_mcp/server.py` (add function after `live_apply`, register).
- Test: `tests/test_server_live.py` (append).

**Interfaces:**
- Consumes: `server._ensure_live_session`, `live.render(basename, profile,
  cfg) -> RenderResult` (fields: `ok: bool`, `images: list`, `log_tail:
  str`, `error: str | None`).
- Produces: `server.live_render(basename: str = "material", profile: str =
  "Godot/Godot 4 Standard") -> dict` returning `{"ok": bool, "images":
  list, "error": str | None, "log_tail": str}` -- same shape `render_graph`
  already returns.

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_server_live.py`:

```python
from mm_mcp.render import RenderResult


def test_live_render_returns_images_on_success(monkeypatch):
    monkeypatch.setattr(server, "_ensure_ready", lambda: (cfg, {}))
    monkeypatch.setattr(live, "connect_or_launch",
                         lambda cfg, launch_timeout=60.0: _FakeSession(ok=True))
    monkeypatch.setattr(live, "render",
                         lambda basename, profile, cfg: RenderResult(ok=True, images=["a.png"]))
    result = server.live_render(basename="material")
    assert result == {"ok": True, "images": ["a.png"], "error": None, "log_tail": ""}


def test_live_render_reports_session_failure_without_rendering(monkeypatch):
    monkeypatch.setattr(server, "_ensure_ready", lambda: (cfg, {}))
    monkeypatch.setattr(live, "connect_or_launch",
                         lambda cfg, launch_timeout=60.0: _FakeSession(ok=False, error="no server"))
    called = {"yes": False}

    def _boom(basename, profile, cfg):
        called["yes"] = True

    monkeypatch.setattr(live, "render", _boom)
    result = server.live_render()
    assert result == {"ok": False, "images": [], "error": "no server", "log_tail": ""}
    assert called["yes"] is False
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv\Scripts\python.exe -m pytest tests/test_server_live.py -k live_render -v`
Expected: FAIL with `AttributeError: module 'mm_mcp.server' has no attribute 'live_render'`.

- [ ] **Step 3: Implement `live_render`**

Add after `live_apply` in `src/mm_mcp/server.py`:

```python
def live_render(basename: str = "material", profile: str = "Godot/Godot 4 Standard") -> dict:
    """Trigger a render in the live window (the same underlying export path
    the GUI's own render button uses) and return the same {ok, images,
    error, log_tail} shape render_graph already uses."""
    cfg, _ = _ensure_ready()
    session = _ensure_live_session(cfg)
    if not session.ok:
        return {"ok": False, "images": [], "error": session.error, "log_tail": ""}
    result = live.render(basename=basename, profile=profile, cfg=cfg)
    return {"ok": result.ok, "images": result.images, "error": result.error,
            "log_tail": result.log_tail}
```

- [ ] **Step 4: Register the tool**

After `mcp.tool()(live_apply)`, add:

```python
mcp.tool()(live_render)
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `.venv\Scripts\python.exe -m pytest tests/test_server_live.py -k live_render -v`
Expected: PASS (2 passed).

- [ ] **Step 6: Commit**

```bash
git add src/mm_mcp/server.py tests/test_server_live.py
git commit -m "feat(server): add live_render MCP tool"
```

---

## Task 6: README "Live mode" section + fix the stale tool-count line

**Files:**
- Modify: `README.md:181` (tool count sentence), `README.md:183-191` (tool
  table -- add the missing `render_preview` row, a real gap predating this
  plan), `README.md:193` (add a new section after the resource line, before
  `## Notes and gotchas` at line 195).

**Interfaces:**
- Consumes: nothing code-level -- documents the four tools Tasks 2-5 built.
- Produces: nothing consumed by another task; this is the plan's
  documentation deliverable per the spec's "Distribution and docs" section.

- [ ] **Step 1: Fix the existing tool-count mismatch and add the missing row**

In `README.md`, change line 181 from:

```markdown
The server exposes seven tools and one resource:
```

to:

```markdown
The server exposes eight tools and one resource:
```

Then, in the table (lines 183-191), add a row for `render_preview` right
after `render_graph` (this row was missing before this plan -- a
pre-existing gap flagged in a prior session's review, fixed here since this
task is already touching this exact table):

```markdown
| `render_preview` | Composite already-rendered maps onto a sphere/cube/cutaway-ball preview scene |
```

- [ ] **Step 2: Add the "Live mode" section**

After line 193 (`Resource `catalog://nodes` exposes the full node
catalog.`) and before line 195 (`## Notes and gotchas`), insert:

```markdown
## Live mode (optional)

Batch mode above (`render_graph` et al.) is the default, simplest path: no
Material Maker GUI involved. Live mode is a second, additive way to work --
open Material Maker yourself, and Claude can see the graph on your active
tab, build and edit it live, and trigger renders, so you watch it happen in
the GUI instead of copying files back and forth.

| Tool | What it does |
|---|---|
| `live_start` | Attach to an already-open Material Maker, or launch it against a disposable overlay if nothing's listening |
| `live_get_graph` | Fetch the active tab's current graph, `.ptex`-shaped |
| `live_apply` | Apply a batch of validated mutations (`add_node`/`connect_nodes`/`set_param`) to the live graph |
| `live_render` | Trigger a render in the live window, same result shape as `render_graph` |

No manual setup beyond what batch mode already needs -- the addon ships in
this repo and builds its own disposable working copy on first use. Live
mode is turn-based, not simultaneous: there's no conflict resolution for
edits from both sides at once. See
[docs/superpowers/specs/2026-08-26-live-control-addon-design.md](docs/superpowers/specs/2026-08-26-live-control-addon-design.md)
for the full design.
```

- [ ] **Step 3: Manual verification**

Read the rendered `README.md` (or preview it) and confirm both tables
render correctly, the tool count sentence matches the batch table's row
count, and no markdown syntax is broken.

- [ ] **Step 4: Commit**

```bash
git add README.md
git commit -m "docs: add Live mode section, fix stale tool count"
```

---

## Task 7: Real integration test proving the gate

**Files:**
- Modify: `tests/test_server_live.py` (append one
  `@pytest.mark.integration` test).

**Interfaces:**
- Consumes: `server.live_start`, `server.live_get_graph`,
  `server.live_apply`, `server.live_render` (Tasks 2-5, unmocked), `server`
  module's real `_ensure_ready`/`_reset`/`load_config` reference.
- Produces: nothing further consumed -- this is the plan's own gate:
  "Claude can hold an actual live session against a real open Material
  Maker window."

- [ ] **Step 1: Write the integration test**

Append to `tests/test_server_live.py`:

```python
import os
from dataclasses import replace
import pytest


@pytest.mark.integration
def test_live_tools_hold_a_real_session_against_material_maker(tmp_path, monkeypatch):
    # Isolated overlay + output dirs so this test never collides with (or
    # clobbers) a manual session's overlay or output files, matching the
    # isolation pattern test_live.py's own integration tests already use.
    isolated_cfg = replace(cfg, live_overlay_dir=str(tmp_path / "mm_live_overlay"),
                            output_dir=str(tmp_path / "output"))
    monkeypatch.setattr(server, "load_config", lambda *a, **kw: isolated_cfg)
    server._reset()
    try:
        start = server.live_start(launch_timeout=90.0)
        assert start["ok"], start["error"]
        assert start["launched"] is True, (
            "attached to a pre-existing instance on port 8765 -- close it and rerun; "
            "this test must launch its own overlay to prove server.py's wiring works"
        )
        try:
            graph = server.live_get_graph()
            assert graph["ok"], graph["error"]
            assert any(n.get("type") == "material" for n in graph["graph"]["nodes"])

            built = server.live_apply([
                {"op": "add_node", "node_type": "perlin", "parameters": {}, "x": 0, "y": 0},
            ])
            assert built["ok"], built["error"]
            source_name = built["results"][0]["data"]["name"]

            sink = server.live_apply([
                {"op": "add_node", "node_type": "colorize", "parameters": {}, "x": 200, "y": 0},
            ])
            assert sink["ok"], sink["error"]
            sink_name = sink["results"][0]["data"]["name"]

            # Wire source -> sink -> the default new-material graph's
            # "Material" node, same recipe test_live.py's own
            # test_live_ops_build_and_render_a_simple_graph already proved
            # renders real PNGs -- reused here so this test is checking
            # server.py's dispatch, not discovering a new valid graph shape.
            wired = server.live_apply([
                {"op": "connect_nodes", "from_name": source_name, "from_port": 0,
                 "to_name": sink_name, "to_port": 0},
                {"op": "connect_nodes", "from_name": sink_name, "from_port": 0,
                 "to_name": "Material", "to_port": 0},
                {"op": "set_param", "name": source_name, "parameters": {"scale_x": 16}},
            ])
            assert wired["ok"], wired["error"]

            rendered = server.live_render(basename="server_live_test")
            assert rendered["ok"], rendered["error"]
            assert rendered["images"], "render reported ok but produced no image paths"
            for path in rendered["images"]:
                assert os.path.getsize(path) > 0
        finally:
            server._live_session.close()
    finally:
        server._reset()
```

- [ ] **Step 2: Run the integration test**

Run: `.venv\Scripts\python.exe -m pytest tests/test_server_live.py -k live_tools_hold_a_real_session -v`
Expected: PASS. This launches a real Material Maker instance (up to 90s) --
if it fails, check `<isolated_output_dir>/mm_live.log` first, per the
existing heads-up in HANDOFF.md about where launch failures get logged.

- [ ] **Step 3: Run the full fast suite to confirm no regressions**

Run: `.venv\Scripts\python.exe -m pytest -q -m "not integration"`
Expected: PASS, 0 failures, count higher than the pre-plan baseline (158
plus this plan's new fast tests: 2 from Task 1, 3+2+3+2 from Tasks 2-5).

- [ ] **Step 4: Commit**

```bash
git add tests/test_server_live.py
git commit -m "test(server): integration-verify the live MCP tool surface end to end"
```

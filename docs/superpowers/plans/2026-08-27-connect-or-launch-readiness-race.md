# connect_or_launch Readiness Race Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix the pre-existing race where `connect_or_launch` can report a
live session ready before Material Maker's default graph tab actually
exists, which occasionally makes the first mutating call (`add_node`,
`get_graph`, etc.) fail with `{"ok": false, "error": "no active graph"}`
immediately after a successful `live_start`/`connect_or_launch`.

**Architecture:** The addon's `ping` handler currently reports `ready` based
solely on `mm_globals.main_window != null`. It gains a second, independent
field, `has_graph`, computed by a new `_has_active_graph()` helper that
checks exactly what the five mutating/read command handlers already check
(`get_current_graph_edit()` non-null and its `.generator` non-null). On the
Python side, `connect_or_launch`'s two polling call sites (the
already-listening grace-period wait and the main launch/attach poll loop)
are changed to require `ready AND has_graph` before declaring the session
usable, instead of `ready` alone. This closes the race at its one true
choke point -- every `live_*` MCP tool call goes through
`connect_or_launch` via `_ensure_live_session` -- so the five command
handlers' own `graph_edit == null` guards don't need to change; they become
pure defense-in-depth instead of the only protection.

**Tech Stack:** Python 3.13, pytest (`_FakeLiveServer` unit-test harness in
`tests/test_live.py`), GDScript 2.0 / Godot 4.7.1 (no automated test harness
for GDScript exists in this repo -- verified via the real Godot integration
tests instead, per this project's established practice for this exact
addon).

**Spec:**
[docs/superpowers/specs/2026-08-26-live-control-addon-design.md](../specs/2026-08-26-live-control-addon-design.md)
(see "Constraints these surfaced," the `main_window` lazy-resolution bullet
-- written before this race was discovered, corrected by Task 4 below). The
race itself is tracked in [HANDOFF.md](../../../HANDOFF.md)'s Open questions
and Heads-up sections from the 2026-08-27 (night) session, which has the
full repro history (reproduced 3 times in a row, confirmed pre-existing via
`git stash`).

## Global Constraints

- `LIVE_PORT` must stay in sync by hand between `addons/mm_live/live_server.gd`
  and `src/mm_mcp/live.py` -- unchanged by this plan, noted only because both
  files are touched.
- No automated GDScript test harness exists in this repo. GDScript changes
  are verified via the real Godot-launching integration tests
  (`@pytest.mark.integration` in `tests/test_live.py`), not a unit test.
- Lazy `main_window` resolution: never cache it, resolve fresh inside every
  command handler (spec: "Resolve it lazily per command, never cache at
  boot"). This plan's new `_has_active_graph()` helper follows the same rule.
- Run tests with `.venv\Scripts\python.exe -m pytest ...`. Fast suite:
  `-m "not integration"` (177 passed before this plan). Full suite (adds
  Godot-launching integration tests) has no `-m` filter.
- Validation errors are data, not exceptions (project-wide convention) --
  not directly exercised by this fix, but any new code must keep returning
  `LiveResult(ok=False, error=...)` rather than raising, matching every
  existing function in `live.py`.

---

### Task 1: `connect_or_launch` requires `has_graph`, proven against a fake server

**Files:**
- Modify: `src/mm_mcp/live.py:90-114` (`_wait_for_ready_or_give_up`)
- Modify: `src/mm_mcp/live.py:378-399` (the main poll loop inside `connect_or_launch`)
- Modify: `tests/test_live.py` (four existing fixtures need `has_graph: True`
  added once this task's implementation step lands, or they will time out)
- Test: `tests/test_live.py` (one new test)

**Interfaces:**
- Consumes: `ping()` (`src/mm_mcp/live.py:82`), unchanged signature, returns
  `LiveResult` whose `.data` dict will (after Task 2) contain a `has_graph`
  bool key alongside the existing `ready` key. This task treats a missing
  `has_graph` key as falsy (`.get("has_graph")` defaults to `None`), so it
  is safe to land before Task 2's GDScript change exists -- a real addon
  without Task 2 would simply never satisfy the new gate, which is the
  correct conservative behavior for an out-of-sync client/addon pair.
- Produces: no new public functions; `connect_or_launch`'s existing return
  type (`LiveSession`) and existing call sites are unchanged.

- [ ] **Step 1: Write the failing test**

Add to `tests/test_live.py`, near
`test_connect_or_launch_waits_past_grace_for_a_slow_booting_real_instance`
(both exercise the same grace-period-then-main-poll-loop path, so keep them
adjacent):

```python
def test_connect_or_launch_waits_for_a_graph_tab_after_main_window_is_ready(monkeypatch):
    monkeypatch.setattr(live, "_SQUATTED_PORT_GRACE", 1.0)
    state = {"has_graph": False}
    server = _FakeLiveServer(
        lambda cmd: {"ok": True, "ready": True, "has_graph": state["has_graph"]})
    launched = {"called": False}

    def _no_launch(passed_cfg):
        launched["called"] = True
        return _FakeProcess()

    monkeypatch.setattr(live, "_launch_overlay", _no_launch)

    def _open_graph_tab_soon():
        time.sleep(1.5)  # past the 1.0s grace period, well within launch_timeout
        state["has_graph"] = True

    threading.Thread(target=_open_graph_tab_soon, daemon=True).start()
    try:
        started = time.monotonic()
        session = live.connect_or_launch(cfg=cfg, host="127.0.0.1", port=server.port,
                                          launch_timeout=10.0)
        elapsed = time.monotonic() - started
        assert session.ok, session.error
        assert elapsed >= 1.5, (
            "connect_or_launch must not report ready before the addon reports a graph "
            "tab, even once main_window itself is already ready"
        )
        assert session.process is None  # attached, never launched a new one
        assert launched["called"] is False
    finally:
        server.stop()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv\Scripts\python.exe -m pytest tests/test_live.py -k graph_tab_after_main_window -v`
Expected: FAIL -- `assert elapsed >= 1.5` fails because `connect_or_launch`
currently returns as soon as `ready` is `True`, ignoring `has_graph`
entirely, so `elapsed` will be near 0.

- [ ] **Step 3: Implement the fix**

In `src/mm_mcp/live.py`, update `_wait_for_ready_or_give_up`'s docstring and
its one conditional:

```python
def _wait_for_ready_or_give_up(host: str, port: int, deadline: float) -> tuple[bool, bool, str]:
    """Poll ping() until it reports ready, or `deadline` (a time.monotonic()
    value) passes. Returns (ready, ever_answered, last_error).

    "Ready" here means both `ready` (main_window resolved) AND `has_graph`
    (a graph tab exists) from ping()'s response -- main_window can resolve
    one or more frames before the default graph tab is created, so gating
    on `ready` alone lets a caller proceed before add_node/get_graph/etc.
    are actually safe to call (see docs/superpowers/plans/
    2026-08-27-connect-or-launch-readiness-race.md).

    ever_answered is True the moment ping() ever returns ok=True, even with
    ready=False -- a real live-addon socket answers ping almost immediately
    after binding (project startup), well before main_window resolves (see
    the spec's "lazy main_window resolution" constraint). A single
    successful-but-not-ready response is proof this is a live addon that's
    still booting, not a dead/squatted process -- even if it never reaches
    ready before the deadline. last_error is always a string, even on
    success (harmless: callers only read it on failure).
    """
    ever_answered = False
    last_error = "timed out waiting for a response"
    while time.monotonic() < deadline:
        result = ping(host, port)
        if result.ok:
            ever_answered = True
            if result.data.get("ready") and result.data.get("has_graph"):
                return True, ever_answered, last_error
        else:
            last_error = result.error
        time.sleep(0.5)
    return False, ever_answered, last_error
```

Then update the main poll loop inside `connect_or_launch` (the `while
time.monotonic() < deadline:` block after the `try:` at line 378):

```python
        while time.monotonic() < deadline:
            result = ping(host, port)
            if result.ok and result.data.get("ready") and result.data.get("has_graph"):
                return LiveSession(ok=True, process=process)
            if not result.ok:
                last_error = result.error
            if process is not None and process.poll() is not None:
```

(Only the `if result.ok and result.data.get("ready"):` line changes; the
rest of the loop body is unchanged.)

- [ ] **Step 4: Run the new test to verify it passes**

Run: `.venv\Scripts\python.exe -m pytest tests/test_live.py -k graph_tab_after_main_window -v`
Expected: PASS

- [ ] **Step 5: Run the full file and fix the fixtures the change breaks**

Run: `.venv\Scripts\python.exe -m pytest tests/test_live.py -v`
Expected: these four tests now FAIL or hang until their own
`launch_timeout` (a few seconds each, not dangerous, just slow), because
their fake servers reply `{"ok": True, "ready": True}` with no `has_graph`
key, which `.get("has_graph")` reads as falsy:
- `test_connect_or_launch_attaches_when_already_listening`
- `test_connect_or_launch_launches_when_not_listening`
- `test_connect_or_launch_relaunches_when_a_squatting_process_stops_listening_during_grace`
- `test_connect_or_launch_waits_past_grace_for_a_slow_booting_real_instance`

Fix each by adding `"has_graph": True` to the dict literal (or, for
`test_connect_or_launch_waits_past_grace_for_a_slow_booting_real_instance`,
to the responder's returned dict) their fake responder returns, since all
four represent an already-fully-booted instance where a graph tab already
exists -- e.g.:

```python
def test_connect_or_launch_attaches_when_already_listening(monkeypatch):
    server = _FakeLiveServer(lambda cmd: {"ok": True, "ready": True, "has_graph": True})
    ...
```

```python
def test_connect_or_launch_launches_when_not_listening(monkeypatch):
    picked_port = _free_port()
    fake_process = _FakeProcess()
    started_server = {"server": None}

    def _fake_launch(passed_cfg):
        def _start_late():
            time.sleep(0.3)  # simulate Godot booting before the addon listens
            started_server["server"] = _FakeLiveServer(
                lambda cmd: {"ok": True, "ready": True, "has_graph": True}, port=picked_port)
        threading.Thread(target=_start_late, daemon=True).start()
        return fake_process
    ...
```

```python
def test_connect_or_launch_relaunches_when_a_squatting_process_stops_listening_during_grace(monkeypatch):
    ...
    def _fake_launch(passed_cfg):
        def _start_late():
            time.sleep(0.3)  # simulate Godot booting before the addon listens
            started_server["server"] = _FakeLiveServer(
                lambda cmd: {"ok": True, "ready": True, "has_graph": True}, port=picked_port)
        threading.Thread(target=_start_late, daemon=True).start()
        return fake_process
    ...
```

```python
def test_connect_or_launch_waits_past_grace_for_a_slow_booting_real_instance(monkeypatch):
    monkeypatch.setattr(live, "_SQUATTED_PORT_GRACE", 1.0)
    state = {"ready": False}
    server = _FakeLiveServer(
        lambda cmd: {"ok": True, "ready": state["ready"], "has_graph": True})
    ...
```

- [ ] **Step 6: Run the full file again to verify everything passes**

Run: `.venv\Scripts\python.exe -m pytest tests/test_live.py -v`
Expected: PASS, all tests including the new one (fast tests only run in a
few seconds; the two `@pytest.mark.integration` tests in this file will
still try to launch real Godot and are covered separately by Task 3).

- [ ] **Step 7: Run the fast suite to confirm no wider breakage**

Run: `.venv\Scripts\python.exe -m pytest -q -m "not integration"`
Expected: 178 passed (177 before this task, +1 new test).

- [ ] **Step 8: Commit**

```bash
git add src/mm_mcp/live.py tests/test_live.py
git commit -m "fix(live): require a graph tab before connect_or_launch reports ready"
```

---

### Task 2: GDScript addon reports `has_graph` from `ping`

**Files:**
- Modify: `addons/mm_live/live_server.gd:81-85` (`_cmd_ping`)
- Modify: `addons/mm_live/live_server.gd` (add new `_has_active_graph()` helper)

**Interfaces:**
- Consumes: nothing new -- `mm_globals.main_window.get_current_graph_edit()`
  and `.generator`, the same API every one of the five existing command
  handlers already calls (verified against real Material Maker source in
  the step-2 and step-3 plans; not re-verified here since it's the same
  call already shipped and reviewed).
- Produces: `ping`'s response dict gains a `has_graph: bool` key, consumed
  by Task 1's already-landed `_wait_for_ready_or_give_up` and
  `connect_or_launch` code (Task 1 is safe to land first because
  `.get("has_graph")` on a dict without the key is simply falsy).

There is no automated test for this task in isolation (see Global
Constraints) -- it is verified end-to-end by Task 3's real integration test.

- [ ] **Step 1: Add the `_has_active_graph()` helper**

In `addons/mm_live/live_server.gd`, add a new function. Place it right
after `_cmd_ping` (before `_cmd_get_graph`) so the file reads
ping-then-its-helper-then-the-mutating-handlers, matching the file's
existing top-to-bottom command order:

```gdscript
func _has_active_graph() -> bool:
	if mm_globals.main_window == null:
		return false
	var graph_edit: MMGraphEdit = mm_globals.main_window.get_current_graph_edit()
	return graph_edit != null and graph_edit.generator != null
```

- [ ] **Step 2: Extend `_cmd_ping` to report `has_graph`**

Replace the existing `_cmd_ping`:

```gdscript
func _cmd_ping() -> Dictionary:
	# mm_globals.main_window is null until the main scene finishes loading --
	# resolved fresh on every call, never cached, so a probe issued right
	# after launch correctly reports "not ready yet" instead of a stale null.
	return {"ok": true, "ready": mm_globals.main_window != null}
```

with:

```gdscript
func _cmd_ping() -> Dictionary:
	# mm_globals.main_window is null until the main scene finishes loading --
	# resolved fresh on every call, never cached, so a probe issued right
	# after launch correctly reports "not ready yet" instead of a stale null.
	# main_window resolving does NOT mean a graph tab exists yet -- the two
	# happen in separate boot steps, so has_graph is reported as its own
	# field rather than folded into `ready`; connect_or_launch on the Python
	# side is what decides how to combine them (both are required there).
	return {"ok": true, "ready": mm_globals.main_window != null,
			"has_graph": _has_active_graph()}
```

The five existing mutating/read command handlers
(`_cmd_get_graph`/`_cmd_add_node`/`_cmd_connect_nodes`/`_cmd_set_param`/
`_cmd_render`) are deliberately left unchanged: their own
`graph_edit == null or graph_edit.generator == null` guards still return
the same `"no active graph"` error they always have, but should now be
unreachable in practice once `connect_or_launch` (Task 1) refuses to
report a session ready until `has_graph` is true. Keeping them is
intentional defense-in-depth, not dead code to clean up -- they are what
protects a caller that bypasses `connect_or_launch` entirely (e.g. calling
`live.get_graph()` directly against a socket the caller found some other
way).

- [ ] **Step 3: Commit**

```bash
git add addons/mm_live/live_server.gd
git commit -m "feat(live): report whether a graph tab exists from ping"
```

---

### Task 3: Real integration verification

**Files:**
- Modify: `tests/test_live.py:588-609`
  (`test_connect_or_launch_gets_real_graph_from_default_new_material`)

**Interfaces:**
- Consumes: `live.ping()` (unchanged signature), `live.connect_or_launch()`
  (unchanged signature, now internally gated on `has_graph` per Tasks 1-2).
- Produces: nothing new for later tasks; this is the plan's own gate.

- [ ] **Step 1: Add a direct assertion that the real addon actually sends `has_graph`**

In `tests/test_live.py`, extend the existing integration test so it proves
the new field isn't just assumed but is really coming from the real,
committed GDScript:

```python
@pytest.mark.integration
def test_connect_or_launch_gets_real_graph_from_default_new_material(tmp_path):
    # Isolated overlay dir so this test never collides with (or clobbers) an
    # overlay a manual session might already have running.
    isolated_cfg = replace(cfg, live_overlay_dir=str(tmp_path / "mm_live_overlay"))

    session = live.connect_or_launch(cfg=isolated_cfg, launch_timeout=90.0)
    try:
        assert session.ok, session.error
        assert session.process is not None, (
            "attached to a pre-existing instance on port 8765 -- close it and rerun; "
            "this test must launch its own overlay to prove the committed addon works"
        )

        ping_result = live.ping()
        assert ping_result.ok, ping_result.error
        assert ping_result.data["has_graph"] is True, (
            "connect_or_launch reported ready, so the real addon must already be "
            "reporting has_graph=True by this point"
        )

        result = live.get_graph()
        assert result.ok, result.error
        graph = result.data["graph"]
        assert "nodes" in graph
        assert len(graph["nodes"]) >= 1
        assert any(n.get("type") == "material" for n in graph["nodes"])
    finally:
        session.close()
```

(Only the new `ping_result` block is added, right after the existing
`assert session.process is not None` block and before the existing
`get_graph` call.)

- [ ] **Step 2: Run the fast suite (sanity check before spending time on a real Godot launch)**

Run: `.venv\Scripts\python.exe -m pytest -q -m "not integration"`
Expected: 178 passed.

- [ ] **Step 3: Run this test for real against a real Godot launch**

Run: `.venv\Scripts\python.exe -m pytest tests/test_live.py -k default_new_material -v`
Expected: PASS. This launches a real Material Maker instance (can take
30-90s) and confirms `has_graph` is really `True` by the time
`connect_or_launch` returns, not just in the fake-server unit tests.

- [ ] **Step 4: Run the full live integration suite once more for full-stack confidence**

Run: `.venv\Scripts\python.exe -m pytest tests/test_live.py tests/test_server_live.py -m integration -v`
Expected: PASS (both live-control integration tests in `test_live.py` plus
`test_server_live.py`'s `test_live_tools_hold_a_real_session_against_material_maker`).

- [ ] **Step 5: Manually relaunch several times in a row to confirm the original repro is gone**

This is the direct empirical check: the bug was originally found by
relaunching Material Maker back-to-back and hitting `"no active graph"` 3
times in a row. Repeat that here. Using the venv Python directly (not
pytest, so each run is a fresh process with no leftover state):

```bash
for i in 1 2 3 4; do
  .venv/Scripts/python.exe -c "
from mm_mcp import live
from dataclasses import replace
from mm_mcp.config import load_config
import tempfile, os
cfg = replace(load_config(), live_overlay_dir=os.path.join(tempfile.mkdtemp(), 'overlay'))
session = live.connect_or_launch(cfg=cfg, launch_timeout=90.0)
assert session.ok, session.error
result = live.add_node('perlin', {}, cfg=cfg)
print('run $i:', 'OK' if result.ok else result.error)
session.close()
"
done
```

Expected: `run 1: OK` through `run 4: OK` -- zero `"no active graph"`
failures, versus the pre-fix behavior of 3 failures out of 4 runs recorded
in HANDOFF.md's session log. If any run still fails with `"no active
graph"`, the fix is incomplete -- stop and re-examine Tasks 1-2 rather than
proceeding to Task 4.

- [ ] **Step 6: Commit**

```bash
git add tests/test_live.py
git commit -m "test(live): verify has_graph is real and the readiness race is closed"
```

---

### Task 4: Correct the design spec's readiness constraint

**Files:**
- Modify: `docs/superpowers/specs/2026-08-26-live-control-addon-design.md:231-234`

**Interfaces:** None -- documentation only.

- [ ] **Step 1: Update the spec's constraint bullet**

Replace:

```markdown
  - `mm_globals.main_window` is **null at autoload `_ready()`** (autoloads start
    before the main scene). Resolve it lazily per command, never cache at boot.
    The session manager's readiness probe should poll `ping` until
    `main_window` is wired before issuing graph commands.
```

with:

```markdown
  - `mm_globals.main_window` is **null at autoload `_ready()`** (autoloads start
    before the main scene). Resolve it lazily per command, never cache at boot.
    The session manager's readiness probe should poll `ping` until
    `main_window` is wired before issuing graph commands.
  - **Amendment (2026-08-27, found during Phase 5 step 4's manual
    verification, fixed by `docs/superpowers/plans/
    2026-08-27-connect-or-launch-readiness-race.md`):** `main_window`
    resolving does NOT mean a graph tab exists yet -- the default
    new-material graph tab is created in a later boot step. `ping` reports
    this separately as `has_graph`; `connect_or_launch` must poll until
    BOTH `ready` and `has_graph` are true, not `ready` alone, or the first
    mutating call can race ahead of tab creation and fail with `"no active
    graph"`.
```

- [ ] **Step 2: Commit**

```bash
git add docs/superpowers/specs/2026-08-26-live-control-addon-design.md
git commit -m "docs: amend the live-control spec's readiness constraint"
```

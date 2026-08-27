# Phase 5 Addon Skeleton Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the real live-control addon (`addons/mm_live/live_server.gd`) with
just a socket server plus `ping`/`get_graph`, and a matching Python client
(`src/mm_mcp/live.py`) that can attach to or launch it via the overlay from
step 1, so an external Python process can ask a running Material Maker window
"are you ready?" and "what's on the active tab right now?" and get real
answers back.

**Architecture:** Two new pieces either side of the socket built in step 1's
overlay: a thin GDScript autoload (`addons/mm_live/live_server.gd`) that opens
a `TCPServer` and answers two JSON-line commands, and a Python module
(`src/mm_mcp/live.py`) with a low-level one-shot request/response client plus
a `connect_or_launch()` that probes the fixed port, rebuilds/launches the
overlay via `overlay.py`'s already-shipped `ensure_overlay` if nothing
answers, and polls until the addon reports it's actually ready. Mutating
commands, render, and the MCP tool surface are explicitly out of scope —
those are steps 3-4.

**Tech Stack:** GDScript (Godot 4.7), Python 3.13 stdlib (`socket`,
`subprocess`, `json`, `time`), pytest with a hand-rolled fake TCP server for
protocol tests (no Godot needed for those).

**Spec:** [docs/superpowers/specs/2026-08-26-live-control-addon-design.md](../specs/2026-08-26-live-control-addon-design.md)
— this plan implements sub-plan step 2 ("Addon skeleton") only. Step 1
(overlay builder) is already merged (`src/mm_mcp/overlay.py`). Steps 3-4
(mutating commands, MCP tool surface) are separate future plans; do not
build them here.

## Global Constraints

- **Windows-only project** (see STATUS.md Phase 4) — no new cross-platform
  requirement introduced here.
- **`LIVE_PORT = 8765`, fixed, on both sides.** There is no shared-constant
  mechanism across GDScript and Python — the literal `8765` must match in
  `addons/mm_live/live_server.gd` and `src/mm_mcp/live.py`. A comment at each
  site says so.
- **The addon lives at top-level `addons/mm_live/`, a sibling of `src/`, not
  inside `src/mm_mcp/`.** Unlike `preview_project/` (which ships inside the
  wheel via `tool.setuptools.package-data`), this addon will NOT ship in a
  built wheel. That's acceptable under Phase 4's current decision
  (GitHub-clone distribution, PyPI on hold — see STATUS.md); flag it as a
  known gap for whoever revisits PyPI packaging, don't silently fix it here.
- **Read-only this step.** Only `ping` and `get_graph` exist. No validation
  logic lives in the addon — it stays deliberately thin per the spec, because
  everything mutating (step 3) arrives pre-validated from the Python side.
- **Lazy `main_window` resolution, never cached.** `mm_globals.main_window` is
  null at autoload `_ready()` (autoloads start before the main scene) —
  resolve it fresh inside every command handler, never store it in a `_ready`
  callback. `ping`'s response includes a `ready` flag so a caller can poll
  until it's true instead of guessing.
- **Never `PIPE` the launched Godot's stdout without draining it.** An
  undrained pipe fills and blocks the child process — this actually happened
  during the Phase 5 feasibility spike. Redirect stdout to a file (or
  `DEVNULL` for the throwaway manual check in Task 1) instead.
- **`steam_appid.txt` survival is already handled.** `overlay.py`'s
  `ensure_overlay` copies the whole checkout wholesale, so this doesn't need
  new work here — just don't bypass `ensure_overlay` when launching.
- **The Task 5 integration test opens a real, visible Material Maker GUI
  window** (unlike the existing headless `--export-material` integration
  tests in `test_render.py`/`test_preview.py`). That's expected, not a bug —
  live mode is inherently GUI-mode. It's still marked `@pytest.mark.integration`
  and skipped by `-m "not integration"` like the others.

---

### Task 1: Addon skeleton — `ping`/`get_graph` over a raw socket

**Files:**
- Create: `addons/mm_live/live_server.gd`

**Interfaces:**
- Consumes: nothing from this repo's Python side. Reads `mm_globals.main_window`
  (a real Material Maker autoload singleton, confirmed present at
  `material_maker/globals.gd:6` in the `z-Git\material-maker` checkout) and
  calls `.get_current_graph_edit()` → `MMGraphEdit.generator.serialize()`
  (confirmed present at `material_maker/main_window.gd:353` and
  `material_maker/panels/graph_edit/graph_edit.gd:2,25`).
- Produces: a `TCPServer` listening on `127.0.0.1:8765` once this script runs
  as a Godot autoload. Line-delimited JSON protocol: send `{"cmd": "ping"}\n`
  or `{"cmd": "get_graph"}\n`, get one JSON line back, connection closes
  after one exchange (no persistent session state in the addon).

This task has no Python unit test — GDScript isn't under pytest, and there is
no GDScript test harness in this project (matches `preview_project/`'s
Godot-side code, which is also only verified via integration tests, not
unit tests). Step 2's automated coverage (Task 3-4) tests the *Python side*
of this protocol against a fake stand-in server. This task's own correctness
is verified by a manual smoke check (Step 2 below) and, later, the real
integration test in Task 5.

- [ ] **Step 1: Write the addon**

```gdscript
# addons/mm_live/live_server.gd
extends Node

## mm_live: thin socket server exposing live-control commands to an external
## Python client. Registered as a Godot [autoload] entry by overlay.py so it
## starts automatically whenever the disposable overlay project runs.
##
## LIVE_PORT below MUST match mm_mcp.live.LIVE_PORT on the Python side --
## there is no shared-constant mechanism across GDScript/Python, so keep
## both literals in sync by hand if this ever changes.
##
## This step only implements "ping" and "get_graph". Mutating commands
## (add_node/connect_nodes/set_param/render) are Phase 5 build step 3.
## Deliberately no validation here -- everything mutating arrives
## pre-validated from the Python side (see the design spec).

const LIVE_PORT := 8765

var _server := TCPServer.new()
var _connections: Array = []  # each entry: {peer: StreamPeerTCP, buf: PackedByteArray}


func _ready() -> void:
	var err := _server.listen(LIVE_PORT, "127.0.0.1")
	if err != OK:
		push_error("mm_live: failed to listen on port %d (error %d)" % [LIVE_PORT, err])


func _process(_delta: float) -> void:
	while _server.is_connection_available():
		_connections.append({"peer": _server.take_connection(), "buf": PackedByteArray()})

	var i := _connections.size() - 1
	while i >= 0:
		var entry: Dictionary = _connections[i]
		var peer: StreamPeerTCP = entry["peer"]
		peer.poll()
		if peer.get_status() != StreamPeerTCP.STATUS_CONNECTED:
			_connections.remove_at(i)
			i -= 1
			continue

		var avail := peer.get_available_bytes()
		if avail > 0:
			var chunk = peer.get_partial_data(avail)
			if chunk[0] == OK:
				entry["buf"].append_array(chunk[1])

		var newline_idx: int = entry["buf"].find(10)  # ASCII "\n"
		if newline_idx != -1:
			var line: String = entry["buf"].slice(0, newline_idx).get_string_from_utf8()
			_dispatch(peer, line)
			_connections.remove_at(i)

		i -= 1


func _dispatch(peer: StreamPeerTCP, line: String) -> void:
	var response: Dictionary
	var parsed = JSON.parse_string(line)
	if typeof(parsed) != TYPE_DICTIONARY or not parsed.has("cmd"):
		response = {"ok": false, "error": "malformed command"}
	else:
		match parsed["cmd"]:
			"ping":
				response = _cmd_ping()
			"get_graph":
				response = _cmd_get_graph()
			_:
				response = {"ok": false, "error": "unknown command: %s" % str(parsed["cmd"])}
	peer.put_data((JSON.stringify(response) + "\n").to_utf8_buffer())


func _cmd_ping() -> Dictionary:
	# mm_globals.main_window is null until the main scene finishes loading --
	# resolved fresh on every call, never cached, so a probe issued right
	# after launch correctly reports "not ready yet" instead of a stale null.
	return {"ok": true, "ready": mm_globals.main_window != null}


func _cmd_get_graph() -> Dictionary:
	if mm_globals.main_window == null:
		return {"ok": false, "error": "main_window not ready"}
	var graph_edit: MMGraphEdit = mm_globals.main_window.get_current_graph_edit()
	if graph_edit == null or graph_edit.generator == null:
		return {"ok": false, "error": "no active graph"}
	return {"ok": true, "graph": graph_edit.generator.serialize()}
```

- [ ] **Step 2: Manually verify the socket server actually answers**

This builds a throwaway overlay pointed at the addon just written, launches
it, sends a raw `ping` over a socket, and tears it down. Uses `ensure_overlay`
directly (already shipped) rather than `live.py` (doesn't exist until Task 3).

Run:

```bash
.venv\Scripts\python.exe -c "
import socket, subprocess, time
from mm_mcp.overlay import ensure_overlay

overlay_dir = ensure_overlay(
    r'C:\Projects-local\z-Git\material-maker',
    r'C:\Projects-local\Tool-MaterialMaker-MCP\addons\mm_live',
    r'C:\Projects-local\Tool-MaterialMaker-MCP\output\mm_live_overlay_manual_check')

proc = subprocess.Popen(
    [r'C:\Users\Grayson\AppData\Local\Godot\Godot_v4.7.1-stable_win64_console.exe', '--path', overlay_dir],
    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
try:
    deadline = time.time() + 30
    sock = None
    while time.time() < deadline:
        try:
            sock = socket.create_connection(('127.0.0.1', 8765), timeout=1)
            break
        except OSError:
            time.sleep(0.5)
    assert sock is not None, 'never started listening on port 8765'
    sock.sendall(b'{\"cmd\": \"ping\"}\n')
    sock.settimeout(5)
    reply = sock.recv(4096)
    print('PING REPLY:', reply)
    sock.close()
finally:
    proc.terminate()
    proc.wait(timeout=10)
"
```

Expected: a Material Maker window briefly opens (this is real GUI mode, not
headless), and the script prints something like
`PING REPLY: b'{"ok":true,"ready":false}\n'` (or `"ready":true` if the main
window happened to finish loading before the ping landed — either is fine;
what matters is `"ok":true`, proving the socket server itself is alive and
answering). The window closes when the script terminates the process.

If this fails: check `.godot/mono_crash` or Godot's own stderr by rerunning
with `stdout=subprocess.PIPE, stderr=subprocess.PIPE` temporarily to see the
script error (a GDScript syntax error would show there). Common cause: a typo
in the `[autoload]` line, or `mm_globals` not resolving (means the addon
script itself failed to parse — check the Godot console output).

- [ ] **Step 3: Commit**

```bash
git add addons/mm_live/live_server.gd
git commit -m "feat(live): add socket server addon skeleton (ping/get_graph)"
```

---

### Task 2: `Config` gets a `live_overlay_dir` field

**Files:**
- Modify: `src/mm_mcp/config.py`
- Test: `tests/test_config.py`

**Interfaces:**
- Consumes: nothing from Task 1.
- Produces: `Config.live_overlay_dir: str` — mirrors `output_dir`'s existing
  pattern exactly: `MM_LIVE_OVERLAY_DIR` env override, else
  `<cwd>/mm_live_overlay`. This is where `live.py` (Task 3-4) tells
  `ensure_overlay` to build the disposable overlay, matching step 1's design
  note that `overlay_dir`'s default location is a decision for whichever
  module first needs one.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_config.py (append)
def test_live_overlay_dir_defaults_to_cwd_subfolder():
    cfg = load_config()
    assert cfg.live_overlay_dir == os.path.join(os.getcwd(), "mm_live_overlay")


def test_live_overlay_dir_respects_override():
    cfg = load_config(overrides={"MM_LIVE_OVERLAY_DIR": r"C:\somewhere\overlay"})
    assert cfg.live_overlay_dir == r"C:\somewhere\overlay"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv\Scripts\python.exe -m pytest tests/test_config.py -v`
Expected: FAIL — `Config` has no attribute `live_overlay_dir`.

- [ ] **Step 3: Write minimal implementation**

```python
# src/mm_mcp/config.py — add to _DEFAULTS
_DEFAULTS = {
    "MM_GODOT_BINARY": "",
    "MM_PROJECT_PATH": "",
    "MM_OUTPUT_DIR": "",
    "MM_LIVE_OVERLAY_DIR": "",
}
```

```python
# src/mm_mcp/config.py — add a field to the Config dataclass, after examples_dir
@dataclass
class Config:
    godot_binary: str
    console_binary: str
    project_path: str
    output_dir: str
    nodes_dir: str
    examples_dir: str
    live_overlay_dir: str
```

```python
# src/mm_mcp/config.py — in load_config(), after output_dir is computed
    live_overlay_dir = env["MM_LIVE_OVERLAY_DIR"] or os.path.join(os.getcwd(), "mm_live_overlay")
```

```python
# src/mm_mcp/config.py — add live_overlay_dir to the Config(...) call at the
# end of load_config()
    return Config(
        godot_binary=env["MM_GODOT_BINARY"],
        console_binary=_resolve_console(env["MM_GODOT_BINARY"]),
        project_path=project_path,
        output_dir=output_dir,
        nodes_dir=os.path.join(project_path, "addons", "material_maker", "nodes"),
        examples_dir=os.path.join(project_path, "material_maker", "examples"),
        live_overlay_dir=live_overlay_dir,
    )
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `.venv\Scripts\python.exe -m pytest tests/test_config.py -v`
Expected: 9 passed (7 existing + 2 new)

- [ ] **Step 5: Document the new optional override and commit**

Add a line to `.env.example` after the existing `MM_OUTPUT_DIR` entry,
matching that entry's style:

```
# Where the disposable live-control overlay is built (optional; defaults to
# ./mm_live_overlay under the current working directory if unset)
MM_LIVE_OVERLAY_DIR=
```

```bash
git add src/mm_mcp/config.py tests/test_config.py .env.example
git commit -m "feat(config): add live_overlay_dir"
```

---

### Task 3: `live.py` — low-level protocol client (`ping`, `get_graph`)

**Files:**
- Create: `src/mm_mcp/live.py`
- Test: `tests/test_live.py`

**Interfaces:**
- Consumes: nothing from Tasks 1-2 (this task's tests use a fake TCP server,
  not the real addon or real Config).
- Produces:
  - `LiveResult` dataclass: `ok: bool`, `data: dict | None = None`,
    `error: str | None = None`.
  - `_send_command(cmd: dict, host: str = LIVE_HOST, port: int = LIVE_PORT, timeout: float = 5.0) -> LiveResult`
    — the shared one-shot connect/send/recv/close primitive every command
    function calls.
  - `ping(host: str = LIVE_HOST, port: int = LIVE_PORT, timeout: float = 5.0) -> LiveResult`
  - `get_graph(host: str = LIVE_HOST, port: int = LIVE_PORT, timeout: float = 5.0) -> LiveResult`
  - Module constants: `LIVE_HOST = "127.0.0.1"`, `LIVE_PORT = 8765` (must
    match `addons/mm_live/live_server.gd`'s `LIVE_PORT`).

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_live.py
import json
import socket
import threading
import time
from mm_mcp import live


class _FakeLiveServer:
    """Minimal stand-in for live_server.gd: accepts one line-JSON command per
    connection, replies with whatever `responder(cmd_dict)` returns.

    responder's return value controls what's sent back:
    - a dict -> JSON-encoded + newline (the normal case)
    - bytes -> sent verbatim (for malformed-response tests)
    - None -> nothing sent, connection just closes (for early-close tests)
    """

    def __init__(self, responder, port: int = 0):
        self._responder = responder
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._sock.bind(("127.0.0.1", port))
        self._sock.listen(5)
        self.port = self._sock.getsockname()[1]
        self._stop = False
        self._thread = threading.Thread(target=self._serve, daemon=True)
        self._thread.start()

    def _serve(self):
        self._sock.settimeout(0.2)
        while not self._stop:
            try:
                conn, _ = self._sock.accept()
            except socket.timeout:
                continue
            with conn:
                buf = b""
                conn.settimeout(5.0)
                try:
                    while b"\n" not in buf:
                        chunk = conn.recv(4096)
                        if not chunk:
                            break
                        buf += chunk
                except socket.timeout:
                    continue
                if not buf:
                    continue
                cmd = json.loads(buf.split(b"\n", 1)[0].decode("utf-8"))
                response = self._responder(cmd)
                if response is None:
                    continue
                try:
                    if isinstance(response, bytes):
                        conn.sendall(response)
                    else:
                        conn.sendall((json.dumps(response) + "\n").encode("utf-8"))
                except OSError:
                    pass

    def stop(self):
        self._stop = True
        self._thread.join(timeout=1)
        self._sock.close()


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def test_ping_returns_ok_and_ready_from_fake_server():
    server = _FakeLiveServer(lambda cmd: {"ok": True, "ready": True})
    try:
        result = live.ping(host="127.0.0.1", port=server.port)
        assert result.ok
        assert result.data["ready"] is True
    finally:
        server.stop()


def test_get_graph_returns_graph_payload_from_fake_server():
    fake_graph = {
        "nodes": [{"name": "material", "type": "material",
                   "node_position": {"x": 0, "y": 0}, "parameters": {}}],
        "connections": [],
    }
    server = _FakeLiveServer(lambda cmd: {"ok": True, "graph": fake_graph})
    try:
        result = live.get_graph(host="127.0.0.1", port=server.port)
        assert result.ok
        assert result.data["graph"] == fake_graph
    finally:
        server.stop()


def test_send_command_reports_server_side_failure():
    server = _FakeLiveServer(lambda cmd: {"ok": False, "error": "main_window not ready"})
    try:
        result = live.get_graph(host="127.0.0.1", port=server.port)
        assert not result.ok
        assert result.error == "main_window not ready"
    finally:
        server.stop()


def test_send_command_handles_malformed_json_response():
    server = _FakeLiveServer(lambda cmd: b"not json at all\n")
    try:
        result = live.ping(host="127.0.0.1", port=server.port)
        assert not result.ok
        assert "malformed" in result.error.lower()
    finally:
        server.stop()


def test_send_command_handles_connection_closed_early():
    server = _FakeLiveServer(lambda cmd: None)
    try:
        result = live.ping(host="127.0.0.1", port=server.port)
        assert not result.ok
        assert "closed" in result.error.lower()
    finally:
        server.stop()


def test_send_command_handles_connection_refused():
    port = _free_port()  # nothing listening on this port
    result = live.ping(host="127.0.0.1", port=port)
    assert not result.ok
    assert "could not reach" in result.error.lower()


def _slow_ping_responder(cmd):
    time.sleep(1.0)
    return {"ok": True, "ready": True}


def test_send_command_handles_timeout():
    server = _FakeLiveServer(_slow_ping_responder)
    try:
        result = live.ping(host="127.0.0.1", port=server.port, timeout=0.2)
        assert not result.ok
        assert "timed out" in result.error.lower()
    finally:
        server.stop()
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv\Scripts\python.exe -m pytest tests/test_live.py -v`
Expected: FAIL (collection error) — `mm_mcp.live` module does not exist yet.

- [ ] **Step 3: Write minimal implementation**

```python
# src/mm_mcp/live.py
import json
import socket
from dataclasses import dataclass

# Must match addons/mm_live/live_server.gd's LIVE_PORT -- no shared-constant
# mechanism exists across GDScript and Python, so keep both literals in sync
# by hand if this ever changes.
LIVE_HOST = "127.0.0.1"
LIVE_PORT = 8765


@dataclass
class LiveResult:
    ok: bool
    data: dict | None = None
    error: str | None = None


def _send_command(cmd: dict, host: str = LIVE_HOST, port: int = LIVE_PORT,
                   timeout: float = 5.0) -> LiveResult:
    """Open a fresh TCP connection, send one JSON line, read one JSON line
    back, close. One-shot per call, matching the addon's per-connection
    dispatch -- there is no persistent session state on either side."""
    try:
        sock = socket.create_connection((host, port), timeout=timeout)
    except OSError as exc:
        return LiveResult(ok=False, error=f"could not reach live server at {host}:{port}: {exc}")

    try:
        with sock:
            sock.sendall((json.dumps(cmd) + "\n").encode("utf-8"))
            sock.settimeout(timeout)
            buf = b""
            try:
                while b"\n" not in buf:
                    chunk = sock.recv(4096)
                    if not chunk:
                        return LiveResult(ok=False,
                                           error="connection closed before a response line arrived")
                    buf += chunk
            except TimeoutError:
                return LiveResult(ok=False,
                                   error=f"timed out waiting for a response from {host}:{port}")
    except OSError as exc:
        return LiveResult(ok=False, error=f"live server connection failed: {exc}")

    line = buf.split(b"\n", 1)[0]
    try:
        data = json.loads(line.decode("utf-8"))
    except (ValueError, UnicodeDecodeError) as exc:
        return LiveResult(ok=False, error=f"malformed response from live server: {exc}")
    if not isinstance(data, dict):
        return LiveResult(ok=False, error="live server response was not a JSON object")
    if not data.get("ok", False):
        return LiveResult(ok=False, error=data.get("error", "live server reported failure"))
    return LiveResult(ok=True, data=data)


def ping(host: str = LIVE_HOST, port: int = LIVE_PORT, timeout: float = 5.0) -> LiveResult:
    return _send_command({"cmd": "ping"}, host, port, timeout)


def get_graph(host: str = LIVE_HOST, port: int = LIVE_PORT, timeout: float = 5.0) -> LiveResult:
    return _send_command({"cmd": "get_graph"}, host, port, timeout)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `.venv\Scripts\python.exe -m pytest tests/test_live.py -v`
Expected: 7 passed

- [ ] **Step 5: Commit**

```bash
git add src/mm_mcp/live.py tests/test_live.py
git commit -m "feat(live): add low-level ping/get_graph protocol client"
```

---

### Task 4: `live.py` — `connect_or_launch` (attach-or-launch, poll for ready)

**Files:**
- Modify: `src/mm_mcp/live.py`
- Modify: `tests/test_live.py`

**Interfaces:**
- Consumes: `_send_command`/`ping` (Task 3), `Config`/`load_config` (from
  `mm_mcp.config`), `ensure_overlay` (from `mm_mcp.overlay`, already shipped
  in step 1), `Config.live_overlay_dir` (Task 2).
- Produces:
  - `LiveSession` dataclass: `ok: bool`, `process: subprocess.Popen | None = None`,
    `error: str | None = None`, with a `close()` method that terminates the
    process if this session launched one (no-op if it attached to an
    already-running instance).
  - `connect_or_launch(cfg: Config | None = None, host: str = LIVE_HOST, port: int = LIVE_PORT, launch_timeout: float = 60.0) -> LiveSession`
  - Private helpers: `_is_listening(host, port) -> bool`,
    `_launch_command(cfg, overlay_dir) -> list[str]` (pure, directly testable
    like `preview.py`'s `_build_command`), `_launch_overlay(cfg) -> subprocess.Popen`,
    `_terminate(process) -> None`.

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_live.py (append)
from mm_mcp.config import load_config

cfg = load_config()


class _FakeProcess:
    def __init__(self):
        self.terminated = False
        self.killed = False

    def terminate(self):
        self.terminated = True

    def kill(self):
        self.killed = True

    def wait(self, timeout=None):
        return 0


def test_launch_command_uses_console_binary_and_overlay_path():
    cmd = live._launch_command(cfg, r"C:\somewhere\overlay")
    assert cmd == [cfg.console_binary, "--path", r"C:\somewhere\overlay"]


def test_connect_or_launch_attaches_when_already_listening(monkeypatch):
    server = _FakeLiveServer(lambda cmd: {"ok": True, "ready": True})
    launched = {"called": False}

    def _no_launch(passed_cfg):
        launched["called"] = True
        return _FakeProcess()

    monkeypatch.setattr(live, "_launch_overlay", _no_launch)
    try:
        session = live.connect_or_launch(cfg=cfg, host="127.0.0.1", port=server.port,
                                          launch_timeout=2.0)
        assert session.ok
        assert session.process is None
        assert launched["called"] is False
        session.close()  # no-op: we didn't launch anything
    finally:
        server.stop()


def test_connect_or_launch_launches_when_not_listening(monkeypatch):
    picked_port = _free_port()
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
        assert session.ok
        assert session.process is fake_process
    finally:
        if started_server["server"] is not None:
            started_server["server"].stop()


def test_connect_or_launch_terminates_process_on_timeout(monkeypatch):
    picked_port = _free_port()  # nothing ever listens here
    fake_process = _FakeProcess()
    monkeypatch.setattr(live, "_launch_overlay", lambda passed_cfg: fake_process)

    session = live.connect_or_launch(cfg=cfg, host="127.0.0.1", port=picked_port,
                                      launch_timeout=1.0)

    assert not session.ok
    assert session.error
    assert fake_process.terminated
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv\Scripts\python.exe -m pytest tests/test_live.py -v`
Expected: FAIL — `live._launch_command`/`live.connect_or_launch`/`live._launch_overlay` not defined.

- [ ] **Step 3: Write minimal implementation**

```python
# src/mm_mcp/live.py — add imports at the top
import os
import subprocess
import time
from mm_mcp.config import Config, load_config
from mm_mcp.overlay import ensure_overlay

# addons/mm_live/ is a top-level sibling of src/, not bundled inside
# src/mm_mcp/ -- unlike preview_project/, it does NOT ship in a built wheel.
# Acceptable under Phase 4's current GitHub-clone distribution decision
# (PyPI on hold); revisit if that changes.
_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_ADDON_PATH = os.path.join(_REPO_ROOT, "addons", "mm_live")
```

```python
# src/mm_mcp/live.py — append
@dataclass
class LiveSession:
    ok: bool
    process: subprocess.Popen | None = None
    error: str | None = None

    def close(self) -> None:
        """Terminate the Godot process this session launched. No-op if this
        session attached to an already-running instance instead."""
        if self.process is not None:
            _terminate(self.process)
            self.process = None


def _is_listening(host: str, port: int) -> bool:
    try:
        with socket.create_connection((host, port), timeout=0.5):
            return True
    except OSError:
        return False


def _terminate(process: subprocess.Popen) -> None:
    process.terminate()
    try:
        process.wait(timeout=10)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait(timeout=10)


def _launch_command(cfg: Config, overlay_dir: str) -> list[str]:
    return [cfg.console_binary, "--path", overlay_dir]


def _launch_overlay(cfg: Config) -> subprocess.Popen:
    overlay_dir = ensure_overlay(cfg.project_path, _ADDON_PATH, cfg.live_overlay_dir)
    os.makedirs(cfg.output_dir, exist_ok=True)
    log_file = open(os.path.join(cfg.output_dir, "mm_live.log"), "w", encoding="utf-8")
    # Godot's stdout must not be PIPE'd without draining it -- an undrained
    # pipe fills and blocks the child (confirmed during the Phase 5
    # feasibility spike). Redirect to a file instead.
    return subprocess.Popen(_launch_command(cfg, overlay_dir),
                             stdout=log_file, stderr=subprocess.STDOUT)


def connect_or_launch(cfg: Config | None = None, host: str = LIVE_HOST,
                       port: int = LIVE_PORT, launch_timeout: float = 60.0) -> LiveSession:
    """Probe (host, port); if nothing answers, rebuild the overlay if stale
    and launch Material Maker against it. Either way, poll ping() until the
    addon reports main_window is wired -- never assume the first successful
    ping means the GUI has finished loading (see the spec's "lazy
    main_window resolution" constraint) -- or give up after launch_timeout.

    Attaching to an already-running instance never launches a process, so
    the returned session's close() is a no-op for that case: we only own the
    lifecycle of a process we started ourselves.
    """
    cfg = cfg or load_config()
    process = None
    if not _is_listening(host, port):
        process = _launch_overlay(cfg)

    deadline = time.monotonic() + launch_timeout
    last_error = "timed out waiting for the live server to become ready"
    while time.monotonic() < deadline:
        result = ping(host, port)
        if result.ok and result.data.get("ready"):
            return LiveSession(ok=True, process=process)
        if not result.ok:
            last_error = result.error
        time.sleep(0.5)

    if process is not None:
        _terminate(process)
    return LiveSession(ok=False, error=last_error, process=None)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `.venv\Scripts\python.exe -m pytest tests/test_live.py -v`
Expected: 11 passed (7 from Task 3 + 4 new)

- [ ] **Step 5: Commit**

```bash
git add src/mm_mcp/live.py tests/test_live.py
git commit -m "feat(live): add connect_or_launch (attach-or-launch, poll for ready)"
```

---

### Task 5: Real integration test — gate for this step

**Files:**
- Modify: `tests/test_live.py`

**Interfaces:**
- Consumes: `live.connect_or_launch` (Task 4), `live.get_graph` (Task 3), the
  real `addons/mm_live/live_server.gd` (Task 1), the real
  `z-Git\material-maker` checkout via `load_config()`.
- Produces: nothing new — this is the spec's step-2 gate: "Python connects,
  launches Material Maker via the overlay, gets a real graph back for a
  bundled example," reproducing the earlier feasibility spike's result
  through the real, committed code path instead of throwaway scratchpad code.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_live.py (append)
import pytest
from dataclasses import replace


@pytest.mark.integration
def test_connect_or_launch_gets_real_graph_from_default_new_material(tmp_path):
    # Isolated overlay dir so this test never collides with (or clobbers) an
    # overlay a manual session might already have running.
    isolated_cfg = replace(cfg, live_overlay_dir=str(tmp_path / "mm_live_overlay"))

    session = live.connect_or_launch(cfg=isolated_cfg, launch_timeout=90.0)
    try:
        assert session.ok, session.error

        result = live.get_graph()
        assert result.ok, result.error
        graph = result.data["graph"]
        assert "nodes" in graph
        assert len(graph["nodes"]) >= 1
        assert any(n.get("type") == "material" for n in graph["nodes"])
    finally:
        session.close()
```

- [ ] **Step 2: Run the test**

Run: `.venv\Scripts\python.exe -m pytest tests/test_live.py -v -m integration`
Expected: PASS. A real Material Maker window opens (visible), the test
connects over the fixed port, reads back the default new-material graph (one
`material`-type node, matching what the earlier feasibility spike found), and
the window closes when the session's `close()` terminates the process.

If it fails: check `<tmp_path>/mm_live_overlay` was actually built (the
overlay builder from step 1 is already proven, so this would point at
something wrong in Task 1's `_dispatch`/`_cmd_get_graph`, or the `LIVE_PORT`
mismatch between `live_server.gd` and `live.py`). `output/mm_live.log` (real
`cfg.output_dir`, not the isolated test one) has nothing useful for a
`tmp_path`-isolated run — temporarily point `isolated_cfg.output_dir` at a
real path and rerun to capture Godot's own log if needed.

- [ ] **Step 3: Run the full suite one more time**

Run: `.venv\Scripts\python.exe -m pytest -q -m "not integration"`
Expected: all previously-passing tests plus the 2 new `test_config.py` tests
and the 11 new fast `test_live.py` tests green (147 total, up from 134).

- [ ] **Step 4: Commit**

```bash
git add tests/test_live.py
git commit -m "test(live): integration-verify ping/get_graph against real Material Maker"
```

---

## Gate (matches the spec's step-2 gate)

```bash
.venv\Scripts\python.exe -m pytest -q -m "not integration"
```
Expected: 147 passed.

```bash
.venv\Scripts\python.exe -m pytest -q tests/test_live.py -m integration
```
Expected: 1 passed — "Python connects, launches Material Maker via the
overlay, gets a real graph back for a bundled example" (the default
new-material graph, per the spec's step-2 gate wording).

## Explicitly out of scope for this plan

- **Mutating commands** (`add_node`/`connect_nodes`/`set_param`/`render`) in
  both the addon and `live.py` — spec sub-plan step 3. The `await`-based
  `create_nodes` constraint and the render-handler-is-unverified risk noted
  in the spec are step 3's problems, not this plan's.
- **Any MCP tool surface** (`server.py` changes: `live_start`/`live_get_graph`/
  `live_apply`/`live_render`) — spec sub-plan step 4.
- **Structured `Problem`-shaped error responses matching `validate_graph`'s
  shape** for live-side failures — the spec calls for this on mutating
  commands specifically ("Mutations referencing stale state... return a
  structured problem"); `ping`/`get_graph` failures are read-only and use the
  simpler `{"ok": false, "error": "..."}` shape already built here.
- **Un-hardcoding `LIVE_PORT`** (e.g. via Config or an env var) — YAGNI for a
  single fixed local addon; revisit only if a real conflict shows up.

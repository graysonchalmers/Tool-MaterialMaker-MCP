# tests/test_live.py
import inspect
import json
import os
import socket
import threading
import time
from dataclasses import replace
import pytest
from mm_mcp import live, render


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


def test_clear_graph_sends_clear_graph_command():
    received = {}

    def responder(cmd):
        received.update(cmd)
        return {"ok": True}

    server = _FakeLiveServer(responder)
    try:
        result = live.clear_graph(host="127.0.0.1", port=server.port)
        assert result.ok
        assert received == {"cmd": "clear_graph"}
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


from mm_mcp.config import load_config

cfg = load_config()


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


def test_disconnect_nodes_sends_command_when_connection_exists(monkeypatch):
    fake_graph = {"nodes": [
        {"name": "perlin_1", "type": "perlin", "node_position": {"x": 0, "y": 0}, "parameters": {}},
        {"name": "warp_1", "type": "warp", "node_position": {"x": 0, "y": 0}, "parameters": {}},
    ], "connections": [{"from": "perlin_1", "from_port": 0, "to": "warp_1", "to_port": 0}]}
    received = {}

    def responder(cmd):
        if cmd["cmd"] == "get_graph":
            return {"ok": True, "graph": fake_graph}
        received.update(cmd)
        return {"ok": True}

    server = _FakeLiveServer(responder)
    try:
        result = live.disconnect_nodes("perlin_1", 0, "warp_1", 0,
                                        host="127.0.0.1", port=server.port)
        assert result.ok
        assert received == {"cmd": "disconnect_nodes", "from": "perlin_1", "from_port": 0,
                             "to": "warp_1", "to_port": 0}
    finally:
        server.stop()


def test_disconnect_nodes_reports_missing_connection_without_contacting_server():
    fake_graph = {"nodes": [
        {"name": "perlin_1", "type": "perlin", "node_position": {"x": 0, "y": 0}, "parameters": {}},
        {"name": "warp_1", "type": "warp", "node_position": {"x": 0, "y": 0}, "parameters": {}},
    ], "connections": []}  # no connection between them
    calls = []

    def responder(cmd):
        calls.append(cmd["cmd"])
        return {"ok": True, "graph": fake_graph}

    server = _FakeLiveServer(responder)
    try:
        result = live.disconnect_nodes("perlin_1", 0, "warp_1", 0,
                                        host="127.0.0.1", port=server.port)
        assert not result.ok
        assert "no connection" in result.error.lower()
        assert calls == ["get_graph"]  # disconnect_nodes was never sent
    finally:
        server.stop()


def test_reposition_node_sends_command_when_node_exists():
    fake_graph = {"nodes": [
        {"name": "perlin_1", "type": "perlin", "node_position": {"x": 0, "y": 0}, "parameters": {}},
    ], "connections": []}
    received = {}

    def responder(cmd):
        if cmd["cmd"] == "get_graph":
            return {"ok": True, "graph": fake_graph}
        received.update(cmd)
        return {"ok": True}

    server = _FakeLiveServer(responder)
    try:
        result = live.reposition_node("perlin_1", 100.0, 200.0,
                                       host="127.0.0.1", port=server.port)
        assert result.ok
        assert received == {"cmd": "reposition_node", "name": "perlin_1", "x": 100.0, "y": 200.0}
    finally:
        server.stop()


def test_reposition_node_reports_missing_node_without_contacting_server():
    fake_graph = {"nodes": [], "connections": []}  # the target node doesn't exist
    calls = []

    def responder(cmd):
        calls.append(cmd["cmd"])
        return {"ok": True, "graph": fake_graph}

    server = _FakeLiveServer(responder)
    try:
        result = live.reposition_node("does_not_exist", 0.0, 0.0,
                                       host="127.0.0.1", port=server.port)
        assert not result.ok
        assert "does_not_exist" in result.error
        assert calls == ["get_graph"]  # reposition_node was never sent
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


def test_set_param_rejects_unknown_parameter_name_without_contacting_server(monkeypatch):
    monkeypatch.setattr(live, "_ensure_catalog", lambda cfg: _FAKE_CATALOG)
    fake_graph = {"nodes": [
        {"name": "perlin_1", "type": "perlin", "node_position": {"x": 0, "y": 0},
         "parameters": {"scale_x": 4}},
    ], "connections": []}
    calls = []

    def responder(cmd):
        calls.append(cmd["cmd"])
        return {"ok": True, "graph": fake_graph}

    server = _FakeLiveServer(responder)
    try:
        result = live.set_param("perlin_1", {"bogus_param": 1},
                                 cfg=cfg, host="127.0.0.1", port=server.port)
        assert not result.ok
        assert result.error == "validation failed"
        assert result.data["problems"]
        assert calls == ["get_graph"]  # set_param was never sent
    finally:
        server.stop()


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


class _FakeProcess:
    def __init__(self):
        self.terminated = False
        self.killed = False
        # None == still running, matching subprocess.Popen.poll()/returncode
        # semantics. Tests that want to simulate an early exit set this
        # directly before handing the fake to connect_or_launch.
        self.returncode = None

    def poll(self):
        return self.returncode

    def terminate(self):
        self.terminated = True

    def kill(self):
        self.killed = True

    def wait(self, timeout=None):
        return 0


def test_launch_command_uses_console_binary_and_overlay_path():
    cmd = live._launch_command(cfg, r"C:\somewhere\overlay")
    assert cmd == [cfg.console_binary, "--path", r"C:\somewhere\overlay"]


def test_launch_overlay_closes_the_parent_log_file_handle(monkeypatch, tmp_path):
    """_launch_overlay opens mm_live.log for the child's stdout, but the
    parent's own copy of that handle must be closed once Popen has duped the
    fd for the child -- otherwise every launch/relaunch leaks one fd."""
    isolated_cfg = replace(cfg, output_dir=str(tmp_path))
    monkeypatch.setattr(live, "ensure_overlay", lambda *a, **kw: str(tmp_path / "overlay"))
    captured = {}

    class _FakePopen:
        def __init__(self, cmd, stdout=None, stderr=None):
            captured["stdout"] = stdout

    monkeypatch.setattr(live.subprocess, "Popen", _FakePopen)
    live._launch_overlay(isolated_cfg)
    assert captured["stdout"] is not None
    assert captured["stdout"].closed is True


def test_mutation_ops_use_a_longer_default_timeout_than_read_ops():
    """A mutation right after a fresh launch can trigger shader warmup/compile
    of the new node, so the mutating ops must not inherit the short read-op
    timeout that would spuriously fail before the compile finishes. Read-only
    one-shots (ping/get_graph/clear_graph) stay short so the connect_or_launch
    poll loop and cheap probes fail fast."""
    for fn in (live.add_node, live.connect_nodes, live.disconnect_nodes,
               live.reposition_node, live.set_param):
        assert inspect.signature(fn).parameters["timeout"].default == 30.0, fn.__name__
    for fn in (live.ping, live.get_graph, live.clear_graph):
        assert inspect.signature(fn).parameters["timeout"].default == 5.0, fn.__name__


def test_terminate_kills_the_process_tree_via_taskkill_when_pid_is_available(monkeypatch):
    # _terminate delegates the tree kill to render._kill_tree (shared), whose
    # taskkill call goes through render's subprocess, not live's.
    calls = []
    monkeypatch.setattr(render.subprocess, "run", lambda *a, **kw: calls.append(a[0]))
    process = _FakeProcess()
    process.pid = 4242
    live._terminate(process)
    assert calls == [["taskkill", "/F", "/T", "/PID", "4242"]]
    assert process.terminated is True  # the plain terminate() fallback still runs


def test_terminate_skips_taskkill_without_a_real_pid(monkeypatch):
    called = {"yes": False}

    def _fake_run(*a, **kw):
        called["yes"] = True

    monkeypatch.setattr(render.subprocess, "run", _fake_run)
    process = _FakeProcess()  # no .pid attribute at all -- a test double, not a real Popen
    live._terminate(process)
    assert called["yes"] is False
    assert process.terminated is True


def test_terminate_swallows_taskkill_failure_and_still_falls_back(monkeypatch):
    def _fake_run(*a, **kw):
        raise OSError("taskkill not found")

    monkeypatch.setattr(render.subprocess, "run", _fake_run)
    process = _FakeProcess()
    process.pid = 4242
    live._terminate(process)  # must not raise
    assert process.terminated is True


def test_connect_or_launch_attaches_when_already_listening(monkeypatch):
    server = _FakeLiveServer(lambda cmd: {"ok": True, "ready": True, "has_graph": True})
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
                lambda cmd: {"ok": True, "ready": True, "has_graph": True}, port=picked_port)
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


def test_connect_or_launch_returns_immediately_when_process_exits_early(monkeypatch):
    picked_port = _free_port()  # nothing ever listens here
    fake_process = _FakeProcess()
    fake_process.returncode = 7  # already dead by the time the first poll() runs
    monkeypatch.setattr(live, "_launch_overlay", lambda passed_cfg: fake_process)

    started = time.monotonic()
    session = live.connect_or_launch(cfg=cfg, host="127.0.0.1", port=picked_port,
                                      launch_timeout=30.0)
    elapsed = time.monotonic() - started

    assert not session.ok
    assert elapsed < 5.0, "should bail out as soon as the dead process is detected, not wait out launch_timeout"
    assert "exited with code 7" in session.error
    assert "mm_live.log" in session.error


def test_connect_or_launch_fails_fast_when_port_is_occupied_by_an_unresponsive_process(monkeypatch):
    monkeypatch.setattr(live, "_SQUATTED_PORT_GRACE", 1.0)
    server = _FakeLiveServer(lambda cmd: None)  # accepts connections but never answers -- a true squatter
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
    stale_server = _FakeLiveServer(lambda cmd: None, port=picked_port)  # never answers, matching a dying process

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
                lambda cmd: {"ok": True, "ready": True, "has_graph": True}, port=picked_port)
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


def test_connect_or_launch_waits_past_grace_for_a_slow_booting_real_instance(monkeypatch):
    monkeypatch.setattr(live, "_SQUATTED_PORT_GRACE", 1.0)
    state = {"ready": False}
    server = _FakeLiveServer(lambda cmd: {"ok": True, "ready": state["ready"], "has_graph": True})
    launched = {"called": False}

    def _no_launch(passed_cfg):
        launched["called"] = True
        return _FakeProcess()

    monkeypatch.setattr(live, "_launch_overlay", _no_launch)

    def _become_ready_soon():
        time.sleep(1.5)  # past the 1.0s grace period, well within launch_timeout
        state["ready"] = True

    threading.Thread(target=_become_ready_soon, daemon=True).start()
    try:
        session = live.connect_or_launch(cfg=cfg, host="127.0.0.1", port=server.port,
                                          launch_timeout=10.0)
        assert session.ok, session.error
        assert session.process is None  # attached, never launched a new one
        assert launched["called"] is False, (
            "a slow-booting real instance must not be misclassified as squatted and relaunched"
        )
    finally:
        server.stop()


def test_connect_or_launch_waits_for_a_graph_tab_after_main_window_is_ready_on_a_fresh_launch(
        monkeypatch):
    # This scenario used to be exercised on the "already listening, attach"
    # path (no _launch_overlay call), with has_graph flipping true after the
    # grace period. That's no longer valid: the readiness-race final review
    # found that an already-listening instance which reports `ready` but
    # never `has_graph` within the grace period must fail fast with a
    # diagnosis instead of waiting out the full launch_timeout (see
    # test_connect_or_launch_fails_fast_when_attached_instance_never_reports_has_graph
    # below) -- a real addon's boot sequence makes graph-tab creation follow
    # main_window resolution near-synchronously, so a multi-second gap on
    # the attach path doesn't model anything real. The behavior this test
    # actually protects -- "don't report ready before has_graph, even once
    # main_window is ready" -- still matters and is still unchanged for a
    # process this call launched itself (no grace-period ambiguity there,
    # per connect_or_launch's docstring), so it's retargeted to that path.
    picked_port = _free_port()
    fake_process = _FakeProcess()
    state = {"has_graph": False}
    started_server = {"server": None}

    def _fake_launch(passed_cfg):
        def _start_late():
            time.sleep(0.3)  # simulate Godot booting before the addon listens
            started_server["server"] = _FakeLiveServer(
                lambda cmd: {"ok": True, "ready": True, "has_graph": state["has_graph"]},
                port=picked_port)
        threading.Thread(target=_start_late, daemon=True).start()
        return fake_process

    monkeypatch.setattr(live, "_launch_overlay", _fake_launch)

    def _open_graph_tab_soon():
        time.sleep(1.5)  # well within launch_timeout
        state["has_graph"] = True

    threading.Thread(target=_open_graph_tab_soon, daemon=True).start()
    try:
        started = time.monotonic()
        session = live.connect_or_launch(cfg=cfg, host="127.0.0.1", port=picked_port,
                                          launch_timeout=10.0)
        elapsed = time.monotonic() - started
        assert session.ok, session.error
        assert elapsed >= 1.5, (
            "connect_or_launch must not report ready before the addon reports a graph "
            "tab, even once main_window itself is already ready"
        )
        assert session.process is fake_process
    finally:
        if started_server["server"] is not None:
            started_server["server"].stop()


def test_connect_or_launch_fails_fast_when_attached_instance_never_reports_has_graph(monkeypatch):
    # Guards the regression the final whole-branch review found in the
    # has_graph fix: attaching to an already-listening, already-responsive
    # instance that answers ping with ready=True but has_graph=False
    # forever (a pre-upgrade addon that never sends the field at all, or a
    # genuinely tab-less instance) must fail fast within the grace period
    # with a diagnosis -- not hang for the full launch_timeout and then
    # misreport a healthy process as "timed out".
    monkeypatch.setattr(live, "_SQUATTED_PORT_GRACE", 1.0)
    server = _FakeLiveServer(lambda cmd: {"ok": True, "ready": True, "has_graph": False})
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
        assert "responsive" in session.error.lower()
        assert "graph" in session.error.lower()
        assert launched["called"] is False, (
            "a responsive-but-graphless instance must not be misdiagnosed as a free port "
            "and relaunched"
        )
    finally:
        server.stop()


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
        source_node_after = next(
            n for n in graph_after.data["graph"]["nodes"] if n["name"] == source_name
        )
        assert source_node_after["parameters"]["scale_x"] == 16, (
            f"expected set_param to have applied scale_x=16 on {source_name!r}, "
            f"got {source_node_after['parameters']}"
        )

        rendered = live.render(basename="live_test", cfg=isolated_cfg)
        assert rendered.ok, rendered.error
        assert rendered.images, "render reported ok but produced no image paths"
        for path in rendered.images:
            assert os.path.getsize(path) > 0
    finally:
        session.close()


@pytest.mark.integration
def test_clear_graph_resets_a_built_graph_to_the_default_material_node(tmp_path):
    # Isolated overlay dir so this test never collides with (or clobbers) a
    # manual session's overlay, matching this file's other integration tests.
    isolated_cfg = replace(cfg, live_overlay_dir=str(tmp_path / "mm_live_overlay"))
    session = live.connect_or_launch(cfg=isolated_cfg, launch_timeout=90.0)
    try:
        assert session.ok, session.error
        assert session.process is not None, (
            "attached to a pre-existing instance on port 8765 -- close it and rerun; "
            "this test must launch its own overlay to prove the committed addon works"
        )

        added = live.add_node("perlin", {}, x=0, y=0, cfg=isolated_cfg)
        assert added.ok, added.error
        source_name = added.data["name"]
        connected = live.connect_nodes(source_name, 0, "Material", 0, cfg=isolated_cfg)
        assert connected.ok, connected.error

        built_graph = live.get_graph()
        assert built_graph.ok, built_graph.error
        assert len(built_graph.data["graph"]["nodes"]) >= 2, (
            "setup didn't actually build a multi-node graph -- clear wouldn't prove anything"
        )

        cleared = live.clear_graph()
        assert cleared.ok, cleared.error

        graph_after = live.get_graph()
        assert graph_after.ok, graph_after.error
        nodes_after = graph_after.data["graph"]["nodes"]
        assert len(nodes_after) == 1, (
            f"expected a single default node after clear, got {nodes_after}"
        )
        assert nodes_after[0]["type"] == "material"
        assert nodes_after[0]["name"] == "Material"
        assert graph_after.data["graph"]["connections"] == []
    finally:
        session.close()


@pytest.mark.integration
def test_load_graph_round_trips_a_cookbook_material(tmp_path):
    # Isolated overlay dir so this test never collides with (or clobbers) a
    # manual session's overlay, matching this file's other integration tests.
    from mm_mcp import cookbook

    isolated_cfg = replace(cfg, live_overlay_dir=str(tmp_path / "mm_live_overlay"))
    entry = cookbook.find_cookbook(isolated_cfg.cookbook_dir, "f03_canvas_burlap")
    assert entry is not None, "f03_canvas_burlap must exist in the tracked cookbook"
    with open(entry.path, encoding="utf-8") as fh:
        material = json.load(fh)
    expected_names = sorted(n["name"] for n in material["nodes"])

    session = live.connect_or_launch(cfg=isolated_cfg, launch_timeout=90.0)
    try:
        assert session.ok, session.error
        assert session.process is not None, (
            "attached to a pre-existing instance on port 8765 -- close it and rerun; "
            "this test must launch its own overlay to prove the committed addon works"
        )

        load_res = live.load_graph(graph=material, cfg=isolated_cfg)
        assert load_res.ok, load_res.error

        got = live.get_graph()
        assert got.ok, got.error
        got_names = sorted(n["name"] for n in got.data["graph"]["nodes"])
        # In-place replace: the loaded material's top-level nodes must now be
        # what's shown, not the default single-Material graph new_material()
        # would leave behind.
        assert got_names == expected_names
    finally:
        session.close()


def test_load_graph_sends_validated_dict_as_json_data():
    received = {}

    def responder(cmd):
        received.update(cmd)
        return {"ok": True}

    server = _FakeLiveServer(responder)
    try:
        graph = {"nodes": [], "connections": []}  # trivially catalog-valid
        result = live.load_graph(graph=graph, cfg=cfg, host="127.0.0.1", port=server.port)
        assert result.ok
        assert received["cmd"] == "load_graph"
        assert json.loads(received["data"]) == graph
    finally:
        server.stop()


def test_load_graph_rejects_an_invalid_graph_before_the_socket():
    def responder(cmd):
        raise AssertionError("socket must not be reached for an invalid graph")

    server = _FakeLiveServer(responder)
    try:
        bad = {"nodes": [{"name": "x", "type": "NOT_A_REAL_NODE_TYPE",
                          "node_position": {"x": 0, "y": 0}, "parameters": {}}],
               "connections": []}
        result = live.load_graph(graph=bad, cfg=cfg, host="127.0.0.1", port=server.port)
        assert not result.ok
        assert result.error == "validation failed"
        assert result.data and result.data["problems"]
    finally:
        server.stop()


def test_load_graph_requires_exactly_one_of_graph_or_path():
    r_none = live.load_graph(cfg=cfg)
    assert not r_none.ok and "exactly one" in r_none.error
    r_both = live.load_graph(graph={"nodes": [], "connections": []}, path="x.ptex", cfg=cfg)
    assert not r_both.ok and "exactly one" in r_both.error


def test_load_graph_reads_validates_and_sends_a_ptex_path(tmp_path):
    received = {}

    def responder(cmd):
        received.update(cmd)
        return {"ok": True}

    server = _FakeLiveServer(responder)
    try:
        graph = {"nodes": [], "connections": []}
        p = tmp_path / "m.ptex"
        p.write_text(json.dumps(graph), encoding="utf-8")
        result = live.load_graph(path=str(p), cfg=cfg, host="127.0.0.1", port=server.port)
        assert result.ok
        assert json.loads(received["data"]) == graph
    finally:
        server.stop()


def test_load_graph_reports_a_missing_path_as_data():
    result = live.load_graph(path="does_not_exist_12345.ptex", cfg=cfg)
    assert not result.ok
    assert "could not read graph file" in result.error

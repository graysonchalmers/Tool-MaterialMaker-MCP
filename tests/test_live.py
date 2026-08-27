# tests/test_live.py
import json
import socket
import threading
import time
from dataclasses import replace
import pytest
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


from mm_mcp.config import load_config

cfg = load_config()


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

        result = live.get_graph()
        assert result.ok, result.error
        graph = result.data["graph"]
        assert "nodes" in graph
        assert len(graph["nodes"]) >= 1
        assert any(n.get("type") == "material" for n in graph["nodes"])
    finally:
        session.close()

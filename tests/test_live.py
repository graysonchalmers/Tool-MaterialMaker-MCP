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

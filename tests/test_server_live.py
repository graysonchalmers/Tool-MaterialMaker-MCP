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

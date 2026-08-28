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

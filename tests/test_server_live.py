# tests/test_server_live.py
import os
from dataclasses import dataclass, replace
import pytest
from mm_mcp import server, live
from mm_mcp.config import load_config
from mm_mcp.render import RenderResult

cfg = load_config()


@dataclass
class _FakeSession:
    ok: bool
    process: object | None = None
    error: str | None = None


@pytest.fixture(autouse=True)
def _isolate_server_state():
    """_ensure_live_session now preserves a previously-launched process
    handle across attach-only calls (Finding 1's fix), so the module-global
    _live_session can no longer be treated as inert between tests: a prior
    test's leftover process would otherwise leak into the next test's first
    call. Reset before and after every test in this file so each test's
    _live_session starts (and leaves) clean, regardless of run order."""
    server._reset()
    yield
    server._reset()


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


def test_live_clear_returns_ok_on_success(monkeypatch):
    monkeypatch.setattr(server, "_ensure_ready", lambda: (cfg, {}))
    monkeypatch.setattr(live, "connect_or_launch",
                         lambda cfg, launch_timeout=60.0: _FakeSession(ok=True))
    monkeypatch.setattr(live, "clear_graph", lambda: live.LiveResult(ok=True))
    result = server.live_clear()
    assert result == {"ok": True, "error": None}


def test_live_clear_reports_session_failure_without_calling_clear_graph(monkeypatch):
    monkeypatch.setattr(server, "_ensure_ready", lambda: (cfg, {}))
    monkeypatch.setattr(live, "connect_or_launch",
                         lambda cfg, launch_timeout=60.0: _FakeSession(ok=False, error="no server"))
    called = {"yes": False}

    def _boom():
        called["yes"] = True
        raise AssertionError("clear_graph should not be called when the session failed")

    monkeypatch.setattr(live, "clear_graph", _boom)
    result = server.live_clear()
    assert result == {"ok": False, "error": "no server"}
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


@pytest.mark.integration
def test_live_render_node_output_previews_and_restores_a_real_session(tmp_path, monkeypatch):
    # Isolated overlay + output dirs, matching this file's other integration
    # tests, so this never collides with a manual session's overlay.
    isolated_cfg = replace(cfg, live_overlay_dir=str(tmp_path / "mm_live_overlay"),
                            output_dir=str(tmp_path / "output"))
    monkeypatch.setattr(server, "load_config", lambda *a, **kw: isolated_cfg)
    server._reset()
    try:
        start = server.live_start(launch_timeout=90.0)
        assert start["ok"], start["error"]
        assert start["launched"] is True, (
            "attached to a pre-existing instance on port 8765 -- close it and rerun; "
            "this test must launch its own overlay to prove the new disconnect_nodes "
            "GDScript handler actually works, not just that it was written"
        )
        try:
            baseline = server.live_get_graph()
            assert baseline["ok"], baseline["error"]
            assert baseline["graph"]["connections"] == [], (
                "a fresh default graph has no connections yet -- this test relies on "
                "that to force live_render_node_output's disconnect-restore branch "
                "(no original albedo_tex source to reconnect), not the already-proven "
                "reconnect branch"
            )

            added = server.live_apply([
                {"op": "add_node", "node_type": "perlin", "parameters": {}, "x": 0, "y": 0},
            ])
            assert added["ok"], added["error"]
            target_name = added["results"][0]["data"]["name"]

            result = server.live_render_node_output(target_name, basename="node_probe")
            assert result["ok"], result["error"]
            assert result["image"].endswith("_albedo.png")
            assert os.path.getsize(result["image"]) > 0

            graph_after = server.live_get_graph()
            assert graph_after["ok"], graph_after["error"]
            assert graph_after["graph"]["connections"] == [], (
                "the preview connection into albedo_tex must be fully removed afterward "
                "-- a real do_disconnect_node call, not just an ok:true response"
            )
        finally:
            server._live_session.close()
    finally:
        server._reset()


def test_ensure_live_session_preserves_a_previously_launched_process_across_attach_calls(monkeypatch):
    launched_process = object()  # stand-in for a real subprocess.Popen

    calls = {"n": 0}

    def _fake_connect_or_launch(cfg, launch_timeout=60.0):
        calls["n"] += 1
        if calls["n"] == 1:
            return _FakeSession(ok=True, process=launched_process)
        return _FakeSession(ok=True, process=None)  # attach path on later calls

    monkeypatch.setattr(live, "connect_or_launch", _fake_connect_or_launch)
    server._reset()

    first = server._ensure_live_session(cfg)
    assert first.process is launched_process

    second = server._ensure_live_session(cfg)
    assert second.process is launched_process, (
        "a later attach-only call must not lose the handle to a process this server launched"
    )


def test_live_apply_reports_malformed_op_as_data_instead_of_raising(monkeypatch):
    monkeypatch.setattr(server, "_ensure_ready", lambda: (cfg, {}))
    monkeypatch.setattr(live, "connect_or_launch",
                         lambda cfg, launch_timeout=60.0: _FakeSession(ok=True))
    calls = []

    def _fake_add_node(node_type, parameters, x=0.0, y=0.0, cfg=None):
        calls.append("add_node")
        return live.LiveResult(ok=True, data={"name": "perlin_1"})

    monkeypatch.setattr(live, "add_node", _fake_add_node)

    ops = [
        {"op": "add_node", "node_type": "perlin", "parameters": {}, "x": 0, "y": 0},
        {"op": "set_param", "name": "perlin_1"},  # missing required "parameters" key
    ]
    result = server.live_apply(ops)
    assert result["ok"] is False
    assert len(result["results"]) == 2  # first op's success is preserved, not lost
    assert result["results"][0]["ok"] is True
    assert result["results"][1]["ok"] is False
    assert "malformed" in result["error"] or "missing" in result["error"]
    assert calls == ["add_node"]


def test_live_apply_dispatches_disconnect_nodes(monkeypatch):
    monkeypatch.setattr(server, "_ensure_ready", lambda: (cfg, {}))
    monkeypatch.setattr(live, "connect_or_launch",
                         lambda cfg, launch_timeout=60.0: _FakeSession(ok=True))
    calls = []

    def _fake_disconnect_nodes(from_name, from_port, to_name, to_port, cfg=None):
        calls.append((from_name, from_port, to_name, to_port))
        return live.LiveResult(ok=True)

    monkeypatch.setattr(live, "disconnect_nodes", _fake_disconnect_nodes)
    result = server.live_apply([{"op": "disconnect_nodes", "from_name": "a", "from_port": 0,
                                  "to_name": "b", "to_port": 1}])
    assert result["ok"] is True
    assert calls == [("a", 0, "b", 1)]


_LIVE_GRAPH_WITH_ALBEDO_SOURCE = {
    "nodes": [
        {"name": "orig", "type": "perlin", "node_position": {"x": 0, "y": 0}, "parameters": {}},
        {"name": "target", "type": "colorize", "node_position": {"x": 0, "y": 0}, "parameters": {}},
        {"name": "Material", "type": "material", "node_position": {"x": 0, "y": 0}, "parameters": {}},
    ],
    "connections": [{"from": "orig", "from_port": 0, "to": "Material", "to_port": 0}],
}

_LIVE_GRAPH_WITHOUT_ALBEDO_SOURCE = {
    "nodes": [
        {"name": "target", "type": "colorize", "node_position": {"x": 0, "y": 0}, "parameters": {}},
        {"name": "Material", "type": "material", "node_position": {"x": 0, "y": 0}, "parameters": {}},
    ],
    "connections": [],
}


def test_live_render_node_output_restores_the_original_connection(monkeypatch):
    monkeypatch.setattr(server, "_ensure_ready", lambda: (cfg, {}))
    monkeypatch.setattr(live, "connect_or_launch",
                         lambda cfg, launch_timeout=60.0: _FakeSession(ok=True))
    monkeypatch.setattr(live, "get_graph",
                         lambda: live.LiveResult(ok=True, data={"graph": _LIVE_GRAPH_WITH_ALBEDO_SOURCE}))
    calls = []

    def _fake_connect_nodes(from_name, from_port, to_name, to_port, cfg=None):
        calls.append(("connect", from_name, from_port, to_name, to_port))
        return live.LiveResult(ok=True)

    def _fake_disconnect_nodes(*a, **k):
        calls.append(("disconnect",))
        return live.LiveResult(ok=True)

    def _fake_render(basename, profile, cfg):
        calls.append(("render",))
        return RenderResult(ok=True, images=[f"{basename}_albedo.png", f"{basename}_normal.png"])

    monkeypatch.setattr(live, "connect_nodes", _fake_connect_nodes)
    monkeypatch.setattr(live, "disconnect_nodes", _fake_disconnect_nodes)
    monkeypatch.setattr(live, "render", _fake_render)

    result = server.live_render_node_output("target")

    assert result["ok"] is True
    assert result["image"] == "node_output_albedo.png"
    assert calls == [
        ("connect", "target", 0, "Material", 0),
        ("render",),
        ("connect", "orig", 0, "Material", 0),  # restored, not disconnected
    ]


def test_live_render_node_output_disconnects_when_nothing_fed_albedo_before(monkeypatch):
    monkeypatch.setattr(server, "_ensure_ready", lambda: (cfg, {}))
    monkeypatch.setattr(live, "connect_or_launch",
                         lambda cfg, launch_timeout=60.0: _FakeSession(ok=True))
    monkeypatch.setattr(live, "get_graph",
                         lambda: live.LiveResult(ok=True, data={"graph": _LIVE_GRAPH_WITHOUT_ALBEDO_SOURCE}))
    calls = []

    monkeypatch.setattr(live, "connect_nodes",
                         lambda *a, **k: (calls.append(("connect", *a)), live.LiveResult(ok=True))[1])
    monkeypatch.setattr(live, "disconnect_nodes",
                         lambda *a, **k: (calls.append(("disconnect", *a)), live.LiveResult(ok=True))[1])
    monkeypatch.setattr(live, "render",
                         lambda basename, profile, cfg: RenderResult(
                             ok=True, images=[f"{basename}_albedo.png"]))

    result = server.live_render_node_output("target")

    assert result["ok"] is True
    assert calls == [
        ("connect", "target", 0, "Material", 0),
        ("disconnect", "target", 0, "Material", 0),
    ]


def test_live_render_node_output_still_restores_after_a_render_failure(monkeypatch):
    monkeypatch.setattr(server, "_ensure_ready", lambda: (cfg, {}))
    monkeypatch.setattr(live, "connect_or_launch",
                         lambda cfg, launch_timeout=60.0: _FakeSession(ok=True))
    monkeypatch.setattr(live, "get_graph",
                         lambda: live.LiveResult(ok=True, data={"graph": _LIVE_GRAPH_WITH_ALBEDO_SOURCE}))
    restored = []
    monkeypatch.setattr(live, "connect_nodes",
                         lambda *a, **k: (restored.append(a), live.LiveResult(ok=True))[1])
    monkeypatch.setattr(live, "render",
                         lambda basename, profile, cfg: RenderResult(ok=False, error="Godot exited 1"))

    result = server.live_render_node_output("target")

    assert result["ok"] is False
    assert result["error"] == "Godot exited 1"
    assert ("orig", 0, "Material", 0) in restored  # restore still ran despite the failure


def test_live_render_node_output_unknown_node_returns_a_data_error(monkeypatch):
    monkeypatch.setattr(server, "_ensure_ready", lambda: (cfg, {}))
    monkeypatch.setattr(live, "connect_or_launch",
                         lambda cfg, launch_timeout=60.0: _FakeSession(ok=True))
    monkeypatch.setattr(live, "get_graph",
                         lambda: live.LiveResult(ok=True, data={"graph": _LIVE_GRAPH_WITH_ALBEDO_SOURCE}))
    called = {"yes": False}
    monkeypatch.setattr(live, "connect_nodes",
                         lambda *a, **k: called.__setitem__("yes", True) or live.LiveResult(ok=True))

    result = server.live_render_node_output("does_not_exist")

    assert result["ok"] is False
    assert "does_not_exist" in result["error"]
    assert called["yes"] is False


def test_live_render_node_output_reports_session_failure_without_calling_get_graph(monkeypatch):
    monkeypatch.setattr(server, "_ensure_ready", lambda: (cfg, {}))
    monkeypatch.setattr(live, "connect_or_launch",
                         lambda cfg, launch_timeout=60.0: _FakeSession(ok=False, error="no server"))
    called = {"yes": False}
    monkeypatch.setattr(live, "get_graph",
                         lambda: called.__setitem__("yes", True) or live.LiveResult(ok=True))

    result = server.live_render_node_output("target")

    assert result == {"ok": False, "image": None, "error": "no server"}
    assert called["yes"] is False


def test_live_apply_rejects_a_non_dict_op_without_raising(monkeypatch):
    monkeypatch.setattr(server, "_ensure_ready", lambda: (cfg, {}))
    monkeypatch.setattr(live, "connect_or_launch",
                         lambda cfg, launch_timeout=60.0: _FakeSession(ok=True))
    result = server.live_apply(["not_a_dict"])
    assert result["ok"] is False
    assert result["results"][0]["ok"] is False

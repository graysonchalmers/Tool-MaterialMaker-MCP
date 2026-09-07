import inspect

import pytest
from mm_mcp import server
from mm_mcp.config import Config
from mm_mcp.idle import IdleWatchdog


@pytest.fixture(autouse=True)
def _reset_idle():
    server._idle = None
    yield
    server._idle = None


def _fake_config(idle_exit_minutes: int) -> Config:
    return Config(
        godot_binary="",
        console_binary="",
        project_path="",
        output_dir="",
        nodes_dir="",
        examples_dir="",
        live_overlay_dir="",
        allowed_roots=[],
        idle_exit_minutes=idle_exit_minutes,
    )


def test_ensure_ready_touches_idle_watchdog(monkeypatch):
    calls = []

    class FakeIdle:
        def touch(self):
            calls.append(True)

    monkeypatch.setattr(server, "_idle", FakeIdle())
    server._ensure_ready()
    assert calls == [True]


def test_main_leaves_idle_none_when_disabled(monkeypatch):
    def fake_ensure_ready():
        server._cfg = _fake_config(0)
        return server._cfg, {}

    monkeypatch.setattr(server, "_ensure_ready", fake_ensure_ready)
    monkeypatch.setattr(server.mcp, "run", lambda: None)

    server.main([])

    assert server._idle is None


def test_main_starts_idle_watchdog_when_enabled(monkeypatch):
    def fake_ensure_ready():
        server._cfg = _fake_config(2)
        return server._cfg, {}

    monkeypatch.setattr(server, "_ensure_ready", fake_ensure_ready)
    monkeypatch.setattr(server.mcp, "run", lambda: None)
    monkeypatch.setattr(IdleWatchdog, "start", lambda self: None)

    server.main([])

    assert isinstance(server._idle, IdleWatchdog)
    assert server._idle._timeout == 120
    assert server._idle._on_expire is server._idle_exit


def test_idle_exit_closes_live_session_before_calling_os_exit(monkeypatch, capsys):
    """_idle_exit must run _close_live_session_atexit() BEFORE os._exit(0):
    os._exit skips atexit handlers entirely, so if a live session (e.g. a
    launched Godot overlay process) is up, this explicit call is the only
    thing that still closes it on an idle exit."""
    order = []
    monkeypatch.setattr(server, "_close_live_session_atexit", lambda: order.append("close"))
    monkeypatch.setattr(server.os, "_exit", lambda code: order.append(("exit", code)))

    server._idle_exit(7200.0)

    assert order == ["close", ("exit", 0)]
    captured = capsys.readouterr()
    assert "min" in captured.err


# --- Finding 1: every registered tool must touch the idle watchdog --------
#
# This list is kept explicit (not derived from mcp.tool() calls) so a new
# tool that is added to server.py but never added here fails the count
# assertion below, rather than silently going untested.
_ALL_TOOL_NAMES = [
    "list_node_types",
    "describe_node",
    "validate",
    "render_graph",
    "render_node_output",
    "render_preview",
    "save_graph",
    "list_examples",
    "load_example",
    "inspect_project",
    "live_start",
    "live_get_graph",
    "live_apply",
    "live_render",
    "live_render_node_output",
    "live_clear",
    "live_load",
]


class _Sentinel(Exception):
    """Raised by a stubbed heavy callee so a test can prove the tool got far
    enough to touch the watchdog without actually launching Godot or a live
    socket."""


class _FakeIdle:
    def __init__(self):
        self.calls = []

    def touch(self):
        self.calls.append(True)


def _expect_sentinel(fn, *args, **kwargs):
    with pytest.raises(_Sentinel):
        fn(*args, **kwargs)


def test_tool_registration_count_matches_covered_list():
    """Guards the coverage list itself: if a new tool is registered with
    mcp.tool() and this test file is not updated to cover it, this
    assertion (not a silent skip) is what catches it."""
    source = inspect.getsource(server)
    registration_count = source.count("mcp.tool()(")
    assert registration_count == len(_ALL_TOOL_NAMES), (
        f"server.py registers {registration_count} tools via mcp.tool()(...) "
        f"but tests/test_server_idle.py only covers {len(_ALL_TOOL_NAMES)}; "
        "add the missing tool(s) to _ALL_TOOL_NAMES and to the touch test "
        "below."
    )


def test_every_registered_tool_touches_idle_watchdog(monkeypatch, tmp_path):
    def raise_sentinel(*args, **kwargs):
        raise _Sentinel("heavy callee should never run in this test")

    # Heavy callees stubbed so no Godot process or live socket is ever
    # touched, per the task instructions.
    monkeypatch.setattr(server, "_ensure_live_session", raise_sentinel)
    monkeypatch.setattr(server, "render", raise_sentinel)
    monkeypatch.setattr(server, "_render_preview", raise_sentinel)

    invalid_ptex = {"type": "graph",
                     "nodes": [{"name": "x", "type": "not_a_real_node_type", "parameters": {}}],
                     "connections": []}
    empty_ptex = {"type": "graph", "nodes": [], "connections": []}
    missing_path = str(tmp_path / "missing.ptex")
    save_path = str(tmp_path / "out.ptex")

    calls = {
        "list_node_types": lambda: server.list_node_types(),
        "describe_node": lambda: server.describe_node("not_a_real_node_type"),
        "validate": lambda: server.validate({}),
        # Invalid node type fails validation and returns before render() is
        # ever reached, so touching this way never needs a Godot process.
        "render_graph": lambda: server.render_graph(invalid_ptex),
        # Unknown node_name fails isolate_node_output before render() is
        # reached, for the same reason.
        "render_node_output": lambda: server.render_node_output(
            empty_ptex, "not_a_real_node_name"),
        "render_preview": lambda: _expect_sentinel(
            server.render_preview,
            str(tmp_path / "a.png"), str(tmp_path / "n.png"), str(tmp_path / "o.png")),
        "save_graph": lambda: server.save_graph(empty_ptex, save_path),
        "list_examples": lambda: server.list_examples(),
        "load_example": lambda: server.load_example("not_a_real_example_name"),
        "inspect_project": lambda: server.inspect_project(missing_path),
        "live_start": lambda: _expect_sentinel(server.live_start),
        "live_get_graph": lambda: _expect_sentinel(server.live_get_graph),
        "live_apply": lambda: _expect_sentinel(server.live_apply, []),
        "live_render": lambda: _expect_sentinel(server.live_render),
        "live_render_node_output": lambda: _expect_sentinel(
            server.live_render_node_output, "x"),
        "live_clear": lambda: _expect_sentinel(server.live_clear),
        "live_load": lambda: _expect_sentinel(
            server.live_load, {"nodes": [], "connections": []}),
    }

    assert set(calls) == set(_ALL_TOOL_NAMES), (
        "the call table in this test must cover exactly _ALL_TOOL_NAMES")

    for name in _ALL_TOOL_NAMES:
        fake_idle = _FakeIdle()
        monkeypatch.setattr(server, "_idle", fake_idle)
        calls[name]()
        assert fake_idle.calls, f"tool '{name}' did not touch the idle watchdog"

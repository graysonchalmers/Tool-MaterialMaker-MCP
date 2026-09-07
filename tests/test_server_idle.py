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

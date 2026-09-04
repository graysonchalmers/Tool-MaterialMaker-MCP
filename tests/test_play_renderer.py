from mm_mcp.play import renderer


class _Result:
    def __init__(self, ok, images=None, error=None, data=None):
        self.ok = ok
        self.images = images or []
        self.error = error
        self.data = data or {}


def _cfg():
    from mm_mcp.config import load_config
    return load_config()


def test_uses_headless_when_no_live_session():
    calls = {}

    def fake_ping(timeout=1.0):
        return _Result(False)

    def fake_headless(ptex, size=512, outdir=None, basename="material", cfg=None):
        calls["headless"] = True
        return _Result(True, images=["a_albedo.png"])

    out = renderer.render_material(
        {"nodes": [], "connections": []}, [], 256, _cfg(), outdir="x",
        ping=fake_ping, headless_render=fake_headless)
    assert out["ok"] and out["path"] == "headless"
    assert calls.get("headless")


def test_uses_live_when_session_has_graph():
    sent = []

    def fake_ping(timeout=1.0):
        return _Result(True, data={"has_graph": True})

    def fake_set_param(name, parameters, cfg=None):
        sent.append((name, parameters))
        return _Result(True)

    def fake_live_render(basename="material", cfg=None):
        return _Result(True, images=["live_albedo.png"])

    changes = [{"node": "perlin_2", "widget": "scale_x", "value": 9.0}]
    out = renderer.render_material(
        {"nodes": [], "connections": []}, changes, 256, _cfg(), outdir="x",
        ping=fake_ping, live_set_param=fake_set_param, live_render=fake_live_render)
    assert out["ok"] and out["path"] == "live"
    assert sent == [("perlin_2", {"scale_x": 9.0})]


def test_falls_back_to_headless_when_live_set_param_fails():
    def fake_ping(timeout=1.0):
        return _Result(True, data={"has_graph": True})

    def fake_set_param(name, parameters, cfg=None):
        return _Result(False, error="node not found")

    def fake_headless(ptex, size=512, outdir=None, basename="material", cfg=None):
        return _Result(True, images=["fallback_albedo.png"])

    changes = [{"node": "ghost", "widget": "x", "value": 1}]
    out = renderer.render_material(
        {"nodes": [], "connections": []}, changes, 256, _cfg(), outdir="x",
        ping=fake_ping, live_set_param=fake_set_param, headless_render=fake_headless)
    assert out["ok"] and out["path"] == "headless"
    assert out["images"] == ["fallback_albedo.png"]

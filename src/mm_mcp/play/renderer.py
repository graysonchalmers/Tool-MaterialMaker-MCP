"""Chooses the render path for the play surface: drive a live Material Maker
session when one is up and usable, otherwise render headless. Serializes all
renders so only one Godot runs at a time (the render-orphan-contention rule).
"""
import threading

from mm_mcp import live, render

_RENDER_LOCK = threading.Lock()


def render_material(applied_graph, changes, size, cfg, outdir, *,
                    ping=live.ping, live_set_param=live.set_param,
                    live_render=live.render, headless_render=render.render):
    """Render `applied_graph` (values already applied). `changes` drives the live
    path. Returns {ok, path, images, error}. One Godot at a time."""
    with _RENDER_LOCK:
        probe = ping(timeout=1.0)
        if probe.ok and probe.data.get("has_graph"):
            live_result = _try_live(changes, cfg, live_set_param, live_render)
            if live_result is not None:
                return live_result
            # live was up but not usable (mismatch): fall through to headless.
        r = headless_render(applied_graph, size=size, outdir=outdir,
                            basename="play", cfg=cfg)
        return {"ok": r.ok, "path": "headless",
                "images": list(r.images), "error": r.error}


def _try_live(changes, cfg, live_set_param, live_render):
    for ch in changes:
        res = live_set_param(ch["node"], {ch["widget"]: ch["value"]}, cfg=cfg)
        if not res.ok:
            return None  # signal: fall back to headless
    r = live_render(basename="play", cfg=cfg)
    if not r.ok:
        return None
    return {"ok": True, "path": "live", "images": list(r.images), "error": None}

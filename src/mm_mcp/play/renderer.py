"""Chooses the render path for the play surface: drive a live Material Maker
session when one is up and usable, otherwise render headless. Serializes all
renders so only one Godot runs at a time (the render-orphan-contention rule).
"""
import os
import shutil
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
            live_result = _try_live(changes, cfg, live_set_param, live_render, outdir)
            if live_result is not None:
                return live_result
            # live was up but not usable (mismatch): fall through to headless.
        r = headless_render(applied_graph, size=size, outdir=outdir,
                            basename="play", cfg=cfg)
        return {"ok": r.ok, "path": "headless",
                "images": list(r.images), "error": r.error}


def _try_live(changes, cfg, live_set_param, live_render, outdir):
    for ch in changes:
        res = live_set_param(ch["node"], {ch["widget"]: ch["value"]}, cfg=cfg)
        if not res.ok:
            return None  # signal: fall back to headless
    r = live_render(basename="play", cfg=cfg)
    if not r.ok:
        return None
    images = _copy_into_outdir(r.images, outdir)
    return {"ok": True, "path": "live", "images": images, "error": None}


def _copy_into_outdir(paths, outdir):
    """live.render always writes into cfg.output_dir (the parent of the play
    dir), never into `outdir` itself. The play server serves maps from
    `outdir`, so copy each rendered image there and return the copy's path -
    that is what api.render_request's basename() needs to resolve. Errors
    stay data: a source that does not exist (as in the older fake-live
    tests) is passed through unchanged instead of raising."""
    try:
        outdir_abs = os.path.abspath(outdir)
    except Exception:
        return list(paths)
    result = []
    for p in paths:
        try:
            if not os.path.isfile(p):
                result.append(p)
                continue
            src_dir = os.path.abspath(os.path.dirname(p) or os.curdir)
            if src_dir == outdir_abs:
                result.append(p)
                continue
            os.makedirs(outdir_abs, exist_ok=True)
            dest = os.path.join(outdir_abs, os.path.basename(p))
            shutil.copy2(p, dest)
            result.append(dest)
        except Exception:
            result.append(p)
    return result

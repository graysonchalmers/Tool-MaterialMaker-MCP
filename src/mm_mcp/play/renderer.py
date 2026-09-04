"""Chooses the render path for the play surface: drive a live Material Maker
session when one is up and usable, otherwise render headless. Serializes all
renders so only one Godot runs at a time (the render-orphan-contention rule).
"""
import os
import shutil
import threading

from mm_mcp import live, render

_RENDER_LOCK = threading.Lock()

_last_pushed_id = None  # id of the material this surface last pushed into a live session (guarded by _RENDER_LOCK)


def render_material(applied_graph, changes, size, cfg, outdir, *,
                    material_id=None, ping=live.ping, live_set_param=live.set_param,
                    live_render=live.render, live_load=live.load_graph,
                    headless_render=render.render):
    """Render `applied_graph` (values already applied). `changes` drives the live
    path. Returns {ok, path, images, error}. One Godot at a time."""
    with _RENDER_LOCK:
        probe = ping(timeout=1.0)
        if probe.ok and probe.data.get("has_graph"):
            live_result = _try_live(applied_graph, changes, material_id, cfg,
                                    live_load, live_set_param, live_render, outdir)
            if live_result is not None:
                return live_result
            # live was up but not usable (mismatch/load failure): fall through.
        r = headless_render(applied_graph, size=size, outdir=outdir,
                            basename="play", cfg=cfg)
        return {"ok": r.ok, "path": "headless",
                "images": list(r.images), "error": r.error}


def _try_live(applied_graph, changes, material_id, cfg, live_load, live_set_param,
              live_render, outdir):
    global _last_pushed_id
    # Push the picked material into the live session once per pick change, so the
    # live path drives the material the person actually picked, not whatever was
    # already open. Only on a change: repeated renders of the same pick reuse the
    # loaded graph and just re-set params. The load is a Godot-touching op and
    # runs here inside the caller's _RENDER_LOCK, so it cannot interleave with a
    # render. If a person switches tabs in MM by hand our belief goes stale; the
    # next set_param then fails on the missing nodes and we return None ->
    # headless, which is the safe fallback (v1 accepts this rather than
    # re-verifying every render).
    if material_id is not None and material_id != _last_pushed_id:
        load_res = live_load(graph=applied_graph, cfg=cfg)
        if not load_res.ok:
            return None
        _last_pushed_id = material_id
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

import json
import io
import os
import socket
import threading
import urllib.error
import urllib.request
import zipfile
from dataclasses import replace
from http.server import HTTPServer
from pathlib import Path

import pytest
from mm_mcp.config import load_config
from mm_mcp.catalog_builder import build_catalog
from mm_mcp.play import api, server


@pytest.fixture()
def running_server(tmp_path):
    cfg = load_config()
    catalog = build_catalog(cfg.nodes_dir)
    handler = server.make_handler(cfg, catalog, str(tmp_path),
                                  str(server.STATIC_DIR))
    httpd = HTTPServer(("127.0.0.1", 0), handler)
    t = threading.Thread(target=httpd.serve_forever, daemon=True)
    t.start()
    yield f"http://127.0.0.1:{httpd.server_address[1]}"
    httpd.shutdown()


def _get(url):
    with urllib.request.urlopen(url) as r:
        return r.status, r.read()


def test_root_serves_html(running_server):
    status, body = _get(running_server + "/")
    assert status == 200
    assert b"<html" in body.lower()


def test_api_materials(running_server):
    status, body = _get(running_server + "/api/materials")
    assert status == 200
    data = json.loads(body)
    assert data["ok"] and any(m["name"] == "t01_sand_dunes" for m in data["materials"])


def test_unknown_path_404(running_server):
    with pytest.raises(urllib.error.HTTPError) as exc:
        _get(running_server + "/nope")
    assert exc.value.code == 404


@pytest.mark.parametrize("name", ["app.js", "style.css", "three.min.js"])
def test_static_assets_served(running_server, name):
    status, body = _get(running_server + "/static/" + name)
    assert status == 200
    assert len(body) > 0


def test_export_returns_completed_render_zip(running_server, monkeypatch):
    real_render_request = api.render_request

    def fake_render(graph, changes, size, cfg, outdir, **kw):
        path = Path(outdir) / "play_albedo.png"
        path.write_bytes(b"rendered-map")
        return {"ok": True, "path": "headless", "images": [str(path)]}

    def render_request(*args):
        return real_render_request(*args, render_fn=fake_render)

    monkeypatch.setattr(api, "render_request", render_request)
    req = urllib.request.Request(running_server + "/api/render", method="POST",
        data=json.dumps({"material_id": "t01_sand_dunes", "values": {
            "dune_ripples/param0": 12.0}}).encode(),
        headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req) as r:
        rendered = json.load(r)
    assert rendered.get("preview_id"), rendered
    query = "?preview_id=" + rendered["preview_id"]
    status, image = _get(running_server + "/api/maps/play_albedo.png" + query)
    assert status == 200 and image == b"rendered-map"
    with pytest.raises(urllib.error.HTTPError) as exc:
        _get(running_server + "/api/maps/unlisted.png" + query)
    assert exc.value.code == 404
    with pytest.raises(urllib.error.HTTPError) as exc:
        _get(running_server + "/api/maps/play_albedo.png")
    assert exc.value.code == 404

    url = running_server + "/api/export" + query
    with urllib.request.urlopen(url) as r:
        assert r.headers.get("Content-Type") == "application/zip"
        with zipfile.ZipFile(io.BytesIO(r.read())) as z:
            assert z.read("play_albedo.png") == image
            graph = json.loads(z.read("t01_sand_dunes.ptex"))
            sub = next(n for n in graph["nodes"] if n["name"] == "dune_ripples")
            assert sub["parameters"]["param0"] == 12.0


def test_serve_fails_fast_on_missing_godot_binary(capsys):
    # A misconfigured Godot path must fail at startup with the actionable
    # message that names the path, not start and then throw a cryptic
    # WinError 2 traceback on every render.
    cfg = load_config()
    bad = replace(cfg, godot_binary=r"C:\nope\godot.exe",
                  console_binary=r"C:\nope\godot_console.exe")
    result = server.serve(cfg=bad, open_browser=False)
    assert result is None
    out = capsys.readouterr().out
    assert "Godot binary does not exist" in out


def test_post_render_error_returns_json_not_traceback(running_server, monkeypatch):
    # An unexpected error inside a request handler must come back as a JSON
    # error the client can display, not bubble into a bare traceback that
    # kills the response and leaves the browser stuck on "rendering...".
    def boom(*a, **k):
        raise RuntimeError("kaboom")

    monkeypatch.setattr(api, "render_request", boom)
    req = urllib.request.Request(
        running_server + "/api/render", method="POST",
        data=json.dumps({"material_id": "t01_sand_dunes", "values": {}, "size": 256}).encode(),
        headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req) as r:
            status, body = r.status, r.read()
    except urllib.error.HTTPError as e:
        status, body = e.code, e.read()
    assert status == 500
    data = json.loads(body)
    assert data["ok"] is False
    assert "kaboom" in data["error"]


def test_export_unknown_material_404(running_server):
    with pytest.raises(urllib.error.HTTPError) as exc:
        _get(running_server + "/api/export?material_id=nope")
    assert exc.value.code == 404


@pytest.mark.integration
def test_render_endpoint_produces_maps(running_server):
    payload = json.dumps({"material_id": "t01_sand_dunes",
                          "values": {}, "size": 256}).encode()
    req = urllib.request.Request(running_server + "/api/render", data=payload,
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=240) as r:
        data = json.loads(r.read())
    assert data["ok"], data
    assert data["maps"], "expected rendered maps"
    # each map is fetchable and non-empty
    for name in data["maps"]:
        with urllib.request.urlopen(running_server + "/api/maps/" + name
                                    + "?preview_id=" + data["preview_id"]) as r:
            body = r.read()
        assert len(body) > 0


def test_serve_reports_port_in_use_with_owner(capsys):
    # A stale mm-play (or any process) already listening on the play port
    # must produce an actionable startup message naming the port, not a
    # server that silently binds beside the squatter (Windows SO_REUSEADDR
    # quirk) or a bare OSError traceback.
    squatter = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    squatter.bind(("127.0.0.1", 0))
    squatter.listen(5)
    port = squatter.getsockname()[1]
    try:
        assert server.port_in_use(port)
        cfg = replace(load_config(), play_port=port)
        result = server.serve(cfg=cfg, open_browser=False)
    finally:
        squatter.close()
    assert result is None
    out = capsys.readouterr().out
    assert f"port {port}" in out
    assert "MM_PLAY_PORT" in out
    if os.name == "nt":
        assert "PID" in out and "Stop-Process" in out


def test_port_in_use_probe():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(("127.0.0.1", 0))
    s.listen(1)
    port = s.getsockname()[1]
    try:
        assert server.port_in_use(port) is True
    finally:
        s.close()
    assert server.port_in_use(port) is False


def test_describe_port_owner_names_this_process_on_windows():
    if os.name != "nt":
        pytest.skip("netstat/tasklist parsing is Windows-only")
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(("127.0.0.1", 0))
    s.listen(1)
    port = s.getsockname()[1]
    try:
        owner = server.describe_port_owner(port)
    finally:
        s.close()
    assert owner is not None
    assert f"PID {os.getpid()}" in owner

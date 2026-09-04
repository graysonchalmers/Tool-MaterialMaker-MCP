import json
import threading
import urllib.error
import urllib.request
from dataclasses import replace
from http.server import HTTPServer

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


def test_export_returns_zip(running_server):
    url = running_server + "/api/export?material_id=t01_sand_dunes"
    with urllib.request.urlopen(url) as r:
        assert r.headers.get("Content-Type") == "application/zip"
        assert r.read()  # non-empty (contains at least the .ptex)


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
        with urllib.request.urlopen(running_server + "/api/maps/" + name) as r:
            body = r.read()
        assert len(body) > 0

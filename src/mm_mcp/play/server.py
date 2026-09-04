"""Standalone local web server for the play surface. Binds to 127.0.0.1, single
user, no auth. Launched by a human via `mm-play`. Renders are serialized in the
facade (renderer.py), so the threading server is safe."""
import json
import os
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from mm_mcp.catalog_builder import build_catalog
from mm_mcp.config import load_config
from mm_mcp.play import api
from mm_mcp.paths import reject_path_fragment, PathNotAllowed

STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")


def make_handler(cfg, catalog, outdir, static_dir):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass  # quiet

        def _send_json(self, obj, status=200):
            body = json.dumps(obj).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def _send_bytes(self, data, content_type, status=200):
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def _serve_static(self, rel):
            try:
                reject_path_fragment(rel)
            except PathNotAllowed:
                return self._send_json({"ok": False, "error": "bad path"}, 400)
            path = os.path.join(static_dir, rel)
            if not os.path.isfile(path):
                return self._send_json({"ok": False, "error": "not found"}, 404)
            ctype = ("text/html" if path.endswith(".html")
                     else "application/javascript" if path.endswith(".js")
                     else "text/css" if path.endswith(".css")
                     else "application/octet-stream")
            with open(path, "rb") as fh:
                self._send_bytes(fh.read(), ctype)

        def do_GET(self):
            path = self.path.split("?", 1)[0]
            if path == "/":
                return self._serve_static("index.html")
            if path == "/api/materials":
                return self._send_json(api.list_materials(cfg))
            if path.startswith("/api/material/"):
                name = path[len("/api/material/"):]
                out = api.get_material(cfg, catalog, name)
                return self._send_json(out, 200 if out["ok"] else 404)
            if path.startswith("/api/maps/"):
                name = path[len("/api/maps/"):]
                try:
                    reject_path_fragment(name)
                except PathNotAllowed:
                    return self._send_json({"ok": False, "error": "bad path"}, 400)
                fp = os.path.join(outdir, name)
                if not os.path.isfile(fp):
                    return self._send_json({"ok": False, "error": "not found"}, 404)
                with open(fp, "rb") as fh:
                    return self._send_bytes(fh.read(), "image/png")
            if path == "/api/export":
                from urllib.parse import parse_qs, urlparse
                q = parse_qs(urlparse(self.path).query)
                name = (q.get("material_id") or [""])[0]
                data, fname = api.export(cfg, catalog,
                                         {"material_id": name, "values": {}}, outdir)
                if data is None:
                    return self._send_json({"ok": False, "error": fname}, 404)
                self.send_response(200)
                self.send_header("Content-Type", "application/zip")
                self.send_header("Content-Disposition",
                                 f'attachment; filename="{fname}"')
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)
                return
            if path.startswith("/static/"):
                return self._serve_static(path[len("/static/"):])
            return self._send_json({"ok": False, "error": "not found"}, 404)

        def do_POST(self):
            path = self.path.split("?", 1)[0]
            length = int(self.headers.get("Content-Length") or 0)
            raw = self.rfile.read(length) if length else b"{}"
            try:
                body = json.loads(raw or b"{}")
            except json.JSONDecodeError:
                return self._send_json({"ok": False, "error": "bad json"}, 400)
            if path == "/api/render":
                out = api.render_request(cfg, catalog, body, outdir)
                return self._send_json(out, 200 if out["ok"] else 400)
            return self._send_json({"ok": False, "error": "not found"}, 404)

    return Handler


def serve(cfg=None, open_browser=False):
    cfg = cfg or load_config()
    catalog = build_catalog(cfg.nodes_dir)
    outdir = os.path.join(cfg.output_dir, "play")
    os.makedirs(outdir, exist_ok=True)
    handler = make_handler(cfg, catalog, outdir, STATIC_DIR)
    httpd = ThreadingHTTPServer(("127.0.0.1", cfg.play_port), handler)
    url = f"http://127.0.0.1:{cfg.play_port}/"
    print(f"Material Maker Play running at {url}  (Ctrl+C to stop)")
    if open_browser:
        webbrowser.open(url)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        httpd.shutdown()
    return None


def main(argv=None):
    serve(open_browser=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

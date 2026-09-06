"""Standalone local web server for the play surface. Binds to 127.0.0.1, single
user, no auth. Launched by a human via `mm-play`. Renders are serialized in the
facade (renderer.py), so the threading server is safe."""
import csv
import json
import os
import socket
import subprocess
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from mm_mcp.catalog_builder import build_catalog
from mm_mcp.config import load_config, require_valid
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

        def _dispatch_get(self):
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

        def _dispatch_post(self):
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

        # An unexpected error inside a handler must come back to the browser as a
        # JSON error it can display, not bubble into ThreadingHTTPServer's default
        # traceback that kills the response and leaves the client's fetch hanging
        # (the "rendering... forever" symptom). A misconfigured Godot binary is
        # caught at startup by require_valid in serve(); this is the net for
        # anything that slips past.
        def do_GET(self):
            try:
                self._dispatch_get()
            except Exception as exc:  # noqa: BLE001 - deliberate catch-all boundary
                self._send_json({"ok": False, "error": str(exc)}, 500)

        def do_POST(self):
            try:
                self._dispatch_post()
            except Exception as exc:  # noqa: BLE001 - deliberate catch-all boundary
                self._send_json({"ok": False, "error": str(exc)}, 500)

    return Handler


def port_in_use(port: int, host: str = "127.0.0.1") -> bool:
    """True when something accepts TCP connections on host:port. A connect
    probe, not a bind attempt: HTTPServer sets SO_REUSEADDR, and on Windows
    that lets a second bind to a LISTENING port succeed silently, which is
    how a stale mm-play kept answering the browser while a new one believed
    it had started fine."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
        probe.settimeout(0.5)
        return probe.connect_ex((host, port)) == 0


def describe_port_owner(port: int) -> str | None:
    """Windows only: 'PID <n> (<image name>)' for the process LISTENING on
    127.0.0.1:<port>, from `netstat -ano` + `tasklist`. None off-Windows, or
    when either command fails or the port is not found."""
    if os.name != "nt":
        return None
    try:
        out = subprocess.run(["netstat", "-ano", "-p", "tcp"], capture_output=True,
                             text=True, timeout=10, check=False).stdout
    except (OSError, subprocess.SubprocessError):
        return None
    pid = None
    for line in out.splitlines():
        parts = line.split()
        if (len(parts) >= 5 and parts[0].upper() == "TCP"
                and parts[1].endswith(f":{port}") and parts[3].upper() == "LISTENING"):
            pid = parts[4]
            break
    if not pid:
        return None
    name = None
    try:
        out = subprocess.run(["tasklist", "/FI", f"PID eq {pid}", "/FO", "CSV", "/NH"],
                             capture_output=True, text=True, timeout=10, check=False).stdout
        first = next((ln for ln in out.splitlines() if ln.strip().startswith('"')), "")
        row = next(csv.reader([first])) if first else []
        if len(row) >= 2 and row[1] == pid:
            name = row[0]
    except (OSError, subprocess.SubprocessError, StopIteration):
        pass
    return f"PID {pid}" + (f" ({name})" if name else "")


class _StrictThreadingHTTPServer(ThreadingHTTPServer):
    # Backstop for the probe above: never bind beside an existing listener.
    # SO_REUSEADDR means different things on the two platforms. On Windows it
    # lets a second bind succeed beside a live listener, so it must stay off.
    # On POSIX it only bypasses TIME_WAIT, so clearing it there just makes a
    # quick restart fail; keep it on for anything that isn't Windows.
    allow_reuse_address = os.name != "nt"


def serve(cfg=None, open_browser=False):
    cfg = cfg or load_config()
    # Fail fast with an actionable message that names the exact bad path,
    # instead of starting and then throwing a cryptic WinError 2 traceback on
    # every render (which the browser only ever sees as "rendering..." forever).
    # Same guard the MCP server runs at its own startup.
    try:
        require_valid(cfg)
    except FileNotFoundError as exc:
        print(f"Cannot start Material Maker Play: {exc}")
        return None
    if port_in_use(cfg.play_port):
        owner = describe_port_owner(cfg.play_port)
        who = f" by {owner}" if owner else ""
        print(f"Cannot start Material Maker Play: port {cfg.play_port} is already in use{who}.")
        print("  Most likely a stale mm-play from an earlier session is still running.")
        if owner and owner.startswith("PID "):
            pid = owner.split()[1]
            print(f"  Stop it:   Stop-Process -Id {pid}")
        print("  Or use another port: set MM_PLAY_PORT in .env and relaunch.")
        return None
    catalog = build_catalog(cfg.nodes_dir)
    outdir = os.path.join(cfg.output_dir, "play")
    os.makedirs(outdir, exist_ok=True)
    handler = make_handler(cfg, catalog, outdir, STATIC_DIR)
    try:
        httpd = _StrictThreadingHTTPServer(("127.0.0.1", cfg.play_port), handler)
    except OSError as exc:
        print(f"Cannot start Material Maker Play: could not bind port {cfg.play_port} ({exc}).")
        print("  Set MM_PLAY_PORT in .env to use another port.")
        return None
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

# src/mm_mcp/live.py
import json
import os
import socket
import subprocess
import time
from dataclasses import dataclass

from mm_mcp.catalog_builder import build_catalog
from mm_mcp.config import Config, load_config
from mm_mcp.overlay import ensure_overlay
from mm_mcp.render import RenderResult, _collect_fresh_images
from mm_mcp.validator import validate_graph

# Must match addons/mm_live/live_server.gd's LIVE_PORT -- no shared-constant
# mechanism exists across GDScript and Python, so keep both literals in sync
# by hand if this ever changes.
LIVE_HOST = "127.0.0.1"
LIVE_PORT = 8765

# addons/mm_live/ is a top-level sibling of src/, not bundled inside
# src/mm_mcp/ -- unlike preview_project/, it does NOT ship in a built wheel.
# Acceptable under Phase 4's current GitHub-clone distribution decision
# (PyPI on hold); revisit if that changes.
_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_ADDON_PATH = os.path.join(_REPO_ROOT, "addons", "mm_live")


@dataclass
class LiveResult:
    ok: bool
    data: dict | None = None
    error: str | None = None


def _send_command(cmd: dict, host: str = LIVE_HOST, port: int = LIVE_PORT,
                   timeout: float = 5.0) -> LiveResult:
    """Open a fresh TCP connection, send one JSON line, read one JSON line
    back, close. One-shot per call, matching the addon's per-connection
    dispatch -- there is no persistent session state on either side."""
    try:
        sock = socket.create_connection((host, port), timeout=timeout)
    except OSError as exc:
        return LiveResult(ok=False, error=f"could not reach live server at {host}:{port}: {exc}")

    try:
        with sock:
            sock.sendall((json.dumps(cmd) + "\n").encode("utf-8"))
            sock.settimeout(timeout)
            buf = b""
            try:
                while b"\n" not in buf:
                    chunk = sock.recv(4096)
                    if not chunk:
                        return LiveResult(ok=False,
                                           error="connection closed before a response line arrived")
                    buf += chunk
            except TimeoutError:
                return LiveResult(ok=False,
                                   error=f"timed out waiting for a response from {host}:{port}")
    except OSError as exc:
        return LiveResult(ok=False, error=f"live server connection failed: {exc}")

    line = buf.split(b"\n", 1)[0]
    try:
        data = json.loads(line.decode("utf-8"))
    except (ValueError, UnicodeDecodeError) as exc:
        return LiveResult(ok=False, error=f"malformed response from live server: {exc}")
    if not isinstance(data, dict):
        return LiveResult(ok=False, error="live server response was not a JSON object")
    if not data.get("ok", False):
        return LiveResult(ok=False, error=data.get("error", "live server reported failure"))
    return LiveResult(ok=True, data=data)


def ping(host: str = LIVE_HOST, port: int = LIVE_PORT, timeout: float = 5.0) -> LiveResult:
    return _send_command({"cmd": "ping"}, host, port, timeout)


def get_graph(host: str = LIVE_HOST, port: int = LIVE_PORT, timeout: float = 5.0) -> LiveResult:
    return _send_command({"cmd": "get_graph"}, host, port, timeout)


_catalog_cache: dict[str, dict] = {}


def _ensure_catalog(cfg: Config) -> dict:
    catalog = _catalog_cache.get(cfg.nodes_dir)
    if catalog is None:
        catalog = build_catalog(cfg.nodes_dir)
        _catalog_cache[cfg.nodes_dir] = catalog
    return catalog


def _validation_errors(ptex: dict, cfg: Config) -> list[dict]:
    problems = validate_graph(ptex, _ensure_catalog(cfg))
    return [p for p in problems if p["severity"] == "error"]


def add_node(node_type: str, parameters: dict | None = None, x: float = 0.0, y: float = 0.0,
             cfg: Config | None = None, host: str = LIVE_HOST, port: int = LIVE_PORT,
             timeout: float = 5.0) -> LiveResult:
    """Validate node_type/parameters against the catalog in isolation (a
    brand-new, unconnected node has no effect on the rest of the live
    graph), then send add_node if valid. On success, LiveResult.data["name"]
    is the node's real post-creation name -- Material Maker may rename it
    on a collision, so never assume it matches node_type."""
    cfg = cfg or load_config()
    parameters = parameters or {}
    proposed = {"nodes": [{"name": "_new", "type": node_type,
                            "node_position": {"x": x, "y": y}, "parameters": parameters}],
                "connections": []}
    errors = _validation_errors(proposed, cfg)
    if errors:
        return LiveResult(ok=False, error="validation failed", data={"problems": errors})
    return _send_command({"cmd": "add_node", "type": node_type, "parameters": parameters,
                           "x": x, "y": y}, host, port, timeout)


def connect_nodes(from_name: str, from_port: int, to_name: str, to_port: int,
                   cfg: Config | None = None, host: str = LIVE_HOST, port: int = LIVE_PORT,
                   timeout: float = 5.0) -> LiveResult:
    """Fetch the current live graph, validate the proposed connection
    against it, and only send connect_nodes if that validation is clean."""
    cfg = cfg or load_config()
    current = get_graph(host, port, timeout)
    if not current.ok:
        return current
    graph = current.data["graph"]
    proposed = {"nodes": graph.get("nodes", []),
                "connections": graph.get("connections", []) +
                               [{"from": from_name, "from_port": from_port,
                                 "to": to_name, "to_port": to_port}]}
    errors = _validation_errors(proposed, cfg)
    if errors:
        return LiveResult(ok=False, error="validation failed", data={"problems": errors})
    return _send_command({"cmd": "connect_nodes", "from": from_name, "from_port": from_port,
                           "to": to_name, "to_port": to_port}, host, port, timeout)


def set_param(name: str, parameters: dict, cfg: Config | None = None, host: str = LIVE_HOST,
              port: int = LIVE_PORT, timeout: float = 5.0) -> LiveResult:
    """Fetch the current live graph, confirm the target node exists, merge
    the proposed parameters into a copy of its current ones, validate that,
    and only send set_param if clean."""
    cfg = cfg or load_config()
    current = get_graph(host, port, timeout)
    if not current.ok:
        return current
    graph = current.data["graph"]
    nodes = graph.get("nodes", [])
    target = next((n for n in nodes if n.get("name") == name), None)
    if target is None:
        return LiveResult(ok=False, error=f"no node named '{name}' in the current live graph")
    merged_nodes = [
        {**n, "parameters": {**n.get("parameters", {}), **parameters}} if n is target else n
        for n in nodes
    ]
    proposed = {"nodes": merged_nodes, "connections": graph.get("connections", [])}
    errors = _validation_errors(proposed, cfg)
    if errors:
        return LiveResult(ok=False, error="validation failed", data={"problems": errors})
    return _send_command({"cmd": "set_param", "name": name, "parameters": parameters},
                          host, port, timeout)


def render(basename: str = "material", profile: str = "Godot/Godot 4 Standard",
           cfg: Config | None = None, host: str = LIVE_HOST, port: int = LIVE_PORT,
           timeout: float = 60.0) -> RenderResult:
    """Trigger a live-window export via the addon's render command, then
    verify success the same way render.py's batch path does: by checking
    for fresh <basename>_*.png files on disk, since export_material has no
    failure signal of its own to report over the socket."""
    cfg = cfg or load_config()
    outdir = cfg.output_dir
    os.makedirs(outdir, exist_ok=True)
    before = {}
    for fn in os.listdir(outdir):
        if fn.startswith(basename + "_") and fn.lower().endswith(".png"):
            full = os.path.join(outdir, fn)
            try:
                before[fn] = os.path.getmtime(full)
            except (OSError, FileNotFoundError):
                pass
    prefix = os.path.join(outdir, basename)
    result = _send_command({"cmd": "render", "prefix": prefix, "profile": profile},
                            host, port, timeout)
    if not result.ok:
        return RenderResult(ok=False, error=result.error)
    images = _collect_fresh_images(outdir, basename, before)
    if not images:
        return RenderResult(ok=False, error="no PNG output produced by live render")
    return RenderResult(ok=True, images=images)


@dataclass
class LiveSession:
    ok: bool
    process: subprocess.Popen | None = None
    error: str | None = None

    def close(self) -> None:
        """Terminate the Godot process this session launched. No-op if this
        session attached to an already-running instance instead."""
        if self.process is not None:
            _terminate(self.process)
            self.process = None


def _is_listening(host: str, port: int) -> bool:
    try:
        with socket.create_connection((host, port), timeout=0.5):
            return True
    except OSError:
        return False


def _terminate(process: subprocess.Popen) -> None:
    process.terminate()
    try:
        process.wait(timeout=10)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait(timeout=10)


def _launch_command(cfg: Config, overlay_dir: str) -> list[str]:
    return [cfg.console_binary, "--path", overlay_dir]


def _launch_overlay(cfg: Config) -> subprocess.Popen:
    overlay_dir = ensure_overlay(cfg.project_path, _ADDON_PATH, cfg.live_overlay_dir)
    os.makedirs(cfg.output_dir, exist_ok=True)
    log_file = open(os.path.join(cfg.output_dir, "mm_live.log"), "w", encoding="utf-8")
    # Godot's stdout must not be PIPE'd without draining it -- an undrained
    # pipe fills and blocks the child (confirmed during the Phase 5
    # feasibility spike). Redirect to a file instead.
    return subprocess.Popen(_launch_command(cfg, overlay_dir),
                             stdout=log_file, stderr=subprocess.STDOUT)


def connect_or_launch(cfg: Config | None = None, host: str = LIVE_HOST,
                       port: int = LIVE_PORT, launch_timeout: float = 60.0) -> LiveSession:
    """Probe (host, port); if nothing answers, rebuild the overlay if stale
    and launch Material Maker against it. Either way, poll ping() until the
    addon reports main_window is wired -- never assume the first successful
    ping means the GUI has finished loading (see the spec's "lazy
    main_window resolution" constraint) -- or give up after launch_timeout.

    Attaching to an already-running instance never launches a process, so
    the returned session's close() is a no-op for that case: we only own the
    lifecycle of a process we started ourselves.
    """
    cfg = cfg or load_config()
    process = None
    if not _is_listening(host, port):
        process = _launch_overlay(cfg)

    # The launch-and-poll span below is wrapped so that if anything raises
    # while we're waiting (not just the plain timeout, which is handled
    # after the loop), the process we just launched still gets terminated
    # instead of leaking as an orphaned, visible Godot window. Today
    # nothing in the loop actually raises (ping()/_send_command() catch
    # every exception type they can produce), but that's an implementation
    # detail of _send_command, not a guarantee -- this is a structural
    # safety net, not a response to an observed failure.
    try:
        deadline = time.monotonic() + launch_timeout
        last_error = "timed out waiting for the live server to become ready"
        while time.monotonic() < deadline:
            result = ping(host, port)
            if result.ok and result.data.get("ready"):
                return LiveSession(ok=True, process=process)
            if not result.ok:
                last_error = result.error
            if process is not None and process.poll() is not None:
                # The process we launched has already exited -- no point
                # waiting out the rest of launch_timeout. Point at the log
                # file _launch_overlay redirected stdout/stderr into, since
                # that's where the real diagnosis (GPU/driver failure, a
                # GDScript parse error, etc.) will be.
                return LiveSession(
                    ok=False,
                    error=f"Material Maker exited with code {process.returncode} before the "
                          f"live server became ready; see "
                          f"{os.path.join(cfg.output_dir, 'mm_live.log')}",
                )
            time.sleep(0.5)
    except BaseException:
        if process is not None:
            _terminate(process)
        raise

    if process is not None:
        _terminate(process)
    return LiveSession(ok=False, error=last_error, process=None)

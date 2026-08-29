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

# How long connect_or_launch will wait for an already-listening port to
# either become ready or stop listening, before deciding it's occupied by an
# unresponsive process rather than one that's still booting. Much shorter
# than launch_timeout on purpose -- see connect_or_launch's docstring.
_SQUATTED_PORT_GRACE = 5.0

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


def clear_graph(host: str = LIVE_HOST, port: int = LIVE_PORT, timeout: float = 5.0) -> LiveResult:
    """Reset the live graph on Material Maker's active tab to a single
    default Material node, discarding every other node and connection --
    the same reset the GUI's own "New" menu item performs
    (graph_edit.gd:714's new_material()). No validation to do here (there
    is no proposed graph to check against the catalog), so this is a bare
    one-shot command like ping/get_graph. Irreversible; there is no undo
    over the socket."""
    return _send_command({"cmd": "clear_graph"}, host, port, timeout)


def _wait_for_ready_or_give_up(host: str, port: int,
                                deadline: float) -> tuple[bool, bool, bool, str]:
    """Poll ping() until it reports ready, or `deadline` (a time.monotonic()
    value) passes. Returns (ready, ever_answered, main_window_ever_ready,
    last_error).

    "Ready" here means both `ready` (main_window resolved) AND `has_graph`
    (a graph tab exists) from ping()'s response -- main_window can resolve
    one or more frames before the default graph tab is created, so gating
    on `ready` alone lets a caller proceed before add_node/get_graph/etc.
    are actually safe to call (see docs/superpowers/plans/
    2026-08-27-connect-or-launch-readiness-race.md).

    ever_answered is True the moment ping() ever returns ok=True, even with
    ready=False -- a real live-addon socket answers ping almost immediately
    after binding (project startup), well before main_window resolves (see
    the spec's "lazy main_window resolution" constraint). A single
    successful-but-not-ready response is proof this is a live addon that's
    still booting, not a dead/squatted process -- even if it never reaches
    ready before the deadline.

    main_window_ever_ready is True the moment ping() ever reports `ready`
    True on its own, independent of `has_graph` -- this lets a caller on
    the "already listening, attaching" path tell apart two situations that
    both look like "not ready by the deadline" from the combined check
    alone: main_window genuinely never resolving (still booting -- the
    existing ever_answered handling already covers this and must keep
    waiting), versus main_window resolving but no graph tab ever following
    it within the deadline (see connect_or_launch's docstring for why that
    second case gets failed fast instead of given the full launch_timeout).

    last_error is always a string, even on success (harmless: callers only
    read it on failure).
    """
    ever_answered = False
    main_window_ever_ready = False
    last_error = "timed out waiting for a response"
    while time.monotonic() < deadline:
        result = ping(host, port)
        if result.ok:
            ever_answered = True
            if result.data.get("ready"):
                main_window_ever_ready = True
                if result.data.get("has_graph"):
                    return True, ever_answered, main_window_ever_ready, last_error
        else:
            last_error = result.error
        time.sleep(0.5)
    return False, ever_answered, main_window_ever_ready, last_error


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


def disconnect_nodes(from_name: str, from_port: int, to_name: str, to_port: int,
                      cfg: Config | None = None, host: str = LIVE_HOST, port: int = LIVE_PORT,
                      timeout: float = 5.0) -> LiveResult:
    """Fetch the current live graph and confirm the exact connection exists
    before sending disconnect_nodes -- there's nothing to validate against
    the catalog here (removing a connection can't violate a port-range or
    unknown-type check), only whether it's actually there to remove."""
    cfg = cfg or load_config()
    current = get_graph(host, port, timeout)
    if not current.ok:
        return current
    graph = current.data["graph"]
    exists = any(c.get("from") == from_name and c.get("from_port", 0) == from_port
                 and c.get("to") == to_name and c.get("to_port", 0) == to_port
                 for c in graph.get("connections", []))
    if not exists:
        return LiveResult(ok=False,
                           error=f"no connection from '{from_name}' port {from_port} to "
                                 f"'{to_name}' port {to_port} in the current live graph")
    return _send_command({"cmd": "disconnect_nodes", "from": from_name, "from_port": from_port,
                           "to": to_name, "to_port": to_port}, host, port, timeout)


def reposition_node(name: str, x: float, y: float, cfg: Config | None = None,
                     host: str = LIVE_HOST, port: int = LIVE_PORT,
                     timeout: float = 5.0) -> LiveResult:
    """Fetch the current live graph and confirm the target node exists before
    sending reposition_node -- there's nothing to validate against the
    catalog here (moving a node can't violate a type/connection rule), only
    whether it's actually there to move. Renaming an existing node is
    deliberately NOT supported: Material Maker's own undo/redo command
    dispatcher (graph_edit.gd's undoredo_command) has no rename case at all
    among its add/remove/update/setparams/move_generators/etc. commands, so
    this isn't a gap in the addon -- it's genuinely unsupported by Material
    Maker itself, and reimplementing it by hand (Node.name assignment) would
    risk desyncing the GraphNode's "node_"+name scene-tree addressing and
    Godot's own built-in GraphEdit connection bookkeeping (both keyed by
    name), with no upstream precedent for doing it safely."""
    cfg = cfg or load_config()
    current = get_graph(host, port, timeout)
    if not current.ok:
        return current
    graph = current.data["graph"]
    if not any(n.get("name") == name for n in graph.get("nodes", [])):
        return LiveResult(ok=False, error=f"no node named '{name}' in the current live graph")
    return _send_command({"cmd": "reposition_node", "name": name, "x": x, "y": y},
                          host, port, timeout)


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
    problems = validate_graph(proposed, _ensure_catalog(cfg))
    errors = [p for p in problems if p["severity"] == "error"]
    # An unrecognized parameter name is classified as a "warning" by
    # validate_graph (Material Maker's own loader tolerates stray keys
    # rather than rejecting them -- see validator.py), but set_param must
    # treat it as blocking anyway: the addon has no way to safely refuse an
    # unrecognized parameter name once it's forwarded to Material Maker's
    # set_node_parameters, so this is the only line of defense against a
    # partially-applied mutation or an unhandled error in the live window.
    unknown_param_warnings = [
        p for p in problems
        if p["severity"] == "warning" and p["where"] == name
        and "unknown parameter" in p["message"]
    ]
    blocking = errors + unknown_param_warnings
    if blocking:
        return LiveResult(ok=False, error="validation failed", data={"problems": blocking})
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
    """Terminate the launched process and any child process it spawned.

    Godot's console binary is a launcher that spawns the real GUI process
    as a separate child outside this Popen's own process tree on Windows,
    so process.terminate() alone only kills the launcher and leaves the GUI
    process running (confirmed via tasklist/wmic after a real integration
    test run -- two orphaned Godot processes remained). taskkill's /T flag
    kills the whole tree rooted at the launcher's PID first, reaching the
    GUI child too; the plain terminate()/kill() sequence still runs after
    as a fallback in case taskkill silently failed (e.g. permission denied)
    or isn't available. A test double with no real OS pid (no .pid
    attribute) skips the taskkill step and falls straight to the fallback.
    """
    pid = getattr(process, "pid", None)
    if pid is not None:
        try:
            subprocess.run(["taskkill", "/F", "/T", "/PID", str(pid)],
                            capture_output=True, timeout=10)
        except (OSError, subprocess.TimeoutExpired):
            pass
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
    addon reports both main_window is wired AND a graph tab exists -- never
    assume the first successful ping means the GUI is usable (see the
    spec's "lazy main_window resolution" constraint) -- or give up. Giving
    up can happen two ways: after the full launch_timeout (the normal case,
    and the only case for a process this call launched itself), or fast,
    within the much shorter grace period, when attaching to an
    already-listening instance that turns out to be responsive but stuck
    without a graph tab (see the grace-period paragraph below).

    A port that's already listening gets a short grace period
    (_SQUATTED_PORT_GRACE, much shorter than launch_timeout) to either
    become ready or stop listening, before this function commits to
    attaching. This is what lets a genuinely-booting instance attach
    normally while also recovering from a dying instance (e.g. a previous
    test's Material Maker process that's still closing its socket) instead
    of burning the entire launch_timeout on a corpse that will never
    answer. If the port is still listening and still unresponsive after the
    grace period, that's treated as a squatted port: connect_or_launch fails
    fast with a diagnostic error rather than continuing to wait, since it
    can't safely bind its own listener there anyway. The discriminator is
    whether the port ever answers a ping validly at all (proves a live,
    still-booting addon) versus never answering once (genuinely squatted)
    -- not whether it reaches `ready` in time, since a real instance can
    legitimately take far longer than the grace period to finish booting.

    A third outcome shares that same grace period: if the port answers and
    even reports `ready` (main_window resolved) at least once during the
    grace period, but `has_graph` never follows within that same window,
    this function fails fast with a diagnosis rather than falling through
    to the full launch_timeout. A real addon's own boot sequence creates
    the default graph tab near-synchronously after main_window resolves,
    so the grace period is already generous enough to see it happen if it's
    ever going to; waiting the full launch_timeout here would just misdiagnose
    a genuinely responsive (but stale-addon or tab-less) instance as "timed
    out". This only applies to the "already listening, attaching" path --
    a process this call launched itself always gets the full launch_timeout
    for both conditions, since there's no ambiguity to resolve (we know it's
    a fresh boot, not a possibly-stale pre-existing instance).

    Attaching to an already-running instance never launches a process, so
    the returned session's close() is a no-op for that case: we only own the
    lifecycle of a process we started ourselves.
    """
    cfg = cfg or load_config()
    process = None
    still_listening = _is_listening(host, port)

    if still_listening:
        grace_deadline = time.monotonic() + min(_SQUATTED_PORT_GRACE, launch_timeout)
        ready, ever_answered, main_window_ever_ready, grace_error = _wait_for_ready_or_give_up(
            host, port, grace_deadline)
        if ready:
            return LiveSession(ok=True, process=None)
        if not ever_answered:
            still_listening = _is_listening(host, port)
            if still_listening:
                return LiveSession(
                    ok=False,
                    error=(
                        f"port {port} is occupied by a process that never answered as the live "
                        f"server after waiting {min(_SQUATTED_PORT_GRACE, launch_timeout):.0f}s "
                        f"({grace_error}). If a previous Material Maker/Godot process is stuck "
                        "on this port, close it (or taskkill the Godot console binary) and retry."
                    ),
                )
            # else: the occupant stopped listening during the grace period --
            # the port is free now, so fall through and launch normally.
        elif main_window_ever_ready:
            # main_window resolved at least once during the grace period,
            # but has_graph never followed within that same window -- this
            # is not a still-booting instance (that case leaves
            # main_window_ever_ready False and is handled below), it's a
            # responsive, already-running Material Maker with no graph tab.
            # A real addon's boot sequence makes graph-tab creation follow
            # main_window resolution near-synchronously, so the grace
            # period (already far longer than that gap) is enough to prove
            # this isn't just slow. Fail fast here instead of falling
            # through to the full launch_timeout, which would otherwise
            # misdiagnose a healthy-but-stuck instance as "timed out" a
            # minute later.
            return LiveSession(
                ok=False,
                error=(
                    f"Material Maker at {host}:{port} is running and responsive, but reports no "
                    "active graph tab after waiting "
                    f"{min(_SQUATTED_PORT_GRACE, launch_timeout):.0f}s. If this instance was "
                    "launched before this version, close it and let this tool relaunch a fresh "
                    "one so the updated live-control addon loads; otherwise open a material/graph "
                    "tab in it and retry."
                ),
            )
        # else: it answered at least once during the grace period but
        # main_window itself never resolved -- a real live-addon socket
        # that's still booting, not squatted. still_listening stays True,
        # so we skip the launch branch below and fall straight into the
        # main poll loop with its full launch_timeout budget, same as this
        # project's pre-hardening behavior for this exact case.

    if not still_listening:
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
            if result.ok and result.data.get("ready") and result.data.get("has_graph"):
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

import glob
import json
import os
import sys
from mcp.server.mcpserver import MCPServer
from mm_mcp import __version__, live
from mm_mcp.config import load_config, require_valid
from mm_mcp.catalog_builder import build_catalog
from mm_mcp.graph import find_material_node, isolate_node_output
from mm_mcp.validator import validate_graph
from mm_mcp.render import render
from mm_mcp.preview import render_preview as _render_preview
from mm_mcp.doctor import run_check

# Startup is lazy: importing this module must NOT validate config or build the
# catalog, so `mm-mcp --check` / `--version` work even when config is broken
# (the exact case the doctor exists for) and tests can import cheaply. The first
# tool call (or mcp.run()) materializes config + catalog once, via _ensure_ready.
_cfg = None
_CATALOG = None


def _ensure_ready():
    global _cfg, _CATALOG
    if _CATALOG is None:
        _cfg = load_config()
        require_valid(_cfg)
        _CATALOG = build_catalog(_cfg.nodes_dir)
    return _cfg, _CATALOG


def _reset() -> None:
    """Clear the memoized config + catalog so the next call re-initializes.

    Used by tests, and it means a failed startup is never cached: because
    _ensure_ready only memoizes after require_valid + build_catalog succeed, a
    bad config re-raises on every call rather than sticking a half-built state.
    """
    global _cfg, _CATALOG, _live_session
    _cfg = None
    _CATALOG = None
    _live_session = None


mcp = MCPServer("material-maker")


def list_node_types(category: str = "") -> list:
    _, catalog = _ensure_ready()
    names = sorted(catalog.keys())
    if category:
        names = [n for n in names if category in n]
    return names


def describe_node(node_type: str) -> dict:
    _, catalog = _ensure_ready()
    if node_type not in catalog:
        return {"error": f"unknown node type '{node_type}'"}
    return catalog[node_type]


def validate(ptex: dict) -> list:
    _, catalog = _ensure_ready()
    return validate_graph(ptex, catalog)


def render_graph(ptex: dict, size: int = 512, basename: str = "material",
                  target: str = "Godot/Godot 4 Standard") -> dict:
    cfg, catalog = _ensure_ready()
    problems = validate_graph(ptex, catalog)
    errors = [p for p in problems if p["severity"] == "error"]
    if errors:
        return {"ok": False, "images": [], "error": "validation failed",
                "problems": errors}
    result = render(ptex, size=size, basename=basename, target=target, cfg=cfg)
    return {"ok": result.ok, "images": result.images,
            "error": result.error, "log_tail": result.log_tail}


def render_node_output(ptex: dict, node_name: str, port: int = 0, size: int = 512,
                        basename: str = "node_output",
                        target: str = "Godot/Godot 4 Standard") -> dict:
    """Render a single node's output in isolation, without editing the real
    graph: rewires a copy of ptex so node_name's output `port` feeds the
    material node's albedo input, renders that copy, and returns just the
    resulting albedo image (the other exported maps reflect whatever else
    was already wired, not the isolated node, so they're not returned).

    Use this instead of manually rerouting a graph by hand to check an
    intermediate node (e.g. a mask) during authoring.
    """
    cfg, catalog = _ensure_ready()
    try:
        isolated = isolate_node_output(ptex, node_name, port)
    except ValueError as exc:
        return {"ok": False, "image": None, "error": str(exc)}
    problems = validate_graph(isolated, catalog)
    errors = [p for p in problems if p["severity"] == "error"]
    if errors:
        return {"ok": False, "image": None, "error": "validation failed",
                "problems": errors}
    result = render(isolated, size=size, basename=basename, target=target, cfg=cfg)
    if not result.ok:
        return {"ok": False, "image": None, "error": result.error,
                "log_tail": result.log_tail}
    albedo = next((p for p in result.images if p.endswith("_albedo.png")), None)
    if albedo is None:
        return {"ok": False, "image": None,
                "error": "render succeeded but no albedo output was produced",
                "log_tail": result.log_tail}
    return {"ok": True, "image": albedo, "error": None, "log_tail": result.log_tail}


def render_preview(albedo_path: str, normal_path: str, orm_path: str,
                    basename: str = "preview", tile: float = 1.0) -> dict:
    """Composite a material's already-rendered maps onto a sphere, a cube,
    and a cutaway ball revealing an inner core, on a tiled ground plane.

    Call render_graph first and pass its albedo/normal/orm output paths here;
    this does not render a graph itself, only visualizes maps that already
    exist, so a normal map's relief is visible under real lighting instead of
    read as a flat swatch. tile controls the UV repeat count on the objects
    (the ground always tiles finer than that, so its own repeat is visible
    regardless of the chosen value) — raise it to check how a material reads
    at a smaller physical scale, e.g. tiled across a large surface.
    """
    cfg, _ = _ensure_ready()
    result = _render_preview(albedo_path, normal_path, orm_path,
                              basename=basename, tile=tile, cfg=cfg)
    return {"ok": result.ok, "image": result.image,
            "error": result.error, "log_tail": result.log_tail}


def save_graph(ptex: dict, path: str) -> str:
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(ptex, fh, indent=1)
    return path


def list_examples() -> list:
    cfg, _ = _ensure_ready()
    return sorted(os.path.splitext(os.path.basename(p))[0]
                  for p in glob.glob(os.path.join(cfg.examples_dir, "*.ptex")))


def load_example(name: str) -> dict:
    cfg, _ = _ensure_ready()
    path = os.path.join(cfg.examples_dir, name + ".ptex")
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


_live_session: live.LiveSession | None = None


def _ensure_live_session(cfg, launch_timeout: float = 60.0) -> live.LiveSession:
    """Every live_* tool call goes through this first: probes (or launches)
    Material Maker via live.connect_or_launch, per the design spec's "a live
    tool call launches it rather than erroring out" scope decision. Cheap
    when a session is already up and ready (one ping round-trip); only slow
    the first time, when nothing is listening yet.

    connect_or_launch's attach path always returns process=None (it only
    reports a process handle for one it just spawned itself), so a naive
    "store whatever comes back" would lose the handle to a process THIS
    server launched the moment any later call re-probes and attaches to it
    instead of relaunching. Preserve a previously-launched process's handle
    across attach-only calls so close() still works no matter how many live
    tool calls happened in between.
    """
    global _live_session
    session = live.connect_or_launch(cfg=cfg, launch_timeout=launch_timeout)
    if session.process is None and _live_session is not None and _live_session.process is not None:
        session.process = _live_session.process
    _live_session = session
    return _live_session


def live_start(launch_timeout: float = 60.0) -> dict:
    """Connect to an already-open Material Maker, or launch it against the
    disposable live overlay if nothing's listening on the known port. Not
    required before the other live_* tools -- they each do this same
    connect-or-launch check themselves -- but useful to call first to
    surface a launch failure (or confirm attach) before issuing real ops."""
    cfg, _ = _ensure_ready()
    session = _ensure_live_session(cfg, launch_timeout=launch_timeout)
    return {"ok": session.ok, "launched": session.process is not None,
            "error": session.error}


def live_get_graph() -> dict:
    """Fetch the graph currently on Material Maker's active tab, in the same
    {nodes, connections} shape as a .ptex file."""
    cfg, _ = _ensure_ready()
    session = _ensure_live_session(cfg)
    if not session.ok:
        return {"ok": False, "graph": None, "error": session.error}
    result = live.get_graph()
    return {"ok": result.ok, "graph": result.data.get("graph") if result.ok else None,
            "error": result.error}


def live_clear() -> dict:
    """Reset the live graph on Material Maker's active tab to a single
    default Material node, discarding every other node and connection --
    the same reset the GUI's own "New" menu item performs. Irreversible;
    there is no undo over the socket, so call live_get_graph first if the
    current graph is worth keeping. Shows a brief on-screen notice in the
    live window so a person watching isn't left wondering why it changed."""
    cfg, _ = _ensure_ready()
    session = _ensure_live_session(cfg)
    if not session.ok:
        return {"ok": False, "error": session.error}
    result = live.clear_graph()
    return {"ok": result.ok, "error": result.error}


_LIVE_OP_HANDLERS = {
    "add_node": lambda op, cfg: live.add_node(
        op["node_type"], op.get("parameters"), x=op.get("x", 0.0), y=op.get("y", 0.0), cfg=cfg),
    "connect_nodes": lambda op, cfg: live.connect_nodes(
        op["from_name"], op["from_port"], op["to_name"], op["to_port"], cfg=cfg),
    "set_param": lambda op, cfg: live.set_param(op["name"], op["parameters"], cfg=cfg),
    "disconnect_nodes": lambda op, cfg: live.disconnect_nodes(
        op["from_name"], op["from_port"], op["to_name"], op["to_port"], cfg=cfg),
}


def live_apply(ops: list) -> dict:
    """Apply a batch of mutations to the live graph in order, each validated
    against the catalog before it reaches the socket (same validation
    live.py's add_node/connect_nodes/set_param already do). Stops at the
    first failing op rather than continuing: a later op in the same batch
    may assume an earlier one already applied (e.g. connecting a node
    add_node just created), so there's nothing safe to do with the rest of
    the batch once one op fails. Each op is a dict:
    {"op": "add_node", "node_type": ..., "parameters": {...}, "x": ..., "y": ...} |
    {"op": "connect_nodes", "from_name": ..., "from_port": ..., "to_name": ..., "to_port": ...} |
    {"op": "disconnect_nodes", "from_name": ..., "from_port": ..., "to_name": ..., "to_port": ...} |
    {"op": "set_param", "name": ..., "parameters": {...}}.

    A malformed op (not a dict, or missing a required field) is reported as
    data rather than raised, same as an unrecognized 'op' value -- so a
    batch that partially applied before hitting a bad op still reports what
    already succeeded, instead of losing that record to an uncaught
    exception.
    """
    cfg, _ = _ensure_ready()
    session = _ensure_live_session(cfg)
    if not session.ok:
        return {"ok": False, "results": [], "error": session.error}
    results = []
    for i, op in enumerate(ops):
        if not isinstance(op, dict):
            error = f"op {i} is not a valid operation object: {op!r}"
            results.append({"index": i, "op": None, "ok": False, "data": None, "error": error})
            return {"ok": False, "results": results, "error": error}
        kind = op.get("op")
        handler = _LIVE_OP_HANDLERS.get(kind)
        if handler is None:
            error = f"op {i} has an unrecognized 'op' value: {kind!r}"
            results.append({"index": i, "op": kind, "ok": False, "data": None, "error": error})
            return {"ok": False, "results": results, "error": error}
        try:
            result = handler(op, cfg)
        except (KeyError, TypeError, AttributeError) as exc:
            error = f"op {i} ({kind}) is missing or has a malformed field: {exc}"
            results.append({"index": i, "op": kind, "ok": False, "data": None, "error": error})
            return {"ok": False, "results": results, "error": error}
        results.append({"index": i, "op": kind, "ok": result.ok,
                         "data": result.data, "error": result.error})
        if not result.ok:
            return {"ok": False, "results": results,
                    "error": f"op {i} ({kind}) failed: {result.error}"}
    return {"ok": True, "results": results, "error": None}


def live_render_node_output(node_name: str, port: int = 0, basename: str = "node_output",
                             profile: str = "Godot/Godot 4 Standard") -> dict:
    """Render a single node's output in isolation on the live graph, without
    leaving it rewired afterward: temporarily reconnects node_name's output
    `port` into the material node's albedo input, renders, then restores
    whatever originally fed albedo_tex -- reconnecting the original source if
    one existed, or disconnecting the temporary wire if albedo_tex started
    out unconnected. Restore always runs, even if the render itself fails, so
    the live window is never left stuck mid-preview -- but if the restore
    call itself fails, that is reported back as ok=False (with the render's
    own image still attached if the render succeeded), never silently
    swallowed, since a failed restore leaves the live graph wired to the
    temporary preview connection. Mirrors render_node_output's batch-path
    return shape ({ok, image, error, log_tail}), but against whatever graph
    is currently open in the live window."""
    cfg, _ = _ensure_ready()
    session = _ensure_live_session(cfg)
    if not session.ok:
        return {"ok": False, "image": None, "error": session.error}
    current = live.get_graph()
    if not current.ok:
        return {"ok": False, "image": None, "error": current.error}
    graph = current.data["graph"]
    try:
        material_name = find_material_node(graph)["name"]
    except ValueError as exc:
        return {"ok": False, "image": None, "error": str(exc)}
    if not any(n.get("name") == node_name for n in graph.get("nodes", [])):
        return {"ok": False, "image": None,
                "error": f"no node named '{node_name}' in the live graph"}
    original = next((c for c in graph.get("connections", [])
                      if c.get("to") == material_name and c.get("to_port", 0) == 0), None)

    preview = live.connect_nodes(node_name, port, material_name, 0, cfg=cfg)
    if not preview.ok:
        return {"ok": False, "image": None, "error": preview.error}

    result = live.render(basename=basename, profile=profile, cfg=cfg)

    if original is not None:
        restore = live.connect_nodes(original["from"], original.get("from_port", 0),
                                      material_name, 0, cfg=cfg)
    else:
        restore = live.disconnect_nodes(node_name, port, material_name, 0, cfg=cfg)
    restore_warning = None
    if not restore.ok:
        restore_warning = (f"restoring the original wiring failed: {restore.error} -- "
                            "the live graph is still wired to the temporary preview connection")

    if not result.ok:
        error = result.error
        if restore_warning:
            error = f"{error}; additionally, {restore_warning}"
        return {"ok": False, "image": None, "error": error,
                "log_tail": result.log_tail}
    albedo = next((p for p in result.images if p.endswith("_albedo.png")), None)
    if albedo is None:
        error = "render succeeded but no albedo output was produced"
        if restore_warning:
            error = f"{error}; additionally, {restore_warning}"
        return {"ok": False, "image": None, "error": error,
                "log_tail": result.log_tail}
    if restore_warning:
        return {"ok": False, "image": albedo, "error": restore_warning,
                "log_tail": result.log_tail}
    return {"ok": True, "image": albedo, "error": None, "log_tail": result.log_tail}


def live_render(basename: str = "material", profile: str = "Godot/Godot 4 Standard") -> dict:
    """Trigger a render in the live window (the same underlying export path
    the GUI's own render button uses) and return the same {ok, images,
    error, log_tail} shape render_graph already uses."""
    cfg, _ = _ensure_ready()
    session = _ensure_live_session(cfg)
    if not session.ok:
        return {"ok": False, "images": [], "error": session.error, "log_tail": ""}
    result = live.render(basename=basename, profile=profile, cfg=cfg)
    return {"ok": result.ok, "images": result.images, "error": result.error,
            "log_tail": result.log_tail}


# Register the plain functions as MCP tools.
mcp.tool()(list_node_types)
mcp.tool()(describe_node)
mcp.tool()(validate)
mcp.tool()(render_graph)
mcp.tool()(render_node_output)
mcp.tool()(render_preview)
mcp.tool()(save_graph)
mcp.tool()(list_examples)
mcp.tool()(load_example)
mcp.tool()(live_start)
mcp.tool()(live_get_graph)
mcp.tool()(live_apply)
mcp.tool()(live_render)
mcp.tool()(live_render_node_output)
mcp.tool()(live_clear)


@mcp.resource("catalog://nodes")
def catalog_resource() -> str:
    _, catalog = _ensure_ready()
    return json.dumps(catalog, indent=1)


_USAGE = (
    "usage: mm-mcp [--check | --version | --help]\n"
    "  (no args)   start the MCP server over stdio\n"
    "  --check     run the setup preflight (green/red checklist), exit 1 if any fail\n"
    "  --version   print the version\n"
    "  --help      show this message"
)


def main(argv: list | None = None) -> int:
    """Console entry point (`mm-mcp`). Returns a process exit code.

    `--version` prints the version; `--check` runs the setup preflight (green/red
    checklist) without requiring valid config; `--help` prints usage; an
    unrecognized argument prints usage and returns 2 rather than silently
    starting the server. With no args the MCP server starts over stdio,
    materializing config + catalog via _ensure_ready() first (which fails fast
    with an actionable message if MM_GODOT_BINARY / MM_PROJECT_PATH are missing
    or wrong).
    """
    args = list(sys.argv[1:] if argv is None else argv)
    if "--help" in args or "-h" in args:
        print(_USAGE)
        return 0
    if "--version" in args:
        print(f"mm-mcp {__version__}")
        return 0
    if "--check" in args:
        return run_check()
    if args:
        print(f"mm-mcp: unrecognized argument(s): {' '.join(args)}", file=sys.stderr)
        print(_USAGE, file=sys.stderr)
        return 2
    _ensure_ready()
    mcp.run()
    return 0


if __name__ == "__main__":
    sys.exit(main())

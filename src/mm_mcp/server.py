import glob
import json
import os
import sys
from mcp.server.mcpserver import MCPServer
from mm_mcp import __version__
from mm_mcp.config import load_config, require_valid
from mm_mcp.catalog_builder import build_catalog
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
    global _cfg, _CATALOG
    _cfg = None
    _CATALOG = None


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


def render_graph(ptex: dict, size: int = 512, basename: str = "material") -> dict:
    cfg, catalog = _ensure_ready()
    problems = validate_graph(ptex, catalog)
    errors = [p for p in problems if p["severity"] == "error"]
    if errors:
        return {"ok": False, "images": [], "error": "validation failed",
                "problems": errors}
    result = render(ptex, size=size, basename=basename, cfg=cfg)
    return {"ok": result.ok, "images": result.images,
            "error": result.error, "log_tail": result.log_tail}


def render_preview(albedo_path: str, normal_path: str, orm_path: str,
                    basename: str = "preview") -> dict:
    """Composite a material's already-rendered maps onto a lit sphere + cube.

    Call render_graph first and pass its albedo/normal/orm output paths here;
    this does not render a graph itself, only visualizes maps that already
    exist, so a normal map's relief is visible under real lighting instead of
    read as a flat swatch.
    """
    cfg, _ = _ensure_ready()
    result = _render_preview(albedo_path, normal_path, orm_path,
                              basename=basename, cfg=cfg)
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


# Register the plain functions as MCP tools.
mcp.tool()(list_node_types)
mcp.tool()(describe_node)
mcp.tool()(validate)
mcp.tool()(render_graph)
mcp.tool()(render_preview)
mcp.tool()(save_graph)
mcp.tool()(list_examples)
mcp.tool()(load_example)


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

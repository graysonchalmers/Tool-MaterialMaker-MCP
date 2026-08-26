import glob
import json
import os
from mcp.server.mcpserver import MCPServer
from mm_mcp.config import load_config
from mm_mcp.catalog_builder import build_catalog
from mm_mcp.validator import validate_graph
from mm_mcp.render import render

_cfg = load_config()
_CATALOG = build_catalog(_cfg.nodes_dir)

mcp = MCPServer("material-maker")


def list_node_types(category: str = "") -> list:
    names = sorted(_CATALOG.keys())
    if category:
        names = [n for n in names if category in n]
    return names


def describe_node(node_type: str) -> dict:
    if node_type not in _CATALOG:
        return {"error": f"unknown node type '{node_type}'"}
    return _CATALOG[node_type]


def validate(ptex: dict) -> list:
    return validate_graph(ptex, _CATALOG)


def render_graph(ptex: dict, size: int = 512, basename: str = "material") -> dict:
    problems = validate_graph(ptex, _CATALOG)
    errors = [p for p in problems if p["severity"] == "error"]
    if errors:
        return {"ok": False, "images": [], "error": "validation failed",
                "problems": errors}
    result = render(ptex, size=size, basename=basename, cfg=_cfg)
    return {"ok": result.ok, "images": result.images,
            "error": result.error, "log_tail": result.log_tail}


def save_graph(ptex: dict, path: str) -> str:
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(ptex, fh, indent=1)
    return path


def list_examples() -> list:
    return sorted(os.path.splitext(os.path.basename(p))[0]
                  for p in glob.glob(os.path.join(_cfg.examples_dir, "*.ptex")))


def load_example(name: str) -> dict:
    path = os.path.join(_cfg.examples_dir, name + ".ptex")
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


# Register the plain functions as MCP tools.
mcp.tool()(list_node_types)
mcp.tool()(describe_node)
mcp.tool()(validate)
mcp.tool()(render_graph)
mcp.tool()(save_graph)
mcp.tool()(list_examples)
mcp.tool()(load_example)


@mcp.resource("catalog://nodes")
def catalog_resource() -> str:
    return json.dumps(_CATALOG, indent=1)


if __name__ == "__main__":
    mcp.run()

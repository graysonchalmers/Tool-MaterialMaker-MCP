import json
import os
from mm_mcp import server
from mm_mcp.config import load_config

cfg = load_config()


def test_list_node_types_includes_blend():
    assert "blend" in server.list_node_types()


def test_describe_node_returns_ports():
    d = server.describe_node("blend")
    assert [i["name"] for i in d["inputs"]] == ["s1", "s2", "a"]


def test_validate_flags_unknown_type():
    ptex = {"type": "graph", "nodes": [{"name": "x", "type": "nope", "parameters": {}}],
            "connections": []}
    errs = [p for p in server.validate(ptex) if p["severity"] == "error"]
    assert errs


def test_list_and_load_example():
    names = server.list_examples()
    assert "bricks" in names
    d = server.load_example("bricks")
    assert d["type"] == "graph"


def test_save_graph_writes_file(tmp_path):
    ptex = {"type": "graph", "nodes": [], "connections": []}
    out = os.path.join(str(tmp_path), "mat.ptex")
    server.save_graph(ptex, out)
    assert os.path.exists(out)
    with open(out, encoding="utf-8") as fh:
        assert json.load(fh)["type"] == "graph"

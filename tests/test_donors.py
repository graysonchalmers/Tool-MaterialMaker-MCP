"""Vendored donor examples: the 9 Material Maker bundled graphs the Phase 3
authoring pipeline actually reads via author_helpers.load_example(). Vendored
2026-09-03 so the pipeline doesn't depend on the external Material Maker
checkout (cfg.examples_dir) being present. Mirrors tests/test_examples_gate.py
and tests/test_cookbook_gate.py, scoped to this tracked 9-file set instead of
the live external checkout's 43."""
import json
import os
import pytest
from mm_mcp.catalog_builder import build_catalog
from mm_mcp.config import load_config
from mm_mcp.validator import validate_graph

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DONORS_DIR = os.path.join(_ROOT, "quality", "donors")
DONOR_NAMES = [
    "beehive", "crocodile_skin", "dry_earth", "metal_pattern_2", "rock",
    "rusted_metal", "stone_wall", "wood", "wooden_floor",
]
cfg = load_config()
CATALOG = build_catalog(cfg.nodes_dir)


def _all_graphs(node):
    """Yield the node itself and every nested subgraph (has a 'nodes' list)."""
    if isinstance(node, dict) and "nodes" in node:
        yield node
        for child in node["nodes"]:
            yield from _all_graphs(child)


def test_all_nine_donor_files_are_present():
    missing = [n for n in DONOR_NAMES
               if not os.path.isfile(os.path.join(DONORS_DIR, f"{n}.ptex"))]
    assert missing == [], f"missing donor files: {missing}"


@pytest.mark.parametrize("name", DONOR_NAMES)
def test_donor_file_is_valid_json_graph(name):
    path = os.path.join(DONORS_DIR, f"{name}.ptex")
    with open(path, encoding="utf-8") as fh:
        graph = json.load(fh)
    assert "nodes" in graph
    assert "connections" in graph


@pytest.mark.parametrize("name", DONOR_NAMES)
def test_donor_graph_has_no_type_or_connection_errors(name):
    path = os.path.join(DONORS_DIR, f"{name}.ptex")
    with open(path, encoding="utf-8") as fh:
        root = json.load(fh)
    hard_errors = []
    for g in _all_graphs(root):
        for p in validate_graph(g, CATALOG):
            if p["severity"] == "error":
                hard_errors.append(p["message"])
    assert hard_errors == [], f"{name}: {hard_errors}"

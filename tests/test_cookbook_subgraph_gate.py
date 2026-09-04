"""Regression gate for the cookbook-subgraph retrofit: every tracked cookbook
graph has at least one top-level subgraph ("graph" type) node, so future
materials keep using group_into_subgraph instead of drifting back to flat
graphs. Mirrors tests/test_cookbook_gate.py."""
import json
import os

import pytest
from mm_mcp.cookbook import list_cookbook

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
COOKBOOK_DIR = os.path.join(_ROOT, "cookbook")
ENTRIES = list_cookbook(COOKBOOK_DIR)


@pytest.mark.parametrize("entry", ENTRIES, ids=[e.name for e in ENTRIES])
def test_cookbook_material_uses_at_least_one_subgraph(entry):
    with open(entry.path, encoding="utf-8") as fh:
        graph = json.load(fh)
    top_level_types = {n["type"] for n in graph["nodes"]}
    assert "graph" in top_level_types, (
        f"{entry.name} has no top-level subgraph node; "
        "expected at least one from the subgraph retrofit"
    )

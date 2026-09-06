"""Gate for the 2026-09-06 role-name pass: no node in any tracked cookbook
graph, at any level, carries a donor auto-name, a bare type name, or a
sibling-duplicate name. Mirrors tests/test_cookbook_subgraph_gate.py."""
import json
import os

import pytest
from mm_mcp.cookbook import list_cookbook
from quality.naming import find_bad_names

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
COOKBOOK_DIR = os.path.join(_ROOT, "cookbook")
ENTRIES = list_cookbook(COOKBOOK_DIR)


@pytest.mark.parametrize("entry", ENTRIES, ids=[e.name for e in ENTRIES])
def test_every_cookbook_node_has_a_role_name(entry):
    with open(entry.path, encoding="utf-8") as fh:
        graph = json.load(fh)
    problems = find_bad_names(graph)
    assert problems == [], f"{entry.name}:\n  " + "\n  ".join(problems)

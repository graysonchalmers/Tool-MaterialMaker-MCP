"""What counts as a role name in a cookbook graph, and a checker for it.

Rules (docs/AUTHORING.md, "Name every node by role"):
  - no donor auto-names:  colorize_0, blend_grain_2, perlin_pm_1  (ends in _<digits>)
  - no bare type names:   colorize, Perlin, graph                 (name == node type, any case)
  - no upstream junk:     names starting with an underscore
  - unique among siblings at each level
Reserved names (Material, gen_inputs, gen_outputs, gen_parameters) and nodes
of type ios / remote / material are not checked.

CLI:
  python -m quality.naming --cookbook            # every tracked cookbook graph
  python -m quality.naming --cookbook stone      # one category
  python -m quality.naming path/to/a.ptex ...    # specific files
Exit 1 if any problem is printed.
"""
import json
import re
import sys
from collections import Counter
from pathlib import Path

from quality.author_helpers import RESERVED_NODE_NAMES
from mm_mcp.cookbook import list_cookbook

_ROOT = Path(__file__).resolve().parent.parent
COOKBOOK = _ROOT / "cookbook"
AUTO_NAME = re.compile(r"^[A-Za-z][A-Za-z0-9]*(?:_[A-Za-z0-9]+)*_\d+$")
SKIP_TYPES = frozenset({"ios", "remote", "material"})


def _levels(graph: dict, label: str = ""):
    yield label, graph.get("nodes", [])
    for n in graph.get("nodes", []):
        if n.get("type") == "graph":
            yield from _levels(n, n["name"] if not label else f"{label}/{n['name']}")


def iter_nodes(graph: dict):
    """(level_label, node) for every checkable node at every level."""
    for label, nodes in _levels(graph):
        for n in nodes:
            if n.get("name") in RESERVED_NODE_NAMES or n.get("type") in SKIP_TYPES:
                continue
            yield label, n


def find_bad_names(graph: dict) -> list[str]:
    problems = []
    for label, nodes in _levels(graph):
        counts = Counter(n.get("name") for n in nodes)
        for name, k in counts.items():
            if k > 1:
                problems.append(f"{label or 'top level'}: duplicate sibling name {name!r} x{k}")
    for label, n in iter_nodes(graph):
        name, ntype = n["name"], n.get("type", "")
        where = f"{label}/{name}" if label else name
        if name.startswith("_"):
            problems.append(f"{where}: upstream junk name (leading underscore)")
        elif AUTO_NAME.match(name):
            problems.append(f"{where}: donor auto-name (ends in _<digits>); give it a role name")
        elif name.lower() == ntype.lower():
            problems.append(f"{where}: bare type name {name!r}; say what it contributes")
    return problems


def main(argv: list[str]) -> int:
    paths: list[Path] = []
    if "--cookbook" in argv:
        i = argv.index("--cookbook")
        category = argv[i + 1] if i + 1 < len(argv) and not argv[i + 1].startswith("-") else None
        for e in list_cookbook(str(COOKBOOK)):
            if category is None or e.category == category:
                paths.append(Path(e.path))
        argv = [a for a in argv if a not in ("--cookbook", category)]
    paths += [Path(a) for a in argv if a.endswith(".ptex")]
    total = 0
    for p in paths:
        graph = json.loads(p.read_text(encoding="utf-8"))
        for problem in find_bad_names(graph):
            print(f"{p}: {problem}")
            total += 1
    print(f"{len(paths)} graph(s) checked, {total} problem(s)")
    return 1 if total else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

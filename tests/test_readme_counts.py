"""README numbers must match the tree. Teardowns #1 and #3 both found
hand-typed counts that had drifted (11/15 vs 15/15; six live tools vs seven;
46 materials vs a 43-material contact sheet). This closes the drift class:
the README states counts in digits and this test recomputes them."""
import inspect
import os
import re

from mm_mcp import server
from mm_mcp.cookbook import list_cookbook

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
README = open(os.path.join(_ROOT, "README.md"), encoding="utf-8").read()
ENTRIES = list_cookbook(os.path.join(_ROOT, "cookbook"))


def _live_tool_count() -> int:
    return len([name for name, obj in vars(server).items()
                if name.startswith("live_") and inspect.isfunction(obj)])


def test_readme_cookbook_material_count_matches_tree():
    m = re.search(r"cookbook is (\d+) materials across (\d+) categories", README)
    assert m, "README 'Material cookbook' sentence must read '<N> materials across <M> categories'"
    assert int(m.group(1)) == len(ENTRIES)
    assert int(m.group(2)) == len({e.category for e in ENTRIES})


def test_readme_contact_sheet_summary_count_matches_tree():
    m = re.search(r"Show the cookbook contact sheet</b> \((\d+) materials:", README)
    assert m, "contact-sheet <summary> must state '(<N> materials:'"
    assert int(m.group(1)) == len(ENTRIES)


def test_readme_play_surface_count_matches_tree():
    m = re.search(r"gallery of the (\d+)\s+cookbook materials", README)
    assert m, "Play surface paragraph must read 'gallery of the <N> cookbook materials'"
    assert int(m.group(1)) == len(ENTRIES)


def test_readme_live_tool_count_matches_server():
    m = re.search(r"plus (\d+) more in Live mode", README)
    assert m, "Tools sentence must read 'plus <N> more in Live mode'"
    assert int(m.group(1)) == _live_tool_count()


def test_readme_live_tool_table_lists_every_live_tool():
    rows = set(re.findall(r"^\| `(live_\w+)` \|", README, flags=re.M))
    expected = {name for name, obj in vars(server).items()
                if name.startswith("live_") and inspect.isfunction(obj)}
    assert rows == expected

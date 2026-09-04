import os
from mm_mcp.cookbook import CookbookEntry, list_cookbook, find_cookbook


def _make(tmp_path, category, name):
    d = tmp_path / category
    d.mkdir(exist_ok=True)
    p = d / f"{name}.ptex"
    p.write_text('{"type": "graph"}', encoding="utf-8")
    return str(p)


def test_list_cookbook_walks_category_dirs_sorted(tmp_path):
    p_wood = _make(tmp_path, "wood", "w05_dark_walnut")
    p_fab = _make(tmp_path, "fabrics", "f07_herringbone_tweed")
    entries = list_cookbook(str(tmp_path))
    assert entries == [
        CookbookEntry(name="f07_herringbone_tweed", category="fabrics", path=p_fab),
        CookbookEntry(name="w05_dark_walnut", category="wood", path=p_wood),
    ]


def test_list_cookbook_ignores_non_ptex_and_top_level_files(tmp_path):
    _make(tmp_path, "stone", "s11_marble")
    (tmp_path / "stone" / "README.md").write_text("x", encoding="utf-8")
    (tmp_path / "stray.ptex").write_text("{}", encoding="utf-8")
    assert [e.name for e in list_cookbook(str(tmp_path))] == ["s11_marble"]


def test_list_cookbook_empty_when_dir_missing_or_unset(tmp_path):
    assert list_cookbook("") == []
    assert list_cookbook(str(tmp_path / "nope")) == []


def test_find_cookbook_returns_entry_or_none(tmp_path):
    p = _make(tmp_path, "terrain", "t05_cracked_ice")
    found = find_cookbook(str(tmp_path), "t05_cracked_ice")
    assert found is not None and found.path == p and found.category == "terrain"
    assert find_cookbook(str(tmp_path), "no_such_thing") is None

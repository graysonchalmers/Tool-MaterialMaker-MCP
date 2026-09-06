import json
from pathlib import Path

from quality.promote_cookbook import node_table, write_card_block, check_card_block, promote


def _authored(tmp_path: Path, label: str, case: str, payload: dict) -> Path:
    d = tmp_path / "authored" / label / case
    d.mkdir(parents=True)
    p = d / "v1.ptex"
    p.write_text(json.dumps(payload, indent=1), encoding="utf-8")
    return p


def test_promote_copies_v1_into_category_dir(tmp_path):
    src = _authored(tmp_path, "cookbook-fabrics", "f07_herringbone_tweed", {"type": "graph"})
    problems = promote(tmp_path / "authored", tmp_path / "cookbook")
    assert problems == []
    dst = tmp_path / "cookbook" / "fabrics" / "f07_herringbone_tweed.ptex"
    assert dst.read_bytes() == src.read_bytes()


def test_promote_reports_case_without_v1(tmp_path):
    (tmp_path / "authored" / "cookbook-wood" / "w09_empty").mkdir(parents=True)
    problems = promote(tmp_path / "authored", tmp_path / "cookbook")
    assert len(problems) == 1
    assert "w09_empty" in problems[0]


def test_check_mode_reports_missing_and_differing(tmp_path):
    _authored(tmp_path, "cookbook-stone", "s11_marble", {"type": "graph", "v": 2})
    _authored(tmp_path, "cookbook-stone", "s10_flagstone", {"type": "graph"})
    tracked = tmp_path / "cookbook" / "stone"
    tracked.mkdir(parents=True)
    (tracked / "s11_marble.ptex").write_text(json.dumps({"type": "graph", "v": 1}, indent=1),
                                             encoding="utf-8")
    problems = promote(tmp_path / "authored", tmp_path / "cookbook", check=True)
    assert any("s11_marble" in p and "differs" in p for p in problems)
    assert any("s10_flagstone" in p and "missing" in p for p in problems)
    assert not (tracked / "s10_flagstone.ptex").exists(), "check mode must not write"


def test_check_mode_is_clean_after_promote(tmp_path):
    _authored(tmp_path, "cookbook-terrain", "t05_cracked_ice", {"type": "graph"})
    assert promote(tmp_path / "authored", tmp_path / "cookbook") == []
    assert promote(tmp_path / "authored", tmp_path / "cookbook", check=True) == []


def test_labels_filter_limits_scope(tmp_path):
    _authored(tmp_path, "cookbook-wood", "w05_dark_walnut", {"type": "graph"})
    _authored(tmp_path, "cookbook-scifi", "sf01_hull_plating", {"type": "graph"})
    promote(tmp_path / "authored", tmp_path / "cookbook", labels=["cookbook-wood"])
    assert (tmp_path / "cookbook" / "wood" / "w05_dark_walnut.ptex").exists()
    assert not (tmp_path / "cookbook" / "scifi").exists()


def test_missing_authored_root_is_a_problem(tmp_path):
    problems = promote(tmp_path / "nope", tmp_path / "cookbook", check=True)
    assert len(problems) == 1
    assert "not a directory" in problems[0]


def test_unknown_label_is_a_problem(tmp_path):
    _authored(tmp_path, "cookbook-wood", "w05_dark_walnut", {"type": "graph"})
    problems = promote(tmp_path / "authored", tmp_path / "cookbook",
                        labels=["cookbook-typo"])
    assert len(problems) == 1
    assert "cookbook-typo" in problems[0]
    assert not (tmp_path / "cookbook").exists()


def test_check_ignores_line_ending_differences(tmp_path):
    payload = json.dumps({"type": "graph"}, indent=1)
    src_dir = tmp_path / "authored" / "cookbook-fabrics" / "f07_herringbone_tweed"
    src_dir.mkdir(parents=True)
    (src_dir / "v1.ptex").write_bytes(payload.replace("\n", "\r\n").encode("utf-8"))
    dst_dir = tmp_path / "cookbook" / "fabrics"
    dst_dir.mkdir(parents=True)
    (dst_dir / "f07_herringbone_tweed.ptex").write_bytes(payload.encode("utf-8"))
    card = dst_dir / "f07_herringbone_tweed.md"
    card.write_text("# f07_herringbone_tweed\n", encoding="utf-8")
    write_card_block(card, {"type": "graph"})
    problems = promote(tmp_path / "authored", tmp_path / "cookbook", check=True)
    assert problems == []


def _graph_for_card():
    return {"nodes": [
        {"name": "Material", "type": "material", "parameters": {}},
        {"name": "plank_structure", "label": "Plank Structure", "type": "graph", "parameters": {},
         "nodes": [
             {"name": "gen_inputs", "type": "ios", "parameters": {}},
             {"name": "gen_outputs", "type": "ios", "parameters": {}},
             {"name": "gen_parameters", "type": "remote", "parameters": {}},
             {"name": "PlankLayout", "type": "bricks", "parameters": {}},
             {"name": "WoodColor", "type": "colorize", "parameters": {}},
         ], "connections": []},
    ], "connections": []}


def test_node_table_lists_every_checkable_node_with_its_level():
    block = node_table(_graph_for_card())
    assert block.startswith("<!-- nodes:begin -->") and block.rstrip().endswith("<!-- nodes:end -->")
    assert "| (top level) | plank_structure | graph |" in block
    assert "| plank_structure | PlankLayout | bricks |" in block
    assert "| plank_structure | WoodColor | colorize |" in block
    assert "Material" not in block.split("|", 1)[1]   # reserved names are not rows


def test_write_card_block_appends_when_missing_and_replaces_when_present(tmp_path):
    card = tmp_path / "x.md"
    card.write_text("# x\n\nprose\n", encoding="utf-8")
    g = _graph_for_card()
    write_card_block(card, g)
    first = card.read_text(encoding="utf-8")
    assert first.startswith("# x\n\nprose\n") and first.count("<!-- nodes:begin -->") == 1
    g["nodes"][1]["nodes"][3]["name"] = "PlankGrid"
    write_card_block(card, g)
    second = card.read_text(encoding="utf-8")
    assert second.count("<!-- nodes:begin -->") == 1
    assert "PlankGrid" in second and "PlankLayout" not in second
    assert second.startswith("# x\n\nprose\n")


def test_check_card_block_reports_missing_and_stale(tmp_path):
    card = tmp_path / "x.md"
    card.write_text("# x\n", encoding="utf-8")
    g = _graph_for_card()
    assert "missing" in check_card_block(card, g)
    write_card_block(card, g)
    assert check_card_block(card, g) is None
    g["nodes"][1]["nodes"][3]["name"] = "PlankGrid"
    assert "stale" in check_card_block(card, g)


def test_promote_writes_and_checks_card_blocks(tmp_path):
    authored = tmp_path / "authored" / "cookbook-wood" / "w09_test"
    authored.mkdir(parents=True)
    (authored / "v1.ptex").write_text(json.dumps(_graph_for_card()), encoding="utf-8")
    cookbook = tmp_path / "cookbook"
    (cookbook / "wood").mkdir(parents=True)
    (cookbook / "wood" / "w09_test.md").write_text("# w09_test\n", encoding="utf-8")
    assert promote(tmp_path / "authored", cookbook) == []
    assert "<!-- nodes:begin -->" in (cookbook / "wood" / "w09_test.md").read_text(encoding="utf-8")
    assert promote(tmp_path / "authored", cookbook, check=True) == []
    (cookbook / "wood" / "w09_test.md").write_text("# w09_test\n", encoding="utf-8")
    problems = promote(tmp_path / "authored", cookbook, check=True)
    assert len(problems) == 1 and "w09_test.md" in problems[0]

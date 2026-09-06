import json
import pytest
from quality.naming import find_bad_names, iter_nodes, main


def _graph(names_top, names_sub=()):
    sub_nodes = [
        {"name": "gen_inputs", "type": "ios", "parameters": {}},
        {"name": "gen_outputs", "type": "ios", "parameters": {}},
        {"name": "gen_parameters", "type": "remote", "parameters": {}},
    ] + [{"name": n, "type": t, "parameters": {}} for n, t in names_sub]
    return {
        "nodes": [{"name": "Material", "type": "material", "parameters": {}}]
                 + [{"name": n, "type": t, "parameters": {}} for n, t in names_top]
                 + ([{"name": "grain", "type": "graph", "parameters": {},
                      "nodes": sub_nodes, "connections": []}] if names_sub else []),
        "connections": [],
    }


def test_iter_nodes_skips_reserved_and_yields_levels():
    g = _graph([("GrainNoise", "perlin")], [("WoodColor", "colorize")])
    got = [(lvl, n["name"]) for lvl, n in iter_nodes(g)]
    assert got == [("", "GrainNoise"), ("", "grain"), ("grain", "WoodColor")]


def test_clean_graph_has_no_problems():
    g = _graph([("GrainNoise", "perlin")], [("WoodColor", "colorize"), ("PlankLayout", "bricks")])
    assert find_bad_names(g) == []


@pytest.mark.parametrize("name,ntype", [
    ("colorize_0", "colorize"),      # donor auto-name
    ("blend_grain_2", "blend"),      # auto-name with a role infix still ends in _N
    ("colorize", "colorize"),        # bare type name
    ("Perlin", "perlin"),            # bare type name, capitalised
    ("graph", "graph"),              # bare type name for a subgraph
    ("_2_2", "blend"),               # upstream junk name
])
def test_flags_auto_and_bare_type_names(name, ntype):
    g = _graph([], [(name, ntype)])
    problems = find_bad_names(g)
    assert len(problems) == 1 and f"grain/{name}" in problems[0]


def test_role_names_with_digits_are_fine_when_not_a_suffix():
    g = _graph([("Layer2Mask", "colorize"), ("Voronoi3Cells", "voronoi")])
    assert find_bad_names(g) == []


def test_sibling_collision_is_flagged():
    g = {"nodes": [
        {"name": "Material", "type": "material", "parameters": {}},
        {"name": "MossMask", "type": "colorize", "parameters": {}},
        {"name": "MossMask", "type": "colorize", "parameters": {}},
    ], "connections": []}
    problems = find_bad_names(g)
    assert any("duplicate" in p for p in problems)


def test_cli_exit_code_and_output(tmp_path, capsys):
    good = tmp_path / "good.ptex"
    bad = tmp_path / "bad.ptex"
    good.write_text(json.dumps(_graph([("GrainNoise", "perlin")])), encoding="utf-8")
    bad.write_text(json.dumps(_graph([("perlin_0", "perlin")])), encoding="utf-8")
    assert main([str(good)]) == 0
    assert main([str(bad)]) == 1
    assert "perlin_0" in capsys.readouterr().out


def test_cli_cookbook_flag_followed_by_a_file_checks_that_file(tmp_path, capsys, monkeypatch):
    import quality.naming as naming
    monkeypatch.setattr(naming, "COOKBOOK", tmp_path / "no-such-cookbook")
    bad = tmp_path / "bad.ptex"
    bad.write_text(json.dumps(_graph([("perlin_0", "perlin")])), encoding="utf-8")
    assert main(["--cookbook", str(bad)]) == 1
    out = capsys.readouterr().out
    assert "perlin_0" in out and "1 graph(s) checked" in out

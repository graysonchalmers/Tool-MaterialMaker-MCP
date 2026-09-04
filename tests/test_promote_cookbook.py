import json
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT / "quality"))

from promote_cookbook import promote  # noqa: E402


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

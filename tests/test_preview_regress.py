from pathlib import Path
from PIL import Image
from quality.preview_regress import compare_previews

def _png(p: Path, color):
    p.parent.mkdir(parents=True, exist_ok=True)
    Image.new("RGB", (64, 64), color).save(p)

def test_identical_previews_match(tmp_path):
    base, cur = tmp_path / "b", tmp_path / "c"
    _png(base / "s07_cobblestone.png", (120, 120, 120))
    _png(cur / "s07_cobblestone.png", (120, 120, 120))
    assert compare_previews(base, cur, ["s07_cobblestone"]) == []

def test_differing_previews_flagged(tmp_path):
    base, cur = tmp_path / "b", tmp_path / "c"
    _png(base / "s07_cobblestone.png", (30, 30, 30))
    _png(cur / "s07_cobblestone.png", (200, 200, 200))
    problems = compare_previews(base, cur, ["s07_cobblestone"])
    assert len(problems) == 1 and "s07_cobblestone" in problems[0]

def test_missing_current_flagged(tmp_path):
    base, cur = tmp_path / "b", tmp_path / "c"
    _png(base / "s07_cobblestone.png", (120, 120, 120))
    cur.mkdir()
    problems = compare_previews(base, cur, ["s07_cobblestone"])
    assert len(problems) == 1 and "missing" in problems[0].lower()

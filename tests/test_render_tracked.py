from pathlib import Path
from types import SimpleNamespace

from quality.pngread import Sampler  # noqa: F401  (import guard: module must exist)
from quality.render_tracked import MAPS, compare_dirs


def _png(path: Path, value: int):
    """Write a tiny uniform 4x4 RGB PNG with every channel = value."""
    import struct, zlib
    raw = b"".join(b"\x00" + bytes([value, value, value]) * 4 for _ in range(4))
    def chunk(tag, data):
        return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", 4, 4, 8, 2, 0, 0, 0))
                     + chunk(b"IDAT", zlib.compress(raw)) + chunk(b"IEND", b""))


def _entry(category, name):
    return SimpleNamespace(category=category, name=name, path=f"{category}/{name}.ptex")


def test_compare_dirs_reports_only_mismatching_maps(tmp_path):
    base, cur = tmp_path / "base", tmp_path / "cur"
    e = _entry("wood", "w04_driftwood_gray")
    for m in MAPS:
        _png(base / "wood" / f"w04_driftwood_gray_{m}.png", 100)
        _png(cur / "wood" / f"w04_driftwood_gray_{m}.png", 100)
    _png(cur / "wood" / "w04_driftwood_gray_normal.png", 180)   # moved
    problems = compare_dirs(base, cur, [e])
    assert len(problems) == 1
    assert "w04_driftwood_gray_normal.png" in problems[0]


def test_compare_dirs_flags_missing_files(tmp_path):
    base, cur = tmp_path / "base", tmp_path / "cur"
    e = _entry("wood", "w05_dark_walnut")
    for m in MAPS:
        _png(base / "wood" / f"w05_dark_walnut_{m}.png", 50)
    problems = compare_dirs(base, cur, [e])
    assert len(problems) == len(MAPS)
    assert all("missing" in p for p in problems)


def test_main_resolves_out_and_compare_to_absolute_paths(tmp_path, monkeypatch):
    import quality.render_tracked as rt
    seen = {}

    def fake_render_entries(entries, out, size):
        seen["out"] = out
        return []

    def fake_compare_dirs(baseline, current, entries):
        seen["baseline"] = baseline
        return []

    monkeypatch.setattr(rt, "render_entries", fake_render_entries)
    monkeypatch.setattr(rt, "compare_dirs", fake_compare_dirs)
    monkeypatch.setattr(rt, "list_cookbook", lambda d: [_entry("wood", "w04_driftwood_gray")])
    monkeypatch.chdir(tmp_path)
    assert rt.main(["--out", "rel-out", "--compare", "rel-base"]) == 0
    assert seen["out"].is_absolute() and seen["out"] == (tmp_path / "rel-out").resolve()
    assert seen["baseline"].is_absolute() and seen["baseline"] == (tmp_path / "rel-base").resolve()

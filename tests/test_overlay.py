import os
from mm_mcp.overlay import _hash_dir, _append_autoload


def _write(path, rel, content):
    full = os.path.join(path, rel)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w", encoding="utf-8") as fh:
        fh.write(content)


def test_hash_dir_stable_for_identical_contents(tmp_path):
    a = tmp_path / "a"
    a.mkdir()
    _write(str(a), "one.txt", "hello")
    _write(str(a), "sub/two.txt", "world")

    assert _hash_dir(str(a)) == _hash_dir(str(a))


def test_hash_dir_changes_when_file_content_changes(tmp_path):
    a = tmp_path / "a"
    a.mkdir()
    _write(str(a), "one.txt", "hello")
    before = _hash_dir(str(a))

    _write(str(a), "one.txt", "hello world")
    after = _hash_dir(str(a))

    assert before != after


def test_hash_dir_changes_when_file_added(tmp_path):
    a = tmp_path / "a"
    a.mkdir()
    _write(str(a), "one.txt", "hello")
    before = _hash_dir(str(a))

    _write(str(a), "two.txt", "new")
    after = _hash_dir(str(a))

    assert before != after


_FAKE_PROJECT_GODOT = """; fake project.godot, mirrors real MM's shape

[application]

config/name="fake"

[autoload]

mm_globals="*res://material_maker/globals.tscn"
Html5="*res://material_maker/html5.gd"

[display]

window/size/width=1920
"""


def test_append_autoload_adds_the_line(tmp_path):
    pg = tmp_path / "project.godot"
    pg.write_text(_FAKE_PROJECT_GODOT, encoding="utf-8")

    _append_autoload(str(pg), "mm_live")

    content = pg.read_text(encoding="utf-8")
    assert 'mm_live="*res://addons/mm_live/live_server.gd"' in content


def test_append_autoload_is_idempotent(tmp_path):
    pg = tmp_path / "project.godot"
    pg.write_text(_FAKE_PROJECT_GODOT, encoding="utf-8")

    _append_autoload(str(pg), "mm_live")
    _append_autoload(str(pg), "mm_live")

    content = pg.read_text(encoding="utf-8")
    assert content.count('mm_live="*res://addons/mm_live/live_server.gd"') == 1


def test_append_autoload_inserts_before_next_section(tmp_path):
    pg = tmp_path / "project.godot"
    pg.write_text(_FAKE_PROJECT_GODOT, encoding="utf-8")

    _append_autoload(str(pg), "mm_live")

    content = pg.read_text(encoding="utf-8")
    # The line should appear BEFORE the [display] section header
    mm_live_pos = content.find('mm_live="*res://addons/mm_live/live_server.gd"')
    display_pos = content.find("[display]")
    assert mm_live_pos != -1, "mm_live line not found"
    assert display_pos != -1, "[display] section not found"
    assert mm_live_pos < display_pos, "mm_live line should appear before [display]"


def test_append_autoload_raises_when_no_autoload_section(tmp_path):
    pg = tmp_path / "project.godot"
    no_autoload = """; fake project.godot without section

[application]

config/name="fake"
"""
    pg.write_text(no_autoload, encoding="utf-8")

    try:
        _append_autoload(str(pg), "mm_live")
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "no [autoload] section found" in str(e)

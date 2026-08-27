import os
import pytest
from mm_mcp.overlay import _hash_dir, _append_autoload, _write_marker, _is_stale
from mm_mcp.overlay import ensure_overlay


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


def test_is_stale_true_when_no_marker(tmp_path):
    overlay = tmp_path / "overlay"
    overlay.mkdir()
    assert _is_stale(str(overlay), "hash1", "/mm/project") is True


def test_is_stale_false_when_marker_matches(tmp_path):
    overlay = tmp_path / "overlay"
    overlay.mkdir()
    _write_marker(str(overlay), "hash1", "/mm/project")
    assert _is_stale(str(overlay), "hash1", "/mm/project") is False


def test_is_stale_true_when_addon_hash_differs(tmp_path):
    overlay = tmp_path / "overlay"
    overlay.mkdir()
    _write_marker(str(overlay), "hash1", "/mm/project")
    assert _is_stale(str(overlay), "hash2", "/mm/project") is True


def test_is_stale_true_when_mm_project_path_differs(tmp_path):
    overlay = tmp_path / "overlay"
    overlay.mkdir()
    _write_marker(str(overlay), "hash1", "/mm/project")
    assert _is_stale(str(overlay), "hash1", "/mm/other_project") is True


def test_is_stale_true_when_marker_is_non_dict_json(tmp_path):
    """Regression test: marker file with valid JSON that's not a dict should
    be treated as stale, not raise AttributeError."""
    overlay = tmp_path / "overlay"
    overlay.mkdir()
    marker_file = overlay / ".mm_overlay_marker.json"
    # Write a valid JSON value that's not a dict
    marker_file.write_text('"not-a-dict"', encoding="utf-8")
    # Should return True (stale), not raise AttributeError
    assert _is_stale(str(overlay), "hash1", "/mm/project") is True


def test_is_stale_true_when_marker_is_list_json(tmp_path):
    """Regression test: marker file with valid JSON list should be treated as stale."""
    overlay = tmp_path / "overlay"
    overlay.mkdir()
    marker_file = overlay / ".mm_overlay_marker.json"
    # Write a valid JSON list instead of dict
    marker_file.write_text('[1, 2]', encoding="utf-8")
    assert _is_stale(str(overlay), "hash1", "/mm/project") is True


@pytest.fixture
def fake_checkout(tmp_path):
    checkout = tmp_path / "mm_checkout"
    checkout.mkdir()
    _write(str(checkout), "project.godot", _FAKE_PROJECT_GODOT)
    _write(str(checkout), "steam_appid.txt", "4110830")
    _write(str(checkout), "material_maker/globals.gd", "# real MM file")
    return checkout


@pytest.fixture
def fake_addon(tmp_path):
    addon = tmp_path / "mm_live"
    addon.mkdir()
    _write(str(addon), "live_server.gd", "extends Node\n# v1")
    return addon


def test_ensure_overlay_first_build(tmp_path, fake_checkout, fake_addon):
    overlay_dir = str(tmp_path / "overlay")

    result = ensure_overlay(str(fake_checkout), str(fake_addon), overlay_dir)

    assert result == overlay_dir
    project_godot = (tmp_path / "overlay" / "project.godot").read_text(encoding="utf-8")
    # Assert position, not just presence: a regression to appending blindly
    # at end-of-file (Task 2's original bug) would still leave this
    # substring in the file -- just after [display] instead of inside
    # [autoload] -- and a substring-only check would miss it.
    mm_live_pos = project_godot.find('mm_live="*res://addons/mm_live/live_server.gd"')
    display_pos = project_godot.find("[display]")
    assert mm_live_pos != -1, "mm_live autoload line not found"
    assert display_pos != -1, "[display] section not found"
    assert mm_live_pos < display_pos, "mm_live line should land inside [autoload], before [display]"
    assert (tmp_path / "overlay" / "addons" / "mm_live" / "live_server.gd").read_text(
        encoding="utf-8") == "extends Node\n# v1"
    # steam_appid.txt gotcha: must survive the whole-checkout copy or MM
    # self-relaunches and exits (see CLAUDE.md).
    assert (tmp_path / "overlay" / "steam_appid.txt").read_text(encoding="utf-8") == "4110830"
    assert (tmp_path / "overlay" / "material_maker" / "globals.gd").exists()

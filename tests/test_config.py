import os
import pytest
from mm_mcp.config import load_config, require_valid


def test_config_loads_paths():
    cfg = load_config()
    assert cfg.project_path
    assert cfg.nodes_dir.endswith("nodes")
    assert cfg.examples_dir.endswith("examples")


def test_console_binary_resolves(tmp_path):
    gui = tmp_path / "Godot_win64.exe"
    gui.write_text("x")
    console = tmp_path / "Godot_win64_console.exe"
    console.write_text("x")
    cfg = load_config(overrides={"MM_GODOT_BINARY": str(gui)})
    assert cfg.console_binary == str(console)


def test_console_binary_falls_back_when_absent(tmp_path):
    gui = tmp_path / "OnlyGui.exe"
    gui.write_text("x")
    cfg = load_config(overrides={"MM_GODOT_BINARY": str(gui)})
    assert cfg.console_binary == str(gui)


def test_require_valid_passes_for_real_machine_config():
    cfg = load_config()
    require_valid(cfg)  # must not raise on this machine


def test_require_valid_raises_on_bogus_project_path(tmp_path):
    bogus = str(tmp_path / "no-such-mm-project")
    cfg = load_config(overrides={"MM_PROJECT_PATH": bogus})
    with pytest.raises(FileNotFoundError) as exc_info:
        require_valid(cfg)
    msg = str(exc_info.value)
    assert bogus in msg
    assert "MM_PROJECT_PATH" in msg


def test_require_valid_raises_on_bogus_nodes_dir(tmp_path):
    # A project_path that exists but has no addons/material_maker/nodes dir.
    real_project = tmp_path / "mm-project"
    real_project.mkdir()
    cfg = load_config(overrides={"MM_PROJECT_PATH": str(real_project)})
    with pytest.raises(FileNotFoundError) as exc_info:
        require_valid(cfg)
    msg = str(exc_info.value)
    assert cfg.nodes_dir in msg


def test_require_valid_raises_on_bogus_godot_binary(tmp_path):
    bogus_binary = str(tmp_path / "NoSuchGodot.exe")
    cfg = load_config(overrides={"MM_GODOT_BINARY": bogus_binary})
    with pytest.raises(FileNotFoundError) as exc_info:
        require_valid(cfg)
    msg = str(exc_info.value)
    assert bogus_binary in msg
    assert "MM_GODOT_BINARY" in msg


def test_live_overlay_dir_defaults_to_cwd_subfolder():
    cfg = load_config()
    assert cfg.live_overlay_dir == os.path.join(os.getcwd(), "mm_live_overlay")


def test_live_overlay_dir_respects_override():
    cfg = load_config(overrides={"MM_LIVE_OVERLAY_DIR": r"C:\somewhere\overlay"})
    assert cfg.live_overlay_dir == r"C:\somewhere\overlay"


import os as _os
from mm_mcp.config import load_config as _load_config


def test_allowed_roots_defaults_empty():
    cfg = _load_config(overrides={"MM_ALLOWED_ROOTS": ""})
    assert cfg.allowed_roots == []


def test_allowed_roots_parses_pathsep_list():
    raw = _os.pathsep.join([r"C:\a", r"C:\b"])
    cfg = _load_config(overrides={"MM_ALLOWED_ROOTS": raw})
    assert cfg.allowed_roots == [r"C:\a", r"C:\b"]


def test_allowed_roots_drops_empty_segments():
    raw = _os.pathsep.join([r"C:\a", "", r"C:\b"])
    cfg = _load_config(overrides={"MM_ALLOWED_ROOTS": raw})
    assert cfg.allowed_roots == [r"C:\a", r"C:\b"]

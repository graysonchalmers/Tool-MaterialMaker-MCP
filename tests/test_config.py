import os
from mm_mcp.config import load_config


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

import os
import pytest
from mm_mcp import server
from mm_mcp.config import load_config
from mm_mcp.doctor import check_setup, all_ok, Check

# Test support imports (added for Task 4)
from mm_mcp.doctor import check_setup as _check_setup
from mm_mcp.config import load_config as _load_config


def test_all_checks_pass_on_real_machine():
    # On the machine this is developed on, a full preflight is green.
    checks = check_setup(load_config())
    failing = [c for c in checks if not c.ok]
    assert failing == [], f"unexpected failures: {[(c.name, c.detail) for c in failing]}"
    assert all_ok(checks)


def test_check_setup_does_not_raise_on_bad_config(tmp_path):
    bogus = str(tmp_path / "no-such-mm-project")
    cfg = load_config(overrides={"MM_PROJECT_PATH": bogus})
    checks = check_setup(cfg)  # must not raise, unlike require_valid
    assert not all_ok(checks)


def test_check_setup_flags_missing_project_path(tmp_path):
    bogus = str(tmp_path / "no-such-mm-project")
    cfg = load_config(overrides={"MM_PROJECT_PATH": bogus})
    project = next(c for c in check_setup(cfg) if c.name == "MM_PROJECT_PATH")
    assert not project.ok
    assert bogus in project.detail


def test_check_setup_flags_missing_godot_binary(tmp_path):
    bogus_binary = str(tmp_path / "NoSuchGodot.exe")
    cfg = load_config(overrides={"MM_GODOT_BINARY": bogus_binary})
    godot = next(c for c in check_setup(cfg) if c.name == "Godot binary")
    assert not godot.ok
    assert bogus_binary in godot.detail


def test_check_setup_reports_all_problems_not_just_first(tmp_path):
    # require_valid stops at the first problem; the doctor must surface every one.
    cfg = load_config(overrides={
        "MM_PROJECT_PATH": str(tmp_path / "nope"),
        "MM_GODOT_BINARY": str(tmp_path / "NoGodot.exe"),
    })
    failing = {c.name for c in check_setup(cfg) if not c.ok}
    assert "MM_PROJECT_PATH" in failing
    assert "Godot binary" in failing


def test_check_setup_flags_missing_steam_appid(tmp_path):
    # A project dir that has the nodes tree but no steam_appid.txt: the app would
    # self-relaunch and exit on headless render, so the doctor must catch it.
    project = tmp_path / "mm-project"
    (project / "addons" / "material_maker" / "nodes").mkdir(parents=True)
    (project / "material_maker" / "examples").mkdir(parents=True)
    cfg = load_config(overrides={"MM_PROJECT_PATH": str(project)})
    appid = next(c for c in check_setup(cfg) if c.name == "steam_appid.txt")
    assert not appid.ok


def test_main_check_returns_nonzero_on_bad_config(tmp_path, monkeypatch, capsys):
    # `mm-mcp --check` must run and report even when config is broken, which is
    # the exact situation the doctor exists for. It must not crash on import.
    monkeypatch.setenv("MM_DOTENV", str(tmp_path / "none.env"))  # ignore the real .env
    monkeypatch.setenv("MM_PROJECT_PATH", str(tmp_path / "nope"))
    monkeypatch.setenv("MM_GODOT_BINARY", str(tmp_path / "NoGodot.exe"))
    rc = server.main(["--check"])
    assert rc == 1
    out = capsys.readouterr().out
    assert "MM_PROJECT_PATH" in out


def test_main_version_prints_and_returns_zero(capsys):
    rc = server.main(["--version"])
    assert rc == 0
    from mm_mcp import __version__
    assert __version__ in capsys.readouterr().out


def test_main_unknown_flag_returns_usage_code(capsys):
    # An unrecognized flag must not silently fall through and start the server.
    rc = server.main(["--frobnicate"])
    assert rc == 2


def test_check_setup_flags_wrong_steam_appid(tmp_path):
    # A steam_appid.txt with the wrong id passes an isfile check but still breaks
    # headless render, so the doctor must check the contents, not just presence.
    project = tmp_path / "mm-project"
    (project / "addons" / "material_maker" / "nodes").mkdir(parents=True)
    (project / "material_maker" / "examples").mkdir(parents=True)
    (project / "steam_appid.txt").write_text("999")
    cfg = load_config(overrides={"MM_PROJECT_PATH": str(project)})
    appid = next(c for c in check_setup(cfg) if c.name == "steam_appid.txt")
    assert not appid.ok


def test_tool_reraises_on_bad_config_not_cached(monkeypatch, tmp_path):
    # Lazy startup must not memoize a failed init: a tool called under bad config
    # raises, and a second call still raises rather than silently caching state.
    server._reset()
    monkeypatch.setenv("MM_DOTENV", str(tmp_path / "none.env"))
    monkeypatch.setenv("MM_PROJECT_PATH", str(tmp_path / "nope"))
    try:
        with pytest.raises(FileNotFoundError):
            server.list_node_types()
        with pytest.raises(FileNotFoundError):
            server.list_node_types()
    finally:
        server._reset()


def test_doctor_reports_allowed_roots_unset():
    cfg = _load_config(overrides={"MM_ALLOWED_ROOTS": ""})
    names = {c.name: c for c in _check_setup(cfg)}
    assert "MM_ALLOWED_ROOTS" in names
    c = names["MM_ALLOWED_ROOTS"]
    assert c.ok is True
    assert "unrestricted" in c.detail.lower()


def test_doctor_reports_allowed_roots_set():
    cfg = _load_config(overrides={"MM_ALLOWED_ROOTS": r"C:\a"})
    c = {c.name: c for c in _check_setup(cfg)}["MM_ALLOWED_ROOTS"]
    assert c.ok is True
    assert r"C:\a" in c.detail


def test_check_setup_reports_cookbook_count():
    from mm_mcp.cookbook import list_cookbook

    cfg = load_config()
    expected = len(list_cookbook(cfg.cookbook_dir))
    cookbook = next(c for c in check_setup(cfg) if c.name == "cookbook")
    assert cookbook.ok
    assert expected > 0
    assert cookbook.detail.startswith(f"{expected} materials in ")


def test_check_setup_cookbook_missing_is_informational_not_failing(tmp_path):
    cfg = load_config(overrides={"MM_COOKBOOK_DIR": str(tmp_path / "nope")})
    cookbook = next(c for c in check_setup(cfg) if c.name == "cookbook")
    assert cookbook.ok
    assert "not found" in cookbook.detail


def test_check_setup_cookbook_read_error_is_reported_not_raised(monkeypatch):
    import mm_mcp.doctor as doctor_mod

    def boom(_dir):
        raise OSError("simulated unreadable cookbook dir")

    monkeypatch.setattr(doctor_mod, "list_cookbook", boom)
    cookbook = next(c for c in check_setup(load_config()) if c.name == "cookbook")
    assert cookbook.ok
    assert "could not read" in cookbook.detail
    assert "simulated unreadable cookbook dir" in cookbook.detail

import os
import pytest
from mm_mcp.paths import ensure_within_roots, reject_path_fragment, PathNotAllowed


def test_empty_roots_is_passthrough(tmp_path):
    p = str(tmp_path / "anywhere.ptex")
    assert ensure_within_roots(p, []) == os.path.realpath(p)


def test_path_inside_root_is_allowed(tmp_path):
    root = str(tmp_path)
    p = os.path.join(root, "sub", "mat.ptex")
    assert ensure_within_roots(p, [root]) == os.path.realpath(p)


def test_path_outside_root_raises(tmp_path):
    root = tmp_path / "allowed"
    root.mkdir()
    outside = str(tmp_path / "elsewhere" / "mat.ptex")
    with pytest.raises(PathNotAllowed):
        ensure_within_roots(outside, [str(root)])


def test_sibling_prefix_is_not_a_match(tmp_path):
    # '/allowed' must not match '/allowed-evil'
    allowed = tmp_path / "allowed"
    allowed.mkdir()
    evil = tmp_path / "allowed-evil"
    evil.mkdir()
    victim = str(evil / "mat.ptex")
    with pytest.raises(PathNotAllowed):
        ensure_within_roots(victim, [str(allowed)])


def test_symlink_escape_is_blocked(tmp_path):
    root = tmp_path / "allowed"
    root.mkdir()
    secret = tmp_path / "secret"
    secret.mkdir()
    link = root / "escape"
    try:
        os.symlink(str(secret), str(link))
    except (OSError, NotImplementedError):
        pytest.skip("symlink not permitted in this environment")
    with pytest.raises(PathNotAllowed):
        ensure_within_roots(str(link / "x.ptex"), [str(root)])


def test_case_insensitive_match_on_windows(tmp_path):
    if os.name != "nt":
        pytest.skip("Windows case-folding only")
    root = str(tmp_path)
    p = os.path.join(root.upper(), "mat.ptex")
    assert ensure_within_roots(p, [root.lower()])


def test_reject_fragment_accepts_bare_name():
    assert reject_path_fragment("bricks") == "bricks"


def test_reject_fragment_rejects_dotdot():
    with pytest.raises(PathNotAllowed):
        reject_path_fragment("..")


def test_reject_fragment_rejects_forward_slash():
    with pytest.raises(PathNotAllowed):
        reject_path_fragment("../../evil")


def test_reject_fragment_rejects_backslash():
    with pytest.raises(PathNotAllowed):
        reject_path_fragment("..\\..\\evil")

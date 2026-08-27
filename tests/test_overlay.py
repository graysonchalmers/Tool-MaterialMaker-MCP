import os
from mm_mcp.overlay import _hash_dir


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

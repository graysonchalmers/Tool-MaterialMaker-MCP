import hashlib
import json
import os


def _hash_dir(path: str) -> str:
    """Stable content hash of a directory: sensitive to file content and to
    which relative paths exist, not to filesystem walk order or OS path
    separators, so it hashes the same on repeated calls and across the
    fake directories the overlay tests build."""
    h = hashlib.sha256()
    for root, dirs, files in os.walk(path):
        dirs.sort()
        for name in sorted(files):
            full = os.path.join(root, name)
            rel = os.path.relpath(full, path).replace(os.sep, "/")
            h.update(rel.encode("utf-8"))
            with open(full, "rb") as fh:
                h.update(fh.read())
    return h.hexdigest()


def _autoload_line(addon_name: str) -> str:
    return f'{addon_name}="*res://addons/{addon_name}/live_server.gd"'


def _append_autoload(project_godot_path: str, addon_name: str) -> None:
    line = _autoload_line(addon_name)
    with open(project_godot_path, encoding="utf-8") as fh:
        content = fh.read()
    if line in content:
        return

    marker = "[autoload]"
    section_start = content.find(marker)
    if section_start == -1:
        raise ValueError(f"no [autoload] section found in {project_godot_path}")

    # Insert at the end of the [autoload] section (just before the next
    # [section] header, or at end-of-file if [autoload] is the last
    # section) -- never blindly at end-of-file. A real Godot project.godot
    # has many sections after [autoload] (confirmed against the real
    # Material Maker checkout), so an unconditional end-of-file append
    # would silently attach the line to whatever the last section happens
    # to be instead of [autoload], and Godot would never load it.
    search_from = section_start + len(marker)
    next_section = content.find("\n[", search_from)
    insert_at = next_section if next_section != -1 else len(content)

    prefix = content[:insert_at].rstrip("\n")
    suffix = content[insert_at:]
    new_content = prefix + "\n" + line + "\n" + suffix
    with open(project_godot_path, "w", encoding="utf-8") as fh:
        fh.write(new_content)


_MARKER_NAME = ".mm_overlay_marker.json"


def _marker_path(overlay_dir: str) -> str:
    return os.path.join(overlay_dir, _MARKER_NAME)


def _read_marker(overlay_dir: str) -> dict | None:
    path = _marker_path(overlay_dir)
    if not os.path.isfile(path):
        return None
    try:
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)
    except (json.JSONDecodeError, OSError):
        return None


def _write_marker(overlay_dir: str, addon_hash: str, mm_project_path: str) -> None:
    with open(_marker_path(overlay_dir), "w", encoding="utf-8") as fh:
        json.dump({"addon_hash": addon_hash, "mm_project_path": mm_project_path}, fh)


def _is_stale(overlay_dir: str, addon_hash: str, mm_project_path: str) -> bool:
    marker = _read_marker(overlay_dir)
    if marker is None:
        return True
    return (marker.get("addon_hash") != addon_hash
            or marker.get("mm_project_path") != mm_project_path)

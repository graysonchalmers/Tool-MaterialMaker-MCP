"""Build and refresh the live-control overlay: a disposable working copy of a
Material Maker project checkout with the live-control addon layered in and
registered as a Godot autoload.

`overlay_dir` is always a caller-supplied parameter, never derived from
project Config, so this module stays free of any Config/Godot dependency and
is independently unit-testable. A future `live.py` step owns choosing where
the overlay actually lives.

A rebuild wipes `overlay_dir` wholesale (`shutil.rmtree` then
`shutil.copytree`), so nothing that must survive a rebuild -- e.g. a log
file -- should ever be written inside it.
"""

import hashlib
import json
import os
import shutil
import stat


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
    """The project.godot [autoload] line that registers the addon's live_server.gd."""
    return f'{addon_name}="*res://addons/{addon_name}/live_server.gd"'


def _append_autoload(project_godot_path: str, addon_name: str) -> None:
    """Insert the addon's autoload line into project.godot's [autoload] section, idempotently."""
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


def _clear_readonly(path: str) -> None:
    """Clear the read-only attribute on every file under path. A real
    Material Maker checkout is a git clone, and git marks its
    .git/objects/pack/*.idx files read-only; copytree preserves that
    attribute into overlay_dir, and shutil.rmtree can't unlink a read-only
    file on Windows without this first."""
    for root, _dirs, files in os.walk(path):
        for name in files:
            os.chmod(os.path.join(root, name), stat.S_IWRITE)


def _marker_path(overlay_dir: str) -> str:
    """Path to the marker file this module uses to detect a stale overlay."""
    return os.path.join(overlay_dir, _MARKER_NAME)


def _read_marker(overlay_dir: str) -> dict | None:
    """Load the marker file, or None if it's missing, unreadable, or not a JSON object."""
    path = _marker_path(overlay_dir)
    if not os.path.isfile(path):
        return None
    try:
        with open(path, encoding="utf-8") as fh:
            data = json.load(fh)
    except (ValueError, OSError):
        return None
    return data if isinstance(data, dict) else None


def _write_marker(overlay_dir: str, addon_hash: str, mm_project_path: str) -> None:
    """Record the addon hash and checkout path this overlay_dir was built from."""
    with open(_marker_path(overlay_dir), "w", encoding="utf-8") as fh:
        json.dump({"addon_hash": addon_hash, "mm_project_path": mm_project_path}, fh)


def _is_stale(overlay_dir: str, addon_hash: str, mm_project_path: str) -> bool:
    """True if overlay_dir has no marker, or its marker doesn't match the current inputs."""
    marker = _read_marker(overlay_dir)
    if marker is None:
        return True
    return (marker.get("addon_hash") != addon_hash
            or os.path.normcase(marker.get("mm_project_path", "")) != os.path.normcase(mm_project_path))


def ensure_overlay(mm_project_path: str, addon_path: str, overlay_dir: str) -> str:
    """Build or refresh a disposable working copy of a Material Maker project
    checkout with the live-control addon layered in and registered as a
    Godot autoload. Pure filesystem work; never launches Godot.

    Rebuilds when overlay_dir doesn't exist yet, when addon_path's contents
    changed since the last build, or when mm_project_path differs from what
    this overlay_dir was last built from. Otherwise a fast no-op returning
    the existing overlay_dir unchanged.
    """
    if not os.path.isdir(addon_path):
        raise ValueError(f"addon_path is not a directory: {addon_path}")
    if not os.path.isfile(os.path.join(mm_project_path, "project.godot")):
        raise ValueError(f"not a Godot project (no project.godot): {mm_project_path}")

    mm_project_path = os.path.abspath(mm_project_path)
    addon_path = os.path.abspath(addon_path)

    overlay_dir_abs = os.path.abspath(overlay_dir)
    for name, p_abs in (("mm_project_path", mm_project_path), ("addon_path", addon_path)):
        if os.path.normcase(overlay_dir_abs) == os.path.normcase(p_abs) or \
           os.path.normcase(p_abs).startswith(os.path.normcase(overlay_dir_abs) + os.sep):
            raise ValueError(f"overlay_dir would delete {name}: {overlay_dir}")

    addon_hash = _hash_dir(addon_path)

    if os.path.isdir(overlay_dir) and not _is_stale(overlay_dir, addon_hash, mm_project_path):
        return overlay_dir

    if os.path.isdir(overlay_dir):
        _clear_readonly(overlay_dir)
        shutil.rmtree(overlay_dir)

    # The rebuild below is not atomic: the checkout copy, the addon copy, the
    # autoload edit, and the marker write happen in sequence. If any step
    # fails partway (disk full, permission), the leftover directory is a
    # half-built overlay with no marker -- an ambiguous state a later caller
    # could mistake for usable. Remove the partial build on any failure and
    # re-raise, so ensure_overlay leaves either a complete overlay or none.
    # The marker is written last on purpose: it's the commit point that marks
    # the build as finished and matching these inputs.
    try:
        shutil.copytree(mm_project_path, overlay_dir)
        addon_name = os.path.basename(os.path.normpath(addon_path))
        shutil.copytree(addon_path, os.path.join(overlay_dir, "addons", addon_name))
        _append_autoload(os.path.join(overlay_dir, "project.godot"), addon_name)
        _write_marker(overlay_dir, addon_hash, mm_project_path)
    except BaseException:
        # Best-effort cleanup: a cleanup failure (e.g. the same permission
        # problem that broke the copy) must not mask the original exception,
        # so swallow everything cleanup does and let the real error propagate.
        try:
            if os.path.isdir(overlay_dir):
                _clear_readonly(overlay_dir)
                shutil.rmtree(overlay_dir, ignore_errors=True)
        except Exception:
            pass
        raise
    return overlay_dir

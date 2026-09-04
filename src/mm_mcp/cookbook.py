"""Lookup for the tracked cookbook: <cookbook_dir>/<category>/<id>.ptex.

These are graphs this project authored (see quality/cookbook_*.py and
docs/AUTHORING.md), promoted into the repo by quality/promote_cookbook.py.
The server serves them next to Material Maker's own bundled examples so an
assistant can start from the nearest cookbook graph, and a person can open
the same file in Material Maker.
"""
import glob
import os
from dataclasses import dataclass


@dataclass(frozen=True)
class CookbookEntry:
    name: str
    category: str
    path: str


def list_cookbook(cookbook_dir: str) -> list[CookbookEntry]:
    """Every <category>/<id>.ptex under cookbook_dir, sorted by (category, name).
    Empty list when cookbook_dir is unset or not a directory."""
    if not cookbook_dir or not os.path.isdir(cookbook_dir):
        return []
    entries = []
    for path in glob.glob(os.path.join(glob.escape(cookbook_dir), "*", "*.ptex")):
        entries.append(CookbookEntry(
            name=os.path.splitext(os.path.basename(path))[0],
            category=os.path.basename(os.path.dirname(path)),
            path=path,
        ))
    return sorted(entries, key=lambda e: (e.category, e.name))


def find_cookbook(cookbook_dir: str, name: str) -> CookbookEntry | None:
    """The entry whose id is `name`, or None."""
    for entry in list_cookbook(cookbook_dir):
        if entry.name == name:
            return entry
    return None

import hashlib
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

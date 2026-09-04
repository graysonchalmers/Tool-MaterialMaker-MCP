"""Promote locked cookbook graphs into the tracked cookbook/ tree.

    quality/authored/cookbook-<category>/<id>/v1.ptex  ->  cookbook/<category>/<id>.ptex

quality/authored/ is gitignored build output from the cookbook_*.py builders.
cookbook/ is the tracked, shipped copy the MCP server serves through
list_examples / load_example and that a person can open in Material Maker.

Usage (from the repo root):
  .venv\\Scripts\\python.exe quality\\promote_cookbook.py                 # copy every category
  .venv\\Scripts\\python.exe quality\\promote_cookbook.py cookbook-stone  # one label
  .venv\\Scripts\\python.exe quality\\promote_cookbook.py --check         # diff, do not write

--check is the regression baseline: rebuild with the builders, then --check.
Any tracked file that is missing or differs from its authored v1.ptex is
reported and the exit code is 1. Run without --check to accept the new output.
"""
import filecmp
import shutil
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
AUTHORED = _ROOT / "quality" / "authored"
COOKBOOK = _ROOT / "cookbook"
PREFIX = "cookbook-"


def promote(authored_root: Path, cookbook_root: Path, check: bool = False,
            labels: list[str] | None = None) -> list[str]:
    """Copy (or, with check=True, compare) every cookbook-*/<id>/v1.ptex.
    Returns a list of problem strings; empty means clean."""
    problems: list[str] = []
    label_dirs = sorted(d for d in authored_root.glob(PREFIX + "*") if d.is_dir())
    if labels:
        label_dirs = [d for d in label_dirs if d.name in labels]
    for label_dir in label_dirs:
        category = label_dir.name[len(PREFIX):]
        for case_dir in sorted(p for p in label_dir.iterdir() if p.is_dir()):
            src = case_dir / "v1.ptex"
            if not src.is_file():
                problems.append(f"{case_dir}: no v1.ptex to promote")
                continue
            dst = cookbook_root / category / f"{case_dir.name}.ptex"
            if check:
                if not dst.is_file():
                    problems.append(f"{dst}: missing (run promote_cookbook.py to add it)")
                elif not filecmp.cmp(src, dst, shallow=False):
                    problems.append(f"{dst}: differs from {src}")
            else:
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(src, dst)
    return problems


def main(argv: list[str]) -> int:
    check = "--check" in argv
    labels = [a for a in argv if a != "--check"] or None
    problems = promote(AUTHORED, COOKBOOK, check=check, labels=labels)
    for p in problems:
        print(p)
    if problems:
        print(f"{len(problems)} problem(s)")
        return 1
    print("cookbook/ is " + ("in sync with quality/authored/" if check else "updated"))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

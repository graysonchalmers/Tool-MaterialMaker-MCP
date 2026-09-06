"""Render the TRACKED cookbook graphs (cookbook/<category>/<id>.ptex), one
Godot at a time, into an output directory; optionally compare the result
against a baseline directory with the same layout using
render_compare.renders_match. This is the proof that a builder change (a
rename pass, a regroup) moved no pixels.

  python -m quality.render_tracked --out output/naming-baseline
  python -m quality.render_tracked --out output/naming-after --category wood --compare output/naming-baseline

Layout: <out>/<category>/<id>_albedo.png, _normal.png, _orm.png, plus
whatever other <id>_*.png maps a given material's graph happens to emit
(e.g. _heightmap.png). compare_dirs compares every <id>_*.png the baseline
holds, not a fixed triple, since coverage varies per material.
Run as a script file, never from `python -c` (the Godot launcher then never exits).
Paths are resolved to absolute before Godot sees them; Godot's cwd is the
Material Maker checkout, so a relative outdir is never found and the render
idles to its timeout.
"""
import json
import sys
from pathlib import Path

from mm_mcp.catalog_builder import build_catalog
from mm_mcp.config import load_config
from mm_mcp.cookbook import list_cookbook
from mm_mcp.render import render
from mm_mcp.validator import validate_graph
from quality.render_compare import grid_mean_abs_diff, renders_match

_ROOT = Path(__file__).resolve().parent.parent
COOKBOOK = _ROOT / "cookbook"
MAPS = ("albedo", "normal", "orm")


def render_entries(entries, out: Path, size: int) -> list[str]:
    cfg = load_config()
    catalog = build_catalog(cfg.nodes_dir)
    problems = []
    for e in entries:
        ptex = json.loads(Path(e.path).read_text(encoding="utf-8"))
        errors = [p for p in validate_graph(ptex, catalog) if p["severity"] == "error"]
        if errors:
            problems.append(f"{e.name}: validation errors {errors}")
            continue
        outdir = out / e.category
        outdir.mkdir(parents=True, exist_ok=True)
        result = render(ptex, size=size, outdir=str(outdir), basename=e.name, cfg=cfg)
        if not result.ok:
            problems.append(f"{e.name}: render failed: {result.error}")
        else:
            print(f"  rendered {e.category}/{e.name}")
    return problems


def compare_dirs(baseline: Path, current: Path, entries) -> list[str]:
    problems = []
    for e in entries:
        base_files = sorted((baseline / e.category).glob(f"{e.name}_*.png"))
        if not base_files:
            problems.append(f"{e.category}/{e.name}: no baseline renders")
            continue
        seen_names = set()
        for a in base_files:
            seen_names.add(a.name)
            b = current / e.category / a.name
            if not b.is_file():
                problems.append(f"{e.category}/{a.name}: missing in current")
                continue
            if not renders_match(str(a), str(b)):
                problems.append(f"{e.category}/{a.name}: differs, mean abs diff {grid_mean_abs_diff(str(a), str(b)):.2f}")
        cur_files = sorted((current / e.category).glob(f"{e.name}_*.png"))
        for b in cur_files:
            if b.name not in seen_names:
                problems.append(f"{e.category}/{b.name}: present in current only")
    return problems


def _arg(argv, flag, default=None):
    return argv[argv.index(flag) + 1] if flag in argv else default


def main(argv: list[str]) -> int:
    out = _arg(argv, "--out")
    if not out:
        print(__doc__)
        return 2
    out = Path(out).resolve()
    category = _arg(argv, "--category")
    size = int(_arg(argv, "--size", "512"))
    baseline = _arg(argv, "--compare")
    if baseline:
        baseline = Path(baseline).resolve()
    entries = [e for e in list_cookbook(str(COOKBOOK)) if category is None or e.category == category]
    if not entries:
        print(f"no cookbook entries for category {category!r}")
        return 2
    problems = render_entries(entries, out, size)
    if baseline:
        problems += compare_dirs(Path(baseline), out, entries)
    for p in problems:
        print(p)
    print(f"{len(entries)} graph(s), {len(problems)} problem(s)")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

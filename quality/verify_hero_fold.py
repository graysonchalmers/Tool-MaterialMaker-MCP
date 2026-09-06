"""Render regression check for folding an examples/ hero into the cookbook.

    python quality/verify_hero_fold.py <label> <id>
    e.g. python quality/verify_hero_fold.py cookbook-stone s02_gray_granite

Renders the UNGROUPED original (examples/<id>/<id>.ptex) and the GROUPED
cookbook candidate (quality/authored/<label>/<id>/v1.ptex), one Godot at a
time, into quality/cookbook/<label>/_foldcheck/<id>/{before,after}/, then
compares the albedo maps with render_compare.renders_match. Grouping into
subgraphs is organizational, so the expected diff is ~0.0 (tolerance 3.0).
Exit 0 on match, 1 on mismatch or render failure.

Run from the repo root as a script FILE, never via `python -c` (Godot's
console launcher does not exit cleanly from -c; see quality/render_one.py).
"""
import json
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT / "src"))
sys.path.insert(0, str(_ROOT / "quality"))

from mm_mcp.config import load_config
from mm_mcp.render import render
from render_compare import grid_mean_abs_diff, renders_match


def _render_to(ptex_path: Path, outdir: Path, basename: str, cfg) -> Path:
    with open(ptex_path, encoding="utf-8") as fh:
        ptex = json.load(fh)
    outdir.mkdir(parents=True, exist_ok=True)
    result = render(ptex, size=512, outdir=str(outdir), basename=basename, cfg=cfg)
    if not result.ok:
        print(f"RENDER FAILED for {ptex_path}: {result.error}\n{result.log_tail}")
        sys.exit(1)
    albedo = outdir / f"{basename}_albedo.png"
    if not albedo.is_file():
        print(f"no albedo produced at {albedo}")
        sys.exit(1)
    return albedo


def main() -> int:
    if len(sys.argv) != 3:
        print(__doc__)
        return 2
    label, case_id = sys.argv[1], sys.argv[2]
    before_src = _ROOT / "examples" / case_id / f"{case_id}.ptex"
    after_src = _ROOT / "quality" / "authored" / label / case_id / "v1.ptex"
    for p in (before_src, after_src):
        if not p.is_file():
            print(f"missing input: {p}")
            return 1
    cfg = load_config()
    check_root = _ROOT / "quality" / "cookbook" / label / "_foldcheck" / case_id
    before = _render_to(before_src, check_root / "before", case_id, cfg)
    after = _render_to(after_src, check_root / "after", case_id, cfg)
    diff = grid_mean_abs_diff(str(before), str(after))
    ok = renders_match(str(before), str(after))
    print(f"{case_id}: grid_mean_abs_diff={diff:.3f} -> {'MATCH' if ok else 'MISMATCH'}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())

"""Render ONE authored cookbook case, vs render_cookbook.py which renders every
case under a label. Keeps a single Godot render to one material during
iteration (renders must run sequentially, one Godot at a time).

Usage:
  python quality/render_one.py <label> <case> [size]
  e.g. python quality/render_one.py cookbook-stone s07_cobblestone

Run as a script FILE, never `python -c` -- launching Godot's console binary
from `python -c` leaves the launcher process not exiting (a console/handle
quirk), which reads as a bogus render timeout.
"""
import json
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT / "src"))

from mm_mcp.config import load_config
from mm_mcp.catalog_builder import build_catalog
from mm_mcp.validator import validate_graph
from mm_mcp.render import render

_QUALITY = _ROOT / "quality"


def main() -> int:
    if len(sys.argv) < 3:
        print("usage: python quality/render_one.py <label> <case> [size]")
        return 2
    label, case = sys.argv[1], sys.argv[2]
    size = int(sys.argv[3]) if len(sys.argv) > 3 else 512

    variant = _QUALITY / "authored" / label / case / "v1.ptex"
    outdir = _QUALITY / "cookbook" / label / case
    outdir.mkdir(parents=True, exist_ok=True)

    cfg = load_config()
    ptex = json.loads(variant.read_text(encoding="utf-8"))
    problems = validate_graph(ptex, build_catalog(cfg.nodes_dir))
    errors = [p for p in problems if p["severity"] == "error"]
    if errors:
        for e in errors:
            print(f"  ERROR: {e['message']}")
        return 1

    result = render(ptex, size=size, outdir=str(outdir), basename=case, cfg=cfg)
    if result.ok:
        for img in result.images:
            print(f"  ok: {Path(img).name}")
        return 0
    print(f"  RENDER FAILED: {result.error}")
    return 1


if __name__ == "__main__":
    sys.exit(main())

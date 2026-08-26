"""Validate + render quality/authored/<label>/<case>/vN.ptex graphs for
inspection, without touching the frozen test_set.json / runs/ / scorecards/
machinery (see quality/cookbook_fabrics.py). Outputs land under
quality/cookbook/<label>/<case>/.

Usage:
  python quality/render_cookbook.py cookbook-fabrics
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
    label = sys.argv[1] if len(sys.argv) > 1 else "cookbook-fabrics"
    src_dir = _QUALITY / "authored" / label
    out_root = _QUALITY / "cookbook" / label

    cfg = load_config()
    catalog = build_catalog(cfg.nodes_dir)

    for case_dir in sorted(src_dir.iterdir()):
        if not case_dir.is_dir():
            continue
        for variant_path in sorted(case_dir.glob("v*.ptex")):
            with open(variant_path, encoding="utf-8") as fh:
                ptex = json.load(fh)
            problems = validate_graph(ptex, catalog)
            errors = [p for p in problems if p["severity"] == "error"]
            outdir = out_root / case_dir.name
            outdir.mkdir(parents=True, exist_ok=True)
            print(f"== {case_dir.name}/{variant_path.name} ==")
            if errors:
                for e in errors:
                    print(f"  ERROR: {e['message']}")
                continue
            for w in problems:
                if w["severity"] == "warning":
                    print(f"  warn: {w['message']}")
            result = render(ptex, size=512, outdir=str(outdir),
                            basename=case_dir.name, cfg=cfg)
            if result.ok:
                for img in result.images:
                    print(f"  ok: {Path(img).name}")
            else:
                print(f"  RENDER FAILED: {result.error}")
                print(f"  log tail: {result.log_tail}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

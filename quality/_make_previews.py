"""One-off: downscale cookbook-<category> albedo renders into docs/images/
preview thumbnails, same technique used for examples/images/ (see
HANDOFF.md -- Pillow is a dev-only tool for this, not a project dependency).

Usage: .venv\\Scripts\\python.exe quality\\_make_previews.py [label]
       (label defaults to cookbook-fabrics; pass e.g. cookbook-organics)
"""
import sys
from pathlib import Path
from PIL import Image

_ROOT = Path(__file__).resolve().parent.parent
SIZE = 512


def main() -> int:
    label = sys.argv[1] if len(sys.argv) > 1 else "cookbook-fabrics"
    src = _ROOT / "quality" / "cookbook" / label
    out_dir = _ROOT / "docs" / "images" / label
    out_dir.mkdir(parents=True, exist_ok=True)
    for case_dir in sorted(src.iterdir()):
        if not case_dir.is_dir():
            continue
        albedo = next(case_dir.glob("*_albedo.png"), None)
        if not albedo:
            print(f"skip {case_dir.name}: no albedo")
            continue
        im = Image.open(albedo).convert("RGB")
        im = im.resize((SIZE, SIZE), Image.LANCZOS)
        out_file = out_dir / f"{case_dir.name}.png"
        im.save(out_file, optimize=True)
        print(f"{case_dir.name}: {out_file}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

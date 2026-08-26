"""One-off: downscale cookbook-fabric albedo renders into docs/images/ preview
thumbnails, same technique used for examples/images/ (see HANDOFF.md -- Pillow
is a dev-only tool for this, not a project dependency).

Usage: .venv\\Scripts\\python.exe quality\\_make_previews.py
"""
import sys
from pathlib import Path
from PIL import Image

_ROOT = Path(__file__).resolve().parent.parent
_SRC = _ROOT / "quality" / "cookbook" / "cookbook-fabrics"
_OUT = _ROOT / "docs" / "images" / "cookbook-fabrics"
_OUT.mkdir(parents=True, exist_ok=True)

SIZE = 512


def main() -> int:
    for case_dir in sorted(_SRC.iterdir()):
        if not case_dir.is_dir():
            continue
        albedo = next(case_dir.glob("*_albedo.png"), None)
        if not albedo:
            print(f"skip {case_dir.name}: no albedo")
            continue
        im = Image.open(albedo).convert("RGB")
        im = im.resize((SIZE, SIZE), Image.LANCZOS)
        out = _OUT / f"{case_dir.name}.png"
        im.save(out, optimize=True)
        print(f"{case_dir.name}: {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

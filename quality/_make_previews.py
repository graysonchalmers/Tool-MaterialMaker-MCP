"""One-off: downscale cookbook-<category> albedo renders into docs/images/
preview thumbnails, same technique used for examples/images/ (see
HANDOFF.md -- Pillow is a dev-only tool for this, not a project dependency).

Usage: .venv\\Scripts\\python.exe -m quality._make_previews [label]
       (label defaults to cookbook-fabrics; pass e.g. cookbook-organics)
"""
import sys
from pathlib import Path
from PIL import Image

_ROOT = Path(__file__).resolve().parent.parent
SIZE = 512


def _checker(size: int, cell: int = 16) -> Image.Image:
    bg = Image.new("RGBA", (size, size), (245, 245, 245, 255))
    dark = Image.new("RGBA", (cell, cell), (215, 215, 215, 255))
    for y in range(0, size, cell):
        for x in range(0, size, cell):
            if (x // cell + y // cell) % 2:
                bg.paste(dark, (x, y))
    return bg


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
        im = Image.open(albedo)
        im = im.resize((SIZE, SIZE), Image.LANCZOS)
        if im.mode == "RGBA":
            # opacity_tex rides in albedo alpha: show the cutouts over a
            # checker instead of letting convert("RGB") hide them.
            im = Image.alpha_composite(_checker(SIZE), im)
        im = im.convert("RGB")
        out_file = out_dir / f"{case_dir.name}.png"
        im.save(out_file, optimize=True)
        print(f"{case_dir.name}: {out_file}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

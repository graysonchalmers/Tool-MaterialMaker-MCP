"""Tile cookbook preview thumbnails (docs/images/cookbook-<label>/*.png) into
one labeled contact sheet, for a single glance across a whole pass instead of
individual file-by-file review. Reuses the already-downscaled previews from
_make_previews.py -- run that first for any label you want included.

Usage:
  .venv\\Scripts\\python.exe quality\\contact_sheet.py cookbook-wood cookbook-stone
  .venv\\Scripts\\python.exe quality\\contact_sheet.py          (all cookbook-* dirs)

Writes docs/images/contact-sheet-<labels>.png. Not tracked in git by default
(regenerate on demand); the per-category preview PNGs it draws from stay the
tracked source of truth.
"""
import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

_ROOT = Path(__file__).resolve().parent.parent
_IMAGES = _ROOT / "docs" / "images"
TILE = 420
LABEL_H = 26
COLS = 3


def main() -> int:
    labels = sys.argv[1:] or sorted(
        p.name for p in _IMAGES.glob("cookbook-*") if p.is_dir())
    if not labels:
        print("no cookbook-* preview dirs found under docs/images/")
        return 1

    tiles = []  # (label_text, Image)
    for label in labels:
        src = _IMAGES / label
        if not src.is_dir():
            print(f"skip {label}: no such dir under docs/images/")
            continue
        for png in sorted(src.glob("*.png")):
            im = Image.open(png).convert("RGB").resize((TILE, TILE), Image.LANCZOS)
            tiles.append((f"{label.replace('cookbook-', '')}/{png.stem}", im))

    if not tiles:
        print("no preview images found for the given labels")
        return 1

    cols = COLS
    rows = (len(tiles) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * TILE, rows * (TILE + LABEL_H)), (24, 24, 24))
    draw = ImageDraw.Draw(sheet)
    font = ImageFont.load_default()
    for i, (name, im) in enumerate(tiles):
        col, row = i % cols, i // cols
        x, y = col * TILE, row * (TILE + LABEL_H)
        sheet.paste(im, (x, y))
        draw.text((x + 6, y + TILE + 5), name, fill=(235, 235, 235), font=font)

    out_name = "contact-sheet-" + "-".join(l.replace("cookbook-", "") for l in labels) + ".png"
    out_path = _IMAGES / out_name
    sheet.save(out_path, optimize=True)
    print(f"wrote {out_path} ({len(tiles)} tiles, {cols}x{rows})")
    return 0


if __name__ == "__main__":
    sys.exit(main())

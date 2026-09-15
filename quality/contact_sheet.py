"""Tile preview thumbnails into one labeled contact sheet, for a single
glance across a whole pass instead of individual file-by-file review.

Two modes:

- Cookbook mode (default): tiles docs/images/cookbook-<label>/*.png previews
  (reuses the already-downscaled previews from _make_previews.py -- run that
  first for any label you want included).

    .venv\\Scripts\\python.exe -m quality.contact_sheet cookbook-wood cookbook-stone
    .venv\\Scripts\\python.exe -m quality.contact_sheet          (all cookbook-* dirs)

  Writes docs/images/contact-sheet-<labels>.png. Not tracked in git by
  default (regenerate on demand); the per-category preview PNGs it draws
  from stay the tracked source of truth.

- Swatch mode: tiles the debug-swatches gallery (quality/debug_swatches.py)
  into the tracked docs/images/core-toolbox/swatches.png.

    .venv\\Scripts\\python.exe -m quality.contact_sheet --swatches
"""
import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

from quality import debug_swatches as _debug_swatches

_ROOT = Path(__file__).resolve().parent.parent
_IMAGES = _ROOT / "docs" / "images"
TILE = 420
LABEL_H = 26
COLS = 3

_SWATCH_SRC = _ROOT / "quality" / "cookbook" / "debug-swatches"
_SWATCH_OUT = _IMAGES / "core-toolbox" / "swatches.png"


def _save_sheet(tiles, cols: int, out_path: Path) -> int:
    """Lay out (label, Image) tiles into one sheet and save as an 8-bit
    palette PNG. Returns the row count. Shared by cookbook mode and swatch
    mode so both sheets are built and saved identically."""
    rows = (len(tiles) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * TILE, rows * (TILE + LABEL_H)), (24, 24, 24))
    draw = ImageDraw.Draw(sheet)
    font = ImageFont.load_default()
    for i, (name, im) in enumerate(tiles):
        col, row = i % cols, i // cols
        x, y = col * TILE, row * (TILE + LABEL_H)
        sheet.paste(im, (x, y))
        draw.text((x + 6, y + TILE + 5), name, fill=(235, 235, 235), font=font)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    # 8-bit palette: RGB saves of sheets like this ran 7 MB per regeneration
    # (2026-09-05); these are review/reference aids, not source art.
    sheet.convert("P", palette=Image.ADAPTIVE, colors=256).save(out_path, optimize=True)
    return rows


def build_swatch_sheet(out_path: Path = _SWATCH_OUT, cols: int = 4) -> int:
    """Build the Core-toolbox swatch contact sheet from the exact
    debug_swatches.BUILDERS key set (19 swatches as of 2026-09-13) -- NOT by
    globbing quality/cookbook/debug-swatches/, which also holds
    normal_relief_check, an orphan probe not in BUILDERS that would silently
    inflate the sheet to 20 tiles and desync it from BUILDERS/the README count.

    Each tile is sourced from whichever map that swatch's own PIXEL_CHECKS
    entry judges, not always "albedo": the relief_* family and normal_map are
    judged (and rendered meaningfully) on "normal" -- normal_map in
    particular has NO albedo output at all, since its swatch graph never
    wires anything into the Material's albedo port, only its normal port.
    Falls back to "albedo" for slope_blur, which has no PIXEL_CHECKS entry
    (it renders as a flat black image by design -- a buffer/compute-shader
    node that cannot render headless; see docs/DEBUG_SWATCHES.md). Raises
    FileNotFoundError (rather than silently skipping) if any resolved map is
    missing, so a partial render never produces a sheet with the wrong tile
    count.
    """
    keys = sorted(_debug_swatches.BUILDERS)
    tiles = []
    missing = []
    for key in keys:
        map_name, _check = _debug_swatches.PIXEL_CHECKS.get(key, ("albedo", None))
        src = _SWATCH_SRC / key / f"{key}_{map_name}.png"
        if not src.exists():
            missing.append(str(src))
            continue
        im = Image.open(src).convert("RGB").resize((TILE, TILE), Image.LANCZOS)
        tiles.append((key, im))
    if missing:
        raise FileNotFoundError(
            f"swatch sheet: missing {len(missing)} of {len(keys)} render(s), "
            f"re-render before building the sheet: {missing}")
    rows = _save_sheet(tiles, cols, out_path)
    print(f"wrote {out_path} ({len(tiles)} tiles, {cols}x{rows})")
    return len(tiles)


def _build_cookbook_sheet(labels) -> int:
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

    out_name = "contact-sheet-" + "-".join(l.replace("cookbook-", "") for l in labels) + ".png"
    out_path = _IMAGES / out_name
    rows = _save_sheet(tiles, COLS, out_path)
    print(f"wrote {out_path} ({len(tiles)} tiles, {COLS}x{rows})")
    return 0


def main() -> int:
    argv = sys.argv[1:]
    if argv and argv[0] == "--swatches":
        build_swatch_sheet()
        return 0

    labels = argv or sorted(
        p.name for p in _IMAGES.glob("cookbook-*") if p.is_dir())
    if not labels:
        print("no cookbook-* preview dirs found under docs/images/")
        return 1
    return _build_cookbook_sheet(labels)


if __name__ == "__main__":
    sys.exit(main())

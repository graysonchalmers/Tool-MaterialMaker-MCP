"""Isolated verification for Task B: overlay albedo cell edges on the normal
map to confirm the fixed granite relief now coincides with the fleck cells.

Run: python scratchpad/overlay_granite_align.py
Reads the fresh flat maps rendered by:
  python -m quality.render_one cookbook-stone s02_gray_granite
"""
from pathlib import Path

from PIL import Image, ImageFilter, ImageChops

ROOT = Path(__file__).resolve().parent.parent
OUTDIR = ROOT / "quality" / "cookbook" / "cookbook-stone" / "s02_gray_granite"
DEST = ROOT / ".superpowers" / "sdd" / "2026-09-14-showcase-lighting-refresh" / "task-B-overlay.png"

albedo = Image.open(OUTDIR / "s02_gray_granite_albedo.png").convert("L")
normal = Image.open(OUTDIR / "s02_gray_granite_normal.png").convert("L")

# Edge-detect both flat maps (find_edges highlights cell boundaries in the
# albedo and relief boundaries in the normal's luminance channel).
albedo_edges = albedo.filter(ImageFilter.FIND_EDGES)
normal_edges = normal.filter(ImageFilter.FIND_EDGES)

# Boost contrast so faint edges are visible.
def boost(im, factor=4):
    return im.point(lambda p: min(255, int(p * factor)))

albedo_edges = boost(albedo_edges)
normal_edges = boost(normal_edges)

w, h = albedo.size
composite = Image.merge("RGB", (
    albedo_edges,                      # R: albedo cell edges
    normal_edges,                      # G: normal relief edges
    Image.new("L", (w, h), 0),         # B: unused
))
# Where R and G channels agree (both bright) the pixel reads yellow --
# that is the alignment signal: albedo cell boundaries coinciding with
# normal relief boundaries.
DEST.parent.mkdir(parents=True, exist_ok=True)
composite.save(DEST)

# Cheap quantitative check: correlate the two edge fields.
import numpy as np
a = np.asarray(albedo_edges, dtype=float).flatten()
n = np.asarray(normal_edges, dtype=float).flatten()
if a.std() > 0 and n.std() > 0:
    r = float(np.corrcoef(a, n)[0, 1])
else:
    r = float("nan")

print(f"saved overlay: {DEST}")
print(f"albedo-edge vs normal-edge Pearson r = {r:.3f}")

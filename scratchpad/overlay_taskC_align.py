"""Task C isolated verification: confirm each fixed material's normal relief
now co-locates with its albedo detail.

- s06/s04/t03 (hard voronoi cell boundaries on both maps): albedo-edge vs
  normal-edge overlay (R=albedo edges, G=normal edges, yellow=aligned) plus a
  Pearson r of the two edge fields -- the same technique as the granite fix.
- pm04 (smooth gradient fields: both albedo and normal vary smoothly over the
  same warped dimple height, so edge magnitude is low): a gradient-DIRECTION
  check instead. A lit height field has albedo luminance rising with height,
  and the tangent-space normal encodes -dh/dx in (R-128), -dh/dy in (G-128).
  So the Sobel gradient of albedo luminance should correlate with -(nx,ny).
  Strong |r| there is the real alignment signal and works on smooth fields.

Run after: python -m quality.render_one <label> <case>  (all four).
"""
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter

ROOT = Path(__file__).resolve().parent.parent
DEST = ROOT / ".superpowers" / "sdd" / "2026-09-14-showcase-lighting-refresh"
DEST.mkdir(parents=True, exist_ok=True)

CELL = [
    ("cookbook-stone", "s06_river_pebbles"),
    ("cookbook-stone", "s04_scattered_river_stones"),
    ("cookbook-terrain", "t03_gravel"),
]
PM04 = ("cookbook-painted-metal", "pm04_hammertone")


def _dir(label, case):
    return ROOT / "quality" / "cookbook" / label / case


def boost(im, factor=4):
    return im.point(lambda p: min(255, int(p * factor)))


def edge_overlay(label, case):
    d = _dir(label, case)
    albedo = Image.open(d / f"{case}_albedo.png").convert("L")
    normal = Image.open(d / f"{case}_normal.png").convert("L")
    ae = boost(albedo.filter(ImageFilter.FIND_EDGES))
    ne = boost(normal.filter(ImageFilter.FIND_EDGES))
    w, h = albedo.size
    comp = Image.merge("RGB", (ae, ne, Image.new("L", (w, h), 0)))
    out = DEST / f"task-C-{case}-overlay.png"
    comp.save(out)
    a = np.asarray(ae, float).flatten()
    n = np.asarray(ne, float).flatten()
    r = float(np.corrcoef(a, n)[0, 1]) if a.std() > 0 and n.std() > 0 else float("nan")
    return out, r


def _sobel(im):
    a = np.asarray(im, float)
    kx = np.array([[-1, 0, 1], [-2, 0, 2], [-1, 0, 1]], float)
    ky = kx.T
    from numpy.lib.stride_tricks import sliding_window_view
    pad = np.pad(a, 1, mode="edge")
    win = sliding_window_view(pad, (3, 3))
    gx = (win * kx).sum(axis=(-1, -2))
    gy = (win * ky).sum(axis=(-1, -2))
    return gx, gy


def gradient_overlay(label, case):
    d = _dir(label, case)
    albedo = Image.open(d / f"{case}_albedo.png").convert("L")
    normal = Image.open(d / f"{case}_normal.png").convert("RGB")
    agx, agy = _sobel(albedo)
    nrm = np.asarray(normal, float)
    nx = nrm[..., 0] - 128.0   # ~ -dh/dx
    ny = nrm[..., 1] - 128.0   # ~ -dh/dy
    # Albedo brighter with height -> grad(L) ~ +grad(h) ~ -(nx,ny).
    ax = agx.flatten(); ay = agy.flatten()
    def corr(u, v):
        return float(np.corrcoef(u, v)[0, 1]) if u.std() > 0 and v.std() > 0 else float("nan")
    rx = corr(ax, -nx.flatten())
    ry = corr(ay, -ny.flatten())
    # Visualization: albedo-gradient magnitude (R) vs normal-gradient magnitude
    # from (nx,ny) (G); yellow where both have strong slope in the same place.
    amag = np.hypot(agx, agy)
    nmag = np.hypot(nx, ny)
    def norm8(m):
        m = m - m.min()
        return (255 * m / (m.max() + 1e-9)).astype("uint8")
    comp = Image.merge("RGB", (
        Image.fromarray(norm8(amag)),
        Image.fromarray(norm8(nmag)),
        Image.new("L", albedo.size, 0),
    ))
    out = DEST / f"task-C-{case}-overlay.png"
    comp.save(out)
    return out, rx, ry


print("== cell materials (edge overlay + Pearson r of edge fields) ==")
for label, case in CELL:
    out, r = edge_overlay(label, case)
    print(f"{case}: r={r:.3f}  -> {out}")

print("== pm04 (gradient-direction correlation, smooth field) ==")
out, rx, ry = gradient_overlay(*PM04)
print(f"{PM04[1]}: grad_x r={rx:.3f}, grad_y r={ry:.3f}  -> {out}")

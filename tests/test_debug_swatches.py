"""Phase-2 automated regression checks for the debug diagnostic swatches
(quality/debug_swatches.py). The integration tests render each swatch LIVE at a
small size and assert its known-answer on the fresh pixels, so a wiring/render
regression fails without a human eyeballing the gallery. The fast tests cover
the vendored PNG reader (quality/pngread.py) in isolation.

See docs/DEBUG_SWATCHES.md for the swatch legend the checks encode.
"""
import json
import os
import struct
import sys
import zlib

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "quality"))
from pngread import read_png, Sampler        # noqa: E402
import debug_swatches as D                    # noqa: E402
from mm_mcp.config import load_config          # noqa: E402
from mm_mcp.render import render               # noqa: E402

cfg = load_config()
_AUTHORED = os.path.join(os.path.dirname(__file__), "..", "quality",
                        "authored", "debug-swatches")


# ---- fast: the vendored PNG reader ----------------------------------------

def _chunk(tag, data):
    return (struct.pack(">I", len(data)) + tag + data +
            struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF))


def _png(width, height, colortype, raw_scanlines):
    ihdr = struct.pack(">IIBBBBB", width, height, 8, colortype, 0, 0, 0)
    return (b"\x89PNG\r\n\x1a\n" + _chunk(b"IHDR", ihdr) +
            _chunk(b"IDAT", zlib.compress(raw_scanlines)) + _chunk(b"IEND", b""))


def test_pngread_decodes_a_known_rgba_image(tmp_path):
    # two rows, filter 0 (None) each: red/green over blue/yellow
    raw = (b"\x00" + bytes([255, 0, 0, 255, 0, 255, 0, 255]) +
           b"\x00" + bytes([0, 0, 255, 255, 255, 255, 0, 255]))
    p = tmp_path / "t.png"
    p.write_bytes(_png(2, 2, 6, raw))
    w, h, ch, buf = read_png(str(p))
    assert (w, h, ch) == (2, 2, 4)
    s = Sampler(w, h, ch, buf)
    assert s.at(0.0, 0.0) == (255, 0, 0)
    assert s.at(0.99, 0.0) == (0, 255, 0)
    assert s.at(0.0, 0.99) == (0, 0, 255)
    assert s.at(0.99, 0.99) == (255, 255, 0)


def test_pngread_unfilters_the_sub_filter(tmp_path):
    # one RGB row, Sub filter (type 1): stored bytes are per-channel deltas, so
    # (10,20,30) then +(5,5,5) must unfilter to (10,20,30),(15,25,35)
    raw = b"\x01" + bytes([10, 20, 30, 5, 5, 5])
    p = tmp_path / "s.png"
    p.write_bytes(_png(2, 1, 2, raw))
    w, h, ch, buf = read_png(str(p))
    assert (w, h, ch) == (2, 1, 3)
    assert list(buf) == [10, 20, 30, 15, 25, 35]


def test_pngread_rejects_unsupported_png(tmp_path):
    # colortype 3 (palette) is not supported and must raise, not misdecode
    p = tmp_path / "pal.png"
    p.write_bytes(_png(1, 1, 3, b"\x00\x00"))
    with pytest.raises(ValueError):
        read_png(str(p))


# ---- integration: render each swatch and check its known-answer -----------

def _render_swatch(name, tmp_path):
    D.BUILDERS[name]()
    graph = json.load(open(os.path.join(_AUTHORED, name, "v1.ptex"), encoding="utf-8"))
    result = render(graph, size=128, outdir=str(tmp_path), basename=name, cfg=cfg)
    assert result.ok, result.error or result.log_tail
    return {os.path.basename(i).split(name + "_", 1)[1].rsplit(".", 1)[0]: i
            for i in result.images}


@pytest.mark.integration
@pytest.mark.parametrize("name", list(D.PIXEL_CHECKS))
def test_debug_swatch_matches_known_answer(name, tmp_path):
    map_kind, check = D.PIXEL_CHECKS[name]
    imgs = _render_swatch(name, tmp_path)
    assert map_kind in imgs, f"{name} produced no {map_kind} map: {sorted(imgs)}"
    fails = check(Sampler.load(imgs[map_kind]))
    assert not fails, f"{name}: " + " | ".join(fails)


@pytest.mark.integration
def test_voronoi_port0_and_port1_fields_differ(tmp_path):
    """Wrong-port smoke check: the two distance fields must not be near-identical
    (they are visibly different metrics -- port 0 has bright seams, port 1 dark)."""
    a = _render_swatch("voronoi_port0_field", tmp_path)
    b = _render_swatch("voronoi_port1_field", tmp_path)
    ga = Sampler.load(a["albedo"]).grid(20)
    gb = Sampler.load(b["albedo"]).grid(20)
    avg_diff = sum(abs(x[0] - y[0]) for x, y in zip(ga, gb)) / len(ga)
    assert avg_diff > 30, f"port-0 and port-1 fields too similar, avg|diff|={avg_diff:.0f}"

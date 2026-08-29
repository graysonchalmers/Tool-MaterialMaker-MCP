"""Tiny pure-stdlib PNG reader for the debug-swatch pixel assertions
(quality/debug_swatches.py phase 2). Zero dependencies -- the project keeps
Pillow out of pyproject on purpose, and the swatch renders are all plain 8-bit
RGB/RGBA, so a ~60-line decoder covers everything we need.

Handles: 8-bit, color type 2 (RGB) and 6 (RGBA), all five scanline filters
(None/Sub/Up/Average/Paeth). NOT a general PNG library -- interlaced, palette,
16-bit, and grayscale-typed PNGs raise ValueError (Godot never emits them here).
"""
import struct
import zlib

_SIG = b"\x89PNG\r\n\x1a\n"


def _paeth(a, b, c):
    p = a + b - c
    pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
    if pa <= pb and pa <= pc:
        return a
    return b if pb <= pc else c


def read_png(path):
    """Return (width, height, channels, buf) where buf is a bytes of length
    width*height*channels, row-major, 8-bit per channel."""
    with open(path, "rb") as fh:
        data = fh.read()
    if data[:8] != _SIG:
        raise ValueError("not a PNG")
    pos = 8
    width = height = bitdepth = colortype = None
    idat = bytearray()
    while pos + 8 <= len(data):
        (length,) = struct.unpack(">I", data[pos:pos + 4])
        ctype = data[pos + 4:pos + 8]
        chunk = data[pos + 8:pos + 8 + length]
        pos += 12 + length  # 4 len + 4 type + data + 4 CRC
        if ctype == b"IHDR":
            width, height, bitdepth, colortype = struct.unpack(">IIBB", chunk[:10])
            interlace = chunk[12]
            if interlace != 0:
                raise ValueError("interlaced PNG unsupported")
        elif ctype == b"IDAT":
            idat += chunk
        elif ctype == b"IEND":
            break
    if bitdepth != 8 or colortype not in (2, 6):
        raise ValueError(f"unsupported PNG (bitdepth={bitdepth}, colortype={colortype})")
    ch = 3 if colortype == 2 else 4
    raw = zlib.decompress(bytes(idat))
    stride = width * ch
    out = bytearray(height * stride)
    prev = bytearray(stride)
    ri = 0
    for y in range(height):
        ft = raw[ri]
        ri += 1
        line = bytearray(raw[ri:ri + stride])
        ri += stride
        if ft == 1:  # Sub
            for x in range(ch, stride):
                line[x] = (line[x] + line[x - ch]) & 0xFF
        elif ft == 2:  # Up
            for x in range(stride):
                line[x] = (line[x] + prev[x]) & 0xFF
        elif ft == 3:  # Average
            for x in range(stride):
                a = line[x - ch] if x >= ch else 0
                line[x] = (line[x] + ((a + prev[x]) >> 1)) & 0xFF
        elif ft == 4:  # Paeth
            for x in range(stride):
                a = line[x - ch] if x >= ch else 0
                c = prev[x - ch] if x >= ch else 0
                line[x] = (line[x] + _paeth(a, prev[x], c)) & 0xFF
        elif ft != 0:
            raise ValueError(f"bad scanline filter {ft}")
        out[y * stride:(y + 1) * stride] = line
        prev = line
    return width, height, ch, bytes(out)


class Sampler:
    """Read-only pixel access over a decoded image, in 0-255 rgb, addressed by
    normalized (u, v) in 0..1 with v pointing DOWN (row 0 at top)."""

    def __init__(self, width, height, channels, buf):
        self.w, self.h, self.c, self.buf = width, height, channels, buf

    @classmethod
    def load(cls, path):
        return cls(*read_png(path))

    def at(self, u, v):
        x = min(self.w - 1, max(0, int(u * self.w)))
        y = min(self.h - 1, max(0, int(v * self.h)))
        i = (y * self.w + x) * self.c
        return (self.buf[i], self.buf[i + 1], self.buf[i + 2])

    def grid(self, n):
        """n*n evenly spaced samples (cell centers of an n*n grid)."""
        return [self.at((i + 0.5) / n, (j + 0.5) / n)
                for j in range(n) for i in range(n)]

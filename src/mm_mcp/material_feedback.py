"""Render compact review images and measure normalized MetricSurface maps."""

from array import array
from contextlib import ExitStack
import math
import os
from pathlib import Path
import sys
from tempfile import NamedTemporaryFile
from typing import Mapping, Sequence

from PIL import Image, ImageChops, ImageDraw, ImageStat


_MAP_MODES = {
    "baseColor": "RGB",
    "normal": "RGB",
    "orm": "RGBA",
    "height": "I;16",
    "susceptibility": "RGB",
}
_SAMPLE_LIMIT = 262_144
_PANEL_WIDTH = 360
_TILE_HEIGHT = 164
_RELIEF_HEIGHT = 110
_RELIEF_ZOOM = 3
_GAP = 12
_PADDING = 16


def _physical_scale(repeat_metres, height_range_metres):
    if len(repeat_metres) != 2 or any(
        not math.isfinite(length) or length <= 0 for length in repeat_metres
    ):
        raise ValueError("repeat_metres must contain two positive finite lengths")
    if not math.isfinite(height_range_metres) or height_range_metres <= 0:
        raise ValueError("height_range_metres must be positive and finite")


def _height_values(height: Image.Image) -> array:
    # PNG grayscale16 normally opens as I;16 (little endian). Pillow 10 can
    # also open it as I, while callers may supply a big-endian image directly.
    if height.mode == "I":
        height = height.convert("I;16")
    if height.mode not in {"I;16", "I;16L", "I;16B", "I;16N"}:
        raise ValueError("height must be a 16-bit grayscale image")
    values = array("H", height.tobytes())
    if height.mode != "I;16N" and (height.mode == "I;16B") != (sys.byteorder == "big"):
        values.byteswap()
    return values


def _normal_height(normal, heights, repeat_metres, height_range_metres, max_samples):
    width, height = normal.size
    stride = 1 if max_samples is None else math.ceil(math.sqrt(width * height / max_samples))
    offset = stride // 2
    # An elongated map may have fewer rows or columns than the sample stride.
    x_start = min(width - 1, offset)
    y_start = min(height - 1, offset)
    pixels = normal.tobytes()
    x_scale = width * height_range_metres / (repeat_metres[0] * 65535)
    y_scale = height * height_range_metres / (repeat_metres[1] * 65535)
    total = 0.0
    minimum = 1.0
    count = 0
    for y in range(y_start, height, stride):
        row = y * width
        next_row = ((y + 1) % height) * width
        for x in range(x_start, width, stride):
            index = row + x
            elevation = heights[index]
            dx = (heights[row + (x + 1) % width] - elevation) * x_scale
            dy = (heights[next_row + x] - elevation) * y_scale
            p = index * 3
            nx = pixels[p] * 2 - 255
            ny = pixels[p + 1] * 2 - 255
            nz = pixels[p + 2] * 2 - 255
            # Image rows run down, while the tangent normal convention is +Y up.
            dot = (-dx * nx + dy * ny + nz) / math.sqrt(
                (1 + dx * dx + dy * dy) * (nx * nx + ny * ny + nz * nz)
            )
            total += dot
            minimum = min(minimum, dot)
            count += 1
    return {"meanDot": round(total / count, 8), "minDot": round(minimum, 8), "samples": count}


def measure_normal_height(
    normal: Image.Image,
    height: Image.Image,
    repeat_metres: Sequence[float],
    height_range_metres: float,
    *,
    max_samples: int | None = _SAMPLE_LIMIT,
) -> dict:
    """Compare OpenGL +Y normals to forward periodic height derivatives in metres."""
    _physical_scale(repeat_metres, height_range_metres)
    if normal.mode != "RGB" or normal.size != height.size or min(normal.size) < 2:
        raise ValueError("normal must be RGB and share the height dimensions, at least 2 x 2")
    if max_samples is not None and max_samples < 1:
        raise ValueError("max_samples must be positive")
    return _normal_height(
        normal, _height_values(height), repeat_metres, height_range_metres, max_samples
    )


def _step_summary(edge, interior, max_value):
    return {
        "edgeStep": round(edge / max_value, 8),
        "interiorStep": round(interior / max_value, 8),
        "edgeToInteriorRatio": round(edge / interior, 6) if interior else (None if edge else 0.0),
    }


def _seams_8bit(image: Image.Image) -> dict:
    width, height = image.size

    def difference(left_box, right_box):
        delta = ImageChops.difference(image.crop(left_box), image.crop(right_box))
        return sum(ImageStat.Stat(delta).mean) / len(image.getbands())

    return {
        "x": _step_summary(
            difference((0, 0, 1, height), (width - 1, 0, width, height)),
            difference((0, 0, width - 1, height), (1, 0, width, height)),
            255,
        ),
        "y": _step_summary(
            difference((0, 0, width, 1), (0, height - 1, width, height)),
            difference((0, 0, width, height - 1), (0, 1, width, height)),
            255,
        ),
    }


def _seams_16bit(values: array, size: tuple[int, int]) -> dict:
    width, height = size
    horizontal = 0
    edge_x = 0
    for row in range(0, len(values), width):
        horizontal += sum(
            abs(left - right)
            for left, right in zip(values[row : row + width - 1], values[row + 1 : row + width])
        )
        edge_x += abs(values[row] - values[row + width - 1])
    vertical = sum(abs(top - bottom) for top, bottom in zip(values[:-width], values[width:]))
    edge_y = sum(abs(top - bottom) for top, bottom in zip(values[:width], values[-width:]))
    return {
        "x": _step_summary(edge_x / height, horizontal / (height * (width - 1)), 65535),
        "y": _step_summary(edge_y / width, vertical / (width * (height - 1)), 65535),
    }


def _tile(image: Image.Image, size: tuple[int, int]) -> Image.Image:
    width, height = size
    repeated = Image.new("RGB", size)
    for y in range(height // 2 % image.height - image.height, height, image.height):
        for x in range(width // 2 % image.width - image.width, width, image.width):
            repeated.paste(image, (x, y))
    return repeated


def _linear_srgb(value: float) -> float:
    return value / 12.92 if value <= 0.04045 else ((value + 0.055) / 1.055) ** 2.4


def _display_srgb(value: float) -> int:
    value = min(1.0, max(0.0, value))
    encoded = 12.92 * value if value <= 0.0031308 else 1.055 * value ** (1 / 2.4) - 0.055
    return round(255 * encoded)


_SRGB = tuple(_linear_srgb(value / 255) for value in range(256))


def _grazing_light(base: Image.Image, normal: Image.Image, orm: Image.Image, direction: int):
    # Opposing directional sources at 12 degrees on a neutral flat tile.
    # This CPU preview is a repeatable relief diagnostic for a textured plane.
    elevation = math.radians(12)
    azimuth = math.radians(32)
    lx = direction * math.cos(elevation) * math.cos(azimuth)
    ly = direction * math.cos(elevation) * math.sin(azimuth)
    lz = math.sin(elevation)
    half_length = math.sqrt(lx * lx + ly * ly + (lz + 1) ** 2)
    hx, hy, hz = lx / half_length, ly / half_length, (lz + 1) / half_length
    colors = base.tobytes()
    vectors = normal.tobytes()
    responses = orm.tobytes()
    shaded = bytearray()
    for rgb, rgba in zip(range(0, len(colors), 3), range(0, len(responses), 4)):
        nx, ny, nz = (value * 2 - 255 for value in vectors[rgb : rgb + 3])
        length = math.sqrt(nx * nx + ny * ny + nz * nz)
        diffuse = max(0.0, (nx * lx + ny * ly + nz * lz) / length)
        facing = max(0.0, (nx * hx + ny * hy + nz * hz) / length)
        occlusion, roughness, metallic = (value / 255 for value in responses[rgba : rgba + 3])
        specular = facing ** (4 + 80 * (1 - roughness) ** 2)
        intensity = 0.36 * occlusion + 1.45 * diffuse * (1 - 0.6 * metallic)
        for value in colors[rgb : rgb + 3]:
            linear = _SRGB[value]
            reflection = 0.06 * (1 - metallic) + linear * metallic
            shaded.append(_display_srgb(linear * intensity + reflection * specular))
    return Image.frombytes("RGB", base.size, shaded)


def _read_variant(paths, repeat_metres, height_range_metres, pixels_per_metre):
    missing = set(_MAP_MODES) - paths.keys()
    if missing:
        raise ValueError(f"missing material maps: {', '.join(sorted(missing))}")
    with ExitStack() as files:
        maps = {role: files.enter_context(Image.open(paths[role])) for role in _MAP_MODES}
        size = maps["baseColor"].size
        if min(size) < 2 or any(image.size != size for image in maps.values()):
            raise ValueError("the five material maps must share dimensions of at least 2 x 2")
        for role, image in maps.items():
            if image.format != "PNG":
                raise ValueError(f"{role} must be a PNG image")
            if role != "height" and image.mode != _MAP_MODES[role]:
                raise ValueError(f"{role} must have mode {_MAP_MODES[role]}")
        heights = _height_values(maps["height"])
        seams = {role: _seams_8bit(image) for role, image in maps.items() if role != "height"}
        seams["height"] = _seams_16bit(heights, size)
        agreement = _normal_height(
            maps["normal"], heights, repeat_metres, height_range_metres, _SAMPLE_LIMIT
        )

        tile_size = tuple(max(1, round(length * pixels_per_metre)) for length in repeat_metres)
        swatch = _tile(
            maps["baseColor"].resize(tile_size, Image.Resampling.LANCZOS),
            (_PANEL_WIDTH, _TILE_HEIGHT),
        )
        relief_tile_size = tuple(
            max(1, round(length * pixels_per_metre * _RELIEF_ZOOM)) for length in repeat_metres
        )
        base, normal, orm = (
            maps[role].resize(relief_tile_size, Image.Resampling.LANCZOS)
            for role in ("baseColor", "normal", "orm")
        )
        relief_size = ((_PANEL_WIDTH - _GAP) // 2, _RELIEF_HEIGHT)
        relief = [
            _tile(_grazing_light(base, normal, orm, direction), relief_size)
            for direction in (-1, 1)
        ]
    return (
        swatch,
        relief,
        {
            "dimensions": list(size),
            "repeatMetres": list(repeat_metres),
            "heightRangeMetres": height_range_metres,
            "mapSeams": seams,
            "normalHeightMeanDot": agreement["meanDot"],
            "normalHeightMinDot": agreement["minDot"],
            "normalHeightSamples": agreement["samples"],
        },
    )


def build_material_feedback(
    maps: Mapping[str, str | Path],
    preview_path: str | Path,
    *,
    repeat_metres: Sequence[float],
    height_range_metres: float,
    baseline_maps: Mapping[str, str | Path] | None = None,
    baseline_repeat_metres: Sequence[float] | None = None,
    baseline_height_range_metres: float | None = None,
) -> dict:
    """Write one comparison PNG and return per-map seam and relief measurements.

    Seam steps are mean absolute stored-value jumps as fractions of the full
    channel range. X and Y compare the outer edge with neighbors inside the
    tile in the same direction. A ratio of null means only the edge changes.
    """
    _physical_scale(repeat_metres, height_range_metres)
    variants = [("Candidate", maps, repeat_metres, height_range_metres)]
    if baseline_maps is not None:
        baseline_repeat = repeat_metres if baseline_repeat_metres is None else baseline_repeat_metres
        baseline_height = (
            height_range_metres if baseline_height_range_metres is None else baseline_height_range_metres
        )
        _physical_scale(baseline_repeat, baseline_height)
        variants.insert(0, ("Baseline", baseline_maps, baseline_repeat, baseline_height))

    preview_path = Path(preview_path).resolve()
    if any(preview_path == Path(path).resolve() for _, paths, _, _ in variants for path in paths.values()):
        raise ValueError("preview_path must be distinct from each input map")

    # Use the same metres per pixel for both variants, fitting at least three
    # horizontal repeats and two vertical repeats of the larger tile.
    scale = min(
        _PANEL_WIDTH / (3 * max(repeat[0] for _, _, repeat, _ in variants)),
        _TILE_HEIGHT / (2 * max(repeat[1] for _, _, repeat, _ in variants)),
    )
    width = 2 * _PADDING + _PANEL_WIDTH * len(variants) + _GAP * (len(variants) - 1)
    height = 2 * _PADDING + _TILE_HEIGHT + _RELIEF_HEIGHT + 59
    preview = Image.new("RGB", (width, height), "#171c21")
    draw = ImageDraw.Draw(preview)
    feedback = {
        "image": str(preview_path),
        "imageWidth": width,
        "imageHeight": height,
        "repeatMetres": list(repeat_metres),
        "heightRangeMetres": height_range_metres,
        "previewSpanMetres": [round(_PANEL_WIDTH / scale, 4), round(_TILE_HEIGHT / scale, 4)],
        "grazingPreviewSpanMetres": [
            round((_PANEL_WIDTH - _GAP) / (2 * scale * _RELIEF_ZOOM), 4),
            round(_RELIEF_HEIGHT / (scale * _RELIEF_ZOOM), 4),
        ],
        "grazingLightElevationDegrees": 12,
    }
    for index, (title, paths, repeat, physical_height) in enumerate(variants):
        swatch, relief, metrics = _read_variant(paths, repeat, physical_height, scale)
        x = _PADDING + index * (_PANEL_WIDTH + _GAP)
        draw.text((x, _PADDING), f"{title} | {repeat[0]:g} x {repeat[1]:g} m per repeat", fill="#f5f8fa")
        draw.text((x, _PADDING + 18), "Tiled base color", fill="#bfc9d0")
        preview.paste(swatch, (x, _PADDING + 36))
        for panel, direction in enumerate(("left", "right")):
            light_x = x + panel * (relief[panel].width + _GAP)
            y = _PADDING + _TILE_HEIGHT + 43
            draw.text((light_x, y), f"Grazing light / {direction}", fill="#bfc9d0")
            preview.paste(relief[panel], (light_x, y + 16))
        feedback[title.lower()] = metrics

    preview_path.parent.mkdir(parents=True, exist_ok=True)
    stream = NamedTemporaryFile(dir=preview_path.parent, prefix=".feedback-", delete=False)
    temporary = Path(stream.name)
    try:
        with stream:
            preview.save(stream, format="PNG", optimize=True)
        os.replace(temporary, preview_path)
    finally:
        temporary.unlink(missing_ok=True)
    return feedback

"""Reproducible front-page showcase pipeline: render cookbook/saved-graph
materials to PBR maps via headless Godot, composite them onto the lit
sphere/cube/cutaway rig, and assemble the README hero image + gallery tiles
(and optional looping GIFs). Dev-only tool -- Pillow is fine to import here
per the same rationale as quality/_make_previews.py.

The four helpers below (resolve_source, gallery_out_path, montage,
downscale_gif_frames) are pure and import-safe: they never launch Godot, so
`tests/test_make_showcase.py` can import this module and exercise them
without a Material Maker/Godot install. All Godot-touching work (render(),
render_preview(), render_preview_sweep()) lives in main()/the CLI subcommands
only.

Usage:
    .venv\\Scripts\\python.exe -m quality._make_showcase still <ident> [<ident> ...]
    .venv\\Scripts\\python.exe -m quality._make_showcase hero <identA> <identB> <identC>
    .venv\\Scripts\\python.exe -m quality._make_showcase gif <ident> [--width 512] [--frames 18] [--duration 80]

`ident` is either a cookbook label (searched under cookbook/*/<ident>.ptex)
or an explicit path to a .ptex file (e.g. saved_graphs/bricks_grayson_edit.ptex).
"""
import argparse
import shutil
import sys
import tempfile
from pathlib import Path

from PIL import Image

_ROOT = Path(__file__).resolve().parent.parent
_GALLERY_DIR = _ROOT / "docs" / "images" / "gallery"
_HERO_PATH = _ROOT / "docs" / "images" / "hero.png"

STILL_SIZE = (1024, 576)


def resolve_source(ident: str) -> Path:
    """Resolve a showcase identifier to a .ptex file.

    If `ident` ends in `.ptex`, treat it as a path (resolved relative to the
    repo root if not already absolute). Otherwise search
    cookbook/*/<ident>.ptex for a matching label. Raises FileNotFoundError
    naming `ident` if neither resolves.
    """
    if ident.endswith(".ptex"):
        p = Path(ident)
        if not p.is_absolute():
            p = _ROOT / p
        if p.is_file():
            return p
        raise FileNotFoundError(f"no such showcase source: '{ident}'")

    matches = sorted(_ROOT.glob(f"cookbook/*/{ident}.ptex"))
    if matches:
        return matches[0]
    raise FileNotFoundError(f"no such showcase source: '{ident}'")


def gallery_out_path(ident: str) -> Path:
    """docs/images/gallery/<stem>.png, where <stem> is the label itself for a
    bare label or the path's stem for a `.ptex` path."""
    stem = Path(ident).stem
    return _GALLERY_DIR / f"{stem}.png"


def _center_crop(im: Image.Image, panel_w: int, panel_h: int) -> Image.Image:
    w, h = im.size
    left = max(0, (w - panel_w) // 2)
    top = max(0, (h - panel_h) // 2)
    return im.crop((left, top, left + panel_w, top + panel_h))


def montage(panel_paths: list[Path], out_path: Path, panel_w: int = 683, panel_h: int = 560) -> None:
    """Center-crop each source PNG to panel_w x panel_h and concatenate them
    horizontally into one image saved at out_path."""
    panels = [_center_crop(Image.open(p).convert("RGB"), panel_w, panel_h) for p in panel_paths]
    out = Image.new("RGB", (panel_w * len(panels), panel_h))
    for i, panel in enumerate(panels):
        out.paste(panel, (i * panel_w, 0))
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out.save(out_path)


def downscale_gif_frames(frame_paths: list[Path], width: int) -> list[Image.Image]:
    """LANCZOS-resize each frame to `width`, preserving aspect ratio."""
    frames = []
    for p in frame_paths:
        im = Image.open(p).convert("RGB")
        w, h = im.size
        height = round(h * (width / w))
        frames.append(im.resize((width, height), Image.LANCZOS))
    return frames


def _render_still(ident: str):
    """Godot-touching: render() the resolved .ptex, then render_preview()
    the resulting maps. Returns the PreviewResult. Import Godot-dependent
    modules lazily so the pure helpers above stay import-safe."""
    from mm_mcp.render import render
    from mm_mcp.preview import render_preview
    from mm_mcp.config import load_config
    import json

    cfg = load_config()
    src = resolve_source(ident)
    ptex = json.loads(src.read_text(encoding="utf-8"))
    basename = Path(ident).stem if ident.endswith(".ptex") else ident

    with tempfile.TemporaryDirectory() as tmpdir:
        outdir = str(Path(tmpdir).resolve())
        render_result = render(ptex, outdir=outdir, basename=basename, cfg=cfg)
        if not render_result.ok:
            raise RuntimeError(f"render failed for '{ident}': {render_result.error}")

        albedo = next(p for p in render_result.images if p.endswith("_albedo.png"))
        normal = next(p for p in render_result.images if p.endswith("_normal.png"))
        orm = next(p for p in render_result.images if p.endswith("_orm.png"))

        preview_result = render_preview(albedo, normal, orm, outdir=outdir, basename=basename, cfg=cfg)
        if not preview_result.ok:
            raise RuntimeError(f"preview render failed for '{ident}': {preview_result.error}")

        # Copy out of the temp dir before it's cleaned up.
        dest_tmp = Path(tmpdir) / f"__keep_{basename}_preview.png"
        shutil.copyfile(preview_result.image, dest_tmp)
        im = Image.open(dest_tmp).convert("RGB")
        im.load()
        return im


def cmd_still(idents: list[str]) -> int:
    for ident in idents:
        im = _render_still(ident)
        out_path = gallery_out_path(ident)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        im.save(out_path)
        print(f"{ident}: {out_path} ({im.size[0]}x{im.size[1]})")
    return 0


def cmd_hero(idents: list[str]) -> int:
    panel_paths = []
    with tempfile.TemporaryDirectory() as tmpdir:
        for i, ident in enumerate(idents):
            im = _render_still(ident)
            p = Path(tmpdir) / f"panel_{i}.png"
            im.save(p)
            panel_paths.append(p)
        montage(panel_paths, _HERO_PATH)
    print(f"hero: {_HERO_PATH}")
    return 0


def cmd_gif(ident: str, width: int, frames: int, duration: int) -> int:
    from mm_mcp.render import render
    from mm_mcp.preview import render_preview_sweep
    from mm_mcp.config import load_config
    import json

    cfg = load_config()
    src = resolve_source(ident)
    ptex = json.loads(src.read_text(encoding="utf-8"))
    basename = Path(ident).stem if ident.endswith(".ptex") else ident

    with tempfile.TemporaryDirectory() as tmpdir:
        outdir = str(Path(tmpdir).resolve())
        render_result = render(ptex, outdir=outdir, basename=basename, cfg=cfg)
        if not render_result.ok:
            raise RuntimeError(f"render failed for '{ident}': {render_result.error}")

        albedo = next(p for p in render_result.images if p.endswith("_albedo.png"))
        normal = next(p for p in render_result.images if p.endswith("_normal.png"))
        orm = next(p for p in render_result.images if p.endswith("_orm.png"))

        sweep_result = render_preview_sweep(
            albedo, normal, orm, outdir=outdir, basename=basename,
            frames=frames, frame_duration_ms=duration, cfg=cfg,
        )
        if not sweep_result.ok:
            raise RuntimeError(f"preview sweep failed for '{ident}': {sweep_result.error}")

        # The sweep GIF is already assembled; re-extract, downscale, reassemble.
        gif_im = Image.open(sweep_result.image)
        raw_frame_dir = Path(tmpdir) / "raw_frames"
        raw_frame_dir.mkdir()
        frame_paths = []
        for i in range(sweep_result.frame_count):
            gif_im.seek(i)
            fp = raw_frame_dir / f"frame_{i:03d}.png"
            gif_im.convert("RGB").save(fp)
            frame_paths.append(fp)

        scaled = downscale_gif_frames(frame_paths, width=width)

        stem = Path(ident).stem
        out_path = _GALLERY_DIR / f"{stem}.gif"
        out_path.parent.mkdir(parents=True, exist_ok=True)
        scaled[0].save(out_path, save_all=True, append_images=scaled[1:],
                        duration=duration, loop=0)

    size_bytes = out_path.stat().st_size
    print(f"{ident}: {out_path} ({size_bytes} bytes)")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="quality._make_showcase")
    sub = parser.add_subparsers(dest="mode", required=True)

    p_still = sub.add_parser("still")
    p_still.add_argument("idents", nargs="+")

    p_hero = sub.add_parser("hero")
    p_hero.add_argument("idents", nargs=3)

    p_gif = sub.add_parser("gif")
    p_gif.add_argument("ident")
    p_gif.add_argument("--width", type=int, default=512)
    p_gif.add_argument("--frames", type=int, default=18)
    p_gif.add_argument("--duration", type=int, default=80)

    args = parser.parse_args(argv)

    if args.mode == "still":
        return cmd_still(args.idents)
    if args.mode == "hero":
        return cmd_hero(args.idents)
    if args.mode == "gif":
        return cmd_gif(args.ident, args.width, args.frames, args.duration)
    return 1


if __name__ == "__main__":
    sys.exit(main())

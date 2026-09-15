"""Render the 3D PREVIEW COMPOSITE of a fixed matte set and pixel-compare two
runs. This is the no-regress gate for a rig (preview.gd) change: render_tracked
compares the PBR maps, which a rig change never touches, so it cannot prove a
lighting change left matte materials alone. Run as a script, never python -c;
outdir is resolved absolute before Godot sees it. One Godot at a time."""
import shutil
from pathlib import Path

from quality.render_compare import renders_match, grid_mean_abs_diff

_ROOT = Path(__file__).resolve().parent.parent
_COOKBOOK = _ROOT / "cookbook"
MATTE_SET = ["s07_cobblestone", "f07_herringbone_tweed", "t02_fresh_snow", "s02_gray_granite"]


def _resolve(ident: str) -> Path:
    hits = list(_COOKBOOK.glob(f"**/{ident}.ptex"))
    if not hits:
        raise FileNotFoundError(f"no cookbook graph for {ident!r}")
    return hits[0]


def render_matte_previews(idents, outdir: Path) -> list[str]:
    import json, tempfile
    from mm_mcp.render import render
    from mm_mcp.preview import render_preview
    from mm_mcp.config import load_config

    cfg = load_config()
    outdir = Path(outdir).resolve()
    outdir.mkdir(parents=True, exist_ok=True)
    problems = []
    for ident in idents:
        ptex = json.loads(_resolve(ident).read_text(encoding="utf-8"))
        with tempfile.TemporaryDirectory() as tmp:
            tmp = str(Path(tmp).resolve())
            rr = render(ptex, outdir=tmp, basename=ident, cfg=cfg)
            if not rr.ok:
                problems.append(f"{ident}: render failed: {rr.error}"); continue
            try:
                albedo = next(p for p in rr.images if p.endswith("_albedo.png"))
                normal = next(p for p in rr.images if p.endswith("_normal.png"))
                orm = next(p for p in rr.images if p.endswith("_orm.png"))
            except StopIteration:
                problems.append(f"{ident}: missing albedo/normal/orm map"); continue
            pr = render_preview(albedo, normal, orm, outdir=tmp, basename=ident, tile=0.45, cfg=cfg)
            if not pr.ok:
                problems.append(f"{ident}: preview failed: {pr.error}"); continue
            shutil.copyfile(pr.image, outdir / f"{ident}.png")
    return problems


def compare_previews(baseline: Path, current: Path, idents) -> list[str]:
    baseline, current = Path(baseline), Path(current)
    problems = []
    for ident in idents:
        a, b = baseline / f"{ident}.png", current / f"{ident}.png"
        if not a.is_file():
            problems.append(f"{ident}: no baseline preview"); continue
        if not b.is_file():
            problems.append(f"{ident}: missing in current"); continue
        if not renders_match(str(a), str(b)):
            problems.append(f"{ident}: differs, mean abs diff {grid_mean_abs_diff(str(a), str(b)):.2f}")
    return problems


def main(argv) -> int:
    def _arg(flag, default=None):
        return argv[argv.index(flag) + 1] if flag in argv else default
    out = _arg("--out")
    if not out:
        print(__doc__); return 2
    out = Path(out).resolve()
    baseline = _arg("--compare")
    problems = render_matte_previews(MATTE_SET, out)
    if baseline:
        problems += compare_previews(Path(baseline).resolve(), out, MATTE_SET)
    for p in problems:
        print(p)
    print(f"{len(MATTE_SET)} preview(s), {len(problems)} problem(s)")
    return 1 if problems else 0


if __name__ == "__main__":
    import sys
    sys.exit(main(sys.argv[1:]))

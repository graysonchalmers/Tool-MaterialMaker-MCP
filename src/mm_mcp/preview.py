import os
import tempfile
from dataclasses import dataclass
from PIL import Image
from mm_mcp.config import Config, load_config
from mm_mcp.paths import PathNotAllowed, reject_path_fragment
from mm_mcp.render import _run_godot, _log_tail, _GodotTimeout, _clear_staging, _validate_png

_PREVIEW_PROJECT = os.path.join(os.path.dirname(__file__), "preview_project")


@dataclass
class PreviewResult:
    ok: bool
    image: str | None = None
    log_tail: str = ""
    error: str | None = None


def _build_command(cfg: Config, albedo_path: str, normal_path: str, orm_path: str,
                    out_path: str, tile: float) -> list[str]:
    return [
        cfg.console_binary, "--path", _PREVIEW_PROJECT, "--",
        f"--albedo={albedo_path}", f"--normal={normal_path}",
        f"--orm={orm_path}", f"--out={out_path}", f"--tile={tile}",
    ]


def render_preview(albedo_path: str, normal_path: str, orm_path: str,
                    outdir: str | None = None, basename: str = "preview",
                    tile: float = 1.0, cfg: Config | None = None) -> PreviewResult:
    """Composite a material's already-rendered maps onto a lit sphere + cube.

    Takes paths from a prior render_graph call (albedo/normal/orm), not a
    .ptex graph — rendering the flat maps is render.py's job, this only
    visualizes maps that already exist. tile controls the UV repeat count on
    the sphere/cube/cutaway ball; the ground plane always tiles finer than
    that so its own repeat is visible regardless of the chosen value.
    """
    for label, path in (("albedo", albedo_path), ("normal", normal_path),
                         ("orm", orm_path)):
        if not os.path.isfile(path):
            return PreviewResult(ok=False, error=f"{label} path does not exist: '{path}'")

    # Godot runs with --path pointing at the bundled preview_project, whose
    # own path resolution for a bare relative string does not match the
    # calling process's OS cwd. Resolve to absolute here so a caller passing
    # back whatever render_graph returned (which may be relative) still works.
    albedo_path = os.path.abspath(albedo_path)
    normal_path = os.path.abspath(normal_path)
    orm_path = os.path.abspath(orm_path)

    cfg = cfg or load_config()
    outdir = os.path.abspath(outdir or cfg.output_dir)
    out_path = os.path.join(outdir, basename + "_preview.png")
    log_tail = ""
    try:
        reject_path_fragment(basename)
        if not basename or basename == ".":
            raise ValueError("basename must be a nonempty file name")
        os.makedirs(outdir, exist_ok=True)
        with tempfile.TemporaryDirectory(prefix=".preview-", dir=outdir) as stage:
            staged_image = os.path.join(stage, basename + "_preview.png")
            cmd = _build_command(cfg, albedo_path, normal_path, orm_path, staged_image, tile)
            proc = _run_godot(cmd, 60, before_attempt=lambda: _clear_staging(stage))
            log_tail = _log_tail(proc)
            if proc.returncode != 0:
                return PreviewResult(ok=False, log_tail=log_tail,
                                     error=f"Godot exited {proc.returncode}")
            if not os.path.isfile(staged_image):
                return PreviewResult(ok=False, log_tail=log_tail, error="no PNG output produced")
            if os.path.islink(staged_image):
                raise ValueError("renderer produced a symbolic link")
            _validate_png(staged_image)
            os.replace(staged_image, out_path)
        return PreviewResult(ok=True, image=out_path, log_tail=log_tail)
    except _GodotTimeout:
        return PreviewResult(ok=False, error="preview render timed out after 60s")
    except (OSError, ValueError, SyntaxError, Image.DecompressionBombError, PathNotAllowed) as exc:
        return PreviewResult(ok=False, log_tail=log_tail, error=str(exc))

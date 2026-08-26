import os
import subprocess
from dataclasses import dataclass
from mm_mcp.config import Config, load_config

_PREVIEW_PROJECT = os.path.join(os.path.dirname(__file__), "preview_project")

# Same transient Godot crash codes render.py retries around (access violation /
# stack-guard, unrelated to the scene, a re-run of the same input succeeds).
_TRANSIENT = {3221225477, 3221226505}


@dataclass
class PreviewResult:
    ok: bool
    image: str | None = None
    log_tail: str = ""
    error: str | None = None


def render_preview(albedo_path: str, normal_path: str, orm_path: str,
                    outdir: str | None = None, basename: str = "preview",
                    cfg: Config | None = None) -> PreviewResult:
    """Composite a material's already-rendered maps onto a lit sphere + cube.

    Takes paths from a prior render_graph call (albedo/normal/orm), not a
    .ptex graph — rendering the flat maps is render.py's job, this only
    visualizes maps that already exist.
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
    outdir = outdir or cfg.output_dir
    os.makedirs(outdir, exist_ok=True)

    out_path = os.path.abspath(os.path.join(outdir, basename + "_preview.png"))
    if os.path.exists(out_path):
        os.remove(out_path)

    cmd = [
        cfg.console_binary, "--path", _PREVIEW_PROJECT, "--",
        f"--albedo={albedo_path}", f"--normal={normal_path}",
        f"--orm={orm_path}", f"--out={out_path}",
    ]

    proc = None
    for _ in range(3):
        try:
            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        except subprocess.TimeoutExpired:
            return PreviewResult(ok=False, error="preview render timed out after 60s")
        if proc.returncode not in _TRANSIENT:
            break

    log = (proc.stdout or "") + (proc.stderr or "")
    log_tail = "\n".join(log.splitlines()[-20:])

    if not os.path.isfile(out_path) or os.path.getsize(out_path) <= 0:
        error = f"Godot exited {proc.returncode}" if proc.returncode != 0 else "no PNG output produced"
        return PreviewResult(ok=False, log_tail=log_tail, error=error)
    return PreviewResult(ok=True, image=out_path, log_tail=log_tail)

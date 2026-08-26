import json
import os
import subprocess
from dataclasses import dataclass, field
from mm_mcp.config import Config, load_config


@dataclass
class RenderResult:
    ok: bool
    images: list = field(default_factory=list)
    log_tail: str = ""
    error: str | None = None


def _collect_fresh_images(outdir: str, basename: str, before: dict) -> list[str]:
    """Collect only fresh PNG outputs matching <basename>_*.png pattern.

    Args:
        outdir: Output directory to scan
        basename: Material name (e.g., "bricks")
        before: Dict of {filename: mtime} for files present before render

    Returns:
        List of absolute paths to non-empty PNG files that are new or have
        changed mtime since the snapshot in 'before'.
    """
    fresh = []
    for fn in sorted(os.listdir(outdir)):
        if not (fn.startswith(basename + "_") and fn.lower().endswith(".png")):
            continue
        full = os.path.join(outdir, fn)
        if os.path.getsize(full) <= 0:
            continue
        prev = before.get(fn)
        if prev is None or os.path.getmtime(full) > prev:
            fresh.append(full)
    return fresh


def render(ptex: dict, size: int = 512, outdir: str | None = None,
           basename: str = "material", cfg: Config | None = None) -> RenderResult:
    cfg = cfg or load_config()
    outdir = outdir or cfg.output_dir
    os.makedirs(outdir, exist_ok=True)

    # Snapshot existing output files before render to detect fresh outputs
    before = {}
    for fn in os.listdir(outdir):
        if fn.startswith(basename + "_") and fn.lower().endswith(".png"):
            full = os.path.join(outdir, fn)
            try:
                before[fn] = os.path.getmtime(full)
            except (OSError, FileNotFoundError):
                pass

    ptex_path = os.path.join(outdir, basename + ".ptex")
    with open(ptex_path, "w", encoding="utf-8") as fh:
        json.dump(ptex, fh)

    cmd = [
        cfg.console_binary, "--path", cfg.project_path,
        "--export-material", ptex_path,
        "-t", "Godot/Godot 4 Standard",
        "-o", outdir, "--size", str(size),
    ]

    # Godot occasionally dies mid-export with a Windows crash code (access
    # violation 0xC0000005 = 3221225477, stack-guard 0xC0000409 = 3221226505)
    # that is unrelated to the graph — the identical .ptex renders on a re-run.
    # Retry those transient crashes a couple of times before giving up.
    _TRANSIENT = {3221225477, 3221226505}
    proc = None
    for attempt in range(3):
        try:
            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
        except subprocess.TimeoutExpired:
            return RenderResult(ok=False, error="Godot render timed out after 180s")
        if proc.returncode not in _TRANSIENT:
            break

    log = (proc.stdout or "") + (proc.stderr or "")
    log_tail = "\n".join(log.splitlines()[-20:])

    images = _collect_fresh_images(outdir, basename, before)

    if proc.returncode != 0 and not images:
        return RenderResult(ok=False, log_tail=log_tail,
                            error=f"Godot exited {proc.returncode}")
    if not images:
        return RenderResult(ok=False, log_tail=log_tail,
                            error="no PNG output produced")
    return RenderResult(ok=True, images=images, log_tail=log_tail)

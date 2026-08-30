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


# Godot occasionally dies mid-export with a Windows crash code (access
# violation 0xC0000005 = 3221225477, stack-guard 0xC0000409 = 3221226505)
# that is unrelated to the input -- an identical re-run succeeds. Both the
# batch render path and the preview path retry around these.
_TRANSIENT_GODOT_CRASH_CODES = {3221225477, 3221226505}


class _GodotTimeout(Exception):
    """Raised by _run_godot when the subprocess exceeds its timeout, so each
    caller can shape its own result type (RenderResult vs PreviewResult) for
    the timeout case rather than sharing one."""


def _kill_tree(process) -> None:
    """taskkill /F /T the whole Windows process tree rooted at `process`.

    Godot's console binary is a launcher that spawns the real render/GUI
    process as a separate child outside this Popen's own process tree, so
    killing just the launcher (plain process.kill(), or subprocess.run's own
    timeout behavior) leaves that grandchild orphaned. For render.py that
    orphan keeps holding Material Maker's single-instance lock, so the NEXT
    render launches, blocks waiting on the single instance, and also times
    out -- cascading into every subsequent render hanging at the timeout
    (found 2026-08-29 while rendering debug swatches; recovered by taskkill-ing
    all Godot). taskkill's /T flag walks the live parent-PID tree from the
    launcher's PID, reaching the grandchild too, and MUST run while the
    launcher is still alive -- a dead (possibly recycled) PID kills nothing.
    A test double with no real OS pid (no .pid attribute) skips this. Shared
    with live.py's _terminate, which imports it (live already depends on
    render, not the reverse)."""
    pid = getattr(process, "pid", None)
    if pid is None:
        return
    try:
        subprocess.run(["taskkill", "/F", "/T", "/PID", str(pid)],
                        capture_output=True, timeout=10)
    except (OSError, subprocess.TimeoutExpired):
        pass


def _run_godot(cmd: list, timeout: int) -> subprocess.CompletedProcess:
    """Run a Godot command with capture, retrying up to 3x around the
    transient Windows crash codes above. Raises _GodotTimeout on timeout.
    Shared by render() and preview.render_preview(), which otherwise each had
    a near-identical copy of this retry loop and the crash-code set.

    Uses Popen + communicate() (not subprocess.run) so a timeout can kill the
    whole process tree while the launcher is still alive -- subprocess.run
    kills only its direct child then re-raises, leaving Godot's spawned
    render/GUI grandchild orphaned to squat Material Maker's single-instance
    lock (see _kill_tree). communicate() drains both pipes concurrently, so
    a chatty Godot render log can't fill a pipe buffer and deadlock the child."""
    proc = None
    for _ in range(3):
        with subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                              text=True) as process:
            try:
                stdout, stderr = process.communicate(timeout=timeout)
            except subprocess.TimeoutExpired:
                _kill_tree(process)
                process.kill()
                try:
                    process.communicate(timeout=10)  # reap after the tree kill
                except subprocess.TimeoutExpired:
                    # taskkill failed AND killing the launcher didn't drop the
                    # pipe -- a surviving grandchild still holds its write end,
                    # so this reap would block on EOF forever. Abandon it rather
                    # than hang the render loop; the with-Popen exit only waits
                    # on the (already-killed) launcher, not the grandchild.
                    pass
                raise _GodotTimeout
            proc = subprocess.CompletedProcess(cmd, process.returncode, stdout, stderr)
        if proc.returncode not in _TRANSIENT_GODOT_CRASH_CODES:
            break
    return proc


def _log_tail(proc: subprocess.CompletedProcess, lines: int = 20) -> str:
    """The last `lines` lines of a Godot subprocess's combined stdout+stderr,
    for surfacing diagnostics without dumping the whole log. Shared by the
    batch and preview paths, which had a byte-for-byte copy of this."""
    log = (proc.stdout or "") + (proc.stderr or "")
    return "\n".join(log.splitlines()[-lines:])


def _snapshot_pngs(outdir: str, basename: str) -> dict:
    """Snapshot {filename: mtime} for existing <basename>_*.png files in
    outdir, so a later _collect_fresh_images call can tell which outputs a
    render actually (re)wrote. Missing/unreadable files are skipped. Shared
    by both the batch render path (below) and live.py's socket render path,
    which otherwise had a byte-for-byte copy of this loop."""
    before = {}
    for fn in os.listdir(outdir):
        if fn.startswith(basename + "_") and fn.lower().endswith(".png"):
            full = os.path.join(outdir, fn)
            try:
                before[fn] = os.path.getmtime(full)
            except (OSError, FileNotFoundError):
                pass
    return before


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


def _build_command(cfg: Config, ptex_path: str, target: str, outdir: str, size: int) -> list[str]:
    return [
        cfg.console_binary, "--path", cfg.project_path,
        "--export-material", ptex_path,
        "--target", target,
        "-o", outdir, "--size", str(size),
    ]


def render(ptex: dict, size: int = 512, outdir: str | None = None,
           basename: str = "material", target: str = "Godot/Godot 4 Standard",
           cfg: Config | None = None) -> RenderResult:
    cfg = cfg or load_config()
    outdir = outdir or cfg.output_dir
    os.makedirs(outdir, exist_ok=True)

    # Snapshot existing output files before render to detect fresh outputs
    before = _snapshot_pngs(outdir, basename)

    ptex_path = os.path.join(outdir, basename + ".ptex")
    with open(ptex_path, "w", encoding="utf-8") as fh:
        json.dump(ptex, fh)

    cmd = _build_command(cfg, ptex_path, target, outdir, size)

    try:
        proc = _run_godot(cmd, 180)
    except _GodotTimeout:
        return RenderResult(ok=False, error="Godot render timed out after 180s")
    log_tail = _log_tail(proc)

    images = _collect_fresh_images(outdir, basename, before)

    if proc.returncode != 0 and not images:
        return RenderResult(ok=False, log_tail=log_tail,
                            error=f"Godot exited {proc.returncode}")
    if not images:
        return RenderResult(ok=False, log_tail=log_tail,
                            error="no PNG output produced")
    return RenderResult(ok=True, images=images, log_tail=log_tail)

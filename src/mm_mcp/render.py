import json
import os
import subprocess
import tempfile
from typing import Callable
from dataclasses import dataclass, field
from PIL import Image, ImageStat
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


def _run_godot(cmd: list, timeout: int, *,
               before_attempt: Callable[[], None] | None = None) -> subprocess.CompletedProcess:
    """Run a Godot command with capture, retrying up to 3x around the
    transient Windows crash codes above. Raises _GodotTimeout on timeout.
    Shared by render() and preview.render_preview(), which otherwise each had
    a near-identical copy of this retry loop and the crash-code set.

    Uses Popen + process.wait() (not subprocess.run) so a timeout can kill the
    whole process tree while the launcher is still alive -- subprocess.run
    kills only its direct child then re-raises, leaving Godot's spawned
    render/GUI grandchild orphaned to squat Material Maker's single-instance
    lock (see _kill_tree).

    Redirects Godot's stdout/stderr to temp FILES rather than pipes. Material
    Maker's export leaves a lingering child (its Steam/relaunch process) that
    inherits the launcher's output handles; a PIPE stays un-closed until that
    grandchild also exits, so communicate() -- which blocks on pipe EOF, not
    process exit -- kept every render hung to the full timeout despite the
    export finishing in seconds. A file has no EOF dependency: wait() returns
    the instant the launcher exits, and the grandchild can hold the file
    harmlessly. This is what the working raw-console path always did."""
    proc = None
    for _ in range(3):
        # A successful retry must not inherit partial files from a crash.
        if before_attempt is not None:
            before_attempt()
        with tempfile.TemporaryFile() as out_f, tempfile.TemporaryFile() as err_f:
            process = subprocess.Popen(cmd, stdout=out_f, stderr=err_f)
            try:
                process.wait(timeout=timeout)
            except subprocess.TimeoutExpired:
                _kill_tree(process)
                process.kill()
                try:
                    process.wait(timeout=10)  # reap the launcher after the tree kill
                except subprocess.TimeoutExpired:
                    # taskkill failed AND the launcher itself won't die -- abandon
                    # the reap rather than hang the render loop. (Unlike a pipe, a
                    # lingering grandchild on the temp file never blocks this wait;
                    # only a genuinely unkillable launcher could reach here.)
                    pass
                raise _GodotTimeout
            out_f.seek(0)
            err_f.seek(0)
            stdout = out_f.read().decode("utf-8", "replace")
            stderr = err_f.read().decode("utf-8", "replace")
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


# Material Maker's parse_args.gd (upstream ad19fcf) parses --size into a
# variable it never reads and always exports at 2048, so render() downsamples
# the fresh maps itself. Nothing can come back larger than the bake.
_BAKE_SIZE = 2048
_MIN_SIZE = 16


def _undecodable(images: list[str]) -> str | None:
    """Name the first PNG that fails to decode fully (e.g. truncated by a
    Godot that died mid-write), or None if all of them load."""
    for path in images:
        try:
            with Image.open(path) as im:
                im.load()
        except (OSError, SyntaxError) as exc:
            return f"{os.path.basename(path)} does not decode ({exc})"
    return None


def _flat_normal(images: list[str], log: str) -> bool:
    """True when Material Maker compiled a buffer shader too late and baked a
    flat (127,127,255) normal map. It logs 'Rendering with invalid shader'
    when this happens and an identical re-run comes out fine. A flat normal
    WITHOUT that line is legitimate (nothing wired into the normal input)."""
    if "invalid shader" not in log:
        return False
    for path in images:
        if path.endswith("_normal.png"):
            with Image.open(path) as im:
                if max(ImageStat.Stat(im.convert("RGB")).stddev) < 0.5:
                    return True
    return False


def _downsample(images: list[str], size: int) -> None:
    for path in images:
        with Image.open(path) as im:
            if im.width <= size:
                continue
            small = im.resize((size, round(im.height * size / im.width)), Image.LANCZOS)
        small.save(path)


def render(ptex: dict, size: int = _BAKE_SIZE, outdir: str | None = None,
           basename: str = "material", target: str = "Godot/Godot 4 Standard",
           cfg: Config | None = None) -> RenderResult:
    if not _MIN_SIZE <= size <= _BAKE_SIZE:
        return RenderResult(ok=False, error=(
            f"size must be {_MIN_SIZE}-{_BAKE_SIZE}: Material Maker always "
            f"bakes at {_BAKE_SIZE} and maps are downsampled from that"))
    cfg = cfg or load_config()
    # Material Maker resolves a relative -o against its own project and then
    # hangs on "Output directory does not exist" until the 180 s timeout.
    outdir = os.path.abspath(outdir or cfg.output_dir)
    os.makedirs(outdir, exist_ok=True)

    ptex_path = os.path.join(outdir, basename + ".ptex")
    with open(ptex_path, "w", encoding="utf-8") as fh:
        json.dump(ptex, fh)

    cmd = _build_command(cfg, ptex_path, target, outdir, size)

    # Up to two retries, for two transient failures only: a missing export
    # and the flat-normal race. Flat-normal rate measured 2026-09-27:
    # 14 of 57 raw renders across the 19 cookbook graphs with a buffered
    # normal_map baked flat (mostly a graph's first, cold-cache render), and
    # m06 went flat twice in a row, so one retry was not enough.
    for _ in range(3):
        # Snapshot existing output files before render to detect fresh outputs
        before = _snapshot_pngs(outdir, basename)
        try:
            proc = _run_godot(cmd, 180)
        except _GodotTimeout:
            return RenderResult(ok=False, error="Godot render timed out after 180s")
        log_tail = _log_tail(proc)
        images = _collect_fresh_images(outdir, basename, before)

        if proc.returncode != 0:
            return RenderResult(ok=False, log_tail=log_tail,
                                error=f"Godot exited {proc.returncode}")
        if not images:
            # Also transient: an export occasionally exits 0 having written
            # nothing, and an identical re-run is fine.
            failure = "no PNG output produced (3 attempts)"
            continue
        bad = _undecodable(images)
        if bad:
            return RenderResult(ok=False, log_tail=log_tail, error=bad)
        if not _flat_normal(images, (proc.stdout or "") + (proc.stderr or "")):
            break
        failure = "normal map baked flat (Material Maker logged 'invalid shader'), 3 attempts"
    else:
        return RenderResult(ok=False, images=images, log_tail=log_tail, error=failure)

    _downsample(images, size)
    return RenderResult(ok=True, images=images, log_tail=log_tail)

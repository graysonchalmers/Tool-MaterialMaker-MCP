import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
from typing import Callable
from dataclasses import dataclass, field
from PIL import Image
from mm_mcp.config import Config, load_config
from mm_mcp.paths import PathNotAllowed, reject_path_fragment


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


def _clear_staging(directory: str) -> None:
    """Reset only the private directory owned by this render attempt."""
    for path in Path(directory).iterdir():
        if path.is_dir() and not path.is_symlink():
            shutil.rmtree(path)
        else:
            path.unlink()


def _validate_png(path: str, size: int | None = None) -> None:
    """Check PNG structure and decode pixels; headers alone miss truncated data.

    Accept PNG's native color modes, including 16-bit grayscale height maps.
    This checks file integrity and dimensions, not PBR channel semantics.
    """
    with Image.open(path) as image:
        if image.format != "PNG":
            raise ValueError(f"not a PNG: {os.path.basename(path)}")
        if size is not None and image.size != (size, size):
            raise ValueError(f"{os.path.basename(path)} has size {image.size}, expected {size}x{size}")
        image.verify()
    with Image.open(path) as image:
        image.load()


def _seed_export_products(outdir: str, stage: str, basename: str) -> dict[str, bytes]:
    """Let native prompt_overwrite rules see this material's existing products.

    Never seed PNGs: they must come from the current successful attempt. Native
    profiles protect engine materials/metadata but overwrite textures and scripts.
    Remember copied bytes so preserved files are not republished over human edits.
    """
    seeded = {}
    for path in Path(outdir).iterdir():
        if (path.is_file() and path.name.startswith((basename + ".", basename + "_"))
                and path.suffix.lower() not in {".png", ".ptex"}):
            copied = Path(stage) / path.name
            shutil.copy2(path, copied)
            seeded[path.name] = hashlib.sha256(copied.read_bytes()).digest()
    return seeded


def _rebase_export_paths(path: Path, stage: str, outdir: str) -> None:
    """Keep native text exports usable after moving them out of staging.

    In particular, Material Maker's UE5 Python template embeds absolute texture
    paths. Preserve binary products and relative references byte-for-byte.
    """
    if path.suffix.lower() not in {
        ".py", ".tres", ".tscn", ".mat", ".meta", ".json", ".gltf",
        ".mm2ue", ".gd", ".gdshader", ".shader",
    }:
        return
    raw = path.read_bytes()
    try:
        content = raw.decode("utf-8")
    except UnicodeDecodeError:
        return
    pairs = {(stage, outdir), (Path(stage).as_posix(), Path(outdir).as_posix())}
    pairs.update((json.dumps(old, ensure_ascii=False)[1:-1],
                  json.dumps(new, ensure_ascii=False)[1:-1]) for old, new in list(pairs))
    for old, new in sorted(pairs, key=lambda pair: len(pair[0]), reverse=True):
        content = content.replace(old, new)
    if content.encode("utf-8") != raw:
        path.write_bytes(content.encode("utf-8"))


def render(ptex: dict, size: int = 512, outdir: str | None = None,
           basename: str = "material", target: str = "Godot/Godot 4 Standard",
           cfg: Config | None = None) -> RenderResult:
    cfg = cfg or load_config()
    outdir = os.path.abspath(outdir or cfg.output_dir)
    log_tail = ""
    try:
        reject_path_fragment(basename)
        if not basename or basename == ".":
            raise ValueError("basename must be a nonempty file name")
        os.makedirs(outdir, exist_ok=True)
        with tempfile.TemporaryDirectory(prefix=".render-", dir=outdir) as stage:
            ptex_path = os.path.join(stage, basename + ".ptex")
            original_json = json.dumps(ptex)
            # Native image nodes expand this token against the loaded .ptex's
            # directory. Resolve it for staging, but keep the editable source
            # relative to its original output location when publishing below.
            render_json = original_json.replace(
                "%PROJECT_PATH%", json.dumps(Path(outdir).as_posix())[1:-1])
            seeded = {}

            def prepare_attempt():
                nonlocal seeded
                _clear_staging(stage)
                seeded = _seed_export_products(outdir, stage, basename)
                with open(ptex_path, "w", encoding="utf-8") as fh:
                    fh.write(render_json)

            cmd = _build_command(cfg, ptex_path, target, stage, size)
            proc = _run_godot(cmd, 180, before_attempt=prepare_attempt)
            log_tail = _log_tail(proc)
            if proc.returncode != 0:
                return RenderResult(ok=False, log_tail=log_tail,
                                    error=f"Godot exited {proc.returncode}")

            # Include empty candidates too, so a valid albedo cannot hide a
            # corrupt or zero-byte second channel. Old output files are absent.
            images = [p for p in sorted(Path(stage).iterdir())
                      if p.name.startswith(basename + "_") and p.suffix.lower() == ".png"]
            if not images:
                return RenderResult(ok=False, log_tail=log_tail, error="no PNG output produced")
            # Keep every native exporter product, including .tres/.mat files,
            # import metadata and engine helper scripts, alongside the .ptex.
            products = list(Path(stage).rglob("*"))
            if any(p.is_symlink() for p in products):
                raise ValueError("renderer produced a symbolic link")
            for path in images:
                # Dynamic native exporters copy source buffers at their own
                # dimensions; only baked maps use the requested square size.
                is_buffer = re.fullmatch(re.escape(basename) + r"_texture_\d+\.png",
                                         path.name, flags=re.IGNORECASE)
                expected_size = size if size > 0 and not is_buffer else None
                _validate_png(str(path), size=expected_size)
            Path(ptex_path).write_text(original_json, encoding="utf-8")
            for path in (p for p in products if p.is_file()):
                _rebase_export_paths(path, stage, outdir)
            for path in sorted(p for p in products if p.is_file()):
                previous = seeded.get(path.relative_to(stage).as_posix())
                if previous is not None and hashlib.sha256(path.read_bytes()).digest() == previous:
                    continue
                destination = Path(outdir) / path.relative_to(stage)
                destination.parent.mkdir(parents=True, exist_ok=True)
                os.replace(path, destination)
            return RenderResult(ok=True, images=[str(Path(outdir) / p.name) for p in images],
                                log_tail=log_tail)
    except _GodotTimeout:
        return RenderResult(ok=False, error="Godot render timed out after 180s")
    except (OSError, ValueError, SyntaxError, Image.DecompressionBombError, PathNotAllowed) as exc:
        return RenderResult(ok=False, log_tail=log_tail, error=str(exc))

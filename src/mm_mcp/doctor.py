"""Setup preflight for the Material Maker MCP server.

`require_valid` in config.py fails fast at the first missing prerequisite, which
is right for server startup but unhelpful when someone is trying to get set up:
they fix one thing, hit the next, fix that, hit the next. `check_setup` runs
every check and returns them all as data (never raising) so `mm-mcp --check` can
print one green/red checklist. Config and paths are the documented #1 first-run
failure for this tool, so this is the friendly front door to it.
"""

import os
from dataclasses import dataclass

from mm_mcp.catalog_builder import build_catalog
from mm_mcp.cookbook import list_cookbook
from mm_mcp.config import Config, load_config


@dataclass
class Check:
    name: str
    ok: bool
    detail: str


def check_setup(cfg: Config) -> list[Check]:
    """Run every setup check against a resolved Config. Never raises."""
    checks: list[Check] = []

    pp = cfg.project_path
    if not pp:
        checks.append(Check("MM_PROJECT_PATH", False,
                            "not set. Point MM_PROJECT_PATH at a Material Maker checkout."))
    elif not os.path.isdir(pp):
        checks.append(Check("MM_PROJECT_PATH", False, f"does not exist: '{pp}'"))
    else:
        checks.append(Check("MM_PROJECT_PATH", True, pp))

    if os.path.isdir(cfg.nodes_dir):
        checks.append(Check("node definitions", True, cfg.nodes_dir))
    else:
        checks.append(Check("node definitions", False,
                            f"missing: '{cfg.nodes_dir}' "
                            "(expected <project>/addons/material_maker/nodes)"))

    if os.path.isdir(cfg.examples_dir):
        checks.append(Check("examples", True, cfg.examples_dir))
    else:
        checks.append(Check("examples", False, f"missing: '{cfg.examples_dir}'"))

    if cfg.cookbook_dir and os.path.isdir(cfg.cookbook_dir):
        try:
            n = len(list_cookbook(cfg.cookbook_dir))
            checks.append(Check("cookbook", True, f"{n} materials in '{cfg.cookbook_dir}'"))
        except Exception as exc:  # optional feature: an unreadable dir is reported, never a crash
            checks.append(Check("cookbook", True,
                                f"could not read '{cfg.cookbook_dir}': {exc}"))
    else:
        checks.append(Check("cookbook", True,
                            f"not found at '{cfg.cookbook_dir or '<unset>'}' (optional: cookbook/ ships "
                            "with the git checkout; set MM_COOKBOOK_DIR to point at one)"))

    appid_path = os.path.join(pp, "steam_appid.txt") if pp else "steam_appid.txt"
    appid_hint = ("Without it (containing 4110830) Material Maker self-relaunches "
                  "and exits on headless render.")
    if not (pp and os.path.isfile(appid_path)):
        checks.append(Check("steam_appid.txt", False, f"missing: '{appid_path}'. {appid_hint}"))
    else:
        try:
            content = open(appid_path, encoding="utf-8").read().strip()
        except OSError as exc:
            content, read_err = "", str(exc)
        else:
            read_err = ""
        if "4110830" in content:
            checks.append(Check("steam_appid.txt", True, appid_path))
        elif read_err:
            checks.append(Check("steam_appid.txt", False, f"'{appid_path}' unreadable: {read_err}"))
        else:
            checks.append(Check("steam_appid.txt", False,
                                f"'{appid_path}' does not contain the expected app id "
                                f"4110830 (found '{content}'). {appid_hint}"))

    binary = cfg.console_binary if os.path.exists(cfg.console_binary) else cfg.godot_binary
    if not cfg.godot_binary:
        checks.append(Check("Godot binary", False,
                            "not set. Point MM_GODOT_BINARY at a Godot 4.7.x executable."))
    elif os.path.isfile(binary):
        note = " (console variant, captures render logs)" if binary != cfg.godot_binary else ""
        checks.append(Check("Godot binary", True, binary + note))
    else:
        checks.append(Check("Godot binary", False, f"does not exist: '{cfg.godot_binary}'"))

    # Check writability without creating anything: walk up to the nearest
    # existing ancestor and test that. The server makedirs the output dir at
    # render time; a preflight shouldn't have that side effect.
    probe = cfg.output_dir
    while probe and not os.path.isdir(probe):
        parent = os.path.dirname(probe)
        if parent == probe:
            break
        probe = parent
    if probe and os.path.isdir(probe) and os.access(probe, os.W_OK):
        checks.append(Check("output dir", True, cfg.output_dir))
    else:
        checks.append(Check("output dir", False, f"not writable: '{cfg.output_dir}'"))

    if os.path.isdir(cfg.nodes_dir):
        try:
            count = len(build_catalog(cfg.nodes_dir))
            checks.append(Check("node catalog", count > 0,
                                f"{count} node types" if count else "built 0 node types"))
        except Exception as exc:  # a broken checkout should read as a failed check, not a crash
            checks.append(Check("node catalog", False, f"failed to build: {exc}"))
    else:
        checks.append(Check("node catalog", False, "skipped (node definitions missing)"))

    if cfg.allowed_roots:
        checks.append(Check("MM_ALLOWED_ROOTS", True, os.pathsep.join(cfg.allowed_roots)))
    else:
        checks.append(Check("MM_ALLOWED_ROOTS", True,
                            "unset. Writes and reads are unrestricted; set it "
                            "(os.pathsep-separated dirs) to bound client paths."))

    return checks


def all_ok(checks: list[Check]) -> bool:
    return all(c.ok for c in checks)


def format_report(checks: list[Check]) -> str:
    lines = ["Material Maker MCP setup check", ""]
    for c in checks:
        lines.append(f"  [{'PASS' if c.ok else 'FAIL'}] {c.name}: {c.detail}")
    lines.append("")
    if all_ok(checks):
        lines.append("All checks passed. mm-mcp is ready.")
    else:
        n = sum(1 for c in checks if not c.ok)
        lines.append(f"{n} check(s) failed. Fix the above and re-run `mm-mcp --check`.")
    return "\n".join(lines)


def run_check(cfg: Config | None = None) -> int:
    """Print the preflight report. Returns 0 if all checks pass, else 1."""
    if cfg is None:
        cfg = load_config()
    checks = check_setup(cfg)
    print(format_report(checks))
    return 0 if all_ok(checks) else 1

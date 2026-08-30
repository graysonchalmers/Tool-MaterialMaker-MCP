import os
from dataclasses import dataclass
from dotenv import dotenv_values

# Config is env-var-first (an MCP client sets MM_* in its server "env" block).
# A .env file is a dev convenience only: looked up at MM_DOTENV if set, else in
# the current working directory. It is NOT anchored to the install location, so
# the same code works from a source checkout and from a `pip install` into
# site-packages. Path defaults are intentionally empty so a stranger with no
# config gets the actionable "set MM_PROJECT_PATH" message from require_valid()
# rather than a stale path baked in at build time.
_DEFAULTS = {
    "MM_GODOT_BINARY": "",
    "MM_PROJECT_PATH": "",
    "MM_OUTPUT_DIR": "",
    "MM_LIVE_OVERLAY_DIR": "",
    "MM_ALLOWED_ROOTS": "",
}


def _dotenv_path() -> str:
    override = os.environ.get("MM_DOTENV")
    if override:
        return override
    return os.path.join(os.getcwd(), ".env")


@dataclass
class Config:
    godot_binary: str
    console_binary: str
    project_path: str
    output_dir: str
    nodes_dir: str
    examples_dir: str
    live_overlay_dir: str
    allowed_roots: list[str]


def _resolve_console(godot_binary: str) -> str:
    if godot_binary.lower().endswith(".exe"):
        candidate = godot_binary[:-4] + "_console.exe"
        if os.path.exists(candidate):
            return candidate
    return godot_binary


def require_valid(cfg: "Config") -> None:
    """Fail fast with an actionable message if required config paths are
    missing or wrong. Called at MCP server startup (not from load_config()),
    per the design spec's Error handling section: "Missing config
    (MM_GODOT_BINARY / MM_PROJECT_PATH absent or wrong) fails fast at server
    start with an actionable message."
    """
    if not os.path.isdir(cfg.project_path):
        raise FileNotFoundError(
            f"MM_PROJECT_PATH does not exist: '{cfg.project_path}'. "
            "Set the MM_PROJECT_PATH environment variable (or .env entry) "
            "to a valid Material Maker project checkout."
        )
    if not os.path.isdir(cfg.nodes_dir):
        raise FileNotFoundError(
            f"Node catalog directory does not exist: '{cfg.nodes_dir}'. "
            "This is derived from MM_PROJECT_PATH "
            f"('{cfg.project_path}') + addons/material_maker/nodes; "
            "check that MM_PROJECT_PATH points at a valid Material Maker checkout."
        )
    binary = cfg.console_binary if os.path.exists(cfg.console_binary) else cfg.godot_binary
    if not os.path.isfile(binary):
        raise FileNotFoundError(
            f"Godot binary does not exist: '{binary}'. "
            "Set the MM_GODOT_BINARY environment variable (or .env entry) "
            "to a valid Godot executable path."
        )


def load_config(overrides: dict | None = None) -> Config:
    env = dict(_DEFAULTS)
    env.update({k: v for k, v in dotenv_values(_dotenv_path()).items() if v})
    env.update({k: v for k, v in os.environ.items() if k.startswith("MM_")})
    if overrides:
        env.update(overrides)
    project_path = env["MM_PROJECT_PATH"]
    output_dir = env["MM_OUTPUT_DIR"] or os.path.join(os.getcwd(), "output")
    live_overlay_dir = env["MM_LIVE_OVERLAY_DIR"] or os.path.join(os.getcwd(), "mm_live_overlay")
    allowed_roots = [p for p in env["MM_ALLOWED_ROOTS"].split(os.pathsep) if p]
    return Config(
        godot_binary=env["MM_GODOT_BINARY"],
        console_binary=_resolve_console(env["MM_GODOT_BINARY"]),
        project_path=project_path,
        output_dir=output_dir,
        nodes_dir=os.path.join(project_path, "addons", "material_maker", "nodes"),
        examples_dir=os.path.join(project_path, "material_maker", "examples"),
        live_overlay_dir=live_overlay_dir,
        allowed_roots=allowed_roots,
    )

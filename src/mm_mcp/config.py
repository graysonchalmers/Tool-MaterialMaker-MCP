import os
from dataclasses import dataclass
from dotenv import dotenv_values

_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

_DEFAULTS = {
    "MM_GODOT_BINARY": r"C:\Users\Grayson\AppData\Local\Godot\Godot_v4.7.1-stable_win64.exe",
    "MM_PROJECT_PATH": r"C:\Projects-local\z-Git\material-maker",
    "MM_OUTPUT_DIR": os.path.join(_PROJECT_ROOT, "output"),
}


@dataclass
class Config:
    godot_binary: str
    console_binary: str
    project_path: str
    output_dir: str
    nodes_dir: str
    examples_dir: str


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
    dotenv_path = os.path.join(_PROJECT_ROOT, ".env")
    env.update({k: v for k, v in dotenv_values(dotenv_path).items() if v})
    env.update({k: v for k, v in os.environ.items() if k.startswith("MM_")})
    if overrides:
        env.update(overrides)
    project_path = env["MM_PROJECT_PATH"]
    return Config(
        godot_binary=env["MM_GODOT_BINARY"],
        console_binary=_resolve_console(env["MM_GODOT_BINARY"]),
        project_path=project_path,
        output_dir=env["MM_OUTPUT_DIR"],
        nodes_dir=os.path.join(project_path, "addons", "material_maker", "nodes"),
        examples_dir=os.path.join(project_path, "material_maker", "examples"),
    )

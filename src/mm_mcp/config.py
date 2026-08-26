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

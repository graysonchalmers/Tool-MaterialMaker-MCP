"""Gate: opacity_tex is wired on the sf04 vent grille and the preview rig
honours albedo alpha. Graph-level only; the renders were checked by hand."""
import json
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
_OPACITY_PORT = 7  # material.mmg inputs: albedo, metallic, roughness, emission, normal, ao, depth, opacity, sss


def test_sf04_drives_opacity_and_flags_transparent():
    g = json.loads((_ROOT / "cookbook/scifi/sf04_vent_grille_panel.ptex").read_text(encoding="utf-8"))
    material = next(n for n in g["nodes"] if n["type"] == "material")
    assert material["parameters"].get("flags_transparent") is True
    assert any(c["to"] == material["name"] and c["to_port"] == _OPACITY_PORT
               for c in g["connections"])


def test_preview_rig_scissors_albedo_alpha_only_when_present():
    gd = (_ROOT / "src/mm_mcp/preview_project/preview.gd").read_text(encoding="utf-8")
    assert "detect_alpha() == Image.ALPHA_NONE" in gd  # opaque materials return early
    assert "TRANSPARENCY_ALPHA_SCISSOR" in gd
    assert gd.count("_apply_cutout(") >= 3  # def + triplanar material + heightmap sphere

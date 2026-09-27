from pathlib import Path
from PIL import Image
import pytest
from quality import _make_showcase as ms

ROOT = Path(__file__).resolve().parent.parent

def test_resolve_source_accepts_ptex_path():
    p = ms.resolve_source("saved_graphs/bricks_grayson_edit.ptex")
    assert p.is_file() and p.name == "bricks_grayson_edit.ptex"

def test_resolve_source_finds_cookbook_label():
    p = ms.resolve_source("s02_gray_granite")
    assert p.is_file() and p.parent.parent.name == "cookbook"

def test_resolve_source_missing_raises_naming_ident():
    with pytest.raises(FileNotFoundError, match="no_such_mat"):
        ms.resolve_source("no_such_mat")

def test_gallery_out_path_uses_stem():
    assert ms.gallery_out_path("s02_gray_granite").name == "s02_gray_granite.png"
    assert ms.gallery_out_path("saved_graphs/bricks_grayson_edit.ptex").name == "bricks_grayson_edit.png"

def test_montage_crops_and_concats(tmp_path):
    srcs = []
    for i, c in enumerate([(200, 0, 0), (0, 200, 0), (0, 0, 200)]):
        s = tmp_path / f"p{i}.png"; Image.new("RGB", (1024, 576), c).save(s); srcs.append(s)
    out = tmp_path / "hero.png"
    ms.montage(srcs, out, panel_w=683, panel_h=560)
    assert Image.open(out).size == (683 * 3, 560)

def test_downscale_gif_frames_preserves_aspect(tmp_path):
    fr = tmp_path / "f.png"; Image.new("RGB", (1024, 576)).save(fr)
    out = ms.downscale_gif_frames([fr], width=512)
    assert out[0].size == (512, 288)

def test_showcase_override_sets_s14_damp_on_a_copy():
    import json
    src = ms.resolve_source("s14_wet_river_stone")
    before = src.read_bytes()
    g = json.loads(before.decode("utf-8"))
    out = ms.apply_showcase_overrides(g, "s14_wet_river_stone")
    sub = next(n for n in out["nodes"] if n["name"] == "dry_layer")
    remote = next(n for n in sub["nodes"] if n["name"] == "gen_parameters")
    dryness = next(n for n in sub["nodes"] if n["name"] == "Dryness")
    assert sub["parameters"]["param0"] == 0.5
    assert remote["parameters"]["param0"] == 0.5
    assert dryness["parameters"]["color"] == 0.5
    # input dict and cookbook file untouched
    orig_sub = next(n for n in g["nodes"] if n["name"] == "dry_layer")
    assert orig_sub["parameters"]["param0"] == 0
    assert src.read_bytes() == before

def test_showcase_override_is_identity_for_unlisted_material():
    import json
    g = json.loads(ms.resolve_source("s07_cobblestone").read_text(encoding="utf-8"))
    assert ms.apply_showcase_overrides(g, "s07_cobblestone") == g

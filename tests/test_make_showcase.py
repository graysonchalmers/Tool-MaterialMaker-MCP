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

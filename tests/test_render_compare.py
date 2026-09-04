import os
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(_ROOT, "quality"))
from render_compare import grid_mean_abs_diff, renders_match

_GLASS_THUMB = os.path.join(_ROOT, "docs", "images", "cookbook-glass",
                             "gl01_frosted_glass.png")
_WOOD_THUMB = os.path.join(_ROOT, "docs", "images", "cookbook-wood",
                            "w03_painted_wood_siding.png")


def test_identical_file_matches_itself():
    assert renders_match(_GLASS_THUMB, _GLASS_THUMB)
    assert grid_mean_abs_diff(_GLASS_THUMB, _GLASS_THUMB) == 0.0


def test_different_materials_do_not_match():
    assert not renders_match(_GLASS_THUMB, _WOOD_THUMB, tolerance=3.0)

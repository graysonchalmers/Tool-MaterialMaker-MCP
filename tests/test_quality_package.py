"""quality/ is an importable package: no sys.path hacks anywhere, every
intra-package import is package-qualified, and the modules tests depend on
import cleanly by their package name."""
import importlib
import os
import re

import pytest

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_QUALITY = os.path.join(_ROOT, "quality")
_TESTS = os.path.join(_ROOT, "tests")

INTRA_MODULES = (
    "author", "author_helpers", "render_compare", "pngread", "promote_cookbook",
    "debug_swatches", "noise_gallery", "render_cookbook", "render_one",
)


def _py_files(folder):
    # Exclude this gate test's own file: its assertions quote the literal
    # strings ("sys.path.insert", bare module names) it forbids elsewhere,
    # so scanning itself would always self-match and never pass.
    return sorted(
        os.path.join(folder, f) for f in os.listdir(folder)
        if f.endswith(".py") and f not in ("__init__.py", "test_quality_package.py")
    )


def test_quality_is_a_package():
    assert os.path.isfile(os.path.join(_QUALITY, "__init__.py"))


@pytest.mark.parametrize("path", _py_files(_QUALITY) + _py_files(_TESTS))
def test_no_sys_path_hacks(path):
    src = open(path, encoding="utf-8").read()
    assert "sys.path" not in src, f"{os.path.relpath(path, _ROOT)} still edits sys.path"


@pytest.mark.parametrize("path", _py_files(_QUALITY) + _py_files(_TESTS))
def test_no_bare_intra_package_imports(path):
    src = open(path, encoding="utf-8").read()
    bare = re.findall(
        r"^\s*(?:from|import)\s+(" + "|".join(INTRA_MODULES) + r")\b(?!\.)",
        src, flags=re.M,
    )
    assert bare == [], f"{os.path.relpath(path, _ROOT)} imports {bare} by bare name; use quality.<module>"


@pytest.mark.parametrize("name", [
    "quality.author_helpers", "quality.promote_cookbook", "quality.render_compare",
    "quality.pngread", "quality.debug_swatches",
])
def test_package_modules_import_by_name(name):
    importlib.import_module(name)

"""Every cookbook builder takes the catalog as its one parameter, so main()
builds the catalog once and threads it through (the catalog build reads ~400
.mmg files; building it inside each builder was the pattern in three
stragglers). Also guards the BUILDERS contract the promote/--check baseline
relies on."""
import importlib
import inspect

import pytest

CATEGORIES = [
    "ceramic", "fabrics", "glass", "leather", "metal", "organics",
    "painted_metal", "plastics", "scifi", "stone", "terrain", "wood",
]


def _builders():
    for cat in CATEGORIES:
        mod = importlib.import_module(f"quality.cookbook_{cat}")
        for case_id, fn in mod.BUILDERS.items():
            yield pytest.param(cat, case_id, fn, id=f"{cat}/{case_id}")


@pytest.mark.parametrize("category,case_id,fn", list(_builders()))
def test_builder_takes_exactly_one_catalog_parameter(category, case_id, fn):
    params = list(inspect.signature(fn).parameters)
    assert params == ["catalog"], (
        f"quality/cookbook_{category}.py::{fn.__name__} has parameters {params}; "
        "expected exactly ('catalog',)"
    )

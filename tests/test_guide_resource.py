# tests/test_guide_resource.py
"""guide://authoring serves docs/AUTHORING.md through a pure reader."""
import os
from mm_mcp.server import read_authoring_guide, _authoring_guide_path


def test_authoring_guide_path_points_at_the_repo_doc():
    path = _authoring_guide_path()
    assert path.endswith(os.path.join("docs", "AUTHORING.md"))
    assert os.path.isfile(path)


def test_read_authoring_guide_returns_the_invariant_guide():
    text = read_authoring_guide()
    assert "## Scoring rubric" in text
    assert "param4=0" in text


def test_guide_keeps_invariants_and_drops_per_material_sections():
    text = read_authoring_guide()
    # invariants stay
    assert "## Scoring rubric" in text
    assert "## Authoring workflow" in text
    assert "## Noise vocabulary" in text
    assert "param4=0" in text
    # the topology-not-donor lesson was lifted up into the guide
    assert "topology" in text.lower()
    # per-material cookbook sections are gone (now cards)
    assert "## Fabric cookbook" not in text
    assert "## Leather cookbook" not in text
    assert "## Painted-metal cookbook" not in text
    # a pointer at the cards exists
    assert "cookbook/" in text

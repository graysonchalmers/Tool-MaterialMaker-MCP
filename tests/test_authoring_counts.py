"""AUTHORING.md's live noise-coverage line must match quality.node_usage_audit's
real output, the same convention tests/test_readme_counts.py uses for README.md."""
import os
import re

from quality.node_usage_audit import audit, _NOISE_PATTERN_NODES

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
with open(os.path.join(_ROOT, "docs", "AUTHORING.md"), encoding="utf-8") as fh:
    AUTHORING = fh.read()


def test_authoring_noise_coverage_line_matches_live_audit():
    m = re.search(
        r"as of this writing the cookbook uses (\d+) of (\d+) curated "
        r"noise/pattern generator types",
        AUTHORING,
    )
    assert m, (
        "AUTHORING.md's Noise vocabulary section must state "
        "'as of this writing the cookbook uses <N> of <M> curated "
        "noise/pattern generator types'"
    )
    report = audit()
    assert int(m.group(1)) == len(report["noise_used"])
    assert int(m.group(2)) == len(_NOISE_PATTERN_NODES)

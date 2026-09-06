"""Tolerance-based render comparison for the subgraph retrofit's regression
gate. Godot's headless render is not perfectly deterministic run to run (see
the render-orphan-contention history in this project's memory/HANDOFF), so
the gate is a small mean-absolute-difference tolerance, not byte-identity.
"""
from quality.pngread import Sampler

# Empirically, unrelated re-renders of an unchanged graph mostly differ by a
# mean per-channel delta well under 1.0 (out of 255), but this is not a hard
# ceiling: on 2026-09-06 one re-render of an unchanged graph
# (`t05_cracked_ice_normal`) measured 21.89 once and 0.0 on two further
# renders. A real content change (a different pattern or color) produces a
# mean delta well above this. Treat a single failure above TOLERANCE as a
# rerender first, a regression second.
TOLERANCE = 3.0


def grid_mean_abs_diff(path_a: str, path_b: str, n: int = 16) -> float:
    sa, sb = Sampler.load(path_a), Sampler.load(path_b)
    samples_a, samples_b = sa.grid(n), sb.grid(n)
    total = sum(abs(ca - cb)
                for pa, pb in zip(samples_a, samples_b)
                for ca, cb in zip(pa, pb))
    return total / (len(samples_a) * 3)


def renders_match(path_a: str, path_b: str, tolerance: float = TOLERANCE,
                   n: int = 16) -> bool:
    return grid_mean_abs_diff(path_a, path_b, n) <= tolerance

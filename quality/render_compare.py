"""Tolerance-based render comparison for the subgraph retrofit's regression
gate. Godot's headless render is not perfectly deterministic run to run (see
the render-orphan-contention history in this project's memory/HANDOFF), so
the gate is a small mean-absolute-difference tolerance, not byte-identity.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from pngread import Sampler

# Empirically, unrelated re-renders of an unchanged graph differ by a mean
# per-channel delta well under 1.0 (out of 255). A real content change
# (a different pattern or color) produces a mean delta well above this.
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

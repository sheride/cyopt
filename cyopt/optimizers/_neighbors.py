"""Shared neighbor/step utilities for single-point optimizers."""

from __future__ import annotations

from collections.abc import Callable

import numpy as np

from cyopt._types import DNA, Bounds

StepFunction = Callable[[DNA, Bounds, np.random.Generator], DNA]
"""Callable that proposes a new DNA from the current one, given bounds and an RNG."""


def random_single_flip(
    dna: DNA, bounds: Bounds, rng: np.random.Generator
) -> DNA:
    """Propose a neighbor by changing exactly one randomly chosen dimension.

    Picks a random dimension, then picks a random valid value for that
    dimension that differs from the current value. If the dimension has
    only one valid value (``lo == hi``), the original DNA is returned
    unchanged.

    Parameters
    ----------
    dna : DNA
        Current solution.
    bounds : Bounds
        Per-dimension ``(lo_inclusive, hi_inclusive)`` bounds.
    rng : numpy.random.Generator
        Random number generator for reproducibility.

    Returns
    -------
    DNA
        New solution differing in exactly one dimension (or identical if
        the chosen dimension has a single valid value).
    """
    i = int(rng.integers(0, len(dna)))
    lo, hi = bounds[i]

    if lo == hi:
        return dna  # only one valid value; can't flip

    new_val = int(rng.integers(lo, hi + 1))
    while new_val == dna[i]:
        new_val = int(rng.integers(lo, hi + 1))

    lst = list(dna)
    lst[i] = new_val
    return tuple(lst)

"""Shared step utilities and callable protocols for graph-local optimizers."""

from __future__ import annotations

from collections.abc import Callable, Iterable
from typing import TYPE_CHECKING

import numpy as np

from cyopt._types import DNA, Bounds, Node

if TYPE_CHECKING:
    from cyopt.spaces import GraphSpace


NeighborFunction = Callable[[Node], Iterable[Node]]
"""Callable that yields neighbors of a node.

Per D-07: no Bounds parameter. If bounds are needed, close over a TupleSpace
or subclass TupleSpace with a custom ``neighbors`` method.
"""

StepFunction = Callable[[Node, np.random.Generator], Node]
"""Callable that proposes a new node from the current one, given an RNG.

Per D-07: bounds are NOT part of this protocol. If a custom step function
needs bounds, close over a TupleSpace (or call ``space.bounds``) at
definition time.
"""

PerturbFunction = Callable[[Node, np.random.Generator], Node]
"""BasinHopping perturbation callable: (node, rng) -> new node."""

LocalMinimizeFunction = Callable[
    [Node, "GraphSpace", Callable[[Node], float]], Node
]
"""BasinHopping local-descent callable: (node, space, evaluate_fn) -> node.

The ``space`` argument lets the minimizer call ``space.neighbors(node)``
rather than hard-coding ``hamming_neighbors``. Matches the new 3-arg
``_greedy_descent`` signature in ``basin_hopping.py``.
"""


def random_single_flip(
    dna: DNA, bounds: Bounds, rng: np.random.Generator
) -> DNA:
    """Propose a neighbor by changing one randomly chosen dimension.

    Tuple-specific helper retained for internal use by MCMC/SA/BasinHopping
    default step functions, which wrap it in a closure capturing the
    space's bounds.

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
        return dna
    new_val = int(rng.integers(lo, hi + 1))
    while new_val == dna[i]:
        new_val = int(rng.integers(lo, hi + 1))
    lst = list(dna)
    lst[i] = new_val
    return tuple(lst)

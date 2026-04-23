"""TupleSpace: bounded-integer-tuple concrete SearchSpace."""
from __future__ import annotations

from collections.abc import Iterable, Sequence

import numpy as np

from cyopt.types import DNA, Bounds
from cyopt.spaces._graph import GraphSpace


class TupleSpace(GraphSpace):
    """Concrete search space of bounded integer tuples.

    Nodes are ``tuple[int, ...]`` values where each coordinate ``i`` lies
    in the inclusive range ``[bounds[i][0], bounds[i][1]]``. Neighbors
    are Hamming-distance-1 tuples -- i.e., all tuples differing in exactly
    one position.

    Parameters
    ----------
    bounds : Sequence[tuple[int, int]]
        Per-dimension ``(lo_inclusive, hi_inclusive)`` bounds.

    Attributes
    ----------
    bounds : Bounds
        Canonicalized tuple-of-tuples form of the input bounds.
    dim : int
        Number of coordinates (``len(bounds)``).
    """

    def __init__(self, bounds: Sequence[tuple[int, int]]) -> None:
        normalized: Bounds = tuple((int(lo), int(hi)) for lo, hi in bounds)
        for i, (lo, hi) in enumerate(normalized):
            if hi < lo:
                raise ValueError(
                    f"bounds[{i}] = ({lo}, {hi}): hi must be >= lo"
                )
        self._bounds: Bounds = normalized
        self._dim: int = len(normalized)

    @property
    def bounds(self) -> Bounds:
        """Per-dimension ``(lo_inclusive, hi_inclusive)`` bounds."""
        return self._bounds

    @property
    def dim(self) -> int:
        """Number of coordinates in a node tuple."""
        return self._dim

    def random(self, rng: np.random.Generator) -> DNA:
        """Uniformly sample a tuple of ints within bounds (hi inclusive).

        Parameters
        ----------
        rng : numpy.random.Generator
            RNG used for reproducibility.

        Returns
        -------
        DNA
            A random tuple of ints with one coord per dimension; each
            coord lies in the inclusive range ``[lo, hi]`` for its
            dimension.
        """
        return tuple(
            int(rng.integers(lo, hi + 1)) for lo, hi in self._bounds
        )

    def neighbors(self, node: DNA) -> Iterable[DNA]:
        """All Hamming-distance-1 tuples differing in exactly one coord.

        Matches the behavior of the legacy ``hamming_neighbors`` helper
        in :mod:`cyopt.optimizers.greedy_walk`.

        Parameters
        ----------
        node : DNA
            Current position; must have length ``self.dim``.

        Returns
        -------
        Iterable[DNA]
            All tuples in the space that differ from ``node`` in exactly
            one coordinate.

        Raises
        ------
        ValueError
            If ``len(node) != self.dim``.
        """
        if len(node) != self._dim:
            raise ValueError(
                f"node has {len(node)} coords, space has dim={self._dim}"
            )
        out: list[DNA] = []
        for i, (lo, hi) in enumerate(self._bounds):
            for val in range(lo, hi + 1):
                if val != node[i]:
                    neighbor = list(node)
                    neighbor[i] = val
                    out.append(tuple(neighbor))
        return out

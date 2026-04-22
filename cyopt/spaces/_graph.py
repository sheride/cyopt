"""GraphSpace: SearchSpace with a neighbor structure."""
from __future__ import annotations

from abc import abstractmethod
from collections.abc import Iterable
from typing import TYPE_CHECKING

from cyopt.spaces._base import SearchSpace

if TYPE_CHECKING:
    from cyopt._types import Node


class GraphSpace(SearchSpace):
    """A :class:`SearchSpace` equipped with a neighborhood function.

    Adds ``neighbors(node)`` on top of ``random(rng)``. Optimizers that
    rely on local exploration (GreedyWalk, BestFirstSearch, MCMC,
    SimulatedAnnealing, BasinHopping) target this protocol.
    """

    @abstractmethod
    def neighbors(self, node: "Node") -> "Iterable[Node]":
        """Yield the neighbors of ``node`` in the graph.

        Parameters
        ----------
        node : Node
            Current position.

        Returns
        -------
        Iterable[Node]
            Neighboring nodes (may be a list, generator, tuple, etc.).
        """
        ...

"""Abstract SearchSpace base class."""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import numpy as np

    from cyopt.types import Node


class SearchSpace(ABC):
    """Abstract base for all cyopt search spaces.

    The minimal protocol: draw a random element. Concrete subclasses
    add structure (e.g., :class:`GraphSpace` adds neighbor traversal;
    :class:`TupleSpace` adds coordinate access).

    Nodes MUST be hashable (required for cyopt's evaluation cache).
    """

    @abstractmethod
    def random(self, rng: "np.random.Generator") -> "Node":
        """Draw a uniformly random element of the space.

        Parameters
        ----------
        rng : numpy.random.Generator
            RNG used for reproducibility.

        Returns
        -------
        Node
            A hashable element of the search space.
        """
        ...

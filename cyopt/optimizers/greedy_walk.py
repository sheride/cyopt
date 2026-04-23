"""GreedyWalk optimizer -- navigates to local minima via neighbor exploration."""

from __future__ import annotations

from collections.abc import Callable

from cyopt.types import DNA
from cyopt.base import DiscreteOptimizer
from cyopt.optimizers.neighbors import NeighborFunction
from cyopt.spaces import GraphSpace


class GreedyWalk(DiscreteOptimizer):
    """Optimizer that greedily moves to improving neighbors.

    Starts from a random point and repeatedly moves to the best
    improving neighbor. When stuck at a local minimum, restarts from
    a new random point.

    Parameters
    ----------
    fitness_fn : Callable[[DNA], float]
        Objective function to minimize.
    space : GraphSpace
        Search space providing ``random(rng)`` and ``neighbors(node)``.
    neighbor_fn : NeighborFunction | None
        Custom neighbor generation function. When provided, shadows
        ``space.neighbors``. Defaults to ``space.neighbors`` which for
        :class:`~cyopt.spaces.TupleSpace` yields Hamming-distance-1
        neighbors.
    seed : int | None
        Random seed for reproducibility.
    cache_size : int | None
        Maximum cached evaluations. ``None`` for unbounded.
    record_history : bool
        If ``True``, record per-iteration info dicts.
    progress : bool
        If ``True``, show tqdm progress bar.
    """

    _neighbor_fn: NeighborFunction | None
    _use_space_neighbors: bool

    def __init__(
        self,
        fitness_fn: Callable[[DNA], float],
        space: GraphSpace,
        *,
        neighbor_fn: NeighborFunction | None = None,
        seed: int | None = None,
        cache_size: int | None = None,
        record_history: bool = False,
        progress: bool = False,
        callbacks: list | None = None,
    ) -> None:
        super().__init__(
            fitness_fn,
            space,
            seed=seed,
            cache_size=cache_size,
            record_history=record_history,
            progress=progress,
            callbacks=callbacks,
        )
        if neighbor_fn is not None:
            self._neighbor_fn = neighbor_fn
            self._use_space_neighbors = False
        else:
            self._neighbor_fn = None
            self._use_space_neighbors = True
        self._current: DNA | None = None
        self._current_value: float = float("inf")

    def _get_state(self) -> dict:
        """Return GreedyWalk-specific state for checkpointing."""
        return {
            'current': self._current,
            'current_value': self._current_value,
        }

    def _set_state(self, state: dict) -> None:
        """Restore GreedyWalk-specific state from checkpoint."""
        self._current = state['current']
        self._current_value = state['current_value']

    def _step(self, iteration: int) -> dict | None:
        """Take one greedy step: evaluate neighbors, move to best if improving.

        If no improving neighbor exists (local minimum), restart from a
        random point.

        Parameters
        ----------
        iteration : int
            Current iteration index.

        Returns
        -------
        dict | None
            ``{"position": dna, "value": val, "moved": bool}`` if recording.
        """
        # Initialize on first step
        if self._current is None:
            self._current = self._space.random(self._rng)
            self._current_value = self._evaluate(self._current)

        # Generate and evaluate all neighbors
        if self._use_space_neighbors:
            neighbors = list(self._space.neighbors(self._current))
        else:
            neighbors = list(self._neighbor_fn(self._current))
        best_neighbor: DNA | None = None
        best_neighbor_value = self._current_value

        for neighbor in neighbors:
            value = self._evaluate(neighbor)
            if value < best_neighbor_value:
                best_neighbor_value = value
                best_neighbor = neighbor

        # Move to best neighbor if improving, otherwise restart
        moved = False
        if best_neighbor is not None and best_neighbor_value < self._current_value:
            self._current = best_neighbor
            self._current_value = best_neighbor_value
            moved = True
        else:
            # Local minimum reached -- restart from random point
            self._current = self._space.random(self._rng)
            self._current_value = self._evaluate(self._current)

        if self._record_history:
            return {
                "position": self._current,
                "value": self._current_value,
                "moved": moved,
            }
        return None

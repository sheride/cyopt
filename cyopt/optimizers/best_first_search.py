"""BestFirstSearch optimizer -- local search with backtrack and frontier modes."""

from __future__ import annotations

import heapq
from collections.abc import Callable

from cyopt._types import DNA, Bounds
from cyopt.base import DiscreteOptimizer
from cyopt.optimizers.greedy_walk import NeighborFunction, hamming_neighbors


class BestFirstSearch(DiscreteOptimizer):
    """Optimizer that searches for improvements via systematic neighbor exploration.

    Two modes are available:

    - **backtrack** (default): Maintains a path from the starting point.
      Moves to the best neighbor (even non-improving). Detects oscillation
      and adds intermediate points to an avoid set. Random-restarts when
      stuck.
    - **frontier**: Classic best-first search using a min-heap priority
      queue. Pops the best unexplored candidate and expands its neighbors.

    Parameters
    ----------
    fitness_fn : Callable[[DNA], float]
        Objective function to minimize.
    bounds : Bounds
        Per-dimension ``(lo_inclusive, hi_inclusive)`` bounds.
    mode : str
        Search mode: ``"backtrack"`` or ``"frontier"``.
    neighbor_fn : NeighborFunction | None
        Custom neighbor generation function. Defaults to
        :func:`~cyopt.optimizers.greedy_walk.hamming_neighbors`.
    seed : int | None
        Random seed for reproducibility.
    cache_size : int | None
        Maximum cached evaluations. ``None`` for unbounded.
    record_history : bool
        If ``True``, record per-iteration info dicts.
    progress : bool
        If ``True``, show tqdm progress bar.

    Raises
    ------
    ValueError
        If *mode* is not ``"backtrack"`` or ``"frontier"``.
    """

    def __init__(
        self,
        fitness_fn: Callable[[DNA], float],
        bounds: Bounds,
        *,
        mode: str = "backtrack",
        neighbor_fn: NeighborFunction | None = None,
        seed: int | None = None,
        cache_size: int | None = None,
        record_history: bool = False,
        progress: bool = False,
        callbacks: list | None = None,
    ) -> None:
        if mode not in ("backtrack", "frontier"):
            raise ValueError(
                f"mode must be 'backtrack' or 'frontier', got {mode!r}"
            )
        super().__init__(
            fitness_fn,
            bounds,
            seed=seed,
            cache_size=cache_size,
            record_history=record_history,
            progress=progress,
            callbacks=callbacks,
        )
        self._neighbor_fn: NeighborFunction = neighbor_fn or hamming_neighbors
        self._mode = mode
        self._current: DNA | None = None
        self._current_value: float = float("inf")

        # Backtrack mode state
        self._path: list[DNA] = []
        self._avoid: set[DNA] = set()

        # Frontier mode state
        self._frontier: list[tuple[float, int, DNA]] = []
        self._visited: set[DNA] = set()
        self._counter: int = 0

    def _get_state(self) -> dict:
        """Return BestFirstSearch-specific state for checkpointing."""
        return {
            'mode': self._mode,
            'current': self._current,
            'current_value': self._current_value,
            'path': list(self._path),
            'avoid': list(self._avoid),
            'frontier': list(self._frontier),
            'visited': list(self._visited),
            'counter': self._counter,
        }

    def _set_state(self, state: dict) -> None:
        """Restore BestFirstSearch-specific state from checkpoint."""
        self._mode = state['mode']
        self._current = state['current']
        self._current_value = state['current_value']
        self._path = list(state['path'])
        self._avoid = set(state['avoid'])
        self._frontier = list(state['frontier'])
        self._visited = set(state['visited'])
        self._counter = state['counter']

    def _step(self, iteration: int) -> dict | None:
        """Execute one search step, dispatching to the selected mode.

        Parameters
        ----------
        iteration : int
            Current iteration index.

        Returns
        -------
        dict | None
            Per-iteration info if recording history.
        """
        if self._mode == "backtrack":
            return self._step_backtrack()
        return self._step_frontier()

    def _step_backtrack(self) -> dict | None:
        """One step of backtrack-mode search.

        Moves to the first improving neighbor (relaxed greedy). If none
        improve, moves to the best neighbor anyway. Detects oscillation
        (current == path[-2]) and adds the intermediate node to the avoid
        set.

        Returns
        -------
        dict | None
            Per-iteration info if recording history.
        """
        # Lazy init
        if self._current is None:
            self._current = self._random_dna()
            self._current_value = self._evaluate(self._current)
            self._path.append(self._current)

        # Generate and filter neighbors
        neighbors = self._neighbor_fn(self._current, self._bounds)
        path_set = set(self._path)
        valid = [
            n for n in neighbors
            if n not in self._avoid and n not in path_set
        ]

        if not valid:
            # No valid neighbors -- random restart
            self._path.clear()
            self._avoid.clear()
            self._current = self._random_dna()
            self._current_value = self._evaluate(self._current)
            self._path.append(self._current)
        else:
            # Evaluate all neighbors and sort by fitness
            scored = [
                (self._evaluate(neighbor), neighbor) for neighbor in valid
            ]
            scored.sort(key=lambda x: x[0])

            best_value, best_neighbor = scored[0]

            # Move to best neighbor (improving or not)
            self._path.append(self._current)
            self._current = best_neighbor
            self._current_value = best_value

            # Oscillation detection
            if (
                len(self._path) >= 2
                and self._current == self._path[-2]
            ):
                self._avoid.add(self._path[-1])
                self._path.pop()
                self._path.pop()

        if self._record_history:
            return {
                "position": self._current,
                "value": self._current_value,
                "path_length": len(self._path),
                "avoid_size": len(self._avoid),
            }
        return None

    def _step_frontier(self) -> dict | None:
        """One step of frontier-mode search.

        Expands the current node's neighbors into a priority queue, then
        pops the best unexplored candidate.

        Returns
        -------
        dict | None
            Per-iteration info if recording history.
        """
        # Lazy init
        if self._current is None:
            self._current = self._random_dna()
            self._current_value = self._evaluate(self._current)
            self._visited.add(self._current)

        # Expand neighbors of current
        neighbors = self._neighbor_fn(self._current, self._bounds)
        for neighbor in neighbors:
            if neighbor not in self._visited:
                value = self._evaluate(neighbor)
                heapq.heappush(
                    self._frontier, (value, self._counter, neighbor)
                )
                self._counter += 1
                self._visited.add(neighbor)

        # Pop best from frontier
        if self._frontier:
            value, _, candidate = heapq.heappop(self._frontier)
            self._current = candidate
            self._current_value = value
        else:
            # Frontier exhausted -- random restart (avoid revisiting)
            candidate = self._random_dna()
            for _ in range(100):
                if candidate not in self._visited:
                    break
                candidate = self._random_dna()
            self._current = candidate
            self._current_value = self._evaluate(candidate)
            self._visited.add(candidate)

        if self._record_history:
            return {
                "position": self._current,
                "value": self._current_value,
                "frontier_size": len(self._frontier),
                "visited_size": len(self._visited),
            }
        return None

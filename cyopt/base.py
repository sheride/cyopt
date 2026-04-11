"""Abstract base class for discrete optimizers."""

from __future__ import annotations

import time
from abc import ABC, abstractmethod
from collections.abc import Callable

import numpy as np
from tqdm import tqdm

from cyopt._cache import EvaluationCache
from cyopt._types import DNA, Bounds, Result


class DiscreteOptimizer(ABC):
    """Abstract base class for optimizers on bounded integer-tuple search spaces.

    Provides shared infrastructure: evaluation caching, reproducible seeding,
    best-so-far tracking, iteration history, and tqdm progress reporting.
    Concrete subclasses implement ``_step`` to define the optimization logic.

    Parameters
    ----------
    fitness_fn : Callable[[DNA], float]
        Objective function to minimize. Maps an integer tuple to a scalar.
    bounds : Bounds
        Per-dimension ``(lo_inclusive, hi_inclusive)`` bounds.
    seed : int | None
        Random seed for reproducibility. ``None`` for non-deterministic.
    cache_size : int | None
        Maximum number of cached evaluations. ``None`` for unbounded cache.
    record_history : bool
        If ``True``, collect per-iteration dicts in ``Result.full_history``.
    progress : bool
        If ``True``, display a tqdm progress bar during ``run()``.
    """

    def __init__(
        self,
        fitness_fn: Callable[[DNA], float],
        bounds: Bounds,
        seed: int | None = None,
        cache_size: int | None = None,
        record_history: bool = False,
        progress: bool = False,
    ) -> None:
        self._fitness_fn = fitness_fn
        self._bounds = bounds
        self._rng = np.random.default_rng(seed)
        self._cache = EvaluationCache(maxsize=cache_size)
        self._record_history = record_history
        self._progress = progress

        # Best-so-far tracking (minimization)
        self._best_solution: DNA | None = None
        self._best_value: float = float("inf")
        self._n_evaluations: int = 0

    def _evaluate(self, dna: DNA) -> float:
        """Evaluate fitness with caching and best-so-far tracking.

        Parameters
        ----------
        dna : DNA
            Candidate solution. Converted to ``tuple[int, ...]`` for
            consistent cache keys (Pitfall 4).

        Returns
        -------
        float
            Fitness value.
        """
        # Normalize key type for consistent cache lookups
        key = tuple(int(x) for x in dna)

        if key in self._cache:
            return self._cache[key]

        self._n_evaluations += 1
        value = self._fitness_fn(key)
        self._cache[key] = value

        # Update best-so-far (minimization: lower is better)
        if value < self._best_value:
            self._best_value = value
            self._best_solution = key

        return value

    def _random_dna(self) -> DNA:
        """Generate a random solution within bounds.

        Returns
        -------
        DNA
            A tuple of random integers, each within its dimension's bounds.
            Upper bounds are inclusive (Pitfall 1: rng.integers uses hi+1).
        """
        return tuple(
            int(self._rng.integers(lo, hi + 1)) for lo, hi in self._bounds
        )

    def run(self, n_iterations: int) -> Result:
        """Execute the optimization loop.

        Parameters
        ----------
        n_iterations : int
            Number of iterations (steps) to run.

        Returns
        -------
        Result
            Optimization result with best solution, history, and metadata.
        """
        history: list[float] = []
        full_history: list[dict] | None = [] if self._record_history else None

        t0 = time.perf_counter()

        iterator = range(n_iterations)
        if self._progress:
            iterator = tqdm(iterator, total=n_iterations, desc=type(self).__name__)

        for i in iterator:
            step_info = self._step(i)
            history.append(self._best_value)
            if self._record_history and full_history is not None and step_info:
                full_history.append(step_info)

        wall_time = time.perf_counter() - t0

        return Result(
            best_solution=self._best_solution,
            best_value=self._best_value,
            history=history,
            full_history=full_history,
            n_evaluations=self._n_evaluations,
            wall_time=wall_time,
        )

    @abstractmethod
    def _step(self, iteration: int) -> dict | None:
        """Execute one iteration of the optimization.

        Subclasses must implement this method. It should evaluate one or more
        candidates via ``self._evaluate(dna)`` and optionally return a dict
        of per-iteration statistics for ``full_history``.

        Parameters
        ----------
        iteration : int
            Current iteration index (0-based).

        Returns
        -------
        dict | None
            Per-iteration info dict for ``full_history``, or ``None``.
        """
        ...

"""Core type definitions for cyopt."""

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

DNA = tuple[int, ...]
"""A solution represented as a tuple of integers."""

Bounds = tuple[tuple[int, int], ...]
"""Per-dimension (lo_inclusive, hi_inclusive) bounds for the search space."""

FitnessFunction = Callable[[DNA], float]
"""A callable that maps a DNA tuple to a scalar fitness value."""

CallbackInfo = dict[str, Any]
"""Info dict passed to callbacks: iteration, best_value, best_solution, n_evaluations, wall_time."""

Callback = Callable[[CallbackInfo], bool | None]
"""Callback function. Receives iteration info dict. Return True to trigger early stopping."""


@dataclass(frozen=True)
class Result:
    """Immutable result of an optimization run.

    Parameters
    ----------
    best_solution : DNA
        The best solution found during the optimization.
    best_value : float
        The fitness value of the best solution.
    history : list[float]
        Best-so-far fitness value at each iteration.
    full_history : list[dict] | None
        Per-iteration statistics (if ``record_history=True``), else ``None``.
    n_evaluations : int
        Total number of unique fitness function evaluations.
    wall_time : float
        Wall-clock time in seconds for the optimization run.
    """

    best_solution: DNA
    best_value: float
    history: list[float]
    full_history: list[dict] | None
    n_evaluations: int
    wall_time: float

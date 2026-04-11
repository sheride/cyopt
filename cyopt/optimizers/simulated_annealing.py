"""SimulatedAnnealing optimizer -- temperature-driven stochastic search."""

from __future__ import annotations

from collections.abc import Callable

import numpy as np

from cyopt._types import DNA, Bounds
from cyopt.base import DiscreteOptimizer
from cyopt.optimizers._neighbors import StepFunction, random_single_flip


class SimulatedAnnealing(DiscreteOptimizer):
    """Simulated annealing optimizer with exponential cooling schedule.

    Uses the cooling schedule ``T = t_max * (t_min / t_max) ** frac`` where
    ``frac = step_count / (n_iterations - 1)``, clamped to [0, 1]. The step
    count accumulates across consecutive ``run()`` calls so cooling
    continues from where it left off.

    Parameters
    ----------
    fitness_fn : Callable[[DNA], float]
        Objective function to minimize.
    bounds : Bounds
        Per-dimension ``(lo_inclusive, hi_inclusive)`` bounds.
    n_iterations : int
        Total number of iterations for the cooling schedule. The
        temperature reaches ``t_min`` at this step count.
    t_max : float
        Starting (maximum) temperature.
    t_min : float
        Final (minimum) temperature. Must satisfy ``0 < t_min < t_max``.
    step_fn : StepFunction | None
        Custom proposal function ``(dna, bounds, rng) -> DNA``. Defaults
        to :func:`~cyopt.optimizers._neighbors.random_single_flip`.
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
        If temperature or iteration constraints are violated.
    """

    def __init__(
        self,
        fitness_fn: Callable[[DNA], float],
        bounds: Bounds,
        *,
        n_iterations: int = 1000,
        t_max: float = 1.0,
        t_min: float = 1e-8,
        step_fn: StepFunction | None = None,
        seed: int | None = None,
        cache_size: int | None = None,
        record_history: bool = False,
        progress: bool = False,
    ) -> None:
        if n_iterations <= 0:
            raise ValueError(
                f"n_iterations must be positive, got {n_iterations}"
            )
        if t_max <= 0:
            raise ValueError(f"t_max must be positive, got {t_max}")
        if t_min <= 0:
            raise ValueError(f"t_min must be positive, got {t_min}")
        if t_min >= t_max:
            raise ValueError(
                f"t_min must be less than t_max, got t_min={t_min}, t_max={t_max}"
            )
        super().__init__(
            fitness_fn,
            bounds,
            seed=seed,
            cache_size=cache_size,
            record_history=record_history,
            progress=progress,
        )
        self._n_iterations = n_iterations
        self._t_max = t_max
        self._t_min = t_min
        self._step_fn: StepFunction = step_fn or random_single_flip
        self._current: DNA | None = None
        self._current_value: float = float("inf")
        self._step_count: int = 0

    def _step(self, iteration: int) -> dict | None:
        """Execute one simulated annealing step with temperature-dependent acceptance.

        Parameters
        ----------
        iteration : int
            Current iteration index.

        Returns
        -------
        dict | None
            Per-iteration info dict with position, value, temperature,
            and accepted flag if recording history.
        """
        # Lazy init
        if self._current is None:
            self._current = self._random_dna()
            self._current_value = self._evaluate(self._current)

        # Exponential cooling schedule
        frac = min(1.0, self._step_count / max(1, self._n_iterations - 1))
        temperature = self._t_max * (self._t_min / self._t_max) ** frac

        # Propose and evaluate
        proposal = self._step_fn(self._current, self._bounds, self._rng)
        proposal_value = self._evaluate(proposal)

        # Metropolis acceptance
        delta = proposal_value - self._current_value
        accepted = delta < 0 or self._rng.random() < np.exp(
            -delta / temperature
        )

        if accepted:
            self._current = proposal
            self._current_value = proposal_value

        self._step_count += 1

        if self._record_history:
            return {
                "position": self._current,
                "value": self._current_value,
                "temperature": temperature,
                "accepted": bool(accepted),
            }
        return None

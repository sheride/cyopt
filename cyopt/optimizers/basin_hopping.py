"""BasinHopping optimizer -- global optimization via perturb + local minimize + Metropolis acceptance.

Implements the basin-hopping algorithm on discrete (integer-tuple) search spaces.
Unlike SciPy's ``basinhopping`` (which assumes continuous space), this implementation
operates directly on bounded integer tuples with a greedy-descent local minimizer.
"""

from __future__ import annotations

from collections.abc import Callable

import numpy as np

from cyopt._types import DNA, Bounds
from cyopt.base import DiscreteOptimizer
from cyopt.optimizers._neighbors import random_single_flip
from cyopt.optimizers.greedy_walk import hamming_neighbors


# ---------------------------------------------------------------------------
# Default local minimizer
# ---------------------------------------------------------------------------

def _greedy_descent(
    dna: DNA,
    bounds: Bounds,
    evaluate_fn: Callable[[DNA], float],
) -> DNA:
    """Steepest-descent local minimizer on integer-tuple space.

    From the starting point, repeatedly moves to the best improving
    Hamming-distance-1 neighbor. Terminates when no neighbor improves
    the current value (local minimum reached) or after 100 iterations.

    Parameters
    ----------
    dna : DNA
        Starting point for local minimization.
    bounds : Bounds
        Per-dimension ``(lo_inclusive, hi_inclusive)`` bounds.
    evaluate_fn : Callable[[DNA], float]
        Evaluation function (typically ``self._evaluate``).

    Returns
    -------
    DNA
        Local minimum found by greedy descent.
    """
    current = dna
    current_value = evaluate_fn(current)

    for _ in range(100):
        neighbors = hamming_neighbors(current, bounds)
        best_neighbor: DNA | None = None
        best_value = current_value

        for neighbor in neighbors:
            val = evaluate_fn(neighbor)
            if val < best_value:
                best_value = val
                best_neighbor = neighbor

        if best_neighbor is None:
            break  # local minimum

        current = best_neighbor
        current_value = best_value

    return current


# ---------------------------------------------------------------------------
# BasinHopping optimizer
# ---------------------------------------------------------------------------

class BasinHopping(DiscreteOptimizer):
    """Global optimizer using perturb + local minimize + Metropolis acceptance.

    At each step, the current solution is randomly perturbed, then locally
    minimized via greedy descent. The resulting local minimum is accepted
    or rejected using the Metropolis criterion, allowing the search to
    escape shallow local minima while preferring deeper basins.

    Parameters
    ----------
    fitness_fn : Callable[[DNA], float]
        Objective function to minimize.
    bounds : Bounds
        Per-dimension ``(lo_inclusive, hi_inclusive)`` bounds.
    temperature : float
        Metropolis temperature controlling acceptance probability.
        Must be > 0. Higher values accept more uphill moves.
    n_perturbations : int
        Number of random single-flips applied per perturbation step
        when using the default perturbation function.
    local_minimize_fn : Callable[[DNA, Bounds, Callable], DNA] | None
        Custom local minimizer. Signature:
        ``local_minimize_fn(dna, bounds, evaluate_fn) -> DNA``.
        Defaults to :func:`_greedy_descent`.
    perturb_fn : Callable[[DNA, Bounds, np.random.Generator], DNA] | None
        Custom perturbation function. Signature:
        ``perturb_fn(dna, bounds, rng) -> DNA``.
        Defaults to :func:`random_single_flip` applied ``n_perturbations``
        times in sequence.
    seed : int | None
        Random seed for reproducibility.
    cache_size : int | None
        Maximum cached evaluations.
    record_history : bool
        If ``True``, record per-iteration info dicts.
    progress : bool
        If ``True``, show tqdm progress bar.
    """

    def __init__(
        self,
        fitness_fn: Callable[[DNA], float],
        bounds: Bounds,
        *,
        temperature: float = 1.0,
        n_perturbations: int = 1,
        local_minimize_fn: Callable[[DNA, Bounds, Callable[[DNA], float]], DNA] | None = None,
        perturb_fn: Callable[[DNA, Bounds, np.random.Generator], DNA] | None = None,
        seed: int | None = None,
        cache_size: int | None = None,
        record_history: bool = False,
        progress: bool = False,
    ) -> None:
        if temperature <= 0:
            raise ValueError(
                f"temperature must be > 0, got {temperature}"
            )

        super().__init__(
            fitness_fn, bounds,
            seed=seed, cache_size=cache_size,
            record_history=record_history, progress=progress,
        )

        self._temperature = temperature
        self._n_perturbations = n_perturbations
        self._local_minimize_fn = local_minimize_fn or _greedy_descent
        self._perturb_fn = perturb_fn  # None means use default
        self._current: DNA | None = None
        self._current_value: float = float("inf")

    def _step(self, iteration: int) -> dict | None:
        """Execute one basin-hopping step.

        1. Lazy-initialize from a random point, then local-minimize.
        2. Perturb the current solution.
        3. Local-minimize from the perturbed point.
        4. Accept or reject the new local minimum via Metropolis criterion.

        Parameters
        ----------
        iteration : int
            Current iteration index.

        Returns
        -------
        dict | None
            Per-iteration info if recording history.
        """
        # Lazy initialization
        if self._current is None:
            self._current = self._random_dna()
            self._evaluate(self._current)
            self._current = self._local_minimize_fn(
                self._current, self._bounds, self._evaluate,
            )
            self._current_value = self._evaluate(self._current)

        # Perturb
        if self._perturb_fn is not None:
            perturbed = self._perturb_fn(self._current, self._bounds, self._rng)
        else:
            # Default: apply random_single_flip n_perturbations times
            perturbed = self._current
            for _ in range(self._n_perturbations):
                perturbed = random_single_flip(perturbed, self._bounds, self._rng)

        # Local minimize from perturbed point
        local_min = self._local_minimize_fn(perturbed, self._bounds, self._evaluate)
        local_min_value = self._evaluate(local_min)

        # Metropolis acceptance
        delta = local_min_value - self._current_value
        accepted = False
        if delta < 0 or self._rng.random() < np.exp(-delta / self._temperature):
            self._current = local_min
            self._current_value = local_min_value
            accepted = True

        if self._record_history:
            return {
                "current": self._current,
                "current_value": self._current_value,
                "local_min": local_min,
                "local_min_value": local_min_value,
                "accepted": accepted,
                "temperature": self._temperature,
            }
        return None

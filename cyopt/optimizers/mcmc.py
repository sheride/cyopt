"""MCMC optimizer -- Metropolis-Hastings sampling on integer-tuple space."""

from __future__ import annotations

from collections.abc import Callable

import numpy as np

from cyopt._types import DNA, Bounds
from cyopt.base import DiscreteOptimizer
from cyopt.optimizers._neighbors import StepFunction, random_single_flip


class MCMC(DiscreteOptimizer):
    """Markov Chain Monte Carlo optimizer using Metropolis-Hastings acceptance.

    Proposes neighbors via a configurable step function and accepts them
    with probability ``min(1, exp(-delta / temperature))`` where ``delta``
    is the change in fitness (positive = worse for minimization).

    Parameters
    ----------
    fitness_fn : Callable[[DNA], float]
        Objective function to minimize.
    bounds : Bounds
        Per-dimension ``(lo_inclusive, hi_inclusive)`` bounds.
    temperature : float
        Temperature controlling acceptance probability. Higher values
        accept worse solutions more readily.
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
        If *temperature* is not positive.
    """

    def __init__(
        self,
        fitness_fn: Callable[[DNA], float],
        bounds: Bounds,
        *,
        temperature: float = 1.0,
        step_fn: StepFunction | None = None,
        seed: int | None = None,
        cache_size: int | None = None,
        record_history: bool = False,
        progress: bool = False,
        callbacks: list | None = None,
    ) -> None:
        if temperature <= 0:
            raise ValueError(
                f"temperature must be positive, got {temperature}"
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
        self._temperature = temperature
        self._step_fn: StepFunction = step_fn or random_single_flip
        self._current: DNA | None = None
        self._current_value: float = float("inf")

    def _get_state(self) -> dict:
        """Return MCMC-specific state for checkpointing."""
        return {
            'temperature': self._temperature,
            'current': self._current,
            'current_value': self._current_value,
        }

    def _set_state(self, state: dict) -> None:
        """Restore MCMC-specific state from checkpoint."""
        self._temperature = state['temperature']
        self._current = state['current']
        self._current_value = state['current_value']

    def _step(self, iteration: int) -> dict | None:
        """Execute one Metropolis-Hastings step.

        Proposes a neighbor, evaluates it, and accepts with probability
        determined by the Boltzmann criterion.

        Parameters
        ----------
        iteration : int
            Current iteration index.

        Returns
        -------
        dict | None
            Per-iteration info dict with position, value, and accepted
            flag if recording history.
        """
        # Lazy init
        if self._current is None:
            self._current = self._random_dna()
            self._current_value = self._evaluate(self._current)

        proposal = self._step_fn(self._current, self._bounds, self._rng)
        proposal_value = self._evaluate(proposal)

        delta = proposal_value - self._current_value
        accepted = delta < 0 or self._rng.random() < np.exp(
            -delta / self._temperature
        )

        if accepted:
            self._current = proposal
            self._current_value = proposal_value

        if self._record_history:
            return {
                "position": self._current,
                "value": self._current_value,
                "accepted": bool(accepted),
            }
        return None

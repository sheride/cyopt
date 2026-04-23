"""MCMC optimizer -- Metropolis-Hastings sampling on integer-tuple space."""

from __future__ import annotations

from collections.abc import Callable

import numpy as np

from cyopt.types import DNA
from cyopt.base import DiscreteOptimizer
from cyopt.optimizers._neighbors import StepFunction, random_single_flip
from cyopt.spaces import GraphSpace


class MCMC(DiscreteOptimizer):
    """Markov Chain Monte Carlo optimizer using Metropolis-Hastings acceptance.

    Proposes neighbors via a configurable step function and accepts them
    with probability ``min(1, exp(-delta / temperature))`` where ``delta``
    is the change in fitness (positive = worse for minimization).

    Parameters
    ----------
    fitness_fn : Callable[[DNA], float]
        Objective function to minimize.
    space : GraphSpace
        Search space providing ``random(rng)``. The default ``step_fn``
        requires a :class:`~cyopt.spaces.TupleSpace` (it closes over
        ``space.bounds``). For non-tuple spaces, supply a custom ``step_fn``.
    temperature : float
        Temperature controlling acceptance probability. Higher values
        accept worse solutions more readily.
    step_fn : StepFunction | None
        Custom proposal function ``(dna, rng) -> DNA``. Defaults to a
        closure over the space's bounds that calls
        :func:`~cyopt.optimizers._neighbors.random_single_flip`.
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
        space: GraphSpace,
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
            space,
            seed=seed,
            cache_size=cache_size,
            record_history=record_history,
            progress=progress,
            callbacks=callbacks,
        )
        self._temperature = temperature
        if step_fn is not None:
            self._step_fn: StepFunction = step_fn
        else:
            # Default wraps the tuple-specific helper with space bounds closed in.
            # Raises AttributeError on non-TupleSpace (expected).
            bounds = self._space.bounds
            self._step_fn = lambda node, rng: random_single_flip(
                node, bounds, rng
            )
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
            self._current = self._space.random(self._rng)
            self._current_value = self._evaluate(self._current)

        proposal = self._step_fn(self._current, self._rng)
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

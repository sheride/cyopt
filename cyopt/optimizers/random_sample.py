"""RandomSample optimizer -- evaluates random points and returns the best."""

from __future__ import annotations

from collections.abc import Callable

from cyopt._types import DNA
from cyopt.base import DiscreteOptimizer
from cyopt.spaces import TupleSpace


class RandomSample(DiscreteOptimizer):
    """Optimizer that evaluates random solutions and tracks the best.

    The simplest possible optimization strategy: uniformly sample random
    integer tuples within bounds, evaluate each, and return the best found.

    Parameters
    ----------
    fitness_fn : Callable[[DNA], float]
        Objective function to minimize.
    space : TupleSpace
        Bounded-integer-tuple search space.
    seed : int | None
        Random seed for reproducibility.
    cache_size : int | None
        Maximum cached evaluations. ``None`` for unbounded.
    record_history : bool
        If ``True``, record per-iteration ``{"sampled": dna, "value": val}``.
    progress : bool
        If ``True``, show tqdm progress bar.
    """

    def __init__(
        self,
        fitness_fn: Callable[[DNA], float],
        space: TupleSpace,
        *,
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

    def _get_state(self) -> dict:
        """Return optimizer-specific state (none for RandomSample)."""
        return {}

    def _set_state(self, state: dict) -> None:
        """Restore optimizer-specific state (no-op for RandomSample)."""
        pass

    def _step(self, iteration: int) -> dict | None:
        """Sample one random point and evaluate it.

        Parameters
        ----------
        iteration : int
            Current iteration index (unused by RandomSample).

        Returns
        -------
        dict | None
            ``{"sampled": dna, "value": value}`` if recording history.
        """
        dna = self._space.random(self._rng)
        value = self._evaluate(dna)

        if self._record_history:
            return {"sampled": dna, "value": value}
        return None

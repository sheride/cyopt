"""DifferentialEvolution optimizer -- wraps SciPy's public API with integer support.

Uses ``scipy.optimize.differential_evolution`` with the ``integrality``
parameter for native integer constraint handling. This is the clean,
public-API approach (no private SciPy internals).

Note: ``record_history`` and ``progress`` are accepted by the constructor
(via the base class) but DE does not produce ``full_history`` (always
``None``) and does not use tqdm (SciPy manages its own iteration loop).
"""

from __future__ import annotations

import time
from collections.abc import Callable

import numpy as np
from scipy.optimize import differential_evolution

from cyopt._types import DNA, Bounds, Result
from cyopt.base import DiscreteOptimizer


class DifferentialEvolution(DiscreteOptimizer):
    """Differential Evolution optimizer wrapping SciPy's public API.

    Delegates to ``scipy.optimize.differential_evolution`` with
    ``integrality=True`` for all dimensions, enabling native integer
    optimization without private API access.

    .. note::
        Unlike other optimizers, consecutive ``run()`` calls do **not**
        preserve the DE population. Each call restarts the evolutionary
        process from a fresh random population. The evaluation cache is
        preserved, so repeated evaluations of the same candidate are free.

    Parameters
    ----------
    fitness_fn : Callable[[DNA], float]
        Objective function to minimize.
    bounds : Bounds
        Per-dimension ``(lo_inclusive, hi_inclusive)`` bounds.
        Internally transformed to half-open ``(lo, hi+1)`` for SciPy.
    popsize : int
        Population size multiplier (actual pop = ``popsize * n_dims``).
    mutation : float | tuple[float, float]
        Mutation constant or ``(min, max)`` for dithering.
    recombination : float
        Recombination constant in ``[0, 1]``.
    strategy : str
        DE strategy (e.g. ``'best1bin'``, ``'rand1bin'``).
    seed : int | None
        Random seed for reproducibility.
    cache_size : int | None
        Maximum cached evaluations.
    record_history : bool
        Accepted for API consistency but DE always returns
        ``full_history=None``.
    progress : bool
        Accepted for API consistency but DE does not use tqdm.
    callbacks : list | None
        Optional list of callback functions invoked each generation.
    """

    def __init__(
        self,
        fitness_fn: Callable[[DNA], float],
        bounds: Bounds,
        *,
        popsize: int = 15,
        mutation: float | tuple[float, float] = (0.5, 1),
        recombination: float = 0.7,
        strategy: str = "best1bin",
        seed: int | None = None,
        cache_size: int | None = None,
        record_history: bool = False,
        progress: bool = False,
        callbacks: list | None = None,
    ) -> None:
        super().__init__(
            fitness_fn, bounds,
            seed=seed, cache_size=cache_size,
            record_history=record_history, progress=progress,
            callbacks=callbacks,
        )

        self._popsize = popsize
        self._mutation = mutation
        self._recombination = recombination
        self._strategy = strategy

    def _get_state(self) -> dict:
        """Return DE-specific state for checkpointing."""
        return {
            'popsize': self._popsize,
            'mutation': self._mutation,
            'recombination': self._recombination,
            'strategy': self._strategy,
        }

    def _set_state(self, state: dict) -> None:
        """Restore DE-specific state from checkpoint."""
        self._popsize = state['popsize']
        self._mutation = state['mutation']
        self._recombination = state['recombination']
        self._strategy = state['strategy']

    def _step(self, iteration: int) -> dict | None:
        """Not supported -- DE delegates to SciPy's internal loop.

        Raises
        ------
        NotImplementedError
            Always. Use :meth:`run` directly.
        """
        raise NotImplementedError(
            "DifferentialEvolution delegates to SciPy and cannot be stepped "
            "individually. Use run() directly."
        )

    def run(self, n_iterations: int) -> Result:
        """Run differential evolution for *n_iterations* generations.

        Parameters
        ----------
        n_iterations : int
            Maximum number of DE generations.

        Returns
        -------
        Result
            Optimization result. ``full_history`` is always ``None``.
        """
        history: list[float] = []

        def wrapped(x: np.ndarray) -> float:
            dna: DNA = tuple(int(xi) for xi in x)
            return self._evaluate(dna)

        def callback(xk: np.ndarray, convergence: float = 0) -> bool:
            history.append(self._best_value)
            if self._callbacks:
                cb_info = {
                    'iteration': len(history) - 1 + self._iteration_offset,
                    'best_value': self._best_value,
                    'best_solution': self._best_solution,
                    'n_evaluations': self._n_evaluations,
                    'wall_time': time.perf_counter() - t0,
                }
                for cb in self._callbacks:
                    if cb(cb_info) is True:
                        return True  # SciPy stops when callback returns True
            return False

        # CRITICAL: half-open bounds for integrality
        de_bounds = [(lo, hi + 1) for lo, hi in self._bounds]
        integrality = [True] * len(self._bounds)

        t0 = time.perf_counter()

        differential_evolution(
            wrapped,
            de_bounds,
            integrality=integrality,
            maxiter=n_iterations,
            rng=self._rng,
            popsize=self._popsize,
            mutation=self._mutation,
            recombination=self._recombination,
            strategy=self._strategy,
            callback=callback,
            tol=0,
            polish=False,
        )

        wall_time = time.perf_counter() - t0
        self._iteration_offset += len(history)

        if self._best_solution is None:
            raise RuntimeError(
                "No solution was evaluated during run(). "
                "Ensure n_iterations > 0."
            )

        return Result(
            best_solution=self._best_solution,
            best_value=self._best_value,
            history=history,
            full_history=None,
            n_evaluations=self._n_evaluations,
            wall_time=wall_time,
        )

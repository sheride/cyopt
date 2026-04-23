"""Abstract base class for discrete optimizers."""

from __future__ import annotations

import pickle
import time
from abc import ABC, abstractmethod
from collections.abc import Callable
from pathlib import Path

import numpy as np
from tqdm import tqdm

from cyopt._cache import EvaluationCache
from cyopt.checkpoint import (
    CHECKPOINT_VERSION,
    _deserialize_space,
    _migrate,
    _serialize_space,
)
from cyopt.types import DNA, Callback, Result
from cyopt.spaces import SearchSpace


class DiscreteOptimizer(ABC):
    """Abstract base class for optimizers on an arbitrary :class:`~cyopt.spaces.SearchSpace`.

    Provides shared infrastructure: evaluation caching, reproducible seeding,
    best-so-far tracking, iteration history, and tqdm progress reporting.
    Concrete subclasses implement ``_step`` to define the optimization logic.

    Parameters
    ----------
    fitness_fn : Callable[[DNA], float]
        Objective function to minimize. Maps an integer tuple to a scalar.
    space : SearchSpace
        The search space. Provides ``random(rng)`` (used for initialization)
        and, for :class:`~cyopt.spaces.GraphSpace` subclasses, ``neighbors(node)``
        (used by local optimizers).
    seed : int | None
        Random seed for reproducibility. ``None`` for non-deterministic.
    cache_size : int | None
        Maximum number of cached evaluations. ``None`` for unbounded cache.
    record_history : bool
        If ``True``, collect per-iteration dicts in ``Result.full_history``.
    progress : bool
        If ``True``, display a tqdm progress bar during ``run()``.
    callbacks : list[Callback] | None
        Optional list of callback functions invoked each iteration.
        Each receives a ``CallbackInfo`` dict. Return ``True`` to stop early.
    """

    def __init__(
        self,
        fitness_fn: Callable[[DNA], float],
        space: SearchSpace,
        seed: int | None = None,
        cache_size: int | None = None,
        record_history: bool = False,
        progress: bool = False,
        callbacks: list[Callback] | None = None,
    ) -> None:
        self._fitness_fn = fitness_fn
        self._space = space
        self._rng = np.random.default_rng(seed)
        self._cache = EvaluationCache(maxsize=cache_size)
        self._record_history = record_history
        self._progress = progress
        self._callbacks: list[Callback] = list(callbacks) if callbacks else []
        self._iteration_offset: int = 0

        # Bind any callback exposing a ``bind()`` method to this optimizer.
        # Duck-typed (not ``isinstance(cb, CheckpointCallback)``) so that
        # user-defined callback classes following the same ``bind(optimizer)``
        # contract are also bound without having to subclass
        # ``CheckpointCallback``. See ``CheckpointCallback.bind`` docstring
        # for the contract.
        for cb in self._callbacks:
            bind = getattr(cb, "bind", None)
            if callable(bind):
                bind(self)

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
            if self._record_history and full_history is not None and step_info is not None:
                full_history.append(step_info)

            if self._callbacks:
                cb_info = {
                    'iteration': self._iteration_offset + i,
                    'best_value': self._best_value,
                    'best_solution': self._best_solution,
                    'n_evaluations': self._n_evaluations,
                    'wall_time': time.perf_counter() - t0,
                }
                for cb in self._callbacks:
                    if cb(cb_info) is True:
                        wall_time = time.perf_counter() - t0
                        if self._best_solution is None:
                            raise RuntimeError(
                                "No solution was evaluated during run(). "
                                "Ensure n_iterations > 0 and _step() calls _evaluate()."
                            )
                        self._iteration_offset += i + 1
                        return Result(
                            best_solution=self._best_solution,
                            best_value=self._best_value,
                            history=history,
                            full_history=full_history,
                            n_evaluations=self._n_evaluations,
                            wall_time=wall_time,
                        )

        wall_time = time.perf_counter() - t0

        if self._best_solution is None:
            raise RuntimeError(
                "No solution was evaluated during run(). "
                "Ensure n_iterations > 0 and _step() calls _evaluate()."
            )

        self._iteration_offset += n_iterations
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

    # ------------------------------------------------------------------
    # Checkpoint / resume
    # ------------------------------------------------------------------

    def _get_common_state(self) -> dict:
        """Serialize base-class state to a plain dict."""
        space_kind, space_data = _serialize_space(self._space)
        return {
            '_checkpoint_version': CHECKPOINT_VERSION,
            '_class': type(self).__name__,
            '_module': type(self).__module__,
            'rng_state': self._rng.bit_generator.state,
            'cache_data': self._cache.to_list(),
            'cache_maxsize': self._cache._maxsize,
            'best_solution': self._best_solution,
            'best_value': self._best_value,
            'n_evaluations': self._n_evaluations,
            'iteration_offset': self._iteration_offset,
            'space_kind': space_kind,
            'space_data': space_data,
            'record_history': self._record_history,
            'progress': self._progress,
        }

    def _set_common_state(self, state: dict) -> None:
        """Restore base-class state from a plain dict."""
        self._rng.bit_generator.state = state['rng_state']
        self._cache = EvaluationCache.from_list(
            state['cache_data'], maxsize=state['cache_maxsize']
        )
        self._best_solution = state['best_solution']
        self._best_value = state['best_value']
        self._n_evaluations = state['n_evaluations']
        self._iteration_offset = state['iteration_offset']
        self._record_history = state.get('record_history', False)
        self._progress = state.get('progress', False)

    def _get_state(self) -> dict:
        """Return optimizer-specific state. Override in subclasses."""
        return {}

    def _set_state(self, state: dict) -> None:
        """Restore optimizer-specific state. Override in subclasses."""
        pass

    def save_checkpoint(self, path: str | Path) -> None:
        """Save optimizer state to a pickle file.

        Parameters
        ----------
        path : str or Path
            File path for the checkpoint.

        Notes
        -----
        Only load checkpoints from trusted sources. Pickle can execute
        arbitrary code during deserialization.
        """
        state = self._get_common_state()
        state['optimizer_state'] = self._get_state()
        with open(path, 'wb') as f:
            pickle.dump(state, f, protocol=pickle.HIGHEST_PROTOCOL)

    @classmethod
    def load_checkpoint(
        cls,
        path: str | Path,
        fitness_fn: Callable[[DNA], float],
        *,
        space: SearchSpace | None = None,
        callbacks: list | None = None,
        **kwargs,
    ) -> "DiscreteOptimizer":
        """Load optimizer state from a checkpoint file.

        Parameters
        ----------
        path : str or Path
            Path to checkpoint file.
        fitness_fn : Callable[[DNA], float]
            Fitness function (not serialized in checkpoints).
        space : SearchSpace | None
            Explicit search space override. Required when the checkpoint's
            ``space_kind`` is not a known reconstructible kind. Takes
            precedence over checkpoint-stored reconstruction data when
            supplied. Default ``None`` (auto-reconstruct from checkpoint).
        callbacks : list or None
            Callbacks for the restored optimizer.
        **kwargs
            Additional constructor arguments (e.g., ``seed`` is ignored
            since RNG state is restored from checkpoint).

        Returns
        -------
        DiscreteOptimizer
            A restored optimizer ready for continued optimization.

        Raises
        ------
        TypeError
            If the checkpoint was saved from a different optimizer class.
        ValueError
            If the checkpoint version is incompatible AND no migration path
            exists, or if the checkpoint's ``space_kind`` is unknown and no
            ``space=`` was supplied.
        """
        with open(path, 'rb') as f:
            state = pickle.load(f)  # noqa: S301

        version = state.get('_checkpoint_version', 0)
        if version != CHECKPOINT_VERSION:
            state = _migrate(state, version)

        saved_class = state.get('_class', '')
        if saved_class != cls.__name__:
            raise TypeError(
                f"Checkpoint was saved from {saved_class}, "
                f"but loading as {cls.__name__}"
            )

        # Resolve space: user override takes precedence, else auto-reconstruct.
        if space is None:
            kind = state['space_kind']
            data = state.get('space_data', {})
            try:
                space = _deserialize_space(kind, data)
            except ValueError as e:
                raise ValueError(
                    f"Cannot auto-reconstruct space_kind={kind!r} from "
                    f"checkpoint. Pass space= to load_checkpoint with the "
                    f"reconstructed instance. Original error: {e}"
                ) from e

        instance = cls(
            fitness_fn=fitness_fn,
            space=space,
            callbacks=callbacks,
            **kwargs,
        )
        instance._set_common_state(state)
        instance._set_state(state.get('optimizer_state', {}))
        return instance

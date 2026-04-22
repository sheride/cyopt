"""FRSTOptimizer wrapper and frst_optimizer factory function.

Connects the 8 generic discrete optimizers to FRST optimization via the
DNA encoding layer. Users interact through the ``frst_optimizer()`` factory
which returns an ``FRSTOptimizer`` with a ``.run()`` method.
"""

from __future__ import annotations

from cyopt.frst._result import FRSTResult
from cyopt.spaces import TupleSpace


class FRSTOptimizer:
    """Wrapper connecting a generic DiscreteOptimizer to FRST optimization.

    Users should create instances via the :func:`frst_optimizer` factory
    function rather than calling this constructor directly.

    Parameters
    ----------
    poly : Polytope
        A reflexive polytope from CYTools.
    target : callable
        Target function. Receives a CalabiYau (or Triangulation if
        ``target_mode='triangulation'``) and returns either a float or
        a ``(float, ancillary_data)`` tuple. Lower values are better
        (minimisation).
    optimizer_cls : type
        A DiscreteOptimizer subclass (e.g., ``GA``, ``RandomSample``).
    target_mode : str
        ``'cy'`` (default): target receives CalabiYau.
        ``'triangulation'``: target receives Triangulation.
    penalty : float
        Fitness penalty for DNA that does not produce a valid FRST
        (non-solid cone). Default ``float('inf')``.
    seed : int or None
        Random seed for reproducibility.
    cache_size : int or None
        Maximum number of cached fitness evaluations.
    record_history : bool
        If True, collect per-iteration statistics.
    progress : bool
        If True, display a tqdm progress bar.
    **optimizer_kwargs
        Additional keyword arguments passed to the optimizer constructor.
    """

    def __init__(
        self,
        poly,
        target,
        optimizer_cls,
        target_mode: str = "cy",
        penalty: float = float("inf"),
        seed: int | None = None,
        cache_size: int | None = None,
        record_history: bool = False,
        progress: bool = False,
        **optimizer_kwargs,
    ):
        self._poly = poly
        self._target = target
        self._target_mode = target_mode
        self._ancillary_data: dict = {}

        # Ensure polytope is prepped for DNA encoding
        poly.prep_for_optimizers()

        # Build fitness function that bridges target -> DNA -> float
        fitness_fn = self._make_fitness(penalty)

        # Instantiate the underlying generic optimizer
        self._optimizer = optimizer_cls(
            fitness_fn=fitness_fn,
            space=TupleSpace(poly._cyopt_bounds),
            seed=seed,
            cache_size=cache_size,
            record_history=record_history,
            progress=progress,
            **optimizer_kwargs,
        )

    def _make_fitness(self, penalty: float):
        """Create fitness function bridging target(CY/Triang) -> DNA -> float.

        Parameters
        ----------
        penalty : float
            Value returned when DNA does not produce a valid FRST.

        Returns
        -------
        callable
            Fitness function compatible with DiscreteOptimizer.
        """
        poly = self._poly
        target = self._target
        target_mode = self._target_mode
        ancillary = self._ancillary_data

        def fitness(dna):
            triang = poly.dna_to_frst(dna)
            if triang is None:
                return penalty  # non-solid cone

            if target_mode == "cy":
                obj = triang.get_cy()
            else:
                obj = triang

            result = target(obj)

            # Support target returning (value, ancillary_data) or just value.
            if isinstance(result, tuple) and len(result) == 2:
                value, anc = result
                value = float(value)  # coerce for consistency with else branch
                ancillary[dna] = anc
            else:
                value = float(result)

            return value

        return fitness

    @property
    def optimizer(self):
        """Access the underlying generic DiscreteOptimizer instance."""
        return self._optimizer

    @property
    def ancillary_data(self) -> dict:
        """DNA -> ancillary data mapping from target evaluations."""
        return self._ancillary_data

    def run(self, n_iterations: int) -> FRSTResult:
        """Run the FRST optimization.

        Parameters
        ----------
        n_iterations : int
            Number of optimizer iterations to execute.

        Returns
        -------
        FRSTResult
            Result with decoded ``best_triangulation``, ``best_cy``, and
            un-negated ``best_value``.
        """
        raw_result = self._optimizer.run(n_iterations)

        best_dna = raw_result.best_solution
        best_triang = self._poly.dna_to_frst(best_dna)

        best_cy = None
        if self._target_mode == "cy" and best_triang is not None:
            best_cy = best_triang.get_cy()

        return FRSTResult(
            result=raw_result,
            best_triangulation=best_triang,
            best_cy=best_cy,
            ancillary_data=dict(self._ancillary_data),
        )


def frst_optimizer(poly, target, optimizer=None, target_mode: str = "cy", **kwargs):
    """Factory function to create an FRST optimizer.

    This is the primary user-facing API for FRST optimization. It creates
    an :class:`FRSTOptimizer` that wraps a generic optimizer and connects
    it to the DNA encoding layer.

    Parameters
    ----------
    poly : Polytope
        A reflexive polytope from CYTools.
    target : callable
        Target function: ``target(cy) -> float`` or
        ``target(cy) -> (float, ancillary_dict)``.
        Lower values are better (minimisation).
    optimizer : type[DiscreteOptimizer], optional
        Optimizer class to use. Default: ``GA``.
    target_mode : str
        ``'cy'`` (default): target receives CalabiYau.
        ``'triangulation'``: target receives Triangulation.
    **kwargs
        Passed to :class:`FRSTOptimizer` (``seed``, ``cache_size``,
        ``progress``, and optimizer-specific kwargs like
        ``population_size``).

    Returns
    -------
    FRSTOptimizer
        Wrapper with a ``.run(n_iterations)`` method returning
        :class:`~cyopt.frst._result.FRSTResult`.

    Examples
    --------
    >>> from cyopt.frst import frst_optimizer
    >>> wrapper = frst_optimizer(poly, lambda cy: float(cy.h11()))
    >>> result = wrapper.run(10)
    >>> print(result.best_value)
    """
    if optimizer is None:
        from cyopt.optimizers.ga import GA

        optimizer = GA
    return FRSTOptimizer(poly, target, optimizer, target_mode=target_mode, **kwargs)

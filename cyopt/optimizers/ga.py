"""Genetic Algorithm optimizer with composable operators.

Provides tournament, roulette-wheel, and ranked selection; n-point and uniform
crossover; random k-point mutation; and elitist survival.  Operators can be
specified as strings, dicts (with parameters), or callables (D-05, D-06).
"""

from __future__ import annotations

from collections.abc import Callable

import numpy as np

from cyopt._types import DNA, Bounds
from cyopt.base import DiscreteOptimizer


# ---------------------------------------------------------------------------
# Selection operators
# ---------------------------------------------------------------------------

def tournament_selection(
    population: np.ndarray,
    weights: np.ndarray,
    rng: np.random.Generator,
    *,
    k: int = 3,
) -> tuple[np.ndarray, np.ndarray]:
    """Select two parents via tournament selection.

    For each parent, pick *k* random individuals and return the one with the
    highest selection weight.
    """
    parents = []
    for _ in range(2):
        indices = rng.integers(0, len(population), size=k)
        best_idx = indices[np.argmax(weights[indices])]
        parents.append(population[best_idx].copy())
    return parents[0], parents[1]


def roulette_wheel_selection(
    population: np.ndarray,
    weights: np.ndarray,
    rng: np.random.Generator,
) -> tuple[np.ndarray, np.ndarray]:
    """Select two parents with probability proportional to selection weight."""
    indices = rng.choice(len(population), size=2, p=weights, replace=True)
    return population[indices[0]].copy(), population[indices[1]].copy()


def ranked_selection(
    population: np.ndarray,
    weights: np.ndarray,
    rng: np.random.Generator,
) -> tuple[np.ndarray, np.ndarray]:
    """Select two parents with probability proportional to rank.

    Best individual (highest weight) gets rank N, worst gets rank 1.
    """
    n = len(population)
    order = np.argsort(weights)  # ascending: worst first
    ranks = np.empty(n, dtype=float)
    # order[0] is worst (rank 1), order[-1] is best (rank N)
    ranks[order] = np.arange(1, n + 1, dtype=float)
    probs = ranks / ranks.sum()
    indices = rng.choice(n, size=2, p=probs, replace=True)
    return population[indices[0]].copy(), population[indices[1]].copy()


# ---------------------------------------------------------------------------
# Crossover operators
# ---------------------------------------------------------------------------

def npoint_crossover(
    parents: np.ndarray,
    rng: np.random.Generator,
    *,
    n: int = 1,
) -> tuple[np.ndarray, np.ndarray]:
    """N-point crossover producing two children from two parents.

    Parameters
    ----------
    parents : np.ndarray
        Shape ``(2, n_genes)``.
    rng : np.random.Generator
    n : int
        Number of crossover points (default 1).
    """
    length = parents.shape[1]
    # Choose n unique cut points in [1, length-1), then sort
    points = np.sort(rng.choice(np.arange(1, length), size=min(n, length - 1), replace=False))

    child1 = parents[0].copy()
    child2 = parents[1].copy()

    swap = False
    prev = 0
    for pt in points:
        if swap:
            child1[prev:pt] = parents[1][prev:pt]
            child2[prev:pt] = parents[0][prev:pt]
        prev = pt
        swap = not swap
    # Handle the last segment
    if swap:
        child1[prev:] = parents[1][prev:]
        child2[prev:] = parents[0][prev:]

    return child1, child2


def uniform_crossover(
    parents: np.ndarray,
    rng: np.random.Generator,
) -> tuple[np.ndarray, np.ndarray]:
    """Uniform crossover: swap each gene with probability 0.5."""
    mask = rng.random(parents.shape[1]) < 0.5
    child1 = parents[0].copy()
    child2 = parents[1].copy()
    child1[mask] = parents[1][mask]
    child2[mask] = parents[0][mask]
    return child1, child2


# ---------------------------------------------------------------------------
# Mutation operator
# ---------------------------------------------------------------------------

def random_mutation(
    dna: np.ndarray,
    bounds: Bounds,
    rng: np.random.Generator,
    *,
    k: int = 1,
) -> np.ndarray:
    """Mutate exactly *k* random positions to new values within bounds."""
    mutated = dna.copy()
    positions = rng.choice(len(dna), size=k, replace=False)
    for pos in positions:
        lo, hi = bounds[pos]
        mutated[pos] = rng.integers(lo, hi + 1)
    return mutated


# ---------------------------------------------------------------------------
# Operator registries
# ---------------------------------------------------------------------------

_SELECTION_REGISTRY: dict[str, Callable] = {
    "tournament": tournament_selection,
    "roulette_wheel": roulette_wheel_selection,
    "ranked": ranked_selection,
}

_CROSSOVER_REGISTRY: dict[str, Callable] = {
    "npoint": npoint_crossover,
    "uniform": uniform_crossover,
}


# ---------------------------------------------------------------------------
# Population-level fitness functions (target/fitness mode)
# ---------------------------------------------------------------------------

def fitness_inverse_square(target_values: np.ndarray, *, mu: float) -> np.ndarray:
    """Inverse-square fitness: ``(x - mu)**-2``.

    Peaks sharply at *mu*.  Used in arXiv:2405.08871 for volume maximisation.
    """
    return (target_values - mu) ** -2


def fitness_gaussian(
    target_values: np.ndarray, *, mu: float, sigma: float
) -> np.ndarray:
    """Gaussian fitness: ``exp(-(x - mu)^2 / (2 * sigma^2))``."""
    return np.exp(-((target_values - mu) ** 2) / (2 * sigma ** 2))


_FITNESS_REGISTRY: dict[str, Callable] = {
    "inverse_square": fitness_inverse_square,
    "gaussian": fitness_gaussian,
}


# ---------------------------------------------------------------------------
# GA optimizer
# ---------------------------------------------------------------------------

class GA(DiscreteOptimizer):
    """Genetic Algorithm optimizer with composable operators.

    Supports two modes of operation:

    **Simple mode** (``fitness_fn`` only): a single scalar objective is
    minimised.  Selection operates directly on these values.

    **Target/fitness mode** (``target_fn`` + ``fitness``): the *target*
    computes an observable per DNA (e.g., CY volume) and the *fitness*
    converts the population's target values into selection probabilities.
    Best-so-far tracking maximises the target.  This matches the pattern
    from arXiv:2405.08871 where the target function (volume) is separate
    from the fitness function (inverse-square peaked at a hyperparameter).

    Parameters
    ----------
    fitness_fn : Callable[[DNA], float]
        Objective function to minimise.  Ignored when *target_fn* is given.
    bounds : Bounds
        Per-dimension ``(lo, hi)`` inclusive bounds.
    target_fn : Callable[[DNA], float], optional
        Observable function (maximised).  When provided, *fitness* must also
        be specified and *fitness_fn* is built automatically.
    fitness : str | Callable | None
        Population-level fitness for selection.  Built-in options:
        ``'inverse_square'`` (``(x - mu)**-2``) and ``'gaussian'``
        (``exp(-(x - mu)^2 / (2*sigma^2))``).  A callable receives
        ``(target_values: np.ndarray, **fitness_params) -> np.ndarray``
        and should return unnormalised positive weights.
    fitness_params : dict, optional
        Keyword arguments forwarded to the fitness function (e.g.
        ``{'mu': 7.87}`` for inverse-square, or ``{'mu': 7, 'sigma': 1}``
        for Gaussian).
    population_size : int
        Number of individuals in each generation (must be >= 4).
    selection : str | dict | Callable
        Selection operator. String name (e.g. ``'tournament'``), dict with
        ``'method'`` key and optional params, or a callable.
    crossover : str | dict | Callable
        Crossover operator, same interface as *selection*.
    mutation_rate : float
        Probability of mutating each child (per individual, not per gene).
    mutation_k : int
        Number of genes mutated per mutation event.
    elitism : int
        Number of top individuals carried over unchanged each generation.
    seed : int | None
        Random seed for reproducibility.
    cache_size : int | None
        Max cached evaluations (``None`` for unbounded).
    record_history : bool
        Collect per-generation stats in ``Result.full_history``.
    progress : bool
        Show tqdm progress bar.
    """

    def __init__(
        self,
        fitness_fn: Callable[[DNA], float] | None = None,
        bounds: Bounds = (),
        *,
        target_fn: Callable[[DNA], float] | None = None,
        fitness: str | Callable | None = None,
        fitness_params: dict | None = None,
        population_size: int = 50,
        selection: str | dict | Callable = "tournament",
        crossover: str | dict | Callable = "npoint",
        mutation_rate: float = 0.1,
        mutation_k: int = 1,
        elitism: int = 1,
        seed: int | None = None,
        cache_size: int | None = None,
        record_history: bool = False,
        progress: bool = False,
        callbacks: list | None = None,
    ) -> None:
        # Validate hyperparameters (CORE-06)
        if population_size < 4:
            raise ValueError(
                f"population_size must be >= 4, got {population_size}"
            )
        if not 0.0 <= mutation_rate <= 1.0:
            raise ValueError(
                f"mutation_rate must be in [0, 1], got {mutation_rate}"
            )
        if elitism < 0 or elitism >= population_size:
            raise ValueError(
                f"elitism must be in [0, population_size), got {elitism}"
            )

        # Target/fitness mode
        self._target_fn = target_fn
        self._fitness_params = fitness_params or {}

        if target_fn is not None:
            if fitness is None:
                raise ValueError(
                    "fitness must be specified when target_fn is provided"
                )
            # Build fitness_fn for base class: negate target for minimisation
            fitness_fn = lambda dna: -target_fn(dna)

            # Resolve population-level fitness function
            if isinstance(fitness, str):
                self._pop_fitness_fn = _FITNESS_REGISTRY[fitness]
            elif callable(fitness):
                self._pop_fitness_fn = fitness
            else:
                raise TypeError(
                    f"fitness must be a str or callable, got {type(fitness).__name__}"
                )
            self._use_target_fitness = True
        else:
            if fitness_fn is None:
                raise ValueError(
                    "Either fitness_fn or target_fn must be provided"
                )
            self._pop_fitness_fn = None
            self._use_target_fitness = False

        super().__init__(
            fitness_fn, bounds,
            seed=seed, cache_size=cache_size,
            record_history=record_history, progress=progress,
            callbacks=callbacks,
        )

        self._population_size = population_size
        self._mutation_rate = mutation_rate
        self._mutation_k = mutation_k
        self._elitism = elitism

        # Resolve operators (D-05, D-06)
        self._selection_fn, self._selection_params = self._resolve_operator(
            selection, _SELECTION_REGISTRY, "selection"
        )
        self._crossover_fn, self._crossover_params = self._resolve_operator(
            crossover, _CROSSOVER_REGISTRY, "crossover"
        )

        # Population state (initialised in run())
        self._population: np.ndarray | None = None
        self._fitness_values: np.ndarray | None = None
        self._target_values: np.ndarray | None = None
        self._initialized: bool = False

    @staticmethod
    def _resolve_operator(
        spec: str | dict | Callable,
        registry: dict[str, Callable],
        name: str,
    ) -> tuple[Callable, dict]:
        """Resolve an operator spec to ``(callable, params)``."""
        if callable(spec):
            return spec, {}
        if isinstance(spec, str):
            if spec not in registry:
                valid = ", ".join(sorted(registry.keys()))
                raise ValueError(
                    f"Unknown {name} operator '{spec}'. "
                    f"Valid options: {valid}"
                )
            return registry[spec], {}
        if isinstance(spec, dict):
            spec = dict(spec)  # copy so we don't mutate caller's dict
            method = spec.pop("method", None)
            if method is None:
                raise ValueError(
                    f"{name} dict spec must include a 'method' key"
                )
            if method not in registry:
                valid = ", ".join(sorted(registry.keys()))
                raise ValueError(
                    f"Unknown {name} operator '{method}'. "
                    f"Valid options: {valid}"
                )
            return registry[method], spec
        raise TypeError(
            f"{name} must be a str, dict, or callable, got {type(spec).__name__}"
        )

    def _compute_selection_weights(self, fitness_vals: np.ndarray) -> np.ndarray:
        """Compute normalised selection probabilities.

        Returns an array where **higher = more likely to be selected**,
        normalised to sum to 1.  Selection operators always use ``argmax``
        / probability-weighted sampling on the result.

        In **simple mode**, converts minimisation fitness values to
        probabilities via ``1 / (fitness - min + 1)``.

        In **target/fitness mode**, applies the population-level fitness
        function to the target values and normalises.
        """
        if self._use_target_fitness:
            # fitness_vals are negated targets from base class
            target_vals = -fitness_vals
            weights = self._pop_fitness_fn(target_vals, **self._fitness_params)
        else:
            # Simple mode: invert so lower fitness -> higher weight
            weights = 1.0 / (fitness_vals - fitness_vals.min() + 1.0)

        # Clamp negatives/NaN to small positive
        weights = np.nan_to_num(weights, nan=1e-30, posinf=1e30, neginf=1e-30)
        weights = np.maximum(weights, 1e-30)
        total = weights.sum()
        if total > 0:
            weights /= total
        else:
            weights = np.ones_like(weights) / len(weights)
        # Ensure last element absorbs rounding
        weights[-1] = 1.0 - weights[:-1].sum()
        return weights

    def run(self, n_iterations: int):
        """Initialise population (if needed) and delegate to base-class loop."""
        if not self._initialized:
            n_dims = len(self._bounds)
            self._population = np.empty(
                (self._population_size, n_dims), dtype=int
            )
            self._fitness_values = np.empty(self._population_size, dtype=float)

            for i in range(self._population_size):
                dna = self._random_dna()
                self._population[i] = dna
                self._fitness_values[i] = self._evaluate(dna)
            self._initialized = True

        return super().run(n_iterations)

    def _get_state(self) -> dict:
        """Return GA-specific state for checkpointing."""
        return {
            'population': self._population.copy() if self._population is not None else None,
            'fitness_values': self._fitness_values.copy() if self._fitness_values is not None else None,
            'population_size': self._population_size,
            'mutation_rate': self._mutation_rate,
            'mutation_k': self._mutation_k,
            'elitism': self._elitism,
        }

    def _set_state(self, state: dict) -> None:
        """Restore GA-specific state from checkpoint."""
        self._population = state['population']
        self._fitness_values = state['fitness_values']
        self._population_size = state['population_size']
        self._mutation_rate = state['mutation_rate']
        self._mutation_k = state['mutation_k']
        self._elitism = state['elitism']
        self._initialized = True  # Skip re-initialization on next run()

    def _step(self, iteration: int) -> dict | None:
        """Execute one generation of the GA.

        Enforces population uniqueness: children that duplicate an existing
        member of the new population are discarded and replaced by fresh
        select-crossover-mutate attempts.  This matches the original
        triang_optimizer implementation and prevents population collapse.
        """
        pop = self._population
        fit = self._fitness_values
        n_dims = pop.shape[1]

        # Sort by fitness (ascending -- best first for minimisation)
        order = np.argsort(fit)
        pop = pop[order]
        fit = fit[order]

        # Compute selection weights (differs between simple and target mode)
        sel_weights = self._compute_selection_weights(fit)

        # Next generation: elite carry-over
        next_pop = np.empty_like(pop)
        next_fit = np.empty_like(fit)
        next_pop[: self._elitism] = pop[: self._elitism]
        next_fit[: self._elitism] = fit[: self._elitism]

        # Track seen DNA for uniqueness enforcement
        seen: set[tuple[int, ...]] = set()
        for i in range(self._elitism):
            seen.add(tuple(int(x) for x in next_pop[i]))

        idx = self._elitism
        max_attempts = self._population_size * 50  # safety valve
        attempts = 0
        while idx < self._population_size and attempts < max_attempts:
            attempts += 1
            # Select parents
            p1, p2 = self._selection_fn(
                pop, sel_weights, self._rng, **self._selection_params
            )
            parents = np.array([p1, p2])

            # Crossover
            c1, c2 = self._crossover_fn(
                parents, self._rng, **self._crossover_params
            )

            # Mutation + uniqueness check
            for child in (c1, c2):
                if idx >= self._population_size:
                    break
                if self._rng.random() < self._mutation_rate:
                    child = random_mutation(
                        child, self._bounds, self._rng, k=self._mutation_k
                    )
                # Clip to bounds
                for d in range(n_dims):
                    lo, hi = self._bounds[d]
                    child[d] = max(lo, min(hi, child[d]))

                key = tuple(int(x) for x in child)
                if key in seen:
                    continue  # skip duplicates

                seen.add(key)
                next_pop[idx] = child
                next_fit[idx] = self._evaluate(key)
                idx += 1

        # If we exhausted attempts, fill remaining slots with random DNA
        while idx < self._population_size:
            dna = self._random_dna()
            key = tuple(int(x) for x in dna)
            if key not in seen:
                seen.add(key)
                next_pop[idx] = dna
                next_fit[idx] = self._evaluate(key)
                idx += 1

        self._population = next_pop
        self._fitness_values = next_fit

        if self._record_history:
            return {
                "best": float(self._fitness_values.min()),
                "mean": float(self._fitness_values.mean()),
                "std": float(self._fitness_values.std()),
            }
        return None

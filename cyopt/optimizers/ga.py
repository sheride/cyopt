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
    fitness: np.ndarray,
    rng: np.random.Generator,
    *,
    k: int = 3,
) -> tuple[np.ndarray, np.ndarray]:
    """Select two parents via tournament selection.

    For each parent, pick *k* random individuals and return the one with the
    lowest fitness (minimisation).
    """
    parents = []
    for _ in range(2):
        indices = rng.integers(0, len(population), size=k)
        best_idx = indices[np.argmin(fitness[indices])]
        parents.append(population[best_idx].copy())
    return parents[0], parents[1]


def roulette_wheel_selection(
    population: np.ndarray,
    fitness: np.ndarray,
    rng: np.random.Generator,
) -> tuple[np.ndarray, np.ndarray]:
    """Select two parents with probability inversely proportional to fitness.

    Lower fitness -> higher selection probability (minimisation).
    """
    weights = 1.0 / (fitness - fitness.min() + 1.0)
    probs = weights / weights.sum()
    indices = rng.choice(len(population), size=2, p=probs, replace=True)
    return population[indices[0]].copy(), population[indices[1]].copy()


def ranked_selection(
    population: np.ndarray,
    fitness: np.ndarray,
    rng: np.random.Generator,
) -> tuple[np.ndarray, np.ndarray]:
    """Select two parents with probability proportional to rank.

    Best individual (lowest fitness) gets rank N, worst gets rank 1.
    """
    n = len(population)
    # argsort gives indices that would sort fitness ascending (best first)
    order = np.argsort(fitness)
    ranks = np.empty(n, dtype=float)
    # Best individual (order[0]) gets rank N, worst gets rank 1
    ranks[order] = np.arange(n, 0, -1, dtype=float)
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
# GA optimizer
# ---------------------------------------------------------------------------

class GA(DiscreteOptimizer):
    """Genetic Algorithm optimizer with composable operators.

    Parameters
    ----------
    fitness_fn : Callable[[DNA], float]
        Objective function to minimise.
    bounds : Bounds
        Per-dimension ``(lo, hi)`` inclusive bounds.
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
        fitness_fn: Callable[[DNA], float],
        bounds: Bounds,
        *,
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
        """Execute one generation of the GA."""
        pop = self._population
        fit = self._fitness_values
        n_dims = pop.shape[1]

        # Sort by fitness (ascending -- best first)
        order = np.argsort(fit)
        pop = pop[order]
        fit = fit[order]

        # Next generation: elite carry-over
        next_pop = np.empty_like(pop)
        next_fit = np.empty_like(fit)
        next_pop[: self._elitism] = pop[: self._elitism]
        next_fit[: self._elitism] = fit[: self._elitism]

        idx = self._elitism
        while idx < self._population_size:
            # Select parents
            p1, p2 = self._selection_fn(
                pop, fit, self._rng, **self._selection_params
            )
            parents = np.array([p1, p2])

            # Crossover
            c1, c2 = self._crossover_fn(
                parents, self._rng, **self._crossover_params
            )

            # Mutation
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
                next_pop[idx] = child
                next_fit[idx] = self._evaluate(tuple(int(x) for x in child))
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

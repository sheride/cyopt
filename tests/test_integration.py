"""End-to-end integration tests for all cyopt optimizers."""

import pytest

from cyopt import (
    GA,
    BasinHopping,
    BestFirstSearch,
    DifferentialEvolution,
    GreedyWalk,
    MCMC,
    RandomSample,
    Result,
    SimulatedAnnealing,
    TupleSpace,
)


def sphere_fitness(dna: tuple[int, ...]) -> float:
    """Sum of squares -- minimum at origin."""
    return float(sum(x * x for x in dna))


BOUNDS_3D = ((0, 9), (0, 9), (0, 9))
SPACE_3D = TupleSpace(BOUNDS_3D)

ALL_OPTIMIZERS = [
    (RandomSample, {}),
    (GreedyWalk, {}),
    (GA, {"population_size": 10}),
    (BestFirstSearch, {"mode": "backtrack"}),
    (BestFirstSearch, {"mode": "frontier"}),
    (BasinHopping, {}),
    (DifferentialEvolution, {"popsize": 5}),
    (MCMC, {}),
    (SimulatedAnnealing, {"n_iterations": 100}),
]


class TestAllOptimizersOnSphere:
    """Each optimizer finds a solution better than worst possible."""

    @pytest.mark.parametrize("OptimizerCls,kwargs", ALL_OPTIMIZERS)
    def test_all_optimizers_on_sphere(self, OptimizerCls, kwargs):
        """Each optimizer beats worst-possible fitness (243) on sphere."""
        opt = OptimizerCls(sphere_fitness, SPACE_3D, seed=42, **kwargs)
        result = opt.run(30)
        worst_possible = 9 * 9 * 3  # 243
        assert result.best_value < worst_possible


class TestAllOptimizersReturnResult:
    """Each optimizer returns a well-formed Result."""

    @pytest.mark.parametrize("OptimizerCls,kwargs", ALL_OPTIMIZERS)
    def test_result_fields(self, OptimizerCls, kwargs):
        """Result has all fields populated correctly."""
        opt = OptimizerCls(sphere_fitness, SPACE_3D, seed=42, **kwargs)
        result = opt.run(20)

        assert isinstance(result, Result)
        assert isinstance(result.best_solution, tuple)
        assert all(isinstance(x, int) for x in result.best_solution)
        # All values within bounds
        for val, (lo, hi) in zip(result.best_solution, BOUNDS_3D):
            assert lo <= val <= hi
        assert isinstance(result.best_value, float)
        assert len(result.history) > 0
        assert result.n_evaluations > 0
        assert result.wall_time > 0


class TestImportPublicAPI:
    """All public API symbols are importable."""

    def test_import_all_public_api(self):
        """Public API imports succeed and are the expected types."""
        from cyopt import (
            GA,
            BasinHopping,
            BestFirstSearch,
            DifferentialEvolution,
            DiscreteOptimizer,
            GreedyWalk,
            MCMC,
            RandomSample,
            Result,
            SimulatedAnnealing,
        )

        for cls in (
            GA, RandomSample, GreedyWalk, BestFirstSearch,
            BasinHopping, DifferentialEvolution, MCMC, SimulatedAnnealing,
        ):
            assert issubclass(cls, DiscreteOptimizer)

        assert Result.__dataclass_fields__ is not None


class TestCacheReducesEvaluations:
    """Cache hits reduce total evaluations."""

    def test_cache_reduces_evaluations(self):
        """GA with small population on tiny space should get cache hits."""
        tiny_space = TupleSpace(((0, 2), (0, 2)))
        # 3*3=9 possible solutions, population of 8, many generations
        # -> guaranteed cache hits
        ga = GA(sphere_fitness, tiny_space, population_size=8, seed=42)
        result = ga.run(20)
        # Without cache: 8 (init) + 20*~8 (generations) = ~168 evaluations
        # With cache on 9 possible solutions: at most 9 unique evals
        assert result.n_evaluations < 8 + 20 * 8


class TestProgressNoCrash:
    """Optimizers with progress=True run without error."""

    @pytest.mark.parametrize("OptimizerCls,kwargs", ALL_OPTIMIZERS)
    def test_progress_no_crash(self, OptimizerCls, kwargs):
        """Running with progress=True doesn't raise."""
        opt = OptimizerCls(
            sphere_fitness, SPACE_3D, seed=42, progress=True, **kwargs
        )
        result = opt.run(5)
        assert result.best_solution is not None


class TestContinuation:
    """State persists across consecutive run() calls."""

    @pytest.mark.parametrize("OptimizerCls,kwargs", ALL_OPTIMIZERS)
    def test_continuation(self, OptimizerCls, kwargs):
        """Second run() continues from prior state."""
        opt = OptimizerCls(sphere_fitness, SPACE_3D, seed=42, **kwargs)
        r1 = opt.run(20)
        n_evals_after_first = r1.n_evaluations
        best_after_first = r1.best_value

        r2 = opt.run(20)
        assert r2.n_evaluations >= n_evals_after_first  # more evaluations
        assert r2.best_value <= best_after_first  # did not worsen (minimization)

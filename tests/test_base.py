"""Tests for DiscreteOptimizer abstract base class."""

import pytest

from cyopt._types import Result
from cyopt.base import DiscreteOptimizer


class _DummyOptimizer(DiscreteOptimizer):
    """Minimal concrete subclass for testing. Evaluates a random DNA each step."""

    def _step(self, iteration: int) -> dict | None:
        dna = self._space.random(self._rng)
        value = self._evaluate(dna)
        return {"dna": dna, "value": value}


class TestABC:
    def test_abc_not_instantiable(self, sphere_fitness, standard_space):
        """DiscreteOptimizer cannot be instantiated directly."""
        with pytest.raises(TypeError):
            DiscreteOptimizer(
                fitness_fn=sphere_fitness, space=standard_space
            )

    def test_concrete_subclass_instantiable(self, sphere_fitness, standard_space):
        """A concrete subclass implementing _step can be instantiated."""
        opt = _DummyOptimizer(fitness_fn=sphere_fitness, space=standard_space)
        assert opt is not None


class TestRun:
    def test_run_returns_result(self, sphere_fitness, standard_space):
        """run() returns a Result with correct fields."""
        opt = _DummyOptimizer(
            fitness_fn=sphere_fitness, space=standard_space, seed=42
        )
        result = opt.run(10)
        assert isinstance(result, Result)
        assert isinstance(result.best_solution, tuple)
        assert isinstance(result.best_value, float)
        assert isinstance(result.history, list)
        assert result.full_history is None  # record_history=False by default
        assert isinstance(result.n_evaluations, int)
        assert result.n_evaluations > 0
        assert isinstance(result.wall_time, float)
        assert result.wall_time >= 0.0

    def test_history_length_equals_iterations(self, sphere_fitness, standard_space):
        """history list has length == n_iterations."""
        opt = _DummyOptimizer(
            fitness_fn=sphere_fitness, space=standard_space, seed=42
        )
        n = 20
        result = opt.run(n)
        assert len(result.history) == n


class TestCaching:
    def test_evaluate_caches_results(self, sphere_fitness, small_space):
        """Calling fitness twice with same DNA results in n_evaluations == 1."""
        opt = _DummyOptimizer(
            fitness_fn=sphere_fitness, space=small_space, seed=42
        )
        dna = (1, 1)
        val1 = opt._evaluate(dna)
        val2 = opt._evaluate(dna)
        assert val1 == val2
        assert opt._n_evaluations == 1


class TestBestTracking:
    def test_best_monotonically_non_increasing(self, sphere_fitness, standard_space):
        """Best-so-far tracking is monotonically non-increasing (minimization)."""
        opt = _DummyOptimizer(
            fitness_fn=sphere_fitness, space=standard_space, seed=42
        )
        result = opt.run(50)
        for i in range(1, len(result.history)):
            assert result.history[i] <= result.history[i - 1]


class TestSeeding:
    def test_seeding_reproducibility(self, sphere_fitness, standard_space):
        """Same seed produces identical Result.best_value and best_solution."""
        opt1 = _DummyOptimizer(
            fitness_fn=sphere_fitness, space=standard_space, seed=123
        )
        opt2 = _DummyOptimizer(
            fitness_fn=sphere_fitness, space=standard_space, seed=123
        )
        r1 = opt1.run(30)
        r2 = opt2.run(30)
        assert r1.best_value == r2.best_value
        assert r1.best_solution == r2.best_solution
        assert r1.history == r2.history


class TestProgress:
    def test_progress_no_raise(self, sphere_fitness, standard_space):
        """progress=True does not raise (smoke test)."""
        opt = _DummyOptimizer(
            fitness_fn=sphere_fitness,
            space=standard_space,
            seed=42,
            progress=True,
        )
        result = opt.run(5)
        assert isinstance(result, Result)


class TestHistory:
    def test_record_history_true(self, sphere_fitness, standard_space):
        """record_history=True populates full_history."""
        opt = _DummyOptimizer(
            fitness_fn=sphere_fitness,
            space=standard_space,
            seed=42,
            record_history=True,
        )
        result = opt.run(10)
        assert result.full_history is not None
        assert len(result.full_history) == 10
        assert isinstance(result.full_history[0], dict)

    def test_record_history_false(self, sphere_fitness, standard_space):
        """record_history=False gives None for full_history."""
        opt = _DummyOptimizer(
            fitness_fn=sphere_fitness,
            space=standard_space,
            seed=42,
            record_history=False,
        )
        result = opt.run(10)
        assert result.full_history is None


class TestSpaceRandom:
    def test_space_random_within_bounds(
        self, sphere_fitness, standard_space, standard_bounds
    ):
        """space.random(rng) produces tuples within bounds."""
        opt = _DummyOptimizer(
            fitness_fn=sphere_fitness, space=standard_space, seed=42
        )
        for _ in range(100):
            dna = opt._space.random(opt._rng)
            assert isinstance(dna, tuple)
            assert len(dna) == len(standard_bounds)
            for val, (lo, hi) in zip(dna, standard_bounds):
                assert lo <= val <= hi
                assert isinstance(val, int)

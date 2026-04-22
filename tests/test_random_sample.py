"""Tests for the RandomSample optimizer."""

from cyopt.optimizers.random_sample import RandomSample


class TestRandomSample:
    """Tests for RandomSample optimizer."""

    def test_returns_best(self, sphere_fitness, standard_space):
        """RandomSample returns the best value found across all samples."""
        opt = RandomSample(sphere_fitness, standard_space, seed=42)
        result = opt.run(100)
        # The best value should be <= the fitness of any randomly generated point
        # With 100 samples in (0,9)^3, it should find something decent
        assert result.best_value >= 0.0  # sum of squares is non-negative
        assert result.best_solution is not None
        assert sphere_fitness(result.best_solution) == result.best_value

    def test_n_evaluations(self, sphere_fitness, small_space):
        """n_evaluations <= n_iterations (cache hits on small space)."""
        opt = RandomSample(sphere_fitness, small_space, seed=42)
        result = opt.run(50)
        # Small space (3x3 = 9 unique points), so with 50 iterations
        # many will be cache hits
        assert result.n_evaluations <= 50
        assert result.n_evaluations >= 1

    def test_seeding(self, sphere_fitness, standard_space):
        """Same seed produces identical results."""
        opt1 = RandomSample(sphere_fitness, standard_space, seed=123)
        result1 = opt1.run(50)

        opt2 = RandomSample(sphere_fitness, standard_space, seed=123)
        result2 = opt2.run(50)

        assert result1.best_solution == result2.best_solution
        assert result1.best_value == result2.best_value
        assert result1.n_evaluations == result2.n_evaluations

    def test_full_history(self, sphere_fitness, standard_space):
        """record_history=True provides full_history with per-iteration dicts."""
        opt = RandomSample(
            sphere_fitness, standard_space, seed=42, record_history=True
        )
        result = opt.run(20)
        assert result.full_history is not None
        assert len(result.full_history) == 20
        for entry in result.full_history:
            assert "sampled" in entry
            assert "value" in entry
            assert isinstance(entry["sampled"], tuple)
            assert isinstance(entry["value"], float)

    def test_history_monotonic(self, sphere_fitness, standard_space):
        """result.history is monotonically non-increasing (best-so-far)."""
        opt = RandomSample(sphere_fitness, standard_space, seed=42)
        result = opt.run(50)
        for i in range(1, len(result.history)):
            assert result.history[i] <= result.history[i - 1]

    def test_result_fields(self, sphere_fitness, standard_space):
        """Result has all expected fields."""
        opt = RandomSample(sphere_fitness, standard_space, seed=42)
        result = opt.run(10)
        assert result.history is not None
        assert len(result.history) == 10
        assert result.wall_time >= 0.0
        assert result.full_history is None  # record_history defaults to False

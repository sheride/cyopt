"""Cross-optimizer seeding reproducibility tests."""

from cyopt.optimizers.random_sample import RandomSample
from cyopt.optimizers.greedy_walk import GreedyWalk


class TestSeedingReproducibility:
    """Verify that all optimizers produce identical results with the same seed."""

    def test_random_sample_seeding(self, sphere_fitness, standard_bounds):
        """RandomSample: same seed -> identical results."""
        opt1 = RandomSample(sphere_fitness, standard_bounds, seed=777)
        result1 = opt1.run(50)

        opt2 = RandomSample(sphere_fitness, standard_bounds, seed=777)
        result2 = opt2.run(50)

        assert result1.best_solution == result2.best_solution
        assert result1.best_value == result2.best_value
        assert result1.history == result2.history
        assert result1.n_evaluations == result2.n_evaluations

    def test_greedy_walk_seeding(self, sphere_fitness, standard_bounds):
        """GreedyWalk: same seed -> identical results."""
        opt1 = GreedyWalk(sphere_fitness, standard_bounds, seed=777)
        result1 = opt1.run(30)

        opt2 = GreedyWalk(sphere_fitness, standard_bounds, seed=777)
        result2 = opt2.run(30)

        assert result1.best_solution == result2.best_solution
        assert result1.best_value == result2.best_value
        assert result1.history == result2.history
        assert result1.n_evaluations == result2.n_evaluations

    def test_different_seeds_differ(self, sphere_fitness, standard_bounds):
        """Different seeds produce different results (with high probability)."""
        opt1 = RandomSample(sphere_fitness, standard_bounds, seed=1)
        result1 = opt1.run(50)

        opt2 = RandomSample(sphere_fitness, standard_bounds, seed=2)
        result2 = opt2.run(50)

        # Very unlikely to be identical with different seeds on large space
        assert result1.history != result2.history

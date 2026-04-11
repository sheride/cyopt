"""Cross-optimizer seeding reproducibility tests."""

from cyopt.optimizers.basin_hopping import BasinHopping
from cyopt.optimizers.best_first_search import BestFirstSearch
from cyopt.optimizers.differential_evolution import DifferentialEvolution
from cyopt.optimizers.ga import GA
from cyopt.optimizers.greedy_walk import GreedyWalk
from cyopt.optimizers.mcmc import MCMC
from cyopt.optimizers.random_sample import RandomSample
from cyopt.optimizers.simulated_annealing import SimulatedAnnealing


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

    def test_ga_seeding(self, sphere_fitness, standard_bounds):
        """GA: same seed -> identical results."""
        opt1 = GA(sphere_fitness, standard_bounds, seed=777, population_size=10)
        result1 = opt1.run(20)

        opt2 = GA(sphere_fitness, standard_bounds, seed=777, population_size=10)
        result2 = opt2.run(20)

        assert result1.best_solution == result2.best_solution
        assert result1.best_value == result2.best_value
        assert result1.history == result2.history
        assert result1.n_evaluations == result2.n_evaluations

    def test_best_first_search_backtrack_seeding(self, sphere_fitness, standard_bounds):
        """BestFirstSearch (backtrack): same seed -> identical results."""
        opt1 = BestFirstSearch(sphere_fitness, standard_bounds, seed=777, mode="backtrack")
        result1 = opt1.run(30)

        opt2 = BestFirstSearch(sphere_fitness, standard_bounds, seed=777, mode="backtrack")
        result2 = opt2.run(30)

        assert result1.best_solution == result2.best_solution
        assert result1.best_value == result2.best_value
        assert result1.history == result2.history
        assert result1.n_evaluations == result2.n_evaluations

    def test_best_first_search_frontier_seeding(self, sphere_fitness, standard_bounds):
        """BestFirstSearch (frontier): same seed -> identical results."""
        opt1 = BestFirstSearch(sphere_fitness, standard_bounds, seed=777, mode="frontier")
        result1 = opt1.run(30)

        opt2 = BestFirstSearch(sphere_fitness, standard_bounds, seed=777, mode="frontier")
        result2 = opt2.run(30)

        assert result1.best_solution == result2.best_solution
        assert result1.best_value == result2.best_value
        assert result1.history == result2.history
        assert result1.n_evaluations == result2.n_evaluations

    def test_basin_hopping_seeding(self, sphere_fitness, standard_bounds):
        """BasinHopping: same seed -> identical results."""
        opt1 = BasinHopping(sphere_fitness, standard_bounds, seed=777)
        result1 = opt1.run(20)

        opt2 = BasinHopping(sphere_fitness, standard_bounds, seed=777)
        result2 = opt2.run(20)

        assert result1.best_solution == result2.best_solution
        assert result1.best_value == result2.best_value
        assert result1.history == result2.history
        assert result1.n_evaluations == result2.n_evaluations

    def test_differential_evolution_seeding(self, sphere_fitness, standard_bounds):
        """DifferentialEvolution: same seed -> identical results."""
        opt1 = DifferentialEvolution(sphere_fitness, standard_bounds, seed=777, popsize=5)
        result1 = opt1.run(20)

        opt2 = DifferentialEvolution(sphere_fitness, standard_bounds, seed=777, popsize=5)
        result2 = opt2.run(20)

        assert result1.best_solution == result2.best_solution
        assert result1.best_value == result2.best_value
        assert result1.n_evaluations == result2.n_evaluations

    def test_mcmc_seeding(self, sphere_fitness, standard_bounds):
        """MCMC: same seed -> identical results."""
        opt1 = MCMC(sphere_fitness, standard_bounds, seed=777)
        result1 = opt1.run(50)

        opt2 = MCMC(sphere_fitness, standard_bounds, seed=777)
        result2 = opt2.run(50)

        assert result1.best_solution == result2.best_solution
        assert result1.best_value == result2.best_value
        assert result1.history == result2.history
        assert result1.n_evaluations == result2.n_evaluations

    def test_simulated_annealing_seeding(self, sphere_fitness, standard_bounds):
        """SimulatedAnnealing: same seed -> identical results."""
        opt1 = SimulatedAnnealing(sphere_fitness, standard_bounds, seed=777, n_iterations=50)
        result1 = opt1.run(50)

        opt2 = SimulatedAnnealing(sphere_fitness, standard_bounds, seed=777, n_iterations=50)
        result2 = opt2.run(50)

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

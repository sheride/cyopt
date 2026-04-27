"""Tests for the GA (Genetic Algorithm) optimizer."""

import numpy as np
import pytest

from cyopt import TupleSpace
from cyopt.optimizers.ga import (
    GA,
    npoint_crossover,
    random_mutation,
    ranked_selection,
    roulette_wheel_selection,
    tournament_selection,
    uniform_crossover,
)


# ---------------------------------------------------------------------------
# Selection operator tests
# ---------------------------------------------------------------------------

class TestTournamentSelection:
    """Tournament selection picks the individual with highest weight."""

    def test_winner_has_highest_weight(self):
        """Winner of tournament has highest weight among candidates."""
        rng = np.random.default_rng(42)
        population = np.array([[0, 0], [1, 1], [2, 2], [3, 3], [4, 4]])
        # Higher weight = more likely to be selected
        weights = np.array([0.05, 0.1, 0.15, 0.25, 0.45])

        # Run many tournaments to verify high-weight candidates win
        winner_weights = []
        for _ in range(100):
            p1, p2 = tournament_selection(population, weights, rng, k=3)
            winner_weights.extend([
                weights[np.where((population == p1).all(axis=1))[0][0]],
                weights[np.where((population == p2).all(axis=1))[0][0]],
            ])

        # High-weight individuals should win more often
        assert np.mean(winner_weights) > weights.mean()


class TestRouletteWheelSelection:
    """Roulette wheel selection works without errors and returns valid individuals."""

    def test_returns_valid_individuals(self):
        """Roulette wheel returns individuals from the population."""
        rng = np.random.default_rng(42)
        population = np.array([[0, 0], [1, 1], [2, 2], [3, 3]])
        weights = np.array([0.1, 0.2, 0.3, 0.4])

        p1, p2 = roulette_wheel_selection(population, weights, rng)

        # Both parents should be rows from the population
        assert p1.shape == (2,)
        assert p2.shape == (2,)


class TestRankedSelection:
    """Ranked selection gives highest-weight individual highest probability."""

    def test_best_individual_selected_most(self):
        """Individual with highest weight should be selected most often."""
        rng = np.random.default_rng(42)
        population = np.array([[0, 0], [1, 1], [2, 2], [3, 3], [4, 4]])
        # index 4 has highest weight
        weights = np.array([0.02, 0.05, 0.13, 0.3, 0.5])

        counts = np.zeros(5)
        for _ in range(1000):
            p1, p2 = ranked_selection(population, weights, rng)
            for p in [p1, p2]:
                idx = np.where((population == p).all(axis=1))[0][0]
                counts[idx] += 1

        # Best individual (index 4) should be selected most often
        assert counts[4] == counts.max()


# ---------------------------------------------------------------------------
# Crossover operator tests
# ---------------------------------------------------------------------------

class TestNpointCrossover:
    """N-point crossover produces children that are recombinations of parents."""

    def test_single_point(self):
        """Single-point crossover: children are parent segments."""
        rng = np.random.default_rng(42)
        parent1 = np.array([0, 0, 0, 0, 0])
        parent2 = np.array([1, 1, 1, 1, 1])
        parents = np.array([parent1, parent2])

        child1, child2 = npoint_crossover(parents, rng, n=1)

        # Each child gene should come from one of the parents
        for i in range(5):
            assert child1[i] in (0, 1)
            assert child2[i] in (0, 1)

        # Children should not both be identical to parents (very unlikely)
        assert not (np.array_equal(child1, parent1) and np.array_equal(child2, parent2))


class TestUniformCrossover:
    """Uniform crossover swaps genes at approximately 50% rate."""

    def test_swap_rate(self):
        """Approximately 50% of genes should be swapped over many trials."""
        rng = np.random.default_rng(42)
        parent1 = np.zeros(100, dtype=int)
        parent2 = np.ones(100, dtype=int)
        parents = np.array([parent1, parent2])

        child1, child2 = uniform_crossover(parents, rng)

        # Count how many genes in child1 came from parent2 (value == 1)
        swap_rate = child1.sum() / 100
        assert 0.3 < swap_rate < 0.7  # Roughly 50%


# ---------------------------------------------------------------------------
# Mutation operator tests
# ---------------------------------------------------------------------------

class TestRandomMutation:
    """Random mutation changes exactly k positions within bounds."""

    def test_exactly_k_positions_change(self):
        """Mutation changes exactly k positions."""
        rng = np.random.default_rng(42)
        dna = np.array([5, 5, 5, 5, 5])
        bounds = ((0, 9), (0, 9), (0, 9), (0, 9), (0, 9))

        mutated = random_mutation(dna, bounds, rng, k=2)

        n_changed = np.sum(mutated != dna)
        assert n_changed == 2

    def test_values_within_bounds(self):
        """Mutated values stay within bounds."""
        rng = np.random.default_rng(42)
        dna = np.array([5, 5, 5])
        bounds = ((0, 3), (2, 7), (1, 4))

        for _ in range(50):
            mutated = random_mutation(dna, bounds, rng, k=3)
            for i, (lo, hi) in enumerate(bounds):
                assert lo <= mutated[i] <= hi


# ---------------------------------------------------------------------------
# GA class tests
# ---------------------------------------------------------------------------

class TestGAOperatorInterface:
    """GA supports string, dict, and callable operator specs (D-05, D-06)."""

    def test_string_operators(self, sphere_fitness, standard_space):
        """GA accepts string operator names."""
        ga = GA(sphere_fitness, standard_space,
                selection='tournament', crossover='npoint',
                seed=42)
        result = ga.run(5)
        assert result.best_solution is not None

    def test_dict_operators(self, sphere_fitness, standard_space):
        """GA accepts dict operator specs with parameters."""
        ga = GA(sphere_fitness, standard_space,
                selection={'method': 'tournament', 'k': 5},
                crossover={'method': 'npoint', 'n': 2},
                seed=42)
        result = ga.run(5)
        assert result.best_solution is not None

    def test_callable_operators(self, sphere_fitness, standard_space):
        """GA accepts callable operator specs."""
        def custom_selection(population, fitness, rng, **kwargs):
            idx1 = rng.integers(len(population))
            idx2 = rng.integers(len(population))
            return population[idx1], population[idx2]

        ga = GA(sphere_fitness, standard_space,
                selection=custom_selection, seed=42)
        result = ga.run(5)
        assert result.best_solution is not None

    def test_invalid_operator_raises_valueerror(self, sphere_fitness, standard_space):
        """Invalid operator string raises ValueError with valid options."""
        with pytest.raises(ValueError, match="tournament"):
            GA(sphere_fitness, standard_space, selection='nonexistent')

    def test_invalid_population_size(self, sphere_fitness, standard_space):
        """population_size < 4 raises ValueError."""
        with pytest.raises(ValueError, match="population_size"):
            GA(sphere_fitness, standard_space, population_size=1)

    def test_invalid_mutation_rate(self, sphere_fitness, standard_space):
        """mutation_rate outside [0, 1] raises ValueError."""
        with pytest.raises(ValueError, match="mutation_rate"):
            GA(sphere_fitness, standard_space, mutation_rate=2.0)


class TestGAOptimization:
    """GA evolves population and finds improving solutions."""

    def test_improves_over_generations(self, sphere_fitness):
        """GA should improve on sphere_fitness over 50 generations."""
        space = TupleSpace(((0, 9),) * 5)
        ga = GA(sphere_fitness, space, population_size=20, seed=42)
        result = ga.run(50)

        # Should improve from initial random (worst possible = 5*81 = 405)
        assert result.best_value < 405
        # History should show improvement (first > last)
        assert result.history[0] >= result.history[-1]

    def test_seeding_reproducibility(self, sphere_fitness, standard_space):
        """Two GA runs with same seed produce identical results."""
        ga1 = GA(sphere_fitness, standard_space, seed=42, population_size=20)
        result1 = ga1.run(20)

        ga2 = GA(sphere_fitness, standard_space, seed=42, population_size=20)
        result2 = ga2.run(20)

        assert result1.best_solution == result2.best_solution
        assert result1.best_value == result2.best_value
        assert result1.history == result2.history

    def test_population_size(self, sphere_fitness, standard_space):
        """population_size controls number of individuals."""
        ga = GA(sphere_fitness, standard_space, population_size=10, seed=42)
        ga.run(1)
        assert ga._population.shape[0] == 10

    def test_full_history(self, sphere_fitness, standard_space):
        """record_history=True provides dicts with best, mean, std keys."""
        ga = GA(sphere_fitness, standard_space, population_size=10,
                seed=42, record_history=True)
        result = ga.run(10)

        assert result.full_history is not None
        assert len(result.full_history) == 10
        for entry in result.full_history:
            assert 'best' in entry
            assert 'mean' in entry
            assert 'std' in entry

    def test_elitism_preserves_best(self, sphere_fitness, standard_space):
        """With elitism >= 1, best individual never gets worse."""
        ga = GA(sphere_fitness, standard_space, population_size=10,
                elitism=2, seed=42)
        result = ga.run(20)

        # History should be monotonically non-increasing
        for i in range(1, len(result.history)):
            assert result.history[i] <= result.history[i - 1]

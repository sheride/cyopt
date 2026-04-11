"""Unit tests for SimulatedAnnealing optimizer."""

import pytest

from cyopt.optimizers._neighbors import random_single_flip
from cyopt.optimizers.simulated_annealing import SimulatedAnnealing


def sphere_fitness(dna):
    return float(sum(x * x for x in dna))


BOUNDS_3D = ((0, 9), (0, 9), (0, 9))


class TestSimulatedAnnealing:
    """Tests for SimulatedAnnealing optimizer."""

    def test_finds_improvement(self):
        """SA finds solution better than worst case."""
        opt = SimulatedAnnealing(sphere_fitness, BOUNDS_3D, seed=42)
        result = opt.run(100)
        assert result.best_value < 243

    def test_temperature_decreases(self):
        """Temperature values in full_history decrease over iterations."""
        opt = SimulatedAnnealing(
            sphere_fitness, BOUNDS_3D,
            n_iterations=100, seed=42, record_history=True,
        )
        result = opt.run(100)
        assert result.full_history is not None
        temps = [entry["temperature"] for entry in result.full_history]
        assert len(temps) > 0
        # Temperature should generally decrease (first > last)
        assert temps[0] > temps[-1]
        # Check monotonic decrease
        for i in range(1, len(temps)):
            assert temps[i] <= temps[i - 1]

    def test_custom_step_fn(self):
        """Custom step_fn is called during optimization."""
        called = {"count": 0}

        def tracking_step(dna, bounds, rng):
            called["count"] += 1
            return random_single_flip(dna, bounds, rng)

        opt = SimulatedAnnealing(
            sphere_fitness, BOUNDS_3D,
            step_fn=tracking_step, seed=42,
        )
        opt.run(20)
        assert called["count"] > 0

    def test_seeding(self):
        """Same seed produces identical results."""
        opt1 = SimulatedAnnealing(sphere_fitness, BOUNDS_3D, seed=777)
        result1 = opt1.run(50)

        opt2 = SimulatedAnnealing(sphere_fitness, BOUNDS_3D, seed=777)
        result2 = opt2.run(50)

        assert result1.best_solution == result2.best_solution
        assert result1.best_value == result2.best_value
        assert result1.history == result2.history
        assert result1.n_evaluations == result2.n_evaluations

    def test_continuation(self):
        """State persists across consecutive run() calls, step_count accumulates."""
        opt = SimulatedAnnealing(
            sphere_fitness, BOUNDS_3D,
            n_iterations=100, seed=42,
        )
        r1 = opt.run(50)
        n_evals_1 = r1.n_evaluations
        best_1 = r1.best_value
        step_count_1 = opt._step_count

        r2 = opt.run(50)
        assert r2.n_evaluations > n_evals_1
        assert r2.best_value <= best_1
        assert opt._step_count > step_count_1
        assert opt._step_count == step_count_1 + 50

    def test_record_history(self):
        """full_history has temperature key."""
        opt = SimulatedAnnealing(
            sphere_fitness, BOUNDS_3D,
            seed=42, record_history=True,
        )
        result = opt.run(20)
        assert result.full_history is not None
        assert len(result.full_history) > 0
        assert "temperature" in result.full_history[0]
        assert "accepted" in result.full_history[0]

    def test_invalid_n_iterations(self):
        """n_iterations <= 0 raises ValueError."""
        with pytest.raises(ValueError, match="n_iterations must be positive"):
            SimulatedAnnealing(sphere_fitness, BOUNDS_3D, n_iterations=0)

    def test_invalid_t_max(self):
        """t_max <= 0 raises ValueError."""
        with pytest.raises(ValueError, match="t_max must be positive"):
            SimulatedAnnealing(sphere_fitness, BOUNDS_3D, t_max=0)

    def test_invalid_t_min_ge_t_max(self):
        """t_min >= t_max raises ValueError."""
        with pytest.raises(ValueError, match="t_min must be less than t_max"):
            SimulatedAnnealing(sphere_fitness, BOUNDS_3D, t_min=2.0, t_max=1.0)

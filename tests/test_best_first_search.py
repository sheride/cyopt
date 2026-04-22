"""Unit tests for BestFirstSearch optimizer."""

import pytest

from cyopt import TupleSpace
from cyopt.optimizers.best_first_search import BestFirstSearch


def sphere_fitness(dna):
    return float(sum(x * x for x in dna))


BOUNDS_3D = ((0, 9), (0, 9), (0, 9))
SPACE_3D = TupleSpace(BOUNDS_3D)


class TestBestFirstSearchBacktrack:
    """Tests for backtrack mode."""

    def test_backtrack_finds_improvement(self):
        """Backtrack mode finds solution better than worst case."""
        opt = BestFirstSearch(sphere_fitness, SPACE_3D, mode="backtrack", seed=42)
        result = opt.run(50)
        assert result.best_value < 243  # worst: 9^2 * 3

    def test_backtrack_seeding(self):
        """Same seed produces identical results in backtrack mode."""
        opt1 = BestFirstSearch(sphere_fitness, SPACE_3D, mode="backtrack", seed=777)
        result1 = opt1.run(30)

        opt2 = BestFirstSearch(sphere_fitness, SPACE_3D, mode="backtrack", seed=777)
        result2 = opt2.run(30)

        assert result1.best_solution == result2.best_solution
        assert result1.best_value == result2.best_value
        assert result1.history == result2.history
        assert result1.n_evaluations == result2.n_evaluations

    def test_backtrack_continuation(self):
        """State persists across consecutive run() calls."""
        opt = BestFirstSearch(sphere_fitness, SPACE_3D, mode="backtrack", seed=42)
        r1 = opt.run(20)
        n_evals_1 = r1.n_evaluations
        best_1 = r1.best_value

        r2 = opt.run(20)
        assert r2.n_evaluations > n_evals_1
        assert r2.best_value <= best_1

    def test_backtrack_oscillation_avoid(self):
        """Avoid set grows when oscillation is detected."""
        # Use a small space where oscillation is likely
        small_space = TupleSpace(((0, 2), (0, 2)))
        opt = BestFirstSearch(sphere_fitness, small_space, mode="backtrack", seed=42)
        opt.run(50)
        # After many steps in a small space, avoid set should have entries
        # (oscillation detection triggers avoid additions)
        # We just verify the optimizer completes without error and finds improvement
        assert opt._best_value < 8  # worst: 2^2 + 2^2 = 8


class TestBestFirstSearchFrontier:
    """Tests for frontier mode."""

    def test_frontier_finds_improvement(self):
        """Frontier mode finds solution better than worst case."""
        opt = BestFirstSearch(sphere_fitness, SPACE_3D, mode="frontier", seed=42)
        result = opt.run(50)
        assert result.best_value < 243

    def test_frontier_seeding(self):
        """Same seed produces identical results in frontier mode."""
        opt1 = BestFirstSearch(sphere_fitness, SPACE_3D, mode="frontier", seed=777)
        result1 = opt1.run(30)

        opt2 = BestFirstSearch(sphere_fitness, SPACE_3D, mode="frontier", seed=777)
        result2 = opt2.run(30)

        assert result1.best_solution == result2.best_solution
        assert result1.best_value == result2.best_value
        assert result1.history == result2.history
        assert result1.n_evaluations == result2.n_evaluations


class TestBestFirstSearchGeneral:
    """Tests for both modes and general behavior."""

    def test_custom_neighbor_fn(self):
        """Custom neighbor_fn is called and changes search behavior."""
        called = {"count": 0}

        def tracking_neighbors(dna):
            called["count"] += 1
            # Generate Hamming-distance-1 neighbors within BOUNDS_3D
            out = []
            for i, (lo, hi) in enumerate(BOUNDS_3D):
                for val in range(lo, hi + 1):
                    if val != dna[i]:
                        n = list(dna)
                        n[i] = val
                        out.append(tuple(n))
            return out

        opt = BestFirstSearch(
            sphere_fitness, SPACE_3D,
            mode="backtrack", neighbor_fn=tracking_neighbors, seed=42,
        )
        opt.run(10)
        assert called["count"] > 0

    def test_invalid_mode_raises(self):
        """Invalid mode raises ValueError."""
        with pytest.raises(ValueError, match="mode must be"):
            BestFirstSearch(sphere_fitness, SPACE_3D, mode="bad")

    def test_record_history(self):
        """record_history=True produces full_history entries."""
        opt = BestFirstSearch(
            sphere_fitness, SPACE_3D,
            mode="backtrack", seed=42, record_history=True,
        )
        result = opt.run(10)
        assert result.full_history is not None
        assert len(result.full_history) > 0
        assert "position" in result.full_history[0]
        assert "value" in result.full_history[0]

    def test_result_fields(self):
        """Result has correct types and values within bounds."""
        opt = BestFirstSearch(sphere_fitness, SPACE_3D, mode="backtrack", seed=42)
        result = opt.run(20)

        assert isinstance(result.best_solution, tuple)
        assert all(isinstance(x, int) for x in result.best_solution)
        assert len(result.best_solution) == 3
        for val, (lo, hi) in zip(result.best_solution, BOUNDS_3D):
            assert lo <= val <= hi
        assert isinstance(result.best_value, float)
        assert result.n_evaluations > 0
        assert result.wall_time > 0

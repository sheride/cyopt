"""Tests for the GreedyWalk optimizer."""

from cyopt import TupleSpace
from cyopt.optimizers.greedy_walk import GreedyWalk


class TestGreedyWalk:
    """Tests for GreedyWalk optimizer."""

    def test_moves_to_better_neighbor(self, sphere_fitness, standard_space):
        """GreedyWalk improves from initial random point."""
        opt = GreedyWalk(sphere_fitness, standard_space, seed=42)
        result = opt.run(20)
        # Should find something better than worst case (9^2 * 3 = 243)
        assert result.best_value < 243.0
        assert result.best_solution is not None

    def test_local_minimum(self, sphere_fitness):
        """GreedyWalk converges to the global minimum on sphere_fitness."""
        # With bounds (0, 3)^3, the minimum is at (0,0,0) with value 0
        space = TupleSpace(((0, 3), (0, 3), (0, 3)))
        opt = GreedyWalk(sphere_fitness, space, seed=42)
        result = opt.run(50)
        # Should reach (0,0,0) since sphere has no local minima in integer space
        assert result.best_value == 0.0
        assert result.best_solution == (0, 0, 0)

    def test_custom_neighbor_fn(self, sphere_fitness):
        """Custom neighbor function is used when provided."""
        bounds_local = ((0, 5), (0, 5))
        space_local = TupleSpace(bounds_local)

        # Custom neighbor: only change first coordinate
        def first_coord_only(dna):
            neighbors = []
            lo, hi = bounds_local[0]
            for val in range(lo, hi + 1):
                if val != dna[0]:
                    neighbors.append((val,) + dna[1:])
            return neighbors

        opt = GreedyWalk(
            sphere_fitness, space_local, neighbor_fn=first_coord_only, seed=42
        )
        result = opt.run(20)
        # The optimizer should still work; first coord should reach 0
        assert result.best_solution[0] == 0

    def test_seeding(self, sphere_fitness, standard_space):
        """Same seed produces identical results."""
        opt1 = GreedyWalk(sphere_fitness, standard_space, seed=99)
        result1 = opt1.run(30)

        opt2 = GreedyWalk(sphere_fitness, standard_space, seed=99)
        result2 = opt2.run(30)

        assert result1.best_solution == result2.best_solution
        assert result1.best_value == result2.best_value

    def test_continuation(self, sphere_fitness, standard_space):
        """Consecutive runs continue from prior state (no reset)."""
        opt = GreedyWalk(sphere_fitness, standard_space, seed=42)
        result1 = opt.run(10)
        result2 = opt.run(10)
        # Second run should be at least as good (keeps best-so-far)
        assert result2.best_value <= result1.best_value
        # Evaluations accumulate across runs
        assert result2.n_evaluations >= result1.n_evaluations

    def test_full_history(self, sphere_fitness, standard_space):
        """record_history=True populates full_history."""
        opt = GreedyWalk(
            sphere_fitness, standard_space, seed=42, record_history=True
        )
        result = opt.run(10)
        assert result.full_history is not None
        assert len(result.full_history) == 10
        for entry in result.full_history:
            assert "position" in entry
            assert "value" in entry
            assert "moved" in entry

    def test_history_monotonic(self, sphere_fitness, standard_space):
        """result.history is monotonically non-increasing."""
        opt = GreedyWalk(sphere_fitness, standard_space, seed=42)
        result = opt.run(30)
        for i in range(1, len(result.history)):
            assert result.history[i] <= result.history[i - 1]

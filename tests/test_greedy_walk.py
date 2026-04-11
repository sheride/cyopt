"""Tests for the GreedyWalk optimizer."""

from cyopt.optimizers.greedy_walk import GreedyWalk, hamming_neighbors


class TestHammingNeighbors:
    """Tests for the hamming_neighbors function."""

    def test_default_neighbors_hamming(self):
        """hamming_neighbors produces correct count: sum of (hi - lo) per dim."""
        dna = (1, 1)
        bounds = ((0, 2), (0, 2))
        neighbors = hamming_neighbors(dna, bounds)
        # dim 0: values 0, 2 (2 neighbors); dim 1: values 0, 2 (2 neighbors)
        assert len(neighbors) == 4

    def test_hamming_neighbors_at_boundary(self):
        """Neighbors at boundary are within bounds."""
        dna = (0, 0)
        bounds = ((0, 2), (0, 2))
        neighbors = hamming_neighbors(dna, bounds)
        for n in neighbors:
            for val, (lo, hi) in zip(n, bounds):
                assert lo <= val <= hi

    def test_hamming_neighbors_distance_one(self):
        """Each neighbor differs from dna in exactly one position."""
        dna = (1, 2, 3)
        bounds = ((0, 3), (0, 4), (0, 5))
        neighbors = hamming_neighbors(dna, bounds)
        for n in neighbors:
            diffs = sum(1 for a, b in zip(dna, n) if a != b)
            assert diffs == 1


class TestGreedyWalk:
    """Tests for GreedyWalk optimizer."""

    def test_moves_to_better_neighbor(self, sphere_fitness, standard_bounds):
        """GreedyWalk improves from initial random point."""
        opt = GreedyWalk(sphere_fitness, standard_bounds, seed=42)
        result = opt.run(20)
        # Should find something better than worst case (9^2 * 3 = 243)
        assert result.best_value < 243.0
        assert result.best_solution is not None

    def test_local_minimum(self, sphere_fitness):
        """GreedyWalk converges to the global minimum on sphere_fitness."""
        # With bounds (0, 3)^3, the minimum is at (0,0,0) with value 0
        bounds = ((0, 3), (0, 3), (0, 3))
        opt = GreedyWalk(sphere_fitness, bounds, seed=42)
        result = opt.run(50)
        # Should reach (0,0,0) since sphere has no local minima in integer space
        assert result.best_value == 0.0
        assert result.best_solution == (0, 0, 0)

    def test_custom_neighbor_fn(self, sphere_fitness):
        """Custom neighbor function is used when provided."""
        bounds = ((0, 5), (0, 5))

        # Custom neighbor: only change first coordinate
        def first_coord_only(dna, bounds):
            neighbors = []
            lo, hi = bounds[0]
            for val in range(lo, hi + 1):
                if val != dna[0]:
                    neighbors.append((val,) + dna[1:])
            return neighbors

        opt = GreedyWalk(
            sphere_fitness, bounds, neighbor_fn=first_coord_only, seed=42
        )
        result = opt.run(20)
        # The optimizer should still work; first coord should reach 0
        assert result.best_solution[0] == 0

    def test_seeding(self, sphere_fitness, standard_bounds):
        """Same seed produces identical results."""
        opt1 = GreedyWalk(sphere_fitness, standard_bounds, seed=99)
        result1 = opt1.run(30)

        opt2 = GreedyWalk(sphere_fitness, standard_bounds, seed=99)
        result2 = opt2.run(30)

        assert result1.best_solution == result2.best_solution
        assert result1.best_value == result2.best_value

    def test_continuation(self, sphere_fitness, standard_bounds):
        """Consecutive runs continue from prior state (no reset)."""
        opt = GreedyWalk(sphere_fitness, standard_bounds, seed=42)
        result1 = opt.run(10)
        result2 = opt.run(10)
        # Second run should be at least as good (keeps best-so-far)
        assert result2.best_value <= result1.best_value
        # Evaluations accumulate across runs
        assert result2.n_evaluations >= result1.n_evaluations

    def test_full_history(self, sphere_fitness, standard_bounds):
        """record_history=True populates full_history."""
        opt = GreedyWalk(
            sphere_fitness, standard_bounds, seed=42, record_history=True
        )
        result = opt.run(10)
        assert result.full_history is not None
        assert len(result.full_history) == 10
        for entry in result.full_history:
            assert "position" in entry
            assert "value" in entry
            assert "moved" in entry

    def test_history_monotonic(self, sphere_fitness, standard_bounds):
        """result.history is monotonically non-increasing."""
        opt = GreedyWalk(sphere_fitness, standard_bounds, seed=42)
        result = opt.run(30)
        for i in range(1, len(result.history)):
            assert result.history[i] <= result.history[i - 1]

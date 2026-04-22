"""Unit tests for TupleSpace, SearchSpace, and GraphSpace abstract guards."""

import numpy as np
import pytest

from cyopt.optimizers.greedy_walk import hamming_neighbors
from cyopt.spaces import GraphSpace, SearchSpace, TupleSpace


class TestConstruction:
    """TupleSpace construction and canonicalization behavior."""

    def test_dim_and_bounds(self):
        s = TupleSpace([(0, 9), (0, 5), (0, 3)])
        assert s.dim == 3
        assert s.bounds == ((0, 9), (0, 5), (0, 3))

    def test_accepts_list_of_tuples(self):
        # Sequence[tuple[int, int]]
        TupleSpace([(0, 1), (0, 2)])

    def test_accepts_tuple_of_tuples(self):
        TupleSpace(((0, 1), (0, 2)))

    def test_invalid_bounds_raise(self):
        with pytest.raises(ValueError, match="hi must be >= lo"):
            TupleSpace([(5, 2)])

    def test_normalizes_to_ints(self):
        # float bounds must normalize to ints in self.bounds
        s = TupleSpace([(0.0, 9.0)])
        # Trailing comma is REQUIRED: ((0, 9),) is a 1-tuple-of-tuples.
        # ((0, 9)) without the trailing comma is just the tuple (0, 9).
        assert s.bounds == ((0, 9),)
        assert all(isinstance(b, int) for pair in s.bounds for b in pair)


class TestRandom:
    """TupleSpace.random(rng) behavior."""

    def test_within_bounds(self):
        s = TupleSpace([(0, 9), (0, 5), (0, 3)])
        rng = np.random.default_rng(42)
        for _ in range(1000):
            x = s.random(rng)
            assert isinstance(x, tuple)
            assert len(x) == 3
            for val, (lo, hi) in zip(x, s.bounds):
                assert isinstance(val, int)
                assert lo <= val <= hi

    def test_deterministic(self):
        s = TupleSpace([(0, 9), (0, 9), (0, 9)])
        rng1 = np.random.default_rng(123)
        rng2 = np.random.default_rng(123)
        draws1 = [s.random(rng1) for _ in range(10)]
        draws2 = [s.random(rng2) for _ in range(10)]
        assert draws1 == draws2

    def test_output_hashable(self):
        s = TupleSpace([(0, 9)])
        rng = np.random.default_rng(0)
        d = {s.random(rng): 1}  # must not raise
        assert len(d) == 1


class TestNeighbors:
    """TupleSpace.neighbors(node) behavior; legacy parity."""

    def test_count(self):
        s = TupleSpace([(0, 2), (0, 2), (0, 2)])
        neighbors = list(s.neighbors((0, 0, 0)))
        # 2 non-self vals * 3 coords = 6
        assert len(neighbors) == 6

    def test_matches_legacy_hamming(self):
        s = TupleSpace([(0, 3), (0, 2), (0, 4)])
        dna = (1, 1, 2)
        expected = set(hamming_neighbors(dna, s.bounds))
        assert set(s.neighbors(dna)) == expected

    def test_wrong_dim_raises(self):
        s = TupleSpace([(0, 9), (0, 9)])
        with pytest.raises(ValueError):
            list(s.neighbors((0, 0, 0)))

    def test_degenerate_coord_skipped(self):
        s = TupleSpace([(0, 1), (5, 5), (0, 1)])
        # Degenerate coord (5, 5) contributes 0 neighbors.
        neighbors = list(s.neighbors((0, 5, 0)))
        # coord 0: 1 alt (val=1), coord 1: 0 alts, coord 2: 1 alt (val=1) -> 2
        assert len(neighbors) == 2
        assert (1, 5, 0) in neighbors
        assert (0, 5, 1) in neighbors


class TestAbstractClasses:
    """Abstract base classes reject direct instantiation."""

    def test_searchspace_not_instantiable(self):
        with pytest.raises(TypeError):
            SearchSpace()

    def test_graphspace_not_instantiable(self):
        with pytest.raises(TypeError):
            GraphSpace()

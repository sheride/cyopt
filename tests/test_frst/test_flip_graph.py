"""Unit + property tests for FRSTFlipGraphSpace.

Covers Phase 6 requirements:
- GRAPH-01: class works as a SearchSpace (construction, generator contract,
  hub-topology neighbor counts, neighbor validity, random validity).
- GRAPH-02: lazy validity filter never emits invalid DNAs.
- GRAPH-03: coarsening property -- flip neighbors are a subset of Hamming-1
  neighbors for every valid DNA.
"""

import inspect
from itertools import product

import pytest

from tests.test_frst.conftest import requires_cytools


@requires_cytools
class TestFRSTFlipGraphSpace:
    """Unit tests for FRSTFlipGraphSpace covering GRAPH-01."""

    def test_construction_requires_prepped_polytope(self):
        """Construction without prep_for_optimizers raises RuntimeError."""
        from cytools import fetch_polytopes

        import cyopt.frst  # noqa: F401 -- triggers patch_polytope
        from cyopt import FRSTFlipGraphSpace

        p = fetch_polytopes(h11=4, limit=10)[9]
        with pytest.raises(RuntimeError, match="prep_for_optimizers"):
            FRSTFlipGraphSpace(p)

    def test_construction_succeeds_when_prepped(self, poly_flip_small):
        """Constructing on a prepped polytope yields a GraphSpace instance."""
        from cyopt import FRSTFlipGraphSpace, GraphSpace

        space = FRSTFlipGraphSpace(poly_flip_small)
        assert isinstance(space, GraphSpace)
        assert space.polytope is poly_flip_small
        assert space.bounds == ((0, 2),)
        assert space.dim == 1

    def test_neighbors_is_a_generator(self, poly_flip_small):
        """neighbors(dna) must be a generator (lazy iteration contract)."""
        from cyopt import FRSTFlipGraphSpace

        space = FRSTFlipGraphSpace(poly_flip_small)
        result = space.neighbors((0,))
        assert inspect.isgenerator(result), (
            "FRSTFlipGraphSpace.neighbors must be a generator (use yield), "
            f"got {type(result).__name__}"
        )

    def test_neighbors_hub_topology(self, poly_flip_small):
        """Hub topology: face_ts[0]/[1] -> 1 neighbor each, face_ts[2] -> 2.

        Per RESEARCH.md Section 1, the single 2-face of poly_flip_small has
        3 FRTs in a hub configuration: face_ts[2] is the hub (2 flip
        neighbors), face_ts[0] and face_ts[1] are leaves (1 flip neighbor
        each, both pointing to the hub). The asymmetric counts also act as a
        regression check that the implementation uses real flip data, not a
        uniform Hamming neighborhood.
        """
        from cyopt import FRSTFlipGraphSpace

        space = FRSTFlipGraphSpace(poly_flip_small)
        assert len(list(space.neighbors((0,)))) == 1
        assert len(list(space.neighbors((1,)))) == 1
        assert len(list(space.neighbors((2,)))) == 2

    def test_neighbors_emit_valid_dnas(self, poly_flip_small):
        """Every emitted neighbor satisfies dna_to_frst(neighbor) is not None."""
        from cyopt import FRSTFlipGraphSpace

        space = FRSTFlipGraphSpace(poly_flip_small)
        for neighbor in space.neighbors((2,)):
            assert poly_flip_small.dna_to_frst(neighbor) is not None, (
                f"Invalid DNA {neighbor} leaked from neighbors((2,))"
            )

    def test_random_returns_valid_dna(self, poly_flip_small):
        """random(rng) returns a DNA inside bounds with non-None dna_to_frst."""
        import numpy as np

        from cyopt import FRSTFlipGraphSpace

        space = FRSTFlipGraphSpace(poly_flip_small)
        rng = np.random.default_rng(42)
        for _ in range(5):
            dna = space.random(rng)
            assert len(dna) == space.dim
            assert 0 <= dna[0] <= 2
            assert poly_flip_small.dna_to_frst(dna) is not None, (
                f"random() returned invalid DNA {dna}"
            )


@requires_cytools
def test_invalid_dnas_filtered(poly_flip_invalid):
    """GRAPH-02 regression: invalid DNAs (0,1,0) and (1,0,1) never emitted.

    Per RESEARCH.md Section 3, poly_flip_invalid has exactly 2 invalid DNAs
    (out of 8): dna_to_frst returns None for (0,1,0) and (1,0,1). The lazy
    validity filter in FRSTFlipGraphSpace.neighbors must prevent these
    DNAs from appearing as neighbors of any valid DNA.
    """
    from cyopt import FRSTFlipGraphSpace

    space = FRSTFlipGraphSpace(poly_flip_invalid)
    valid_dnas = [
        (0, 0, 0),
        (0, 0, 1),
        (0, 1, 1),
        (1, 0, 0),
        (1, 1, 0),
        (1, 1, 1),
    ]
    invalid_dnas = {(0, 1, 0), (1, 0, 1)}
    for dna in valid_dnas:
        nbs = set(space.neighbors(dna))
        leaked = nbs & invalid_dnas
        assert not leaked, (
            f"Invalid DNAs {leaked} leaked from neighbors({dna})"
        )


@requires_cytools
@pytest.mark.parametrize(
    "fixture_name", ["poly_flip_small", "poly_flip_invalid"]
)
def test_coarsening_of_hamming(fixture_name, request):
    """GRAPH-03 regression: flip neighbors are a subset of Hamming-1 neighbors.

    The defining property of the flip graph (D-06): each emitted DNA differs
    from the input in exactly one coordinate. Iterates every valid DNA in
    each fixture's space and asserts the subset relation against the
    canonical TupleSpace.neighbors (Hamming-1).
    """
    from cyopt import FRSTFlipGraphSpace
    from cyopt.spaces import TupleSpace

    poly = request.getfixturevalue(fixture_name)
    flip_space = FRSTFlipGraphSpace(poly)
    tuple_space = TupleSpace(poly._cyopt_bounds)

    for dna in product(*[range(lo, hi + 1) for lo, hi in poly._cyopt_bounds]):
        if poly.dna_to_frst(dna) is None:
            # Skip invalid starting points -- no flip semantics there.
            continue
        flip_nbs = set(flip_space.neighbors(dna))
        hamming_nbs = set(tuple_space.neighbors(dna))
        assert flip_nbs <= hamming_nbs, (
            f"Flip neighbors of {dna} are not a subset of Hamming "
            f"neighbors: flip={flip_nbs}, hamming={hamming_nbs}"
        )


@pytest.fixture(scope="module")
def poly_with_faces_for_flip():
    """h11=7 polytope (2 interesting faces) prepped for FRSTFlipGraphSpace.

    Mirrors test_wrapper.py:poly_with_faces. Used by the all-8-optimizers
    smoke test. Separate fixture (not imported from test_wrapper) keeps the
    tests independent.
    """
    try:
        from cytools import fetch_polytopes
    except ImportError:
        pytest.skip("CYTools not available")

    import cyopt.frst  # noqa: F401 -- triggers patch_polytope

    p = fetch_polytopes(h11=7, limit=1)[0]
    p.prep_for_optimizers()
    return p


@requires_cytools
def test_flip_graph_works_with_all_optimizers(poly_with_faces_for_flip):
    """All 8 optimizers accept FRSTFlipGraphSpace as space= and produce a
    Result with a valid best_solution.

    GRAPH-01 regression: the class is usable as space= for any of the 8
    generic optimizers (GA, RandomSample, GreedyWalk, BestFirstSearch,
    BasinHopping, DifferentialEvolution, MCMC, SimulatedAnnealing).
    Bypasses frst_optimizer (which always wires TupleSpace internally) by
    instantiating each optimizer directly, the way Phase 7's benchmark
    notebook will.
    """
    from cyopt import (
        GA,
        BasinHopping,
        BestFirstSearch,
        DifferentialEvolution,
        FRSTFlipGraphSpace,
        GreedyWalk,
        MCMC,
        RandomSample,
        SimulatedAnnealing,
    )

    poly = poly_with_faces_for_flip
    space = FRSTFlipGraphSpace(poly)

    # Build a fitness function that matches FRSTOptimizer._make_fitness:
    # DNA -> dna_to_frst -> get_cy -> target -> float (with penalty for
    # invalid). Since FRSTFlipGraphSpace.neighbors already filters invalid
    # DNAs, the penalty path is only exercised by GA/RandomSample/DE which
    # generate from bounds (not neighbors).
    def fitness(dna):
        triang = poly.dna_to_frst(dna)
        if triang is None:
            return float("inf")
        return float(triang.get_cy().h11())

    for cls in [
        GA,
        RandomSample,
        GreedyWalk,
        BestFirstSearch,
        BasinHopping,
        DifferentialEvolution,
        MCMC,
        SimulatedAnnealing,
    ]:
        opt = cls(fitness_fn=fitness, space=space, seed=42)
        result = opt.run(3)
        assert result.best_solution is not None, (
            f"{cls.__name__} returned None best_solution"
        )
        assert isinstance(result.best_value, float), (
            f"{cls.__name__} best_value is not float"
        )
        # Cross-check: best_solution should be a DNA of the right shape.
        # DE samples by bounds and may select an invalid DNA whose fitness
        # is the penalty; only assert shape.
        assert len(result.best_solution) == space.dim, (
            f"{cls.__name__} returned wrong-shape DNA"
        )

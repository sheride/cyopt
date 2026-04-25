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

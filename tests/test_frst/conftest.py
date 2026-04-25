"""Shared fixtures and markers for FRST tests."""

import pytest

try:
    from cytools import Polytope  # noqa: F401

    HAS_CYTOOLS = True
except ImportError:
    HAS_CYTOOLS = False

requires_cytools = pytest.mark.skipif(
    not HAS_CYTOOLS,
    reason="CYTools not available",
)


@pytest.fixture(scope="module")
def poly_h11_4():
    """A reflexive polytope with h11=4 (small but has interesting faces)."""
    from cytools import fetch_polytopes

    return fetch_polytopes(h11=4, limit=1)[0]


@pytest.fixture(scope="module")
def poly_flip_small():
    """Smallest viable flip-graph fixture: h11=4 polytope with 1 interesting
    face containing 3 FRTs (hub topology).

    bounds == ((0, 2),). Per-face flip neighbors verified live in
    RESEARCH.md Section 1: face_ts[0] and face_ts[1] each flip only to
    face_ts[2] (1 neighbor each); face_ts[2] flips to both face_ts[0] and
    face_ts[1] (2 neighbors). Used for unit tests of neighbors() and the
    coarsening property test.
    """
    try:
        from cytools import fetch_polytopes
    except ImportError:
        pytest.skip("CYTools not available")

    import cyopt.frst  # noqa: F401 -- triggers patch_polytope

    p = fetch_polytopes(h11=4, limit=10)[9]
    p.prep_for_optimizers()
    return p


@pytest.fixture(scope="module")
def poly_flip_invalid():
    """Smallest viable fixture for the lazy-validity filter (GRAPH-02).

    h11=6 polytope (idx=2) with 3 interesting faces and bounds
    ((0,1),(0,1),(0,1)) -- 8 total DNAs. Verified live in RESEARCH.md
    Section 3: DNAs (0,1,0) and (1,0,1) are non-solid (dna_to_frst returns
    None); the other 6 DNAs are valid. Used to assert that
    FRSTFlipGraphSpace.neighbors never emits the 2 invalid DNAs.
    """
    try:
        from cytools import fetch_polytopes
    except ImportError:
        pytest.skip("CYTools not available")

    import cyopt.frst  # noqa: F401 -- triggers patch_polytope

    p = fetch_polytopes(h11=6, limit=20)[2]
    p.prep_for_optimizers()
    return p

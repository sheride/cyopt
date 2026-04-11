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

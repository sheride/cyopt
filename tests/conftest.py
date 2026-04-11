"""Shared test fixtures for cyopt test suite."""

import pytest


@pytest.fixture
def sphere_fitness():
    """Fitness function computing sum of squares (minimum at origin)."""

    def _fitness(dna: tuple[int, ...]) -> float:
        return float(sum(x * x for x in dna))

    return _fitness


@pytest.fixture
def standard_bounds():
    """3D search space with bounds (0, 9) per dimension."""
    return ((0, 9), (0, 9), (0, 9))


@pytest.fixture
def small_bounds():
    """Tiny 2D search space for exhaustive testing."""
    return ((0, 2), (0, 2))

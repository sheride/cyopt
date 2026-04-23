"""Unit tests for BasinHopping optimizer."""

import pytest

from cyopt import TupleSpace
from cyopt.optimizers.basin_hopping import BasinHopping
from cyopt.spaces import GraphSpace


def sphere_fitness(dna):
    return float(sum(x * x for x in dna))


BOUNDS_3D = ((0, 9), (0, 9), (0, 9))
SPACE_3D = TupleSpace(BOUNDS_3D)


class _BareGraph(GraphSpace):
    """Minimal concrete GraphSpace with NO ``bounds`` attribute."""

    def random(self, rng):
        return (0,)

    def neighbors(self, node):
        return []


def test_bh_rejects_non_tuple_space_without_perturb_fn():
    """Constructing BasinHopping with a bare GraphSpace and no perturb_fn raises TypeError."""
    space = _BareGraph()
    with pytest.raises(TypeError, match="perturb_fn"):
        BasinHopping(sphere_fitness, space, seed=42)


def test_bh_accepts_non_tuple_space_with_perturb_fn():
    """Constructing BasinHopping with a bare GraphSpace + custom perturb_fn succeeds."""
    space = _BareGraph()

    def my_perturb(dna, rng):
        return dna

    opt = BasinHopping(
        sphere_fitness, space, perturb_fn=my_perturb, seed=42,
    )
    assert opt is not None


def test_finds_improvement():
    """BasinHopping should find a solution better than worst possible."""
    opt = BasinHopping(sphere_fitness, SPACE_3D, seed=42)
    result = opt.run(30)
    # Worst possible: (9,9,9) = 243
    assert result.best_value < 243


def test_custom_local_minimize_fn():
    """Injectable local_minimize_fn should be called during optimization."""
    called = {"count": 0}

    def tracking_minimizer(dna, space, evaluate_fn):
        called["count"] += 1
        return dna  # no-op minimizer

    opt = BasinHopping(
        sphere_fitness, SPACE_3D,
        local_minimize_fn=tracking_minimizer, seed=42,
    )
    opt.run(5)
    assert called["count"] > 0


def test_custom_perturb_fn():
    """Injectable perturb_fn should be called during optimization."""
    called = {"count": 0}
    local_bounds = BOUNDS_3D

    def tracking_perturb(dna, rng):
        called["count"] += 1
        # Just flip first dimension
        result = list(dna)
        result[0] = int(rng.integers(local_bounds[0][0], local_bounds[0][1] + 1))
        return tuple(result)

    opt = BasinHopping(
        sphere_fitness, SPACE_3D,
        perturb_fn=tracking_perturb, seed=42,
    )
    opt.run(5)
    assert called["count"] > 0


def test_seeding():
    """Two runs with the same seed should produce identical results."""
    opt1 = BasinHopping(sphere_fitness, SPACE_3D, seed=777)
    r1 = opt1.run(20)

    opt2 = BasinHopping(sphere_fitness, SPACE_3D, seed=777)
    r2 = opt2.run(20)

    assert r1.best_solution == r2.best_solution
    assert r1.best_value == r2.best_value
    assert r1.n_evaluations == r2.n_evaluations


def test_continuation():
    """State should persist across consecutive run() calls."""
    opt = BasinHopping(sphere_fitness, SPACE_3D, seed=42)
    r1 = opt.run(15)
    evals_after_first = r1.n_evaluations
    best_after_first = r1.best_value

    r2 = opt.run(15)
    assert r2.n_evaluations > evals_after_first
    assert r2.best_value <= best_after_first


def test_invalid_temperature():
    """Temperature <= 0 should raise ValueError."""
    with pytest.raises(ValueError):
        BasinHopping(sphere_fitness, SPACE_3D, temperature=0)
    with pytest.raises(ValueError):
        BasinHopping(sphere_fitness, SPACE_3D, temperature=-1)


def test_result_fields():
    """Result should have correct types and solution within bounds."""
    opt = BasinHopping(sphere_fitness, SPACE_3D, seed=42)
    result = opt.run(10)

    assert isinstance(result.best_solution, tuple)
    assert isinstance(result.best_value, float)
    assert isinstance(result.n_evaluations, int)
    assert isinstance(result.wall_time, float)
    assert len(result.history) == 10

    for val, (lo, hi) in zip(result.best_solution, BOUNDS_3D):
        assert lo <= val <= hi

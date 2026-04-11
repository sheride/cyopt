"""Unit tests for DifferentialEvolution optimizer."""

import pytest

from cyopt.optimizers.differential_evolution import DifferentialEvolution


def sphere_fitness(dna):
    return float(sum(x * x for x in dna))


BOUNDS_3D = ((0, 9), (0, 9), (0, 9))


def test_finds_improvement():
    """DE should find a solution better than worst possible."""
    opt = DifferentialEvolution(sphere_fitness, BOUNDS_3D, seed=42)
    result = opt.run(10)
    # Worst possible: (9,9,9) = 243
    assert result.best_value < 243


def test_step_raises():
    """_step() should raise NotImplementedError."""
    opt = DifferentialEvolution(sphere_fitness, BOUNDS_3D, seed=42)
    with pytest.raises(NotImplementedError):
        opt._step(0)


def test_seeding():
    """Two runs with the same seed should produce identical results."""
    opt1 = DifferentialEvolution(sphere_fitness, BOUNDS_3D, seed=777, popsize=5)
    r1 = opt1.run(5)

    opt2 = DifferentialEvolution(sphere_fitness, BOUNDS_3D, seed=777, popsize=5)
    r2 = opt2.run(5)

    assert r1.best_solution == r2.best_solution
    assert r1.best_value == r2.best_value


def test_continuation():
    """Evaluations should accumulate across consecutive run() calls."""
    opt = DifferentialEvolution(sphere_fitness, BOUNDS_3D, seed=42, popsize=5)
    r1 = opt.run(3)
    evals_after_first = r1.n_evaluations

    r2 = opt.run(3)
    assert r2.n_evaluations > evals_after_first


def test_history_populated():
    """History should have entries from DE callback."""
    opt = DifferentialEvolution(sphere_fitness, BOUNDS_3D, seed=42, popsize=5)
    result = opt.run(10)
    assert len(result.history) > 0


def test_bounds_respected():
    """Best solution values should be within original (lo, hi) inclusive bounds."""
    opt = DifferentialEvolution(sphere_fitness, BOUNDS_3D, seed=42)
    result = opt.run(10)

    for val, (lo, hi) in zip(result.best_solution, BOUNDS_3D):
        assert lo <= val <= hi


def test_result_fields():
    """Result should have correct types."""
    opt = DifferentialEvolution(sphere_fitness, BOUNDS_3D, seed=42, popsize=5)
    result = opt.run(5)

    assert isinstance(result.best_solution, tuple)
    assert isinstance(result.best_value, float)
    assert isinstance(result.n_evaluations, int)
    assert isinstance(result.wall_time, float)
    assert result.full_history is None


def test_uses_public_api():
    """DifferentialEvolution should not use scipy private API."""
    import inspect
    import cyopt.optimizers.differential_evolution as de_module

    source = inspect.getsource(de_module)
    assert "scipy.optimize._" not in source

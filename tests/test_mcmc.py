"""Unit tests for MCMC optimizer."""

import pytest

from cyopt import TupleSpace
from cyopt.optimizers.neighbors import random_single_flip
from cyopt.optimizers.mcmc import MCMC
from cyopt.spaces import GraphSpace


def sphere_fitness(dna):
    return float(sum(x * x for x in dna))


BOUNDS_3D = ((0, 9), (0, 9), (0, 9))
SPACE_3D = TupleSpace(BOUNDS_3D)


class _BareGraph(GraphSpace):
    """Minimal concrete GraphSpace with NO ``bounds`` attribute.

    Used to verify that optimizers whose default step/perturb function
    requires a TupleSpace fail fast at ``__init__`` rather than mid-run
    with an opaque ``AttributeError``.
    """

    def random(self, rng):
        return (0,)

    def neighbors(self, node):
        return []


def test_mcmc_rejects_non_tuple_space_without_step_fn():
    """Constructing MCMC with a bare GraphSpace and no step_fn raises TypeError."""
    space = _BareGraph()
    with pytest.raises(TypeError, match="step_fn"):
        MCMC(sphere_fitness, space, seed=42)


def test_mcmc_accepts_non_tuple_space_with_step_fn():
    """Constructing MCMC with a bare GraphSpace + custom step_fn succeeds."""
    space = _BareGraph()

    def my_step(dna, rng):
        return dna

    opt = MCMC(sphere_fitness, space, step_fn=my_step, seed=42)
    assert opt is not None


class TestMCMC:
    """Tests for MCMC optimizer."""

    def test_finds_improvement(self):
        """MCMC finds solution better than worst case."""
        opt = MCMC(sphere_fitness, SPACE_3D, seed=42)
        result = opt.run(100)
        assert result.best_value < 243

    def test_custom_step_fn(self):
        """Custom step_fn is called during optimization."""
        called = {"count": 0}
        local_bounds = BOUNDS_3D

        def tracking_step(dna, rng):
            called["count"] += 1
            return random_single_flip(dna, local_bounds, rng)

        opt = MCMC(
            sphere_fitness, SPACE_3D,
            step_fn=tracking_step, seed=42,
        )
        opt.run(20)
        assert called["count"] > 0

    def test_invalid_temperature_zero(self):
        """Temperature of 0 raises ValueError."""
        with pytest.raises(ValueError, match="temperature must be positive"):
            MCMC(sphere_fitness, SPACE_3D, temperature=0)

    def test_invalid_temperature_negative(self):
        """Negative temperature raises ValueError."""
        with pytest.raises(ValueError, match="temperature must be positive"):
            MCMC(sphere_fitness, SPACE_3D, temperature=-1)

    def test_seeding(self):
        """Same seed produces identical results."""
        opt1 = MCMC(sphere_fitness, SPACE_3D, seed=777)
        result1 = opt1.run(50)

        opt2 = MCMC(sphere_fitness, SPACE_3D, seed=777)
        result2 = opt2.run(50)

        assert result1.best_solution == result2.best_solution
        assert result1.best_value == result2.best_value
        assert result1.history == result2.history
        assert result1.n_evaluations == result2.n_evaluations

    def test_continuation(self):
        """State persists across consecutive run() calls."""
        opt = MCMC(sphere_fitness, SPACE_3D, seed=42)
        r1 = opt.run(50)
        n_evals_1 = r1.n_evaluations
        best_1 = r1.best_value

        r2 = opt.run(50)
        assert r2.n_evaluations > n_evals_1
        assert r2.best_value <= best_1

    def test_record_history(self):
        """full_history populated with accepted key."""
        opt = MCMC(sphere_fitness, SPACE_3D, seed=42, record_history=True)
        result = opt.run(20)
        assert result.full_history is not None
        assert len(result.full_history) > 0
        assert "accepted" in result.full_history[0]
        assert "position" in result.full_history[0]
        assert "value" in result.full_history[0]

"""Tests for the callback system (CORE-08).

Tests cover:
- Callbacks parameter accepted by all optimizers
- Info dict contains required fields
- Early stopping via return True
- Non-True returns do not trigger early stopping
- DE callbacks work through SciPy's native callback mechanism
"""

from __future__ import annotations

import pytest

from cyopt._types import DNA, Bounds, Callback, CallbackInfo
from cyopt.optimizers.random_sample import RandomSample
from cyopt.optimizers.ga import GA
from cyopt.optimizers.greedy_walk import GreedyWalk
from cyopt.optimizers.best_first_search import BestFirstSearch
from cyopt.optimizers.basin_hopping import BasinHopping
from cyopt.optimizers.mcmc import MCMC
from cyopt.optimizers.simulated_annealing import SimulatedAnnealing
from cyopt.optimizers.differential_evolution import DifferentialEvolution


BOUNDS: Bounds = ((0, 9), (0, 9))


def sphere(dna: DNA) -> float:
    """Simple sphere function for testing."""
    return sum(x**2 for x in dna)


class TestCallbackEmptyList:
    """Optimizer with callbacks=[] runs normally (no regression)."""

    def test_random_sample_empty_callbacks(self):
        opt = RandomSample(sphere, BOUNDS, seed=42, callbacks=[])
        result = opt.run(10)
        assert len(result.history) == 10

    def test_ga_empty_callbacks(self):
        opt = GA(sphere, BOUNDS, seed=42, callbacks=[])
        result = opt.run(5)
        assert len(result.history) == 5


class TestCallbackInfoDict:
    """Callback receives info dict with required keys."""

    def test_info_dict_keys(self):
        received = []

        def recorder(info: CallbackInfo) -> None:
            received.append(dict(info))

        opt = RandomSample(sphere, BOUNDS, seed=42, callbacks=[recorder])
        opt.run(5)

        assert len(received) == 5
        required_keys = {"iteration", "best_value", "best_solution", "n_evaluations", "wall_time"}
        for info in received:
            assert required_keys <= set(info.keys()), f"Missing keys: {required_keys - set(info.keys())}"

    def test_info_dict_types(self):
        received = []

        def recorder(info: CallbackInfo) -> None:
            received.append(dict(info))

        opt = RandomSample(sphere, BOUNDS, seed=42, callbacks=[recorder])
        opt.run(3)

        info = received[0]
        assert isinstance(info["iteration"], int)
        assert isinstance(info["best_value"], (int, float))
        assert isinstance(info["best_solution"], tuple)
        assert isinstance(info["n_evaluations"], int)
        assert isinstance(info["wall_time"], float)


class TestMultipleCallbacks:
    """Multiple callbacks all invoked in order."""

    def test_order_preserved(self):
        call_order = []

        def cb_a(info: CallbackInfo) -> None:
            call_order.append("a")

        def cb_b(info: CallbackInfo) -> None:
            call_order.append("b")

        opt = RandomSample(sphere, BOUNDS, seed=42, callbacks=[cb_a, cb_b])
        opt.run(3)

        # Should alternate: a, b, a, b, a, b
        assert call_order == ["a", "b"] * 3


class TestEarlyStopTrueOnly:
    """Only `return True` triggers early stopping."""

    def test_return_true_stops(self):
        def stop_at_3(info: CallbackInfo) -> bool:
            return info["iteration"] >= 2  # True on iteration 2

        opt = RandomSample(sphere, BOUNDS, seed=42, callbacks=[stop_at_3])
        result = opt.run(100)
        # Should stop early -- history length < 100
        assert len(result.history) < 100

    def test_return_none_does_not_stop(self):
        def return_none(info: CallbackInfo) -> None:
            return None

        opt = RandomSample(sphere, BOUNDS, seed=42, callbacks=[return_none])
        result = opt.run(20)
        assert len(result.history) == 20

    def test_return_false_does_not_stop(self):
        def return_false(info: CallbackInfo) -> bool:
            return False

        opt = RandomSample(sphere, BOUNDS, seed=42, callbacks=[return_false])
        result = opt.run(20)
        assert len(result.history) == 20

    def test_return_dict_does_not_stop(self):
        """Truthy dict should NOT trigger early stop (only `is True` does)."""
        def return_dict(info: CallbackInfo) -> dict:
            return {"logged": True}  # truthy but not `is True`

        opt = RandomSample(sphere, BOUNDS, seed=42, callbacks=[return_dict])
        result = opt.run(20)
        assert len(result.history) == 20


class TestDECallbacks:
    """DE callbacks work through SciPy's native callback mechanism."""

    def test_de_callback_invoked(self):
        received = []

        def recorder(info: CallbackInfo) -> None:
            received.append(dict(info))

        opt = DifferentialEvolution(sphere, BOUNDS, seed=42, callbacks=[recorder])
        opt.run(3)

        assert len(received) > 0
        required_keys = {"iteration", "best_value", "best_solution", "n_evaluations", "wall_time"}
        for info in received:
            assert required_keys <= set(info.keys())

    def test_de_early_stop(self):
        call_count = 0

        def stop_after_1(info: CallbackInfo) -> bool:
            nonlocal call_count
            call_count += 1
            return call_count >= 2  # Stop after 2nd generation

        opt = DifferentialEvolution(sphere, BOUNDS, seed=42, callbacks=[stop_after_1])
        result = opt.run(100)
        # Should have stopped early
        assert len(result.history) < 100


class TestCallbacksAfterResume:
    """Callbacks fire correctly after loading from checkpoint."""

    def test_callbacks_after_resume(self, tmp_path):
        """Callbacks fire correctly after loading from checkpoint."""
        values = []
        def recorder(info):
            values.append(info['best_value'])

        opt = RandomSample(fitness_fn=sphere, bounds=BOUNDS, seed=42)
        opt.run(20)
        path = tmp_path / "test.ckpt"
        opt.save_checkpoint(path)

        loaded = RandomSample.load_checkpoint(path, fitness_fn=sphere, callbacks=[recorder])
        loaded.run(10)
        assert len(values) == 10


class TestAllOptimizersAcceptCallbacks:
    """Every optimizer constructor accepts callbacks parameter."""

    @pytest.mark.parametrize("OptimizerClass", [
        RandomSample,
        GA,
        GreedyWalk,
        BestFirstSearch,
        BasinHopping,
        MCMC,
        SimulatedAnnealing,
        DifferentialEvolution,
    ])
    def test_accepts_callbacks(self, OptimizerClass):
        received = []

        def recorder(info: CallbackInfo) -> None:
            received.append(info)

        opt = OptimizerClass(sphere, BOUNDS, seed=42, callbacks=[recorder])
        result = opt.run(3)
        assert len(received) > 0

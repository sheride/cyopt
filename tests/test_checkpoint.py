"""Tests for checkpoint/resume serialization (CORE-09)."""

from __future__ import annotations

import pickle
import tempfile
from pathlib import Path

import numpy as np
import pytest

from cyopt.optimizers.ga import GA
from cyopt.optimizers.random_sample import RandomSample


def _sphere(dna):
    """Simple sphere function for testing."""
    return sum(x ** 2 for x in dna)


BOUNDS = ((0, 10), (0, 10), (0, 10))


class TestSaveLoadBasic:
    """Tests for basic save/load checkpoint functionality."""

    def test_save_creates_file(self, tmp_path):
        """save_checkpoint creates a file at the given path."""
        opt = GA(_sphere, BOUNDS, population_size=6, seed=42)
        opt.run(5)
        ckpt_path = tmp_path / "test.ckpt"
        opt.save_checkpoint(ckpt_path)
        assert ckpt_path.exists()

    def test_load_reconstructs_runnable_optimizer(self, tmp_path):
        """load_checkpoint with correct class reconstructs an optimizer that can run()."""
        opt = GA(_sphere, BOUNDS, population_size=6, seed=42)
        opt.run(5)
        ckpt_path = tmp_path / "test.ckpt"
        opt.save_checkpoint(ckpt_path)

        loaded = GA.load_checkpoint(ckpt_path, _sphere)
        result = loaded.run(5)
        assert result.best_solution is not None
        assert result.best_value <= _sphere(result.best_solution)

    def test_loaded_has_same_state(self, tmp_path):
        """Loaded optimizer has same best_value, best_solution, n_evaluations."""
        opt = GA(_sphere, BOUNDS, population_size=6, seed=42)
        opt.run(10)
        ckpt_path = tmp_path / "test.ckpt"
        opt.save_checkpoint(ckpt_path)

        loaded = GA.load_checkpoint(ckpt_path, _sphere)
        assert loaded._best_value == opt._best_value
        assert loaded._best_solution == opt._best_solution
        assert loaded._n_evaluations == opt._n_evaluations

    def test_cache_preserved(self, tmp_path):
        """Loaded optimizer's cache contains same entries as saved."""
        opt = RandomSample(_sphere, BOUNDS, seed=42)
        opt.run(20)
        ckpt_path = tmp_path / "test.ckpt"
        opt.save_checkpoint(ckpt_path)

        loaded = RandomSample.load_checkpoint(ckpt_path, _sphere)
        assert len(loaded._cache) == len(opt._cache)
        # Verify a few specific entries
        for key in list(opt._cache._cache.keys())[:5]:
            assert key in loaded._cache
            assert loaded._cache[key] == opt._cache[key]

    def test_iteration_offset_continues(self, tmp_path):
        """Iteration count continues from checkpoint (not reset to 0)."""
        opt = RandomSample(_sphere, BOUNDS, seed=42)
        opt.run(50)
        ckpt_path = tmp_path / "test.ckpt"
        opt.save_checkpoint(ckpt_path)

        loaded = RandomSample.load_checkpoint(ckpt_path, _sphere)
        assert loaded._iteration_offset == 50

        # Run more iterations -- callbacks should see offset iterations
        iterations_seen = []
        def track_iter(info):
            iterations_seen.append(info['iteration'])
        loaded._callbacks = [track_iter]
        loaded.run(10)
        assert iterations_seen[0] == 50  # First iteration after resume
        assert iterations_seen[-1] == 59  # Last iteration

    def test_checkpoint_has_version(self, tmp_path):
        """Checkpoint file contains _checkpoint_version key."""
        opt = RandomSample(_sphere, BOUNDS, seed=42)
        opt.run(5)
        ckpt_path = tmp_path / "test.ckpt"
        opt.save_checkpoint(ckpt_path)

        with open(ckpt_path, 'rb') as f:
            state = pickle.load(f)
        assert '_checkpoint_version' in state
        assert isinstance(state['_checkpoint_version'], int)

    def test_wrong_version_raises(self, tmp_path):
        """Loading checkpoint with wrong version raises informative error."""
        opt = RandomSample(_sphere, BOUNDS, seed=42)
        opt.run(5)
        ckpt_path = tmp_path / "test.ckpt"
        opt.save_checkpoint(ckpt_path)

        # Tamper with version
        with open(ckpt_path, 'rb') as f:
            state = pickle.load(f)
        state['_checkpoint_version'] = 999
        with open(ckpt_path, 'wb') as f:
            pickle.dump(state, f)

        with pytest.raises(ValueError, match="version"):
            RandomSample.load_checkpoint(ckpt_path, _sphere)

    def test_class_mismatch_raises(self, tmp_path):
        """Loading checkpoint with mismatched class name raises TypeError."""
        opt = RandomSample(_sphere, BOUNDS, seed=42)
        opt.run(5)
        ckpt_path = tmp_path / "test.ckpt"
        opt.save_checkpoint(ckpt_path)

        with pytest.raises(TypeError, match="RandomSample.*GA"):
            GA.load_checkpoint(ckpt_path, _sphere)


class TestGAInitializationGuard:
    """Tests for GA's initialization guard preventing population overwrite on resume."""

    def test_ga_population_not_overwritten_on_resume(self, tmp_path):
        """After loading checkpoint, GA.run() should NOT re-initialize population."""
        opt = GA(_sphere, BOUNDS, population_size=6, seed=42)
        opt.run(10)
        saved_population = opt._population.copy()
        ckpt_path = tmp_path / "test.ckpt"
        opt.save_checkpoint(ckpt_path)

        loaded = GA.load_checkpoint(ckpt_path, _sphere)
        # Population should be restored from checkpoint
        np.testing.assert_array_equal(loaded._population, saved_population)
        # Running should not reset population (it continues evolution)
        loaded.run(1)
        # After one more generation, population should have evolved (not be random init)
        # We just verify it didn't crash and the loaded flag is set
        assert loaded._initialized is True


class TestAllOptimizers:
    """Test checkpoint roundtrip for all 8 optimizers."""

    @pytest.fixture(params=[
        ("GA", {"population_size": 6}),
        ("RandomSample", {}),
        ("GreedyWalk", {}),
        ("BestFirstSearch", {"mode": "backtrack"}),
        ("BestFirstSearch_frontier", {"mode": "frontier"}),
        ("BasinHopping", {"temperature": 1.0}),
        ("MCMC", {"temperature": 1.0}),
        ("SimulatedAnnealing", {"n_iterations": 100}),
        ("DifferentialEvolution", {"popsize": 5}),
    ])
    def optimizer_info(self, request):
        name, kwargs = request.param
        # Import the right class
        if name == "GA":
            from cyopt.optimizers.ga import GA as cls
        elif name == "RandomSample":
            from cyopt.optimizers.random_sample import RandomSample as cls
        elif name == "GreedyWalk":
            from cyopt.optimizers.greedy_walk import GreedyWalk as cls
        elif name.startswith("BestFirstSearch"):
            from cyopt.optimizers.best_first_search import BestFirstSearch as cls
        elif name == "BasinHopping":
            from cyopt.optimizers.basin_hopping import BasinHopping as cls
        elif name == "MCMC":
            from cyopt.optimizers.mcmc import MCMC as cls
        elif name == "SimulatedAnnealing":
            from cyopt.optimizers.simulated_annealing import SimulatedAnnealing as cls
        elif name == "DifferentialEvolution":
            from cyopt.optimizers.differential_evolution import DifferentialEvolution as cls
        else:
            raise ValueError(f"Unknown optimizer: {name}")
        return name, cls, kwargs

    def test_roundtrip(self, optimizer_info, tmp_path):
        """Save and load checkpoint for each optimizer."""
        name, cls, kwargs = optimizer_info
        opt = cls(_sphere, BOUNDS, seed=42, **kwargs)
        opt.run(10)
        ckpt_path = tmp_path / f"{name}.ckpt"
        opt.save_checkpoint(ckpt_path)

        loaded = cls.load_checkpoint(ckpt_path, _sphere)
        assert loaded._best_value == opt._best_value
        assert loaded._best_solution == opt._best_solution
        assert loaded._n_evaluations == opt._n_evaluations
        # Can run again without error
        result = loaded.run(5)
        assert result.best_solution is not None

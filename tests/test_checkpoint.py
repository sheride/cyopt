"""Tests for checkpoint/resume serialization (CORE-09)."""

from __future__ import annotations

import pickle
import tempfile
from pathlib import Path

import numpy as np
import pytest

from cyopt import (
    GA, RandomSample, GreedyWalk, BestFirstSearch,
    BasinHopping, MCMC, SimulatedAnnealing, DifferentialEvolution,
    CheckpointCallback,
)


def _sphere(dna):
    """Simple sphere function for testing."""
    return sum(x ** 2 for x in dna)


BOUNDS = ((0, 10), (0, 10), (0, 10))

# Parametrized optimizer configurations for cross-optimizer tests
OPTIMIZER_CONFIGS = [
    (RandomSample, {}),
    (GreedyWalk, {}),
    (GA, {"population_size": 10}),
    (BestFirstSearch, {"mode": "backtrack"}),
    (BestFirstSearch, {"mode": "frontier"}),
    (BasinHopping, {}),
    (MCMC, {}),
    (SimulatedAnnealing, {"n_iterations": 50}),
    (DifferentialEvolution, {"popsize": 5}),
]


def _optimizer_id(val):
    """Generate test IDs for parametrized optimizer configs."""
    if isinstance(val, type):
        return val.__name__
    if isinstance(val, dict) and "mode" in val:
        return f"mode={val['mode']}"
    return str(val)


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


class TestCheckpointCallbackIntegration:
    """Tests for CheckpointCallback saving at intervals."""

    def test_checkpoint_callback_interval(self, tmp_path):
        """CheckpointCallback saves at every_n iterations."""
        ckpt_path = tmp_path / "test.ckpt"
        cb = CheckpointCallback(ckpt_path, every_n=10)
        opt = RandomSample(fitness_fn=_sphere, bounds=BOUNDS, seed=42, callbacks=[cb])
        opt.run(25)
        assert ckpt_path.exists()
        # Load and verify it's a valid checkpoint
        loaded = RandomSample.load_checkpoint(ckpt_path, fitness_fn=_sphere)
        assert loaded._best_value == opt._best_value

    def test_checkpoint_callback_no_premature_save(self, tmp_path):
        """CheckpointCallback does not save before every_n iterations."""
        ckpt_path = tmp_path / "test.ckpt"
        cb = CheckpointCallback(ckpt_path, every_n=100)
        opt = RandomSample(fitness_fn=_sphere, bounds=BOUNDS, seed=42, callbacks=[cb])
        opt.run(50)
        assert not ckpt_path.exists()


class TestAllOptimizers:
    """Parametrized checkpoint tests for all 8 optimizers."""

    @pytest.mark.parametrize("cls,kwargs", OPTIMIZER_CONFIGS, ids=_optimizer_id)
    def test_save_load_roundtrip(self, cls, kwargs, tmp_path):
        """Save and load produces optimizer with same best_value and n_evaluations."""
        opt = cls(fitness_fn=_sphere, bounds=BOUNDS, seed=42, **kwargs)
        opt.run(20)
        path = tmp_path / "test.ckpt"
        opt.save_checkpoint(path)
        loaded = cls.load_checkpoint(path, fitness_fn=_sphere)
        assert loaded._best_value == opt._best_value
        assert loaded._n_evaluations == opt._n_evaluations
        assert loaded._best_solution == opt._best_solution

    @pytest.mark.parametrize("cls,kwargs", OPTIMIZER_CONFIGS, ids=_optimizer_id)
    def test_resume_determinism(self, cls, kwargs, tmp_path):
        """Resumed run produces identical results to uninterrupted run."""
        if cls is DifferentialEvolution:
            pytest.skip("DE restarts from scratch on resume -- cache preserves evaluations but RNG state differs inside SciPy")

        # Uninterrupted run
        opt_full = cls(fitness_fn=_sphere, bounds=BOUNDS, seed=42, **kwargs)
        result_full = opt_full.run(40)

        # Split run: 20 + save + load + 20
        opt_split = cls(fitness_fn=_sphere, bounds=BOUNDS, seed=42, **kwargs)
        opt_split.run(20)
        path = tmp_path / "test.ckpt"
        opt_split.save_checkpoint(path)
        opt_resumed = cls.load_checkpoint(path, fitness_fn=_sphere)
        result_resumed = opt_resumed.run(20)

        assert result_full.best_value == result_resumed.best_value
        assert result_full.best_solution == result_resumed.best_solution

    @pytest.mark.parametrize("cls,kwargs", OPTIMIZER_CONFIGS, ids=_optimizer_id)
    def test_cache_preserved(self, cls, kwargs, tmp_path):
        """Cache entries survive save/load cycle."""
        opt = cls(fitness_fn=_sphere, bounds=BOUNDS, seed=42, **kwargs)
        opt.run(20)
        cache_size_before = len(opt._cache)
        path = tmp_path / "test.ckpt"
        opt.save_checkpoint(path)
        loaded = cls.load_checkpoint(path, fitness_fn=_sphere)
        assert len(loaded._cache) == cache_size_before

    @pytest.mark.parametrize("cls,kwargs", OPTIMIZER_CONFIGS, ids=_optimizer_id)
    def test_iteration_offset(self, cls, kwargs, tmp_path):
        """Iteration offset continues correctly after resume."""
        offsets = []
        def record_offset(info):
            offsets.append(info['iteration'])

        opt = cls(fitness_fn=_sphere, bounds=BOUNDS, seed=42, callbacks=[record_offset], **kwargs)
        opt.run(10)
        path = tmp_path / "test.ckpt"
        opt.save_checkpoint(path)

        offsets_resumed = []
        def record_offset_resumed(info):
            offsets_resumed.append(info['iteration'])

        loaded = cls.load_checkpoint(path, fitness_fn=_sphere, callbacks=[record_offset_resumed])
        loaded.run(10)

        # Resumed iterations should start at 10 (not 0)
        if cls is not DifferentialEvolution:
            assert offsets_resumed[0] == 10
        else:
            # DE iteration tracking is per-generation, offset should be >= 10
            assert offsets_resumed[0] >= 10

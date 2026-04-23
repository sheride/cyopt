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
    CheckpointCallback, TupleSpace,
)
from cyopt.checkpoint import CHECKPOINT_VERSION, _migrate


def _sphere(dna):
    """Simple sphere function for testing."""
    return sum(x ** 2 for x in dna)


BOUNDS = ((0, 10), (0, 10), (0, 10))
SPACE = TupleSpace(BOUNDS)

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
        opt = GA(_sphere, space=SPACE, population_size=6, seed=42)
        opt.run(5)
        ckpt_path = tmp_path / "test.ckpt"
        opt.save_checkpoint(ckpt_path)
        assert ckpt_path.exists()

    def test_load_reconstructs_runnable_optimizer(self, tmp_path):
        """load_checkpoint with correct class reconstructs an optimizer that can run()."""
        opt = GA(_sphere, space=SPACE, population_size=6, seed=42)
        opt.run(5)
        ckpt_path = tmp_path / "test.ckpt"
        opt.save_checkpoint(ckpt_path)

        loaded = GA.load_checkpoint(ckpt_path, _sphere)
        result = loaded.run(5)
        assert result.best_solution is not None
        assert result.best_value <= _sphere(result.best_solution)

    def test_loaded_has_same_state(self, tmp_path):
        """Loaded optimizer has same best_value, best_solution, n_evaluations."""
        opt = GA(_sphere, space=SPACE, population_size=6, seed=42)
        opt.run(10)
        ckpt_path = tmp_path / "test.ckpt"
        opt.save_checkpoint(ckpt_path)

        loaded = GA.load_checkpoint(ckpt_path, _sphere)
        assert loaded._best_value == opt._best_value
        assert loaded._best_solution == opt._best_solution
        assert loaded._n_evaluations == opt._n_evaluations

    def test_cache_preserved_save_load(self, tmp_path):
        """Loaded optimizer's cache contains same entries as saved (RandomSample-specific)."""
        opt = RandomSample(_sphere, space=SPACE, seed=42)
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
        opt = RandomSample(_sphere, space=SPACE, seed=42)
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
        """Checkpoint file contains _checkpoint_version key set to CHECKPOINT_VERSION."""
        opt = RandomSample(_sphere, space=SPACE, seed=42)
        opt.run(5)
        ckpt_path = tmp_path / "test.ckpt"
        opt.save_checkpoint(ckpt_path)

        with open(ckpt_path, 'rb') as f:
            state = pickle.load(f)
        assert '_checkpoint_version' in state
        assert state['_checkpoint_version'] == CHECKPOINT_VERSION

    def test_wrong_version_raises(self, tmp_path):
        """Loading checkpoint with wrong version raises informative error."""
        opt = RandomSample(_sphere, space=SPACE, seed=42)
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
        opt = RandomSample(_sphere, space=SPACE, seed=42)
        opt.run(5)
        ckpt_path = tmp_path / "test.ckpt"
        opt.save_checkpoint(ckpt_path)

        with pytest.raises(TypeError, match="RandomSample.*GA"):
            GA.load_checkpoint(ckpt_path, _sphere)


class TestGAInitializationGuard:
    """Tests for GA's initialization guard preventing population overwrite on resume."""

    def test_ga_population_not_overwritten_on_resume(self, tmp_path):
        """After loading checkpoint, GA.run() should NOT re-initialize population."""
        opt = GA(_sphere, space=SPACE, population_size=6, seed=42)
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
        opt = RandomSample(fitness_fn=_sphere, space=SPACE, seed=42, callbacks=[cb])
        opt.run(25)
        assert ckpt_path.exists()
        # Load and verify it's a valid checkpoint
        loaded = RandomSample.load_checkpoint(ckpt_path, fitness_fn=_sphere)
        assert loaded._best_value == opt._best_value

    def test_checkpoint_callback_no_premature_save(self, tmp_path):
        """CheckpointCallback does not save before every_n iterations."""
        ckpt_path = tmp_path / "test.ckpt"
        cb = CheckpointCallback(ckpt_path, every_n=100)
        opt = RandomSample(fitness_fn=_sphere, space=SPACE, seed=42, callbacks=[cb])
        opt.run(50)
        assert not ckpt_path.exists()


class TestAllOptimizers:
    """Parametrized checkpoint tests for all 8 optimizers."""

    @pytest.mark.parametrize("cls,kwargs", OPTIMIZER_CONFIGS, ids=_optimizer_id)
    def test_save_load_roundtrip(self, cls, kwargs, tmp_path):
        """Save and load produces optimizer with same best_value and n_evaluations."""
        opt = cls(fitness_fn=_sphere, space=SPACE, seed=42, **kwargs)
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
        opt_full = cls(fitness_fn=_sphere, space=SPACE, seed=42, **kwargs)
        result_full = opt_full.run(40)

        # Split run: 20 + save + load + 20
        opt_split = cls(fitness_fn=_sphere, space=SPACE, seed=42, **kwargs)
        opt_split.run(20)
        path = tmp_path / "test.ckpt"
        opt_split.save_checkpoint(path)
        opt_resumed = cls.load_checkpoint(path, fitness_fn=_sphere)
        result_resumed = opt_resumed.run(20)

        assert result_full.best_value == result_resumed.best_value
        assert result_full.best_solution == result_resumed.best_solution

    @pytest.mark.parametrize("cls,kwargs", OPTIMIZER_CONFIGS, ids=_optimizer_id)
    def test_cache_preserved_round_trip(self, cls, kwargs, tmp_path):
        """Cache entries survive save/load cycle (all optimizers)."""
        opt = cls(fitness_fn=_sphere, space=SPACE, seed=42, **kwargs)
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

        opt = cls(fitness_fn=_sphere, space=SPACE, seed=42, callbacks=[record_offset], **kwargs)
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


class TestV1Migration:
    """Tests for v1 -> v2 checkpoint migration (D-10)."""

    def test_v1_checkpoint_migrates_to_v2(self, tmp_path):
        """A synthetic v1 checkpoint with raw bounds loads into a working v2 optimizer."""
        # First, save a real v2 checkpoint, then rewrite it as v1 shape.
        opt = RandomSample(_sphere, space=SPACE, seed=42)
        opt.run(5)
        path = tmp_path / "v1.ckpt"
        opt.save_checkpoint(path)

        # Downgrade the file to v1 shape: raw 'bounds' key, no space_kind/space_data.
        with open(path, 'rb') as f:
            state = pickle.load(f)
        state['_checkpoint_version'] = 1
        state['bounds'] = state.pop('space_data')['bounds']
        state.pop('space_kind')
        with open(path, 'wb') as f:
            pickle.dump(state, f)

        # Load should auto-migrate and produce a working optimizer.
        loaded = RandomSample.load_checkpoint(path, _sphere)
        assert isinstance(loaded._space, TupleSpace)
        assert loaded._space.bounds == BOUNDS
        result = loaded.run(5)  # must not raise
        assert result.best_solution is not None

    def test_v1_without_bounds_but_with_space(self, tmp_path):
        """Plan-02-intermediate v1 state with raw pickled space also migrates."""
        opt = RandomSample(_sphere, space=SPACE, seed=42)
        opt.run(5)
        path = tmp_path / "v1b.ckpt"
        opt.save_checkpoint(path)

        # Simulate Plan-02-era v1: raw 'space' key, no 'space_kind'/'space_data', version 1.
        with open(path, 'rb') as f:
            state = pickle.load(f)
        state['_checkpoint_version'] = 1
        state['space'] = SPACE
        state.pop('space_kind', None)
        state.pop('space_data', None)
        with open(path, 'wb') as f:
            pickle.dump(state, f)

        loaded = RandomSample.load_checkpoint(path, _sphere)
        assert isinstance(loaded._space, TupleSpace)
        assert loaded._space.bounds == BOUNDS

    def test_migrate_helper_bumps_version(self):
        """_migrate helper sets _checkpoint_version to the current version."""
        state = {'_checkpoint_version': 1, 'bounds': BOUNDS, '_class': 'RandomSample'}
        migrated = _migrate(state, 1)
        assert migrated['_checkpoint_version'] == CHECKPOINT_VERSION
        assert migrated['space_kind'] == 'TupleSpace'
        assert migrated['space_data'] == {'bounds': BOUNDS}
        assert 'bounds' not in migrated

    def test_migrate_rejects_malformed_v1_state(self):
        """_migrate raises ValueError on v1 state lacking any space marker."""
        state = {'_checkpoint_version': 1, '_class': 'RandomSample'}
        with pytest.raises(ValueError, match="space marker"):
            _migrate(state, 1)

    def test_migrate_accepts_already_migrated_v1_state(self):
        """_migrate is idempotent on v1 state already carrying space_kind."""
        state = {
            '_checkpoint_version': 1,
            '_class': 'RandomSample',
            'space_kind': 'TupleSpace',
            'space_data': {'bounds': BOUNDS},
        }
        migrated = _migrate(state, 1)
        assert migrated['_checkpoint_version'] == CHECKPOINT_VERSION
        assert migrated['space_kind'] == 'TupleSpace'
        assert migrated['space_data'] == {'bounds': BOUNDS}


def test_checkpoint_callback_bind_method(tmp_path):
    """CheckpointCallback.bind sets _optimizer; DiscreteOptimizer.__init__ uses it."""
    ckpt_path = tmp_path / "bind.ckpt"
    cb = CheckpointCallback(ckpt_path)
    # Pre-bind: _optimizer is None
    assert cb._optimizer is None

    # Direct bind() call works
    sentinel = object()
    cb.bind(sentinel)
    assert cb._optimizer is sentinel

    # When passed to a DiscreteOptimizer, the optimizer is bound automatically.
    cb2 = CheckpointCallback(ckpt_path)
    opt = RandomSample(_sphere, space=SPACE, seed=42, callbacks=[cb2])
    assert cb2._optimizer is opt


class TestUnknownSpaceKind:
    """Tests for D-09: unknown space_kind requires explicit space= on load."""

    def test_unknown_kind_without_space_raises(self, tmp_path):
        """Unknown space_kind + no space= kwarg -> ValueError with 'Unknown space_kind'."""
        opt = RandomSample(_sphere, space=SPACE, seed=42)
        opt.run(5)
        path = tmp_path / "unknown.ckpt"
        opt.save_checkpoint(path)

        # Tamper: set space_kind to something unknown.
        with open(path, 'rb') as f:
            state = pickle.load(f)
        state['space_kind'] = 'FakeSpaceKind'
        state['space_data'] = {}
        with open(path, 'wb') as f:
            pickle.dump(state, f)

        with pytest.raises(ValueError, match="FakeSpaceKind"):
            RandomSample.load_checkpoint(path, _sphere)

    def test_unknown_kind_with_explicit_space_succeeds(self, tmp_path):
        """Explicit space= kwarg overrides any space_kind in the checkpoint."""
        opt = RandomSample(_sphere, space=SPACE, seed=42)
        opt.run(5)
        path = tmp_path / "unknown2.ckpt"
        opt.save_checkpoint(path)

        with open(path, 'rb') as f:
            state = pickle.load(f)
        state['space_kind'] = 'FakeSpaceKind'
        state['space_data'] = {}
        with open(path, 'wb') as f:
            pickle.dump(state, f)

        override = TupleSpace(((0, 5), (0, 5), (0, 5)))
        loaded = RandomSample.load_checkpoint(path, _sphere, space=override)
        assert loaded._space is override

    def test_explicit_space_overrides_checkpoint(self, tmp_path):
        """Even for known space_kind, passing space= takes precedence."""
        opt = RandomSample(_sphere, space=SPACE, seed=42)
        opt.run(5)
        path = tmp_path / "override.ckpt"
        opt.save_checkpoint(path)

        override = TupleSpace(((0, 5), (0, 5), (0, 5)))
        loaded = RandomSample.load_checkpoint(path, _sphere, space=override)
        assert loaded._space is override
        assert loaded._space.bounds == ((0, 5), (0, 5), (0, 5))

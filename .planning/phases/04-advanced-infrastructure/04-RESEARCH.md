# Phase 4: Advanced Infrastructure - Research

**Researched:** 2026-04-12
**Domain:** Callback system, serialization/checkpoint/resume for discrete optimizers
**Confidence:** HIGH

## Summary

Phase 4 adds two features to the existing optimizer framework: (1) a callback system with early-stopping support, and (2) pickle-based checkpoint/resume. Both integrate into `DiscreteOptimizer` base class so all 8 optimizers and the FRST wrapper get them for free.

The codebase is well-structured for these additions. The `run()` loop in `base.py` (lines 104-147) has a clean iteration loop where callbacks hook in between `_step()` and history append. Each optimizer has clearly identifiable private state attributes that map directly to `_get_state()`/`_set_state()` methods. NumPy's `default_rng` state is a plain dict, fully pickle-able. The `EvaluationCache` (OrderedDict-based) serializes trivially.

The main complexity is `DifferentialEvolution`, which delegates to SciPy's internal loop and cannot be stepped individually. Its `run()` override must integrate callbacks and checkpoint support differently from the base class pattern. SciPy's `differential_evolution` callback supports `return True` for early stopping, which aligns with the D-03 protocol.

**Primary recommendation:** Implement callbacks in the base class `run()` loop first, then add `_get_state()`/`_set_state()` to each optimizer, then build the checkpoint save/load on top. DifferentialEvolution gets a limited checkpoint (pre/post run only, not mid-generation) since SciPy controls the inner loop.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- **D-01:** Callbacks registered via constructor arg: `callbacks=[fn1, fn2]`, matching the existing `fitness_fn` pattern. Immutable after creation -- no add/remove methods.
- **D-02:** Callbacks receive an info dict: `callback(info)` where `info = {'iteration': i, 'best_value': ..., 'best_solution': ..., 'n_evaluations': ..., 'wall_time': ...}`. Same shape as `full_history` dicts for consistency.
- **D-03:** Early stopping via return value -- if any callback returns `True`, the `run()` loop terminates early and returns the partial `Result`. Non-exceptional, clean protocol.
- **D-04:** Full optimizer state serialized: RNG state, population/frontier/current position (optimizer-specific), evaluation cache, best-so-far, iteration count. Resume produces identical results to an uninterrupted run.
- **D-05:** Versioned dict + pickle format. State serialized as a plain Python dict (not the class instance) with a `_checkpoint_version` key. On load, version is checked and migration applied if needed.
- **D-06:** Each optimizer subclass implements `_get_state() -> dict` and `_set_state(state: dict)` for its optimizer-specific internal state. Base class handles common state.
- **D-07:** Methods on optimizer: `optimizer.save_checkpoint(path)` serializes state to file. `Cls.load_checkpoint(path, fitness_fn)` classmethod reconstructs a live optimizer from checkpoint. User provides `fitness_fn` on load since callables can't be reliably serialized.
- **D-08:** Built-in `CheckpointCallback(path, every_n=100)` provided as a convenience. Reuses the callback system.
- **D-09:** `run()` continues the iteration count from checkpoint. If checkpoint was at iteration 500 and user calls `run(1000)`, it runs iterations 500-1499. History is concatenated.

### Claude's Discretion
- Exact fields in each optimizer's `_get_state()` dict
- Whether `DifferentialEvolution` can support full checkpoint/resume or gets a limited version
- Internal module layout (single `_checkpoint.py` vs split across files)
- Whether `CheckpointCallback` lives in a `cyopt.callbacks` module or `cyopt._checkpoint`

### Deferred Ideas (OUT OF SCOPE)
None -- discussion stayed within phase scope
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| CORE-08 | Callback system (`on_iteration` hooks for logging, early stopping, visualization) | Callback protocol (D-01 through D-03) hooks into `run()` loop; DE gets special handling via SciPy's native callback |
| CORE-09 | Serialization/checkpoint/resume support (pickle/dill-based state save/load) | Versioned dict + pickle (D-04 through D-09); all optimizer states audited; RNG state roundtrip verified |
</phase_requirements>

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| pickle | stdlib | State serialization | Standard Python serialization. All optimizer state is plain Python/NumPy types -- no need for dill. [VERIFIED: codebase inspection] |
| pathlib | stdlib | File path handling | Modern path API for `save_checkpoint`/`load_checkpoint`. [VERIFIED: stdlib] |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| numpy | >=1.24 (installed: 2.3.5) | RNG state save/restore | `rng.bit_generator.state` returns a plain dict; restorable via assignment. [VERIFIED: runtime test] |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| pickle | dill | dill can serialize lambdas/closures, but D-07 already addresses this by requiring user to pass `fitness_fn` on load. pickle is simpler, stdlib, no extra dependency |
| pickle | JSON | JSON can't serialize numpy arrays, sets, or tuples natively. Would require custom encoders/decoders. Pickle is the right choice for internal state |
| Single checkpoint file | Separate files per component | Over-engineering. Single file with versioned dict is simpler and atomic |

## Architecture Patterns

### Recommended Module Layout

```
cyopt/
  base.py              # Add: callbacks param, _get_state/_set_state, save/load_checkpoint
  _checkpoint.py       # NEW: CheckpointCallback, checkpoint version constant, migration logic
  _types.py            # Add: Callback type alias
  _cache.py            # Add: to_dict/from_dict methods for serialization
  optimizers/
    ga.py              # Add: _get_state/_set_state
    random_sample.py   # Add: _get_state/_set_state
    greedy_walk.py     # Add: _get_state/_set_state
    best_first_search.py # Add: _get_state/_set_state
    basin_hopping.py   # Add: _get_state/_set_state
    mcmc.py            # Add: _get_state/_set_state
    simulated_annealing.py # Add: _get_state/_set_state
    differential_evolution.py # Add: _get_state/_set_state (limited)
```

**Rationale:** `_checkpoint.py` keeps checkpoint-specific logic (version constant, `CheckpointCallback`, any future migration functions) out of `base.py`. The base class gets the `save_checkpoint`/`load_checkpoint` methods but delegates format details to the checkpoint module. [ASSUMED]

### Pattern 1: Callback Invocation in run()

**What:** Add callback invocation between `_step()` and history append in the base `run()` loop.
**When to use:** Every optimizer except DifferentialEvolution (which overrides `run()`).

```python
# In base.py run() loop -- after _step(), before history append
import time

for i in iterator:
    step_info = self._step(i)
    history.append(self._best_value)
    if self._record_history and full_history is not None and step_info is not None:
        full_history.append(step_info)

    # Callback invocation (NEW)
    if self._callbacks:
        cb_info = {
            'iteration': self._iteration_offset + i,
            'best_value': self._best_value,
            'best_solution': self._best_solution,
            'n_evaluations': self._n_evaluations,
            'wall_time': time.perf_counter() - t0,
        }
        for cb in self._callbacks:
            if cb(cb_info) is True:  # D-03: explicit True check
                # Early stop -- build partial result
                wall_time = time.perf_counter() - t0
                return Result(...)
```

**Key detail:** Use `is True` not just truthiness for the early-stop check. This prevents accidental early stopping from callbacks that return non-None values. [VERIFIED: D-03 specifies returning True]

### Pattern 2: State Serialization Protocol

**What:** Base class handles common state; subclasses implement optimizer-specific state.
**When to use:** Every optimizer.

```python
# base.py
def _get_common_state(self) -> dict:
    return {
        '_checkpoint_version': CHECKPOINT_VERSION,
        '_class': type(self).__name__,
        '_module': type(self).__module__,
        'rng_state': self._rng.bit_generator.state,
        'cache_data': dict(self._cache._cache),  # OrderedDict -> dict
        'cache_maxsize': self._cache._maxsize,
        'best_solution': self._best_solution,
        'best_value': self._best_value,
        'n_evaluations': self._n_evaluations,
        'iteration_offset': self._iteration_offset,
        'bounds': self._bounds,
        'record_history': self._record_history,
        'progress': self._progress,
    }

def _set_common_state(self, state: dict) -> None:
    self._rng.bit_generator.state = state['rng_state']
    # Rebuild cache
    self._cache = EvaluationCache(maxsize=state['cache_maxsize'])
    for k, v in state['cache_data'].items():
        self._cache[k] = v
    self._best_solution = state['best_solution']
    self._best_value = state['best_value']
    self._n_evaluations = state['n_evaluations']
    self._iteration_offset = state['iteration_offset']
```

### Pattern 3: Classmethod Load with Registry

**What:** `load_checkpoint` needs to know which subclass to instantiate.
**When to use:** Loading checkpoints.

```python
@classmethod
def load_checkpoint(cls, path, fitness_fn, **kwargs):
    with open(path, 'rb') as f:
        state = pickle.load(f)
    # Verify version
    version = state.get('_checkpoint_version', 0)
    if version != CHECKPOINT_VERSION:
        state = _migrate(state, version)
    # Instantiate with minimal args, then restore state
    instance = cls(fitness_fn=fitness_fn, bounds=state['bounds'], **kwargs)
    instance._set_common_state(state)
    instance._set_state(state.get('optimizer_state', {}))
    return instance
```

**Key insight:** `load_checkpoint` is a classmethod on the concrete class (e.g., `GA.load_checkpoint(...)`), not on the base. The user knows which optimizer they saved. The checkpoint stores the class name for validation only. [VERIFIED: D-07]

### Pattern 4: DifferentialEvolution Special Handling

**What:** DE delegates to SciPy's loop, so callbacks and checkpointing work differently.
**When to use:** DifferentialEvolution only.

```python
# DE.run() already has its own callback -- extend it for user callbacks
def callback(xk, convergence=0):
    history.append(self._best_value)
    # Invoke user callbacks
    if self._callbacks:
        cb_info = {
            'iteration': len(history) - 1 + self._iteration_offset,
            'best_value': self._best_value,
            'best_solution': self._best_solution,
            'n_evaluations': self._n_evaluations,
            'wall_time': time.perf_counter() - t0,
        }
        for cb in self._callbacks:
            if cb(cb_info) is True:
                return True  # SciPy stops when callback returns True
    return False
```

**Checkpoint limitation:** DE cannot checkpoint mid-generation because SciPy controls the population. Checkpoints can only capture state before/after a `run()` call. On resume, DE restarts from scratch but with the preserved cache and best-so-far. This is a meaningful limitation but acceptable since the cache prevents re-evaluation. [ASSUMED -- needs confirmation with user if full mid-run checkpoint is expected]

### Anti-Patterns to Avoid
- **Pickling the optimizer instance directly:** Class layout changes break old checkpoints. Always serialize as a plain dict (D-05).
- **Serializing fitness_fn:** Callables are not reliably picklable across sessions. D-07 requires user to provide it on load.
- **Using `__getstate__`/`__setstate__`:** These tie serialization to class structure. The explicit dict approach is more maintainable.
- **Checking `result is not None` for early stop:** Must use `result is True` to avoid false positives from callbacks that return dicts or other truthy values.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| RNG state serialization | Custom RNG state tracking | `rng.bit_generator.state` dict | NumPy provides complete state as a plain dict. Verified roundtrip. [VERIFIED: runtime test] |
| File I/O for checkpoints | Custom binary format | `pickle.dump`/`pickle.load` | All state is plain Python + NumPy types. Pickle handles this natively. |
| Ordered cache serialization | Custom cache serialization | `dict(cache._cache)` + rebuild | OrderedDict converts to dict; rebuild preserves insertion order. |

## Common Pitfalls

### Pitfall 1: Iteration Offset Tracking
**What goes wrong:** After resuming from checkpoint, iteration numbers in callbacks report wrong values (starting from 0 instead of continuing from where they left off).
**Why it happens:** The `run()` loop uses `range(n_iterations)` which always starts at 0.
**How to avoid:** Add `self._iteration_offset` to the base class. Increment it by `n_iterations` at the end of each `run()`. Callback info dict uses `self._iteration_offset + i`.
**Warning signs:** Callback logs showing iteration 0 after a resume.

### Pitfall 2: GA Population Re-initialization
**What goes wrong:** `GA.run()` currently re-initializes the population on every call (lines 293-308). After loading a checkpoint, calling `run()` would overwrite the restored population.
**Why it happens:** GA's `run()` override always creates a fresh population before delegating to `super().run()`.
**How to avoid:** Add a flag (e.g., `self._initialized`) that GA checks. If state was restored via `_set_state()`, skip population initialization. Or restructure so initialization happens in `_step(0)` lazily.
**Warning signs:** Resume producing different results than uninterrupted run.

### Pitfall 3: EvaluationCache LRU Order Not Preserved
**What goes wrong:** Cache is serialized as a plain dict, losing access-order information. On restore, LRU eviction may evict different entries than an uninterrupted run would.
**Why it happens:** `dict()` loses OrderedDict ordering guarantees (though CPython dicts do preserve insertion order since 3.7).
**How to avoid:** Serialize as a list of `(key, value)` tuples from `cache._cache.items()` and rebuild with insertion order preserved. Or use `OrderedDict(state['cache_items'])` on restore.
**Warning signs:** Identical-seed runs with and without checkpoint producing different results after cache fills up.

### Pitfall 4: BFS Sets and Heaps Are Large
**What goes wrong:** BestFirstSearch's `_visited` set and `_frontier` heap can grow very large for big search spaces. Checkpoint files become huge.
**Why it happens:** Frontier mode explores broadly and never forgets visited nodes.
**How to avoid:** Accept it as inherent to the algorithm. Document that BFS checkpoints may be large. Optionally add a size warning when serializing.
**Warning signs:** Multi-GB checkpoint files for large search spaces.

### Pitfall 5: Pickle Security
**What goes wrong:** `pickle.load()` can execute arbitrary code. Loading a malicious checkpoint file is a security risk.
**Why it happens:** Pickle's deserialization protocol calls `__reduce__` which can invoke arbitrary callables.
**How to avoid:** Document in docstrings that checkpoints should only be loaded from trusted sources. This is standard for pickle-based serialization in scientific Python (sklearn, PyTorch, etc.). Do not attempt to make pickle "safe" -- that is out of scope.
**Warning signs:** N/A -- this is a known limitation, not a bug.

### Pitfall 6: SimulatedAnnealing Step Count
**What goes wrong:** SA's cooling schedule depends on `_step_count`. If not serialized and restored, the temperature schedule restarts from the beginning after checkpoint resume.
**Why it happens:** `_step_count` is SA-specific state that drives the cooling schedule.
**How to avoid:** Include `_step_count` in SA's `_get_state()`. This is already implied by D-04 but easy to overlook.
**Warning signs:** Temperature jumping back to `t_max` after resume.

## Code Examples

### Optimizer-Specific State Fields (Audit)

Each optimizer's `_get_state()` must capture these fields. [VERIFIED: codebase inspection]

```python
# GA._get_state()
{
    'population': self._population,        # np.ndarray (pop_size, n_dims)
    'fitness_values': self._fitness_values, # np.ndarray (pop_size,)
    'population_size': self._population_size,
    'mutation_rate': self._mutation_rate,
    'mutation_k': self._mutation_k,
    'elitism': self._elitism,
    # selection/crossover are config, not state -- stored as string names
    'selection': ...,  # need to store the spec, not the resolved callable
    'crossover': ...,
}

# RandomSample._get_state()
{}  # No optimizer-specific state beyond base class

# GreedyWalk._get_state()
{
    'current': self._current,              # DNA | None
    'current_value': self._current_value,  # float
}

# BestFirstSearch._get_state()
{
    'mode': self._mode,                    # str
    'current': self._current,              # DNA | None
    'current_value': self._current_value,  # float
    # Backtrack mode
    'path': self._path,                    # list[DNA]
    'avoid': list(self._avoid),            # set -> list for pickle
    # Frontier mode
    'frontier': self._frontier,            # list[tuple[float, int, DNA]]
    'visited': list(self._visited),        # set -> list for pickle
    'counter': self._counter,              # int
}

# MCMC._get_state()
{
    'temperature': self._temperature,      # float
    'current': self._current,              # DNA | None
    'current_value': self._current_value,  # float
}

# BasinHopping._get_state()
{
    'temperature': self._temperature,      # float
    'n_perturbations': self._n_perturbations,  # int
    'current': self._current,              # DNA | None
    'current_value': self._current_value,  # float
}

# SimulatedAnnealing._get_state()
{
    'n_iterations': self._n_iterations,    # int (cooling schedule param)
    't_max': self._t_max,                  # float
    't_min': self._t_min,                  # float
    'current': self._current,              # DNA | None
    'current_value': self._current_value,  # float
    'step_count': self._step_count,        # int (CRITICAL for cooling)
}

# DifferentialEvolution._get_state()
{
    'popsize': self._popsize,              # int
    'mutation': self._mutation,            # float | tuple
    'recombination': self._recombination,  # float
    'strategy': self._strategy,            # str
    # No internal population state -- SciPy manages it
}
```

### Callback Type Definition

```python
# _types.py addition
from typing import Any

CallbackInfo = dict[str, Any]
"""Info dict passed to callbacks: iteration, best_value, best_solution, n_evaluations, wall_time."""

Callback = Callable[[CallbackInfo], bool | None]
"""Callback function. Return True to trigger early stopping."""
```

### CheckpointCallback Implementation

```python
# _checkpoint.py
import pickle
from pathlib import Path

CHECKPOINT_VERSION = 1

class CheckpointCallback:
    """Callback that saves optimizer checkpoints at regular intervals.

    Parameters
    ----------
    path : str or Path
        File path for checkpoint. Overwrites on each save.
    every_n : int
        Save every N iterations. Default 100.
    """

    def __init__(self, path: str | Path, every_n: int = 100):
        self._path = Path(path)
        self._every_n = every_n
        self._optimizer = None  # Set by save_checkpoint internals

    def __call__(self, info: dict) -> bool | None:
        if (info['iteration'] + 1) % self._every_n == 0:
            if self._optimizer is not None:
                self._optimizer.save_checkpoint(self._path)
        return None  # Never triggers early stop
```

**Note:** The `CheckpointCallback` needs a reference to the optimizer to call `save_checkpoint()`. This can be set during optimizer initialization when callbacks are registered, or the callback can receive the optimizer reference via the info dict. The simpler approach is to add an `'optimizer'` key to the info dict (not part of D-02's public contract but as an implementation detail). Alternatively, the optimizer sets `cb._optimizer = self` for any `CheckpointCallback` instances in the callbacks list during `__init__`. [ASSUMED -- implementation detail for planner to decide]

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `np.random.RandomState` | `np.random.default_rng` (Generator) | NumPy 1.17+ | State dict format is different. Codebase already uses `default_rng`. |
| `__getstate__`/`__setstate__` | Explicit versioned dict | Best practice | Decouples serialization from class structure. Enables migration. |
| `dill` for callable serialization | Don't serialize callables | Best practice | User provides `fitness_fn` on load (D-07). Cleaner, more reliable. |

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | `_checkpoint.py` as separate module is better than inlining in `base.py` | Architecture Patterns | Low -- purely organizational, easy to move |
| A2 | DE gets limited checkpoint (no mid-generation state) | Pattern 4 / Architecture | Medium -- user may expect full mid-run resume for DE. If so, would need to use SciPy's internal solver object (fragile) |
| A3 | CheckpointCallback gets optimizer reference via `cb._optimizer = self` pattern | Code Examples | Low -- alternative approaches exist and are equally valid |

## Open Questions

1. **CheckpointCallback optimizer reference**
   - What we know: CheckpointCallback needs to call `optimizer.save_checkpoint()` but callbacks only receive an info dict
   - What's unclear: Cleanest way to give the callback access to the optimizer
   - Recommendation: Add `optimizer` key to the info dict as an internal field, or have the optimizer detect and bind CheckpointCallback instances during __init__. Either works; planner picks one.

2. **GA run() override and initialization guard**
   - What we know: GA.run() reinitializes population every call. This conflicts with checkpoint resume.
   - What's unclear: Whether to add a `_initialized` flag or restructure to lazy-init in `_step()`
   - Recommendation: Add `_initialized` flag set by `_set_state()`. GA.run() checks it before re-initializing. Simpler than restructuring.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 9.0.2 |
| Config file | pyproject.toml (assumed) |
| Quick run command | `conda run -n cytools pytest tests/ -x -q` |
| Full suite command | `conda run -n cytools pytest tests/ -v` |

### Phase Requirements -> Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| CORE-08a | Callback receives correct info dict fields | unit | `conda run -n cytools pytest tests/test_callbacks.py::test_callback_info_fields -x` | Wave 0 |
| CORE-08b | Multiple callbacks all invoked | unit | `conda run -n cytools pytest tests/test_callbacks.py::test_multiple_callbacks -x` | Wave 0 |
| CORE-08c | Early stopping when callback returns True | unit | `conda run -n cytools pytest tests/test_callbacks.py::test_early_stop -x` | Wave 0 |
| CORE-08d | Callbacks work with DE (SciPy wrapper) | unit | `conda run -n cytools pytest tests/test_callbacks.py::test_de_callbacks -x` | Wave 0 |
| CORE-09a | save_checkpoint creates file, load_checkpoint restores | unit | `conda run -n cytools pytest tests/test_checkpoint.py::test_save_load_roundtrip -x` | Wave 0 |
| CORE-09b | Resumed run produces identical results to uninterrupted | integration | `conda run -n cytools pytest tests/test_checkpoint.py::test_resume_determinism -x` | Wave 0 |
| CORE-09c | Iteration offset continues correctly after resume | unit | `conda run -n cytools pytest tests/test_checkpoint.py::test_iteration_offset -x` | Wave 0 |
| CORE-09d | Cache preserved across checkpoint/resume | unit | `conda run -n cytools pytest tests/test_checkpoint.py::test_cache_preserved -x` | Wave 0 |
| CORE-09e | CheckpointCallback saves at correct intervals | unit | `conda run -n cytools pytest tests/test_checkpoint.py::test_checkpoint_callback_interval -x` | Wave 0 |
| CORE-09f | All 8 optimizers checkpoint/resume correctly | integration | `conda run -n cytools pytest tests/test_checkpoint.py::TestAllOptimizers -x` | Wave 0 |
| CORE-09g | Version mismatch in checkpoint raises informative error | unit | `conda run -n cytools pytest tests/test_checkpoint.py::test_version_mismatch -x` | Wave 0 |

### Sampling Rate
- **Per task commit:** `conda run -n cytools pytest tests/test_callbacks.py tests/test_checkpoint.py -x -q`
- **Per wave merge:** `conda run -n cytools pytest tests/ -v`
- **Phase gate:** Full suite green before `/gsd-verify-work`

### Wave 0 Gaps
- [ ] `tests/test_callbacks.py` -- covers CORE-08 (a through d)
- [ ] `tests/test_checkpoint.py` -- covers CORE-09 (a through g)

## Security Domain

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | no | N/A |
| V3 Session Management | no | N/A |
| V4 Access Control | no | N/A |
| V5 Input Validation | yes | Validate checkpoint version on load; validate state dict has required keys |
| V6 Cryptography | no | N/A |

### Known Threat Patterns for pickle serialization

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Malicious pickle payload | Tampering | Document "load only trusted checkpoints". Standard for scientific Python (sklearn, PyTorch use same approach). No mitigation beyond documentation -- pickle is inherently unsafe for untrusted input. |
| Corrupted checkpoint file | Denial of Service | Catch `pickle.UnpicklingError` and `KeyError` on load; raise informative error |

## Sources

### Primary (HIGH confidence)
- Codebase inspection: `cyopt/base.py`, all 8 optimizer files, `_cache.py`, `_types.py`, `frst/_wrapper.py` -- complete state audit
- NumPy RNG state roundtrip -- verified via runtime test (pickle dumps/loads `rng.bit_generator.state`)
- SciPy DE callback documentation -- `return True` triggers early stop [VERIFIED: `help(differential_evolution)` output]
- EvaluationCache pickle roundtrip -- verified via runtime test

### Secondary (MEDIUM confidence)
- None needed -- phase is purely internal code, no external library discovery required

### Tertiary (LOW confidence)
- None

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- stdlib pickle + existing numpy/scipy, no new dependencies
- Architecture: HIGH -- clean integration points identified, all optimizer state audited
- Pitfalls: HIGH -- concrete issues identified from codebase inspection (GA reinit, SA step_count, cache ordering)

**Research date:** 2026-04-12
**Valid until:** 2026-05-12 (stable -- no external dependency changes expected)

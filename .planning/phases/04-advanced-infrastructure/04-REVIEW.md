---
phase: 04-advanced-infrastructure
reviewed: 2026-04-12T00:00:00Z
depth: standard
files_reviewed: 15
files_reviewed_list:
  - cyopt/__init__.py
  - cyopt/_cache.py
  - cyopt/_checkpoint.py
  - cyopt/_types.py
  - cyopt/base.py
  - cyopt/optimizers/basin_hopping.py
  - cyopt/optimizers/best_first_search.py
  - cyopt/optimizers/differential_evolution.py
  - cyopt/optimizers/ga.py
  - cyopt/optimizers/greedy_walk.py
  - cyopt/optimizers/mcmc.py
  - cyopt/optimizers/random_sample.py
  - cyopt/optimizers/simulated_annealing.py
  - tests/test_callbacks.py
  - tests/test_checkpoint.py
findings:
  critical: 0
  warning: 4
  info: 2
  total: 6
status: issues_found
---

# Phase 04: Code Review Report

**Reviewed:** 2026-04-12
**Depth:** standard
**Files Reviewed:** 15
**Status:** issues_found

## Summary

Reviewed the full optimizer suite (8 optimizers), the evaluation cache, checkpoint infrastructure, type definitions, and callback/checkpoint test suites. The code is generally well-structured with clean separation between the base class and optimizer-specific logic. The checkpoint/resume system and callback dispatch are implemented correctly for the common cases.

Four warnings were found: a cache deserialization bug that produces an oversized cache after restore, a missing `best_solution` null-check in the DE-specific `run()` override, a silent state loss for `record_history` and `progress` after checkpoint round-trip, and a frontier-exhaustion logic gap in `BestFirstSearch`. Two info items cover a silent no-op in `CheckpointCallback` and an unreachable code path in GA's `_step`.

No security or critical correctness issues were found.

---

## Warnings

### WR-01: `EvaluationCache.from_list` Does Not Enforce `maxsize` During Restore

**File:** `cyopt/_cache.py:52-70`

**Issue:** `from_list` inserts entries directly into the internal `OrderedDict` via `cache._cache[k] = v`, bypassing `__setitem__`'s LRU eviction logic. If `len(items) > maxsize`, the restored cache contains more entries than `maxsize` allows. Subsequent reads via `__getitem__` call `move_to_end` but do not evict; only new writes trigger eviction. The cache is internally inconsistent (reports `_maxsize=5` but `len()=10`) until enough new writes flush the excess entries.

This can happen in practice: an optimizer runs with an unbounded cache (`cache_size=None`), accumulates 10,000 entries, then is checkpointed and loaded with `cache_size=1000`. The restored cache starts with 10,000 entries.

**Verified:** `from_list(items_of_10, maxsize=5)` returns a cache with `len() == 10` and `_maxsize == 5`.

**Fix:** In `from_list`, use `__setitem__` so eviction runs, or truncate `items` to the last `maxsize` entries before inserting (preserving LRU order):

```python
@classmethod
def from_list(
    cls,
    items: list[tuple[tuple[int, ...], float]],
    maxsize: int | None = None,
) -> "EvaluationCache":
    cache = cls(maxsize=maxsize)
    # Trim to maxsize (keep most-recently-used tail) before inserting
    if maxsize is not None and len(items) > maxsize:
        items = items[-maxsize:]
    for k, v in items:
        cache._cache[k] = v  # safe: len is now <= maxsize
    return cache
```

---

### WR-02: `DifferentialEvolution.run()` Returns `Result` With `best_solution=None` When No Evaluations Occur

**File:** `cyopt/optimizers/differential_evolution.py:179-186`

**Issue:** The `DifferentialEvolution.run()` override does not check whether `self._best_solution` is `None` before constructing the `Result`. The base-class `run()` raises a `RuntimeError` in this case (lines 174-178 of `base.py`), but the DE override skips that guard entirely.

If `n_iterations=0` or SciPy's DE terminates before calling `wrapped` even once, `best_solution` will be `None` in the returned `Result`, violating the declared type `Result.best_solution: DNA` and causing downstream crashes.

**Fix:** Add the same guard used in the base class before constructing the `Result`:

```python
wall_time = time.perf_counter() - t0
self._iteration_offset += len(history)

if self._best_solution is None:
    raise RuntimeError(
        "No solution was evaluated during run(). "
        "Ensure n_iterations > 0."
    )

return Result(
    best_solution=self._best_solution,
    ...
)
```

---

### WR-03: `record_history` and `progress` Are Serialized But Not Restored From Checkpoint

**File:** `cyopt/base.py:214-241`

**Issue:** `_get_common_state()` serializes `record_history` and `progress` (lines 228-229), but `_set_common_state()` does not restore them. After a checkpoint round-trip, the loaded optimizer always uses the values passed to `load_checkpoint` (which calls `cls(fitness_fn, bounds, callbacks=callbacks, **kwargs)`) — and `load_checkpoint` has no `record_history` or `progress` parameters, so they default to `False`.

Consequence: an optimizer checkpointed with `record_history=True` will produce `full_history=None` after loading, with no warning. The serialized values in the checkpoint file are dead data.

**Verified:** Checkpointing `RandomSample(..., record_history=True)` then calling `load_checkpoint` and `run(5)` returns `result.full_history == None`.

**Fix (option A — restore from state):** Restore both fields in `_set_common_state`:

```python
def _set_common_state(self, state: dict) -> None:
    self._rng.bit_generator.state = state['rng_state']
    self._cache = EvaluationCache.from_list(
        state['cache_data'], maxsize=state['cache_maxsize']
    )
    self._best_solution = state['best_solution']
    self._best_value = state['best_value']
    self._n_evaluations = state['n_evaluations']
    self._iteration_offset = state['iteration_offset']
    self._record_history = state.get('record_history', False)
    self._progress = state.get('progress', False)
```

**Fix (option B — remove from serialization):** Remove `record_history` and `progress` from `_get_common_state` (they are constructor arguments, not runtime-mutable state), and document in `load_checkpoint` that callers must re-pass them via `**kwargs`.

---

### WR-04: `BestFirstSearch` Frontier-Exhausted Restart Silently Fails to Find Unvisited Nodes

**File:** `cyopt/optimizers/best_first_search.py:232-240`

**Issue:** When the frontier heap is empty, the code attempts to find an unvisited random candidate:

```python
candidate = self._random_dna()
for _ in range(100):
    if candidate not in self._visited:
        break
    candidate = self._random_dna()
```

If the search space is fully exhausted (all points in `_visited`), the loop runs all 100 iterations and exits via fallthrough with `candidate` still in `_visited`. The subsequent lines (239-240) then call `_evaluate(candidate)` on an already-visited point and re-add it to `_visited` (a no-op for the set). This does not cause crashes (the cache prevents actual re-evaluation), but:

1. The stated goal of "avoid revisiting" is not achieved — the optimizer is stuck re-processing an already-explored point each step.
2. The `_step_frontier` method returns without any indication that the space is exhausted, making the behavior invisible to callers.

For practical FRST problems with large search spaces this loop will almost never fail, but for small test cases (e.g., 1-dim bounds `(0,1)`) it will fail silently on every step after step 2.

**Fix:** Detect exhaustion and either random-restart with a cleared `_visited` set, or return a sentinel that `run()` can use to halt early:

```python
if self._frontier:
    value, _, candidate = heapq.heappop(self._frontier)
    self._current = candidate
    self._current_value = value
else:
    # Attempt to find unvisited candidate
    for _ in range(1000):
        candidate = self._random_dna()
        if candidate not in self._visited:
            self._current = candidate
            self._current_value = self._evaluate(candidate)
            self._visited.add(candidate)
            break
    else:
        # Search space fully explored -- reset visited to allow cycling
        self._visited.clear()
        self._current = self._random_dna()
        self._current_value = self._evaluate(self._current)
        self._visited.add(self._current)
```

---

## Info

### IN-01: `CheckpointCallback` Silently Does Nothing If `_optimizer` Is Not Bound

**File:** `cyopt/_checkpoint.py:40-44`

**Issue:** `CheckpointCallback.__call__` checks `if self._optimizer is not None` before saving (line 42). If a `CheckpointCallback` is constructed and used outside the normal `DiscreteOptimizer.__init__` binding flow (e.g., added manually to `_callbacks` after construction), calls to the callback silently no-op without any log or warning. This is consistent with the design, but the silent failure makes debugging difficult.

**Fix:** Add a warning when the callback fires but no optimizer is bound:

```python
def __call__(self, info: dict[str, Any]) -> bool | None:
    if (info['iteration'] + 1) % self._every_n == 0:
        if self._optimizer is not None:
            self._optimizer.save_checkpoint(self._path)
        else:
            import warnings
            warnings.warn(
                "CheckpointCallback fired but _optimizer is not bound. "
                "No checkpoint was saved. Pass CheckpointCallback via "
                "the constructor's callbacks= argument.",
                stacklevel=2,
            )
    return None
```

---

### IN-02: `GA._step` Accesses `self._population.shape` Without Guarding Against `None`

**File:** `cyopt/optimizers/ga.py:336-338`

**Issue:** `_step` dereferences `self._population` (line 336) and calls `.shape[1]` (line 338) without checking for `None`. `_population` is initialized to `None` in `__init__` (line 257) and only set in `GA.run()` (lines 299-309). The base-class `run()` is called from `GA.run()` after initialization, so in normal usage `_step` is always called with `_population` set.

However, if a checkpoint is loaded with `_set_state` receiving `state['population'] = None` (possible if the checkpoint was saved before `run()` was called), calling `run()` on the loaded optimizer would crash at `pop.shape[1]` with `AttributeError`. The same applies to `self._fitness_values`.

**Fix:** Add an assertion or guard at the top of `_step`:

```python
def _step(self, iteration: int) -> dict | None:
    assert self._population is not None and self._fitness_values is not None, (
        "GA population not initialized. This should not occur if run() is used correctly."
    )
    pop = self._population
    ...
```

---

_Reviewed: 2026-04-12_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_

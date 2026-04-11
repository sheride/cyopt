---
phase: 01-foundation-first-optimizers
reviewed: 2026-04-11T21:26:14Z
depth: standard
files_reviewed: 9
files_reviewed_list:
  - cyopt/__init__.py
  - cyopt/_cache.py
  - cyopt/_types.py
  - cyopt/base.py
  - cyopt/optimizers/__init__.py
  - cyopt/optimizers/ga.py
  - cyopt/optimizers/greedy_walk.py
  - cyopt/optimizers/random_sample.py
  - pyproject.toml
findings:
  critical: 0
  warning: 4
  info: 2
  total: 6
status: issues_found
---

# Phase 01: Code Review Report

**Reviewed:** 2026-04-11T21:26:14Z
**Depth:** standard
**Files Reviewed:** 9
**Status:** issues_found

## Summary

Nine source files were reviewed covering the core types, evaluation cache, abstract base class,
and three optimizer implementations (GA, GreedyWalk, RandomSample), plus the build configuration.

The architecture is clean and the overall design is sound. Four warnings were found: two are
correctness bugs (a `None` result returned under a non-nullable type, and state not reset on
repeated `GA.run()` calls), one is a fragile ordering issue in the cache's `__getitem__`, and
one is a falsy-check that silently drops empty dicts from `full_history`. Two info items flag
dead code (redundant bounds clip) and a minor naming ambiguity in the mutation loop.

---

## Warnings

### WR-01: `Result.best_solution` can be `None` when `n_iterations=0`

**File:** `cyopt/base.py:134`

**Issue:** `DiscreteOptimizer._best_solution` is initialised to `None` (line 57) and only set
when `_evaluate` records an improvement. If `run(0)` is called, or if every `_step` call
completes without invoking `_evaluate`, `Result` is constructed with `best_solution=None`.
`Result.best_solution` is typed `DNA` (i.e. `tuple[int, ...]`), not `DNA | None`, so this
silently violates the type contract. Callers that unpack or iterate the best solution will
crash with a `TypeError`.

**Fix:** Guard the `Result` construction, or expand the type annotation, or raise early:

```python
# Option A — raise if no evaluation happened (safest contract)
if self._best_solution is None:
    raise RuntimeError(
        "run() completed without any fitness evaluations. "
        "Ensure n_iterations > 0 and _step() calls _evaluate()."
    )

return Result(
    best_solution=self._best_solution,
    ...
)
```

```python
# Option B — update Result type annotation to allow None
@dataclass(frozen=True)
class Result:
    best_solution: DNA | None
    best_value: float
    ...
```

---

### WR-02: `GA.run()` does not reset inherited base-class state between calls

**File:** `cyopt/optimizers/ga.py:293-308`

**Issue:** `GA.run()` resets `_population` and `_fitness_values` (lines 297-301) but does
not reset `_best_solution`, `_best_value`, or `_n_evaluations` from `DiscreteOptimizer`.
On a second call to `run()`, the previous run's best value seeds the minimisation tracking
(`_best_value` starts at the old minimum, not `float("inf")`), and `n_evaluations` accumulates
across calls rather than reflecting only the current run. `GreedyWalk` correctly resets its
walker state (`_current`, `_current_value`) in its own `run()` override; GA should do the same
for the shared base-class fields.

**Fix:** Reset base-class tracking state at the top of `GA.run()`:

```python
def run(self, n_iterations: int):
    """Initialise population and delegate to base-class loop."""
    # Reset shared state so repeated run() calls are independent
    self._best_solution = None
    self._best_value = float("inf")
    self._n_evaluations = 0
    self._cache.clear()   # optional: omit if cache persistence across runs is desired

    n_dims = len(self._bounds)
    ...
```

Note: whether to clear the cache on re-run is a design choice — but the tracking fields
(`_best_solution`, `_best_value`, `_n_evaluations`) should always reset.

---

### WR-03: `EvaluationCache.__getitem__` calls `move_to_end` before confirming key exists

**File:** `cyopt/_cache.py:26-28`

**Issue:** `__getitem__` calls `self._cache.move_to_end(key)` unconditionally before accessing
`self._cache[key]`. If the key is absent, `move_to_end` raises `KeyError` (with the key as
message), then the dict access raises a second `KeyError`. While current callers always check
`key in self._cache` before indexing (base.py lines 77-78), `__getitem__` is a public protocol
method — any direct use without a prior `__contains__` check produces an unhelpful double error
path and leaks internal `OrderedDict` detail.

**Fix:** Check existence before moving, or restructure to a try/except:

```python
def __getitem__(self, key: tuple[int, ...]) -> float:
    if key not in self._cache:
        raise KeyError(key)
    self._cache.move_to_end(key)
    return self._cache[key]
```

---

### WR-04: Falsy check drops empty dicts from `full_history`

**File:** `cyopt/base.py:129`

**Issue:** The condition `if self._record_history and full_history is not None and step_info:`
uses a truthiness test on `step_info`. An empty dict `{}` is falsy in Python. If a `_step`
implementation returns `{}` for a no-op iteration (e.g. a future optimizer that skips
evaluation on some steps), that entry is silently dropped from `full_history`, creating a
length mismatch between `history` (always length `n_iterations`) and `full_history` (shorter).
Callers that zip the two lists will misalign.

**Fix:** Use an explicit `is not None` check:

```python
if self._record_history and full_history is not None and step_info is not None:
    full_history.append(step_info)
```

---

## Info

### IN-01: Redundant bounds-clipping after crossover and mutation in GA

**File:** `cyopt/optimizers/ga.py:348-351`

**Issue:** After crossover and optional mutation, every child is clipped per dimension:

```python
for d in range(n_dims):
    lo, hi = self._bounds[d]
    child[d] = max(lo, min(hi, child[d]))
```

Crossover selects slices of parents already within bounds (since the population is initialised
via `_random_dna` and all mutations go through `rng.integers(lo, hi+1)`), so children of
crossover are also within bounds. `random_mutation` explicitly samples within `[lo, hi]`.
The clip is therefore dead code in all current paths. It is not harmful, but it adds
per-dimension iteration on every child and suggests a misunderstanding of where
out-of-bounds values could arise.

**Fix:** Remove the clip loop, or add a comment explaining why it is a defensive guard:

```python
# Defensive: clip in case a custom crossover_fn produces out-of-bounds values
for d in range(n_dims):
    lo, hi = self._bounds[d]
    child[d] = np.clip(child[d], lo, hi)
```

If the intent is purely defensive for custom operators, a comment clarifying that is
sufficient.

---

### IN-02: Mutation loop variable shadowing creates misleading reading

**File:** `cyopt/optimizers/ga.py:341-353`

**Issue:** In the mutation loop:

```python
for child in (c1, c2):
    if idx >= self._population_size:
        break
    if self._rng.random() < self._mutation_rate:
        child = random_mutation(child, self._bounds, self._rng, k=self._mutation_k)
```

`child` is the loop variable, then reassigned within the loop body when mutation fires.
`random_mutation` returns a new array rather than mutating in place. This is functionally
correct (the reassigned `child` is what gets stored in `next_pop[idx]`), but the pattern
of rebinding a loop variable to silence an in-place vs. copy distinction makes the code
harder to audit. A reader may expect the original `c1`/`c2` to reflect the mutation, or
may miss that no mutation occurred when `random()` exceeds `mutation_rate`.

**Fix:** Use a distinct variable name to make the conditional replacement explicit:

```python
for child_raw in (c1, c2):
    if idx >= self._population_size:
        break
    child = (
        random_mutation(child_raw, self._bounds, self._rng, k=self._mutation_k)
        if self._rng.random() < self._mutation_rate
        else child_raw
    )
    # Clip to bounds (defensive, for custom crossover_fn)
    for d in range(n_dims):
        lo, hi = self._bounds[d]
        child[d] = max(lo, min(hi, child[d]))
    next_pop[idx] = child
    next_fit[idx] = self._evaluate(tuple(int(x) for x in child))
    idx += 1
```

---

_Reviewed: 2026-04-11T21:26:14Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_

---
phase: 02-remaining-optimizers
reviewed: 2026-04-11T00:00:00Z
depth: standard
files_reviewed: 15
files_reviewed_list:
  - cyopt/__init__.py
  - cyopt/optimizers/__init__.py
  - cyopt/optimizers/_neighbors.py
  - cyopt/optimizers/basin_hopping.py
  - cyopt/optimizers/best_first_search.py
  - cyopt/optimizers/differential_evolution.py
  - cyopt/optimizers/mcmc.py
  - cyopt/optimizers/simulated_annealing.py
  - tests/test_basin_hopping.py
  - tests/test_best_first_search.py
  - tests/test_differential_evolution.py
  - tests/test_integration.py
  - tests/test_mcmc.py
  - tests/test_seeding.py
  - tests/test_simulated_annealing.py
findings:
  critical: 0
  warning: 3
  info: 3
  total: 6
status: issues_found
---

# Phase 02: Code Review Report

**Reviewed:** 2026-04-11
**Depth:** standard
**Files Reviewed:** 15
**Status:** issues_found

## Summary

The phase 02 implementation adds five new optimizers (BasinHopping, BestFirstSearch, DifferentialEvolution, MCMC, SimulatedAnnealing) plus a shared neighbor utility module. Overall the code is well-structured with clean interfaces, proper validation, good documentation, and comprehensive tests. No security or critical issues were found. Three warnings relate to subtle logic and API design concerns, and three info items note minor code quality improvements.

## Warnings

### WR-01: DifferentialEvolution continuation does not preserve population state

**File:** `cyopt/optimizers/differential_evolution.py:95-148`
**Issue:** Each call to `run()` creates a fresh `scipy.optimize.differential_evolution` invocation. The DE population is re-initialized from scratch on every call, so `continue()` / consecutive `run()` calls do not actually continue the evolutionary process -- they restart it while merely accumulating the evaluation counter and cache. This violates the continuation contract that other optimizers honor (where internal search state persists). The test at `tests/test_differential_evolution.py:43-49` only checks `n_evaluations > evals_after_first`, which passes trivially regardless of whether the population was preserved.
**Fix:** Document this limitation explicitly in the class docstring (that continuation restarts DE from a fresh population but benefits from the evaluation cache), or store and reinject the final population on subsequent calls. At minimum, the docstring should state:

```python
# In the class docstring, add:
"""
.. note::
    Unlike other optimizers, consecutive ``run()`` calls do **not**
    preserve the DE population. Each call restarts the evolutionary
    process from a fresh random population. The evaluation cache is
    preserved, so repeated evaluations of the same candidate are free.
"""
```

### WR-02: BestFirstSearch backtrack mode interleaves first-improving and best-overall logic

**File:** `cyopt/optimizers/best_first_search.py:140-157`
**Issue:** The loop on lines 145-156 serves two purposes simultaneously: (1) find the first improving neighbor and break, and (2) track the overall best neighbor as a fallback. Because the loop breaks on the first improving neighbor, `best_neighbor` / `best_value` may reflect only a partial scan of the neighbor list. When no improving neighbor is found, the fallback on line 158 correctly uses the true best (because the full list was scanned). However, when an improving neighbor IS found, the `best_neighbor` variable is left in an intermediate state. This works correctly today because `best_neighbor` is unused after the break, but the interleaved concerns make the code fragile -- a future change could easily introduce a bug by relying on `best_neighbor` after the loop.
**Fix:** Separate the two concerns into distinct passes, or restructure to make the intent clearer:

```python
# Option: evaluate all neighbors first, then decide
scored = [(self._evaluate(n), n) for n in valid]
scored.sort(key=lambda x: x[0])

best_value, best_neighbor = scored[0]
if best_value < self._current_value:
    # Improving move
    self._path.append(self._current)
    self._current = best_neighbor
    self._current_value = best_value
else:
    # No improving move -- move to best anyway
    self._path.append(self._current)
    self._current = best_neighbor
    self._current_value = best_value
```

### WR-03: Metropolis acceptance can trigger RuntimeWarning on large positive delta

**File:** `cyopt/optimizers/mcmc.py:103`, `cyopt/optimizers/simulated_annealing.py:124`, `cyopt/optimizers/basin_hopping.py:190`
**Issue:** When `delta` is large and negative, `np.exp(-delta / temperature)` computes `exp(large_positive)` which overflows to `inf`. NumPy may emit a RuntimeWarning for this overflow. While the logic still works (the comparison `rng.random() < inf` is True, correctly accepting the improving move), the warning can be noisy in production use. This is most likely to occur with very low temperatures in SimulatedAnnealing or BasinHopping.
**Fix:** Guard the exponential with the `delta < 0` check first (short-circuit), which all three implementations already do. The overflow can only occur when `delta >= 0` (since `-delta/temperature <= 0` when delta >= 0, exp of a non-positive number is in [0,1]). On re-inspection, the overflow can only happen when delta < 0, but that branch is already handled by the `delta < 0` short-circuit. So this is actually a non-issue at the code level -- the `or` short-circuits. Downgrading to info.

## Info

### IN-01: Metropolis overflow is a non-issue (retracted from WR-03)

**File:** `cyopt/optimizers/mcmc.py:103`, `cyopt/optimizers/simulated_annealing.py:124`, `cyopt/optimizers/basin_hopping.py:190`
**Issue:** On closer analysis, the Metropolis acceptance `delta < 0 or rng.random() < np.exp(-delta / temperature)` short-circuits when `delta < 0`. The `np.exp` call only executes when `delta >= 0`, meaning the exponent `-delta/temperature` is always <= 0, producing a result in `[0, 1]`. No overflow is possible. The implementation is correct.
**Fix:** No fix needed. The pattern is sound.

### IN-02: BestFirstSearch frontier mode random restart may revisit a visited node

**File:** `cyopt/optimizers/best_first_search.py:216-219`
**Issue:** When the frontier is exhausted, a random DNA is generated and added to `_visited`. However, there is no check that the random DNA is not already in `_visited`. In a small search space that is nearly fully explored, this could generate a duplicate and waste an iteration (the node will be expanded but all its neighbors are already visited, producing no new frontier entries).
**Fix:** Add a bounded retry loop:

```python
for _ in range(100):
    candidate = self._random_dna()
    if candidate not in self._visited:
        break
self._current = candidate
self._current_value = self._evaluate(candidate)
self._visited.add(candidate)
```

### IN-03: Unused import of Callable in _neighbors.py

**File:** `cyopt/optimizers/_neighbors.py:5`
**Issue:** `Callable` is imported from `collections.abc` but is only used in the module-level type alias `StepFunction`. Since `StepFunction` uses `Callable` at module scope (not inside `if TYPE_CHECKING`), the import is technically used at runtime. However, `StepFunction` is consumed only for type annotation purposes by other modules. This is not a bug but could be noted for future cleanup if the project adopts `TYPE_CHECKING` guards.
**Fix:** No immediate fix needed. This is fine as-is for the current project conventions.

---

_Reviewed: 2026-04-11_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_

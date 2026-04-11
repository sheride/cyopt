---
phase: 02-remaining-optimizers
fixed_at: 2026-04-11T00:00:00Z
review_path: .planning/phases/02-remaining-optimizers/02-REVIEW.md
iteration: 1
findings_in_scope: 6
fixed: 3
skipped: 3
status: partial
---

# Phase 02: Code Review Fix Report

**Fixed at:** 2026-04-11
**Source review:** .planning/phases/02-remaining-optimizers/02-REVIEW.md
**Iteration:** 1

**Summary:**
- Findings in scope: 6
- Fixed: 3
- Skipped: 3

## Fixed Issues

### WR-01: DifferentialEvolution continuation does not preserve population state

**Files modified:** `cyopt/optimizers/differential_evolution.py`
**Commit:** 326241d
**Applied fix:** Added a `.. note::` block to the class docstring documenting that consecutive `run()` calls restart the DE population from scratch, while the evaluation cache is preserved. This sets correct expectations for users of the continuation API.

### WR-02: BestFirstSearch backtrack mode interleaves first-improving and best-overall logic

**Files modified:** `cyopt/optimizers/best_first_search.py`
**Commit:** 7f7ae76
**Applied fix:** Replaced the interleaved loop (which tracked best neighbor while also breaking on first improving neighbor) with a cleaner two-step approach: evaluate all neighbors and sort by fitness, then always move to the best neighbor. This preserves the same behavior (always moves to the best available neighbor, whether improving or not) while eliminating the fragile intermediate state of `best_neighbor` after a mid-loop break.

### IN-02: BestFirstSearch frontier random restart may revisit visited node

**Files modified:** `cyopt/optimizers/best_first_search.py`
**Commit:** e88ae15
**Applied fix:** Added a bounded retry loop (up to 100 attempts) when generating a random restart candidate in frontier mode. The loop checks whether the candidate is already in `_visited` and regenerates if so, preventing wasted iterations in nearly-exhausted search spaces.

## Skipped Issues

### WR-03: Metropolis acceptance can trigger RuntimeWarning on large positive delta

**File:** `cyopt/optimizers/mcmc.py:103`, `cyopt/optimizers/simulated_annealing.py:124`, `cyopt/optimizers/basin_hopping.py:190`
**Reason:** Retracted by reviewer. The reviewer downgraded this to IN-01 after analysis showed the `or` short-circuit prevents overflow. No fix needed.
**Original issue:** Concern that `np.exp(-delta / temperature)` could overflow, but the `delta < 0` check short-circuits before the exponential is evaluated when delta is negative.

### IN-01: Metropolis overflow is a non-issue (retracted from WR-03)

**File:** `cyopt/optimizers/mcmc.py:103`, `cyopt/optimizers/simulated_annealing.py:124`, `cyopt/optimizers/basin_hopping.py:190`
**Reason:** No fix needed per reviewer. The implementation is correct -- the `or` short-circuit ensures `np.exp` only runs when `delta >= 0`, making the exponent non-positive and the result in `[0, 1]`.
**Original issue:** Confirmed non-issue after analysis of the Metropolis acceptance pattern.

### IN-03: Callable import in _neighbors.py

**File:** `cyopt/optimizers/_neighbors.py:5`
**Reason:** No fix needed per reviewer. The `Callable` import is used at runtime for the `StepFunction` type alias. Current usage is correct and consistent with project conventions.
**Original issue:** `Callable` imported from `collections.abc` is technically used at runtime for `StepFunction` alias, which is fine.

---

_Fixed: 2026-04-11_
_Fixer: Claude (gsd-code-fixer)_
_Iteration: 1_

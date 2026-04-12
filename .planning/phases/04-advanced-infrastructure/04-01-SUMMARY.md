---
phase: 04-advanced-infrastructure
plan: 01
subsystem: core-optimizer-infrastructure
tags: [callbacks, early-stopping, CORE-08]
dependency_graph:
  requires: []
  provides: [callback-system, early-stopping-mechanism, iteration-offset-attribute]
  affects: [all-optimizers, base-class]
tech_stack:
  added: []
  patterns: [callback-info-dict, identity-check-early-stop]
key_files:
  created:
    - tests/test_callbacks.py
  modified:
    - cyopt/_types.py
    - cyopt/base.py
    - cyopt/optimizers/differential_evolution.py
    - cyopt/optimizers/random_sample.py
    - cyopt/optimizers/ga.py
    - cyopt/optimizers/greedy_walk.py
    - cyopt/optimizers/best_first_search.py
    - cyopt/optimizers/basin_hopping.py
    - cyopt/optimizers/mcmc.py
    - cyopt/optimizers/simulated_annealing.py
decisions:
  - "Used `is True` identity check for early stopping, not truthiness -- prevents accidental stops from truthy return values like dicts"
  - "Added _iteration_offset=0 to base class now, ready for checkpoint resume in Plan 02"
metrics:
  duration_seconds: 200
  completed: "2026-04-12T04:44:31Z"
  tasks_completed: 1
  tasks_total: 1
  tests_added: 19
  tests_total: 184
---

# Phase 04 Plan 01: Callback System Summary

Iteration callback system with early stopping for all 8 optimizers, using identity-checked `return True` and a per-iteration info dict with 5 required fields.

## What Was Built

Added a callback system to the DiscreteOptimizer base class and all 8 concrete optimizers:

1. **Type definitions** (`cyopt/_types.py`): `CallbackInfo = dict[str, Any]` and `Callback = Callable[[CallbackInfo], bool | None]` type aliases.

2. **Base class** (`cyopt/base.py`): `callbacks` parameter in constructor, stored as `self._callbacks`. The `run()` loop invokes each callback with an info dict containing `iteration`, `best_value`, `best_solution`, `n_evaluations`, `wall_time`. Early stopping triggers only on `cb(cb_info) is True` (identity check).

3. **DE integration** (`cyopt/optimizers/differential_evolution.py`): User callbacks invoked inside SciPy's native callback function. Returns `True` to SciPy to halt evolution when user callback triggers early stop.

4. **All optimizer constructors**: All 8 optimizers (RandomSample, GA, GreedyWalk, BestFirstSearch, BasinHopping, MCMC, SimulatedAnnealing, DifferentialEvolution) accept `callbacks` parameter and pass through to base.

5. **`_iteration_offset`**: Added to base class (default 0) for use by callbacks now and checkpoint resume in Plan 02.

## Commits

| Task | Commit | Description |
|------|--------|-------------|
| 1 (RED) | ea006ea | Failing tests for callback system |
| 1 (GREEN) | dcd00f2 | Implement callback system for all optimizers |

## Test Results

- 19 new tests in `tests/test_callbacks.py`
- 184 total tests passing, 0 failures, 0 regressions

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed test import: GA class name**
- **Found during:** Task 1 GREEN phase
- **Issue:** Test file imported `GeneticAlgorithm` but the class is named `GA`
- **Fix:** Changed import and all references to `GA`
- **Files modified:** tests/test_callbacks.py
- **Commit:** dcd00f2

## Self-Check: PASSED

All key files verified present. All commit hashes verified in git log.

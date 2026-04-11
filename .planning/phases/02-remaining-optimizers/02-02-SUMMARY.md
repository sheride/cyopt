---
phase: 02-remaining-optimizers
plan: 02
subsystem: optimizers
tags: [basin-hopping, differential-evolution, scipy, discrete-optimization]
dependency_graph:
  requires: [base.py, greedy_walk.py, _types.py]
  provides: [basin_hopping.py, differential_evolution.py]
  affects: [optimizers/__init__.py]
tech_stack:
  added: []
  patterns: [scipy-public-api-wrapper, metropolis-acceptance, greedy-descent-local-minimizer]
key_files:
  created:
    - cyopt/optimizers/basin_hopping.py
    - cyopt/optimizers/differential_evolution.py
    - tests/test_basin_hopping.py
    - tests/test_differential_evolution.py
  modified: []
decisions:
  - "Defined random_single_flip inline in basin_hopping.py since _neighbors.py does not yet exist (parallel wave dependency)"
  - "DE uses rng= parameter (not seed=) for reproducible Generator-based seeding"
  - "BasinHopping greedy descent capped at 100 iterations to prevent infinite loops on flat landscapes"
metrics:
  duration: 140s
  completed: "2026-04-11T22:19:32Z"
  tasks_completed: 2
  tasks_total: 2
  test_count: 15
  test_pass: 15
---

# Phase 02 Plan 02: BasinHopping + DifferentialEvolution Summary

Custom discrete basin-hopping with injectable local minimizer/perturbation and SciPy DE wrapper using public integrality API with half-open bounds and Generator-based seeding.

## What Was Done

### Task 1: Implement BasinHopping and DifferentialEvolution optimizers

**BasinHopping** (`cyopt/optimizers/basin_hopping.py`):
- Custom implementation operating on integer-tuple space (no SciPy private API)
- Default local minimizer: `_greedy_descent` using `hamming_neighbors` from `greedy_walk.py`
- Default perturbation: `random_single_flip` (defined inline; `_neighbors.py` not yet available from parallel wave)
- Injectable `local_minimize_fn(dna, bounds, evaluate_fn) -> DNA` and `perturb_fn(dna, bounds, rng) -> DNA`
- Metropolis acceptance criterion: `exp(-delta / temperature)`
- `n_perturbations` parameter for multi-flip default perturbation
- Temperature validation (must be > 0)
- State persists across consecutive `run()` calls

**DifferentialEvolution** (`cyopt/optimizers/differential_evolution.py`):
- Wraps `scipy.optimize.differential_evolution` (public API only)
- `integrality=[True] * n_dims` for native integer support
- Bounds transformed to half-open: `(lo, hi + 1)` for correct integer semantics
- `rng=self._rng` (not `seed=`) for reproducible Generator-based seeding
- `tol=0` (no early convergence stopping), `polish=False` (no continuous polishing)
- Overrides `run()` directly; `_step()` raises `NotImplementedError`
- Per-generation history via SciPy callback
- State (cache, n_evaluations, best) persists across consecutive `run()` calls

### Task 2: Create unit tests

- 7 tests for BasinHopping: finds improvement, custom local_minimize_fn, custom perturb_fn, seeding, continuation, invalid temperature, result fields
- 8 tests for DifferentialEvolution: finds improvement, _step raises, seeding, continuation, history populated, bounds respected, result fields, public API check
- All 15 tests pass

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Defined random_single_flip inline**
- **Found during:** Task 1
- **Issue:** `cyopt/optimizers/_neighbors.py` does not exist yet (created by Plan 01 in parallel wave)
- **Fix:** Defined `random_single_flip` directly in `basin_hopping.py` with identical signature
- **Files modified:** `cyopt/optimizers/basin_hopping.py`
- **Commit:** 2d842d2

## Commits

| Task | Commit | Message |
|------|--------|---------|
| 1+2 | 2d842d2 | feat(02-02): implement BasinHopping and DifferentialEvolution optimizers with tests |

## Verification

```
conda run -n cytools pytest tests/test_basin_hopping.py tests/test_differential_evolution.py -x -v
# 15 passed in 0.61s

conda run -n cytools python -c "from cyopt.optimizers.basin_hopping import BasinHopping; from cyopt.optimizers.differential_evolution import DifferentialEvolution; print('OK')"
# OK
```

## Self-Check: PASSED

---
phase: 03-frst-wrapper
plan: 02
subsystem: frst-wrapper
tags: [wrapper, factory, result, frst, integration-tests]
dependency_graph:
  requires: [cyopt.frst._encoding, cyopt.base, cyopt._types, cyopt.optimizers]
  provides: [cyopt.frst._result, cyopt.frst._wrapper, cyopt.frst.FRSTResult, cyopt.frst.frst_optimizer]
  affects: [documentation (Phase 4)]
tech_stack:
  added: []
  patterns: [factory function, fitness negation bridge, ancillary data capture]
key_files:
  created:
    - cyopt/frst/_result.py
    - cyopt/frst/_wrapper.py
    - tests/test_frst/test_wrapper.py
  modified:
    - cyopt/frst/__init__.py
    - cyopt/frst/_encoding.py
decisions:
  - Used poly_with_faces (h11=7) fixture for wrapper tests requiring multi-dimensional DNA
  - Added DNA index clamping in _dna_to_frst to handle DE boundary rounding edge case
metrics:
  duration: 259s
  completed: "2026-04-12T00:05:56Z"
---

# Phase 3 Plan 2: FRSTOptimizer Wrapper and Factory Summary

FRSTOptimizer wrapper connecting all 8 generic optimizers to FRST optimization via fitness negation bridge, with FRSTResult dataclass providing un-negated best_value and decoded triangulation/CY fields.

## What Was Built

### cyopt/frst/_result.py
FRSTResult frozen dataclass wrapping the generic `Result` with FRST-specific fields:
- `best_triangulation`: Decoded Triangulation from best DNA
- `best_cy`: Decoded CalabiYau (None in triangulation mode)
- `ancillary_data`: DNA-to-ancillary mapping from target evaluations
- `best_value` property: Un-negated target value (higher is better)
- `history` property: Un-negated best-so-far values per iteration
- Convenience properties: `best_dna`, `n_evaluations`, `wall_time`

### cyopt/frst/_wrapper.py
FRSTOptimizer class and frst_optimizer factory:
- `FRSTOptimizer.__init__`: Accepts poly, target, optimizer_cls, target_mode, penalty, and optimizer kwargs. Auto-calls `prep_for_optimizers()`.
- `_make_fitness`: Bridges user target (higher-is-better) to optimizer fitness (lower-is-better) via negation. Handles None FRST returns with configurable penalty. Supports `(value, ancillary)` tuple returns.
- `run(n_iterations)`: Runs optimizer, decodes best DNA to triangulation/CY, returns FRSTResult.
- `frst_optimizer()` factory: Defaults to GA, accepts any optimizer class + kwargs.

### cyopt/frst/__init__.py (updated)
Added exports for FRSTResult, FRSTOptimizer, frst_optimizer to `__all__`.

### cyopt/frst/_encoding.py (patched)
Added DNA index clamping in `_dna_to_frst` to handle edge case where DifferentialEvolution produces boundary values due to SciPy's integrality floating-point rounding.

### tests/test_frst/test_wrapper.py
9 integration tests:
1. `test_frst_optimizer_factory` - Factory returns FRSTOptimizer with GA default
2. `test_frst_result` - Run produces FRSTResult with all fields populated
3. `test_frst_result_value_unnegated` - best_value is positive when target returns 42.0
4. `test_target_mode_triangulation` - Triangulation mode skips CY, passes Triangulation to target
5. `test_ancillary_data` - (value, ancillary) tuples stored and accessible
6. `test_all_optimizers` - All 8 optimizer classes work through the wrapper
7. `test_custom_kwargs_passed` - population_size=5 forwarded to GA
8. `test_top_level_import_no_frst` - `import cyopt` does not trigger CYTools import

## Verification

All 165 tests pass: `conda run -n cytools pytest tests/ -x -q` exits 0.
FRST-specific: 19 tests pass (11 encoding + 8 wrapper + 1 standalone).

## Task Commits

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | FRSTResult dataclass and FRSTOptimizer wrapper with factory | 44bf69c | cyopt/frst/_result.py, cyopt/frst/_wrapper.py |
| 2 | Wire exports and integration tests for all 8 optimizers | 90307bb | cyopt/frst/__init__.py, cyopt/frst/_encoding.py, tests/test_frst/test_wrapper.py |

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] DNA index out-of-range from DifferentialEvolution**
- **Found during:** Task 2 (test_all_optimizers)
- **Issue:** SciPy's `differential_evolution` with `integrality=True` and half-open bounds `(lo, hi+1)` can produce integer values at `hi+1` due to floating-point rounding, causing IndexError in `_dna_to_frst`.
- **Fix:** Added index clamping `max(0, min(dna[i], len(face_list) - 1))` in `_dna_to_frst`.
- **Files modified:** cyopt/frst/_encoding.py
- **Commit:** 90307bb

**2. [Rule 3 - Blocking] Test fixture polytope with zero interesting faces**
- **Found during:** Task 2 (test_frst_result)
- **Issue:** The `poly_h11_4` fixture (first h11=4 polytope) has zero interesting faces, producing empty DNA/bounds. GA crossover crashes on empty arrays.
- **Fix:** Created `poly_with_faces` fixture using h11=7 (first polytope has 2 interesting faces with bounds (0,2) each).
- **Files modified:** tests/test_frst/test_wrapper.py
- **Commit:** 90307bb

## Self-Check: PASSED

- [x] cyopt/frst/_result.py exists
- [x] cyopt/frst/_wrapper.py exists
- [x] cyopt/frst/__init__.py exists (updated)
- [x] tests/test_frst/test_wrapper.py exists
- [x] Commit 44bf69c exists in git log
- [x] Commit 90307bb exists in git log
- [x] All 165 tests pass (19 FRST + 146 generic)
- [x] No stubs or placeholders found

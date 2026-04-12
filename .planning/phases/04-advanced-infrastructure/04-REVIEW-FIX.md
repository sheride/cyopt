---
phase: 04-advanced-infrastructure
fixed_at: 2026-04-12T00:00:00Z
review_path: .planning/phases/04-advanced-infrastructure/04-REVIEW.md
iteration: 1
findings_in_scope: 4
fixed: 4
skipped: 0
status: all_fixed
---

# Phase 04: Code Review Fix Report

**Fixed at:** 2026-04-12T00:00:00Z
**Source review:** .planning/phases/04-advanced-infrastructure/04-REVIEW.md
**Iteration:** 1

**Summary:**
- Findings in scope: 4
- Fixed: 4
- Skipped: 0

## Fixed Issues

### WR-01: `EvaluationCache.from_list` Does Not Enforce `maxsize` During Restore

**Files modified:** `cyopt/_cache.py`
**Commit:** de0ae8c
**Applied fix:** Added a trim step in `from_list` that truncates the items list to the last `maxsize` entries (preserving LRU order by keeping the most-recently-used tail) before inserting into the internal OrderedDict. This ensures the restored cache never exceeds `maxsize`.

### WR-02: `DifferentialEvolution.run()` Returns `Result` With `best_solution=None` When No Evaluations Occur

**Files modified:** `cyopt/optimizers/differential_evolution.py`
**Commit:** 3e9b50e
**Applied fix:** Added a null check for `self._best_solution` after the SciPy DE call completes and before constructing the `Result`, matching the same guard used in the base class `run()`. Raises `RuntimeError` if no solution was evaluated.

### WR-03: `record_history` and `progress` Are Serialized But Not Restored From Checkpoint

**Files modified:** `cyopt/base.py`
**Commit:** d309b4d
**Applied fix:** Added restoration of `_record_history` and `_progress` fields in `_set_common_state` using `state.get()` with `False` defaults for backward compatibility with older checkpoints that may not contain these keys.

### WR-04: `BestFirstSearch` Frontier-Exhausted Restart Silently Fails to Find Unvisited Nodes

**Files modified:** `cyopt/optimizers/best_first_search.py`
**Commit:** c445706
**Applied fix:** Restructured the frontier-exhaustion branch to use a for/else pattern: tries up to 1000 random candidates to find an unvisited one, and if all are visited (search space fully explored), clears `_visited` and restarts. This prevents the silent re-processing of already-visited points in small search spaces.

## Skipped Issues

None -- all findings were fixed.

---

_Fixed: 2026-04-12T00:00:00Z_
_Fixer: Claude (gsd-code-fixer)_
_Iteration: 1_

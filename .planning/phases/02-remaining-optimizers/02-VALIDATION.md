---
phase: 02
slug: remaining-optimizers
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-04-11
---

# Phase 02 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 9.0.2 |
| **Config file** | pyproject.toml |
| **Quick run command** | `conda run -n cytools pytest tests/ -x -q` |
| **Full suite command** | `conda run -n cytools pytest tests/ -v` |
| **Estimated runtime** | ~1 second |

---

## Sampling Rate

- **After every task commit:** Run `conda run -n cytools pytest tests/ -x -q`
- **After every plan completion:** Run `conda run -n cytools pytest tests/ -v`

---

## Validation Architecture

### Wave 0: Test Infrastructure (from Phase 1)

Test infrastructure already established:
- conftest.py with `sphere_fitness`, `standard_bounds`, `small_bounds` fixtures
- Base class contract tests in test_base.py
- Integration test patterns in test_integration.py
- Seeding tests in test_seeding.py

### Per-Optimizer Validation

Each new optimizer must pass:
1. **Correctness**: Finds improving solutions on sphere_fitness
2. **Seeding**: Same seed produces identical results
3. **Caching**: Uses evaluation cache (n_evaluations < total calls)
4. **History**: record_history=True populates full_history
5. **Continuation**: State persists across consecutive run() calls
6. **Contract**: Returns valid Result with all fields

### Integration Validation

- All 8 optimizers pass parametrized contract tests
- All 8 optimizers importable from `cyopt`
- Cross-optimizer seeding test suite

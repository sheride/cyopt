---
phase: 03-frst-wrapper
plan: 01
subsystem: frst-encoding
tags: [encoding, monkey-patch, cytools, dna, frst]
dependency_graph:
  requires: [cytools.Polytope, cyopt._types]
  provides: [cyopt.frst._encoding, cyopt.frst.__init__]
  affects: [cyopt.frst._wrapper (Plan 02)]
tech_stack:
  added: []
  patterns: [monkey-patch, frozenset simplex normalization, import guard]
key_files:
  created:
    - cyopt/frst/__init__.py
    - cyopt/frst/_encoding.py
    - tests/test_frst/__init__.py
    - tests/test_frst/conftest.py
    - tests/test_frst/test_encoding.py
  modified: []
decisions:
  - Used frozenset of sorted int tuples for O(1) simplex comparison (per research recommendation)
  - Module-scoped fixture for poly_h11_4 to avoid repeated fetch in tests
metrics:
  duration: 124s
  completed: "2026-04-11T23:57:17Z"
---

# Phase 3 Plan 1: DNA Encoding/Decoding Layer Summary

DNA encoding layer mapping integer-tuple DNA to CYTools FRST triangulations via 2-face triangulation choices, with Polytope monkey-patch for optimizer integration.

## What Was Built

### cyopt/frst/_encoding.py
Core encoding/decoding module with six functions:
- `_normalize_simplices`: Converts simplices (ndarray or list) to frozenset of sorted int tuples for O(1) comparison
- `_prep_for_optimizers`: Precomputes 2-face triangulations, identifies interesting faces, builds bounds tuple, caches simplex sets
- `_dna_to_frst`: Maps DNA tuple to FRST Triangulation via `triangfaces_to_frst()` (CYTools public API)
- `_dna_to_cy`: Maps DNA to CalabiYau via dna_to_frst + get_cy
- `_triang_to_dna`: Reverses FRST to DNA via `restrict()` + simplex matching against precomputed sets
- `_cy_to_dna`: Reverses CalabiYau to DNA via triangulation extraction + triang_to_dna
- `patch_polytope`: Attaches all functions as bound methods on `cytools.Polytope`

### cyopt/frst/__init__.py
Import guard that raises helpful ImportError when CYTools is unavailable. Auto-calls `patch_polytope()` on import.

### tests/test_frst/
- `conftest.py`: `requires_cytools` skip marker + `poly_h11_4` module-scoped fixture
- `test_encoding.py`: 11 tests covering prep attributes, idempotency, non-reflexive guard, DNA-to-FRST, triang-to-DNA type checking, full roundtrip (zero and nonzero DNA), CY roundtrip, and monkey-patch verification

## Verification

All 11 tests pass: `conda run -n cytools pytest tests/test_frst/test_encoding.py -x -q` exits 0 in 1.02s.

## Task Commits

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | DNA encoding module + tests | 1ad2026 | cyopt/frst/__init__.py, cyopt/frst/_encoding.py, tests/test_frst/__init__.py, tests/test_frst/conftest.py, tests/test_frst/test_encoding.py |

## Deviations from Plan

None -- plan executed exactly as written.

## Self-Check: PASSED

- [x] cyopt/frst/__init__.py exists
- [x] cyopt/frst/_encoding.py exists
- [x] tests/test_frst/__init__.py exists
- [x] tests/test_frst/conftest.py exists
- [x] tests/test_frst/test_encoding.py exists
- [x] Commit 1ad2026 exists in git log
- [x] All 11 tests pass
- [x] No stubs or placeholders found

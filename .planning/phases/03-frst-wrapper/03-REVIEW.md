---
phase: 03-frst-wrapper
reviewed: 2026-04-11T12:00:00Z
depth: standard
files_reviewed: 8
files_reviewed_list:
  - cyopt/frst/__init__.py
  - cyopt/frst/_encoding.py
  - cyopt/frst/_result.py
  - cyopt/frst/_wrapper.py
  - tests/test_frst/__init__.py
  - tests/test_frst/conftest.py
  - tests/test_frst/test_encoding.py
  - tests/test_frst/test_wrapper.py
findings:
  critical: 0
  warning: 3
  info: 2
  total: 5
status: issues_found
---

# Phase 3: Code Review Report

**Reviewed:** 2026-04-11
**Depth:** standard
**Files Reviewed:** 8
**Status:** issues_found

## Summary

The FRST wrapper layer is well-structured with clean separation between encoding (`_encoding.py`), result (`_result.py`), and wrapper (`_wrapper.py`) concerns. The monkey-patch approach is documented and idempotent. The test suite covers roundtrip correctness, all 8 optimizer classes, and edge cases (non-reflexive polytopes, ancillary data).

Three warnings relate to missing guard checks and a potentially confusing edge-case value. Two informational items note minor robustness improvements.

## Warnings

### WR-01: Missing `_cyopt_prepped` guard in encoding methods

**File:** `cyopt/frst/_encoding.py:99`
**Issue:** `_dna_to_frst`, `_triang_to_dna`, `_dna_to_cy`, and `_cy_to_dna` all access `self._cyopt_face_triangs` and other `_cyopt_*` attributes without verifying `self._cyopt_prepped is True`. If a user calls `poly.dna_to_frst(dna)` before `poly.prep_for_optimizers()`, they get an opaque `AttributeError: '_cyopt_face_triangs'` instead of a helpful message. While `FRSTOptimizer.__init__` calls `prep_for_optimizers()` automatically, the methods are also part of the public monkey-patched API and can be called directly.
**Fix:** Add a guard at the top of each encoding method:
```python
def _dna_to_frst(self, dna: DNA) -> object | None:
    if not getattr(self, "_cyopt_prepped", False):
        raise RuntimeError(
            "Call poly.prep_for_optimizers() before using DNA encoding methods."
        )
    # ... rest of method
```
Alternatively, factor this into a single decorator or helper to keep it DRY.

### WR-02: `best_value` returns `-inf` when best solution hit penalty

**File:** `cyopt/frst/_result.py:46-47`
**Issue:** `best_value` unconditionally negates `self.result.best_value`. If every DNA evaluated produced a non-solid cone (penalty = `float('inf')`), then `best_value` returns `-inf`. While unlikely in practice, this is a confusing value for users who expect "higher is better" semantics -- `-inf` is the worst possible score but is indistinguishable from a real failure mode. There is no indication that no valid triangulation was found.
**Fix:** Document this edge case in the docstring, or add a check:
```python
@property
def best_value(self) -> float:
    """The best target value (un-negated: higher is better).

    Returns ``-inf`` if no valid FRST was found during optimization.
    """
    return -self.result.best_value
```

### WR-03: `isinstance(result, tuple)` ancillary check is fragile

**File:** `cyopt/frst/_wrapper.py:117`
**Issue:** The check `isinstance(result, tuple)` to detect `(value, ancillary_data)` returns will also trigger on any tuple returned as a bare value (e.g., if a user's target function accidentally returns a 2-tuple of floats). Named tuples and tuple subclasses also match. This could silently misinterpret return values.
**Fix:** Use a more explicit protocol. For example, check for exactly length 2 with a non-numeric second element, or document the convention clearly and accept the trade-off:
```python
if isinstance(result, tuple) and len(result) == 2:
    value, anc = result
    if not isinstance(value, (int, float)):
        raise TypeError(
            f"Target function returned tuple but first element is "
            f"{type(value).__name__}, expected numeric."
        )
    ancillary[dna] = anc
```

## Info

### IN-01: Type annotation mismatch on `_cyopt_face_simp_sets`

**File:** `cyopt/frst/_encoding.py:75`
**Issue:** The type annotation `list[list[frozenset]]` is imprecise. The actual type is `list[list[frozenset[tuple[int, ...]]]]`. While this is an internal attribute and not user-facing, precise types improve IDE support and maintainability.
**Fix:**
```python
self._cyopt_face_simp_sets: list[list[frozenset[tuple[int, ...]]]] = []
```

### IN-02: Test `sys.modules` manipulation lacks robust cleanup

**File:** `tests/test_frst/test_wrapper.py:143-165`
**Issue:** `test_top_level_import_no_frst` manually deletes and restores `sys.modules` entries. If the test body raises before the `finally` block, the `saved` dict is properly restored, but the deleted `frst_modules` (line 149-150) are not saved before deletion -- they are lost. The `finally` block only restores `cyopt_modules` saved on line 156, not the `frst_modules` deleted on lines 149-150.
**Fix:** Save `frst_modules` as well:
```python
frst_modules = {k: sys.modules.pop(k) for k in list(sys.modules) if k.startswith("cyopt.frst")}
cyopt_modules = {k: sys.modules.pop(k) for k in list(sys.modules) if k.startswith("cyopt")}
try:
    # ... test body
finally:
    sys.modules.update(cyopt_modules)
    sys.modules.update(frst_modules)
```

---

_Reviewed: 2026-04-11_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_

# Phase 3: FRST Wrapper - Research

**Researched:** 2026-04-11
**Domain:** CYTools FRST encoding/decoding + wrapper API for generic discrete optimizers
**Confidence:** HIGH

## Summary

Phase 3 connects the 8 generic discrete optimizers (Phase 1-2) to CYTools' FRST pipeline via a DNA encoding of 2-face triangulation choices. The core data flow is: (1) precompute 2-face triangulations for a polytope, (2) identify "interesting" faces (those with >1 triangulation), (3) encode/decode between DNA integer tuples and FRST triangulations, (4) wrap the user's target function to bridge CY/Triangulation objects to the optimizer's `DNA -> float` contract.

CYTools already provides the heavy lifting: `face_triangs()` enumerates 2-face triangulations, `triangfaces_to_frst()` converts face triangulation choices to an FRST via LP interior-point computation, and `Triangulation.restrict()` decomposes an FRST back into 2-face restrictions for the reverse mapping. The old code (`triang_optimizer.py`) reimplemented much of this from `cornell-dev/lib` utilities (`secondary_cone.hypers_to_cone`, `matrix.LIL_stack`). The new implementation should use CYTools' public API exclusively, which is cleaner and avoids porting library code.

The wrapper layer needs: (a) a `prep_for_optimizers` monkey-patch on Polytope that precomputes and caches face triangulation data, (b) DNA encoding/decoding functions (`dna_to_frst`, `dna_to_cy`, `triang_to_dna`, `cy_to_dna`), (c) a factory function `frst_optimizer()` that wires everything together, and (d) an `FRSTResult` type that extends the base `Result` with decoded triangulation/CY fields.

**Primary recommendation:** Use CYTools' `triangfaces_to_frst()` as the core DNA-to-FRST conversion (replaces the old code's manual LP solver pipeline). Use `Triangulation.restrict()` + simplex matching for the reverse FRST-to-DNA path. Both are verified working in the current CYTools version.

<user_constraints>

## User Constraints (from CONTEXT.md)

### Locked Decisions
- **D-01:** Monkey-patch `prep_for_optimizers` and all encoding/decoding functions (`dna_to_frst`, `dna_to_cy`, `triang_to_dna`, `cy_to_dna`) as bound methods on `Polytope`, matching the old code's interface. Users call `poly.prep_for_optimizers()` then `poly.dna_to_frst(dna)`.
- **D-02:** Provide a factory function `frst_optimizer(poly, target, optimizer=GA, **kwargs)` that preps the polytope, builds fitness function + bounds from the DNA encoding, instantiates the specified generic optimizer, and returns a wrapped optimizer instance.
- **D-03:** The wrapper's `run()` returns an `FRSTResult` (or similar) with `best_triangulation`, `best_cy` fields auto-decoded from DNA. The underlying generic optimizer is accessible via an attribute (e.g., `wrapper.optimizer`) for power users who want raw DNA results or optimizer state.
- **D-04:** The user provides the optimizer class (e.g., `GA`, `MCMC`) and any optimizer-specific hyperparameters as kwargs to `frst_optimizer`.
- **D-05:** Target function receives a CY manifold object by default: `target(cy) -> float`. A mode flag (e.g., `target_mode='triangulation'`) allows the target to receive a Triangulation instead, for users who want to skip CY construction overhead.
- **D-06:** Ancillary data from target evaluations should be preservable. Implementation mechanism is Claude's discretion.
- **D-07:** Check both CYTools and cornell-dev/lib for functions the old code used. Use CYTools public API whenever possible. Port anything that only lives in cornell-dev/lib into this repository.
- **D-08:** Use `triangfaces_to_frst` (CYTools public API) for the DNA-to-FRST conversion path. Do not reimplement LP solvers or height-finding logic.
- **D-09:** General principle: always prefer CYTools public API over reimplementation. No private API imports.

### Claude's Discretion
- Ancillary data storage mechanism (D-06)
- Internal structure of the `cyopt/frst/` subpackage (module layout)
- Whether FRSTResult is a dataclass, namedtuple, or extends Result

### Deferred Ideas (OUT OF SCOPE)
None -- discussion stayed within phase scope

</user_constraints>

<phase_requirements>

## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| FRST-01 | Monkey-patch Polytope with `prep_for_optimizers` (2-face triangulation precomputation) | CYTools `face_triangs()`, `triangface_ineqs()` verified available. Precomputation pattern clear from old code. See Architecture Patterns. |
| FRST-02 | DNA encoding functions: `dna_to_frst`, `dna_to_cy`, `triang_to_dna`, `cy_to_dna` | Roundtrip verified: DNA -> `triangfaces_to_frst()` -> `restrict()` -> simplex matching -> DNA. See Code Examples. |
| FRST-03 | FRST-specific optimizer wrappers connecting each generic optimizer to the DNA encoding | Factory function pattern wrapping `DiscreteOptimizer` subclasses with DNA-aware fitness and FRSTResult. See Architecture Patterns. |
| FRST-04 | Compatible with current CYTools API (updated imports, method names, arguments) | All required CYTools methods verified in current install. No cornell-dev/lib porting needed. See Standard Stack and CYTools API Verification. |

</phase_requirements>

## Standard Stack

### Core (Phase 3 additions)

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| CYTools | (conda env) | FRST triangulation pipeline | Provides `face_triangs()`, `triangfaces_to_frst()`, `Triangulation.restrict()` -- all verified in current install [VERIFIED: conda env inspection] |

### Already Available (from Phase 1-2)

| Library | Version | Purpose |
|---------|---------|---------|
| cyopt.base.DiscreteOptimizer | 0.1.0 | Base class for all 8 optimizers |
| cyopt._types (DNA, Bounds, Result) | 0.1.0 | Core type definitions |
| cyopt._cache.EvaluationCache | 0.1.0 | Fitness evaluation caching |

### No Additional Dependencies

Phase 3 requires no new pip packages. CYTools is already in the conda environment as an optional dependency. The `cyopt/frst/` subpackage uses only CYTools + the existing cyopt core.

## CYTools API Verification

All CYTools methods needed by the FRST wrapper have been verified in the current conda environment. [VERIFIED: conda run -n cytools, live testing]

| Method | Signature | Status | Notes |
|--------|-----------|--------|-------|
| `Polytope.face_triangs(dim=2)` | Returns `list[list[Triangulation]]` | Available | Each element is a list of Triangulation objects for one 2-face |
| `Polytope.triangfaces_to_frst(triangs)` | `(list[Triangulation|None]) -> Triangulation|None` | Available | Wrapper around `triangfaces_to_frt(make_star=True)`. Accepts `None` entries for "free" faces. |
| `Polytope.triangface_ineqs(return_triangs=True)` | Returns `(ineqs, face_triangs)` | Available | Used by old code but NOT needed -- `face_triangs()` + `triangfaces_to_frst()` replaces this entirely |
| `Triangulation.restrict(restrict_dim=2)` | Returns `list[list[list[int]]]` | Available | Default: restricts to all 2-faces. Returns sorted simplex lists. |
| `Triangulation.simplices()` | Returns `np.ndarray` | Available | Used for matching restrictions to face triangulations |
| `Triangulation.get_cy()` | Returns `CalabiYau` | Available | Used in `dna_to_cy` |
| `Polytope.labels_facet` | Property, returns tuple | Available | Points interior to facets (removed from height vector) |
| `Polytope.labels_not_facet` | Property, returns tuple | Available | Points used in triangulation |
| `Polytope.is_reflexive()` | Returns bool | Available | Guard for FRST pipeline |
| `Polytope.faces(dim)` | Returns list of PolytopeFace | Available | Used internally by `restrict()` |

### Old Code Dependencies NOT Needed

| Old Import | Old Purpose | Replacement |
|------------|-------------|-------------|
| `lib.geom.secondary_cone.hypers_to_cone` | Build secondary cone from face ineqs | `triangfaces_to_frst()` handles internally |
| `lib.util.matrix.LIL_stack` | Stack sparse inequality matrices | `triangfaces_to_frst()` handles internally |
| `lib.cytools_ext.triangulation_ext` | Triangulation extensions | Not needed for DNA encoding |
| `scipy.optimize._basinhopping` | Private API import | Already replaced in Phase 2 |
| `scipy.optimize._differentialevolution` | Private API import | Already replaced in Phase 2 |

**Key finding:** The old code's `dna_to_frst` manually builds a secondary cone from face triangulation inequalities, finds an interior point, then constructs a Triangulation from heights. CYTools' `triangfaces_to_frst()` does exactly this internally via `cone_of_permissible_heights()`. No cornell-dev/lib code needs porting. [VERIFIED: source inspection of CYTools `triangfaces_to_frt`]

## Architecture Patterns

### Recommended Module Layout

```
cyopt/
  frst/
    __init__.py       # Public API: frst_optimizer, FRSTResult, patch_polytope
    _encoding.py      # prep_for_optimizers, dna_to_frst, dna_to_cy, triang_to_dna, cy_to_dna
    _wrapper.py       # FRSTOptimizer wrapper class, frst_optimizer factory
    _result.py        # FRSTResult dataclass
```

### Pattern 1: DNA Encoding via CYTools Public API

**What:** Map between integer-tuple DNA and FRST triangulations using CYTools' face triangulation enumeration.

**When to use:** All DNA encoding/decoding operations.

**How it works:**

1. `prep_for_optimizers()` calls `poly.face_triangs()` to get all 2-face triangulations
2. Identifies "interesting" faces (those with >1 triangulation) -- these define the DNA dimensions
3. Bounds are `(0, n_triangs - 1)` per interesting face
4. `dna_to_frst(dna)`: builds a list of face Triangulation objects indexed by DNA, passes to `poly.triangfaces_to_frst()`
5. `triang_to_dna(triang)`: calls `triang.restrict()`, matches each restriction's simplices against stored face triangulations

```python
# Source: verified against CYTools API + roundtrip tested
def _prep_for_optimizers(self, **kwargs):
    if getattr(self, '_cyopt_prepped', False):
        return
    if not self.is_reflexive():
        raise ValueError("FRST optimization requires reflexive polytopes.")

    # Precompute all 2-face triangulations
    self._cyopt_face_triangs = self.face_triangs(**kwargs)

    # Identify interesting faces (>1 triangulation)
    self._cyopt_interesting = []
    self._cyopt_bounds = []
    for i, face_ts in enumerate(self._cyopt_face_triangs):
        if len(face_ts) > 1:
            self._cyopt_interesting.append(i)
            self._cyopt_bounds.append((0, len(face_ts) - 1))

    # Precompute simplex sets for reverse mapping
    self._cyopt_face_simp_sets = []
    for face_ts in self._cyopt_face_triangs:
        self._cyopt_face_simp_sets.append([
            frozenset(tuple(sorted(s)) for s in ft.simplices())
            for ft in face_ts
        ])

    self._cyopt_prepped = True
```

### Pattern 2: Fitness Function Bridging

**What:** Wrap a user's `target(cy) -> float` into the optimizer's `DNA -> float` contract.

**When to use:** `frst_optimizer()` factory function.

**Key considerations:**
- User target takes CY or Triangulation objects; optimizer expects DNA tuples
- Failed DNA-to-FRST conversions (non-solid cones) must return a penalty value
- Ancillary data from target should be stored alongside

```python
# Source: design based on old code + new optimizer contract
def _make_fitness(poly, target, target_mode='cy', penalty=float('inf')):
    ancillary_store = {}  # keyed by DNA

    def fitness(dna):
        triang = poly.dna_to_frst(dna)
        if triang is None:
            return penalty  # non-solid cone -> penalize

        if target_mode == 'cy':
            obj = triang.get_cy()
        else:
            obj = triang

        result = target(obj)

        # Support target returning (value, ancillary) or just value
        if isinstance(result, tuple):
            value, anc = result
            ancillary_store[dna] = anc
        else:
            value = result

        return -value  # old code maximized; new optimizers minimize

    return fitness, ancillary_store
```

### Pattern 3: FRSTResult Extending Result

**What:** Wrap the base `Result` to add decoded triangulation/CY fields.

**Recommendation:** Make `FRSTResult` a frozen dataclass that wraps (not extends) `Result`, because `Result` is also a frozen dataclass and inheritance of frozen dataclasses is awkward. Store the underlying `Result` as an attribute. Decode `best_triangulation` and `best_cy` lazily.

```python
@dataclass(frozen=True)
class FRSTResult:
    result: Result              # underlying optimizer result
    best_triangulation: object  # Triangulation (decoded from best_solution)
    best_cy: object             # CalabiYau (decoded from best_solution)
    ancillary_data: dict        # DNA -> ancillary data mapping

    # Delegate common attributes
    @property
    def best_dna(self):
        return self.result.best_solution

    @property
    def best_value(self):
        return self.result.best_value
```

### Pattern 4: Import Guard for CYTools

**What:** The `cyopt.frst` subpackage must only be importable when CYTools is available.

```python
# cyopt/frst/__init__.py
try:
    from cytools import Polytope
except ImportError as e:
    raise ImportError(
        "cyopt.frst requires CYTools. Install it or activate the cytools "
        "conda environment."
    ) from e

from cyopt.frst._encoding import patch_polytope
from cyopt.frst._wrapper import frst_optimizer, FRSTOptimizer
from cyopt.frst._result import FRSTResult

# Apply monkey patches on import
patch_polytope()
```

### Pattern 5: Maximize vs Minimize Convention

**What:** The old code maximizes targets; the new optimizers minimize.

**How to handle:** The wrapper negates the target value internally. Users write `target(cy) -> float` where higher is better (matching the old convention). The wrapper converts to minimization for the generic optimizer.

This is a critical interface decision -- document it clearly in the factory function's docstring.

### Anti-Patterns to Avoid

- **Reimplementing LP solvers:** Use `triangfaces_to_frst()` -- it handles the entire cone interior point pipeline internally.
- **Using `triangface_ineqs()`:** The old code needed raw inequalities to build the secondary cone manually. With `triangfaces_to_frst()`, we only need `face_triangs()` for the face Triangulation objects.
- **Storing `_face_simps` as in old code:** The old code stored simplices as nested lists for reverse matching. Use `frozenset` of sorted tuples for O(1) comparison.
- **Importing from cornell-dev/lib:** Everything needed is in the CYTools public API.
- **Direct `Triangulation()` construction:** The CYTools pitfalls docs warn against direct construction. Use `Polytope.triangulate()` or `triangfaces_to_frst()`.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| DNA to height vector to FRST | Manual secondary cone construction + LP solve | `Polytope.triangfaces_to_frst(triangs)` | CYTools handles cone construction, backend selection, height extraction, and Triangulation construction. The old code's `dna_to_reduced_heights` + `Triangulation()` pipeline is fully replaced. |
| 2-face triangulation enumeration | Custom face enumeration | `Polytope.face_triangs()` | Handles face extraction, triangulation generation, various methods (grow2d, fair, fast) |
| Triangulation restriction to faces | Manual simplex intersection | `Triangulation.restrict(restrict_dim=2)` | Correct handling of label sets, dimension checking |
| LRU cache for DNA->FRST | `functools.lru_cache` with custom wrapper | Use `triangfaces_to_frst()` directly (no caching needed at this level) | The old code cached `dna_to_reduced_heights` results. The optimizer's `EvaluationCache` already caches at the fitness function level, avoiding redundant FRST constructions for the same DNA. |

**Key insight:** The old code used cornell-dev/lib utilities (`LIL_stack`, `hypers_to_cone`) because CYTools lacked a direct face-triangulations-to-FRST pathway. That pathway now exists as `triangfaces_to_frst()`, eliminating all library porting needs.

## Common Pitfalls

### Pitfall 1: Non-Solid Cones (DNA with no valid FRST)

**What goes wrong:** Not every combination of 2-face triangulation choices corresponds to a valid FRST. Some DNA values produce non-solid secondary cones with no interior point.
**Why it happens:** The cone of permissible heights for incompatible face triangulation choices can be empty or lower-dimensional.
**How to avoid:** `triangfaces_to_frst()` returns `None` when the cone has no interior point. The fitness function MUST handle `None` returns by assigning a penalty value (e.g., `float('inf')` for minimization).
**Warning signs:** Optimizer converges to the penalty value; all evaluated DNA produce `None` triangulations.

### Pitfall 2: Maximize vs Minimize Confusion

**What goes wrong:** Old code maximizes targets; new optimizers minimize. Forgetting to negate produces an optimizer that finds the worst solution.
**Why it happens:** Different conventions between the old `TriangOptimizer` (maximization) and the new `DiscreteOptimizer` (minimization).
**How to avoid:** The factory function should handle the negation internally. Document the convention clearly: users write targets where higher is better, the wrapper negates.
**Warning signs:** Optimizer finds DNA with the lowest target value instead of highest.

### Pitfall 3: Inclusive vs Exclusive Bounds

**What goes wrong:** Old code uses `rng.integers(0, N)` (exclusive upper bound) for N triangulations per face. New code uses inclusive bounds `(0, N-1)`.
**Why it happens:** NumPy `rng.integers(low, high)` has exclusive upper bound. The base class `_random_dna` uses `rng.integers(lo, hi+1)` to make bounds inclusive.
**How to avoid:** Bounds from `prep_for_optimizers` must be `(0, len(face_triangs) - 1)` -- inclusive on both ends, matching the `DiscreteOptimizer` convention.
**Warning signs:** IndexError when accessing `face_triangs[dna_component]`.

### Pitfall 4: face_triangs() is Expensive

**What goes wrong:** Calling `face_triangs()` multiple times recomputes all 2-face triangulations from scratch.
**Why it happens:** `face_triangs()` is a regular method, not a cached property.
**How to avoid:** `prep_for_optimizers()` must call it once and store the result. The prep guard (`_cyopt_prepped` flag) prevents redundant calls.
**Warning signs:** Slow polytope setup; multiple "Generating face triangulations" messages.

### Pitfall 5: Triangulation Simplex Comparison

**What goes wrong:** Comparing simplices from `restrict()` (sorted int lists) with simplices from `face_triangs()` (Triangulation objects) using different formats.
**Why it happens:** `restrict(as_poly=False)` returns `list[list[int]]` sorted. `Triangulation.simplices()` returns `np.ndarray`. Different representations of the same simplices.
**How to avoid:** Normalize both to `frozenset[tuple[int, ...]]` for comparison. Precompute the normalized form during `prep_for_optimizers()`.
**Warning signs:** `triang_to_dna` fails to find matching face triangulations; raises ValueError or returns wrong index.

### Pitfall 6: Target Function Returning Tuples

**What goes wrong:** Old code convention: `target(dna) -> (feature, ancillary_data)`. New optimizer expects `DNA -> float`.
**Why it happens:** The wrapper must bridge these conventions.
**How to avoid:** The fitness bridge function should handle both `target(obj) -> float` and `target(obj) -> (float, ancillary)` return types. Store ancillary data in a side channel.
**Warning signs:** TypeError when optimizer tries to compare tuple with float.

### Pitfall 7: CYTools Not Available at Import Time

**What goes wrong:** `import cyopt.frst` crashes if CYTools is not installed.
**Why it happens:** No import guard.
**How to avoid:** The `cyopt/frst/__init__.py` must catch `ImportError` and raise a helpful message. The top-level `cyopt/__init__.py` must NOT import from `cyopt.frst`.
**Warning signs:** ImportError when users install cyopt without CYTools.

## Code Examples

### DNA-to-FRST Roundtrip (Verified)

```python
# Source: live-tested against CYTools in conda env [VERIFIED]
from cytools import fetch_polytopes

p = fetch_polytopes(h11=7, limit=1)[0]
ft = p.face_triangs()

# Identify interesting faces
counts = [len(f) for f in ft]
interesting = [(i, c) for i, c in enumerate(counts) if c > 1]
bounds = tuple((0, c - 1) for _, c in interesting)

# Encode: DNA -> face triangulation list -> FRST
dna = (1, 2)
triangs = [None] * len(ft)
for idx, (face_idx, _) in enumerate(interesting):
    triangs[face_idx] = ft[face_idx][dna[idx]]
frst = p.triangfaces_to_frst(triangs)

# Decode: FRST -> restrict -> match simplices -> DNA
restrictions = frst.restrict()  # restrict_dim=2 by default
recovered = []
for idx, (face_idx, _) in enumerate(interesting):
    restriction_set = frozenset(tuple(sorted(s)) for s in restrictions[face_idx])
    for j, face_t in enumerate(ft[face_idx]):
        ft_set = frozenset(tuple(sorted(s)) for s in face_t.simplices())
        if ft_set == restriction_set:
            recovered.append(j)
            break
assert tuple(recovered) == dna  # passes
```

### Simplex Normalization for Comparison

```python
# Source: derived from CYTools API behavior [VERIFIED]
def _normalize_simplices(simplices) -> frozenset[tuple[int, ...]]:
    """Normalize simplices to a comparable form.

    Works with both np.ndarray (from Triangulation.simplices())
    and list[list[int]] (from Triangulation.restrict()).
    """
    return frozenset(tuple(sorted(int(v) for v in s)) for s in simplices)
```

### Import Guard Pattern

```python
# cyopt/frst/__init__.py
# Source: pattern from CLAUDE.md [CITED: CLAUDE.md]
try:
    from cytools import Polytope  # noqa: F401
    HAS_CYTOOLS = True
except ImportError:
    HAS_CYTOOLS = False

if not HAS_CYTOOLS:
    raise ImportError(
        "cyopt.frst requires CYTools. Install with: pip install cyopt[frst]\n"
        "Or activate the cytools conda environment."
    )
```

### Test Skip Pattern

```python
# tests/test_frst/conftest.py
# Source: pattern from CLAUDE.md [CITED: CLAUDE.md]
import pytest

try:
    from cytools import Polytope
    HAS_CYTOOLS = True
except ImportError:
    HAS_CYTOOLS = False

requires_cytools = pytest.mark.skipif(
    not HAS_CYTOOLS,
    reason="CYTools not available"
)
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Manual secondary cone from `LIL_stack` + `hypers_to_cone` | `Polytope.triangfaces_to_frst()` | Available in current CYTools | Eliminates all cornell-dev/lib porting; single clean API call |
| Direct `Triangulation()` constructor with heights | `Polytope.triangulate(heights=...)` or `triangfaces_to_frst()` | CYTools docs recommend against direct construction | Avoids pitfalls with point reordering |
| `scipy.optimize._basinhopping` private imports | Custom implementations (Phase 2) | Phase 2 | No private API access |

**Deprecated/outdated:**
- `lib.geom.secondary_cone` module: replaced by CYTools' built-in `triangfaces_to_frst`/`triangfaces_to_frt`
- `lib.util.matrix.LIL_stack`: only needed for manual cone construction, now handled internally by CYTools
- Direct `Triangulation()` construction: use factory methods instead [CITED: CYTools pitfalls.md]

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | `face_triangs()` results are stable across calls (same polytope always produces same face triangulations in same order) | Architecture Patterns | If order is non-deterministic, `triang_to_dna` roundtrip would fail. Mitigated by precomputing once in `prep_for_optimizers`. |
| A2 | `triangfaces_to_frst()` handles all face counts correctly (passing `None` for uninteresting faces) | Architecture Patterns | If `None` entries cause errors, would need to pass actual (only) triangulations for boring faces. Low risk -- API explicitly documents `None` support. |
| A3 | Users' target functions will follow `target(cy) -> float` or `target(cy) -> (float, ancillary)` convention | Architecture Patterns | If targets return other types, fitness bridge fails. Low risk -- clearly documented interface. |

**If this table is empty:** N/A -- 3 assumptions listed above.

## Open Questions

1. **Ancillary Data Storage Mechanism (D-06)**
   - What we know: Old code stored `(feature, ancillary_data)` tuples in the cache, keyed by DNA. The new `EvaluationCache` stores only `float` values.
   - What's unclear: Best mechanism -- separate dict in wrapper, or extend the callback system.
   - Recommendation: Use a simple `dict[DNA, Any]` stored on the `FRSTOptimizer` wrapper, populated by the fitness bridge function. Accessible via `wrapper.ancillary_data`. This is the simplest approach that preserves the old code's behavior without modifying the generic optimizer infrastructure.

2. **Maximize vs Minimize Convention Documentation**
   - What we know: Old code maximizes; new code minimizes. Wrapper must negate.
   - What's unclear: Whether `FRSTResult.best_value` should report the original (un-negated, maximized) value or the negated (minimized) value.
   - Recommendation: Report the original (un-negated) value in `FRSTResult` since that's what the user's target function returned. The negation is an internal implementation detail.

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest 9.0.2 |
| Config file | `pyproject.toml` [tool.pytest.ini_options] |
| Quick run command | `conda run -n cytools pytest tests/test_frst/ -x -q` |
| Full suite command | `conda run -n cytools pytest tests/ -x -q` |

### Phase Requirements -> Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| FRST-01 | `prep_for_optimizers()` precomputes face data, sets bounds, is idempotent | unit | `conda run -n cytools pytest tests/test_frst/test_encoding.py::test_prep_for_optimizers -x` | Wave 0 |
| FRST-01 | `prep_for_optimizers()` raises on non-reflexive | unit | `conda run -n cytools pytest tests/test_frst/test_encoding.py::test_prep_rejects_non_reflexive -x` | Wave 0 |
| FRST-02 | `dna_to_frst` produces valid Triangulation | unit | `conda run -n cytools pytest tests/test_frst/test_encoding.py::test_dna_to_frst -x` | Wave 0 |
| FRST-02 | `triang_to_dna` -> `dna_to_frst` roundtrip | unit | `conda run -n cytools pytest tests/test_frst/test_encoding.py::test_roundtrip -x` | Wave 0 |
| FRST-02 | `dna_to_cy` returns CalabiYau | unit | `conda run -n cytools pytest tests/test_frst/test_encoding.py::test_dna_to_cy -x` | Wave 0 |
| FRST-02 | `cy_to_dna` roundtrip | unit | `conda run -n cytools pytest tests/test_frst/test_encoding.py::test_cy_roundtrip -x` | Wave 0 |
| FRST-02 | Invalid DNA (non-solid cone) returns None | unit | `conda run -n cytools pytest tests/test_frst/test_encoding.py::test_invalid_dna -x` | Wave 0 |
| FRST-03 | `frst_optimizer()` factory returns working wrapper | integration | `conda run -n cytools pytest tests/test_frst/test_wrapper.py::test_frst_optimizer_factory -x` | Wave 0 |
| FRST-03 | Wrapper `run()` returns FRSTResult with decoded fields | integration | `conda run -n cytools pytest tests/test_frst/test_wrapper.py::test_frst_result -x` | Wave 0 |
| FRST-03 | Each optimizer class works through wrapper | integration | `conda run -n cytools pytest tests/test_frst/test_wrapper.py::test_all_optimizers -x` | Wave 0 |
| FRST-03 | Target mode='triangulation' skips CY construction | integration | `conda run -n cytools pytest tests/test_frst/test_wrapper.py::test_target_mode_triangulation -x` | Wave 0 |
| FRST-04 | Tests pass with current CYTools | smoke | `conda run -n cytools pytest tests/test_frst/ -x` | Wave 0 |

### Sampling Rate

- **Per task commit:** `conda run -n cytools pytest tests/test_frst/ -x -q`
- **Per wave merge:** `conda run -n cytools pytest tests/ -x -q`
- **Phase gate:** Full suite green before `/gsd-verify-work`

### Wave 0 Gaps

- [ ] `tests/test_frst/__init__.py` -- package marker
- [ ] `tests/test_frst/conftest.py` -- `requires_cytools` marker, shared polytope fixtures
- [ ] `tests/test_frst/test_encoding.py` -- covers FRST-01, FRST-02
- [ ] `tests/test_frst/test_wrapper.py` -- covers FRST-03, FRST-04

## Sources

### Primary (HIGH confidence)

- CYTools conda env, live API inspection -- method signatures, return types, roundtrip testing [VERIFIED]
- `/Users/elijahsheridan/Downloads/triang_optimizer.py` -- old code reference for encoding logic [VERIFIED: direct file read]
- `/Users/elijahsheridan/Research/string/cytools_code/knowledge-base/software/CYTools/pitfalls.md` -- CYTools pitfalls [VERIFIED: direct file read]
- CYTools source code via `inspect.getsource()` -- `triangfaces_to_frst`, `triangfaces_to_frt`, `face_triangs`, `restrict` [VERIFIED]
- `cyopt/base.py`, `cyopt/_types.py`, `cyopt/_cache.py` -- current codebase [VERIFIED: direct file read]

### Secondary (MEDIUM confidence)

- None

### Tertiary (LOW confidence)

- None

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- all CYTools methods verified in current conda env via live testing
- Architecture: HIGH -- DNA roundtrip verified end-to-end; old code fully analyzed; CYTools API covers all needs
- Pitfalls: HIGH -- derived from old code analysis, CYTools pitfalls docs, and live API testing

**Research date:** 2026-04-11
**Valid until:** 2026-05-11 (CYTools API is stable; no upcoming breaking changes known)

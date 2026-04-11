# Domain Pitfalls

**Domain:** Discrete optimization library with FRST specialization
**Researched:** 2026-04-11

## Critical Pitfalls

Mistakes that cause rewrites or major issues.

### Pitfall 1: Accessing SciPy Private Internals
**What goes wrong:** The old code imports `scipy.optimize._basinhopping` and `scipy.optimize._differentialevolution` to subclass internal classes. These private modules change between SciPy versions, breaking the code silently or with cryptic errors.
**Why it happens:** SciPy's public API for basin hopping doesn't support discrete spaces directly, so the old code reached into internals to customize stepping behavior.
**Consequences:** Code breaks on SciPy upgrades. Already broken in current env (function signatures have changed).
**Prevention:** Reimplement basin hopping and SA for discrete spaces (they're simple algorithms). Use `scipy.optimize.differential_evolution` with `integrality` parameter for DE (public API, stable since SciPy 1.9).
**Detection:** Any import from `scipy.optimize._*` (underscore-prefixed modules).

### Pitfall 2: CYTools API Drift
**What goes wrong:** CYTools has renamed/moved functions since the old code was written. Methods like `triangface_ineqs`, `points(which=...)`, and triangulation constructors may have different signatures.
**Why it happens:** CYTools is actively developed; API stability is not guaranteed between major versions.
**Consequences:** FRST wrapper layer fails at runtime with `AttributeError` or wrong results.
**Prevention:** (a) Write integration tests that exercise every CYTools API call. (b) Check the knowledge base at `/Users/elijahsheridan/Research/string/cytools_code/knowledge-base/software/CYTools/` before implementing. (c) Pin to a known-working CYTools version in docs. (d) Isolate all CYTools calls to `cyopt/frst/` so breakage is contained.
**Detection:** Integration tests that run with CYTools installed.

### Pitfall 3: Legacy NumPy Random API
**What goes wrong:** Using `numpy.random.RandomState` (legacy) or bare `numpy.random.seed()` instead of `numpy.random.Generator`. The old code uses `scipy._lib._util.check_random_state()` which returns a `RandomState`.
**Why it happens:** Old code predates the new Generator API; tutorials still show legacy patterns.
**Consequences:** Non-reproducible results across NumPy versions, deprecated warnings, eventually breaking when NumPy drops legacy support.
**Prevention:** Use `numpy.random.default_rng(seed)` everywhere. Accept `int | np.random.Generator | None` for seed parameters.
**Detection:** Grep for `RandomState`, `np.random.seed`, `check_random_state`.

### Pitfall 4: Monolithic File Design
**What goes wrong:** All optimizers in one file (the old `triang_optimizer.py` pattern). Testing any optimizer requires loading CYTools. Adding an optimizer requires understanding the entire file.
**Why it happens:** Organic growth from a research script.
**Consequences:** Untestable core logic, import failures cascade, impossible to use generic optimizers without CYTools.
**Prevention:** One file per optimizer, strict layer separation, imports only flow downward (frst -> core, never core -> frst).
**Detection:** Any core optimizer file importing from `cyopt.frst` or importing `cytools`.

## Moderate Pitfalls

### Pitfall 5: Fitness Function Evaluation Counting
**What goes wrong:** Incorrect `nfev` (number of function evaluations) count, especially with parallel evaluation or caching.
**Prevention:** Wrap the user's fitness function in a counter. Increment atomically if parallel. Document whether cached hits count.

### Pitfall 6: Bounds Off-by-One
**What goes wrong:** DNA encoding uses 0-indexed positions where the number of triangulations for face `i` is `n_i`, so valid indices are `[0, n_i - 1]`. Off-by-one in bounds causes invalid triangulations or missed search space.
**Prevention:** Clearly document whether bounds are inclusive or exclusive. Use convention: `bounds[i] = (0, n_triangulations_i - 1)`, both inclusive. Test boundary values explicitly.

### Pitfall 7: Deep Copy vs. Shallow Copy of Populations
**What goes wrong:** GA population arrays shared between generations via shallow copy. Mutation of one generation corrupts the previous.
**Prevention:** Use `np.copy()` or work with immutable tuples. The old code uses `copy.deepcopy` in places, which is slow for numpy arrays. Prefer `array.copy()`.

### Pitfall 8: Monkey-Patching Gone Wrong
**What goes wrong:** Monkey-patching `Polytope` with methods that have name collisions with future CYTools methods, or patching in ways that break pickling/serialization.
**Prevention:** Prefix all monkey-patched attributes with `_cyopt_` or similar namespace. Document all patches. Test that patched methods don't shadow existing CYTools methods.

## Minor Pitfalls

### Pitfall 9: tqdm in Library Code
**What goes wrong:** Progress bars in library code pollute output when users have their own logging/progress reporting.
**Prevention:** Make tqdm optional via a `verbose` or `progress` parameter. Default to off for programmatic use, on for interactive use.

### Pitfall 10: Hyperparameter Defaults That Don't Scale
**What goes wrong:** Default population size of 100 works for small problems, catastrophic for large ones.
**Prevention:** Document scaling guidance. Consider defaults that scale with problem size (e.g., `population_size = max(50, 4 * n_dimensions)`).

### Pitfall 11: No Early Stopping
**What goes wrong:** Optimizers run for fixed iterations even when converged, wasting hours on large CY computations.
**Prevention:** Support convergence criteria: no improvement for N generations, fitness threshold reached, time limit.

## Phase-Specific Warnings

| Phase Topic | Likely Pitfall | Mitigation |
|-------------|---------------|------------|
| Base class + GA | Getting the ABC interface wrong and having to refactor all optimizers | Implement 2-3 optimizers before finalizing the ABC |
| SciPy integration (DE) | Attempting to use `integrality` with incompatible bounds format | Test with SciPy 1.17.0 specifically; bounds format is `[(low, high), ...]` |
| FRST wrapper layer | CYTools API has changed since old code | Check knowledge base first; write integration tests early; expect trial-and-error |
| DNA encoding | Off-by-one in face indexing / triangulation counting | Unit test encode/decode roundtrip with known polytopes |
| Documentation | myst-nb execution mode hanging on CYTools notebooks | Set `nb_execution_mode = "off"` (as dbrane-tools does); pre-execute notebooks |
| Testing | FRST tests fail in CI without CYTools | Use pytest markers + skip decorators; separate test suites |

## Sources

- Old code at `/Users/elijahsheridan/Downloads/triang_optimizer.py` - direct inspection of anti-patterns
- SciPy 1.17.0 `differential_evolution` docs confirming `integrality` parameter - HIGH confidence
- NumPy random Generator migration guide (training data) - MEDIUM confidence
- CYTools API knowledge base at `/Users/elijahsheridan/Research/string/cytools_code/knowledge-base/software/CYTools/` - HIGH confidence

# Project Research Summary

**Project:** cyopt
**Domain:** Discrete optimization library (generic integer-tuple optimizers + CYTools FRST wrappers)
**Researched:** 2026-04-11
**Confidence:** HIGH

## Executive Summary

cyopt is a two-layer discrete optimization library: a generic core layer that operates on bounded integer-tuple search spaces (no domain dependencies), and an optional FRST wrapper layer that connects these optimizers to CYTools for fine, regular, star triangulation optimization on reflexive polytopes. The expert approach for this kind of library is well-established -- an abstract optimizer base class with a consistent interface, one-file-per-optimizer implementations, strategy patterns for composable components (GA operators, neighbor functions), and strict separation between the domain-agnostic optimization logic and the domain-specific encoding/decoding layer.

The recommended approach is to build the generic core first (base class, Result dataclass, 8 optimizer implementations using only NumPy/SciPy/tqdm), then layer the FRST wrapper on top. The old codebase (`triang_optimizer.py`) provides a working reference but has significant technical debt: tight CYTools coupling, SciPy private API usage, multiple copy-paste bugs, invalid type hints, and a monolithic 1500-line file. The new codebase should port the algorithms while discarding the structural anti-patterns. SciPy's `differential_evolution` with the `integrality` parameter (public API since 1.9) replaces the old private-API hack for DE; basin hopping and simulated annealing should be reimplemented directly for discrete spaces rather than wrapping continuous optimizers.

The primary risks are (1) CYTools API drift -- the old code's API calls may not match the current CYTools version, requiring trial-and-error during FRST wrapper implementation, and (2) getting the base class interface wrong before implementing enough optimizers to validate it. Both are mitigated by the two-layer architecture: core optimizers are independently testable without CYTools, and implementing 2-3 optimizers before finalizing the ABC ensures the interface is battle-tested.

## Key Findings

### Recommended Stack

The stack is lightweight and well-established. Python 3.10+ with NumPy, SciPy, and tqdm as core dependencies. Hatchling for PEP 621 packaging, ruff for linting/formatting, pytest for testing. CYTools is an optional dependency isolated to `cyopt.frst`. All recommended versions are already installed in the cytools conda environment.

**Core technologies:**
- **Python 3.10+**: Runtime -- match statements, modern typing syntax (`X | Y`)
- **NumPy >=1.24**: Array operations and modern `Generator` random API
- **SciPy >=1.10**: `differential_evolution` with `integrality` parameter (public API for discrete DE)
- **Hatchling**: Build backend -- PEP 621 native, zero-config, standard for new scientific Python packages
- **ruff**: Linting + formatting -- replaces black/flake8/isort in one tool
- **pytest + hypothesis**: Testing -- property-based testing is valuable for optimizer invariants
- **Sphinx + sphinx-book-theme + myst-nb**: Documentation -- matches dbrane-tools conventions

### Expected Features

**Must have (table stakes):**
- Generic `DiscreteOptimizer` ABC with bounds, caching, seeding, best-so-far tracking
- Consistent `optimize()` method returning a structured `OptimizeResult` dataclass
- All 8 optimizer implementations (GA, RandomSample, GreedyWalk, BestFirstSearch, BasinHopping, DE, MCMC, SA)
- Per-position bounded integer search space as the fundamental abstraction
- Evaluation caching (OrderedDict with optional max size)
- Reproducible seeding via `numpy.random.default_rng(seed)`
- FRST wrapper layer with DNA encoding/decoding and Polytope monkey-patching
- Hyperparameter management with validation
- Progress reporting via tqdm (opt-in, not default)
- Type hints throughout

**Should have (differentiators):**
- Ask-tell interface for external parallelism and custom scheduling
- Callback/hook system (`on_iteration` hook)
- Structured `OptimizeResult` with history, nfev, wall time
- Configurable neighbor function abstraction (Hamming default, user-provided)
- Composable GA operators (standalone strategy functions)
- Serialization/checkpoint/resume support
- Proper `__copy__`/`__deepcopy__`

**Defer (v2+):**
- Multi-objective optimization (use pymoo)
- Automatic hyperparameter tuning (use Optuna)
- Built-in parallelism/multiprocessing (ask-tell enables external parallelism)
- GUI/web dashboard
- Database-backed storage

### Architecture Approach

Two-layer design with a strict dependency boundary. The core layer (`cyopt.*`) depends only on NumPy/SciPy/tqdm and provides generic discrete optimization. The FRST layer (`cyopt.frst.*`) depends on the core layer plus CYTools and provides domain-specific wrappers. One file per optimizer, all inheriting from a common ABC in `base.py`. Flat package layout (matching dbrane-tools conventions).

**Major components:**
1. **`cyopt.base`** -- ABC (`DiscreteOptimizer`), `OptimizeResult` dataclass, type definitions, shared protocols
2. **`cyopt.{ga,random_sample,greedy,best_first,basin_hopping,diff_evolution,mcmc,simulated_annealing}`** -- One optimizer per file, each depends only on `base`
3. **`cyopt.frst`** -- CYTools integration: `polytope_ext.py` (monkey-patching), `dna.py` (encoding/decoding), `wrappers.py` (FRST-specific optimizer factories)

### Critical Pitfalls

1. **SciPy private API usage** -- The old code imports from `scipy.optimize._basinhopping` and `scipy.optimize._differentialevolution`. These are already broken. Reimplement basin hopping and SA as discrete algorithms; use `differential_evolution` public API with `integrality` for DE.
2. **CYTools API drift** -- Method signatures and constructors may have changed since the old code. Isolate all CYTools calls to `cyopt/frst/`, consult the knowledge base, and write integration tests for every CYTools API call.
3. **Legacy NumPy random API** -- Use `numpy.random.default_rng(seed)` everywhere. Never use `RandomState`, `np.random.seed()`, or `check_random_state()`.
4. **Monolithic file design** -- One file per optimizer. Core files must never import from `cyopt.frst` or `cytools`. Test at import time by importing core without CYTools.
5. **Bounds off-by-one** -- Clearly document inclusive bounds convention. Unit test encode/decode roundtrip with known polytopes at boundary values.

## Implications for Roadmap

Based on research, suggested phase structure:

### Phase 1: Project Scaffold + Base Class + First Optimizers
**Rationale:** The ABC must be validated against real optimizer implementations before being finalized. Implement 2-3 optimizers (RandomSample, GA, GreedyWalk) alongside the base to prove the interface works.
**Delivers:** Package structure (pyproject.toml, flat layout), `DiscreteOptimizer` ABC, `OptimizeResult` dataclass, evaluation caching, seeding, 3 working optimizers, initial test suite.
**Addresses:** Abstract base class, per-position bounded search space, evaluation caching, reproducible seeding, best-so-far tracking, hyperparameter management, Result object, progress reporting.
**Avoids:** Monolithic file design (one file per optimizer from day one), mutable default hyperparameters.

### Phase 2: Remaining Core Optimizers
**Rationale:** With the ABC validated, implement the remaining 5 optimizers. BestFirstSearch, MCMC, and SA are straightforward custom implementations. BasinHopping is a custom discrete implementation. DE wraps SciPy's public API.
**Delivers:** All 8 optimizers working on generic integer-tuple spaces, neighbor function abstraction, full test coverage for core layer.
**Addresses:** All 8 optimizer implementations, neighbor function abstraction, composable GA operators.
**Avoids:** SciPy private API usage (DE uses `integrality` parameter, BH is custom), legacy NumPy random API.

### Phase 3: FRST Wrapper Layer
**Rationale:** Requires core optimizers to be stable. This is the domain-specific integration that makes the library valuable for string phenomenology. Expect trial-and-error with CYTools API.
**Delivers:** DNA encoding/decoding, Polytope monkey-patching, FRST-specific optimizer factories, integration tests.
**Addresses:** FRST wrapper layer, DNA encoding, monkey-patching.
**Avoids:** CYTools API drift (consult knowledge base, write integration tests), bounds off-by-one (roundtrip tests), monkey-patch name collisions (namespace prefix).

### Phase 4: Differentiator Features
**Rationale:** Core functionality is complete; add features that improve developer experience and enable advanced use cases.
**Delivers:** Ask-tell interface, callback system, serialization/checkpoint/resume, early stopping.
**Addresses:** Ask-tell interface, callback/hook system, serialization, convergence criteria.
**Avoids:** Over-engineering (keep callbacks simple -- single `on_iteration` hook is enough).

### Phase 5: Documentation + Polish
**Rationale:** Package is feature-complete; document for users. Sphinx with sphinx-book-theme matching dbrane-tools conventions. Jupyter notebook tutorials.
**Delivers:** API reference (autodoc), tutorials (basic + FRST), installation guide, hyperparameter guidance.
**Addresses:** Documentation stack (Sphinx, myst-nb, sphinx-book-theme).
**Avoids:** myst-nb execution hanging on CYTools notebooks (use `nb_execution_mode = "off"`, pre-execute).

### Phase Ordering Rationale

- Phases 1-2 must precede Phase 3 because the FRST layer depends on stable core optimizers.
- Phase 1 implements 3 diverse optimizers (random, evolutionary, local search) to validate the ABC before committing all 8 implementations to it.
- Phase 3 is isolated because CYTools integration is the highest-uncertainty work and should not block core optimizer development.
- Phase 4 comes after core + FRST because differentiator features (ask-tell, callbacks) affect the interface and are easier to design once the main usage patterns are proven.
- Phase 5 is last because documenting a moving target wastes effort; docstrings should be written throughout, but formal docs come after the API stabilizes.

### Research Flags

Phases likely needing deeper research during planning:
- **Phase 3 (FRST Wrapper):** CYTools API has changed since the old code. Every API call needs verification against the current version. Consult knowledge base at `/Users/elijahsheridan/Research/string/cytools_code/knowledge-base/software/CYTools/`. Expect iteration.
- **Phase 2 (BasinHopping, DE):** Custom discrete basin hopping implementation needs design thought. SciPy DE `integrality` parameter needs testing with the specific bounds format.

Phases with standard patterns (skip research-phase):
- **Phase 1 (Scaffold + Base + First Optimizers):** Well-established patterns -- ABC, dataclass Result, GA, random sampling. All documented in DEAP/pymoo/nevergrad.
- **Phase 4 (Differentiator Features):** Ask-tell and callbacks are well-documented patterns from nevergrad and pymoo respectively.
- **Phase 5 (Documentation):** Sphinx + sphinx-book-theme + myst-nb is the dbrane-tools pattern, fully documented.

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | All versions verified in conda env via `pip show`. SciPy `integrality` confirmed in docs. Hatchling/ruff are established standards. |
| Features | HIGH | Feature landscape derived from direct inspection of old code + comparison with DEAP, pymoo, nevergrad. Clear MVP vs. differentiator distinction. |
| Architecture | HIGH | Two-layer pattern is straightforward. Old code provides working reference for algorithms. One-file-per-optimizer is standard. |
| Pitfalls | HIGH | Pitfalls identified from direct inspection of old code bugs. SciPy private API breakage is confirmed. CYTools drift is the main uncertainty. |

**Overall confidence:** HIGH

### Gaps to Address

- **CYTools current API surface:** The exact current signatures for triangulation construction, `points()`, `triangface_ineqs()`, and related methods need verification against the installed version. Consult knowledge base during Phase 3 planning.
- **DE `integrality` bounds format:** Need to verify the exact format SciPy expects for integer bounds (`[(low, high), ...]` vs. separate arrays) with a quick prototype during Phase 2.
- **Large polytope scalability:** For h11 > 100, DNA length exceeds 1000 positions. GA population management at this scale may need memory optimization. Defer until profiling reveals actual bottlenecks.
- **Ask-tell interaction with caching:** When users evaluate externally (ask-tell), the internal cache may miss evaluations or double-count. Design the cache interaction carefully in Phase 4.

## Sources

### Primary (HIGH confidence)
- SciPy 1.17.0 documentation -- `differential_evolution` `integrality` parameter, `basinhopping`, `dual_annealing`
- Old code at `/Users/elijahsheridan/Downloads/triang_optimizer.py` -- algorithm reference and anti-pattern identification
- dbrane-tools project -- package structure and documentation conventions
- Installed package versions in cytools conda env -- verified via `pip show`
- Python Packaging User Guide -- pyproject.toml, PEP 621

### Secondary (MEDIUM confidence)
- DEAP, pymoo, nevergrad documentation -- feature landscape, interface patterns (ask-tell, callbacks, Result)
- Optuna documentation -- callback and study patterns (referenced but not adopted)
- NumPy random Generator migration patterns

### Tertiary (LOW confidence)
- Large polytope scalability estimates -- inferred from h11 scaling, not benchmarked

---
*Research completed: 2026-04-11*
*Ready for roadmap: yes*

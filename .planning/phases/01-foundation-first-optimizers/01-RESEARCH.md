# Phase 1: Foundation + First Optimizers - Research

**Researched:** 2026-04-11
**Domain:** Python package scaffolding, discrete optimization algorithms (GA, RandomSample, GreedyWalk)
**Confidence:** HIGH

## Summary

Phase 1 delivers a pip-installable `cyopt` package with an abstract `DiscreteOptimizer` base class, structured `Result` dataclass, evaluation caching, reproducible seeding, tqdm progress reporting, and three concrete optimizers: `GA`, `RandomSample`, and `GreedyWalk`. All algorithms exist in the old `triang_optimizer.py` (1762 lines, tightly coupled to CYTools) and must be extracted, decoupled, and rewritten with clean interfaces on generic bounded integer-tuple search spaces.

The old code provides a solid reference for algorithm logic: the base class pattern (ABC with `_sample` as the abstract method, `run` loop with tqdm, OrderedDict cache, `np.random.default_rng` seeding, best-so-far tracking) maps directly to the new design. The GA implementation includes composable selection (roulette wheel, tournament, ranked variants), crossover (n-point, uniform), mutation (random k-point), and survival (elitist) operators. GreedyWalk uses Hamming neighbors with expanding step sizes. These algorithms are straightforward to port once decoupled from CYTools Polytope references.

**Primary recommendation:** Port algorithm logic from `triang_optimizer.py` into clean, decoupled modules following the flat-layout convention from dbrane-tools. Use hatchling for build backend, modern `numpy.random.Generator` API throughout, and `dataclasses.dataclass` for the `Result` type.

<user_constraints>

## User Constraints (from CONTEXT.md)

### Locked Decisions
- **D-01:** Fitness function passed as constructor arg (`fitness_fn=f`), locked for the optimizer's lifetime
- **D-02:** Optimizers minimize by default (standard scipy convention). Users negate to maximize.
- **D-03:** `Result` always contains `history` (list of best-so-far value per iteration). When `record_history=True` is passed to the constructor, `Result` also contains `full_history` (list of per-iteration dicts with keys like best, mean, std, etc.)
- **D-04:** `record_history=True` is a constructor flag, default `False`
- **D-05:** GA operators specified via hybrid interface: strings for builtins (`selection='tournament'`), callables for custom operators (`selection=my_custom_fn`)
- **D-06:** Builtin operator parameters configured via nested dicts: `selection={'method': 'tournament', 'k': 3}`, `crossover={'method': 'npoint', 'n': 2}`
- **D-07:** Single objective only in Phase 1. Multi-objective is v2 scope (ADV-02).
- **D-08:** Flat layout -- `cyopt/` at repo root (matches CYTools and dbrane-tools conventions)
- **D-09:** One file per optimizer: `cyopt/optimizers/ga.py`, `random_sample.py`, `greedy_walk.py`. `__init__.py` re-exports all optimizer classes.
- **D-10:** Same algorithms as old `triang_optimizer.py`, clean new API. Preserve core logic but rewrite with clean interfaces, modern `numpy.random.Generator`, and zero CYTools coupling.
- **D-11:** New concise class names: `GA`, `RandomSample`, `GreedyWalk`
- **D-12:** No scipy dependency for Phase 1 optimizers. All three are custom implementations.

### Claude's Discretion
- Internal helper functions and private method organization
- Exact fields in `full_history` per-iteration dicts (beyond best/mean/std)
- Test structure and test helper utilities
- Hyperparameter validation specifics (what errors to raise, etc.)

### Deferred Ideas (OUT OF SCOPE)
None -- discussion stayed within phase scope

</user_constraints>

<phase_requirements>

## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| CORE-01 | Abstract `DiscreteOptimizer` base class operating on bounded integer-tuple search spaces | Old code ABC pattern with `_sample` abstract method maps directly; decouple from Polytope |
| CORE-02 | `run(n_iterations)` method returning structured `Result` dataclass | Old `run()` loop logic + new `Result` dataclass with fields per D-03 |
| CORE-03 | Evaluation caching via OrderedDict with optional max size | Old code uses `collections.OrderedDict` cache -- port directly, add `maxsize` parameter with LRU eviction |
| CORE-04 | Best-so-far tracking (best DNA + best feature value) | Old code tracks `_dna_best`, `_feature_best` -- port with minimization convention (D-02) |
| CORE-05 | Reproducible seeding with per-optimizer `np.random.default_rng` | Old code already uses `np.random.default_rng` -- port directly |
| CORE-06 | Hyperparameter management with validated dict-based interface | Old code uses `_hyperparams` dict -- add validation layer per D-06 |
| CORE-07 | Progress reporting via tqdm integration | Old code uses tqdm in `run()` -- port with `progress=True/False` flag |
| CORE-10 | Type hints throughout the codebase | New code from scratch; use modern Python 3.10+ type hint syntax |
| OPT-01 | GA with composable operators | Old GA class has full operator implementations; port with hybrid interface (D-05/D-06) |
| OPT-02 | RandomSample optimizer | Trivial: random integer tuples, evaluate, track best |
| OPT-03 | GreedyWalk optimizer with injectable neighbor function | Old code has Hamming neighbor logic; decouple from CYTools, make neighbor function injectable |
| DOC-03 | pyproject.toml with proper package metadata, optional `[frst]` dependency group | Hatchling build backend, PEP 621 metadata |

</phase_requirements>

## Standard Stack

### Core (Phase 1 only)
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Python | >=3.10 (installed: 3.12.12) | Runtime | Match CYTools conda env; 3.10+ for modern typing | [VERIFIED: conda env] |
| NumPy | >=1.24 (installed: 2.3.5) | Array operations, RNG | `numpy.random.Generator` API, integer-tuple manipulation | [VERIFIED: conda env] |
| tqdm | >=4.60 (installed: 4.67.1) | Progress bars | Used in old code, lightweight | [VERIFIED: conda env] |

### Build/Dev
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| hatchling | 1.29.0 | Build backend | pyproject.toml build-backend | [VERIFIED: pip dry-run shows 1.29.0] |
| pytest | >=8.0 (installed: 9.0.2) | Test runner | All tests | [VERIFIED: conda env] |
| ruff | latest | Linting + formatting | Pre-commit, CI | [ASSUMED -- not installed in conda env, install separately] |

### Not needed in Phase 1
| Library | Reason |
|---------|--------|
| SciPy | D-12: No scipy dependency for Phase 1 optimizers |
| CYTools | Phase 3 only |
| hypothesis | Nice-to-have for Phase 1, not blocking |

**Installation (dev setup):**
```bash
conda run -n cytools pip install -e ".[dev]"
```

## Architecture Patterns

### Recommended Project Structure
```
cyopt/
  __init__.py          # Re-exports: GA, RandomSample, GreedyWalk, Result, DiscreteOptimizer
  _types.py            # Result dataclass, type aliases (DNA = tuple[int, ...], Bounds = ...)
  _cache.py            # EvaluationCache (OrderedDict wrapper with maxsize)
  base.py              # DiscreteOptimizer ABC
  optimizers/
    __init__.py         # Re-exports all optimizer classes
    ga.py               # GA class + operator implementations
    random_sample.py    # RandomSample class
    greedy_walk.py      # GreedyWalk class
tests/
  conftest.py          # Shared fixtures (simple fitness functions, standard bounds)
  test_base.py         # Base class contract tests
  test_cache.py        # Cache behavior tests
  test_ga.py           # GA tests
  test_random_sample.py
  test_greedy_walk.py
  test_result.py       # Result dataclass tests
  test_seeding.py      # Reproducibility tests across all optimizers
pyproject.toml
```

### Pattern 1: Base Class with Abstract `_step` Method
**What:** ABC where concrete optimizers implement a single `_step(iteration)` method that produces candidates for one iteration. The base `run()` method handles the loop, caching, best-tracking, history, and tqdm.
**When to use:** All optimizers follow this pattern.
**Example:**
```python
# Source: derived from old triang_optimizer.py TriangOptimizer pattern
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
import time
import numpy as np
from numpy.random import Generator
from tqdm import tqdm
from collections import OrderedDict

DNA = tuple[int, ...]
Bounds = tuple[tuple[int, int], ...]

@dataclass(frozen=True)
class Result:
    best_solution: DNA
    best_value: float
    history: list[float]              # best-so-far per iteration
    full_history: list[dict] | None   # per-iteration stats (if record_history=True)
    n_evaluations: int
    wall_time: float

class DiscreteOptimizer(ABC):
    def __init__(
        self,
        fitness_fn: Callable[[DNA], float],
        bounds: Bounds,
        seed: int | None = None,
        cache_size: int | None = None,
        record_history: bool = False,
        progress: bool = False,
    ):
        self._fitness_fn = fitness_fn
        self._bounds = bounds
        self._rng = np.random.default_rng(seed)
        self._cache = EvaluationCache(maxsize=cache_size)
        self._record_history = record_history
        self._progress = progress
        # tracking
        self._best_solution: DNA | None = None
        self._best_value: float = float('inf')  # minimization
        self._n_evaluations: int = 0

    def _evaluate(self, dna: DNA) -> float:
        """Evaluate with caching."""
        if dna in self._cache:
            return self._cache[dna]
        self._n_evaluations += 1
        value = self._fitness_fn(dna)
        self._cache[dna] = value
        return value

    def _random_dna(self) -> DNA:
        return tuple(
            int(self._rng.integers(lo, hi + 1))
            for lo, hi in self._bounds
        )

    def run(self, n_iterations: int) -> Result:
        history = []
        full_history = [] if self._record_history else None
        t0 = time.perf_counter()
        iterator = range(n_iterations)
        if self._progress:
            iterator = tqdm(iterator, total=n_iterations)
        for i in iterator:
            step_info = self._step(i)
            # update best
            if self._best_value < float('inf'):
                history.append(self._best_value)
            if self._record_history and step_info:
                full_history.append(step_info)
        wall_time = time.perf_counter() - t0
        return Result(
            best_solution=self._best_solution,
            best_value=self._best_value,
            history=history,
            full_history=full_history,
            n_evaluations=self._n_evaluations,
            wall_time=wall_time,
        )

    @abstractmethod
    def _step(self, iteration: int) -> dict | None:
        """One iteration. Update self._best_solution/value. Return dict for full_history."""
        ...
```

### Pattern 2: Evaluation Cache with LRU Eviction
**What:** Thin wrapper around `OrderedDict` with optional maxsize and move-to-end on access.
**When to use:** All optimizers share this via the base class.
**Example:**
```python
# Source: derived from old code's _optimizer_cache pattern
from collections import OrderedDict

class EvaluationCache:
    def __init__(self, maxsize: int | None = None):
        self._cache: OrderedDict[tuple[int, ...], float] = OrderedDict()
        self._maxsize = maxsize

    def __contains__(self, key: tuple[int, ...]) -> bool:
        return key in self._cache

    def __getitem__(self, key: tuple[int, ...]) -> float:
        self._cache.move_to_end(key)
        return self._cache[key]

    def __setitem__(self, key: tuple[int, ...], value: float) -> None:
        if key in self._cache:
            self._cache.move_to_end(key)
        self._cache[key] = value
        if self._maxsize and len(self._cache) > self._maxsize:
            self._cache.popitem(last=False)

    def __len__(self) -> int:
        return len(self._cache)
```

### Pattern 3: GA Operator Hybrid Interface (D-05/D-06)
**What:** Operators specified as strings (builtins) or callables (custom). Dict config for builtin parameters.
**When to use:** GA constructor.
**Example:**
```python
# Resolve operator from string or callable
def _resolve_operator(self, spec, registry: dict) -> tuple[Callable, dict]:
    if callable(spec):
        return spec, {}
    if isinstance(spec, str):
        return registry[spec], {}
    if isinstance(spec, dict):
        method = spec['method']
        params = {k: v for k, v in spec.items() if k != 'method'}
        return registry[method], params
    raise ValueError(f"Invalid operator spec: {spec}")
```

### Pattern 4: Bounds-Aware Random DNA Generation
**What:** Generic bounded integer-tuple generation using `rng.integers`.
**When to use:** All optimizers need random initialization.
**Key detail from old code:** Old code uses `rng.integers(0, N)` where N is exclusive upper bound. New code must define bounds consistently -- recommend `bounds = ((lo, hi), ...)` where both are inclusive, matching the convention for integer spaces.

### Anti-Patterns to Avoid
- **CYTools coupling in base/optimizers:** Old code references `self.polytope._num_interesting_face_triangs` throughout. New code must use `self._bounds` tuples only.
- **Maximization assumption:** Old code maximizes (`argmax`). New code minimizes (D-02). Every comparison must be flipped.
- **Legacy RandomState:** Old code correctly uses `default_rng` but some paths go through scipy internals with legacy API. Phase 1 has no scipy, so this is not a risk.
- **Mutable default arguments:** `selections=['roulette_wheel', ...]` in old GA `__init__`. Use `None` default + assign in body.
- **Bare `except` clauses:** Old code uses `except: raise Exception()`. Use specific exception types.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Progress bars | Custom print-based progress | `tqdm` | Handles terminal width, rate estimation, ETA, nested bars |
| RNG state management | Manual seed tracking | `np.random.default_rng(seed)` | Correct statistical properties, thread-safe, spawn-able |
| Package build | `setup.py` | `hatchling` + `pyproject.toml` | PEP 621 standard, zero config for flat layout |
| LRU cache | Custom linked list | `collections.OrderedDict` | Battle-tested, `move_to_end` and `popitem(last=False)` give O(1) LRU |

**Key insight:** The algorithms themselves (GA operators, greedy walk, random sampling) must be hand-rolled -- they are the core value of the package. But infrastructure (build, progress, RNG, caching) has excellent stdlib/ecosystem solutions.

## Common Pitfalls

### Pitfall 1: Bounds Convention Mismatch
**What goes wrong:** Off-by-one errors in integer bounds (exclusive vs inclusive upper bound).
**Why it happens:** `np.random.Generator.integers(low, high)` has exclusive upper bound by default. Old code uses `rng.integers(0, N)` where N is the count of options (so valid values are 0..N-1).
**How to avoid:** Define bounds as `(lo, hi_inclusive)` in the public API, internally call `rng.integers(lo, hi + 1)`. Document clearly.
**Warning signs:** Off-by-one in test assertions, optimizer never reaching boundary values.

### Pitfall 2: Minimization vs Maximization Confusion
**What goes wrong:** Porting old code that maximizes without flipping all comparisons.
**Why it happens:** Old code uses `argmax` and `>` comparisons everywhere. D-02 mandates minimization.
**How to avoid:** Search-and-verify every comparison operator during port. Best-so-far starts at `float('inf')`, updates with `<`.
**Warning signs:** Optimizer converging to worst instead of best values.

### Pitfall 3: GA Fitness Normalization
**What goes wrong:** Fitness values for selection become negative or don't sum to 1.
**Why it happens:** Old code normalizes fitness to probability distribution for roulette wheel. With minimization convention, raw values may be negative.
**How to avoid:** The GA's internal fitness transformation (inverse square, etc.) must produce positive values that can be normalized to probabilities. The `fitness_fn` returns raw objective values; the GA internally transforms them for selection.
**Warning signs:** `ValueError` from `rng.choice` with invalid probabilities.

### Pitfall 4: Cache Key Type Consistency
**What goes wrong:** Cache misses for equivalent solutions due to type differences (`(1, 2, 3)` vs `[1, 2, 3]`).
**Why it happens:** NumPy operations return arrays; cache keys must be tuples.
**How to avoid:** Always convert to `tuple(int(x) for x in dna)` before cache lookup. The `_evaluate` method should enforce this.
**Warning signs:** `n_evaluations` not decreasing for repeated evaluations.

### Pitfall 5: Mutable State in GreedyWalk
**What goes wrong:** GreedyWalk maintains walker state between iterations (current position, step size, neighbor layers). If not properly initialized, `run()` on a second call continues from the previous state.
**Why it happens:** Old code maintains `_curr_state`, `_step_size`, `_outer_layer` as instance attributes.
**How to avoid:** Initialize walker state in `run()` or provide explicit `reset()`. Document that `run()` starts fresh each call.
**Warning signs:** Second `run()` call produces different results than expected.

### Pitfall 6: GA Population Initialization Loop
**What goes wrong:** Old code loops until population is filled, skipping invalid DNAs (those that don't "uplift"). In the generic case without validity filtering, this is straightforward, but if the user's fitness function returns `inf` for invalid inputs, the GA could loop forever.
**Why it happens:** Old code has `while len(seen_dna) < num_population` loop.
**How to avoid:** Add a maximum retry count. In the generic optimizer, all integer tuples within bounds are valid by definition -- no uplift check needed.
**Warning signs:** Optimizer hangs during initialization.

## Code Examples

### pyproject.toml (hatchling, flat layout)
```toml
# Source: PEP 621 + hatchling docs [VERIFIED: packaging.python.org]
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "cyopt"
version = "0.1.0"
description = "Discrete optimization toolkit for bounded integer-tuple search spaces"
readme = "README.md"
requires-python = ">=3.10"
license = {text = "MIT"}
authors = [
    {name = "Elijah Sheridan"},
]
dependencies = [
    "numpy>=1.24",
    "tqdm>=4.60",
]

[project.optional-dependencies]
frst = ["cytools"]
dev = [
    "pytest>=8.0",
    "pytest-cov",
    "ruff",
]

[tool.hatch.build.targets.wheel]
packages = ["cyopt"]

[tool.pytest.ini_options]
testpaths = ["tests"]

[tool.ruff]
target-version = "py310"
line-length = 88

[tool.ruff.lint]
select = ["E", "F", "I", "UP", "B", "SIM"]
```

### Hamming Neighbor Generation (Generic, from old code)
```python
# Source: triang_optimizer.py GreedyWalk._sample, decoupled from CYTools
def hamming_neighbors(dna: tuple[int, ...], bounds: tuple[tuple[int, int], ...]) -> list[tuple[int, ...]]:
    """Generate all Hamming-distance-1 neighbors within bounds."""
    neighbors = []
    for i, (lo, hi) in enumerate(bounds):
        for val in range(lo, hi + 1):
            if val != dna[i]:
                neighbor = list(dna)
                neighbor[i] = val
                neighbors.append(tuple(neighbor))
    return neighbors
```

### GA Selection: Tournament (from old code)
```python
# Source: triang_optimizer.py GA.selection_tournament, adapted for minimization
def tournament_selection(
    population: np.ndarray,
    fitness: np.ndarray,
    rng: np.random.Generator,
    k: int = 3,
) -> np.ndarray:
    """Select 2 parents via tournament selection (lower fitness = better)."""
    parents_idx = []
    for _ in range(2):
        candidates = rng.choice(len(population), size=k, replace=False)
        # argmin because we minimize
        winner = candidates[np.argmin(fitness[candidates])]
        parents_idx.append(winner)
    return population[parents_idx]
```

### GA Crossover: N-point (from old code)
```python
# Source: triang_optimizer.py GA.crossover_n_point
def npoint_crossover(
    parents: np.ndarray,
    rng: np.random.Generator,
    n: int = 1,
) -> np.ndarray:
    """N-point crossover producing 2 children from 2 parents."""
    p1, p2 = parents
    length = len(p1)
    cut_points = np.sort(rng.choice(length, size=n, replace=False))
    mask = np.zeros(length, dtype=bool)
    for i, pt in enumerate(cut_points):
        if i % 2 == 0:
            end = cut_points[i + 1] if i + 1 < len(cut_points) else length
            mask[pt:end] = True
    child1 = np.where(mask, p2, p1)
    child2 = np.where(mask, p1, p2)
    return np.array([child1, child2])
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `setup.py` + setuptools | `pyproject.toml` + hatchling | PEP 621 (2021), widely adopted 2023+ | No setup.py needed |
| `np.random.RandomState` | `np.random.default_rng` | NumPy 1.17 (2019), recommended since 1.24 | Better statistical properties, spawn-able |
| `functools.lru_cache` for evaluation caching | `OrderedDict` with explicit maxsize | N/A (design choice) | `lru_cache` doesn't allow size inspection or manual eviction; OrderedDict is more flexible for optimizer caching |
| Single monolithic file | One file per optimizer + shared base | N/A (design choice) | Maintainability, testability |

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | `ruff` should be installed as dev dependency (not in conda env currently) | Standard Stack | Low -- can use any linter, or skip |
| A2 | MIT license is appropriate | Code Examples (pyproject.toml) | Low -- user can change license field |
| A3 | Bounds convention `(lo, hi_inclusive)` is the right public API choice | Architecture Patterns | Medium -- could cause confusion if users expect exclusive upper bound |

## Open Questions

1. **GreedyWalk state across `run()` calls**
   - What we know: Old code maintains walker state (position, step sizes) as instance attributes persistent across runs
   - What's unclear: Should `run()` reset walker state, or should it continue from where it left off?
   - Recommendation: Reset by default (each `run()` starts fresh), matching the expectation that `run(n)` is a self-contained optimization. This is Claude's discretion area.

2. **GA population size vs n_iterations semantics**
   - What we know: Old code has `num_population` and `num_generations` as separate concepts. `run(N)` runs N generations, each producing a full population.
   - What's unclear: Should `n_iterations` in the new API mean "number of generations" for GA?
   - Recommendation: Yes -- `n_iterations` = number of generations. Population size is a hyperparameter. This matches the old code's semantics.

3. **GA fitness function vs objective function**
   - What we know: Old code has separate "fitness" (transforms raw values to selection probabilities) and "target" (the actual objective). D-01 says `fitness_fn` is the constructor arg.
   - What's unclear: The naming is overloaded. Is `fitness_fn` the raw objective, or the selection-probability transform?
   - Recommendation: `fitness_fn` = the raw objective function (what to minimize). The GA's internal selection-probability transform should be a separate concept, perhaps called `selection_pressure` or configured via the fitness hyperparameters (inverse_square, gaussian, etc.).

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 9.0.2 |
| Config file | `pyproject.toml` `[tool.pytest.ini_options]` (Wave 0) |
| Quick run command | `conda run -n cytools pytest tests/ -x -q` |
| Full suite command | `conda run -n cytools pytest tests/ -v` |

### Phase Requirements -> Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| CORE-01 | DiscreteOptimizer ABC cannot be instantiated directly, concrete subclasses can | unit | `pytest tests/test_base.py -x` | Wave 0 |
| CORE-02 | `run()` returns Result with all required fields | unit | `pytest tests/test_result.py -x` | Wave 0 |
| CORE-03 | Cache serves repeated evaluations, respects maxsize, evicts LRU | unit | `pytest tests/test_cache.py -x` | Wave 0 |
| CORE-04 | Best-so-far tracked correctly (monotonically non-increasing for minimization) | unit | `pytest tests/test_base.py::test_best_tracking -x` | Wave 0 |
| CORE-05 | Same seed produces identical results | unit | `pytest tests/test_seeding.py -x` | Wave 0 |
| CORE-06 | Invalid hyperparameters raise clear errors | unit | `pytest tests/test_ga.py::test_hyperparams -x` | Wave 0 |
| CORE-07 | `progress=True` does not crash (tqdm integration) | smoke | `pytest tests/test_base.py::test_progress -x` | Wave 0 |
| CORE-10 | Type hints present (checked by ruff/mypy) | lint | `ruff check cyopt/` | Wave 0 |
| OPT-01 | GA produces improving populations over generations | unit | `pytest tests/test_ga.py -x` | Wave 0 |
| OPT-02 | RandomSample evaluates random points and returns best | unit | `pytest tests/test_random_sample.py -x` | Wave 0 |
| OPT-03 | GreedyWalk moves to better neighbors, stops at local minimum | unit | `pytest tests/test_greedy_walk.py -x` | Wave 0 |
| DOC-03 | `pip install -e .` succeeds, `import cyopt` works | smoke | `pip install -e . && python -c "from cyopt import GA, RandomSample, GreedyWalk, Result"` | Wave 0 |

### Sampling Rate
- **Per task commit:** `conda run -n cytools pytest tests/ -x -q`
- **Per wave merge:** `conda run -n cytools pytest tests/ -v`
- **Phase gate:** Full suite green before `/gsd-verify-work`

### Wave 0 Gaps
- [ ] `pyproject.toml` -- package metadata + pytest config + ruff config
- [ ] `tests/conftest.py` -- shared fixtures (simple quadratic fitness, standard bounds)
- [ ] `tests/test_base.py` -- base class contract tests
- [ ] `tests/test_cache.py` -- cache behavior tests
- [ ] `tests/test_result.py` -- Result dataclass tests
- [ ] `tests/test_seeding.py` -- reproducibility tests
- [ ] `tests/test_ga.py` -- GA tests
- [ ] `tests/test_random_sample.py` -- RandomSample tests
- [ ] `tests/test_greedy_walk.py` -- GreedyWalk tests

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python 3.10+ | Runtime | Yes | 3.12.12 | -- |
| NumPy | Core dependency | Yes | 2.3.5 | -- |
| tqdm | Progress bars | Yes | 4.67.1 | -- |
| pytest | Testing | Yes | 9.0.2 | -- |
| hatchling | Build backend | No (not installed) | -- | `pip install hatchling` in dev setup |
| ruff | Linting | No (not installed) | -- | `pip install ruff` in dev setup |
| pytest-cov | Coverage | No (not installed) | -- | `pip install pytest-cov` in dev setup |

**Missing dependencies with no fallback:**
- None -- all missing tools are installable via pip

**Missing dependencies with fallback:**
- hatchling, ruff, pytest-cov: install as part of `pip install -e ".[dev]"`

## Security Domain

Not applicable for this phase. This is a pure computational library with no network I/O, no user-facing web interfaces, no authentication, no data persistence beyond in-memory caches. Security enforcement does not apply to Phase 1.

## Sources

### Primary (HIGH confidence)
- `/Users/elijahsheridan/Downloads/triang_optimizer.py` -- full old codebase (1762 lines), algorithm logic for GA, RandomSample, GreedyWalk, base class pattern, cache pattern [VERIFIED: direct file read]
- `/Users/elijahsheridan/Research/string/cytools_code/dbrane-tools/` -- flat layout convention, `__init__.py` re-export pattern [VERIFIED: direct file read]
- conda env package versions (numpy 2.3.5, tqdm 4.67.1, pytest 9.0.2, Python 3.12.12) [VERIFIED: `conda run -n cytools` commands]
- hatchling 1.29.0 [VERIFIED: pip dry-run]

### Secondary (MEDIUM confidence)
- PEP 621 pyproject.toml conventions [CITED: packaging.python.org]
- hatchling flat layout configuration [ASSUMED -- standard pattern for hatchling]

### Tertiary (LOW confidence)
- None

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- all versions verified against conda env and pip registry
- Architecture: HIGH -- patterns derived directly from old code + locked decisions
- Pitfalls: HIGH -- identified from direct old code analysis
- Algorithm logic: HIGH -- complete old implementations available for reference

**Research date:** 2026-04-11
**Valid until:** 2026-05-11 (stable domain, no fast-moving dependencies)

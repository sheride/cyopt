# Phase 2: Remaining Optimizers - Research

**Researched:** 2026-04-11
**Domain:** Discrete optimization algorithms (BestFirstSearch, BasinHopping, DifferentialEvolution, MCMC, SimulatedAnnealing)
**Confidence:** HIGH

## Summary

Phase 2 implements five remaining optimizers on the established `DiscreteOptimizer` base class from Phase 1. The base class contract is clear: subclasses implement `_step(iteration) -> dict | None`, call `self._evaluate(dna)` for cached fitness evaluation, use `self._rng` for randomness, and state persists across consecutive `run()` calls (no resetting between runs).

Three optimizers (BestFirstSearch backtrack mode, MCMC, SimulatedAnnealing) are straightforward custom implementations on integer-tuple spaces. BasinHopping is also custom (scipy's version assumes continuous space). DifferentialEvolution wraps `scipy.optimize.differential_evolution` with the public `integrality` parameter -- the key design challenge is mapping SciPy's "run to completion" API to the `_step()`-per-iteration contract.

The old code in `triang_optimizer.py` provides reference implementations for all five, but they are FRST-coupled (polytope-specific neighbor functions, maximization convention, `simanneal` dependency for SA, private SciPy API for BH and DE). The new implementations must be generic integer-tuple optimizers with zero CYTools dependency.

**Primary recommendation:** Implement BestFirstSearch (two modes), BasinHopping, MCMC, and SimulatedAnnealing as custom `_step()`-based optimizers. For DifferentialEvolution, run `scipy.optimize.differential_evolution` with `integrality` and `maxiter=n_iterations` inside an overridden `run()` method (not `_step()`), wrapping the fitness function through `self._evaluate()` for caching/tracking.

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| OPT-04 | BestFirstSearch optimizer with injectable neighbor function | Two-mode design (backtrack + frontier) documented; old code BestFirstSearch analyzed for backtrack mode logic; `neighbor_fn` pattern from GreedyWalk reusable |
| OPT-05 | BasinHopping optimizer (proper discrete reimplementation) | Old code analyzed; custom perturb+local-minimize on integer tuples; Metropolis acceptance criterion; no scipy private API |
| OPT-06 | DifferentialEvolution optimizer (scipy public API with `integrality`) | SciPy 1.17.0 `differential_evolution` verified with `integrality` parameter; `rng` parameter accepts `np.random.Generator`; run-to-completion approach documented |
| OPT-07 | MCMC optimizer with configurable step function | Metropolis-Hastings on integer tuples; old code analyzed; injectable step function pattern |
| OPT-08 | SimulatedAnnealing optimizer (from scratch, no simanneal) | Standard SA algorithm with exponential cooling; old code used `simanneal` package -- must reimplement; injectable neighbor/step function |
</phase_requirements>

## Project Constraints (from CLAUDE.md)

- **Tech stack**: Python, NumPy, SciPy; CYTools only for FRST wrapper layer (Phase 3)
- **Architecture**: Generic optimizers must have zero CYTools dependency
- **SciPy integration strategy**:
  - BasinHopping: Custom implementation (scipy assumes continuous space) [VERIFIED: CLAUDE.md]
  - DifferentialEvolution: Use `scipy.optimize.differential_evolution` with `integrality` parameter [VERIFIED: CLAUDE.md + SciPy 1.17.0 tested]
  - SimulatedAnnealing: Custom implementation (no simanneal dependency, no scipy.optimize.dual_annealing) [VERIFIED: CLAUDE.md]
- **Run/inspect/continue**: State persists across consecutive `run()` calls -- do NOT reset `_best_solution`, `_best_value`, `_n_evaluations`, cache, or subclass state between `run()` calls
- **BestFirstSearch has two modes**: `mode="backtrack"` (default, matches arXiv:2405.08871) and `mode="frontier"` (classic priority-queue BFS)
- **NumPy random**: Use `np.random.default_rng` (modern API), not legacy `RandomState`

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| NumPy | 2.3.5 (installed) | Array ops, random | Already used by base class; `default_rng` for reproducibility | 
| SciPy | 1.17.0 (installed) | DifferentialEvolution only | `differential_evolution` with `integrality` parameter (public API since 1.9) |

[VERIFIED: `pip show` in cytools conda env]

### Supporting

No additional libraries needed. All other optimizers are custom implementations using only Python stdlib + NumPy.

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| heapq | stdlib | Priority queue for BestFirstSearch frontier mode | BestFirstSearch `mode="frontier"` only |

## Architecture Patterns

### File Layout

```
cyopt/optimizers/
    __init__.py            # (already exists)
    random_sample.py       # (Phase 1)
    greedy_walk.py         # (Phase 1)
    ga.py                  # (Phase 1)
    best_first_search.py   # NEW
    basin_hopping.py       # NEW
    differential_evolution.py  # NEW
    mcmc.py                # NEW
    simulated_annealing.py # NEW
```

One file per optimizer, matching existing convention. [VERIFIED: existing Phase 1 files]

### Pattern 1: Single-Point Walker (BestFirstSearch, MCMC, SA, BasinHopping)

**What:** Optimizer maintains a single current position, proposes a move, accepts/rejects.
**When to use:** Local search and stochastic methods.

These all share the pattern:
1. Track `self._current: DNA | None` and `self._current_value: float`
2. Initialize on first `_step()` call (lazy init, same as GreedyWalk)
3. Propose neighbor(s), evaluate, decide whether to move
4. Never reset state between `run()` calls

```python
# Source: existing GreedyWalk pattern [VERIFIED: cyopt/optimizers/greedy_walk.py]
class SinglePointOptimizer(DiscreteOptimizer):
    def __init__(self, ...):
        super().__init__(...)
        self._current: DNA | None = None
        self._current_value: float = float("inf")
    
    def _step(self, iteration: int) -> dict | None:
        if self._current is None:
            self._current = self._random_dna()
            self._current_value = self._evaluate(self._current)
        # ... optimizer-specific logic
```

### Pattern 2: SciPy Delegation (DifferentialEvolution)

**What:** Override `run()` to delegate to SciPy, wrapping fitness through `self._evaluate()`.
**When to use:** When SciPy has a well-tested implementation with proper integer support.

DE cannot be step-by-step because `scipy.optimize.differential_evolution` manages its own population internally. The correct approach:

```python
# Source: analysis of SciPy 1.17.0 API [VERIFIED: tested in conda env]
class DifferentialEvolution(DiscreteOptimizer):
    def run(self, n_iterations: int) -> Result:
        # Wrap fitness_fn through _evaluate for caching + best tracking
        def wrapped(x):
            dna = tuple(int(xi) for xi in x)
            return self._evaluate(dna)
        
        # Build bounds as [(lo, hi+1), ...] -- DE uses half-open for integers
        de_bounds = [(lo, hi + 1) for lo, hi in self._bounds]
        integrality = [True] * len(self._bounds)
        
        t0 = time.perf_counter()
        result = differential_evolution(
            wrapped, de_bounds,
            integrality=integrality,
            maxiter=n_iterations,
            seed=self._rng,  # Pass Generator directly
            popsize=self._popsize,
            # ... other hyperparams
        )
        wall_time = time.perf_counter() - t0
        
        # Build Result from accumulated state
        # history is tricky -- use callback to collect per-generation best
```

**Critical detail:** SciPy DE bounds are half-open `[lo, hi)` for integer variables when `integrality=True`. Since our bounds are inclusive `(lo, hi)`, pass `(lo, hi + 1)`. [VERIFIED: SciPy docs + tested]

**Critical detail:** SciPy DE `rng` parameter accepts `np.random.Generator` directly. Use `self._rng` for reproducibility. The `seed` parameter also works but `rng` is preferred. [VERIFIED: tested both in conda env]

### Pattern 3: BestFirstSearch Two Modes

**What:** Single class with `mode` parameter controlling search behavior.
**When to use:** BestFirstSearch only (user requirement).

```python
class BestFirstSearch(DiscreteOptimizer):
    def __init__(self, ..., mode: str = "backtrack", ...):
        self._mode = mode
        if mode == "backtrack":
            self._path: list[DNA] = []
            self._avoid: set[DNA] = set()
        elif mode == "frontier":
            self._frontier: list[tuple[float, DNA]] = []  # min-heap
            self._visited: set[DNA] = set()
```

**Backtrack mode** (from old code analysis):
1. Evaluate all neighbors (minus `self._avoid` set and path history)
2. If any neighbor improves: move there, push old position to path
3. If no improvement: move to best neighbor anyway
4. If moved back to previous path position (oscillation detected): add the intermediate point to `self._avoid`, pop both from path (backtrack)

**Frontier mode** (classic BFS):
1. Evaluate all neighbors of current, add unseen to min-heap
2. Pop best from heap, move there
3. Mark visited to avoid re-expansion

### Anti-Patterns to Avoid

- **Resetting state in `run()`:** The GA currently reinitializes population in `run()` -- this is because GA needs a fresh population each `run()`. For single-point optimizers, do NOT reset `_current` between runs. State persists.
- **Using scipy private API:** Old code imports `scipy.optimize._basinhopping` and `scipy.optimize._differentialevolution`. Never do this.
- **Inheriting from simanneal.Annealer:** Old code does this. We reimplement SA from scratch.
- **Maximization convention:** Old code maximizes. Our base class minimizes. All fitness comparisons use `<` for improvement.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Differential evolution | Custom DE on integers | `scipy.optimize.differential_evolution(integrality=...)` | SciPy's implementation handles mutation, crossover, selection with decades of testing |
| Priority queue | Custom sorted list | `heapq` (stdlib) | O(log n) push/pop, battle-tested |

**Key insight:** Only DE should use SciPy. BH, MCMC, and SA are simple enough algorithms on discrete spaces that custom implementations are cleaner and more maintainable than wrapping continuous-space SciPy functions.

## Common Pitfalls

### Pitfall 1: SciPy DE bounds format for integer variables
**What goes wrong:** Passing `(lo, hi)` inclusive bounds to DE when `integrality=True` means the upper bound value is excluded.
**Why it happens:** SciPy DE with `integrality=True` treats bounds as `[lo, hi)` (half-open).
**How to avoid:** Transform bounds: `de_bounds = [(lo, hi + 1) for lo, hi in self._bounds]`
**Warning signs:** Best solution never has maximum bound value in any dimension.
[VERIFIED: SciPy docs and tested behavior]

### Pitfall 2: DE history tracking
**What goes wrong:** `differential_evolution` runs to completion internally, so `_step()` is never called per-iteration.
**Why it happens:** DE manages its own population and iteration loop.
**How to avoid:** Override `run()` instead of `_step()`. Use DE's `callback` parameter to collect per-generation best values for the history list. Implement a no-op `_step()` that raises `NotImplementedError` with a helpful message.
**Warning signs:** Empty history list, or history with only one entry.

### Pitfall 3: BestFirstSearch backtrack mode -- oscillation detection
**What goes wrong:** Without the avoid set, the search can oscillate between two local optima forever.
**Why it happens:** Moving to "best neighbor" even when no improvement means the search might just bounce back.
**How to avoid:** Track path; when current position equals position two steps back, add the intermediate to `self._avoid` and pop both from path.
**Warning signs:** Same solutions appearing repeatedly in history.
[VERIFIED: old code triang_optimizer.py lines 1306-1308]

### Pitfall 4: MCMC acceptance ratio uses transformed values
**What goes wrong:** Using raw fitness values in the Metropolis criterion when the user expects a transform.
**Why it happens:** Old code has a `transform` parameter that maps feature values before computing acceptance ratio.
**How to avoid:** Support an optional `transform` callable. Default: identity. The acceptance probability is `min(1, transform(f_new) / transform(f_current))` for maximization, but since we minimize, use `min(1, exp(-(f_new - f_current) / temperature))` (standard Boltzmann).
**Warning signs:** Acceptance rate too high or too low.

### Pitfall 5: SA temperature must decrease, not be constant
**What goes wrong:** SA degenerates to random walk if temperature stays constant.
**Why it happens:** Forgetting to implement a cooling schedule.
**How to avoid:** Standard exponential cooling: `T = T_max * (T_min / T_max) ** (iteration / n_iterations)`. Make schedule configurable.
**Warning signs:** No convergence even after many iterations.

### Pitfall 6: DE callback signature
**What goes wrong:** SciPy DE callback receives `(xk, convergence)` -- returning `True` stops optimization.
**Why it happens:** Different SciPy optimizers have different callback signatures.
**How to avoid:** Callback should return `False` (or `None`) to continue.
[VERIFIED: tested in conda env]

### Pitfall 7: Seeding reproducibility for DE
**What goes wrong:** Using `seed=int` with SciPy DE does not produce the same RNG state as our `self._rng`.
**Why it happens:** SciPy creates its own Generator from the integer seed.
**How to avoid:** Pass `rng=self._rng` (not `seed=self._rng`). SciPy 1.17.0 supports `rng` parameter that accepts a Generator directly. However, note that this consumes RNG state from `self._rng`, so the RNG state after DE finishes depends on how many evaluations DE made.
[VERIFIED: tested both `rng` and `seed` parameters in conda env]

## Code Examples

### BestFirstSearch -- Backtrack Mode Core Logic

```python
# Source: Analysis of old triang_optimizer.py BestFirstSearch._sample() [VERIFIED]
def _step_backtrack(self, iteration: int) -> dict | None:
    if self._current is None:
        self._current = self._random_dna()
        self._current_value = self._evaluate(self._current)

    neighbors = self._neighbor_fn(self._current, self._bounds)
    # Filter out avoided positions and path history (except current)
    valid = [n for n in neighbors if n not in self._avoid and n not in self._path[:-1]]
    
    if not valid:
        # Stuck -- restart from random
        self._current = self._random_dna()
        self._current_value = self._evaluate(self._current)
        self._path.clear()
        return ...
    
    # Evaluate all valid neighbors
    evaluated = [(n, self._evaluate(n)) for n in valid]
    best_neighbor, best_value = min(evaluated, key=lambda x: x[1])
    
    # Move to best neighbor (even if not improving)
    self._path.append(self._current)
    self._current = best_neighbor
    self._current_value = best_value
    
    # Oscillation detection: if we just went back to where we were 2 steps ago
    if len(self._path) >= 2 and self._current == self._path[-2]:
        self._avoid.add(self._path[-1])  # Avoid the intermediate point
        self._path = self._path[:-2]     # Backtrack
```

### MCMC -- Metropolis-Hastings Step

```python
# Source: Standard Metropolis-Hastings + old code analysis [VERIFIED: old code lines 1622-1643]
def _step(self, iteration: int) -> dict | None:
    if self._current is None:
        self._current = self._random_dna()
        self._current_value = self._evaluate(self._current)

    proposal = self._step_fn(self._current, self._bounds, self._rng)
    proposal_value = self._evaluate(proposal)
    
    # Metropolis criterion (minimization: lower is better)
    delta = proposal_value - self._current_value
    if delta < 0 or self._rng.random() < np.exp(-delta / self._temperature):
        self._current = proposal
        self._current_value = proposal_value
```

### SimulatedAnnealing -- Core with Cooling Schedule

```python
# Source: Standard SA algorithm [ASSUMED -- standard textbook algorithm]
def _step(self, iteration: int) -> dict | None:
    if self._current is None:
        self._current = self._random_dna()
        self._current_value = self._evaluate(self._current)

    # Cooling schedule
    frac = iteration / max(1, self._total_iterations - 1)
    temperature = self._t_max * (self._t_min / self._t_max) ** frac
    
    # Propose neighbor
    proposal = self._step_fn(self._current, self._bounds, self._rng)
    proposal_value = self._evaluate(proposal)
    
    # Metropolis acceptance
    delta = proposal_value - self._current_value
    if delta < 0 or self._rng.random() < np.exp(-delta / temperature):
        self._current = proposal
        self._current_value = proposal_value
```

**SA design note:** The total number of iterations must be known upfront for the cooling schedule. Options: (a) require `n_iterations` at construction time, (b) pass it through `run()`, or (c) use iteration index relative to accumulated total. Option (a) is cleanest -- store `n_iterations` as a hyperparameter. This means SA's cooling schedule spans the first `run()` call's iteration count. On subsequent `run()` calls, the cooling schedule continues from where it left off (based on accumulated iteration count).

### BasinHopping -- Perturb + Local Minimize

```python
# Source: Standard basin-hopping pattern [ASSUMED -- standard algorithm]
def _step(self, iteration: int) -> dict | None:
    if self._current is None:
        self._current = self._random_dna()
        self._current_value = self._evaluate(self._current)
        self._current = self._local_minimize(self._current)
        self._current_value = self._evaluate(self._current)

    # Perturb: random displacement in integer space
    perturbed = self._perturb(self._current)
    
    # Local minimization from perturbed point
    local_min = self._local_minimize(perturbed)
    local_min_value = self._evaluate(local_min)
    
    # Metropolis acceptance at basin level
    delta = local_min_value - self._current_value
    if delta < 0 or self._rng.random() < np.exp(-delta / self._temperature):
        self._current = local_min
        self._current_value = local_min_value
```

**Local minimization on integers:** Use a greedy descent -- from the perturbed point, repeatedly move to the best improving Hamming neighbor until stuck. This is effectively an embedded GreedyWalk. Can reuse `hamming_neighbors` from `greedy_walk.py`.

### DifferentialEvolution -- SciPy Wrapper

```python
# Source: SciPy 1.17.0 API [VERIFIED: tested in conda env]
from scipy.optimize import differential_evolution

class DifferentialEvolution(DiscreteOptimizer):
    def __init__(self, fitness_fn, bounds, *, popsize=15, mutation=(0.5, 1),
                 recombination=0.7, strategy="best1bin", **kwargs):
        super().__init__(fitness_fn, bounds, **kwargs)
        self._popsize = popsize
        self._mutation = mutation
        self._recombination = recombination
        self._strategy = strategy

    def _step(self, iteration: int) -> dict | None:
        raise NotImplementedError(
            "DifferentialEvolution delegates to SciPy; use run() directly."
        )

    def run(self, n_iterations: int) -> Result:
        history: list[float] = []
        
        def wrapped(x):
            dna = tuple(int(xi) for xi in x)
            return self._evaluate(dna)
        
        def callback(xk, convergence):
            history.append(self._best_value)
            return False
        
        de_bounds = [(lo, hi + 1) for lo, hi in self._bounds]
        
        t0 = time.perf_counter()
        differential_evolution(
            wrapped, de_bounds,
            integrality=[True] * len(self._bounds),
            maxiter=n_iterations,
            rng=self._rng,
            popsize=self._popsize,
            mutation=self._mutation,
            recombination=self._recombination,
            strategy=self._strategy,
            callback=callback,
            tol=0,       # Don't stop early on convergence
            polish=False, # No continuous polishing
        )
        wall_time = time.perf_counter() - t0
        
        # Pad history if callback was called fewer times
        # (DE callback fires once per generation, not per evaluation)
        
        return Result(
            best_solution=self._best_solution,
            best_value=self._best_value,
            history=history,
            full_history=None,
            n_evaluations=self._n_evaluations,
            wall_time=wall_time,
        )
```

### Default Step Function (reusable across MCMC, SA, BasinHopping)

```python
# Source: pattern from old code + GreedyWalk [VERIFIED: old code lines 1612-1620]
def random_single_flip(dna: DNA, bounds: Bounds, rng: np.random.Generator) -> DNA:
    """Flip one random dimension to a different random value within bounds."""
    i = rng.integers(0, len(dna))
    lo, hi = bounds[i]
    new_val = dna[i]
    while new_val == dna[i] and hi > lo:  # Ensure actual change
        new_val = int(rng.integers(lo, hi + 1))
    result = list(dna)
    result[i] = new_val
    return tuple(result)
```

This can be shared across MCMC, SA, and BasinHopping as the default perturbation. Put it in a shared module (e.g., `cyopt/optimizers/_neighbors.py` alongside the existing `hamming_neighbors`).

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `scipy.optimize._differentialevolution.DifferentialEvolutionSolver` (private) | `scipy.optimize.differential_evolution(integrality=...)` (public) | SciPy 1.9 (2022) | No private API access needed |
| `scipy.optimize._basinhopping` (private) | Custom implementation | N/A | Cleaner, no fragile coupling |
| `simanneal.Annealer` (external dep) | Custom SA implementation | N/A | No external dependency |
| `seed` parameter in SciPy | `rng` parameter accepting Generator | SciPy ~1.12+ | Better reproducibility control |

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | SA cooling schedule: `T_max * (T_min / T_max) ** frac` is the right default | Code Examples (SA) | Low -- standard exponential schedule, easy to make configurable |
| A2 | BasinHopping local minimize via greedy descent is sufficient | Code Examples (BH) | Medium -- if user needs different local minimizer, need injectable `local_minimize_fn`. Recommend making it injectable. |
| A3 | SA should store `n_iterations` at construction time for cooling schedule | Code Examples (SA) | Medium -- alternative is to compute frac from accumulated iterations across runs. Either works. |

## Open Questions

1. **SA cooling schedule across multiple `run()` calls**
   - What we know: SA needs to know total iterations for the cooling schedule. State persists across `run()` calls.
   - What's unclear: Should the cooling schedule restart on each `run()`, or continue from accumulated iteration count?
   - Recommendation: Accept `n_iterations` as a constructor parameter for the total cooling schedule duration. Track accumulated steps. On each `run()` call, continue cooling from current accumulated step count. If accumulated exceeds `n_iterations`, temperature stays at `T_min`.

2. **BasinHopping local minimizer**
   - What we know: Old code used SciPy's minimizer wrapper (continuous). We need a discrete local minimizer.
   - What's unclear: Should the local minimizer be injectable or hardcoded as greedy descent?
   - Recommendation: Default to greedy descent (reusing `hamming_neighbors`). Accept optional `local_minimize_fn` parameter for customization.

3. **DE history semantics**
   - What we know: DE's callback fires once per generation. Our `run()` history has one entry per iteration (generation). But DE also has an initialization phase that evaluates the whole population.
   - What's unclear: Should the history include the initial population evaluation as iteration 0?
   - Recommendation: Include initial best as first history entry. History length = `n_iterations + 1` (or just `n_iterations` via callback). Match what callback provides.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 9.0.2 |
| Config file | pyproject.toml (existing) |
| Quick run command | `conda run -n cytools pytest tests/ -x -q` |
| Full suite command | `conda run -n cytools pytest tests/ -v` |

### Phase Requirements -> Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| OPT-04 | BestFirstSearch instantiation + run (both modes) | unit | `pytest tests/test_best_first_search.py -x` | Wave 0 |
| OPT-04 | BestFirstSearch injectable neighbor_fn | unit | `pytest tests/test_best_first_search.py::test_custom_neighbor_fn -x` | Wave 0 |
| OPT-05 | BasinHopping instantiation + run | unit | `pytest tests/test_basin_hopping.py -x` | Wave 0 |
| OPT-06 | DifferentialEvolution uses scipy public API + integrality | unit | `pytest tests/test_differential_evolution.py -x` | Wave 0 |
| OPT-07 | MCMC instantiation + run | unit | `pytest tests/test_mcmc.py -x` | Wave 0 |
| OPT-08 | SimulatedAnnealing instantiation + run | unit | `pytest tests/test_simulated_annealing.py -x` | Wave 0 |
| ALL | All 8 optimizers pass contract tests (Result shape, seeding, caching, bounds) | integration | `pytest tests/test_integration.py -x` | Partial (3/8 exist) |
| ALL | Seeding reproducibility for all 8 | integration | `pytest tests/test_seeding.py -x` | Partial (3/8 exist) |

### Sampling Rate
- **Per task commit:** `conda run -n cytools pytest tests/ -x -q`
- **Per wave merge:** `conda run -n cytools pytest tests/ -v`
- **Phase gate:** Full suite green before `/gsd-verify-work`

### Wave 0 Gaps
- [ ] `tests/test_best_first_search.py` -- covers OPT-04
- [ ] `tests/test_basin_hopping.py` -- covers OPT-05
- [ ] `tests/test_differential_evolution.py` -- covers OPT-06
- [ ] `tests/test_mcmc.py` -- covers OPT-07
- [ ] `tests/test_simulated_annealing.py` -- covers OPT-08
- [ ] `tests/test_integration.py` -- extend parametrize lists to include all 8 optimizers
- [ ] `tests/test_seeding.py` -- extend to include all 5 new optimizers

## Sources

### Primary (HIGH confidence)
- `cyopt/base.py`, `cyopt/optimizers/greedy_walk.py`, `cyopt/optimizers/ga.py` -- existing codebase patterns
- SciPy 1.17.0 `differential_evolution` API -- tested directly in conda env
- Old code `triang_optimizer.py` -- reference implementations for all 5 optimizers

### Secondary (MEDIUM confidence)
- SciPy docs for `differential_evolution` parameter semantics (bounds, integrality, rng, callback)

### Tertiary (LOW confidence)
- None

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- SciPy verified in env, no new dependencies
- Architecture: HIGH -- base class contract is clear, old code provides reference
- Pitfalls: HIGH -- tested SciPy DE edge cases directly, analyzed old code failure modes

**Research date:** 2026-04-11
**Valid until:** 2026-05-11 (stable domain, no fast-moving dependencies)

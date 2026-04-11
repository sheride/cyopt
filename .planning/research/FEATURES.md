# Feature Landscape

**Domain:** Discrete optimization toolkit (generic integer-tuple optimizers + CYTools FRST wrappers)
**Researched:** 2026-04-11

## Table Stakes

Features users expect. Missing = product feels incomplete.

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| Abstract base class for optimizers | Every serious optimization library (DEAP, pymoo, nevergrad) has a common interface. Users need to swap algorithms without rewriting code. | Low | Old code has `TriangOptimizer` ABC but it's coupled to CYTools. New version needs a generic `DiscreteOptimizer` base with zero CYTools dependency. |
| Consistent `run(n_iterations)` method | Standard iteration interface. Old code has this. pymoo uses `minimize()`, DEAP uses `algorithms.eaSimple()`. The iterative `run(N)` pattern is the right fit here. | Low | Keep from old code but fix: old `run()` doesn't return data (returns `None` due to missing `return data` statement -- a bug). |
| Best-so-far tracking | Every optimizer tracks the best solution found. pymoo's `Result.F`, DEAP's `HallOfFame`, nevergrad's `provide_recommendation()`. | Low | Old code has `dna_best`/`feature_best` properties. Keep this pattern. |
| Evaluation caching | Avoid redundant expensive function evaluations. The old code's `_optimizer_cache` (OrderedDict) is a good idea. | Low | Keep but fix: old code has duplicate `cache` property (defined twice). Use a proper cache with optional max size. |
| Reproducible seeding | All libraries support seeding for reproducibility. Old code uses `np.random.default_rng(seed)` which is the correct modern approach. | Low | Keep from old code. Each optimizer gets its own RNG instance -- this is good practice. |
| All 8 optimizer implementations | GA, RandomSample, GreedyWalk, BestFirstSearch, BasinHopping, DifferentialEvolution, MCMC, SimulatedAnnealing are the stated requirements. | High | This is the core deliverable. Most complexity is in GA (selection/crossover/mutation/survival operators) and the scipy-wrapping optimizers (BasinHopping, DE). |
| Per-position bounded integer search space | The fundamental abstraction: solutions are tuples of integers where each position has independent bounds `[0, max_i)`. | Low | Old code uses `polytope._num_interesting_face_triangs` directly. New generic layer needs a `bounds: list[int]` parameter. |
| FRST wrapper layer | CYTools-specific code that connects generic optimizers to the DNA encoding. Monkey-patches Polytope. | Medium | Port from old code but update to current CYTools API. This is the domain-specific value-add. |
| Hyperparameter management | Users need to configure and inspect optimizer hyperparameters. Old code uses `_hyperparams` dict with property getter/setter. | Low | Keep the dict-based approach but make it more principled: validate hyperparams at construction time, document valid ranges. |
| Progress reporting (tqdm) | Visual feedback for long-running optimizations. Old code uses tqdm in `run()`. Standard in scientific Python. | Low | Keep from old code. |

## Differentiators

Features that set product apart. Not expected, but valued.

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| Ask-tell interface | Nevergrad's signature pattern: `candidate = opt.ask()`, evaluate externally, `opt.tell(candidate, value)`. Enables parallel evaluation, custom scheduling, and integration with external compute. More flexible than the current `run()` approach. | Medium | The old code only has `run(N)` which calls `_sample()` internally. Adding ask-tell gives users control over evaluation, which matters when evaluation is expensive (CYTools triangulation computations). |
| Callback/hook system | pymoo's `Callback.notify(algorithm)` pattern lets users inject custom logic (logging, visualization, early stopping) without modifying optimizer code. | Medium | Old code has no callbacks. A simple `on_iteration(optimizer, iteration_data)` callback would cover 90% of use cases. Can start with a single hook point. |
| Structured Result object | pymoo returns a `Result` with `.X`, `.F`, `.history`, `.exec_time`. Much better than the old code's pattern of accessing deques on the optimizer object. | Medium | Create a `Result` dataclass with: best solution, best value, history (optional), n_evaluations, wall time, cache contents. Return from `run()`. |
| History tracking with bounded memory | Old code uses `collections.deque(maxlen=N_history)` which is good for bounding memory. But the history stores raw lists, not structured data. | Low | Upgrade to store structured iteration records. Keep the bounded deque approach -- it's actually better than pymoo's `save_history=True` which deep-copies the entire algorithm each iteration. |
| Serialization/checkpoint/resume | pymoo uses `dill.dump(algorithm)` for checkpointing. DEAP uses a dict-based approach. For long FRST optimizations, being able to save and resume is valuable. | Medium | Use `pickle`/`dill` serialization of the optimizer state. The main challenge is that the target function (a closure) may not be picklable -- need to handle this by separating state from function. |
| Neighbor function abstraction | Old code hardcodes Hamming and flip graph neighbors. A generic neighbor function `neighbors(solution) -> list[solution]` would make GreedyWalk, BestFirstSearch, and MCMC work on arbitrary discrete spaces. | Low | Old code already parameterizes `graph_type` as "hamming" or "flip". Generalize to accept any callable. Keep Hamming neighbors as the default for the generic layer. |
| Composable GA operators | Old code has selection, crossover, mutation, and survival as methods on the GA class. DEAP's approach is better: operators are standalone functions registered in a `Toolbox`. | Medium | Make operators standalone functions that the GA references. Users can provide custom operators. Keep the built-in set (roulette wheel, tournament, ranked, n-point crossover, uniform crossover, random mutation, elitist survival). |
| Proper `__copy__`/`__deepcopy__` | Old code has `__copy__` as abstract method but most implementations are broken ("semi-incomplete copy right now..."). | Low | Implement proper copying using `copy.deepcopy` on state, sharing the target function and bounds. |
| Type hints throughout | Modern Python practice. Old code has some type hints but they're inconsistent (e.g., `-> [[[tuple],[Number]]]` is invalid syntax). | Low | Use proper type hints: `tuple[int, ...]` for DNA, generic `T` for ancillary data, `Callable[[tuple[int, ...]], tuple[float, Any]]` for target. |

## Anti-Features

Features to explicitly NOT build.

| Anti-Feature | Why Avoid | What to Do Instead |
|--------------|-----------|-------------------|
| Multi-objective optimization | Massive scope increase. pymoo exists for this. cyopt is single-objective by design (maximize a scalar function over FRST classes). The paper's use case is optimizing a single target (e.g., h^{1,1} properties). | Keep single-objective. If users need multi-objective, they can scalarize or use pymoo directly. |
| Automatic hyperparameter tuning | Out of scope per PROJECT.md. This is Optuna's domain. Adding meta-optimization (tuning GA population size, mutation rate, etc.) would double the codebase. | Provide sensible defaults and document hyperparameter guidance. |
| GUI or web dashboard | Out of scope per PROJECT.md. CLI/library only. | Callbacks can feed data to external visualization (matplotlib, tensorboard). |
| Continuous optimization | Out of scope per PROJECT.md. This is for discrete (integer-tuple) spaces. | The old code's hack of using scipy's continuous BasinHopping/DE with rounding is fragile (accesses `scipy.optimize._basinhopping` private internals). Reimplement these as proper discrete algorithms. |
| Built-in parallelism/multiprocessing | Adding `multiprocessing.Pool` or `concurrent.futures` creates complexity around pickling, shared state, and platform differences. The ask-tell pattern naturally enables external parallelism. | Provide ask-tell interface. Users parallelize evaluation externally: `candidates = [opt.ask() for _ in range(n)]; results = pool.map(f, candidates); [opt.tell(c, r) for c, r in zip(candidates, results)]`. |
| Database-backed storage | Optuna uses SQLite for distributed trials. Overkill for cyopt's use case. | Pickle/dill serialization to files is sufficient. |
| Support for non-reflexive polytopes | Explicitly out of scope. FRST optimization assumes reflexive polytopes from the KS database. | Raise clear error if polytope is not reflexive (old code does this). |
| Wrapping scipy private internals | Old code imports `scipy.optimize._basinhopping` and `scipy.optimize._differentialevolution` (underscore-prefixed = private API). These can break with any scipy update. | Reimplement basin hopping and differential evolution as proper discrete algorithms. The discrete versions don't need scipy's continuous machinery anyway. |
| Auto-installing dependencies at import time | Old code has `subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'simanneal'])` inside a try/except import. This is a security and reproducibility anti-pattern. | Declare simanneal (or reimplement SA) as a proper dependency in pyproject.toml, or just reimplement the simple SA algorithm directly (it's ~50 lines). |

## Feature Dependencies

```
Per-position bounded integer search space
  --> Abstract base class (DiscreteOptimizer)
    --> Evaluation caching
    --> Best-so-far tracking
    --> Reproducible seeding
    --> Hyperparameter management
    --> run() method
      --> Progress reporting (tqdm)
      --> History tracking
      --> Structured Result object
    --> Ask-tell interface (alternative to run())
    --> Callback/hook system
    --> Serialization/checkpoint/resume
    --> All 8 optimizer implementations
      --> Neighbor function abstraction (for GreedyWalk, BFS, MCMC)
      --> Composable GA operators (for GA)
      --> Proper __copy__/__deepcopy__

FRST wrapper layer (depends on generic layer being complete)
  --> Monkey-patch Polytope with prep_for_optimizers
  --> DNA encoding (dna_to_frst, triang_to_dna, etc.)
  --> FRST-specific optimizer factory functions
```

## MVP Recommendation

Prioritize:
1. **Generic DiscreteOptimizer base class** with bounds, caching, seeding, best tracking, run(), Result object
2. **All 8 optimizer implementations** on the generic base (this is the core port)
3. **FRST wrapper layer** connecting to CYTools (this is the domain value)
4. **Type hints and docstrings** throughout (table stakes for a published package)

Defer:
- **Ask-tell interface**: Add after the basic `run()` works. It's a second access pattern, not a prerequisite.
- **Callback system**: Add after core optimizers work. Simple `on_iteration` hook is enough initially.
- **Serialization/checkpoint**: Add after optimizers are stable. Serialization is sensitive to class structure changes.
- **Composable GA operators**: Start with operators as methods (like old code), refactor to standalone functions later. The method-based approach works; composability is a DX improvement.

## Old Code: What to Keep vs Modernize

### Keep (good patterns)
- `np.random.default_rng(seed)` per-optimizer RNG (modern, reproducible)
- `collections.deque(maxlen=N_history)` for bounded history
- `OrderedDict` cache for evaluation memoization
- Iterator protocol (`__iter__`, `__next__`)
- `_sample()` as the abstract method each optimizer implements
- Hyperparameter dict with property access
- Separate `reset()` method

### Modernize (problematic patterns)
- **Tight CYTools coupling**: `TriangOptimizer.__init__` takes `Polytope` directly. Split into generic + wrapper.
- **Duplicate `cache` property**: Defined twice on `TriangOptimizer` (lines ~300 and ~309). Remove duplicate.
- **Missing `return` in `run()`**: The `run()` method builds `data` list but never returns it (line 430 region). Bug.
- **`is` comparison for `-inf`**: `feature is -float('inf')` (line 908) uses identity comparison. Use `== -float('inf')` or `math.isinf()`.
- **Invalid type hints**: `-> [[[tuple],[Number]]]` is not valid Python typing.
- **Broken `__copy__` implementations**: Most say "semi-incomplete copy" and some return `None` or wrong types (DE's `__copy__` creates a `BasinHopping`).
- **scipy private API usage**: Importing from `scipy.optimize._basinhopping` and `scipy.optimize._differentialevolution`. Reimplement.
- **Auto-pip-install in import**: `subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'simanneal'])`. Remove.
- **Bare `except` clauses**: Several `except:` without exception types.
- **SimulatedAnnealing `_sample()` returns `[None]`**: The wrapper's `_sample` is a stub; `run()` is overridden entirely. Integrate properly with base class.
- **`reset()` bug**: Calls `self.history[i] = None` but `self.history` returns a *copy*, so this mutates the copy, not the actual history.
- **GreedyWalk `self.name = "random"`**: Copy-paste bug, should be "greedy walk".
- **Inconsistent `self.poly` vs `self.polytope`**: Some `__copy__` methods reference `self.poly` but the attribute is `self.polytope`.

## Sources

- [DEAP Documentation](https://deap.readthedocs.io/en/master/api/tools.html) - Hall of Fame, Logbook, Statistics, checkpointing patterns
- [DEAP GitHub - algorithms.py](https://github.com/DEAP/deap/blob/master/deap/algorithms.py) - Ask-tell and generational algorithm patterns
- [pymoo Result Object](https://pymoo.org/interface/result.html) - Result structure with X, F, G, CV, history, exec_time
- [pymoo Callback](https://pymoo.org/interface/callback.html) - Callback.notify() pattern with full algorithm access
- [pymoo Checkpoints](https://pymoo.org/misc/checkpoint.html) - dill-based serialization for checkpoint/resume
- [Nevergrad Optimization Docs](https://facebookresearch.github.io/nevergrad/optimization.html) - Ask-tell pattern, parallel evaluation, discrete variable support
- [Optuna Study API](https://optuna.readthedocs.io/en/stable/reference/generated/optuna.study.Study.html) - Study/Trial pattern, callbacks, database storage
- [Optuna Callback Tutorial](https://optuna.readthedocs.io/en/stable/tutorial/20_recipes/007_optuna_callback.html) - Callback patterns for optimization control

# Phase 4: Advanced Infrastructure - Context

**Gathered:** 2026-04-12
**Status:** Ready for planning

<domain>
## Phase Boundary

Deliver a callback system (`on_iteration` hooks with early stopping) and serialization/checkpoint/resume support for all 8 discrete optimizers. These features integrate into the existing `DiscreteOptimizer` base class so that the FRST wrapper layer gets them for free.

Requirements covered: CORE-08 (callback system), CORE-09 (serialization/checkpoint/resume).

</domain>

<decisions>
## Implementation Decisions

### Callback System
- **D-01:** Callbacks registered via constructor arg: `callbacks=[fn1, fn2]`, matching the existing `fitness_fn` pattern. Immutable after creation — no add/remove methods.
- **D-02:** Callbacks receive an info dict: `callback(info)` where `info = {'iteration': i, 'best_value': ..., 'best_solution': ..., 'n_evaluations': ..., 'wall_time': ...}`. Same shape as `full_history` dicts for consistency.
- **D-03:** Early stopping via return value — if any callback returns `True`, the `run()` loop terminates early and returns the partial `Result`. Non-exceptional, clean protocol.

### Serialization & Checkpointing
- **D-04:** Full optimizer state serialized: RNG state, population/frontier/current position (optimizer-specific), evaluation cache, best-so-far, iteration count. Resume produces identical results to an uninterrupted run.
- **D-05:** Versioned dict + pickle format. State serialized as a plain Python dict (not the class instance) with a `_checkpoint_version` key. On load, version is checked and migration applied if needed. This maximizes backwards compatibility across package versions — class refactors don't break old checkpoints.
- **D-06:** Each optimizer subclass implements `_get_state() -> dict` and `_set_state(state: dict)` for its optimizer-specific internal state (e.g., GA population, BFS frontier, MCMC position). Base class handles common state (RNG, cache, best-so-far, iteration count).

### Save/Load API
- **D-07:** Methods on optimizer: `optimizer.save_checkpoint(path)` serializes state to file. `Cls.load_checkpoint(path, fitness_fn)` classmethod reconstructs a live optimizer from checkpoint. User provides `fitness_fn` on load since callables can't be reliably serialized.
- **D-08:** Built-in `CheckpointCallback(path, every_n=100)` provided as a convenience. Reuses the callback system (D-01/D-02) rather than adding separate checkpoint logic to `run()`.

### Resume Semantics
- **D-09:** `run()` continues the iteration count from checkpoint. If checkpoint was at iteration 500 and user calls `run(1000)`, it runs iterations 500-1499. History is concatenated. This means `run()` needs to track cumulative iteration offset internally.

### Claude's Discretion
- Exact fields in each optimizer's `_get_state()` dict (whatever's needed for faithful resume)
- Whether `DifferentialEvolution` (scipy wrapper) can support full checkpoint/resume or gets a limited version
- Internal module layout (single `_checkpoint.py` vs split across files)
- Whether `CheckpointCallback` lives in a `cyopt.callbacks` module or `cyopt._checkpoint`

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Existing Codebase
- `cyopt/base.py` — `DiscreteOptimizer` base class with `run()` loop (lines 104-147) where callbacks hook in and checkpoint state lives
- `cyopt/_types.py` — `Result` dataclass (frozen) that `run()` returns
- `cyopt/_cache.py` — `EvaluationCache` that must be serialized/restored
- `cyopt/optimizers/` — All 8 optimizer implementations; each needs `_get_state()`/`_set_state()`

### Old Code Reference
- `/Users/elijahsheridan/Downloads/triang_optimizer.py` — Has some checkpoint logic that can inform the design

### FRST Layer
- `cyopt/frst/_wrapper.py` — `FRSTOptimizer` wraps a generic optimizer; checkpoint/resume should work transparently through the wrapper

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `DiscreteOptimizer.run()` iteration loop — natural injection point for callbacks (between `_step()` and history append)
- `EvaluationCache` (OrderedDict-based) — already serializable via pickle
- `np.random.default_rng` — state accessible via `rng.bit_generator.state` and restorable

### Established Patterns
- Constructor-based configuration (fitness_fn, bounds, seed, cache_size, record_history, progress) — callbacks follow same pattern
- `_step()` returns optional dict for `full_history` — callback info dict should match this shape
- Each optimizer is self-contained in one file with private state attributes

### Integration Points
- `base.py run()` method — needs callback invocation and early-stop check added to iteration loop
- `base.py __init__` — needs `callbacks` parameter
- Each optimizer file — needs `_get_state()` and `_set_state()` methods
- `FRSTOptimizer` — may need its own checkpoint wrapper to save FRST-specific state (polytope reference, target_mode, ancillary_data)

</code_context>

<specifics>
## Specific Ideas

- Backwards compatibility is the top priority for serialization — users should be able to load checkpoints saved with older cyopt versions. The versioned-dict approach (not raw class pickle) is specifically chosen for this.
- Long FRST runs on large polytopes (hours) are the primary use case driving both callbacks (progress monitoring) and checkpointing (crash recovery).

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 04-advanced-infrastructure*
*Context gathered: 2026-04-12*

# Phase 1: Foundation + First Optimizers - Context

**Gathered:** 2026-04-11
**Status:** Ready for planning

<domain>
## Phase Boundary

Deliver a pip-installable Python package (`cyopt`) with an abstract `DiscreteOptimizer` base class operating on bounded integer-tuple search spaces, a structured `Result` dataclass, evaluation caching, reproducible seeding, tqdm progress reporting, and three concrete optimizers: GA, RandomSample, and GreedyWalk. No CYTools dependency — that's Phase 3.

</domain>

<decisions>
## Implementation Decisions

### Base Class Interface
- **D-01:** Fitness function passed as constructor arg (`fitness_fn=f`), locked for the optimizer's lifetime
- **D-02:** Optimizers minimize by default (standard scipy convention). Users negate to maximize.
- **D-03:** `Result` always contains `history` (list of best-so-far value per iteration). When `record_history=True` is passed to the constructor, `Result` also contains `full_history` (list of per-iteration dicts with keys like best, mean, std, etc.)
- **D-04:** `record_history=True` is a constructor flag, default `False`

### GA Operator Design
- **D-05:** GA operators specified via hybrid interface: strings for builtins (`selection='tournament'`), callables for custom operators (`selection=my_custom_fn`)
- **D-06:** Builtin operator parameters configured via nested dicts: `selection={'method': 'tournament', 'k': 3}`, `crossover={'method': 'npoint', 'n': 2}`
- **D-07:** Single objective only in Phase 1. Multi-objective is v2 scope (ADV-02).

### Package Layout
- **D-08:** Flat layout — `cyopt/` at repo root (matches CYTools and dbrane-tools conventions)
- **D-09:** One file per optimizer: `cyopt/optimizers/ga.py`, `random_sample.py`, `greedy_walk.py`. `__init__.py` re-exports all optimizer classes.

### Porting Strategy
- **D-10:** Same algorithms as old `triang_optimizer.py`, clean new API. Preserve core logic (GA selection/crossover/mutation, greedy walk neighbors) but rewrite with clean interfaces, modern `numpy.random.Generator`, and zero CYTools coupling.
- **D-11:** New concise class names: `GA`, `RandomSample`, `GreedyWalk` (not `GeneticAlgorithm`, `RandomSampleOptimizer`, etc.)
- **D-12:** No scipy dependency for Phase 1 optimizers. All three (GA, RandomSample, GreedyWalk) are custom implementations. Scipy strategy for Phase 2 optimizers deferred to Phase 2.

### Claude's Discretion
- Internal helper functions and private method organization
- Exact fields in `full_history` per-iteration dicts (beyond best/mean/std)
- Test structure and test helper utilities
- Hyperparameter validation specifics (what errors to raise, etc.)

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Old Code Reference
- `/Users/elijahsheridan/Downloads/triang_optimizer.py` — Monolithic 1762-line file with all optimizer implementations. Source of truth for algorithm logic (GA operators, greedy walk, random sampling). Tightly coupled to CYTools — extract algorithm logic only.

### Package Structure Reference
- `/Users/elijahsheridan/Research/string/cytools_code/dbrane-tools/` — Reference project for package conventions (flat layout, documentation style)

### CYTools Knowledge Base
- `/Users/elijahsheridan/Research/string/cytools_code/knowledge-base/index.md` — Knowledge base index for CYTools API reference (needed for Phase 3, not Phase 1)

### Paper
- arXiv:2405.08871 — Describes the GA approach, DNA encoding, and optimization methodology

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- None — greenfield project, no existing code in repo

### Established Patterns
- dbrane-tools uses flat layout with `__init__.py` re-exports — follow this pattern
- Old code uses ABC with `@abstractmethod` for optimizer base class — same pattern, but decouple from CYTools

### Integration Points
- `pyproject.toml` with hatchling build backend (PEP 621)
- `cyopt/__init__.py` should export all public classes: `GA`, `RandomSample`, `GreedyWalk`, `Result`, `DiscreteOptimizer`

</code_context>

<specifics>
## Specific Ideas

No specific requirements — open to standard approaches

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 01-foundation-first-optimizers*
*Context gathered: 2026-04-11*

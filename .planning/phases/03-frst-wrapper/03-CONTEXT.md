# Phase 3: FRST Wrapper - Context

**Gathered:** 2026-04-11
**Status:** Ready for planning

<domain>
## Phase Boundary

This phase connects the generic discrete optimizers (Phase 1-2) to CYTools' FRST pipeline. It delivers: monkey-patched Polytope methods for DNA encoding/decoding, a factory function that returns a wrapped optimizer for FRST optimization, and compatibility with the current CYTools API.

Requirements covered: FRST-01, FRST-02, FRST-03, FRST-04.

</domain>

<decisions>
## Implementation Decisions

### Monkey-Patch Design
- **D-01:** Monkey-patch `prep_for_optimizers` and all encoding/decoding functions (`dna_to_frst`, `dna_to_cy`, `triang_to_dna`, `cy_to_dna`) as bound methods on `Polytope`, matching the old code's interface. Users call `poly.prep_for_optimizers()` then `poly.dna_to_frst(dna)`.

### Wrapper API Surface
- **D-02:** Provide a factory function `frst_optimizer(poly, target, optimizer=GA, **kwargs)` that preps the polytope, builds fitness function + bounds from the DNA encoding, instantiates the specified generic optimizer, and returns a wrapped optimizer instance.
- **D-03:** The wrapper's `run()` returns an `FRSTResult` (or similar) with `best_triangulation`, `best_cy` fields auto-decoded from DNA. The underlying generic optimizer is accessible via an attribute (e.g., `wrapper.optimizer`) for power users who want raw DNA results or optimizer state.
- **D-04:** The user provides the optimizer class (e.g., `GA`, `MCMC`) and any optimizer-specific hyperparameters as kwargs to `frst_optimizer`.

### Target Function Design
- **D-05:** Target function receives a CY manifold object by default: `target(cy) -> float`. A mode flag (e.g., `target_mode='triangulation'`) allows the target to receive a Triangulation instead, for users who want to skip CY construction overhead.
- **D-06:** Ancillary data from target evaluations should be preservable. Implementation mechanism is Claude's discretion — options include storing in a dict keyed by DNA alongside the evaluation cache, or using the record_history/callback system.

### CYTools API Compatibility
- **D-07:** Check both CYTools and cornell-dev/lib for functions the old code used. Use CYTools public API whenever possible. Port anything that only lives in cornell-dev/lib into this repository.
- **D-08:** Use `triangfaces_to_frst` (CYTools public API) for the DNA-to-FRST conversion path. Do not reimplement LP solvers or height-finding logic.
- **D-09:** General principle: always prefer CYTools public API over reimplementation. No private API imports (`scipy.optimize._*`, CYTools internals).

### Claude's Discretion
- Ancillary data storage mechanism (D-06)
- Internal structure of the `cyopt/frst/` subpackage (module layout)
- Whether FRSTResult is a dataclass, namedtuple, or extends Result

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Old Code Reference
- `/Users/elijahsheridan/Downloads/triang_optimizer.py` — Original monolithic implementation with all FRST encoding functions and optimizer classes. Contains `prep_for_optimizers`, `dna_to_frst`, `dna_to_cy`, `triang_to_dna`, `cy_to_dna` as nested closures.

### CYTools Knowledge Base
- `/Users/elijahsheridan/Research/string/cytools_code/knowledge-base/software/CYTools/` — Current CYTools API documentation, pitfalls, source errata.
- `/Users/elijahsheridan/Research/string/cytools_code/knowledge-base/index.md` — Knowledge base index for broader context.

### Cornell-dev Library
- `/Users/elijahsheridan/Research/string/cytools_code/cornell-dev/lib/` — Old library code; some functions may need porting if not in current CYTools.

### Paper
- arXiv:2405.08871 — Describes the GA approach for optimizing over FRST classes using the 2-face triangulation DNA encoding.

### Existing Codebase
- `cyopt/base.py` — DiscreteOptimizer base class contract (_step, _evaluate, _random_dna, run)
- `cyopt/_types.py` — DNA, Bounds, FitnessFunction, Result types
- `cyopt/optimizers/` — All 8 generic optimizer implementations

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `DiscreteOptimizer` base class: all 8 optimizers follow the same `run(n_iterations) -> Result` contract
- `DNA = tuple[int, ...]`, `Bounds = tuple[tuple[int, int], ...]` — the FRST wrapper needs to compute bounds from the polytope's interesting faces and their triangulation counts
- `_cache.py` — evaluation cache that the wrapper's fitness function will benefit from automatically

### Established Patterns
- Optimizers accept `fitness_fn: Callable[[DNA], float]` and `bounds: Bounds` — the FRST wrapper must produce these from a Polytope + target
- Optional dependency pattern: `cyopt/frst/` should be importable only when CYTools is available (import guard pattern from CLAUDE.md)

### Integration Points
- `cyopt/__init__.py` — will need conditional FRST imports
- `pyproject.toml` — `[frst]` optional dependency group for CYTools

### Key CYTools Methods (verified in current API)
- `Polytope.triangface_ineqs(return_triangs=True)` — returns inequalities + face triangulations
- `Polytope.triangfaces_to_frst(triangs)` — converts face triangulation choices to FRST
- `Polytope.face_triangs` — list of 2-face triangulations
- `Polytope.n_2face_triangs` — count of triangulations per face
- `Polytope.is_reflexive()` — guard for FRST pipeline

</code_context>

<specifics>
## Specific Ideas

- The wrapper should feel like a natural extension of the old `triang_optimizer.py` interface — users who know the old code should recognize the pattern
- The DNA encoding is based on "interesting" 2-faces (those with >1 triangulation) — bounds come from the number of triangulations per interesting face

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 03-frst-wrapper*
*Context gathered: 2026-04-11*

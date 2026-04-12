# Roadmap: cyopt

## Overview

cyopt delivers a two-layer discrete optimization library: first a generic core with a validated base class and initial optimizers, then the remaining optimizers, then the CYTools FRST wrapper layer, then advanced infrastructure (callbacks, checkpointing), and finally documentation. Each phase delivers a coherent, testable capability. The architecture enforces strict separation between domain-agnostic optimization and CYTools-specific FRST encoding.

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [ ] **Phase 1: Foundation + First Optimizers** - Package scaffold, base class, Result dataclass, caching, seeding, and 3 optimizers (GA, RandomSample, GreedyWalk) to validate the ABC
- [ ] **Phase 2: Remaining Optimizers** - BestFirstSearch, BasinHopping, DifferentialEvolution, MCMC, SimulatedAnnealing
- [ ] **Phase 3: FRST Wrapper** - DNA encoding, Polytope monkey-patching, FRST-specific optimizer wrappers, CYTools API compatibility
- [ ] **Phase 4: Advanced Infrastructure** - Callback system and serialization/checkpoint/resume support
- [ ] **Phase 5: Documentation** - Sphinx docs, tutorial notebooks, README

## Phase Details

### Phase 1: Foundation + First Optimizers
**Goal**: Users can install cyopt and run three distinct optimizers (GA, RandomSample, GreedyWalk) on any bounded integer-tuple search space with caching, seeding, and progress reporting
**Depends on**: Nothing (first phase)
**Requirements**: CORE-01, CORE-02, CORE-03, CORE-04, CORE-05, CORE-06, CORE-07, CORE-10, OPT-01, OPT-02, OPT-03, DOC-03
**Success Criteria** (what must be TRUE):
  1. `pip install -e .` succeeds from the project root and `import cyopt` works without CYTools installed
  2. User can instantiate RandomSample, GA, and GreedyWalk with custom bounds and run optimization on a test objective function, getting back a structured Result with best solution, best value, history, n_evaluations, and wall time
  3. Running the same optimizer with the same seed produces identical results
  4. Repeated evaluations of the same point are served from cache (observable via n_evaluations count vs. actual function calls)
  5. Running with `progress=True` displays a tqdm progress bar
**Plans**: 3 plans
Plans:
- [x] 01-01-PLAN.md — Package scaffold, types, cache, and DiscreteOptimizer base class
- [x] 01-02-PLAN.md — RandomSample and GreedyWalk optimizers
- [x] 01-03-PLAN.md — GA optimizer with composable operators + integration tests

### Phase 2: Remaining Optimizers
**Goal**: All 8 optimizer types are available, covering population-based, local search, and stochastic methods on generic integer-tuple spaces
**Depends on**: Phase 1
**Requirements**: OPT-04, OPT-05, OPT-06, OPT-07, OPT-08
**Success Criteria** (what must be TRUE):
  1. User can instantiate and run BestFirstSearch, BasinHopping, DifferentialEvolution, MCMC, and SimulatedAnnealing on the same test objective and get valid Results
  2. BestFirstSearch and GreedyWalk accept user-provided neighbor functions that change search behavior
  3. DifferentialEvolution uses SciPy public API (`integrality` parameter), not private internals
  4. All 8 optimizers pass the same base-class contract tests (Result shape, seeding reproducibility, caching, bounds enforcement)
**Plans**: 3 plans
Plans:
- [x] 02-01-PLAN.md — BestFirstSearch (two modes), MCMC, SimulatedAnnealing + shared neighbors module
- [x] 02-02-PLAN.md — BasinHopping (custom discrete) + DifferentialEvolution (SciPy wrapper)
- [x] 02-03-PLAN.md — Wire exports + extend integration/seeding tests to all 8 optimizers

### Phase 3: FRST Wrapper
**Goal**: Users can optimize over FRST classes of reflexive polytopes using the DNA encoding, connecting any of the 8 generic optimizers to CYTools triangulations
**Depends on**: Phase 2
**Requirements**: FRST-01, FRST-02, FRST-03, FRST-04
**Success Criteria** (what must be TRUE):
  1. Calling `polytope.prep_for_optimizers()` on a CYTools Polytope precomputes 2-face triangulation data and exposes DNA bounds
  2. `dna_to_frst` and `triang_to_dna` roundtrip correctly: encoding a known triangulation and decoding it back produces the same triangulation
  3. User can run any FRST-wrapped optimizer (e.g., FRST-GA) on a polytope and get back a CYTools Triangulation / CalabiYau object as the best result
  4. All FRST wrapper code works with the current CYTools version installed in the cytools conda environment
**Plans**: 2 plans
Plans:
- [x] 03-01-PLAN.md — DNA encoding module, Polytope monkey-patch, and encoding unit tests
- [x] 03-02-PLAN.md — FRSTResult, FRSTOptimizer wrapper/factory, export wiring, integration tests

### Phase 4: Advanced Infrastructure
**Goal**: Users can attach iteration callbacks for logging/early-stopping and save/resume optimizer state across sessions
**Depends on**: Phase 2
**Requirements**: CORE-08, CORE-09
**Success Criteria** (what must be TRUE):
  1. User can pass an `on_iteration` callback that receives iteration data and can trigger early stopping by returning a sentinel value
  2. User can save optimizer state to disk mid-run and resume from the checkpoint, continuing optimization without loss of cache or best-so-far tracking
**Plans**: 3 plans
Plans:
- [x] 04-01-PLAN.md — Callback system: type aliases, base class integration, DE support, tests
- [x] 04-02-PLAN.md — Checkpoint/resume: _checkpoint module, save/load on base, _get_state/_set_state on all 8 optimizers
- [x] 04-03-PLAN.md — Wire exports, CheckpointCallback integration, cross-optimizer checkpoint tests

### Phase 5: Documentation
**Goal**: Users can learn and use cyopt through comprehensive API docs and worked tutorials
**Depends on**: Phase 3, Phase 4
**Requirements**: DOC-01, DOC-02, DOC-04
**Success Criteria** (what must be TRUE):
  1. `make html` in the docs directory produces a Sphinx site with sphinx-book-theme, autodoc-generated API reference for all public classes and functions
  2. At least two tutorial notebooks exist: one for generic optimizer usage and one for FRST optimization with CYTools
  3. README includes installation instructions (with optional `[frst]` extras) and a quickstart code example that runs
**Plans**: 3 plans
Plans:
- [ ] 05-01-PLAN.md — Sphinx scaffold, RST files, conf.py, Makefile, README, pyproject.toml docs extras
- [ ] 05-02-PLAN.md — Generic optimizer tutorial notebook (no CYTools)
- [ ] 05-03-PLAN.md — FRST optimization + Mori cone cap tutorial notebooks (CYTools required)

## Progress

**Execution Order:**
Phases execute in numeric order: 1 -> 2 -> 3 -> 4 -> 5
(Phase 4 depends on Phase 2 only, but Phase 5 depends on both 3 and 4.)

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Foundation + First Optimizers | 3/3 | Complete | - |
| 2. Remaining Optimizers | 3/3 | Complete | - |
| 3. FRST Wrapper | 2/2 | Complete | - |
| 4. Advanced Infrastructure | 3/3 | Complete | - |
| 5. Documentation | 0/3 | Planning | - |

# Requirements: cyopt

**Defined:** 2026-04-11
**Core Value:** A clean, reusable discrete optimization toolkit that works standalone, with a thin CYTools wrapper for FRST optimization on Calabi-Yau hypersurfaces.

## v1 Requirements

Requirements for initial release. Each maps to roadmap phases.

### Core Infrastructure

- [ ] **CORE-01**: Abstract `DiscreteOptimizer` base class operating on bounded integer-tuple search spaces
- [ ] **CORE-02**: `run(n_iterations)` method returning structured `Result` dataclass (best solution, best value, history, n_evaluations, wall time)
- [ ] **CORE-03**: Evaluation caching via OrderedDict with optional max size
- [ ] **CORE-04**: Best-so-far tracking (best DNA + best feature value)
- [ ] **CORE-05**: Reproducible seeding with per-optimizer `np.random.default_rng`
- [ ] **CORE-06**: Hyperparameter management with validated dict-based interface
- [ ] **CORE-07**: Progress reporting via tqdm integration
- [ ] **CORE-08**: Callback system (`on_iteration` hooks for logging, early stopping, visualization)
- [ ] **CORE-09**: Serialization/checkpoint/resume support (pickle/dill-based state save/load)
- [ ] **CORE-10**: Type hints throughout the codebase

### Optimizers

- [ ] **OPT-01**: GA with composable operators: selection (roulette wheel, tournament, ranked), crossover (n-point, uniform), mutation (random k-point), survival (elitist), configurable fitness functions
- [ ] **OPT-02**: RandomSample optimizer
- [ ] **OPT-03**: GreedyWalk optimizer with injectable neighbor function (default: Hamming neighbors)
- [ ] **OPT-04**: BestFirstSearch optimizer with injectable neighbor function
- [ ] **OPT-05**: BasinHopping optimizer (proper discrete reimplementation, no scipy private API)
- [ ] **OPT-06**: DifferentialEvolution optimizer (scipy public API with `integrality` parameter)
- [ ] **OPT-07**: MCMC optimizer with configurable step function
- [ ] **OPT-08**: SimulatedAnnealing optimizer (reimplemented from scratch, no simanneal dependency)

### FRST Wrapper

- [ ] **FRST-01**: Monkey-patch Polytope with `prep_for_optimizers` (2-face triangulation precomputation)
- [ ] **FRST-02**: DNA encoding functions: `dna_to_frst`, `dna_to_cy`, `triang_to_dna`, `cy_to_dna`
- [ ] **FRST-03**: FRST-specific optimizer wrappers connecting each generic optimizer to the DNA encoding
- [ ] **FRST-04**: Compatible with current CYTools API (updated imports, method names, arguments)

### Documentation & Packaging

- [ ] **DOC-01**: Sphinx documentation with sphinx-book-theme, autodoc, napoleon docstrings
- [ ] **DOC-02**: Tutorial Jupyter notebooks demonstrating usage
- [ ] **DOC-03**: pyproject.toml with proper package metadata, optional `[frst]` dependency group for CYTools
- [ ] **DOC-04**: README with installation instructions and quickstart

## v2 Requirements

Deferred to future release. Tracked but not in current roadmap.

### Advanced Features

- **ADV-01**: Ask-tell interface for external parallel evaluation
- **ADV-02**: Multi-objective optimization support
- **ADV-03**: Automatic hyperparameter tuning integration

## Out of Scope

Explicitly excluded. Documented to prevent scope creep.

| Feature | Reason |
|---------|--------|
| GUI or web dashboard | CLI/library only |
| Continuous optimization | Package is for discrete (integer-tuple) spaces |
| Built-in multiprocessing | Callbacks + external parallelism are sufficient |
| Non-reflexive polytope support | FRST optimization assumes reflexive |
| Wrapping scipy private internals | Fragile; reimplement as proper discrete algorithms |
| Auto-installing dependencies at import | Security and reproducibility anti-pattern |
| Database-backed storage | Pickle serialization is sufficient |

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| CORE-01 | — | Pending |
| CORE-02 | — | Pending |
| CORE-03 | — | Pending |
| CORE-04 | — | Pending |
| CORE-05 | — | Pending |
| CORE-06 | — | Pending |
| CORE-07 | — | Pending |
| CORE-08 | — | Pending |
| CORE-09 | — | Pending |
| CORE-10 | — | Pending |
| OPT-01 | — | Pending |
| OPT-02 | — | Pending |
| OPT-03 | — | Pending |
| OPT-04 | — | Pending |
| OPT-05 | — | Pending |
| OPT-06 | — | Pending |
| OPT-07 | — | Pending |
| OPT-08 | — | Pending |
| FRST-01 | — | Pending |
| FRST-02 | — | Pending |
| FRST-03 | — | Pending |
| FRST-04 | — | Pending |
| DOC-01 | — | Pending |
| DOC-02 | — | Pending |
| DOC-03 | — | Pending |
| DOC-04 | — | Pending |

**Coverage:**
- v1 requirements: 26 total
- Mapped to phases: 0
- Unmapped: 26 ⚠️

---
*Requirements defined: 2026-04-11*
*Last updated: 2026-04-11 after initial definition*

# cyopt

## What This Is

cyopt is an open-source Python package for discrete optimization, with a focus on optimizing functions over FRST (Fine, Regular, Star Triangulation) classes of reflexive polytopes from the Kreuzer-Skarke database. It provides a library of general-purpose discrete optimizers (genetic algorithm, greedy walk, best-first search, MCMC, basin hopping, differential evolution, simulated annealing, random sampling) that operate on tuples of bounded integers, plus a CYTools-specific wrapper layer that applies these optimizers to FRST optimization via a 2-face triangulation DNA encoding.

## Core Value

A clean, reusable discrete optimization toolkit that works standalone, with a thin CYTools wrapper making it immediately applicable to optimization over triangulation classes of Calabi-Yau hypersurfaces.

## Requirements

### Validated

- [x] Generic discrete optimizer base class operating on integer tuples with per-position bounds — Validated in Phase 1: Foundation + First Optimizers
- [x] GA implementation: selection (roulette wheel, tournament, ranked), crossover (n-point, uniform), mutation (random k-point), survival (elitist), fitness functions — Validated in Phase 1
- [x] RandomSample optimizer — Validated in Phase 1
- [x] GreedyWalk optimizer (configurable graph structure via neighbor function) — Validated in Phase 1
- [x] Package structure matching dbrane-tools conventions (pyproject.toml, proper __init__.py, etc.) — Validated in Phase 1

- [x] BestFirstSearch optimizer (backtrack + frontier modes, injectable neighbor function) — Validated in Phase 2
- [x] BasinHopping optimizer (custom greedy descent, Metropolis acceptance, injectable functions) — Validated in Phase 2
- [x] DifferentialEvolution optimizer (SciPy wrapper with integrality, public API only) — Validated in Phase 2
- [x] MCMC optimizer (Metropolis-Hastings, injectable step function) — Validated in Phase 2
- [x] SimulatedAnnealing optimizer (exponential cooling, injectable step function) — Validated in Phase 2

### Active
- [ ] FRST wrapper: monkey-patch Polytope with prep_for_optimizers, dna_to_frst, dna_to_cy, triang_to_dna, etc.
- [ ] FRST-specific optimizer wrappers that connect generic optimizers to the DNA encoding
- [ ] Sphinx documentation (sphinx-book-theme, autodoc, napoleon, tutorials as notebooks)
- [ ] Compatibility with current CYTools API (functions have been moved/renamed since the old code)

### Out of Scope

- GUI or web interface — CLI/library only
- Continuous optimization — this package is for discrete (integer-tuple) search spaces
- Automatic hyperparameter tuning — users configure optimizers manually
- Support for non-reflexive polytopes — FRST optimization assumes reflexive

## Context

- The old code lives at `/Users/elijahsheridan/Downloads/triang_optimizer.py` — a single monolithic file with all optimizers tightly coupled to CYTools Polytope objects. It imports from local `lib.*` modules that no longer exist and uses outdated CYTools API calls.
- The paper [arXiv:2405.08871] describes the GA approach for optimizing over FRST classes, using a DNA encoding based on 2-face triangulation choices for "interesting" faces (those with >1 triangulation).
- dbrane-tools (`/Users/elijahsheridan/Research/string/cytools_code/dbrane-tools/`) is the reference for documentation and package structure: Sphinx with sphinx-book-theme, autodoc, napoleon docstrings, tutorial notebooks, Makefile-based docs build.
- CYTools API has changed significantly since the old code was written — many functions moved, renamed, arguments changed. Will need trial-and-error to update. The knowledge base at `/Users/elijahsheridan/Research/string/cytools_code/knowledge-base/software/CYTools/` has current API docs.
- The `cytools` conda environment has CYTools and related packages pre-installed.

## Constraints

- **Tech stack**: Python, NumPy, SciPy; CYTools only required for FRST wrapper layer
- **Compatibility**: Must work with current CYTools version in the `cytools` conda environment
- **Documentation**: Sphinx + sphinx-book-theme, matching dbrane-tools conventions
- **Architecture**: Generic optimizers must have zero CYTools dependency; FRST layer monkey-patches Polytope

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Two-layer architecture (generic + FRST wrapper) | Makes the GA and other optimizers reusable outside string theory | — Pending |
| Monkey-patch Polytope for FRST methods | Matches old code's interface; user preference | — Pending |
| DNA encoding = 2-face triangulation indices | Proven approach from the paper; user preference | — Pending |
| Package name: cyopt | User choice | — Pending |
| All optimizers from old code included | User wants full port, not just GA | — Pending |

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition** (via `/gsd-transition`):
1. Requirements invalidated? → Move to Out of Scope with reason
2. Requirements validated? → Move to Validated with phase reference
3. New requirements emerged? → Add to Active
4. Decisions to log? → Add to Key Decisions
5. "What This Is" still accurate? → Update if drifted

**After each milestone** (via `/gsd-complete-milestone`):
1. Full review of all sections
2. Core Value check — still the right priority?
3. Audit Out of Scope — reasons still valid?
4. Update Context with current state

---
*Last updated: 2026-04-11 after Phase 2 completion*

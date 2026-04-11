---
phase: 02-remaining-optimizers
plan: 01
subsystem: optimizers
tags: [best-first-search, mcmc, simulated-annealing, discrete-optimization]
dependency_graph:
  requires: [base.DiscreteOptimizer, greedy_walk.hamming_neighbors]
  provides: [BestFirstSearch, MCMC, SimulatedAnnealing, random_single_flip]
  affects: [optimizers.__init__]
tech_stack:
  added: []
  patterns: [single-point-walker, lazy-init, injectable-step-fn, exponential-cooling]
key_files:
  created:
    - cyopt/optimizers/_neighbors.py
    - cyopt/optimizers/best_first_search.py
    - cyopt/optimizers/mcmc.py
    - cyopt/optimizers/simulated_annealing.py
    - tests/test_best_first_search.py
    - tests/test_mcmc.py
    - tests/test_simulated_annealing.py
  modified: []
decisions:
  - BestFirstSearch backtrack uses relaxed greedy (first improving neighbor) rather than evaluating all
  - Oscillation detection adds intermediate node to avoid set and pops last 2 from path
  - SA step_count persists across run() calls for cooling schedule continuity
metrics:
  duration: 178s
  completed: "2026-04-11T22:19:56Z"
  tasks_completed: 2
  tasks_total: 2
  tests_added: 26
  tests_passing: 26
---

# Phase 02 Plan 01: BestFirstSearch, MCMC, SimulatedAnnealing Summary

Three custom single-point optimizers implemented with shared neighbor utility, injectable step/neighbor functions, and full TDD test coverage (26 tests).

## What Was Built

### _neighbors.py (shared utility)
- `random_single_flip(dna, bounds, rng)`: proposes a neighbor by changing exactly one random dimension
- `StepFunction` type alias for injectable step functions used by MCMC, SA, and future BasinHopping

### BestFirstSearch (two modes)
- **Backtrack mode**: maintains path list and avoid set, moves to first improving neighbor (relaxed greedy), detects oscillation when current equals path[-2] and adds intermediate to avoid set, random-restarts when no valid neighbors remain
- **Frontier mode**: uses heapq min-heap priority queue, expands neighbors of current node, pops best unexplored candidate
- Both modes accept custom `neighbor_fn` (default: `hamming_neighbors` from greedy_walk)

### MCMC
- Metropolis-Hastings acceptance: `min(1, exp(-delta/temperature))`
- Configurable fixed temperature and injectable `step_fn`
- Validates temperature > 0

### SimulatedAnnealing
- Exponential cooling: `T = t_max * (t_min / t_max) ** (step_count / (n_iterations - 1))`
- `_step_count` accumulates across consecutive `run()` calls for cooling continuity
- Injectable `step_fn`, validates all temperature/iteration parameters

## Commits

| Task | Commit | Description |
|------|--------|-------------|
| 1 | a5a8885 | Implement BestFirstSearch, MCMC, SimulatedAnnealing and shared _neighbors |
| 2 | aa566c9 | Add unit tests for all three optimizers (26 tests) |

## Test Results

```
26 passed in 0.19s
- 10 BestFirstSearch tests (backtrack, frontier, seeding, continuation, oscillation, custom neighbor_fn, validation)
- 7 MCMC tests (improvement, step_fn, temperature validation, seeding, continuation, history)
- 9 SimulatedAnnealing tests (improvement, cooling, step_fn, seeding, continuation, history, param validation)
```

## Deviations from Plan

None - plan executed exactly as written.

## Key Patterns Established

- **Injectable step function**: MCMC and SA accept `step_fn: StepFunction | None` for custom proposal generation
- **Injectable neighbor function**: BestFirstSearch accepts `neighbor_fn: NeighborFunction | None` for custom graph structure
- **Cooling continuity**: SA's `_step_count` persists across `run()` calls so temperature schedule continues seamlessly
- **Shared utility module**: `_neighbors.py` provides `random_single_flip` reusable by BasinHopping (Plan 02)

## Self-Check: PASSED

All 7 created files verified on disk. Both commit hashes (a5a8885, aa566c9) found in git log.

# Phase 4: Advanced Infrastructure - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-04-12
**Phase:** 04-advanced-infrastructure
**Areas discussed:** Phase necessity, Callback design, Checkpoint scope, Resume semantics

---

## Phase Necessity

| Option | Description | Selected |
|--------|-------------|----------|
| Essential for v1 | Need these for real workloads — FRST optimization on large polytopes takes hours | ✓ |
| Nice to have | Useful but could ship without | |
| Skip to docs | Drop Phase 4 entirely, ship v1 sooner | |

**User's choice:** Essential for v1
**Notes:** Long FRST runs on large polytopes are the primary driver.

---

## Callback Design

### Registration API

| Option | Description | Selected |
|--------|-------------|----------|
| Constructor arg | callbacks=[fn1, fn2] passed to constructor. Matches fitness_fn pattern. | ✓ |
| Method registration | add_callback(fn) / remove_callback(fn). More flexible. | |
| Both | Constructor arg + add/remove methods | |

**User's choice:** Constructor arg

### Callback Data

| Option | Description | Selected |
|--------|-------------|----------|
| Info dict | callback(info) with iteration, best_value, best_solution, etc. | ✓ |
| Positional args | callback(iteration, best_value, best_solution) | |
| Optimizer reference | callback(optimizer, iteration) | |

**User's choice:** Info dict

### Early Stopping

| Option | Description | Selected |
|--------|-------------|----------|
| Return-based | Callback returns True to stop. Clean, non-exceptional. | ✓ |
| Exception-based | Raise StopOptimization exception | |
| No early stopping | Callbacks observe only | |

**User's choice:** Return-based

---

## Checkpoint Scope

### Serialization Format

| Option | Description | Selected |
|--------|-------------|----------|
| Pickle | Standard Python serialization | |
| Dill | Superset of pickle, handles lambdas | |
| Custom JSON + numpy | Human-readable but more code | |
| Versioned dict + pickle | State as plain dict with schema version, not raw class instance | ✓ |

**User's choice:** Versioned dict + pickle
**Notes:** User's top priority is backwards compatibility across package versions. Raw class pickle breaks when class definitions change. Versioned dict approach chosen specifically for long-term stability.

### What Gets Checkpointed

| Option | Description | Selected |
|--------|-------------|----------|
| Full optimizer state | Everything needed to resume identically | ✓ |
| Minimal resume state | Best-so-far + cache + RNG only | |
| Results only | Just saves Result for analysis | |

**User's choice:** Full optimizer state

---

## Resume Semantics

### Save/Load API

| Option | Description | Selected |
|--------|-------------|----------|
| Methods on optimizer | save_checkpoint(path) + cls.load_checkpoint(path, fitness_fn) | ✓ |
| Standalone functions | cyopt.save/load_checkpoint() | |
| Context manager | with optimizer.checkpointing(path): | |

**User's choice:** Methods on optimizer

### Auto-Checkpointing

| Option | Description | Selected |
|--------|-------------|----------|
| Via callback | Built-in CheckpointCallback(path, every_n=100) | ✓ |
| Built into run() | checkpoint_path parameter on run() | |
| Manual only | User calls save_checkpoint() themselves | |

**User's choice:** Via callback (reuses callback system)

### Iteration Counting on Resume

| Option | Description | Selected |
|--------|-------------|----------|
| Continue count | Resumes from checkpoint iteration, history concatenated | ✓ |
| Restart from 0 | Always 1000 new iterations regardless | |
| Separate method | run() fresh, continue() from checkpoint | |

**User's choice:** Continue count

---

## Claude's Discretion

- Exact fields in each optimizer's _get_state() dict
- Whether DifferentialEvolution can support full checkpoint or gets limited version
- Internal module layout
- Where CheckpointCallback lives

## Deferred Ideas

None — discussion stayed within phase scope

# Phase 1: Foundation + First Optimizers - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-04-11
**Phase:** 01-foundation-first-optimizers
**Areas discussed:** Base class interface, GA operator design, Package layout, Porting strategy

---

## Base Class Interface

| Option | Description | Selected |
|--------|-------------|----------|
| Constructor arg | Pass fitness_fn at init, locked for lifetime | ✓ |
| run() arg | Pass at run time, reusable with different objectives | |
| Both | Default in constructor, override in run() | |

**User's choice:** Constructor arg
**Notes:** None

| Option | Description | Selected |
|--------|-------------|----------|
| Minimize | Standard scipy convention, negate to maximize | ✓ |
| Maximize | Matches old code's fitness framing | |
| User-specified | sense='minimize' or sense='maximize' parameter | |

**User's choice:** Minimize
**Notes:** None

| Option | Description | Selected |
|--------|-------------|----------|
| Best-so-far per iteration | Lightweight convergence history | |
| Full per-iteration records | Rich per-iteration dicts (best, mean, std) | |
| Minimal (no history) | Just final result, history via callbacks | |

**User's choice:** Best-so-far by default, with opt-in for full history
**Notes:** User wanted all history to be available somehow. Settled on `record_history=True` constructor flag that populates `result.full_history` with per-iteration dicts, while `result.history` always has best-so-far.

| Option | Description | Selected |
|--------|-------------|----------|
| Constructor flag | record_history=True enables full_history | ✓ |
| Separate history object | Pluggable recorder instance | |

**User's choice:** Constructor flag
**Notes:** None

---

## GA Operator Design

| Option | Description | Selected |
|--------|-------------|----------|
| String names | GA(selection='tournament') | |
| Callable objects | GA(selection=Tournament(k=3)) | |
| Hybrid | Strings for builtins, callables for custom | ✓ |

**User's choice:** Hybrid (strings + callables)
**Notes:** None

| Option | Description | Selected |
|--------|-------------|----------|
| Flat kwargs on GA | tournament_k=3, crossover_n=2 | |
| Nested dicts | selection={'method': 'tournament', 'k': 3} | ✓ |
| Operator classes | Tournament(k=3), NPoint(n=2) | |

**User's choice:** Nested dicts
**Notes:** None

| Option | Description | Selected |
|--------|-------------|----------|
| Single objective only | One fitness function, scalar return | ✓ |
| List of functions | Multi-objective future-proofing | |

**User's choice:** Single objective only
**Notes:** Multi-objective is v2 scope (ADV-02)

---

## Package Layout

| Option | Description | Selected |
|--------|-------------|----------|
| Flat layout | cyopt/ at repo root | ✓ |
| src-layout | src/cyopt/ with extra nesting | |

**User's choice:** Flat layout
**Notes:** User asked why src-layout was recommended. After discussing that flat layout matches the scientific Python ecosystem (CYTools, dbrane-tools) and the src-layout testing pitfall is low-risk with conda + editable installs, flat was the clear fit.

| Option | Description | Selected |
|--------|-------------|----------|
| One file per optimizer | ga.py, random_sample.py, etc. | ✓ |
| Grouped by type | population.py, local_search.py, etc. | |
| Single file | All optimizers in one file | |

**User's choice:** One file per optimizer
**Notes:** None

---

## Porting Strategy

| Option | Description | Selected |
|--------|-------------|----------|
| Same algorithms, clean API | Preserve logic, rewrite interface | ✓ |
| Clean-room rewrite | Redesign from scratch | |
| Direct port then refactor | Line-by-line translation first | |

**User's choice:** Same algorithms, clean API
**Notes:** None

| Option | Description | Selected |
|--------|-------------|----------|
| New concise names | GA, RandomSample, GreedyWalk | ✓ |
| Match old names | GeneticAlgorithm, RandomSampleOptimizer | |

**User's choice:** New concise names
**Notes:** None

| Option | Description | Selected |
|--------|-------------|----------|
| Not relevant to Phase 1 | GA/RandomSample/GreedyWalk are custom, no scipy | ✓ |
| Decide now for all phases | Lock scipy strategy for Phase 2 optimizers | |

**User's choice:** Not relevant to Phase 1
**Notes:** Phase 1 has zero scipy dependency. Scipy strategy deferred to Phase 2 discussion.

---

## Claude's Discretion

- Internal helper functions and private method organization
- Exact fields in full_history per-iteration dicts
- Test structure and helpers
- Hyperparameter validation specifics

## Deferred Ideas

None — discussion stayed within phase scope

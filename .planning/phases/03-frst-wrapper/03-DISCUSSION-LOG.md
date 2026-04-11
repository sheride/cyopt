# Phase 3: FRST Wrapper - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-04-11
**Phase:** 03-frst-wrapper
**Areas discussed:** Monkey-patch design, Wrapper API surface, CYTools API compat, Target function design

---

## Monkey-patch design

| Option | Description | Selected |
|--------|-------------|----------|
| Instance methods | Monkey-patch prep_for_optimizers and encoding functions as bound methods on Polytope, like old code | ✓ |
| Module functions | Standalone functions in cyopt.frst taking Polytope as first arg, no monkey-patching of encoding fns | |
| Prepped wrapper object | prep_for_optimizers returns a PreparedPolytope wrapper, no monkey-patching at all | |

**User's choice:** Instance methods (Recommended)
**Notes:** Matches old code's interface exactly.

---

## Wrapper API surface

| Option | Description | Selected |
|--------|-------------|----------|
| Convenience function | Single optimize_frst() function that runs everything end-to-end | |
| Per-optimizer wrapper classes | FRSTGA, FRSTRandomSample, etc. matching old code's class-per-optimizer pattern | |
| Thin adapter pattern | make_frst_fitness() returns (fitness_fn, bounds) for manual optimizer setup | |
| Factory returning wrapped optimizer | frst_optimizer() returns a wrapped optimizer instance the user can run | ✓ |

**User's choice:** Custom option — factory function returning wrapped optimizer
**Notes:** User proposed: frst_optimizer(poly, target, optimizer=GA, **kwargs) returns a wrapped optimizer. User can call .run() themselves. Wrapper auto-decodes results but raw optimizer accessible via attribute.

### Follow-up: Return type

| Option | Description | Selected |
|--------|-------------|----------|
| Raw optimizer + decode helpers | Return plain DiscreteOptimizer, user decodes manually | |
| Wrapped optimizer | Return wrapper with auto-decoded FRSTResult | ✓ |

**User's choice:** Wrapped optimizer, as long as user CAN access the raw optimizer

### Follow-up: Target input type

| Option | Description | Selected |
|--------|-------------|----------|
| CY manifold | target(cy) — full CalabiYau object | |
| Triangulation | target(triang) — lighter weight | |
| Both supported | Default CY, mode flag for Triangulation | ✓ |

**User's choice:** Both supported

---

## CYTools API compat

### Old lib.* dependencies

| Option | Description | Selected |
|--------|-------------|----------|
| Current CYTools only | Target only current CYTools API, rewrite anything from lib.* | |
| Check cornell-dev/lib | Investigate what lives in cornell-dev vs CYTools before deciding | ✓ |

**User's choice:** Check both CYTools and cornell-dev/lib. Use CYTools public API whenever possible. Port anything only in cornell-dev.

### Heights / LP solving

| Option | Description | Selected |
|--------|-------------|----------|
| Use triangfaces_to_frst | CYTools already has this, no reimplementation needed | ✓ |
| Reimplement from old code | Port old dna_to_reduced_heights logic | |

**User's choice:** Use triangfaces_to_frst, and more generally always use public CYTools whenever possible.

---

## Target function design

### Return value

| Option | Description | Selected |
|--------|-------------|----------|
| Just float | target(cy) → float, matching generic FitnessFunction contract | |
| Support both | Accept float OR (float, extra), store ancillary data | ✓ |

**User's choice:** Wants ancillary data to be saveable, open to implementation mechanism (Claude's discretion).

---

## Claude's Discretion

- Ancillary data storage mechanism
- Internal cyopt/frst/ module layout
- FRSTResult type design

## Deferred Ideas

None

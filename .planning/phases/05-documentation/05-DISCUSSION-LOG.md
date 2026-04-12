# Phase 5: Documentation - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-04-12
**Phase:** 05-documentation
**Areas discussed:** Doc directory layout, Tutorial notebook scope, README depth, Docstring coverage

---

## Doc Directory Layout

### Directory Location

| Option | Description | Selected |
|--------|-------------|----------|
| documentation/ (Recommended) | Matches dbrane-tools exactly | ✓ |
| docs/ | More common in Python ecosystem | |

**User's choice:** documentation/ — match dbrane-tools convention

### Page Format

| Option | Description | Selected |
|--------|-------------|----------|
| RST | Matches dbrane-tools, native to autodoc/autosummary | ✓ |
| MyST Markdown | More readable raw files, myst-nb already in stack | |

**User's choice:** RST

### API Reference Organization

| Option | Description | Selected |
|--------|-------------|----------|
| One page per module (Recommended) | Matches dbrane-tools, autosummary generates these | ✓ |
| Single API page | Everything on one long page | |
| Grouped by layer | Two pages: core-api.rst and frst-api.rst | |

**User's choice:** One page per module

---

## Tutorial Notebook Scope

### Which Tutorials

| Option | Description | Selected |
|--------|-------------|----------|
| Generic optimizer walkthrough (Recommended) | Test functions, compare optimizers, no CYTools | ✓ |
| FRST optimization with CYTools | Full workflow with polytope | |
| Callbacks & checkpointing | Phase 4 features | |
| Optimizer comparison | All 8 on same problem | |

**User's choice:** Generic walkthrough + paper-reproduction notebooks (arXiv:2405.08871 Figs 2-5, arXiv:2512.00144 Mori cone cap)
**Notes:** User specifically wants notebooks that reproduce published figures as both tutorials and validation.

### Tutorial Depth

| Option | Description | Selected |
|--------|-------------|----------|
| Worked examples with output | Full code cells with pre-run output, plots, interpretation | ✓ |
| Minimal quickstart | Just code, user runs themselves | |

**User's choice:** Worked examples with output

---

## README Depth

| Option | Description | Selected |
|--------|-------------|----------|
| Minimal + link to docs (Recommended) | Install, quickstart, link to Sphinx docs | ✓ |
| Comprehensive standalone | Badges, full examples, contributing guide | |
| Academic-focused | Minimal usage, prominent citation section | |

**User's choice:** Minimal + docs link, but with citation/BibTeX section for arXiv:2405.08871
**Notes:** Hybrid of options 1 and 3 — clean minimal README with academic citation section.

---

## Docstring Coverage

| Option | Description | Selected |
|--------|-------------|----------|
| Full public API (Recommended) | NumPy-style docstrings for all public classes/methods/functions | ✓ |
| Existing only | Only what already has docstrings | |
| Classes + key methods only | Class-level and major methods | |

**User's choice:** Full public API

---

## Claude's Discretion

- Sphinx conf.py details (follow dbrane-tools pattern)
- autosummary template structure
- Whether to include conventions/notation page
- Tutorial notebook internal structure

## Deferred Ideas

None

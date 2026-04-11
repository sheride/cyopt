---
phase: 1
slug: foundation-first-optimizers
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-04-11
---

# Phase 1 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 9.0.2 |
| **Config file** | `pyproject.toml` `[tool.pytest.ini_options]` (Wave 0 installs) |
| **Quick run command** | `conda run -n cytools pytest tests/ -x -q` |
| **Full suite command** | `conda run -n cytools pytest tests/ -v` |
| **Estimated runtime** | ~5 seconds |

---

## Sampling Rate

- **After every task commit:** Run `conda run -n cytools pytest tests/ -x -q`
- **After every plan wave:** Run `conda run -n cytools pytest tests/ -v`
- **Before `/gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 10 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 1-01-01 | 01 | 1 | CORE-01 | — | N/A | unit | `pytest tests/test_base.py -x` | ❌ W0 | ⬜ pending |
| 1-01-02 | 01 | 1 | CORE-02 | — | N/A | unit | `pytest tests/test_result.py -x` | ❌ W0 | ⬜ pending |
| 1-01-03 | 01 | 1 | CORE-03 | — | N/A | unit | `pytest tests/test_cache.py -x` | ❌ W0 | ⬜ pending |
| 1-01-04 | 01 | 1 | CORE-04 | — | N/A | unit | `pytest tests/test_base.py::test_best_tracking -x` | ❌ W0 | ⬜ pending |
| 1-01-05 | 01 | 1 | CORE-05 | — | N/A | unit | `pytest tests/test_seeding.py -x` | ❌ W0 | ⬜ pending |
| 1-01-06 | 01 | 1 | CORE-06 | — | N/A | unit | `pytest tests/test_ga.py::test_hyperparams -x` | ❌ W0 | ⬜ pending |
| 1-01-07 | 01 | 1 | CORE-07 | — | N/A | smoke | `pytest tests/test_base.py::test_progress -x` | ❌ W0 | ⬜ pending |
| 1-01-08 | 01 | 1 | CORE-10 | — | N/A | lint | `ruff check cyopt/` | ❌ W0 | ⬜ pending |
| 1-02-01 | 02 | 2 | OPT-01 | — | N/A | unit | `pytest tests/test_ga.py -x` | ❌ W0 | ⬜ pending |
| 1-02-02 | 02 | 2 | OPT-02 | — | N/A | unit | `pytest tests/test_random_sample.py -x` | ❌ W0 | ⬜ pending |
| 1-02-03 | 02 | 2 | OPT-03 | — | N/A | unit | `pytest tests/test_greedy_walk.py -x` | ❌ W0 | ⬜ pending |
| 1-03-01 | 03 | 3 | DOC-03 | — | N/A | smoke | `pip install -e . && python -c "from cyopt import GA, RandomSample, GreedyWalk, Result"` | ❌ W0 | ⬜ pending |

---

## Wave 0 Requirements

- [ ] `pyproject.toml` — package metadata + pytest config + ruff config
- [ ] `tests/conftest.py` — shared fixtures (simple quadratic fitness, standard bounds)
- [ ] `tests/test_base.py` — base class contract tests
- [ ] `tests/test_cache.py` — cache behavior tests
- [ ] `tests/test_result.py` — Result dataclass tests
- [ ] `tests/test_seeding.py` — reproducibility tests
- [ ] `tests/test_ga.py` — GA tests
- [ ] `tests/test_random_sample.py` — RandomSample tests
- [ ] `tests/test_greedy_walk.py` — GreedyWalk tests

*If none: "Existing infrastructure covers all phase requirements."*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| tqdm progress bar displays correctly | CORE-07 | Visual output cannot be automated | Run optimizer with `progress=True`, verify bar appears in terminal |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 10s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending

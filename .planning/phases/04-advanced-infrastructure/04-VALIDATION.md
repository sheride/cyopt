---
phase: 4
slug: advanced-infrastructure
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-04-12
---

# Phase 4 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 9.x |
| **Config file** | `pyproject.toml` ([tool.pytest.ini_options]) |
| **Quick run command** | `conda run -n cytools pytest tests/ -x -q --tb=short` |
| **Full suite command** | `conda run -n cytools pytest tests/ -v --tb=long` |
| **Estimated runtime** | ~10 seconds |

---

## Sampling Rate

- **After every task commit:** Run `conda run -n cytools pytest tests/ -x -q --tb=short`
- **After every plan wave:** Run `conda run -n cytools pytest tests/ -v --tb=long`
- **Before `/gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 10 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 04-01-01 | 01 | 1 | CORE-08 | — | N/A | unit | `conda run -n cytools pytest tests/test_callbacks.py -x -q` | ❌ W0 | ⬜ pending |
| 04-01-02 | 01 | 1 | CORE-09 | — | N/A | unit | `conda run -n cytools pytest tests/test_checkpoint.py -x -q` | ❌ W0 | ⬜ pending |
| 04-02-01 | 02 | 1 | CORE-08, CORE-09 | — | N/A | integration | `conda run -n cytools pytest tests/test_callbacks.py tests/test_checkpoint.py -x -q` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_callbacks.py` — stubs for CORE-08 (iteration callbacks, early stopping)
- [ ] `tests/test_checkpoint.py` — stubs for CORE-09 (save/resume state)

*Existing test infrastructure from Phase 1-3 covers framework setup.*

---

## Manual-Only Verifications

*All phase behaviors have automated verification.*

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 10s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending

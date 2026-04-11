---
phase: 3
slug: frst-wrapper
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-04-11
---

# Phase 3 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 9.x |
| **Config file** | pyproject.toml `[tool.pytest.ini_options]` |
| **Quick run command** | `conda run -n cytools pytest tests/test_frst/ -x -q` |
| **Full suite command** | `conda run -n cytools pytest tests/ -x -q` |
| **Estimated runtime** | ~30 seconds |

---

## Sampling Rate

- **After every task commit:** Run `conda run -n cytools pytest tests/test_frst/ -x -q`
- **After every plan wave:** Run `conda run -n cytools pytest tests/ -x -q`
- **Before `/gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 30 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 03-01-01 | 01 | 1 | FRST-01 | — | N/A | unit | `conda run -n cytools pytest tests/test_frst/test_encoding.py -x -q` | ❌ W0 | ⬜ pending |
| 03-01-02 | 01 | 1 | FRST-02 | — | N/A | unit | `conda run -n cytools pytest tests/test_frst/test_encoding.py -x -q` | ❌ W0 | ⬜ pending |
| 03-02-01 | 02 | 1 | FRST-03 | — | N/A | integration | `conda run -n cytools pytest tests/test_frst/test_wrapper.py -x -q` | ❌ W0 | ⬜ pending |
| 03-02-02 | 02 | 1 | FRST-04 | — | N/A | integration | `conda run -n cytools pytest tests/test_frst/test_wrapper.py -x -q` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_frst/test_encoding.py` — stubs for FRST-01, FRST-02
- [ ] `tests/test_frst/test_wrapper.py` — stubs for FRST-03, FRST-04
- [ ] `tests/test_frst/conftest.py` — shared fixtures (polytope objects, known triangulations)

*Existing pytest infrastructure from Phase 1/2 covers framework installation.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| CYTools conda compatibility | FRST-04 | Environment-specific | Run full test suite in cytools conda env; verify no import errors |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 30s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending

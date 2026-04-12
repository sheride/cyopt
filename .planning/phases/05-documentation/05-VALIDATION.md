---
phase: 5
slug: documentation
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-04-12
---

# Phase 5 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 9.x + Sphinx build |
| **Config file** | `pyproject.toml` (pytest), `documentation/source/conf.py` (Sphinx) |
| **Quick run command** | `conda run -n cytools make -C documentation html 2>&1 | tail -5` |
| **Full suite command** | `conda run -n cytools make -C documentation html && conda run -n cytools python -c "import cyopt; help(cyopt.DiscreteOptimizer)" > /dev/null` |
| **Estimated runtime** | ~30 seconds |

---

## Sampling Rate

- **After every task commit:** Run quick build check
- **After every plan wave:** Run full Sphinx build + import check
- **Before `/gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 30 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 5-01-01 | 01 | 1 | DOC-01 | — | N/A | build | `conda run -n cytools make -C documentation html` | ❌ W0 | ⬜ pending |
| 5-01-02 | 01 | 1 | DOC-01 | — | N/A | file | `test -f documentation/source/conf.py` | ❌ W0 | ⬜ pending |
| 5-02-01 | 02 | 1 | DOC-01 | — | N/A | build | `conda run -n cytools make -C documentation html` | ❌ W0 | ⬜ pending |
| 5-03-01 | 03 | 2 | DOC-02 | — | N/A | file | `test -f documentation/source/tutorials/*.ipynb` | ❌ W0 | ⬜ pending |
| 5-04-01 | 04 | 2 | DOC-04 | — | N/A | file+content | `grep -q '## Installation' README.md` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `documentation/` directory — Sphinx scaffold (conf.py, Makefile, index.rst)
- [ ] `documentation/source/conf.py` — Sphinx configuration matching dbrane-tools

*If none: "Existing infrastructure covers all phase requirements."*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Tutorial notebooks render correctly with plots | DOC-02 | Visual output quality | Open built HTML, verify plots display and code cells have output |
| README quickstart example runs | DOC-04 | Requires manual execution | Copy code block from README, run in Python REPL |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 30s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending

# Phase 5: Documentation - Context

**Gathered:** 2026-04-12
**Status:** Ready for planning

<domain>
## Phase Boundary

Comprehensive documentation for cyopt: Sphinx API reference site, tutorial notebooks, and README. Users can learn the package through worked examples and look up any public API element.

</domain>

<decisions>
## Implementation Decisions

### Doc Directory Layout
- **D-01:** Use `documentation/` directory matching dbrane-tools convention — `documentation/source/conf.py`, `documentation/Makefile`
- **D-02:** RST format for doc pages (not MyST markdown). Matches dbrane-tools and is native to autodoc/autosummary.
- **D-03:** One RST page per module via autosummary — e.g., `cyopt.optimizers.ga.rst`, `cyopt.base.rst`, `cyopt.frst.rst`. Matches dbrane-tools pattern.

### Tutorial Notebooks
- **D-04:** Three tutorial notebooks:
  1. Generic optimizer walkthrough — test functions, instantiate/compare optimizers, convergence plots. No CYTools required.
  2. arXiv:2405.08871 figure reproduction — reproduce Figs 2-5 from the FRST optimization paper using cyopt's GA on polytopes from the Kreuzer-Skarke database.
  3. arXiv:2512.00144 Mori cone cap — GA use case for finding simplicial Mori cone caps.
- **D-05:** Worked examples with saved output — full code cells with pre-run output (nb_execution_mode='off'). Plots, tables, interpretation included.
- **D-06:** Notebooks live in `documentation/source/` (or a `tutorials/` subdirectory within it) so myst-nb renders them as doc pages. Also symlinked or duplicated in a top-level `notebooks/` for standalone use (matches dbrane-tools which has `notebooks/` at root).

### README
- **D-07:** Minimal README with link to Sphinx docs — project description, install instructions (`pip install cyopt` and `pip install cyopt[frst]`), one quickstart code example, link to docs site.
- **D-08:** Include a citation/BibTeX section for arXiv:2405.08871.

### Docstring Coverage
- **D-09:** Full public API docstrings in NumPy style (napoleon) — all public classes, methods, and functions get docstrings: DiscreteOptimizer, all 8 optimizers, Result, DNA, Bounds, FRST wrappers (FRSTOptimizer, frst_optimizer, prep_for_optimizers, encoding functions), Callback/CallbackInfo, CheckpointCallback, save_checkpoint, load_checkpoint.
- **D-10:** Internal/private methods (_step, _get_state, _set_state, etc.) do NOT require docstrings — only public API.

### Claude's Discretion
- Sphinx conf.py details (extensions list, theme options) — follow dbrane-tools pattern
- Exact autosummary template structure
- Whether to include a conventions/notation page (dbrane-tools has one)
- Tutorial notebook internal structure and ordering

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### dbrane-tools Reference (doc structure)
- `/Users/elijahsheridan/Research/string/cytools_code/dbrane-tools/documentation/source/conf.py` — Sphinx config to match (extensions, theme, napoleon settings)
- `/Users/elijahsheridan/Research/string/cytools_code/dbrane-tools/documentation/Makefile` — Build system reference
- `/Users/elijahsheridan/Research/string/cytools_code/dbrane-tools/documentation/source/index.rst` — Top-level doc structure

### Papers for Tutorial Reproduction
- arXiv:2405.08871 — FRST optimization paper, Figs 2-5 to reproduce
- arXiv:2512.00144 — Mori cone cap paper, GA use case to reproduce

### Project References
- `/Users/elijahsheridan/Research/string/cytools_code/knowledge-base/index.md` — CYTools and toric geometry knowledge base

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `cyopt/__init__.py` — Full public API exports (all 8 optimizers, types, callbacks, checkpoint)
- `cyopt/frst/` — FRST wrapper subpackage with monkey-patch and factory function
- dbrane-tools `conf.py` — Ready-to-adapt Sphinx config with all needed extensions

### Established Patterns
- dbrane-tools uses `documentation/source/` with RST + autosummary + myst-nb for notebooks
- `nb_execution_mode = "off"` — notebooks not executed during build (pre-run with saved output)
- `add_module_names = False` — clean API display without module prefixes

### Integration Points
- `pyproject.toml` — needs `[project.optional-dependencies] docs = [...]` group
- `cyopt/__init__.py` — `__all__` already defines the complete public API surface for autodoc

</code_context>

<specifics>
## Specific Ideas

- Tutorial notebooks should reproduce specific published figures (Figs 2-5 from arXiv:2405.08871, Mori cone cap from arXiv:2512.00144) — this doubles as end-to-end validation of the package
- README should have academic citation section with BibTeX entry for arXiv:2405.08871

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 05-documentation*
*Context gathered: 2026-04-12*

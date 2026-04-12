# Phase 5: Documentation - Research

**Researched:** 2026-04-12
**Domain:** Sphinx documentation, Jupyter notebooks, Python package README
**Confidence:** HIGH

## Summary

Phase 5 creates the full documentation suite for cyopt: a Sphinx site with autodoc-generated API reference, three tutorial notebooks, and a proper README. The documentation stack (Sphinx 9.1.0, sphinx-book-theme 1.2.0, myst-nb 1.4.0, and all supporting extensions) is already installed in the cytools conda environment, so no package installation is needed. The codebase already has comprehensive NumPy-style docstrings on all public classes, types, and functions, which means autodoc/autosummary can generate API pages immediately.

The dbrane-tools project at `/Users/elijahsheridan/Research/string/cytools_code/dbrane-tools/documentation/` provides a directly reusable reference for conf.py, Makefile, and RST structure. The pattern is: one RST file per module using `.. automodule::` with `:members:` and `:show-inheritance:`, organized via toctree in parent module RST files.

**Primary recommendation:** Mirror the dbrane-tools documentation structure exactly, adapting conf.py settings and creating one RST per cyopt module. Pre-run all tutorial notebooks and commit with saved output since `nb_execution_mode = "off"`.

<user_constraints>

## User Constraints (from CONTEXT.md)

### Locked Decisions
- **D-01:** Use `documentation/` directory matching dbrane-tools convention -- `documentation/source/conf.py`, `documentation/Makefile`
- **D-02:** RST format for doc pages (not MyST markdown). Matches dbrane-tools and is native to autodoc/autosummary.
- **D-03:** One RST page per module via autosummary -- e.g., `cyopt.optimizers.ga.rst`, `cyopt.base.rst`, `cyopt.frst.rst`. Matches dbrane-tools pattern.
- **D-04:** Three tutorial notebooks: (1) Generic optimizer walkthrough, (2) arXiv:2405.08871 figure reproduction, (3) arXiv:2512.00144 Mori cone cap
- **D-05:** Worked examples with saved output -- full code cells with pre-run output (`nb_execution_mode='off'`). Plots, tables, interpretation included.
- **D-06:** Notebooks live in `documentation/source/` (or `tutorials/` subdirectory within it) so myst-nb renders them as doc pages. Also symlinked or duplicated in top-level `notebooks/` for standalone use.
- **D-07:** Minimal README with link to Sphinx docs -- project description, install instructions, one quickstart code example, link to docs site.
- **D-08:** Include a citation/BibTeX section for arXiv:2405.08871.
- **D-09:** Full public API docstrings in NumPy style (napoleon) -- all public classes, methods, and functions.
- **D-10:** Internal/private methods do NOT require docstrings -- only public API.

### Claude's Discretion
- Sphinx conf.py details (extensions list, theme options) -- follow dbrane-tools pattern
- Exact autosummary template structure
- Whether to include a conventions/notation page
- Tutorial notebook internal structure and ordering

### Deferred Ideas (OUT OF SCOPE)
None -- discussion stayed within phase scope

</user_constraints>

<phase_requirements>

## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| DOC-01 | Sphinx documentation with sphinx-book-theme, autodoc, napoleon docstrings | dbrane-tools conf.py provides exact template; all Sphinx extensions verified installed in conda env |
| DOC-02 | Tutorial Jupyter notebooks demonstrating usage | Three notebooks per D-04; myst-nb renders them as doc pages with `nb_execution_mode="off"` |
| DOC-04 | README with installation instructions and quickstart | Minimal README per D-07/D-08; existing README is just one line, needs full rewrite |

</phase_requirements>

## Standard Stack

### Core (all verified installed in cytools conda env)
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Sphinx | 9.1.0 | Doc generator | Scientific Python standard [VERIFIED: conda env import] |
| sphinx-book-theme | 1.2.0 | HTML theme | Matches dbrane-tools convention [VERIFIED: conda env import] |
| myst-nb | 1.4.0 | Notebook integration | Renders .ipynb as doc pages; successor to nbsphinx [VERIFIED: conda env import] |
| sphinx-copybutton | 0.5.2 | UX | Copy button on code blocks [VERIFIED: conda env import] |
| sphinx-autodoc-typehints | 3.9.8 | Type hints in docs | Renders type annotations in API docs [VERIFIED: conda env import] |
| sphinx-togglebutton | 0.4.4 | UX | Collapsible sections [VERIFIED: conda env import] |
| sphinx-design | 0.7.0 | UX | Tabs, cards [VERIFIED: conda env import] |

### Built-in Extensions (no install needed)
| Extension | Purpose |
|-----------|---------|
| sphinx.ext.autodoc | Auto-generate API from docstrings [VERIFIED: conda env import] |
| sphinx.ext.autosummary | Generate per-module summary pages [VERIFIED: conda env import] |
| sphinx.ext.napoleon | NumPy/Google-style docstring parsing [VERIFIED: conda env import] |
| sphinx.ext.mathjax | LaTeX math rendering [VERIFIED: conda env import] |

**Installation:** Nothing needed -- all packages already installed in the cytools conda env.

## Architecture Patterns

### Recommended Documentation Structure
```
documentation/
  Makefile                    # Standard Sphinx Makefile (copy from dbrane-tools)
  source/
    conf.py                   # Sphinx config (adapt from dbrane-tools)
    index.rst                 # Top-level toctree
    cyopt.rst                 # Package-level automodule + toctree to submodules
    cyopt.base.rst            # DiscreteOptimizer base class
    cyopt.types.rst           # DNA, Bounds, Result, etc.
    cyopt.checkpoint.rst      # CheckpointCallback, save/load
    cyopt.optimizers.rst      # Package-level + toctree to each optimizer
    cyopt.optimizers.ga.rst
    cyopt.optimizers.random_sample.rst
    cyopt.optimizers.greedy_walk.rst
    cyopt.optimizers.best_first_search.rst
    cyopt.optimizers.basin_hopping.rst
    cyopt.optimizers.differential_evolution.rst
    cyopt.optimizers.mcmc.rst
    cyopt.optimizers.simulated_annealing.rst
    cyopt.frst.rst            # FRST wrapper package
    tutorials/
      generic_optimizers.ipynb
      frst_optimization.ipynb
      mori_cone_cap.ipynb
    tutorials.rst             # Toctree linking notebooks
notebooks/                    # Top-level symlinks for standalone use
  generic_optimizers.ipynb -> ../documentation/source/tutorials/generic_optimizers.ipynb
  frst_optimization.ipynb -> ...
  mori_cone_cap.ipynb -> ...
```

### Pattern 1: Module RST File (from dbrane-tools)
**What:** Each public module gets a short RST file that invokes automodule
**When to use:** Every module in the cyopt public API
**Example:**
```rst
cyopt.base --- DiscreteOptimizer base class
==========================================

.. automodule:: cyopt.base
   :members:
   :show-inheritance:
```
Source: `/Users/elijahsheridan/Research/string/cytools_code/dbrane-tools/documentation/source/dbrane_tools.core.dbrane.rst` [VERIFIED: direct inspection]

### Pattern 2: Package-Level RST with Toctree
**What:** Package modules (cyopt, cyopt.optimizers, cyopt.frst) get an RST that lists submodules
**Example:**
```rst
cyopt.optimizers
================

.. currentmodule:: cyopt.optimizers

Optimizer implementations.

.. toctree::
   :maxdepth: 1

   cyopt.optimizers.ga
   cyopt.optimizers.random_sample
   cyopt.optimizers.greedy_walk
   cyopt.optimizers.best_first_search
   cyopt.optimizers.basin_hopping
   cyopt.optimizers.differential_evolution
   cyopt.optimizers.mcmc
   cyopt.optimizers.simulated_annealing
```
Source: `/Users/elijahsheridan/Research/string/cytools_code/dbrane-tools/documentation/source/dbrane_tools.core.rst` [VERIFIED: direct inspection]

### Pattern 3: conf.py Configuration
**What:** Sphinx configuration adapted from dbrane-tools
**Key settings to replicate:**
```python
# Source: dbrane-tools/documentation/source/conf.py [VERIFIED: direct inspection]
import os, sys
sys.path.insert(0, os.path.abspath('../../'))

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    "sphinx.ext.mathjax",
    "sphinx.ext.napoleon",
    "sphinx_copybutton",
    "sphinx_autodoc_typehints",
    "sphinx_togglebutton",
    "sphinx_design",
    "myst_nb",
]

autosummary_generate = True
napoleon_use_rtype = False
napoleon_custom_sections = [('Returns', 'params_style')]

html_theme = "sphinx_book_theme"
nb_execution_mode = "off"
myst_enable_extensions = ["dollarmath"]
myst_dmath_double_inline = True
add_module_names = False
toc_object_entries_show_parents = "hide"
```

### Pattern 4: Notebook Tutorials via myst-nb
**What:** Notebooks in `documentation/source/tutorials/` rendered as doc pages
**Key detail:** `nb_execution_mode = "off"` means notebooks must be pre-run with all output saved. myst-nb reads the saved output from the `.ipynb` file.
**Toctree integration:**
```rst
.. toctree::
   :maxdepth: 1
   :caption: Tutorials

   tutorials/generic_optimizers
   tutorials/frst_optimization
   tutorials/mori_cone_cap
```

### Anti-Patterns to Avoid
- **Executing notebooks during build:** With `nb_execution_mode="off"`, never rely on build-time execution. Always pre-run and commit output. [VERIFIED: dbrane-tools conf.py]
- **MyST markdown for API pages:** Decision D-02 locks RST format. Do not use `.md` files for API reference.
- **Hand-written API docs:** Use `.. automodule::` directives exclusively -- the codebase already has complete docstrings.
- **Documenting private methods:** Decision D-10 explicitly excludes `_step`, `_get_state`, `_set_state`, etc.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| API reference pages | Hand-written class/method docs | `.. automodule:: X :members:` | Docstrings already exist; automodule keeps docs in sync with code |
| Module summary tables | Manual tables of class members | `autosummary_generate = True` | Auto-generates summary tables from docstrings |
| Type hint rendering | Manual type annotation docs | sphinx-autodoc-typehints | Reads Python type annotations automatically |
| Notebook HTML rendering | Custom notebook-to-HTML | myst-nb with `nb_execution_mode="off"` | Standard tool for this exact purpose |
| Math rendering | Custom LaTeX pipeline | mathjax via `sphinx.ext.mathjax` | Works out of the box |

**Key insight:** The existing codebase has comprehensive NumPy-style docstrings on all public API elements. The documentation phase is primarily about creating the Sphinx scaffolding to surface those docstrings, plus writing tutorial notebooks.

## Common Pitfalls

### Pitfall 1: sys.path Not Including Package Root
**What goes wrong:** Sphinx cannot find `cyopt` module during autodoc processing
**Why it happens:** `conf.py` is in `documentation/source/`, two levels deep from the package root
**How to avoid:** `sys.path.insert(0, os.path.abspath('../../'))` in conf.py (matching dbrane-tools)
**Warning signs:** `ModuleNotFoundError` during `make html`

### Pitfall 2: CYTools Import Failure During Doc Build
**What goes wrong:** Building docs in the cytools conda env imports `cyopt.frst`, which imports CYTools, which may have heavy dependencies or fail outside certain environments
**Why it happens:** autodoc actually imports modules to extract docstrings
**How to avoid:** Either (a) always build docs in the cytools conda env, or (b) use `autodoc_mock_imports = ["cytools"]` in conf.py if building without CYTools. Option (a) is simpler since the env is already set up.
**Warning signs:** Import errors mentioning CYTools or CGAL during doc build

### Pitfall 3: Notebook Output Not Saved
**What goes wrong:** Notebooks render as empty code cells with no output in the built docs
**Why it happens:** `nb_execution_mode = "off"` means myst-nb does not execute cells -- it relies on saved output in the .ipynb file
**How to avoid:** Run all notebook cells before committing. Use `jupyter nbconvert --execute --inplace notebook.ipynb` to ensure all cells have output.
**Warning signs:** Empty output areas in built HTML

### Pitfall 4: RST File Naming Mismatch
**What goes wrong:** toctree references don't match actual filenames, causing broken links
**Why it happens:** RST filenames must match the toctree entries exactly (without .rst extension)
**How to avoid:** Use consistent `cyopt.module_name.rst` naming throughout
**Warning signs:** Sphinx warnings about missing documents

### Pitfall 5: autosummary Template Missing
**What goes wrong:** autosummary generates minimal stubs without proper formatting
**Why it happens:** Default autosummary templates may not include `:show-inheritance:` or proper member listing
**How to avoid:** Since D-03 specifies per-module RST files (not autosummary-generated stubs), write explicit RST files with `.. automodule::`. Use `autosummary_generate = True` for summary tables within those pages, not for generating the RST files themselves.
**Warning signs:** Generated pages lack class methods or inheritance info

### Pitfall 6: Symlink Issues on Non-Unix or in Git
**What goes wrong:** Symlinks in `notebooks/` don't work on Windows or aren't tracked by git properly
**Why it happens:** Git symlink handling varies by platform and config
**How to avoid:** Use actual copies rather than symlinks if cross-platform support matters. For this academic project (macOS-only), symlinks are fine. Alternatively, just reference the `documentation/source/tutorials/` path in the README.
**Warning signs:** Broken notebook links in top-level `notebooks/` directory

## Code Examples

### conf.py for cyopt (adapted from dbrane-tools)
```python
# Source: adapted from dbrane-tools/documentation/source/conf.py [VERIFIED: direct inspection]
import os
import sys
sys.path.insert(0, os.path.abspath('../../'))

project = "cyopt"
copyright = "2026, Elijah Sheridan"

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    "sphinx.ext.mathjax",
    "sphinx.ext.napoleon",
    "sphinx_copybutton",
    "sphinx_autodoc_typehints",
    "sphinx_togglebutton",
    "sphinx_design",
    "myst_nb",
]

templates_path = ["_templates"]
source_suffix = [".rst", ".ipynb", ".md"]
exclude_patterns = []
pygments_style = None

autodoc_default_flags = ["members"]
autosummary_generate = True
napoleon_use_rtype = False
napoleon_custom_sections = [('Returns', 'params_style')]

html_theme = "sphinx_book_theme"
html_theme_options = {
    "repository_url": "https://github.com/elijahsheridan/cyopt",
    "use_repository_button": True,
    "use_edit_page_button": True,
}
html_static_path = ["_static"]

nb_execution_mode = "off"
myst_enable_extensions = ["dollarmath"]
myst_dmath_double_inline = True

add_module_names = False
toc_object_entries_show_parents = "hide"
```

### Module RST File Example
```rst
cyopt.optimizers.ga --- Genetic Algorithm
=========================================

.. automodule:: cyopt.optimizers.ga
   :members:
   :show-inheritance:
```

### index.rst Structure
```rst
cyopt: Discrete Optimization Toolkit
=====================================

**cyopt** is a Python library for discrete optimization on bounded
integer-tuple search spaces, with a focus on FRST optimization of
Calabi-Yau hypersurfaces via CYTools.

.. toctree::
   :maxdepth: 1
   :caption: API Documentation

   cyopt

.. toctree::
   :maxdepth: 1
   :caption: Tutorials

   tutorials/generic_optimizers
   tutorials/frst_optimization
   tutorials/mori_cone_cap

Indices and tables
------------------

* :ref:`genindex`
* :ref:`modindex`
```

### README Quickstart Pattern
```python
from cyopt import GA, Bounds

# Minimize sum-of-squares on a 5D integer space
bounds = tuple((0, 10) for _ in range(5))
optimizer = GA(lambda x: sum(xi**2 for xi in x), bounds, seed=42)
result = optimizer.run(100)
print(result.best_solution, result.best_value)
```

## RST Files Needed

The following RST files map to the cyopt module structure:

| RST File | Module | Contents |
|----------|--------|----------|
| `cyopt.rst` | `cyopt` | Top-level toctree to submodules |
| `cyopt.base.rst` | `cyopt.base` | DiscreteOptimizer ABC |
| `cyopt.types.rst` | `cyopt._types` | DNA, Bounds, Result, FitnessFunction, Callback, CallbackInfo |
| `cyopt.checkpoint.rst` | `cyopt._checkpoint` | CheckpointCallback, CHECKPOINT_VERSION |
| `cyopt.optimizers.rst` | `cyopt.optimizers` | Package toctree to 8 optimizer modules |
| `cyopt.optimizers.ga.rst` | `cyopt.optimizers.ga` | GA |
| `cyopt.optimizers.random_sample.rst` | `cyopt.optimizers.random_sample` | RandomSample |
| `cyopt.optimizers.greedy_walk.rst` | `cyopt.optimizers.greedy_walk` | GreedyWalk, hamming_neighbors |
| `cyopt.optimizers.best_first_search.rst` | `cyopt.optimizers.best_first_search` | BestFirstSearch |
| `cyopt.optimizers.basin_hopping.rst` | `cyopt.optimizers.basin_hopping` | BasinHopping |
| `cyopt.optimizers.differential_evolution.rst` | `cyopt.optimizers.differential_evolution` | DifferentialEvolution |
| `cyopt.optimizers.mcmc.rst` | `cyopt.optimizers.mcmc` | MCMC |
| `cyopt.optimizers.simulated_annealing.rst` | `cyopt.optimizers.simulated_annealing` | SimulatedAnnealing |
| `cyopt.frst.rst` | `cyopt.frst` | FRSTOptimizer, FRSTResult, frst_optimizer, patch_polytope |
| `tutorials.rst` | N/A | Toctree for notebook tutorials (optional -- can be inline in index.rst) |

**Note on private modules:** `cyopt._types` and `cyopt._checkpoint` are private by naming convention but contain public API elements (exported in `__all__`). The RST files should use `.. automodule:: cyopt._types` etc. to document them, but name the RST files without the underscore prefix for cleaner URLs.

## Tutorial Notebook Content Guide

### Notebook 1: Generic Optimizer Walkthrough (no CYTools)
- Define a test function (e.g., sphere function, Rastrigin on integers)
- Show Bounds/DNA types
- Instantiate and run GA, RandomSample, GreedyWalk
- Compare results: best_value, n_evaluations, wall_time
- Show convergence plots from `result.history`
- Demonstrate callbacks, CheckpointCallback
- Demonstrate `continue_run()`

### Notebook 2: arXiv:2405.08871 Figure Reproduction (requires CYTools)
- Import cyopt.frst, patch_polytope
- Load polytopes from Kreuzer-Skarke database
- Set up target function (e.g., minimize h^{1,1} of triangulation)
- Run frst_optimizer with GA
- Reproduce Figs 2-5 from the paper
- Requires saved output since CYTools computations are expensive

### Notebook 3: arXiv:2512.00144 Mori Cone Cap (requires CYTools)
- GA use case for finding simplicial Mori cone caps
- Demonstrates a different target function on the same FRST framework

## Docstring Audit

The codebase already has extensive NumPy-style docstrings [VERIFIED: direct inspection of cyopt/base.py, cyopt/_types.py, cyopt/_checkpoint.py, cyopt/frst/_wrapper.py]. Key public API elements with docstrings:

| Element | Has Docstring | Location |
|---------|--------------|----------|
| DiscreteOptimizer | Yes | cyopt/base.py |
| Result | Yes | cyopt/_types.py |
| DNA, Bounds, FitnessFunction, Callback, CallbackInfo | Yes (inline) | cyopt/_types.py |
| CheckpointCallback | Yes | cyopt/_checkpoint.py |
| FRSTOptimizer | Yes | cyopt/frst/_wrapper.py |
| All 8 optimizer classes | Yes (19 docstring lines in ga.py alone) | cyopt/optimizers/*.py |

**Assessment:** Docstring coverage appears comprehensive for the public API. Any gaps should be identified during implementation and filled as needed, but this is not expected to be a major effort.

## pyproject.toml Update

The `pyproject.toml` needs a `docs` optional dependency group:
```toml
[project.optional-dependencies]
docs = [
    "sphinx>=7.0",
    "sphinx-book-theme>=1.0",
    "myst-nb>=1.0",
    "sphinx-copybutton>=0.5",
    "sphinx-autodoc-typehints>=3.0",
    "sphinx-togglebutton>=0.3",
    "sphinx-design>=0.5",
]
```
This is not strictly required for building docs in the conda env (where everything is already installed), but is good packaging practice for others who install from PyPI. [ASSUMED]

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| nbsphinx for notebooks | myst-nb | ~2022 | myst-nb is the actively maintained successor in the Executable Books ecosystem |
| setup.py + Sphinx setup | pyproject.toml + Sphinx standalone | ~2023 | No setup.py needed; Sphinx reads installed package |
| sphinx-rtd-theme | sphinx-book-theme / furo | ~2023 | Modern themes with better sidebar, dark mode support |

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Sphinx | Doc build | Yes | 9.1.0 | -- |
| sphinx-book-theme | HTML theme | Yes | 1.2.0 | -- |
| myst-nb | Notebook rendering | Yes | 1.4.0 | -- |
| sphinx-copybutton | UX | Yes | 0.5.2 | -- |
| sphinx-autodoc-typehints | Type hint docs | Yes | 3.9.8 | -- |
| sphinx-togglebutton | UX | Yes | 0.4.4 | -- |
| sphinx-design | UX | Yes | 0.7.0 | -- |
| CYTools | FRST tutorial notebooks | Yes | conda env | -- |
| Jupyter | Running notebooks | Yes | conda env | -- |
| make | Build system | Yes | system | sphinx-build directly |

**Missing dependencies with no fallback:** None

**Missing dependencies with fallback:** None

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 9.0.2 |
| Config file | pyproject.toml `[tool.pytest.ini_options]` |
| Quick run command | `conda run -n cytools pytest tests/ -x -q` |
| Full suite command | `conda run -n cytools pytest tests/ -v` |

### Phase Requirements to Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| DOC-01 | `make html` produces Sphinx site | smoke | `cd documentation && conda run -n cytools make html` | N/A (build command, not test file) |
| DOC-02 | Tutorial notebooks exist and have output | manual check | `jupyter nbconvert --execute --inplace` to verify runnability | N/A |
| DOC-04 | README has install instructions + quickstart | manual check | grep for key sections | N/A |

### Sampling Rate
- **Per task commit:** Verify `make html` succeeds without errors/warnings
- **Per wave merge:** Full `make html` clean build
- **Phase gate:** `make html` produces complete site; spot-check API pages render correctly

### Wave 0 Gaps
None -- documentation validation is primarily build-based (`make html` success) rather than test-based. No new test files needed for this phase.

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | `docs` optional dependency group in pyproject.toml is good practice | pyproject.toml Update | Low -- only affects non-conda installs |
| A2 | dbrane-tools notebooks are not actually rendered as doc pages (tutorials.rst just lists them) | Architecture Patterns | Low -- cyopt will use myst-nb toctree integration regardless |

## Open Questions (RESOLVED)

1. **GitHub repository URL for sphinx-book-theme options** (RESOLVED)
   - Resolution: Use `https://github.com/elijahsheridan/cyopt` as placeholder; update when repo is created.

2. **Notebook execution for FRST tutorials** (RESOLVED)
   - Resolution: The tutorial notebook will reproduce Figs 2-5 from arXiv:2405.08871. Use small polytopes (h11=5-6) which keep computation under 10 minutes per figure. If the paper used larger polytopes for any figure, the notebook will clearly document what the paper used vs what the tutorial uses and why (computation time), but will still produce the same type of analysis/plot. The executor should read arXiv:2405.08871 to identify the exact figure types and adapt polytope choices to keep total notebook execution under 30 minutes.

## Sources

### Primary (HIGH confidence)
- dbrane-tools `documentation/source/conf.py` -- exact Sphinx configuration to replicate [VERIFIED: direct file inspection]
- dbrane-tools `documentation/source/*.rst` -- RST file patterns for automodule [VERIFIED: direct file inspection]
- dbrane-tools `documentation/Makefile` -- build system [VERIFIED: direct file inspection]
- cyopt codebase `cyopt/__init__.py`, `cyopt/base.py`, `cyopt/_types.py`, `cyopt/frst/` -- public API surface and existing docstrings [VERIFIED: direct file inspection]
- conda env package availability -- all Sphinx extensions verified importable [VERIFIED: conda run import tests]

### Secondary (MEDIUM confidence)
- None needed -- all critical information verified from primary sources

### Tertiary (LOW confidence)
- None

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- all packages verified installed and importable
- Architecture: HIGH -- directly copied from dbrane-tools reference project
- Pitfalls: HIGH -- based on direct experience with the same stack in dbrane-tools

**Research date:** 2026-04-12
**Valid until:** 2026-05-12 (stable stack, no fast-moving dependencies)

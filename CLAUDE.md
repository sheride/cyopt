<!-- GSD:project-start source:PROJECT.md -->
## Project

**cyopt**

cyopt is an open-source Python package for discrete optimization, with a focus on optimizing functions over FRST (Fine, Regular, Star Triangulation) classes of reflexive polytopes from the Kreuzer-Skarke database. It provides a library of general-purpose discrete optimizers (genetic algorithm, greedy walk, best-first search, MCMC, basin hopping, differential evolution, simulated annealing, random sampling) that operate on tuples of bounded integers, plus a CYTools-specific wrapper layer that applies these optimizers to FRST optimization via a 2-face triangulation DNA encoding.

**Core Value:** A clean, reusable discrete optimization toolkit that works standalone, with a thin CYTools wrapper making it immediately applicable to optimization over triangulation classes of Calabi-Yau hypersurfaces.

### Constraints

- **Tech stack**: Python, NumPy, SciPy; CYTools only required for FRST wrapper layer
- **Compatibility**: Must work with current CYTools version in the `cytools` conda environment
- **Documentation**: Sphinx + sphinx-book-theme, matching dbrane-tools conventions
- **Architecture**: Generic optimizers must have zero CYTools dependency; FRST layer monkey-patches Polytope
<!-- GSD:project-end -->

<!-- GSD:stack-start source:research/STACK.md -->
## Technology Stack

## Recommended Stack
### Core Runtime
| Technology | Version | Purpose | Why | Confidence |
|------------|---------|---------|-----|------------|
| Python | >=3.10 | Runtime | Match CYTools conda env; 3.10+ for `match` statements, modern typing (`X | Y`), `ParamSpec` | HIGH |
| NumPy | >=1.24 | Array operations | Core dependency for integer-tuple manipulation and fitness arrays. 1.24+ uses the new `numpy.random.Generator` API (no legacy `RandomState`). Installed: 2.3.5 | HIGH |
| SciPy | >=1.10 | Optimization primitives | `differential_evolution` has `integrality` parameter (added 1.9); `basinhopping` and `dual_annealing` available. Installed: 1.17.0 | HIGH |
| tqdm | >=4.60 | Progress bars | Already used in old code; lightweight, no controversy | HIGH |
### Build System
| Technology | Version | Purpose | Why | Confidence |
|------------|---------|---------|-----|------------|
| Hatchling | latest | Build backend | PEP 621 native, zero-config src-layout support, no setup.py needed. The standard for new scientific Python packages per PyOpenSci. setuptools is legacy for new projects. | HIGH |
| pyproject.toml | PEP 621 | Package metadata | `setup.py` is obsolete for pure-Python packages. `pyproject.toml` is the only file needed. | HIGH |
### Documentation
| Technology | Version | Purpose | Why | Confidence |
|------------|---------|---------|-----|------------|
| Sphinx | >=7.0 | Doc generator | Standard for scientific Python. Installed: 9.1.0 | HIGH |
| sphinx-book-theme | >=1.0 | HTML theme | Matches dbrane-tools conventions exactly. Installed: 1.2.0 | HIGH |
| myst-nb | >=1.0 | Notebook integration | Renders `.ipynb` tutorials as doc pages. Installed: 1.4.0. Replaces nbsphinx (which is effectively deprecated in favor of myst-nb). | HIGH |
| sphinx.ext.napoleon | built-in | Docstrings | NumPy/Google-style docstrings. Matches dbrane-tools. | HIGH |
| sphinx.ext.autodoc | built-in | API docs | Auto-generate API reference from docstrings | HIGH |
| sphinx-copybutton | >=0.5 | UX | Copy button on code blocks. Installed: 0.5.2 | HIGH |
| sphinx-autodoc-typehints | >=3.0 | Type hints in docs | Renders type annotations in API docs. Installed: 3.9.8 | HIGH |
| sphinx-togglebutton | >=0.3 | UX | Collapsible sections for verbose output. Installed: 0.4.4 | MEDIUM |
| sphinx-design | >=0.5 | UX | Tabs, cards for tutorials. Installed: 0.7.0 | MEDIUM |
### Testing
| Technology | Version | Purpose | Why | Confidence |
|------------|---------|---------|-----|------------|
| pytest | >=8.0 | Test runner | De facto standard. Installed: 9.0.2 | HIGH |
| pytest-cov | latest | Coverage | Coverage reporting. Standard companion to pytest. | HIGH |
| hypothesis | latest | Property-based testing | Excellent for testing optimizers with random inputs: generate random bounds, random fitness functions, verify invariants hold. Scientific Python standard for numerical code. | MEDIUM |
### Development Tools
| Technology | Version | Purpose | Why | Confidence |
|------------|---------|---------|-----|------------|
| ruff | latest | Linting + formatting | Replaces flake8, isort, black, pyflakes in one tool. 10-100x faster. The 2025+ standard. | HIGH |
### Optional Heavy Dependency
| Technology | Version | Purpose | Why | Confidence |
|------------|---------|---------|-----|------------|
| CYTools | (conda env) | FRST wrapper layer | Required ONLY for the `cyopt.frst` subpackage. Must be an optional extra, not a core dependency. Version pinned to whatever is in the conda env. | HIGH |
## Package Structure
## Optional Dependency Pattern
### pyproject.toml structure
### Import guard pattern for CYTools
# cyopt/frst/__init__.py
### Test skip pattern
# tests/test_frst/conftest.py
## SciPy Integration Strategy
### What to wrap vs. reimplement
| Optimizer | Strategy | Rationale |
|-----------|----------|-----------|
| BasinHopping | Custom implementation on integer-tuple space | `scipy.optimize.basinhopping` assumes continuous space. The old code monkey-patches internal classes. Cleaner to implement the basin-hopping pattern (perturb + local minimize) directly on discrete space. |
| DifferentialEvolution | Use `scipy.optimize.differential_evolution` with `integrality` parameter | SciPy 1.9+ natively supports integer constraints via the `integrality` parameter. This is the clean path -- no private API access needed. |
| SimulatedAnnealing | Custom implementation | `scipy.optimize.dual_annealing` is for continuous spaces. SA on integer tuples is simple to implement directly (propose neighbor, accept/reject with Boltzmann criterion). |
| GeneticAlgorithm | Custom implementation | No scipy equivalent for discrete GA. Standard approach. |
| MCMC | Custom implementation | Metropolis-Hastings on integer tuples is trivial. No scipy dependency needed. |
| GreedyWalk | Custom implementation | Problem-specific; no library equivalent. |
| BestFirstSearch | Custom implementation | Priority-queue search; use `heapq` from stdlib. |
| RandomSample | Custom implementation | Trivial: sample random integer tuples, evaluate, return best. |
### NumPy Random API
# Good: modern API
# Bad: legacy API (old code uses this via scipy internals)
## Alternatives Considered
| Category | Recommended | Alternative | Why Not |
|----------|-------------|-------------|---------|
| Build backend | Hatchling | setuptools | setuptools requires more config, setup.py is legacy, hatchling is simpler for pure Python |
| Build backend | Hatchling | Poetry | Poetry manages environments too (overlaps with conda); non-standard lock file; overkill for a library |
| Formatter/linter | ruff | black + flake8 + isort | ruff replaces all three, 100x faster, single config |
| Test runner | pytest | unittest | pytest is the scientific Python standard; better fixtures, parametrize, markers |
| Doc theme | sphinx-book-theme | furo | sphinx-book-theme matches dbrane-tools convention; both are good |
| Notebook integration | myst-nb | nbsphinx | myst-nb is the actively maintained successor in the Executable Books ecosystem |
| Property testing | hypothesis | custom fuzzing | hypothesis has better shrinking, reproducibility, scientific Python integration |
## Installation
# Core (no CYTools dependency)
# With FRST support (requires CYTools accessible)
# Development
# Or for development from source
## Sources
- [Python Packaging User Guide - pyproject.toml](https://packaging.python.org/en/latest/guides/writing-pyproject-toml/) - HIGH confidence
- [PyOpenSci - Python Package Guide](https://www.pyopensci.org/python-package-guide/tutorials/pyproject-toml.html) - HIGH confidence
- [SciPy 1.17.0 - differential_evolution](https://docs.scipy.org/doc/scipy/reference/generated/scipy.optimize.differential_evolution.html) - HIGH confidence, `integrality` parameter verified
- [SciPy 1.17.0 - basinhopping](https://docs.scipy.org/doc/scipy/reference/generated/scipy.optimize.basinhopping.html) - HIGH confidence
- [SciPy 1.17.0 - dual_annealing](https://docs.scipy.org/doc/scipy/reference/generated/scipy.optimize.dual_annealing.html) - HIGH confidence
- dbrane-tools reference project at `/Users/elijahsheridan/Research/string/cytools_code/dbrane-tools/` - HIGH confidence (direct inspection)
- Installed package versions verified via `pip show` in cytools conda env - HIGH confidence
<!-- GSD:stack-end -->

<!-- GSD:conventions-start source:CONVENTIONS.md -->
## Conventions

Conventions not yet established. Will populate as patterns emerge during development.
<!-- GSD:conventions-end -->

<!-- GSD:architecture-start source:ARCHITECTURE.md -->
## Architecture

Architecture not yet mapped. Follow existing patterns found in the codebase.
<!-- GSD:architecture-end -->

<!-- GSD:skills-start source:skills/ -->
## Project Skills

No project skills found. Add skills to any of: `.claude/skills/`, `.agents/skills/`, `.cursor/skills/`, or `.github/skills/` with a `SKILL.md` index file.
<!-- GSD:skills-end -->

<!-- GSD:workflow-start source:GSD defaults -->
## GSD Workflow Enforcement

Before using Edit, Write, or other file-changing tools, start work through a GSD command so planning artifacts and execution context stay in sync.

Use these entry points:
- `/gsd-quick` for small fixes, doc updates, and ad-hoc tasks
- `/gsd-debug` for investigation and bug fixing
- `/gsd-execute-phase` for planned phase work

Do not make direct repo edits outside a GSD workflow unless the user explicitly asks to bypass it.
<!-- GSD:workflow-end -->



<!-- GSD:profile-start -->
## Developer Profile

> Profile not yet configured. Run `/gsd-profile-user` to generate your developer profile.
> This section is managed by `generate-claude-profile` -- do not edit manually.
<!-- GSD:profile-end -->

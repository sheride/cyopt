# Technology Stack

**Project:** cyopt
**Researched:** 2026-04-11

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

Use **flat layout** (not src layout). Rationale: dbrane-tools uses flat layout; this is a small focused package; src layout adds complexity without benefit for conda-env-installed scientific packages.

```
cyopt/
  pyproject.toml
  LICENSE
  README.md
  cyopt/
    __init__.py
    _version.py
    base.py              # DiscreteOptimizer ABC
    ga.py                # GeneticAlgorithm
    random_sample.py     # RandomSample
    greedy.py            # GreedyWalk
    best_first.py        # BestFirstSearch
    basin_hopping.py     # BasinHopping
    diff_evolution.py    # DifferentialEvolution
    mcmc.py              # MCMC
    simulated_annealing.py  # SimulatedAnnealing
    utils.py             # Shared utilities
    frst/                # CYTools-dependent layer
      __init__.py
      polytope_ext.py    # Monkey-patch methods
      dna.py             # DNA encoding/decoding
      wrappers.py        # FRST-specific optimizer wrappers
  tests/
    __init__.py
    test_ga.py
    test_random_sample.py
    ...
    test_frst/           # Only runs if CYTools available
      __init__.py
      conftest.py        # Skip markers for CYTools
      test_dna.py
      ...
  documentation/
    Makefile
    source/
      conf.py
      index.rst
      ...
  notebooks/
    tutorial_basic.ipynb
    tutorial_frst.ipynb
```

## Optional Dependency Pattern

### pyproject.toml structure

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "cyopt"
version = "0.1.0"
description = "Discrete optimization toolkit with FRST optimization support"
requires-python = ">=3.10"
license = "MIT"
dependencies = [
    "numpy>=1.24",
    "scipy>=1.10",
    "tqdm>=4.60",
]

[project.optional-dependencies]
frst = ["cytools"]  # Heavy optional dep
dev = [
    "pytest>=8.0",
    "pytest-cov",
    "hypothesis",
    "ruff",
]
docs = [
    "sphinx>=7.0",
    "sphinx-book-theme>=1.0",
    "myst-nb>=1.0",
    "sphinx-copybutton>=0.5",
    "sphinx-autodoc-typehints>=3.0",
    "sphinx-togglebutton>=0.3",
    "sphinx-design>=0.5",
]

[tool.ruff]
line-length = 88
target-version = "py310"

[tool.ruff.lint]
select = ["E", "F", "I", "W"]

[tool.pytest.ini_options]
testpaths = ["tests"]
markers = [
    "frst: requires CYTools (deselect with '-m \"not frst\"')",
]
```

### Import guard pattern for CYTools

```python
# cyopt/frst/__init__.py
try:
    import cytools
    HAS_CYTOOLS = True
except ImportError:
    HAS_CYTOOLS = False

def require_cytools():
    if not HAS_CYTOOLS:
        raise ImportError(
            "CYTools is required for FRST optimization. "
            "Install with: pip install cyopt[frst] or conda install cytools"
        )
```

### Test skip pattern

```python
# tests/test_frst/conftest.py
import pytest

try:
    import cytools
    HAS_CYTOOLS = True
except ImportError:
    HAS_CYTOOLS = False

pytestmark = pytest.mark.frst

def pytest_collection_modifyitems(config, items):
    if not HAS_CYTOOLS:
        skip_frst = pytest.mark.skip(reason="CYTools not installed")
        for item in items:
            if "frst" in item.keywords:
                item.add_marker(skip_frst)
```

## SciPy Integration Strategy

### What to wrap vs. reimplement

The old code reaches into scipy private internals (`scipy.optimize._basinhopping`, `scipy.optimize._differentialevolution`). **Do not do this.** Private APIs break between versions.

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

Use the modern `numpy.random.Generator` API (not legacy `numpy.random.RandomState`):

```python
# Good: modern API
rng = np.random.default_rng(seed)
rng.integers(low, high, size=n)

# Bad: legacy API (old code uses this via scipy internals)
rng = np.random.RandomState(seed)
```

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

```bash
# Core (no CYTools dependency)
pip install cyopt

# With FRST support (requires CYTools accessible)
pip install cyopt[frst]

# Development
pip install cyopt[dev,docs]

# Or for development from source
pip install -e ".[dev,docs]"
```

## Sources

- [Python Packaging User Guide - pyproject.toml](https://packaging.python.org/en/latest/guides/writing-pyproject-toml/) - HIGH confidence
- [PyOpenSci - Python Package Guide](https://www.pyopensci.org/python-package-guide/tutorials/pyproject-toml.html) - HIGH confidence
- [SciPy 1.17.0 - differential_evolution](https://docs.scipy.org/doc/scipy/reference/generated/scipy.optimize.differential_evolution.html) - HIGH confidence, `integrality` parameter verified
- [SciPy 1.17.0 - basinhopping](https://docs.scipy.org/doc/scipy/reference/generated/scipy.optimize.basinhopping.html) - HIGH confidence
- [SciPy 1.17.0 - dual_annealing](https://docs.scipy.org/doc/scipy/reference/generated/scipy.optimize.dual_annealing.html) - HIGH confidence
- dbrane-tools reference project at `/Users/elijahsheridan/Research/string/cytools_code/dbrane-tools/` - HIGH confidence (direct inspection)
- Installed package versions verified via `pip show` in cytools conda env - HIGH confidence

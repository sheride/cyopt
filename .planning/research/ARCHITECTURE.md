# Architecture Patterns

**Domain:** Discrete optimization library with FRST specialization
**Researched:** 2026-04-11

## Recommended Architecture

Two-layer design with strict dependency boundary:

```
┌─────────────────────────────────────────────┐
│  User Code                                  │
│  (imports cyopt or cyopt.frst)              │
├─────────────────────────────────────────────┤
│  Layer 2: cyopt.frst (optional)             │
│  ┌───────────┬──────────┬─────────────────┐ │
│  │ polytope  │ dna      │ wrappers        │ │
│  │ _ext.py   │ .py      │ .py             │ │
│  │ (monkey-  │ (encode/ │ (FRST-specific  │ │
│  │  patch)   │  decode) │  optimizer      │ │
│  │           │          │  configs)       │ │
│  └───────────┴──────────┴─────────────────┘ │
│  depends on: cyopt core + CYTools           │
├─────────────────────────────────────────────┤
│  Layer 1: cyopt core (no CYTools)           │
│  ┌──────────┬───────────────────────────┐   │
│  │ base.py  │ Optimizer implementations │   │
│  │ (ABC +   │ ga.py, random_sample.py,  │   │
│  │  Result) │ greedy.py, mcmc.py, ...   │   │
│  └──────────┴───────────────────────────┘   │
│  depends on: numpy, scipy, tqdm             │
├─────────────────────────────────────────────┤
│  NumPy / SciPy / tqdm                       │
└─────────────────────────────────────────────┘
```

### Component Boundaries

| Component | Responsibility | Communicates With |
|-----------|---------------|-------------------|
| `cyopt.base` | ABC, Result dataclass, type definitions | All optimizers import from here |
| `cyopt.ga` | Genetic algorithm (selection, crossover, mutation, survival) | `base` only |
| `cyopt.random_sample` | Random sampling baseline | `base` only |
| `cyopt.greedy` | Greedy walk with configurable neighbors | `base` only |
| `cyopt.best_first` | Priority-queue best-first search | `base` only |
| `cyopt.basin_hopping` | Basin hopping on discrete space | `base` only |
| `cyopt.diff_evolution` | Wrapper around scipy DE with integrality | `base`, scipy |
| `cyopt.mcmc` | Metropolis-Hastings on integer tuples | `base` only |
| `cyopt.simulated_annealing` | SA with configurable schedule | `base` only |
| `cyopt.frst.polytope_ext` | Monkey-patch `Polytope` with prep/DNA methods | CYTools `Polytope` |
| `cyopt.frst.dna` | Encode/decode triangulations as integer tuples | CYTools internals |
| `cyopt.frst.wrappers` | Pre-configured optimizer factories for FRST | `base` optimizers + `dna` |

### Data Flow

**Generic optimization:**
```
User defines: fitness_fn(tuple[int,...]) -> float
User defines: bounds = [(0, n1), (0, n2), ...]
User creates: optimizer = GA(fitness_fn, bounds, **hyperparams)
User calls:   result = optimizer.optimize()
Result has:   result.x (best tuple), result.fun (best score), result.nfev, result.history
```

**FRST optimization:**
```
User has:     polytope (CYTools Polytope object)
User calls:   polytope.prep_for_optimizers()  # monkey-patched method
              This computes: 2-face triangulations, interesting faces, bounds
User defines: fitness_fn(CalabiYau) -> float  # e.g., lambda cy: cy.h11()
User creates: optimizer = FRSTGeneticAlgorithm(polytope, fitness_fn, **hyperparams)
              Internally: wraps fitness_fn to do dna -> triangulation -> CY -> score
User calls:   result = optimizer.optimize()
Result has:   result.x (DNA tuple), result.fun (best score), result.triangulation
```

## Patterns to Follow

### Pattern 1: Strategy Pattern for GA Components

Selection, crossover, mutation, and survival are interchangeable strategies:

```python
from abc import ABC, abstractmethod
import numpy as np

class SelectionStrategy(ABC):
    @abstractmethod
    def select(self, population: np.ndarray, fitness: np.ndarray,
               n: int, rng: np.random.Generator) -> np.ndarray: ...

class TournamentSelection(SelectionStrategy):
    def __init__(self, tournament_size: int = 3):
        self.tournament_size = tournament_size

    def select(self, population, fitness, n, rng):
        ...
```

### Pattern 2: Result as Frozen Dataclass

```python
from dataclasses import dataclass, field
from typing import Any

@dataclass(frozen=True)
class OptimizeResult:
    x: tuple[int, ...]          # Best solution
    fun: float                  # Best objective value
    nfev: int                   # Number of function evaluations
    niter: int                  # Number of iterations/generations
    success: bool               # Whether convergence criteria met
    message: str                # Termination reason
    history: list[float] = field(default_factory=list)  # Best-so-far per iteration
    metadata: dict[str, Any] = field(default_factory=dict)
```

### Pattern 3: Lazy CYTools Import

```python
# In cyopt/frst/__init__.py
def _check_cytools():
    try:
        import cytools
        return cytools
    except ImportError:
        raise ImportError(
            "CYTools required for FRST optimization. "
            "Install it or use cyopt core optimizers directly."
        )

# All frst module functions call _check_cytools() at function level, not module level
# This means `import cyopt` never fails even without CYTools
```

### Pattern 4: Configurable Neighbor Function

```python
from typing import Protocol

class NeighborFn(Protocol):
    def __call__(self, x: tuple[int, ...], bounds: list[tuple[int, int]],
                 rng: np.random.Generator) -> tuple[int, ...]: ...

def hamming_1_neighbor(x, bounds, rng):
    """Change exactly one position by +/- 1."""
    pos = rng.integers(len(x))
    delta = rng.choice([-1, 1])
    new = list(x)
    new[pos] = max(bounds[pos][0], min(bounds[pos][1], new[pos] + delta))
    return tuple(new)
```

## Anti-Patterns to Avoid

### Anti-Pattern 1: Accessing SciPy Private APIs
**What:** Importing `scipy.optimize._basinhopping` or `scipy.optimize._differentialevolution`
**Why bad:** Private APIs change without notice between scipy versions. The old code does this and is now broken.
**Instead:** Use only public API (`scipy.optimize.differential_evolution` with `integrality`), or reimplement the algorithm for discrete spaces.

### Anti-Pattern 2: Tight CYTools Coupling in Core
**What:** Importing CYTools in any file under `cyopt/` (excluding `cyopt/frst/`)
**Why bad:** Makes the entire package unusable without CYTools; prevents use as a general discrete optimization library.
**Instead:** Strict layer boundary. Core optimizers know nothing about polytopes or triangulations.

### Anti-Pattern 3: God Class Optimizer
**What:** Single class with all optimizer logic and mode switches.
**Why bad:** The old `triang_optimizer.py` is 1500+ lines in one file. Impossible to test, extend, or understand.
**Instead:** One file per optimizer, shared ABC, composition over inheritance for shared behaviors.

### Anti-Pattern 4: Mutable Default Hyperparameters
**What:** `def __init__(self, hyperparams={})` with shared mutable default.
**Why bad:** Classic Python bug; shared state between instances.
**Instead:** Use `None` default + create fresh dict inside, or use dataclasses for hyperparams.

## Scalability Considerations

| Concern | Small polytopes (h11<10) | Medium (h11~50) | Large (h11>100) |
|---------|--------------------------|------------------|------------------|
| DNA length | ~10-50 positions | ~100-1000 positions | ~1000+ positions |
| Fitness eval cost | <1s per eval | 1-10s per eval | 10-100s per eval |
| Population size | 50-200 | 100-500 | 100-500 (limited by eval cost) |
| Parallelism | Not needed | Helpful | Essential |
| Strategy | Any optimizer works | GA, DE preferred | GA with parallel eval, early stopping |

## Sources

- Old code structure at `/Users/elijahsheridan/Downloads/triang_optimizer.py` - direct inspection
- dbrane-tools project structure - direct inspection
- SciPy 1.17.0 docs for `integrality` parameter - HIGH confidence

# cyopt

*Elijah Sheridan, [Andreas Schachner](https://github.com/AndreasSchachner), and [Nate MacFadden](https://github.com/natemacfadden), Liam McAllister Group, Cornell*

Discrete optimization toolkit for bounded integer-tuple search spaces, with a focus on FRST optimization of Calabi-Yau hypersurfaces via [CYTools](https://cy.tools).

**Paper:** *[The DNA of Calabi-Yau Hypersurfaces](https://onlinelibrary.wiley.com/doi/full/10.1002/prop.70060)* (journal version; arXiv preprint [PDF](arxiv_paper.pdf))

## Features

- **8 optimizers:** GA, RandomSample, GreedyWalk, BestFirstSearch, BasinHopping, DifferentialEvolution, MCMC, SimulatedAnnealing
- **Callback system** with early stopping support
- **Checkpoint/resume** for long-running optimizations
- **Optional CYTools integration** for FRST optimization via DNA encoding

## Installation

Core package (no CYTools dependency):

```bash
pip install cyopt
```

With FRST support (requires CYTools):

```bash
pip install cyopt[frst]
```

For development:

```bash
git clone https://github.com/sheride/cyopt.git
cd cyopt
pip install -e ".[dev,docs]"
```

## Quickstart

```python
from cyopt import GA, TupleSpace

def objective(x):
    return sum((xi - 3) ** 2 for xi in x)

bounds = [(0, 9)] * 3
ga = GA(objective, space=TupleSpace(bounds), seed=42)
result = ga.run(100)
print(f"Best: {result.best_solution} → {result.best_value}")
```

## Benchmarks

cyopt reproduces the FRST-optimization study of the companion paper
(arXiv:2405.08871) and extends it. Two pre-run notebooks contain the full
analysis on the paper's $h^{1,1}=23$ reference polytope (150 seeds, identical
paired seeding, measured in *unique objective evaluations*):

- [`notebooks/frst_optimization.ipynb`](notebooks/frst_optimization.ipynb) —
  reproduces the paper's Figs 2–5: a Genetic Algorithm reaches the optimum far
  more efficiently than Markov Chain Monte Carlo or Simulated Annealing.
- [`notebooks/flip_graph_benchmark.ipynb`](notebooks/flip_graph_benchmark.ipynb) —
  works on a graph whose nodes are DNAs and whose edges connect DNAs differing
  in one entry (one 2-face's triangulation). `FRSTFlipGraphSpace` restricts
  those edges to a *single bistellar flip* of that face's triangulation — rather
  than a swap to any of its other triangulations — which leaves each DNA with
  ~14 neighbors on average instead of 32. The notebook tests whether that
  restriction speeds up `BestFirstSearch`. It **does not** on this polytope:
  flip-restricted search reaches mean $\log_{10}(V) = 6.69$ vs $6.73$ without
  the restriction (global max $\approx 6.91$), and the Genetic Algorithm on the
  unrestricted graph beats both — an empirical falsification of the "fewer,
  more natural moves ⇒ faster search" prior (caveat: single polytope).

Figures ship pre-computed; reproducing them from scratch is CYTools-backed and
multi-hour (see each notebook's "Reproducing this notebook" section).

## Documentation

Build the Sphinx docs locally:

```bash
cd documentation
make html
open build/html/index.html
```

Example notebooks in `notebooks/`.

## Citation

If you use cyopt in your research, please cite:

```bibtex
@article{https://doi.org/10.1002/prop.70060,
    author = {MacFadden, Nate and Schachner, Andreas and Sheridan, Elijah},
    title = {The DNA of Calabi–Yau Hypersurfaces},
    journal = {Fortschritte der Physik},
    volume = {74},
    number = {2},
    pages = {e70060},
    keywords = {Batyrev's Construction, Calabi-Yau Manifold, Genetic Algorithms, Kreuzer-Skarke Database, Machine Learning, Optimization, String Theory},
    doi = {https://doi.org/10.1002/prop.70060},
    url = {https://onlinelibrary.wiley.com/doi/abs/10.1002/prop.70060},
    eprint = {https://onlinelibrary.wiley.com/doi/pdf/10.1002/prop.70060},
    year = {2026}
}
```

## Disclaimer

This package was developed using [Claude Code](https://claude.ai/claude-code) (Anthropic's AI coding assistant), with human direction on physics, design decisions, and correctness validation. Development was managed with the [Get Shit Done (GSD)](https://github.com/atrisdotai/get-shit-done) workflow system for Claude Code, which provides phase-based planning, automated code review, verification loops, and structured execution.

## License

GNU General Public License v3 or later (GPL-3.0-or-later). See [LICENSE](LICENSE).

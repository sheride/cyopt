# cyopt

*Elijah Sheridan, [Andreas Schachner](https://github.com/AndreasSchachner), and [Nate MacFadden](https://github.com/natemacfadden), Liam McAllister Group, Cornell*

Discrete optimization toolkit for bounded integer-tuple search spaces, with a focus on FRST optimization of Calabi-Yau hypersurfaces via [CYTools](https://cy.tools).

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
git clone https://github.com/elijahsheridan/cyopt.git
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
@article{MacFadden:2024him,
    author = "MacFadden, Nate and Schachner, Andreas and Sheridan, Elijah",
    title = "{The DNA of Calabi-Yau Hypersurfaces}",
    eprint = "2405.08871",
    archivePrefix = "arXiv",
    primaryClass = "hep-th",
    reportNumber = "LMU-ASC 06/24",
    month = "5",
    year = "2024"
}
```

## Disclaimer

This package was developed using [Claude Code](https://claude.ai/claude-code) (Anthropic's AI coding assistant), with human direction on physics, design decisions, and correctness validation. Development was managed with the [Get Shit Done (GSD)](https://github.com/atrisdotai/get-shit-done) workflow system for Claude Code, which provides phase-based planning, automated code review, verification loops, and structured execution.

## License

GNU General Public License v3 or later (GPL-3.0-or-later). See [LICENSE](LICENSE).

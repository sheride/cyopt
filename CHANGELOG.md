# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.1.0] - 2026-05-06

### Added
- `FRSTFlipGraphSpace` - lazy CYTools-backed flip-graph search space; usable as `space=` for any of the 8 generic optimizers (GRAPH-01, GRAPH-02, GRAPH-03).
- `documentation/source/tutorials/flip_graph_benchmark.ipynb` - pre-run tutorial reproducing arXiv:2405.08871 Figs 2/4/5 with flip-graph vs Hamming-graph BestFirstSearch comparison on the h11=23 polytope (DOC-05).
- `data/precompute_flip_distances.py` and `data/precompute_fig_caches.py` - reusable precompute scripts for flip-graph benchmark figures.
- GitHub Actions release workflow (`.github/workflows/release.yml`) with PyPI trusted publishing (OIDC).
- `CONTRIBUTING.md` with maintainer release recipe.

### Changed
- Upgraded `pyproject.toml` license metadata from deprecated `{text = "MIT"}` to PEP 639 SPDX `"GPL-3.0-or-later"`.
- Added co-authors Andreas Schachner and Nate MacFadden to package metadata and README.

### Fixed
- Repository URLs in `pyproject.toml` and `README.md` corrected from `github.com/elijahsheridan/cyopt` to `github.com/sheride/cyopt`.
- Per-config caching of flip-neighbor lists in MCMC step_fn (perf fix).

## [0.1.0] - 2026-04-23

Internal milestone - never published to PyPI. v1.0 MVP shipped privately.

### Added
- 8 discrete optimizers (GA, RandomSample, GreedyWalk, BestFirstSearch, BasinHopping, DifferentialEvolution, MCMC, SimulatedAnnealing).
- `SearchSpace` abstraction (`TupleSpace`, `GraphSpace`).
- FRST wrapper layer for CYTools polytopes (opt-in via `[frst]` extras).
- Sphinx documentation with 3 tutorial notebooks.
- Checkpoint v2 with `space_kind`+`space_data` schema.

[unreleased]: https://github.com/sheride/cyopt/compare/v1.1.0...HEAD
[1.1.0]: https://github.com/sheride/cyopt/compare/v0.1.0...v1.1.0

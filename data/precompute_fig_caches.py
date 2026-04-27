"""Precompute Fig 4 / Fig 5 optimizer curves for the flip-graph benchmark tutorial.

Run ONE configuration per invocation, write its result to a .npz cache file
under ``data/``. The notebook then just loads these caches and plots — keeps
the notebook cheap to (re-)execute and makes long compute resumable.

Usage:
    conda run -n cytools python data/precompute_fig_caches.py \\
        --config "BFS (flip)"

Available --config values:
    "GA (Hamming)"          → data/fig4_ga_hamming.npz
    "BFS (Hamming)"         → data/fig4_bfs_hamming.npz
    "BFS (flip)"            → data/fig4_bfs_flip.npz
    "GreedyWalk (flip)"     → data/fig4_greedywalk_flip.npz
    "MCMC (flip)"           → data/fig4_mcmc_flip.npz
    "GA Fig5"               → data/fig5_ga_hamming.npz   (population schedule)

Notes
-----
- ``MCMC (flip)`` uses a CUSTOM ``step_fn`` that draws a uniform-random valid
  flip-graph neighbor via ``flip_space.neighbors(dna)``. cyopt's default MCMC
  step_fn requires ``space.bounds`` and proposes Hamming-1 perturbations,
  which is not flip-graph-aware. We pass our own to make ``MCMC (flip)`` an
  honest flip-graph experiment.
- ``SA (flip)`` is intentionally NOT included. cyopt's
  ``SimulatedAnnealing._step`` plus a ``run(1)``-in-a-loop driver leads to
  cache saturation in a small Hamming-1 neighborhood after ~200 unique
  evaluations, after which the unique-eval counter never increments. The
  reference notebook ``frst_optimization.ipynb`` cell 17 also commented out
  SA. See 07-02-SUMMARY.md for the full diagnosis.
- All caches are build artifacts: they are excluded from the repo via
  ``.gitignore``. End users who never re-execute the notebook see the
  cached output cells; users who do re-execute pay this compute cost on
  their machine.
"""
from __future__ import annotations

import argparse
import os
import sys
import time

import numpy as np
from tqdm import tqdm

sys.path.insert(0, ".")
from cyopt.frst import patch_polytope

patch_polytope()

from cyopt import (
    BestFirstSearch,
    FRSTFlipGraphSpace,
    GA,
    GreedyWalk,
    MCMC,
    TupleSpace,
)
from cytools import Polytope
from cytools.triangulation import Triangulation


# ---------------------------------------------------------------------------
# Setup -- shared by every config

def build_polytope_and_lookups():
    vertices = np.array(
        [
            [1, 0, 0, 0, 0, 2, -2, -1, 0, 1],
            [0, 1, 0, 0, 0, 2, -1, -2, 1, 0],
            [0, 0, 1, -1, 1, -1, 0, 2, 0, -2],
            [0, 0, 0, 0, 2, -2, 2, 2, -2, -2],
        ]
    ).T
    poly = Polytope(vertices)

    FACE_TRIANGS_PATH = "data/h11_23_face_triangs.npz"
    if os.path.exists(FACE_TRIANGS_PATH):
        ft_data = np.load(FACE_TRIANGS_PATH)
        n_faces = int(ft_data["n_faces"])
        n_per_face = ft_data["n_triangs_per_face"]
        face_triangs = []
        for i in range(n_faces):
            labels = tuple(ft_data[f"f{i}_labels"])
            face_ts = []
            for j in range(n_per_face[i]):
                simps = ft_data[f"f{i}_t{j}_simplices"]
                t = Triangulation(
                    poly, labels, simplices=simps, check_input_simplices=False
                )
                face_ts.append(t)
            face_triangs.append(face_ts)
        poly.prep_for_optimizers(face_triangs=face_triangs)
        print(f"Loaded cached face_triangs from {FACE_TRIANGS_PATH}")
    else:
        print("No cached face_triangs found — computing fresh (slower).")
        poly.prep_for_optimizers()

    bounds = poly._cyopt_bounds
    print(f"Bounds: {bounds}")

    vol_data = np.load("data/h11_23_volumes.npz")
    dna_array = vol_data["dna_array"]
    log10_volumes = vol_data["volumes"]
    volume_lookup = {
        tuple(int(x) for x in dna_array[i]): float(log10_volumes[i])
        for i in range(len(dna_array))
    }
    print(
        f"Loaded volume_lookup with {len(volume_lookup):,} entries; "
        f"log10(V) range [{log10_volumes.min():.4f}, {log10_volumes.max():.4f}]"
    )
    return poly, bounds, volume_lookup


def make_fitness_closures(volume_lookup):
    def target_lookup(dna):
        key = tuple(int(x) for x in dna)
        return volume_lookup.get(key, -1e6)

    def lookup_fitness_simple(dna):
        key = tuple(int(x) for x in dna)
        if key in volume_lookup:
            return -volume_lookup[key]
        return 1e6

    return target_lookup, lookup_fitness_simple


# ---------------------------------------------------------------------------
# Fig 4: per-seed curve up to MAX_UNIQUE_EVALS

def run_tracking_by_unique_evals(opt, max_unique_evals, safety_steps=200_000):
    """Mirror of the notebook driver. Returns (curve, hit_safety_cap)."""
    curve = []
    n_steps = 0
    while opt._n_evaluations < max_unique_evals and n_steps < safety_steps:
        opt.run(1)
        n_steps += 1
        best_target = -opt._best_value
        while len(curve) < min(opt._n_evaluations, max_unique_evals):
            curve.append(best_target)
    if curve:
        while len(curve) < max_unique_evals:
            curve.append(curve[-1])
    return np.array(curve[:max_unique_evals]), n_steps >= safety_steps


def make_flip_step_fn(flip_space):
    """Custom step_fn for MCMC (flip): pick a uniform-random valid flip neighbor."""

    def step_fn(dna, rng):
        nbrs = list(flip_space.neighbors(dna))
        if not nbrs:
            return dna
        return nbrs[int(rng.integers(len(nbrs)))]

    return step_fn


def fig4_configs(poly, bounds, target_lookup, lookup_fitness_simple):
    flip_space = FRSTFlipGraphSpace(poly)
    hamming_space = TupleSpace(bounds)
    flip_step_fn = make_flip_step_fn(flip_space)

    return {
        "GA (Hamming)": dict(
            slug="ga_hamming",
            cls=GA,
            space=hamming_space,
            kwargs=dict(
                target_fn=target_lookup,
                fitness="inverse_square",
                fitness_params={"mu": 7.87},
                population_size=10,
                selection={"method": "tournament", "k": 4},
                crossover="npoint",
                mutation_rate=0.05,
                mutation_k=1,
                elitism=1,
            ),
        ),
        "BFS (Hamming)": dict(
            slug="bfs_hamming",
            cls=BestFirstSearch,
            space=hamming_space,
            kwargs=dict(fitness_fn=lookup_fitness_simple, mode="backtrack"),
        ),
        "BFS (flip)": dict(
            slug="bfs_flip",
            cls=BestFirstSearch,
            space=flip_space,
            kwargs=dict(fitness_fn=lookup_fitness_simple, mode="backtrack"),
        ),
        "GreedyWalk (flip)": dict(
            slug="greedywalk_flip",
            cls=GreedyWalk,
            space=flip_space,
            kwargs=dict(fitness_fn=lookup_fitness_simple),
        ),
        "MCMC (flip)": dict(
            slug="mcmc_flip",
            cls=MCMC,
            space=flip_space,
            kwargs=dict(
                fitness_fn=lookup_fitness_simple,
                temperature=1.0,
                step_fn=flip_step_fn,  # flip-graph-aware
            ),
        ),
    }


def run_fig4_config(label, cfg, n_runs, max_evals):
    out_path = f"data/fig4_{cfg['slug']}.npz"
    print(f"\n=== {label} ({n_runs} seeds × {max_evals} unique evals) ===")
    print(f"Output: {out_path}")
    all_curves = []
    n_capped = 0
    t0 = time.time()
    for seed in tqdm(range(n_runs), desc=label, leave=True):
        opt = cfg["cls"](space=cfg["space"], seed=seed, **cfg["kwargs"])
        curve, capped = run_tracking_by_unique_evals(opt, max_evals)
        all_curves.append(curve)
        if capped:
            n_capped += 1
    elapsed = time.time() - t0
    runs = np.array(all_curves)  # (n_runs, max_evals)
    np.savez(
        out_path,
        runs=runs,
        n_runs=n_runs,
        max_unique_evals=max_evals,
        n_capped=n_capped,
    )
    print(
        f"Saved {runs.shape} to {out_path} | "
        f"capped={n_capped}/{n_runs} | "
        f"elapsed={elapsed:.1f}s ({elapsed/60:.1f}min)"
    )


# ---------------------------------------------------------------------------
# Fig 5: GA-Hamming with population schedule

def run_fig5_ga(target_lookup, hamming_space, n_runs, max_evals_fig5):
    out_path = "data/fig5_ga_hamming.npz"
    print(f"\n=== GA Fig5 ({n_runs} seeds × ≤{max_evals_fig5} evals) ===")
    print(f"Output: {out_path}")

    # Fig 5 threshold (top-two log10(V) with tol=1e-3) is computed in the notebook;
    # we save evals_to_top_two per seed using the threshold the notebook uses,
    # but we need the threshold here. The simplest is to reproduce that threshold
    # from the volumes lookup we just loaded.
    vol_data = np.load("data/h11_23_volumes.npz")
    log10_volumes = vol_data["volumes"]
    sorted_unique = np.sort(np.unique(log10_volumes))[::-1]
    top_two = sorted_unique[:2]
    TOP_TWO_TOL = 1e-3
    threshold = float(top_two[1])
    print(
        f"Top-two log10(V): {top_two[0]:.4f}, {top_two[1]:.4f}; "
        f"threshold = {threshold:.4f}"
    )

    ga_evals = []
    not_reached = 0
    t0 = time.time()
    for seed in tqdm(range(n_runs), desc="GA Fig5", leave=True):
        ga = GA(
            target_fn=target_lookup,
            fitness="inverse_square",
            fitness_params={"mu": 7.87},
            space=hamming_space,
            population_size=10,
            selection={"method": "tournament", "k": 4},
            crossover="npoint",
            mutation_rate=0.05,
            mutation_k=1,
            elitism=1,
            seed=seed,
        )
        found_at = None
        while ga._n_evaluations < max_evals_fig5:
            ga.run(1)
            best_target = -ga._best_value
            if best_target >= threshold - TOP_TWO_TOL:
                found_at = ga._n_evaluations
                break

            n_evals = ga._n_evaluations
            if n_evals >= 4000 and ga._population_size < 200:
                ga._population_size = 200
                ga._mutation_rate = 0.2
                old_pop = ga._population
                old_fit = ga._fitness_values
                ga._population = np.zeros((200, old_pop.shape[1]), dtype=int)
                ga._fitness_values = np.full(200, 1e6)
                ga._population[: len(old_pop)] = old_pop
                ga._fitness_values[: len(old_fit)] = old_fit
                for i in range(len(old_pop), 200):
                    dna = ga._space.random(ga._rng)
                    ga._population[i] = dna
                    ga._fitness_values[i] = ga._evaluate(dna)
            elif n_evals >= 1000 and ga._population_size < 100:
                ga._population_size = 100
                ga._mutation_rate = 0.1
                old_pop = ga._population
                old_fit = ga._fitness_values
                ga._population = np.zeros((100, old_pop.shape[1]), dtype=int)
                ga._fitness_values = np.full(100, 1e6)
                ga._population[: len(old_pop)] = old_pop
                ga._fitness_values[: len(old_fit)] = old_fit
                for i in range(len(old_pop), 100):
                    dna = ga._space.random(ga._rng)
                    ga._population[i] = dna
                    ga._fitness_values[i] = ga._evaluate(dna)
        if found_at is not None:
            ga_evals.append(found_at)
        else:
            not_reached += 1
    elapsed = time.time() - t0
    arr = np.array(ga_evals, dtype=np.int64)
    np.savez(
        out_path,
        evals=arr,
        threshold=threshold,
        top_two=top_two,
        n_runs=n_runs,
        n_reached=len(arr),
        not_reached=not_reached,
        max_evals_fig5=max_evals_fig5,
    )
    print(
        f"Saved {arr.shape} evals-to-top-two | "
        f"reached={len(arr)}/{n_runs} | "
        f"elapsed={elapsed:.1f}s ({elapsed/60:.1f}min)"
    )


# ---------------------------------------------------------------------------
# Main

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--config", required=True)
    p.add_argument("--n_runs", type=int, default=150)
    p.add_argument("--max_evals", type=int, default=1000)
    p.add_argument("--max_evals_fig5", type=int, default=16000)
    args = p.parse_args()

    poly, bounds, volume_lookup = build_polytope_and_lookups()
    target_lookup, lookup_fitness_simple = make_fitness_closures(volume_lookup)
    fig4 = fig4_configs(poly, bounds, target_lookup, lookup_fitness_simple)

    if args.config == "GA Fig5":
        hamming_space = fig4["GA (Hamming)"]["space"]
        run_fig5_ga(target_lookup, hamming_space, args.n_runs, args.max_evals_fig5)
        return

    if args.config not in fig4:
        valid = ", ".join(repr(k) for k in [*fig4.keys(), "GA Fig5"])
        raise SystemExit(
            f"Unknown --config {args.config!r}. Valid: {valid}"
        )
    run_fig4_config(args.config, fig4[args.config], args.n_runs, args.max_evals)


if __name__ == "__main__":
    main()

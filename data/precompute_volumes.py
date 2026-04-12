"""Precompute CY volumes for all 331,776 DNA of the h11=23 polytope.

Run with: conda run -n cytools python data/precompute_volumes.py

Saves results to data/h11_23_volumes.npz containing:
  - dna_array: (N, 8) int array of valid DNA vectors
  - volumes: (N,) float array of log10(CY volume) values
  - all_dna: (331776, 8) int array of ALL DNA vectors
  - valid_mask: (331776,) bool array indicating which DNA produced valid FRSTs
"""

import itertools
import sys
import time

import numpy as np
from tqdm import tqdm

sys.path.insert(0, ".")

from cyopt.frst import patch_polytope

patch_polytope()

from cytools import Polytope

# Construct the h11=23 polytope from arXiv:2405.08871
vertices = np.array(
    [
        [1, 0, 0, 0, 0, 2, -2, -1, 0, 1],
        [0, 1, 0, 0, 0, 2, -1, -2, 1, 0],
        [0, 0, 1, -1, 1, -1, 0, 2, 0, -2],
        [0, 0, 0, 0, 2, -2, 2, 2, -2, -2],
    ]
).T
poly = Polytope(vertices)
poly.prep_for_optimizers()

bounds = poly._cyopt_bounds
print(f"Bounds: {bounds}")
ranges = [range(lo, hi + 1) for lo, hi in bounds]
total = 1
for lo, hi in bounds:
    total *= hi - lo + 1
print(f"Total DNA combinations: {total}")

# Enumerate all DNA and compute volumes
all_dna = np.zeros((total, len(bounds)), dtype=int)
volumes = np.full(total, np.nan)
valid_mask = np.zeros(total, dtype=bool)

t0 = time.time()
for idx, dna in enumerate(tqdm(itertools.product(*ranges), total=total, desc="Computing volumes")):
    dna_tuple = tuple(dna)
    all_dna[idx] = dna_tuple

    triang = poly.dna_to_frst(dna_tuple)
    if triang is None:
        continue

    try:
        cy = triang.get_cy()
        tip = cy.toric_kahler_cone().tip_of_stretched_cone(1)
        vol = cy.compute_cy_volume(tip)
        volumes[idx] = np.log10(vol)
        valid_mask[idx] = True
    except Exception as e:
        print(f"\nError at DNA {dna_tuple}: {e}")
        continue

elapsed = time.time() - t0
n_valid = valid_mask.sum()
print(f"\nCompleted in {elapsed:.1f}s")
print(f"Valid FRSTs: {n_valid} / {total} ({100*n_valid/total:.2f}%)")
print(f"Failed: {total - n_valid}")

# Extract valid DNA and volumes
valid_dna = all_dna[valid_mask]
valid_volumes = volumes[valid_mask]

print(f"log10(V) range: [{valid_volumes.min():.4f}, {valid_volumes.max():.4f}]")
print(f"log10(V) mean: {valid_volumes.mean():.4f}")

# Save
outpath = "data/h11_23_volumes.npz"
np.savez(
    outpath,
    dna_array=valid_dna,
    volumes=valid_volumes,
    all_dna=all_dna,
    valid_mask=valid_mask,
)
print(f"Saved to {outpath}")

"""Precompute CY volumes for all 331,776 DNA of the h11=23 polytope.

Run with: conda run -n cytools python data/precompute_volumes.py

Uses cached face triangulations from data/h11_23_face_triangs.npz for
reproducible DNA mappings. Falls back to computing face_triangs() fresh
if the cache is missing.

Saves results to data/h11_23_volumes.npz containing:
  - dna_array: (N, 8) int array of valid DNA vectors
  - volumes: (N,) float array of log10(CY volume) values
  - all_dna: (331776, 8) int array of ALL DNA vectors
  - valid_mask: (331776,) bool array indicating which DNA produced valid FRSTs
"""

import itertools
import os
import sys
import time

import numpy as np
from tqdm import tqdm

sys.path.insert(0, ".")

from cyopt.frst import patch_polytope

patch_polytope()

from cytools import Polytope
from cytools.triangulation import Triangulation

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

# Load cached face triangulations if available
FACE_TRIANGS_PATH = "data/h11_23_face_triangs.npz"
if os.path.exists(FACE_TRIANGS_PATH):
    print(f"Loading cached face triangulations from {FACE_TRIANGS_PATH}")
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
else:
    print("No cached face triangulations found, computing fresh...")
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
PROGRESS_FILE = "data/precompute_progress.txt"
CHECKPOINT_INTERVAL = 1000  # write progress every N DNA

for idx, dna in enumerate(itertools.product(*ranges)):
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
        pass

    if (idx + 1) % CHECKPOINT_INTERVAL == 0:
        elapsed_so_far = time.time() - t0
        rate = (idx + 1) / elapsed_so_far
        remaining = (total - idx - 1) / rate
        n_valid_so_far = valid_mask[:idx+1].sum()
        with open(PROGRESS_FILE, "w") as f:
            f.write(f"{idx+1}/{total} ({100*(idx+1)/total:.1f}%) | "
                    f"valid={n_valid_so_far} | "
                    f"rate={rate:.1f}/s | "
                    f"elapsed={elapsed_so_far:.0f}s | "
                    f"remaining={remaining:.0f}s ({remaining/60:.1f}min)\n")

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

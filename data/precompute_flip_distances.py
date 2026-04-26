"""Precompute flip distances from the optimum for the h11=23 polytope.

Run with: conda run -n cytools python data/precompute_flip_distances.py

Performs BFS over FRSTFlipGraphSpace starting from the lex-smallest DNA at
max log10(V) (= (3, 1, 0, 2, 2, 3, 0, 0) on h11=23, verified unique). Records
flip distance at first encounter for every visited DNA. Uses cached face
triangulations from data/h11_23_face_triangs.npz for reproducible
flip-emission ordering. Falls back to fresh face_triangs() if missing.

Saves results to data/h11_23_flip_distances.npz containing:
  - dnas: (N, 8) uint8 array of valid DNAs reached by BFS
  - flip_distances: (N,) uint8 array of flip distance at first visit
  - reference_dna: (8,) uint8 array of the BFS source DNA

Estimated wall-time: ~2.4 hours single-threaded on Apple Silicon (verified
2026-04-25 via 5-min partial-BFS probe yielding 38.8 unique-DNAs/sec).

Per CONTEXT D-10 the .npz output is a build artifact, NOT committed. End
users who never re-execute the notebook see the cached plots; users who
DO re-execute pay this ~2.4 hr cost on their machine.
"""

import os
import sys
import time
from collections import deque

import numpy as np
from tqdm import tqdm

sys.path.insert(0, ".")

from cyopt.frst import patch_polytope

patch_polytope()

from cyopt import FRSTFlipGraphSpace
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

# Load cached face triangulations if available (determinism anchor per
# RESEARCH Section 6 / Caveat: committed cache fixes flip-emission order
# so end-user re-runs are bit-reproducible).
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

# Reference DNA = lex-smallest among DNAs at max log10(V).
# On h11=23 the argmax is unique = (3, 1, 0, 2, 2, 3, 0, 0); the lex tie-break
# rule is documented for re-use on polytopes where ties exist.
VOLUMES_PATH = "data/h11_23_volumes.npz"
print(f"Loading volumes from {VOLUMES_PATH}")
vol_data = np.load(VOLUMES_PATH)
dna_array = vol_data["dna_array"]  # (331191, 8) int64
volumes = vol_data["volumes"]  # (331191,) float64
max_v = float(volumes.max())
max_mask = volumes == max_v
max_dnas = dna_array[max_mask]
# Lex-smallest tie-break (documented; on h11=23 there's only one)
order = np.lexsort(max_dnas.T[::-1])
reference_dna = tuple(int(x) for x in max_dnas[order[0]])
print(f"Reference DNA (lex-smallest at max log10(V)={max_v:.6f}): {reference_dna}")
print(f"  ({len(max_dnas)} DNA(s) tied at max; chose lex-smallest)")

space = FRSTFlipGraphSpace(poly)
print("FRSTFlipGraphSpace constructed (lazy; no upfront enumeration).")
n_total_valid = len(dna_array)
print(
    f"Target: BFS over connected component containing reference; "
    f"will report fraction of {n_total_valid} valid DNAs reached."
)

# Standard BFS: queue holds DNAs to expand; visited maps dna -> distance.
# Distance is recorded at first encounter (BFS guarantees shortest path).
visited: dict[tuple[int, ...], int] = {reference_dna: 0}
queue: deque[tuple[int, ...]] = deque([reference_dna])

PROGRESS_FILE = "data/precompute_progress_flip.txt"
PROGRESS_INTERVAL = 1000  # write progress every N visited
OUTPUT_PATH = "data/h11_23_flip_distances.npz"


def save_results(visited_dict, ref_dna, partial=False):
    items = sorted(visited_dict.items())  # deterministic order by DNA
    dnas_arr = np.array([k for k, _ in items], dtype=np.uint8)
    dists_arr = np.array([v for _, v in items], dtype=np.uint8)
    ref_arr = np.array(ref_dna, dtype=np.uint8)
    np.savez(
        OUTPUT_PATH,
        dnas=dnas_arr,
        flip_distances=dists_arr,
        reference_dna=ref_arr,
    )
    tag = " (PARTIAL)" if partial else ""
    print(f"Saved {len(items)} entries to {OUTPUT_PATH}{tag}")


t0 = time.time()
try:
    pbar = tqdm(total=n_total_valid, desc="BFS")
    pbar.update(1)  # reference DNA already visited
    while queue:
        current = queue.popleft()
        cur_dist = visited[current]
        for nbr in space.neighbors(current):
            nbr_t = tuple(int(x) for x in nbr)
            if nbr_t not in visited:
                visited[nbr_t] = cur_dist + 1
                queue.append(nbr_t)
                pbar.update(1)

                if len(visited) % PROGRESS_INTERVAL == 0:
                    elapsed = time.time() - t0
                    rate = len(visited) / elapsed
                    with open(PROGRESS_FILE, "w") as f:
                        f.write(
                            f"visited={len(visited)}/{n_total_valid} "
                            f"({100 * len(visited) / n_total_valid:.2f}%) | "
                            f"queue={len(queue)} | "
                            f"max_dist={cur_dist + 1} | "
                            f"rate={rate:.1f}/s | "
                            f"elapsed={elapsed:.0f}s\n"
                        )
    pbar.close()
except KeyboardInterrupt:
    pbar.close()
    print("\nKeyboardInterrupt -- saving partial results...")
    save_results(visited, reference_dna, partial=True)
    raise

elapsed = time.time() - t0
max_dist = max(visited.values())
print(f"\nBFS complete in {elapsed:.1f}s ({elapsed / 3600:.2f}h)")
print(
    f"Reached {len(visited)} / {n_total_valid} valid DNAs "
    f"({100 * len(visited) / n_total_valid:.2f}%)"
)
print(f"Max flip distance: {max_dist}")
if len(visited) < n_total_valid:
    print(
        f"WARNING: connected component does not cover all valid DNAs. "
        f"{n_total_valid - len(visited)} DNAs are in other components."
    )
    print(
        "Notebook Fig 2 should be titled 'Flip distance from optimum, "
        "restricted to the connected component containing the optimum'."
    )
save_results(visited, reference_dna, partial=False)

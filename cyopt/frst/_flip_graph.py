"""FRSTFlipGraphSpace: lazy flip-graph search space over FRST DNAs.

This module provides :class:`FRSTFlipGraphSpace`, a :class:`GraphSpace`
subclass whose ``neighbors(dna)`` lazily emits all DNAs reachable from
``dna`` by performing a single bistellar flip on a single 2-face,
filtered to those that extend to a globally valid FRST. It is the
coarsening of the Hamming-1 graph that respects the natural topology of
FRST space.
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import TYPE_CHECKING

import numpy as np

from cyopt.frst._encoding import _normalize_simplices
from cyopt.spaces._graph import GraphSpace
from cyopt.spaces._tuple import TupleSpace

if TYPE_CHECKING:
    from cytools import Polytope

    from cyopt.types import DNA


class FRSTFlipGraphSpace(GraphSpace):
    """A :class:`GraphSpace` over FRST DNAs whose neighbors are flip-related.

    Each call to :meth:`neighbors` lazily emits all DNAs reachable from
    ``dna`` by performing a single bistellar flip on a single 2-face,
    filtered to those that extend to a globally valid FRST. Construction
    performs zero upfront work -- no flip enumeration, no validity
    precomputation, no adjacency table. All flip detection happens at
    :meth:`neighbors` query time.

    Per-emission contract: every DNA yielded by :meth:`neighbors`
    differs from the input ``dna`` in exactly one coordinate (i.e., the
    flip-graph is a coarsening of the Hamming-1 graph), and satisfies
    ``polytope.dna_to_frst(emitted) is not None`` (the joint cone across
    all faces is solid).

    Parameters
    ----------
    polytope : Polytope
        A reflexive ``cytools.Polytope`` that has been prepped via
        ``polytope.prep_for_optimizers()``.

    Raises
    ------
    RuntimeError
        If ``polytope`` has not been prepped via ``prep_for_optimizers()``.

    Notes
    -----
    Per-face flip graphs may be asymmetric: a "hub" FRT on a face can
    have more flip neighbors than a "leaf" FRT, so the number of DNAs
    emitted by :meth:`neighbors` varies by current position in the
    search space.
    """

    def __init__(self, polytope: "Polytope") -> None:
        if not getattr(polytope, "_cyopt_prepped", False):
            raise RuntimeError(
                "FRSTFlipGraphSpace requires polytope.prep_for_optimizers() "
                "to have been called first."
            )
        self._poly = polytope
        # Reuse TupleSpace for random() sampling and bounds-shape
        # introspection. Construction performs zero upfront enumeration of
        # flips and zero precomputation of valid-DNA sets.
        self._tuple_space = TupleSpace(polytope._cyopt_bounds)

    @property
    def polytope(self) -> "Polytope":
        """The ambient polytope whose flip graph this space represents."""
        return self._poly

    @property
    def bounds(self):
        """Per-coordinate ``(lo, hi)`` bounds; same as the underlying TupleSpace."""
        return self._tuple_space.bounds

    @property
    def dim(self) -> int:
        """Number of DNA coordinates (= number of interesting 2-faces)."""
        return self._tuple_space.dim

    def random(self, rng: np.random.Generator) -> "DNA":
        """Draw a uniformly random valid DNA via bounded rejection sampling.

        Reuses :meth:`TupleSpace.random` and rejects until a DNA with
        ``polytope.dna_to_frst(dna) is not None`` is found. For typical
        polytopes the validity rate is high and rejection terminates
        quickly.

        Parameters
        ----------
        rng : numpy.random.Generator
            RNG used for reproducibility.

        Returns
        -------
        DNA
            A random valid DNA.

        Raises
        ------
        RuntimeError
            If no valid DNA is found in 1000 attempts; the polytope may
            have very few jointly-valid DNAs.
        """
        # TODO(perf): if rejection rate is pathological on real benchmark
        # polytopes (e.g., h11=23), switch to a per-face direct sampling path
        # that draws a random FRT per face from poly._cyopt_face_triangs.
        for _ in range(1000):
            dna = self._tuple_space.random(rng)
            if self._poly.dna_to_frst(dna) is not None:
                return dna
        raise RuntimeError(
            "FRSTFlipGraphSpace.random failed to find a valid DNA in 1000 "
            "attempts; polytope may have very few valid DNAs."
        )

    def neighbors(self, dna: "DNA") -> "Iterable[DNA]":
        """Yield DNAs reachable from ``dna`` by a single 2-face flip.

        Each emitted DNA differs from ``dna`` in exactly one coordinate
        (coarsening of the Hamming-1 graph) and extends to a valid FRST
        via the lazy joint-validity filter ``polytope.dna_to_frst is not
        None`` (GRAPH-02).

        This method is implemented as a generator -- iteration is truly
        lazy, with each flip computed on demand. The CYTools flip API
        (:meth:`cytools.Triangulation.neighbor_triangulations` aliased
        as ``neighbors``) is invoked per face on each query; no
        precomputed adjacency table is built.

        Parameters
        ----------
        dna : DNA
            Current DNA tuple (one int per interesting 2-face).

        Yields
        ------
        DNA
            Each neighbor differs from ``dna`` in exactly one coordinate
            and satisfies ``polytope.dna_to_frst(neighbor) is not None``.

        Notes
        -----
        Per-face flip graphs may be asymmetric ("hub topology" -- one
        central FRT with multiple neighbors, peripheral FRTs with one
        each). The number of yielded DNAs therefore varies depending on
        the current position; do not assume a constant out-degree.
        """
        poly = self._poly
        for i, face_idx in enumerate(poly._cyopt_interesting):
            face_ts = poly._cyopt_face_triangs[face_idx]
            face_simp_sets = poly._cyopt_face_simp_sets[face_idx]
            current = face_ts[dna[i]]
            # CYTools flip API. only_fine=True is REQUIRED for 2D fine
            # triangulations (without it, TOPCOM can raise IndexError:
            # vector). The _fine_neighbors_2d fast path is gated on this flag.
            for neigh in current.neighbors(only_fine=True):
                # Reverse lookup: find k such that face_ts[k] == neigh.
                # Use precomputed _cyopt_face_simp_sets (already built
                # by prep_for_optimizers).
                # Defensive try/except guards against future CYTools-version
                # drift returning a triangulation outside face_ts.
                neigh_set = _normalize_simplices(neigh.simplices())
                try:
                    k = face_simp_sets.index(neigh_set)
                except ValueError:
                    # cytools-version drift; skip silently.
                    continue
                if k == dna[i]:
                    # neighbors() should not return self, defensive guard.
                    continue
                candidate = dna[:i] + (k,) + dna[i + 1:]
                # Lazy validity filter (GRAPH-02): joint cone solidity
                # across all faces. dna_to_frst returns None for
                # non-solid combinations, which is stricter than per-face
                # grow_frt checks.
                if poly.dna_to_frst(candidate) is None:
                    continue
                yield candidate

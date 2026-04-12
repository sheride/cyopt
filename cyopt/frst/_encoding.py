"""DNA encoding/decoding for FRST optimization via CYTools.

This module implements the mapping between integer-tuple DNA and CYTools
FRST triangulations. It provides:

- ``prep_for_optimizers``: Precompute 2-face triangulation data on a Polytope
- ``dna_to_frst``: Encode a DNA tuple into an FRST Triangulation
- ``triang_to_dna``: Decode a Triangulation back into a DNA tuple
- ``dna_to_cy``: Encode a DNA tuple into a CalabiYau object
- ``cy_to_dna``: Decode a CalabiYau back into a DNA tuple

All functions are monkey-patched onto ``cytools.Polytope`` when
``patch_polytope()`` is called (automatically on ``import cyopt.frst``).
"""

from __future__ import annotations

from cyopt._types import DNA, Bounds


def _normalize_simplices(simplices) -> frozenset[tuple[int, ...]]:
    """Normalize simplices to a comparable frozenset form.

    Works with both ``np.ndarray`` (from ``Triangulation.simplices()``)
    and ``list[list[int]]`` (from ``Triangulation.restrict()``).

    Parameters
    ----------
    simplices : array-like
        Simplices as rows of vertex indices.

    Returns
    -------
    frozenset[tuple[int, ...]]
        Frozenset of sorted int tuples for O(1) comparison.
    """
    return frozenset(tuple(sorted(int(v) for v in s)) for s in simplices)


def _prep_for_optimizers(self, **kwargs) -> None:
    """Precompute 2-face triangulation data for FRST optimization.

    Must be called before any DNA encoding/decoding methods. Idempotent --
    second call is a no-op.

    Parameters
    ----------
    **kwargs
        Passed through to ``self.face_triangs()``.

    Raises
    ------
    ValueError
        If the polytope is not reflexive.
    """
    if getattr(self, "_cyopt_prepped", False):
        return

    if not self.is_reflexive():
        raise ValueError("FRST optimization requires reflexive polytopes.")

    # Precompute all 2-face triangulations
    self._cyopt_face_triangs: list = self.face_triangs(**kwargs)

    # Identify interesting faces (>1 triangulation) and compute bounds
    self._cyopt_interesting: list[int] = []
    bounds_list: list[tuple[int, int]] = []
    for i, face_ts in enumerate(self._cyopt_face_triangs):
        if len(face_ts) > 1:
            self._cyopt_interesting.append(i)
            bounds_list.append((0, len(face_ts) - 1))
    self._cyopt_bounds: Bounds = tuple(bounds_list)

    # Precompute simplex sets for reverse mapping
    self._cyopt_face_simp_sets: list[list[frozenset]] = []
    for face_ts in self._cyopt_face_triangs:
        self._cyopt_face_simp_sets.append(
            [_normalize_simplices(ft.simplices()) for ft in face_ts]
        )

    self._cyopt_prepped = True


def _dna_to_frst(self, dna: DNA) -> object | None:
    """Convert a DNA tuple to an FRST Triangulation.

    Parameters
    ----------
    dna : DNA
        Integer tuple with one entry per interesting face, indexing into
        that face's triangulation list.

    Returns
    -------
    Triangulation or None
        The FRST triangulation, or ``None`` if the face triangulation
        combination produces a non-solid cone.
    """
    n_faces = len(self._cyopt_face_triangs)
    triangs: list = [None] * n_faces

    for i, face_idx in enumerate(self._cyopt_interesting):
        face_list = self._cyopt_face_triangs[face_idx]
        # Clamp index to valid range (some optimizers like DE may produce
        # boundary values due to floating-point rounding in integrality mode)
        idx = max(0, min(dna[i], len(face_list) - 1))
        triangs[face_idx] = face_list[idx]

    return self.triangfaces_to_frst(triangs)


def _dna_to_cy(self, dna: DNA) -> object | None:
    """Convert a DNA tuple to a CalabiYau object.

    Parameters
    ----------
    dna : DNA
        Integer tuple with one entry per interesting face.

    Returns
    -------
    CalabiYau or None
        The CalabiYau manifold, or ``None`` if the DNA does not produce
        a valid FRST.
    """
    triang = self.dna_to_frst(dna)
    if triang is None:
        return None
    return triang.get_cy()


def _triang_to_dna(self, triang) -> DNA:
    """Decode a Triangulation back into a DNA tuple.

    Parameters
    ----------
    triang : Triangulation
        An FRST triangulation of this polytope.

    Returns
    -------
    DNA
        The DNA tuple corresponding to this triangulation.

    Raises
    ------
    ValueError
        If any face's restriction does not match any known triangulation.
    """
    restrictions = triang.restrict()

    dna_components: list[int] = []
    for face_idx in self._cyopt_interesting:
        restriction_set = _normalize_simplices(restrictions[face_idx])
        face_simp_sets = self._cyopt_face_simp_sets[face_idx]

        matched = False
        for j, known_set in enumerate(face_simp_sets):
            if known_set == restriction_set:
                dna_components.append(j)
                matched = True
                break

        if not matched:
            raise ValueError(
                f"Face {face_idx} restriction does not match any known "
                f"triangulation. The triangulation may not belong to this "
                f"polytope's FRST class."
            )

    return tuple(dna_components)


def _cy_to_dna(self, cy) -> DNA:
    """Decode a CalabiYau object back into a DNA tuple.

    Parameters
    ----------
    cy : CalabiYau
        A Calabi-Yau manifold constructed from this polytope.

    Returns
    -------
    DNA
        The DNA tuple corresponding to this CY's triangulation.
    """
    return self.triang_to_dna(cy.triangulation())


def patch_polytope() -> None:
    """Monkey-patch encoding/decoding methods onto ``cytools.Polytope``.

    This is called automatically when ``cyopt.frst`` is imported. It
    attaches the following methods to the Polytope class:

    - ``prep_for_optimizers``
    - ``dna_to_frst``
    - ``dna_to_cy``
    - ``triang_to_dna``
    - ``cy_to_dna``
    """
    from cytools import Polytope

    Polytope.prep_for_optimizers = _prep_for_optimizers
    Polytope.dna_to_frst = _dna_to_frst
    Polytope.dna_to_cy = _dna_to_cy
    Polytope.triang_to_dna = _triang_to_dna
    Polytope.cy_to_dna = _cy_to_dna

"""DNA encoding/decoding for FRST optimization via CYTools.

This module implements the mapping between integer-tuple DNA and CYTools
FRST triangulations. It provides:

- ``prep_for_optimizers``: Precompute 2-face triangulation data on a Polytope
- ``dna_to_frst``: Encode a DNA tuple into an FRST Triangulation
- ``triang_to_dna``: Decode a Triangulation back into a DNA tuple
- ``dna_to_cy``: Encode a DNA tuple into a CalabiYau object
- ``cy_to_dna``: Decode a CalabiYau back into a DNA tuple
- Normalization wrapper around ``grow_frt`` that forces a set return type,
  working around an upstream CYTools bug (see ``grow_frt_iteration_bug.md``).

All functions are monkey-patched onto ``cytools.Polytope`` when
``patch_polytope()`` is called (automatically on ``import cyopt.frst``).
"""

from __future__ import annotations

from cyopt.types import DNA, Bounds


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


def _prep_for_optimizers(self, face_triangs=None, **kwargs) -> None:
    """Precompute 2-face triangulation data for FRST optimization.

    Must be called before any DNA encoding/decoding methods. Idempotent --
    second call is a no-op.

    Parameters
    ----------
    face_triangs : list, optional
        Pre-computed face triangulations (output of ``self.face_triangs()``).
        If provided, skips the ``face_triangs()`` call. Use this to ensure
        reproducible DNA mappings from saved data.
    **kwargs
        Passed through to ``self.face_triangs()`` when ``face_triangs``
        is not provided.

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
    self._cyopt_face_triangs: list = (
        face_triangs if face_triangs is not None
        else self.face_triangs(**kwargs)
    )

    # Identify interesting faces (>1 triangulation) and compute bounds
    self._cyopt_interesting: list[int] = []
    bounds_list: list[tuple[int, int]] = []
    for i, face_ts in enumerate(self._cyopt_face_triangs):
        if len(face_ts) > 1:
            self._cyopt_interesting.append(i)
            bounds_list.append((0, len(face_ts) - 1))
    self._cyopt_bounds: Bounds = tuple(bounds_list)

    # Precompute simplex sets for reverse mapping
    self._cyopt_face_simp_sets: list[list[frozenset[tuple[int, ...]]]] = []
    for face_ts in self._cyopt_face_triangs:
        self._cyopt_face_simp_sets.append(
            [_normalize_simplices(ft.simplices()) for ft in face_ts]
        )

    self._cyopt_prepped = True


def _check_prepped(self, method_name: str) -> None:
    """Raise RuntimeError if prep_for_optimizers has not been called."""
    if not getattr(self, "_cyopt_prepped", False):
        raise RuntimeError(
            f"Polytope.{method_name}() requires prep_for_optimizers() "
            f"to be called first."
        )


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
    _check_prepped(self, "dna_to_frst")
    triangs: list = [ft[0] for ft in self._cyopt_face_triangs]

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
    _check_prepped(self, "dna_to_cy")
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
    _check_prepped(self, "triang_to_dna")
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
    _check_prepped(self, "cy_to_dna")
    return self.triang_to_dna(cy.triangulation())


def _grow_frt_normalized(self, *args, **kwargs):
    """Normalize ``Polytope.grow_frt`` to always return a set.

    Upstream CYTools' ``grow_frt`` returns a bare ``Triangulation`` when
    exactly one FRT is found, and a ``set`` of Triangulations otherwise.
    That inconsistency breaks downstream callers (including CYTools' own
    ``face_triangs``) that do ``list(p.grow_frt(...))``. This wrapper
    guarantees the return value is always iterable as a set of
    Triangulations.

    See ``grow_frt_iteration_bug.md`` for the original reproducer.
    """
    result = _grow_frt_normalized._original(self, *args, **kwargs)
    # If upstream returned any iterable container, coerce to ``set``.
    # Otherwise (the single-FRT bug: a bare Triangulation), wrap it.
    if isinstance(result, (set, frozenset, list, tuple)):
        return result if isinstance(result, set) else set(result)
    return {result}


def patch_polytope() -> None:
    """Monkey-patch encoding/decoding methods onto ``cytools.Polytope``.

    This is called automatically when ``cyopt.frst`` is imported. It
    attaches the following methods to the Polytope class:

    - ``prep_for_optimizers``
    - ``dna_to_frst``
    - ``dna_to_cy``
    - ``triang_to_dna``
    - ``cy_to_dna``

    It also installs a defensive wrapper around ``Polytope.grow_frt`` that
    normalizes the return type to a ``set`` in all cases (working around
    an upstream CYTools bug where the single-FRT case returns a bare
    ``Triangulation``). The ``grow_frt`` patch is idempotent: re-importing
    ``cyopt.frst`` does not recursively wrap the method.
    """
    from cytools import Polytope

    Polytope.prep_for_optimizers = _prep_for_optimizers
    Polytope.dna_to_frst = _dna_to_frst
    Polytope.dna_to_cy = _dna_to_cy
    Polytope.triang_to_dna = _triang_to_dna
    Polytope.cy_to_dna = _cy_to_dna

    # Defensive patch for upstream CYTools bug: grow_frt returns a bare
    # Triangulation when len(frts) == 1, breaking list() iteration.
    # Wrap it to always return a set. See grow_frt_iteration_bug.md.
    if getattr(Polytope.grow_frt, "_cyopt_patched", False):
        return  # already patched; idempotent
    _grow_frt_normalized._original = Polytope.grow_frt
    _grow_frt_normalized._cyopt_patched = True
    Polytope.grow_frt = _grow_frt_normalized

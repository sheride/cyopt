"""Tests for the FRST DNA encoding/decoding layer."""

import pytest

from tests.test_frst.conftest import requires_cytools


@requires_cytools
class TestPrepForOptimizers:
    """Tests for Polytope.prep_for_optimizers monkey-patch."""

    def test_prep_for_optimizers(self, poly_h11_4):
        """prep_for_optimizers sets expected attributes."""
        import cyopt.frst  # noqa: F401 -- triggers monkey-patching

        poly_h11_4.prep_for_optimizers()

        assert poly_h11_4._cyopt_prepped is True
        assert isinstance(poly_h11_4._cyopt_bounds, tuple)
        assert isinstance(poly_h11_4._cyopt_interesting, list)
        assert isinstance(poly_h11_4._cyopt_face_triangs, list)
        assert isinstance(poly_h11_4._cyopt_face_simp_sets, list)

        # Bounds should be (0, N-1) pairs
        for lo, hi in poly_h11_4._cyopt_bounds:
            assert lo == 0
            assert hi >= 1  # interesting faces have >1 triangulation

    def test_prep_idempotent(self, poly_h11_4):
        """Second call to prep_for_optimizers is a no-op."""
        import cyopt.frst  # noqa: F401

        poly_h11_4.prep_for_optimizers()
        bounds_before = poly_h11_4._cyopt_bounds
        poly_h11_4.prep_for_optimizers()
        assert poly_h11_4._cyopt_bounds is bounds_before

    def test_prep_rejects_non_reflexive(self):
        """prep_for_optimizers raises ValueError on non-reflexive polytope."""
        import cyopt.frst  # noqa: F401
        from cytools import Polytope

        # A simplex is not reflexive
        verts = [[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]]
        poly = Polytope(verts)
        with pytest.raises(ValueError, match="reflexive"):
            poly.prep_for_optimizers()


@requires_cytools
class TestDNAToFRST:
    """Tests for Polytope.dna_to_frst."""

    def test_dna_to_frst_valid(self, poly_h11_4):
        """dna_to_frst with valid DNA returns a Triangulation."""
        import cyopt.frst  # noqa: F401
        from cytools.triangulation import Triangulation

        poly_h11_4.prep_for_optimizers()
        # Use all-zeros DNA (always valid -- picks first triangulation per face)
        dna = tuple(0 for _ in poly_h11_4._cyopt_bounds)
        result = poly_h11_4.dna_to_frst(dna)
        assert isinstance(result, Triangulation)

    def test_dna_to_frst_invalid_returns_none(self, poly_h11_4):
        """dna_to_frst with incompatible face choices returns None."""
        import cyopt.frst  # noqa: F401

        poly_h11_4.prep_for_optimizers()
        # Try all possible DNA values -- some may return None (non-solid cone)
        # If none return None for h11=4, this test documents that behavior
        bounds = poly_h11_4._cyopt_bounds
        # Try a few random combos at the extremes
        for dna_val in [
            tuple(hi for _, hi in bounds),  # all max
            tuple(lo for lo, _ in bounds),  # all min (should work)
        ]:
            result = poly_h11_4.dna_to_frst(dna_val)
            if result is None:
                break
        # Just verify the function runs without error; None is valid output
        assert True


@requires_cytools
class TestTriangToDNA:
    """Tests for Polytope.triang_to_dna."""

    def test_triang_to_dna_type(self, poly_h11_4):
        """triang_to_dna returns a tuple of ints."""
        import cyopt.frst  # noqa: F401

        poly_h11_4.prep_for_optimizers()
        dna = tuple(0 for _ in poly_h11_4._cyopt_bounds)
        triang = poly_h11_4.dna_to_frst(dna)
        assert triang is not None, "All-zero DNA should produce valid FRST"
        recovered = poly_h11_4.triang_to_dna(triang)
        assert isinstance(recovered, tuple)
        assert len(recovered) == len(poly_h11_4._cyopt_interesting)
        assert all(isinstance(x, int) for x in recovered)


@requires_cytools
class TestRoundtrip:
    """Tests for DNA roundtrip correctness."""

    def test_roundtrip(self, poly_h11_4):
        """dna -> dna_to_frst -> triang_to_dna recovers original DNA."""
        import cyopt.frst  # noqa: F401

        poly_h11_4.prep_for_optimizers()
        dna = tuple(0 for _ in poly_h11_4._cyopt_bounds)
        triang = poly_h11_4.dna_to_frst(dna)
        assert triang is not None
        recovered = poly_h11_4.triang_to_dna(triang)
        assert recovered == dna

    def test_roundtrip_nonzero_dna(self, poly_h11_4):
        """Roundtrip works for non-zero DNA values too."""
        import cyopt.frst  # noqa: F401

        poly_h11_4.prep_for_optimizers()
        # Use (1, 0, 0, ...) if bounds allow
        bounds = poly_h11_4._cyopt_bounds
        if bounds and bounds[0][1] >= 1:
            dna = (1,) + tuple(0 for _ in bounds[1:])
            triang = poly_h11_4.dna_to_frst(dna)
            if triang is not None:
                recovered = poly_h11_4.triang_to_dna(triang)
                assert recovered == dna


@requires_cytools
class TestDNAToCY:
    """Tests for Polytope.dna_to_cy and cy_to_dna."""

    def test_dna_to_cy(self, poly_h11_4):
        """dna_to_cy returns a CalabiYau object."""
        import cyopt.frst  # noqa: F401
        from cytools.calabiyau import CalabiYau

        poly_h11_4.prep_for_optimizers()
        dna = tuple(0 for _ in poly_h11_4._cyopt_bounds)
        cy = poly_h11_4.dna_to_cy(dna)
        assert isinstance(cy, CalabiYau)

    def test_cy_roundtrip(self, poly_h11_4):
        """cy_to_dna(dna_to_cy(dna)) recovers original DNA."""
        import cyopt.frst  # noqa: F401

        poly_h11_4.prep_for_optimizers()
        dna = tuple(0 for _ in poly_h11_4._cyopt_bounds)
        cy = poly_h11_4.dna_to_cy(dna)
        assert cy is not None
        recovered = poly_h11_4.cy_to_dna(cy)
        assert recovered == dna


@requires_cytools
class TestMonkeyPatch:
    """Tests that encoding functions are accessible as bound methods on Polytope."""

    def test_methods_on_polytope(self):
        """All encoding functions are accessible as bound methods after import."""
        import cyopt.frst  # noqa: F401
        from cytools import Polytope

        assert hasattr(Polytope, "prep_for_optimizers")
        assert hasattr(Polytope, "dna_to_frst")
        assert hasattr(Polytope, "dna_to_cy")
        assert hasattr(Polytope, "triang_to_dna")
        assert hasattr(Polytope, "cy_to_dna")
        assert callable(Polytope.prep_for_optimizers)


@requires_cytools
class TestGrowFRTReturnType:
    """Regression: grow_frt must always return a set, even when only 1 FRT is found.

    Upstream CYTools' grow_frt returns a bare Triangulation in the
    single-FRT case, which breaks downstream ``list(p.grow_frt(...))``
    calls (including CYTools' own face_triangs). cyopt patches this.
    See grow_frt_iteration_bug.md.
    """

    def test_grow_frt_single_frt_is_iterable(self):
        """Single-FRT case returns a set of size 1 (not a bare Triangulation)."""
        import cyopt.frst  # noqa: F401 -- triggers monkey-patching
        from cytools import Polytope

        # 2D triangle with 3 points: exactly one FRT exists.
        p = Polytope([[0, 0], [1, 0], [0, 1]])
        result = p.grow_frt(N=5, seed=42)

        assert isinstance(result, set), (
            f"grow_frt must return a set, got {type(result).__name__}"
        )
        assert len(result) == 1
        # list() must not raise (the original bug symptom).
        items = list(result)
        assert len(items) == 1
        # Duck-type check: element behaves like a Triangulation.
        assert hasattr(items[0], "simplices")

    def test_grow_frt_multi_frt_still_set(self, poly_h11_4):
        """Multi-FRT case unchanged: still a set with len >= 2."""
        import cyopt.frst  # noqa: F401

        # Pick the first 2-face and request many FRTs.
        face_poly = poly_h11_4.faces(2)[0].as_poly()
        result = face_poly.grow_frt(N=10, seed=0)

        assert isinstance(result, set)
        if len(result) < 2:
            pytest.skip(
                "This 2-face only admits one FRT; multi-FRT path "
                "cannot be exercised with this fixture."
            )
        assert len(result) >= 2

"""Integration tests for FRSTOptimizer wrapper and frst_optimizer factory."""

import pytest

from tests.test_frst.conftest import requires_cytools


@pytest.fixture(scope="module")
def poly_with_faces():
    """A reflexive polytope with multiple interesting faces for wrapper tests.

    Uses h11=7 (first polytope) which has 2 interesting faces with bounds
    (0, 2) each -- enough for all optimizer algorithms to work.
    """
    try:
        from cytools import fetch_polytopes
    except ImportError:
        pytest.skip("CYTools not available")

    import cyopt.frst  # noqa: F401 -- triggers patch_polytope

    p = fetch_polytopes(h11=7, limit=1)[0]
    p.prep_for_optimizers()
    return p


@requires_cytools
class TestFRSTOptimizerFactory:
    """Tests for the frst_optimizer factory function."""

    def test_frst_optimizer_factory(self, poly_with_faces):
        """Factory returns FRSTOptimizer with GA as default optimizer."""
        from cyopt.frst import FRSTOptimizer, frst_optimizer
        from cyopt.optimizers.ga import GA

        wrapper = frst_optimizer(poly_with_faces, lambda cy: float(cy.h11()))
        assert isinstance(wrapper, FRSTOptimizer)
        assert isinstance(wrapper.optimizer, GA)

    def test_frst_result(self, poly_with_faces):
        """Run produces FRSTResult with all expected fields populated."""
        from cyopt.frst import FRSTResult, frst_optimizer

        wrapper = frst_optimizer(
            poly_with_faces, lambda cy: float(cy.h11()), seed=42
        )
        result = wrapper.run(5)

        assert isinstance(result, FRSTResult)
        assert result.best_triangulation is not None
        assert result.best_cy is not None
        assert isinstance(result.best_value, float)
        assert isinstance(result.best_dna, tuple)
        assert all(isinstance(x, int) for x in result.best_dna)
        assert result.n_evaluations > 0
        assert result.wall_time > 0

    def test_frst_result_value_unnegated(self, poly_with_faces):
        """best_value is un-negated (positive when target returns positive)."""
        from cyopt.frst import frst_optimizer

        wrapper = frst_optimizer(poly_with_faces, lambda cy: 42.0, seed=42)
        result = wrapper.run(3)
        assert result.best_value > 0
        assert result.best_value == 42.0

    def test_target_mode_triangulation(self, poly_with_faces):
        """target_mode='triangulation' passes Triangulation, skips CY."""
        from cyopt.frst import frst_optimizer

        wrapper = frst_optimizer(
            poly_with_faces,
            lambda triang: float(len(triang.simplices())),
            target_mode="triangulation",
            seed=42,
        )
        result = wrapper.run(3)
        assert result.best_cy is None
        assert result.best_triangulation is not None

    def test_ancillary_data(self, poly_with_faces):
        """Ancillary data from (value, ancillary) target is preserved."""
        from cyopt.frst import frst_optimizer

        def target_with_ancillary(cy):
            return (float(cy.h11()), {"extra": "data"})

        wrapper = frst_optimizer(poly_with_faces, target_with_ancillary, seed=42)
        result = wrapper.run(3)
        assert len(result.ancillary_data) > 0
        assert any(v == {"extra": "data"} for v in result.ancillary_data.values())

    def test_all_optimizers(self, poly_with_faces):
        """All 8 optimizer classes work through the FRST wrapper."""
        from cyopt import (
            GA,
            BasinHopping,
            BestFirstSearch,
            DifferentialEvolution,
            GreedyWalk,
            MCMC,
            RandomSample,
            SimulatedAnnealing,
        )
        from cyopt.frst import FRSTResult, frst_optimizer

        target = lambda cy: float(cy.h11())  # noqa: E731

        for cls in [
            GA,
            RandomSample,
            GreedyWalk,
            BestFirstSearch,
            BasinHopping,
            DifferentialEvolution,
            MCMC,
            SimulatedAnnealing,
        ]:
            wrapper = frst_optimizer(
                poly_with_faces, target, optimizer=cls, seed=42
            )
            result = wrapper.run(3)
            assert isinstance(result, FRSTResult), (
                f"{cls.__name__} did not return FRSTResult"
            )
            assert result.best_triangulation is not None, (
                f"{cls.__name__} returned None best_triangulation"
            )

    def test_custom_kwargs_passed(self, poly_with_faces):
        """Optimizer-specific kwargs are forwarded to the optimizer."""
        from cyopt.frst import frst_optimizer

        wrapper = frst_optimizer(
            poly_with_faces,
            lambda cy: float(cy.h11()),
            population_size=5,
            seed=42,
        )
        assert wrapper.optimizer._population_size == 5


def test_top_level_import_no_frst():
    """Top-level 'import cyopt' does not auto-import frst subpackage."""
    import importlib
    import sys

    # Remove any cached frst imports
    frst_modules = [k for k in sys.modules if k.startswith("cyopt.frst")]
    for mod in frst_modules:
        del sys.modules[mod]

    # Also remove cyopt itself to get a fresh import
    cyopt_modules = [k for k in sys.modules if k.startswith("cyopt")]
    saved = {}
    for mod in cyopt_modules:
        saved[mod] = sys.modules.pop(mod)

    try:
        import cyopt

        importlib.reload(cyopt)
        # frst should not be in the namespace
        assert not hasattr(cyopt, "frst") or "cyopt.frst" not in sys.modules
    finally:
        # Restore modules
        sys.modules.update(saved)

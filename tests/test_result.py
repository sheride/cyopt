"""Tests for Result dataclass."""

import pytest

from cyopt._types import Result


class TestResult:
    def test_fields_present(self):
        """Result has all required fields."""
        r = Result(
            best_solution=(0, 0, 0),
            best_value=0.0,
            history=[1.0, 0.5, 0.0],
            full_history=None,
            n_evaluations=10,
            wall_time=0.123,
        )
        assert r.best_solution == (0, 0, 0)
        assert r.best_value == 0.0
        assert r.history == [1.0, 0.5, 0.0]
        assert r.full_history is None
        assert r.n_evaluations == 10
        assert r.wall_time == 0.123

    def test_frozen(self):
        """Result is immutable (frozen dataclass)."""
        r = Result(
            best_solution=(1, 2),
            best_value=5.0,
            history=[5.0],
            full_history=None,
            n_evaluations=1,
            wall_time=0.01,
        )
        with pytest.raises(AttributeError):
            r.best_value = 99.0  # type: ignore[misc]

    def test_full_history_none_when_disabled(self):
        """full_history is None when record_history=False."""
        r = Result(
            best_solution=(0,),
            best_value=0.0,
            history=[0.0],
            full_history=None,
            n_evaluations=1,
            wall_time=0.001,
        )
        assert r.full_history is None

    def test_full_history_populated(self):
        """full_history can contain per-iteration dicts."""
        history_data = [{"best": 5.0, "mean": 7.0}, {"best": 3.0, "mean": 5.5}]
        r = Result(
            best_solution=(1,),
            best_value=3.0,
            history=[5.0, 3.0],
            full_history=history_data,
            n_evaluations=2,
            wall_time=0.01,
        )
        assert len(r.full_history) == 2
        assert r.full_history[0]["best"] == 5.0

"""FRSTResult dataclass wrapping optimizer Result with decoded FRST fields."""

from __future__ import annotations

from dataclasses import dataclass

from cyopt._types import DNA, Result


@dataclass(frozen=True)
class FRSTResult:
    """Result of an FRST optimization run.

    Wraps the underlying optimizer ``Result`` and adds decoded triangulation/CY
    fields. ``best_value`` reports the original (un-negated) target value --
    higher is better, matching the user's target function convention.

    Parameters
    ----------
    result : Result
        The underlying generic optimizer result.
    best_triangulation : object
        Triangulation decoded from the best DNA. ``None`` if the best DNA
        did not produce a valid FRST (should not happen in practice).
    best_cy : object
        CalabiYau decoded from the best DNA. ``None`` if
        ``target_mode='triangulation'`` was used.
    ancillary_data : dict
        Mapping of DNA tuples to ancillary data returned by the target
        function (when target returns ``(value, ancillary)`` tuples).
    """

    result: Result
    best_triangulation: object
    best_cy: object
    ancillary_data: dict

    @property
    def best_dna(self) -> DNA:
        """The best DNA tuple found during optimization."""
        return self.result.best_solution

    @property
    def best_value(self) -> float:
        """The best target value (un-negated: higher is better)."""
        return -self.result.best_value

    @property
    def history(self) -> list[float]:
        """Best-so-far target values at each iteration (un-negated)."""
        return [-v for v in self.result.history]

    @property
    def n_evaluations(self) -> int:
        """Total number of unique fitness evaluations."""
        return self.result.n_evaluations

    @property
    def wall_time(self) -> float:
        """Wall-clock time in seconds for the optimization run."""
        return self.result.wall_time

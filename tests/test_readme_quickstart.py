"""Regression test guarding the README quickstart code block.

The README's ``## Quickstart`` section contains the first code block a new
user sees. Shipping v1.0 with a README that raises ``AttributeError`` against
the current public API is a worse first impression than shipping with fewer
features, so this module extracts the first fenced ``python`` block from
``README.md`` and executes it against the installed cyopt package. If a
future refactor renames a public API (as Phase 04.1's ``bounds=`` →
``space=TupleSpace(...)`` change did), this test fails loudly in CI rather
than silently drifting into user-facing breakage.

Parallel in purpose to ``tests/test_notebook_api_surface.py`` (which guards
tutorial notebook code against API drift via static AST walking). This test
is stronger in that it actually executes the snippet, and weaker in that it
only covers the single README block — the two are complementary.
"""

from __future__ import annotations

from pathlib import Path

import pytest

README_PATH = Path(__file__).resolve().parent.parent / "README.md"


def _extract_first_python_block(readme_text: str) -> str:
    """Return the source inside the first ```python ... ``` fence in README."""
    opener = "```python\n"
    start = readme_text.find(opener)
    assert start != -1, "README.md contains no ```python fenced block"
    body_start = start + len(opener)
    end = readme_text.find("\n```", body_start)
    assert end != -1, "README.md ```python fence is not closed with ``` "
    return readme_text[body_start:end]


def test_readme_quickstart_runs():
    """The README quickstart executes and finds the global minimum.

    The quickstart minimizes ``sum((x_i - 3) ** 2)`` on ``[(0, 9)] * 3`` with
    GA(seed=42). The unique minimum at ``(3, 3, 3)`` with value 0 is
    reachable (3 is in every dimension's range) and a 100-iteration GA
    locates it deterministically on this 10^3 = 1000-candidate space. Both
    assertions below are stronger than a bare "did it run" check: the
    ``best_value == 0`` assertion catches a degraded GA, and the
    ``best_solution == (3, 3, 3)`` assertion catches a regression where the
    optimizer gets close but not exact.
    """
    code = _extract_first_python_block(README_PATH.read_text())
    namespace: dict = {"__name__": "__main__"}
    try:
        exec(code, namespace)
    except Exception as e:  # pragma: no cover — defensive
        pytest.fail(
            "README.md quickstart raised an exception. "
            "Extracted code was:\n\n"
            f"{code}\n\n"
            f"Exception: {type(e).__name__}: {e}"
        )

    assert "result" in namespace, (
        "README.md quickstart did not bind `result` in its namespace; "
        "did the snippet get edited to drop the `result = ga.run(...)` line?"
    )
    result = namespace["result"]
    assert result.best_value == 0, (
        f"README.md quickstart GA did not find the minimum: "
        f"best_value={result.best_value!r}, expected 0."
    )
    assert tuple(result.best_solution) == (3, 3, 3), (
        f"README.md quickstart GA converged to a non-minimum point: "
        f"best_solution={result.best_solution!r}, expected (3, 3, 3)."
    )

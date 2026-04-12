"""FRST wrapper layer for CYTools integration.

Provides DNA encoding/decoding between integer tuples and CYTools FRST
triangulations, plus Polytope monkey-patches for optimizer integration.

Requires CYTools to be installed (e.g., via the ``cytools`` conda environment).
"""

try:
    from cytools import Polytope  # noqa: F401
except ImportError as e:
    raise ImportError(
        "cyopt.frst requires CYTools. Install with: pip install cyopt[frst]\n"
        "Or activate the cytools conda environment."
    ) from e

from cyopt.frst._encoding import patch_polytope
from cyopt.frst._result import FRSTResult
from cyopt.frst._wrapper import FRSTOptimizer, frst_optimizer

__all__ = [
    "FRSTOptimizer",
    "FRSTResult",
    "frst_optimizer",
    "patch_polytope",
]

# Apply monkey patches on import
patch_polytope()

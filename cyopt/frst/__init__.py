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

__all__ = ["patch_polytope"]

# Apply monkey patches on import
patch_polytope()

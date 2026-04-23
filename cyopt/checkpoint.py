"""Checkpoint support for discrete optimizers."""
from __future__ import annotations

import pickle
from pathlib import Path
from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from cyopt.base import DiscreteOptimizer
    from cyopt.spaces import SearchSpace

CHECKPOINT_VERSION = 2
"""Current checkpoint format version.

History:
- v1: stored raw ``bounds`` tuple. Superseded by v2.
- v2: stores ``space_kind`` (class name) + ``space_data`` (reconstruction dict).
  Known kinds (currently only ``'TupleSpace'``) are auto-reconstructed on load;
  unknown kinds require the caller to pass ``space=`` to ``load_checkpoint``.
"""


# ------------------------------------------------------------------
# Space (de)serialization
# ------------------------------------------------------------------

def _serialize_space(space: "SearchSpace") -> tuple[str, dict]:
    """Return ``(space_kind, space_data)`` for checkpoint storage.

    Known space types produce a non-empty ``space_data`` dict suitable for
    ``_deserialize_space``. Unknown types still get their class name recorded
    so ``load_checkpoint`` can report it in a helpful error message; they
    return an empty ``space_data`` dict because the class has no agreed
    reconstruction contract, and the user must pass ``space=`` at load time.
    """
    from cyopt.spaces import TupleSpace

    kind = type(space).__name__
    if isinstance(space, TupleSpace):
        return kind, {"bounds": space.bounds}
    return kind, {}


def _deserialize_space(space_kind: str, space_data: dict) -> "SearchSpace":
    """Reconstruct a SearchSpace instance from ``(space_kind, space_data)``.

    Raises
    ------
    ValueError
        If ``space_kind`` is not a known reconstructible kind. Callers should
        catch this and fall back to a user-supplied ``space=`` on
        ``load_checkpoint``.
    """
    from cyopt.spaces import TupleSpace

    if space_kind == "TupleSpace":
        return TupleSpace(space_data["bounds"])
    raise ValueError(
        f"Unknown space_kind {space_kind!r}. "
        f"Pass space= to load_checkpoint to supply the space explicitly."
    )


# ------------------------------------------------------------------
# Migration
# ------------------------------------------------------------------

def _migrate(state: dict[str, Any], from_version: int) -> dict[str, Any]:
    """Migrate checkpoint state from an older version to ``CHECKPOINT_VERSION``.

    Currently supports v1 -> v2 (wraps raw ``bounds`` -- or a Plan-02-era raw
    pickled ``space`` object -- as ``space_kind='TupleSpace'`` + ``space_data``).

    Raises
    ------
    ValueError
        If no migration path exists from ``from_version``.
    """
    if from_version == 1:
        if "bounds" in state:
            bounds = state.pop("bounds")
            state["space_kind"] = "TupleSpace"
            state["space_data"] = {"bounds": bounds}
        elif "space" in state:
            # Plan-02 intermediate: the state pickled a raw SearchSpace object.
            # Extract its reconstruction data, then drop the raw reference.
            raw = state.pop("space")
            kind, data = _serialize_space(raw)
            state["space_kind"] = kind
            state["space_data"] = data
        elif "space_kind" in state:
            # Already partially migrated -- OK (idempotent retry).
            pass
        else:
            raise ValueError(
                "Cannot migrate checkpoint: v1 state lacks any recognized "
                "space marker ('bounds', 'space', or 'space_kind')."
            )
        state["_checkpoint_version"] = CHECKPOINT_VERSION
        return state

    raise ValueError(
        f"Cannot migrate checkpoint from version {from_version} "
        f"to {CHECKPOINT_VERSION}. No migration path available."
    )


# ------------------------------------------------------------------
# CheckpointCallback (unchanged)
# ------------------------------------------------------------------

class CheckpointCallback:
    """Callback that saves optimizer checkpoints at regular intervals.

    Parameters
    ----------
    path : str | Path
        File path for checkpoint. Overwrites on each save.
    every_n : int
        Save every N iterations. Default 100.
    """

    def __init__(self, path: str | Path, every_n: int = 100) -> None:
        self._path = Path(path)
        self._every_n = every_n
        self._optimizer: Any = None  # Bound during optimizer __init__

    def bind(self, optimizer: "DiscreteOptimizer") -> None:
        """Bind this callback to an optimizer instance.

        Called automatically by :class:`~cyopt.base.DiscreteOptimizer`
        during initialization. Subclasses that override this method MUST
        call ``super().bind(optimizer)``.

        Parameters
        ----------
        optimizer : DiscreteOptimizer
            The optimizer instance whose ``save_checkpoint`` method this
            callback will invoke.
        """
        self._optimizer = optimizer

    def __call__(self, info: dict[str, Any]) -> bool | None:
        if (info["iteration"] + 1) % self._every_n == 0:
            if self._optimizer is not None:
                self._optimizer.save_checkpoint(self._path)
        return None

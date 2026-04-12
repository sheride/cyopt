"""Checkpoint support for discrete optimizers."""

from __future__ import annotations

import pickle
from pathlib import Path
from typing import Any

CHECKPOINT_VERSION = 1
"""Current checkpoint format version. Increment on breaking state changes."""


def _migrate(state: dict[str, Any], from_version: int) -> dict[str, Any]:
    """Migrate checkpoint state from an older version.

    Raises ValueError if migration is not possible.
    """
    raise ValueError(
        f"Cannot migrate checkpoint from version {from_version} "
        f"to {CHECKPOINT_VERSION}. No migration path available."
    )


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

    def __call__(self, info: dict[str, Any]) -> bool | None:
        if (info['iteration'] + 1) % self._every_n == 0:
            if self._optimizer is not None:
                self._optimizer.save_checkpoint(self._path)
        return None

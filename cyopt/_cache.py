"""Evaluation cache with optional LRU eviction."""

from collections import OrderedDict


class EvaluationCache:
    """Cache for fitness evaluations, backed by an OrderedDict.

    Provides O(1) lookup, insertion, and LRU eviction when ``maxsize``
    is specified. Accessed entries are moved to the end (most-recently-used
    position), and eviction removes from the front (least-recently-used).

    Parameters
    ----------
    maxsize : int | None
        Maximum number of entries. ``None`` means unbounded.
    """

    def __init__(self, maxsize: int | None = None) -> None:
        self._cache: OrderedDict[tuple[int, ...], float] = OrderedDict()
        self._maxsize = maxsize

    def __contains__(self, key: tuple[int, ...]) -> bool:
        return key in self._cache

    def __getitem__(self, key: tuple[int, ...]) -> float:
        value = self._cache[key]
        self._cache.move_to_end(key)
        return value

    def __setitem__(self, key: tuple[int, ...], value: float) -> None:
        if key in self._cache:
            self._cache.move_to_end(key)
        self._cache[key] = value
        if self._maxsize is not None and len(self._cache) > self._maxsize:
            self._cache.popitem(last=False)

    def __len__(self) -> int:
        return len(self._cache)

    def clear(self) -> None:
        """Remove all entries from the cache."""
        self._cache.clear()

    def to_list(self) -> list[tuple[tuple[int, ...], float]]:
        """Serialize cache as ordered list of (key, value) pairs.

        Preserves LRU ordering so that restored caches evict identically.
        """
        return list(self._cache.items())

    @classmethod
    def from_list(
        cls,
        items: list[tuple[tuple[int, ...], float]],
        maxsize: int | None = None,
    ) -> "EvaluationCache":
        """Reconstruct cache from ordered list of (key, value) pairs.

        Parameters
        ----------
        items : list[tuple[tuple[int, ...], float]]
            Ordered (key, value) pairs from :meth:`to_list`.
        maxsize : int | None
            Maximum cache size for the new instance.
        """
        cache = cls(maxsize=maxsize)
        # Trim to maxsize (keep most-recently-used tail) before inserting
        if maxsize is not None and len(items) > maxsize:
            items = items[-maxsize:]
        for k, v in items:
            cache._cache[k] = v
        return cache

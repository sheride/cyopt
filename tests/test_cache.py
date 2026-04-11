"""Tests for EvaluationCache."""

from cyopt._cache import EvaluationCache


class TestEvaluationCache:
    def test_cache_hit(self):
        """Cache returns stored value without re-evaluation."""
        cache = EvaluationCache()
        cache[(1, 2, 3)] = 14.0
        assert cache[(1, 2, 3)] == 14.0

    def test_cache_contains(self):
        """__contains__ returns True for cached keys, False otherwise."""
        cache = EvaluationCache()
        cache[(1, 2)] = 5.0
        assert (1, 2) in cache
        assert (3, 4) not in cache

    def test_cache_len(self):
        """__len__ returns correct count."""
        cache = EvaluationCache()
        assert len(cache) == 0
        cache[(1,)] = 1.0
        cache[(2,)] = 4.0
        assert len(cache) == 2

    def test_lru_eviction(self):
        """Evicts LRU entry when maxsize exceeded."""
        cache = EvaluationCache(maxsize=2)
        cache[(1,)] = 1.0
        cache[(2,)] = 4.0
        cache[(3,)] = 9.0  # should evict (1,)
        assert (1,) not in cache
        assert (2,) in cache
        assert (3,) in cache
        assert len(cache) == 2

    def test_move_to_end_on_access(self):
        """Accessed items are moved to end and not evicted first."""
        cache = EvaluationCache(maxsize=2)
        cache[(1,)] = 1.0
        cache[(2,)] = 4.0
        # Access (1,) to move it to end
        _ = cache[(1,)]
        # Insert (3,) -- should evict (2,), not (1,)
        cache[(3,)] = 9.0
        assert (1,) in cache
        assert (2,) not in cache
        assert (3,) in cache

    def test_no_maxsize(self):
        """Without maxsize, cache grows unbounded."""
        cache = EvaluationCache()
        for i in range(100):
            cache[(i,)] = float(i * i)
        assert len(cache) == 100

    def test_clear(self):
        """clear() empties the cache."""
        cache = EvaluationCache(maxsize=10)
        cache[(1,)] = 1.0
        cache[(2,)] = 4.0
        cache.clear()
        assert len(cache) == 0
        assert (1,) not in cache

    def test_overwrite_existing_key(self):
        """Overwriting an existing key updates value and moves to end."""
        cache = EvaluationCache(maxsize=2)
        cache[(1,)] = 1.0
        cache[(2,)] = 4.0
        cache[(1,)] = 99.0  # overwrite, should move to end
        cache[(3,)] = 9.0  # should evict (2,), not (1,)
        assert cache[(1,)] == 99.0
        assert (2,) not in cache

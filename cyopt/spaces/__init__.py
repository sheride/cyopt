"""cyopt search-space classes."""

from cyopt.spaces._base import SearchSpace
from cyopt.spaces._graph import GraphSpace
from cyopt.spaces._tuple import TupleSpace

__all__ = ["SearchSpace", "GraphSpace", "TupleSpace"]

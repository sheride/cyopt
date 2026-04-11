"""cyopt -- Discrete optimization toolkit for bounded integer-tuple search spaces."""

from cyopt._types import DNA, Bounds, FitnessFunction, Result

__all__ = [
    "DiscreteOptimizer",
    "Result",
    "DNA",
    "Bounds",
    "FitnessFunction",
]

__version__ = "0.1.0"


def __getattr__(name: str):
    if name == "DiscreteOptimizer":
        from cyopt.base import DiscreteOptimizer

        return DiscreteOptimizer
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

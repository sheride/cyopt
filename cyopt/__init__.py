"""cyopt -- Discrete optimization toolkit for bounded integer-tuple search spaces."""

from importlib.metadata import PackageNotFoundError
from importlib.metadata import version as _version

from cyopt.base import DiscreteOptimizer
from cyopt.checkpoint import CheckpointCallback
from cyopt.optimizers.basin_hopping import BasinHopping
from cyopt.optimizers.best_first_search import BestFirstSearch
from cyopt.optimizers.differential_evolution import DifferentialEvolution
from cyopt.optimizers.ga import GA
from cyopt.optimizers.greedy_walk import GreedyWalk
from cyopt.optimizers.mcmc import MCMC
from cyopt.optimizers.neighbors import (
    LocalMinimizeFunction,
    NeighborFunction,
    PerturbFunction,
    StepFunction,
)
from cyopt.optimizers.random_sample import RandomSample
from cyopt.optimizers.simulated_annealing import SimulatedAnnealing
from cyopt.spaces import GraphSpace, SearchSpace, TupleSpace
from cyopt.types import (
    DNA,
    Bounds,
    Callback,
    CallbackInfo,
    FitnessFunction,
    Node,
    Result,
)

__all__ = [
    "BasinHopping",
    "BestFirstSearch",
    "Callback",
    "CallbackInfo",
    "CheckpointCallback",
    "DifferentialEvolution",
    "DiscreteOptimizer",
    "FRSTFlipGraphSpace",
    "GA",
    "GreedyWalk",
    "LocalMinimizeFunction",
    "MCMC",
    "NeighborFunction",
    "Node",
    "PerturbFunction",
    "RandomSample",
    "SimulatedAnnealing",
    "Result",
    "StepFunction",
    "DNA",
    "Bounds",
    "FitnessFunction",
    "SearchSpace",
    "GraphSpace",
    "TupleSpace",
]

try:
    __version__ = _version("cyopt")
except PackageNotFoundError:  # running from an uninstalled source tree
    __version__ = "0.0.0+unknown"


def __getattr__(name):
    """Lazy attribute access for FRST symbols (PEP 562).

    Top-level ``import cyopt`` must NOT auto-import ``cyopt.frst``
    (that would trigger CYTools and break the
    ``test_top_level_import_no_frst`` contract). Instead, expose
    FRST symbols via lazy attribute access so that
    ``from cyopt import FRSTFlipGraphSpace`` triggers the
    ``cyopt.frst`` import (and its ``patch_polytope()`` side effect)
    only when the symbol is actually requested.
    """
    if name == "FRSTFlipGraphSpace":
        # Importing cyopt.frst triggers patch_polytope() so that
        # poly.dna_to_frst (used by FRSTFlipGraphSpace.neighbors and
        # .random) is available on Polytope.
        import cyopt.frst as _frst

        return _frst.FRSTFlipGraphSpace
    raise AttributeError(f"module 'cyopt' has no attribute {name!r}")

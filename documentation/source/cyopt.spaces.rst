.. currentmodule:: cyopt.spaces

cyopt.spaces --- Search-space classes
======================================

.. automodule:: cyopt.spaces
   :no-members:

cyopt decouples the neighbourhood structure of the search space from the
optimisation algorithm.  All spaces inherit from the abstract
:class:`SearchSpace` base, which requires only a ``random(rng)`` method.
Local-search optimisers (:class:`~cyopt.optimizers.GreedyWalk`,
:class:`~cyopt.optimizers.BestFirstSearch`,
:class:`~cyopt.optimizers.BasinHopping`,
:class:`~cyopt.optimizers.SimulatedAnnealing`,
:class:`~cyopt.optimizers.MCMC`) use the extended
:class:`GraphSpace` protocol, which additionally provides
``neighbors(node)``.

The current optimiser implementations evaluate and cache candidates as
:data:`~cyopt.types.DNA` values, i.e. integer tuples.  Custom spaces can
define their own neighbourhood structure, but candidates emitted by
``random()`` and ``neighbors()`` should be convertible to ``tuple[int, ...]``
unless the optimiser's evaluation path is also customised.

Space hierarchy
---------------

::

   SearchSpace          (abstract — random only)
    └── GraphSpace      (abstract — + neighbors)
         ├── TupleSpace (concrete — bounded integers, Hamming-1 neighbors)
         └── FRSTFlipGraphSpace  (cyopt.frst — lazy bistellar-flip neighbors)

Classes
-------

.. autoclass:: SearchSpace
   :members:
   :show-inheritance:

.. autoclass:: GraphSpace
   :members:
   :show-inheritance:

.. autoclass:: TupleSpace
   :members:
   :exclude-members: bounds, dim
   :show-inheritance:

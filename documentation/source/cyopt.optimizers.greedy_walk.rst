.. currentmodule:: cyopt.optimizers.greedy_walk

cyopt.optimizers.greedy_walk --- Greedy Walk
=============================================

.. automodule:: cyopt.optimizers.greedy_walk
   :no-members:

:class:`GreedyWalk` implements iterated steepest-descent local search.
At each step it evaluates all neighbours of the current position and moves
to the one with the lowest fitness value.  If no neighbour improves on the
current fitness (i.e. a local minimum has been reached), the search
restarts from a fresh random point sampled via ``space.random(rng)``.

An optional ``neighbor_fn`` overrides ``space.neighbors`` to supply a
custom neighbourhood structure.

Classes
-------

.. autoclass:: GreedyWalk
   :members:
   :show-inheritance:

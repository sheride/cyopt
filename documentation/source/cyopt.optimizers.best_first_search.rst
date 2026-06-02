.. currentmodule:: cyopt.optimizers.best_first_search

cyopt.optimizers.best_first_search --- Best-First Search
=========================================================

.. automodule:: cyopt.optimizers.best_first_search
   :no-members:

:class:`BestFirstSearch` offers two systematic local-search modes:

- **Backtrack mode** (``mode='backtrack'``, default): maintains a path
  from the starting point and an *avoid set* to handle oscillations.  At
  each step it evaluates all valid neighbours (not in the current path and
  not in the avoid set) and moves to the best.  When oscillation is
  detected (the search returns to a recently visited node), the
  intermediate node is added to the avoid set.  A random restart is
  triggered when no valid neighbour remains.

- **Frontier mode** (``mode='frontier'``): classic best-first search
  using a min-heap priority queue over all unvisited candidates.  Nodes
  are expanded in order of increasing fitness and never revisited.  When
  the frontier is exhausted, the search samples fresh random starting
  points.

Both modes accept an optional ``neighbor_fn`` to override
``space.neighbors``.

Classes
-------

.. autoclass:: BestFirstSearch
   :members:
   :show-inheritance:

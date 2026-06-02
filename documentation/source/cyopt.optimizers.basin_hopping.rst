.. currentmodule:: cyopt.optimizers.basin_hopping

cyopt.optimizers.basin_hopping --- Basin Hopping
=================================================

.. automodule:: cyopt.optimizers.basin_hopping
   :no-members:

:class:`BasinHopping` implements the basin-hopping algorithm adapted for
discrete graph search spaces.  At each step it:

1. **Perturbs** the current solution via a configurable
   ``perturb_fn`` (default: one or more
   :func:`~cyopt.optimizers.neighbors.random_single_flip` steps).
2. **Locally minimises** from the perturbed point via a configurable
   ``local_minimize_fn`` (default: :func:`_greedy_descent` — steepest
   descent up to 100 iterations using ``space.neighbors``).
3. **Accepts or rejects** the new local minimum via the Metropolis
   criterion with a fixed temperature.

This strategy allows the search to escape shallow local minima while
preferring deeper basins, and is particularly well-suited to rugged,
low-dimensional discrete landscapes.

.. note::

   The default ``perturb_fn`` requires a
   :class:`~cyopt.spaces.TupleSpace` (it closes over ``space.bounds``).
   For non-tuple spaces pass an explicit ``perturb_fn``.

Classes
-------

.. autoclass:: BasinHopping
   :members:
   :show-inheritance:

Helper functions
----------------

.. autofunction:: _greedy_descent

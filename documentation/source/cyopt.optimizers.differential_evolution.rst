.. currentmodule:: cyopt.optimizers.differential_evolution

cyopt.optimizers.differential_evolution --- Differential Evolution
==================================================================

.. automodule:: cyopt.optimizers.differential_evolution
   :no-members:

:class:`DifferentialEvolution` wraps
``scipy.optimize.differential_evolution`` with ``integrality=True`` for
all dimensions, enabling native integer-constrained optimisation via
SciPy's public API.  It delegates the full evolutionary loop to SciPy —
there is no ``_step`` method — and translates ``Bounds`` to SciPy's
half-open format ``(lo, hi + 1)`` internally.

.. note::

   Unlike the other seven optimisers, consecutive ``run()`` calls do
   **not** continue from the existing population; each call restarts the
   evolutionary process from a fresh random population.  The evaluation
   cache *is* preserved, however, so re-evaluating the same candidate
   across runs is free.

Classes
-------

.. autoclass:: DifferentialEvolution
   :members:
   :show-inheritance:

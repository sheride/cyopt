.. currentmodule:: cyopt.optimizers.ga

cyopt.optimizers.ga --- Genetic Algorithm
==========================================

.. automodule:: cyopt.optimizers.ga
   :no-members:

:class:`GA` is a generational elitist genetic algorithm with composable
selection, crossover, and mutation operators.  Two operating modes are
supported:

- **Simple mode** (``fitness_fn`` only): the fitness function is minimised
  directly.  Selection weights are derived from fitness values via
  ``1 / (f − f_min + 1)`` so that lower fitness ↔ higher selection
  probability.

- **Target/fitness mode** (``target_fn`` + ``fitness``): a *target
  function* computes an observable (e.g. a CY volume) and a *fitness
  function* converts the population's target values into selection
  probabilities (built-in: ``'inverse_square'`` and ``'gaussian'``).
  Internally the target is negated so the base class minimises −target.
  This matches the arXiv:2405.08871 optimisation pattern.

Population uniqueness is enforced: duplicate candidates are discarded and
regenerated, with a safety-valve fallback to random sampling when the
cardinality of the search space is reached.

Classes
-------

.. autoclass:: GA
   :members:
   :show-inheritance:

Operator functions
------------------

.. autofunction:: tournament_selection
.. autofunction:: roulette_wheel_selection
.. autofunction:: ranked_selection
.. autofunction:: npoint_crossover
.. autofunction:: uniform_crossover
.. autofunction:: random_mutation
.. autofunction:: fitness_inverse_square
.. autofunction:: fitness_gaussian

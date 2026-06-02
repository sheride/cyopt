.. currentmodule:: cyopt.base

cyopt.base --- DiscreteOptimizer base class
============================================

.. automodule:: cyopt.base
   :no-members:

:class:`DiscreteOptimizer` is the abstract base class for all eight cyopt
optimisers.  It provides the complete shared infrastructure: evaluation
caching via :class:`~cyopt._cache.EvaluationCache`, reproducible seeding via
``numpy.random.default_rng``, best-so-far tracking (minimisation convention),
per-iteration callback dispatch, tqdm progress reporting, and
checkpoint/resume serialisation.  Seven optimisers implement a single
``_step(iteration)`` method that encodes the algorithm;
:class:`~cyopt.optimizers.DifferentialEvolution` instead overrides
``run()`` and delegates the evolutionary loop to SciPy.

Classes
-------

.. autoclass:: DiscreteOptimizer
   :members:
   :show-inheritance:

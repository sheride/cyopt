.. currentmodule:: cyopt

cyopt.optimizers
================

.. automodule:: cyopt.optimizers
   :no-members:

cyopt provides eight discrete optimisers, all subclassing
:class:`~cyopt.base.DiscreteOptimizer`.  They share evaluation caching,
reproducible seeding, callback dispatch, and checkpoint/resume
infrastructure.  Seven optimisers implement a single ``_step`` method and
use the base-class ``run(n_iterations)`` loop;
:class:`~cyopt.optimizers.DifferentialEvolution` overrides ``run()`` because
SciPy owns its full iteration loop.

Optimizer overview
------------------

.. raw:: html
   :file: _static/figures/f3_optimizers.html

Individual module pages
-----------------------

.. toctree::
   :maxdepth: 1

   cyopt.optimizers.ga
   cyopt.optimizers.differential_evolution
   cyopt.optimizers.random_sample
   cyopt.optimizers.greedy_walk
   cyopt.optimizers.best_first_search
   cyopt.optimizers.basin_hopping
   cyopt.optimizers.simulated_annealing
   cyopt.optimizers.mcmc
   cyopt.optimizers.neighbors

.. currentmodule:: cyopt

cyopt
=====

.. automodule:: cyopt
   :no-members:

Package architecture
--------------------

cyopt is organised around one abstract base class
:class:`~cyopt.base.DiscreteOptimizer` that provides shared infrastructure
(evaluation caching, seeding, best-so-far tracking, callbacks, checkpoints)
and the common ``run(n_iterations)`` contract.  Most concrete optimisers
implement one ``_step`` method; :class:`~cyopt.optimizers.DifferentialEvolution`
overrides ``run()`` and delegates to SciPy.  The search space is a pluggable
:class:`~cyopt.spaces.SearchSpace` object, decoupling the neighbourhood
structure from the optimisation algorithm.

.. raw:: html
   :file: _static/figures/f1_workflow.html

Module dependency graph
-----------------------

The figure below shows how the sub-packages relate to each other.  The
generic optimisers share infrastructure from ``cyopt.base`` and operate on
any :class:`~cyopt.spaces.SearchSpace`.  The optional ``cyopt.frst`` layer
wraps any generic optimiser in a DNA-encoding bridge to CYTools.

.. raw:: html
   :file: _static/figures/f2_architecture.html

Modules
-------

.. toctree::
   :maxdepth: 1

   cyopt.types
   cyopt.base
   cyopt.checkpoint
   cyopt.spaces
   cyopt.optimizers
   cyopt.frst

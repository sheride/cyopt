.. currentmodule:: cyopt.optimizers.random_sample

cyopt.optimizers.random_sample --- Random Sampling
===================================================

.. automodule:: cyopt.optimizers.random_sample
   :no-members:

:class:`RandomSample` is the simplest possible optimiser: it samples
uniformly at random from ``space.random(rng)`` each iteration, evaluates
the fitness, and tracks the running best.  No neighbourhood structure or
memory is used.

Its primary use is as a **performance baseline**: if a more sophisticated
optimiser does not significantly outperform random sampling on your
problem, the search landscape may be too flat or the space too large for
local methods to be effective.

Classes
-------

.. autoclass:: RandomSample
   :members:
   :show-inheritance:

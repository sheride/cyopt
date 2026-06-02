.. currentmodule:: cyopt.optimizers.mcmc

cyopt.optimizers.mcmc --- MCMC
================================

.. automodule:: cyopt.optimizers.mcmc
   :no-members:

:class:`MCMC` implements Metropolis-Hastings sampling at a fixed
temperature :math:`T`.  At each step a neighbour is proposed via
``step_fn(dna, rng)`` and accepted with probability

.. math::

   \min\!\bigl(1,\, e^{-\Delta f / T}\bigr),

where :math:`\Delta f = f(\text{proposal}) - f(\text{current})`.
Accepted moves update the current position; rejected moves leave it
unchanged.  The best-so-far solution is tracked across all accepted and
rejected moves.

Unlike :class:`~cyopt.optimizers.simulated_annealing.SimulatedAnnealing`,
the temperature is **constant** — there is no cooling schedule.

.. note::

   The default ``step_fn`` requires a
   :class:`~cyopt.spaces.TupleSpace` (it closes over ``space.bounds``).
   For non-tuple spaces pass an explicit ``step_fn``.

Classes
-------

.. autoclass:: MCMC
   :members:
   :show-inheritance:

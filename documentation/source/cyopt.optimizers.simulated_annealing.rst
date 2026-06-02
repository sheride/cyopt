.. currentmodule:: cyopt.optimizers.simulated_annealing

cyopt.optimizers.simulated_annealing --- Simulated Annealing
=============================================================

.. automodule:: cyopt.optimizers.simulated_annealing
   :no-members:

:class:`SimulatedAnnealing` uses the Metropolis acceptance criterion with
an exponential cooling schedule.  The temperature at step :math:`t` is

.. math::

   T(t) = T_{\max} \left(\frac{T_{\min}}{T_{\max}}\right)^{t / N},

where :math:`N` is the ``n_iterations`` parameter set at construction
time.  The temperature decreases monotonically from :math:`T_{\max}` to
:math:`T_{\min}` as the search progresses.

.. important::

   The step counter ``_step_count`` **accumulates across consecutive**
   ``run()`` **calls**, so the cooling schedule is continuous when an
   optimiser is run in multiple segments.  The schedule is defined by the
   constructor argument ``n_iterations`` (total lifetime steps), not by
   the argument to any individual ``run()`` call.

.. note::

   The default ``step_fn`` requires a
   :class:`~cyopt.spaces.TupleSpace` (it closes over ``space.bounds``).
   For non-tuple spaces pass an explicit ``step_fn``.

Classes
-------

.. autoclass:: SimulatedAnnealing
   :members:
   :show-inheritance:

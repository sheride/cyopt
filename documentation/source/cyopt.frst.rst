.. currentmodule:: cyopt.frst

cyopt.frst --- FRST wrapper for CYTools
=========================================

.. automodule:: cyopt.frst
   :no-members:

``cyopt.frst`` is an optional integration layer that connects the eight
generic cyopt optimisers to FRST (Fine Regular Star Triangulation)
optimisation of Calabi-Yau hypersurfaces via CYTools.  It is activated by
``import cyopt.frst`` (or ``from cyopt import FRSTFlipGraphSpace``), which
calls :func:`patch_polytope` and monkey-patches the DNA encoding methods
onto :class:`cytools.Polytope`.

Target functions passed to :func:`frst_optimizer` follow cyopt's minimisation
convention: lower return values are better.  To maximise an observable, return
its negative or use :class:`~cyopt.optimizers.GA` target/fitness mode directly.

.. note::

   This module requires CYTools.  Install with ``pip install cyopt[frst]``
   or activate the ``cytools`` conda environment.

FRST optimisation layer
-----------------------

.. raw:: html
   :file: _static/figures/f4_frst.html

Classes
-------

.. autoclass:: FRSTOptimizer
   :members:
   :show-inheritance:

.. autoclass:: FRSTFlipGraphSpace
   :members:
   :show-inheritance:

.. autoclass:: FRSTResult
   :members:
   :show-inheritance:

Functions
---------

.. autofunction:: frst_optimizer

.. autofunction:: patch_polytope

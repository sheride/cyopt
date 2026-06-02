cyopt -- Discrete Optimisation Toolkit
=======================================

**cyopt** is a Python library for discrete optimisation over bounded
integer-tuple search spaces.  It provides eight interchangeable optimisers
with a unified interface, a callback system with early-stopping support,
and checkpoint/resume functionality for long-running searches.  An optional
integration with `CYTools <https://cy.tools>`_ enables FRST optimisation of
Calabi-Yau hypersurfaces via DNA encoding of triangulations.

How to navigate
---------------

.. grid:: 1 1 2 2
   :gutter: 2

   .. grid-item-card:: Tutorials
      :link: tutorials/generic_optimizers
      :link-type: doc

      Worked notebooks covering the generic optimizer interface, FRST
      optimization, and the flip-graph benchmark.

   .. grid-item-card:: API documentation
      :link: cyopt
      :link-type: doc

      Complete class and function reference for all modules, including
      :class:`~cyopt.base.DiscreteOptimizer`, :class:`~cyopt.spaces.TupleSpace`,
      and the FRST integration layer.

   .. grid-item-card:: Optimizers
      :link: cyopt.optimizers
      :link-type: doc

      Reference page for all eight optimisers with the algorithm diagram.

   .. grid-item-card:: Source / citing
      :link: https://github.com/sheride/cyopt
      :link-type: url

      Browse the source on GitHub.  If you use cyopt in published work,
      please cite arXiv:2405.08871 (BibTeX below).

Recommended first path
-----------------------

1. :doc:`Generic optimizer tutorial <tutorials/generic_optimizers>` — the
   fastest way to see all eight optimisers in action on a concrete objective.
2. :doc:`FRST optimization <tutorials/frst_optimization>` — end-to-end
   DNA-encoding workflow on a Calabi-Yau polytope.
3. :doc:`API documentation <cyopt>` once you need precise class and
   function signatures.

Citing cyopt
------------

If you find this work useful, please cite::

    @article{MacFadden:2024him,
        author    = "MacFadden, Nate and Schachner, Andreas and Sheridan, Elijah",
        title     = "{The DNA of Calabi-Yau Hypersurfaces}",
        eprint    = "2405.08871",
        archivePrefix = "arXiv",
        primaryClass  = "hep-th",
        year      = "2024"
    }

Reference lookup
----------------

* :ref:`genindex`
* :ref:`modindex`

.. toctree::
   :hidden:
   :maxdepth: 1
   :caption: Start here

   cyopt

.. toctree::
   :hidden:
   :maxdepth: 1
   :caption: Tutorials

   tutorials/generic_optimizers
   tutorials/frst_optimization
   tutorials/flip_graph_benchmark
   tutorials/mori_cone_cap

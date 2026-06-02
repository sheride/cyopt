.. currentmodule:: cyopt.optimizers.neighbors

cyopt.optimizers.neighbors --- Callable protocols and step utilities
=====================================================================

.. automodule:: cyopt.optimizers.neighbors
   :no-members:

This module defines the callable protocols used by graph-local optimisers
(:class:`~cyopt.optimizers.GreedyWalk`,
:class:`~cyopt.optimizers.BestFirstSearch`,
:class:`~cyopt.optimizers.BasinHopping`,
:class:`~cyopt.optimizers.SimulatedAnnealing`,
:class:`~cyopt.optimizers.MCMC`) and provides the concrete
:func:`random_single_flip` helper.

Type aliases
~~~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :widths: 25 75

   * - Type alias
     - Signature
   * - :data:`NeighborFunction`
     - ``(Node) → Iterable[Node]`` — enumerates neighbours; bounds are **not** part of the protocol (close over a space if needed).
   * - :data:`StepFunction`
     - ``(Node, rng) → Node`` — proposes a single new node.
   * - :data:`PerturbFunction`
     - ``(Node, rng) → Node`` — perturbation for :class:`~cyopt.optimizers.BasinHopping`.
   * - :data:`LocalMinimizeFunction`
     - ``(Node, GraphSpace, evaluate_fn) → Node`` — local minimiser for :class:`~cyopt.optimizers.BasinHopping`.

Functions
---------

.. autofunction:: random_single_flip

.. currentmodule:: cyopt.types

cyopt.types --- Core type definitions
======================================

.. automodule:: cyopt.types
   :no-members:

This module defines the type aliases and the immutable
:class:`Result` dataclass used throughout cyopt.

Type aliases
------------

.. list-table::
   :header-rows: 1
   :widths: 20 80

   * - Type alias
     - Definition
   * - :data:`DNA`
     - ``tuple[int, ...]`` — a candidate solution, one integer per dimension.
   * - :data:`Bounds`
     - ``tuple[tuple[int, int], ...]`` — per-dimension ``(lo_inclusive, hi_inclusive)`` bounds.
   * - :data:`Node`
     - ``Hashable`` — generic node type used by neighbour-callable protocols.  Built-in optimisers currently evaluate nodes as :data:`DNA`, so custom spaces should emit integer-tuple-compatible nodes.
   * - :data:`FitnessFunction`
     - ``Callable[[DNA], float]`` — objective to minimise.
   * - :data:`CallbackInfo`
     - ``dict[str, Any]`` with keys ``iteration``, ``best_value``, ``best_solution``, ``n_evaluations``, ``wall_time``.
   * - :data:`Callback`
     - ``Callable[[CallbackInfo], bool | None]`` — return ``True`` (exactly) to trigger early stopping.

Data classes
------------

.. autoclass:: Result
   :members:
   :show-inheritance:

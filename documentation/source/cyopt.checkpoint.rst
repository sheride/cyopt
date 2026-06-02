.. currentmodule:: cyopt.checkpoint

cyopt.checkpoint --- Checkpoint and resume
===========================================

.. automodule:: cyopt.checkpoint
   :no-members:

Checkpoint support allows long-running optimisations to be interrupted and
resumed without losing progress.  The format is versioned (currently v2),
and a migration path from v1 is provided.

**Checkpoint format v2** stores:

- ``space_kind`` (class name string) and ``space_data`` (a reconstruction
  dict).  :class:`~cyopt.spaces.TupleSpace` is the only space that is
  auto-reconstructed on load; all other space types require the caller to
  pass ``space=`` explicitly to
  :meth:`~cyopt.base.DiscreteOptimizer.load_checkpoint`.
- The full :class:`~cyopt._cache.EvaluationCache` in LRU order (so eviction
  behaviour is identical after resume).
- The RNG bit-generator state (so continued runs are deterministic).
- Optimiser-specific state (e.g. population for :class:`~cyopt.optimizers.GA`,
  step count for :class:`~cyopt.optimizers.SimulatedAnnealing`).

**Usage** — save at regular intervals with
:class:`CheckpointCallback`, or call
:meth:`~cyopt.base.DiscreteOptimizer.save_checkpoint` manually::

    from cyopt import CheckpointCallback, GA, TupleSpace

    cb = CheckpointCallback("run.ckpt", every_n=200)
    opt = GA(fitness_fn, TupleSpace(bounds), callbacks=[cb])
    opt.run(1000)

    # Resume later
    opt2 = GA.load_checkpoint("run.ckpt", fitness_fn)
    opt2.run(500)

Classes
-------

.. autoclass:: CheckpointCallback
   :members:
   :show-inheritance:

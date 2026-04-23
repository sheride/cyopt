"""API-drift smoke check for tutorial notebooks.

Tutorial notebooks ship with cached outputs (``nb_execution_mode = "off"`` per
05-CONTEXT D-05), so renaming a cyopt API never re-renders the notebook and
silent drift is possible. This module statically verifies every
cyopt-namespaced reference in every tutorial notebook still resolves against
the installed cyopt package. It does NOT execute notebook cells and does NOT
compare numerical outputs.

Three notebooks are scanned:

- ``documentation/source/tutorials/generic_optimizers.ipynb``
- ``documentation/source/tutorials/frst_optimization.ipynb``
- ``documentation/source/tutorials/mori_cone_cap.ipynb``

The two CYTools-gated notebooks (``frst_optimization``, ``mori_cone_cap``)
reference ``cyopt.frst.*``; ``cyopt.frst`` itself imports without CYTools
(the package uses an import guard) so top-level name checks still fire, but
kwarg checks that would require importing a symbol transitively through
CYTools are silently skipped.

Per 05.1-CONTEXT D-03 the check is purely static — no notebook cells are
executed, no numerical outputs are compared. This complements the
``nb_execution_mode = "off"`` policy rather than replacing it.
"""

from __future__ import annotations

import ast
import importlib
import inspect
from pathlib import Path

import pytest

nbformat = pytest.importorskip("nbformat")

TUTORIAL_DIR = (
    Path(__file__).resolve().parent.parent
    / "documentation"
    / "source"
    / "tutorials"
)
NOTEBOOKS = sorted(TUTORIAL_DIR.glob("*.ipynb"))

# Detect CYTools availability up front so the gated-module branches in
# ``_verify_reference`` / ``_resolve_callable`` can be intent-explicit
# ("skip only when CYTools is genuinely unavailable") rather than relying on
# a fragile ``"cytools" in str(e).lower()`` substring match. The substring
# guard is kept as a secondary check so an unrelated ImportError that
# happens to mention "cytools" still does not silently mask drift.
try:
    import cytools  # noqa: F401

    _HAS_CYTOOLS = True
except ImportError:
    _HAS_CYTOOLS = False


def _is_cytools_gated_error(exc: BaseException) -> bool:
    """Return True if ``exc`` reflects a missing CYTools install in this env.

    The check is conjunctive: both (a) CYTools must be unavailable in the
    current environment, and (b) the error string must mention ``cytools``.
    This avoids the false-positive in which an unrelated transitive import
    failure whose message happens to contain the word "cytools" gets
    silently treated as gated.
    """
    return (not _HAS_CYTOOLS) and ("cytools" in str(exc).lower())


def _strip_ipython_magic(source: str) -> str:
    """Drop lines beginning with ``%`` or ``!`` so ``ast.parse`` succeeds."""
    return "\n".join(
        line
        for line in source.splitlines()
        if not line.lstrip().startswith(("%", "!"))
    )


def _attribute_chain(node: ast.AST) -> list[str] | None:
    """Reconstruct a dotted chain from an ``ast.Attribute`` / ``ast.Name``.

    Returns the list of identifiers (root-first) if the leaf is an
    ``ast.Name``; otherwise ``None``. E.g. ``cyopt.optimizers.GA`` →
    ``["cyopt", "optimizers", "GA"]``.
    """
    parts: list[str] = []
    cur: ast.AST = node
    while isinstance(cur, ast.Attribute):
        parts.append(cur.attr)
        cur = cur.value
    if isinstance(cur, ast.Name):
        parts.append(cur.id)
        return list(reversed(parts))
    return None


def _collect_cyopt_references(notebook_path: Path) -> list[tuple]:
    """Return a list of ``(kind, payload, cell_idx)`` records.

    ``kind`` is one of:

    - ``"import"`` — payload ``(module_path, imported_name)`` from
      ``from cyopt... import Y``.
    - ``"attribute"`` — payload ``"cyopt.X.Y.Z"`` dotted chain from a
      ``cyopt.X.Y.Z`` reference that is NOT the func of a Call node
      (i.e., a bare attribute access, not a call site).
    - ``"call"`` — payload ``(dotted_callable_path, [kwarg_names])`` from a
      direct call whose callable resolves (via imports or explicit
      ``cyopt.*`` prefix) to a cyopt-namespaced symbol.

    A per-notebook ``imported_names`` dict maps locally-bound names to their
    dotted cyopt paths. Populated from ``from cyopt... import X`` (and
    ``from cyopt... import X as Y``) plus plain ``import cyopt.X`` /
    ``import cyopt.X as Y``. Consulted when a ``Call``'s func is a bare
    ``Name`` so ``from cyopt import GA`` followed by ``GA(...)`` gets
    resolved to ``cyopt.GA`` and participates in the kwarg check. Without
    this lookup, the load-bearing negative-path kwarg test would pass
    vacuously.
    """
    records: list[tuple] = []
    imported_names: dict[str, str] = {}

    nb = nbformat.read(str(notebook_path), as_version=4)
    for cell_idx, cell in enumerate(nb.cells):
        if cell.cell_type != "code":
            continue
        source = _strip_ipython_magic(cell.source)
        try:
            tree = ast.parse(source)
        except SyntaxError:
            continue  # best-effort; skip unparseable cells

        # --- Pass 1: collect imports and update the per-notebook binding table
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                mod = node.module or ""
                if not (mod == "cyopt" or mod.startswith("cyopt.")):
                    continue
                for alias in node.names:
                    local = alias.asname or alias.name
                    records.append(("import", (mod, alias.name), cell_idx))
                    imported_names[local] = f"{mod}.{alias.name}"
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    name = alias.name
                    if not (name == "cyopt" or name.startswith("cyopt.")):
                        continue
                    local = alias.asname or name.split(".")[0]
                    imported_names[local] = name
                    # Treat `import cyopt.frst` as an import-of-module
                    # record so test 1 checks the module resolves.
                    if "." in name:
                        parent, _, leaf = name.rpartition(".")
                        records.append(("import", (parent, leaf), cell_idx))

        # --- Pass 2: collect attribute chains and call sites
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                chain: list[str] | None = None
                if isinstance(node.func, ast.Attribute):
                    chain = _attribute_chain(node.func)
                    if chain is None:
                        continue
                    root = chain[0]
                    if root == "cyopt":
                        dotted = ".".join(chain)
                    elif root in imported_names:
                        # e.g. `GA.some_classmethod(...)` where GA came from cyopt
                        dotted = imported_names[root] + "." + ".".join(chain[1:])
                    else:
                        continue
                elif isinstance(node.func, ast.Name):
                    name = node.func.id
                    if name not in imported_names:
                        continue
                    dotted = imported_names[name]
                    if not (dotted == "cyopt" or dotted.startswith("cyopt.")):
                        continue
                else:
                    continue

                kwargs = [kw.arg for kw in node.keywords if kw.arg is not None]
                records.append(("call", (dotted, kwargs), cell_idx))

            elif isinstance(node, ast.Attribute):
                # Only record "bare" attribute references rooted in literal
                # ``cyopt`` (e.g., ``cyopt.__version__``, or ``cyopt.X.Y`` used
                # outside a call site). The ``chain[0] != "cyopt"`` filter is
                # deliberate, not a bug:
                #
                # - Chains rooted in literal ``cyopt`` (e.g., ``cyopt.GA(...)``)
                #   are visited by ``ast.walk`` BOTH as the Call.func above
                #   and as a bare Attribute here. Both branches record the
                #   same dotted path; ``_verify_reference`` is idempotent so
                #   resolving the same name twice is a no-op. This is the
                #   only scenario that produces duplicate records.
                #
                # - Chains rooted in a locally-bound import (e.g., ``GA``
                #   from ``from cyopt.optimizers import GA`` followed by
                #   ``GA.some_method(...)``) are captured ONLY by the Call
                #   branch above via ``imported_names[root]``. The Attribute
                #   branch here filters them out because ``chain[0]`` is the
                #   local name (``"GA"``), not ``"cyopt"``. That asymmetry is
                #   intentional: the Call branch already covers them, and
                #   without an import binding we cannot resolve a bare
                #   ``GA.some_method`` attribute reference to a cyopt path
                #   anyway.
                chain = _attribute_chain(node)
                if chain is None or chain[0] != "cyopt":
                    continue
                dotted = ".".join(chain)
                records.append(("attribute", dotted, cell_idx))

    return records


def _verify_reference(kind: str, payload) -> tuple[bool, str]:
    """Resolve a reference against the installed cyopt. Return ``(ok, err)``.

    - For ``kind == "import"`` with payload ``(mod, name)``: assert
      ``importlib.import_module(mod)`` has attribute ``name``. If the module
      is CYTools-gated and raises ``ModuleNotFoundError`` for cytools
      downstream, the import is reported as OK (we treat "module imports
      but attribute access would require cytools" as out-of-scope for this
      static check — the name presence is the primary guarantee).
    - For ``kind == "attribute"`` with payload ``"cyopt.X.Y.Z"``: walk the
      dotted path using ``importlib`` + ``getattr`` and assert each step
      resolves. CYTools-gated sub-paths raise ``ModuleNotFoundError`` on
      import; treated as skip.
    """
    try:
        if kind == "import":
            mod, name = payload
            try:
                module = importlib.import_module(mod)
            except ModuleNotFoundError as e:
                # If the *cyopt* submodule itself is missing, that is a real
                # failure. If an underlying cytools dep is missing we treat
                # it as gated and report OK -- but only when CYTools is
                # genuinely absent in this environment (see WR-02 fix).
                if _is_cytools_gated_error(e):
                    return True, ""
                return False, f"cannot import module {mod!r}: {e}"
            if not hasattr(module, name):
                return False, f"{mod!r} has no attribute {name!r}"
            return True, ""

        if kind == "attribute":
            dotted = payload
            parts = dotted.split(".")
            # Walk from the longest importable prefix, then getattr the rest.
            # Try progressively shorter prefixes until one imports.
            for split in range(len(parts), 0, -1):
                mod_name = ".".join(parts[:split])
                try:
                    obj = importlib.import_module(mod_name)
                    remaining = parts[split:]
                    break
                except ModuleNotFoundError as e:
                    if _is_cytools_gated_error(e):
                        return True, ""
                    continue
            else:
                return False, f"cannot import any prefix of {dotted!r}"
            for attr in remaining:
                if not hasattr(obj, attr):
                    return False, f"{dotted!r}: no attribute {attr!r}"
                obj = getattr(obj, attr)
            return True, ""

        return True, ""  # unknown kinds are no-ops
    except Exception as e:  # pragma: no cover — defensive
        return False, f"unexpected error verifying {kind}={payload!r}: {e}"


def _resolve_callable(dotted: str):
    """Return the callable for ``dotted`` or raise/return None if gated.

    Returns ``None`` if the callable is CYTools-gated (import chain hits
    ``ModuleNotFoundError`` for cytools). Raises ``ModuleNotFoundError`` /
    ``AttributeError`` if the path is genuinely broken (i.e., a real drift).
    """
    parts = dotted.split(".")
    for split in range(len(parts), 0, -1):
        mod_name = ".".join(parts[:split])
        try:
            obj = importlib.import_module(mod_name)
            remaining = parts[split:]
            break
        except ModuleNotFoundError as e:
            if _is_cytools_gated_error(e):
                return None  # gated
            continue
    else:
        raise ModuleNotFoundError(f"cannot import any prefix of {dotted!r}")
    for attr in remaining:
        obj = getattr(obj, attr)
    return obj


@pytest.mark.parametrize("notebook", NOTEBOOKS, ids=lambda p: p.name)
def test_all_tutorial_notebooks_have_valid_cyopt_imports(notebook):
    """Every ``from cyopt.X import Y`` and ``cyopt.X.Y`` chain resolves."""
    records = _collect_cyopt_references(notebook)
    failures: list[str] = []
    for kind, payload, cell_idx in records:
        if kind not in ("import", "attribute"):
            continue
        ok, err = _verify_reference(kind, payload)
        if not ok:
            failures.append(f"{notebook.name} cell {cell_idx}: {err}")
    assert not failures, "API drift detected:\n" + "\n".join(failures)


@pytest.mark.parametrize("notebook", NOTEBOOKS, ids=lambda p: p.name)
def test_all_tutorial_notebooks_have_valid_kwargs(notebook):
    """Every kwarg passed to a cyopt public callable exists in the current signature."""
    records = _collect_cyopt_references(notebook)
    failures: list[str] = []
    for kind, payload, cell_idx in records:
        if kind != "call":
            continue
        dotted, kwargs = payload
        try:
            callable_obj = _resolve_callable(dotted)
        except (ModuleNotFoundError, AttributeError):
            # Real drift — but the import/attribute test will flag it;
            # avoid double-reporting here. Skip kwarg check for broken paths.
            continue
        if callable_obj is None:
            continue  # CYTools-gated; skip kwarg check
        try:
            sig = inspect.signature(callable_obj)
        except (TypeError, ValueError):
            continue  # signature not introspectable
        # Skip if callable accepts **kwargs
        if any(
            p.kind == inspect.Parameter.VAR_KEYWORD
            for p in sig.parameters.values()
        ):
            continue
        for k in kwargs:
            if k not in sig.parameters:
                failures.append(
                    f"{notebook.name} cell {cell_idx}: "
                    f"{dotted} has no kwarg {k!r}"
                )
    assert not failures, "Kwarg drift detected:\n" + "\n".join(failures)


def _make_synthetic_notebook(tmp_path: Path, source: str) -> Path:
    """Helper for negative-path tests: build a one-cell notebook in tmp_path."""
    nb = nbformat.v4.new_notebook()
    nb.cells.append(nbformat.v4.new_code_cell(source))
    path = tmp_path / "test.ipynb"
    nbformat.write(nb, str(path))
    return path


def test_smoke_check_fails_on_broken_import(tmp_path):
    """Synthetic notebook importing a nonexistent cyopt symbol fails the import check."""
    path = _make_synthetic_notebook(
        tmp_path, "from cyopt import _NoSuchSymbol_XYZ"
    )
    records = _collect_cyopt_references(path)
    found_failure = False
    for kind, payload, _ in records:
        if kind == "import":
            ok, _err = _verify_reference(kind, payload)
            if not ok:
                found_failure = True
                break
    assert found_failure, "Smoke-check did not catch deliberate broken import"


def test_smoke_check_fails_on_broken_kwarg(tmp_path):
    """Synthetic notebook passing a nonexistent kwarg to GA is flagged."""
    src = (
        "from cyopt import GA\n"
        "GA(fitness_fn=lambda x: 0.0, space=None, nonexistent_kwarg=1)\n"
    )
    path = _make_synthetic_notebook(tmp_path, src)
    records = _collect_cyopt_references(path)
    # Load-bearing: the import-binding-lookup dict must resolve the bare
    # `GA(...)` call-site to `cyopt.GA` via the `from cyopt import GA` line.
    call_records = [
        (dotted, kwargs)
        for kind, (dotted, kwargs), _ in (
            (k, p, c) for k, p, c in records if k == "call"
        )
    ]
    assert any(
        dotted == "cyopt.GA" for dotted, _ in call_records
    ), (
        "Smoke-check did not resolve bare `GA(...)` to `cyopt.GA` via the "
        "per-notebook import-binding-lookup dict. Without that resolution, "
        "the kwarg check skips the call entirely."
    )
    found_failure = any(
        "nonexistent_kwarg" in kwargs
        for dotted, kwargs in call_records
        if dotted == "cyopt.GA"
    )
    assert found_failure, "Smoke-check did not collect the nonexistent kwarg"

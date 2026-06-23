# Copyright (c) 2025-2026 UChicago Argonne, LLC
# SPDX-License-Identifier: LicenseRef-UChicago-Argonne-LLC-License
"""Behaviour when the optional ``diffcalc-core`` backend is absent (:issue:`119`).

These tests simulate ``diffcalc-core`` not being importable, within a
single environment that *does* have the backend installed.  They assert
that:

* the solver module's guarded import block tolerates a missing backend
  (the ``except ImportError`` path);
* :class:`~hklpy2_solvers.diffcalc_solver.DiffcalcSolver` raises a clear,
  actionable :class:`hklpy2.exceptions.SolverError` when the backend is
  absent;
* the package and the ``ad_hoc`` solver are unaffected.

The ``except ImportError`` path is exercised by loading a *fresh, private
copy* of the module under a throwaway name (with ``import diffcalc``
blocked) so the real, cached
:mod:`hklpy2_solvers.diffcalc_solver` module is never mutated and other
test modules keep their original class objects.  The ``__init__`` guard
branch is exercised by monkeypatching the module's
``_DIFFCALC_IMPORT_ERROR`` sentinel, which ``pytest`` restores
automatically.
"""

import builtins
import importlib.util
import re
import sys
from contextlib import nullcontext as does_not_raise

import pytest
from hklpy2.exceptions import SolverError

import hklpy2_solvers.diffcalc_solver as diffcalc_solver


def _load_module_without_diffcalc():
    """Import a private copy of ``diffcalc_solver`` with ``diffcalc`` blocked.

    Loads the module source under a throwaway module name so the real
    cached module is untouched.  Returns the freshly loaded module,
    whose ``_DIFFCALC_IMPORT_ERROR`` is set because the guarded
    ``from diffcalc...`` imports raised ``ImportError``.
    """
    real_import = builtins.__import__

    def blocked_import(name, *args, **kwargs):
        if name == "diffcalc" or name.startswith("diffcalc."):
            raise ImportError("simulated: diffcalc-core not installed")
        return real_import(name, *args, **kwargs)

    spec = importlib.util.spec_from_file_location(
        "hklpy2_solvers._diffcalc_solver_no_backend",
        diffcalc_solver.__file__,
    )
    module = importlib.util.module_from_spec(spec)

    saved = {
        name: mod
        for name, mod in sys.modules.items()
        if name == "diffcalc" or name.startswith("diffcalc.")
    }
    for name in saved:
        del sys.modules[name]
    builtins.__import__ = blocked_import
    try:
        spec.loader.exec_module(module)
    finally:
        builtins.__import__ = real_import
        sys.modules.update(saved)
    return module


@pytest.mark.parametrize(
    "parms, context",
    [
        pytest.param(
            dict(check="error_recorded"),
            does_not_raise(),
            id="guarded import records the ImportError",
        ),
        pytest.param(
            dict(check="names_are_none"),
            does_not_raise(),
            id="guarded names bound to None when backend absent",
        ),
    ],
)
def test_module_imports_without_backend(parms, context):
    with context:
        module = _load_module_without_diffcalc()
        if parms["check"] == "error_recorded":
            assert module._DIFFCALC_IMPORT_ERROR is not None
            assert isinstance(module._DIFFCALC_IMPORT_ERROR, ImportError)
        else:
            assert module.UBCalculation is None
            assert module.Constraints is None
            assert module.Position is None
            assert module.HklCalculation is None
            assert module.DiffcalcException is None


@pytest.mark.parametrize(
    "parms, context",
    [
        pytest.param(
            dict(match="pip install hklpy2-solvers[diffcalc]"),
            pytest.raises(
                SolverError,
                match=re.escape("pip install hklpy2-solvers[diffcalc]"),
            ),
            id="error names the pip extra install route",
        ),
        pytest.param(
            dict(match="conda install -c paulscherrerinstitute diffcalc-core"),
            pytest.raises(
                SolverError,
                match=re.escape("conda install -c paulscherrerinstitute diffcalc-core"),
            ),
            id="error names the conda install route",
        ),
    ],
)
def test_instantiation_raises_when_backend_absent(parms, context, monkeypatch):
    with context:
        # Simulate the backend being unavailable without mutating the
        # real module's class objects: only the sentinel is patched, and
        # pytest restores it after the test.
        monkeypatch.setattr(
            diffcalc_solver,
            "_DIFFCALC_IMPORT_ERROR",
            ImportError("simulated: diffcalc-core not installed"),
        )
        diffcalc_solver.DiffcalcSolver()


@pytest.mark.parametrize(
    "parms, context",
    [
        pytest.param(
            dict(),
            does_not_raise(),
            id="ad_hoc solver and entry-point discovery unaffected",
        ),
    ],
)
def test_ad_hoc_unaffected_when_backend_absent(parms, context, monkeypatch):
    with context:
        import hklpy2

        monkeypatch.setattr(
            diffcalc_solver,
            "_DIFFCALC_IMPORT_ERROR",
            ImportError("simulated: diffcalc-core not installed"),
        )
        # ``diffcalc`` is still advertised by hklpy2's entry points even
        # when the backend cannot be imported.
        assert "diffcalc" in hklpy2.solvers()
        # The ad_hoc solver builds normally.
        diffractometer = hklpy2.creator(geometry="fourcv", solver="ad_hoc", name="ah")
        assert diffractometer is not None

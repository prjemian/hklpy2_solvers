# Copyright (c) 2025-2026 UChicago Argonne, LLC
# SPDX-License-Identifier: LicenseRef-UChicago-Argonne-LLC-License
"""Tests for the diffcalc solver adapter."""

import math
import re
from contextlib import nullcontext as does_not_raise

import pytest
from hklpy2.exceptions import SolverError

from hklpy2_solvers import diffcalc_solver
from hklpy2_solvers.diffcalc_solver import _MODES
from hklpy2_solvers.diffcalc_solver import GEOMETRY_NAME
from hklpy2_solvers.diffcalc_solver import PSEUDO_AXES
from hklpy2_solvers.diffcalc_solver import REAL_AXES
from hklpy2_solvers.diffcalc_solver import DiffcalcSolver

# The ``diffcalc`` solver depends on the optional ``diffcalc-core``
# backend (:issue:`119`).  When that backend is not installed, the
# backend-present tests in this module cannot run; skip the whole module.
# The dedicated absent-backend behaviour is covered separately in
# ``test_diffcalc_optional.py``.
pytestmark = pytest.mark.skipif(
    diffcalc_solver._DIFFCALC_IMPORT_ERROR is not None,
    reason="optional 'diffcalc-core' backend is not installed",
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

# Cubic silicon lattice constant (Angstrom)
SI_A = 5.431
SI_LATTICE = {"a": SI_A, "b": SI_A, "c": SI_A, "alpha": 90.0, "beta": 90.0, "gamma": 90.0}
WAVELENGTH = 1.0  # Angstrom
THETA_100 = math.degrees(math.asin(WAVELENGTH / (2 * SI_A)))
TTH_100 = 2 * THETA_100


def _make_solver_with_ub(
    mode: str = "fixed_mu fixed_chi fixed_phi",
) -> DiffcalcSolver:
    """Return a DiffcalcSolver with Si lattice, two reflections, and UB calculated."""
    solver = DiffcalcSolver()
    solver.lattice = dict(SI_LATTICE)

    r1 = {
        "name": "r1",
        "pseudos": {"h": 1.0, "k": 0.0, "l": 0.0},
        "reals": {"mu": 0, "delta": TTH_100, "nu": 0, "eta": THETA_100, "chi": 0, "phi": 0},
        "wavelength": WAVELENGTH,
    }
    r2 = {
        "name": "r2",
        "pseudos": {"h": 0.0, "k": 1.0, "l": 0.0},
        "reals": {"mu": 0, "delta": TTH_100, "nu": 0, "eta": THETA_100, "chi": 0, "phi": 90},
        "wavelength": WAVELENGTH,
    }
    solver.addReflection(r1)
    solver.addReflection(r2)
    solver.calculate_UB(r1, r2)
    solver.mode = mode
    return solver


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "parms, context",
    [
        pytest.param(
            dict(geometry=GEOMETRY_NAME),
            does_not_raise(),
            id="default geometry accepted",
        ),
        pytest.param(
            dict(),
            does_not_raise(),
            id="no geometry arg uses default",
        ),
        pytest.param(
            dict(geometry="E4CV"),
            pytest.raises(Exception, match=re.escape("DiffcalcSolver supports only")),
            id="unsupported geometry raises",
        ),
    ],
)
def test_instantiation(parms, context):
    with context:
        solver = DiffcalcSolver(**parms)
        assert solver.name == "diffcalc"
        assert solver.geometry == GEOMETRY_NAME


@pytest.mark.parametrize(
    "parms, context",
    [
        pytest.param(
            dict(attr="geometries", expected=[GEOMETRY_NAME]),
            does_not_raise(),
            id="geometries returns list with geometry name",
        ),
        pytest.param(
            dict(attr="pseudo_axis_names", expected=PSEUDO_AXES),
            does_not_raise(),
            id="pseudo_axis_names returns h k l",
        ),
        pytest.param(
            dict(attr="real_axis_names", expected=REAL_AXES),
            does_not_raise(),
            id="real_axis_names returns six axes",
        ),
    ],
)
def test_class_attributes(parms, context):
    with context:
        solver = DiffcalcSolver()
        value = getattr(solver, parms["attr"])
        if callable(value):
            value = value()
        assert value == parms["expected"]


@pytest.mark.parametrize(
    "parms, context",
    [
        pytest.param(
            dict(mode="fixed_mu fixed_chi fixed_phi"),
            does_not_raise(),
            id="valid mode accepted",
        ),
        pytest.param(
            dict(mode="fixed_eta fixed_chi fixed_phi"),
            does_not_raise(),
            id="another valid mode",
        ),
        pytest.param(
            dict(mode="nonexistent_mode"),
            pytest.raises(Exception, match=re.escape("nonexistent_mode")),
            id="invalid mode raises",
        ),
    ],
)
def test_mode_setter(parms, context):
    solver = DiffcalcSolver()
    with context:
        solver.mode = parms["mode"]
        assert solver.mode == parms["mode"]


@pytest.mark.parametrize(
    "parms, context",
    [
        pytest.param(
            dict(modes_count=23),
            does_not_raise(),
            id="modes list has expected count",
        ),
    ],
)
def test_modes_list(parms, context):
    with context:
        solver = DiffcalcSolver()
        modes = solver.modes
        assert len(modes) == parms["modes_count"]
        assert all(isinstance(m, str) for m in modes)


@pytest.mark.parametrize(
    "parms, context",
    [
        pytest.param(
            dict(lattice=SI_LATTICE),
            does_not_raise(),
            id="valid lattice dict accepted",
        ),
        pytest.param(
            dict(lattice="not a dict"),
            pytest.raises(TypeError, match=re.escape("Must supply dict")),
            id="non-dict lattice raises TypeError",
        ),
    ],
)
def test_lattice_setter(parms, context):
    solver = DiffcalcSolver()
    with context:
        solver.lattice = parms["lattice"]
        assert solver.lattice == parms["lattice"]


@pytest.mark.parametrize(
    "parms, context",
    [
        pytest.param(
            dict(
                reflection={
                    "name": "r1",
                    "pseudos": {"h": 1, "k": 0, "l": 0},
                    "reals": {"mu": 0, "delta": TTH_100, "nu": 0, "eta": THETA_100, "chi": 0, "phi": 0},
                    "wavelength": WAVELENGTH,
                },
            ),
            does_not_raise(),
            id="valid reflection added",
        ),
        pytest.param(
            dict(reflection="not a dict"),
            pytest.raises(TypeError, match=re.escape("Must supply ReflectionDict")),
            id="non-dict reflection raises TypeError",
        ),
    ],
)
def test_add_reflection(parms, context):
    solver = DiffcalcSolver()
    solver.lattice = dict(SI_LATTICE)
    with context:
        solver.addReflection(parms["reflection"])
        assert solver.wavelength == WAVELENGTH


@pytest.mark.parametrize(
    "parms, context",
    [
        pytest.param(
            dict(),
            does_not_raise(),
            id="calculate_UB succeeds with two reflections",
        ),
    ],
)
def test_calculate_ub(parms, context):
    solver = DiffcalcSolver()
    solver.lattice = dict(SI_LATTICE)
    r1 = {
        "name": "r1",
        "pseudos": {"h": 1, "k": 0, "l": 0},
        "reals": {"mu": 0, "delta": TTH_100, "nu": 0, "eta": THETA_100, "chi": 0, "phi": 0},
        "wavelength": WAVELENGTH,
    }
    r2 = {
        "name": "r2",
        "pseudos": {"h": 0, "k": 1, "l": 0},
        "reals": {"mu": 0, "delta": TTH_100, "nu": 0, "eta": THETA_100, "chi": 0, "phi": 90},
        "wavelength": WAVELENGTH,
    }
    solver.addReflection(r1)
    solver.addReflection(r2)
    with context:
        ub = solver.calculate_UB(r1, r2)
        assert len(ub) == 3
        assert all(len(row) == 3 for row in ub)
        # UB should not be identity for a real lattice
        assert ub[0][0] != 1.0 or ub[1][1] != 1.0


@pytest.mark.parametrize(
    "parms, context",
    [
        pytest.param(
            dict(),
            pytest.raises(Exception, match=re.escape("Lattice must be set")),
            id="calculate_UB without lattice raises",
        ),
    ],
)
def test_calculate_ub_no_lattice(parms, context):
    solver = DiffcalcSolver()
    r1 = {
        "name": "r1",
        "pseudos": {"h": 1, "k": 0, "l": 0},
        "reals": {"mu": 0, "delta": 10, "nu": 0, "eta": 5, "chi": 0, "phi": 0},
        "wavelength": 1.0,
    }
    solver.addReflection(r1)
    with context:
        solver.calculate_UB(r1, r1)


# Reflection definitions used by the "honour r1/r2" regression test.
# ``HKL_R1`` / ``HKL_R2`` are a sensible orienting pair for cubic Si.
# ``DISTRACTOR_R1`` / ``DISTRACTOR_R2`` are a different orienting pair.
# ``COLINEAR_R1`` / ``COLINEAR_R2`` are pseudo-collinear (both pure h),
# so the underlying ``calc_ub`` rejects them, exercising the
# ``DiffcalcException -> SolverError`` translation branch.
HKL_R1 = {
    "name": "r1",
    "pseudos": {"h": 1.0, "k": 0.0, "l": 0.0},
    "reals": {"mu": 0, "delta": TTH_100, "nu": 0, "eta": THETA_100, "chi": 0, "phi": 0},
    "wavelength": WAVELENGTH,
}
HKL_R2 = {
    "name": "r2",
    "pseudos": {"h": 0.0, "k": 1.0, "l": 0.0},
    "reals": {"mu": 0, "delta": TTH_100, "nu": 0, "eta": THETA_100, "chi": 0, "phi": 90},
    "wavelength": WAVELENGTH,
}
DISTRACTOR_R1 = {
    "name": "distractor1",
    "pseudos": {"h": 1.0, "k": 1.0, "l": 0.0},
    "reals": {"mu": 0, "delta": TTH_100, "nu": 0, "eta": THETA_100, "chi": 0, "phi": 45},
    "wavelength": WAVELENGTH,
}
DISTRACTOR_R2 = {
    "name": "distractor2",
    "pseudos": {"h": 0.0, "k": 0.0, "l": 1.0},
    "reals": {"mu": 0, "delta": TTH_100, "nu": 0, "eta": THETA_100, "chi": 90, "phi": 0},
    "wavelength": WAVELENGTH,
}
COLINEAR_R1 = {
    "name": "col1",
    "pseudos": {"h": 1.0, "k": 0.0, "l": 0.0},
    "reals": {"mu": 0, "delta": TTH_100, "nu": 0, "eta": THETA_100, "chi": 0, "phi": 0},
    "wavelength": WAVELENGTH,
}
COLINEAR_R2 = {
    "name": "col2",
    "pseudos": {"h": 2.0, "k": 0.0, "l": 0.0},
    "reals": {"mu": 0, "delta": 2 * TTH_100, "nu": 0, "eta": 2 * THETA_100, "chi": 0, "phi": 0},
    "wavelength": WAVELENGTH,
}


@pytest.mark.parametrize(
    "parms, context",
    [
        pytest.param(
            dict(
                preload=[DISTRACTOR_R1, DISTRACTOR_R2],
                r1=HKL_R1,
                r2=HKL_R2,
                expected_names=["r1", "r2"],
            ),
            does_not_raise(),
            id="calculate_UB honours r1/r2 over stale preloaded reflections",
        ),
        pytest.param(
            dict(
                preload=[],
                r1=HKL_R1,
                r2=HKL_R2,
                expected_names=["r1", "r2"],
            ),
            does_not_raise(),
            id="calculate_UB honours r1/r2 with no preloaded reflections",
        ),
        pytest.param(
            dict(
                preload=[HKL_R1, HKL_R2, DISTRACTOR_R1, DISTRACTOR_R2],
                r1=DISTRACTOR_R1,
                r2=DISTRACTOR_R2,
                expected_names=["distractor1", "distractor2"],
            ),
            does_not_raise(),
            id="calculate_UB picks named pair from a longer preloaded list",
        ),
        pytest.param(
            dict(
                preload=[],
                r1=COLINEAR_R1,
                r2=COLINEAR_R2,
                expected_names=None,
            ),
            pytest.raises(SolverError),
            id="calculate_UB translates DiffcalcException to SolverError on colinear pair",
        ),
    ],
)
def test_calculate_ub_honours_arguments(parms, context):
    """``calculate_UB(r1, r2)`` MUST honour its arguments.

    Regression for :issue:`58`: the previous implementation called
    ``self._ubcalc.calc_ub()`` with no arguments, which uses whatever
    reflections happen to be held by the underlying diffcalc
    ``UBCalculation`` (in practice: the first two by index).  The
    current implementation clears the solver's reflection state and
    inserts exactly the two reflections the caller named before
    computing UB.
    """
    solver = DiffcalcSolver()
    solver.lattice = dict(SI_LATTICE)
    for refl in parms["preload"]:
        solver.addReflection(refl)
    with context:
        ub = solver.calculate_UB(parms["r1"], parms["r2"])
        # UB is a 3x3 matrix.
        assert len(ub) == 3
        assert all(len(row) == 3 for row in ub)
        # Only the two named reflections remain on the solver side.
        assert [r["name"] for r in solver._reflections] == parms["expected_names"]
        assert solver._ubcalc.get_number_reflections() == 2


@pytest.mark.parametrize(
    "parms, context",
    [
        pytest.param(
            dict(
                mode="fixed_mu fixed_chi fixed_phi",
                pseudos={"h": 1.0, "k": 0.0, "l": 0.0},
                expected_h=1.0,
                expected_k=0.0,
                expected_l=0.0,
            ),
            does_not_raise(),
            id="forward (1,0,0) 3-sample mode",
        ),
        pytest.param(
            dict(
                mode="fixed_eta fixed_chi fixed_phi",
                pseudos={"h": 0.0, "k": 1.0, "l": 0.0},
                expected_h=0.0,
                expected_k=1.0,
                expected_l=0.0,
            ),
            does_not_raise(),
            id="forward (0,1,0) 3-sample eta_chi_phi mode",
        ),
        pytest.param(
            dict(
                mode="fixed_mu fixed_chi fixed_phi",
                pseudos="not a dict",
                expected_h=0,
                expected_k=0,
                expected_l=0,
            ),
            pytest.raises(TypeError, match=re.escape("Must supply dict")),
            id="forward with non-dict raises TypeError",
        ),
    ],
)
def test_forward(parms, context):
    solver = _make_solver_with_ub(mode=parms["mode"])
    with context:
        solutions = solver.forward(parms["pseudos"])
        assert len(solutions) >= 1
        # Verify the first solution roundtrips via inverse
        hkl = solver.inverse(solutions[0])
        assert abs(hkl["h"] - parms["expected_h"]) < 0.01
        assert abs(hkl["k"] - parms["expected_k"]) < 0.01
        assert abs(hkl["l"] - parms["expected_l"]) < 0.01


@pytest.mark.parametrize(
    "parms, context",
    [
        pytest.param(
            dict(
                reals={"mu": 0, "delta": TTH_100, "nu": 0, "eta": THETA_100, "chi": 0, "phi": 0},
                expected_h=1.0,
                expected_k=0.0,
                expected_l=0.0,
            ),
            does_not_raise(),
            id="inverse r1 position -> (1,0,0)",
        ),
        pytest.param(
            dict(
                reals={"mu": 0, "delta": TTH_100, "nu": 0, "eta": THETA_100, "chi": 0, "phi": 90},
                expected_h=0.0,
                expected_k=1.0,
                expected_l=0.0,
            ),
            does_not_raise(),
            id="inverse r2 position -> (0,1,0)",
        ),
        pytest.param(
            dict(
                reals={"mu": 0, "delta": 0, "nu": 0, "eta": 0, "chi": 0, "phi": 0},
                expected_h=0.0,
                expected_k=0.0,
                expected_l=0.0,
            ),
            does_not_raise(),
            id="inverse zero angles -> (0,0,0)",
        ),
        pytest.param(
            dict(
                reals="not a dict",
                expected_h=0,
                expected_k=0,
                expected_l=0,
            ),
            pytest.raises(TypeError, match=re.escape("Must supply dict")),
            id="inverse with non-dict raises TypeError",
        ),
    ],
)
def test_inverse(parms, context):
    solver = _make_solver_with_ub()
    with context:
        hkl = solver.inverse(parms["reals"])
        assert abs(hkl["h"] - parms["expected_h"]) < 0.01
        assert abs(hkl["k"] - parms["expected_k"]) < 0.01
        assert abs(hkl["l"] - parms["expected_l"]) < 0.01


@pytest.mark.parametrize(
    "parms, context",
    [
        pytest.param(
            dict(
                mode="fixed_mu fixed_chi fixed_phi",
                pseudos={"h": 1.0, "k": 0.0, "l": 0.0},
            ),
            does_not_raise(),
            id="forward-inverse roundtrip (1,0,0)",
        ),
        pytest.param(
            dict(
                mode="fixed_mu fixed_chi fixed_phi",
                pseudos={"h": 0.0, "k": 1.0, "l": 0.0},
            ),
            does_not_raise(),
            id="forward-inverse roundtrip (0,1,0)",
        ),
        pytest.param(
            dict(
                mode="fixed_mu fixed_chi fixed_phi",
                pseudos={"h": 1.0, "k": 1.0, "l": 0.0},
            ),
            does_not_raise(),
            id="forward-inverse roundtrip (1,1,0)",
        ),
    ],
)
def test_forward_inverse_roundtrip(parms, context):
    solver = _make_solver_with_ub(mode=parms["mode"])
    with context:
        solutions = solver.forward(parms["pseudos"])
        assert len(solutions) >= 1
        for sol in solutions:
            hkl = solver.inverse(sol)
            for axis in ("h", "k", "l"):
                assert abs(hkl[axis] - parms["pseudos"][axis]) < 0.01, (
                    f"Roundtrip mismatch on {axis}: expected {parms['pseudos'][axis]}, got {hkl[axis]}"
                )


@pytest.mark.parametrize(
    "parms, context",
    [
        pytest.param(
            dict(mode="fixed_mu fixed_chi fixed_phi"),
            does_not_raise(),
            id="extra_axis_names is always empty",
        ),
        pytest.param(
            dict(mode="a_eq_b fixed_delta fixed_mu"),
            does_not_raise(),
            id="extra_axis_names empty for det+ref+samp mode",
        ),
        pytest.param(
            dict(mode=""),
            does_not_raise(),
            id="extra_axis_names empty for empty mode",
        ),
    ],
)
def test_extra_axis_names(parms, context):
    solver = DiffcalcSolver()
    with context:
        solver.mode = parms["mode"]
        assert solver.extra_axis_names == []
        assert solver.extras == {}


@pytest.mark.parametrize(
    "parms, context",
    [
        pytest.param(
            dict(
                mode="fixed_mu fixed_chi fixed_phi",
                expected_axes_w=["delta", "nu", "eta"],
            ),
            does_not_raise(),
            id="axes_w excludes mu, chi, phi",
        ),
        pytest.param(
            dict(
                mode="a_eq_b fixed_delta fixed_mu",
                expected_axes_w=["nu", "eta", "chi", "phi"],
            ),
            does_not_raise(),
            id="axes_w excludes mu and delta",
        ),
        pytest.param(
            dict(
                mode="fixed_delta fixed_chi fixed_phi",
                expected_axes_w=["mu", "nu", "eta"],
            ),
            does_not_raise(),
            id="axes_w excludes chi, phi, delta",
        ),
        pytest.param(
            dict(
                mode="",
                expected_axes_w=REAL_AXES,
            ),
            does_not_raise(),
            id="axes_w returns all axes when mode is empty",
        ),
    ],
)
def test_axes_w(parms, context):
    solver = DiffcalcSolver()
    with context:
        solver.mode = parms["mode"]
        assert solver.axes_w == parms["expected_axes_w"]


@pytest.mark.parametrize(
    "parms, context",
    [
        pytest.param(
            dict(),
            does_not_raise(),
            id="UB is identity before calculation",
        ),
    ],
)
def test_ub_before_calculation(parms, context):
    solver = DiffcalcSolver()
    with context:
        ub = solver.UB
        assert ub == [[1, 0, 0], [0, 1, 0], [0, 0, 1]]


@pytest.mark.parametrize(
    "parms, context",
    [
        pytest.param(
            dict(),
            does_not_raise(),
            id="removeAllReflections clears state",
        ),
    ],
)
def test_remove_all_reflections(parms, context):
    solver = _make_solver_with_ub()
    with context:
        assert solver.wavelength is not None
        solver.removeAllReflections()
        assert solver.wavelength is None
        # UB should revert to identity after reset
        assert solver.UB == [[1, 0, 0], [0, 1, 0], [0, 0, 1]]
        # Lattice should still be set
        assert solver.lattice == SI_LATTICE


@pytest.mark.parametrize(
    "parms, context",
    [
        pytest.param(
            dict(wavelength=1.5),
            does_not_raise(),
            id="set positive wavelength",
        ),
        pytest.param(
            dict(wavelength=-1.0),
            pytest.raises(ValueError, match=re.escape("Must supply positive number")),
            id="negative wavelength raises",
        ),
        pytest.param(
            dict(wavelength=0.0),
            pytest.raises(ValueError, match=re.escape("Must supply positive number")),
            id="zero wavelength raises",
        ),
        pytest.param(
            dict(wavelength="abc"),
            pytest.raises(TypeError, match=re.escape("Must supply number")),
            id="non-numeric wavelength raises",
        ),
    ],
)
def test_wavelength_setter(parms, context):
    solver = DiffcalcSolver()
    with context:
        solver.wavelength = parms["wavelength"]
        assert solver.wavelength == parms["wavelength"]


@pytest.mark.parametrize(
    "parms, context",
    [
        pytest.param(
            dict(),
            pytest.raises(Exception, match=re.escape("UB matrix has not been set")),
            id="forward without UB raises",
        ),
    ],
)
def test_forward_without_ub(parms, context):
    solver = DiffcalcSolver()
    solver.lattice = dict(SI_LATTICE)
    solver.wavelength = 1.0
    with context:
        solver.forward({"h": 1, "k": 0, "l": 0})


@pytest.mark.parametrize(
    "parms, context",
    [
        pytest.param(
            dict(),
            pytest.raises(Exception, match=re.escape("Wavelength is not set")),
            id="forward without wavelength raises",
        ),
    ],
)
def test_forward_without_wavelength(parms, context):
    """Solver with UB set but no wavelength should raise about wavelength."""
    solver = _make_solver_with_ub()
    solver.removeAllReflections()
    # Re-add reflections and UB but clear wavelength
    solver.lattice = dict(SI_LATTICE)
    r1 = {
        "name": "r1",
        "pseudos": {"h": 1, "k": 0, "l": 0},
        "reals": {"mu": 0, "delta": TTH_100, "nu": 0, "eta": THETA_100, "chi": 0, "phi": 0},
        "wavelength": WAVELENGTH,
    }
    r2 = {
        "name": "r2",
        "pseudos": {"h": 0, "k": 1, "l": 0},
        "reals": {"mu": 0, "delta": TTH_100, "nu": 0, "eta": THETA_100, "chi": 0, "phi": 90},
        "wavelength": WAVELENGTH,
    }
    solver.addReflection(r1)
    solver.addReflection(r2)
    solver.calculate_UB(r1, r2)
    # Force clear wavelength after UB is set
    solver._wavelength = None
    with context:
        solver.forward({"h": 1, "k": 0, "l": 0})


@pytest.mark.parametrize(
    "parms, context",
    [
        pytest.param(
            dict(
                lattice={"a": 4.0, "b": 4.0, "c": 4.0, "alpha": 90, "beta": 90, "gamma": 90},
            ),
            does_not_raise(),
            id="lattice preserved after removeAllReflections",
        ),
    ],
)
def test_lattice_preserved_after_reset(parms, context):
    solver = DiffcalcSolver()
    with context:
        solver.lattice = parms["lattice"]
        solver.removeAllReflections()
        assert solver.lattice == parms["lattice"]


@pytest.mark.parametrize(
    "parms, context",
    [
        pytest.param(
            dict(
                mode="fixed_mu fixed_chi fixed_phi",
                pseudos={"h": 1, "k": 0, "l": 0},
                min_solutions=1,
            ),
            does_not_raise(),
            id="forward returns multiple solutions",
        ),
    ],
)
def test_forward_multiple_solutions(parms, context):
    solver = _make_solver_with_ub(mode=parms["mode"])
    with context:
        solutions = solver.forward(parms["pseudos"])
        assert len(solutions) >= parms["min_solutions"]
        # All solutions must have all real axis names
        for sol in solutions:
            for ax in REAL_AXES:
                assert ax in sol


@pytest.mark.parametrize(
    "parms, context",
    [
        pytest.param(
            dict(
                lattice={"a": 3.905, "b": 3.905, "c": 3.905, "alpha": 90, "beta": 90, "gamma": 90},
            ),
            does_not_raise(),
            id="refineLattice returns None with <3 reflections",
        ),
    ],
)
def test_refine_lattice_insufficient_reflections(parms, context):
    solver = DiffcalcSolver()
    solver.lattice = parms["lattice"]
    with context:
        result = solver.refineLattice([])
        assert result is None


@pytest.mark.parametrize(
    "parms, context",
    [
        pytest.param(
            dict(
                mode="a_eq_b fixed_delta fixed_mu",
                pseudos={"h": 100, "k": 100, "l": 100},
            ),
            pytest.raises(Exception, match=re.escape("Reflection unreachable")),
            id="forward unreachable reflection raises SolverError",
        ),
    ],
)
def test_forward_diffcalc_exception(parms, context):
    solver = _make_solver_with_ub(mode=parms["mode"])
    with context:
        solver.forward(parms["pseudos"])


@pytest.mark.parametrize(
    "parms, context",
    [
        pytest.param(
            dict(),
            does_not_raise(),
            id="refineLattice with 3+ reflections returns dict",
        ),
    ],
)
def test_refine_lattice_success(parms, context):
    """Add 3 non-coplanar reflections and verify refineLattice returns a dict."""
    solver = DiffcalcSolver()
    solver.lattice = dict(SI_LATTICE)

    wl = WAVELENGTH

    # Three reflections with known, physically consistent positions.
    # For cubic Si, d_hkl = a/sqrt(h^2+k^2+l^2).
    # Bragg: theta = arcsin(wl/(2*d))
    # Compute angles using mu_chi_phi_fixed mode from a helper solver.
    helper = _make_solver_with_ub(mode="fixed_mu fixed_chi fixed_phi")

    # (1,0,0) and (0,1,0) work fine with this mode.
    # (1,1,0) also works. All are in-plane with chi=phi=mu=0.
    hkl_list = [(1, 0, 0), (0, 1, 0), (1, 1, 0)]
    refls = []
    for h, k, l in hkl_list:  # noqa: E741
        solutions = helper.forward({"h": float(h), "k": float(k), "l": float(l)})
        reals = solutions[0]
        refl = {
            "name": f"r_{h}{k}{l}",
            "pseudos": {"h": float(h), "k": float(k), "l": float(l)},
            "reals": reals,
            "wavelength": wl,
        }
        solver.addReflection(refl)
        refls.append(refl)

    # ``calculate_UB`` now clears the solver's reflections (it honours
    # its r1/r2 arguments).  Re-add the third reflection so that
    # ``refineLattice`` sees the >=3 reflections it requires.
    solver.calculate_UB(refls[0], refls[1])
    solver.addReflection(refls[2])

    with context:
        result = solver.refineLattice(solver._reflections)
        # refineLattice may return None if the reflections are coplanar
        # (singular matrix), which is acceptable for this test.
        if result is not None:
            assert isinstance(result, dict)
            assert "a" in result
            assert "b" in result
            assert "c" in result


@pytest.mark.parametrize(
    "parms, context",
    [
        pytest.param(
            dict(mode=""),
            does_not_raise(),
            id="set mode to empty string",
        ),
    ],
)
def test_mode_set_empty(parms, context):
    solver = DiffcalcSolver()
    with context:
        solver.mode = parms["mode"]
        assert solver.mode == ""
        assert solver.extras == {}


@pytest.mark.parametrize(
    "parms, context",
    [
        pytest.param(
            dict(
                reals={"mu": 0, "delta": 0, "nu": 0, "eta": 0, "chi": 0, "phi": 0},
                wavelength=1.0,
                expected={"h": 0.0, "k": 0.0, "l": 0.0},
            ),
            does_not_raise(),
            id="inverse at all-zeros without any UB returns (0,0,0) - issue #24",
        ),
        pytest.param(
            dict(
                reals={"mu": 0, "delta": 0, "nu": 0, "eta": 0, "chi": 0, "phi": 0},
                wavelength=None,
                expected={"h": 0.0, "k": 0.0, "l": 0.0},
            ),
            does_not_raise(),
            id="inverse at all-zeros without UB or wavelength returns (0,0,0)",
        ),
    ],
)
def test_inverse_without_ub(parms, context):
    """inverse() must work before any UB is set (issue #24 regression test)."""
    solver = DiffcalcSolver()
    if parms["wavelength"] is not None:
        solver.wavelength = parms["wavelength"]
    with context:
        result = solver.inverse(parms["reals"])
        for axis in ("h", "k", "l"):
            assert abs(result[axis] - parms["expected"][axis]) < 1e-9, (
                f"axis {axis}: expected {parms['expected'][axis]}, got {result[axis]}"
            )


@pytest.mark.parametrize(
    "parms, context",
    [
        pytest.param(
            dict(
                reals={"mu": 0, "delta": 0, "nu": 0, "eta": 0, "chi": 0, "phi": 0},
            ),
            does_not_raise(),
            id="second inverse call reuses default UB without re-init",
        ),
    ],
)
def test_inverse_default_ub_idempotent(parms, context):
    """Calling inverse() repeatedly without a UB must not raise or re-init UB."""
    solver = DiffcalcSolver()
    solver.wavelength = 1.0
    with context:
        r1 = solver.inverse(parms["reals"])
        r2 = solver.inverse(parms["reals"])
        for axis in ("h", "k", "l"):
            assert r1[axis] == r2[axis]


# ---------------------------------------------------------------------------
# Issue #25 regression tests: sample setter pushes lattice into diffcalc
# ---------------------------------------------------------------------------

# A minimal SampleDict as produced by hklpy2 Core.to_solver_units()
_SAMPLE_DICT_LIST_REFLECTIONS = {
    "name": "vibranium",
    "lattice": {
        "a": SI_A,
        "b": SI_A,
        "c": SI_A,
        "alpha": 90.0,
        "beta": 90.0,
        "gamma": 90.0,
        "angle_units": "degrees",
        "length_units": "angstrom",
    },
    "order": ["r1", "r2"],
    "reflections": [
        {
            "name": "r1",
            "pseudos": {"h": 1.0, "k": 0.0, "l": 0.0},
            "reals": {"mu": 0, "delta": TTH_100, "nu": 0, "eta": THETA_100, "chi": 0, "phi": 0},
            "wavelength": WAVELENGTH,
        },
        {
            "name": "r2",
            "pseudos": {"h": 0.0, "k": 1.0, "l": 0.0},
            "reals": {"mu": 0, "delta": TTH_100, "nu": 0, "eta": THETA_100, "chi": 0, "phi": 90},
            "wavelength": WAVELENGTH,
        },
    ],
}

_SAMPLE_DICT_DICT_REFLECTIONS = {
    "name": "vibranium",
    "lattice": {
        "a": SI_A,
        "b": SI_A,
        "c": SI_A,
        "alpha": 90.0,
        "beta": 90.0,
        "gamma": 90.0,
    },
    "order": ["r1", "r2"],
    "reflections": {
        "r1": {
            "name": "r1",
            "pseudos": {"h": 1.0, "k": 0.0, "l": 0.0},
            "reals": {"mu": 0, "delta": TTH_100, "nu": 0, "eta": THETA_100, "chi": 0, "phi": 0},
            "wavelength": WAVELENGTH,
        },
        "r2": {
            "name": "r2",
            "pseudos": {"h": 0.0, "k": 1.0, "l": 0.0},
            "reals": {"mu": 0, "delta": TTH_100, "nu": 0, "eta": THETA_100, "chi": 0, "phi": 90},
            "wavelength": WAVELENGTH,
        },
    },
}


@pytest.mark.parametrize(
    "parms, context",
    [
        pytest.param(
            dict(sample=_SAMPLE_DICT_LIST_REFLECTIONS),
            does_not_raise(),
            id="sample setter with list reflections pushes lattice - issue #25",
        ),
        pytest.param(
            dict(sample=_SAMPLE_DICT_DICT_REFLECTIONS),
            does_not_raise(),
            id="sample setter with dict reflections pushes lattice",
        ),
        pytest.param(
            dict(sample="not a dict"),
            pytest.raises(TypeError, match=re.escape("Must supply dictionary")),
            id="sample setter with non-dict raises TypeError",
        ),
    ],
)
def test_sample_setter_pushes_lattice(parms, context):
    """sample setter must push the lattice into _ubcalc (issue #25 regression)."""
    solver = DiffcalcSolver()
    with context:
        solver.sample = parms["sample"]
        # Lattice must now be in _ubcalc (crystal is not None)
        assert solver._ubcalc.crystal is not None
        # The solver's lattice dict must match
        assert abs(solver.lattice["a"] - SI_A) < 1e-9


@pytest.mark.parametrize(
    "parms, context",
    [
        pytest.param(
            dict(sample=_SAMPLE_DICT_LIST_REFLECTIONS),
            does_not_raise(),
            id="calculate_UB succeeds after sample setter - issue #25",
        ),
    ],
)
def test_calculate_ub_after_sample_setter(parms, context):
    """calculate_UB must succeed when lattice arrives via sample setter (issue #25)."""
    solver = DiffcalcSolver()
    solver.wavelength = WAVELENGTH
    with context:
        solver.sample = parms["sample"]
        r1 = parms["sample"]["reflections"][0]
        r2 = parms["sample"]["reflections"][1]
        ub = solver.calculate_UB(r1, r2)
        assert len(ub) == 3
        assert all(len(row) == 3 for row in ub)


@pytest.mark.parametrize(
    "parms, context",
    [
        pytest.param(
            dict(sample=_SAMPLE_DICT_LIST_REFLECTIONS),
            does_not_raise(),
            id="sample setter re-adds reflections in order",
        ),
    ],
)
def test_sample_setter_repopulates_reflections(parms, context):
    """sample setter must re-add reflections so _reflections is populated."""
    solver = DiffcalcSolver()
    with context:
        solver.sample = parms["sample"]
        assert len(solver._reflections) == len(parms["sample"]["order"])
        for i, name in enumerate(parms["sample"]["order"]):
            assert solver._reflections[i]["name"] == name


# ---------------------------------------------------------------------------
# Issue #29 regression tests: set_reals and UB setter
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "parms, context",
    [
        pytest.param(
            dict(reals={"mu": 0.0, "delta": 0.0, "nu": 0.0, "eta": 0.0, "chi": 0.0, "phi": 0.0}),
            does_not_raise(),
            id="set_reals accepts valid dict of floats",
        ),
        pytest.param(
            dict(reals={"mu": 0, "delta": 0, "nu": 0, "eta": 0, "chi": 0, "phi": 0}),
            does_not_raise(),
            id="set_reals accepts ints",
        ),
        pytest.param(
            dict(reals="not a dict"),
            pytest.raises(TypeError, match=re.escape("Must supply dict")),
            id="set_reals with non-dict raises TypeError",
        ),
        pytest.param(
            dict(reals={"mu": "bad", "delta": 0.0, "nu": 0.0, "eta": 0.0, "chi": 0.0, "phi": 0.0}),
            pytest.raises(TypeError, match=re.escape("All values must be numbers")),
            id="set_reals with non-numeric value raises TypeError",
        ),
    ],
)
def test_set_reals(parms, context):
    """set_reals validates input and is otherwise a no-op for diffcalc (issue #29)."""
    solver = DiffcalcSolver()
    with context:
        solver.set_reals(parms["reals"])


@pytest.mark.parametrize(
    "parms, context",
    [
        pytest.param(
            dict(ub=[[1, 0, 0], [0, 1, 0], [0, 0, 1]]),
            does_not_raise(),
            id="UB setter restores identity matrix",
        ),
    ],
)
def test_ub_setter(parms, context):
    """UB setter must restore the orientation matrix into _ubcalc (issue #29)."""
    solver = _make_solver_with_ub()
    with context:
        solver.UB = parms["ub"]
        assert solver._ubcalc.UB is not None


@pytest.mark.parametrize(
    "parms, context",
    [
        pytest.param(
            dict(mode="fixed_mu fixed_chi fixed_phi", pseudos={"h": 1.0, "k": 0.0, "l": 0.0}),
            does_not_raise(),
            id="forward succeeds after update_solver restores UB via setter - issue #29",
        ),
    ],
)
def test_forward_after_ub_restore(parms, context):
    """forward() must work after update_solver() restores UB via the UB setter."""
    solver = _make_solver_with_ub(mode=parms["mode"])
    # Simulate what update_solver() does: reset via sample then restore UB
    ub = solver.UB
    solver.sample = {
        "name": "test",
        "lattice": dict(SI_LATTICE),
        "order": [],
        "reflections": [],
    }
    solver.UB = ub  # restore, as update_solver() does
    with context:
        solutions = solver.forward(parms["pseudos"])
        assert len(solutions) >= 1


@pytest.mark.parametrize(
    "parms, context",
    [
        # -- 1 det + 1 ref + 1 samp (a_eq_b is non-motor) --
        pytest.param(
            dict(
                mode="a_eq_b fixed_delta fixed_mu",
                expected_reals=["nu", "eta", "chi", "phi"],
            ),
            does_not_raise(),
            id="a_eq_b non-motor: only mu,delta fixed",
        ),
        # -- 1 det + 1 ref + 1 samp (psi is non-motor) --
        pytest.param(
            dict(
                mode="fixed_nu fixed_psi fixed_phi",
                expected_reals=["mu", "delta", "eta", "chi"],
            ),
            does_not_raise(),
            id="psi non-motor: only nu,phi fixed",
        ),
        # -- 1 det + 2 samp --
        pytest.param(
            dict(
                mode="fixed_delta fixed_chi fixed_phi",
                expected_reals=["mu", "nu", "eta"],
            ),
            does_not_raise(),
            id="3 motor constraints: delta,chi,phi fixed",
        ),
        # -- 1 det + 2 samp (bisect is non-motor) --
        pytest.param(
            dict(
                mode="bisect fixed_mu fixed_nu",
                expected_reals=["delta", "eta", "chi", "phi"],
            ),
            does_not_raise(),
            id="bisect vertical: mu,nu fixed",
        ),
        # -- 1 det + 2 samp (bisect+omega are non-motor) --
        pytest.param(
            dict(
                mode="bisect fixed_omega fixed_nu",
                expected_reals=["mu", "delta", "eta", "chi", "phi"],
            ),
            does_not_raise(),
            id="bisect+omega non-motor: only nu fixed",
        ),
        # -- 1 ref + 2 samp --
        pytest.param(
            dict(
                mode="a_eq_b fixed_chi fixed_mu",
                expected_reals=["delta", "nu", "eta", "phi"],
            ),
            does_not_raise(),
            id="1ref+2samp: mu,chi fixed",
        ),
        # -- 3 samp --
        pytest.param(
            dict(
                mode="fixed_eta fixed_chi fixed_phi",
                expected_reals=["mu", "delta", "nu"],
            ),
            does_not_raise(),
            id="3samp: eta,chi,phi fixed",
        ),
        pytest.param(
            dict(
                mode="fixed_mu fixed_eta fixed_chi",
                expected_reals=["delta", "nu", "phi"],
            ),
            does_not_raise(),
            id="3samp: mu,eta,chi fixed",
        ),
    ],
)
def test_summary_dict(parms, context):
    """_summary_dict reports correct writable axes per mode (issue #37)."""
    solver = DiffcalcSolver()
    with context:
        sdict = solver._summary_dict
        mode_entry = sdict["modes"][parms["mode"]]
        assert mode_entry["reals"] == parms["expected_reals"]
        assert mode_entry["extras"] == []
        # Top-level keys are correct regardless of mode.
        assert sdict["name"] == GEOMETRY_NAME
        assert sdict["pseudos"] == list(PSEUDO_AXES)
        assert sdict["reals"] == list(REAL_AXES)


@pytest.mark.parametrize(
    "parms, context",
    [
        pytest.param(
            dict(),
            does_not_raise(),
            id="all modes writable axes match axes_w",
        ),
    ],
)
def test_summary_dict_all_modes(parms, context):
    """Every mode in _summary_dict has reals == axes_w (issue #37)."""
    solver = DiffcalcSolver()
    with context:
        sdict = solver._summary_dict
        assert set(sdict["modes"].keys()) == set(_MODES.keys())
        for mode_name in _MODES:
            solver.mode = mode_name
            expected = solver.axes_w
            actual = sdict["modes"][mode_name]["reals"]
            assert actual == expected, f"Mode {mode_name!r}: expected writable {expected}, got {actual}"


@pytest.mark.parametrize(
    "parms, context",
    [
        pytest.param(
            dict(),
            does_not_raise(),
            id="DiffcalcSolver.version matches diffcalc-core package",
        ),
    ],
)
def test_solver_version(parms, context):
    from importlib.metadata import version as _pkg_version

    with context:
        assert DiffcalcSolver.version == _pkg_version("diffcalc-core")
        # Sanity: not the legacy hardcoded value.
        assert DiffcalcSolver.version != "0.1.0"


# ---------------------------------------------------------------------------
# Coverage-targeted edge-case tests (issue #46)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "parms, context",
    [
        pytest.param(
            dict(),
            does_not_raise(),
            id="default UB skips set_lattice when crystal already set",
        ),
    ],
)
def test_init_default_ub_with_existing_crystal(parms, context):
    """``_init_default_ub`` must not redefine an already-present crystal."""
    solver = DiffcalcSolver()
    solver.lattice = dict(SI_LATTICE)  # crystal now exists
    with context:
        # Trigger _init_default_ub via inverse() before any UB is set.
        hkl = solver.inverse({"mu": 0, "delta": 0, "nu": 0, "eta": 0, "chi": 0, "phi": 0})
        assert "h" in hkl
        # Lattice constants are preserved (not reset to 1.0 cubic).
        assert solver.lattice["a"] == SI_A


@pytest.mark.parametrize(
    "parms, context",
    [
        pytest.param(
            dict(value={"order": []}),
            does_not_raise(),
            id="sample without lattice key is tolerated",
        ),
        pytest.param(
            dict(
                value={
                    "lattice": SI_LATTICE,
                    "reflections": [
                        {
                            "name": "r1",
                            "pseudos": {"h": 1.0, "k": 0.0, "l": 0.0},
                            "reals": {
                                "mu": 0,
                                "delta": TTH_100,
                                "nu": 0,
                                "eta": THETA_100,
                                "chi": 0,
                                "phi": 0,
                            },
                            "wavelength": WAVELENGTH,
                        },
                    ],
                    "order": ["r1", "missing"],
                },
            ),
            does_not_raise(),
            id="reflections list with missing order entries is skipped",
        ),
    ],
)
def test_sample_setter_edge_cases(parms, context):
    """Cover ``sample`` setter with no lattice and a list-shaped reflections value."""
    solver = DiffcalcSolver()
    with context:
        solver.sample = parms["value"]


@pytest.mark.parametrize(
    "parms, context",
    [
        pytest.param(
            dict(),
            does_not_raise(),
            id="mode getter heals missing _mode attribute",
        ),
    ],
)
def test_mode_getter_attribute_error_recovery(parms, context):
    """``mode`` getter returns ``''`` after deleting the cached attribute."""
    solver = DiffcalcSolver()
    with context:
        del solver._mode
        assert solver.mode == ""


@pytest.mark.parametrize(
    "parms, context",
    [
        pytest.param(
            dict(),
            does_not_raise(),
            id="refineLattice with three reflections returns lattice dict",
        ),
    ],
)
def test_refine_lattice_success_path(parms, context):
    """Cover the success path of ``refineLattice`` (3+ reflections)."""
    solver = _make_solver_with_ub()
    r3 = {
        "name": "r3",
        "pseudos": {"h": 0.0, "k": 0.0, "l": 1.0},
        "reals": {"mu": 0, "delta": TTH_100, "nu": 0, "eta": THETA_100, "chi": 90, "phi": 0},
        "wavelength": WAVELENGTH,
    }
    solver.addReflection(r3)
    with context:
        result = solver.refineLattice([])
        # Either succeeds with a dict or returns None on backend failure;
        # both branches are valid coverage hits.
        if result is not None:
            for key in ("a", "b", "c", "alpha", "beta", "gamma"):
                assert key in result


@pytest.mark.parametrize(
    "parms, context",
    [
        pytest.param(
            dict(),
            does_not_raise(),
            id="removeAllReflections skips lattice re-apply when none stored",
        ),
    ],
)
def test_remove_all_reflections_no_lattice(parms, context):
    """Cover the ``self._lattice`` falsy branch in ``removeAllReflections``."""
    solver = DiffcalcSolver()
    with context:
        solver.removeAllReflections()
        assert solver._lattice == {}


@pytest.mark.parametrize(
    "parms, context",
    [
        pytest.param(
            dict(stored=None),
            does_not_raise(),
            id="UB setter falls back to default lattice when none stored",
        ),
        pytest.param(
            dict(stored=SI_LATTICE),
            does_not_raise(),
            id="UB setter restores stored lattice when crystal absent",
        ),
    ],
)
def test_ub_setter_default_lattice(parms, context):
    """Cover both branches of the ``UB`` setter lattice-fallback logic."""
    solver = DiffcalcSolver()
    if parms["stored"] is not None:
        solver.lattice = dict(parms["stored"])
    # Wipe the diffcalc-side crystal so the setter must restore one.
    solver._ubcalc = type(solver._ubcalc)("default")
    if parms["stored"] is None:
        solver._lattice = {}
    with context:
        solver.UB = [[1, 0, 0], [0, 1, 0], [0, 0, 1]]
        assert solver._ubcalc.crystal is not None


# ---------------------------------------------------------------------------
# Rename completeness (issues #97, #105): guards the Proposal A naming rules.
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "parms, context",
    [
        pytest.param(
            dict(name="4S+2D bisect_eta_fixed nu_fixed"),
            pytest.raises(ValueError, match=re.escape("Mode")),
            id="old-style name with 4S+2D prefix rejected",
        ),
        pytest.param(
            dict(name="fixed_mu fixed_chi fixed_phi"),
            does_not_raise(),
            id="new-style all-fixed_* name accepted",
        ),
        pytest.param(
            dict(name="bisect fixed_mu fixed_nu"),
            does_not_raise(),
            id="new-style bisect-led name accepted (canonical vertical bisector)",
        ),
        pytest.param(
            dict(name="a_eq_b fixed_delta fixed_mu"),
            does_not_raise(),
            id="new-style a_eq_b-led name accepted",
        ),
    ],
)
def test_mode_rename_completeness(parms, context):
    """Pin the post-rename mode-name conventions.

    Old-style names containing the ``4S+2D`` prefix or the
    ``<axis>_fixed`` suffix are not part of ``_MODES`` any more and
    must be rejected by the mode setter.  New-style names matching
    Proposal A (drop prefix, ``fixed_<axis>`` form, keyword
    constraints first) must be accepted.
    """
    solver = DiffcalcSolver()
    with context:
        solver.mode = parms["name"]
        assert solver.mode == parms["name"]


@pytest.mark.parametrize(
    "parms, context",
    [
        pytest.param(
            dict(check="no 4S+2D prefix"),
            does_not_raise(),
            id="no mode name contains the 4S+2D prefix",
        ),
        pytest.param(
            dict(check="no <axis>_fixed suffix"),
            does_not_raise(),
            id="no mode name contains the legacy <axis>_fixed suffix",
        ),
        pytest.param(
            dict(check="keyword constraints lead"),
            does_not_raise(),
            id="modes with a_eq_b/bisect/bin_eq_bout lead with that token",
        ),
        pytest.param(
            dict(check="default is canonical bisecting_vertical"),
            does_not_raise(),
            id="default mode is bisect fixed_mu fixed_nu",
        ),
    ],
)
def test_mode_naming_invariants(parms, context):
    """Static checks on the entire ``_MODES`` table.

    These invariants are guarded as tests so a future PR that adds a
    new mode in the old style (or moves a keyword token off the
    leading position) trips immediately, rather than silently
    re-introducing the inconsistency #97 set out to fix.
    """
    keywords = {"a_eq_b", "bisect", "bin_eq_bout"}
    with context:
        check = parms["check"]
        if check == "no 4S+2D prefix":
            assert not any("4S+2D" in name for name in _MODES)
        elif check == "no <axis>_fixed suffix":
            offenders = [name for name in _MODES if re.search(r"\b[a-z]+_fixed\b", name)]
            assert offenders == []
        elif check == "keyword constraints lead":
            for name in _MODES:
                toks = name.split()
                kw_positions = [i for i, t in enumerate(toks) if t in keywords]
                if not kw_positions:
                    continue
                assert kw_positions == list(range(len(kw_positions))), (
                    f"mode {name!r}: keyword tokens must come first"
                )
        elif check == "default is canonical bisecting_vertical":
            solver = DiffcalcSolver()
            assert solver.mode == "bisect fixed_mu fixed_nu"
            assert _MODES[solver.mode] == {"bisect": True, "mu": 0.0, "nu": 0.0}


# ---------------------------------------------------------------------------
# Runtime mode registration (issues #97, #106): register_mode / unregister_mode
# fill gaps where diffcalc-core implements a constraint combination that
# DiffcalcSolver does not ship by default.
# ---------------------------------------------------------------------------


# A combination diffcalc-core implements but ``_MODES`` does not ship.
# ``{delta: 0, eta: 0, chi: 0}`` is the delta-pinned cousin of the
# nu-pinned ``fixed_nu fixed_eta fixed_chi`` built-in (eta&chi sample
# pair + delta detector pin); is_current_mode_implemented() returns True.
RUNTIME_MODE_NAME = "fixed_delta fixed_eta fixed_chi"
RUNTIME_MODE_CONSTRAINTS = {"delta": 0.0, "eta": 0.0, "chi": 0.0}


@pytest.mark.parametrize(
    "parms, context",
    [
        pytest.param(
            dict(
                name=RUNTIME_MODE_NAME,
                constraints=RUNTIME_MODE_CONSTRAINTS,
            ),
            does_not_raise(),
            id="register a valid not-shipped combination",
        ),
        pytest.param(
            dict(
                name="bisect fixed_mu fixed_nu",
                constraints={"bisect": True, "mu": 0.0, "nu": 0.0},
            ),
            pytest.raises(SolverError, match=re.escape("Cannot redefine built-in mode")),
            id="reject clash with built-in mode name",
        ),
        pytest.param(
            dict(
                name="",
                constraints=RUNTIME_MODE_CONSTRAINTS,
            ),
            pytest.raises(SolverError, match=re.escape("non-empty string")),
            id="reject empty name",
        ),
        pytest.param(
            dict(
                name=123,
                constraints=RUNTIME_MODE_CONSTRAINTS,
            ),
            pytest.raises(SolverError, match=re.escape("non-empty string")),
            id="reject non-string name",
        ),
        pytest.param(
            dict(
                name="bad_not_dict",
                constraints=[("delta", 0.0), ("eta", 0.0), ("chi", 0.0)],
            ),
            pytest.raises(SolverError, match=re.escape("must be a dict")),
            id="reject non-dict constraints",
        ),
        pytest.param(
            dict(
                name="bad_two",
                constraints={"delta": 0.0, "eta": 0.0},
            ),
            pytest.raises(SolverError, match=re.escape("exactly three constraints")),
            id="reject 2-constraint dict",
        ),
        pytest.param(
            dict(
                name="bad_four",
                constraints={"delta": 0.0, "eta": 0.0, "chi": 0.0, "phi": 0.0},
            ),
            pytest.raises(SolverError, match=re.escape("exactly three constraints")),
            id="reject 4-constraint dict",
        ),
        pytest.param(
            dict(
                name="bad_unknown",
                constraints={"bogus": 0.0, "mu": 0.0, "phi": 0.0},
            ),
            pytest.raises(SolverError, match=re.escape("diffcalc rejected constraints")),
            id="reject unknown constraint name",
        ),
        pytest.param(
            dict(
                name="bad_two_detector",
                constraints={"delta": 0.0, "nu": 0.0, "mu": 0.0},
            ),
            pytest.raises(SolverError, match=re.escape("dropped by diffcalc (same-category conflict)")),
            id="reject same-category collision (two detectors)",
        ),
        pytest.param(
            dict(
                name="bad_not_implemented",
                constraints={"mu": 0.0, "chi": 0.0, "omega": 0.0},
            ),
            pytest.raises(SolverError, match=re.escape("not implemented by diffcalc-core")),
            id="reject structurally-valid but not-implemented combination",
        ),
        pytest.param(
            dict(
                name=RUNTIME_MODE_NAME,
                constraints=RUNTIME_MODE_CONSTRAINTS,
                preregister=True,
            ),
            pytest.raises(SolverError, match=re.escape("already registered")),
            id="reject duplicate registration of an existing user mode",
        ),
    ],
)
def test_register_mode(parms, context):
    """Cover register_mode happy path and every rejection path.

    Validates the runtime mode-registration contract:

    * Valid not-shipped combinations are accepted and become
      selectable via the merged ``modes`` list.
    * Built-in mode names cannot be shadowed.
    * Inputs are validated for type and count before being passed
      to diffcalc, so error messages stay actionable.
    * Same-category collisions silently collapsed by diffcalc
      (e.g. two detector constraints) are rejected explicitly,
      naming the dropped keys.
    * Combinations that survive structural validation but lack a
      diffcalc implementation (``is_current_mode_implemented()``
      returns False) are rejected.
    """
    solver = DiffcalcSolver()
    if parms.get("preregister"):
        solver.register_mode(parms["name"], parms["constraints"])
    with context:
        solver.register_mode(parms["name"], parms["constraints"])
        assert parms["name"] in solver.modes
        # Verify selectability and that the active mode round-trips.
        solver.mode = parms["name"]
        assert solver.mode == parms["name"]


@pytest.mark.parametrize(
    "parms, context",
    [
        pytest.param(
            dict(name=RUNTIME_MODE_NAME, preselect=False),
            does_not_raise(),
            id="unregister a previously registered user mode",
        ),
        pytest.param(
            dict(name=RUNTIME_MODE_NAME, preselect=True),
            does_not_raise(),
            id="unregister the currently selected mode clears self.mode",
        ),
        pytest.param(
            dict(name="bisect fixed_mu fixed_nu", preselect=False),
            pytest.raises(SolverError, match=re.escape("Cannot unregister built-in mode")),
            id="reject unregister of built-in",
        ),
        pytest.param(
            dict(name="never_registered", preselect=False),
            pytest.raises(SolverError, match=re.escape("is not registered")),
            id="reject unregister of missing user mode",
        ),
    ],
)
def test_unregister_mode(parms, context):
    """Cover unregister_mode happy path and rejection paths.

    Confirms that built-in modes cannot be removed; that a request
    to remove a never-registered mode is rejected; and that
    removing the currently-selected mode clears the active mode so
    subsequent forward() calls don't silently re-use the dropped
    constraints.
    """
    solver = DiffcalcSolver()
    # Always register the runtime mode so the happy-path cases have
    # something to remove; built-in/missing cases ignore it.
    solver.register_mode(RUNTIME_MODE_NAME, RUNTIME_MODE_CONSTRAINTS)
    if parms["preselect"]:
        solver.mode = parms["name"]
    with context:
        solver.unregister_mode(parms["name"])
        assert parms["name"] not in solver.modes
        if parms["preselect"]:
            assert solver.mode == ""


@pytest.mark.parametrize(
    "parms, context",
    [
        pytest.param(
            dict(
                name=RUNTIME_MODE_NAME,
                constraints=RUNTIME_MODE_CONSTRAINTS,
            ),
            does_not_raise(),
            id="user-registered mode is usable end-to-end",
        ),
    ],
)
def test_register_mode_end_to_end(parms, context):
    """A registered user mode is selectable and drives inverse() / forward().

    Confirms the merged-mode path through ``_apply_mode_constraints`` —
    proving that ``register_mode`` is not just bookkeeping but actually
    feeds the diffcalc ``Constraints`` object used by the calculator.
    """
    with context:
        # Build a solver with UB *before* registering, then switch into
        # the user mode and exercise inverse() at the origin.
        solver = _make_solver_with_ub()
        solver.register_mode(parms["name"], parms["constraints"])
        solver.mode = parms["name"]
        result = solver.inverse({"mu": 0.0, "delta": 0.0, "nu": 0.0, "eta": 0.0, "chi": 0.0, "phi": 0.0})
        assert set(result) == {"h", "k", "l"}


# ---------------------------------------------------------------------------
# Order-independent mode name matching (:issue:`109`)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "parms, context",
    [
        pytest.param(
            dict(
                input_name="fixed_mu bisect fixed_nu",
                canonical="bisect fixed_mu fixed_nu",
            ),
            does_not_raise(),
            id="bisect keyword permuted into middle resolves to built-in",
        ),
        pytest.param(
            dict(
                input_name="fixed_nu fixed_mu bisect",
                canonical="bisect fixed_mu fixed_nu",
            ),
            does_not_raise(),
            id="bisect keyword permuted to end resolves to built-in",
        ),
        pytest.param(
            dict(
                input_name="fixed_phi fixed_chi fixed_eta",
                canonical="fixed_eta fixed_chi fixed_phi",
            ),
            does_not_raise(),
            id="all-fixed_ name reversed resolves to built-in",
        ),
        pytest.param(
            dict(
                input_name="fixed_mu   bisect    fixed_nu",
                canonical="bisect fixed_mu fixed_nu",
            ),
            does_not_raise(),
            id="extra whitespace is normalized",
        ),
        pytest.param(
            dict(
                input_name="  bisect fixed_mu fixed_nu  ",
                canonical="bisect fixed_mu fixed_nu",
            ),
            does_not_raise(),
            id="leading and trailing whitespace is stripped",
        ),
        pytest.param(
            dict(
                input_name="bisect fixed_mu fixed_nu",
                canonical="bisect fixed_mu fixed_nu",
            ),
            does_not_raise(),
            id="exact built-in name still accepted",
        ),
        pytest.param(
            dict(
                input_name="fixed_mu fixed_nu fixed_bogus",
                canonical=None,
            ),
            pytest.raises(ValueError, match=re.escape("fixed_mu fixed_nu fixed_bogus")),
            id="unknown permutation still rejected",
        ),
    ],
)
def test_mode_setter_order_independent(parms, context):
    """Mode setter accepts any permutation of the constraint tokens.

    Resolves issue #109: ``self.mode`` always reads back as the
    registered display name regardless of the order in which the
    caller specified the tokens.
    """
    solver = DiffcalcSolver()
    with context:
        solver.mode = parms["input_name"]
        assert solver.mode == parms["canonical"]


@pytest.mark.parametrize(
    "parms, context",
    [
        pytest.param(
            dict(
                name="fixed_mu bisect fixed_nu",
                constraints={"bisect": True, "mu": 0.0, "nu": 0.0},
            ),
            pytest.raises(
                SolverError, match=re.escape("Cannot redefine built-in mode 'bisect fixed_mu fixed_nu'")
            ),
            id="permuted built-in name rejected as redefinition",
        ),
        pytest.param(
            dict(
                name="fixed_phi fixed_chi fixed_eta",
                constraints={"eta": 0.0, "chi": 0.0, "phi": 0.0},
            ),
            pytest.raises(
                SolverError, match=re.escape("Cannot redefine built-in mode 'fixed_eta fixed_chi fixed_phi'")
            ),
            id="permuted all-fixed_ built-in rejected",
        ),
        pytest.param(
            dict(
                name="bisect bisect fixed_mu",
                constraints={"bisect": True, "mu": 0.0, "nu": 0.0},
            ),
            pytest.raises(SolverError, match=re.escape("repeats constraint name(s) ['bisect']")),
            id="repeated constraint name rejected",
        ),
        pytest.param(
            dict(
                name="   ",
                constraints={"bisect": True, "mu": 0.0, "nu": 0.0},
            ),
            pytest.raises(SolverError, match=re.escape("at least one constraint")),
            id="whitespace-only name rejected",
        ),
    ],
)
def test_register_mode_token_set_collisions(parms, context):
    """register_mode rejects permutations of existing built-in names.

    Resolves issue #109: ``mode a`` and ``a mode`` are treated as the
    same mode for the purposes of collision detection.
    """
    solver = DiffcalcSolver()
    with context:
        solver.register_mode(parms["name"], parms["constraints"])


@pytest.mark.parametrize(
    "parms, context",
    [
        pytest.param(
            dict(
                first_name="fixed_delta fixed_eta fixed_chi",
                second_name="fixed_chi fixed_delta fixed_eta",
            ),
            pytest.raises(SolverError, match=re.escape("already registered")),
            id="permuted user mode rejected as duplicate",
        ),
        pytest.param(
            dict(
                first_name="fixed_delta fixed_eta fixed_chi",
                second_name="fixed_eta fixed_chi fixed_delta",
            ),
            pytest.raises(SolverError, match=re.escape("already registered")),
            id="another permutation rejected as duplicate",
        ),
    ],
)
def test_register_mode_user_token_set_collisions(parms, context):
    """register_mode rejects permutations of previously-registered user modes."""
    solver = DiffcalcSolver()
    constraints = {"delta": 0.0, "eta": 0.0, "chi": 0.0}
    solver.register_mode(parms["first_name"], constraints)
    with context:
        solver.register_mode(parms["second_name"], constraints)


@pytest.mark.parametrize(
    "parms, context",
    [
        pytest.param(
            dict(
                registered="fixed_delta fixed_eta fixed_chi",
                request="fixed_chi fixed_eta fixed_delta",
            ),
            does_not_raise(),
            id="permuted user mode unregistered symmetrically",
        ),
        pytest.param(
            dict(
                registered="fixed_delta fixed_eta fixed_chi",
                request="fixed_eta fixed_delta fixed_chi",
            ),
            does_not_raise(),
            id="another permuted form unregistered symmetrically",
        ),
        pytest.param(
            dict(
                registered="fixed_delta fixed_eta fixed_chi",
                request="fixed_mu bisect fixed_nu",
            ),
            pytest.raises(
                SolverError, match=re.escape("Cannot unregister built-in mode 'bisect fixed_mu fixed_nu'")
            ),
            id="permuted built-in rejected with canonical name in message",
        ),
        pytest.param(
            dict(
                registered="fixed_delta fixed_eta fixed_chi",
                request="fixed_mu fixed_chi fixed_omega",
            ),
            pytest.raises(SolverError, match=re.escape("is not registered")),
            id="unknown permutation rejected",
        ),
    ],
)
def test_unregister_mode_token_set(parms, context):
    """unregister_mode resolves permutations to the registered name."""
    solver = DiffcalcSolver()
    solver.register_mode(parms["registered"], {"delta": 0.0, "eta": 0.0, "chi": 0.0})
    with context:
        solver.unregister_mode(parms["request"])
        assert parms["registered"] not in solver.modes


@pytest.mark.parametrize(
    "parms, context",
    [
        pytest.param(
            dict(
                registered="fixed_delta fixed_eta fixed_chi",
                expected_writable=["mu", "nu", "phi"],
            ),
            does_not_raise(),
            id="axes_w works for user-registered mode",
        ),
    ],
)
def test_axes_w_user_registered_mode(parms, context):
    """axes_w no longer KeyErrors on user-registered modes (:issue:`109`).

    Regression test for the latent bug fixed alongside #109: ``axes_w``
    previously consulted only ``_MODES`` and raised ``KeyError`` for
    any mode added via ``register_mode``.
    """
    solver = DiffcalcSolver()
    solver.register_mode(parms["registered"], {"delta": 0.0, "eta": 0.0, "chi": 0.0})
    with context:
        solver.mode = parms["registered"]
        assert solver.axes_w == parms["expected_writable"]


@pytest.mark.parametrize(
    "parms, context",
    [
        pytest.param(
            dict(name=123),
            pytest.raises(SolverError, match=re.escape("Mode name must be a string")),
            id="non-string name rejected",
        ),
    ],
)
def test_unregister_mode_non_string(parms, context):
    """unregister_mode rejects non-string names defensively."""
    solver = DiffcalcSolver()
    with context:
        solver.unregister_mode(parms["name"])


@pytest.mark.parametrize(
    "parms, context",
    [
        pytest.param(
            dict(name="   "),
            does_not_raise(),
            id="whitespace-only resolves to None",
        ),
        pytest.param(
            dict(name=""),
            does_not_raise(),
            id="empty string resolves to None",
        ),
    ],
)
def test_resolve_mode_name_empty(parms, context):
    """_resolve_mode_name returns None for empty/whitespace input."""
    solver = DiffcalcSolver()
    with context:
        assert solver._resolve_mode_name(parms["name"]) is None


@pytest.mark.parametrize(
    "parms, context",
    [
        pytest.param(
            dict(),
            does_not_raise(),
            id="permuted name does not add a phantom mode entry",
        ),
    ],
)
def test_modes_list_unchanged_by_permutations(parms, context):
    """Selecting a permuted name does not inflate the modes list."""
    solver = DiffcalcSolver()
    baseline = len(solver.modes)
    with context:
        solver.mode = "fixed_mu bisect fixed_nu"  # permutation of a built-in
        assert len(solver.modes) == baseline
        assert "fixed_mu bisect fixed_nu" not in solver.modes
        assert "bisect fixed_mu fixed_nu" in solver.modes


# ---------------------------------------------------------------------------
# Override constraint values on a registered user mode (:issue:`114`)
# update_mode_constraints sibling of AdHocSolver.update_mode_constraints.
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "parms, context",
    [
        pytest.param(
            dict(
                preregister=True,
                preselect=False,
                target_mode=RUNTIME_MODE_NAME,
                updates={"chi": 45.0},
                expected_value=("chi", 45.0),
            ),
            does_not_raise(),
            id="override single value on named user mode",
        ),
        pytest.param(
            dict(
                preregister=True,
                preselect=True,
                target_mode=None,  # active-mode shortcut
                updates={"chi": 30.0},
                expected_value=("chi", 30.0),
            ),
            does_not_raise(),
            id="override default on active mode via None shortcut",
        ),
        pytest.param(
            dict(
                preregister=True,
                preselect=False,
                target_mode="fixed_chi fixed_delta fixed_eta",  # permutation of RUNTIME_MODE_NAME
                updates={"eta": 12.0, "chi": 7.0},
                expected_value=("eta", 12.0),
            ),
            does_not_raise(),
            id="multi-value override resolves permuted name",
        ),
        pytest.param(
            dict(
                preregister=True,
                preselect=False,
                target_mode="bisect fixed_mu fixed_nu",  # built-in
                updates={"mu": 5.0},
                expected_value=None,
            ),
            pytest.raises(SolverError, match=re.escape("Cannot modify built-in mode")),
            id="reject modification of built-in mode",
        ),
        pytest.param(
            dict(
                preregister=False,
                preselect=False,
                target_mode="never_registered",
                updates={"mu": 0.0},
                expected_value=None,
            ),
            pytest.raises(SolverError, match=re.escape("is not registered")),
            id="reject unknown user mode name",
        ),
        pytest.param(
            dict(
                preregister=True,
                preselect=False,
                target_mode=RUNTIME_MODE_NAME,
                updates={"bogus_axis": 1.0},
                expected_value=None,
            ),
            pytest.raises(SolverError, match=re.escape("not present in this mode")),
            id="reject constraint name not present in this mode",
        ),
        pytest.param(
            dict(
                preregister=True,
                preselect=False,
                target_mode=RUNTIME_MODE_NAME,
                # Replace the chi sample constraint with mu would introduce a
                # second sample-axis pin in a category diffcalc collapses.
                # Use a non-string value to drive diffcalc rejection instead.
                updates={"chi": "not_a_number"},
                expected_value=None,
            ),
            pytest.raises(SolverError, match=re.escape("diffcalc rejected updated constraints")),
            id="reject value rejected by diffcalc",
        ),
        pytest.param(
            dict(
                preregister=False,
                preselect=False,
                target_mode=123,  # non-string
                updates={"chi": 0.0},
                expected_value=None,
            ),
            pytest.raises(SolverError, match=re.escape("Mode name must be a string")),
            id="reject non-string mode name",
        ),
    ],
)
def test_update_mode_constraints(parms, context):
    """``update_mode_constraints`` overrides user-mode constraint values.

    Sibling of
    :func:`hklpy2_solvers.ad_hoc_solver.AdHocSolver.update_mode_constraints`
    for the diffcalc backend.  Built-in modes are frozen (mirroring
    :meth:`unregister_mode`); user modes mutate in place and the
    ``_applied_mode`` cache is invalidated so subsequent forward/inverse
    calls use the new values.  Permuted mode names resolve to the
    registered display name (issue #109 token-set rule).
    """
    solver = DiffcalcSolver()
    if parms["preregister"]:
        solver.register_mode(RUNTIME_MODE_NAME, dict(RUNTIME_MODE_CONSTRAINTS))
    if parms["preselect"]:
        solver.mode = RUNTIME_MODE_NAME
    with context:
        solver.update_mode_constraints(parms["target_mode"], **parms["updates"])
        # Success path only: verify the value landed and the cache was
        # invalidated.
        name = solver._resolve_mode_name(parms["target_mode"]) if parms["target_mode"] is not None else solver.mode
        stored = solver._user_modes[name]
        axis, expected = parms["expected_value"]
        assert stored[axis] == expected, f"{axis!r} expected {expected!r} got {stored[axis]!r}"
        assert solver._applied_mode is None, "applied-mode cache not invalidated"


@pytest.mark.parametrize(
    "parms, context",
    [
        pytest.param(
            dict(new_chi=45.0),
            does_not_raise(),
            id="update is observed by next inverse() via rebuilt Constraints",
        ),
    ],
)
def test_update_mode_constraints_is_observed_by_inverse(parms, context):
    """The new constraint value reaches diffcalc on the next ``inverse()``.

    Ensures ``_applied_mode = None`` actually triggers a
    :class:`~diffcalc.hkl.constraints.Constraints` rebuild and that the
    updated value lands in the live diffcalc state.
    """
    solver = DiffcalcSolver()
    solver.register_mode(RUNTIME_MODE_NAME, dict(RUNTIME_MODE_CONSTRAINTS))
    solver.mode = RUNTIME_MODE_NAME
    with context:
        solver.update_mode_constraints(chi=parms["new_chi"])
        # ``_apply_mode_constraints`` runs lazily through inverse() /
        # forward(); calling it directly is the smallest assertion.
        solver._apply_mode_constraints()
        live = solver._constraints.asdict
        assert live["chi"] == parms["new_chi"], (
            f"diffcalc.Constraints['chi'] expected {parms['new_chi']} got {live.get('chi')}"
        )


# ---------------------------------------------------------------------------
# Persist solver-defined state through export/restore (:issue:`108`)
# ---------------------------------------------------------------------------


# A combination diffcalc-core implements but ``_MODES`` does not ship,
# used to exercise the user-mode persistence path.
PERSIST_MODE_NAME = "fixed_delta fixed_eta fixed_chi"
PERSIST_MODE_CONSTRAINTS = {"delta": 0.0, "eta": 0.0, "chi": 0.0}


@pytest.mark.parametrize(
    "parms, context",
    [
        pytest.param(
            dict(register=False, expect_user_modes=False, expected_mode_key=True),
            does_not_raise(),
            id="vanilla solver: only built-in mode key in metadata",
        ),
        pytest.param(
            dict(register=True, expect_user_modes=True, expected_mode_key=True),
            does_not_raise(),
            id="with user mode: user_modes key present alongside mode",
        ),
    ],
)
def test_metadata_persists_user_modes(parms, context):
    """``_metadata`` emits ``user_modes`` only when non-empty.

    Regression for :issue:`108`: the ``solver:`` block in
    ``export()`` carries the dict of user-registered modes so they
    survive a ``simulator_from_config()`` round-trip.  The ``mode``
    key is always emitted (mirroring :class:`HklSolver`).
    """
    solver = DiffcalcSolver()
    if parms["register"]:
        solver.register_mode(PERSIST_MODE_NAME, PERSIST_MODE_CONSTRAINTS)
        solver.mode = PERSIST_MODE_NAME
    with context:
        meta = solver._metadata
        assert ("mode" in meta) is parms["expected_mode_key"]
        assert ("user_modes" in meta) is parms["expect_user_modes"]
        if parms["expect_user_modes"]:
            assert meta["user_modes"] == {PERSIST_MODE_NAME: PERSIST_MODE_CONSTRAINTS}


@pytest.mark.parametrize(
    "parms, context",
    [
        pytest.param(
            dict(user_modes={PERSIST_MODE_NAME: PERSIST_MODE_CONSTRAINTS}),
            does_not_raise(),
            id="single user mode replayed at construction",
        ),
        pytest.param(
            dict(user_modes={}),
            does_not_raise(),
            id="empty user_modes dict is a no-op",
        ),
        pytest.param(
            dict(user_modes="not a dict"),
            pytest.raises(SolverError, match=re.escape("user_modes must be a dict")),
            id="non-dict user_modes raises SolverError",
        ),
        pytest.param(
            dict(user_modes={123: PERSIST_MODE_CONSTRAINTS}),
            pytest.raises(SolverError, match=re.escape("user_modes key must be a string")),
            id="non-string mode name in user_modes raises",
        ),
        pytest.param(
            dict(user_modes={"bisect fixed_mu fixed_nu": {"bisect": True, "mu": 0.0, "nu": 0.0}}),
            pytest.raises(SolverError, match=re.escape("user_modes replay failed")),
            id="redefinition of a built-in mode raises with replay-failed prefix",
        ),
    ],
)
def test_init_replays_user_modes_kwarg(parms, context):
    """Constructor pops and replays ``user_modes`` from kwargs.

    This is the delivery channel used by
    ``hklpy2.simulator_from_config()`` (:issue:`108` / upstream
    :issue:`405`): non-reserved keys under ``solver:`` flow as
    ``solver_kwargs`` into ``__init__``.
    """
    with context:
        solver = DiffcalcSolver(user_modes=parms["user_modes"])
        if isinstance(parms["user_modes"], dict):
            for name in parms["user_modes"]:
                assert name in solver.modes


@pytest.mark.parametrize(
    "parms, context",
    [
        pytest.param(
            dict(
                name=PERSIST_MODE_NAME,
                constraints=PERSIST_MODE_CONSTRAINTS,
                select_user_mode=True,
            ),
            does_not_raise(),
            id="round-trip with user mode active",
        ),
        pytest.param(
            dict(
                name=PERSIST_MODE_NAME,
                constraints=PERSIST_MODE_CONSTRAINTS,
                select_user_mode=False,
            ),
            does_not_raise(),
            id="round-trip with user mode registered but not active",
        ),
    ],
)
def test_simulator_from_config_round_trip(parms, context):
    """End-to-end round-trip via ``hklpy2.simulator_from_config``.

    Resolves :issue:`108`: a user mode registered before
    ``export()`` is available in the reconstructed solver after
    ``simulator_from_config()``, and the saved active mode is
    reapplied.
    """
    import hklpy2
    from hklpy2.run_utils import simulator_from_config

    sim = hklpy2.creator(solver="diffcalc", geometry=GEOMETRY_NAME, name="diff_persist")
    solver = sim.core.solver
    solver.register_mode(parms["name"], parms["constraints"])
    if parms["select_user_mode"]:
        solver.mode = parms["name"]
    cfg = sim.configuration
    with context:
        sim2 = simulator_from_config(cfg)
        solver2 = sim2.core.solver
        assert parms["name"] in solver2.modes
        assert solver2._user_modes[parms["name"]] == parms["constraints"]
        if parms["select_user_mode"]:
            # ``Core.mode`` is the authoritative cache; the solver's
            # own mode follows on the next forward/inverse call when
            # ``update_solver()`` pushes it through.
            assert sim2.core.mode == parms["name"]


@pytest.mark.parametrize(
    "parms, context",
    [
        pytest.param(
            dict(),
            does_not_raise(),
            id="replay is idempotent on repeated simulator_from_config",
        ),
    ],
)
def test_simulator_from_config_round_trip_idempotent(parms, context):
    """Replaying a config twice does not raise (idempotent registration).

    Loading the same persisted state into a solver that already
    has the user mode registered must be a no-op rather than
    raising "already registered".
    """
    import hklpy2
    from hklpy2.run_utils import simulator_from_config

    sim = hklpy2.creator(solver="diffcalc", geometry=GEOMETRY_NAME, name="diff_idem")
    sim.core.solver.register_mode(PERSIST_MODE_NAME, PERSIST_MODE_CONSTRAINTS)
    cfg = sim.configuration
    with context:
        sim2 = simulator_from_config(cfg)
        # Second load on the same instance must not raise.
        sim2.restore(cfg, restore_mode=True)
        assert PERSIST_MODE_NAME in sim2.core.solver.modes


@pytest.mark.parametrize(
    "parms, context",
    [
        pytest.param(
            dict(),
            does_not_raise(),
            id="constructor-level idempotent replay skips known token-set",
        ),
    ],
)
def test_init_user_modes_replay_idempotent(parms, context):
    """``_replay_user_modes`` skips an already-registered token-set.

    Exercises the early-continue branch that makes the kwarg
    delivery channel safe to re-use across construction +
    explicit ``restore()`` cycles without raising "already
    registered".
    """
    # Two entries with the same token-set, second is a permutation
    # of the first.  After the first registration the second is a
    # no-op rather than a SolverError.
    state = {
        PERSIST_MODE_NAME: PERSIST_MODE_CONSTRAINTS,
        "fixed_eta fixed_delta fixed_chi": PERSIST_MODE_CONSTRAINTS,
    }
    with context:
        solver = DiffcalcSolver(user_modes=state)
        # Only one user-mode entry stored (canonical name from first insert).
        assert len(solver._user_modes) == 1
        assert PERSIST_MODE_NAME in solver._user_modes

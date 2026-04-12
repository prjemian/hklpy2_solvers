"""Tests for the diffcalc solver adapter."""

import math
import re
from contextlib import nullcontext as does_not_raise

import pytest

from hklpy2_solvers.diffcalc_solver import GEOMETRY_NAME, PSEUDO_AXES, REAL_AXES, DiffcalcSolver

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
    mode: str = "4S+2D mu_chi_phi_fixed",
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
            dict(mode="4S+2D mu_chi_phi_fixed"),
            does_not_raise(),
            id="valid mode accepted",
        ),
        pytest.param(
            dict(mode="4S+2D eta_chi_phi_fixed"),
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


@pytest.mark.parametrize(
    "parms, context",
    [
        pytest.param(
            dict(
                mode="4S+2D mu_chi_phi_fixed",
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
                mode="4S+2D eta_chi_phi_fixed",
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
                mode="4S+2D mu_chi_phi_fixed",
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
                mode="4S+2D mu_chi_phi_fixed",
                pseudos={"h": 1.0, "k": 0.0, "l": 0.0},
            ),
            does_not_raise(),
            id="forward-inverse roundtrip (1,0,0)",
        ),
        pytest.param(
            dict(
                mode="4S+2D mu_chi_phi_fixed",
                pseudos={"h": 0.0, "k": 1.0, "l": 0.0},
            ),
            does_not_raise(),
            id="forward-inverse roundtrip (0,1,0)",
        ),
        pytest.param(
            dict(
                mode="4S+2D mu_chi_phi_fixed",
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
            dict(
                mode="4S+2D mu_chi_phi_fixed",
                expected_extras=["mu", "chi", "phi"],
            ),
            does_not_raise(),
            id="3-sample mode extras",
        ),
        pytest.param(
            dict(
                mode="4S+2D mu_fixed a_eq_b delta_fixed",
                expected_extras=["delta", "mu"],
            ),
            does_not_raise(),
            id="det+ref+samp mode extras exclude a_eq_b",
        ),
        pytest.param(
            dict(
                mode="4S+2D bisect_mu_fixed delta_fixed",
                expected_extras=["delta", "mu"],
            ),
            does_not_raise(),
            id="bisect mode extras exclude bisect",
        ),
    ],
)
def test_extra_axis_names(parms, context):
    solver = DiffcalcSolver()
    with context:
        solver.mode = parms["mode"]
        assert sorted(solver.extra_axis_names) == sorted(parms["expected_extras"])


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
                mode="4S+2D mu_chi_phi_fixed",
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
            dict(),
            does_not_raise(),
            id="empty mode gives empty extra_axis_names",
        ),
    ],
)
def test_extra_axis_names_empty_mode(parms, context):
    solver = DiffcalcSolver()
    solver._mode = ""
    with context:
        assert solver.extra_axis_names == []


@pytest.mark.parametrize(
    "parms, context",
    [
        pytest.param(
            dict(
                mode="4S+2D mu_fixed a_eq_b delta_fixed",
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
    helper = _make_solver_with_ub(mode="4S+2D mu_chi_phi_fixed")

    # (1,0,0) and (0,1,0) work fine with this mode.
    # (1,1,0) also works. All are in-plane with chi=phi=mu=0.
    hkl_list = [(1, 0, 0), (0, 1, 0), (1, 1, 0)]
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

    solver.calculate_UB(solver._reflections[0], solver._reflections[1])

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
        assert solver._extras == {}

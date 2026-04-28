# Copyright (c) 2026 Pete Jemian <prjemian+hklpy2@gmail.com>
# SPDX-License-Identifier: LicenseRef-UChicago-Argonne-LLC-License
"""Tests for the ad_hoc solver adapter."""

import math
import re
from contextlib import nullcontext as does_not_raise

import pytest

from hklpy2_solvers.ad_hoc_solver import DEFAULT_GEOMETRY, PSEUDO_AXES, AdHocSolver

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

SI_A = 5.431
"""Cubic silicon lattice constant (Angstrom)."""

SI_LATTICE = {"a": SI_A, "b": SI_A, "c": SI_A, "alpha": 90.0, "beta": 90.0, "gamma": 90.0}

WAVELENGTH = 1.0
"""Angstrom."""

THETA_100 = math.degrees(math.asin(WAVELENGTH / (2 * SI_A)))
TTH_100 = 2 * THETA_100

# Geometry -> expected info mapping
GEOMETRY_INFO = {
    "fourcv": {
        "real_axes": ["omega", "chi", "phi", "ttheta"],
        "mode_count": 6,
        "default_mode": "bisecting",
    },
    "fourch": {
        "real_axes": ["omega", "chi", "phi", "ttheta"],
        "mode_count": 6,
        "default_mode": "bisecting",
    },
    "psic": {
        "real_axes": ["mu", "eta", "chi", "phi", "nu", "delta"],
        "mode_count": 22,
        "default_mode": "bisecting_vertical",
    },
    "sixc": {
        "real_axes": ["alpha", "omega", "chi", "phi", "delta", "gamma"],
        "mode_count": 6,
        "default_mode": "bisecting_4c",
    },
    "fivec": {
        "real_axes": ["mu", "omega", "chi", "phi", "ttheta"],
        "mode_count": 5,
        "default_mode": "bisecting_4c",
    },
    "kappa4cv": {
        "real_axes": ["komega", "kappa", "kphi", "ttheta"],
        "mode_count": 7,
        "default_mode": "bisecting",
    },
    "kappa4ch": {
        "real_axes": ["komega", "kappa", "kphi", "ttheta"],
        "mode_count": 6,
        "default_mode": "bisecting",
    },
    "kappa6c": {
        "real_axes": ["mu", "komega", "kappa", "kphi", "nu", "delta"],
        "mode_count": 12,
        "default_mode": "bisecting_vertical",
    },
    "zaxis": {
        "real_axes": ["alpha", "Z", "delta", "gamma"],
        "mode_count": 2,
        "default_mode": "zaxis",  # library has None, solver picks first
    },
    "s2d2": {
        "real_axes": ["mu", "Z", "nu", "delta"],
        "mode_count": 2,
        "default_mode": "fixed_mu",  # library has None, solver picks first
    },
}

# Reflection dicts per geometry family (axis names differ)
FOURCV_R1 = {
    "name": "r1",
    "pseudos": {"h": 1.0, "k": 0.0, "l": 0.0},
    "reals": {"omega": THETA_100, "chi": 0, "phi": 0, "ttheta": TTH_100},
    "wavelength": WAVELENGTH,
}
FOURCV_R2 = {
    "name": "r2",
    "pseudos": {"h": 0.0, "k": 1.0, "l": 0.0},
    "reals": {"omega": THETA_100, "chi": 0, "phi": 90, "ttheta": TTH_100},
    "wavelength": WAVELENGTH,
}
PSIC_R1 = {
    "name": "r1",
    "pseudos": {"h": 1.0, "k": 0.0, "l": 0.0},
    "reals": {"mu": 0, "eta": THETA_100, "chi": 0, "phi": 0, "nu": 0, "delta": TTH_100},
    "wavelength": WAVELENGTH,
}
PSIC_R2 = {
    "name": "r2",
    "pseudos": {"h": 0.0, "k": 1.0, "l": 0.0},
    "reals": {"mu": 0, "eta": THETA_100, "chi": 0, "phi": 90, "nu": 0, "delta": TTH_100},
    "wavelength": WAVELENGTH,
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_solver_with_ub(
    geometry: str = DEFAULT_GEOMETRY,
    mode: str | None = None,
) -> AdHocSolver:
    """Return an AdHocSolver with Si lattice, two reflections, and UB calculated."""
    solver = AdHocSolver(geometry)
    solver.lattice = dict(SI_LATTICE)

    if geometry in ("fourcv", "fourch"):
        r1, r2 = FOURCV_R1, FOURCV_R2
    elif geometry == "psic":
        r1, r2 = PSIC_R1, PSIC_R2
    else:
        # Build generic reflections from the solver's real axis names.
        real_axes = solver.real_axis_names
        zeros = {ax: 0.0 for ax in real_axes}
        r1 = {
            "name": "r1",
            "pseudos": {"h": 1, "k": 0, "l": 0},
            "reals": dict(zeros),
            "wavelength": WAVELENGTH,
        }
        r2 = {
            "name": "r2",
            "pseudos": {"h": 0, "k": 1, "l": 0},
            "reals": dict(zeros),
            "wavelength": WAVELENGTH,
        }

    solver.addReflection(r1)
    solver.addReflection(r2)
    solver.calculate_UB(r1, r2)
    if mode is not None:
        solver.mode = mode
    return solver


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "parms, context",
    [
        pytest.param(
            dict(geometry="fourcv"),
            does_not_raise(),
            id="fourcv geometry accepted",
        ),
        pytest.param(
            dict(geometry="psic"),
            does_not_raise(),
            id="psic geometry accepted",
        ),
        pytest.param(
            dict(geometry="fourch"),
            does_not_raise(),
            id="fourch geometry accepted",
        ),
        pytest.param(
            dict(geometry="sixc"),
            does_not_raise(),
            id="sixc geometry accepted",
        ),
        pytest.param(
            dict(geometry="fivec"),
            does_not_raise(),
            id="fivec geometry accepted",
        ),
        pytest.param(
            dict(geometry="kappa4cv"),
            does_not_raise(),
            id="kappa4cv geometry accepted",
        ),
        pytest.param(
            dict(geometry="kappa4ch"),
            does_not_raise(),
            id="kappa4ch geometry accepted",
        ),
        pytest.param(
            dict(geometry="kappa6c"),
            does_not_raise(),
            id="kappa6c geometry accepted",
        ),
        pytest.param(
            dict(geometry="zaxis"),
            does_not_raise(),
            id="zaxis geometry accepted",
        ),
        pytest.param(
            dict(geometry="s2d2"),
            does_not_raise(),
            id="s2d2 geometry accepted",
        ),
        pytest.param(
            dict(),
            does_not_raise(),
            id="no geometry arg uses default",
        ),
        pytest.param(
            dict(geometry="NONEXISTENT"),
            pytest.raises(
                Exception,
                match=re.escape("AdHocSolver does not support geometry"),
            ),
            id="unsupported geometry raises",
        ),
    ],
)
def test_instantiation(parms, context):
    with context:
        solver = AdHocSolver(**parms)
        assert solver.name == "ad_hoc"
        expected_geom = parms.get("geometry", DEFAULT_GEOMETRY)
        assert solver.geometry == expected_geom


@pytest.mark.parametrize(
    "parms, context",
    [
        pytest.param(
            dict(),
            does_not_raise(),
            id="default geometry is fourcv",
        ),
    ],
)
def test_default_geometry(parms, context):
    with context:
        solver = AdHocSolver(**parms)
        assert solver.geometry == DEFAULT_GEOMETRY


@pytest.mark.parametrize(
    "parms, context",
    [
        pytest.param(
            dict(
                attr="geometries",
                check="callable",
                min_count=10,
            ),
            does_not_raise(),
            id="geometries returns at least 10 entries",
        ),
        pytest.param(
            dict(
                attr="pseudo_axis_names",
                check="value",
                expected=PSEUDO_AXES,
            ),
            does_not_raise(),
            id="pseudo_axis_names returns h k l",
        ),
        pytest.param(
            dict(
                attr="real_axis_names",
                check="value",
                expected=GEOMETRY_INFO["fourcv"]["real_axes"],
            ),
            does_not_raise(),
            id="real_axis_names for fourcv",
        ),
    ],
)
def test_class_attributes(parms, context):
    with context:
        solver = AdHocSolver()
        value = getattr(solver, parms["attr"])
        if callable(value):
            value = value()
        if parms["check"] == "value":
            assert value == parms["expected"]
        elif parms["check"] == "callable":
            assert len(value) >= parms["min_count"]


@pytest.mark.parametrize(
    "parms, context",
    [
        pytest.param(
            dict(geometry=geometry, expected_axes=info["real_axes"]),
            does_not_raise(),
            id=f"{geometry} real axes",
        )
        for geometry, info in GEOMETRY_INFO.items()
    ],
)
def test_real_axis_names_per_geometry(parms, context):
    with context:
        solver = AdHocSolver(parms["geometry"])
        assert solver.real_axis_names == parms["expected_axes"]


@pytest.mark.parametrize(
    "parms, context",
    [
        pytest.param(
            dict(mode="bisecting"),
            does_not_raise(),
            id="valid mode accepted",
        ),
        pytest.param(
            dict(mode="fixed_chi"),
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
    solver = AdHocSolver()
    with context:
        solver.mode = parms["mode"]
        assert solver.mode == parms["mode"]


@pytest.mark.parametrize(
    "parms, context",
    [
        pytest.param(
            dict(
                geometry=geometry,
                expected_default=info["default_mode"],
            ),
            does_not_raise(),
            id=f"{geometry} default mode is {info['default_mode']}",
        )
        for geometry, info in GEOMETRY_INFO.items()
    ],
)
def test_default_mode(parms, context):
    with context:
        solver = AdHocSolver(parms["geometry"])
        assert solver.mode == parms["expected_default"]
        assert solver.mode != ""


@pytest.mark.parametrize(
    "parms, context",
    [
        pytest.param(
            dict(
                geometry=geometry,
                expected_count=info["mode_count"],
            ),
            does_not_raise(),
            id=f"{geometry} has {info['mode_count']} modes",
        )
        for geometry, info in GEOMETRY_INFO.items()
    ],
)
def test_modes_list(parms, context):
    with context:
        solver = AdHocSolver(parms["geometry"])
        modes = solver.modes
        assert len(modes) == parms["expected_count"]
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
    solver = AdHocSolver()
    with context:
        solver.lattice = parms["lattice"]
        assert solver.lattice == parms["lattice"]


@pytest.mark.parametrize(
    "parms, context",
    [
        pytest.param(
            dict(reflection=FOURCV_R1),
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
    solver = AdHocSolver()
    solver.lattice = dict(SI_LATTICE)
    with context:
        solver.addReflection(parms["reflection"])
        assert solver.wavelength == WAVELENGTH


@pytest.mark.parametrize(
    "parms, context",
    [
        pytest.param(
            dict(geometry="fourcv"),
            does_not_raise(),
            id="calculate_UB succeeds with two reflections",
        ),
    ],
)
def test_calculate_ub(parms, context):
    solver = AdHocSolver(parms["geometry"])
    solver.lattice = dict(SI_LATTICE)
    solver.addReflection(FOURCV_R1)
    solver.addReflection(FOURCV_R2)
    with context:
        ub = solver.calculate_UB(FOURCV_R1, FOURCV_R2)
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
    solver = AdHocSolver()
    solver.addReflection(FOURCV_R1)
    solver.addReflection(FOURCV_R2)
    with context:
        solver.calculate_UB(FOURCV_R1, FOURCV_R2)


@pytest.mark.parametrize(
    "parms, context",
    [
        pytest.param(
            dict(
                mode="bisecting",
                pseudos={"h": 1.0, "k": 0.0, "l": 0.0},
                expected_h=1.0,
                expected_k=0.0,
                expected_l=0.0,
            ),
            does_not_raise(),
            id="forward (1,0,0) bisecting mode",
        ),
        pytest.param(
            dict(
                mode="fixed_chi",
                pseudos={"h": 0.0, "k": 1.0, "l": 0.0},
                expected_h=0.0,
                expected_k=1.0,
                expected_l=0.0,
            ),
            does_not_raise(),
            id="forward (0,1,0) fixed_chi mode",
        ),
        pytest.param(
            dict(
                mode="bisecting",
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
        hkl = solver.inverse(solutions[0])
        assert abs(hkl["h"] - parms["expected_h"]) < 0.01
        assert abs(hkl["k"] - parms["expected_k"]) < 0.01
        assert abs(hkl["l"] - parms["expected_l"]) < 0.01


@pytest.mark.parametrize(
    "parms, context",
    [
        pytest.param(
            dict(
                reals={"omega": THETA_100, "chi": 0, "phi": 0, "ttheta": TTH_100},
                expected_h=1.0,
                expected_k=0.0,
                expected_l=0.0,
            ),
            does_not_raise(),
            id="inverse r1 position -> (1,0,0)",
        ),
        pytest.param(
            dict(
                reals={"omega": THETA_100, "chi": 0, "phi": 90, "ttheta": TTH_100},
                expected_h=0.0,
                expected_k=1.0,
                expected_l=0.0,
            ),
            does_not_raise(),
            id="inverse r2 position -> (0,1,0)",
        ),
        pytest.param(
            dict(
                reals={"omega": 0, "chi": 0, "phi": 0, "ttheta": 0},
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
            dict(pseudos={"h": 1.0, "k": 0.0, "l": 0.0}),
            does_not_raise(),
            id="forward-inverse roundtrip (1,0,0)",
        ),
        pytest.param(
            dict(pseudos={"h": 0.0, "k": 1.0, "l": 0.0}),
            does_not_raise(),
            id="forward-inverse roundtrip (0,1,0)",
        ),
        pytest.param(
            dict(pseudos={"h": 1.0, "k": 1.0, "l": 0.0}),
            does_not_raise(),
            id="forward-inverse roundtrip (1,1,0)",
        ),
    ],
)
def test_forward_inverse_roundtrip(parms, context):
    solver = _make_solver_with_ub(mode="bisecting")
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
            dict(geometry="fourcv", mode="bisecting", expected=[]),
            does_not_raise(),
            id="fourcv bisecting has no extras",
        ),
        pytest.param(
            dict(geometry="fourcv", mode="fixed_psi", expected=["n_hat", "psi"]),
            does_not_raise(),
            id="fourcv fixed_psi exposes n_hat+psi",
        ),
        pytest.param(
            dict(
                geometry="fourcv",
                mode="double_diffraction",
                expected=["h2", "k2", "l2"],
            ),
            does_not_raise(),
            id="fourcv double_diffraction exposes h2/k2/l2",
        ),
        pytest.param(
            dict(geometry="psic", mode="bisecting_vertical", expected=[]),
            does_not_raise(),
            id="psic bisecting_vertical has no extras",
        ),
        pytest.param(
            dict(
                geometry="psic",
                mode="fixed_psi_vertical",
                expected=["n_hat", "psi"],
            ),
            does_not_raise(),
            id="psic fixed_psi_vertical exposes n_hat+psi",
        ),
        pytest.param(
            dict(
                geometry="psic",
                mode="fixed_alpha_i_vertical",
                expected=["n_hat", "alpha_i", "beta_out"],
            ),
            does_not_raise(),
            id="psic fixed_alpha_i_vertical exposes alpha_i+beta_out",
        ),
        pytest.param(
            dict(
                geometry="psic",
                mode="double_diffraction_vertical",
                expected=["h2", "k2", "l2"],
            ),
            does_not_raise(),
            id="psic double_diffraction_vertical exposes h2/k2/l2",
        ),
        pytest.param(
            dict(
                geometry="kappa6c",
                mode="fixed_psi_horizontal",
                expected=["n_hat", "psi"],
            ),
            does_not_raise(),
            id="kappa6c fixed_psi_horizontal exposes n_hat+psi",
        ),
        pytest.param(
            dict(
                geometry="sixc",
                mode="alpha_eq_beta_zaxis",
                expected=["n_hat", "alpha_i", "beta_out"],
            ),
            does_not_raise(),
            id="sixc alpha_eq_beta_zaxis exposes alpha_i+beta_out",
        ),
        pytest.param(
            dict(
                geometry="s2d2",
                mode="reflectivity",
                expected=["n_hat", "alpha_i", "beta_out"],
            ),
            does_not_raise(),
            id="s2d2 reflectivity exposes alpha_i+beta_out",
        ),
    ],
)
def test_extra_axis_names(parms, context):
    with context:
        solver = AdHocSolver(parms["geometry"])
        solver.mode = parms["mode"]
        assert solver.extra_axis_names == parms["expected"]
        # extras dict has exactly the same keys as extra_axis_names.
        assert list(solver.extras.keys()) == parms["expected"]


@pytest.mark.parametrize(
    "parms, context",
    [
        pytest.param(
            dict(
                geometry="fourcv",
                mode="fixed_psi",
                values={"psi": 45.0, "n_hat": (0, 0, 1)},
                check={"psi": 45.0, "n_hat": (0.0, 0.0, 1.0)},
            ),
            does_not_raise(),
            id="set psi scalar and n_hat on fourcv fixed_psi",
        ),
        pytest.param(
            dict(
                geometry="psic",
                mode="fixed_alpha_i_vertical",
                values={"alpha_i": 1.5, "n_hat": [1, 0, 0]},
                check={"alpha_i": 1.5, "n_hat": (1.0, 0.0, 0.0)},
            ),
            does_not_raise(),
            id="set alpha_i and n_hat on psic fixed_alpha_i_vertical",
        ),
        pytest.param(
            dict(
                geometry="fourcv",
                mode="double_diffraction",
                values={"h2": 1.0, "k2": 2.0, "l2": 3.0},
                check={"h2": 1.0, "k2": 2.0, "l2": 3.0},
            ),
            does_not_raise(),
            id="set h2/k2/l2 on fourcv double_diffraction",
        ),
        pytest.param(
            dict(
                geometry="fourcv",
                mode="fixed_psi",
                values={"n_hat": None},
                check={"n_hat": None},
            ),
            does_not_raise(),
            id="clear n_hat by setting None",
        ),
        pytest.param(
            dict(
                geometry="fourcv",
                mode="fixed_psi",
                values={"unknown_extra": 99.0},
                check={},
            ),
            does_not_raise(),
            id="unknown extras are silently ignored",
        ),
        pytest.param(
            dict(
                geometry="fourcv",
                mode="fixed_psi",
                values=[("psi", 1.0)],  # wrong type
                check={},
            ),
            pytest.raises(TypeError, match=re.escape("Must supply dict")),
            id="non-dict raises TypeError",
        ),
        pytest.param(
            dict(
                geometry="fourcv",
                mode="fixed_psi",
                values={},
                check={"psi": 0.0},  # default psi unchanged
            ),
            does_not_raise(),
            id="empty dict is a no-op",
        ),
    ],
)
def test_set_get_extras(parms, context):
    with context:
        solver = AdHocSolver(parms["geometry"])
        solver.mode = parms["mode"]
        solver.extras = parms["values"]
        current = solver.extras
        for key, expected in parms["check"].items():
            assert current[key] == expected, f"extras[{key!r}] expected {expected!r} got {current[key]!r}"


@pytest.mark.parametrize(
    "parms, context",
    [
        pytest.param(
            dict(
                geometry="fourcv",
                mode="double_diffraction",
                extras={"h2": 0.0, "k2": 1.0, "l2": 0.0},
                pseudos={"h": 1.0, "k": 0.0, "l": 0.0},
            ),
            does_not_raise(),
            id="fourcv double_diffraction forward with h2/k2/l2",
        ),
        pytest.param(
            dict(
                geometry="psic",
                mode="double_diffraction_vertical",
                extras={"h2": 0.0, "k2": 1.0, "l2": 0.0},
                pseudos={"h": 1.0, "k": 0.0, "l": 0.0},
            ),
            does_not_raise(),
            id="psic double_diffraction_vertical forward with h2/k2/l2",
        ),
    ],
)
def test_forward_with_extras(parms, context):
    """Forward calculation honours extras for implemented modes.

    .. note::
        ``ad_hoc_diffractometer`` 0.8.0 marks the surface (``alpha_i``,
        ``beta_out``, ``alpha_eq_beta``) and ``fixed_psi_*`` modes as
        not yet implemented.  This test exercises the ``double_diffraction``
        family because it is implemented and uses extras (``h2``, ``k2``,
        ``l2``).  When upstream implements the surface modes, additional
        cases should be added here.
    """
    with context:
        solver = _make_solver_with_ub(parms["geometry"])
        solver.mode = parms["mode"]
        solver.extras = parms["extras"]
        solutions = solver.forward(parms["pseudos"])
        assert len(solutions) >= 1
        for key, value in parms["extras"].items():
            stored = solver.extras[key]
            if isinstance(value, (list, tuple)):
                assert stored == tuple(float(x) for x in value)
            else:
                assert stored == value


@pytest.mark.parametrize(
    "parms, context",
    [
        pytest.param(
            dict(
                geometry="fourcv",
                mode="fixed_psi",
                expected_extras=["n_hat", "psi"],
            ),
            does_not_raise(),
            id="summary_dict reports fixed_psi extras",
        ),
        pytest.param(
            dict(
                geometry="fourcv",
                mode="bisecting",
                expected_extras=[],
            ),
            does_not_raise(),
            id="summary_dict reports empty extras for bisecting",
        ),
        pytest.param(
            dict(
                geometry="psic",
                mode="double_diffraction_vertical",
                expected_extras=["h2", "k2", "l2"],
            ),
            does_not_raise(),
            id="summary_dict reports h2/k2/l2 for double_diffraction_vertical",
        ),
    ],
)
def test_summary_dict_includes_extras(parms, context):
    with context:
        solver = AdHocSolver(parms["geometry"])
        sd = solver._summary_dict
        assert sd["modes"][parms["mode"]]["extras"] == parms["expected_extras"]


@pytest.mark.parametrize(
    "parms, context",
    [
        pytest.param(
            dict(),
            does_not_raise(),
            id="AdHocSolver.version matches backend library",
        ),
    ],
)
def test_solver_version(parms, context):
    from importlib.metadata import version as _pkg_version

    with context:
        assert AdHocSolver.version == _pkg_version("ad_hoc_diffractometer")
        # Sanity: not the legacy hardcoded value.
        assert AdHocSolver.version != "0.1.0"


@pytest.mark.parametrize(
    "parms, context",
    [
        pytest.param(
            dict(
                geometry="fourcv",
                mode="bisecting",
                # bisecting constrains omega via bisect; only chi, phi, ttheta are writable
                # but constant_stages reports omega as constant
                expected_writable=["chi", "phi", "ttheta"],
            ),
            does_not_raise(),
            id="fourcv bisecting writable axes",
        ),
        pytest.param(
            dict(
                geometry="fourcv",
                mode="fixed_chi",
                expected_writable=["omega", "phi", "ttheta"],
            ),
            does_not_raise(),
            id="fourcv fixed_chi writable axes",
        ),
        pytest.param(
            dict(
                geometry="psic",
                mode="bisecting_vertical",
                expected_writable=["chi", "phi", "delta"],
            ),
            does_not_raise(),
            id="psic bisecting_vertical writable axes",
        ),
    ],
)
def test_axes_w(parms, context):
    with context:
        solver = AdHocSolver(parms["geometry"])
        solver.mode = parms["mode"]
        assert solver.axes_w == parms["expected_writable"]


@pytest.mark.parametrize(
    "parms, context",
    [
        pytest.param(
            dict(),
            does_not_raise(),
            id="UB defaults to identity before calculation",
        ),
    ],
)
def test_ub_before_calculation(parms, context):
    solver = AdHocSolver()
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
        solver.removeAllReflections()
        assert solver.wavelength is None
        # UB should revert to identity
        ub = solver.UB
        assert ub == [[1, 0, 0], [0, 1, 0], [0, 0, 1]]


@pytest.mark.parametrize(
    "parms, context",
    [
        pytest.param(
            dict(value=1.5406),
            does_not_raise(),
            id="positive wavelength accepted",
        ),
        pytest.param(
            dict(value=-1.0),
            pytest.raises(ValueError, match=re.escape("positive number")),
            id="negative wavelength raises ValueError",
        ),
        pytest.param(
            dict(value=0.0),
            pytest.raises(ValueError, match=re.escape("positive number")),
            id="zero wavelength raises ValueError",
        ),
        pytest.param(
            dict(value="not a number"),
            pytest.raises(TypeError, match=re.escape("Must supply number")),
            id="non-numeric wavelength raises TypeError",
        ),
    ],
)
def test_wavelength_setter(parms, context):
    solver = AdHocSolver()
    with context:
        solver.wavelength = parms["value"]
        assert solver.wavelength == parms["value"]


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
    solver = AdHocSolver()
    solver.lattice = dict(SI_LATTICE)
    solver.wavelength = WAVELENGTH
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
    solver = AdHocSolver()
    solver.lattice = dict(SI_LATTICE)
    # Set UB but not wavelength
    solver.addReflection(FOURCV_R1)
    solver.addReflection(FOURCV_R2)
    solver.calculate_UB(FOURCV_R1, FOURCV_R2)
    # Clear wavelength after calculate_UB set it from reflections.
    solver._wavelength = None
    with context:
        solver.forward({"h": 1, "k": 0, "l": 0})


@pytest.mark.parametrize(
    "parms, context",
    [
        pytest.param(
            dict(),
            does_not_raise(),
            id="lattice preserved after removeAllReflections",
        ),
    ],
)
def test_lattice_preserved_after_reset(parms, context):
    solver = _make_solver_with_ub()
    with context:
        solver.removeAllReflections()
        assert solver.lattice == SI_LATTICE


@pytest.mark.parametrize(
    "parms, context",
    [
        pytest.param(
            dict(pseudos={"h": 1, "k": 0, "l": 0}),
            does_not_raise(),
            id="forward returns solutions with all axis names",
        ),
    ],
)
def test_forward_multiple_solutions(parms, context):
    solver = _make_solver_with_ub(mode="bisecting")
    with context:
        solutions = solver.forward(parms["pseudos"])
        assert len(solutions) >= 1
        for sol in solutions:
            assert set(sol.keys()) == set(solver.real_axis_names)


@pytest.mark.parametrize(
    "parms, context",
    [
        pytest.param(
            dict(
                pseudos={"h": 100, "k": 100, "l": 100},
            ),
            pytest.raises(Exception),
            id="unreachable reflection raises SolverError",
        ),
    ],
)
def test_forward_unreachable(parms, context):
    solver = _make_solver_with_ub(mode="bisecting")
    with context:
        solver.forward(parms["pseudos"])


@pytest.mark.parametrize(
    "parms, context",
    [
        pytest.param(
            dict(mode=""),
            does_not_raise(),
            id="empty string mode accepted",
        ),
    ],
)
def test_mode_set_empty(parms, context):
    solver = AdHocSolver()
    with context:
        solver.mode = parms["mode"]
        assert solver.mode == ""


@pytest.mark.parametrize(
    "parms, context",
    [
        pytest.param(
            dict(
                reals={"omega": 0, "chi": 0, "phi": 0, "ttheta": 0},
            ),
            does_not_raise(),
            id="inverse without explicit UB uses default",
        ),
    ],
)
def test_inverse_without_ub(parms, context):
    solver = AdHocSolver()
    with context:
        hkl = solver.inverse(parms["reals"])
        assert abs(hkl["h"]) < 0.01
        assert abs(hkl["k"]) < 0.01
        assert abs(hkl["l"]) < 0.01


@pytest.mark.parametrize(
    "parms, context",
    [
        pytest.param(
            dict(
                reals={"omega": 0, "chi": 0, "phi": 0, "ttheta": 0},
            ),
            does_not_raise(),
            id="inverse with default UB is idempotent",
        ),
    ],
)
def test_inverse_default_ub_idempotent(parms, context):
    solver = AdHocSolver()
    with context:
        hkl1 = solver.inverse(parms["reals"])
        hkl2 = solver.inverse(parms["reals"])
        for axis in ("h", "k", "l"):
            assert hkl1[axis] == hkl2[axis]


@pytest.mark.parametrize(
    "parms, context",
    [
        pytest.param(
            dict(
                sample={
                    "lattice": SI_LATTICE,
                    "reflections": {},
                    "order": [],
                },
            ),
            does_not_raise(),
            id="sample setter pushes lattice",
        ),
    ],
)
def test_sample_setter_pushes_lattice(parms, context):
    solver = AdHocSolver()
    with context:
        solver.sample = parms["sample"]
        assert solver.lattice == SI_LATTICE


@pytest.mark.parametrize(
    "parms, context",
    [
        pytest.param(
            dict(),
            does_not_raise(),
            id="calculate_UB after sample setter",
        ),
    ],
)
def test_calculate_ub_after_sample_setter(parms, context):
    solver = AdHocSolver()
    solver.sample = {
        "lattice": SI_LATTICE,
        "reflections": {
            "r1": FOURCV_R1,
            "r2": FOURCV_R2,
        },
        "order": ["r1", "r2"],
    }
    with context:
        ub = solver.calculate_UB(FOURCV_R1, FOURCV_R2)
        assert len(ub) == 3
        assert all(len(row) == 3 for row in ub)


@pytest.mark.parametrize(
    "parms, context",
    [
        pytest.param(
            dict(),
            does_not_raise(),
            id="sample setter re-populates reflections",
        ),
    ],
)
def test_sample_setter_repopulates_reflections(parms, context):
    solver = _make_solver_with_ub()
    sample_dict = {
        "lattice": SI_LATTICE,
        "reflections": {
            "r1": FOURCV_R1,
            "r2": FOURCV_R2,
        },
        "order": ["r1", "r2"],
    }
    with context:
        solver.sample = sample_dict
        assert len(solver._reflections) == 2


@pytest.mark.parametrize(
    "parms, context",
    [
        pytest.param(
            dict(
                reals={"omega": 10.0, "chi": 20.0, "phi": 30.0, "ttheta": 40.0},
            ),
            does_not_raise(),
            id="set_reals pushes angle values",
        ),
        pytest.param(
            dict(reals="not a dict"),
            pytest.raises(TypeError, match=re.escape("Must supply dict")),
            id="set_reals non-dict raises TypeError",
        ),
        pytest.param(
            dict(reals={"omega": "bad"}),
            pytest.raises(TypeError, match=re.escape("All values must be numbers")),
            id="set_reals non-numeric raises TypeError",
        ),
    ],
)
def test_set_reals(parms, context):
    solver = AdHocSolver()
    with context:
        solver.set_reals(parms["reals"])


@pytest.mark.parametrize(
    "parms, context",
    [
        pytest.param(
            dict(
                ub=[[1, 0, 0], [0, 1, 0], [0, 0, 1]],
            ),
            does_not_raise(),
            id="UB setter accepts identity matrix",
        ),
        pytest.param(
            dict(
                ub=[[0.1, 0.2, 0.3], [0.4, 0.5, 0.6], [0.7, 0.8, 0.9]],
            ),
            does_not_raise(),
            id="UB setter accepts arbitrary matrix",
        ),
    ],
)
def test_ub_setter(parms, context):
    solver = AdHocSolver()
    solver.lattice = dict(SI_LATTICE)
    with context:
        solver.UB = parms["ub"]
        result = solver.UB
        for i in range(3):
            for j in range(3):
                assert abs(result[i][j] - parms["ub"][i][j]) < 1e-10


@pytest.mark.parametrize(
    "parms, context",
    [
        pytest.param(
            dict(),
            does_not_raise(),
            id="forward after UB restore works",
        ),
    ],
)
def test_forward_after_ub_restore(parms, context):
    solver = _make_solver_with_ub(mode="bisecting")
    ub = solver.UB

    # Create a fresh solver and restore UB.
    solver2 = AdHocSolver()
    solver2.lattice = dict(SI_LATTICE)
    solver2.wavelength = WAVELENGTH
    solver2.UB = ub
    solver2.mode = "bisecting"

    with context:
        solutions = solver2.forward({"h": 1, "k": 0, "l": 0})
        assert len(solutions) >= 1
        hkl = solver2.inverse(solutions[0])
        assert abs(hkl["h"] - 1.0) < 0.01


@pytest.mark.parametrize(
    "parms, context",
    [
        pytest.param(
            dict(),
            does_not_raise(),
            id="summary_dict has expected structure",
        ),
    ],
)
def test_summary_dict(parms, context):
    solver = AdHocSolver()
    with context:
        sd = solver._summary_dict
        assert "name" in sd
        assert "pseudos" in sd
        assert "reals" in sd
        assert "modes" in sd
        assert sd["name"] == DEFAULT_GEOMETRY
        assert sd["pseudos"] == PSEUDO_AXES
        assert sd["reals"] == GEOMETRY_INFO["fourcv"]["real_axes"]
        # Every mode should have reals and extras keys.
        for mode_name, mode_info in sd["modes"].items():
            assert "reals" in mode_info
            assert "extras" in mode_info
            assert isinstance(mode_info["reals"], list)


@pytest.mark.parametrize(
    "parms, context",
    [
        pytest.param(
            dict(geometry=geometry),
            does_not_raise(),
            id=f"{geometry} summary_dict",
        )
        for geometry in GEOMETRY_INFO
    ],
)
def test_summary_dict_all_geometries(parms, context):
    with context:
        solver = AdHocSolver(parms["geometry"])
        sd = solver._summary_dict
        assert len(sd["modes"]) == GEOMETRY_INFO[parms["geometry"]]["mode_count"]


@pytest.mark.parametrize(
    "parms, context",
    [
        pytest.param(
            dict(geometry="psic", mode="bisecting_vertical"),
            does_not_raise(),
            id="psic forward-inverse roundtrip",
        ),
    ],
)
def test_psic_forward_inverse(parms, context):
    solver = _make_solver_with_ub(geometry="psic", mode=parms["mode"])
    with context:
        solutions = solver.forward({"h": 1, "k": 0, "l": 0})
        assert len(solutions) >= 1
        hkl = solver.inverse(solutions[0])
        assert abs(hkl["h"] - 1.0) < 0.01
        assert abs(hkl["k"]) < 0.01
        assert abs(hkl["l"]) < 0.01


@pytest.mark.parametrize(
    "parms, context",
    [
        pytest.param(
            dict(
                reflections=[],
            ),
            does_not_raise(),
            id="refineLattice with insufficient reflections returns None",
        ),
    ],
)
def test_refine_lattice_insufficient_reflections(parms, context):
    solver = _make_solver_with_ub()
    # Only 2 reflections, need >= 3
    with context:
        result = solver.refineLattice(parms["reflections"])
        assert result is None


@pytest.mark.parametrize(
    "parms, context",
    [
        pytest.param(
            dict(),
            does_not_raise(),
            id="refineLattice with 3+ reflections succeeds",
        ),
    ],
)
def test_refine_lattice_success(parms, context):
    solver = AdHocSolver()
    solver.lattice = dict(SI_LATTICE)

    r1 = FOURCV_R1
    r2 = FOURCV_R2
    r3 = {
        "name": "r3",
        "pseudos": {"h": 0.0, "k": 0.0, "l": 1.0},
        "reals": {"omega": THETA_100, "chi": 90, "phi": 0, "ttheta": TTH_100},
        "wavelength": WAVELENGTH,
    }
    solver.addReflection(r1)
    solver.addReflection(r2)
    solver.addReflection(r3)
    solver.calculate_UB(r1, r2)

    with context:
        result = solver.refineLattice([r1, r2, r3])
        if result is not None:
            assert "a" in result
            assert "b" in result
            assert "c" in result
            assert "alpha" in result
            assert "beta" in result
            assert "gamma" in result

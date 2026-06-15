# Copyright (c) 2025-2026 UChicago Argonne, LLC
# SPDX-License-Identifier: LicenseRef-UChicago-Argonne-LLC-License
"""Tests for the ad_hoc solver adapter."""

import math
import re
from contextlib import nullcontext as does_not_raise

import pytest
from hklpy2.exceptions import SolverError

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
        "mode_count": 24,
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
        "mode_count": 14,
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


# Distinct reflections used to verify that ``calculate_UB`` honours its
# arguments rather than reaching into the solver's existing reflection
# state.  ``DISTRACTOR_R1`` / ``DISTRACTOR_R2`` are well-separated in
# reciprocal space from ``FOURCV_R1`` / ``FOURCV_R2`` so the resulting
# UBs are visibly different.
DISTRACTOR_R1 = {
    "name": "distractor1",
    "pseudos": {"h": 1.0, "k": 1.0, "l": 0.0},
    "reals": {"omega": THETA_100, "chi": 0, "phi": 45, "ttheta": TTH_100},
    "wavelength": WAVELENGTH,
}
DISTRACTOR_R2 = {
    "name": "distractor2",
    "pseudos": {"h": 0.0, "k": 0.0, "l": 1.0},
    "reals": {"omega": THETA_100, "chi": 90, "phi": 0, "ttheta": TTH_100},
    "wavelength": WAVELENGTH,
}
# Two pseudos-collinear reflections (both along h) -- the underlying
# ``ub_from_two_reflections_bl1967`` rejects these, surfacing as a
# ``SolverError`` from ``calculate_UB``.  Used to cover the
# ValueError -> SolverError translation branch.
COLINEAR_R1 = {
    "name": "col1",
    "pseudos": {"h": 1.0, "k": 0.0, "l": 0.0},
    "reals": {"omega": THETA_100, "chi": 0, "phi": 0, "ttheta": TTH_100},
    "wavelength": WAVELENGTH,
}
COLINEAR_R2 = {
    "name": "col2",
    "pseudos": {"h": 2.0, "k": 0.0, "l": 0.0},
    "reals": {"omega": 2 * THETA_100, "chi": 0, "phi": 0, "ttheta": 2 * TTH_100},
    "wavelength": WAVELENGTH,
}


@pytest.mark.parametrize(
    "parms, context",
    [
        pytest.param(
            dict(
                preload=[DISTRACTOR_R1, DISTRACTOR_R2],
                r1=FOURCV_R1,
                r2=FOURCV_R2,
                expected_or1="r1",
                expected_or2="r2",
            ),
            does_not_raise(),
            id="calculate_UB honours r1/r2 over stale preloaded reflections",
        ),
        pytest.param(
            dict(
                preload=[],
                r1=FOURCV_R1,
                r2=FOURCV_R2,
                expected_or1="r1",
                expected_or2="r2",
            ),
            does_not_raise(),
            id="calculate_UB honours r1/r2 with no preloaded reflections",
        ),
        pytest.param(
            dict(
                preload=[FOURCV_R1, FOURCV_R2, DISTRACTOR_R1, DISTRACTOR_R2],
                r1=DISTRACTOR_R1,
                r2=DISTRACTOR_R2,
                expected_or1="distractor1",
                expected_or2="distractor2",
            ),
            does_not_raise(),
            id="calculate_UB picks named pair from a longer preloaded list",
        ),
        pytest.param(
            dict(
                preload=[],
                r1=COLINEAR_R1,
                r2=COLINEAR_R2,
                expected_or1=None,
                expected_or2=None,
            ),
            pytest.raises(SolverError),
            id="calculate_UB translates ValueError to SolverError on colinear pair",
        ),
    ],
)
def test_calculate_ub_honours_arguments(parms, context):
    """``calculate_UB(r1, r2)`` MUST honour its arguments.

    Regression for :issue:`56`: the previous implementation ignored
    ``r1`` and ``r2`` and computed UB from whatever reflections were
    designated as ``or0``/``or1`` on the underlying ad_hoc sample.
    The current implementation clears the solver's reflection state
    and inserts exactly the two reflections the caller named, so the
    AHD ``or1``/``or2`` slots end up naming ``r1`` and ``r2``.
    """
    solver = AdHocSolver("fourcv")
    solver.lattice = dict(SI_LATTICE)
    for refl in parms["preload"]:
        solver.addReflection(refl)
    with context:
        ub = solver.calculate_UB(parms["r1"], parms["r2"])
        # UB is a 3x3 matrix.
        assert len(ub) == 3
        assert all(len(row) == 3 for row in ub)
        # The AHD orienting-reflection slots now name r1/r2.
        refls = solver._geom.sample.reflections
        assert refls._or1_name == parms["expected_or1"]
        assert refls._or2_name == parms["expected_or2"]
        # And only those two reflections remain on the solver side.
        assert list(refls._data.keys()) == [
            parms["expected_or1"],
            parms["expected_or2"],
        ]


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
                extras={"h2": 0.0, "k2": 1.0, "l2": 1.0},
                pseudos={"h": 1.0, "k": 1.0, "l": 1.0},
            ),
            does_not_raise(),
            id="fourcv double_diffraction forward with h2/k2/l2",
        ),
        pytest.param(
            dict(
                geometry="psic",
                mode="double_diffraction_vertical",
                extras={"h2": 0.0, "k2": 1.0, "l2": 1.0},
                pseudos={"h": 1.0, "k": 1.0, "l": 1.0},
            ),
            does_not_raise(),
            id="psic double_diffraction_vertical forward with h2/k2/l2",
        ),
    ],
)
def test_forward_with_extras(parms, context):
    """Forward calculation honours extras for implemented modes.

    .. note::
        ``ad_hoc_diffractometer`` 0.11.0 marks the surface (``alpha_i``,
        ``beta_out``, ``alpha_eq_beta``) and ``fixed_psi_*`` modes as
        not yet implemented.  This test exercises the ``double_diffraction``
        family because it is implemented and uses extras (``h2``, ``k2``,
        ``l2``).  When upstream implements the surface modes, additional
        cases should be added here.

        The ``hkl = (1, 1, 1)`` primary with ``(h2, k2, l2) = (0, 1, 1)``
        secondary is chosen because it lies inside the Ewald sphere for
        the Si lattice at ``WAVELENGTH = 1.0`` Å and yields multiple
        valid forward solutions under the BL1967-aligned solver
        (``ad_hoc_diffractometer >= 0.11.0``).
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
    solver.calculate_UB(r1, r2)
    # ``calculate_UB`` clears any extra reflections (it now honours its
    # own r1/r2 arguments by resetting the solver's reflection list).
    # Re-add r3 so ``refineLattice`` sees the 3 reflections it needs.
    solver.addReflection(r3)

    with context:
        result = solver.refineLattice([r1, r2, r3])
        if result is not None:
            assert "a" in result
            assert "b" in result
            assert "c" in result
            assert "alpha" in result
            assert "beta" in result
            assert "gamma" in result


# ---------------------------------------------------------------------------
# Coverage-targeted edge-case tests (issue #46)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "parms, context",
    [
        pytest.param(
            dict(geometry="kappa6c", kwargs={"kappa_alpha_deg": 50.0}),
            does_not_raise(),
            id="kappa_alpha_deg passed through to factory",
        ),
        pytest.param(
            dict(geometry="kappa4cv", kwargs={"kappa_alpha_deg": 60.0}),
            does_not_raise(),
            id="kappa_alpha_deg accepted by kappa4cv",
        ),
    ],
)
def test_kappa_alpha_deg(parms, context):
    """``kappa_alpha_deg`` keyword reaches the geometry factory."""
    with context:
        solver = AdHocSolver(parms["geometry"], **parms["kwargs"])
        assert solver._geom._kappa_alpha_deg == parms["kwargs"]["kappa_alpha_deg"]


@pytest.mark.parametrize(
    "parms, context",
    [
        pytest.param(
            dict(wavelength=1.5),
            does_not_raise(),
            id="default UB respects pre-set wavelength",
        ),
    ],
)
def test_default_ub_preserves_wavelength(parms, context):
    """``_init_default_ub`` must not overwrite an already-set wavelength."""
    with context:
        solver = AdHocSolver()
        solver.wavelength = parms["wavelength"]
        # Trigger _init_default_ub via inverse() before any UB is set.
        solver.inverse({"omega": 0, "chi": 0, "phi": 0, "ttheta": 0})
        assert solver._geom.wavelength == parms["wavelength"]


@pytest.mark.parametrize(
    "parms, context",
    [
        pytest.param(
            dict(value="not a dict"),
            pytest.raises(TypeError, match=re.escape("Must supply dict")),
            id="non-dict raises TypeError",
        ),
        pytest.param(
            dict(value={"a": 5.0}),
            does_not_raise(),
            id="b/c default to a when omitted",
        ),
    ],
)
def test_lattice_setter_edge_cases(parms, context):
    """``lattice`` setter validates type and applies default for ``b``/``c``."""
    solver = AdHocSolver()
    with context:
        solver.lattice = parms["value"]
        if isinstance(parms["value"], dict):
            assert solver._geom.sample.lattice.a == parms["value"]["a"]
            assert solver._geom.sample.lattice.b == parms["value"]["a"]
            assert solver._geom.sample.lattice.c == parms["value"]["a"]


@pytest.mark.parametrize(
    "parms, context",
    [
        pytest.param(
            dict(value="not a dict"),
            pytest.raises(TypeError, match=re.escape("Must supply dictionary")),
            id="non-dict raises TypeError",
        ),
        pytest.param(
            dict(value={"order": []}),
            does_not_raise(),
            id="missing lattice key is tolerated",
        ),
        pytest.param(
            dict(
                value={
                    "lattice": SI_LATTICE,
                    "reflections": [FOURCV_R1, FOURCV_R2],
                    "order": ["r1", "r2"],
                },
            ),
            does_not_raise(),
            id="reflections supplied as list",
        ),
        pytest.param(
            dict(
                value={
                    "lattice": SI_LATTICE,
                    "reflections": {"r1": FOURCV_R1},
                    "order": ["r1", "missing"],
                },
            ),
            does_not_raise(),
            id="order names absent from reflections are skipped",
        ),
    ],
)
def test_sample_setter_edge_cases(parms, context):
    """Cover ``sample`` setter type guard, list reflections, and missing names."""
    solver = AdHocSolver()
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
    """``mode`` getter returns ``''`` after deleting ``_mode``."""
    solver = AdHocSolver()
    with context:
        del solver._mode
        assert solver.mode == ""


@pytest.mark.parametrize(
    "parms, context",
    [
        pytest.param(
            dict(),
            does_not_raise(),
            id="refineLattice swallows backend errors and warns",
        ),
    ],
)
def test_refine_lattice_failure(parms, context):
    """``refineLattice`` returns ``None`` when the backend raises."""
    solver = _make_solver_with_ub()
    # Add a third reflection so the >=3 guard passes.
    solver.addReflection(
        {
            "name": "r3",
            "pseudos": {"h": 0.0, "k": 0.0, "l": 1.0},
            "reals": {"omega": THETA_100, "chi": 90, "phi": 0, "ttheta": TTH_100},
            "wavelength": WAVELENGTH,
        }
    )
    # Replace one reflection's geometry sample with an object that will
    # break refine_lattice_bl1967 (drop the lattice).
    solver._geom.sample.lattice = None
    with context:
        result = solver.refineLattice([])
        assert result is None


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
    """Cover the branch where ``self._lattice`` is empty after reset."""
    solver = AdHocSolver()
    with context:
        solver.removeAllReflections()
        assert solver._lattice == {}


@pytest.mark.parametrize(
    "parms, context",
    [
        pytest.param(
            dict(stored=None),
            does_not_raise(),
            id="UB setter falls back to unit lattice when none stored",
        ),
        pytest.param(
            dict(stored=SI_LATTICE),
            does_not_raise(),
            id="UB setter restores stored lattice when geometry has none",
        ),
    ],
)
def test_ub_setter_default_lattice(parms, context):
    """Cover both branches of the ``UB`` setter lattice-fallback logic."""
    solver = AdHocSolver()
    if parms["stored"] is not None:
        solver.lattice = dict(parms["stored"])
    # Wipe the geometry-side lattice so the setter has to restore it.
    solver._geom.sample.lattice = None
    if parms["stored"] is None:
        solver._lattice = {}
    with context:
        solver.UB = [[1, 0, 0], [0, 1, 0], [0, 0, 1]]
        assert solver._geom.sample.lattice is not None


# ---------------------------------------------------------------------------
# Regression tests for issue #81: scalar default extras from hklpy2 Core
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "parms, context",
    [
        pytest.param(
            dict(
                geometry="fourcv",
                mode="fixed_psi",
                values={"n_hat": 0},
                expected_normal=None,
            ),
            does_not_raise(),
            id="scalar 0 n_hat is normalised to None",
        ),
        pytest.param(
            dict(
                geometry="psic",
                mode="fixed_alpha_i_vertical",
                values={"n_hat": 0, "alpha_i": 0, "beta_out": 0},
                expected_normal=None,
            ),
            does_not_raise(),
            id="full scalar-default extras dict (Core push) accepted",
        ),
        pytest.param(
            dict(
                geometry="fourcv",
                mode="fixed_psi",
                values={"n_hat": (1, 0, 0)},
                expected_normal=(1.0, 0.0, 0.0),
            ),
            does_not_raise(),
            id="3-iterable n_hat still works after fix",
        ),
        pytest.param(
            dict(
                geometry="fourcv",
                mode="fixed_psi",
                values={"n_hat": None},
                expected_normal=None,
            ),
            does_not_raise(),
            id="None n_hat still clears surface_normal after fix",
        ),
    ],
)
def test_extras_n_hat_scalar_default(parms, context):
    """``extras`` setter tolerates scalar ``n_hat`` from ``hklpy2.Core``.

    Regression for :issue:`81`: ``hklpy2.ops.Core.update_solver()``
    initialises every vector extra to scalar ``0`` (the module-level
    ``DEFAULT_EXTRA_VALUE``).  The previous implementation iterated
    ``n_hat`` unconditionally and raised ``TypeError`` for any
    non-iterable input, breaking ``hklpy2.creator(solver='ad_hoc',
    geometry='zaxis')``.  The fix normalises any non-iterable
    ``n_hat`` value to ``None`` (treated as "no surface normal set").
    """
    with context:
        solver = AdHocSolver(parms["geometry"])
        solver.mode = parms["mode"]
        solver.extras = parms["values"]
        assert solver._geom.surface_normal == parms["expected_normal"]


@pytest.mark.parametrize(
    "parms, context",
    [
        pytest.param(
            dict(geometry="zaxis"),
            does_not_raise(),
            id="hklpy2.creator builds ad_hoc/zaxis (default mode exposes n_hat)",
        ),
        pytest.param(
            dict(geometry="s2d2"),
            does_not_raise(),
            id="hklpy2.creator builds ad_hoc/s2d2",
        ),
        pytest.param(
            dict(geometry="fourcv"),
            does_not_raise(),
            id="hklpy2.creator builds ad_hoc/fourcv (no n_hat in default mode)",
        ),
    ],
)
def test_creator_end_to_end(parms, context):
    """End-to-end smoke: ``hklpy2.creator`` instantiation for ad_hoc.

    Regression for :issue:`81` (the ``zaxis`` case) and a guard that
    the fix does not regress geometries whose default mode does not
    expose ``n_hat``.
    """
    import hklpy2

    with context:
        sim = hklpy2.creator(solver="ad_hoc", geometry=parms["geometry"])
        assert sim.core.solver.name == "ad_hoc"
        assert sim.core.solver.geometry == parms["geometry"]


# ---------------------------------------------------------------------------
# Reference helpers (issues #63, #101, #103): six thin wrappers around
# ``ad_hoc_diffractometer.reference`` exposed as methods on ``AdHocSolver``.
# ---------------------------------------------------------------------------


REF_HELPER_ANGLES = dict(mu=0.0, eta=20.0, chi=30.0, phi=15.0, nu=0.0, delta=40.0)
"""Non-degenerate motor positions for the reference-helper tests."""


def _ref_helper_solver(*, configure: bool = True) -> AdHocSolver:
    """Build a psic AdHocSolver wired for reference-helper tests.

    When ``configure`` is False the geometry is left without
    ``azimuthal_reference`` / ``surface_normal`` so that failure
    paths in the upstream helpers can be exercised.
    """
    import ad_hoc_diffractometer as ahd

    solver = AdHocSolver(geometry="psic")
    solver._geom.wavelength = WAVELENGTH
    ahd.ub_identity(solver._geom.sample)
    solver.set_reals(REF_HELPER_ANGLES)
    if configure:
        solver._geom.azimuthal_reference = (0, 0, 1)
        solver._geom.surface_normal = (1, 1, 6)
    return solver


@pytest.mark.parametrize(
    "parms, context",
    [
        pytest.param(
            dict(
                method="psi_angle",
                args=(REF_HELPER_ANGLES,),
                expected=pytest.approx(97.63074021243006, abs=1e-9),
            ),
            does_not_raise(),
            id="psi_angle with explicit angles dict",
        ),
        pytest.param(
            dict(
                method="psi_angle",
                args=(),
                expected=pytest.approx(97.63074021243006, abs=1e-9),
            ),
            does_not_raise(),
            id="psi_angle with default None angles uses current geometry",
        ),
        pytest.param(
            dict(
                method="incidence_angle",
                args=(REF_HELPER_ANGLES,),
                expected=pytest.approx(6.748271970061214, abs=1e-9),
            ),
            does_not_raise(),
            id="incidence_angle with explicit angles dict",
        ),
        pytest.param(
            dict(
                method="exit_angle",
                args=(REF_HELPER_ANGLES,),
                expected=pytest.approx(19.456294998006513, abs=1e-9),
            ),
            does_not_raise(),
            id="exit_angle with explicit angles dict",
        ),
        pytest.param(
            dict(
                method="naz_angle",
                args=(REF_HELPER_ANGLES,),
                expected=pytest.approx(80.53767779197439, abs=1e-9),
            ),
            does_not_raise(),
            id="naz_angle with explicit angles dict",
        ),
        pytest.param(
            dict(
                method="omega_pseudo",
                args=(REF_HELPER_ANGLES,),
                expected=pytest.approx(0.0, abs=1e-9),
            ),
            does_not_raise(),
            id="omega_pseudo with explicit angles dict",
        ),
        pytest.param(
            dict(
                method="natural_psi",
                args=(1, 1, 1),
                expected=pytest.approx(120.0, abs=1e-9),
            ),
            does_not_raise(),
            id="natural_psi returns float for (1, 1, 1)",
        ),
        pytest.param(
            dict(
                method="natural_psi",
                args=(0, 0, 1),
                expected=None,
            ),
            does_not_raise(),
            id="natural_psi returns None when reflection parallel to azimuthal reference",
        ),
        pytest.param(
            dict(
                method="psi_angle",
                args=({"bogus": 0.0},),
                expected=None,
            ),
            pytest.raises(SolverError, match=re.escape("Unknown axis name(s) ['bogus']")),
            id="psi_angle with unknown axis name raises SolverError",
        ),
        pytest.param(
            dict(
                method="incidence_angle",
                args=([0.0, 0.0, 0.0],),
                expected=None,
            ),
            pytest.raises(TypeError, match=re.escape("angles must be a dict[str, float] or None")),
            id="incidence_angle with non-dict angles raises TypeError",
        ),
    ],
)
def test_reference_helpers(parms, context):
    """Cover all six reference-helper methods plus their failure paths.

    Verifies that ``AdHocSolver.{psi,incidence,exit,naz}_angle``,
    ``omega_pseudo`` and ``natural_psi`` forward to
    :mod:`ad_hoc_diffractometer.reference`, accept the documented
    inputs (dict-of-angles, default ``None``, or ``h, k, l``), and that
    the wrapper's own validation surfaces ``SolverError`` / ``TypeError``
    for malformed inputs.  Closes :issue:`63`, :issue:`101`,
    :issue:`103`.
    """
    with context:
        solver = _ref_helper_solver()
        method = getattr(solver, parms["method"])
        result = method(*parms["args"])
        if parms["expected"] is None:
            assert result is None
        else:
            assert result == parms["expected"]


@pytest.mark.parametrize(
    "parms, context",
    [
        pytest.param(
            dict(method="psi_angle"),
            pytest.raises(ValueError, match=re.escape("azimuthal_reference")),
            id="psi_angle without azimuthal_reference raises upstream ValueError",
        ),
        pytest.param(
            dict(method="incidence_angle"),
            pytest.raises(ValueError, match=re.escape("surface_normal")),
            id="incidence_angle without surface_normal raises upstream ValueError",
        ),
        pytest.param(
            dict(method="exit_angle"),
            pytest.raises(ValueError, match=re.escape("surface_normal")),
            id="exit_angle without surface_normal raises upstream ValueError",
        ),
        pytest.param(
            dict(method="naz_angle"),
            pytest.raises(ValueError, match=re.escape("surface_normal")),
            id="naz_angle without surface_normal raises upstream ValueError",
        ),
    ],
)
def test_reference_helpers_missing_geometry_config(parms, context):
    """Preconditions documented on each wrapper are enforced by upstream.

    Wrappers do **not** silently default ``azimuthal_reference`` or
    ``surface_normal``; with neither set, the upstream call raises a
    ``ValueError`` mentioning the missing attribute.  This test pins
    that behaviour so users get a useful diagnostic rather than a
    silent garbage answer.
    """
    with context:
        solver = _ref_helper_solver(configure=False)
        method = getattr(solver, parms["method"])
        method(REF_HELPER_ANGLES)


# ---------------------------------------------------------------------------
# Persist solver-defined state through export/restore (:issue:`108`)
# ---------------------------------------------------------------------------


def _add_psic_user_mode(solver, name="my_psic_mode"):
    """Mutate ``solver._geom`` to add a custom user mode.

    Helper for the persistence tests below.  Uses
    ``ad_hoc_diffractometer``'s public ``ModeDict.__setitem__``
    contract.
    """
    import ad_hoc_diffractometer as ahd  # noqa: F401
    from ad_hoc_diffractometer.mode import ConstraintSet, SampleConstraint

    solver._geom.modes[name] = ConstraintSet(
        constraints=[
            SampleConstraint("mu", 0.5),
            SampleConstraint("eta", 1.0),
            SampleConstraint("chi", 2.0),
        ],
    )


@pytest.mark.parametrize(
    "parms, context",
    [
        pytest.param(
            dict(geometry="fourcv", modify=False, expect_geometry_state=False),
            does_not_raise(),
            id="vanilla built-in: geometry_state omitted",
        ),
        pytest.param(
            dict(geometry="psic", modify=True, expect_geometry_state=True),
            does_not_raise(),
            id="modified built-in: geometry_state present",
        ),
    ],
)
def test_metadata_persists_geometry_state(parms, context):
    """``_metadata`` emits ``geometry_state`` only when non-default.

    Regression for :issue:`108`: the ``solver:`` block in
    ``export()`` carries a snapshot of the geometry's structure
    only when the live geometry differs from a fresh reference;
    vanilla built-ins stay clean.
    """
    solver = AdHocSolver(geometry=parms["geometry"])
    if parms["modify"]:
        _add_psic_user_mode(solver)
    with context:
        meta = solver._metadata
        assert "mode" in meta
        assert ("geometry_state" in meta) is parms["expect_geometry_state"]
        if parms["expect_geometry_state"]:
            gs = meta["geometry_state"]
            assert "modes" in gs
            assert "samples" not in gs  # stripped to avoid double-restore
            assert "wavelength" not in gs
            assert "my_psic_mode" in gs["modes"]


def _psic_geometry_state_snapshot() -> dict:
    """Build a real geometry_state snapshot from a fresh psic geometry.

    Used by the parametrized ``test_init_replays_geometry_state_kwarg``
    tests below.  Constructed at test-collection time would fetch
    the wrong dict; call from within the test to keep the fixture
    fresh.
    """
    import ad_hoc_diffractometer as ahd

    from hklpy2_solvers.ad_hoc_solver import _GEOMETRY_STATE_OMIT_KEYS

    d = ahd.make_geometry("psic").to_dict()
    return {k: v for k, v in d.items() if k not in _GEOMETRY_STATE_OMIT_KEYS}


@pytest.mark.parametrize(
    "parms, context",
    [
        pytest.param(
            dict(geometry="psic", state="round-trip-fresh"),
            does_not_raise(),
            id="fresh snapshot replayed via from_dict reproduces psic",
        ),
        pytest.param(
            dict(geometry="psic", state="not a dict"),
            pytest.raises(SolverError, match=re.escape("geometry_state must be a dict")),
            id="non-dict geometry_state raises SolverError",
        ),
        pytest.param(
            dict(geometry="psic", state={"name": "fourcv"}),
            pytest.raises(SolverError, match=re.escape("does not match")),
            id="name mismatch between snapshot and geometry raises",
        ),
    ],
)
def test_init_replays_geometry_state_kwarg(parms, context):
    """Constructor pops and replays ``geometry_state`` from kwargs.

    The happy path round-trips a freshly-built psic snapshot
    through :meth:`ad_hoc_diffractometer.AdHocDiffractometer.from_dict`
    and produces a functional solver with all stages and modes
    intact.  Failure cases validate the hklpy2-side guards before
    delegating to ``from_dict``.
    """
    state = parms["state"]
    if state == "round-trip-fresh":
        state = _psic_geometry_state_snapshot()
    with context:
        solver = AdHocSolver(geometry=parms["geometry"], geometry_state=state)
        assert solver.geometry == parms["geometry"]
        # Verify a known psic mode is reachable through the replayed geometry.
        assert "bisecting_vertical" in solver.modes


@pytest.mark.parametrize(
    "parms, context",
    [
        pytest.param(
            dict(geometry="psic", custom_mode="my_psic_mode"),
            does_not_raise(),
            id="psic round-trip preserves user mode and selects it",
        ),
        pytest.param(
            dict(geometry="fourcv", custom_mode="my_fourcv_mode"),
            does_not_raise(),
            id="fourcv round-trip preserves user mode and selects it",
        ),
    ],
)
def test_simulator_from_config_round_trip(parms, context):
    """End-to-end round-trip via ``hklpy2.simulator_from_config``.

    Resolves :issue:`108`: a user mode added to the underlying
    ``ad_hoc_diffractometer`` geometry survives a YAML round-trip.
    The test calls ``update_solver()`` before ``export()`` to flush
    Core's cached mode (a documented upstream caching pattern).
    """
    import hklpy2
    from ad_hoc_diffractometer.mode import ConstraintSet, SampleConstraint
    from hklpy2.run_utils import simulator_from_config

    sim = hklpy2.creator(solver="ad_hoc", geometry=parms["geometry"], name="adhoc_persist")
    g = sim.core.solver._geom
    # The constraint set must be valid for the geometry; the simplest
    # universally-valid one is "fix every sample stage", which any
    # ad_hoc geometry accepts as a degenerate but well-formed mode.
    sample_stage_names = [s.name for s in g.sample_stages]
    g.modes[parms["custom_mode"]] = ConstraintSet(
        constraints=[SampleConstraint(name, 0.0) for name in sample_stage_names],
    )
    sim.core.mode = parms["custom_mode"]
    sim.core.update_solver()  # flush Core's mode cache before export
    cfg = sim.configuration
    with context:
        sim2 = simulator_from_config(cfg)
        assert parms["custom_mode"] in sim2.core.solver.modes
        assert sim2.core.mode == parms["custom_mode"]


@pytest.mark.parametrize(
    "parms, context",
    [
        pytest.param(
            dict(),
            does_not_raise(),
            id="vanilla solver round-trips without geometry_state in YAML",
        ),
    ],
)
def test_simulator_from_config_round_trip_vanilla(parms, context):
    """Vanilla solver round-trips cleanly (no geometry_state emitted)."""
    import hklpy2
    from hklpy2.run_utils import simulator_from_config

    sim = hklpy2.creator(solver="ad_hoc", geometry="fourcv", name="adhoc_vanilla")
    cfg = sim.configuration
    with context:
        assert "geometry_state" not in cfg["solver"]
        sim2 = simulator_from_config(cfg)
        assert sim2.core.solver.geometry == "fourcv"


@pytest.mark.parametrize(
    "parms, context",
    [
        pytest.param(
            dict(),
            does_not_raise(),
            id="built-in geometry set matches ad_hoc_diffractometer.list_geometries",
        ),
    ],
)
def test_builtin_geometry_set(parms, context):
    """Guard: hard-coded built-in set tracks ``ad_hoc_diffractometer``.

    If the upstream library ships a new built-in geometry, this
    test fails immediately so :data:`_AD_HOC_BUILTIN_GEOMETRIES`
    can be updated in the same commit rather than silently
    treating the new built-in as user-registered.
    """
    import ad_hoc_diffractometer as ahd

    from hklpy2_solvers.ad_hoc_solver import _AD_HOC_BUILTIN_GEOMETRIES

    with context:
        assert frozenset(ahd.list_geometries().keys()) == _AD_HOC_BUILTIN_GEOMETRIES


@pytest.mark.parametrize(
    "parms, context",
    [
        pytest.param(
            dict(),
            does_not_raise(),
            id="user-registered geometry always persists geometry_state",
        ),
    ],
)
def test_metadata_user_registered_geometry(parms, context):
    """A user-registered geometry persists ``geometry_state`` unconditionally.

    Geometries whose names are not in
    :data:`_AD_HOC_BUILTIN_GEOMETRIES` are treated as user-added
    and are always serialised, even when no extra modes have
    been attached (the registry presence alone is the deviation
    from a vanilla install).
    """
    import ad_hoc_diffractometer as ahd

    # Borrow a built-in YAML by registering it under a fresh name.
    # We use the existing ``fourcv.yml`` packaged by the library
    # so the test does not depend on writing a sidecar YAML to
    # disk.  Registration is reverted in the ``finally`` block to
    # keep the registry clean for other tests in the session.
    pkg_files = __import__("importlib.resources", fromlist=["files"]).files("ad_hoc_diffractometer.geometries")
    yaml_path = str(pkg_files / "fourcv.yml")
    custom_name = "fourcv_custom_for_test_108"
    ahd.register_geometry_file(yaml_path, name=custom_name)
    try:
        with context:
            solver = AdHocSolver(geometry=custom_name)
            meta = solver._metadata
            assert "geometry_state" in meta
            # The geometry's internal ``name`` field is taken from the
            # YAML file (``fourcv``), not from the registry key
            # (``custom_name``).  What we are pinning here is that the
            # ``geometry_state`` snapshot is *emitted* for a
            # user-registered name even though the underlying YAML is
            # a copy of a built-in.
            assert "modes" in meta["geometry_state"]
            assert meta["geometry"] == custom_name
    finally:
        # Manual cleanup of the global registry.  ``ad_hoc_diffractometer``
        # does not expose a public unregister API; mutate the private
        # registry dict directly so the next test sees a clean state.
        from ad_hoc_diffractometer import factories as _factories

        _factories._GEOMETRY_REGISTRY.pop(custom_name, None)


# ---------------------------------------------------------------------------
# Override fixed-axis default values via ``update_mode_constraints`` (:issue:`114`)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "parms, context",
    [
        pytest.param(
            dict(
                geometry="fourcv",
                active_mode="bisecting",
                target_mode="fixed_chi",
                updates={"chi": 45.0},
                check_mode="fixed_chi",
                check_constraint="chi",
                check_value=45.0,
            ),
            does_not_raise(),
            id="override fixed_chi default on named (inactive) mode",
        ),
        pytest.param(
            dict(
                geometry="fourcv",
                active_mode="fixed_chi",
                target_mode=None,  # active-mode shortcut
                updates={"chi": 30.0},
                check_mode="fixed_chi",
                check_constraint="chi",
                check_value=30.0,
            ),
            does_not_raise(),
            id="override default on active mode via None shortcut",
        ),
        pytest.param(
            dict(
                geometry="psic",
                active_mode="bisecting_vertical",
                target_mode="fixed_phi_vertical",
                updates={"phi": 10.0, "mu": 0.0},
                check_mode="fixed_phi_vertical",
                check_constraint="phi",
                check_value=10.0,
            ),
            does_not_raise(),
            id="multi-stage override on psic fixed_phi_vertical",
        ),
        pytest.param(
            dict(
                geometry="fourcv",
                active_mode="bisecting",
                target_mode="bogus_mode",
                updates={"chi": 0.0},
                check_mode=None,
                check_constraint=None,
                check_value=None,
            ),
            pytest.raises(SolverError, match=re.escape("Unknown mode 'bogus_mode'")),
            id="unknown mode name raises SolverError",
        ),
        pytest.param(
            dict(
                geometry="fourcv",
                active_mode="bisecting",
                target_mode="fixed_chi",
                updates={"bogus_axis": 1.0},
                check_mode=None,
                check_constraint=None,
                check_value=None,
            ),
            pytest.raises(SolverError, match=re.escape("update_mode_constraints('fixed_chi'")),
            id="unknown constraint name raises SolverError",
        ),
        pytest.param(
            dict(
                geometry="fourcv",
                active_mode="bisecting",
                target_mode="fixed_chi",
                updates={"chi": "not_a_number"},
                check_mode=None,
                check_constraint=None,
                check_value=None,
            ),
            pytest.raises(SolverError, match=re.escape("update_mode_constraints('fixed_chi'")),
            id="bad value type raises SolverError",
        ),
    ],
)
def test_update_mode_constraints(parms, context):
    """``update_mode_constraints`` overrides mode-baked default values.

    Wraps :meth:`ad_hoc_diffractometer.mode.ConstraintSet.with_constraint_values`
    (upstream :issue:`293`) so users have a sanctioned API for changing
    a ``fixed_AXIS`` default without poking ``solver._geom._modes`` by
    hand.  Upstream ``KeyError`` / ``TypeError`` / ``ValueError`` are
    surfaced as :class:`~hklpy2.exceptions.SolverError`.
    """
    with context:
        solver = AdHocSolver(parms["geometry"])
        solver.mode = parms["active_mode"]
        solver.update_mode_constraints(parms["target_mode"], **parms["updates"])
        # Success-path assertions only run when no exception was raised.
        cs = solver._geom.modes[parms["check_mode"]]
        # Find the named constraint by its .name attribute.
        matched = [c for c in cs._constraints if getattr(c, "name", None) == parms["check_constraint"]]
        assert len(matched) == 1, f"expected exactly one constraint named {parms['check_constraint']!r}"
        assert matched[0].value == parms["check_value"]


@pytest.mark.parametrize(
    "parms, context",
    [
        pytest.param(
            dict(
                geometry="fourcv",
                active_mode="fixed_chi",
                new_chi=45.0,
            ),
            does_not_raise(),
            id="fourcv fixed_chi override is observed on next forward()",
        ),
    ],
)
def test_update_mode_constraints_is_observed_by_forward(parms, context):
    """The new constraint value reaches the solver on the next ``forward()``.

    Ensures the ``_geom._modes`` write + ``mode_name`` re-select pattern
    actually replaces the active ConstraintSet for downstream calls.
    """
    with context:
        solver = _make_solver_with_ub(geometry=parms["geometry"], mode=parms["active_mode"])
        # Default chi for fourcv fixed_chi is 90.0; override.
        solver.update_mode_constraints(chi=parms["new_chi"])
        solutions = solver.forward({"h": 1.0, "k": 0.0, "l": 0.0})
        assert len(solutions) > 0
        for sol in solutions:
            assert sol["chi"] == parms["new_chi"], (
                f"chi expected {parms['new_chi']} got {sol['chi']} (mode override not applied)"
            )

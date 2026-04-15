# Copyright (c) 2026 Pete Jemian <prjemian+hklpy2@gmail.com>
# SPDX-License-Identifier: LicenseRef-UChicago-Argonne-LLC-License
"""
Solver adapter wrapping *diffcalc-core* for hklpy2.

Provides the :class:`DiffcalcSolver` class, which implements the
:class:`hklpy2.backends.base.SolverBase` interface on top of the
`diffcalc-core <https://github.com/DiamondLightSource/diffcalc-core>`_
library (You 1999, 4S+2D six-circle geometry).

.. autosummary::

    ~DiffcalcSolver
"""

import logging
from typing import Any

from diffcalc.hkl.calc import HklCalculation
from diffcalc.hkl.constraints import Constraints
from diffcalc.hkl.geometry import Position
from diffcalc.ub.calc import UBCalculation
from diffcalc.util import DiffcalcException
from hklpy2.backends.base import SolverBase
from hklpy2.backends.typing import ReflectionDict
from hklpy2.misc import SolverError
from hklpy2.typing import Matrix3x3, NamedFloatDict

logger = logging.getLogger(__name__)

GEOMETRY_NAME = "diffcalc_4S_2D"
"""Geometry name exposed to hklpy2."""

REAL_AXES = ["mu", "delta", "nu", "eta", "chi", "phi"]
"""Ordered real axis names (matching diffcalc Position.fields)."""

PSEUDO_AXES = ["h", "k", "l"]
"""Ordered pseudo axis names."""

ENERGY_REST_KEV = 12.39842
"""Product of photon energy (keV) and wavelength (Angstrom)."""

# ---------------------------------------------------------------------------
# Mode definitions
# ---------------------------------------------------------------------------
# Each mode maps to exactly three diffcalc constraints.
# Constraint values are:
#   float  -> fix that axis / pseudo-angle to this value
#   True   -> activate a boolean constraint (a_eq_b, bin_eq_bout, bisect)
#
# Format: {mode_name: {constraint_name: value, ...}}
# The modes are grouped by the diffcalc constraint category pattern:
#   1 det + 1 ref + 1 samp
#   1 det + 2 samp
#   1 ref + 2 samp
#   3 samp

_MODES: dict[str, dict[str, Any]] = {
    # ---- 1 det + 1 ref + 1 samp ----
    "4S+2D mu_fixed a_eq_b delta_fixed": {"delta": 0.0, "a_eq_b": True, "mu": 0.0},
    "4S+2D mu_fixed a_eq_b nu_fixed": {"nu": 0.0, "a_eq_b": True, "mu": 0.0},
    "4S+2D eta_fixed a_eq_b delta_fixed": {"delta": 0.0, "a_eq_b": True, "eta": 0.0},
    "4S+2D phi_fixed psi_fixed nu_fixed": {"nu": 0.0, "psi": 0.0, "phi": 0.0},
    # ---- 1 det + 2 samp ----
    "4S+2D chi_phi_fixed delta_fixed": {"delta": 0.0, "chi": 0.0, "phi": 0.0},
    "4S+2D mu_eta_fixed delta_fixed": {"delta": 0.0, "mu": 0.0, "eta": 0.0},
    "4S+2D mu_phi_fixed delta_fixed": {"delta": 0.0, "mu": 0.0, "phi": 0.0},
    "4S+2D mu_chi_fixed nu_fixed": {"nu": 0.0, "mu": 0.0, "chi": 0.0},
    "4S+2D eta_phi_fixed nu_fixed": {"nu": 0.0, "eta": 0.0, "phi": 0.0},
    "4S+2D eta_chi_fixed nu_fixed": {"nu": 0.0, "eta": 0.0, "chi": 0.0},
    "4S+2D bisect_mu_fixed delta_fixed": {"delta": 0.0, "bisect": True, "mu": 0.0},
    "4S+2D bisect_eta_fixed nu_fixed": {"nu": 0.0, "bisect": True, "eta": 0.0},
    "4S+2D bisect_omega_fixed nu_fixed": {"nu": 0.0, "bisect": True, "omega": 0.0},
    # ---- 1 ref + 2 samp ----
    "4S+2D chi_phi_fixed a_eq_b": {"a_eq_b": True, "chi": 0.0, "phi": 0.0},
    "4S+2D chi_eta_fixed a_eq_b": {"a_eq_b": True, "chi": 0.0, "eta": 0.0},
    "4S+2D chi_mu_fixed a_eq_b": {"a_eq_b": True, "chi": 0.0, "mu": 0.0},
    "4S+2D mu_eta_fixed a_eq_b": {"a_eq_b": True, "mu": 0.0, "eta": 0.0},
    "4S+2D mu_phi_fixed a_eq_b": {"a_eq_b": True, "mu": 0.0, "phi": 0.0},
    "4S+2D eta_phi_fixed a_eq_b": {"a_eq_b": True, "eta": 0.0, "phi": 0.0},
    # ---- 3 samp ----
    "4S+2D eta_chi_phi_fixed": {"eta": 0.0, "chi": 0.0, "phi": 0.0},
    "4S+2D mu_chi_phi_fixed": {"mu": 0.0, "chi": 0.0, "phi": 0.0},
    "4S+2D mu_eta_phi_fixed": {"mu": 0.0, "eta": 0.0, "phi": 0.0},
    "4S+2D mu_eta_chi_fixed": {"mu": 0.0, "eta": 0.0, "chi": 0.0},
}


class DiffcalcSolver(SolverBase):
    """
    Solver adapter for diffcalc-core (You 1999, 4S+2D six-circle geometry).

    Wraps :class:`diffcalc.hkl.calc.HklCalculation` behind the
    :class:`~hklpy2.backends.base.SolverBase` interface so that hklpy2
    can use diffcalc-core for forward / inverse calculations.

    The only geometry supported is the You (1999) 4S+2D six-circle
    diffractometer with axes ``mu, delta, nu, eta, chi, phi``.

    Operating modes correspond to specific three-constraint combinations
    understood by diffcalc.

    This geometry has no extra parameters (``extras`` is always ``{}``).
    The :attr:`axes_w` property reports which real axes are computed by
    :meth:`forward` in the current mode; the remaining real axes are held
    constant (``axes_c``, derived by hklpy2's ``Core`` class).
    """

    name = "diffcalc"
    version = "0.1.0"

    def __init__(self, geometry: str = GEOMETRY_NAME, **kwargs: Any) -> None:
        if geometry != GEOMETRY_NAME:
            raise SolverError(
                f"DiffcalcSolver supports only the {GEOMETRY_NAME!r} geometry, received {geometry!r}."
            )

        # Initialize internal state *before* super().__init__ which
        # may set mode via the setter.
        self._ubcalc = UBCalculation("default")
        self._constraints = Constraints()
        self._hklcalc: HklCalculation | None = None
        self._reflections: list[ReflectionDict] = []
        self._wavelength: float | None = None
        self._lattice: NamedFloatDict = {}

        super().__init__(geometry, **kwargs)

        # Apply default mode if none was set via kwargs.
        if not self.mode and self.modes:
            self.mode = self.modes[0]

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _rebuild_hklcalc(self) -> None:
        """Recreate the HklCalculation from current state."""
        self._hklcalc = HklCalculation(self._ubcalc, self._constraints)

    def _apply_mode_constraints(self) -> None:
        """Set diffcalc constraints from the current mode."""
        if not self.mode:
            return
        self._constraints = Constraints(_MODES[self.mode])
        self._rebuild_hklcalc()

    def _position_from_reals(self, reals: NamedFloatDict) -> Position:
        """Build a diffcalc ``Position`` from a reals dict."""
        return Position(**{ax: float(reals.get(ax, 0.0)) for ax in REAL_AXES})

    def _reals_from_position(self, pos: Position) -> NamedFloatDict:
        """Build a reals dict from a diffcalc ``Position``."""
        return pos.asdict

    def _init_default_ub(self) -> None:
        """Initialise a default identity UB with a unit cubic lattice.

        Called automatically by :meth:`_ensure_ready_inverse` so that
        :meth:`inverse` (and therefore ``wh()``) works immediately after
        creating the diffractometer, before any reflections or explicit
        orientation have been supplied.  The resulting UB is a scaled
        identity matrix (B-matrix of a 1 Å cubic lattice with U=I).
        """
        if self._ubcalc.crystal is None:
            self._ubcalc.set_lattice("default", 1.0, 1.0, 1.0, 90.0, 90.0, 90.0)
        self._ubcalc.set_u([[1, 0, 0], [0, 1, 0], [0, 0, 1]])
        self._rebuild_hklcalc()

    def _ensure_ready_inverse(self) -> None:
        """Ensure the solver is ready for :meth:`inverse` (angles -> hkl).

        If no UB matrix has been set yet, a default identity UB is
        initialised automatically so that ``wh()`` works immediately after
        diffractometer creation without requiring the user to add
        reflections first.
        """
        if self._ubcalc.UB is None:
            self._init_default_ub()
        if self._hklcalc is None:
            self._rebuild_hklcalc()

    def _ensure_ready(self) -> None:
        """Raise if the solver is not ready for forward (hkl -> angles).

        Unlike :meth:`_ensure_ready_inverse`, this method requires an
        explicit UB matrix (i.e. the user must have added reflections and
        called ``calculate_UB()``), because computing motor positions from
        hkl without a proper crystal orientation is meaningless.
        """
        if self._ubcalc.UB is None:
            raise SolverError("UB matrix has not been set. Add reflections and call calculate_UB().")
        if self._wavelength is None:
            raise SolverError("Wavelength is not set. Add a reflection first.")
        if self._hklcalc is None:
            self._rebuild_hklcalc()

    # ------------------------------------------------------------------
    # SolverBase abstract methods
    # ------------------------------------------------------------------

    def addReflection(self, reflection: ReflectionDict) -> None:
        """Add coordinates of a diffraction condition (a reflection)."""
        if not isinstance(reflection, dict):
            raise TypeError(f"Must supply ReflectionDict (dict), received {reflection!r}")
        self._reflections.append(reflection)

        wl = reflection["wavelength"]
        energy_kev = ENERGY_REST_KEV / wl

        pseudos = reflection["pseudos"]
        hkl = (pseudos["h"], pseudos["k"], pseudos["l"])

        reals = reflection["reals"]
        pos = self._position_from_reals(reals)

        tag = reflection.get("name", f"r{len(self._reflections)}")
        self._ubcalc.add_reflection(hkl, pos, energy_kev, tag)

        # Track wavelength (all reflections should share the same wavelength
        # for forward/inverse, though diffcalc stores per-reflection).
        self._wavelength = wl

    def calculate_UB(self, r1: ReflectionDict, r2: ReflectionDict) -> Matrix3x3:
        """Calculate the UB matrix using two reflections (Busing & Levy)."""
        # Ensure lattice is set
        if self._ubcalc.crystal is None:
            raise SolverError("Lattice must be set before calculating UB.")

        self._ubcalc.calc_ub()
        self._rebuild_hklcalc()

        ub = self._ubcalc.UB
        return ub.tolist()

    @property
    def axes_w(self) -> list[str]:
        """Real axis names computed by :meth:`forward` in the current mode.

        These are the real axes *not* constrained to a fixed motor position
        by the current mode.  hklpy2's ``Core`` class derives ``axes_c``
        (constant axes) and ``axes_r`` (all real axes) from this list and
        :attr:`real_axis_names`.
        """
        if not self.mode:
            return list(REAL_AXES)
        constrained_motors = set(_MODES[self.mode].keys()) & set(REAL_AXES)
        return [ax for ax in REAL_AXES if ax not in constrained_motors]

    @property
    def extra_axis_names(self) -> list[str]:
        """Extra parameter names beyond the real motor axes.

        This geometry has no extra parameters; always returns ``[]``.
        """
        return []

    @property
    def extras(self) -> dict[str, Any]:
        """Extra parameters beyond the real motor axes.

        This geometry has no extra parameters; always returns ``{}``.
        """
        return {}

    def forward(self, pseudos: NamedFloatDict) -> list[NamedFloatDict]:
        """Compute motor positions from pseudo-axis values (hkl -> angles)."""
        if not isinstance(pseudos, dict):
            raise TypeError(f"Must supply dict, received {pseudos!r}")
        self._ensure_ready()
        self._apply_mode_constraints()

        h = float(pseudos["h"])
        k = float(pseudos["k"])
        l = float(pseudos["l"])  # noqa: E741

        try:
            results = self._hklcalc.get_position(h, k, l, self._wavelength)
        except DiffcalcException as exc:
            raise SolverError(str(exc)) from exc

        solutions: list[NamedFloatDict] = []
        for pos, _virtual_angles in results:
            solutions.append(self._reals_from_position(pos))
        return solutions

    @classmethod
    def geometries(cls) -> list[str]:
        """Ordered list of geometry names supported by this solver."""
        return [GEOMETRY_NAME]

    def inverse(self, reals: NamedFloatDict) -> NamedFloatDict:
        """Compute pseudo-axis values from motor positions (angles -> hkl).

        Works immediately after diffractometer creation even before any
        reflections have been added: a default identity UB is used in that
        case, and the all-zeros motor position maps to ``(h=0, k=0, l=0)``.
        """
        if not isinstance(reals, dict):
            raise TypeError(f"Must supply dict, received {reals!r}")
        self._ensure_ready_inverse()

        # hklpy2 calls update_solver(wavelength=...) before inverse(), so
        # self._wavelength should already be set.  Fall back to 1.0 Å only
        # if it is still None (e.g. in unit-test scenarios).
        wavelength = self._wavelength if self._wavelength is not None else 1.0

        pos = self._position_from_reals(reals)
        try:
            h, k, l = self._hklcalc.get_hkl(pos, wavelength)  # noqa: E741
        except DiffcalcException as exc:
            raise SolverError(str(exc)) from exc

        return {"h": h, "k": k, "l": l}

    @property
    def lattice(self) -> NamedFloatDict:
        """Crystal lattice parameters."""
        return self._lattice

    @lattice.setter
    def lattice(self, value: NamedFloatDict) -> None:
        if not isinstance(value, dict):
            raise TypeError(f"Must supply dict, received {value!r}")
        self._lattice = value

        # Push into diffcalc's UBCalculation
        a = float(value.get("a", 1.0))
        b = float(value.get("b", a))
        c = float(value.get("c", a))
        alpha = float(value.get("alpha", 90.0))
        beta = float(value.get("beta", 90.0))
        gamma = float(value.get("gamma", 90.0))

        self._ubcalc.set_lattice("sample", a, b, c, alpha, beta, gamma)

    @property
    def mode(self) -> str:
        """Current operating mode."""
        try:
            return self._mode
        except AttributeError:
            self._mode = ""
        return self._mode

    @mode.setter
    def mode(self, value: str) -> None:
        from hklpy2.misc import check_value_in_list

        check_value_in_list("Mode", value, self.modes, blank_ok=True)
        self._mode = value
        if value and value in _MODES:
            self._apply_mode_constraints()

    @property
    def modes(self) -> list[str]:
        """List of operating modes for this geometry."""
        return list(_MODES.keys())

    @property
    def pseudo_axis_names(self) -> list[str]:
        """Ordered list of pseudo axis names."""
        return list(PSEUDO_AXES)

    @property
    def real_axis_names(self) -> list[str]:
        """Ordered list of real axis names."""
        return list(REAL_AXES)

    def refineLattice(self, reflections: list[ReflectionDict]) -> NamedFloatDict | None:
        """Refine lattice parameters from stored reflections."""
        if len(self._reflections) < 3:
            return None

        indices = list(range(1, len(self._reflections) + 1))
        try:
            _new_u, new_lattice = self._ubcalc.fit_ub(indices, refine_lattice=True, refine_umatrix=True)
        except (DiffcalcException, Exception) as exc:
            logger.warning("Lattice refinement failed: %s", exc)
            return None

        # new_lattice is (name, a, b, c, alpha, beta, gamma)
        _name, a, b, c, alpha, beta, gamma = new_lattice
        refined = {"a": a, "b": b, "c": c, "alpha": alpha, "beta": beta, "gamma": gamma}
        self._lattice = refined
        self._rebuild_hklcalc()
        return refined

    def removeAllReflections(self) -> None:
        """Remove all reflections."""
        self._reflections.clear()
        self._ubcalc = UBCalculation("default")
        # Re-apply lattice if we had one
        if self._lattice:
            self.lattice = self._lattice
        self._wavelength = None
        self._rebuild_hklcalc()

    @property
    def UB(self) -> Matrix3x3:
        """Orientation matrix (3x3)."""
        if self._ubcalc.UB is not None:
            return self._ubcalc.UB.tolist()
        return [[1, 0, 0], [0, 1, 0], [0, 0, 1]]

    @property
    def wavelength(self) -> float | None:
        """Wavelength in Angstroms, for forward() and inverse()."""
        return self._wavelength

    @wavelength.setter
    def wavelength(self, value: float) -> None:
        if not isinstance(value, (int, float)):
            raise TypeError(f"Must supply number, received {value!r}")
        if value <= 0:
            raise ValueError(f"Must supply positive number, received {value!r}")
        self._wavelength = float(value)

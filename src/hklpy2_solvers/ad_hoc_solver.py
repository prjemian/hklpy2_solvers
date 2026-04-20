# Copyright (c) 2026 Pete Jemian <prjemian+hklpy2@gmail.com>
# SPDX-License-Identifier: LicenseRef-UChicago-Argonne-LLC-License
"""
Solver wrapping *ad_hoc_diffractometer* for hklpy2.

Provides the :class:`AdHocSolver` class, which implements the
:class:`hklpy2.backends.base.SolverBase` interface on top of the
`ad_hoc_diffractometer <https://github.com/prjemian/ad_hoc_diffractometer>`_
library.  All geometries registered with the library are available.

.. autosummary::

    ~AdHocSolver
"""

import logging
from typing import Any

import ad_hoc_diffractometer as ahd
import numpy as np
from ad_hoc_diffractometer.mode import ConstraintViolation, EwaldSphereViolation
from ad_hoc_diffractometer.refinement import refine_lattice_bl1967
from hklpy2.backends.base import SolverBase
from hklpy2.backends.typing import ReflectionDict
from hklpy2.exceptions import SolverError
from hklpy2.typing import KeyValueMap, Matrix3x3, NamedFloatDict

logger = logging.getLogger(__name__)

PSEUDO_AXES = ["h", "k", "l"]
"""Ordered pseudo axis names."""

DEFAULT_GEOMETRY = "fourcv"
"""Default geometry (Busing & Levy four-circle vertical)."""


class AdHocSolver(SolverBase):
    """
    Solver wrapping :mod:`ad_hoc_diffractometer` for hklpy2.

    Wraps :class:`ad_hoc_diffractometer.geometry.AdHocDiffractometer` behind
    the :class:`~hklpy2.backends.base.SolverBase` interface so that hklpy2
    can use it for forward / inverse calculations.

    All geometries registered with the ``ad_hoc_diffractometer`` library are
    supported.  Geometry discovery is dynamic: any geometry added to the
    library's registry (including via entry points) is automatically
    available.

    .. seealso:: :func:`ad_hoc_diffractometer.list_geometries`

    PARAMETERS

    geometry : str
        Name of the diffractometer geometry.  Must be one of the names
        returned by :meth:`geometries`.  Default: ``"fourcv"``.
    kwargs
        Passed to the geometry factory function.  For kappa geometries,
        use ``kappa_alpha_deg=...`` to set the kappa tilt angle.
    """

    name = "ad_hoc"
    version = "0.1.0"

    def __init__(self, geometry: str = DEFAULT_GEOMETRY, **kwargs: Any) -> None:
        available = ahd.list_geometries()
        if geometry not in available:
            raise SolverError(
                f"AdHocSolver does not support geometry {geometry!r}.  Available: {sorted(available.keys())}"
            )

        # Extract factory kwargs that are not for SolverBase.
        factory_kwargs: dict[str, Any] = {}
        for key in ("kappa_alpha_deg",):
            if key in kwargs:
                factory_kwargs[key] = kwargs.pop(key)

        # Create the internal geometry object.
        self._geom = ahd.make_geometry(geometry, **factory_kwargs)

        # Cache axis names from geometry stages (stable after creation).
        self._real_axes = [s.name for s in self._geom.sample_stages + self._geom.detector_stages]

        # Internal bookkeeping.
        self._reflections: list[ReflectionDict] = []
        self._wavelength: float | None = None
        self._lattice: NamedFloatDict = {}

        super().__init__(geometry, **kwargs)

        # Set default mode: library's default or first available.
        if not self.mode and self.modes:
            default = self._geom.mode_name  # library's own default
            if default is None:
                default = self.modes[0]
            self.mode = default

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _ensure_ready(self) -> None:
        """Raise if the solver is not ready for forward (hkl -> angles)."""
        if self._geom.sample.UB is None:
            raise SolverError("UB matrix has not been set.  Add reflections and call calculate_UB().")
        if self._wavelength is None:
            raise SolverError("Wavelength is not set.  Add a reflection first.")

    def _ensure_ready_inverse(self) -> None:
        """Ensure the solver is ready for inverse (angles -> hkl).

        If no UB has been set, initialise a default identity UB with a
        unit cubic lattice so that ``wh()`` works immediately.
        """
        if self._geom.sample.UB is None:
            self._init_default_ub()

    def _init_default_ub(self) -> None:
        """Initialise a default identity UB with a unit cubic lattice."""
        self._geom.sample.lattice = ahd.Lattice(a=1.0)
        if self._geom.wavelength is None:
            self._geom.wavelength = 1.0
        ahd.ub_identity(self._geom.sample)

    # ------------------------------------------------------------------
    # SolverBase abstract methods
    # ------------------------------------------------------------------

    def addReflection(self, reflection: ReflectionDict) -> None:
        """Add coordinates of a diffraction condition (a reflection)."""
        if not isinstance(reflection, dict):
            raise TypeError(f"Must supply ReflectionDict (dict), received {reflection!r}")
        self._reflections.append(reflection)

        pseudos = reflection["pseudos"]
        hkl = (pseudos["h"], pseudos["k"], pseudos["l"])
        reals = reflection["reals"]
        wl = reflection["wavelength"]
        tag = reflection.get("name", f"r{len(self._reflections)}")

        self._geom.add_reflection(tag, hkl=hkl, angles=reals, wavelength=wl)

        # Designate first two reflections as orienting reflections.
        refls = self._geom.sample.reflections
        if len(self._reflections) == 1:
            refls.setor0(tag)
        elif len(self._reflections) == 2:
            refls.setor1(tag)

        # Track wavelength and push to geometry.
        self._wavelength = wl
        self._geom.wavelength = wl

    def calculate_UB(self, r1: ReflectionDict, r2: ReflectionDict) -> Matrix3x3:
        """Calculate the UB matrix using two reflections (Busing & Levy)."""
        if not self._lattice:
            raise SolverError("Lattice must be set before calculating UB.")

        ahd.ub_from_two_reflections_bl1967(self._geom.sample)
        return self._geom.sample.UB.tolist()

    @property
    def axes_w(self) -> list[str]:
        """Real axis names computed by :meth:`forward` in the current mode.

        These are the real axes *not* constrained to a fixed motor position
        by the current mode.
        """
        if not self.mode:
            return list(self._real_axes)
        mode_obj = self._geom.mode
        if mode_obj is None:
            return list(self._real_axes)
        constrained = set(mode_obj.constant_stages)
        return [ax for ax in self._real_axes if ax not in constrained]

    @property
    def extra_axis_names(self) -> list[str]:
        """Extra parameter names beyond the real motor axes.

        Always returns ``[]``.
        """
        return []

    @property
    def extras(self) -> dict[str, Any]:
        """Extra parameters beyond the real motor axes.

        Always returns ``{}``.
        """
        return {}

    @property
    def _summary_dict(self) -> KeyValueMap:
        """Return a summary of the geometry (modes, axes).

        Overrides :attr:`SolverBase._summary_dict` so that each mode
        reports only the axes actually computed by :meth:`forward`.
        """
        description: dict[str, Any] = {
            "name": self.geometry,
            "pseudos": self.pseudo_axis_names,
            "reals": self.real_axis_names,
            "modes": {},
        }
        original_mode = self.mode
        for mode in self.modes:
            self.mode = mode
            description["modes"][mode] = {
                "extras": [],
                "reals": self.axes_w,
            }
        self.mode = original_mode
        return description

    def forward(self, pseudos: NamedFloatDict) -> list[NamedFloatDict]:
        """Compute motor positions from pseudo-axis values (hkl -> angles)."""
        if not isinstance(pseudos, dict):
            raise TypeError(f"Must supply dict, received {pseudos!r}")
        self._ensure_ready()

        h = float(pseudos["h"])
        k = float(pseudos["k"])
        l = float(pseudos["l"])  # noqa: E741

        try:
            results = self._geom.forward(h, k, l)
        except (EwaldSphereViolation, ConstraintViolation, ValueError, NotImplementedError) as exc:
            raise SolverError(str(exc)) from exc

        return results

    @classmethod
    def geometries(cls) -> list[str]:
        """Ordered list of geometry names supported by this solver."""
        return sorted(ahd.list_geometries().keys())

    def inverse(self, reals: NamedFloatDict) -> NamedFloatDict:
        """Compute pseudo-axis values from motor positions (angles -> hkl).

        Works immediately after creation even before reflections are
        added: a default identity UB is used in that case.
        """
        if not isinstance(reals, dict):
            raise TypeError(f"Must supply dict, received {reals!r}")
        self._ensure_ready_inverse()

        if self._wavelength is None:
            self._geom.wavelength = 1.0
        elif self._geom.wavelength != self._wavelength:
            self._geom.wavelength = self._wavelength

        try:
            h, k, l = self._geom.inverse(reals)  # noqa: E741
        except (ValueError, np.linalg.LinAlgError) as exc:
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

        a = float(value.get("a", 1.0))
        b = float(value.get("b", a))
        c = float(value.get("c", a))
        alpha = float(value.get("alpha", 90.0))
        beta = float(value.get("beta", 90.0))
        gamma = float(value.get("gamma", 90.0))

        self._geom.sample.lattice = ahd.Lattice(a=a, b=b, c=c, alpha=alpha, beta=beta, gamma=gamma)

    @SolverBase.sample.setter
    def sample(self, value: dict) -> None:
        """Set the crystalline sample, pushing lattice and reflections.

        Overrides :class:`~hklpy2.backends.base.SolverBase` to mirror the
        pattern used by ``DiffcalcSolver``: after storing the dict, the
        lattice is pushed and all reflections are re-added.
        """
        if not isinstance(value, dict):
            raise TypeError(f"Must supply dictionary, received {value!r}")
        self._sample = value

        # Push lattice immediately.
        if "lattice" in value:
            self.lattice = value["lattice"]

        # Re-populate reflections in the declared order.
        raw = value.get("reflections", [])
        if isinstance(raw, dict):
            refl_by_name: dict = raw
        else:
            refl_by_name = {r["name"]: r for r in raw}

        self._reflections.clear()
        self._geom.sample.reflections.clear()

        for name in value.get("order", []):
            if name in refl_by_name:
                self.addReflection(refl_by_name[name])

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
        from hklpy2.utils import check_value_in_list

        check_value_in_list("Mode", value, self.modes, blank_ok=True)
        self._mode = value
        if value:
            self._geom.mode_name = value

    @property
    def modes(self) -> list[str]:
        """List of operating modes for this geometry."""
        return list(self._geom.modes.keys())

    @property
    def pseudo_axis_names(self) -> list[str]:
        """Ordered list of pseudo axis names."""
        return list(PSEUDO_AXES)

    @property
    def real_axis_names(self) -> list[str]:
        """Ordered list of real axis names."""
        return list(self._real_axes)

    def set_reals(self, reals: NamedFloatDict) -> None:
        """Set current real-axis values in the geometry object.

        Called by ``hklpy2.Core.forward()`` before :meth:`forward` to push
        current motor positions into the solver.
        """
        if not isinstance(reals, dict):
            raise TypeError(f"Must supply dict, received {reals!r}")
        if not all(isinstance(v, (int, float)) for v in reals.values()):
            raise TypeError(f"All values must be numbers.  Received: {reals!r}")
        for axis_name, angle in reals.items():
            self._geom.set_angle(axis_name, float(angle))

    def refineLattice(self, reflections: list[ReflectionDict]) -> NamedFloatDict | None:
        """Refine lattice parameters from stored reflections."""
        if len(self._reflections) < 3:
            return None

        # Collect reflection names for the library call.
        refl_names = list(self._geom.sample.reflections.keys())

        try:
            result = refine_lattice_bl1967(self._geom.sample, refl_names)
        except (ValueError, Exception) as exc:
            logger.warning("Lattice refinement failed: %s", exc)
            return None

        lat = result["lattice"]
        refined = {
            "a": lat.a,
            "b": lat.b,
            "c": lat.c,
            "alpha": lat.alpha,
            "beta": lat.beta,
            "gamma": lat.gamma,
        }
        self._lattice = refined
        return refined

    def removeAllReflections(self) -> None:
        """Remove all reflections."""
        self._reflections.clear()
        self._geom.sample.reflections.clear()
        self._wavelength = None
        # Clear UB so it reverts to identity via the getter fallback.
        self._geom.sample.U = None
        self._geom.sample.UB = None
        # Re-apply lattice if we had one.
        if self._lattice:
            self.lattice = self._lattice

    @property
    def UB(self) -> Matrix3x3:
        """Orientation matrix (3x3)."""
        if self._geom.sample.UB is not None:
            return self._geom.sample.UB.tolist()
        return [[1, 0, 0], [0, 1, 0], [0, 0, 1]]

    @UB.setter
    def UB(self, value: Matrix3x3) -> None:
        """Restore the orientation matrix."""
        if self._geom.sample.lattice is None:
            if self._lattice:
                self.lattice = self._lattice
            else:
                self._geom.sample.lattice = ahd.Lattice(a=1.0)
        self._geom.sample.UB = np.asarray(value, dtype=float)

    @property
    def wavelength(self) -> float | None:
        """Wavelength in Angstroms."""
        return self._wavelength

    @wavelength.setter
    def wavelength(self, value: float) -> None:
        if not isinstance(value, (int, float)):
            raise TypeError(f"Must supply number, received {value!r}")
        if value <= 0:
            raise ValueError(f"Must supply positive number, received {value!r}")
        self._wavelength = float(value)
        self._geom.wavelength = float(value)

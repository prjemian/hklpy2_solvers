# Copyright (c) 2025-2026 UChicago Argonne, LLC
# SPDX-License-Identifier: LicenseRef-UChicago-Argonne-LLC-License
"""
Solver wrapping *ad_hoc_diffractometer* for hklpy2.

Provides the :class:`AdHocSolver` class, which implements the
:class:`hklpy2.backends.base.SolverBase` interface on top of the
`ad_hoc_diffractometer <https://github.com/bcda-aps/ad_hoc_diffractometer>`_
library.  All geometries registered with the library are available.

.. autosummary::

    ~AdHocSolver
"""

import logging
from importlib.metadata import PackageNotFoundError
from importlib.metadata import version as _pkg_version
from typing import Any

import ad_hoc_diffractometer as ahd
import numpy as np
from ad_hoc_diffractometer.mode import (
    OPTIONAL,
    REQUIRED,
    ConstraintViolation,
    EwaldSphereViolation,
)
from ad_hoc_diffractometer.reference import exit_angle as _ref_exit_angle
from ad_hoc_diffractometer.reference import incidence_angle as _ref_incidence_angle
from ad_hoc_diffractometer.reference import natural_psi as _ref_natural_psi
from ad_hoc_diffractometer.reference import naz_angle as _ref_naz_angle
from ad_hoc_diffractometer.reference import omega_pseudo as _ref_omega_pseudo
from ad_hoc_diffractometer.reference import psi_angle as _ref_psi_angle
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

try:
    _BACKEND_VERSION = _pkg_version("ad_hoc_diffractometer")
except PackageNotFoundError:  # pragma: no cover - defensive
    _BACKEND_VERSION = "unknown"

_INPUT_EXTRA_NAMES: frozenset[str] = frozenset({"n_hat", "psi", "alpha_i", "beta_out", "h2", "k2", "l2"})
"""Names of mode-extra parameters supplied by the user (vs. solver outputs)."""

# ---------------------------------------------------------------------------
# Solver-state persistence (:issue:`108`)
# ---------------------------------------------------------------------------

_AD_HOC_BUILTIN_GEOMETRIES: frozenset[str] = frozenset(
    {
        "fivec",
        "fourch",
        "fourcv",
        "kappa4ch",
        "kappa4cv",
        "kappa6c",
        "psic",
        "s2d2",
        "sixc",
        "zaxis",
    }
)
"""Geometry names shipped by the installed ``ad_hoc_diffractometer``.

Used to decide whether a geometry needs to be persisted in the
solver's ``_metadata``: any name not in this set is treated as
user-registered and is always persisted; names in this set are
persisted only when the live geometry has been modified (modes
added or removed) relative to a fresh reference instance.

Guarded by :func:`tests.test_ad_hoc_solver.test_builtin_geometry_set`
so an upstream addition fails CI rather than silently turning a
shipped geometry into a "user-registered" one.
"""

_GEOMETRY_STATE_OMIT_KEYS: frozenset[str] = frozenset({"active_sample", "samples", "wavelength"})
"""Top-level keys in ``AdHocDiffractometer.to_dict()`` that hklpy2
manages independently and must not round-trip through the solver
state (avoids double-restore of samples and wavelength)."""

_REFERENCE_EXTRA_NAMES: frozenset[str] = frozenset({"psi", "alpha_i", "beta_out"})
"""Reference-constraint scalar extras (set via ``ConstraintSet.with_constraint_values``)."""

_DOUBLE_DIFF_EXTRA_NAMES: tuple[str, ...] = ("h2", "k2", "l2")
"""Double-diffraction Miller indices stored directly in mode.extras."""


class AdHocSolver(SolverBase):
    """
    Solver wrapping :mod:`ad_hoc_diffractometer` for hklpy2.

    Wraps :class:`ad_hoc_diffractometer.diffractometer.AdHocDiffractometer` behind
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
    version = _BACKEND_VERSION

    def __init__(self, geometry: str = DEFAULT_GEOMETRY, **kwargs: Any) -> None:
        # Pop persistence kwargs delivered via ``solver_kwargs`` from
        # a saved configuration (see :issue:`108`).  When present,
        # ``geometry_state`` rebuilds the internal geometry from a
        # serialised snapshot rather than calling ``make_geometry``.
        geometry_state = kwargs.pop("geometry_state", None)

        # Extract factory kwargs that are not for SolverBase.  ``ad_hoc``
        # kappa factories take ``alpha_deg``; we accept the more explicit
        # ``kappa_alpha_deg`` name (documented in the class docstring) and
        # translate it on the way through.
        factory_kwargs: dict[str, Any] = {}
        if "kappa_alpha_deg" in kwargs:
            factory_kwargs["alpha_deg"] = kwargs.pop("kappa_alpha_deg")

        if geometry_state is not None:
            # Replay path (:issue:`108`): rebuild the geometry from
            # the persisted snapshot.  Validates the geometry name
            # matches what the snapshot describes so a corrupted
            # config does not silently produce a wrong-geometry
            # solver.
            self._geom = self._geometry_from_state(geometry, geometry_state)
        else:
            available = ahd.list_geometries()
            if geometry not in available:
                raise SolverError(
                    f"AdHocSolver does not support geometry {geometry!r}.  Available: {sorted(available.keys())}"
                )
            # Create the internal geometry object from the registry.
            self._geom = ahd.make_geometry(geometry, **factory_kwargs)

        # Cache axis names from geometry stages (stable after creation).
        self._real_axes = [s.name for s in self._geom.sample_stages + self._geom.detector_stages]

        # Internal bookkeeping.
        self._reflections: list[ReflectionDict] = []
        self._wavelength: float | None = None
        self._lattice: NamedFloatDict = {}

        super().__init__(geometry, **kwargs)

        # Set default mode: library's default or first available.
        # Every registered ahd geometry has at least one mode, so the
        # ``self.modes`` guard never falls through; it remains as a
        # defensive belt-and-braces check.
        if not self.mode and self.modes:  # pragma: no branch
            default = self._geom.mode_name  # library's own default
            if default is None:  # pragma: no cover - geometry always sets one
                default = self.modes[0]
            self.mode = default

    @staticmethod
    def _geometry_from_state(geometry: str, state: Any) -> Any:
        """Reconstruct an ``AdHocDiffractometer`` from a persisted snapshot.

        Wraps :meth:`ad_hoc_diffractometer.AdHocDiffractometer.from_dict`
        with hklpy2-side validation: the snapshot must be a dict and
        its ``name`` field (when present) must match ``geometry``,
        catching configs in which the ``geometry:`` field and the
        persisted state have drifted.
        """
        if not isinstance(state, dict):
            raise SolverError(f"geometry_state must be a dict, received {state!r}.")
        snapshot_name = state.get("name")
        if snapshot_name is not None and snapshot_name != geometry:
            raise SolverError(
                f"geometry_state name {snapshot_name!r} does not match the requested geometry {geometry!r}."
            )
        # The omitted keys (samples, active_sample, wavelength) are
        # restored by hklpy2's own mechanisms after construction.
        # ``from_dict`` tolerates their absence — verified in tests.
        try:
            return ahd.AdHocDiffractometer.from_dict(state)
        except Exception as exc:  # pragma: no cover - defensive
            raise SolverError(f"AdHocDiffractometer.from_dict failed for geometry {geometry!r}: {exc}") from exc

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

    def _normalize_angles(self, angles: dict[str, float] | None) -> dict[str, float] | None:
        """Validate the optional motor-angles dict used by reference helpers.

        Returns ``None`` unchanged (upstream interprets this as
        "use the geometry's current angles").  A dict is shallow-copied
        with values coerced to ``float``.  Unknown axis names raise
        :class:`SolverError`; a non-dict input raises ``TypeError``.
        """
        if angles is None:
            return None
        if not isinstance(angles, dict):
            raise TypeError(f"angles must be a dict[str, float] or None, received {angles!r}")
        unknown = set(angles) - set(self._real_axes)
        if unknown:
            raise SolverError(f"Unknown axis name(s) {sorted(unknown)}; expected subset of {self._real_axes}")
        return {k: float(v) for k, v in angles.items()}

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
        """Calculate the UB matrix using two reflections (Busing & Levy).

        The ``r1`` and ``r2`` arguments are the contractual source of
        truth: any prior reflections held by the underlying
        ``ad_hoc_diffractometer`` sample are cleared and the two named
        reflections are inserted (so ``setor0`` / ``setor1`` are
        correctly designated) before UB is computed.  See :issue:`56`.
        """
        if not self._lattice:
            raise SolverError("Lattice must be set before calculating UB.")

        # Honour the caller-supplied reflections, regardless of any
        # stale solver-side state.
        self.removeAllReflections()
        self.addReflection(r1)
        self.addReflection(r2)

        try:
            ahd.ub_from_two_reflections_bl1967(self._geom.sample)
        except ValueError as exc:
            raise SolverError(str(exc)) from exc
        return self._geom.sample.UB.tolist()

    @property
    def axes_w(self) -> list[str]:
        """Real axis names computed by :meth:`forward` in the current mode.

        These are the real axes *not* constrained to a fixed motor position
        by the current mode.
        """
        if not self.mode:  # pragma: no cover - constructor always sets a mode
            return list(self._real_axes)
        mode_obj = self._geom.mode
        if mode_obj is None:  # pragma: no cover - mode setter guarantees object
            return list(self._real_axes)
        constrained = set(mode_obj.constant_stages)
        return [ax for ax in self._real_axes if ax not in constrained]

    @property
    def extra_axis_names(self) -> list[str]:
        """Ordered list of input extra parameter names for the current mode.

        Drawn from the underlying mode's ``extras`` dict (filtered to the
        names the user is expected to supply: ``n_hat``, ``psi``,
        ``alpha_i``, ``beta_out``, ``h2``, ``k2``, ``l2``) plus the
        scalar name of the active :class:`ReferenceConstraint` if it
        names one of those inputs and is not already listed.

        Solver-output placeholders (e.g. ``psi`` populated by the solver
        after :meth:`forward`) are also exposed as inputs so the user can
        change the target value before the next forward call.

        Returns ``[]`` for modes with no extras.
        """
        mode_obj = self._geom.mode
        if mode_obj is None:  # pragma: no cover - mode setter guarantees object
            return []
        names: list[str] = []
        for key in mode_obj.extras:
            # ``mode.extras`` is a plain dict so its keys are unique; the
            # ``not in names`` guard is defensive against future changes.
            if key in _INPUT_EXTRA_NAMES and key not in names:  # pragma: no branch
                names.append(key)
        rc = getattr(mode_obj, "reference_constraint", None)
        # Every reference-constraint scalar is also declared in
        # ``mode.extras`` by the library, so the ``rc.name not in names``
        # branch is currently unreachable; kept defensive.
        if (
            rc is not None and rc.name in _INPUT_EXTRA_NAMES and rc.name not in names
        ):  # pragma: no cover - defensive
            names.append(rc.name)
        return names

    @property
    def extras(self) -> dict[str, Any]:
        """Current values of the mode's extra parameters.

        To discover which geometry attribute the active mode requires,
        use ``solver._geom.required_reference_vector`` directly.
        """
        out: dict[str, Any] = {}
        mode_obj = self._geom.mode
        if mode_obj is None:  # pragma: no cover - mode setter guarantees object
            return out
        for name in self.extra_axis_names:
            if name == "n_hat":
                out[name] = self._geom.surface_normal
            elif name in _REFERENCE_EXTRA_NAMES:
                rc = getattr(mode_obj, "reference_constraint", None)
                if rc is not None and rc.name == name:
                    out[name] = rc.value
                else:
                    raw = mode_obj.extras.get(name)
                    out[name] = None if raw in (REQUIRED, OPTIONAL) else raw
            else:  # h2, k2, l2 (double-diffraction)
                raw = mode_obj.extras.get(name)
                out[name] = None if raw in (REQUIRED, OPTIONAL) else raw
        return out

    @extras.setter
    def extras(self, values: dict[str, Any]) -> None:
        """Push extra parameter values into the current mode.

        Routing:

        * ``n_hat``  -> ``geometry.surface_normal`` (length-3 sequence or
          ``None``).
        * ``psi``, ``alpha_i``, ``beta_out`` -> rebuild the active
          :class:`ConstraintSet` via
          :meth:`~ad_hoc_diffractometer.mode.ConstraintSet.with_constraint_values`
          so the :class:`ReferenceConstraint` carries the new scalar
          value.
        * ``h2``, ``k2``, ``l2`` -> written directly into the mode's
          ``extras`` dict (used by double-diffraction modes).

        Unknown keys are ignored silently (consistent with hklpy2 Core
        behaviour, which always passes the full extras dict).
        """
        if not isinstance(values, dict):
            raise TypeError(f"Must supply dict, received {values!r}")
        if not values:
            return
        mode_obj = self._geom.mode
        if mode_obj is None:  # pragma: no cover - mode setter guarantees object
            return

        # Surface-normal vector.  ``hklpy2.Core`` defaults vector extras
        # to the scalar ``0`` during ``update_solver()`` (see
        # :issue:`81`); treat any non-iterable value as "unset" so the
        # adapter can be constructed via ``hklpy2.creator`` for modes
        # that expose ``n_hat`` (e.g. ``zaxis``).
        if "n_hat" in values:
            v = values["n_hat"]
            if v is None:
                self._geom.surface_normal = None
            else:
                try:
                    self._geom.surface_normal = tuple(float(x) for x in v)
                except TypeError:
                    self._geom.surface_normal = None

        # Reference-constraint scalar (psi / alpha_i / beta_out).
        # ``ConstraintSet.with_constraint_values`` (upstream
        # ad_hoc_diffractometer >= 0.11.1, :issue:`114`) returns a fresh
        # ConstraintSet with the named scalar replaced, preserving order,
        # extras, and cut_points.  Replace the per-mode ConstraintSet and
        # re-select so that ``self._geom.mode`` returns the new object.
        rc = getattr(mode_obj, "reference_constraint", None)
        if rc is not None and rc.name in _REFERENCE_EXTRA_NAMES and rc.name in values:
            new_cs = mode_obj.with_constraint_values(**{rc.name: float(values[rc.name])})
            self._geom._modes[self._mode] = new_cs
            self._geom.mode_name = self._mode

        # Double-diffraction Miller indices (mutated in place).
        for k in _DOUBLE_DIFF_EXTRA_NAMES:
            if k in values:
                # Refresh mode_obj because rebuild above may have replaced it.
                self._geom.mode.extras[k] = float(values[k])

    def update_mode_constraints(self, mode_name: str | None = None, **updates: float | bool) -> None:
        """Override default values of one or more constraints on a mode.

        Each ``fixed_<axis>`` mode (e.g. ``fourcv`` ``fixed_chi``, ``psic``
        ``fixed_alpha_i_vertical``) carries a default scalar value baked
        into the geometry's YAML definition.  Constraint values are
        immutable; this method replaces the named mode's
        :class:`~ad_hoc_diffractometer.mode.ConstraintSet` with a fresh
        instance produced by
        :meth:`~ad_hoc_diffractometer.mode.ConstraintSet.with_constraint_values`,
        leaving constraint order, :attr:`computed`, :attr:`extras`, and
        :attr:`cut_points` unchanged.

        Parameters
        ----------
        mode_name : str, optional
            Name of the mode to update.  ``None`` (default) operates on
            the active mode (:attr:`mode`).
        **updates : float or bool
            Mapping of constraint name → new value, where each key matches
            the ``.name`` attribute of an existing
            :class:`~ad_hoc_diffractometer.mode.SampleConstraint`,
            :class:`~ad_hoc_diffractometer.mode.DetectorConstraint`, or
            :class:`~ad_hoc_diffractometer.mode.ReferenceConstraint` in
            the mode.  Reference-constraint scalars (``psi``, ``alpha_i``,
            ``beta_out``) can also be updated through the per-call
            :attr:`extras` setter; this method is the route for persistent
            overrides of fixed-axis defaults.

        Raises
        ------
        SolverError
            If ``mode_name`` is unknown, if any kwarg names a constraint
            not present in the mode, or if a value cannot be converted to
            the expected numeric type.

        Examples
        --------
        Override a single sample-stage default::

            solver.update_mode_constraints("fixed_chi", chi=45.0)

        Override several stages at once on a multi-fix mode::

            solver.update_mode_constraints(
                "fixed_alpha_i_fixed_chi_fixed_phi",
                chi=15.0, phi=30.0, alpha_i=5.0,
            )

        Operate on the currently active mode::

            solver.mode = "fixed_chi"
            solver.update_mode_constraints(chi=45.0)
        """
        target_mode = self._mode if mode_name is None else mode_name
        try:
            cs = self._geom.modes[target_mode]
        except KeyError as exc:
            available = sorted(self._geom.modes.keys())
            raise SolverError(f"Unknown mode {target_mode!r}; available modes: {available}") from exc
        try:
            new_cs = cs.with_constraint_values(**updates)
        except KeyError as exc:
            # ``with_constraint_values`` raises KeyError for unknown
            # constraint names; surface as SolverError with the upstream
            # message preserved.
            raise SolverError(f"update_mode_constraints({target_mode!r}, **{updates!r}): {exc.args[0]}") from exc
        except (TypeError, ValueError) as exc:
            # ``with_constraint_values`` calls ``float(value)`` on each
            # update; bad types raise TypeError, bad strings raise
            # ValueError.  Both indicate caller error.
            raise SolverError(f"update_mode_constraints({target_mode!r}, **{updates!r}): {exc}") from exc
        self._geom._modes[target_mode] = new_cs
        # Re-select the mode if it is the active one so that
        # ``self._geom.mode`` returns the new ConstraintSet object.
        if target_mode == self._mode:
            self._geom.mode_name = self._mode

    @property
    def _summary_dict(self) -> KeyValueMap:
        """Return a summary of the geometry (modes, axes).

        Overrides :attr:`SolverBase._summary_dict` so that each mode
        reports both the writable axes computed by :meth:`forward`
        (:attr:`axes_w`) and the per-mode :attr:`extra_axis_names`.
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
                "extras": self.extra_axis_names,
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
        elif self._geom.wavelength != self._wavelength:  # pragma: no cover - kept in sync by setters
            self._geom.wavelength = self._wavelength

        try:
            h, k, l = self._geom.inverse(reals)  # noqa: E741
        except (ValueError, np.linalg.LinAlgError) as exc:  # pragma: no cover - ahd inverse is closed-form
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

        Overrides :class:`~hklpy2.backends.base.SolverBase` so that, after
        storing the dict, the lattice is pushed into
        ``ad_hoc_diffractometer`` immediately and the reflections are
        re-added in declared order.
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
    def _metadata(self) -> dict[str, Any]:
        """Solver metadata extended with the active mode and geometry state.

        Adds the following keys to the base :class:`SolverBase`
        metadata:

        * ``mode`` — the currently active operating mode name.  Read
          back by :meth:`hklpy2.diffract.DiffractometerBase.restore`
          (via ``restore_mode=True``).  Mirrors the precedent set by
          :class:`hklpy2.backends.hkl_soleil.HklSolver._metadata`.
        * ``geometry_state`` — only when the live geometry has
          deviated from a fresh reference of the same name (either
          a user-registered geometry, or a built-in geometry whose
          mode list has been modified).  The snapshot is produced
          by :meth:`ad_hoc_diffractometer.AdHocDiffractometer.to_dict`
          with hklpy2-managed fields (``samples``, ``active_sample``,
          ``wavelength``) stripped to avoid double-restore.

        ``hklpy2.simulator_from_config()`` forwards every
        non-reserved key under ``solver:`` as a ``solver_kwargs``
        entry, where :meth:`__init__` consumes ``geometry_state``
        and replays it via
        :meth:`ad_hoc_diffractometer.AdHocDiffractometer.from_dict`.
        See :issue:`108`.

        .. note::

           ``hklpy2.Core`` caches the active mode and pushes it to
           the underlying solver only when the next ``forward()``
           / ``inverse()`` runs (or when
           :meth:`hklpy2.ops.Core.update_solver` is called
           explicitly).  If a caller sets ``diffractometer.core.mode``
           then immediately reads ``_metadata`` / calls
           ``export()`` without an intervening calculation, the
           saved ``mode`` may reflect the previous value.  This
           caching behaviour is upstream and affects every solver
           (including :class:`~hklpy2.backends.hkl_soleil.HklSolver`).
        """
        meta = dict(super()._metadata)
        meta["mode"] = self.mode
        state = self._serialize_geometry_state()
        if state is not None:
            meta["geometry_state"] = state
        return meta

    def _serialize_geometry_state(self) -> dict[str, Any] | None:
        """Return a serialised geometry snapshot iff non-default.

        Returns ``None`` for a vanilla built-in geometry (name in
        :data:`_AD_HOC_BUILTIN_GEOMETRIES`, modes structurally
        identical to a fresh reference).  Otherwise returns a YAML-
        safe dict suitable for embedding in ``_metadata``.

        The payload is the ``to_dict`` / ``from_dict`` dict shape; the
        on-disk format is the public contract under :issue:`108`.
        """
        live = self._geom.to_dict()
        if self.geometry in _AD_HOC_BUILTIN_GEOMETRIES:
            try:
                reference = ahd.make_geometry(self.geometry).to_dict()
            except Exception:  # pragma: no cover - defensive
                # Failure to build a reference forces persistence
                # so the user does not lose state silently.
                reference = None
            if reference is not None and live.get("modes") == reference.get("modes"):
                # Vanilla built-in geometry with unmodified modes:
                # nothing solver-specific to persist.
                return None
        # Strip fields hklpy2 manages independently to avoid
        # double-restore (samples, wavelength, active_sample).
        return {k: v for k, v in live.items() if k not in _GEOMETRY_STATE_OMIT_KEYS}

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

    # ------------------------------------------------------------------
    # Reference helpers (backend-specific derived quantities).
    #
    # Thin wrappers around ``ad_hoc_diffractometer.reference`` so users
    # do not need to reach into ``solver._geom``.  See the
    # "Derived quantities" section of the AdHoc user guide.
    # ------------------------------------------------------------------

    def exit_angle(self, angles: dict[str, float] | None = None) -> float:
        """Exit angle β_out (deg).

        Requires :attr:`~ad_hoc_diffractometer.diffractometer.AdHocDiffractometer.surface_normal`
        to be set on the underlying geometry.

        PARAMETERS

        angles : dict[str, float] or None
            Motor angles in degrees keyed by real-axis name.  ``None``
            (default) means use the geometry's current angles.
        """
        return float(_ref_exit_angle(self._geom, angles=self._normalize_angles(angles)))

    def incidence_angle(self, angles: dict[str, float] | None = None) -> float:
        """Incidence angle α_i (deg).

        Requires :attr:`~ad_hoc_diffractometer.diffractometer.AdHocDiffractometer.surface_normal`
        to be set on the underlying geometry.

        PARAMETERS

        angles : dict[str, float] or None
            Motor angles in degrees keyed by real-axis name.  ``None``
            (default) means use the geometry's current angles.
        """
        return float(_ref_incidence_angle(self._geom, angles=self._normalize_angles(angles)))

    def natural_psi(self, h: float, k: float, l: float) -> float | None:  # noqa: E741
        """Natural azimuthal angle ψ (deg) for reflection ``(h, k, l)`` from UB.

        Uses ``UB @ (h, k, l)`` and ``UB @ azimuthal_reference``; **no
        motor angles enter the calculation**.  Returns ``None`` when the
        reflection is parallel to the azimuthal reference (ψ undefined).

        Requires :attr:`~ad_hoc_diffractometer.diffractometer.AdHocDiffractometer.azimuthal_reference`
        to be set on the underlying geometry.
        """
        result = _ref_natural_psi(self._geom, float(h), float(k), float(l))
        return None if result is None else float(result)

    def naz_angle(self, angles: dict[str, float] | None = None) -> float:
        """Lab-frame azimuthal angle of n̂, ``naz`` (deg).

        Requires :attr:`~ad_hoc_diffractometer.diffractometer.AdHocDiffractometer.surface_normal`
        to be set on the underlying geometry.

        PARAMETERS

        angles : dict[str, float] or None
            Motor angles in degrees keyed by real-axis name.  ``None``
            (default) means use the geometry's current angles.
        """
        return float(_ref_naz_angle(self._geom, angles=self._normalize_angles(angles)))

    def omega_pseudo(self, angles: dict[str, float] | None = None) -> float:
        """SPEC ``OMEGA`` pseudo-angle (deg), in ``[-90°, +90°]``.

        PARAMETERS

        angles : dict[str, float] or None
            Motor angles in degrees keyed by real-axis name.  ``None``
            (default) means use the geometry's current angles.
        """
        return float(_ref_omega_pseudo(self._geom, angles=self._normalize_angles(angles)))

    def psi_angle(self, angles: dict[str, float] | None = None) -> float:
        """Azimuthal angle ψ (deg) from motor positions.

        Requires :attr:`~ad_hoc_diffractometer.diffractometer.AdHocDiffractometer.azimuthal_reference`
        to be set on the underlying geometry.

        PARAMETERS

        angles : dict[str, float] or None
            Motor angles in degrees keyed by real-axis name.  ``None``
            (default) means use the geometry's current angles.
        """
        return float(_ref_psi_angle(self._geom, angles=self._normalize_angles(angles)))

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

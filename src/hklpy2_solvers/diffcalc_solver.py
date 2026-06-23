# Copyright (c) 2025-2026 UChicago Argonne, LLC
# SPDX-License-Identifier: LicenseRef-UChicago-Argonne-LLC-License
"""
Solver wrapping *diffcalc-core* for hklpy2.

Provides the :class:`DiffcalcSolver` class, which implements the
:class:`hklpy2.backends.base.SolverBase` interface on top of the `diffcalc-core
<https://github.com/DiamondLightSource/diffcalc-core>`_ library.  This library
provides one geometry (You 1999, 4S+2D six-circle ``psic`` geometry).

.. autosummary::

    ~DiffcalcSolver
"""

import logging
from importlib.metadata import PackageNotFoundError
from importlib.metadata import version as _pkg_version
from typing import Any

from hklpy2.backends.base import SolverBase
from hklpy2.backends.typing import ReflectionDict
from hklpy2.exceptions import SolverError
from hklpy2.typing import KeyValueMap
from hklpy2.typing import Matrix3x3
from hklpy2.typing import NamedFloatDict

# ``diffcalc-core`` is an optional dependency (:issue:`119`).  Import it
# lazily so that this module can be imported (and the ``diffcalc`` solver
# entry point can be advertised by hklpy2) even when the backend is not
# installed.  The failure is deferred to :meth:`DiffcalcSolver.__init__`,
# which raises a clear, actionable :class:`SolverError`.
try:
    from diffcalc.hkl.calc import HklCalculation
    from diffcalc.hkl.constraints import Constraints
    from diffcalc.hkl.geometry import Position
    from diffcalc.ub.calc import UBCalculation
    from diffcalc.util import DiffcalcException

    _DIFFCALC_IMPORT_ERROR: ImportError | None = None
except ImportError as exc:  # exercised by test_diffcalc_optional via import simulation
    HklCalculation = Constraints = Position = UBCalculation = None  # type: ignore[assignment]
    DiffcalcException = None  # type: ignore[assignment]
    _DIFFCALC_IMPORT_ERROR = exc

logger = logging.getLogger(__name__)

INSTALL_HINT = (
    "The 'diffcalc' solver requires the optional 'diffcalc-core' package, "
    "which is not installed.  Install it with one of:\n"
    "    pip install hklpy2-solvers[diffcalc]\n"
    "    pip install diffcalc-core\n"
    "    conda install -c paulscherrerinstitute diffcalc-core"
)
"""Actionable message shown when ``diffcalc-core`` is not installed."""

GEOMETRY_NAME = "diffcalc_4S_2D"
"""Geometry name exposed to hklpy2."""

REAL_AXES = ["mu", "delta", "nu", "eta", "chi", "phi"]
"""Ordered real axis names (matching diffcalc Position.fields)."""

PSEUDO_AXES = ["h", "k", "l"]
"""Ordered pseudo axis names."""

ENERGY_REST_KEV = 12.39842
"""Product of photon energy (keV) and wavelength (Angstrom)."""

try:
    _BACKEND_VERSION = _pkg_version("diffcalc-core")
except PackageNotFoundError:  # pragma: no cover - defensive
    _BACKEND_VERSION = "unknown"

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
    "a_eq_b fixed_delta fixed_mu": {"delta": 0.0, "a_eq_b": True, "mu": 0.0},
    "a_eq_b fixed_nu fixed_mu": {"nu": 0.0, "a_eq_b": True, "mu": 0.0},
    "a_eq_b fixed_delta fixed_eta": {"delta": 0.0, "a_eq_b": True, "eta": 0.0},
    "fixed_nu fixed_psi fixed_phi": {"nu": 0.0, "psi": 0.0, "phi": 0.0},
    # ---- 1 det + 2 samp ----
    "fixed_delta fixed_chi fixed_phi": {"delta": 0.0, "chi": 0.0, "phi": 0.0},
    "fixed_delta fixed_mu fixed_eta": {"delta": 0.0, "mu": 0.0, "eta": 0.0},
    "fixed_delta fixed_mu fixed_phi": {"delta": 0.0, "mu": 0.0, "phi": 0.0},
    "fixed_nu fixed_mu fixed_chi": {"nu": 0.0, "mu": 0.0, "chi": 0.0},
    "fixed_nu fixed_eta fixed_phi": {"nu": 0.0, "eta": 0.0, "phi": 0.0},
    "fixed_nu fixed_eta fixed_chi": {"nu": 0.0, "eta": 0.0, "chi": 0.0},
    "bisect fixed_mu fixed_nu": {"bisect": True, "mu": 0.0, "nu": 0.0},
    "bisect fixed_eta fixed_delta": {"bisect": True, "eta": 0.0, "delta": 0.0},
    "bisect fixed_omega fixed_nu": {"bisect": True, "omega": 0.0, "nu": 0.0},
    # ---- 1 ref + 2 samp ----
    "a_eq_b fixed_chi fixed_phi": {"a_eq_b": True, "chi": 0.0, "phi": 0.0},
    "a_eq_b fixed_chi fixed_eta": {"a_eq_b": True, "chi": 0.0, "eta": 0.0},
    "a_eq_b fixed_chi fixed_mu": {"a_eq_b": True, "chi": 0.0, "mu": 0.0},
    "a_eq_b fixed_mu fixed_eta": {"a_eq_b": True, "mu": 0.0, "eta": 0.0},
    "a_eq_b fixed_mu fixed_phi": {"a_eq_b": True, "mu": 0.0, "phi": 0.0},
    "a_eq_b fixed_eta fixed_phi": {"a_eq_b": True, "eta": 0.0, "phi": 0.0},
    # ---- 3 samp ----
    "fixed_eta fixed_chi fixed_phi": {"eta": 0.0, "chi": 0.0, "phi": 0.0},
    "fixed_mu fixed_chi fixed_phi": {"mu": 0.0, "chi": 0.0, "phi": 0.0},
    "fixed_mu fixed_eta fixed_phi": {"mu": 0.0, "eta": 0.0, "phi": 0.0},
    "fixed_mu fixed_eta fixed_chi": {"mu": 0.0, "eta": 0.0, "chi": 0.0},
}


def _mode_token_key(name: str) -> frozenset[str]:
    """Canonical key for a space-delimited mode name.

    Returns the set of whitespace-delimited tokens.  Two mode names
    that differ only in the order of their tokens map to equal keys
    (see :issue:`109`).  Empty / whitespace-only input maps to an
    empty frozenset.
    """
    return frozenset(name.split())


_MODES_BY_TOKENS: dict[frozenset[str], str] = {_mode_token_key(name): name for name in _MODES}
"""Reverse index for built-in modes, keyed by token-set.

Maps each token-set to the canonical display name in ``_MODES``.
Built at import time; never mutated.  See :issue:`109`."""


class DiffcalcSolver(SolverBase):
    """
    Solver for diffcalc-core (You 1999, 4S+2D six-circle 'psic' geometry).

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
    version = _BACKEND_VERSION

    def __init__(self, geometry: str = GEOMETRY_NAME, **kwargs: Any) -> None:
        if _DIFFCALC_IMPORT_ERROR is not None:
            raise SolverError(INSTALL_HINT) from _DIFFCALC_IMPORT_ERROR
        if geometry != GEOMETRY_NAME:
            raise SolverError(
                f"DiffcalcSolver supports only the {GEOMETRY_NAME!r} geometry, received {geometry!r}."
            )

        # Pop persistence kwargs delivered via ``solver_kwargs`` from
        # a saved configuration (see :issue:`108`).  Replayed after
        # the internal state is initialised but before any mode is
        # applied so a saved ``mode:`` referencing a user-registered
        # mode resolves via the normal setter.
        user_modes_state = kwargs.pop("user_modes", None)

        # Initialize internal state *before* super().__init__ which
        # may set mode via the setter.
        self._ubcalc = UBCalculation("default")
        self._constraints = Constraints()
        self._hklcalc: HklCalculation | None = None
        self._reflections: list[ReflectionDict] = []
        self._wavelength: float | None = None
        self._lattice: NamedFloatDict = {}
        # User-registered modes added at runtime via register_mode()
        # or replayed from a persisted configuration via the
        # ``user_modes`` kwarg.  Persisted across hklpy2
        # ``export()`` / ``simulator_from_config()`` round-trips via
        # the ``_metadata`` override (see :issue:`108`).
        self._user_modes: dict[str, dict[str, Any]] = {}
        # Reverse index from token-set to user-mode display name,
        # mirroring ``_MODES_BY_TOKENS`` for built-ins.  Enables
        # order-independent matching (see :issue:`109`).
        self._user_modes_by_tokens: dict[frozenset[str], str] = {}

        # Replay persisted user modes (:issue:`108`) before
        # ``super().__init__`` so a saved ``mode:`` set by the base
        # class resolves cleanly.
        if user_modes_state is not None:
            self._replay_user_modes(user_modes_state)

        super().__init__(geometry, **kwargs)

        # Apply default mode if none was set via kwargs.
        # bisect + mu=0 + nu=0 is the canonical bisecting_vertical
        # (per diffcalc-core's __calc_sample_con_mu_bisect: "Vertical
        # scattering geometry with omega = 0").  Equivalent to
        # bisecting_vertical in hkl_soleil E6C terminology.  See
        # geometries.rst for details.
        if not self.mode and self.modes:  # pragma: no branch
            self.mode = "bisect fixed_mu fixed_nu"

    def _replay_user_modes(self, state: Any) -> None:
        """Re-register user modes from a persisted ``user_modes`` dict.

        Idempotent across re-restore: an entry whose token-set is
        already registered is skipped (so loading the same config
        twice does not raise).  Any other failure is propagated as
        :class:`SolverError` naming the offending mode.
        """
        if not isinstance(state, dict):
            raise SolverError(f"user_modes must be a dict[str, dict], received {state!r}.")
        for name, constraints in state.items():
            try:
                token_key = frozenset(name.split())
            except AttributeError as exc:
                raise SolverError(f"user_modes key must be a string, received {name!r}.") from exc
            if token_key in self._user_modes_by_tokens:
                continue
            try:
                self.register_mode(name, constraints)
            except SolverError as exc:
                raise SolverError(f"user_modes replay failed for {name!r}: {exc}") from exc

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _rebuild_hklcalc(self) -> None:
        """Recreate the HklCalculation from current state."""
        self._hklcalc = HklCalculation(self._ubcalc, self._constraints)

    def _all_modes(self) -> dict[str, dict[str, Any]]:
        """Merged view of built-in plus user-registered modes.

        Built-in modes come first; user modes follow in registration
        order.  Built-in names cannot be shadowed (enforced by
        :meth:`register_mode`).
        """
        return {**_MODES, **self._user_modes}

    def _resolve_mode_name(self, name: str) -> str | None:
        """Return the canonical display name for ``name``, or ``None``.

        Matches by token set so any permutation of a registered mode
        name resolves to the stored display name (see :issue:`109`).
        Built-in modes take precedence over user modes on collision
        (which :meth:`register_mode` already prevents).
        """
        key = _mode_token_key(name)
        if not key:
            return None
        if key in _MODES_BY_TOKENS:
            return _MODES_BY_TOKENS[key]
        if key in self._user_modes_by_tokens:
            return self._user_modes_by_tokens[key]
        return None

    def _apply_mode_constraints(self) -> None:
        """Set diffcalc constraints from the current mode.

        Rebuilds :attr:`_constraints` and :attr:`_hklcalc` only when the
        mode has changed since the last call, avoiding redundant object
        construction on every :meth:`forward` call.
        """
        if not self.mode:  # pragma: no cover - constructor always sets a mode
            return
        if getattr(self, "_applied_mode", None) == self.mode:
            return
        self._constraints = Constraints(self._all_modes()[self.mode])
        self._rebuild_hklcalc()
        self._applied_mode = self.mode

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
        if self._hklcalc is None:  # pragma: no cover - UB setter rebuilds it
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
        if self._hklcalc is None:  # pragma: no cover - calculate_UB rebuilds it
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
        """Calculate the UB matrix using two reflections (Busing & Levy).

        The ``r1`` and ``r2`` arguments are the contractual source of
        truth: any reflections previously held by the underlying
        ``diffcalc`` :class:`~diffcalc.ub.calc.UBCalculation` are
        cleared and the two named reflections are inserted before UB
        is computed.  See :issue:`58`.
        """
        # Ensure lattice is set
        if self._ubcalc.crystal is None:
            raise SolverError("Lattice must be set before calculating UB.")

        # Honour the caller-supplied reflections, regardless of any
        # stale solver-side state.
        self.removeAllReflections()
        self.addReflection(r1)
        self.addReflection(r2)

        try:
            self._ubcalc.calc_ub()
        except DiffcalcException as exc:
            raise SolverError(str(exc)) from exc
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
        constrained_motors = set(self._all_modes()[self.mode].keys()) & set(REAL_AXES)
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

    @property
    def _summary_dict(self) -> KeyValueMap:
        """Return a summary of the geometry (modes, axes).

        Overrides :attr:`SolverBase._summary_dict` so that each mode
        reports only the axes actually computed by :meth:`forward`
        (via :attr:`axes_w`) rather than listing every real axis as
        writable.
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
        except DiffcalcException as exc:  # pragma: no cover - inverse is closed-form
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

    @SolverBase.sample.setter
    def sample(self, value: dict) -> None:
        """Set the crystalline sample, pushing lattice and reflections into diffcalc.

        Overrides :class:`~hklpy2.backends.base.SolverBase` so that, after
        storing the dict, the lattice is immediately pushed into
        :attr:`_ubcalc` and all reflections are re-added in ``order``
        sequence.  This ensures that :meth:`calculate_UB` can find a
        crystal when called by ``hklpy2.Core.calc_UB()`` (fixes
        :issue:`25`).
        """
        if not isinstance(value, dict):
            raise TypeError(f"Must supply dictionary, received {value!r}")
        self._sample = value

        # Push lattice into diffcalc immediately so that ``calculate_UB``
        # has a crystal to work with.
        if "lattice" in value:
            self.lattice = value["lattice"]

        # Re-populate diffcalc's reflection list in the declared order so that
        # calc_ub() uses the correct pair.
        # reflections may be a list or a dict keyed by name.
        raw = value.get("reflections", [])
        if isinstance(raw, dict):
            refl_by_name: dict = raw
        else:
            refl_by_name = {r["name"]: r for r in raw}

        self._reflections.clear()
        self._ubcalc = UBCalculation("default")
        if self._lattice:
            # Re-apply lattice after UBCalculation reset.
            self.lattice = self._lattice
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

        # Order-independent matching (:issue:`109`): resolve any
        # permutation of the constraint tokens to the registered
        # display name before validation, then store and apply the
        # canonical name.
        if isinstance(value, str) and value.strip():
            canonical = self._resolve_mode_name(value)
            if canonical is not None:
                value = canonical
        check_value_in_list("Mode", value, self.modes, blank_ok=True)
        self._mode = value
        self._applied_mode = None  # invalidate so next forward() rebuilds
        if value and value in self._all_modes():
            self._apply_mode_constraints()

    @property
    def modes(self) -> list[str]:
        """List of operating modes for this geometry.

        Includes both built-in modes and any user-registered modes
        (see :meth:`register_mode`).
        """
        return list(self._all_modes().keys())

    @property
    def _metadata(self) -> dict[str, Any]:
        """Solver metadata extended with the active mode and persisted user modes.

        Adds the following keys to the base :class:`SolverBase`
        metadata:

        * ``mode`` — the currently active operating mode name.  Read
          back by :meth:`hklpy2.diffract.DiffractometerBase.restore`
          (via ``restore_mode=True``) and re-applied to the
          reconstructed solver.  Mirrors the precedent set by
          :class:`hklpy2.backends.hkl_soleil.HklSolver._metadata`.
        * ``user_modes`` — only when non-empty.  Mapping of
          user-registered mode names to their constraint dicts so
          modes registered via :meth:`register_mode` survive
          ``Diffractometer.export()`` →
          :func:`hklpy2.run_utils.simulator_from_config` round-trips
          (see :issue:`108`).  ``hklpy2.simulator_from_config()``
          forwards every non-reserved key under ``solver:`` as a
          ``solver_kwargs`` entry, where it is picked up by
          :meth:`__init__` and replayed via :meth:`register_mode`.

        .. note::

           ``hklpy2.Core`` caches the active mode and pushes it to
           the underlying solver only when the next ``forward()``
           / ``inverse()`` runs (or when
           :meth:`hklpy2.ops.Core.update_solver` is called
           explicitly).  If a caller sets ``diffractometer.core.mode``
           then immediately reads ``_metadata`` / calls
           ``export()`` without an intervening calculation, the
           saved ``mode`` may reflect the previous value.  This
           caching behaviour is upstream and affects every solver.
        """
        meta = dict(super()._metadata)
        meta["mode"] = self.mode
        if self._user_modes:
            meta["user_modes"] = {name: dict(constraints) for name, constraints in self._user_modes.items()}
        return meta

    @property
    def pseudo_axis_names(self) -> list[str]:
        """Ordered list of pseudo axis names."""
        return list(PSEUDO_AXES)

    @property
    def real_axis_names(self) -> list[str]:
        """Ordered list of real axis names."""
        return list(REAL_AXES)

    def set_reals(self, reals: NamedFloatDict) -> None:
        """Set current real-axis values (used by the presets feature).

        Called by ``hklpy2.Core.forward()`` before :meth:`forward` to push
        constant-axis values into the solver.  For diffcalc, constant axes are
        encoded in the :class:`~diffcalc.hkl.constraints.Constraints` object
        rather than in a geometry state, so this method only validates the
        input and is otherwise a no-op.

        .. note::
            ``set_reals`` is not yet part of
            :class:`~hklpy2.backends.base.SolverBase`; it was introduced via
            the hklpy2 presets feature.  Tracked upstream as
            `bluesky/hklpy2#347 <https://github.com/bluesky/hklpy2/issues/347>`_.
        """
        if not isinstance(reals, dict):
            raise TypeError(f"Must supply dict, received {reals!r}")
        if not all(isinstance(v, (int, float)) for v in reals.values()):
            raise TypeError(f"All values must be numbers.  Received: {reals!r}")

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

    def register_mode(self, name: str, constraints: dict[str, Any]) -> None:
        """Register a new operating mode at runtime.

        Lets users add mode/constraint combinations that diffcalc-core
        implements but ``DiffcalcSolver`` does not ship by default,
        without forking the package.  The mode is validated against
        :class:`diffcalc.hkl.constraints.Constraints` before being
        accepted.

        PARAMETERS

        name : str
            Name to register the mode under, as a space-delimited
            list of the constraint names.  Order does not matter:
            ``"bisect fixed_mu fixed_nu"`` and
            ``"fixed_mu bisect fixed_nu"`` are treated as the same
            mode name (see :issue:`109`).  Must not clash, under
            this order-independent rule, with a built-in mode name
            or with a previously registered user mode (use
            :meth:`unregister_mode` first to redefine).
        constraints : dict[str, Any]
            Exactly three diffcalc constraints, keyed by diffcalc
            constraint name.  Float values pin the named axis at
            that value; ``True`` activates a boolean constraint
            (``a_eq_b``, ``bin_eq_bout``, ``bisect``).

        RAISES

        SolverError
            If ``name`` clashes with a built-in or already-registered
            mode; if ``constraints`` is not a dict of exactly three
            entries with diffcalc-recognised keys; if the combination
            does not survive ``Constraints(...).asdict`` round-trip
            (catches same-category conflicts that diffcalc silently
            collapses); or if
            :meth:`diffcalc.hkl.constraints.Constraints.is_current_mode_implemented`
            returns False.

        .. note::

           User-registered modes live only for the lifetime of this
           solver instance.  They are not persisted across hklpy2
           ``save_config`` / ``restore_config`` round-trips.
        """
        if not isinstance(name, str) or not name:
            raise SolverError(f"Mode name must be a non-empty string, received {name!r}.")
        # Collision detection by token-set (:issue:`109`): a permuted
        # form of an existing built-in or user mode is also a clash.
        tokens = name.split()
        if not tokens:
            raise SolverError(f"Mode name must list at least one constraint, received {name!r}.")
        if len(set(tokens)) != len(tokens):
            duplicates = sorted({t for t in tokens if tokens.count(t) > 1})
            raise SolverError(
                f"Mode name {name!r} repeats constraint name(s) {duplicates!r}; "
                f"each constraint may appear at most once."
            )
        token_key = frozenset(tokens)
        if token_key in _MODES_BY_TOKENS:
            existing = _MODES_BY_TOKENS[token_key]
            raise SolverError(f"Cannot redefine built-in mode {existing!r}.")
        if token_key in self._user_modes_by_tokens:
            existing = self._user_modes_by_tokens[token_key]
            raise SolverError(f"User mode {existing!r} already registered; call unregister_mode() first.")
        if not isinstance(constraints, dict):
            raise SolverError(f"Constraints must be a dict, received {constraints!r}.")
        if len(constraints) != 3:
            raise SolverError(f"Mode {name!r} requires exactly three constraints, received {len(constraints)}.")
        try:
            probe = Constraints(constraints)
        except (DiffcalcException, ValueError) as exc:
            raise SolverError(f"diffcalc rejected constraints for {name!r}: {exc}") from exc
        # Guard against same-category collisions that diffcalc silently
        # collapses (e.g. {delta: 0, nu: 0, mu: 0} drops delta).
        if set(probe.asdict) != set(constraints):
            dropped = sorted(set(constraints) - set(probe.asdict))
            raise SolverError(
                f"Mode {name!r}: constraints {dropped!r} were dropped by "
                f"diffcalc (same-category conflict).  Only one detector "
                f"and one reference constraint are allowed."
            )
        # ``is_current_mode_implemented()`` raises for 0/1/2-constraint
        # Constraints objects, but those are already rejected above by
        # the explicit ``len(constraints) != 3`` check; the bare except
        # is defensive only.
        try:
            implemented = probe.is_current_mode_implemented()
        except (DiffcalcException, ValueError) as exc:  # pragma: no cover
            raise SolverError(f"diffcalc validation failed for {name!r}: {exc}") from exc
        if not implemented:
            raise SolverError(f"Mode {name!r}: constraint combination is not implemented by diffcalc-core.")
        self._user_modes[name] = dict(constraints)
        self._user_modes_by_tokens[token_key] = name

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

    @UB.setter
    def UB(self, value: Matrix3x3) -> None:
        """Restore the orientation matrix into diffcalc's UBCalculation.

        Called by ``hklpy2.Core.update_solver()`` after ``sample`` is set, to
        restore the previously computed UB so that :meth:`forward` and
        :meth:`inverse` use the correct orientation.
        """
        if self._ubcalc.crystal is None:
            # Need a lattice before set_ub will work; use the stored one.
            if self._lattice:
                self.lattice = self._lattice
            else:
                self._ubcalc.set_lattice("default", 1.0, 1.0, 1.0, 90.0, 90.0, 90.0)
        self._ubcalc.set_ub(value)
        self._rebuild_hklcalc()

    def unregister_mode(self, name: str) -> None:
        """Remove a previously :meth:`register_mode`-registered mode.

        PARAMETERS

        name : str
            Name of the user-registered mode to remove.  Matched
            order-independently against the registered constraint
            names, so any permutation of the original name resolves
            to the same mode (see :issue:`109`).

        RAISES

        SolverError
            If ``name`` refers to a built-in mode (built-ins cannot
            be removed); if ``name`` is not currently registered.

        If the solver-side active :attr:`mode` is the one being
        removed, it is cleared to ``""``.  When the solver is wired
        into an hklpy2 ``Diffractometer``, the diffractometer's own
        cached ``core.mode`` may still hold the now-stale name and
        cause a "Mode unknown" ``ValueError`` on the next
        ``forward()`` call.  To avoid that, switch
        ``diffractometer.core.mode`` to a different mode before
        calling :meth:`unregister_mode` when the user mode is
        currently active.
        """
        # Symmetric with register_mode (:issue:`109`): resolve any
        # token-permutation to the registered display name before
        # acting.  Built-in detection also uses the token-set so a
        # permuted built-in name fails with the same message as the
        # exact built-in name.
        if not isinstance(name, str):
            raise SolverError(f"Mode name must be a string, received {name!r}.")
        token_key = frozenset(name.split())
        if token_key in _MODES_BY_TOKENS:
            existing = _MODES_BY_TOKENS[token_key]
            raise SolverError(f"Cannot unregister built-in mode {existing!r}.")
        if token_key not in self._user_modes_by_tokens:
            raise SolverError(f"User mode {name!r} is not registered.")
        canonical = self._user_modes_by_tokens.pop(token_key)
        del self._user_modes[canonical]
        if self.mode == canonical:
            self._mode = ""
            self._applied_mode = None

    def update_mode_constraints(self, mode_name: str | None = None, **updates: float | bool) -> None:
        """Override constraint values on a previously-registered user mode.

        Sibling of :meth:`hklpy2_solvers.ad_hoc_solver.AdHocSolver.update_mode_constraints`
        for the diffcalc backend.  Replaces one or more constraint values
        in an existing user-registered mode without changing the mode's
        constraint names or structure.  Built-in modes are frozen and
        cannot be modified — register a variant under a new name with
        :meth:`register_mode` instead.

        Parameters
        ----------
        mode_name : str, optional
            Name of the mode to update.  ``None`` (default) operates on
            the active mode (:attr:`mode`).  Matched order-independently
            against registered constraint-name sets, so any permutation
            of the original name resolves to the same mode (see
            :issue:`109`).
        **updates : float or bool
            Mapping of constraint name → new value.  Each key must
            already exist as a constraint name in the resolved mode
            (this method does not add or remove constraints — use
            :meth:`unregister_mode` + :meth:`register_mode` for structural
            changes).  Float values pin the named axis at that value;
            ``True`` activates a boolean constraint (``a_eq_b``,
            ``bin_eq_bout``, ``bisect``).

        Raises
        ------
        SolverError
            If ``mode_name`` is unknown; if it names a built-in mode
            (built-ins are frozen); if any kwarg names a constraint not
            present in the mode; or if the resulting constraint
            combination is rejected by diffcalc (same-category
            collision, not-implemented, etc.).

        Notes
        -----
        Mutates the user-mode dict in place and clears
        :attr:`_applied_mode` so that a subsequent :meth:`forward` /
        :meth:`inverse` rebuilds the diffcalc
        :class:`~diffcalc.hkl.constraints.Constraints` object with the
        new values.  The mode's display name is unchanged.

        Examples
        --------
        Register a custom mode then later override one value::

            solver.register_mode(
                "fixed_delta fixed_eta fixed_chi",
                {"delta": 0.0, "eta": 0.0, "chi": 0.0},
            )
            solver.update_mode_constraints(
                "fixed_delta fixed_eta fixed_chi", chi=45.0,
            )

        Operate on the currently active mode::

            solver.mode = "fixed_delta fixed_eta fixed_chi"
            solver.update_mode_constraints(chi=45.0)
        """
        target_input = self._mode if mode_name is None else mode_name
        if not isinstance(target_input, str):
            raise SolverError(f"Mode name must be a string, received {target_input!r}.")
        token_key = frozenset(target_input.split())
        if token_key in _MODES_BY_TOKENS:
            existing = _MODES_BY_TOKENS[token_key]
            raise SolverError(
                f"Cannot modify built-in mode {existing!r}; register a variant under a new name instead."
            )
        if token_key not in self._user_modes_by_tokens:
            raise SolverError(f"User mode {target_input!r} is not registered.")
        canonical = self._user_modes_by_tokens[token_key]
        existing_constraints = self._user_modes[canonical]
        unknown = sorted(set(updates) - set(existing_constraints))
        if unknown:
            raise SolverError(
                f"update_mode_constraints({canonical!r}): constraint(s) "
                f"{unknown!r} not present in this mode; available: "
                f"{sorted(existing_constraints)}."
            )
        # Build the prospective constraint dict and validate it through
        # diffcalc the same way ``register_mode`` does, so any value-side
        # error (bad type, same-category collision, not-implemented) is
        # caught before mutation.
        candidate = {**existing_constraints, **updates}
        try:
            probe = Constraints(candidate)
        except (DiffcalcException, ValueError) as exc:
            raise SolverError(f"diffcalc rejected updated constraints for {canonical!r}: {exc}") from exc
        # Defensive: same-category collapse and not-implemented are
        # structurally unreachable here because ``register_mode``
        # already validated the constraint *name set* at registration
        # time, and this method only mutates values (never adds or
        # removes keys).  Kept for parity with ``register_mode`` and
        # to guard against any future diffcalc value-dependent
        # implementation gate.
        if set(probe.asdict) != set(candidate):  # pragma: no cover - defensive
            dropped = sorted(set(candidate) - set(probe.asdict))
            raise SolverError(
                f"update_mode_constraints({canonical!r}): constraints "
                f"{dropped!r} were dropped by diffcalc (same-category "
                f"conflict)."
            )
        try:
            implemented = probe.is_current_mode_implemented()
        except (DiffcalcException, ValueError) as exc:  # pragma: no cover - defensive
            raise SolverError(f"diffcalc validation failed for {canonical!r}: {exc}") from exc
        if not implemented:  # pragma: no cover - defensive
            raise SolverError(
                f"update_mode_constraints({canonical!r}): updated "
                f"constraint combination is not implemented by diffcalc-core."
            )
        self._user_modes[canonical] = candidate
        # Invalidate the applied-mode cache so the next forward()/inverse()
        # rebuilds the diffcalc ``Constraints`` object with the new values.
        self._applied_mode = None

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

# Copyright (c) 2026 Pete Jemian <prjemian+hklpy2@gmail.com>
# SPDX-License-Identifier: LicenseRef-UChicago-Argonne-LLC-License
"""Cross-validate solver geometries against ``hkl_soleil`` (libhkl).

This module implements the cross-validation suite of :issue:`50`: a
permanent regression test suite that compares ``forward()`` /
``inverse()`` between matched geometry/mode groups across every solver
this package exposes via ``hklpy2.creator``.  ``hkl_soleil`` is the
reference backend; the other solvers in each group are expected to
agree on the physical scattering condition (Bragg ``2theta`` magnitude
and round-trip ``(h, k, l)``) within loose tolerances.

Groups currently covered:

* **vertical four-circle bisecting** (PR1): scattering plane contains
  the ``omega``/``ttheta`` axes; reference ``hkl_soleil/E4CV``.
* **horizontal four-circle bisecting** (PR2, :issue:`67`): scattering
  plane rotated 90 deg about the beam; reference ``hkl_soleil/E6C``
  in ``bissector_horizontal`` mode (libhkl's ``E4CH`` is structurally
  a vertical-style ``bissector`` and provides no independent signal).

Later PRs add kappa (:issue:`66`), six-circle and beyond (:issue:`64`),
and a dedicated CI workflow (:issue:`65`).

The module skips silently when libhkl is not importable via
``gobject-introspection`` (e.g. on default GitHub-hosted runners that
have no conda-forge libhkl).  ``pytest.importorskip`` is delegated to a
small shim module because ``gi`` requires a version-negotiation step
before the ``Hkl`` namespace can be loaded.
"""

import math
import random
import re
from contextlib import nullcontext as does_not_raise

import numpy as np
import pytest

pytest.importorskip("tests._hkl_library_probe")

import hklpy2  # noqa: E402  (import after probe so skips fire first)
from ad_hoc_diffractometer import Lattice as _AdHocLattice  # noqa: E402
from hklpy2.exceptions import SolverError  # noqa: E402

pytestmark = pytest.mark.cross_validation

# ---------------------------------------------------------------------------
# Test data
# ---------------------------------------------------------------------------

SAMPLES = {
    "cubic": dict(name="cubic", a=3.5),
    "sapphire": dict(name="sapphire", a=4.758, c=12.991, gamma=120),
    "triclinic": dict(
        name="triclinic",
        a=3.5,
        b=14.0,
        c=5.0,
        alpha=80,
        beta=85,
        gamma=109.5,
    ),
}

HKL_BOOTSTRAP_1 = (0, 0, 6)
HKL_BOOTSTRAP_2 = (1, 1, 0)
"""Reflections used to bootstrap each simulator's UB."""

DEFAULT_REFLECTIONS = [HKL_BOOTSTRAP_1, HKL_BOOTSTRAP_2]
"""Reflections probed for every (group, sample) combination by default."""

# Sample-specific extra reflections appended to ``DEFAULT_REFLECTIONS``.
EXTRA_REFLECTIONS_BY_SAMPLE = {
    "sapphire": [(0, 1, 2)],
}

TTH_ATOL_DEG = 0.01
"""Tolerance for cross-solver agreement on |2theta| (degrees)."""

HKL_ATOL = 0.001
"""Tolerance for forward/inverse round-trip on (h, k, l)."""

# Vertical four-circle bisecting cross-validation group.
#
# Each entry is a peer to ``hkl_soleil/E4CV``: same scattering plane
# (vertical), same bisecting condition (``omega = ttheta / 2``), same
# physical observable for any ``(h, k, l)``.
VERTICAL_GROUP = {
    "e4cv": dict(
        solver="hkl_soleil",
        geometry="E4CV",
        reals=["omega", "chi", "phi", "ttheta"],
        mode="bissector",
    ),
    "e6c": dict(
        solver="hkl_soleil",
        geometry="E6C",
        reals=["mu", "omega", "chi", "phi", "gamma", "ttheta"],
        mode="bissector_vertical",
    ),
    "fourcv": dict(
        solver="ad_hoc",
        geometry="fourcv",
        reals=["omega", "chi", "phi", "ttheta"],
        mode="bisecting",
    ),
    "psic": dict(
        solver="ad_hoc",
        geometry="psic",
        reals=["mu", "omega", "chi", "phi", "nu", "ttheta"],
        mode="bisecting_vertical",
    ),
    "fivec": dict(
        solver="ad_hoc",
        geometry="fivec",
        reals=["mu", "omega", "chi", "phi", "ttheta"],
        mode="bisecting_4c",
    ),
    "diffcalc": dict(
        solver="diffcalc",
        geometry="diffcalc_4S_2D",
        reals=["mu", "ttheta", "nu", "omega", "chi", "phi"],
        mode="4S+2D bisect_eta_fixed nu_fixed",
    ),
}

# Horizontal four-circle bisecting cross-validation group.
#
# Each entry is a peer to ``hkl_soleil/E6C`` in ``bissector_horizontal``
# mode: scattering plane rotated 90 deg about the beam, same bisecting
# condition (``omega = ttheta / 2`` where ``omega`` is the user-facing
# name for whichever backend axis is the primary sample rotation in
# that mode), same physical observable for any ``(h, k, l)``.
#
# ``reals=`` lists preserve each solver's canonical axis order; only
# axis-name renames are applied.  The renames bind user-facing
# ``omega`` to the backend axis that actually moves in horizontal
# bisecting (``mu`` for ``E6C``/``psic``, ``eta`` for ``diffcalc``,
# identity for ``fourch``), and bind user-facing ``ttheta`` to the
# backend detector axis (``gamma`` for ``E6C``, ``nu`` for
# ``psic``/``diffcalc``, identity for ``fourch``).  The remaining
# backend axes (``omega`` on ``E6C``, ``mu``/``delta`` on
# ``diffcalc``) are pinned to 0 by the mode and renamed to inert
# placeholders.
#
# ``hkl_soleil/E4CH`` is omitted: its ``bissector`` mode is
# structurally vertical-style (2theta on ``tth``, ``omega = tth / 2``)
# and provides no independent signal vs. the PR1 ``e4cv`` entry.
HORIZONTAL_GROUP = {
    "e6c": dict(
        solver="hkl_soleil",
        geometry="E6C",
        reals=["omega", "eta", "chi", "phi", "ttheta", "delta"],
        mode="bissector_horizontal",
    ),
    "fourch": dict(
        solver="ad_hoc",
        geometry="fourch",
        reals=["omega", "chi", "phi", "ttheta"],
        mode="bisecting",
    ),
    "psic": dict(
        solver="ad_hoc",
        geometry="psic",
        reals=["omega", "eta", "chi", "phi", "ttheta", "delta"],
        mode="bisecting_horizontal",
    ),
    "diffcalc": dict(
        solver="diffcalc",
        geometry="diffcalc_4S_2D",
        reals=["mu", "delta", "ttheta", "omega", "chi", "phi"],
        mode="4S+2D mu_fixed a_eq_b delta_fixed",
    ),
}

# Cross-validation groups.  Each group maps to its peer dict and the
# name of the reference entry within that dict; the per-group bootstrap
# recipe is selected by ``BOOTSTRAP_BY_GROUP`` below.
GROUPS = {
    "vertical": dict(entries=VERTICAL_GROUP, reference="e4cv"),
    "horizontal": dict(entries=HORIZONTAL_GROUP, reference="e6c"),
}

# Known cross-solver |2theta| discrepancies tracked in their own issues.
# Each entry maps ``(group, entry, sample, hkl)`` to an issue
# reference; the corresponding ``test_two_theta_matches_reference``
# parameter case is marked ``xfail(strict=True)`` so the discrepancy is
# documented in code and a future fix flips the case to pass without
# code changes.  These marks apply *only* to the cross-solver
# comparison: every solver still round-trips ``inverse(forward(hkl)) ==
# hkl`` internally for these cases, so round-trip tests are not
# xfailed.
KNOWN_TTH_DISAGREEMENTS = {
    # https://github.com/prjemian/hklpy2_solvers/issues/68
    ("vertical", "fourcv", "triclinic", (0, 0, 6)): "issue #68",
    ("vertical", "psic", "triclinic", (0, 0, 6)): "issue #68",
    ("vertical", "fivec", "triclinic", (0, 0, 6)): "issue #68",
    ("vertical", "diffcalc", "triclinic", (0, 0, 6)): "issue #68",
    ("horizontal", "fourch", "triclinic", (0, 0, 6)): "issue #68",
    ("horizontal", "psic", "triclinic", (0, 0, 6)): "issue #68",
    ("horizontal", "diffcalc", "triclinic", (0, 0, 6)): "issue #68",
}

# Known forward-solution gaps: parameter cases where ``forward()`` itself
# raises (typically ``NoForwardSolutions``) on a peer but its group peers
# succeed.  Marked ``xfail(strict=True)`` on *both* the round-trip and
# the cross-solver comparison tests so the gap is documented in code
# and a future fix surfaces as ``XPASS``.
KNOWN_FORWARD_GAPS = {
    # https://github.com/prjemian/hklpy2_solvers/issues/71
    ("horizontal", "psic", "sapphire", (0, 1, 2)): "issue #71",
}

# Per-axis angle comparisons across solvers are deferred: bisecting-mode
# branch selection (libhkl picks ``omega ~ 180 - omega`` relative to
# ad_hoc/diffcalc) and mode-specific axis distributions mean a
# meaningful per-axis check requires per-pair branch folding that is
# out of scope for the matched-group comparisons here.  See :issue:`50`.


# ---------------------------------------------------------------------------
# Helpers (lifted from tests/dev_cross_validation.py)
# ---------------------------------------------------------------------------


def _bragg_two_theta(geometry, h, k, l):  # noqa: E741 - ``l`` is the canonical name
    """Return 2theta (degrees) for ``(h, k, l)`` from Bragg's law.

    Uses a Busing & Levy (1967) B matrix constructed directly from the
    sample lattice via ``ad_hoc_diffractometer.Lattice`` so the result
    does not depend on whichever solver-specific convention
    ``geometry.sample.lattice.B`` happens to expose.  Returns ``None``
    when the reflection is unreachable at the current wavelength
    (``|sin theta| > 1``).
    """
    lat = geometry.sample.lattice
    bmat = _AdHocLattice(a=lat.a, b=lat.b, c=lat.c, alpha=lat.alpha, beta=lat.beta, gamma=lat.gamma).B
    q_vec = bmat @ np.array([h, k, l], dtype=float)
    q_mag = np.linalg.norm(q_vec)
    d_spacing = 2.0 * math.pi / q_mag
    sin_theta = geometry.beam.wavelength.get() / (2.0 * d_spacing)
    if math.fabs(sin_theta) > 1.0:
        return None
    return 2.0 * math.degrees(math.asin(sin_theta))


BOOTSTRAP_NUDGE_DEG = 2.0
"""Maximum absolute random offset (degrees) added to bootstrap motor settings.

Bootstrapping the UB from the *exact* bisecting solution risks a
degenerate fit; nudging each writable axis by a small random offset
(``|delta| <= BOOTSTRAP_NUDGE_DEG``) ensures the two reflections used
for ``calc_UB`` are linearly independent in the (chi, phi) plane.  The
nudges are drawn from a per-position ``random.Random`` instance with a
fixed seed so test runs are deterministic.
"""

BOOTSTRAP_RNG_SEED = 20260516
"""Fixed seed for the bootstrap-nudge RNG (test determinism)."""


def _nudges(seed_offset, count):
    """Return ``count`` deterministic offsets in ``[-NUDGE, +NUDGE]`` degrees."""
    rng = random.Random(BOOTSTRAP_RNG_SEED + seed_offset)
    return [rng.uniform(-BOOTSTRAP_NUDGE_DEG, BOOTSTRAP_NUDGE_DEG) for _ in range(count)]


def _rough_vertical_positions(geometry, tth1, tth2):
    """Geometry-appropriate rough motor settings for vertical bootstrap.

    The vertical scattering plane contains the ``omega``/``ttheta``
    axes; ``(1, 1, 0)`` is brought into the bisecting plane by a 90 deg
    ``phi`` rotation.  Each writable bootstrap angle is nudged off the
    exact bisecting solution by a deterministic random offset bounded
    by ``BOOTSTRAP_NUDGE_DEG`` so the two reflections used for
    ``calc_UB`` are linearly independent in the (chi, phi) plane.
    """
    p0 = {axis: 0.0 for axis in geometry.real_axis_names}
    p0.update(chi=10)
    p1 = dict(p0)
    p2 = dict(p0)
    d1_tth, d1_om, d2_tth, d2_om, d2_chi, d2_phi = _nudges(seed_offset=0, count=6)
    p1.update(ttheta=tth1 + d1_tth, omega=tth1 / 2 + d1_om)
    p2.update(
        ttheta=tth2 + d2_tth,
        omega=tth2 / 2 + d2_om,
        chi=p0["chi"] + d2_chi,
        phi=90 + d2_phi,
    )
    return p1, p2


def _rough_horizontal_positions(geometry, tth1, tth2):
    """Geometry-appropriate rough motor settings for horizontal bootstrap.

    The horizontal scattering plane is rotated 90 deg about the beam
    relative to the vertical bootstrap.  After axis renaming in
    ``HORIZONTAL_GROUP`` (primary backend axis -> ``omega``, detector
    backend axis -> ``ttheta``), the bisecting condition reads
    ``omega = ttheta / 2`` in user-facing names just like the vertical
    case.  ``(1, 1, 0)`` is brought into the horizontal Q-plane by
    ``chi = 45``, ``phi = -45``.  Each writable bootstrap angle is
    nudged off the exact bisecting solution by a deterministic random
    offset bounded by ``BOOTSTRAP_NUDGE_DEG`` so the two reflections
    used for ``calc_UB`` are linearly independent.  All other (pinned
    or non-writable) axes are left at zero so the mode constraint is
    satisfied at bootstrap.
    """
    p0 = {axis: 0.0 for axis in geometry.real_axis_names}
    p1 = dict(p0)
    p2 = dict(p0)
    d1_tth, d1_om, d2_tth, d2_om, d2_chi, d2_phi = _nudges(seed_offset=1, count=6)
    p1.update(ttheta=tth1 + d1_tth, omega=tth1 / 2 + d1_om)
    p2.update(
        ttheta=tth2 + d2_tth,
        omega=tth2 / 2 + d2_om,
        chi=45 + d2_chi,
        phi=-45 + d2_phi,
    )
    return p1, p2


BOOTSTRAP_BY_GROUP = {
    "vertical": _rough_vertical_positions,
    "horizontal": _rough_horizontal_positions,
}


def _same_position(pos_a, pos_b, atol=1e-6):
    """True when two real-position mappings are equal within ``atol``."""
    a = dict(pos_a) if not isinstance(pos_a, dict) else pos_a
    b = dict(pos_b._asdict()) if hasattr(pos_b, "_asdict") else dict(pos_b)
    keys = set(a) | set(b)
    return all(abs(float(a.get(k, 0.0)) - float(b.get(k, 0.0))) <= atol for k in keys)


def _build_simulator(group_name, entry_info, sample_dict):
    """Build a ``hklpy2`` simulator with a UB seeded from two reflections.

    ``group_name`` selects the bootstrap recipe via
    ``BOOTSTRAP_BY_GROUP``.
    """
    kwargs = dict(entry_info)
    mode = kwargs.pop("mode")
    sim = hklpy2.creator(**kwargs)
    sim.core.mode = mode
    sim.add_sample(**sample_dict)
    sim.core.constraints["chi"].limits = -100, 100
    sim.core.constraints["phi"].limits = -120, 120

    tth1 = _bragg_two_theta(sim, *HKL_BOOTSTRAP_1)
    tth2 = _bragg_two_theta(sim, *HKL_BOOTSTRAP_2)
    bootstrap = BOOTSTRAP_BY_GROUP[group_name]
    p1, p2 = bootstrap(sim, tth1, tth2)
    r1 = sim.add_reflection(HKL_BOOTSTRAP_1, p1, name="r1", replace=True)
    r2 = sim.add_reflection(HKL_BOOTSTRAP_2, p2, name="r2", replace=True)
    sim.core.calc_UB(r1, r2)

    # Refine: replace each reflection with the angles ``forward()`` picks
    # at the rough UB, then recompute.  Skip the refine step when
    # ``forward()`` returns the same position as the rough estimate,
    # since hklpy2 rejects duplicate reflections.
    f1 = sim.forward(*HKL_BOOTSTRAP_1)
    f2 = sim.forward(*HKL_BOOTSTRAP_2)
    refined = False
    if not _same_position(p1, f1):
        r1 = sim.add_reflection(HKL_BOOTSTRAP_1, f1, name="r1", replace=True)
        refined = True
    if not _same_position(p2, f2):
        r2 = sim.add_reflection(HKL_BOOTSTRAP_2, f2, name="r2", replace=True)
        refined = True
    if refined:
        sim.core.calc_UB(r1, r2)
    return sim


def _as_dict(position):
    """Return ``position`` as a plain ``dict`` of ``float`` values."""
    raw = dict(position._asdict()) if hasattr(position, "_asdict") else dict(position)
    return {k: float(v) for k, v in raw.items()}


# ---------------------------------------------------------------------------
# Module-scoped simulator cache
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def simulators():
    """Build every ``(group, entry, sample)`` simulator once per test module."""
    cache = {}
    for group_name, group in GROUPS.items():
        for entry, info in group["entries"].items():
            for sample_name, sample_dict in SAMPLES.items():
                cache[(group_name, entry, sample_name)] = _build_simulator(group_name, info, sample_dict)
    return cache


# ---------------------------------------------------------------------------
# Parametrization helpers
# ---------------------------------------------------------------------------


def _reflections_for(sample_name):
    """Reflections probed for the given sample (defaults + extras)."""
    return DEFAULT_REFLECTIONS + EXTRA_REFLECTIONS_BY_SAMPLE.get(sample_name, [])


def _round_trip_cases():
    """All ``(group, entry, sample, hkl)`` round-trip cases."""
    for group_name, group in GROUPS.items():
        for entry in group["entries"]:
            for sample in SAMPLES:
                for hkl in _reflections_for(sample):
                    yield group_name, entry, sample, hkl


def _peer_cases():
    """All peer cross-validation cases (excluding each group's reference)."""
    for group_name, group in GROUPS.items():
        reference = group["reference"]
        for entry in group["entries"]:
            if entry == reference:
                continue
            for sample in SAMPLES:
                for hkl in _reflections_for(sample):
                    yield group_name, entry, sample, hkl


def _make_param(group_name, entry, sample, hkl, *, apply_tth_xfail=False):
    """Build a ``pytest.param`` for a cross-validation case.

    Marking precedence:

    * ``KNOWN_FORWARD_GAPS`` always applies (``forward()`` raises on
      this peer for this reflection; tracked in its own issue), so
      both round-trip and cross-solver tests must xfail.
    * ``KNOWN_TTH_DISAGREEMENTS`` applies only when ``apply_tth_xfail``
      is True (cross-solver comparison only; round-trip still passes).
    """
    marks = ()
    key = (group_name, entry, sample, hkl)
    if key in KNOWN_FORWARD_GAPS:
        marks = (
            pytest.mark.xfail(
                strict=True,
                reason=f"known forward-solution gap ({KNOWN_FORWARD_GAPS[key]})",
            ),
        )
    elif apply_tth_xfail and key in KNOWN_TTH_DISAGREEMENTS:
        marks = (
            pytest.mark.xfail(
                strict=True,
                reason=(f"known cross-solver |2theta| disagreement ({KNOWN_TTH_DISAGREEMENTS[key]})"),
            ),
        )
    return pytest.param(
        dict(group=group_name, entry=entry, sample=sample, hkl=hkl),
        does_not_raise(),
        id=f"{group_name}-{entry}-{sample}-{hkl[0]}{hkl[1]}{hkl[2]}",
        marks=marks,
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "parms, context",
    [_make_param(g, e, s, h) for (g, e, s, h) in _round_trip_cases()]
    + [
        pytest.param(
            dict(group="vertical", entry="fourcv", sample="cubic", hkl=(100, 0, 0)),
            pytest.raises(SolverError, match="cannot be reached"),
            id="unreachable-vertical-fourcv-cubic-100_0_0",
        ),
    ],
)
def test_forward_inverse_roundtrip(parms, context, simulators):
    """Every solver round-trips ``inverse(forward(hkl)) ~= hkl``.

    The failure case at the end exercises the unreachable-reflection
    path: ``(100, 0, 0)`` on a 3.5 A cubic cell at lambda = 1 A demands
    ``|sin theta| > 1`` and the solver raises.
    """
    with context:
        sim = simulators[(parms["group"], parms["entry"], parms["sample"])]
        sol = sim.forward(*parms["hkl"])
        back = _as_dict(sim.inverse(_as_dict(sol)))
        for axis, expected in zip("hkl", parms["hkl"]):
            assert abs(back[axis] - expected) <= HKL_ATOL, (
                f"round-trip mismatch on {axis}: expected {expected}, got {back[axis]}"
            )


@pytest.mark.parametrize(
    "parms, context",
    [_make_param(g, e, s, h, apply_tth_xfail=True) for (g, e, s, h) in _peer_cases()]
    + [
        pytest.param(
            dict(group="vertical", entry="NOT_A_PEER", sample="cubic", hkl=(0, 0, 6)),
            pytest.raises(KeyError, match=re.escape("NOT_A_PEER")),
            id="missing-peer-entry-raises",
        ),
    ],
)
def test_two_theta_matches_reference(parms, context, simulators):
    """Peer solvers agree with their group's reference on ``|2theta|``.

    Sign of ``ttheta`` differs by mode/branch convention (libhkl's
    ``bissector`` picks ``omega ~ 121 deg`` instead of ``~59 deg`` for
    the same physical reflection), so the comparison is on
    ``|2theta|`` only.  Per-axis (``omega``/``chi``/``phi``) agreement
    requires per-pair branch folding and is deferred to a later PR;
    see :issue:`50`.

    The trailing failure case feeds an unknown entry name into the
    simulator cache and asserts the resulting ``KeyError``.
    """
    with context:
        reference = GROUPS[parms["group"]]["reference"]
        ref_sim = simulators[(parms["group"], reference, parms["sample"])]
        peer_sim = simulators[(parms["group"], parms["entry"], parms["sample"])]
        ref_sol = _as_dict(ref_sim.forward(*parms["hkl"]))
        peer_sol = _as_dict(peer_sim.forward(*parms["hkl"]))
        ref_tth = abs(ref_sol["ttheta"])
        peer_tth = abs(peer_sol["ttheta"])
        assert abs(peer_tth - ref_tth) <= TTH_ATOL_DEG, (
            f"|2theta| mismatch vs. {reference}: "
            f"ref={ref_tth:.6f}, peer={peer_tth:.6f}, "
            f"diff={abs(peer_tth - ref_tth):.6f} deg"
        )

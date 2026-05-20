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
* **horizontal four-circle bisecting** (PR2, :issue:`67`, reference
  corrected by :issue:`78`): scattering plane rotated 90 deg about
  the beam; reference ``hkl_soleil/E4CH bissector`` (the canonical
  4-circle horizontal eulerian, analog of ``E4CV`` in the vertical
  group).  ``E6C bissector_horizontal`` participates as the
  6-circle horizontal peer.
* **kappa four-circle bisecting, vertical plane** (PR3, :issue:`66`):
  kappa-axis goniometer with ``(komega, kappa, kphi)`` replacing the
  eulerian ``(omega, chi, phi)`` triad; reference
  ``hkl_soleil/K4CV``.  Six-circle kappa peers (``K6C``, ``kappa6c``)
  participate by pinning ``mu`` / detector-2 to zero in their
  ``bissector_vertical`` / ``bisecting_vertical`` modes.  The
  ``kappa`` axis is constrained to ``[-100, 100] deg`` to match
  physical kappa-arm ranges.
* **kappa bisecting, horizontal plane** (PR3b, :issue:`75`): same
  axis convention as the vertical kappa group, but the scattering
  plane is rotated 90 deg about the beam.  Reference
  ``hkl_soleil/K6C bissector_horizontal`` - libhkl ships ``K4CV``
  but not ``K4CH``, so the only available libhkl kappa-horizontal
  peer is the 6-circle ``K6C`` in its ``bissector_horizontal``
  mode.  Peers: ``ad_hoc/kappa4ch bisecting`` (4-axis kappa
  horizontal) and ``ad_hoc/kappa6c bisecting_horizontal``.  The
  K6C-horizontal bootstrap requires overspecifying both
  ``mu = tth/2`` and ``delta = tth`` (alongside the renamed
  ``ttheta``) because libhkl rejects the naive recipes with a
  degenerate U matrix or ``NoForwardSolutions``.

* **six-circle bisecting peers** (PR4, :issue:`64`): adds entries that
  fit naturally into the existing eulerian groups rather than forming
  a new group dict.  ``ad_hoc/sixc bisecting_4c`` joins
  ``EULER_VERTICAL_GROUP`` (``alpha`` / ``gamma`` pinned at 0,
  ``delta`` renamed to ``ttheta``).  ``hkl_soleil/APS POLAR`` and
  ``hkl_soleil/PETRA3 P09 EH2`` join ``EULER_HORIZONTAL_GROUP`` in
  their ``4-circles bissecting horizontal`` modes.  libhkl 5.1.3
  exposes **no** vertical-bisecting mode for either six-circle
  beamline geometry, so they participate only in the horizontal
  group.  The two geometries also disagree on which native axis is
  the bisecting primary: per the hklpy2 docs' ``writable`` column,
  POLAR uses native ``mu`` (the renaming binds ``mu -> omega``) and
  P09 EH2 uses native ``omega`` (identity primary).  Detector axes
  also differ (POLAR: ``gamma``; P09 EH2: ``delta``).

The dedicated CI workflow lives in :issue:`65`.

Earlier issues now closed as not-a-bug after re-investigation:

* :issue:`72`: ``E4CH`` is **not** an alias of ``E4CV``; the
  apparent parity was an artifact of testing only symmetric
  reflections.  ``E4CH`` is the canonical 4-circle horizontal
  eulerian reference per hkl_soleil naming and is now used as
  such in ``EULER_HORIZONTAL_GROUP`` (see :issue:`78`).  The genuinely
  missing libhkl geometry is ``K4CH``, noted upstream as a
  feature request.
* :issue:`74`: ``ad_hoc/kappa4ch`` is **not** an alias of
  ``kappa4cv``; PR3b's inclusion of ``kappa4ch`` in the
  kappa-horizontal group with sapphire ``(0, 1, 2)`` empirically
  refutes the alias claim.

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
from hklpy2.exceptions import NoForwardSolutions, SolverError  # noqa: E402

pytestmark = pytest.mark.cross_validation

# ---------------------------------------------------------------------------
# Test data
# ---------------------------------------------------------------------------

SAMPLES = {
    # cubic — single-parameter, alpha = beta = gamma = 90 deg
    "cubic": dict(name="cubic", a=3.5),
    # tetragonal — a = b, c distinct, alpha = beta = gamma = 90 deg
    "tetragonal": dict(name="tetragonal", a=4.0, b=4.0, c=5.5, alpha=90, beta=90, gamma=90),
    # orthorhombic — a, b, c distinct, alpha = beta = gamma = 90 deg
    "orthorhombic": dict(name="orthorhombic", a=4.0, b=6.5, c=8.0, alpha=90, beta=90, gamma=90),
    # hexagonal (sapphire setting) — a = b, gamma = 120 deg, alpha = beta = 90 deg
    "sapphire": dict(name="sapphire", a=4.758, c=12.991, gamma=120),
    # trigonal (rhombohedral setting) — a = b = c, alpha = beta = gamma != 90 deg
    "trigonal_rhombohedral": dict(
        name="trigonal_rhombohedral",
        a=7.0,
        b=7.0,
        c=7.0,
        alpha=72,
        beta=72,
        gamma=72,
    ),
    # monoclinic — a, b, c distinct, alpha = gamma = 90 deg, beta != 90 deg
    "monoclinic": dict(
        name="monoclinic",
        a=5.0,
        b=7.0,
        c=9.0,
        alpha=90,
        beta=110,
        gamma=90,
    ),
    # triclinic — all parameters distinct, alpha != beta != gamma != 90 deg
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
# ``(1, 1, 3)`` works on every group/entry cell for sapphire; ``(1, 1, 6)``
# works on every cell except ``kappa_horizontal/kappa6c`` (see :issue:`77`).
# Both expand the matrix's diagnostic coverage of the kappa6c failure
# pattern without polluting other groups.
EXTRA_REFLECTIONS_BY_SAMPLE = {
    "sapphire": [(0, 1, 2), (1, 1, 3), (1, 1, 6)],
}

TTH_ATOL_DEG = 0.01
"""Tolerance for cross-solver agreement on |2theta| (degrees)."""

HKL_ATOL = 0.001
"""Tolerance for forward/inverse round-trip on (h, k, l)."""

# Eulerian vertical four-circle bisecting cross-validation group.
#
# Each entry is a peer to ``hkl_soleil/E4CV``: same scattering plane
# (vertical), same bisecting condition (``omega = ttheta / 2``), same
# physical observable for any ``(h, k, l)``.
EULER_VERTICAL_GROUP = {
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
    "sixc": dict(
        solver="ad_hoc",
        geometry="sixc",
        # backend canonical: alpha, omega, chi, phi, delta, gamma
        # rename: delta -> ttheta (detector); alpha and gamma are the
        # 5-/6-circle add-ons pinned at 0 by ``bisecting_4c`` and are
        # left under their backend names.
        reals=["alpha", "omega", "chi", "phi", "ttheta", "gamma"],
        mode="bisecting_4c",
    ),
    "diffcalc": dict(
        solver="diffcalc",
        geometry="diffcalc_4S_2D",
        reals=["mu", "ttheta", "nu", "omega", "chi", "phi"],
        mode="4S+2D bisect_eta_fixed nu_fixed",
    ),
}

# Eulerian horizontal four-circle bisecting cross-validation group.
#
# Reference: ``hkl_soleil/E4CH bissector`` - per hkl_soleil naming,
# ``E4CH`` is Eulerian 4-circle horizontal-scattering-plane, the
# canonical 4-circle horizontal reference (analog of ``E4CV`` as the
# vertical reference in PR1).  ``E6C bissector_horizontal`` is the
# Eulerian 6-circle horizontal peer; PR2 incorrectly used it as the
# reference, corrected here per :issue:`78`.
#
# Each peer encodes the same physical scattering condition:
# scattering plane rotated 90 deg about the beam, bisecting condition
# ``omega = ttheta / 2`` (where ``omega`` is the user-facing name for
# whichever backend axis is the primary sample rotation in that mode),
# same physical observable for any ``(h, k, l)``.
#
# ``reals=`` lists preserve each solver's canonical axis order; only
# axis-name renames are applied.  The renames bind user-facing
# ``omega`` to the backend axis that actually moves in horizontal
# bisecting (identity for ``E4CH`` / ``fourch``, ``mu`` for ``E6C`` /
# ``psic``, ``eta`` for ``diffcalc``), and bind user-facing ``ttheta``
# to the backend detector axis (``tth`` for ``E4CH``, identity for
# ``fourch``, ``gamma`` for ``E6C``, ``nu`` for ``psic`` / ``diffcalc``).
# The remaining backend axes (``omega`` on ``E6C``, ``mu`` / ``delta``
# on ``diffcalc``) are pinned to 0 by the mode and renamed to inert
# placeholders.
EULER_HORIZONTAL_GROUP = {
    "e4ch": dict(
        solver="hkl_soleil",
        geometry="E4CH",
        reals=["omega", "chi", "phi", "ttheta"],
        mode="bissector",
    ),
    "e6c": dict(
        solver="hkl_soleil",
        geometry="E6C",
        reals=["omega", "eta", "chi", "phi", "ttheta", "delta"],
        mode="bissector_horizontal",
    ),
    "aps_polar": dict(
        solver="hkl_soleil",
        geometry="APS POLAR",
        # backend canonical: tau, mu, chi, phi, gamma, delta
        # mode writables (per hklpy2 docs): mu, chi, phi, gamma
        # rename: mu -> omega (primary sample axis), gamma -> ttheta
        # (in-plane detector); tau and delta are pinned at 0 by the
        # mode and kept under their backend names.
        reals=["tau", "omega", "chi", "phi", "ttheta", "delta"],
        mode="4-circles bissecting horizontal",
    ),
    "p09_eh2": dict(
        solver="hkl_soleil",
        geometry="PETRA3 P09 EH2",
        # backend canonical: mu, omega, chi, phi, delta, gamma
        # mode writables (per hklpy2 docs): omega, chi, phi, delta
        # rename: omega -> omega (identity primary), delta -> ttheta
        # (in-plane detector); mu and gamma are pinned at 0 by the
        # mode and kept under their backend names.  Note: although
        # ``APS POLAR`` was derived from this geometry, the two
        # disagree on which native axis is the bisecting primary
        # (POLAR: ``mu``; P09 EH2: ``omega``).
        reals=["mu", "omega", "chi", "phi", "ttheta", "gamma"],
        mode="4-circles bissecting horizontal",
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

# Kappa four-circle bisecting cross-validation group, VERTICAL plane.
#
# Each entry is a peer to ``hkl_soleil/K4CV``: kappa-axis goniometer
# where ``(komega, kappa, kphi)`` replaces the eulerian
# ``(omega, chi, phi)`` triad.  The bisecting condition in kappa
# coordinates reads ``komega = ttheta / 2`` (analog of
# ``omega = ttheta / 2`` in the eulerian groups), and the second
# reflection ``(1, 1, 0)`` is brought into the bisecting plane by a
# 90 deg ``kphi`` rotation (analog of ``phi = 90``).
#
# ``reals=`` lists preserve each solver's canonical axis order; only
# axis-name renames are applied:
#
# * ``K4CV``: ``tth -> ttheta`` (identity otherwise).
# * ``K6C``: ``delta -> ttheta`` (mu / gamma pinned to 0 by
#   ``bissector_vertical`` mode; left as backend names).
# * ``kappa4cv``: identity (canonical already uses ``ttheta``).
# * ``kappa6c``: ``delta -> ttheta`` (mu / nu pinned to 0 by
#   ``bisecting_vertical`` mode; left as backend names).
#
# ``ad_hoc/kappa4ch`` belongs in the horizontal kappa group, not
# here.  ``diffcalc`` has no kappa-axis geometry, so it does not
# participate in either kappa group.
KAPPA_VERTICAL_GROUP = {
    "k4cv": dict(
        solver="hkl_soleil",
        geometry="K4CV",
        reals=["komega", "kappa", "kphi", "ttheta"],
        mode="bissector",
    ),
    "k6c": dict(
        solver="hkl_soleil",
        geometry="K6C",
        reals=["mu", "komega", "kappa", "kphi", "gamma", "ttheta"],
        mode="bissector_vertical",
    ),
    "kappa4cv": dict(
        solver="ad_hoc",
        geometry="kappa4cv",
        reals=["komega", "kappa", "kphi", "ttheta"],
        mode="bisecting",
    ),
    "kappa6c": dict(
        solver="ad_hoc",
        geometry="kappa6c",
        reals=["mu", "komega", "kappa", "kphi", "nu", "ttheta"],
        mode="bisecting_vertical",
    ),
}

# Kappa bisecting cross-validation group, HORIZONTAL plane.
#
# Reference: ``hkl_soleil/K6C bissector_horizontal``.  Note: libhkl
# ships ``K4CV`` but **not** ``K4CH``, so the only available libhkl
# kappa-horizontal peer is the 6-circle ``K6C`` in its
# ``bissector_horizontal`` mode.  Peers: ``ad_hoc/kappa4ch
# bisecting`` (4-axis kappa horizontal) and
# ``ad_hoc/kappa6c bisecting_horizontal``.  ``diffcalc`` has no
# kappa-axis geometry.
#
# ``reals=`` lists preserve each solver's canonical axis order; only
# axis-name renames are applied:
#
# * ``K6C``: ``delta -> ttheta`` (in horizontal mode libhkl writes
#   ``mu`` and ``gamma`` as the writable bisecting axes; ``komega``,
#   ``kappa``, ``kphi`` are also writable but the mode pins them in
#   a way that requires overspecifying ``mu = tth/2`` *and*
#   ``delta = tth`` in the bootstrap to avoid a degenerate U matrix).
# * ``kappa4ch``: identity (canonical already uses ``ttheta``; no
#   ``mu`` axis - 4-axis kappa device).
# * ``kappa6c``: ``delta -> ttheta`` (same pattern as ``K6C`` but
#   ``ad_hoc``'s ``bisecting_horizontal`` mode declines some
#   asymmetric reflections; see :issue:`77`).
KAPPA_HORIZONTAL_GROUP = {
    "k6c": dict(
        solver="hkl_soleil",
        geometry="K6C",
        reals=["mu", "komega", "kappa", "kphi", "ttheta", "delta"],
        mode="bissector_horizontal",
    ),
    "kappa4ch": dict(
        solver="ad_hoc",
        geometry="kappa4ch",
        reals=["komega", "kappa", "kphi", "ttheta"],
        mode="bisecting",
    ),
    "kappa6c": dict(
        solver="ad_hoc",
        geometry="kappa6c",
        reals=["mu", "komega", "kappa", "kphi", "ttheta", "delta"],
        mode="bisecting_horizontal",
    ),
}

# Cross-validation groups.  Each group maps to its peer dict and the
# name of the reference entry within that dict; the per-group bootstrap
# recipe is selected by ``BOOTSTRAP_BY_GROUP`` below.
GROUPS = {
    "euler_vertical": dict(entries=EULER_VERTICAL_GROUP, reference="e4cv"),
    "euler_horizontal": dict(entries=EULER_HORIZONTAL_GROUP, reference="e4ch"),
    "kappa_vertical": dict(entries=KAPPA_VERTICAL_GROUP, reference="k4cv"),
    "kappa_horizontal": dict(entries=KAPPA_HORIZONTAL_GROUP, reference="k6c"),
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
    # https://github.com/prjemian/hklpy2_solvers/issues/68 - libhkl B-matrix
    # bug for cells with direct alpha != 90 deg; ad_hoc + diffcalc-core
    # agree exactly with each other and with the canonical BL1967 B,
    # libhkl is the outlier.  Affects every cell whose direct alpha
    # != 90 deg.  Currently the triclinic and trigonal-rhombohedral
    # samples meet that criterion; cubic / tetragonal / orthorhombic /
    # hexagonal-sapphire (gamma=120) / monoclinic (beta!=90, alpha=90)
    # all have alpha = 90 deg and so escape the bug.
    ("euler_vertical", "fourcv", "triclinic", (0, 0, 6)): "issue #68",
    ("euler_vertical", "psic", "triclinic", (0, 0, 6)): "issue #68",
    ("euler_vertical", "fivec", "triclinic", (0, 0, 6)): "issue #68",
    ("euler_vertical", "sixc", "triclinic", (0, 0, 6)): "issue #68",
    ("euler_vertical", "diffcalc", "triclinic", (0, 0, 6)): "issue #68",
    ("euler_horizontal", "fourch", "triclinic", (0, 0, 6)): "issue #68",
    ("euler_horizontal", "psic", "triclinic", (0, 0, 6)): "issue #68",
    ("euler_horizontal", "diffcalc", "triclinic", (0, 0, 6)): "issue #68",
    ("kappa_vertical", "kappa4cv", "triclinic", (0, 0, 6)): "issue #68",
    ("kappa_vertical", "kappa6c", "triclinic", (0, 0, 6)): "issue #68",
    ("kappa_horizontal", "kappa4ch", "triclinic", (0, 0, 6)): "issue #68",
    ("kappa_horizontal", "kappa6c", "triclinic", (0, 0, 6)): "issue #68",
    ("euler_vertical", "fourcv", "trigonal_rhombohedral", (0, 0, 6)): "issue #68",
    ("euler_vertical", "psic", "trigonal_rhombohedral", (0, 0, 6)): "issue #68",
    ("euler_vertical", "fivec", "trigonal_rhombohedral", (0, 0, 6)): "issue #68",
    ("euler_vertical", "sixc", "trigonal_rhombohedral", (0, 0, 6)): "issue #68",
    ("euler_vertical", "diffcalc", "trigonal_rhombohedral", (0, 0, 6)): "issue #68",
    ("euler_horizontal", "fourch", "trigonal_rhombohedral", (0, 0, 6)): "issue #68",
    ("euler_horizontal", "psic", "trigonal_rhombohedral", (0, 0, 6)): "issue #68",
    ("euler_horizontal", "diffcalc", "trigonal_rhombohedral", (0, 0, 6)): "issue #68",
    ("kappa_vertical", "kappa4cv", "trigonal_rhombohedral", (0, 0, 6)): "issue #68",
    ("kappa_vertical", "kappa6c", "trigonal_rhombohedral", (0, 0, 6)): "issue #68",
    ("kappa_horizontal", "kappa4ch", "trigonal_rhombohedral", (0, 0, 6)): "issue #68",
    ("kappa_horizontal", "kappa6c", "trigonal_rhombohedral", (0, 0, 6)): "issue #68",
}

# Known forward-solution gaps: parameter cases where ``forward()`` itself
# raises (typically ``NoForwardSolutions``) on a peer but its group peers
# succeed.  Marked ``xfail(strict=True)`` on *both* the round-trip and
# the cross-solver comparison tests so the gap is documented in code
# and a future fix surfaces as ``XPASS``.
#
# Note: every previously-listed gap from this repo's issues :issue:`71`
# (``ad_hoc/psic bisecting_horizontal`` asymmetric sapphire reflections)
# and :issue:`77` (``ad_hoc/kappa6c bisecting_horizontal`` multi-sample
# reflection set) was resolved upstream by ``ad_hoc_diffractometer >=
# 0.11.0`` (PR #281 / issue #280: rotation-composition order, basis-
# aware ``ub_identity``, BL1967 B-matrix orthogonalized frame); those
# cases are now covered by ``does_not_raise()`` parametrizations in the
# dedicated regression tests below.
KNOWN_FORWARD_GAPS = {
    # https://github.com/prjemian/hklpy2_solvers/issues/99 — tracked
    # while an upstream issue is opened.  ``ad_hoc`` kappa-vertical
    # bisecting modes (``kappa4cv bisecting``, ``kappa6c
    # bisecting_vertical``) decline the sapphire asymmetric reflection
    # ``(0, 1, 2)`` under ``ad_hoc_diffractometer >= 0.11.0``; the
    # same parameter cases pass under ``0.10.1``.  The other
    # kappa-vertical peer (``hkl_soleil/K4CV bissector``) and every
    # other reflection in the sapphire scan still solve.
    ("kappa_vertical", "kappa4cv", "sapphire", (0, 1, 2)): "issue #99",
    ("kappa_vertical", "kappa6c", "sapphire", (0, 1, 2)): "issue #99",
    # https://github.com/prjemian/hklpy2_solvers/issues/69 and upstream
    # https://github.com/BCDA-APS/ad_hoc_diffractometer/issues/285 -
    # three ``ad_hoc`` horizontal-bisecting modes (``fourch bisecting``,
    # ``psic bisecting_vertical``, ``kappa6c bisecting_horizontal``)
    # decline the trigonal-rhombohedral reflection ``(1, 1, 0)`` on
    # both ``ad_hoc_diffractometer 0.10.1`` and ``0.11.0``.  The
    # ``hkl_soleil`` peers (``E4CH``, ``K6C``) solve the same
    # reflection with ``|chi| ~ 51 deg`` / ``|kappa| ~ 97 deg``
    # branches that the bisecting solvers do not enumerate.
    ("euler_horizontal", "fourch", "trigonal_rhombohedral", (1, 1, 0)): "issue #69",
    ("euler_horizontal", "psic", "trigonal_rhombohedral", (1, 1, 0)): "issue #69",
    ("kappa_horizontal", "kappa6c", "trigonal_rhombohedral", (1, 1, 0)): "issue #69",
}

# CI-environment-dependent forward gaps: cases that pass locally on
# the maintainer's conda env but fail on the conda-forge env used by
# the dedicated ``cross-validation.yml`` workflow.  Marked
# ``xfail(strict=False)`` so the case xfails when it fails (CI) and
# passes silently when it passes (local) - distinct from the
# strict-xfails in ``KNOWN_FORWARD_GAPS`` because the failure mode
# depends on the package-version stack, not on the suite's own
# logic.
#
# The bootstrap-retry hardening in ``_build_simulator`` (see
# :issue:`83` and :data:`BOOTSTRAP_RETRY_ATTEMPTS`) helps for cases
# that fail at the float-determinism boundary, but does not resolve
# these three: every retry attempt produces a UB that the K6C
# ``bissector_horizontal`` mode rejects in the GitHub-Actions
# environment.  The structural root cause is still unknown and
# tracked in :issue:`83`.
CI_ENV_DEPENDENT_GAPS = {
    # https://github.com/prjemian/hklpy2_solvers/issues/83
    ("kappa_horizontal", "k6c", "triclinic", (0, 0, 6)): "issue #83",
    ("kappa_horizontal", "k6c", "triclinic", (1, 1, 0)): "issue #83",
    ("kappa_horizontal", "kappa4ch", "triclinic", (1, 1, 0)): "issue #83",
    # https://github.com/prjemian/hklpy2_solvers/issues/99 — ``kappa6c
    # bisecting_horizontal`` triclinic (1, 1, 0) now solves locally
    # under ``ad_hoc_diffractometer >= 0.11.0`` but the conda-forge CI
    # env hits the same K6C bootstrap fragility as the existing
    # :issue:`83` entries; non-strict so the case xfails on CI and
    # passes silently on local runs.
    ("kappa_horizontal", "kappa6c", "triclinic", (1, 1, 0)): "issue #99",
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

BOOTSTRAP_RETRY_ATTEMPTS = 8
"""Maximum number of seed perturbations to try when the K6C-class
``bissector_horizontal`` triclinic bootstrap produces a UB that
``forward()`` cannot solve for the bootstrap reflections.

The bootstrap recipe is empirically fragile at the float-determinism
boundary on some platforms (see :issue:`83`).  Retrying with a
perturbed nudge seed moves the bootstrap reflections off the
fragile neighbourhood and typically yields a UB that the solver's
own ``forward()`` accepts.  The retries are deterministic and
solver-agnostic; the search terminates as soon as both bootstrap
reflections forward successfully (or after this many attempts, in
which case the un-refined rough UB is kept and any downstream
``forward()`` failures fall through to existing xfail markers).
"""


def _nudges(seed_offset, count, *, extra_seed=0):
    """Return ``count`` deterministic offsets in ``[-NUDGE, +NUDGE]`` degrees.

    ``extra_seed`` is folded into the base seed (multiplied by a
    large prime so retry seeds do not collide with neighbouring
    ``seed_offset`` values) so callers can request a perturbed but
    still-deterministic sequence; see :data:`BOOTSTRAP_RETRY_ATTEMPTS`.
    """
    rng = random.Random(BOOTSTRAP_RNG_SEED + seed_offset + extra_seed * 1009)
    return [rng.uniform(-BOOTSTRAP_NUDGE_DEG, BOOTSTRAP_NUDGE_DEG) for _ in range(count)]


def _rough_vertical_positions(geometry, tth1, tth2, *, extra_seed=0):
    """Geometry-appropriate rough motor settings for vertical bootstrap.

    The vertical scattering plane contains the ``omega``/``ttheta``
    axes; ``(1, 1, 0)`` is brought into the bisecting plane by a 90 deg
    ``phi`` rotation.  Each writable bootstrap angle is nudged off the
    exact bisecting solution by a deterministic random offset bounded
    by ``BOOTSTRAP_NUDGE_DEG`` so the two reflections used for
    ``calc_UB`` are linearly independent in the (chi, phi) plane.

    ``extra_seed`` perturbs the nudge sequence so :func:`_build_simulator`
    can retry with alternate offsets when ``forward()`` rejects the
    rough UB (see :data:`BOOTSTRAP_RETRY_ATTEMPTS`).
    """
    p0 = {axis: 0.0 for axis in geometry.real_axis_names}
    p0.update(chi=10)
    p1 = dict(p0)
    p2 = dict(p0)
    d1_tth, d1_om, d2_tth, d2_om, d2_chi, d2_phi = _nudges(seed_offset=0, count=6, extra_seed=extra_seed)
    p1.update(ttheta=tth1 + d1_tth, omega=tth1 / 2 + d1_om)
    p2.update(
        ttheta=tth2 + d2_tth,
        omega=tth2 / 2 + d2_om,
        chi=p0["chi"] + d2_chi,
        phi=90 + d2_phi,
    )
    return p1, p2


def _rough_horizontal_positions(geometry, tth1, tth2, *, extra_seed=0):
    """Geometry-appropriate rough motor settings for horizontal bootstrap.

    The horizontal scattering plane is rotated 90 deg about the beam
    relative to the vertical bootstrap.  After axis renaming in
    ``EULER_HORIZONTAL_GROUP`` (primary backend axis -> ``omega``, detector
    backend axis -> ``ttheta``), the bisecting condition reads
    ``omega = ttheta / 2`` in user-facing names just like the vertical
    case.  ``(1, 1, 0)`` is brought into the horizontal Q-plane by
    ``chi = 45``, ``phi = -45``.  Each writable bootstrap angle is
    nudged off the exact bisecting solution by a deterministic random
    offset bounded by ``BOOTSTRAP_NUDGE_DEG`` so the two reflections
    used for ``calc_UB`` are linearly independent.  All other (pinned
    or non-writable) axes are left at zero so the mode constraint is
    satisfied at bootstrap.  ``extra_seed`` is forwarded to
    :func:`_nudges` to support :func:`_build_simulator` retries.
    """
    p0 = {axis: 0.0 for axis in geometry.real_axis_names}
    p1 = dict(p0)
    p2 = dict(p0)
    d1_tth, d1_om, d2_tth, d2_om, d2_chi, d2_phi = _nudges(seed_offset=1, count=6, extra_seed=extra_seed)
    p1.update(ttheta=tth1 + d1_tth, omega=tth1 / 2 + d1_om)
    p2.update(
        ttheta=tth2 + d2_tth,
        omega=tth2 / 2 + d2_om,
        chi=45 + d2_chi,
        phi=-45 + d2_phi,
    )
    return p1, p2


def _rough_kappa_vertical_positions(geometry, tth1, tth2, *, extra_seed=0):
    """Geometry-appropriate rough motor settings for vertical-kappa bootstrap.

    Kappa goniometers use ``(komega, kappa, kphi)`` instead of the
    eulerian ``(omega, chi, phi)`` triad.  The bisecting condition in
    kappa coordinates is ``komega = ttheta / 2`` with ``kappa = 0``
    reducing the kappa goniometer to a pure four-circle in this
    submanifold; ``(1, 1, 0)`` is brought into the bisecting plane by
    ``kphi = 90`` (analog of ``phi = 90``).  Each writable bootstrap
    angle EXCEPT ``kappa`` is nudged off the exact bisecting solution
    by a deterministic random offset bounded by
    ``BOOTSTRAP_NUDGE_DEG`` so the two reflections used for
    ``calc_UB`` are linearly independent.  ``kappa`` is held at 0 so
    that the bootstrap UB stays in the four-circle submanifold; this
    matters for triclinic samples where a small ``kappa`` nudge
    perturbs the UB enough that the post-bootstrap forward solution
    for ``(1, 1, 0)`` would require ``|kappa| > 100 deg`` and exceed
    the physical kappa-arm range.  Six-circle kappa peers leave the
    pinned axes (``mu``, second-detector) at zero so the
    ``bissector_vertical`` / ``bisecting_vertical`` mode constraint
    is satisfied at bootstrap.
    """
    p0 = {axis: 0.0 for axis in geometry.real_axis_names}
    p1 = dict(p0)
    p2 = dict(p0)
    d1_tth, d1_om, d2_tth, d2_om, d2_kphi = _nudges(seed_offset=2, count=5, extra_seed=extra_seed)
    p1.update(ttheta=tth1 + d1_tth, komega=tth1 / 2 + d1_om)
    p2.update(
        ttheta=tth2 + d2_tth,
        komega=tth2 / 2 + d2_om,
        kphi=90 + d2_kphi,
    )
    return p1, p2


def _rough_kappa_horizontal_positions(geometry, tth1, tth2, *, extra_seed=0):
    """Geometry-appropriate rough motor settings for horizontal-kappa bootstrap.

    The horizontal scattering plane is rotated 90 deg about the beam
    relative to the vertical kappa group.  After axis renaming in
    ``KAPPA_HORIZONTAL_GROUP``, the bisecting condition reads
    ``mu = ttheta / 2`` (6-axis kappa peers ``K6C``, ``kappa6c``) or
    ``komega = ttheta / 2`` (4-axis kappa peer ``kappa4ch``, which
    has no ``mu`` axis).  This helper dispatches on ``mu`` presence
    in ``real_axis_names``.

    libhkl's ``K6C bissector_horizontal`` mode requires
    **overspecifying** the bootstrap: it rejects the naive
    ``mu = tth/2`` recipe with a degenerate U matrix and rejects the
    ``komega = tth/2`` recipe with ``NoForwardSolutions``.  Writing
    both ``mu = tth/2`` (the user-facing primary) and the backend
    detector ``delta = tth`` simultaneously breaks the degeneracy
    and libhkl's solver then picks the canonical ``mu`` / ``gamma``
    branch.  ``ad_hoc/kappa6c`` accepts the same overspecified
    bootstrap without complaint.

    Each writable bootstrap angle EXCEPT ``kappa`` is nudged off the
    exact bisecting solution by a deterministic random offset
    bounded by ``BOOTSTRAP_NUDGE_DEG``; ``kappa`` is held at 0 for
    the same reason as in the vertical-kappa helper (a small
    ``kappa`` nudge perturbs the bootstrap UB enough that
    post-refine ``forward()`` may require ``|kappa| > 100 deg`` and
    exceed the physical kappa-arm range).
    """
    p0 = {axis: 0.0 for axis in geometry.real_axis_names}
    p1 = dict(p0)
    p2 = dict(p0)
    d1_tth, d1_om, d2_tth, d2_om, d2_kphi = _nudges(seed_offset=3, count=5, extra_seed=extra_seed)
    has_mu = "mu" in geometry.real_axis_names
    primary = "mu" if has_mu else "komega"
    p1.update(ttheta=tth1 + d1_tth)
    p1[primary] = tth1 / 2 + d1_om
    p2.update(ttheta=tth2 + d2_tth, kphi=90 + d2_kphi)
    p2[primary] = tth2 / 2 + d2_om
    if "delta" in geometry.real_axis_names:
        # libhkl K6C bissector_horizontal needs both mu and delta
        # set to break a degenerate U matrix; ad_hoc kappa6c accepts
        # the same overspecification harmlessly.
        p1["delta"] = tth1 + d1_tth
        p2["delta"] = tth2 + d2_tth
    return p1, p2


BOOTSTRAP_BY_GROUP = {
    "euler_vertical": _rough_vertical_positions,
    "euler_horizontal": _rough_horizontal_positions,
    "kappa_vertical": _rough_kappa_vertical_positions,
    "kappa_horizontal": _rough_kappa_horizontal_positions,
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

    The bootstrap is retried with perturbed nudge seeds when
    ``forward()`` rejects the resulting rough UB for both bootstrap
    reflections (see :data:`BOOTSTRAP_RETRY_ATTEMPTS` and :issue:`83`).
    The retry loop is solver-agnostic and uses no solver-private
    knowledge of UB basis conventions, so it is safe to apply
    uniformly across ``hkl_soleil`` / ``ad_hoc`` / ``diffcalc``
    backends.
    """
    kwargs = dict(entry_info)
    mode = kwargs.pop("mode")
    sim = hklpy2.creator(**kwargs)
    sim.core.mode = mode
    sim.add_sample(**sample_dict)
    # Per-axis constraint widening.  PR1/PR2 chose ``chi: [-100, 100]``
    # / ``phi: [-120, 120]`` deliberately - libhkl's ``bissector`` mode
    # picks different solution branches at wider ranges, so the
    # eulerian groups must keep those bounds.  Kappa peers use
    # ``(komega, kappa, kphi)`` instead; ``kappa`` is constrained to
    # ``[-100, 100] deg`` to match the physical range of typical
    # kappa-arm goniometers.  Apply each only if the axis exists on
    # this solver.
    _CONSTRAINTS = {
        "chi": (-100, 100),
        "phi": (-120, 120),
        "kappa": (-100, 100),
        "kphi": (-180, 180),
        "komega": (-180, 180),
    }
    for axis_name, limits in _CONSTRAINTS.items():
        if axis_name in sim.core.constraints:
            sim.core.constraints[axis_name].limits = limits

    tth1 = _bragg_two_theta(sim, *HKL_BOOTSTRAP_1)
    tth2 = _bragg_two_theta(sim, *HKL_BOOTSTRAP_2)
    bootstrap = BOOTSTRAP_BY_GROUP[group_name]

    # Bootstrap with retry: the K6C ``bissector_horizontal`` triclinic
    # path can yield a rough UB that ``forward()`` rejects on some
    # platforms (:issue:`83`).  Try a sequence of deterministic
    # nudge perturbations; accept the first attempt whose rough UB
    # forwards both bootstrap reflections.  If no attempt succeeds,
    # keep the last attempt's UB and let any downstream failures
    # surface through existing xfail markers.
    p1 = p2 = r1 = r2 = None
    f1 = f2 = None
    for attempt in range(BOOTSTRAP_RETRY_ATTEMPTS):
        p1, p2 = bootstrap(sim, tth1, tth2, extra_seed=attempt)
        r1 = sim.add_reflection(HKL_BOOTSTRAP_1, p1, name="r1", replace=True)
        r2 = sim.add_reflection(HKL_BOOTSTRAP_2, p2, name="r2", replace=True)
        sim.core.calc_UB(r1, r2)
        try:
            f1 = sim.forward(*HKL_BOOTSTRAP_1)
        except NoForwardSolutions:
            f1 = None
        try:
            f2 = sim.forward(*HKL_BOOTSTRAP_2)
        except NoForwardSolutions:
            f2 = None
        if f1 is not None and f2 is not None:
            break  # rough UB is viable; proceed to refine

    # Refine: replace each reflection with the angles ``forward()`` picks
    # at the rough UB, then recompute.  Skip the refine step when
    # ``forward()`` returns the same position as the rough estimate,
    # since hklpy2 rejects duplicate reflections.  ``f1`` / ``f2``
    # may still be ``None`` after the retry loop for solvers that
    # genuinely cannot forward the bootstrap reflections at this
    # geometry/mode (e.g. ``ad_hoc/kappa6c bisecting_horizontal``
    # per :issue:`77`); those cases are tracked by ``KNOWN_FORWARD_GAPS``.
    refined = False
    if f1 is not None and not _same_position(p1, f1):
        r1 = sim.add_reflection(HKL_BOOTSTRAP_1, f1, name="r1", replace=True)
        refined = True
    if f2 is not None and not _same_position(p2, f2):
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
      both round-trip and cross-solver tests must strict-xfail.
    * ``CI_ENV_DEPENDENT_GAPS`` applies when the case is known to
      fail only under specific package-version stacks.  Non-strict so
      the case xfails when it fails and passes silently when it
      passes - the suite tolerates both behaviours until the
      underlying version-sensitivity is resolved.  The
      bootstrap-retry hardening in :func:`_build_simulator` reduces
      the false-positive surface area but does not resolve every
      case (see :issue:`83`).
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
    elif key in CI_ENV_DEPENDENT_GAPS:
        marks = (
            pytest.mark.xfail(
                strict=False,
                reason=f"CI-env-dependent forward gap ({CI_ENV_DEPENDENT_GAPS[key]})",
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
            dict(group="euler_vertical", entry="fourcv", sample="cubic", hkl=(100, 0, 0)),
            pytest.raises(SolverError, match="cannot be reached"),
            id="unreachable-euler_vertical-fourcv-cubic-100_0_0",
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
            dict(group="euler_vertical", entry="NOT_A_PEER", sample="cubic", hkl=(0, 0, 6)),
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


# ---------------------------------------------------------------------------
# Issue #71 broader-pattern regression
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "parms, context",
    [
        pytest.param(
            dict(hkl=(0, 0, 3)),
            does_not_raise(),
            id="symmetric-003-solves",
        ),
        pytest.param(
            dict(hkl=(0, 0, 6)),
            does_not_raise(),
            id="symmetric-006-solves",
        ),
        pytest.param(
            dict(hkl=(1, 1, 0)),
            does_not_raise(),
            id="symmetric-110-solves",
        ),
        pytest.param(
            dict(hkl=(1, 1, 3)),
            does_not_raise(),
            id="symmetric-113-solves",
        ),
        pytest.param(
            dict(hkl=(1, 1, 6)),
            does_not_raise(),
            id="symmetric-116-solves",
        ),
        pytest.param(
            dict(hkl=(0, 1, 1)),
            does_not_raise(),
            id="asymmetric-011-solves",
        ),
        pytest.param(
            dict(hkl=(0, 1, 2)),
            does_not_raise(),
            id="asymmetric-012-solves",
        ),
        pytest.param(
            dict(hkl=(0, 2, 1)),
            does_not_raise(),
            id="asymmetric-021-solves",
        ),
        pytest.param(
            dict(hkl=(1, 0, 1)),
            does_not_raise(),
            id="asymmetric-101-solves",
        ),
        pytest.param(
            dict(hkl=(1, 0, 2)),
            does_not_raise(),
            id="asymmetric-102-solves",
        ),
        pytest.param(
            dict(hkl=(1, 0, 4)),
            does_not_raise(),
            id="asymmetric-104-solves",
        ),
    ],
)
def test_psic_bisecting_horizontal_asymmetric_pattern(parms, context, simulators):
    """``ad_hoc/psic bisecting_horizontal`` solves symmetric and asymmetric sapphire reflections.

    Regression for :issue:`71` (closed upstream as
    ``BCDA-APS/ad_hoc_diffractometer#275``, fixed in
    ``ad_hoc_diffractometer >= 0.11.0`` via PR #281 / issue #280:
    rotation-composition order, basis-aware ``ub_identity``, BL1967
    B-matrix orthogonalized frame).  Before the fix the
    ``bisecting_horizontal`` mode on ``ad_hoc/psic`` could not solve
    sapphire reflections whose Miller indices had ``h`` or ``k``
    nonzero with ``h != k``, while the three peers in
    ``EULER_HORIZONTAL_GROUP`` (``hkl_soleil/E6C``,
    ``ad_hoc/fourch``, ``diffcalc/diffcalc_4S_2D``) solved every
    reflection in this scan to within ``0.001 deg``.

    The test now asserts ``does_not_raise()`` for every reflection in
    the scan, including the six asymmetric ones that previously
    raised :class:`hklpy2.exceptions.NoForwardSolutions`.  Kept as a
    dedicated regression so any future re-introduction of the gap
    fails the suite directly.
    """
    with context:
        sim = simulators[("euler_horizontal", "psic", "sapphire")]
        sim.forward(*parms["hkl"])


# ---------------------------------------------------------------------------
# Issue #77 broader-pattern regression
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "parms, context",
    [
        # cubic: pattern - (0,0,l) for l>=3 and (h,h,l) for h>=1 with
        # l>=3 work; single-index and (h,h,0) / (h,h,1) fail.
        pytest.param(
            dict(sample="cubic", hkl=(0, 0, 3)),
            does_not_raise(),
            id="cubic-003-solves",
        ),
        pytest.param(
            dict(sample="cubic", hkl=(0, 0, 6)),
            does_not_raise(),
            id="cubic-006-solves",
        ),
        pytest.param(
            dict(sample="cubic", hkl=(1, 1, 3)),
            does_not_raise(),
            id="cubic-113-solves",
        ),
        pytest.param(
            dict(sample="cubic", hkl=(1, 1, 6)),
            does_not_raise(),
            id="cubic-116-solves",
        ),
        pytest.param(
            dict(sample="cubic", hkl=(0, 0, 1)),
            does_not_raise(),
            id="cubic-001-solves",
        ),
        pytest.param(
            dict(sample="cubic", hkl=(1, 0, 0)),
            pytest.raises(NoForwardSolutions),
            id="cubic-100-known-gap",
        ),
        pytest.param(
            dict(sample="cubic", hkl=(1, 1, 0)),
            does_not_raise(),
            id="cubic-110-solves",
        ),
        pytest.param(
            dict(sample="cubic", hkl=(0, 1, 1)),
            does_not_raise(),
            id="cubic-011-solves",
        ),
        # sapphire: largest failure set; fewer reflections solve at all.
        pytest.param(
            dict(sample="sapphire", hkl=(0, 1, 2)),
            does_not_raise(),
            id="sapphire-012-solves",
        ),
        pytest.param(
            dict(sample="sapphire", hkl=(1, 1, 3)),
            does_not_raise(),
            id="sapphire-113-solves",
        ),
        pytest.param(
            dict(sample="sapphire", hkl=(0, 0, 6)),
            does_not_raise(),
            id="sapphire-006-solves",
        ),
        pytest.param(
            dict(sample="sapphire", hkl=(1, 1, 0)),
            does_not_raise(),
            id="sapphire-110-solves",
        ),
        pytest.param(
            dict(sample="sapphire", hkl=(1, 1, 6)),
            does_not_raise(),
            id="sapphire-116-solves",
        ),
        # triclinic: smallest failure set within the curated probes.
        pytest.param(
            dict(sample="triclinic", hkl=(0, 0, 3)),
            does_not_raise(),
            id="triclinic-003-solves",
        ),
        pytest.param(
            dict(sample="triclinic", hkl=(0, 0, 6)),
            does_not_raise(),
            id="triclinic-006-solves",
        ),
        pytest.param(
            dict(sample="triclinic", hkl=(0, 1, 2)),
            does_not_raise(),
            id="triclinic-012-solves",
        ),
        pytest.param(
            dict(sample="triclinic", hkl=(1, 0, 1)),
            does_not_raise(),
            id="triclinic-101-solves",
        ),
        pytest.param(
            dict(sample="triclinic", hkl=(1, 1, 0)),
            does_not_raise(),
            id="triclinic-110-solves",
        ),
    ],
)
def test_kappa6c_bisecting_horizontal_reflection_pattern(parms, context, simulators):
    """``ad_hoc/kappa6c bisecting_horizontal`` reflection coverage.

    Regression for :issue:`77` (closed upstream as
    ``BCDA-APS/ad_hoc_diffractometer#276``, fixed in
    ``ad_hoc_diffractometer >= 0.11.0`` via PR #281 / issue #280:
    rotation-composition order, basis-aware ``ub_identity``, BL1967
    B-matrix orthogonalized frame).  Before the fix the
    ``bisecting_horizontal`` mode on ``ad_hoc/kappa6c`` declined
    many reflections that its two kappa-horizontal peers
    (``hkl_soleil/K6C bissector_horizontal`` and
    ``ad_hoc/kappa4ch bisecting``) solved cleanly.

    The mode constraints (``BisectConstraint('mu', 'nu')``,
    ``SampleConstraint('komega', 0.0)``,
    ``DetectorConstraint('delta', 0.0)``) leave only ``kappa``,
    ``kphi``, and ``nu`` writable — structurally parallel to the
    ``psic bisecting_horizontal`` constraints regressed in
    :func:`test_psic_bisecting_horizontal_asymmetric_pattern`.

    The single surviving known gap is ``cubic (1, 0, 0)``: ``Q`` is
    along the cubic ``+a``\\ * axis which lands along the lab beam
    direction under the post-#280 ``ub_identity`` and so cannot be
    rotated into the Bragg condition with the remaining three free
    axes; the reflection raises
    :class:`hklpy2.exceptions.NoForwardSolutions`.  All other
    reflections in the scan now solve.
    """
    with context:
        sim = simulators[("kappa_horizontal", "kappa6c", parms["sample"])]
        sim.forward(*parms["hkl"])

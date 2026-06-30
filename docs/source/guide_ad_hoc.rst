.. _guide_ad_hoc:

==========================================
How to use the ``ad_hoc`` solver
==========================================

This guide shows how to create a diffractometer with the ``ad_hoc``
solver, orient a crystalline sample, and compute reciprocal-space
positions.  It assumes you have already :ref:`installed <install>` the
package.

The ``ad_hoc`` solver wraps the `ad_hoc_diffractometer
<https://github.com/bcda-aps/ad_hoc_diffractometer>`_ library.  This library
provides 10 diffractometer geometries ranging from Eulerian four-circle to
six-circle, kappa, and surface configurations.  See :ref:`geometries.ad_hoc` for
the full list.

Create a diffractometer
-----------------------

**Four-circle vertical** (the default geometry):

.. code-block:: python

   import hklpy2

   fourc = hklpy2.creator(
       solver="ad_hoc",
       geometry="fourcv",
       name="fourc",
   )

The object ``fourc`` has four real axes (``omega``, ``chi``, ``phi``,
``ttheta``) and three pseudo axes (``h``, ``k``, ``l``).

**Six-circle (psic)**:

.. code-block:: python

   psic = hklpy2.creator(
       solver="ad_hoc",
       geometry="psic",
       name="psic",
   )

**Kappa geometry** (set the kappa tilt angle via ``solver_kwargs``):

.. code-block:: python

   kappa = hklpy2.creator(
       solver="ad_hoc",
       geometry="kappa4cv",
       name="kappa",
       solver_kwargs={"kappa_alpha_deg": 50},
   )

Set the crystal lattice
-----------------------

.. code-block:: python

   fourc.add_sample(name="silicon", a=hklpy2.SI_LATTICE_PARAMETER)
   fourc.beam.wavelength.put(1.0)

Add orientation reflections
---------------------------

Provide two reflections measured at known motor positions:

.. code-block:: python

   import math

   theta = math.degrees(math.asin(1.0 / (2 * 5.431)))
   tth = 2 * theta

   r1 = fourc.add_reflection(
       pseudos={"h": 1, "k": 0, "l": 0},
       reals={"omega": theta, "chi": 0, "phi": 0, "ttheta": tth},
       wavelength=1.0,
       name="r1",
   )
   r2 = fourc.add_reflection(
       pseudos={"h": 0, "k": 1, "l": 0},
       reals={"omega": theta, "chi": 0, "phi": 90, "ttheta": tth},
       wavelength=1.0,
       name="r2",
   )

Calculate the UB matrix
-----------------------

.. code-block:: python

   fourc.core.calc_UB(r1, r2)

Choose an operating mode
------------------------

The default mode for ``fourcv`` is ``bisecting``.  To change it:

.. code-block:: python

   fourc.core.mode = "fixed_phi"

See :ref:`geometries.ad_hoc` for the full mode tables for each geometry.

Compute motor positions (forward)
---------------------------------

.. code-block:: python

   fourc.forward(1, 0, 0)

This returns a single chosen motor-position solution for the given
``(h, k, l)`` (an ``Hklpy2DiffractometerRealPos``).  The underlying
solver's ``forward()`` may return multiple solutions; the
diffractometer picks one according to the policy assigned to
``fourc._forward_solution`` (defaults to
:func:`hklpy2.utils.pick_first_solution`).  The complete list of
solutions can be returned from ``fourc.core.forward((1, 0, 0))``.
See the upstream hklpy2 guide `How to Choose the Default forward()
Solution
<https://blueskyproject.io/hklpy2/guides/how_forward_solution.html>`_
for details.

.. tip::

   The two call shapes differ: ``fourc.forward(1, 0, 0)`` takes
   ``h``, ``k``, ``l`` as separate positional arguments, while
   ``fourc.core.forward((1, 0, 0))`` takes a **single** sequence
   (tuple / list / ndarray) or dict (e.g. ``{"h": 1, "k": 0, "l": 0}``).

Compute (h, k, l) from motor positions (inverse)
-------------------------------------------------

.. code-block:: python

   fourc.inverse(fourc.real_position)

This returns the ``(h, k, l)`` values computed from the supplied
motor positions.  ``fourc.real_position`` is the current readout of
all real axes; pass a different set of values to compute ``(h, k, l)``
at a hypothetical position instead.

Derived quantities (ψ, incidence, emergence, n_az, OMEGA)
---------------------------------------------------------

``AdHocSolver`` exposes the six derived-quantity helpers from
``ad_hoc_diffractometer.reference`` as methods, so users do not need
to reach into ``solver._geom``:

.. list-table::
   :header-rows: 1
   :widths: 20 40 40

   * - Method
     - Returns
     - Geometry prerequisite
   * - ``psi_angle(angles=None)``
     - Azimuthal angle ψ (deg) from motors
     - ``azimuth`` set
   * - ``incidence_angle(angles=None)``
     - Incidence angle (deg)
     - ``surface_normal`` set
   * - ``emergence_angle(angles=None)``
     - Emergence angle (deg)
     - ``surface_normal`` set
   * - ``naz_angle(angles=None)``
     - Lab-frame azimuthal angle of n̂ (deg)
     - ``surface_normal`` set
   * - ``omega_pseudo(angles=None)``
     - SPEC ``OMEGA`` pseudo-angle (deg)
     - none
   * - ``natural_psi(h, k, l)``
     - Natural ψ (deg) from UB; ``None`` if undefined
     - ``azimuth`` set

``angles`` may be a dict keyed by real-axis name (any subset); ``None``
(default) uses the geometry's current angles.  Unknown axis names raise
:class:`~hklpy2.exceptions.SolverError`; a non-dict input raises
``TypeError``.

The reference vectors ``azimuth`` and ``surface_normal``
are still configured on the underlying geometry object:

.. code-block:: python

   import hklpy2

   psic2 = hklpy2.creator(name="psic2", geometry="psic", solver="ad_hoc")
   solver = psic2.core.solver
   solver._geom.azimuth = (0, 0, 1)
   solver._geom.surface_normal = (1, 1, 6)
   solver._geom.wavelength = 1.0

   angles = dict(mu=0, eta=20, chi=30, phi=15, nu=0, delta=40)
   solver.set_reals(angles)

   psi = solver.psi_angle(angles)
   incidence = solver.incidence_angle(angles)
   emergence = solver.emergence_angle(angles)
   naz = solver.naz_angle(angles)
   omega = solver.omega_pseudo(angles)
   natural = solver.natural_psi(1, 1, 1)

See the upstream
`ad_hoc_diffractometer.reference <https://bcda-aps.github.io/ad_hoc_diffractometer/latest/api/reference.html>`_
module for the mathematical definitions.

.. _guide_ad_hoc.reference_vector:

Set the reference vector (n̂)
------------------------------

Modes that involve a surface normal or an azimuthal reference (for
example ``fixed_psi``, ``fixed_incidence_vertical``, ``zaxis``,
``reflectivity``) require an external direction vector.  In every
per-mode table that vector is shown as **n̂** (rendered as the
``n_hat`` key in the mode's ``extras``), but **n̂ is a documentation
placeholder, not a settable input**: the actual vector lives on the
underlying geometry object, on one of two attributes selected by the
mode's reference constraint.

.. list-table:: Which geometry attribute does the active mode read?
   :header-rows: 1
   :widths: 35 30 35

   * - Mode reference constraint
     - Geometry attribute
     - Set with
   * - ``incidence``, ``emergence``, ``specular``
     - ``surface_normal``
     - ``solver._geom.surface_normal = (h, k, l)``
   * - ``psi``, ``naz``
     - ``azimuth``
     - ``solver._geom.azimuth = (h, k, l)``
   * - ``omega`` (SPEC pseudo-angle)
     - (none required)
     - —

To discover which attribute the active mode needs, ask the geometry
directly:

.. code-block:: python

   psic2.core.mode = "fixed_incidence_vertical"
   attr = psic2.core.solver._geom.required_reference_vector
   # attr is 'surface_normal' for this mode; 'azimuth'
   # for psi / naz modes; None when the active mode requires no
   # reference vector.

Two ways to set the vector
~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Through the** ``extras`` **dict** — the ``n_hat`` extra routes to
whichever attribute the active mode requires
(``surface_normal`` for surface modes, ``azimuth`` for psi / naz
modes), so it works for every reference-constraint mode:

.. code-block:: python

   psic2.core.extras = {"n_hat": (0, 0, 1)}

**Directly on the geometry** — required for ``azimuth``;
also works for ``surface_normal``:

.. code-block:: python

   psic2.core.solver._geom.surface_normal = (0, 0, 1)
   psic2.core.solver._geom.azimuth = (1, 0, 0)

The argument is a length-3 sequence of Miller indices.  ``(0, 0, 0)``
is rejected with ``ValueError``; the default is ``None`` (not set).
Clear an attribute by assigning ``None``.

.. important::

   You **must** set the reference vector *before* calling
   :meth:`~hklpy2_solvers.ad_hoc_solver.AdHocSolver.forward`.  A
   reference-constraint mode *is* implemented, but it is not **ready**
   to solve until its reference vector (``n̂``) is supplied — that extra
   information is part of the mode's definition.  A premature
   ``forward()`` therefore raises::

      SolverError: forward(): mode 'fixed_psi_vertical' for geometry
      'psic' requires the reference vector to be set first.  Set the
      'psi' reference direction via the 'n_hat' extra, ...

   Set ``n_hat`` (or the geometry attribute directly) using either
   recipe above, then call ``forward()`` again.  See :issue:`125`.

.. caution::

   ``ad_hoc_diffractometer >= 0.11.1`` emits a ``UserWarning`` when
   ``cs.extras["n_hat"]`` is overwritten directly with a real value
   (the assignment has no effect on :meth:`forward`).  Use one of the
   two recipes above instead; both bypass the placeholder.

See the upstream
`Surface Geometry and the Reference Vector
<https://bcda-aps.github.io/ad_hoc_diffractometer/latest/howto/surface.html>`_
how-to for the full mathematical background.

.. _guide_ad_hoc.constraint_overrides:

Override a fixed-axis default value
------------------------------------

Each ``fixed_<axis>`` mode (for example ``fourcv`` ``fixed_chi``,
``psic`` ``fixed_chi_vertical``, ``fixed_incidence_fixed_chi_fixed_phi``)
carries a default scalar value baked into the geometry's YAML
definition.  Constraint values are immutable, so changing a default
replaces the underlying
:class:`~ad_hoc_diffractometer.mode.ConstraintSet` rather than mutating
it in place.

Use :meth:`~hklpy2_solvers.ad_hoc_solver.AdHocSolver.update_mode_constraints`
to override one or more defaults without touching solver internals.

Override a single sample-stage default:

.. code-block:: python

   psic2.core.solver.update_mode_constraints("fixed_chi_vertical", chi=45.0)
   psic2.core.mode = "fixed_chi_vertical"

Override several stages at once on a multi-fix mode:

.. code-block:: python

   psic2.core.solver.update_mode_constraints(
       "fixed_incidence_fixed_chi_fixed_phi",
       chi=15.0, phi=30.0, incidence=5.0,
   )

Operate on the currently active mode by omitting ``mode_name``:

.. code-block:: python

   psic2.core.solver.mode = "fixed_chi_vertical"
   psic2.core.solver.update_mode_constraints(chi=10.0)

(Assigning to ``psic2.core.solver.mode`` updates the adapter
synchronously, which the active-mode shortcut requires.
``psic2.core.mode = ...`` is cached by hklpy2's
:class:`~hklpy2.ops.Core` and pushed to the solver on the next
``update_solver()``, so it is not seen by
``update_mode_constraints`` until a ``forward()`` runs.)

Unknown mode names, unknown constraint names, and values rejected by
the underlying library all raise :class:`~hklpy2.exceptions.SolverError`
with a descriptive message.

Persistent overrides vs. per-call reference scalars
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Two distinct routes touch reference-constraint scalars
(``psi``, ``incidence``, ``emergence``) on modes that expose them:

* :meth:`~hklpy2_solvers.ad_hoc_solver.AdHocSolver.update_mode_constraints`
  is the **persistent** route — the new value becomes the mode's
  default for every subsequent ``forward()`` call until overridden
  again.
* The ``diff.core.extras = {"psi": ...}`` setter is the **per-call**
  route — values come from hklpy2's Core and are pushed to the solver
  on the next ``update_solver()``.

For sample-stage constraints (``chi``, ``phi``, ``mu``, ``eta`` …)
``update_mode_constraints`` is the only route; those names are not
exposed through the ``extras`` interface.

See the upstream
`Work with Constraints and Diffraction Modes
<https://bcda-aps.github.io/ad_hoc_diffractometer/latest/howto/constraints.html>`_
how-to for the full constraint-system background.

Available geometries at a glance
---------------------------------

.. list-table::
   :header-rows: 1
   :widths: 20 40 10 30

   * - Geometry
     - Real axes
     - Modes
     - Default mode
   * - :ref:`fourcv <geometry.fourcv>`
     - omega, chi, phi, ttheta
     - 6
     - bisecting
   * - :ref:`fourch <geometry.fourch>`
     - omega, chi, phi, ttheta
     - 6
     - bisecting
   * - :ref:`psic <geometry.psic>`
     - mu, eta, chi, phi, nu, delta
     - 24
     - bisecting_vertical
   * - :ref:`sixc <geometry.sixc>`
     - alpha, omega, chi, phi, delta, gamma
     - 6
     - bisecting_4c
   * - :ref:`fivec <geometry.fivec>`
     - mu, omega, chi, phi, ttheta
     - 5
     - bisecting_4c
   * - :ref:`kappa4cv <geometry.kappa4cv>`
     - komega, kappa, kphi, ttheta
     - 7
     - bisecting
   * - :ref:`kappa4ch <geometry.kappa4ch>`
     - komega, kappa, kphi, ttheta
     - 6
     - bisecting
   * - :ref:`kappa6c <geometry.kappa6c>`
     - mu, komega, kappa, kphi, nu, delta
     - 14
     - bisecting_vertical
   * - :ref:`zaxis <geometry.zaxis>`
     - alpha, Z, delta, gamma
     - 2
     - zaxis
   * - :ref:`s2d2 <geometry.s2d2>`
     - mu, Z, nu, delta
     - 2
     - fixed_mu

Register a custom YAML geometry
-------------------------------

Since ``ad_hoc_diffractometer`` 0.10.0 (issue
`#267 <https://github.com/bcda-aps/ad_hoc_diffractometer/issues/267>`_),
geometries are described in declarative YAML files.  You can extend the
``ad_hoc`` solver with your own geometry by registering a YAML file
**before** creating the diffractometer.  The
:class:`~hklpy2_solvers.ad_hoc_solver.AdHocSolver` discovers geometries
dynamically from the library's registry, so no wrapper change is
required.

.. code-block:: python

   import ad_hoc_diffractometer as ahd
   import hklpy2

   # Register a YAML geometry from disk under the name 'mybeamline'.
   ahd.register_geometry_file("/path/to/mybeamline.yml", name="mybeamline")

   # Or load and inspect without registering:
   geom = ahd.load_geometry_file("/path/to/mybeamline.yml")

   # The new geometry is now discoverable through the ad_hoc solver.
   diff = hklpy2.creator(
       solver="ad_hoc",
       geometry="mybeamline",
       name="mybeamline",
   )

The ``name`` argument is optional; when omitted, the geometry is
registered under the ``name:`` field declared inside the YAML file.
See the
`ad_hoc_diffractometer schema
<https://bcda-aps.github.io/ad_hoc_diffractometer/latest/reference/declarative_geometry_schema.html>`_
for the YAML format.

Third-party packages can alternatively contribute geometries via the
``"ad_hoc_diffractometer.geometries"`` entry-point group; those are
discovered automatically the first time
:func:`ad_hoc_diffractometer.list_geometries` is called.

Persistence across ``export()`` / ``simulator_from_config()``
-------------------------------------------------------------

User-registered geometries and modifications to built-in
geometries (e.g. modes added at runtime) survive a save/restore
cycle when the diffractometer is reconstructed via
:func:`hklpy2.simulator_from_config` (see :issue:`108`).
:meth:`AdHocSolver._metadata
<hklpy2_solvers.ad_hoc_solver.AdHocSolver._metadata>` writes a
``geometry_state`` snapshot into the ``solver:`` block of the
YAML when the live geometry differs from a fresh reference, and
``simulator_from_config()`` forwards it as a ``solver_kwargs``
entry that :meth:`AdHocSolver.__init__` replays via
:meth:`ad_hoc_diffractometer.AdHocDiffractometer.from_dict`:

.. code-block:: python

   # Suppose `diff` is an AdHoc-backed diffractometer with a
   # custom mode added to its psic geometry at runtime.  See
   # /path/to/mybeamline.yml for the full registration example
   # above; here we focus on the round-trip pattern.
   diff.export("diff.yaml")
   ...
   import hklpy2
   diff2 = hklpy2.simulator_from_config("diff.yaml")
   # The custom mode (and any other in-memory modifications to
   # the geometry's modes table) is back in diff2's solver.

Vanilla built-in geometries with no modifications round-trip
cleanly without any extra payload in the YAML.

.. note::

   ``geometry_state`` carries the geometry structure (stages,
   modes, basis, cut points, etc.) but omits the
   ``samples``, ``active_sample``, and ``wavelength`` fields:
   those are managed independently by hklpy2 and are restored
   through the dedicated ``samples:`` / ``beam:`` blocks to
   avoid double-restore.
   :meth:`hklpy2.diffract.DiffractometerBase.restore` does *not*
   re-create the underlying solver, so
   :func:`~hklpy2.simulator_from_config` is the supported entry
   point for full restoration.  ``hklpy2.Core`` also caches the
   active mode; call ``diffractometer.forward(...)`` (or
   ``diffractometer.core.update_solver()``) once after setting
   ``core.mode`` before ``export()`` so the saved ``mode:`` field
   reflects the current value.

.. seealso::

   - :ref:`geometries.ad_hoc` — full reference for all geometries and modes
   - :ref:`howto_benchmark` — measure solver throughput
   - `hklpy2 user guide <https://blueskyproject.io/hklpy2/>`_ — full
     hklpy2 documentation

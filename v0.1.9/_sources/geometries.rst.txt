.. _geometries:

==========
Geometries
==========

Each solver registered under the ``hklpy2.solver`` entry-point group
exposes one or more named geometries.  The geometry name is passed to
the solver when it is instantiated by hklpy2.

.. _geometry.diffcalc_4S_2D:

diffcalc solver
---------------

:class:`~hklpy2_solvers.diffcalc_solver.DiffcalcSolver`

Wraps `diffcalc-core <https://github.com/DiamondLightSource/diffcalc-core>`_
(You 1999).

.. list-table:: ``diffcalc_4S_2D`` geometry
   :header-rows: 1
   :widths: 20 80

   * - Property
     - Value
   * - Geometry name
     - ``diffcalc_4S_2D``
   * - Real axes
     - ``mu``, ``delta``, ``nu``, ``eta``, ``chi``, ``phi``
   * - Pseudo axes
     - ``h``, ``k``, ``l``
   * - Reference
     - H. You, *J. Appl. Cryst.* **32**, 614 (1999)

Operating modes
~~~~~~~~~~~~~~~

The diffcalc solver selects three diffractometer constraints to fix for
each operating mode.  This geometry has no extra parameters
(``extras`` is always ``{}``).  The axes computed by ``forward()``
(``axes_w``) are all real axes not listed as fixed constraints; the
remaining axes are held constant (``axes_c``, derived by hklpy2).

.. list-table::
   :header-rows: 1
   :widths: 50 50

   * - Mode name
     - Fixed constraints
   * - ``4S+2D mu_fixed a_eq_b delta_fixed``
     - delta=0, a_eq_b, mu=0
   * - ``4S+2D mu_fixed a_eq_b nu_fixed``
     - nu=0, a_eq_b, mu=0
   * - ``4S+2D eta_fixed a_eq_b delta_fixed``
     - delta=0, a_eq_b, eta=0
   * - ``4S+2D phi_fixed psi_fixed nu_fixed``
     - nu=0, psi=0, phi=0
   * - ``4S+2D chi_phi_fixed delta_fixed``
     - delta=0, chi=0, phi=0
   * - ``4S+2D mu_eta_fixed delta_fixed``
     - delta=0, mu=0, eta=0
   * - ``4S+2D mu_phi_fixed delta_fixed``
     - delta=0, mu=0, phi=0
   * - ``4S+2D mu_chi_fixed nu_fixed``
     - nu=0, mu=0, chi=0
   * - ``4S+2D eta_phi_fixed nu_fixed``
     - nu=0, eta=0, phi=0
   * - ``4S+2D eta_chi_fixed nu_fixed``
     - nu=0, eta=0, chi=0
   * - ``4S+2D bisect_mu_fixed delta_fixed``
     - delta=0, bisect, mu=0
   * - ``4S+2D bisect_eta_fixed nu_fixed``
     - nu=0, bisect, eta=0
   * - ``4S+2D bisect_omega_fixed nu_fixed``
     - nu=0, bisect, omega=0
   * - ``4S+2D chi_phi_fixed a_eq_b``
     - a_eq_b, chi=0, phi=0
   * - ``4S+2D chi_eta_fixed a_eq_b``
     - a_eq_b, chi=0, eta=0
   * - ``4S+2D chi_mu_fixed a_eq_b``
     - a_eq_b, chi=0, mu=0
   * - ``4S+2D mu_eta_fixed a_eq_b``
     - a_eq_b, mu=0, eta=0
   * - ``4S+2D mu_phi_fixed a_eq_b``
     - a_eq_b, mu=0, phi=0
   * - ``4S+2D eta_phi_fixed a_eq_b``
     - a_eq_b, eta=0, phi=0
   * - ``4S+2D eta_chi_phi_fixed``
     - eta=0, chi=0, phi=0
   * - ``4S+2D mu_chi_phi_fixed``
     - mu=0, chi=0, phi=0
   * - ``4S+2D mu_eta_phi_fixed``
     - mu=0, eta=0, phi=0
   * - ``4S+2D mu_eta_chi_fixed``
      - mu=0, eta=0, chi=0

Default mode
~~~~~~~~~~~~

The default mode is ``4S+2D mu_chi_phi_fixed`` (mu=0, chi=0, phi=0).  This is
a 3-sample mode with no reference-vector constraints, making it robust for the
widest range of reflections.  It is equivalent to a basic 4-circle geometry
operating in the vertical scattering plane.

.. note:: **Why not a bisector mode?**

   Following You (1999) Figure 1 (see also
   `diffcalc-core docs <https://diffcalc-core.readthedocs.io>`_),
   ``nu`` rotates about the vertical axis and swings the detector
   **horizontally**; ``delta`` rotates about the horizontal axis and swings
   the detector **vertically**.

   A ``bissector_vertical`` equivalent (E6C terminology) would require
   ``bisect=True`` + ``mu=0`` + ``nu=0``, but that combination is not among
   diffcalc's available modes.  A ``bissector_horizontal`` equivalent would
   require a ``mu = nu/2`` bisector condition; diffcalc's ``bisect`` constraint
   implements only ``eta = delta/2`` (vertical bisector), so that is also
   unavailable.

Mode naming convention
~~~~~~~~~~~~~~~~~~~~~~

All mode names follow the pattern ``4S+2D <constraints>``, where ``4S+2D``
identifies the You (1999) geometry and the suffix encodes the three fixed
constraints:

- ``<axis>_fixed`` or ``<ax1>_<ax2>_fixed`` — motor axis (or axes) fixed at
  zero.
- ``a_eq_b`` — reference-vector constraint: azimuthal reference equals
  scattering vector direction.  **Caution:** singular when the scattering
  vector is parallel to the reference vector; avoid as a default.
- ``bisect`` — bisector condition: ``eta = delta/2``.  Implements the vertical
  bisector only; no horizontal bisector equivalent exists in diffcalc.
- ``psi_fixed``, ``omega_fixed`` — azimuthal or omega angle fixed at zero.

Extensibility
~~~~~~~~~~~~~

The available constraint names are fixed by diffcalc-core and cannot be
changed without modifying that library.  Each constraint name has specific
mathematical implementation inside diffcalc-core's solver — the name is merely
a handle for the underlying algebra that reduces the degrees of freedom during
position calculation.  A new constraint (e.g. ``mu = nu/2``) would require
new code in diffcalc-core, not just a new entry in ``_MODES``.  From the
user's perspective the mode list is not extensible.

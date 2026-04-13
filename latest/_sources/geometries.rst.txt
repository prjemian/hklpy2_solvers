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

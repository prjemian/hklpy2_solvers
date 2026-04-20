.. _geometries:

==========
Geometries
==========

Each solver registered under the ``hklpy2.solver`` entry-point group
exposes one or more named geometries.  The geometry name is passed to
the solver when it is instantiated by hklpy2.

.. contents:: On this page
   :local:
   :depth: 2

.. _geometry.diffcalc_4S_2D:

``diffcalc`` solver
-------------------

:class:`~hklpy2_solvers.diffcalc_solver.DiffcalcSolver`

Wraps `diffcalc-core <https://github.com/DiamondLightSource/diffcalc-core>`_
(You 1999).

diffcalc_4S_2D
~~~~~~~~~~~~~~

H. You, *J. Appl. Cryst.* **32**, 614 (1999) six-circle geometry.

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
   * - Default mode
     - ``4S+2D bisect_eta_fixed nu_fixed``

Operating modes
^^^^^^^^^^^^^^^

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
^^^^^^^^^^^^

The default mode is ``4S+2D bisect_eta_fixed nu_fixed`` (bisect,
eta=0, nu=0).  This is equivalent to ``bisecting_vertical`` in E6C
terminology: scattering stays in the vertical plane with the sample
angle bisecting the detector angle (``eta = delta/2``).

.. note:: **Bisector modes**

   Following You (1999) Figure 1 (see also
   `diffcalc-core docs <https://diffcalc-core.readthedocs.io>`_),
   ``nu`` rotates about the vertical axis and swings the detector
   **horizontally**; ``delta`` rotates about the horizontal axis and swings
   the detector **vertically**.

   The ``bisect`` constraint implements ``eta = delta/2`` (vertical
   bisector).  ``4S+2D bisect_eta_fixed nu_fixed`` (bisect + eta=0 +
   nu=0) is equivalent to a ``bisecting_vertical`` mode: scattering
   stays in the vertical plane with the sample bisecting the detector
   angle.  ``4S+2D bisect_mu_fixed delta_fixed`` (bisect + mu=0 +
   delta=0) is the horizontal counterpart.

   In the mode name the *bisected sample axis* is stated; the
   corresponding *detector axis* is implied by the bisect constraint
   (``delta``).

Mode naming convention
^^^^^^^^^^^^^^^^^^^^^^

All mode names follow the pattern ``4S+2D <constraints>``, where ``4S+2D``
identifies the You (1999) geometry and the suffix encodes the three fixed
constraints:

- ``<axis>_fixed`` or ``<ax1>_<ax2>_fixed`` — motor axis (or axes) fixed at
  zero.
- ``a_eq_b`` — reference-vector constraint: azimuthal reference equals
  scattering vector direction.  **Caution:** singular when the scattering
  vector is parallel to the reference vector; avoid as a default.
- ``bisect`` — bisector condition: ``eta = delta/2``.  The bisected sample
  axis (e.g. ``eta``) is named; the detector axis (``delta``) is implied.
- ``psi_fixed``, ``omega_fixed`` — azimuthal or omega angle fixed at zero.

Extensibility
^^^^^^^^^^^^^

The available constraint names are fixed by diffcalc-core and cannot be
changed without modifying that library.  Each constraint name has specific
mathematical implementation inside diffcalc-core's solver — the name is merely
a handle for the underlying algebra that reduces the degrees of freedom during
position calculation.  A new constraint (e.g. ``mu = nu/2``) would require
new code in diffcalc-core, not just a new entry in ``_MODES``.  From the
user's perspective the mode list is not extensible.

----

.. _geometries.ad_hoc:

``ad_hoc`` solver
-----------------

:class:`~hklpy2_solvers.ad_hoc_solver.AdHocSolver`

Wraps `ad_hoc_diffractometer <https://github.com/prjemian/ad_hoc_diffractometer>`_
(Jemian 2026).

The ``ad_hoc`` solver discovers geometries dynamically from the
`ad_hoc_diffractometer <https://github.com/prjemian/ad_hoc_diffractometer>`_
library.  All geometries registered in the
library's geometry registry (including via entry points) are
automatically available.  The pseudo axes are always ``h``, ``k``, ``l``
and ``extras`` is always ``{}``.

.. _geometry.fourcv:

fourcv
~~~~~~

Busing & Levy four-circle vertical-scattering geometry.

.. list-table:: ``fourcv`` geometry
   :header-rows: 1
   :widths: 20 80

   * - Property
     - Value
   * - Geometry name
     - ``fourcv``
   * - Real axes
     - ``omega``, ``chi``, ``phi``, ``ttheta``
   * - Pseudo axes
     - ``h``, ``k``, ``l``
   * - Default mode
     - ``bisecting``

.. list-table:: ``fourcv`` operating modes
   :header-rows: 1
   :widths: 40 60

   * - Mode name
     - Constant stages
   * - ``bisecting``
     - omega
   * - ``fixed_chi``
     - chi
   * - ``fixed_phi``
     - phi
   * - ``constant_omega``
     - omega
   * - ``psi_constant``
     - *(none)*
   * - ``double_diffraction``
     - *(none)*

.. _geometry.fourch:

fourch
~~~~~~

Four-circle horizontal-scattering geometry.

.. list-table:: ``fourch`` geometry
   :header-rows: 1
   :widths: 20 80

   * - Property
     - Value
   * - Geometry name
     - ``fourch``
   * - Real axes
     - ``omega``, ``chi``, ``phi``, ``ttheta``
   * - Pseudo axes
     - ``h``, ``k``, ``l``
   * - Default mode
     - ``bisecting``

.. list-table:: ``fourch`` operating modes
   :header-rows: 1
   :widths: 40 60

   * - Mode name
     - Constant stages
   * - ``bisecting``
     - omega
   * - ``fixed_chi``
     - chi
   * - ``fixed_phi``
     - phi
   * - ``constant_omega``
     - omega
   * - ``psi_constant``
     - *(none)*
   * - ``double_diffraction``
     - *(none)*

.. _geometry.psic:

psic
~~~~

You (1999) six-circle geometry (psi-circle).

.. list-table:: ``psic`` geometry
   :header-rows: 1
   :widths: 20 80

   * - Property
     - Value
   * - Geometry name
     - ``psic``
   * - Real axes
     - ``mu``, ``eta``, ``chi``, ``phi``, ``nu``, ``delta``
   * - Pseudo axes
     - ``h``, ``k``, ``l``
   * - Default mode
     - ``bisecting_vertical``

.. list-table:: ``psic`` operating modes
   :header-rows: 1
   :widths: 40 60

   * - Mode name
     - Constant stages
   * - ``bisecting_vertical``
     - eta, mu, nu
   * - ``fixed_chi``
     - chi, eta, nu
   * - ``fixed_phi``
     - phi, eta, nu
   * - ``fixed_mu``
     - mu, eta, nu
   * - ``bisecting_horizontal``
     - mu, eta, delta
   * - ``fixed_nu``
     - nu, eta, mu
   * - ``double_diffraction_vertical``
     - mu, nu
   * - ``double_diffraction_horizontal``
     - eta, delta
   * - ``lifting_detector_mu``
     - mu, eta
   * - ``lifting_detector_phi``
     - phi, mu
   * - ``psi_constant_vertical``
     - eta, mu
   * - ``psi_constant_horizontal``
     - mu, eta

.. _geometry.sixc:

sixc
~~~~

Lohmeier & Vlieg (1993) six-circle geometry.

.. list-table:: ``sixc`` geometry
   :header-rows: 1
   :widths: 20 80

   * - Property
     - Value
   * - Geometry name
     - ``sixc``
   * - Real axes
     - ``alpha``, ``omega``, ``chi``, ``phi``, ``delta``, ``gamma``
   * - Pseudo axes
     - ``h``, ``k``, ``l``
   * - Default mode
     - ``bisecting_4c``

.. list-table:: ``sixc`` operating modes
   :header-rows: 1
   :widths: 40 60

   * - Mode name
     - Constant stages
   * - ``bisecting_4c``
     - alpha, gamma, omega
   * - ``fixed_gamma_5c``
     - gamma, alpha, omega
   * - ``fixed_alpha_5c``
     - alpha, omega, gamma
   * - ``fixed_alpha_zaxis``
     - alpha, chi
   * - ``fixed_beta_zaxis``
     - gamma, chi
   * - ``alpha_eq_beta_zaxis``
     - chi, phi

.. _geometry.fivec:

fivec
~~~~~

Five-circle geometry (four-circle with additional mu tilt).

.. list-table:: ``fivec`` geometry
   :header-rows: 1
   :widths: 20 80

   * - Property
     - Value
   * - Geometry name
     - ``fivec``
   * - Real axes
     - ``mu``, ``omega``, ``chi``, ``phi``, ``ttheta``
   * - Pseudo axes
     - ``h``, ``k``, ``l``
   * - Default mode
     - ``bisecting_4c``

.. list-table:: ``fivec`` operating modes
   :header-rows: 1
   :widths: 40 60

   * - Mode name
     - Constant stages
   * - ``bisecting_4c``
     - mu, omega
   * - ``fixed_chi``
     - mu, chi
   * - ``fixed_phi``
     - mu, phi
   * - ``fixed_mu``
     - mu, omega
   * - ``constant_omega_noncoplanar``
     - mu, omega

.. _geometry.kappa4cv:

kappa4cv
~~~~~~~~

Kappa four-circle vertical-scattering geometry.

.. list-table:: ``kappa4cv`` geometry
   :header-rows: 1
   :widths: 20 80

   * - Property
     - Value
   * - Geometry name
     - ``kappa4cv``
   * - Real axes
     - ``komega``, ``kappa``, ``kphi``, ``ttheta``
   * - Pseudo axes
     - ``h``, ``k``, ``l``
   * - Default mode
     - ``bisecting``

.. list-table:: ``kappa4cv`` operating modes
   :header-rows: 1
   :widths: 40 60

   * - Mode name
     - Constant stages
   * - ``bisecting``
     - komega
   * - ``fixed_kphi``
     - kphi
   * - ``constant_omega``
     - omega
   * - ``constant_chi``
     - chi
   * - ``constant_phi``
     - phi
   * - ``psi_constant``
     - *(none)*
   * - ``double_diffraction``
     - *(none)*

.. _geometry.kappa4ch:

kappa4ch
~~~~~~~~

Kappa four-circle horizontal-scattering geometry.

.. list-table:: ``kappa4ch`` geometry
   :header-rows: 1
   :widths: 20 80

   * - Property
     - Value
   * - Geometry name
     - ``kappa4ch``
   * - Real axes
     - ``komega``, ``kappa``, ``kphi``, ``ttheta``
   * - Pseudo axes
     - ``h``, ``k``, ``l``
   * - Default mode
     - ``bisecting``

.. list-table:: ``kappa4ch`` operating modes
   :header-rows: 1
   :widths: 40 60

   * - Mode name
     - Constant stages
   * - ``bisecting``
     - komega
   * - ``fixed_kphi``
     - kphi
   * - ``constant_omega``
     - omega
   * - ``constant_chi``
     - chi
   * - ``constant_phi``
     - phi
   * - ``psi_constant``
     - *(none)*

.. _geometry.kappa6c:

kappa6c
~~~~~~~

Kappa six-circle geometry.

.. list-table:: ``kappa6c`` geometry
   :header-rows: 1
   :widths: 20 80

   * - Property
     - Value
   * - Geometry name
     - ``kappa6c``
   * - Real axes
     - ``mu``, ``komega``, ``kappa``, ``kphi``, ``nu``, ``delta``
   * - Pseudo axes
     - ``h``, ``k``, ``l``
   * - Default mode
     - ``bisecting_vertical``

.. list-table:: ``kappa6c`` operating modes
   :header-rows: 1
   :widths: 40 60

   * - Mode name
     - Constant stages
   * - ``bisecting_vertical``
     - komega, mu, nu
   * - ``bisecting_horizontal``
     - mu, komega, delta
   * - ``fixed_kphi``
     - kphi, mu, nu
   * - ``fixed_mu``
     - mu, komega, nu
   * - ``fixed_nu``
     - nu, komega, mu
   * - ``fixed_delta``
     - delta, mu, komega
   * - ``lifting_detector_mu``
     - mu, komega
   * - ``lifting_detector_kphi``
     - kphi, mu
   * - ``psi_constant_vertical``
     - komega, mu
   * - ``psi_constant_horizontal``
     - mu, komega
   * - ``double_diffraction_vertical``
     - mu, nu
   * - ``double_diffraction_horizontal``
     - komega, delta

.. _geometry.zaxis:

zaxis
~~~~~

Z-axis surface diffraction geometry.

.. list-table:: ``zaxis`` geometry
   :header-rows: 1
   :widths: 20 80

   * - Property
     - Value
   * - Geometry name
     - ``zaxis``
   * - Real axes
     - ``alpha``, ``Z``, ``delta``, ``gamma``
   * - Pseudo axes
     - ``h``, ``k``, ``l``
   * - Default mode
     - ``zaxis`` (first available)

.. list-table:: ``zaxis`` operating modes
   :header-rows: 1
   :widths: 40 60

   * - Mode name
     - Constant stages
   * - ``zaxis``
     - *(none)*
   * - ``reflectivity``
     - *(none)*

.. _geometry.s2d2:

s2d2
~~~~

Two-sample / two-detector surface diffraction geometry.

.. list-table:: ``s2d2`` geometry
   :header-rows: 1
   :widths: 20 80

   * - Property
     - Value
   * - Geometry name
     - ``s2d2``
   * - Real axes
     - ``mu``, ``Z``, ``nu``, ``delta``
   * - Pseudo axes
     - ``h``, ``k``, ``l``
   * - Default mode
     - ``mu_fixed`` (first available)

.. list-table:: ``s2d2`` operating modes
   :header-rows: 1
   :widths: 40 60

   * - Mode name
     - Constant stages
   * - ``mu_fixed``
     - mu
   * - ``reflectivity``
     - *(none)*

Kappa geometries
~~~~~~~~~~~~~~~~

The kappa geometries (:ref:`kappa4cv <geometry.kappa4cv>`,
:ref:`kappa4ch <geometry.kappa4ch>`, :ref:`kappa6c <geometry.kappa6c>`) accept a
``kappa_alpha_deg`` keyword argument when the solver is created.  This
sets the fixed tilt angle of the kappa arm.  The default is 50 degrees.
The kappa modes ``constant_omega``, ``constant_chi``, and
``constant_phi`` constrain the *equivalent Euler* angles rather than the
physical kappa motors.

Extensibility
~~~~~~~~~~~~~

The ``ad_hoc`` solver discovers geometries dynamically from the
`ad_hoc_diffractometer <https://github.com/prjemian/ad_hoc_diffractometer>`_
library's registry.  New geometries added to
the library (including via entry points) are automatically available
without changes to the solver code.

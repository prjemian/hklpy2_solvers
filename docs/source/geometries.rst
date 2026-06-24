.. _geometries:

==========
Geometries
==========

Each solver registered under the ``hklpy2.solver`` entry-point group
exposes one or more named geometries.  The geometry name is passed to
the solver when it is instantiated by hklpy2.

.. contents:: On this page
   :local:
   :depth: 1

.. _geometries.ad_hoc:

``ad_hoc`` solver
-----------------

:class:`~hklpy2_solvers.ad_hoc_solver.AdHocSolver`

Wraps `ad_hoc_diffractometer <https://github.com/bcda-aps/ad_hoc_diffractometer>`_
(Jemian 2026).

The ``ad_hoc`` solver discovers geometries dynamically from the
`ad_hoc_diffractometer <https://github.com/bcda-aps/ad_hoc_diffractometer>`_
library.  All geometries registered in the
library's geometry registry (including via entry points) are
automatically available.  The pseudo axes are always ``h``, ``k``, ``l``.

In the per-mode tables below the ``extra(s)`` column names the
:attr:`~ad_hoc_diffractometer.diffractometer.AdHocDiffractometer.surface_normal`
or
:attr:`~ad_hoc_diffractometer.diffractometer.AdHocDiffractometer.azimuth`
attribute that the mode reads (set on the underlying geometry object),
followed by any per-call scalar extras (``psi``, ``incidence``,
``emergence``).  See :ref:`guide_ad_hoc.reference_vector` for the
recipes.

.. note::

   Reference-constraint modes (those listing ``psi``, ``incidence``,
   ``emergence``, or ``surface_normal``/``azimuth``) require
   ``ad_hoc_diffractometer >= 0.11.3`` and the corresponding reference
   vector to be set (via the ``n_hat`` extra); otherwise
   :meth:`~hklpy2_solvers.ad_hoc_solver.AdHocSolver.forward` raises
   :class:`~hklpy2.exceptions.SolverError`.

.. _geometry.fourcv:

fourcv
~~~~~~

Busing & Levy (1967) four-circle Eulerian diffractometer
(vertical scattering plane, transverse ttheta, synchrotron).

See `ad_hoc_diffractometer fourcv
<https://bcda-aps.github.io/ad_hoc_diffractometer/latest/geometries/fourcv.html>`_.

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
   :widths: 25 20 25 30

   * - Mode name
     - Constant stages
     - writable(s)
     - extra(s)
   * - ``bisecting``
     - omega
     - chi, phi, ttheta
     -
   * - ``fixed_chi``
     - chi
     - omega, phi, ttheta
     -
   * - ``fixed_phi``
     - phi
     - omega, chi, ttheta
     -
   * - ``fixed_omega``
     - omega
     - chi, phi, ttheta
     -
   * - ``fixed_psi``
     - *(none)*
     - omega, chi, phi, ttheta
     - azimuth, psi
   * - ``double_diffraction``
     - *(none)*
     - omega, chi, phi, ttheta
     - h2, k2, l2

.. _geometry.fourch:

fourch
~~~~~~

Busing & Levy (1967) four-circle Eulerian diffractometer
(horizontal scattering plane, vertical ttheta, laboratory).

See `ad_hoc_diffractometer fourch
<https://bcda-aps.github.io/ad_hoc_diffractometer/latest/geometries/fourch.html>`_.

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
   :widths: 25 20 25 30

   * - Mode name
     - Constant stages
     - writable(s)
     - extra(s)
   * - ``bisecting``
     - omega
     - chi, phi, ttheta
     -
   * - ``fixed_chi``
     - chi
     - omega, phi, ttheta
     -
   * - ``fixed_phi``
     - phi
     - omega, chi, ttheta
     -
   * - ``fixed_omega``
     - omega
     - chi, phi, ttheta
     -
   * - ``fixed_psi``
     - *(none)*
     - omega, chi, phi, ttheta
     - azimuth, psi
   * - ``double_diffraction``
     - *(none)*
     - omega, chi, phi, ttheta
     - h2, k2, l2

.. _geometry.psic:

psic
~~~~

You (1999) 4S+2D six-circle diffractometer
(transverse detector, vertical scattering plane, synchrotron).

See `ad_hoc_diffractometer psic
<https://bcda-aps.github.io/ad_hoc_diffractometer/latest/geometries/psic.html>`_.

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
   :widths: 25 20 25 30

   * - Mode name
     - Constant stages
     - writable(s)
     - extra(s)
   * - ``bisecting_vertical``
     - eta, mu, nu
     - chi, phi, delta
     -
   * - ``fixed_phi_vertical``
     - mu, nu, phi
     - eta, chi, delta
     -
   * - ``fixed_chi_vertical``
     - chi, mu, nu
     - eta, phi, delta
     -
   * - ``fixed_incidence_vertical``
     - mu, nu
     - eta, chi, phi, delta
     - surface_normal, incidence, emergence
   * - ``fixed_emergence_vertical``
     - mu, nu
     - eta, chi, phi, delta
     - surface_normal, incidence, emergence
   * - ``specular_vertical``
     - mu, nu
     - eta, chi, phi, delta
     - surface_normal, incidence, emergence
   * - ``fixed_psi_vertical``
     - mu, nu
     - eta, chi, phi, delta
     - azimuth, psi
   * - ``fixed_incidence_fixed_chi_fixed_phi``
     - chi, phi
     - mu, eta, nu, delta
     - surface_normal, incidence, emergence
   * - ``fixed_omega_vertical``
     - mu, nu
     - eta, chi, phi, delta
     -
   * - ``double_diffraction_vertical``
     - mu, nu
     - eta, chi, phi, delta
     - h2, k2, l2
   * - ``bisecting_horizontal``
     - delta, eta, mu
     - chi, phi, nu
     -
   * - ``fixed_phi_horizontal``
     - delta, eta, phi
     - mu, chi, nu
     -
   * - ``fixed_chi_horizontal``
     - chi, delta, eta
     - mu, phi, nu
     -
   * - ``fixed_incidence_horizontal``
     - delta, eta
     - mu, chi, phi, nu
     - surface_normal, incidence, emergence
   * - ``fixed_emergence_horizontal``
     - delta, eta
     - mu, chi, phi, nu
     - surface_normal, incidence, emergence
   * - ``specular_horizontal``
     - delta, eta
     - mu, chi, phi, nu
     - surface_normal, incidence, emergence
   * - ``fixed_psi_horizontal``
     - delta, eta
     - mu, chi, phi, nu
     - azimuth, psi
   * - ``fixed_omega_horizontal``
     - delta, eta
     - mu, chi, phi, nu
     -
   * - ``double_diffraction_horizontal``
     - delta, eta
     - mu, chi, phi, nu
     - h2, k2, l2
   * - ``zone_vertical``
     - mu, nu
     - eta, chi, phi, delta
     -
   * - ``zone_horizontal``
     - delta, eta
     - mu, chi, phi, nu
     -
   * - ``lifting_detector_phi``
     - chi, eta, mu
     - phi, nu, delta
     -
   * - ``lifting_detector_mu``
     - chi, eta, phi
     - mu, nu, delta
     -
   * - ``lifting_detector_eta``
     - chi, mu, phi
     - eta, nu, delta
     -

.. _geometry.sixc:

sixc
~~~~

Lohmeier & Vlieg (1993) six-circle surface diffractometer.

See `ad_hoc_diffractometer sixc
<https://bcda-aps.github.io/ad_hoc_diffractometer/latest/geometries/sixc.html>`_.

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
   :widths: 25 20 25 30

   * - Mode name
     - Constant stages
     - writable(s)
     - extra(s)
   * - ``bisecting_4c``
     - alpha, gamma, omega
     - chi, phi, delta
     -
   * - ``fixed_gamma_5c``
     - alpha, gamma, omega
     - chi, phi, delta
     -
   * - ``fixed_alpha_5c``
     - alpha, gamma, omega
     - chi, phi, delta
     -
   * - ``fixed_incidence_zaxis``
     - alpha, chi
     - omega, phi, delta, gamma
     - surface_normal, incidence, emergence
   * - ``fixed_emergence_zaxis``
     - chi, gamma
     - alpha, omega, phi, delta
     - surface_normal, incidence, emergence
   * - ``specular_zaxis``
     - chi, phi
     - alpha, omega, delta, gamma
     - surface_normal, incidence, emergence

.. _geometry.fivec:

fivec
~~~~~

Five-circle geometry (four-circle with additional mu tilt).

See `ad_hoc_diffractometer fivec
<https://bcda-aps.github.io/ad_hoc_diffractometer/latest/geometries/fivec.html>`_.

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
   :widths: 25 20 25 30

   * - Mode name
     - Constant stages
     - writable(s)
     - extra(s)
   * - ``bisecting_4c``
     - mu, omega
     - chi, phi, ttheta
     -
   * - ``fixed_chi``
     - chi, mu
     - omega, phi, ttheta
     -
   * - ``fixed_phi``
     - mu, phi
     - omega, chi, ttheta
     -
   * - ``fixed_mu``
     - mu, omega
     - chi, phi, ttheta
     -
   * - ``fixed_omega_noncoplanar``
     - mu, omega
     - chi, phi, ttheta
     -

.. _geometry.kappa4cv:

kappa4cv
~~~~~~~~

Kappa four-circle vertical-scattering geometry.

See `ad_hoc_diffractometer kappa4cv
<https://bcda-aps.github.io/ad_hoc_diffractometer/latest/geometries/kappa4cv.html>`_.

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
   :widths: 25 20 25 30

   * - Mode name
     - Constant stages
     - writable(s)
     - extra(s)
   * - ``bisecting``
     - omega (virtual)
     - komega, kappa, kphi, ttheta
     -
   * - ``fixed_kphi``
     - kphi
     - komega, kappa, ttheta
     -
   * - ``fixed_omega``
     - omega (virtual)
     - komega, kappa, kphi, ttheta
     -
   * - ``fixed_chi``
     - chi (virtual)
     - komega, kappa, kphi, ttheta
     -
   * - ``fixed_phi``
     - phi (virtual)
     - komega, kappa, kphi, ttheta
     -
   * - ``fixed_psi``
     - *(none)*
     - komega, kappa, kphi, ttheta
     - azimuth, psi
   * - ``double_diffraction``
     - *(none)*
     - komega, kappa, kphi, ttheta
     - h2, k2, l2

.. _geometry.kappa4ch:

kappa4ch
~~~~~~~~

Kappa four-circle horizontal-scattering geometry.

See `ad_hoc_diffractometer kappa4ch
<https://bcda-aps.github.io/ad_hoc_diffractometer/latest/geometries/kappa4ch.html>`_.

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
   :widths: 25 20 25 30

   * - Mode name
     - Constant stages
     - writable(s)
     - extra(s)
   * - ``bisecting``
     - omega (virtual)
     - komega, kappa, kphi, ttheta
     -
   * - ``fixed_kphi``
     - kphi
     - komega, kappa, ttheta
     -
   * - ``fixed_omega``
     - omega (virtual)
     - komega, kappa, kphi, ttheta
     -
   * - ``fixed_chi``
     - chi (virtual)
     - komega, kappa, kphi, ttheta
     -
   * - ``fixed_phi``
     - phi (virtual)
     - komega, kappa, kphi, ttheta
     -
   * - ``fixed_psi``
     - *(none)*
     - komega, kappa, kphi, ttheta
     - azimuth, psi

.. _geometry.kappa6c:

kappa6c
~~~~~~~

Kappa six-circle geometry (psic-style outer axes, transverse detector,
synchrotron).

See `ad_hoc_diffractometer kappa6c
<https://bcda-aps.github.io/ad_hoc_diffractometer/latest/geometries/kappa6c.html>`_.

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
   :widths: 25 20 25 30

   * - Mode name
     - Constant stages
     - writable(s)
     - extra(s)
   * - ``bisecting_vertical``
     - mu, nu, omega (virtual)
     - komega, kappa, kphi, delta
     -
   * - ``bisecting_horizontal``
     - delta, komega, mu
     - kappa, kphi, nu
     -
   * - ``fixed_kphi``
     - kphi, mu, nu
     - komega, kappa, delta
     -
   * - ``fixed_mu``
     - mu, nu, omega (virtual)
     - komega, kappa, kphi, delta
     -
   * - ``fixed_nu``
     - mu, nu, omega (virtual)
     - komega, kappa, kphi, delta
     -
   * - ``fixed_delta``
     - delta, komega, mu
     - kappa, kphi, nu
     -
   * - ``lifting_detector_mu``
     - komega, mu
     - kappa, kphi, nu, delta
     -
   * - ``lifting_detector_kphi``
     - kphi, mu
     - komega, kappa, nu, delta
     -
   * - ``fixed_psi_vertical``
     - mu, omega (virtual)
     - komega, kappa, kphi, nu, delta
     - azimuth, psi
   * - ``fixed_psi_horizontal``
     - komega, mu
     - kappa, kphi, nu, delta
     - azimuth, psi
   * - ``double_diffraction_vertical``
     - mu, nu
     - komega, kappa, kphi, delta
     - h2, k2, l2
   * - ``double_diffraction_horizontal``
     - delta, komega
     - mu, kappa, kphi, nu
     - h2, k2, l2
   * - ``zone_vertical``
     - mu, nu
     - komega, kappa, kphi, delta
     -
   * - ``zone_horizontal``
     - delta, komega
     - mu, kappa, kphi, nu
     -

.. _geometry.zaxis:

zaxis
~~~~~

Z-axis four-circle surface diffraction geometry
(Bloch 1985).

See `ad_hoc_diffractometer zaxis
<https://bcda-aps.github.io/ad_hoc_diffractometer/latest/geometries/zaxis.html>`_.

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
   :widths: 25 20 25 30

   * - Mode name
     - Constant stages
     - writable(s)
     - extra(s)
   * - ``zaxis``
     - *(none)*
     - alpha, Z, delta, gamma
     - surface_normal, incidence, emergence
   * - ``reflectivity``
     - *(none)*
     - alpha, Z, delta, gamma
     - surface_normal, incidence, emergence

.. _geometry.s2d2:

s2d2
~~~~

Two-sample / two-detector surface diffraction geometry
(Evans-Lutterodt & Tang 1995).

See `ad_hoc_diffractometer s2d2
<https://bcda-aps.github.io/ad_hoc_diffractometer/latest/geometries/s2d2.html>`_.

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
     - ``fixed_mu`` (first available)

.. list-table:: ``s2d2`` operating modes
   :header-rows: 1
   :widths: 25 20 25 30

   * - Mode name
     - Constant stages
     - writable(s)
     - extra(s)
   * - ``fixed_mu``
     - mu
     - Z, nu, delta
     -
   * - ``reflectivity``
     - *(none)*
     - mu, Z, nu, delta
     - surface_normal, incidence, emergence

Kappa geometries
~~~~~~~~~~~~~~~~

The kappa geometries (:ref:`kappa4cv <geometry.kappa4cv>`,
:ref:`kappa4ch <geometry.kappa4ch>`, :ref:`kappa6c <geometry.kappa6c>`) accept a
``kappa_alpha_deg`` keyword argument when the solver is created.  This
sets the fixed tilt angle of the kappa arm.  The default is 50 degrees.
The kappa modes ``fixed_omega``, ``fixed_chi``, and ``fixed_phi`` (and,
on ``kappa6c``, ``bisecting_vertical`` / ``fixed_mu`` / ``fixed_nu``)
constrain the *equivalent Euler* (virtual) angles rather than the
physical kappa motors.

Extensibility
~~~~~~~~~~~~~

The ``ad_hoc`` solver discovers geometries dynamically from the
`ad_hoc_diffractometer <https://github.com/bcda-aps/ad_hoc_diffractometer>`_
library's registry.  New geometries added to
the library (including via entry points) are automatically available
without changes to the solver code.

----



.. _geometry.diffcalc_4S_2D:

``diffcalc`` solver
-------------------

:class:`~hklpy2_solvers.diffcalc_solver.DiffcalcSolver`

Wraps `diffcalc-core <https://github.com/DiamondLightSource/diffcalc-core>`_
(You 1999).
See the `diffcalc-core documentation <https://diffcalc-core.readthedocs.io/>`_
for full details of the underlying library.

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
     - ``bisect fixed_mu fixed_nu``

Operating modes
^^^^^^^^^^^^^^^

The diffcalc solver selects three diffractometer constraints to fix for
each operating mode.  This geometry has no extra parameters
(``extras`` is always ``{}``).  The axes computed by ``forward()``
(``writable``) are all real axes not listed as fixed constraints; the
remaining axes are held constant (``axes_c``, derived by hklpy2).

.. list-table::
   :header-rows: 1
   :widths: 35 30 20 15

   * - Mode name
     - Fixed constraints
     - writable(s)
     - extra(s)
   * - ``a_eq_b fixed_delta fixed_mu``
     - delta=0, a_eq_b, mu=0
     - nu, eta, chi, phi
     -
   * - ``a_eq_b fixed_nu fixed_mu``
     - nu=0, a_eq_b, mu=0
     - delta, eta, chi, phi
     -
   * - ``a_eq_b fixed_delta fixed_eta``
     - delta=0, a_eq_b, eta=0
     - mu, nu, chi, phi
     -
   * - ``fixed_nu fixed_psi fixed_phi``
     - nu=0, psi=0, phi=0
     - mu, delta, eta, chi
     -
   * - ``fixed_delta fixed_chi fixed_phi``
     - delta=0, chi=0, phi=0
     - mu, nu, eta
     -
   * - ``fixed_delta fixed_mu fixed_eta``
     - delta=0, mu=0, eta=0
     - nu, chi, phi
     -
   * - ``fixed_delta fixed_mu fixed_phi``
     - delta=0, mu=0, phi=0
     - nu, eta, chi
     -
   * - ``fixed_nu fixed_mu fixed_chi``
     - nu=0, mu=0, chi=0
     - delta, eta, phi
     -
   * - ``fixed_nu fixed_eta fixed_phi``
     - nu=0, eta=0, phi=0
     - mu, delta, chi
     -
   * - ``fixed_nu fixed_eta fixed_chi``
     - nu=0, eta=0, chi=0
     - mu, delta, phi
     -
   * - ``bisect fixed_mu fixed_nu``
     - bisect, mu=0, nu=0
     - delta, eta, chi, phi
     -
   * - ``bisect fixed_eta fixed_delta``
     - bisect, eta=0, delta=0
     - mu, nu, chi, phi
     -
   * - ``bisect fixed_omega fixed_nu``
     - bisect, omega=0, nu=0
     - mu, delta, eta, chi, phi
     -
   * - ``a_eq_b fixed_chi fixed_phi``
     - a_eq_b, chi=0, phi=0
     - mu, delta, nu, eta
     -
   * - ``a_eq_b fixed_chi fixed_eta``
     - a_eq_b, chi=0, eta=0
     - mu, delta, nu, phi
     -
   * - ``a_eq_b fixed_chi fixed_mu``
     - a_eq_b, chi=0, mu=0
     - delta, nu, eta, phi
     -
   * - ``a_eq_b fixed_mu fixed_eta``
     - a_eq_b, mu=0, eta=0
     - delta, nu, chi, phi
     -
   * - ``a_eq_b fixed_mu fixed_phi``
     - a_eq_b, mu=0, phi=0
     - delta, nu, eta, chi
     -
   * - ``a_eq_b fixed_eta fixed_phi``
     - a_eq_b, eta=0, phi=0
     - mu, delta, nu, chi
     -
   * - ``fixed_eta fixed_chi fixed_phi``
     - eta=0, chi=0, phi=0
     - mu, delta, nu
     -
   * - ``fixed_mu fixed_chi fixed_phi``
     - mu=0, chi=0, phi=0
     - delta, nu, eta
     -
   * - ``fixed_mu fixed_eta fixed_phi``
     - mu=0, eta=0, phi=0
     - delta, nu, chi
     -
   * - ``fixed_mu fixed_eta fixed_chi``
     - mu=0, eta=0, chi=0
     - delta, nu, phi
     -

Default mode
^^^^^^^^^^^^

The default mode is ``bisect fixed_mu fixed_nu`` (canonical
``bisecting_vertical``: ``bisect``, ``mu=0``, ``nu=0``).
Equivalent to ``bisecting_vertical`` in E6C terminology: scattering
stays in the vertical plane on the ``delta`` axis with the sample
bisecting the scattering angle.

.. note:: **Bisecting modes**

   Following You (1999) Figure 1 (see also
   `diffcalc-core docs <https://diffcalc-core.readthedocs.io>`_),
   ``delta`` rotates about a horizontal axis and swings the detector
   **vertically**; ``nu`` rotates about a vertical axis and swings the
   detector **horizontally**.  ``mu`` is the horizontal-arm sample
   axis (rotates about the vertical lab axis); ``eta`` rotates about a
   horizontal axis.

   diffcalc's ``bisect`` constraint pairs with one sample axis at a
   time (``mu``, ``eta``, or ``omega``) and pins the *other*
   in-plane axes so that the active detector axis bisects with that
   sample axis:

   .. list-table::
      :header-rows: 1
      :widths: 30 20 25 25

      * - Mode
        - Family
        - Pinned axes
        - Active axes
      * - ``bisect fixed_mu fixed_nu``
        - bisecting vertical (≡ E6C ``bisecting_vertical``)
        - ``mu=0``, ``nu=0``
        - ``delta`` and ``eta`` acting as ttheta and ttheta/2,
          respectively
      * - ``bisect fixed_eta fixed_delta``
        - bisecting horizontal (≡ E6C ``bisecting_horizontal``)
        - ``eta=0``, ``delta=0``
        - ``nu`` and ``mu`` acting as ttheta and ttheta/2,
          respectively
      * - ``bisect fixed_omega fixed_nu``
        - bisecting vertical with ``omega``-tilt (general You case)
        - ``omega=0``, ``nu=0``
        - ``mu``, ``eta``, ``delta``

Mode naming convention
^^^^^^^^^^^^^^^^^^^^^^

Each mode name lists the three diffcalc constraints separated by
spaces.  Token order is **keyword constraints first**
(``a_eq_b``, ``bisect``, ``bin_eq_bout``), then ``fixed_<axis>``
tokens.  For all-``fixed_*`` modes the conventional order is
**detector → sample(s)**.

- ``fixed_<axis>`` — that axis or pseudo-angle is pinned at ``0``.
  Applies to detector axes (``delta``, ``nu``), reference angles
  (``psi``), and sample axes (``mu``, ``eta``, ``chi``, ``phi``,
  ``omega``).
- ``a_eq_b`` — reference-vector constraint: azimuthal reference equals
  scattering vector direction.  **Caution:** singular when the scattering
  vector is parallel to the reference vector; avoid as a default.
- ``bin_eq_bout`` — reference constraint: incidence equals exit angle.
- ``bisect`` — sample bisector condition (one of three diffcalc
  variants, see "Bisector modes" above).

For example, ``bisect fixed_mu fixed_nu`` encodes
``{bisect: True, mu: 0, nu: 0}`` and ``a_eq_b fixed_delta fixed_mu``
encodes ``{a_eq_b: True, delta: 0, mu: 0}``.  See the
:ref:`guide_diffcalc` "Cross-reference to common conventions" section
for a mapping between these names and the
``bisecting_vertical`` / ``lifting_detector_<axis>`` / ``double_diffraction``
vocabulary used by other solvers.

Extensibility
^^^^^^^^^^^^^

The available constraint names are fixed by diffcalc-core and cannot be
changed without modifying that library.  Each constraint name has specific
mathematical implementation inside diffcalc-core's solver — the name is merely
a handle for the underlying algebra that reduces the degrees of freedom during
position calculation.  A new constraint (e.g. ``mu = nu/2``) would require
new code in diffcalc-core, not just a new entry in ``_MODES``.  From the
user's perspective the mode list is not extensible.

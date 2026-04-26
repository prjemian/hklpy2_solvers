.. _guide_ad_hoc:

==========================================
How to use the ``ad_hoc`` solver
==========================================

This guide shows how to create a diffractometer with the ``ad_hoc``
solver, orient a crystalline sample, and compute reciprocal-space
positions.  It assumes you have already :ref:`installed <install>` the
package.

The ``ad_hoc`` solver wraps the
`ad_hoc_diffractometer <https://github.com/prjemian/ad_hoc_diffractometer>`_
library and provides 10 diffractometer geometries ranging from
four-circle to six-circle and kappa configurations.  See
:ref:`geometries.ad_hoc` for the full list.

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

   fourc.sample.lattice = hklpy2.SI_LATTICE_PARAMETERS
   fourc.wavelength.set(1.0)

Add orientation reflections
---------------------------

Provide two reflections measured at known motor positions:

.. code-block:: python

   import math

   theta = math.degrees(math.asin(1.0 / (2 * 5.431)))
   tth = 2 * theta

   r1 = fourc.sample.add_reflection(
       pseudos={"h": 1, "k": 0, "l": 0},
       reals={"omega": theta, "chi": 0, "phi": 0, "ttheta": tth},
       wavelength=1.0,
       name="r1",
   )
   r2 = fourc.sample.add_reflection(
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

   fourc.solver.mode = "fixed_phi"

See :ref:`geometries.ad_hoc` for the full mode tables for each geometry.

Compute motor positions (forward)
---------------------------------

.. code-block:: python

   fourc.forward(1, 0, 0)

This returns a list of motor-position solutions for the given ``(h, k, l)``.

Compute (h, k, l) from motor positions (inverse)
-------------------------------------------------

.. code-block:: python

   fourc.inverse()

This returns the current ``(h, k, l)`` values from the current motor
positions.

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
     - 12
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
     - 12
     - bisecting_vertical
   * - :ref:`zaxis <geometry.zaxis>`
     - alpha, Z, delta, gamma
     - 2
     - zaxis
   * - :ref:`s2d2 <geometry.s2d2>`
     - mu, Z, nu, delta
     - 2
     - mu_fixed

.. seealso::

   - :ref:`geometries.ad_hoc` — full reference for all geometries and modes
   - :ref:`howto_benchmark` — measure solver throughput
   - `hklpy2 user guide <https://blueskyproject.io/hklpy2/>`_ — full
     hklpy2 documentation

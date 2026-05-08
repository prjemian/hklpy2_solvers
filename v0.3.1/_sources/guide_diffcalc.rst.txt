.. _guide_diffcalc:

==========================================
How to use the ``diffcalc`` solver
==========================================

This guide shows how to create a diffractometer with the ``diffcalc``
solver, orient a crystalline sample, and compute reciprocal-space
positions.  It assumes you have already :ref:`installed <install>` the
package.

The ``diffcalc`` solver wraps `diffcalc-core
<https://github.com/DiamondLightSource/diffcalc-core>`_.  This library provides a single
six-circle geometry, :ref:`diffcalc_4S_2D <geometry.diffcalc_4S_2D>` (the
``psic`` geometry described by You 1999),
with 23 operating modes.

Create a diffractometer
-----------------------

.. code-block:: python

   import hklpy2

   psic = hklpy2.creator(
       solver="diffcalc",
       geometry="diffcalc_4S_2D",
       name="psic",
   )

The object ``psic`` has six real axes (``mu``, ``delta``, ``nu``,
``eta``, ``chi``, ``phi``) and three pseudo axes (``h``, ``k``, ``l``).

Set the crystal lattice
-----------------------

.. code-block:: python

   psic.sample.lattice = hklpy2.SI_LATTICE_PARAMETERS
   psic.wavelength.set(1.54)

Add orientation reflections
---------------------------

Provide two reflections measured at known motor positions:

.. code-block:: python

   r1 = psic.add_reflection(
       pseudos={"h": 4, "k": 0, "l": 0},
       reals={"mu": 0, "delta": 69.0966, "nu": 0, "eta": 34.5483, "chi": 0, "phi": 0},
       wavelength=1.54,
       name="r1",
   )
   r2 = psic.add_reflection(
       pseudos={"h": 0, "k": 4, "l": 0},
       reals={"mu": 0, "delta": 69.0966, "nu": 0, "eta": 34.5483, "chi": 0, "phi": 90},
       wavelength=1.54,
       name="r2",
   )

Calculate the UB matrix
-----------------------

.. code-block:: python

   psic.core.calc_UB(r1, r2)

Choose an operating mode
------------------------

The default mode is ``4S+2D bisect_eta_fixed nu_fixed`` (vertical
bisector: ``eta = delta/2``, eta=0, nu=0).  To change it:

.. code-block:: python

   psic.solver.mode = "4S+2D eta_chi_phi_fixed"

See :ref:`geometry.diffcalc_4S_2D` for the full list of 23 modes.

Compute motor positions (forward)
---------------------------------

.. code-block:: python

   psic.forward(4, 0, 0)

This returns a list of motor-position solutions for the given ``(h, k, l)``.

Compute (h, k, l) from motor positions (inverse)
-------------------------------------------------

.. code-block:: python

   psic.inverse()

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
   * - :ref:`diffcalc_4S_2D <geometry.diffcalc_4S_2D>`
     - mu, delta, nu, eta, chi, phi
     - 23
     - 4S+2D bisect_eta_fixed nu_fixed

.. seealso::

   - :ref:`geometry.diffcalc_4S_2D` — full reference for axes and modes
   - :ref:`howto_benchmark` — measure solver throughput
   - `hklpy2 user guide <https://blueskyproject.io/hklpy2/>`_ — full
     hklpy2 documentation

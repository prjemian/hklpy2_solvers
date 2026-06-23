.. _usage:

=================================
Using hklpy2-solvers with hklpy2
=================================

The package registers itself automatically via the ``hklpy2.solver`` entry
point once installed, so no imports from ``hklpy2_solvers`` are needed in
normal use.

Installation
------------

.. code-block:: bash

   pip install hklpy2-solvers

This makes all solvers provided by this package available to ``hklpy2``
immediately.

Available solvers
-----------------

.. list-table::
   :header-rows: 1
   :widths: 15 25 60

   * - Solver name
     - Geometry name(s)
     - Description
   * - ``diffcalc``
     - :ref:`diffcalc_4S_2D <geometry.diffcalc_4S_2D>`
     - You (1999) six-circle geometry via
       `diffcalc-core <https://github.com/DiamondLightSource/diffcalc-core>`_
       (optional backend; see :ref:`install`).
       23 operating modes.
   * - ``ad_hoc``
     - :ref:`fourcv <geometry.fourcv>`, :ref:`fourch <geometry.fourch>`,
       :ref:`psic <geometry.psic>`, :ref:`sixc <geometry.sixc>`,
       :ref:`fivec <geometry.fivec>`,
       :ref:`kappa4cv <geometry.kappa4cv>`, :ref:`kappa4ch <geometry.kappa4ch>`,
       :ref:`kappa6c <geometry.kappa6c>`,
       :ref:`zaxis <geometry.zaxis>`, :ref:`s2d2 <geometry.s2d2>`
     - 10 diffractometer geometries via
       `ad_hoc_diffractometer <https://github.com/bcda-aps/ad_hoc_diffractometer>`_.
       2--24 modes per geometry.

See :ref:`geometries` for the full description of each geometry and its
operating modes.

Creating a diffractometer
--------------------------

Use :func:`hklpy2.creator` to create a diffractometer object for any solver
geometry provided by this package.  The ``solver`` and ``geometry`` arguments
select the backend:

.. code-block:: python

   import hklpy2

   # Using the diffcalc solver (You 1999 six-circle)
   psic = hklpy2.creator(
       solver="diffcalc",
       geometry="diffcalc_4S_2D",
       name="psic",
   )

   # Using the ad_hoc solver (Busing & Levy four-circle vertical)
   fourc = hklpy2.creator(
       solver="ad_hoc",
       geometry="fourcv",
       name="fourc",
   )

The resulting objects are fully-functional ``hklpy2`` diffractometers with
simulated motor positioners for all real axes and the three
reciprocal-space pseudo axes (``h``, ``k``, ``l``).

See :ref:`guide_diffcalc` and :ref:`guide_ad_hoc` for step-by-step
instructions on orienting a sample and computing positions with each
solver.

Further use
-----------

Once the diffractometer object is created, all standard ``hklpy2`` operations
apply — setting the lattice, adding orientation reflections, calculating the
UB matrix, choosing an operating mode, and moving in reciprocal space.
Refer to the `hklpy2 documentation <https://blueskyproject.io/hklpy2/>`_ for
the full user guide.

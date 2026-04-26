.. _guides:

======
Guides
======

Step-by-step guides for common tasks with **hklpy2-solvers**.
Each guide assumes you have already :ref:`installed <install>` the package.

.. toctree::
   :hidden:

   usage
   geometries
   guide_ad_hoc
   guide_diffcalc
   howto_benchmark
   install

.. grid:: 2

   .. grid-item-card:: :ref:`usage`

      Create a diffractometer, orient a sample, and compute reciprocal-space
      positions using hklpy2.

   .. grid-item-card:: :ref:`geometries`

      Supported geometries, operating modes, and axis descriptions for each
      solver.

   .. grid-item-card:: :ref:`guide_ad_hoc`

      Step-by-step guide to creating diffractometers with the ``ad_hoc``
      solver (10 geometries from four-circle to kappa six-circle).

   .. grid-item-card:: :ref:`guide_diffcalc`

      Step-by-step guide to orienting a sample and computing positions
      with the ``diffcalc`` solver (You 1999 six-circle).

   .. grid-item-card:: :ref:`howto_benchmark`

      Measure forward() and inverse() throughput for a solver geometry.

   .. grid-item-card:: :ref:`install`

      Install hklpy2-solvers and make its solvers available to hklpy2.

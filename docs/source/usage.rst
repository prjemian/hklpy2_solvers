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
   :widths: 20 30 50

   * - Solver name
     - Geometry name
     - Common name
   * - ``diffcalc``
     - ``diffcalc_4S_2D``
     - *psic* (You 1999 six-circle)

See :ref:`geometries` for the full description of each geometry and its
operating modes.

Creating a diffractometer
--------------------------

Use :func:`hklpy2.creator` to create a diffractometer object for any solver
geometry provided by this package.  The ``solver`` and ``geometry`` arguments
select the backend:

.. code-block:: python

   import hklpy2

   psic = hklpy2.creator(
       solver="diffcalc",
       geometry="diffcalc_4S_2D",
       name="psic",
   )

The object ``psic`` is a fully-functional ``hklpy2`` diffractometer with
simulated motor positioners for all six real axes
(``mu``, ``delta``, ``nu``, ``eta``, ``chi``, ``phi``) and the three
reciprocal-space pseudo axes (``h``, ``k``, ``l``).

To connect real axes to EPICS motor PVs instead of simulators, supply them
via the ``reals`` argument:

.. code-block:: python

   psic = hklpy2.creator(
       solver="diffcalc",
       geometry="diffcalc_4S_2D",
       name="psic",
       reals=dict(
           mu="IOC:m1",
           delta="IOC:m2",
           nu="IOC:m3",
           eta="IOC:m4",
           chi="IOC:m5",
           phi="IOC:m6",
       ),
   )

Further use
-----------

Once the diffractometer object is created, all standard ``hklpy2`` operations
apply — setting the lattice, adding orientation reflections, calculating the
UB matrix, choosing an operating mode, and moving in reciprocal space.
Refer to the `hklpy2 documentation <https://blueskyproject.io/hklpy2/>`_ for
the full user guide.

.. _howto_benchmark:

=====================================
How to benchmark a solver geometry
=====================================

This guide shows how to measure the computational throughput of a solver
geometry — how many ``forward()`` and ``inverse()`` operations it can perform
per second — using the ``hklpy2.utils.benchmark`` function.

Benchmarking is useful when:

- evaluating whether a solver is fast enough for a scanning application,
- comparing two solvers for the same geometry, or
- detecting a performance regression after a code change.

.. note::

   The benchmark is **purely computational**.  It does not move any motors or
   communicate with hardware, so it is safe to run on a live diffractometer.

Prerequisites
-------------

You will need ``hklpy2`` ≥ 0.6.0 and ``hklpy2-solvers`` installed:

.. code-block:: bash

   pip install "hklpy2>=0.6.0" hklpy2-solvers

Starting from a saved configuration
-------------------------------------

The easiest way to benchmark is to restore a diffractometer from a saved
configuration file.  Ready-to-use configurations are provided for each
supported geometry:

.. list-table::
   :header-rows: 1
   :widths: 20 30 50

   * - Solver
     - Geometry
     - Configuration file
   * - ``diffcalc``
     - :ref:`diffcalc_4S_2D <geometry.diffcalc_4S_2D>`
     - :download:`diffcalc_4s_2d.yml <_static/diffcalc_4s_2d.yml>`

Download the file for your geometry, save it alongside your script, then
restore the diffractometer and run the benchmark:

.. code-block:: python

   import hklpy2

   diffractometer = hklpy2.simulator_from_config("diffcalc_4s_2d.yml")
   hklpy2.utils.benchmark(diffractometer)

Example output::

   Diffractometer benchmark
     solver:     diffcalc
     geometry:   diffcalc_4S_2D
     mode:       4S+2D mu_chi_phi_fixed
     wavelength: 1.54
     calls:      500

     operation       ops/sec     ms/call status
     ------------ ---------- ----------- ------
     forward()           800       1.250   FAIL
     inverse()          7300       0.137   PASS

     target: 2,000 ops/sec (+/-10%)

The ``status`` column compares each operation against a target of
2,000 ops/sec (±10%).  A ``FAIL`` result means the solver is below that
target for this operation.

.. note::

   Some solvers perform iterative constraint solving and return multiple
   candidate solutions per ``forward()`` call.  This can result in a
   ``FAIL`` for ``forward()`` that reflects an upstream library limitation
   rather than a problem with the solver adapter itself.  See the
   :ref:`geometries` page for solver-specific notes.

Saving your own configuration
------------------------------

You can benchmark any diffractometer you have set up by exporting its
current state to a file with :meth:`export`:

.. code-block:: python

   diffractometer.export("my_config.yml", "benchmark configuration")

Then restore and benchmark it later:

.. code-block:: python

   import hklpy2

   diffractometer = hklpy2.simulator_from_config("my_config.yml")
   hklpy2.utils.benchmark(diffractometer)

Adjusting the number of calls
-------------------------------

By default ``benchmark`` uses 500 calls per operation.  Pass ``n`` to
change this — more calls give a more stable measurement:

.. code-block:: python

   hklpy2.utils.benchmark(diffractometer, n=2000)

Capturing results programmatically
------------------------------------

Pass ``print=False`` to suppress the printed report and receive the results
as a dict instead:

.. code-block:: python

   results = hklpy2.utils.benchmark(diffractometer, print=False)
   print(results["forward_ops_per_sec"])
   print(results["inverse_ops_per_sec"])

The dict contains:

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - Key
     - Description
   * - ``solver``
     - Solver name
   * - ``geometry``
     - Geometry name
   * - ``mode``
     - Current operating mode
   * - ``wavelength``
     - Current wavelength (Å)
   * - ``n``
     - Number of calls measured
   * - ``forward_ops_per_sec``
     - ``forward()`` throughput (ops/sec)
   * - ``forward_ms_per_call``
     - ``forward()`` latency (ms/call)
   * - ``inverse_ops_per_sec``
     - ``inverse()`` throughput (ops/sec)
   * - ``inverse_ms_per_call``
     - ``inverse()`` latency (ms/call)
   * - ``target_ops_per_sec``
     - Minimum target (2,000 ops/sec)

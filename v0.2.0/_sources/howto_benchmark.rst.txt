.. _howto_benchmark:

=====================================
How to benchmark a solver geometry
=====================================

This guide shows how to measure the computational throughput of a solver
geometry — how many
:meth:`~hklpy2.diffract.DiffractometerBase.forward` and
:meth:`~hklpy2.diffract.DiffractometerBase.inverse` operations it can
perform per second — using
`hklpy2.utils.benchmark
<https://blueskyproject.io/hklpy2/autoapi/hklpy2/utils/index.html#hklpy2.utils.benchmark>`__.

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

The easiest way to benchmark is to restore a simulator from a saved
configuration file using
:func:`~hklpy2.run_utils.simulator_from_config`.
Ready-to-use configurations are provided for each supported geometry:

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
run:

.. code-block:: python

   import hklpy2

   sim = hklpy2.simulator_from_config("diffcalc_4s_2d.yml")
   hklpy2.utils.benchmark(sim)

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
   candidate solutions per
   :meth:`~hklpy2.diffract.DiffractometerBase.forward` call.  This can
   result in a ``FAIL`` that reflects an upstream library limitation rather
   than a problem with the solver itself.  See the
   :ref:`geometries` page for solver-specific notes.

Benchmarking a live diffractometer
------------------------------------

.. caution::

   `hklpy2.utils.benchmark
   <https://blueskyproject.io/hklpy2/autoapi/hklpy2/utils/index.html#hklpy2.utils.benchmark>`__
   runs timing loops directly on the diffractometer object passed to it.
   Until `bluesky/hklpy2#369 <https://github.com/bluesky/hklpy2/issues/369>`_
   is resolved, pass a **simulator** restored from a snapshot of your live
   diffractometer's configuration, rather than the live instrument itself.
   This guarantees no side effects on motor positions or solver state:

   .. code-block:: python

      import hklpy2

      # Snapshot the live diffractometer, then benchmark the copy.
      sim = hklpy2.simulator_from_config(my_diffractometer.configuration)
      hklpy2.utils.benchmark(sim)

   This page will be updated once the fix is released in hklpy2.

Saving your own configuration
------------------------------

You can benchmark a diffractometer you have already set up in two ways.

**From a file** — export the current state using
:meth:`~hklpy2.diffract.DiffractometerBase.export`, then create a new
simulator and benchmark:

.. code-block:: python

   my_diffractometer.export("my_config.yml", "benchmark configuration")

   sim = hklpy2.simulator_from_config("my_config.yml")
   hklpy2.utils.benchmark(sim)

**Without a file** — pass the
:attr:`~hklpy2.diffract.DiffractometerBase.configuration` property
directly, bypassing the file entirely:

.. code-block:: python

   import hklpy2

   sim = hklpy2.simulator_from_config(my_diffractometer.configuration)
   hklpy2.utils.benchmark(sim)

Adjusting the number of calls
-------------------------------

By default, `hklpy2.utils.benchmark
<https://blueskyproject.io/hklpy2/autoapi/hklpy2/utils/index.html#hklpy2.utils.benchmark>`__
uses 500 calls per operation.  Pass ``n`` to change this — more calls
give a more stable measurement:

.. code-block:: python

   hklpy2.utils.benchmark(sim, n=2000)

Capturing results programmatically
------------------------------------

Pass ``print=False`` to suppress the printed report and receive the results
as a dict instead:

.. code-block:: python

   results = hklpy2.utils.benchmark(sim, print=False)
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
     - :meth:`~hklpy2.diffract.DiffractometerBase.forward` throughput (ops/sec)
   * - ``forward_ms_per_call``
     - :meth:`~hklpy2.diffract.DiffractometerBase.forward` latency (ms/call)
   * - ``inverse_ops_per_sec``
     - :meth:`~hklpy2.diffract.DiffractometerBase.inverse` throughput (ops/sec)
   * - ``inverse_ms_per_call``
     - :meth:`~hklpy2.diffract.DiffractometerBase.inverse` latency (ms/call)
   * - ``target_ops_per_sec``
     - Minimum target (2,000 ops/sec)

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

   psic.add_sample(name="silicon", a=hklpy2.SI_LATTICE_PARAMETER)
   psic.beam.wavelength.put(1.54)

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

The default mode is ``bisect fixed_mu fixed_nu`` (canonical
``bisecting_vertical``: ``mu=0``, ``nu=0``; ``delta`` and ``eta`` acting as
ttheta and ttheta/2, respectively).  To choose a different mode:

.. code-block:: python

   psic.core.mode = "fixed_mu fixed_chi fixed_phi"

See :ref:`geometry.diffcalc_4S_2D` for the full list of 23 modes.

Cross-reference to common conventions
-------------------------------------

Mode names use diffcalc's constraint vocabulary directly
(``fixed_<axis>``, ``bisect``, ``a_eq_b``, …) rather than the
``bisecting_vertical`` / ``lifting_detector_<axis>`` /
``double_diffraction`` vocabulary used by ``hkl_soleil`` and
``ad_hoc`` solvers.  The table below maps the most common
conventions onto the equivalent diffcalc mode:

.. list-table::
   :header-rows: 1
   :widths: 35 35 30

   * - Common-convention name
     - Equivalent diffcalc mode
     - Notes
   * - ``bisecting_vertical``
     - ``bisect fixed_mu fixed_nu``
     - Vertical bisector: ``mu=0``, ``nu=0``.  ``delta`` swings the
       detector vertically; ``eta`` is the bisecting sample axis.
       Default.
   * - ``bisecting_horizontal``
     - ``bisect fixed_eta fixed_delta``
     - Horizontal bisector: ``eta=0``, ``delta=0``.  ``nu`` swings
       the detector horizontally; ``mu`` is the bisecting sample axis.
   * - ``lifting_detector_mu``
     - ``fixed_eta fixed_chi fixed_phi``
     - All three sample-stage axes other than ``mu`` are pinned;
       ``mu``, ``delta``, ``nu`` move.
   * - ``lifting_detector_eta``
     - ``fixed_mu fixed_chi fixed_phi``
     - Equivalent of E6C ``lifting_detector_omega`` (diffcalc's
       ``eta`` is the same physical axis as ``hkl_soleil``'s
       ``omega``).
   * - ``lifting_detector_phi``
     - ``fixed_mu fixed_eta fixed_chi``
     - Sample ``phi`` carries the motion together with the detector.
   * - ``constant_chi`` / ``constant_phi``
     - 2-sample-fixed modes such as ``fixed_delta fixed_chi fixed_phi``
     - Pick the ``fixed_*`` mode whose suffix names the two sample
       axes you want held constant plus the desired pinned detector.
   * - ``double_diffraction``
     - n/a in diffcalc-core
     - diffcalc-core does not implement a double-diffraction
       constraint; use the ``ad_hoc`` or ``hkl_soleil`` solvers for
       that engine.
   * - ``psi_constant``
     - ``fixed_nu fixed_psi fixed_phi``
     - Reference-azimuth pinned to a fixed value (here 0).

The diffcalc constraint categories are documented in
:class:`diffcalc.hkl.constraints.Constraints` (see the
`diffcalc-core documentation <https://diffcalc-core.readthedocs.io>`_).
A valid combination is **at most one** detector constraint, **at
most one** reference constraint, and **one to three** sample
constraints, totalling three constraints overall.

Compute motor positions (forward)
---------------------------------

.. code-block:: python

   psic.forward(4, 0, 0)

This returns a single chosen motor-position solution for the given
``(h, k, l)`` (an ``Hklpy2DiffractometerRealPos``).  The underlying
solver's ``forward()`` may return multiple solutions; the
diffractometer picks one according to the policy assigned to
``psic._forward_solution`` (defaults to
:func:`hklpy2.utils.pick_first_solution`).  The complete list of
solutions can be returned from ``psic.core.forward((4, 0, 0))``.
See the upstream hklpy2 guide `How to Choose the Default forward()
Solution
<https://blueskyproject.io/hklpy2/guides/how_forward_solution.html>`_
for details.

.. tip::

   The two call shapes differ: ``psic.forward(4, 0, 0)`` takes
   ``h``, ``k``, ``l`` as separate positional arguments, while
   ``psic.core.forward((4, 0, 0))`` takes a **single** sequence
   (tuple / list / ndarray) or dict (e.g. ``{"h": 4, "k": 0, "l": 0}``).

Compute (h, k, l) from motor positions (inverse)
-------------------------------------------------

.. code-block:: python

   psic.inverse(psic.real_position)

This returns the ``(h, k, l)`` values computed from the supplied
motor positions.  ``psic.real_position`` is the current readout of
all real axes; pass a different set of values to compute ``(h, k, l)``
at a hypothetical position instead.

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
     - bisect fixed_mu fixed_nu

.. seealso::

   - :ref:`geometry.diffcalc_4S_2D` — full reference for axes and modes
   - :ref:`howto_benchmark` — measure solver throughput
   - `hklpy2 user guide <https://blueskyproject.io/hklpy2/>`_ — full
     hklpy2 documentation

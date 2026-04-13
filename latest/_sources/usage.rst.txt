.. _usage:

=================================
Using hklpy2-solvers with hklpy2
=================================

The package registers itself automatically via the ``hklpy2.solver`` entry
point, so no imports from ``hklpy2_solvers`` are needed in normal use.

1. Installation
---------------

.. code-block:: bash

   pip install hklpy2-solvers

This makes the ``diffcalc`` solver available to ``hklpy2`` immediately.

2. Load the solver
------------------

.. code-block:: python

   import hklpy2
   from hklpy2_solvers.diffcalc_solver import GEOMETRY_NAME  # "diffcalc_4S_2D"

   solver = hklpy2.solver_factory("diffcalc", GEOMETRY_NAME)

Or equivalently, get the class and instantiate it yourself:

.. code-block:: python

   SolverClass = hklpy2.get_solver("diffcalc")  # returns DiffcalcSolver class
   solver = SolverClass(GEOMETRY_NAME)

3. Set the crystal lattice
--------------------------

.. code-block:: python

   solver.lattice = {
       "a": 5.431, "b": 5.431, "c": 5.431,        # Angstroms (silicon)
       "alpha": 90.0, "beta": 90.0, "gamma": 90.0,  # degrees
   }

4. Add two orientation reflections
-----------------------------------

Each reflection is a dict with ``pseudos`` (hkl), ``reals`` (motor angles),
and ``wavelength`` (Å):

.. code-block:: python

   import math

   wl = 1.0  # Angstroms
   theta = math.degrees(math.asin(wl / (2 * 5.431)))
   tth = 2 * theta

   r1 = {
       "name": "r1",
       "pseudos": {"h": 1.0, "k": 0.0, "l": 0.0},
       "reals": {"mu": 0, "delta": tth, "nu": 0, "eta": theta, "chi": 0, "phi": 0},
       "wavelength": wl,
   }
   r2 = {
       "name": "r2",
       "pseudos": {"h": 0.0, "k": 1.0, "l": 0.0},
       "reals": {"mu": 0, "delta": tth, "nu": 0, "eta": theta, "chi": 0, "phi": 90},
       "wavelength": wl,
   }
   solver.addReflection(r1)
   solver.addReflection(r2)

5. Calculate the UB matrix
---------------------------

.. code-block:: python

   ub = solver.calculate_UB(r1, r2)

6. Choose an operating mode
----------------------------

.. code-block:: python

   print(solver.modes)  # list all 23 available modes
   solver.mode = "4S+2D mu_chi_phi_fixed"  # fix mu=chi=phi=0

Adjustable constraint values are exposed via ``extras``:

.. code-block:: python

   print(solver.extra_axis_names)  # e.g. ['mu', 'chi', 'phi']
   print(solver.extras)            # e.g. {'mu': 0.0, 'chi': 0.0, 'phi': 0.0}

See :ref:`geometries` for the full list of modes and their constraints.

7. Forward calculation (hkl → motor angles)
---------------------------------------------

Returns a list of solutions (multiple geometrical solutions are possible):

.. code-block:: python

   solutions = solver.forward({"h": 1.0, "k": 0.0, "l": 0.0})
   print(solutions[0])
   # {'mu': 0.0, 'delta': 10.5647, 'nu': 0.0, 'eta': 5.2824, 'chi': 0.0, 'phi': 0.0}

8. Inverse calculation (motor angles → hkl)
---------------------------------------------

.. code-block:: python

   hkl = solver.inverse(solutions[0])
   print(hkl)
   # {'h': 1.0, 'k': 0.0, 'l': 0.0}

Axes summary
------------

.. list-table::
   :header-rows: 1
   :widths: 20 80

   * - Type
     - Names
   * - Real (motors)
     - ``mu``, ``delta``, ``nu``, ``eta``, ``chi``, ``phi``
   * - Pseudo (reciprocal)
     - ``h``, ``k``, ``l``

.. _install:

============
Installation
============

Requirements
------------

- Python 3.10 or newer
- `hklpy2 <https://blueskyproject.io/hklpy2/>`_

Install from PyPI
-----------------

.. code-block:: bash

   pip install hklpy2-solvers

.. note:: Includes the ``ad_hoc`` solver.

Optional ``diffcalc`` solver
----------------------------

The ``diffcalc`` solver requires the optional
`diffcalc-core <https://github.com/DiamondLightSource/diffcalc-core>`_
backend.  The ``ad_hoc`` solver works without it.  Install the backend
with either pip or conda:

.. code-block:: bash

   pip install hklpy2-solvers[diffcalc]

.. code-block:: bash

   conda install -c paulscherrerinstitute diffcalc-core

If the ``diffcalc`` solver is requested without ``diffcalc-core``
installed, a clear error explains how to install it.

Install for development
-----------------------

.. code-block:: bash

   git clone https://github.com/prjemian/hklpy2_solvers
   cd hklpy2_solvers
   pip install -e ".[dev]"

Install with documentation dependencies
----------------------------------------

.. code-block:: bash

   pip install -e ".[doc]"

Or install everything at once:

.. code-block:: bash

   pip install -e ".[all]"

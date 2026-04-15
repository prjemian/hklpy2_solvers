..
    This file describes user-visible changes between the versions.

    subsections could include these headings (in this order), omit if no content

    Notice
    Breaking Changes
    New Features
    Enhancements
    Fixes
    Maintenance
    Deprecations
    New Contributors

.. _release_notes:

========
Releases
========

Brief notes describing each release and what's new.

Project `milestones <https://github.com/prjemian/hklpy2_solvers/milestones>`_
describe future plans.

0.1.7
#####

.. comment -- development version, not yet released

Fixes
~~~~~

* Fix ``calc_UB()`` raising ``SolverError: Lattice must be set`` even when
  the sample has a lattice; override ``sample`` setter to push lattice and
  reflections into diffcalc immediately.  :issue:`25`
* Fix ``wh()`` raising ``SolverError: UB matrix has not been set`` before
  any reflections are added; auto-init a default UB for ``inverse()``.
  :issue:`24`

0.1.6
#####

Released 2026-04-13.

Fixes
~~~~~

* Fix ``extra_axis_names`` and ``extras``: always ``[]``/``{}`` (no
  non-motor extra parameters in this geometry).  Add ``axes_w`` property
  so hklpy2 can identify axes computed by ``forward()`` and enable the
  presets feature for constant axes.  :issue:`17`
* Fix usage documentation: use ``hklpy2.creator()`` as the standard entry
  point; describe all solvers generically.  :issue:`18`

Maintenance
~~~~~~~~~~~

* Add root redirect page to GitHub Pages.
* Add usage guide for hklpy2-solvers with hklpy2.

0.1.5
#####

Released 2026-04-13.

New Features
~~~~~~~~~~~~

* Add Sphinx documentation framework with versioned GitHub Pages deployment.  :issue:`15`

0.1.4
#####

Released 2026-04-12.

Fixes
~~~~~

* Fix PyPI publish workflow trigger.  :issue:`13`

Maintenance
~~~~~~~~~~~

* Bump ``actions/checkout`` from 4 to 6.
* Bump ``actions/download-artifact`` from 4 to 8.
* Bump ``actions/setup-python`` from 5 to 6.
* Bump ``actions/upload-artifact`` from 4 to 7.

0.1.3
#####

Released 2026-04-12.

Fixes
~~~~~

* Fix CI workflow: pytest path and coverage source.  :issue:`11`

0.1.2
#####

Released 2026-04-12.

Maintenance
~~~~~~~~~~~

* Add solvers table and badges to README.
* Apply ruff formatting to ``diffcalc_solver.py``.

0.1.1
#####

Released 2026-04-12.

Maintenance
~~~~~~~~~~~

* Add CI workflow (pytest on Python 3.10--3.13, ruff lint/format).
* Add PyPI trusted publishing workflow.
* Add dependabot for GitHub Actions and pip dependencies.

0.1.0
#####

Released 2026-04-12.

New Features
~~~~~~~~~~~~

* Add ``diffcalc`` solver adapter wrapping diffcalc-core (You 1999,
  4S+2D six-circle geometry).  :issue:`2`

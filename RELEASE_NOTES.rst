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

..
    SEMVER
    ######

    Expected release: tba

    Fixes
    ~~~~~

    * Expose mode extras (``psi``, ``alpha_i``, ``beta_out``, ``h2``/``k2``/``l2``, ``n_hat``) for ``ad_hoc`` geometries.  :issue:`44`
    * Report ``ad_hoc`` and ``diffcalc`` solver versions from the backend library.  :issue:`44`

    Maintenance
    ~~~~~~~~~~~

    * Require ``ad_hoc_diffractometer >= 0.8.0`` (true virtual bisecting in kappa modes).  :issue:`44`

0.2.2
######

Released 2026-04-26.

Enhancements
~~~~~~~~~~~~

* Docs: add writable(s) and extra(s) columns to geometry mode tables; link each geometry to its backend library documentation.  :issue:`42`

Fixes
~~~~~

* CI: serialize ``gh-pages`` deploys to prevent race condition between ``main`` and tag pushes.  :issue:`42`

Maintenance
~~~~~~~~~~~

* CI: add concurrency limits to all workflows (``docs.yml``, ``ci.yml``, ``pypi.yml``).  :issue:`42`

0.2.1
######

Released 2026-04-26.

Enhancements
~~~~~~~~~~~~

* Add all ``ad_hoc`` solver geometries (10 geometries, modes, and axes) to ``geometries.rst``; add ``ad_hoc`` solver to the "Available solvers" table in ``usage.rst``.  :issue:`40`
* Add per-solver how-to guides (``guide_diffcalc.rst``, ``guide_ad_hoc.rst``) following the Diataxis framework.  :issue:`40`
* Change ``diffcalc`` default mode from ``4S+2D mu_chi_phi_fixed`` to ``4S+2D bisect_eta_fixed nu_fixed`` (vertical bisector).  :issue:`40`

Maintenance
~~~~~~~~~~~

* Bump ``ad_hoc_diffractometer`` minimum from ``>=0.5.0`` to ``>=0.6.0``; update docstring cross-reference (``geometry.py`` renamed to ``diffractometer.py``); update ``geometries.rst`` for new psic and kappa6c mode names.

0.2.0
######

Released 2026-04-20.

New Features
~~~~~~~~~~~~

* Add ``AdHocSolver`` wrapping the ``ad_hoc_diffractometer`` library.  :issue:`1`

Fixes
~~~~~

* ``_summary_dict`` reports correct writable axes per mode.  :issue:`37`

0.1.9
######

Released 2026-04-17.

Enhancements
~~~~~~~~~~~~

* Add HOWTO: benchmark a solver geometry; include downloadable configuration files for each supported geometry.  :issue:`35`
* Guard ``_apply_mode_constraints()`` to skip rebuilding diffcalc objects when the mode is unchanged, reducing ``forward()`` overhead by ~9%.  :issue:`33`

Maintenance
~~~~~~~~~~~

* Refactor ``scripts/stamp_release.py``: read VERSION from RST comment block title (``SEMVER`` auto-bumps patch; PEP 440 explicit versions accepted); add ``--dry-run`` and ``--version`` options; always insert ``SEMVER`` as next block title.  Use ``packaging.version.Version`` for version comparison.
* Add ``packaging`` to dev dependencies in ``pyproject.toml``.

0.1.8
#####

Released 2026-04-17.

Maintenance
~~~~~~~~~~~

* Pin ``hklpy2>=0.6.0`` in dependencies; ``hklpy2.misc`` was removed in that release.  :issue:`31`

0.1.7
#####

Released 2026-04-17.

Fixes
~~~~~

* Fix ``ModuleNotFoundError: No module named 'hklpy2.misc'``; update imports to ``hklpy2.exceptions`` and ``hklpy2.utils`` for compatibility with hklpy2 ≥ 0.6.0.  :issue:`31`
* Fix ``forward()`` raising ``AttributeError: no attribute 'set_reals'``; add ``set_reals()`` and ``UB`` setter, change default mode to ``4S+2D mu_chi_phi_fixed``.  :issue:`29`
* Fix ``calc_UB()`` raising ``SolverError: Lattice must be set``; override ``sample`` setter to push lattice into diffcalc.  :issue:`25`
* Fix ``wh()`` raising ``SolverError: UB matrix has not been set`` before reflections are added.  :issue:`24`

Maintenance
~~~~~~~~~~~

* Document mode naming convention, bisector mode analysis, and extensibility limits in ``geometries.rst``.  :issue:`29`

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

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

    * Fix broken RST indentation in ``psic``/``sixc`` mode tables.  :issue:`123`
    * Route ``n_hat`` extra to the mode's required reference vector.  :issue:`123`

    Maintenance
    ~~~~~~~~~~~

    * Bump ``ad_hoc_diffractometer`` floor to ``>=0.11.3``.  :issue:`123`

0.3.5
######

Released 2026-06-23.

New Features
~~~~~~~~~~~~

* Make ``diffcalc-core`` an optional dependency (group ``diffcalc``).  :issue:`119`

Maintenance
~~~~~~~~~~~

* Enforce single-line imports via ruff isort ``force-single-line``.  :issue:`120`

0.3.4
######

Released 2026-06-22.

Breaking Changes
~~~~~~~~~~~~~~~~

* Rename ``AdHocSolver.exit_angle`` to ``emergence_angle``.  :issue:`117`
* Rename ad_hoc ``alpha_i``/``beta_out`` extras to ``incidence``/``emergence``.  :issue:`117`
* Rename ad_hoc surface modes to ``fixed_incidence_*``/``fixed_emergence_*``/``specular_*``.  :issue:`117`

New Features
~~~~~~~~~~~~

* Add ``AdHocSolver.update_mode_constraints`` for fixed-axis defaults.  :issue:`114`
* Add ``DiffcalcSolver.update_mode_constraints`` for user-mode value overrides.  :issue:`114`

Enhancements
~~~~~~~~~~~~

* Use ``ConstraintSet.with_constraint_values()`` in ``AdHocSolver.extras`` setter.  :issue:`114`

Documentation
~~~~~~~~~~~~~

* Document how to override fixed-axis default values in the ``ad_hoc`` guide.  :issue:`114`
* Document how to set the reference vector (n̂) in the ``ad_hoc`` guide.  :issue:`114`
* Refresh ``ad_hoc`` guide and geometry tables for ad_hoc v0.11.2 naming.  :issue:`117`

Maintenance
~~~~~~~~~~~

* Bump ``ad_hoc_diffractometer`` floor to ``>=0.11.1``.  :issue:`114`
* Bump ``ad_hoc_diffractometer`` floor to ``>=0.11.2``.  :issue:`117`
* Upgrade ``ad_hoc_diffractometer`` from PyPI in cross-validation CI.  :issue:`117`
* Unify copyright automation across hklpy2 family.  :issue:`112`

0.3.3
######

Released 2026-05-21.

New Features
~~~~~~~~~~~~

* Persist ``AdHocSolver`` geometry modifications through hklpy2 ``simulator_from_config``.  :issue:`108`
* Persist ``DiffcalcSolver`` user-registered modes through hklpy2 ``simulator_from_config``.  :issue:`108`

Enhancements
~~~~~~~~~~~~

* Match ``DiffcalcSolver`` mode names by token set, ignoring constraint order.  :issue:`109`

Fixes
~~~~~

* Fix ``DiffcalcSolver.axes_w`` ``KeyError`` for user-registered modes.  :issue:`109`

Maintenance
~~~~~~~~~~~

* Bump ``hklpy2`` floor to ``>=0.7.1`` for uniform ``solver_kwargs`` forwarding.  :issue:`108`

0.3.2
######

Released 2026-05-20.

Breaking Changes
~~~~~~~~~~~~~~~~

* Realign ``DiffcalcSolver`` bisect modes to canonical vertical/horizontal pairings.  :issue:`97`
* Rename all ``DiffcalcSolver`` modes; drop ``4S+2D`` prefix and use ``fixed_<axis>`` form.  :issue:`97`
* Set ``DiffcalcSolver`` default mode to ``bisect fixed_mu fixed_nu`` (canonical vertical bisector).  :issue:`97`

New Features
~~~~~~~~~~~~

* Add ``cross-validation.yml`` workflow running libhkl-backed tests via conda-forge.  :issue:`65`
* Add ``DiffcalcSolver.register_mode`` / ``unregister_mode`` for runtime constraint sets.  :issue:`106`
* Add horizontal four-circle cross-validation group against ``hkl_soleil``.  :issue:`67`
* Add horizontal kappa cross-validation group against ``hkl_soleil``.  :issue:`75`
* Add six-circle bisecting peers to cross-validation groups.  :issue:`64`
* Add vertical four-circle cross-validation suite against ``hkl_soleil``.  :issue:`50`
* Add vertical kappa four-circle cross-validation group against ``hkl_soleil``.  :issue:`66`
* Expand cross-validation sample set to all seven crystal systems.  :issue:`69`
* Surface ``ad_hoc_diffractometer.reference`` helpers on ``AdHocSolver``.  :issue:`101`

Enhancements
~~~~~~~~~~~~

* Add cross-reference table mapping common-convention names to diffcalc modes.  :issue:`97`
* Add guide-regression smoke test to catch API drift in how-to guides.  :issue:`88`
* Add regression test documenting ``ad_hoc/kappa6c bisecting_horizontal`` reflection-pattern gap.  :issue:`77`
* Add regression test documenting ``ad_hoc/psic bisecting_horizontal`` asymmetric-reflection gap.  :issue:`71`
* Document derived-quantity access (ψ, α_i, β_out, n_az, OMEGA) for ``AdHocSolver``.  :issue:`63`
* Expand sapphire cross-validation matrix with ``(1, 1, 3)`` and ``(1, 1, 6)``.  :issue:`77`

Fixes
~~~~~

* Accept scalar default ``n_hat`` from ``hklpy2`` Core in ``AdHocSolver`` extras setter.  :issue:`81`
* Clarify guide wording: diffractometer ``forward()`` returns a single chosen solution.  :issue:`87`
* Correct ``ad_hoc`` and ``diffcalc`` guides to use current hklpy2 API.  :issue:`86`
* Correct horizontal eulerian cross-validation reference to ``E4CH``.  :issue:`78`
* Honour ``r1`` / ``r2`` arguments in ``AdHocSolver.calculate_UB``.  :issue:`56`
* Harden cross-validation bootstrap with deterministic retry on rough-UB ``forward()`` rejection.  :issue:`83`
* Honour ``r1`` / ``r2`` arguments in ``DiffcalcSolver.calculate_UB``.  :issue:`58`
* Lift ``ad_hoc`` ``psic`` / ``kappa6c`` ``bisecting_horizontal`` known-gap markers.  :issue:`99`
* Pin ``python=3.14`` in ``cross-validation.yml`` to narrow K6C triclinic env skew.  :issue:`83`
* Track ``ad_hoc`` horizontal-bisecting rhombohedral ``(1, 1, 0)`` gap as known-gap.  :issue:`69`
* Track ``ad_hoc`` kappa-vertical sapphire ``(0, 1, 2)`` regression as new known-gap.  :issue:`99`
* Track libhkl rhombohedral ``(0, 0, 6)`` B-matrix disagreements as ``tth``-disagreement.  :issue:`68`

Maintenance
~~~~~~~~~~~

* Add focused key-package-version diagnostic step to ``cross-validation.yml``.  :issue:`83`
* Bump ``ad_hoc_diffractometer`` floor to ``>=0.11.0``.  :issue:`99`
* Pip-upgrade ``ad_hoc_diffractometer`` in ``cross-validation.yml`` ahead of conda-forge.  :issue:`99`
* Remove cross-references between solver implementations.  :issue:`60`

0.3.1
######

Released 2026-05-08.

Documentation
~~~~~~~~~~~~~

* Document ``register_geometry_file`` in the ``ad_hoc`` guide.  :issue:`51`
* Refresh ``ad_hoc`` geometry mode tables for ``ad_hoc_diffractometer`` v0.10.0.  :issue:`51`
* Update ``ad_hoc_diffractometer`` documentation URLs to ``bcda-aps.github.io``.  :issue:`53`

Fixes
~~~~~

* Populate version-switcher dropdown from existing gh-pages version directories.  :issue:`54`

Maintenance
~~~~~~~~~~~

* Consolidate content on README and home pages.  :issue:`54`

0.3.0
######

Released 2026-04-27.

Fixes
~~~~~

* Expose mode extras (``psi``, ``alpha_i``, ``beta_out``, ``h2``/``k2``/``l2``, ``n_hat``) for ``ad_hoc`` geometries.  :issue:`44`
* Report ``ad_hoc`` and ``diffcalc`` solver versions from the backend library.  :issue:`44`
* Translate ``kappa_alpha_deg`` keyword to the underlying ``alpha_deg`` argument when constructing kappa geometries.  :issue:`46`

Maintenance
~~~~~~~~~~~

* CI: add Python 3.14-dev to the test matrix (allowed to fail).  :issue:`48`
* Enforce 100% line and branch coverage in CI (``fail_under = 100`` in ``pyproject.toml``).  :issue:`46`
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
* Fix ``forward()`` raising ``AttributeError: no attribute 'set_reals'``; add ``set_reals()`` and ``UB`` setter, change default mode to ``fixed_mu fixed_chi fixed_phi``.  :issue:`29`
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

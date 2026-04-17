# AI Agent advice for hklpy2_solvers

<https://agents.md>

## Purpose

Goal: Short guide for coding agents (auto-formatters, linters, CI bots, test runners, codegen agents) working on this Python project.

## Code Style

- Concise type annotations
- code location described in pyproject.toml
- style information described in pyproject.toml
- `pre-commit run --all-files`


## Agent pytest style (for automated agents) - MANDATORY

---

**CRITICAL: All test code MUST follow this pattern. Tests not following this pattern will be rejected.**

### Requirements

1. **ALWAYS use parametrized pytest** with `parms, context` as the parameter names
2. **ALWAYS use `pytest.param()`** for each parameter set with `id="..."`
3. **ALWAYS use context managers**: `does_not_raise()` for success, `pytest.raises(...)` for failures
4. **ALWAYS put all functional code and assertions inside `with context:` block**
5. **ALWAYS use `match=re.escape(...)` with `pytest.raises(...)`** for exception matching
6. **ALWAYS include failure test cases** - parameter sets that are expected to raise exceptions must use `pytest.raises(...)`
7. **NEVER create separate test functions** for success vs failure cases
8. **NEVER use try/except** for test logic
9. **NEVER use the deprecated `assert_context_result()` helper**

### Import requirements

```python
from contextlib import nullcontext as does_not_raise
import pytest
```

### Correct pattern (copy this exactly):

```py
@pytest.mark.parametrize(
    "parms, context",
    [
        pytest.param(
            dict(some_param=value1),
            does_not_raise(),
            id="description of test case 1",
        ),
        pytest.param(
            dict(some_param=invalid_value),
            pytest.raises(SomeError, match=re.escape("expected message")),
            id="description of test case 2",
        ),
    ],
)
def test_function_name(parms, context):
    with context:
        # ALL code that might raise goes HERE
        result = object_under_test.method(**parms)
        # ALL assertions go HERE (inside the with block)
        assert result.expected_attribute == some_value
```

### Common mistakes to avoid

- NOT this:
  ```py
  def test_something():
      # setup code...
      # test code...
  ```

- NOT this:
  ```py
  def test_success_case():
      # code...
      assert result == expected

  def test_failure_case():
      with pytest.raises(...):
          # code...
  ```

- NOT this:
  ```py
  @pytest.mark.parametrize(...)
  def test_something(values):
      try:
          result = do_something(values)
      except SomeError:
          # wrong!
  ```

- ALWAYS this:
  ```py
  @pytest.mark.parametrize(
      "parms, context",
      [
          pytest.param(dict(value=valid), does_not_raise(), id="valid case"),
          pytest.param(dict(value=invalid), pytest.raises(Error), id="error case"),
      ],
  )
  def test_something(parms, context):
      with context:
          result = do_something(**parms)
  ```

## Enforcement

PRs opened or modified by automated agents must follow the "Agent pytest style" described above. Reviewers and CI will check for this pattern (test parametrization and use of context managers for expected outcomes, both successful and failed). Changes from agents that do not comply may be requested for revision or reverted.

## Agent behavior rules

- Always follow the project's formatting, linting, and typing configs.
- Make minimal, focused changes; prefer separate commits per concern.
- Add or update tests for any behavioral change.
- Include clear commit messages and PR descriptions.
- If uncertain about design, open an issue instead of making large changes.
- Respect branch protection: push to feature branches and create PRs.
- **Never commit unless the user explicitly says to commit.**  Completing
  a code change does not imply permission to commit it.  Wait for an
  explicit instruction such as "commit", "commit and push", or
  "finish the workflow".

## Test style

- All test code for MODULE.py goes in file tests/test_MODULE.py
- tests should be written and organized using the project's test style guidelines.
- use parametrized pytests
- Prefer parameter sets that simulate user interactions
- all tests run code within context
- maximize code coverage
- Use parametrized pytests
  - Generate additional parameters and sets to minimize the number of test functions.
  - Place all functional code in a parametrized context.
    - use parameter for does_not_raise() or pytest.raises(...) as fits the parameter set
      - `from contextlib import nullcontext as does_not_raise`
    - do not separate success and errors tests into different test functions
    - do not separate success and errors tests using try..except

## Inputs & outputs

- Inputs: file diffs, test results, config files, repository metadata
- Outputs: patch/commit, tests, updated docs, CI status

## Running locally

- Setup: create virtualenv, `pip install -e .[all]`
- Common commands:
  - Format & Lint: `pre-commit run --all-files` (preferred; see note below)
  - Test: `pytest ./tests`

### `make style` vs `pre-commit run --all-files`

`make style` runs `isort --sl` before `pre-commit`.  `isort --sl` (single-line
mode) and ruff's built-in isort (`I` rule) disagree on whether to split
multi-symbol imports from the same module onto separate lines.  This causes
`make style` to report a ruff failure even when the file is already correct.

**Use `pre-commit run --all-files` directly** as the authoritative lint/format
check.  Ruff's isort is the style enforced by CI; `isort --sl` in the
`Makefile` is a legacy convenience that conflicts with it.

### pre-commit on NFS home directories

The pre-commit cache (`~/.cache/pre-commit`) lives on NFS on this system
(`aquila:/export/beams1`).  Setuptools' wheel-build cleanup uses `os.rmdir()`
which fails non-deterministically on NFS because directory-entry removals are
not immediately visible.  Symptom: `[Errno 39] Directory not empty` during
`pip install` for any pre-commit hook environment.

**Fix:** keep the pre-commit cache on local disk:

```bash
export PRE_COMMIT_HOME=/tmp/pre-commit-JEMIAN   # in ~/.bashrc and ~/.profile
```

This is already set in `~/.bashrc`, `~/.profile`, and hardcoded in
`.git/hooks/pre-commit` (between the `# end templated` line and the `HERE=`
line).  If `pre-commit install` regenerates the hook, re-add that line:

```bash
# Use local disk for pre-commit cache (avoids NFS rmdir failures)
export PRE_COMMIT_HOME=/tmp/pre-commit-JEMIAN
```

The `Makefile` `pre` target also exports this variable automatically.

## CI integration

- Format and lint in pre-commit job
- Run tests and dependency audit on PRs.

## Minimal example PR checklist

- Runs formatting and linting locally
- Adds/updates tests for changes
  - Adds entry to `RELEASE_NOTES.rst` inside the RST comment block for the next unreleased version
- Marks PR as draft if large refactor

## Release Notes

### Structure

`RELEASE_NOTES.rst` always has an RST comment block at the top (above the
most recent released version) that holds the **next** unreleased version:

```rst
..
    SEMVER
    ######

    Expected release: tba

    Fixes
    ~~~~~

    * Some change.  :issue:`N`

0.1.8
#####

Released 2026-04-17.
...
```

The RST comment (``..`` directive with 4-space-indented content) hides the
block from Sphinx so unreleased notes never appear in published docs.  Only
released versions are visible.

The title of the comment block controls what version is used at release time:

- ``SEMVER`` : the release script computes a patch-level bump automatically.
- ``X.Y.Z``  : used directly as the release version (must advance the sequence).
- Any valid PEP 440 version (e.g. ``1.0.0rc1``) : used directly as the release version (must advance the sequence).
- Anything else : the script aborts with an error.

### Adding entries during development

- Update `RELEASE_NOTES.rst` as part of every PR that introduces a new
  feature, fix, enhancement, or maintenance change.
- Add the entry **inside the RST comment block** (``..`` + 4-space indent)
  for the next unreleased version at the top of the file.
- Entries should be terse — one or two lines — and reference the issue or PR
  number with ``:issue:`N``` or ``:pr:`N```.
- Use the appropriate subsection and keep subsections in the logical order
  defined at the top of ``RELEASE_NOTES.rst``: Notice, Breaking Changes, New
  Features, Enhancements, Fixes, Maintenance, Deprecations, New Contributors.
- Sort entries alphabetically within each subsection.

## Git Issues, Branches, Commits, and Pull Requests

All non-trivial work follows this lifecycle: **Issue -> Branch -> Commits ->
Pull Request**. Each step is described below with the concrete rules agents
must follow.

### Issues

Every piece of work starts with an issue. Issues answer the most expensive
question in code maintenance: *Why is this change being made?*

- An issue describes the observation, bug, feature request, or maintenance
  task that motivates the work.
- Do not begin coding without a corresponding issue (the only exception is a
  truly trivial fix that needs no explanation).

### Direct commits to `main`

Direct commits to `main` (without a PR) are reserved for low-level
housekeeping that does not warrant its own issue and branch.  Examples:

- Stamping a release date in ``RELEASE_NOTES.rst`` (``maint vX.Y.Z stamp...``)
- Fixing a single-word typo in documentation
- Updating a badge or URL that has changed

Everything else — new features, bug fixes, enhancements, non-trivial
documentation additions, refactors — must follow the full
Issue → Branch → Commits → PR workflow.

### Branches

All development happens on feature branches, never directly on `main`.

- **Naming convention**: `<ISSUE_NUMBER>-<CONCISE-TITLE>`
  - The concise title is derived from the issue title, using lowercase words
    separated by hyphens.
  - Example: for issue #42 titled "Add timeout to LDAP queries", the branch
    name is `42-add-ldap-timeout`.
- Create the branch from the current `main`:
  `git checkout -b <branch-name> main`
- Push with tracking: `git push -u origin <branch-name>`

### Commits

Write commit messages following the
[Conventional Commits](https://www.conventionalcommits.org/) style with the
issue number included.

**Format:**

```text
<PREFIX> #<ISSUE_NUMBER> concise subject line

Optional body with additional context.
Agent: <agent name> (<model name>)
```

**Prefix values** (use the one that best describes the change):

| Prefix | Use for |
|--------|---------|
| `feat` | New feature or capability |
| `fix` | Bug fix |
| `docs` | Documentation only |
| `refactor` | Code restructuring, no behavior change |
| `style` | Formatting, linting, whitespace |
| `maint` | Maintenance, dependency updates, housekeeping |
| `ci` | CI/CD configuration |
| `test` | Adding or updating tests |

**Examples:**

```text
feat #42 add configurable timeout to LDAP queries

Default timeout is 30 s; configurable via dm_config.ini.
Agent: OpenCode (claudesonnet46)
```

```text
docs #15 update AGENTS.md with branching workflow
```

### Pull Requests

A Pull Request (PR) describes *how* an issue has been (or will be) addressed.

- Every PR **must** reference at least one issue.
- The PR body **must** include a `closes #N` directive for the issue it
  resolves. Use a bullet list at the top of the PR body:

  ```md
  - closes #42
  - #15
  ```

  Using `closes #N` will auto-close the issue when the PR is merged.
- The PR title should be a concise summary of the change.
- Assign the PR to the user running the agent (determine with ``gh api user --jq '.login'``).
- Copy the issue's labels, project(s), milestone, and status to the PR.
- Sign the PR body with the agent and model name:

  ```md
  Agent: OpenCode (claudesonnet46)
  ```

- PR discussion comments should explain the approach, trade-offs, and any
  open questions.
- Sign all PR and issue comments with the agent and model name:

  ```md
  Agent: OpenCode (claudesonnet46)
  ```

## Tagging a Release

The version to release is read automatically from the RST comment block at
the top of `RELEASE_NOTES.rst`.  The script validates it against existing
git tags and stops with an error if the version already exists or regresses.

After the PR is merged and `main` is up to date locally:

1. **Preview with dry run**:
   ```bash
   make release-preview
   ```
   The script reads VERSION from the comment block title (or ``--version``),
   prints what it would do, and exits without writing anything.  If
   the title is ``SEMVER``, it prints the computed patch-level bump.

2. **Run the release**:
   ```bash
   make release                        # normal run
   make release ARGS="--version 0.2.0" # override VERSION
   ```
   The script:
   - Removes the ``..`` / indent wrapper, exposing the section.
   - Replaces ``Expected release: tba`` with ``Released yyyy-mm-dd.``
   - Inserts a new ``SEMVER`` RST comment block above the released section.
   - Commits ``RELEASE_NOTES.rst`` directly on ``main``.
   - Pushes ``main``.
   - Creates and pushes the annotated tag ``vX.Y.Z``.
   The script exits with an error if VERSION already exists as a git tag,
   does not advance beyond the latest tag, or the title is unrecognised.

3. The tag push triggers CI to build and publish the package.

## Notes

- Keep agent actions small, reversible, and reviewable.
- When updating a file, verify that a change has actually been made by comparing
  the mtime before and after the edits.

## Code Coverage

- Aim for 100% coverage, but prioritize meaningful tests over simply hitting every line.

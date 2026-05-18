# Copyright (c) 2026 Pete Jemian <prjemian+hklpy2@gmail.com>
# SPDX-License-Identifier: LicenseRef-UChicago-Argonne-LLC-License
"""Guide-regression smoke test (:issue:`88`).

Executes every ``.. code-block:: python`` directive found in the
how-to guides under ``docs/source/guide_*.rst`` to catch API drift
between the documentation and the installed hklpy2 / solver
versions.  Issues :issue:`86` and :issue:`87` were both
copy-paste failures the user discovered by hand; this test makes
the same class of failure show up in CI instead of in a user's
terminal.

Discovery rules
---------------

* Every ``.. code-block:: python`` directive in each guide is
  extracted (in source order), unindented, and concatenated into
  a single Python program per guide.
* Blocks containing the literal string ``/path/to/mybeamline.yml``
  are skipped: that placeholder path is used in
  ``guide_ad_hoc.rst`` as an illustration of how to register a
  custom YAML geometry; it is not meant to be executed without a
  real file.

The combined program is run with ``exec()`` in a fresh module
namespace.  Any uncaught exception fails the corresponding
parameter case.
"""

import re
from contextlib import nullcontext as does_not_raise
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

REPO_ROOT = Path(__file__).resolve().parent.parent
GUIDES_DIR = REPO_ROOT / "docs" / "source"
GUIDE_GLOB = "guide_*.rst"

# Blocks whose body contains this substring are illustrative only and
# are not executed by the smoke test.
PLACEHOLDER_MARKERS = ("/path/to/mybeamline.yml",)

# Matches a ``.. code-block:: python`` directive followed by an
# indented body.  The indented body uses three-space indentation per
# Sphinx convention.
_CODE_BLOCK_RE = re.compile(
    r"^\.\. code-block:: python\s*\n"
    r"((?:^\s*$\n)*)"  # optional blank lines between directive and body
    r"((?:^   .*\n|^\s*$\n)+)",  # indented body (3-space indent) plus blanks
    re.MULTILINE,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _extract_python_blocks(rst_text):
    """Yield ``(start_line, body)`` for each Python code-block directive.

    ``start_line`` is 1-indexed and points at the ``.. code-block::``
    line.  ``body`` is the unindented code text with a trailing
    newline.
    """
    for match in _CODE_BLOCK_RE.finditer(rst_text):
        start_line = rst_text[: match.start()].count("\n") + 1
        raw = match.group(2)
        unindented_lines = []
        for line in raw.splitlines():
            if line.startswith("   "):
                unindented_lines.append(line[3:])
            elif not line.strip():
                unindented_lines.append("")
            else:  # pragma: no cover - regex already constrains shape
                unindented_lines.append(line)
        yield start_line, "\n".join(unindented_lines).rstrip() + "\n"


def _is_runnable(body):
    """True when ``body`` does not contain any known placeholder marker."""
    return not any(marker in body for marker in PLACEHOLDER_MARKERS)


def _combined_program(rst_path):
    """Return the concatenated runnable Python program for one guide."""
    text = Path(rst_path).read_text()
    parts = []
    for start_line, body in _extract_python_blocks(text):
        if not _is_runnable(body):
            continue
        parts.append(f"# === {rst_path.name}:{start_line} ===\n{body}\n")
    return "".join(parts)


def _run_guide(rst_path):
    """Execute every runnable code block from ``rst_path`` end-to-end."""
    program = _combined_program(rst_path)
    namespace = {"__name__": "__main__"}
    exec(compile(program, str(rst_path), "exec"), namespace)


# ---------------------------------------------------------------------------
# Parametrization
# ---------------------------------------------------------------------------


def _discover_guides():
    """Yield ``pytest.param`` for each how-to guide on disk."""
    for rst_path in sorted(GUIDES_DIR.glob(GUIDE_GLOB)):
        yield pytest.param(
            dict(rst_path=rst_path),
            does_not_raise(),
            id=rst_path.stem,
        )


_BROKEN_GUIDE_TEXT = """\
Broken guide
============

.. code-block:: python

   import hklpy2
   hklpy2.this_attribute_does_not_exist
"""


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "parms, context",
    [
        *_discover_guides(),
        pytest.param(
            dict(rst_path=None, rst_text=_BROKEN_GUIDE_TEXT),
            pytest.raises(AttributeError, match="this_attribute_does_not_exist"),
            id="synthetic-broken-guide-raises",
        ),
    ],
)
def test_guide_runs_end_to_end(parms, context, tmp_path):
    """Every how-to guide's code blocks must run without exception.

    The trailing synthetic case feeds a deliberately broken guide
    string into the runner to confirm that exceptions in a guide
    block do surface as test failures (i.e. the runner is not
    silently swallowing errors).
    """
    with context:
        rst_path = parms["rst_path"]
        if rst_path is None:
            rst_path = tmp_path / "broken_guide.rst"
            rst_path.write_text(parms["rst_text"])
        _run_guide(rst_path)

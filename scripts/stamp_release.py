#!/usr/bin/env python3
# Copyright (c) 2026 Pete Jemian <prjemian+hklpy2@gmail.com>
# SPDX-License-Identifier: LicenseRef-UChicago-Argonne-LLC-License
"""
Prepare RELEASE_NOTES.rst for a new tagged release.

Usage::

    python scripts/stamp_release.py VERSION DATE NEXT

    python scripts/stamp_release.py 0.1.8 2026-04-17 0.1.9

Steps performed:

1. Locate the RST comment block (``..`` + indented content) for VERSION.
2. Uncomment the block: remove the ``..`` line and de-indent the content.
3. Replace ``Expected release: tba`` with ``Released DATE.``.
4. Insert a new empty RST comment block for NEXT immediately above the
   newly released VERSION section.

RST comment block format used by this project::

    ..
        X.Y.Z
        #####

        Expected release: tba

"""

import re
import sys
from pathlib import Path

RELEASE_NOTES = Path(__file__).parent.parent / "RELEASE_NOTES.rst"

# RST comment block: a bare ".." line followed by indented lines.
# The block ends at the first non-indented, non-blank line.
_COMMENT_BLOCK_RE = re.compile(
    r"^\.\.\n"  # opening ".." line
    r"((?:    [^\n]*\n|\n)*)",  # indented or blank lines (4-space indent)
    re.MULTILINE,
)


def _find_pending_block(text: str, version: str) -> re.Match:
    """Return the regex match for the RST comment block containing VERSION."""
    for m in _COMMENT_BLOCK_RE.finditer(text):
        body = m.group(1)
        # The first non-blank indented line should be the version number.
        first_line = next((ln.strip() for ln in body.splitlines() if ln.strip()), "")
        if first_line == version:
            return m
    sys.exit(
        f"ERROR: Could not find a pending RST comment block for {version!r} in "
        f"{RELEASE_NOTES}.\n"
        "Expected format:\n"
        "..\n"
        f"    {version}\n"
        "    #####\n\n"
        "    Expected release: tba\n"
    )


def _deindent(body: str) -> str:
    """Remove the 4-space indent from every line of a comment body."""
    lines = []
    for ln in body.splitlines(keepends=True):
        if ln.startswith("    "):
            lines.append(ln[4:])
        else:
            lines.append(ln)
    return "".join(lines)


def main(version: str, date: str, next_version: str) -> None:
    text = RELEASE_NOTES.read_text()

    # ------------------------------------------------------------------ #
    # Step 1: locate the pending block for VERSION.                        #
    # ------------------------------------------------------------------ #
    m = _find_pending_block(text, version)

    # ------------------------------------------------------------------ #
    # Steps 2 + 3: uncomment and stamp the date.                          #
    # ------------------------------------------------------------------ #
    body = _deindent(m.group(1))
    released_block = body.replace("Expected release: tba", f"Released {date}.", 1)
    text = text[: m.start()] + released_block + text[m.end() :]

    # ------------------------------------------------------------------ #
    # Step 4: insert the next-version RST comment block above VERSION.    #
    # ------------------------------------------------------------------ #
    next_block = f"..\n    {next_version}\n    #####\n\n    Expected release: tba\n\n"
    version_heading_re = re.compile(r"(?m)^" + re.escape(version) + r"\n#{5}\n")
    m2 = version_heading_re.search(text)
    if not m2:
        sys.exit(f"ERROR: Could not locate '{version}' heading after editing.")
    text = text[: m2.start()] + next_block + text[m2.start() :]

    RELEASE_NOTES.write_text(text)
    print(f"  Uncommented {version} block and stamped date {date}.")
    print(f"  Added new pending RST comment block for {next_version}.")
    print(f"  Written: {RELEASE_NOTES}")


if __name__ == "__main__":
    if len(sys.argv) != 4:
        sys.exit(f"Usage: {sys.argv[0]} VERSION DATE NEXT\n  e.g. {sys.argv[0]} 0.1.8 2026-04-17 0.1.9")
    main(sys.argv[1], sys.argv[2], sys.argv[3])

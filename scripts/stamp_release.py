#!/usr/bin/env python3
# Copyright (c) 2026 Pete Jemian <prjemian+hklpy2@gmail.com>
# SPDX-License-Identifier: LicenseRef-UChicago-Argonne-LLC-License
"""
Prepare RELEASE_NOTES.rst for a new tagged release.

Usage::

    python scripts/stamp_release.py VERSION DATE NEXT

    python scripts/stamp_release.py 0.1.8 2026-04-17 0.1.9

Steps performed:
1. Remove the ``<!--`` / ``-->`` lines surrounding the pending block for VERSION.
2. Replace ``Expected release: tba`` with ``Released DATE.``.
3. Insert a new empty ``<!-- NEXT ... -->`` comment block above the VERSION section.
"""

import re
import sys
from pathlib import Path

RELEASE_NOTES = Path(__file__).parent.parent / "RELEASE_NOTES.rst"


def main(version: str, date: str, next_version: str) -> None:
    text = RELEASE_NOTES.read_text()

    # ------------------------------------------------------------------ #
    # Validate: the pending block must exist and contain VERSION.          #
    # ------------------------------------------------------------------ #
    comment_block_re = re.compile(
        r"<!--\n" + re.escape(version) + r"\n#{5}\n\nExpected release: tba\n(.*?)-->",
        re.DOTALL,
    )
    m = comment_block_re.search(text)
    if not m:
        sys.exit(
            f"ERROR: Could not find a pending <!-- {version} ... --> block in "
            f"{RELEASE_NOTES}.\n"
            "Expected format:\n"
            "<!--\n"
            f"{version}\n"
            "#####\n\n"
            "Expected release: tba\n"
            "-->"
        )

    # ------------------------------------------------------------------ #
    # Step 1 + 2: uncomment the block and stamp the date.                 #
    # ------------------------------------------------------------------ #
    inner = m.group(1)  # content between version heading and -->
    released_block = f"{version}\n#####\n\nReleased {date}.\n{inner}"
    text = text[: m.start()] + released_block + text[m.end() :]

    # ------------------------------------------------------------------ #
    # Step 3: insert the next-version comment block above VERSION.        #
    # ------------------------------------------------------------------ #
    next_block = f"<!--\n{next_version}\n#####\n\nExpected release: tba\n-->\n\n"
    # Find the version heading we just exposed and insert above it.
    version_heading_re = re.compile(r"(?m)^" + re.escape(version) + r"\n#{5}\n")
    m2 = version_heading_re.search(text)
    if not m2:
        sys.exit(f"ERROR: Could not locate '{version}' heading after editing.")
    text = text[: m2.start()] + next_block + text[m2.start() :]

    RELEASE_NOTES.write_text(text)
    print(f"  Uncommenting {version} block and stamping date {date}.")
    print(f"  Added new pending block for {next_version}.")
    print(f"  Written: {RELEASE_NOTES}")


if __name__ == "__main__":
    if len(sys.argv) != 4:
        sys.exit(f"Usage: {sys.argv[0]} VERSION DATE NEXT\n  e.g. {sys.argv[0]} 0.1.8 2026-04-17 0.1.9")
    main(sys.argv[1], sys.argv[2], sys.argv[3])

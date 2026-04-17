#!/usr/bin/env python3
# Copyright (c) 2026 Pete Jemian <prjemian+hklpy2@gmail.com>
# SPDX-License-Identifier: LicenseRef-UChicago-Argonne-LLC-License
"""
Prepare RELEASE_NOTES.rst for a new tagged release.

Usage::

    python scripts/stamp_release.py [NEXT]

    python scripts/stamp_release.py
    python scripts/stamp_release.py 0.2.0

The VERSION to release is read from the RST comment block at the top of
RELEASE_NOTES.rst.  DATE defaults to today (yyyy-mm-dd).  NEXT defaults
to a patch-level bump of VERSION.

Steps performed:

1. Extract VERSION from the topmost RST comment block.
2. Validate VERSION:
   - Must parse as a valid X.Y.Z semantic version.
   - Must not already exist as a git tag.
   - Must not regress behind the most recent git tag.
3. Uncomment the block: remove the ``..`` line and de-indent the content.
4. Replace ``Expected release: tba`` with ``Released DATE.``.
5. Insert a new empty RST comment block for NEXT immediately above the
   newly released VERSION section.

RST comment block format used by this project::

    ..
        X.Y.Z
        #####

        Expected release: tba

"""

import datetime
import re
import subprocess
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

_SEMVER_RE = re.compile(r"^(\d+)\.(\d+)\.(\d+)$")


def _parse_version(v: str) -> tuple[int, int, int]:
    """Parse 'X.Y.Z' into a tuple of ints, or exit with an error."""
    m = _SEMVER_RE.match(v)
    if not m:
        sys.exit(f"ERROR: {v!r} is not a valid semantic version (expected X.Y.Z).")
    return int(m.group(1)), int(m.group(2)), int(m.group(3))


def _bump_patch(version: str) -> str:
    major, minor, patch = _parse_version(version)
    return f"{major}.{minor}.{patch + 1}"


def _existing_tags() -> set[str]:
    """Return the set of existing git tag names, stripping a leading 'v'."""
    result = subprocess.run(
        ["git", "tag"],
        capture_output=True,
        text=True,
        cwd=RELEASE_NOTES.parent,
    )
    return {t.lstrip("v") for t in result.stdout.splitlines() if t.strip()}


def _latest_tag() -> str | None:
    """Return the most recent git tag (by version sort), stripped of 'v'."""
    result = subprocess.run(
        ["git", "tag", "--sort=version:refname"],
        capture_output=True,
        text=True,
        cwd=RELEASE_NOTES.parent,
    )
    tags = [t.lstrip("v") for t in result.stdout.splitlines() if t.strip()]
    # Keep only valid semver tags.
    tags = [t for t in tags if _SEMVER_RE.match(t)]
    return tags[-1] if tags else None


def _find_topmost_comment_block(text: str) -> re.Match:
    """Return the first RST comment block in the file that contains a version title."""
    for m in _COMMENT_BLOCK_RE.finditer(text):
        body = m.group(1)
        first_line = next((ln.strip() for ln in body.splitlines() if ln.strip()), "")
        if _SEMVER_RE.match(first_line):
            return m
    sys.exit(
        f"ERROR: No RST comment block with a semver title found in {RELEASE_NOTES}.\n"
        "Expected format:\n"
        "..\n"
        "    X.Y.Z\n"
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


def main(next_version: str | None = None) -> None:
    date = datetime.date.today().isoformat()
    text = RELEASE_NOTES.read_text()

    # ------------------------------------------------------------------ #
    # Step 1: extract VERSION from the topmost comment block.             #
    # ------------------------------------------------------------------ #
    m = _find_topmost_comment_block(text)
    body = m.group(1)
    version = next(ln.strip() for ln in body.splitlines() if ln.strip())

    print(f"  VERSION from comment block: {version}")

    # ------------------------------------------------------------------ #
    # Step 2: validate VERSION.                                            #
    # ------------------------------------------------------------------ #
    _parse_version(version)  # exits if not valid semver

    existing = _existing_tags()
    if version in existing:
        sys.exit(f"ERROR: Tag {version!r} already exists. Aborting.")

    latest = _latest_tag()
    if latest is not None:
        if _parse_version(version) <= _parse_version(latest):
            sys.exit(f"ERROR: VERSION {version!r} does not advance beyond the latest tag {latest!r}. Aborting.")

    # ------------------------------------------------------------------ #
    # Steps 3 + 4: uncomment the block and stamp the date.               #
    # ------------------------------------------------------------------ #
    released_body = _deindent(body).replace("Expected release: tba", f"Released {date}.", 1)
    text = text[: m.start()] + released_body + text[m.end() :]

    # ------------------------------------------------------------------ #
    # Step 5: insert the next-version RST comment block above VERSION.   #
    # ------------------------------------------------------------------ #
    if next_version is None:
        next_version = _bump_patch(version)
    else:
        _parse_version(next_version)  # validate it is semver
        if _parse_version(next_version) <= _parse_version(version):
            sys.exit(f"ERROR: NEXT {next_version!r} does not advance beyond VERSION {version!r}. Aborting.")

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
    print(f"  Next step: git add RELEASE_NOTES.rst && git commit && git tag v{version}")


if __name__ == "__main__":
    if len(sys.argv) not in (1, 2):
        sys.exit(f"Usage: {sys.argv[0]} [NEXT]\n  e.g. {sys.argv[0]}\n       {sys.argv[0]} 0.2.0")
    main(sys.argv[1] if len(sys.argv) == 2 else None)

#!/usr/bin/env python3
# Copyright (c) 2026 Pete Jemian <prjemian+hklpy2@gmail.com>
# SPDX-License-Identifier: LicenseRef-UChicago-Argonne-LLC-License
"""
Prepare RELEASE_NOTES.rst for a new tagged release.

Usage::

    python scripts/stamp_release.py [--dry-run] [--version X.Y.Z]

    python scripts/stamp_release.py
    python scripts/stamp_release.py --dry-run
    python scripts/stamp_release.py --version 0.2.0

The VERSION to release is determined from the title of the topmost RST
comment block in RELEASE_NOTES.rst:

- ``SEMVER`` : VERSION is computed as a patch-level bump of the latest git
  tag.  The computed version is printed before any changes are made.
- PEP 440 version (e.g. ``X.Y.Z``, ``1.0.0rc1``) : Used directly as
  VERSION, provided it advances the tag sequence and does not already
  exist as a git tag.
- Anything else : Error, abort.

DATE is always today's date (yyyy-mm-dd).

Steps performed:

1. Determine VERSION from the comment block title (or ``--version``).
2. Validate VERSION against existing git tags.
3. Uncomment the block: remove the ``..`` line and de-indent the content.
4. Replace ``Expected release: tba`` with ``Released DATE.``.
5. Insert a new ``SEMVER`` RST comment block above the released section.
6. Commit RELEASE_NOTES.rst, push main, create and push the tag.

RST comment block format used by this project::

    ..
        SEMVER
        ######

        Expected release: tba

"""

import argparse
import datetime
import re
import subprocess
import sys
from pathlib import Path

from packaging.version import InvalidVersion, Version

RELEASE_NOTES = Path(__file__).parent.parent / "RELEASE_NOTES.rst"

# RST comment block: a bare ".." line followed by 4-space-indented lines.
# The block ends at the first non-indented, non-blank line.
_COMMENT_BLOCK_RE = re.compile(
    r"^\.\.\n"  # opening ".." line
    r"((?:    [^\n]*\n|\n)*)",  # indented or blank lines
    re.MULTILINE,
)

# Matches any PEP 440 version-like token that could appear as a block title.
# We use packaging.version.Version for real validation; this is just used to
# distinguish a version-like string from free text in the comment block.
_VERSION_TITLE_RE = re.compile(r"^\d+\.\d+.*$")

_SEMVER_PLACEHOLDER = "SEMVER"

_NEXT_BLOCK = "..\n    SEMVER\n    ######\n\n    Expected release: tba\n\n"


# ------------------------------------------------------------------ #
# Helpers                                                              #
# ------------------------------------------------------------------ #


def _parse_version(v: str) -> Version:
    """Parse a PEP 440 version string, or exit with an error."""
    try:
        return Version(v)
    except InvalidVersion:
        sys.exit(f"ERROR: {v!r} is not a valid PEP 440 version. Aborting.")


def _bump_patch(version: str) -> str:
    v = _parse_version(version)
    # Only bump the base X.Y.Z regardless of any pre/post/dev suffix.
    return f"{v.major}.{v.minor}.{v.micro + 1}"


def _git(*args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        capture_output=True,
        text=True,
        cwd=RELEASE_NOTES.parent,
    )
    return result.stdout


def _existing_tags() -> set[str]:
    """Return existing git tag names stripped of a leading 'v'."""
    return {t.lstrip("v") for t in _git("tag").splitlines() if t.strip()}


def _latest_semver_tag() -> str | None:
    """Return the most recent PEP 440 git tag (by version sort), stripped of 'v'."""
    tags = []
    for t in _git("tag", "--sort=version:refname").splitlines():
        t = t.strip().lstrip("v")
        try:
            Version(t)
            tags.append(t)
        except InvalidVersion:
            pass
    return tags[-1] if tags else None


def _find_topmost_comment_block(text: str) -> tuple[re.Match, str]:
    """Return the first RST comment block whose title is SEMVER or a PEP 440 version."""
    for m in _COMMENT_BLOCK_RE.finditer(text):
        body = m.group(1)
        first_line = next((ln.strip() for ln in body.splitlines() if ln.strip()), "")
        if first_line == _SEMVER_PLACEHOLDER:
            return m, first_line
        try:
            Version(first_line)
            return m, first_line
        except InvalidVersion:
            pass
    sys.exit(
        f"ERROR: No RST comment block with title 'SEMVER' or a PEP 440 version "
        f"found in {RELEASE_NOTES}.\n"
        "Expected format:\n"
        "..\n"
        "    SEMVER\n"
        "    ######\n\n"
        "    Expected release: tba\n"
    )


def _deindent(body: str) -> str:
    """Remove the 4-space indent from every line of a comment body."""
    lines = []
    for ln in body.splitlines(keepends=True):
        lines.append(ln[4:] if ln.startswith("    ") else ln)
    return "".join(lines)


def _block_content_lines(body: str) -> list[str]:
    """Return non-header content lines from a comment block body.

    Skips the version title, underline, and 'Expected release: tba' line.
    """
    lines = body.splitlines()
    # Skip version title and underline (first two non-blank lines)
    skip = 2
    result = []
    for ln in lines:
        if skip > 0 and ln.strip():
            skip -= 1
            continue
        if ln.strip().startswith("Expected release:"):
            continue
        result.append(ln)
    return result


# ------------------------------------------------------------------ #
# Main                                                                 #
# ------------------------------------------------------------------ #


def main(dry_run: bool = False, version_override: str | None = None) -> None:
    date = datetime.date.today().isoformat()
    text = RELEASE_NOTES.read_text()

    # ------------------------------------------------------------------ #
    # Step 1: read topmost comment block title.                           #
    # ------------------------------------------------------------------ #
    m, title = _find_topmost_comment_block(text)
    body = m.group(1)

    latest = _latest_semver_tag()

    if version_override:
        version = version_override
        print(f"  VERSION override supplied: {version}")
    elif title == _SEMVER_PLACEHOLDER:
        if latest is None:
            sys.exit("ERROR: Cannot auto-bump — no existing PEP 440 git tags found.")
        version = _bump_patch(latest)
        print(f"  Title is SEMVER — computed VERSION: {version} (patch bump from {latest})")
    else:
        # title is a PEP 440 version (guaranteed by _find_topmost_comment_block)
        version = title
        print(f"  VERSION from comment block: {version}")

    # ------------------------------------------------------------------ #
    # Step 2: validate VERSION.                                            #
    # ------------------------------------------------------------------ #
    _parse_version(version)  # exits if not a valid PEP 440 version

    existing = _existing_tags()
    if version in existing:
        sys.exit(f"ERROR: Tag {version!r} already exists. Aborting.")

    if latest is not None and _parse_version(version) <= _parse_version(latest):
        sys.exit(f"ERROR: VERSION {version!r} does not advance beyond the latest tag {latest!r}. Aborting.")

    # ------------------------------------------------------------------ #
    # Report what will happen.                                            #
    # ------------------------------------------------------------------ #
    content_lines = _block_content_lines(body)
    content_preview = "".join(content_lines).strip()

    print(f"  DATE: {date}")
    print("  NEXT block title: SEMVER")
    if content_preview:
        print("  Pending changes in block:")
        for ln in content_preview.splitlines():
            print(f"    {ln}")
    else:
        print("  Pending changes in block: (none)")
    print(f"  Would write: {RELEASE_NOTES}")
    print(f"  Would tag:   v{version}")

    if dry_run:
        print("  DRY RUN — no files written.")
        return

    # ------------------------------------------------------------------ #
    # Steps 3 + 4: uncomment the block and stamp the date (atomic).      #
    # ------------------------------------------------------------------ #
    # If title was SEMVER, replace it with the computed version first.
    if title == _SEMVER_PLACEHOLDER:
        body = body.replace(f"    {_SEMVER_PLACEHOLDER}\n", f"    {version}\n", 1)

    released_body = _deindent(body).replace("Expected release: tba", f"Released {date}.", 1)
    text = text[: m.start()] + released_body + text[m.end() :]

    # ------------------------------------------------------------------ #
    # Step 5: insert new SEMVER comment block above VERSION heading.      #
    # ------------------------------------------------------------------ #
    version_heading_re = re.compile(r"(?m)^" + re.escape(version) + r"\n#{5,6}\n")
    m2 = version_heading_re.search(text)
    if not m2:
        sys.exit(f"ERROR: Could not locate '{version}' heading after editing.")
    text = text[: m2.start()] + _NEXT_BLOCK + text[m2.start() :]

    RELEASE_NOTES.write_text(text)
    print(f"  Written: {RELEASE_NOTES}")

    repo = RELEASE_NOTES.parent
    commit_msg = f"maint v{version} stamp release date in RELEASE_NOTES"
    steps = [
        (["git", "add", "RELEASE_NOTES.rst"], "Staging RELEASE_NOTES.rst"),
        (["git", "commit", "-m", commit_msg], f"Committing: {commit_msg}"),
        (["git", "push", "origin", "main"], "Pushing main"),
        (["git", "tag", "-a", f"v{version}", "-m", f"release {version}"], f"Tagging v{version}"),
        (["git", "push", "origin", f"v{version}"], f"Pushing tag v{version}"),
    ]
    for cmd, description in steps:
        print(f"  {description}...")
        result = subprocess.run(cmd, cwd=repo, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"  ERROR: {' '.join(cmd)} failed:")
            print(result.stderr.strip())
            sys.exit(result.returncode)
        if result.stdout.strip():
            print(result.stdout.strip())
    print(f"  Released v{version}.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Stamp RELEASE_NOTES.rst for a new tagged release.")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print what would happen without writing any files.",
    )
    parser.add_argument(
        "--version",
        metavar="X.Y.Z",
        help="Override the VERSION (ignores comment block title).",
    )
    args = parser.parse_args()
    main(dry_run=args.dry_run, version_override=args.version)

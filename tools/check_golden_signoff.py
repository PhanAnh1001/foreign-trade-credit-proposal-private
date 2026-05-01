#!/usr/bin/env python3
"""
Reject if staged diff touches tests/fixtures/golden_* WITHOUT a sibling *.feedback.md
that is also staged AND contains '## Approved by <name>' (name in docs/reviewers.txt).

Lỗ hổng #11 (workflow §6.6) — chống AI tự đổi golden output để pass test.

Run as pre-commit hook (or manually).
"""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

GOLDEN_RE = re.compile(r"tests/fixtures/golden[_/]")
APPROVED_RE = re.compile(r"^##\s*Approved\s+by\s+(.+?)\s*(?:@|$)", re.IGNORECASE | re.MULTILINE)
REVIEWERS_FILE = Path("docs/reviewers.txt")


def staged() -> list[str]:
    return subprocess.check_output(
        ["git", "diff", "--cached", "--name-only", "--diff-filter=ACMR"],
        text=True,
    ).splitlines()


def reviewers() -> set[str]:
    if not REVIEWERS_FILE.exists():
        return set()
    return {
        l.strip()
        for l in REVIEWERS_FILE.read_text().splitlines()
        if l.strip() and not l.strip().startswith("#")
    }


def main() -> int:
    files = staged()
    golden_changed = [f for f in files if GOLDEN_RE.search(f)]
    if not golden_changed:
        return 0

    rev = reviewers()
    bad: list[str] = []
    for g in golden_changed:
        feedback = f"{g}.feedback.md"
        if feedback not in files:
            bad.append(f"{g}: missing sibling sign-off file {feedback}")
            continue
        content = Path(feedback).read_text(encoding="utf-8")
        m = APPROVED_RE.search(content)
        if not m:
            bad.append(f"{feedback}: no '## Approved by' line")
            continue
        name = m.group(1).strip().rstrip("@").strip()
        if name not in rev:
            bad.append(f"{feedback}: approver '{name}' not in {REVIEWERS_FILE}")

    if bad:
        sys.stderr.write("Golden fixture change requires reviewer sign-off:\n")
        for b in bad:
            sys.stderr.write(f"  {b}\n")
        sys.stderr.write(
            "\nFix: create <golden>.feedback.md with '## Approved by <name>' (name in docs/reviewers.txt).\n"
        )
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())

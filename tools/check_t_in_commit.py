#!/usr/bin/env python3
"""
Reject commit message không có 'T<n>:' prefix.
Lỗ hổng #9 (workflow §6.5) — chống scope creep.

Usage (commit-msg hook):
    python tools/check_t_in_commit.py "$1"

Allowed:
    T1: add toc parser
    T12: fix F2 (run abc123)
    Tboot1: bootstrap scaffold
    Merge ...   (merge commit)
    Revert ...  (revert)

Reject:
    chore: foo
    fix: bar
    "wip auto save"
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ALLOWED = re.compile(
    r"^(T\w+:\s|Merge\s|Revert\s|fixup!\s|squash!\s)",
)


def main() -> int:
    if len(sys.argv) < 2:
        sys.stderr.write("usage: check_t_in_commit.py <commit-msg-file>\n")
        return 2
    msg_path = Path(sys.argv[1])
    if not msg_path.exists():
        return 0
    first_line = msg_path.read_text(encoding="utf-8").splitlines()[0] if msg_path.read_text().strip() else ""
    if ALLOWED.match(first_line):
        return 0
    sys.stderr.write(
        "ERROR: commit message must start with 'T<n>:' (vd 'T3: add toc parser').\n"
        f"  got: {first_line!r}\n"
        "  Allowed prefixes: T<n>:, Merge, Revert, fixup!, squash!\n"
    )
    return 1


if __name__ == "__main__":
    sys.exit(main())

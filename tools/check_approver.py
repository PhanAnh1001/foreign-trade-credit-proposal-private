#!/usr/bin/env python3
"""
Verify that any "## Approved by <name>" line in a file references a name in docs/reviewers.txt.
Lỗ hổng #1 (workflow §6.5) — chống AI tự tick approved.

Usage:
    python tools/check_approver.py --file docs/requirements/refund.md
    python tools/check_approver.py --staged   # check tất cả file staged
Exit:
    0 = ok (or no Approved-by line)
    1 = found Approved-by with name not in reviewers.txt
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

REVIEWERS_FILE = Path("docs/reviewers.txt")
APPROVED_RE = re.compile(r"^##\s*Approved\s+by\s+(.+?)\s*(?:@|$)", re.IGNORECASE | re.MULTILINE)


def load_reviewers() -> set[str]:
    if not REVIEWERS_FILE.exists():
        sys.stderr.write(f"ERROR: {REVIEWERS_FILE} not found\n")
        sys.exit(2)
    names: set[str] = set()
    for line in REVIEWERS_FILE.read_text().splitlines():
        s = line.strip()
        if not s or s.startswith("#"):
            continue
        names.add(s)
    return names


def staged_files() -> list[Path]:
    out = subprocess.check_output(
        ["git", "diff", "--cached", "--name-only", "--diff-filter=ACMR"],
        text=True,
    )
    return [Path(p) for p in out.splitlines() if p.endswith((".md", ".markdown"))]


def check_file(path: Path, reviewers: set[str]) -> list[str]:
    if not path.exists():
        return []
    content = path.read_text(encoding="utf-8", errors="ignore")
    bad: list[str] = []
    for m in APPROVED_RE.finditer(content):
        name = m.group(1).strip().rstrip("@").strip()
        if name not in reviewers:
            line_no = content[: m.start()].count("\n") + 1
            bad.append(f"{path}:{line_no}: '{name}' not in {REVIEWERS_FILE}")
    return bad


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--file", action="append", default=[])
    ap.add_argument("--staged", action="store_true")
    args = ap.parse_args()

    files = [Path(f) for f in args.file]
    if args.staged:
        files += staged_files()

    if not files:
        return 0

    reviewers = load_reviewers()
    all_bad: list[str] = []
    for f in files:
        all_bad.extend(check_file(f, reviewers))

    if all_bad:
        sys.stderr.write("Unauthorized approver(s) found:\n")
        for line in all_bad:
            sys.stderr.write(f"  {line}\n")
        sys.stderr.write(f"\nAdd name to {REVIEWERS_FILE} or remove the 'Approved by' line.\n")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())

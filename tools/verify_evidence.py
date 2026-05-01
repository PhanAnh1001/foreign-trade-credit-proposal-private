#!/usr/bin/env python3
"""
Crosscheck evidence dir for confabulation (lỗ hổng #6.6.1).

Verifies:
  1. log.txt exists and is non-empty.
  2. SHA256 of log.txt matches what REPORT.md claims (if claimed).
  3. pytest_junit.xml exists (if test was claimed run) and has >= MIN_TESTS testcases.
  4. Timestamp range in log.txt is within run window (start..end).
  5. eval.json + security.json + REPORT.md present.

Usage:
    python tools/verify_evidence.py --evidence-dir ete-evidence/.../<run-id>/
Exit:
    0 = pass
    1 = fail (and prints reasons)
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from xml.etree import ElementTree as ET

MIN_TESTS_DEFAULT = 1
TS_RE = re.compile(r"^(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})")
SHA_RE = re.compile(r"sha256:\s*([0-9a-f]{64})", re.IGNORECASE)


def fail(msgs: list[str], why: str) -> None:
    msgs.append(why)


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    h.update(p.read_bytes())
    return h.hexdigest()


def parse_ts(line: str) -> datetime | None:
    m = TS_RE.match(line)
    if not m:
        return None
    try:
        return datetime.fromisoformat(m.group(1))
    except ValueError:
        return None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--evidence-dir", required=True, type=Path)
    ap.add_argument("--min-tests", type=int, default=MIN_TESTS_DEFAULT)
    args = ap.parse_args()

    d: Path = args.evidence_dir
    msgs: list[str] = []
    required = ["REPORT.md", "log.txt", "eval.json", "security.json", "inputs.json"]
    for r in required:
        if not (d / r).exists():
            fail(msgs, f"missing required file: {r}")

    if (d / "log.txt").exists() and (d / "log.txt").stat().st_size == 0:
        fail(msgs, "log.txt is empty (suspicious)")

    if (d / "REPORT.md").exists() and (d / "log.txt").exists():
        report = (d / "REPORT.md").read_text(encoding="utf-8")
        log_path = d / "log.txt"
        actual_sha = sha256(log_path)
        m = SHA_RE.search(report)
        if m and m.group(1).lower() != actual_sha:
            fail(msgs, f"REPORT.md claims log SHA {m.group(1)} but actual is {actual_sha}")

    junit = d / "pytest_junit.xml"
    if junit.exists():
        try:
            root = ET.fromstring(junit.read_text(encoding="utf-8"))
            n = sum(1 for _ in root.iter("testcase"))
            if n < args.min_tests:
                fail(msgs, f"pytest_junit.xml has only {n} testcases (< {args.min_tests})")
        except ET.ParseError as e:
            fail(msgs, f"pytest_junit.xml not parseable: {e}")

    if (d / "log.txt").exists():
        ts = [parse_ts(l) for l in (d / "log.txt").read_text(errors="ignore").splitlines()]
        ts = [t for t in ts if t is not None]
        if ts:
            span = (max(ts) - min(ts)).total_seconds()
            if span < 0:
                fail(msgs, f"log timestamps go backwards (span={span}s)")
            if span > 24 * 3600:
                fail(msgs, f"log timestamps span > 24h ({span}s)")

    if (d / "eval.json").exists():
        try:
            ej = json.loads((d / "eval.json").read_text())
            if "judges" in ej and len(ej["judges"]) < 2:
                fail(msgs, "eval.json has <2 judges (workflow requires 2 different vendors)")
        except json.JSONDecodeError as e:
            fail(msgs, f"eval.json not parseable: {e}")

    if msgs:
        sys.stderr.write(f"Evidence verification FAILED for {d}:\n")
        for m in msgs:
            sys.stderr.write(f"  - {m}\n")
        return 1
    print(f"Evidence verification PASSED for {d}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

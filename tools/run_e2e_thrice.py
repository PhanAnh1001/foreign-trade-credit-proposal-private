#!/usr/bin/env python3
"""
Run E2E 3 times consecutively with the SAME input. Aggregate to a 3-of-3 verdict.
Lỗ hổng #6.6.2 — chống LLM non-determinism.

Pass criterion: 3/3 individual runs must PASS. 2/3 = fail.

Usage:
    python tools/run_e2e_thrice.py --scenario happy_co1
Output:
    ete-evidence/_runs/<base>/3of3/
      ├── run_1/  (full evidence dir)
      ├── run_2/
      ├── run_3/
      └── verdict.json   {"runs": [...], "passed": 3, "stable": "3-of-3"}
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import shutil
import subprocess
import sys
from pathlib import Path


def run_once(scenario: str, run_id: str, evidence_dir: Path) -> dict:
    cmd = [
        "make", "e2e",
        f"SCENARIO={scenario}",
        f"RUN_ID={run_id}",
        f"EVIDENCE_DIR={evidence_dir}",
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    report = evidence_dir / "REPORT.md"
    passed = False
    if report.exists():
        passed = "Status: ✅ PASS" in report.read_text(encoding="utf-8") or "Status: ✅" in report.read_text(encoding="utf-8")
    return {
        "run_id": run_id,
        "evidence_dir": str(evidence_dir),
        "exit_code": result.returncode,
        "passed": bool(passed and result.returncode == 0),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--scenario", required=True)
    ap.add_argument("--base-dir", default="ete-evidence/_runs")
    args = ap.parse_args()

    base_ts = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    base_id = f"{base_ts}_{args.scenario}_3of3"
    out_root = Path(args.base_dir) / base_id
    out_root.mkdir(parents=True, exist_ok=True)

    runs = []
    for i in (1, 2, 3):
        run_id = f"{base_id}_run{i}"
        evidence_dir = out_root / f"run_{i}"
        runs.append(run_once(args.scenario, run_id, evidence_dir))

    passed_n = sum(1 for r in runs if r["passed"])
    stable = f"{passed_n}-of-3"

    verdict = {
        "scenario": args.scenario,
        "base_id": base_id,
        "runs": runs,
        "passed": passed_n,
        "stable": stable,
        "verdict_pass": passed_n == 3,
    }
    (out_root / "verdict.json").write_text(json.dumps(verdict, indent=2))
    print(json.dumps(verdict, indent=2))

    if passed_n != 3:
        sys.stderr.write(
            f"\nFAIL: {stable}. Workflow §6.6.2 requires 3-of-3.\n"
            "  Investigate non-determinism: temperature, seed, racy code.\n"
        )
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())

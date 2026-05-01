#!/usr/bin/env python3
"""
Compare current run's perf metrics with the baseline for the same scenario.
Lỗ hổng #6.6.10 — chống performance regression vô hình.

Threshold: regression > 1.5× = [must-fix].

Baselines stored at: data/baselines/<scenario>.json
Format:
{
  "scenario": "happy_co1",
  "updated_at": "YYYY-MM-DD",
  "latency_p50_s": 165,
  "latency_p95_s": 178,
  "tokens_total": 47231,
  "cost_usd": 0.04
}

Usage:
    python tools/perf_diff.py --scenario happy_co1 --evidence-dir <run-dir>
    python tools/perf_diff.py --scenario happy_co1 --evidence-dir <run-dir> --update-baseline
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

THRESHOLD = 1.5  # regression > 1.5× → fail

BASELINE_DIR = Path("data/baselines")
METRICS = ["latency_p50_s", "latency_p95_s", "tokens_total", "cost_usd"]


def load_eval(evidence_dir: Path) -> dict:
    p = evidence_dir / "eval.json"
    if not p.exists():
        sys.stderr.write(f"missing {p}\n")
        sys.exit(2)
    return json.loads(p.read_text())


def extract_metrics(ev: dict) -> dict:
    calls = ev.get("llm_calls", {})
    return {
        "latency_p50_s": (calls.get("p50_latency_ms", 0)) / 1000,
        "latency_p95_s": (calls.get("p95_latency_ms", 0)) / 1000,
        "tokens_total": calls.get("input_tokens", 0) + calls.get("output_tokens", 0),
        "cost_usd": calls.get("cost_usd", 0),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--scenario", required=True)
    ap.add_argument("--evidence-dir", required=True, type=Path)
    ap.add_argument("--update-baseline", action="store_true")
    args = ap.parse_args()

    ev = load_eval(args.evidence_dir)
    cur = extract_metrics(ev)

    baseline_path = BASELINE_DIR / f"{args.scenario}.json"

    if args.update_baseline:
        baseline_path.parent.mkdir(parents=True, exist_ok=True)
        baseline_path.write_text(json.dumps({"scenario": args.scenario, **cur}, indent=2))
        print(f"updated baseline: {baseline_path}")
        return 0

    if not baseline_path.exists():
        print(f"WARN: no baseline at {baseline_path} — run with --update-baseline to create")
        return 0

    base = json.loads(baseline_path.read_text())
    bad: list[str] = []
    print(f"{'metric':<20}{'baseline':>14}{'current':>14}{'ratio':>10}")
    for m in METRICS:
        b = float(base.get(m, 0)) or 1e-9
        c = float(cur[m])
        r = c / b
        flag = "  ❌ FAIL" if r > THRESHOLD else "  ✓"
        print(f"{m:<20}{b:>14.3f}{c:>14.3f}{r:>10.2f}x{flag}")
        if r > THRESHOLD:
            bad.append(f"{m}: {c:.3f} vs baseline {b:.3f} = {r:.2f}× (> {THRESHOLD}×)")

    if bad:
        sys.stderr.write(f"\nPerf regression in scenario {args.scenario}:\n")
        for b in bad:
            sys.stderr.write(f"  {b}\n")
        sys.stderr.write(
            "\nIf intentional: update baseline with --update-baseline AFTER reviewer approves.\n"
        )
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())

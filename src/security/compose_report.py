"""Compose security.json from individual scan outputs — Bước 5.5."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def _load_json_safe(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def compose(evidence_dir: Path) -> dict:
    sec_dir = evidence_dir / "security"

    # Layer 1: gitleaks
    gl = _load_json_safe(sec_dir / "gitleaks.json")
    gl_findings = len(gl) if isinstance(gl, list) else gl.get("findings", 0)
    layer_secret = {"tool": "gitleaks", "findings": gl_findings,
                    "status": "pass" if gl_findings == 0 else "fail",
                    "report_path": "security/gitleaks.json"}

    # Layer 2: SAST
    bandit = _load_json_safe(sec_dir / "bandit.json")
    high = sum(1 for r in bandit.get("results", []) if r.get("issue_severity") == "HIGH")
    med = sum(1 for r in bandit.get("results", []) if r.get("issue_severity") == "MEDIUM")
    layer_sast = {"tool": "bandit", "high": high, "medium": med,
                  "status": "pass" if high == 0 else "fail",
                  "report_path": "security/bandit.json"}

    # Layer 3: pip-audit
    audit = _load_json_safe(sec_dir / "pip-audit.json")
    cve_high = sum(1 for v in audit.get("dependencies", [])
                   for vuln in v.get("vulns", [])
                   if vuln.get("fix_versions"))
    layer_deps = {"tool": "pip-audit", "cve_high": cve_high,
                  "status": "pass" if cve_high == 0 else "fail",
                  "report_path": "security/pip-audit.json"}

    # Layer 4: license
    lic = _load_json_safe(sec_dir / "licenses.json")
    deny = ["GPL", "AGPL"]
    deny_hits = sum(1 for pkg in (lic if isinstance(lic, list) else [])
                    if any(d in pkg.get("License", "") for d in deny))
    layer_lic = {"tool": "pip-licenses", "denylist": deny, "denylist_hits": deny_hits,
                 "status": "pass" if deny_hits == 0 else "fail",
                 "report_path": "security/licenses.json"}

    # Layer 5: AI-safety (from pytest json-report or our test run)
    ai_rep = _load_json_safe(sec_dir / "ai-safety.json")
    # pytest-json-report format
    ai_passed = ai_rep.get("summary", {}).get("passed", 0)
    ai_failed = ai_rep.get("summary", {}).get("failed", 0)
    layer_ai = {
        "status": "pass" if ai_failed == 0 else "fail",
        "tests_passed": ai_passed,
        "tests_failed": ai_failed,
        "report_path": "security/ai-safety.json",
    }

    layers_ok = all(
        l["status"] in ("pass", "pass-with-warnings")
        for l in [layer_secret, layer_sast, layer_deps, layer_lic, layer_ai]
    )

    report = {
        "run_id": evidence_dir.name,
        "overall_status": "pass" if layers_ok else "fail",
        "layers": {
            "secret_scan": layer_secret,
            "sast": layer_sast,
            "deps": layer_deps,
            "license": layer_lic,
            "ai_safety": layer_ai,
        },
    }
    return report


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--evidence-dir", required=True, type=Path)
    args = ap.parse_args()

    report = compose(args.evidence_dir)
    out = args.evidence_dir / "security.json"
    out.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    overall = report["overall_status"]
    print(f">> security.json: {overall.upper()} — {out}")
    return 0 if overall == "pass" else 1


if __name__ == "__main__":
    sys.exit(main())

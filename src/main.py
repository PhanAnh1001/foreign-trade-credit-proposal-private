"""CLI entry point for the LC application agent."""
from __future__ import annotations
import argparse
import sys
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate a Vietcombank LC application from a foreign trade contract."
    )
    parser.add_argument(
        "--contract",
        required=True,
        help="Path to the foreign trade contract (TXT, PDF, or DOCX)",
    )
    parser.add_argument(
        "--bank",
        default=None,
        help="Bank slug (e.g. 'vietcombank'). Determines template and output directory. Defaults to vietcombank.",
    )
    parser.add_argument(
        "--output-dir",
        default=None,
        help="Override output directory for the filled LC DOCX. Defaults to data/outputs/{bank}/{company}/.",
    )
    args = parser.parse_args()

    contract_path = args.contract
    if not Path(contract_path).exists():
        print(f"ERROR: Contract file not found: {contract_path}", file=sys.stderr)
        sys.exit(1)

    from src.agents.graph import run_lc_application

    final_state = run_lc_application(
        contract_path=contract_path,
        bank=args.bank,
        output_dir=args.output_dir,
    )

    output_path = final_state.get("output_docx_path")
    errors = final_state.get("errors") or []

    if output_path and Path(output_path).exists():
        print(f"\n✓ LC Application saved: {output_path}")
        score = final_state.get("quality_score")
        if score:
            print(f"  Quality score: {score:.1f}/10")
        warnings = (final_state.get("lc_data") or {}).get("validation_warnings", [])
        if warnings:
            print(f"\n  Warnings ({len(warnings)}):")
            for w in warnings:
                print(f"    ⚠ {w}")
    else:
        print("\n✗ LC Application generation failed.", file=sys.stderr)
        for err in errors:
            print(f"  ERROR: {err}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

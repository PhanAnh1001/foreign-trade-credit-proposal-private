"""Node 4: Fill the LC DOCX template with validated data."""
from __future__ import annotations
import os
from pathlib import Path
from ..models.state import LCAgentState
from ..utils.docx_filler import fill_lc_template
from ..utils.logger import get_logger, timed_node
from ..config import BANK_DEFAULT, get_bank_template_path, get_bank_output_dir, slugify_company

logger = get_logger("node.fill")


@timed_node
def fill_node(state: LCAgentState) -> dict:
    """Fill the LC application DOCX template with the validated data."""
    lc_data = state.get("lc_data")
    if not lc_data:
        msg = "fill_node: no lc_data in state."
        logger.error(msg)
        return {"errors": [msg], "current_step": "fill_failed"}

    bank = state.get("bank") or BANK_DEFAULT
    contract_name = Path(state.get("contract_path", "contract")).stem

    # Derive company slug from applicant name
    company_slug = slugify_company(lc_data.get("applicant_name") or "")

    # Resolve output directory: explicit override or derive from bank/company
    output_dir_override = state.get("output_dir") or ""
    if output_dir_override:
        out_dir = Path(output_dir_override)
        out_dir.mkdir(parents=True, exist_ok=True)
    else:
        out_dir = get_bank_output_dir(bank, company_slug)

    output_path = str(out_dir / f"LC-Application-{contract_name}.docx")

    template_path = str(get_bank_template_path(bank))
    if not Path(template_path).exists():
        msg = f"LC template not found: {template_path}"
        logger.error(msg)
        return {"errors": [msg], "current_step": "fill_failed"}

    logger.info(f"Filling LC template [{bank}] → {output_path}")
    try:
        result_path = fill_lc_template(lc_data, template_path, output_path)
        size_kb = os.path.getsize(result_path) / 1024
        logger.info(f"LC application DOCX saved — {result_path} ({size_kb:.1f} KB)")
        return {
            "output_docx_path": result_path,
            "company_slug": company_slug,
            "current_step": "filled",
        }
    except Exception as exc:
        msg = f"fill_node error: {exc}"
        logger.exception(msg)
        return {"errors": [msg], "current_step": "fill_failed"}

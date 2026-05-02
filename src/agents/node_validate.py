"""Node 2: Apply UCP600 / ISBP821 / Incoterms rules to validate and enhance LC data."""
from __future__ import annotations
from ..config import BANK_DEFAULT, get_bank_metadata
from ..models.state import LCAgentState
from ..tools.lc_rules_validator import validate_and_enhance
from ..utils.logger import get_logger, timed_node

logger = get_logger("node.validate")


@timed_node
def validate_node(state: LCAgentState) -> dict:
    """Validate extracted LC fields and apply international trade rules."""
    lc_data = state.get("lc_data")
    if not lc_data:
        msg = "validate_node: no lc_data in state — extraction may have failed."
        logger.error(msg)
        return {"errors": [msg], "current_step": "validate_failed"}

    bank = state.get("bank") or BANK_DEFAULT
    bank_meta = get_bank_metadata(bank)

    logger.info("Applying UCP600 / ISBP821 / Incoterms rules...")
    try:
        data = dict(lc_data)
        # Inject issuing bank info from bank param (not extractable from contract)
        if bank_meta:
            data.setdefault("issuing_bank_name", bank_meta["display_name"])
            data.setdefault("issuing_bank_bic", bank_meta["bic"])
            data.setdefault("vcb_branch", bank_meta["short_name"])
        enhanced = validate_and_enhance(data)
        warnings = enhanced.get("validation_warnings", [])
        notes = enhanced.get("compliance_notes", [])
        logger.info(
            f"Validation done — {len(warnings)} warnings, {len(notes)} compliance notes"
        )
        if warnings:
            for w in warnings:
                logger.warning(f"  ⚠ {w}")
        return {
            "lc_data": enhanced,
            "current_step": "validated",
        }
    except Exception as exc:
        msg = f"validate_node error: {exc}"
        logger.exception(msg)
        return {"errors": [msg], "current_step": "validate_failed"}

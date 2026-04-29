"""Node 2: Apply UCP600 / ISBP821 / Incoterms rules to validate and enhance LC data."""
from __future__ import annotations
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

    logger.info("Applying UCP600 / ISBP821 / Incoterms rules...")
    try:
        enhanced = validate_and_enhance(dict(lc_data))
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

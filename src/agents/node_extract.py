"""Node 1: Extract LC application fields from the contract document."""
from __future__ import annotations
import logging
from ..models.state import LCAgentState
from ..tools.contract_extractor import extract_contract_text, extract_lc_fields_from_contract
from ..utils.logger import get_logger, timed_node

logger = get_logger("node.extract")


@timed_node
def extract_node(state: LCAgentState) -> dict:
    """Extract structured LC fields from the uploaded contract."""
    contract_path = state["contract_path"]
    quality_feedback = state.get("quality_feedback")
    retry_count = state.get("retry_count", 0)

    logger.info(f"Extracting LC fields from: {contract_path}  (retry={retry_count})")
    try:
        contract_text = extract_contract_text(contract_path)
        if not contract_text.strip():
            msg = f"Contract file produced empty text: {contract_path}"
            logger.error(msg)
            return {"errors": [msg], "current_step": "extract_failed"}

        lc_data = extract_lc_fields_from_contract(contract_text, quality_feedback=quality_feedback)
        logger.info(
            f"Extraction complete — "
            f"applicant={lc_data.get('applicant_name')!r}  "
            f"currency={lc_data.get('currency')}  amount={lc_data.get('amount')}"
        )
        return {
            "lc_data": lc_data,
            "current_step": "extracted",
            "quality_feedback": None,  # clear after retry
        }
    except Exception as exc:
        msg = f"extract_node error: {exc}"
        logger.exception(msg)
        return {"errors": [msg], "current_step": "extract_failed"}

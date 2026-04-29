"""Node 4: Fill the Vietcombank LC DOCX template with validated data."""
from __future__ import annotations
import os
from pathlib import Path
from ..models.state import LCAgentState
from ..utils.docx_filler import fill_lc_template
from ..utils.logger import get_logger, timed_node
from ..config import LC_TEMPLATE_PATH

logger = get_logger("node.fill")


@timed_node
def fill_node(state: LCAgentState) -> dict:
    """Fill the LC application DOCX template with the validated data."""
    lc_data = state.get("lc_data")
    if not lc_data:
        msg = "fill_node: no lc_data in state."
        logger.error(msg)
        return {"errors": [msg], "current_step": "fill_failed"}

    output_dir = state.get("output_dir", "data/outputs/default")
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    # Derive output filename from contract
    contract_name = Path(state.get("contract_path", "contract")).stem
    output_path = str(Path(output_dir) / f"LC-Application-{contract_name}.docx")

    template_path = str(LC_TEMPLATE_PATH)
    if not Path(template_path).exists():
        msg = f"LC template not found: {template_path}"
        logger.error(msg)
        return {"errors": [msg], "current_step": "fill_failed"}

    logger.info(f"Filling LC template → {output_path}")
    try:
        result_path = fill_lc_template(lc_data, template_path, output_path)
        size_kb = os.path.getsize(result_path) / 1024
        logger.info(f"LC application DOCX saved — {result_path} ({size_kb:.1f} KB)")
        return {
            "output_docx_path": result_path,
            "current_step": "filled",
        }
    except Exception as exc:
        msg = f"fill_node error: {exc}"
        logger.exception(msg)
        return {"errors": [msg], "current_step": "fill_failed"}

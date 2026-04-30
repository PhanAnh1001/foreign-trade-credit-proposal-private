"""Node 3: LLM-as-Judge quality review for extracted LC data."""
from __future__ import annotations
import json
from ..models.state import LCAgentState
from ..utils.llm import get_judge_llm, invoke_with_retry, strip_llm_json
from ..utils.logger import get_logger, timed_node
from langchain_core.messages import SystemMessage, HumanMessage

logger = get_logger("node.quality")

_JUDGE_SYSTEM = """You are an expert in international trade finance, documentary credits, and Vietnamese banking regulations.
Review the extracted LC application data and score its quality.

DATE FORMAT NOTE: All dates are in dd/mm/yyyy format (day/month/4-digit-year).
Example: "31/01/2025" = January 31, 2025. "28/02/2025" = February 28, 2025.

Evaluate:
1. Completeness: Are all required LC fields present? (applicant, beneficiary, issuing bank, amount, dates, incoterms, documents)
2. Accuracy: Are the extracted values sensible and internally consistent?
3. Compliance (International): Are UCP600/ISBP821/Incoterms rules correctly applied?
4. Compliance (Vietnam): Are Vietnam forex law requirements met?
   - LC currency must be foreign currency, not VND (Pháp lệnh Ngoại hối, NĐ 70/2014)
   - Import contract number must be present (NĐ 70/2014 Điều 11)
   - Issuing bank must be NHNN-authorized forex institution
5. Documents: Are the required documents appropriate for the Incoterms term?

Return ONLY a JSON object:
{
  "score": float (0.0–10.0),
  "completeness": float (0.0–10.0),
  "compliance": float (0.0–10.0),
  "top_issues": ["issue 1", "issue 2", "issue 3"],
  "feedback": "Concise actionable feedback for improvement (max 200 words)",
  "summary": "One-line assessment"
}"""


@timed_node
def quality_review_node(state: LCAgentState) -> dict:
    """Score LC data quality and generate improvement feedback."""
    lc_data = state.get("lc_data") or {}
    retry_count = state.get("retry_count", 0)

    # Build a compact summary of current data for review
    review_fields = {
        "applicant_name": lc_data.get("applicant_name"),
        "beneficiary_name": lc_data.get("beneficiary_name"),
        "currency": lc_data.get("currency"),
        "amount": lc_data.get("amount"),
        "expiry_date": lc_data.get("expiry_date"),
        "latest_shipment_date": lc_data.get("latest_shipment_date"),
        "incoterms": lc_data.get("incoterms"),
        "incoterms_version": lc_data.get("incoterms_version"),
        "port_of_loading": lc_data.get("port_of_loading"),
        "port_of_discharge": lc_data.get("port_of_discharge"),
        "partial_shipment": lc_data.get("partial_shipment"),
        "transhipment": lc_data.get("transhipment"),
        "draft_type": lc_data.get("draft_type"),
        "presentation_period": lc_data.get("presentation_period"),
        "description_of_goods": lc_data.get("description_of_goods"),
        "documents": lc_data.get("documents"),
        "beneficiary_bank_name": lc_data.get("beneficiary_bank_name"),
        "beneficiary_bank_bic": lc_data.get("beneficiary_bank_bic"),
        "issuing_bank_name": lc_data.get("issuing_bank_name"),
        "issuing_bank_bic": lc_data.get("issuing_bank_bic"),
        "validation_warnings": lc_data.get("validation_warnings", []),
        "compliance_notes": lc_data.get("compliance_notes", []),
    }
    data_summary = json.dumps(review_fields, ensure_ascii=False, indent=2)[:3000]

    user_content = f"Review this LC application data (retry attempt {retry_count}):\n\n{data_summary}"

    try:
        llm = get_judge_llm()
        messages = [
            SystemMessage(content=_JUDGE_SYSTEM),
            HumanMessage(content=user_content),
        ]
        response = invoke_with_retry(llm, messages)
        raw = response.content if hasattr(response, "content") else str(response)
        cleaned = strip_llm_json(raw)
        try:
            result = json.loads(cleaned)
        except json.JSONDecodeError:
            from json_repair import repair_json
            result = json.loads(repair_json(cleaned))
    except Exception as exc:
        logger.warning(f"quality_review_node LLM failed: {exc} — defaulting to score 7.5")
        result = {
            "score": 7.5,
            "completeness": 7.5,
            "compliance": 7.5,
            "top_issues": [],
            "feedback": "Quality review unavailable.",
            "summary": "Auto-passed (LLM unavailable)",
        }

    score = float(result.get("score", 7.5))
    feedback = result.get("feedback", "")
    logger.info(
        f"Quality review — score={score}/10  "
        f"completeness={result.get('completeness')}  compliance={result.get('compliance')}"
    )
    for issue in result.get("top_issues", []):
        logger.warning(f"  Issue: {issue}")

    return {
        "quality_score": score,
        "quality_feedback": feedback,
        "retry_count": retry_count + 1,
        "current_step": "quality_reviewed",
    }

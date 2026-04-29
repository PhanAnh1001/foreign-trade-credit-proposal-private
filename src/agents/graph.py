"""LangGraph graph definition for the LC application agent."""
from __future__ import annotations
import uuid
import time as _time
from langgraph.graph import StateGraph, END
from ..models.state import LCAgentState
from .node_extract import extract_node
from .node_validate import validate_node
from .node_quality import quality_review_node
from .node_fill import fill_node
from ..utils.logger import get_logger, setup_langsmith_tracing

logger = get_logger("graph")

_QUALITY_THRESHOLD = 7.0
_MAX_RETRIES = 1  # allow exactly 1 retry after quality review


def route_after_review(state: LCAgentState) -> str:
    """Decide: fill (score >= threshold), retry (first attempt), or end with warnings."""
    score = state.get("quality_score") or 0.0
    retry_count = state.get("retry_count", 0)

    if score >= _QUALITY_THRESHOLD:
        logger.info(f"Routing → fill  (score={score:.1f} >= {_QUALITY_THRESHOLD})")
        return "fill"

    # retry_count was incremented by quality_review_node, so after first review it is 1
    if retry_count <= _MAX_RETRIES:
        logger.info(f"Routing → retry extract  (score={score:.1f} < {_QUALITY_THRESHOLD}, retry={retry_count})")
        return "retry_extract"

    # After max retries, proceed with warnings
    logger.warning(
        f"Routing → fill with warnings  "
        f"(score={score:.1f} after {retry_count} retries)"
    )
    return "fill"


def build_lc_graph():
    """Build and compile the LC application LangGraph.

    Topology:
        extract → validate → quality_review ──► fill → END
                                            └──► extract (retry once)
    """
    builder = StateGraph(LCAgentState)

    builder.add_node("extract", extract_node)
    builder.add_node("validate", validate_node)
    builder.add_node("quality_review", quality_review_node)
    builder.add_node("fill", fill_node)

    builder.set_entry_point("extract")
    builder.add_edge("extract", "validate")
    builder.add_edge("validate", "quality_review")
    builder.add_conditional_edges(
        "quality_review",
        route_after_review,
        {
            "fill": "fill",
            "retry_extract": "extract",
        },
    )
    builder.add_edge("fill", END)

    return builder.compile()


def run_lc_application(
    contract_path: str,
    output_dir: str | None = None,
) -> dict:
    """Run the full LC application pipeline end-to-end.

    Args:
        contract_path: Path to the foreign trade contract (TXT/PDF/DOCX).
        output_dir:    Directory for output DOCX. Defaults to data/outputs/default.

    Returns:
        Final LCAgentState dict.
    """
    setup_langsmith_tracing()
    graph = build_lc_graph()

    from ..config import get_output_dir
    resolved_output = output_dir or str(get_output_dir("default"))

    run_id = str(uuid.uuid4())
    initial: LCAgentState = {
        "run_id": run_id,
        "contract_path": contract_path,
        "output_dir": resolved_output,
        "lc_data": None,
        "output_docx_path": None,
        "retry_count": 0,
        "quality_score": None,
        "quality_feedback": None,
        "errors": [],
        "current_step": "started",
        "messages": [],
    }

    logger.info("=" * 60)
    logger.info(f"LC Application Agent  run_id={run_id}")
    logger.info(f"  contract  : {contract_path}")
    logger.info(f"  output_dir: {resolved_output}")
    logger.info("=" * 60)

    t0 = _time.perf_counter()
    final = graph.invoke(initial)
    elapsed = _time.perf_counter() - t0

    score = final.get("quality_score")
    errors = final.get("errors") or []

    logger.info("=" * 60)
    logger.info(f"COMPLETE [{elapsed:.1f}s]  run_id={run_id}")
    logger.info(f"  step      : {final.get('current_step')}")
    logger.info(f"  retries   : {final.get('retry_count', 0) - 1}")
    logger.info(f"  quality   : {score}/10" if score else "  quality   : n/a")
    logger.info(f"  output    : {final.get('output_docx_path')}")
    if errors:
        for err in errors:
            logger.error(f"  ERROR: {err}")
    logger.info("=" * 60)

    return final

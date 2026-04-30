from __future__ import annotations
from typing import TypedDict, Optional, Any, Annotated
from operator import add


class LCAgentState(TypedDict):
    # ── Run identity ─────────────────────────────────────────────────────────
    run_id: str

    # ── Input ────────────────────────────────────────────────────────────────
    contract_path: str
    bank: str         # bank slug, e.g. "vietcombank" — determines template + output path
    output_dir: str   # explicit override; empty string = derive from bank/company

    # ── Extracted & validated data ───────────────────────────────────────────
    lc_data: Optional[dict]   # LCApplicationData as dict (JSON-serialisable)

    # ── Output ───────────────────────────────────────────────────────────────
    output_docx_path: Optional[str]
    company_slug: str  # slugified applicant_name, set by fill_node

    # ── Quality feedback loop ────────────────────────────────────────────────
    retry_count: int
    quality_score: Optional[float]
    quality_feedback: Optional[str]

    # ── Control (Annotated reducers for safe parallel writes) ─────────────────
    errors: Annotated[list[str], add]
    current_step: str   # last-write-wins
    messages: Annotated[list[Any], add]

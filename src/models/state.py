from __future__ import annotations
from typing import TypedDict, Optional, Any, Annotated
from operator import add


class LCAgentState(TypedDict):
    # ── Run identity ─────────────────────────────────────────────────────────
    run_id: str

    # ── Input ────────────────────────────────────────────────────────────────
    contract_path: str
    output_dir: str

    # ── Extracted & validated data ───────────────────────────────────────────
    lc_data: Optional[dict]   # LCApplicationData as dict (JSON-serialisable)

    # ── Output ───────────────────────────────────────────────────────────────
    output_docx_path: Optional[str]

    # ── Quality feedback loop ────────────────────────────────────────────────
    retry_count: int
    quality_score: Optional[float]
    quality_feedback: Optional[str]

    # ── Control (Annotated reducers for safe parallel writes) ─────────────────
    errors: Annotated[list[str], add]
    current_step: str   # last-write-wins
    messages: Annotated[list[Any], add]

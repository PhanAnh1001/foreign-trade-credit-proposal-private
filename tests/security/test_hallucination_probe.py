"""
Bước 5.5c — Hallucination probe cho LC Application Agent.
Kiểm tra rằng fields không có trong contract được trả về null, không bị bịa.
Các test cần GROQ_API_KEY; bỏ qua nếu không có key.
"""
from __future__ import annotations

import os
import pytest

GROQ_AVAILABLE = bool(os.getenv("GROQ_API_KEY"))
pytestmark = pytest.mark.skipif(not GROQ_AVAILABLE, reason="GROQ_API_KEY not set")

# Contract tối giản — chỉ có amount và incoterms, không có nhiều field khác
_MINIMAL_CONTRACT = """
SALES CONTRACT
Contract No.: MIN-001
Seller: ABC Export Co.
Buyer: XYZ Import JSC
Goods: Electronic components
Amount: USD 50,000.00 CIF
Shipment: March 2025
"""

# Contract hoàn toàn trống
_EMPTY_CONTRACT = "   "


def test_minimal_contract_null_fields():
    """Fields không có trong contract phải là null, không được bịa."""
    from src.tools.contract_extractor import extract_lc_fields_from_contract

    result = extract_lc_fields_from_contract(_MINIMAL_CONTRACT)

    # Fields này không có trong contract tối giản
    should_be_null = [
        "applicant_address",
        "beneficiary_address",
        "beneficiary_account_no",
        "beneficiary_bank_name",
        "beneficiary_bank_bic",
        "expiry_date",
        "port_of_loading",
        "port_of_discharge",
    ]
    fabricated = [f for f in should_be_null if result.get(f) not in (None, "", "null")]
    assert not fabricated, (
        f"LLM bịa ra các fields không có trong contract: {fabricated}\n"
        f"Values: { {f: result.get(f) for f in fabricated} }"
    )


def test_minimal_contract_known_fields_extracted():
    """Fields có trong contract tối giản phải được extract đúng."""
    from src.tools.contract_extractor import extract_lc_fields_from_contract

    result = extract_lc_fields_from_contract(_MINIMAL_CONTRACT)

    assert result.get("currency") == "USD", f"currency sai: {result.get('currency')}"
    assert result.get("amount") == "50000.00", f"amount sai: {result.get('amount')}"
    assert result.get("incoterms") in ("CIF", "cif"), f"incoterms sai: {result.get('incoterms')}"


def test_empty_contract_all_null():
    """Contract rỗng → tất cả fields phải null, không được hallucinate."""
    from src.tools.contract_extractor import extract_lc_fields_from_contract

    result = extract_lc_fields_from_contract(_EMPTY_CONTRACT)

    # Loại trừ các defaults hợp lệ từ rule engine / schema:
    # - lc_type, issuance_method, amount_tolerance: prompt defaults
    # - presentation_period: UCP600 Art.14c default (21 ngày) — LLM có thể biết
    # - documents: empty dict với all-null values là schema default, không phải dữ liệu bịa
    ALLOWED_DEFAULTS = {"lc_type", "issuance_method", "amount_tolerance", "presentation_period"}

    def _is_empty_docs(v) -> bool:
        if not isinstance(v, dict):
            return False
        return all(item in (None, "", [], {}) for item in v.values())

    non_null = {
        k: v for k, v in result.items()
        if v not in (None, "", "null", [], {})
        and k not in ALLOWED_DEFAULTS
        and not _is_empty_docs(v)
    }
    assert not non_null, (
        f"LLM hallucinated fields từ contract rỗng: {non_null}"
    )


def test_contract_number_not_fabricated():
    """contract_number phải đúng với contract, không bịa số khác."""
    from src.tools.contract_extractor import extract_lc_fields_from_contract

    result = extract_lc_fields_from_contract(_MINIMAL_CONTRACT)
    extracted = result.get("contract_number")

    if extracted is not None:
        assert "MIN-001" in str(extracted), (
            f"contract_number bị bịa: got {extracted!r}, expected 'MIN-001'"
        )

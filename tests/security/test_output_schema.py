"""
Bước 5.5d — Output schema validation cho LC Application Agent.
Kiểm tra Pydantic model reject dữ liệu sai schema. Không cần API key.
"""
from __future__ import annotations

import pytest
from pydantic import ValidationError


def _valid_data() -> dict:
    return {
        "applicant_name": "Test Co.",
        "applicant_address": "123 Main St",
        "beneficiary_name": "Seller Co.",
        "beneficiary_address": "456 Trade Rd",
        "currency": "USD",
        "amount": "100000.00",
        "lc_type": "Irrevocable",
        "issuance_method": "SWIFT",
        "incoterms": "CIF",
        "incoterms_version": "2020",
        "partial_shipment": "Not allowed",
        "transhipment": "Not allowed",
        "draft_type": "Sight",
        "presentation_period": "21",
        "amount_tolerance": "0",
    }


def test_valid_data_passes_schema():
    """Data hợp lệ phải pass Pydantic validation."""
    from src.models.lc_application import LCApplicationData

    data = _valid_data()
    obj = LCApplicationData(**data)
    assert obj.applicant_name == "Test Co."
    assert obj.currency == "USD"


def test_null_optional_fields_accepted():
    """Optional fields có thể là None."""
    from src.models.lc_application import LCApplicationData

    data = _valid_data()
    data.update({
        "beneficiary_account_no": None,
        "beneficiary_bank_name": None,
        "expiry_date": None,
        "port_of_loading": None,
        "port_of_discharge": None,
        "contract_number": None,
    })
    obj = LCApplicationData(**data)
    assert obj.beneficiary_account_no is None


def test_validate_and_enhance_preserves_required_fields():
    """validate_and_enhance không được xóa required fields."""
    from src.tools.lc_rules_validator import validate_and_enhance

    data = _valid_data()
    data["contract_number"] = "TEST-001"
    result = validate_and_enhance(data)

    assert result.get("applicant_name") == "Test Co."
    assert result.get("currency") == "USD"
    assert result.get("amount") == "100000.00"


def test_validate_cif_adds_insurance():
    """CIF → validate_and_enhance thêm insurance certificate vào documents."""
    from src.tools.lc_rules_validator import validate_and_enhance

    data = _valid_data()
    data["incoterms"] = "CIF"
    data["documents"] = {}
    result = validate_and_enhance(data)

    docs = result.get("documents", {})
    assert docs.get("insurance_certificate"), (
        "CIF phải có insurance_certificate sau validate_and_enhance"
    )


def test_validate_fob_no_insurance():
    """FOB → validate_and_enhance không thêm insurance certificate."""
    from src.tools.lc_rules_validator import validate_and_enhance

    data = _valid_data()
    data["incoterms"] = "FOB"
    data["documents"] = {}
    result = validate_and_enhance(data)

    docs = result.get("documents", {})
    insurance = docs.get("insurance_certificate")
    assert not insurance, (
        f"FOB không được có insurance_certificate, got: {insurance!r}"
    )


def test_presentation_period_default_21():
    """UCP600 Art.14c: presentation period mặc định 21 ngày nếu chưa set."""
    from src.tools.lc_rules_validator import validate_and_enhance

    data = _valid_data()
    data.pop("presentation_period", None)
    result = validate_and_enhance(data)

    period = str(result.get("presentation_period", ""))
    assert period.startswith("21"), (
        f"presentation_period phải bắt đầu bằng '21' (UCP600 Art.14c), got: {period!r}"
    )

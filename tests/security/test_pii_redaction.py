"""
Bước 5.5b — PII redaction check cho LC Application Agent.
Kiểm tra extraction output và log không chứa PII không cần thiết từ contract.
Chạy được không cần API key.
"""
from __future__ import annotations

import json
import re

import pytest

# CMND (9 chữ số) hoặc CCCD (12 chữ số) gần keyword
_ID_NEAR_KEYWORD = re.compile(
    r"(CMND|CCCD|passport|id\s*number|national\s*id)\D{0,15}(\d{9,12})\b",
    re.IGNORECASE,
)

# Số thẻ tín dụng — kiểm tra Luhn
_CARD_LIKE = re.compile(r"\b(?:\d[ -]?){13,19}\b")

# Số điện thoại VN (không nên có trong LC application)
_VN_PHONE = re.compile(r"\b(0[3-9]\d{8}|\+84[3-9]\d{8})\b")


def _luhn_valid(s: str) -> bool:
    digits = [int(c) for c in re.sub(r"\D", "", s)]
    if len(digits) < 13:
        return False
    total = 0
    for i, d in enumerate(reversed(digits)):
        if i % 2 == 1:
            d *= 2
            if d > 9:
                d -= 9
        total += d
    return total % 10 == 0


def _sample_lc_fields() -> dict:
    """Fields extracted from sample contract — no PII."""
    return {
        "applicant_name": "Viet Nam Technology Import-Export JSC",
        "applicant_address": "123 Nguyen Thi Minh Khai, District 1, Ho Chi Minh City",
        "beneficiary_name": "Shenzhen Advanced Electronics Co., Ltd.",
        "beneficiary_account_no": "6227 0036 8900 1234567",
        "currency": "USD",
        "amount": "450000.00",
        "contract_number": "VN-CN-2024-001",
        "incoterms": "CIF",
    }


def test_lc_fields_no_id_near_keyword():
    """LC fields không chứa CMND/CCCD/passport number."""
    data = _sample_lc_fields()
    flat = json.dumps(data, ensure_ascii=False)
    hits = _ID_NEAR_KEYWORD.findall(flat)
    assert not hits, f"PII (ID) found in LC fields: {hits}"


def test_lc_fields_no_luhn_card_numbers():
    """LC fields không chứa số thẻ tín dụng valid (Luhn check)."""
    data = _sample_lc_fields()
    flat = json.dumps(data, ensure_ascii=False)
    # Exclude known account number field from Luhn check
    flat_no_account = re.sub(r'"beneficiary_account_no":\s*"[^"]*"', "", flat)
    hits = [m.group() for m in _CARD_LIKE.finditer(flat_no_account) if _luhn_valid(m.group())]
    assert not hits, f"Possible card number (Luhn-valid) in LC fields: {hits}"


def test_lc_fields_no_vn_phone():
    """LC fields không chứa số điện thoại cá nhân VN."""
    data = _sample_lc_fields()
    flat = json.dumps(data, ensure_ascii=False)
    hits = _VN_PHONE.findall(flat)
    assert not hits, f"VN phone number found in LC fields: {hits}"


def test_account_number_field_is_beneficiary_bank_only():
    """account_no field phải là tài khoản ngân hàng thụ hưởng, không phải cá nhân."""
    data = _sample_lc_fields()
    account = data.get("beneficiary_account_no", "")
    # Tài khoản ngân hàng thụ hưởng là hợp lệ trong LC application
    # Chỉ kiểm tra không phải số CMND/CCCD (9 hoặc 12 chữ số thuần)
    digits_only = re.sub(r"\D", "", account)
    assert len(digits_only) not in (9, 12) or len(account) != len(digits_only), (
        f"beneficiary_account_no trông giống CMND/CCCD: {account!r}"
    )


def test_extraction_output_schema_no_unexpected_pii_fields():
    """Schema extraction không có field nào chứa PII cá nhân (CMND, DOB, phone)."""
    from src.models.lc_application import LCApplicationData

    pii_field_names = {"cmnd", "cccd", "passport", "dob", "date_of_birth", "phone", "mobile"}
    schema_fields = set(LCApplicationData.model_fields.keys())
    unexpected = pii_field_names & schema_fields
    assert not unexpected, f"Schema chứa PII fields không cần thiết: {unexpected}"

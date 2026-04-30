"""Tests for UCP600 / ISBP821 / Incoterms / Vietnam forex law rules validator."""
import pytest
from src.tools.lc_rules_validator import (
    apply_ucp600_defaults,
    apply_incoterms_rules,
    apply_isbp821_defaults,
    apply_vietnam_forex_rules,
    validate_completeness,
    validate_and_enhance,
)


def _base_data(**kwargs) -> dict:
    """Minimal valid LC data dict."""
    base = {
        "lc_type": "Irrevocable",
        "issuance_method": "SWIFT",
        "currency": "USD",
        "amount": "450000.00",
        "expiry_date": "28/02/2025",
        "latest_shipment_date": "31/01/2025",
        "incoterms": "CIF",
        "incoterms_version": "2020",
        "named_port": "Ho Chi Minh City Port",
        "port_of_loading": "Shekou Port, Shenzhen",
        "port_of_discharge": "Cat Lai Port, Ho Chi Minh City",
        "partial_shipment": "Not allowed",
        "transhipment": "Not allowed",
        "draft_type": "Sight",
        "presentation_period": "21",
        "amount_tolerance": "0",
        "issuing_bank_charges_for": "Applicant",
        "other_bank_charges_for": "Beneficiary",
        "contract_number": "VN-CN-2024-001",
        "applicant_name": "Viet Nam Technology Import-Export JSC",
        "beneficiary_name": "Shenzhen Advanced Electronics Co., Ltd.",
        "description_of_goods": "Electronic Circuit Boards",
        "beneficiary_bank_name": "Bank of China",
        "issuing_bank_name": "Joint Stock Commercial Bank for Foreign Trade of Vietnam (Vietcombank)",
        "issuing_bank_bic": "BFTVVNVX",
        "documents": {
            "commercial_invoice": "3 originals",
            "bill_of_lading": "Full set of 3/3 originals",
            "packing_list": "1 original + 2 copies",
            "certificate_of_origin": "1 original",
            "insurance_certificate": None,
            "inspection_certificate": None,
            "other_documents": [],
        },
        "validation_warnings": [],
        "compliance_notes": [],
    }
    base.update(kwargs)
    return base


class TestUCP600Defaults:
    def test_default_lc_type_applied(self):
        data = _base_data(lc_type=None)
        result = apply_ucp600_defaults(data)
        assert result["lc_type"] == "Irrevocable"

    def test_presentation_period_default(self):
        data = _base_data(presentation_period=None)
        result = apply_ucp600_defaults(data)
        assert result["presentation_period"] == "21 days after date of shipment"

    def test_expiry_date_missing_warns(self):
        data = _base_data(expiry_date=None)
        result = apply_ucp600_defaults(data)
        assert any("xpiry" in w for w in result["validation_warnings"])

    def test_shipment_before_expiry(self):
        data = _base_data(latest_shipment_date="31/01/2025", expiry_date="28/02/2025")
        result = apply_ucp600_defaults(data)
        assert any("Date check" in n and "✓" in n for n in result["compliance_notes"])

    def test_shipment_after_expiry_warns(self):
        data = _base_data(latest_shipment_date="01/03/2025", expiry_date="28/02/2025")
        result = apply_ucp600_defaults(data)
        assert any("shipment date" in w.lower() for w in result["validation_warnings"])


class TestIncotermsRules:
    def test_cif_adds_insurance(self):
        data = _base_data(incoterms="CIF")
        # Remove insurance to test injection
        data["documents"]["insurance_certificate"] = None
        result = apply_incoterms_rules(data)
        assert result["documents"]["insurance_certificate"] is not None
        assert "110" in result["documents"]["insurance_certificate"]

    def test_cip_adds_allrisks_insurance(self):
        data = _base_data(incoterms="CIP", incoterms_version="2020")
        data["documents"]["insurance_certificate"] = None
        result = apply_incoterms_rules(data)
        ins = result["documents"]["insurance_certificate"]
        assert ins is not None
        assert "all risks" in ins.lower() or "Institute Cargo Clauses A" in ins

    def test_fob_no_insurance_added(self):
        data = _base_data(incoterms="FOB")
        data["documents"]["insurance_certificate"] = None
        result = apply_incoterms_rules(data)
        assert result["documents"]["insurance_certificate"] is None

    def test_cfr_no_insurance_added(self):
        data = _base_data(incoterms="CFR")
        data["documents"]["insurance_certificate"] = None
        result = apply_incoterms_rules(data)
        assert result["documents"]["insurance_certificate"] is None

    def test_no_incoterms_warns(self):
        data = _base_data(incoterms=None)
        result = apply_incoterms_rules(data)
        assert any("Incoterms" in w for w in result["validation_warnings"])


class TestISBP821Defaults:
    def test_commercial_invoice_default_set(self):
        data = _base_data()
        data["documents"]["commercial_invoice"] = None
        result = apply_isbp821_defaults(data)
        assert result["documents"]["commercial_invoice"] is not None

    def test_english_condition_added(self):
        data = _base_data(additional_conditions=None)
        result = apply_isbp821_defaults(data)
        assert "English" in (result.get("additional_conditions") or "")


class TestValidateCompleteness:
    def test_complete_data_no_warnings(self):
        data = _base_data()
        result = validate_completeness(data)
        assert not any("Required field missing" in w for w in result["validation_warnings"])

    def test_missing_amount_warns(self):
        data = _base_data(amount=None)
        result = validate_completeness(data)
        assert any("Amount" in w for w in result["validation_warnings"])

    def test_missing_description_warns(self):
        data = _base_data(description_of_goods=None)
        result = validate_completeness(data)
        assert any("goods" in w.lower() for w in result["validation_warnings"])


class TestVietnamForexRules:
    def test_vn01_vnd_currency_warns(self):
        data = _base_data(currency="VND")
        result = apply_vietnam_forex_rules(data)
        assert any("VN-01" in w and "VND" in w for w in result["validation_warnings"])

    def test_vn01_usd_currency_ok(self):
        data = _base_data(currency="USD")
        result = apply_vietnam_forex_rules(data)
        assert not any("VND" in w for w in result["validation_warnings"])
        assert any("VN-01" in n and "✓" in n for n in result["compliance_notes"])

    def test_vn01_uncommon_currency_notes(self):
        data = _base_data(currency="CHF")
        result = apply_vietnam_forex_rules(data)
        assert any("CHF" in n for n in result["compliance_notes"])

    def test_vn02_missing_contract_number_warns(self):
        data = _base_data(contract_number=None)
        result = apply_vietnam_forex_rules(data)
        assert any("VN-02" in w for w in result["validation_warnings"])

    def test_vn02_contract_number_present_ok(self):
        data = _base_data(contract_number="VN-CN-2024-001")
        result = apply_vietnam_forex_rules(data)
        assert any("VN-02" in n and "✓" in n for n in result["compliance_notes"])

    def test_vn03_vietcombank_authorized(self):
        data = _base_data(
            issuing_bank_name="Joint Stock Commercial Bank for Foreign Trade of Vietnam (Vietcombank)",
            issuing_bank_bic="BFTVVNVX",
        )
        result = apply_vietnam_forex_rules(data)
        assert any("VN-03" in n and "✓" in n for n in result["compliance_notes"])

    def test_vn04_import_lc_permitted_note(self):
        data = _base_data()
        result = apply_vietnam_forex_rules(data)
        assert any("VN-04" in n for n in result["compliance_notes"])

    def test_vn06_regulated_goods_warns(self):
        data = _base_data(description_of_goods="Industrial Chemicals and Solvents")
        result = apply_vietnam_forex_rules(data)
        assert any("VN-06" in w for w in result["validation_warnings"])

    def test_vn06_normal_goods_ok(self):
        data = _base_data(description_of_goods="Electronic Circuit Boards")
        result = apply_vietnam_forex_rules(data)
        assert any("VN-06" in n and "✓" in n for n in result["compliance_notes"])


class TestValidateAndEnhance:
    def test_full_pipeline_cif(self):
        data = _base_data(incoterms="CIF")
        data["documents"]["insurance_certificate"] = None
        result = validate_and_enhance(data)
        # Insurance should be added for CIF
        assert result["documents"]["insurance_certificate"] is not None
        # No critical warnings for complete data
        critical = [w for w in result["validation_warnings"] if "Required" in w]
        assert len(critical) == 0

    def test_full_pipeline_fob(self):
        data = _base_data(incoterms="FOB")
        result = validate_and_enhance(data)
        # No insurance for FOB
        assert not result["documents"].get("insurance_certificate")

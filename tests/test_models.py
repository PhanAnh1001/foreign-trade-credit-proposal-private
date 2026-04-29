"""Tests for Pydantic models."""
import pytest
from src.models.lc_application import LCApplicationData, DocumentRequirements
from src.models.state import LCAgentState


def test_lc_application_data_defaults():
    data = LCApplicationData()
    assert data.lc_type == "Irrevocable"
    assert data.issuance_method == "SWIFT"
    assert data.partial_shipment == "Not allowed"
    assert data.transhipment == "Not allowed"
    assert data.draft_type == "Sight"
    assert data.presentation_period == "21"
    assert data.amount_tolerance == "0"
    assert data.issuing_bank_charges_for == "Applicant"
    assert data.other_bank_charges_for == "Beneficiary"
    assert data.validation_warnings == []
    assert data.compliance_notes == []


def test_currency_uppercased():
    data = LCApplicationData(currency="usd")
    assert data.currency == "USD"


def test_incoterms_uppercased():
    data = LCApplicationData(incoterms="cif")
    assert data.incoterms == "CIF"


def test_document_requirements_defaults():
    docs = DocumentRequirements()
    assert "original" in docs.commercial_invoice.lower()
    assert "bill" in docs.bill_of_lading.lower() and "lading" in docs.bill_of_lading.lower()
    assert docs.packing_list is not None and len(docs.packing_list) > 0
    assert docs.insurance_certificate is None
    assert docs.other_documents == []


def test_model_dump_for_filling():
    data = LCApplicationData(
        applicant_name="Test Corp",
        currency="USD",
        amount="100000",
    )
    d = data.model_dump_for_filling()
    assert d["applicant_name"] == "Test Corp"
    assert d["currency"] == "USD"
    assert "documents" in d


def test_lc_agent_state_type():
    # LCAgentState is a TypedDict — check it can be instantiated as a dict
    state: LCAgentState = {
        "run_id": "test-123",
        "contract_path": "data/sample/contract.txt",
        "output_dir": "data/outputs/test",
        "lc_data": None,
        "output_docx_path": None,
        "retry_count": 0,
        "quality_score": None,
        "quality_feedback": None,
        "errors": [],
        "current_step": "started",
        "messages": [],
    }
    assert state["run_id"] == "test-123"
    assert state["retry_count"] == 0

"""End-to-end test: contract → LC application DOCX."""
import os
import pytest
from pathlib import Path

SAMPLE_CONTRACT = Path("data/sample/contract.txt")
REQUIRES_API = pytest.mark.skipif(
    not os.getenv("GROQ_API_KEY"),
    reason="GROQ_API_KEY not set — skipping ETE test",
)


@REQUIRES_API
def test_ete_full_pipeline():
    """Run full LC application pipeline on sample contract."""
    import tempfile
    from src.agents.graph import run_lc_application

    if not SAMPLE_CONTRACT.exists():
        pytest.skip("Sample contract not found")

    with tempfile.TemporaryDirectory() as tmpdir:
        final_state = run_lc_application(
            contract_path=str(SAMPLE_CONTRACT),
            output_dir=tmpdir,
        )

        # Check pipeline completed
        assert final_state.get("current_step") in ("filled", "fill_failed", "validated")

        # Check LC data was extracted
        lc_data = final_state.get("lc_data") or {}
        assert lc_data.get("applicant_name"), "Applicant name should be extracted"
        assert lc_data.get("beneficiary_name"), "Beneficiary name should be extracted"
        assert lc_data.get("currency") == "USD", "Currency should be USD"
        assert lc_data.get("amount"), "Amount should be extracted"
        assert lc_data.get("incoterms") == "CIF", "Incoterms should be CIF"

        # Check CIF insurance was applied by rule engine
        docs = lc_data.get("documents") or {}
        assert docs.get("insurance_certificate") is not None, "CIF requires insurance certificate"

        # Check output DOCX created and is non-trivial (file exists within tmpdir)
        output_path = final_state.get("output_docx_path")
        if final_state.get("current_step") == "filled":
            assert output_path and Path(output_path).exists(), "Output DOCX should exist"
            assert Path(output_path).stat().st_size > 1000, "Output DOCX should be non-trivial"

    # Check quality score (outside tmpdir block — state is still valid)
    score = final_state.get("quality_score")
    if score is not None:
        assert score >= 0, "Quality score should be non-negative"
        assert score <= 10, "Quality score should be <= 10"


@REQUIRES_API
def test_ete_lc_data_from_sample_contract():
    """Verify key fields extracted from the sample contract match expected values."""
    from src.tools.contract_extractor import extract_contract_text, extract_lc_fields_from_contract

    if not SAMPLE_CONTRACT.exists():
        pytest.skip("Sample contract not found")

    text = extract_contract_text(str(SAMPLE_CONTRACT))
    assert len(text) > 500

    data = extract_lc_fields_from_contract(text)

    # These values are explicitly stated in the sample contract
    assert data.get("currency") == "USD"
    assert data.get("incoterms") == "CIF"
    assert "450000" in (data.get("amount") or "")
    assert "Shenzhen Advanced Electronics" in (data.get("beneficiary_name") or "")
    assert "VN-CN-2024-001" in (data.get("contract_number") or "")
    assert data.get("partial_shipment") == "Not allowed"
    assert data.get("transhipment") == "Not allowed"


@REQUIRES_API
def test_ete_multi_bank_vcb():
    """Run pipeline with explicit bank='vietcombank' and verify bank-aware output path."""
    import tempfile
    from src.agents.graph import run_lc_application
    from src.config import BANK_VCB

    if not SAMPLE_CONTRACT.exists():
        pytest.skip("Sample contract not found")

    with tempfile.TemporaryDirectory() as tmpdir:
        final_state = run_lc_application(
            contract_path=str(SAMPLE_CONTRACT),
            output_dir=tmpdir,
            bank=BANK_VCB,
        )

        # Pipeline must complete
        assert final_state.get("current_step") in ("filled", "fill_failed", "validated")

        # bank field preserved in state
        assert final_state.get("bank") == BANK_VCB

        # Output DOCX created
        output_path = final_state.get("output_docx_path")
        if final_state.get("current_step") == "filled":
            assert output_path and Path(output_path).exists(), "Output DOCX should exist"
            assert Path(output_path).stat().st_size > 1000, "Output DOCX should be non-trivial"

        # LC data extracted correctly
        lc_data = final_state.get("lc_data") or {}
        assert lc_data.get("currency") == "USD"
        assert lc_data.get("incoterms") == "CIF"

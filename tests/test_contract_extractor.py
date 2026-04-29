"""Tests for contract text extraction (non-LLM parts only)."""
import os
import pytest
from pathlib import Path
from src.tools.contract_extractor import extract_contract_text

SAMPLE_CONTRACT = Path("data/sample/contract.txt")


def test_extract_txt_contract():
    if not SAMPLE_CONTRACT.exists():
        pytest.skip("Sample contract not found")
    text = extract_contract_text(str(SAMPLE_CONTRACT))
    assert len(text) > 500
    assert "Shenzhen Advanced Electronics" in text
    assert "USD 450,000" in text
    assert "CIF" in text


def test_extract_nonexistent_file():
    text = extract_contract_text("nonexistent/path/contract.txt")
    # Should return empty string, not raise
    assert isinstance(text, str)


def test_extract_empty_txt(tmp_path):
    empty = tmp_path / "empty.txt"
    empty.write_text("")
    text = extract_contract_text(str(empty))
    assert text == ""

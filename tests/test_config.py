"""Tests for multi-bank config helpers."""
import tempfile
import pytest
from pathlib import Path
from src.config import (
    BANK_VCB,
    BANK_BIDV,
    BANK_VIETINBANK,
    BANK_DEFAULT,
    get_bank_template_path,
    get_bank_output_dir,
    slugify_company,
    TEMPLATES_DIR,
    OUTPUTS_DIR,
)


class TestMultiBankConfig:
    def test_bank_constants_defined(self):
        assert BANK_VCB == "vietcombank"
        assert BANK_BIDV == "bidv"
        assert BANK_VIETINBANK == "vietinbank"
        assert BANK_DEFAULT == BANK_VCB

    def test_get_bank_template_path_vcb(self):
        path = get_bank_template_path(BANK_VCB)
        assert path == TEMPLATES_DIR / BANK_VCB / "Application-for-LC-issuance.docx"
        assert path.exists(), f"VCB template must exist at {path}"

    def test_get_bank_template_path_other_bank(self):
        path = get_bank_template_path(BANK_BIDV)
        assert path == TEMPLATES_DIR / BANK_BIDV / "Application-for-LC-issuance.docx"
        # BIDV template may not exist yet — just check the path is correct
        assert path.parent.name == BANK_BIDV

    def test_get_bank_output_dir_creates_directory(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            # Monkeypatch OUTPUTS_DIR via direct call
            from src import config as cfg
            original = cfg.OUTPUTS_DIR
            cfg.OUTPUTS_DIR = Path(tmpdir)
            try:
                out = get_bank_output_dir(BANK_VCB, "test_company")
                assert out.exists()
                assert out == Path(tmpdir) / BANK_VCB / "test_company"
            finally:
                cfg.OUTPUTS_DIR = original

    def test_slugify_company_basic(self):
        assert slugify_company("Viet Nam Technology JSC") == "viet_nam_technology_jsc"

    def test_slugify_company_special_chars(self):
        result = slugify_company("ABC Co., Ltd. (Vietnam)")
        assert " " not in result
        assert "," not in result
        assert "." not in result
        assert "(" not in result

    def test_slugify_company_empty(self):
        assert slugify_company("") == "unknown"
        assert slugify_company(None) == "unknown"

    def test_slugify_company_max_length(self):
        long_name = "A" * 200
        assert len(slugify_company(long_name)) <= 50

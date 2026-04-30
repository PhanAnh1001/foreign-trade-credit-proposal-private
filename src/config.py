from pathlib import Path
import re
import os

BASE_DIR    = Path(__file__).parent.parent
DATA_DIR    = BASE_DIR / "data"
TEMPLATES_DIR = DATA_DIR / "templates" / "docx"
OUTPUTS_DIR = DATA_DIR / "outputs"
SAMPLE_DIR  = DATA_DIR / "sample"

# ── Bank slugs ────────────────────────────────────────────────────────────────
# Lowercase, no spaces — used as directory names under templates/ and outputs/.
BANK_VCB        = "vietcombank"
BANK_BIDV       = "bidv"
BANK_VIETINBANK = "vietinbank"
BANK_DEFAULT    = BANK_VCB

# Legacy constant — kept for backward compatibility (points to VCB template).
LC_TEMPLATE_PATH = TEMPLATES_DIR / BANK_VCB / "Application-for-LC-issuance.docx"


def get_bank_template_path(bank: str) -> Path:
    """Return Path to the LC issuance template for the given bank slug.

    Expected location: data/templates/docx/{bank}/Application-for-LC-issuance.docx
    """
    return TEMPLATES_DIR / bank / "Application-for-LC-issuance.docx"


def slugify_company(name: str) -> str:
    """Convert a company name to a filesystem-safe slug (lowercase, underscores, ≤50 chars)."""
    slug = re.sub(r"[^a-zA-Z0-9\s]", "", (name or "").lower())
    slug = re.sub(r"\s+", "_", slug.strip())
    return slug[:50] or "unknown"


def get_bank_output_dir(bank: str, company_slug: str) -> Path:
    """Create and return data/outputs/{bank}/{company_slug}/"""
    d = OUTPUTS_DIR / bank / company_slug
    d.mkdir(parents=True, exist_ok=True)
    return d


def get_output_dir(run_name: str = "default") -> Path:
    """Legacy: return data/outputs/{run_name}/. Kept for backward compat."""
    d = OUTPUTS_DIR / run_name
    d.mkdir(parents=True, exist_ok=True)
    return d

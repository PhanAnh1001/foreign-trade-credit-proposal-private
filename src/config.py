from pathlib import Path
import os

BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
TEMPLATES_DIR = DATA_DIR / "templates" / "docx"
OUTPUTS_DIR = DATA_DIR / "outputs"
SAMPLE_DIR = DATA_DIR / "sample"
LC_TEMPLATE_PATH = TEMPLATES_DIR / "Application-for-LC-issuance.docx"

def get_output_dir(run_name: str = "default") -> Path:
    d = OUTPUTS_DIR / run_name
    d.mkdir(parents=True, exist_ok=True)
    return d

# LC Application Agent

AI Agent that automatically fills an LC (Letter of Credit) application DOCX from a foreign trade contract.

> Vietnamese version: [README.md](README.md)

## Overview

The system uses **LangGraph** to orchestrate a 4-node sequential pipeline with a self-correction loop when the quality score falls below threshold:

1. **extract_node** — LLM extracts structured fields from the foreign trade contract
2. **validate_node** — Pure Python enforces UCP600, ISBP 821, Incoterms, and Vietnamese forex law rules
3. **quality_review_node** — LLM-as-Judge scores the output (0–10); if < 7.0 → retry back to extract_node (max 1 retry)
4. **fill_node** — python-docx fills the bank's DOCX template with validated data

**Input**: foreign trade contract (TXT / PDF / DOCX)

**Output**: `data/outputs/{bank}/{company_slug}/LC-Application-{contract}.docx`

## Architecture

```
Contract (TXT/PDF/DOCX)
         │
   [extract_node]         ← LLM: llama-3.3-70b-versatile
         │
   [validate_node]        ← Pure Python: UCP600 + ISBP821 + Incoterms + Vietnam forex
         │
   [quality_review_node]  ← LLM-as-Judge: qwen/qwen3-32b
         │
    ┌────┴────┐
    │  score? │
  ≥7.0      <7.0 (retry once → extract_node)
    │
  [fill_node]             ← python-docx: fill bank-aware DOCX template
         │
  LC-Application.docx
  data/outputs/{bank}/{company_slug}/
```

## Setup

### Requirements

- Python 3.12 (managed via [uv](https://docs.astral.sh/uv))
- Groq API key (free at [console.groq.com](https://console.groq.com))

### Installation

```bash
# Create virtual environment with Python 3.12
uv venv --python 3.12
source .venv/bin/activate

# Install dependencies
uv pip install -r requirements.txt
```

### Environment Configuration

Create a `.env` file:

```env
GROQ_API_KEY=your_groq_api_key_here          # required

LANGSMITH_API_KEY=your_langsmith_key         # optional, for tracing
LANGCHAIN_TRACING_V2=true                    # optional, enable LangSmith tracing
```

> **Note**: `GROQ_API_KEY` is the only required API key. LangSmith is fully optional.

## Usage

### CLI

```bash
# Basic run
python -m src.main --contract data/sample/contract.txt

# Specify bank and output directory
python -m src.main --contract data/sample/contract.txt --bank vietcombank --output-dir data/outputs/ete
```

### Python API

```python
from src.agents.graph import run_lc_application

state = run_lc_application("data/sample/contract.txt", bank="vietcombank")
```

## Project Structure

```
src/
  config.py              # BANK_VCB/BIDV/VIETINBANK constants, get_bank_template_path(),
                         #   slugify_company(), get_bank_output_dir()
  agents/
    graph.py             # LangGraph pipeline + run_lc_application()
    node_extract.py      # extract_node: LLM field extraction
    node_validate.py     # validate_node: rule engine
    node_quality.py      # quality_review_node: LLM-as-Judge
    node_fill.py         # fill_node: DOCX template filling
  tools/
    contract_extractor.py  # extract_contract_text + extract_lc_fields_from_contract
    lc_rules_validator.py  # UCP600 / ISBP821 / Incoterms / Vietnam forex rules
  models/
    state.py             # LCAgentState TypedDict
    lc_application.py    # LCApplicationData + DocumentRequirements Pydantic models
  knowledge/
    loader.py            # YAML knowledge loader
    rules/               # ucp600_rules.yaml, isbp821_rules.yaml,
                         #   incoterms_rules.yaml, vietnam_forex_law.yaml
  utils/
    docx_filler.py       # Wingdings checkbox filling, run-level text replacement
    llm.py               # get_extraction_llm(), get_judge_llm()
    logger.py            # colored logging, @timed_node decorator, LangSmith tracing
  main.py                # CLI entry point
data/
  sample/contract.txt    # Sample contract (VN-CN-2024-001, USD 450K, CIF)
  templates/docx/
    vietcombank/         # Application-for-LC-issuance.docx
  outputs/{bank}/{slug}/ # Generated DOCX files (gitignored)
tests/
  test_config.py         # Multi-bank config tests (8 tests)
  test_docx_filler.py    # DOCX filling tests
  test_models.py         # Pydantic model tests
  test_lc_rules_validator.py  # Rule engine tests (44 tests)
  test_ete.py            # End-to-end tests (requires GROQ_API_KEY)
```

## LLM Models (Groq)

| Node | Model | TPM | Purpose |
|------|-------|-----|---------|
| `extract_node` | `llama-3.3-70b-versatile` | 12K | Contract field extraction (~7K tokens/call) |
| `quality_review_node` | `openai/gpt-oss-20b` | 8K | LLM-as-Judge scoring; cross-vendor (OpenAI) from extractor (Meta) |

`validate_node` and `fill_node` use no LLM (pure Python).

## Knowledge Base (deterministic, no LLM)

| Source | Key Rules |
|--------|-----------|
| **UCP600** | Irrevocable by default (Art.3), 21-day presentation period (Art.14c), clean B/L (Art.27) |
| **ISBP 821** | Invoice description match, B/L full set, documents in English |
| **Incoterms 2000/2010/2020** | CIF/CIP → insurance certificate (min 110%, ICC A); FOB → B/L freight collect |
| **Vietnam forex law** | VN-01 currency ≠ VND (Decree 70/2014 Art.4), VN-02 contract number required (Art.11), VN-03 issuing bank NHNN-authorized (Art.6), VN-04 import LC = current account transaction ✓, VN-05 margin deposit reminder, VN-06 regulated goods check |

## Multi-Bank Support

Add a new bank by placing its template at `data/templates/docx/{bank_slug}/Application-for-LC-issuance.docx`, then pass `bank={bank_slug}` to `run_lc_application()`. The output directory is automatically `data/outputs/{bank_slug}/{company_slug}/`.

Bank constants defined in `src/config.py`:

| Constant | Value |
|----------|-------|
| `BANK_VCB` | `"vietcombank"` (default) |
| `BANK_BIDV` | `"bidv"` |
| `BANK_VIETINBANK` | `"vietinbank"` |

## Running Tests

```bash
# Unit tests (no API key needed)
python -m pytest tests/ --ignore=tests/test_ete.py -v   # 52 tests

# End-to-end tests (requires GROQ_API_KEY)
python -m pytest tests/test_ete.py -v
```

## Notes

- **GROQ_API_KEY** is the only required API key
- **Anti-hallucination**: The LLM only extracts information explicitly stated in the contract — no fabrication
- **Rule engine**: UCP600 and Incoterms rules are enforced in pure Python, not by the LLM
- **Wingdings checkbox**: The template uses U+F06F (unchecked) / U+F0FE (checked) — **not** standard Unicode □/■
- **Security**: Never commit `.env` or API keys to git (already in `.gitignore`)

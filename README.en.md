# LC Application Agent

**Automatically generate LC (Letter of Credit) applications from foreign trade contracts — works with any bank and any company.**

> Vietnamese version: [README.md](README.md)

---

## Highlights

| | |
|---|---|
| 🏦 **Any bank** | Add a new bank by dropping a DOCX template into the right folder — no code changes needed |
| 🏢 **Any company** | Output is automatically organized by company name (slugified) — files never overwrite each other |
| 📄 **Any contract format** | TXT, PDF, DOCX — auto-extracted, no preprocessing required |
| ⚖️ **International compliance** | Rule engine enforces UCP600, ISBP 821, Incoterms 2020, Vietnamese forex law |
| 🔄 **Self-correction** | LLM-as-Judge scores output; if < 7/10 → re-extracts with targeted feedback |

**Output**: `data/outputs/{bank}/{company}/LC-Application-{contract}.docx`

---

## Adding a new bank

Just 2 steps — **no code changes**:

```
1. Place the DOCX template at:
   data/templates/docx/{bank-name}/Application-for-LC-issuance.docx

2. Pass the bank name to the call:
   run_lc_application("contract.txt", bank="bank-name")
```

The agent automatically:
- Finds the correct template for that bank
- Creates a separate output directory: `data/outputs/{bank}/{company_slug}/`
- Fills the form according to the provided DOCX structure

---

## Architecture Overview

```
Foreign trade contract (TXT / PDF / DOCX)
                │
          [extract_node]          ← LLM: llama-3.3-70b-versatile
                │                    Extracts ~30 fields: buyer, seller,
                │                    amount, dates, Incoterms, ports, documents...
          [validate_node]         ← Pure Python: UCP600 + ISBP821 + Incoterms + VN forex
                │                    Applies defaults, validates consistency,
                │                    adds insurance doc requirement for CIF/CIP
          [quality_review_node]   ← LLM-as-Judge: openai/gpt-oss-20b (cross-vendor)
                │
           ┌────┴────┐
           │  score? │
         ≥7.0      <7.0 → retry extraction with feedback
           │
          [fill_node]             ← python-docx: fill the selected bank's template
                │
   data/outputs/{bank}/{company}/LC-Application-{contract}.docx
```

**Clean separation**: The LLM only extracts data from the contract. All business rules (UCP600, Incoterms, forex law) are enforced by pure Python — no tokens spent, no hallucination risk.

---

## Setup

```bash
uv venv --python 3.12 && source .venv/bin/activate
uv pip install -r requirements.txt
cp .env.example .env   # fill in GROQ_API_KEY
```

Only 1 API key required:

```env
GROQ_API_KEY=your_groq_api_key_here
```

---

## Usage

### CLI

```bash
# Vietcombank (default)
python -m src.main --contract data/sample/contract.txt

# BIDV
python -m src.main --contract contract.txt --bank bidv

# Any bank
python -m src.main --contract contract.txt --bank bank-name

# Override output directory
python -m src.main --contract contract.txt --bank vietcombank --output-dir /tmp/test
```

### Python API

```python
from src.agents.graph import run_lc_application

# Vietcombank
state = run_lc_application("contract.txt", bank="vietcombank")

# BIDV
state = run_lc_application("contract.txt", bank="bidv")

# Results
print(state["output_docx_path"])   # data/outputs/bidv/company_name/LC-Application-contract.docx
print(state["quality_score"])      # 8.5
print(state["company_slug"])       # company_name (auto-derived from applicant in contract)
```

---

## Template and Output Structure

```
data/
├── templates/docx/
│   ├── vietcombank/          ← Vietcombank template (included)
│   │   └── Application-for-LC-issuance.docx
│   ├── bidv/                 ← Add BIDV: just place the file here
│   │   └── Application-for-LC-issuance.docx
│   └── any-other-bank/       ← Any bank
│       └── Application-for-LC-issuance.docx
└── outputs/                  ← Auto-created, organized by bank + company
    ├── vietcombank/
    │   ├── company_abc/
    │   │   └── LC-Application-contract-001.docx
    │   └── company_xyz/
    │       └── LC-Application-contract-002.docx
    └── bidv/
        └── company_abc/
            └── LC-Application-contract-003.docx
```

---

## Project Structure

```
src/
├── config.py              # BANK_VCB/BIDV/VIETINBANK constants + helper functions:
│                          #   get_bank_template_path(bank)    → Path to template
│                          #   get_bank_output_dir(bank, slug) → Output path (auto-created)
│                          #   slugify_company(name)           → "ABC Corp" → "abc_corp"
├── agents/
│   ├── graph.py           # run_lc_application(contract, bank, output_dir)
│   ├── node_extract.py    # LLM: extract ~30 fields from contract
│   ├── node_validate.py   # Python: UCP600 / ISBP821 / Incoterms / VN forex rules
│   ├── node_quality.py    # LLM-as-Judge: score + feedback
│   └── node_fill.py       # python-docx: fill the specified bank's template
├── tools/
│   ├── contract_extractor.py  # TXT/PDF/DOCX → text → structured JSON
│   └── lc_rules_validator.py  # Rule engine: UCP600 + ISBP821 + Incoterms + VN forex
├── models/
│   ├── state.py           # LCAgentState: bank, company_slug, lc_data, quality_score...
│   └── lc_application.py  # LCApplicationData + DocumentRequirements (Pydantic)
├── knowledge/rules/       # ucp600_rules.yaml, isbp821_rules.yaml,
│                          #   incoterms_rules.yaml, vietnam_forex_law.yaml
└── utils/
    ├── docx_filler.py     # Wingdings checkbox, run-level fill, buyer/seller replace
    └── llm.py             # get_extraction_llm(), get_judge_llm()
data/
├── sample/contract.txt    # Sample contract (VN-CN-2024-001, USD 450K, CIF)
└── templates/docx/vietcombank/  # Vietcombank template
tests/                     # 52 unit tests + ETE tests
```

---

## LLM Models (Groq Free Tier)

| Node | Model | TPM | Role |
|------|-------|-----|------|
| `extract_node` | `llama-3.3-70b-versatile` | 12K | Field extraction from contract (~5K tokens/call) |
| `quality_review_node` | `openai/gpt-oss-20b` | 8K | Cross-vendor judge (OpenAI ≠ Meta extractor); uses internal reasoning tokens |

`validate_node` and `fill_node` use no LLM — pure Python, fast, deterministic.

---

## Knowledge Base — Rule Engine (no LLM)

| Source | Key Rules |
|--------|-----------|
| **UCP600** | Irrevocable by default (Art.3), 21-day presentation period (Art.14c), clean B/L (Art.27) |
| **ISBP 821** | Invoice description matches LC, full set B/L, documents in English |
| **Incoterms 2000/2010/2020** | CIF/CIP → insurance ≥ 110% ICC(A); FOB → B/L freight collect |
| **Vietnamese law** | VN-01 currency ≠ VND (Decree 70/2014 Art.4), VN-02 contract number required (Art.11), VN-03 NHNN-authorized bank (Art.6), VN-04 import LC = current account ✓, VN-05 margin reminder, VN-06 regulated goods |

---

## Running Tests

```bash
python -m pytest tests/ --ignore=tests/test_ete.py -v   # 52 unit tests, no API key needed
python -m pytest tests/test_ete.py -v                   # ETE (requires GROQ_API_KEY)
```

---

## Notes

- **Adding a bank**: just place the template file — no code changes
- **Anti-hallucination**: LLM only extracts from contract text, never fabricates
- **Rule engine**: UCP600 / Incoterms checked in pure Python — deterministic, no tokens spent
- **Wingdings checkbox**: VCB template uses U+F06F/U+F0FE (Wingdings PUA), not standard Unicode □/■
- **Security**: Never commit `.env` to git

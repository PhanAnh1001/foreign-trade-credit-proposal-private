# LC Application Agent — Design Document

## 1. Problem Statement

Given a foreign trade contract and any bank's LC application template (Vietcombank by default), automatically draft a Letter of Credit (LC) application conforming to UCP 600, ISBP 821, and Incoterms (2000/2010/2020).

## 2. Architecture

### Agent Topology (LangGraph)

```
Contract (TXT/PDF/DOCX)
          │
    [extract_node]        ← LLM: llama-3.3-70b-versatile
          │
    [validate_node]       ← Pure Python: UCP600 + ISBP821 + Incoterms rules
          │
    [quality_review_node] ← LLM-as-Judge: openai/gpt-oss-20b
          │
     ┌────┴────┐
     │  score? │
   ≥7.0      <7.0 (retry once → extract_node)
     │
  [fill_node]             ← python-docx: fill bank-aware DOCX template
          │
   LC-Application.docx
```

### Memory
- **Short-term**: `LCAgentState` (TypedDict) holds all inter-node data in the LangGraph execution context. Key fields include: `contract_text`, `lc_fields`, `validation_result`, `quality_score`, `bank`, `company_slug`.
- **No long-term memory needed**: each run is fully self-contained from a single contract file.

### Planning
- The validator (`validate_and_enhance`) acts as a deterministic planning step: it maps Incoterms terms to required documents and applies UCP600 defaults before the LLM judge reviews.

## 3. Tool Inventory

| Tool | File | Purpose |
|---|---|---|
| `extract_contract_text` | `tools/contract_extractor.py` | PDF/DOCX/TXT → plain text |
| `extract_lc_fields_from_contract` | `tools/contract_extractor.py` | LLM structured extraction |
| `validate_and_enhance` | `tools/lc_rules_validator.py` | UCP600/ISBP821/Incoterms rule engine |
| `fill_lc_template` | `utils/docx_filler.py` | python-docx template filling |
| `get_bank_template_path(bank)` | `config.py` | Bank-aware template path resolution |
| `get_bank_output_dir(bank, slug)` | `config.py` | Bank + company-slugged output path |
| `slugify_company(name)` | `config.py` | Company name → filesystem-safe slug |

## 4. Action Inventory

| Node | Action | Model | Tokens/call |
|---|---|---|---|
| `extract_node` | Contract → structured JSON | llama-3.3-70b-versatile | ~5K |
| `validate_node` | Rules enforcement | (none — pure Python) | 0 |
| `quality_review_node` | Score 0–10 + feedback | openai/gpt-oss-20b | ~3K |
| `fill_node` | JSON + bank slug → bank-specific DOCX | (none — python-docx) | 0 |

## 5. Key Design Decisions

### No hallucination guarantee
- LLM prompt explicitly states: "Only extract information explicitly stated in the contract. Do not infer or fabricate."
- All financial figures (amount, dates) are extracted verbatim from contract text.
- UCP600/ISBP821 rules (e.g., 21-day presentation period, 110% insurance for CIF) are applied by a deterministic rule engine, not the LLM.

### Self-correction loop
- If quality score < 7.0, the agent retries extraction once with the judge's feedback injected into the prompt — making the retry smarter than a blind re-run.
- After 1 retry, the agent proceeds with warnings rather than blocking output.

### Incoterms-aware document requirements
- The validator automatically adds insurance certificate requirements for CIF and CIP terms.
- Under Incoterms 2020, CIP requires "All Risks" (ICC A) rather than "minimum cover" (ICC C).

### Multi-bank support
- `run_lc_application()` accepts a `bank` parameter (default: `BANK_DEFAULT = "vietcombank"`).
- Template lookup: `data/templates/docx/{bank}/Application-for-LC-issuance.docx`
- Output path: `data/outputs/{bank}/{company_slug}/LC-Application-{contract}.docx`
- `company_slug` is derived deterministically from `applicant_name` via `slugify_company()` — lowercase, underscores, max 50 chars.
- Adding a new bank requires only: (a) place the template in the correct directory, (b) pass `bank=slug` to `run_lc_application()`.

## 6. Limitations

- LLM extraction may miss fields in poorly structured contracts.
- DOCX template filling does not support all cell formatting variations.
- Incoterms 2000 and 2010 difference handling is limited to version labelling.
- No support for amendments (only initial LC issuance).
- DOCX template filling logic is written for the Vietcombank form structure. Other banks' templates may require additional filler functions if their layout differs.

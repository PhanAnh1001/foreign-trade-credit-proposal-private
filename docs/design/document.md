# LC Application Agent — Design Document

## 1. Problem Statement

Given a foreign trade contract (TXT/PDF/DOCX) and a bank's LC application DOCX template, automatically draft a Letter of Credit application conforming to UCP 600, ISBP 821, and Incoterms (2000/2010/2020).

**General-purpose by design**: the agent works with any bank and any company. Adding a new bank requires only placing its template DOCX in `data/templates/docx/{bank}/` — no code changes. The applicant company is identified automatically from the contract and used to organize output files.

## 2. Model Assignment (§2a)

### 2a.1 Token demand per function

| Function | Task | Input tokens | max_tokens | Total/call |
|---|---|---|---|---|
| `get_extraction_llm` | Contract → ~30 structured fields | ~3.5K | 2048 | ~5.5K |
| `get_judge_llm` | Score 0–10 + feedback JSON | ~0.7K | 2048 | ~2.8K (incl. ~520 reasoning) |

`validate_node` and `fill_node` use no LLM — pure Python, 0 tokens.

### 2a.2 Rate limits (Groq free tier)

| Model | RPM | RPD | TPM |
|---|---|---|---|
| `llama-3.3-70b-versatile` | 30 | 1K | **12K** |
| `openai/gpt-oss-20b` | 30 | 1K | **8K** |

### 2a.3 Constraints

- `gpt-oss-20b`: input + max_tokens ≤ ~8K (413 error if exceeded). Uses internal reasoning tokens (~520T) not visible in output — set `max_tokens=2048`, not higher.
- Both models: RPD=1K — sufficient for development; production use needs paid tier.
- Judge must be a different vendor from extractor (cross-vendor independence rule).

### 2a.4 Model assignment

| Rank (demand) | Function | Model | Vendor | Reason |
|---|---|---|---|---|
| 1 (extraction) | `get_extraction_llm` | `llama-3.3-70b-versatile` | Meta | 12K TPM, 128K ctx, high accuracy |
| 2 (judge) | `get_judge_llm` | `openai/gpt-oss-20b` | OpenAI | Cross-vendor vs Meta extractor; reasoning tokens improve judgment |

### 2a.5 Cost estimate (Groq free tier)

- Per run: ~5.5K (extraction) + ~2.8K (judge) = **~8.3K tokens**
- With 1 retry: ~16.6K tokens/run
- Free tier RPD limit: ~60 runs/day (1K RPD ÷ 2 calls/run) before quota hit

---

## 3. Architecture

### Agent Topology (LangGraph)

```
Foreign trade contract (TXT / PDF / DOCX)
              │
        [extract_node]          ← LLM: llama-3.3-70b-versatile
              │                    ~30 fields: parties, amounts, dates,
              │                    Incoterms, ports, documents
        [validate_node]         ← Pure Python rule engine
              │                    UCP600 + ISBP821 + Incoterms + VN forex law
        [quality_review_node]   ← LLM-as-Judge: openai/gpt-oss-20b
              │
         ┌────┴────┐
         │  score? │
       ≥7.0      <7.0 (retry once → extract_node with feedback)
         │
        [fill_node]             ← python-docx: fill bank-aware DOCX template
              │
   data/outputs/{bank}/{company_slug}/LC-Application-{contract}.docx
```

### Memory
- **Short-term**: `LCAgentState` (TypedDict) holds all inter-node data. Key fields: `bank`, `company_slug`, `contract_path`, `lc_data`, `quality_score`, `quality_feedback`, `output_docx_path`.
- **No long-term memory needed**: each run is fully self-contained from a single contract file.

### Planning
- The validator (`validate_and_enhance`) acts as a deterministic planning step: it maps Incoterms terms to required documents and applies UCP600 defaults before the LLM judge reviews.

## 4. Tool Inventory

| Tool | File | Purpose |
|---|---|---|
| `extract_contract_text` | `tools/contract_extractor.py` | PDF/DOCX/TXT → plain text |
| `extract_lc_fields_from_contract` | `tools/contract_extractor.py` | LLM structured extraction (~30 fields) |
| `validate_and_enhance` | `tools/lc_rules_validator.py` | UCP600/ISBP821/Incoterms/VN forex rule engine |
| `fill_lc_template` | `utils/docx_filler.py` | python-docx template filling |
| `get_bank_template_path(bank)` | `config.py` | Resolve template path for any bank slug |
| `get_bank_output_dir(bank, slug)` | `config.py` | Create and return `outputs/{bank}/{slug}/` |
| `slugify_company(name)` | `config.py` | Company name → filesystem-safe slug (max 50 chars) |

## 5. Action Inventory

| Node | Action | Model | Tokens/call |
|---|---|---|---|
| `extract_node` | Contract → structured JSON | llama-3.3-70b-versatile | ~5K |
| `validate_node` | Rules enforcement | (none — pure Python) | 0 |
| `quality_review_node` | Score 0–10 + feedback | openai/gpt-oss-20b | ~3K |
| `fill_node` | JSON + bank slug → bank-specific DOCX | (none — python-docx) | 0 |

## 6. Key Design Decisions

### General-purpose: any bank, any company

The agent is designed to be bank-agnostic and company-agnostic from the ground up:

- **Bank**: `run_lc_application()` takes a `bank` parameter (default: `BANK_DEFAULT = "vietcombank"`). Template lookup is `data/templates/docx/{bank}/Application-for-LC-issuance.docx`. Adding a new bank requires no code — only a template file.
- **Company**: `applicant_name` is extracted from the contract and passed through `slugify_company()` (lowercase, underscores, max 50 chars) to produce `company_slug`. Output is organized as `data/outputs/{bank}/{company_slug}/` — files from different companies never collide.
- **Contract format**: `extract_contract_text()` handles TXT, PDF (PyMuPDF + pdfplumber fallback), and DOCX transparently.

### No hallucination guarantee

- LLM prompt explicitly states: "Only extract information explicitly stated in the contract. Do not infer or fabricate."
- UCP600/ISBP821 rules (e.g., 21-day presentation period, 110% insurance for CIF) are applied by a deterministic rule engine, not the LLM.
- The judge uses a cross-vendor model (OpenAI) to independently review extraction by a different vendor (Meta) — avoiding self-confirmation bias.

### Self-correction loop

- If quality score < 7.0, the agent retries extraction once with the judge's top issues injected into the prompt — targeted retry, not blind re-run.
- After 1 retry, the agent proceeds with warnings rather than blocking output.

### Incoterms-aware document requirements

- The validator automatically adds insurance certificate requirements for CIF and CIP terms.
- Under Incoterms 2020, CIP requires "All Risks" (ICC A) rather than "minimum cover" (ICC C).
- For FOB/CFR, the validator sets B/L freight notation correctly and skips insurance.

## 7. Limitations

- DOCX template filling is implemented for the Vietcombank form layout. Other banks' templates with different table structures may require additional filler functions in `docx_filler.py`.
- LLM extraction may miss fields in poorly structured or non-standard contracts.
- Incoterms 2000 and 2010 difference handling is limited to version labelling; rule differences beyond insurance are not fully modelled.
- No support for LC amendments (only initial issuance).

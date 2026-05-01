# Epic — LC Application Agent

> AI phân rã từ Design thành checklist. Người duyệt bằng `## Approved by <name>` (name ∈ `docs/reviewers.txt`) hoặc viết `lc-application.feedback.md`. Sau approved, AI tick `[x]` từng task khi báo done.

## PRD: docs/requirements/lc-application.md
## Design: docs/design/document.md
## Review summary: plans/lc-application.review-summary.md (AI viết, người đọc trước)

## Checklist

> Atomic (1 commit, ≤ 200 LOC), testable (lệnh test cụ thể), có DoD quan sát được.
> Trạng thái: `[ ]` todo · `[x]` done · `[!]` blocked

- [x] T1. Scaffold project structure và config
      DoD: `src/config.py` import được, `BANK_VCB/BIDV/DEFAULT` defined
- [x] T2. Contract extractor — TXT/PDF/DOCX → plain text
      DoD: `pytest tests/test_contract_extractor.py` pass
- [x] T3. LLM extraction node — contract text → ~30 structured fields
      DoD: `pytest tests/test_node_extract.py` pass; schema validates với Pydantic
- [x] T4. Validator node — UCP600/ISBP821/Incoterms/VN forex rules
      DoD: `pytest tests/test_lc_rules_validator.py` pass; CIF → insurance cert added
- [x] T5. Quality review node — LLM-as-Judge score 0–10
      DoD: `pytest tests/test_node_quality.py` pass; score returned as float
- [x] T6. Fill node — python-docx template filling với Wingdings checkboxes
      DoD: `pytest tests/test_docx_filler.py` pass; output DOCX > 1KB, applicant name present
- [x] T7. LangGraph wiring — 4-node graph với self-correction loop
      DoD: `run_lc_application("data/sample/contract.txt")` completes, output DOCX exists
- [x] T8. Multi-bank support — bank param, slugify_company, bank-aware output dirs
      DoD: `pytest tests/test_config.py` pass (8 tests); output at `data/outputs/{bank}/{slug}/`
- [x] T9. CLI — `python -m src.main --contract ... --bank ...`
      DoD: CLI runs end-to-end, `--bank bidv` accepted
- [x] T10. ETE test + evidence
      DoD: `pytest tests/test_ete.py` pass; `ete-evidence/ete-run-008.json` recorded; quality ≥ 7.0
- [x] T11. Adopt ai-agent-workflow — scaffold + epic artifacts
      DoD: `docs/workflow.md` exists; intent/PRD/plan created; design §2a added
- [x] T12. Bước 5.5 security tests (5 files, 16 passed + 10 skipped no-key)
      DoD: `pytest tests/security/` — 16 passed, 0 failed
- [x] T13. Bước 6 E2E 3-of-3 PASS — happy_cif_vcb scenario
      DoD: `verdict_pass=true`, `stable="3-of-3"`, scores 8.2/7.5/8.4 ≥ 7.0; evidence at `ete-evidence/_runs/20260501_123415_happy_cif_vcb_3of3/`
- [x] T14. Bước 7 Review Summary
      DoD: `plans/lc-application.review-summary.md` exists
- [ ] T15. FOB scenario — fixture + registry entry + E2E 3-of-3
      DoD: `happy_fob_vcb` PASS 3-of-3; no insurance cert in output; evidence at `ete-evidence/_runs/`
- [ ] T16. Adversarial scenario — injection contract + E2E 3-of-3
      DoD: `adversarial_injection` PASS; output fields not hijacked (applicant ≠ HACKED); quality ≥ 6.0
- [ ] T17. Stress scenario — blank contract + E2E 3-of-3
      DoD: `stress_blank_contract` runner exits 0 (no Python crash); pipeline errors handled gracefully

## Phụ thuộc

- T3 phụ thuộc T2
- T5 phụ thuộc T3, T4
- T6 phụ thuộc T3
- T7 phụ thuộc T3, T4, T5, T6
- T8 phụ thuộc T7
- T9 phụ thuộc T7
- T10 phụ thuộc T8, T9

## Test layered (`docs/testing/`)

- `01_env_setup.md` → `02_tools.md` → `03_nodes.md` → `04_pipeline.md` → `05_output.md`
- `055_security.md` ← Bước 5.5 BẮT BUỘC trước E2E

## Security tests (`tests/security/`)

- [x] `test_prompt_injection.py` — 5 vectors (skip without GROQ_API_KEY)
- [x] `test_pii_redaction.py`
- [x] `test_hallucination_probe.py` — skip without GROQ_API_KEY
- [x] `test_tool_whitelist.py`
- [x] `test_output_schema.py`
- [ ] `test_rate_limit.py`

## E2E scenarios

| Scenario | Type | Input fixtures | Expected |
|---|---|---|---|
| `happy_cif_vcb` | normal | `data/sample/contract.txt` + vietcombank template | quality ≥ 7.0, DOCX exists, 3-of-3 |
| `happy_fob` | normal | FOB contract (to be created) | no insurance cert, freight collect |
| `happy_cip` | normal | CIP contract (to be created) | ICC(A) insurance, 110% |
| `adversarial_injection` | adversarial | contract with injected instructions | output không làm theo injected instructions |
| `stress_blank_contract` | stress | empty TXT | flag gracefully, không bịa fields |

## Eval gate

- `quality_score_p50 >= 7.0` (median của 3 runs)
- Judge: `openai/gpt-oss-20b` (cross-vendor vs Meta extractor)
- `security.json` 5/5 lớp pass
- `stable == "3-of-3"` (chống non-determinism)
- 52 unit tests PASS
- Perf không regression > 1.5× so với baseline

## Performance baseline

- File: `data/baselines/happy_cif_vcb.json`
- Baseline từ `ete-evidence/ete-run-008.json`: quality=7.5, latency=5.0s, retries=0

---

## Approved by anh @ 2026-05-01

---

## Tracking

| Task | Commit | Test result | Note |
|---|---|---|---|
| T1–T7 | `4221dc8` | 44 unit tests PASS | v1 initial commit |
| T8 | multi commits | 52 unit tests PASS + ETE PASS | multi-bank refactor |
| T9 | (included T8) | CLI `--bank` flag working | |
| T10 | `ete-run-008` | quality=7.5/10, 5.0s, 0 retries | `ete-evidence/ete-run-008.json` |

## Cascade từ feedback

> Chưa có feedback round nào.

## Feedback rounds

| Round | FEEDBACK file | Tasks added | Run-id | 3-of-3 | Status |
|---|---|---|---|---|---|
| — | — | — | — | — | — |

## ADR phát sinh

- (none yet — tạo qua `/adr "<title>"` khi cần)

---

## Last session — 2026-05-01 (resume pointer)

- **Ended at**: T14 — Bước 7 Review Summary complete
- **Status**: ALL GATES PASS — 52 unit + 16 security + 3-of-3 E2E (8.2/7.5/8.4) + review-summary written
- **Next**: Human reviewer reads `plans/lc-application.review-summary.md`, then deep-dives REPORT if needed. Open: create `data/baselines/happy_cif_vcb.json`, add FOB scenario.
- **Blockers**: none — awaiting human review sign-off

## Session log

- 2026-04-30: T1–T9 completed, v1 code + multi-bank refactor
- 2026-04-30: T10 ETE pass — ete-run-008.json recorded, quality=7.5/10
- 2026-05-01: Adopted ai-agent-workflow; created intent, PRD, plan artifacts (T11)
- 2026-05-01: T12 — 5 security test files; fixed real prompt injection bug (4/5 vectors); 16 passed
- 2026-05-01: T13 — E2E 3-of-3 PASS (8.2/7.5/8.4); bank metadata injection fix; full evidence format
- 2026-05-01: T14 — Review summary written at plans/lc-application.review-summary.md

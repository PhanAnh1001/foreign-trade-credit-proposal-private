# Epic — <tên>

> AI phân rã từ Design thành checklist. Người duyệt bằng `## Approved by <name>` (name ∈ `docs/reviewers.txt`) hoặc viết `<epic-slug>.feedback.md`. Sau approved, AI tick `[x]` từng task khi báo done.

## PRD: docs/requirements/<feature>.md
## Design: docs/design/<feature>.md
## Review summary: plans/<epic-slug>.review-summary.md (AI viết, người đọc trước)

## Checklist

> Atomic (1 commit, ≤ 200 LOC), testable (lệnh test cụ thể), có DoD quan sát được. Commit message: `T<n>: <verb> <object>`.
> Trạng thái:
>   `[ ]` todo · `[x]` done · `[!]` blocked (kèm `Reason:` + `Needs:`)

- [ ] T1. <atomic task>
      DoD: `pytest tests/unit/test_<x>.py::test_<y>` pass
- [ ] T2. <atomic task>
      DoD: file `src/<…>` tồn tại + import được
- [!] T3. <atomic task>
      Reason: provider 404 cho model `<X>`
      Needs: human decision — đổi model hay đợi vendor fix
      DoD: <…>

## Phụ thuộc

- T2 phụ thuộc T1
- T4 phụ thuộc T3

## Test layered (`docs/testing/`)

- `01_env_setup.md` → `02_tools.md` → `03_nodes.md` → `04_pipeline.md` → `05_output.md`
- `055_security.md`  ← Bước 5.5 BẮT BUỘC trước E2E

## Security tests (`tests/security/`)

- [ ] `test_prompt_injection.py` — ≥ 5 vector
- [ ] `test_pii_redaction.py`
- [ ] `test_hallucination_probe.py`
- [ ] `test_tool_whitelist.py`
- [ ] `test_output_schema.py`
- [ ] `test_rate_limit.py`

## E2E scenarios (≥ 1 normal + ≥ 1 adversarial + ≥ 1 stress / epic)

| Scenario | Type | Input fixtures | Expected |
|---|---|---|---|
| `happy_<co1>` | normal | `tests/e2e/fixtures/<co1>/` | REPORT.md PASS, 3-of-3 |
| `edge_<co2>` | normal | `tests/e2e/fixtures/<co2>/` | … |
| `adversarial_injection` | adversarial | `tests/e2e/fixtures/_adversarial/injection/` | output không chứa marker |
| `stress_blank_input` | stress | `tests/e2e/fixtures/_stress/blank/` | flag `data_missing=true`, không bịa |

## Eval gate

- `quality_score_p50 >= 7` (median của 3 runs, 2 judge khác vendor)
- `judge_disagreement <= 2`
- `claim_check.low_confidence < 3`
- `ratios_match == true`
- `security.json` 5/5 lớp pass
- `stable == "3-of-3"` (chống non-determinism)
- Perf không regression > 1.5× so với baseline

## Performance baseline

- File: `data/baselines/<scenario>.json`
- Update baseline khi PRD đổi expectation (cần `*.feedback.md` ký).

---

## Approved by <tên> @ <YYYY-MM-DD>
<!-- Tick khi duyệt. <tên> phải có trong docs/reviewers.txt. -->

---

## Tracking

| Task | Commit | Test result | Note |
|---|---|---|---|
| T1 | `<hash>` | `<tail of pytest>` | |
| T2 | … | … | |

## Cascade từ feedback (Bước 7g — back-propagation)

> Khi nhận feedback ở artifact upstream sau khi đã code:
> 1. Impact analysis vào file feedback (`## AI Response — impact analysis`)
> 2. Update artifact gốc (bump version, changelog cuối)
> 3. Re-derive downstream theo dependency, mỗi cái qua gate riêng
> 4. Thêm task vào mục dưới (T tiếp theo)
> 5. Cascade trên branch riêng: `bash tools/cascade_branch.sh <F-id>`
> 6. Re-run đầy đủ Bước 5 → 5.5 → 6 (3-of-3)
> 7. REPORT.md run mới ghi `## Upstream feedback addressed`

### Cascade từ `docs/requirements/<f>.feedback.md` :: F1 (branch: cascade/F1-PRD-criteria)
- [ ] T<k>. <verb> <object>
      DoD: <test command + expected>

### Cascade từ `docs/design/<f>.feedback.md` :: F<n> (branch: cascade/<F-id>)
- [ ] T<m>. ...

## Feedback rounds (≤ 3 / epic)

| Round | FEEDBACK file | Tasks added | Run-id mới | 3-of-3 | Status |
|---|---|---|---|---|---|
| 1 | `ete-evidence/.../FEEDBACK.md` | T<k>, T<k+1> | <new-id> | 3/3 | ✅ resolved |

> Vòng 4 → epic block, quay lại Bước 2 Design.

## ADR phát sinh

- `docs/adr/<NNNN>-<title>.md` — <1 dòng tóm tắt>

---

## Last session — <YYYY-MM-DD HH:MM> (resume pointer — chống #6.6.4)

- **Ended at**: T<n> — `<title task>`
- **Status**: PASS unit / FAIL E2E (run `<id>`, F2 must-fix) / blocked
- **Next**: T<n+1> — đọc `<đường dẫn cụ thể>` trước
- **Blockers**: none | `[!]` <reason>

## Session log

- <ts>: started, completed T1–T<n>
- <ts>: paused at T<n>, reason: <…>

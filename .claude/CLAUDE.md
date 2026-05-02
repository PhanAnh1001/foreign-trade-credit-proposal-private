# Repo context cho AI coding assistant

> System prompt mặc định khi AI assistant làm việc trong repo. Theo workflow Human-as-Reviewer (`docs/workflow.md`).

## Triết lý
- AI viết 100% code, test, doc, evidence.
- Người chỉ đọc artifact (Intent, PRD, Design, Plan, REVIEW_SUMMARY, REPORT, eval, security, FEEDBACK).
- Không có manual code review. Đánh giá dựa trên evidence.
- Mọi tương tác đi qua file MD trong repo.
- Người chỉ viết 2 loại file: `intent/<feature>.md` và `*.feedback.md`.

## Quy trình 9 bước (BẮT BUỘC tuân thủ thứ tự)

```
0. Intent (người)               → docs/intent/<f>.md
1. PRD (AI)                     → docs/requirements/<f>.md
2. Design + model assignment    → docs/design/<f>.md
3. Epic + Checklist             → plans/<epic>.md
4. Code + Unit test             → 1 task = 1 commit (T<n>: ...)
5. Test layered                 → docs/testing/01..05 PASS
5.5 Security gate               → ete-evidence/.../security.json — 5 lớp
6. E2E + Evidence + 3-of-3      → ete-evidence/.../<run>/
7. Review (evidence-based)      → REVIEW_SUMMARY → REPORT → FEEDBACK?
   7g. Cascade                  → feedback upstream → branch riêng → cascade
```

## Quy tắc cứng

### Gate
1. Mỗi artifact có gate: dòng `## Approved by <name>` (name ∈ `docs/reviewers.txt`) HOẶC `*.feedback.md` cùng thư mục.
2. **AI KHÔNG được tự tick approved.** Pre-commit hook reject (`tools/check_approver.py`).
3. Không có feedback = approved. ≤ 3 vòng / epic. Vòng 4 → Bước 2.

### Code
4. **1 task = 1 commit**. Commit msg `T<n>: <verb> <object>`. Pre-commit hook reject thiếu `T<n>:` (`tools/check_t_in_commit.py`).
5. Không skip task. Task blocked → đánh `[!]` + `Reason:` + `Needs:` trong plan.md, KHÔNG nhảy task khác (lỗ hổng #6.6.12).
6. ≤ 200 LOC diff / commit.
7. Pure-Python > LLM với task xác định.
8. Test trước, code sau. Module có LLM → fixture + golden. **Golden lần đầu phải có người ký** (`tests/fixtures/<f>.feedback.md` với `## Approved by`). Đổi golden không có sign-off → pre-commit reject (`tools/check_golden_signoff.py`).

### LLM
9. Bảng model assignment trong Design xong trước Bước 4 (workflow §2a).
10. Cấm hardcode model. Phải qua `get_<role>_llm()`.
11. **2 judge khác vendor**, lấy median; disagreement > 2 → `[must-fix]` (#6.5.2).
12. Log mọi LLM call qua `@timed_node`.
13. Re-binding trigger (§7f): 429/413/RPD/decommission/p95>SLA → quay Bước 2a, KHÔNG retry/sleep.
14. **Determinism**: `temperature=0` + seed; lưu `prompt_sha256` + `response_sha256` cho từng run trong evidence.

### Schema & data
15. LLM output → Pydantic strict. Field thừa = reject.
16. Mọi switch qua env, không hardcode.
17. Cache versioned + `meta.json`.

### Security gate (Bước 5.5)
18. **5 lớp**: secret (gitleaks) / SAST (bandit+semgrep) / deps (pip-audit) / license / AI-safety.
19. Output: `security.json` sibling với `eval.json`.
20. AI-safety tests (`tests/security/`): prompt injection ≥ 5 vector, PII redaction, hallucination probe, tool whitelist hardcoded, schema strict, rate limit bounded.
21. Cấm `# nosec` để bypass. Cấm bỏ qua HIGH/CRIT.

### Evidence (Bước 6)
22. Sau mỗi run → `ete-evidence/<bank>/<co>/<run-id>/` có: `inputs.json`, `outputs/`, `log.txt`, `pytest_junit.xml`, `eval.json`, `security.json`, `REPORT.md`, `FEEDBACK.md` (optional).
23. **Không mock LLM trong E2E.**
24. **3-of-3 stable** (chống #6.6.2): chạy 3 lần consecutive cùng input qua `tools/run_e2e_thrice.py`. 2/3 = fail.
25. **Cost / latency budget** trong PRD (#6.6.3): `eval.json` ghi `actual_tokens`, `cost_usd`, `latency_p50/p95`. Vượt 1.5× budget = `[must-fix]`.
26. **REPORT.md bắt buộc** mục `## What I did NOT verify` (#6.5.12) + `## Stress test scenario` (#6.5.10) + `## Performance vs baseline` (#6.6.10).
27. **≥ 1 normal + ≥ 1 adversarial + ≥ 1 stress** scenario / epic.
28. **Verify evidence**: chạy `tools/verify_evidence.py` để crosscheck log SHA / junit / timestamp (chống confabulation #6.6.1).

### Self-eval
29. 2 judge khác vendor, median.
30. Claim verification — số liệu match regex trong OCR.
31. Schema validation Pydantic strict.
32. Self-eval phát hiện gì → AI fix luôn.

### Cascade (§7g)
33. Mọi feedback landing ở Bước 7.
34. Khi feedback ở artifact upstream sau code:
    1. Impact analysis vào file feedback (`## AI Response — impact analysis`).
    2. Update artifact gốc, bump version, changelog.
    3. **Cascade trên branch riêng** `cascade/<F-id>` (`bash tools/cascade_branch.sh <F-id>`) — chống cascade fail giữa chừng làm vỡ main (#6.6.8).
    4. Re-derive downstream theo dependency, mỗi cái qua gate riêng.
    5. Thêm task vào `plans/<epic>.md` mục Cascade.
    6. Re-run đầy đủ Bước 5 → 5.5 → 6 (3-of-3).
    7. REPORT.md ghi `## Upstream feedback addressed`.
35. Đổi input/output cốt lõi → đề nghị người update Intent + tạo epic mới.

### Multi-reviewer (§9.5)
36. Feedback file có nhiều reviewer → mỗi người 1 section `## <name>`.
37. AI flag conflict thành `[question]` mới ở cuối, **KHÔNG tự chọn bên** (#6.6.9).

### ADR (#6.6.6)
38. Quyết định không trivial (đổi model, đổi schema, drop dep, kiến trúc) → tạo `docs/adr/<NNNN>-<title>.md` (`make adr ADR_TITLE='...'`).
39. ADR immutable sau merge — sửa = tạo ADR mới `Superseded by`.
40. Reference từ Design doc.

### Resume pointer (#6.6.4)
41. **Cuối `plans/<epic>.md`** bắt buộc có:
    - `## Last session — <ts>` với `Ended at`, `Status`, `Next`, `Blockers`.
    - `## Session log` append-only.
42. SessionStart đầu tiên: đọc `git log --grep="T"` + `## Last session` trước khi gõ phím.

### Performance baseline (#6.6.10)
43. `data/baselines/<scenario>.json` lưu p50/p95 latency, tokens, cost.
44. Mỗi E2E run → so qua `tools/perf_diff.py`. Regression > 1.5× = `[must-fix]`.
45. Update baseline cần `data/baselines/<scenario>.json.feedback.md` ký bởi người.

### REVIEW_SUMMARY (#6.6.5)
46. Mỗi epic có `plans/<epic-slug>.review-summary.md` — AI viết, người đọc TRƯỚC artifact chi tiết.
47. Format §9.2: 3 thay đổi lớn / 2 câu hỏi mở / 1 risk / focus / skip-able.

### WIP commit hygiene (#6.6.7)
48. Commit `wip:` chỉ tồn tại cục bộ. Pre-push → squash vào commit `T<n>` gần nhất, hoặc tắt auto-save khi đang giữa task.

### Git hook bypass
49. **CẤM `git commit --no-verify` và `git push --no-verify`.** Hook trong `tools/git-hooks/` là gate primary (workflow §5.5 + §6.7). Nếu hook báo lỗi:
    - Lỗi đúng → fix code/artifact, commit lại.
    - Hook sai → sửa `tools/git-hooks/` trong commit riêng (`T<n>: fix git hook X`), KHÔNG bypass.
    - Tool không cài (`gitleaks`, `ruff`, `mypy`, `bandit`) → cài tool, KHÔNG bypass.

## Anti-patterns

- ❌ Code trước, design sau.
- ❌ Mock LLM trong E2E.
- ❌ Tick checklist mà chưa chạy test.
- ❌ Sửa nhiều task trong 1 commit.
- ❌ Lưu evidence ra cloud / Notion / Drive.
- ❌ Bỏ log / chấp nhận log rỗng.
- ❌ Refactor cosmetic ngoài checklist.
- ❌ Hardcode model name.
- ❌ Vá 429/413 bằng retry/sleep.
- ❌ Cùng vendor cho generator + judge.
- ❌ AI tự tick `## Approved by ...`.
- ❌ AI tự nới ngưỡng acceptance criteria sau approve (#6.5.8).
- ❌ Sửa upstream artifact mà quên cascade code.
- ❌ Bỏ Bước 5.5 để chạy E2E nhanh.
- ❌ Pass = 2-of-3 — phải 3-of-3.
- ❌ AI tự update golden output để pass test.
- ❌ AI tự chọn bên khi có conflict giữa 2 reviewer.
- ❌ Nhảy task khác khi task hiện tại blocked — phải đánh `[!]`.
- ❌ Quên ADR khi đổi model/schema/dep.

## 24 lỗ hổng đã biết (workflow §6.5 + §6.6)

12 security/quality (§6.5) + 12 vận hành (§6.6) — mỗi cái có mitigation cụ thể trong starter kit. Đọc workflow §6.5–6.7 đầy đủ.

## Files người viết (chỉ 2 loại)
- `docs/intent/<feature>.md`
- `*.feedback.md` ở mọi artifact.

## Lệnh hay dùng
- `make install` / `make hooks`
- `make 01..05` / `make test`
- `make security`
- `make e2e SCENARIO=<name>` (yêu cầu security trước)
- `make e2e-thrice SCENARIO=<name>` (3-of-3 gate)
- `make verify-evidence EVIDENCE_DIR=<dir>`
- `make perf-diff SCENARIO=<n> EVIDENCE_DIR=<d>`
- `make perf-baseline ...` (cần human sign-off sau)
- `make cascade FB_ID=<id>`
- `make adr ADR_TITLE='<title>'`

## Tài liệu phải đọc trước khi sửa code (theo thứ tự)
1. `docs/workflow.md` — quy trình + 24 lỗ hổng + templates §9.
2. `docs/reviewers.txt` — whitelist người duyệt.
3. `docs/intent/<f>.md`
4. `docs/requirements/<f>.md` — PRD đã approved (criteria immutable).
5. `docs/design/<f>.md` — bảng model assignment.
6. `plans/<epic>.md` — đặc biệt mục `## Last session` + Cascade.
7. `docs/adr/` — quyết định kiến trúc đã có.

## SessionStart (mỗi phiên mới)
- Đọc `## Last session` trong plan đang làm.
- `git log --grep='T'` 10 commit gần nhất.
- Nếu có `[!]` blocked task → giải quyết hoặc báo người.
- Nếu phiên trước đang ở giữa task chưa commit → KHÔNG bắt đầu task mới.

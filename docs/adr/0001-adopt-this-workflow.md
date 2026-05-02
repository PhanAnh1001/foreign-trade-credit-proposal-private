# ADR 0001: Adopt Human-as-Reviewer workflow

- **Date**: YYYY-MM-DD
- **Status**: Accepted
- **Deciders**: <tên>

## Context
Đội cần xây AI agent nghiệp vụ với chất lượng kiểm chứng được, nhưng team engineering nhỏ, không kham nổi manual code review từng PR. Đồng thời rủi ro về AI sai (hallucination, prompt injection, criteria drift) cao và không thể kiểm bằng review thông thường.

Lựa chọn: hoặc giữ flow truyền thống (PR + reviewer đọc code) — không scale với khối lượng AI sinh; hoặc chuyển sang evidence-based review — người chỉ đọc artifact (Intent, PRD, Design, Plan, REPORT, eval, security) thay vì diff code.

## Decision
Adopt workflow **Human-as-Reviewer** mô tả trong `docs/workflow.md`. Đặc trưng:
- AI viết 100% code, test, doc, evidence.
- Người chỉ viết 2 loại file: `intent/<f>.md` và `*.feedback.md`.
- Mọi tương tác đi qua file MD trong repo.
- Gate dựa trên evidence (E2E PASS + log + eval + security), không phải đọc diff.
- 9 bước cố định: 0 Intent → 1 PRD → 2 Design → 3 Plan → 4 Code → 5 Test layered → 5.5 Security → 6 E2E → 7 Review (+7g Cascade).

## Consequences
- **Positive**:
  - Scale được volume code AI sinh.
  - Mọi quyết định traceable trong git (artifact + commit có `T<n>`).
  - Reviewer skill thấp hơn vẫn duyệt được nếu evidence rõ.
- **Negative**:
  - Bootstrap epic tốn ~1 tuần để dựng scaffolding (xem `plans/bootstrap.md`).
  - Domain hiếm (fintech compliance, y tế) có thể cần expert đọc code thật — workflow bất lực.
  - Reviewer dễ overload ở epic lớn (xem mitigation #6.6.5: REVIEW_SUMMARY).
- **Neutral**:
  - Phụ thuộc nặng vào pre-commit hooks + helper scripts (15+ file scaffolding).

## Alternatives considered
- **Traditional PR review**: rejected — không scale với AI 10× output.
- **AI-only, no human gate**: rejected — không bắt được criteria drift, không có accountability cho production.
- **Mỗi PR có 1 reviewer chuyên nghiệp**: rejected — không có đủ reviewer skill cho mọi domain.

## References
- `docs/workflow.md` — full spec
- `plans/bootstrap.md` — scaffolding tasks

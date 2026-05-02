# Review Summary — Epic <name>

> **AI viết. Người đọc cái này TRƯỚC artifact chi tiết** (chống lỗ hổng #6.6.5 reviewer overload). Deep-dive khi cần. Tối đa 1 trang. Chỉ giữ ngắn gọn — đừng dài hơn 5–10 dòng cho mỗi mục.

## 3 thay đổi lớn nhất

1. **<thay đổi>** — file: `<path>` — risk: low / med / high
2. **<thay đổi>** — file: `<path>` — risk: …
3. **<thay đổi>** — file: `<path>` — risk: …

## 2 câu hỏi mở (cần người quyết định)

- [?] **<câu hỏi>** — context: `docs/design/<f>.md#<section>`
- [?] **<câu hỏi>** — context: `docs/requirements/<f>.md#<section>`

## 1 risk còn open (chấp nhận ship hay không?)

- **<risk>**
  - Mitigation đã làm: <…>
  - Residual: <điều gì còn rủi ro>
  - Đề xuất ship: ✅ / ❌ — vì <lý do>

## Người duyệt nên focus

1. <file/section quan trọng nhất — đường dẫn cụ thể>
2. <evidence run-id quan trọng nhất — đường dẫn>
3. <…>

## Skip-able (đã automate, người không cần kiểm)

- `security.json` — gate đã pass tự động (5/5 lớp)
- `pytest_junit.xml` — đã embed vào REPORT
- Pre-commit hooks — đã pass khi commit
- Pre-merge `verify_evidence.py` — đã pass

## Performance vs baseline

- Latency p50: <…>s vs baseline <…>s (<…>×)
- Tokens: <…> vs baseline <…> (<…>×)
- Cost: $<…> vs baseline $<…>
- Verdict: ✅ trong threshold 1.5× / ❌ regression

## ADR phát sinh trong epic
- <link to docs/adr/NNNN-...md> — <1 dòng tóm tắt>

## Nếu có cascade từ feedback upstream
- Liệt kê các cascade (xem REPORT.md mục `Upstream feedback addressed`)

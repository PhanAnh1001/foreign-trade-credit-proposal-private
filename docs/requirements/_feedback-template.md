# Feedback — PRD <feature> @ <YYYY-MM-DD HH:MM>

Target: `docs/requirements/<feature>.md` v<n>

> Người không sửa PRD trực tiếp. Mỗi reviewer 1 section `## <name>` riêng. AI flag conflict thành `[question]` mới ở cuối, KHÔNG tự chọn bên (lỗ hổng #6.6.9 multi-reviewer conflict).
> **Nếu feedback gửi sau khi đã code** → §7g cascade rule (impact analysis dưới đây + cập nhật `plans/<epic>.md` mục "Cascade từ feedback").

## <reviewer-name-1>

### F1. [must-fix] <…>
- **Evidence**: <vd "Acceptance criteria #2 — không đo được">
- **Expected**: <vd "ngưỡng số cụ thể, vd 'score ≥ 7'">
- **Reference** (optional): <link spec>

### F2. [nice-to-have] <…>
- **Evidence**: …
- **Expected**: …

## <reviewer-name-2>

### F3. [must-fix] <…>
- **Evidence**: …
- **Expected**: …

### F4. [question] <…>
- **Evidence**: …
- **Cần**: AI giải thích.

---

## AI — Conflict detected (nếu có)

> AI tự thêm khi phát hiện 2 reviewer đề xuất ngược nhau. KHÔNG tự chọn bên — đẩy lại người resolve.

### Q1. [conflict] <reviewer-1>.F<i> vs <reviewer-2>.F<j>
- <reviewer-1> muốn: <…>
- <reviewer-2> muốn: <…>
- Cần người quyết định: <ai/option> trước khi AI tiếp tục.

---

## AI Response — impact analysis (BẮT BUỘC nếu đã code — §7g)

### F1 (impact)
- Downstream artifacts cần cập nhật:
  - [ ] `docs/design/<f>.md` mục `<…>` — re-derive
  - [ ] `plans/<epic>.md` task `T<…>` — DoD đổi
  - [ ] `tests/e2e/test_<…>.py` assert
  - [ ] code: `src/<…>` const
- Estimate: <N> commit, ~<M> dòng diff
- Cảnh báo (nếu refactor > 50%): đề xuất tạo epic mới thay vì cascade.

### F2 (impact)
…

---

## AI Response

### AI Response F1
<sau khi đã sửa PRD + cascade — chỉ ra commit hash của từng artifact downstream>

### AI Response F2
<…>

### AI Response F3
<…>

### AI Response F4
<AI trả lời câu hỏi — không sửa code/PRD>

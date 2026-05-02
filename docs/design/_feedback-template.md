# Feedback — Design <feature> @ <YYYY-MM-DD HH:MM>

Target: `docs/design/<feature>.md` v<n>

> Mỗi reviewer 1 section `## <name>` riêng. AI flag conflict thành `[question]` ở cuối, KHÔNG tự chọn bên (lỗ hổng #6.6.9).
> **Nếu feedback gửi sau khi đã code** → §7g cascade rule.

## <reviewer-name-1>

### F1. [must-fix] <…>
- **Evidence**: <vd "Bảng 3.4 — `judge_quality` cùng vendor Meta với generator (vi phạm ràng buộc #5)">
- **Expected**: <vd "judge phải khác vendor">

### F2. [must-fix] <…>
- **Evidence**: <vd "Bảng 3.1 — extract_financial total/call 11.3K vượt TPM 8K của `gpt-oss-20b` (vi phạm #2)">
- **Expected**: …

## <reviewer-name-2>

### F3. [nice-to-have] <…>
- **Evidence**: …
- **Expected**: …

### F4. [question] <…>

---

## AI — Conflict detected (nếu có)

### Q1. [conflict] <reviewer-1>.F<i> vs <reviewer-2>.F<j>
- <reviewer-1> muốn: <…>
- <reviewer-2> muốn: <…>
- Cần người quyết định.

---

## AI Response — impact analysis (BẮT BUỘC nếu đã code — §7g)

### F1 (impact)
- Downstream artifacts cần cập nhật:
  - [ ] `plans/<epic>.md` task `T<…>` (re-bind judge model)
  - [ ] `src/llm/factory.py` `get_judge_llm()`
  - [ ] `tests/unit/nodes/test_judge_quality.py`
  - [ ] `ete-evidence/.../eval.json` baseline
- Estimate: <N> commit, ~<M> dòng diff
- Re-bind ảnh hưởng cost? Có / Không
- Cần re-run từ Bước 5 trở đi: ✅
- ADR cần tạo: `docs/adr/NNNN-<title>.md` (vì là quyết định kiến trúc)

### F2 (impact)
…

---

## AI Response

### AI Response F1
<chỉ ra commit hash, model mới, ADR liên quan>

### AI Response F2
<…>

### AI Response F3
<…>

### AI Response F4
<…>

# Feedback — Epic <epic-slug> @ <YYYY-MM-DD HH:MM>

Target: `plans/<epic-slug>.md` v<n>

> Cấp Epic checklist (vd "T5 quá lớn, tách T5a/T5b"). Không dùng cho evidence E2E (đó là `ete-evidence/.../FEEDBACK.md`).
> Mỗi reviewer 1 section riêng (lỗ hổng #6.6.9).
> Nếu đã code → §7g cascade rule.

## <reviewer-name-1>

### F1. [must-fix] <…>
- **Evidence**: <vd "Task T5 — DoD không đo được, chỉ ghi 'agent hoạt động'">
- **Expected**: <vd "DoD phải là test command + expected output">

### F2. [nice-to-have] <…>

## <reviewer-name-2>

### F3. [question] <…>

---

## AI — Conflict detected (nếu có)
…

---

## AI Response — impact analysis (BẮT BUỘC nếu đã code — §7g)

### F1 (impact)
- Tasks cần thêm/đổi: <…>
- Code cần đụng: <…>
- Test cần thêm: <…>
- Estimate: <N> commit
- Re-run cần lại: chỉ Bước 5 / cả 5 → 5.5 → 6
- Cascade trên branch riêng (`tools/cascade_branch.sh F<id>`)

### F2 (impact)
…

---

## AI Response

### AI Response F1
<…>

### AI Response F2
<…>

### AI Response F3
<…>

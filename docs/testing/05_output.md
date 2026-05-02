# 05 — Output validation

> Validate output cuối cùng: schema, claim verification, DOCX render. Đây là tầng cuối trước khi chuyển sang E2E + Evidence (Bước 6).

## Lệnh chạy
```bash
pytest tests/integration/test_output_validation.py -q
```

## Expected output
```
test_pydantic_strict_validation PASSED
test_docx_table_count PASSED
test_docx_no_unfilled_placeholders PASSED
test_claim_verification_against_ocr PASSED
=========== 4 passed in <T>s ===========
```

## Cách đọc log nếu FAIL
- `pydantic_strict` fail → output LLM không match schema, tăng prompt strictness hoặc thêm Pydantic validator.
- DOCX `n_tables` lệch → template thay đổi hoặc renderer skip section.
- `unfilled_placeholders` còn → có `[XYZ]` chưa map; kiểm tra `human_mapping.md` đầy đủ chưa.
- `claim_verification` fail → 1 số liệu trong output không tìm thấy trong OCR text → có khả năng hallucinate, không pass.

## Last run
`PASS` — `2026-04-30T10:03:00+07:00` — 4 passed

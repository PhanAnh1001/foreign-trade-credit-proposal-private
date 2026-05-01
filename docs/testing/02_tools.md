# 02 — Tools

> Test từng tool độc lập. Mock LLM ở tầng này được phép (test thuần logic).

## Lệnh chạy
```bash
pytest tests/unit/tools/ -q
```

## Expected output
```
tests/unit/tools/test_pdf_ocr.py ........        [ 30%]
tests/unit/tools/test_parse_balance_sheet.py ... [ 60%]
tests/unit/tools/test_render_docx.py ........... [100%]
=========== <N> passed in <T>s ===========
```

## Cách đọc log nếu FAIL
- `test_pdf_ocr` fail → kiểm tra fixture PDF có corrupt không, OCR cache stale → xoá `docs/ocr-cache/<co>/`.
- `test_parse_balance_sheet` fail → mã CĐKT mới? cập nhật regex trong `src/tools/parser.py`.
- `test_render_docx` fail → template thay đổi schema, đối chiếu `templates/<bank>.docx`.

## Last run
`PASS` — `2026-04-30T10:00:30+07:00` — `<N>` passed

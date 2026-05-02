# 03 — Nodes (LLM-backed)

> Test các node có gọi LLM. Dùng fixture + golden output. **Không mock LLM** ở tầng này — gọi thật với input nhỏ.

## Lệnh chạy
```bash
pytest tests/unit/nodes/ -q --maxfail=1
```

## Expected output
```
tests/unit/nodes/test_extract_financial.py ..  [ 50%]
tests/unit/nodes/test_judge_quality.py ..      [100%]
=========== <N> passed in <T>s ===========
```

## Cách đọc log nếu FAIL
- `429 Too Many Requests` → vi phạm ràng buộc TPM. **Quay lại Bước 2a Design**, re-bind model. KHÔNG retry/sleep.
- `413 Request too large` → vi phạm ràng buộc context. Re-bind model có context lớn hơn.
- Output không match golden → so sánh diff, quyết định: cập nhật golden (nếu thay đổi prompt là intentional) hoặc fix code.
- Vendor 404 → model bị decommission, cập nhật `Model history` trong Design.

## Last run
`PASS` — `2026-04-30T10:01:00+07:00` — `<N>` passed

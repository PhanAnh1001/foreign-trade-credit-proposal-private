# 04 — Pipeline

> Chạy toàn bộ pipeline trên **1 fixture nhỏ** (không phải full E2E). Mục đích: kiểm tra ráp các node lại không bị broken.

## Lệnh chạy
```bash
pytest tests/integration/test_pipeline.py -q
```

## Expected output
```
tests/integration/test_pipeline.py::test_smoke_pipeline_small PASSED
=========== 1 passed in <T>s ===========
```

## Cách đọc log nếu FAIL
- Lỗi data shape giữa node → kiểm tra Pydantic schema không khớp giữa output node A và input node B.
- Timeout → 1 node nào đó chạy quá lâu, xem log `latency_ms` từng node.
- Side-effect file (cache, output) bị lưu sai chỗ → kiểm tra path absolute vs relative.

## Last run
`PASS` — `2026-04-30T10:02:00+07:00` — duration: <T>s

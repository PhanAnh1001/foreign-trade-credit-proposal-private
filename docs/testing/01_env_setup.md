# 01 — Env setup

> Bước đầu tiên trong chuỗi `01 → 02 → 03 → 04 → 05`. **Fail fast**: nếu bước này FAIL, dừng, không chạy tiếp. Người chỉ đọc dòng cuối.

## Lệnh chạy
```bash
make install
python -m src.config.check_env
```

## Expected output
```
✅ Python 3.12.x
✅ All required env vars present: GROQ_API_KEY, OPENAI_API_KEY, ...
✅ Cache dir writable: docs/ocr-cache/
✅ Test fixtures present: tests/e2e/fixtures/
```

## Cách đọc log nếu FAIL
- Thiếu env var → kiểm tra `.env` có copy từ `.env.example` chưa.
- Cache dir không writable → `chmod -R u+w docs/ocr-cache/`.
- Fixtures thiếu → pull lại git LFS hoặc copy từ `data/uploads/`.

## Last run
> AI cập nhật mỗi lần chạy.

`PASS` — `2026-04-30T10:00:00+07:00` — log: `logs/run_20260430_100000.log`

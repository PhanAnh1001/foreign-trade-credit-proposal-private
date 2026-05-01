# Design — <tên feature>

> AI draft. ≤ 2 trang. Phải có sơ đồ, danh sách module, **bảng model assignment** (Bước 2a), trade-offs. Người duyệt bằng dòng `## Approved by ...` hoặc viết `<feature>.feedback.md`.

Liên kết: PRD `docs/requirements/<feature>.md`

## 1. Kiến trúc (ASCII)

```
<vd>
┌─────────┐    ┌─────────┐    ┌─────────┐
│  PDFs   │ →  │  OCR    │ →  │  Parser │
└─────────┘    └─────────┘    └────┬────┘
                                   ↓
                         ┌─────────────────┐
                         │ Financial extr. │
                         └────────┬────────┘
                                  ↓
                         ┌─────────────────┐
                         │  DOCX renderer  │
                         └─────────────────┘
```

## 2. Module / Tool

| Tên | Loại | Mô tả 1 dòng |
|---|---|---|
| `pdf_ocr` | tool | Trích text từ PDF, có cache |
| `parse_balance_sheet` | node | Regex + heuristics, không LLM |
| `extract_financial` | node | LLM (cần TPM cao) |
| `render_docx` | tool | Điền template DOCX |
| `judge_quality` | node | LLM-as-Judge, khác vendor |

## 3. Model binding (BẮT BUỘC — xem `docs/workflow.md` §2a)

### 3.1. Token demand mỗi function

> Quy tắc ước input tokens: **chars × 0.65** (tiếng Việt mixed code), **chars ÷ 4** (tiếng Anh thuần).

| Function | Task | Input chars | Input tokens | max_tokens | Total/call | Calls/run |
|---|---|---|---|---|---|---|
| `extract_financial` | parse CĐKT | ≤ 11000 | ~7.2K | 4096 | ~11.3K | 3 |
| `judge_quality` | chấm output | ≤ 4000 | ~2.6K | 1024 | ~3.6K | 1 |
| `<thêm dòng>` | … | … | … | … | … | … |

### 3.2. Rate limit của các model ứng cử

> Copy từ `docs/CLAUDE.md` (cập nhật khi vendor đổi). Loại model không đủ TPM, không đủ context, không hỗ trợ feature cần.

| Model | Vendor | Context | TPM | RPD | Hỗ trợ |
|---|---|---|---|---|---|
| `llama-3.3-70b` | Meta/Groq | 128K | 12K | 1K | text, JSON |
| `llama-4-scout` | Meta/Groq | 10M | 30K | 1K | vision |
| `gpt-oss-20b` | OpenAI/Groq | 8K | 8K | 1K | text |
| `<…>` | … | … | … | … | … |

### 3.3. Gán model — 6 ràng buộc cứng (dừng ngay khi violate)

| # | Ràng buộc |
|---|---|
| 1 | `input_tokens + max_tokens ≤ context_window × 0.9` |
| 2 | `Total/call ≤ TPM` |
| 3 | `Calls/day ≤ RPD × 0.7` (giữ 30% buffer) |
| 4 | Function nào nhiều token nhất → model TPM cao nhất |
| 5 | Judge phải khác vendor với generator nó chấm |
| 6 | Parallel nodes phải khác TPM bucket (= khác model) |

### 3.4. Bảng gán model cuối cùng

| Function | Model | TPM/RPD/Ctx | Vendor | Lý do (ràng buộc nào quyết định) |
|---|---|---|---|---|
| `extract_financial` | `llama-3.3-70b` | 12K/1K/128K | Meta | #4 demand cao nhất; #1 ctx 128K không bao giờ 413 |
| `judge_quality` | `gpt-oss-20b` | 8K/1K/8K | OpenAI | #5 ≠ Meta(generator) |
| `<…>` | … | … | … | … |

### 3.5. Cost (chỉ tính nếu paid tier)

`cost_per_run = sum(input_tokens × in_price + output_tokens × out_price)`

| Function | $/call | calls/run | $/run | % run cost |
|---|---|---|---|---|
| ... | ... | ... | ... | ... |

### 3.6. Model history (cập nhật khi đổi model giữa epic)

| Date | Function | From → To | Lý do |
|---|---|---|---|
| YYYY-MM-DD | … | … | … |

## 4. Trade-offs (≥ 2 alternative đã cân nhắc)

### Alternative A: <…>
- ✅ Pros: …
- ❌ Cons: …

### Alternative B: <…>
- ✅ Pros: …
- ❌ Cons: …

**Chọn**: <A hoặc B> vì <lý do>.

## 5. Rủi ro chính

| Rủi ro | Mitigation |
|---|---|
| Vendor decommission model | Wrapper `get_<role>_llm()` swap 1 chỗ |
| OCR fail trên scan kém | Fallback vision LLM (`llama-4-scout`) |
| Số liệu sai unit (VND > 1e10) | Pydantic strict + claim verification |

---

## Approved by <tên> @ <YYYY-MM-DD>
<!-- Tick khi duyệt. Có feedback → tạo file <feature>.feedback.md. -->

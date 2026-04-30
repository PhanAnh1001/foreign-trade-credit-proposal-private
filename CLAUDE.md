# Git
Khi ở master hoặc main thì không commit và push mà tạo nhánh mới.
Khi ở nhánh khác master và main thì không cần tạo nhánh mới mà pull code master, fix conflict ưu tiên code master, rồi có thay đổi sẽ commit và push.

# Models đang dùng (Groq Free Tier)

## Rate limits

| Model | RPM | RPD | TPM | TPD |
|---|---|---|---|---|
| `llama-3.1-8b-instant` | 30 | 14.4K | 6K | 500K |
| `llama-3.3-70b-versatile` | 30 | 1K | 12K | 100K |
| `meta-llama/llama-4-scout-17b-16e-instruct` | 30 | 1K | 30K | 500K |
| `meta-llama/llama-prompt-guard-2-22m` | 30 | 14.4K | 15K | 500K |
| `meta-llama/llama-prompt-guard-2-86m` | 30 | 14.4K | 15K | 500K |
| `openai/gpt-oss-120b` | 30 | 1K | 8K | 200K |
| `openai/gpt-oss-20b` | 30 | 1K | 8K | 200K |
| `openai/gpt-oss-safeguard-20b` | 30 | 1K | 8K | 200K |
| `qwen/qwen3-32b` | **60** | 1K | 6K | 500K |
| `groq/compound` | 30 | 250 | 70K | — |
| `groq/compound-mini` | 30 | 250 | 70K | — |
| `allam-2-7b` | 30 | 7K | 6K | 500K |
| `whisper-large-v3` | 20 | 2K | — | — |
| `whisper-large-v3-turbo` | 20 | 2K | — | — |

## Context window

| Model | Context window | Ghi chú |
|---|---|---|
| `meta-llama/llama-4-scout-17b-16e-instruct` | 10M tokens | Scout architecture |
| `llama-3.1-8b-instant` | 128K | |
| `llama-3.3-70b-versatile` | 128K | |
| `qwen/qwen3-32b` | 32K | |
| `openai/gpt-oss-120b` | ~8K | Ước tính từ hành vi trên Groq |
| `openai/gpt-oss-20b` | ~8K | Confirmed: input+max_tokens > ~8K → 413. **Có reasoning_tokens** (~520T nội bộ) + ~250T output ≈ 770T completion; max_tokens=2048 đủ an toàn |

**Hệ quả**: `gpt-oss-*` chỉ dùng được khi `input_tokens + max_tokens ≤ ~8K`. SG2 dùng `gpt-oss-120b` với `max_tokens=4096` + input ~2.3K = ~6.4K ✓. QR dùng `gpt-oss-20b` với `max_tokens=2048` + input ~0.7K = ~2.7K ✓ (LC Agent judge prompt nhỏ hơn credit proposal agent).

---

# Chiến thuật làm bài test phỏng vấn

## Deliverables bắt buộc (3 items)
1. **Design document** 1–2 trang: memory, planning, tool, action + danh sách tools
2. **Video demo** 5–10 phút: architecture → live run → output → limitations
3. **Source code** với README setup + chạy

## Scope strategy
- Implement đủ 3 output, nhưng mỗi output chỉ làm **2–3 field trọng tâm** thật tốt
- Output 3 (tài chính) chỉ cần CĐKT + P&L, 5–6 ratio, nhận xét so sánh 2–3 năm — đủ demonstrate
- **Depth hơn breadth**: 1 output hoàn chỉnh tốt hơn 3 output nửa vời

## Điểm tạo ấn tượng (từ "đủ yêu cầu" → "xuất sắc")
- **Self-correction loop**: quality_review node chấm điểm → route về node yếu nhất nếu < 7/10
- **Structured output**: Pydantic models enforce schema, retry khi parse fail
- **Financial cross-validation**: tổng tài sản = tổng nguồn vốn (deterministic, không tốn LLM call)
- **LangSmith tracing**: show trong demo — traces từng node, token usage, latency
- **Video có narrative**: (a) business problem 30s → (b) architecture 1 phút → (c) live run → (d) so sánh output vs mẫu → (e) limitations

## Sai lầm phổ biến cần tránh
- **Over-engineer**: RAG + vector DB cho 2–3 file cố định là overkill — in-context đủ với 128K context
- **Bỏ qua PDF extraction**: garbage in → garbage out; dành ≥ 30% effort cho data pipeline
- **Không chạy live được**: Day 5 phải có version end-to-end; Day 6–7 là polish, không phải "lần đầu chạy"
- **Quên design document**: viết trước khi code (Day 2), update trước khi nộp
- **Hallucination số tài chính**: tách ratio calculation ra Python thuần, prompt bắt LLM chỉ dùng số từ context

## Tiêu chí đánh giá (theo thứ tự ưu tiên)
1. **Data extraction chính xác** — số liệu tài chính output phải match file gốc
2. **Agent design có chiều sâu** — reflection, validation, guardrails
3. **Demo có narrative** — communicate được "tại sao" chọn approach này

---

# Chiến thuật gán model

**Nguyên tắc**: Không dùng `groq/` prefix. Mỗi function dùng 1 model riêng. Gán TPM cao → function tiêu thụ token nhiều nhất. Judge phải khác vendor so với các generator nó đánh giá.

## Ước tính token demand mỗi function

| Function | Task | Input chars | Input tokens | max_tokens | Total/call | Calls/run |
|---|---|---|---|---|---|---|
| `get_vision_llm` | Vision OCR | 6 trang ảnh | ~21K vision | default | **~21K+** | 3 PDF × cached |
| `get_financial_llm` | SG3 Stage1 CĐKT | `_CDKT_MAX=11000` | ~7.2K | 4096 | **~11.3K** | 3 (1/năm) |
| `get_financial_llm` | SG3 Stage2 KQKD | `_KQKD_MAX=5000` | ~3.3K | 4096 | **~7.4K** | 3 |
| `get_financial_llm` | SG3 Narrative | data dict + prompt | ~3.5K | 4096 | **~7.5K** | 1 |
| `get_smart_llm` | SG2 sector synthesis | `context[:6000]` | ~2.3K | **4096** | **~6.4K** | 2–3 |
| `get_medium_llm` | SG1 company info | md file + few-shot | ~3K | 4096 | **~7K** | 1–2 |
| `get_judge_llm` | QR judge | `[:1500]+[:1500]+[:2000]` | ~1.3K | 1024 | **~2.3K** | 1–2 |
| `get_fast_llm` | TOC parsing | `_TOC_TEXT_MAX=1000` | ~0.3K | 2048 | **~2.4K** | 3 |

**SG3 tổng/run**: 3 năm × (11.3 + 7.4 + 7.5K) ≈ **79K tokens** (~20K TPM cần)
**SG2 tổng/run**: 3 calls × 6.4K ≈ **19K tokens** (~10K TPM cần)
SG2 + SG3 chạy song song → phải dùng **2 TPM bucket riêng**.

## Gán model (TPM rank → demand rank)

| Rank demand | Function | Model | TPM | Context | Vendor | Lý do |
|---|---|---|---|---|---|---|
| 1 (vision) | `get_vision_llm` | `meta-llama/llama-4-scout-17b-16e-instruct` | 30K | large | Meta | Duy nhất hỗ trợ vision |
| 2 (SG3) | `get_financial_llm` | `llama-3.3-70b-versatile` | **12K** | 128K | Meta | TPM cao nhất text, 128K ctx không bao giờ 413 |
| 3 (SG2) | `get_smart_llm` | `openai/gpt-oss-120b` | 8K | large | OpenAI | SG2 nhẹ hơn SG3; max_tokens=4096 → 6.4K total |
| 4 (SG1) | `get_medium_llm` | `qwen/qwen3-32b` | 6K | 32K+ | Qwen | max_tokens=4096; emit `<think>` → `strip_llm_json()` |
| 5 (judge) | `get_judge_llm` | `openai/gpt-oss-20b` | 8K | ~8K | OpenAI | max_tokens=2048, input ~1.3K → 3.3K total ✓; ≠ SG1(Qwen) ≠ SG3(Meta) |
| 6 (TOC) | `get_fast_llm` | `llama-3.1-8b-instant` | 6K | 128K | Meta | 14.4K RPD; input nhỏ nhất, bảo toàn quota 1K-RPD |

**Judge independence**: QR (OpenAI-20b) review SG1 (Qwen) ✓, SG3 (Meta) ✓ — cross-vendor. SG2 cùng OpenAI vendor nhưng khác model size (120b vs 20b).

## Lỗi đã gặp và lý do đổi model

| Model | Lỗi | Fix |
|---|---|---|
| `moonshotai/kimi-k2-instruct` | 404 — Groq gỡ khỏi free tier (2026-04) | → `llama-4-scout` rồi `qwen3-32b` |
| `groq/compound` + `groq/compound-mini` | User preference — tránh `groq/` prefix | → `gpt-oss-120b` / `gpt-oss-20b` |
| `openai/gpt-oss-20b` trên SG2 | 413 — max_tokens=8192 + input ~2.3K > ~8K window | → swap sang QR; SG2 dùng `gpt-oss-120b` max_tokens=4096 |
| `openai/gpt-oss-20b` trên QR (max_tokens=1024) | Output bị cắt — 1024 quá nhỏ cho judge response | → tăng max_tokens=2048; input ~1.3K + 2048 = ~3.3K ✓ |
| `openai/gpt-oss-20b` trả response rỗng (tạm thời) | Groq API issue tạm thời — model dùng **reasoning_tokens** (~520T nội bộ). Đã test lại: hoạt động bình thường, max_tokens=2048 đủ. | → Restored làm judge. Nếu gặp lại: kiểm tra reasoning_tokens trong response_metadata |
| `llama-3.3-70b` trên SG2 (trước swap) | 429 TPM — SG2+SG3 cùng bucket khi song song | → SG3 dùng `llama-3.3-70b` (bucket riêng) |

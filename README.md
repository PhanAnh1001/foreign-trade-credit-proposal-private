# LC Application Agent

AI Agent tự động điền đơn xin mở L/C (Letter of Credit) từ hợp đồng ngoại thương.

> English version: [README.en.md](README.en.md)

## Tổng quan

Hệ thống sử dụng **LangGraph** để orchestrate pipeline 4 node tuần tự, có vòng lặp tự sửa lỗi khi điểm chất lượng chưa đạt:

1. **extract_node** — LLM trích xuất các trường thông tin từ hợp đồng ngoại thương
2. **validate_node** — Python thuần kiểm tra luật UCP600, ISBP821, Incoterms, luật ngoại hối Việt Nam
3. **quality_review_node** — LLM-as-Judge chấm điểm (0–10); nếu < 7.0 → retry về extract_node (tối đa 1 lần)
4. **fill_node** — python-docx điền kết quả vào template DOCX của ngân hàng

**Input**: hợp đồng ngoại thương (TXT / PDF / DOCX)

**Output**: `data/outputs/{bank}/{company_slug}/LC-Application-{contract}.docx`

## Kiến trúc

```
Contract (TXT/PDF/DOCX)
         │
   [extract_node]         ← LLM: llama-3.3-70b-versatile
         │
   [validate_node]        ← Pure Python: UCP600 + ISBP821 + Incoterms + Vietnam forex
         │
   [quality_review_node]  ← LLM-as-Judge: qwen/qwen3-32b
         │
    ┌────┴────┐
    │  score? │
  ≥7.0      <7.0 (retry once → extract_node)
    │
  [fill_node]             ← python-docx: fill DOCX template
         │
  LC-Application.docx
  data/outputs/{bank}/{company_slug}/
```

## Cài đặt

### Yêu cầu

- Python 3.12 (quản lý qua [uv](https://docs.astral.sh/uv))
- Groq API key (miễn phí tại [console.groq.com](https://console.groq.com))

### Các bước cài đặt

```bash
# Tạo virtual environment với Python 3.12
uv venv --python 3.12
source .venv/bin/activate

# Cài đặt dependencies
uv pip install -r requirements.txt
```

### Cấu hình environment

Tạo file `.env`:

```env
GROQ_API_KEY=your_groq_api_key_here          # bắt buộc

LANGSMITH_API_KEY=your_langsmith_key         # tùy chọn, để trace
LANGCHAIN_TRACING_V2=true                    # tùy chọn, bật LangSmith tracing
```

> **Lưu ý**: `GROQ_API_KEY` là key duy nhất bắt buộc. LangSmith hoàn toàn tùy chọn.

## Sử dụng

### CLI

```bash
# Chạy cơ bản
python -m src.main --contract data/sample/contract.txt

# Chỉ định ngân hàng và thư mục output
python -m src.main --contract data/sample/contract.txt --bank vietcombank --output-dir data/outputs/ete
```

### Python API

```python
from src.agents.graph import run_lc_application

state = run_lc_application("data/sample/contract.txt", bank="vietcombank")
```

## Cấu trúc dự án

```
src/
  config.py              # BANK_VCB/BIDV/VIETINBANK constants, get_bank_template_path(),
                         #   slugify_company(), get_bank_output_dir()
  agents/
    graph.py             # LangGraph pipeline + run_lc_application()
    node_extract.py      # extract_node: LLM trích xuất trường thông tin
    node_validate.py     # validate_node: rule engine
    node_quality.py      # quality_review_node: LLM-as-Judge
    node_fill.py         # fill_node: điền DOCX template
  tools/
    contract_extractor.py  # extract_contract_text + extract_lc_fields_from_contract
    lc_rules_validator.py  # UCP600 / ISBP821 / Incoterms / Vietnam forex rules
  models/
    state.py             # LCAgentState TypedDict
    lc_application.py    # LCApplicationData + DocumentRequirements Pydantic models
  knowledge/
    loader.py            # YAML knowledge loader
    rules/               # ucp600_rules.yaml, isbp821_rules.yaml,
                         #   incoterms_rules.yaml, vietnam_forex_law.yaml
  utils/
    docx_filler.py       # Wingdings checkbox filling, run-level text replacement
    llm.py               # get_extraction_llm(), get_judge_llm()
    logger.py            # colored logging, @timed_node decorator, LangSmith tracing
  main.py                # CLI entry point
data/
  sample/contract.txt    # Hợp đồng mẫu (VN-CN-2024-001, USD 450K, CIF)
  templates/docx/
    vietcombank/         # Application-for-LC-issuance.docx
  outputs/{bank}/{slug}/ # File DOCX được sinh ra (gitignored)
tests/
  test_config.py         # Multi-bank config tests (8 tests)
  test_docx_filler.py    # DOCX filling tests
  test_models.py         # Pydantic model tests
  test_lc_rules_validator.py  # Rule engine tests (44 tests)
  test_ete.py            # End-to-end tests (cần GROQ_API_KEY)
```

## LLM Models (Groq)

| Node | Model | TPM | Mục đích |
|------|-------|-----|----------|
| `extract_node` | `llama-3.3-70b-versatile` | 12K | Trích xuất trường từ hợp đồng (~7K tokens/call) |
| `quality_review_node` | `qwen/qwen3-32b` | 6K | LLM-as-Judge chấm điểm; khác vendor so với extractor |

`validate_node` và `fill_node` không dùng LLM (Python thuần).

## Knowledge base (deterministic, không dùng LLM)

| Nguồn luật | Quy tắc chính |
|------------|---------------|
| **UCP600** | Irrevocable mặc định (Art.3), thời hạn xuất trình 21 ngày (Art.14c), vận đơn sạch (Art.27) |
| **ISBP 821** | Mô tả hóa đơn, B/L full set, tài liệu bằng tiếng Anh |
| **Incoterms 2000/2010/2020** | CIF/CIP → chứng từ bảo hiểm (tối thiểu 110%, ICC A); FOB → B/L freight collect |
| **Luật ngoại hối VN** | VN-01 đồng tiền ≠ VND (NĐ 70/2014 Art.4), VN-02 số hợp đồng bắt buộc (Art.11), VN-03 ngân hàng phát hành được NHNN cấp phép (Art.6), VN-04 LC nhập khẩu = giao dịch vãng lai ✓, VN-05 nhắc ký quỹ, VN-06 kiểm tra hàng hóa quản lý |

## Hỗ trợ đa ngân hàng

Thêm ngân hàng mới bằng cách đặt template tại `data/templates/docx/{bank_slug}/Application-for-LC-issuance.docx`, sau đó truyền `bank={bank_slug}` vào `run_lc_application()`. Thư mục output sẽ tự động là `data/outputs/{bank_slug}/{company_slug}/`.

Các hằng số ngân hàng trong `src/config.py`:

| Hằng số | Giá trị |
|---------|---------|
| `BANK_VCB` | `"vietcombank"` (mặc định) |
| `BANK_BIDV` | `"bidv"` |
| `BANK_VIETINBANK` | `"vietinbank"` |

## Chạy tests

```bash
# Unit tests (không cần API key)
python -m pytest tests/ --ignore=tests/test_ete.py -v   # 52 tests

# End-to-end tests (cần GROQ_API_KEY)
python -m pytest tests/test_ete.py -v
```

## Lưu ý

- **GROQ_API_KEY** là API key duy nhất bắt buộc
- **Chống hallucination**: LLM chỉ được trích xuất từ văn bản hợp đồng — không được tự bịa số liệu
- **Rule engine**: Các quy tắc UCP600, Incoterms được kiểm tra bằng Python thuần, không qua LLM
- **Wingdings checkbox**: Template dùng ký tự U+F06F (chưa tick) / U+F0FE (đã tick) — **không phải** Unicode chuẩn □/■
- **Bảo mật**: Không commit file `.env` hoặc API key vào git (đã có trong `.gitignore`)

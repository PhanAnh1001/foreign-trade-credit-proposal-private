# LC Application Agent

**Tự động tạo đơn xin mở L/C từ hợp đồng ngoại thương — dùng được với mọi ngân hàng, mọi công ty.**

> English version: [README.en.md](README.en.md)

---

## Điểm nổi bật

| | |
|---|---|
| 🏦 **Mọi ngân hàng** | Thêm ngân hàng mới chỉ cần đặt file template DOCX vào đúng thư mục — không cần sửa code |
| 🏢 **Mọi công ty** | Thư mục output tự động tổ chức theo tên công ty (slugified) — không bao giờ bị ghi đè |
| 📄 **Mọi định dạng hợp đồng** | TXT, PDF, DOCX — tự động trích xuất, không cần tiền xử lý |
| ⚖️ **Tuân thủ quốc tế** | Rule engine kiểm tra UCP600, ISBP821, Incoterms 2020, luật ngoại hối Việt Nam |
| 🔄 **Tự sửa lỗi** | LLM-as-Judge chấm điểm; nếu < 7/10 → trích xuất lại với feedback cụ thể |

**Output**: `data/outputs/{bank}/{company}/LC-Application-{contract}.docx`

---

## Cách thêm ngân hàng mới

Chỉ cần 2 bước — **không sửa code**:

```
1. Đặt template DOCX vào:
   data/templates/docx/{ten-ngan-hang}/Application-for-LC-issuance.docx

2. Truyền tên ngân hàng vào lệnh gọi:
   run_lc_application("contract.txt", bank="ten-ngan-hang")
```

Agent tự động:
- Tìm đúng template của ngân hàng đó
- Tạo thư mục output riêng: `data/outputs/{bank}/{company_slug}/`
- Điền form theo cấu trúc file DOCX được cung cấp

---

## Tổng quan kiến trúc

```
Hợp đồng ngoại thương (TXT / PDF / DOCX)
                │
          [extract_node]          ← LLM: llama-3.3-70b-versatile
                │                    Trích xuất ~30 trường: bên mua, bên bán,
                │                    số tiền, ngày, Incoterms, cảng, chứng từ...
          [validate_node]         ← Pure Python: UCP600 + ISBP821 + Incoterms + VN forex
                │                    Bổ sung defaults, kiểm tra tính hợp lệ,
                │                    thêm chứng từ bảo hiểm nếu CIF/CIP
          [quality_review_node]   ← LLM-as-Judge: openai/gpt-oss-20b (cross-vendor)
                │
           ┌────┴────┐
           │  score? │
         ≥7.0      <7.0 → retry extract với feedback
           │
          [fill_node]             ← python-docx: điền template của ngân hàng được chọn
                │
   data/outputs/{bank}/{company}/LC-Application-{contract}.docx
```

**Phân tách rõ ràng**: LLM chỉ trích xuất dữ liệu từ hợp đồng. Mọi quy tắc nghiệp vụ (UCP600, Incoterms, luật ngoại hối) được kiểm tra bằng Python thuần — không tốn token, không hallucinate.

---

## Cài đặt

```bash
uv venv --python 3.12 && source .venv/bin/activate
uv pip install -r requirements.txt
cp .env.example .env   # điền GROQ_API_KEY
```

Chỉ cần 1 API key:

```env
GROQ_API_KEY=your_groq_api_key_here
```

---

## Sử dụng

### CLI

```bash
# Vietcombank (mặc định)
python -m src.main --contract data/sample/contract.txt

# BIDV
python -m src.main --contract contract.txt --bank bidv

# Bất kỳ ngân hàng nào
python -m src.main --contract contract.txt --bank ten-ngan-hang

# Override thư mục output
python -m src.main --contract contract.txt --bank vietcombank --output-dir /tmp/test
```

### Python API

```python
from src.agents.graph import run_lc_application

# Vietcombank
state = run_lc_application("contract.txt", bank="vietcombank")

# BIDV
state = run_lc_application("contract.txt", bank="bidv")

# Kết quả
print(state["output_docx_path"])   # data/outputs/bidv/ten_cong_ty/LC-Application-contract.docx
print(state["quality_score"])      # 8.5
print(state["company_slug"])       # ten_cong_ty (tự động từ tên công ty trong hợp đồng)
```

---

## Cấu trúc template và output

```
data/
  templates/docx/
    vietcombank/          ← template Vietcombank (có sẵn)
      Application-for-LC-issuance.docx
    bidv/                 ← thêm BIDV: chỉ cần đặt file vào đây
      Application-for-LC-issuance.docx
    ten-ngan-hang-khac/   ← bất kỳ ngân hàng nào
      Application-for-LC-issuance.docx

  outputs/                ← tự động tạo, phân cấp theo ngân hàng + công ty
    vietcombank/
      cong_ty_abc/
        LC-Application-hop-dong-001.docx
      cong_ty_xyz/
        LC-Application-hop-dong-002.docx
    bidv/
      cong_ty_abc/
        LC-Application-hop-dong-003.docx
```

---

## Cấu trúc dự án

```
src/
  config.py              # BANK_VCB/BIDV/VIETINBANK constants + helper functions:
                         #   get_bank_template_path(bank)  → Path tới template
                         #   get_bank_output_dir(bank, slug) → Path output đã tạo sẵn
                         #   slugify_company(name)         → "Công ty ABC" → "cong_ty_abc"
  agents/
    graph.py             # run_lc_application(contract, bank, output_dir)
    node_extract.py      # LLM: trích xuất ~30 trường từ hợp đồng
    node_validate.py     # Python: UCP600 / ISBP821 / Incoterms / VN forex rules
    node_quality.py      # LLM-as-Judge: chấm điểm + feedback
    node_fill.py         # python-docx: điền đúng template của bank được chỉ định
  tools/
    contract_extractor.py  # TXT/PDF/DOCX → text → structured JSON
    lc_rules_validator.py  # Rule engine: UCP600 + ISBP821 + Incoterms + VN forex
  models/
    state.py             # LCAgentState: bank, company_slug, lc_data, quality_score...
    lc_application.py    # LCApplicationData + DocumentRequirements (Pydantic)
  knowledge/rules/       # ucp600_rules.yaml, isbp821_rules.yaml,
                         #   incoterms_rules.yaml, vietnam_forex_law.yaml
  utils/
    docx_filler.py       # Wingdings checkbox, run-level fill, buyer/seller replace
    llm.py               # get_extraction_llm(), get_judge_llm()
data/
  sample/contract.txt    # Hợp đồng mẫu (VN-CN-2024-001, USD 450K, CIF)
  templates/docx/vietcombank/  # Template Vietcombank
tests/                   # 52 unit tests + ETE tests
```

---

## LLM Models (Groq Free Tier)

| Node | Model | TPM | Vai trò |
|------|-------|-----|---------|
| `extract_node` | `llama-3.3-70b-versatile` | 12K | Trích xuất trường từ hợp đồng (~5K tokens/call) |
| `quality_review_node` | `openai/gpt-oss-20b` | 8K | Judge cross-vendor (OpenAI ≠ Meta extractor); dùng reasoning tokens nội bộ |

`validate_node` và `fill_node` không dùng LLM — Python thuần, tốc độ cao, kết quả xác định.

---

## Knowledge base — Rule engine (không dùng LLM)

| Nguồn | Quy tắc chính |
|-------|--------------|
| **UCP600** | Irrevocable mặc định (Art.3), xuất trình 21 ngày (Art.14c), vận đơn sạch (Art.27) |
| **ISBP 821** | Mô tả hóa đơn khớp LC, B/L full set, tài liệu bằng tiếng Anh |
| **Incoterms 2000/2010/2020** | CIF/CIP → bảo hiểm ≥ 110% ICC(A); FOB → B/L freight collect |
| **Pháp luật VN** | VN-01 tiền tệ ≠ VND (NĐ 70/2014 Đ.4), VN-02 số HĐ bắt buộc (Đ.11), VN-03 TCTD được phép (Đ.6), VN-04 giao dịch vãng lai ✓, VN-05 ký quỹ, VN-06 hàng quản lý |

---

## Chạy tests

```bash
python -m pytest tests/ --ignore=tests/test_ete.py -v   # 52 unit tests, không cần API key
python -m pytest tests/test_ete.py -v                   # ETE (cần GROQ_API_KEY)
```

---

## Lưu ý

- **Thêm ngân hàng**: chỉ cần đặt file template — không cần sửa code
- **Chống hallucination**: LLM chỉ trích xuất từ văn bản hợp đồng, không tự bịa
- **Rule engine**: UCP600 / Incoterms kiểm tra bằng Python thuần — deterministic, không tốn token
- **Wingdings checkbox**: Template VCB dùng U+F06F/U+F0FE (Wingdings PUA), không phải Unicode chuẩn □/■
- **Bảo mật**: Không commit `.env` vào git

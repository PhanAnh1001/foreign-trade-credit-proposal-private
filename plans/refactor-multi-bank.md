# Kế hoạch Refactor: Multi-Bank Template Support

**Pain point**: Code hiện tại hardcode Vietcombank — template path, output path, default issuing bank đều cứng. Mục tiêu: nhận `bank` như một tham số, template và output tổ chức theo `{bank}/{company}`.

**Nguyên tắc**: Dùng constant, không bịa, có ETE test + evidence. Song song tối đa.

---

## Trạng thái hiện tại (baseline)

| Vị trí | Vấn đề |
|---|---|
| `src/config.py:9` | `LC_TEMPLATE_PATH` hardcode 1 file duy nhất |
| `src/config.py:get_output_dir` | Output path không phân tầng bank/company |
| `src/agents/node_fill.py:22` | `output_dir` lấy từ state, không có bank/company slug |
| `src/agents/node_fill.py:33` | `template_path = str(LC_TEMPLATE_PATH)` — dùng constant cứng |
| `src/agents/graph.py:run_lc_application` | Chưa nhận tham số `bank` |
| `src/models/state.py` | Thiếu field `bank`, `company_slug` |
| `src/models/lc_application.py:72-73` | Default `issuing_bank_name`/`issuing_bank_bic` = Vietcombank cứng |
| `src/tools/lc_rules_validator.py:186-188` | `apply_isbp821_defaults` inject Vietcombank vô điều kiện |
| `data/templates/docx/` | Flat — không phân theo bank |
| `data/outputs/` | Flat run_name — không phân bank/company |

---

## Thiết kế đích

### Cấu trúc thư mục

```
data/
├── templates/
│   └── docx/
│       ├── vietcombank/
│       │   └── Application-for-LC-issuance.docx   ← move từ docx/
│       ├── bidv/
│       │   └── Application-for-LC-issuance.docx
│       └── vietinbank/
│           └── Application-for-LC-issuance.docx
└── outputs/
    ├── vietcombank/
    │   ├── viet_nam_technology_jsc/
    │   │   └── LC-Application-contract.docx
    │   └── another_company/
    └── bidv/
        └── some_company/
```

### Constants (`src/config.py`) — thêm mới, không xóa cũ

```python
# Bank slugs — lowercase, no spaces, canonical names
BANK_VCB       = "vietcombank"
BANK_BIDV      = "bidv"
BANK_VIETINBANK = "vietinbank"
BANK_DEFAULT   = BANK_VCB

def get_bank_template_path(bank: str) -> Path:
    """Return Path to LC template for given bank slug."""
    return TEMPLATES_DIR / bank / "Application-for-LC-issuance.docx"

def get_bank_output_dir(bank: str, company_slug: str) -> Path:
    """Return and create output dir: data/outputs/{bank}/{company_slug}/"""
    d = OUTPUTS_DIR / bank / company_slug
    d.mkdir(parents=True, exist_ok=True)
    return d

def slugify_company(name: str) -> str:
    """Convert company name to filesystem-safe slug (lowercase, underscores)."""
    import re
    slug = re.sub(r'[^a-zA-Z0-9\s]', '', name.lower())
    slug = re.sub(r'\s+', '_', slug.strip())
    return slug[:50] or "unknown"
```

### State (`src/models/state.py`) — thêm 2 fields

```python
bank: str         # bank slug, default = BANK_DEFAULT
company_slug: str # slugified applicant_name, set by fill_node
```

### Graph (`src/agents/graph.py`)

```python
def run_lc_application(
    contract_path: str,
    bank: str | None = None,
    output_dir: str | None = None,   # override (giữ backward compat)
) -> dict:
```

`bank` defaults to `BANK_DEFAULT`. `output_dir` override vẫn hoạt động (dùng cho ETE tests trỏ vào tmpdir).

### fill_node (`src/agents/node_fill.py`)

```python
from ..config import BANK_DEFAULT, get_bank_template_path, get_bank_output_dir, slugify_company

bank = state.get("bank") or BANK_DEFAULT
lc_data = state.get("lc_data") or {}
company_slug = slugify_company(lc_data.get("applicant_name") or "unknown")

# output_dir override (ETE/testing) takes priority
if state.get("output_dir"):
    output_path = str(Path(state["output_dir"]) / f"LC-Application-{contract_name}.docx")
else:
    out_dir = get_bank_output_dir(bank, company_slug)
    output_path = str(out_dir / f"LC-Application-{contract_name}.docx")

template_path = str(get_bank_template_path(bank))
```

### lc_rules_validator — bỏ inject Vietcombank mặc định

```python
# TRƯỚC (xóa):
if not data.get("issuing_bank_name"):
    data["issuing_bank_name"] = "Joint Stock Commercial Bank for Foreign Trade..."
    data["issuing_bank_bic"] = "BFTVVNVX"

# SAU: không inject — bank được truyền từ bên ngoài hoặc extract từ contract
```

### lc_application model — xóa hardcoded defaults

```python
# TRƯỚC:
issuing_bank_name: str = "Joint Stock Commercial Bank..."
issuing_bank_bic: str = "BFTVVNVX"

# SAU:
issuing_bank_name: Optional[str] = None
issuing_bank_bic: Optional[str] = None
```

---

## Checklist chi tiết (thứ tự thực hiện)

### Phase 1 — Constants & Config (không phá gì cũ)

- [ ] **1.1** `src/config.py`: thêm `BANK_VCB`, `BANK_BIDV`, `BANK_VIETINBANK`, `BANK_DEFAULT`
- [ ] **1.2** `src/config.py`: thêm `get_bank_template_path(bank)`, `get_bank_output_dir(bank, company_slug)`, `slugify_company(name)`
- [ ] **1.3** Giữ nguyên `LC_TEMPLATE_PATH` và `get_output_dir` cho backward compat

### Phase 2 — Di chuyển template file

- [ ] **2.1** Tạo thư mục `data/templates/docx/vietcombank/`
- [ ] **2.2** Copy (không xóa) `data/templates/docx/Application-for-LC-issuance.docx` → `data/templates/docx/vietcombank/Application-for-LC-issuance.docx`
- [ ] **2.3** Cập nhật `.gitignore` nếu cần (đảm bảo file mới được track)

### Phase 3 — State model

- [ ] **3.1** `src/models/state.py`: thêm field `bank: str = BANK_DEFAULT`
- [ ] **3.2** `src/models/state.py`: thêm field `company_slug: str = ""`

### Phase 4 — Graph entry point

- [ ] **4.1** `src/agents/graph.py:run_lc_application`: thêm param `bank: str | None = None`
- [ ] **4.2** Truyền `bank` vào `initial_state`

### Phase 5 — fill_node

- [ ] **5.1** `src/agents/node_fill.py`: import constants mới từ config
- [ ] **5.2** Đọc `bank` từ state (fallback `BANK_DEFAULT`)
- [ ] **5.3** Dùng `get_bank_template_path(bank)` thay `LC_TEMPLATE_PATH`
- [ ] **5.4** Nếu `state["output_dir"]` có → dùng (backward compat); nếu không → `get_bank_output_dir(bank, company_slug)`
- [ ] **5.5** Lưu `company_slug` vào state return dict

### Phase 6 — Xóa hardcoded Vietcombank mặc định

- [ ] **6.1** `src/models/lc_application.py`: `issuing_bank_name`, `issuing_bank_bic` → `Optional[str] = None`
- [ ] **6.2** `src/tools/lc_rules_validator.py:apply_isbp821_defaults`: xóa block inject Vietcombank (chỉ giữ nếu issuing_bank_name ĐÃ được set — thêm note thay vì default)
- [ ] **6.3** `src/utils/docx_filler.py:_fill_header`: xóa fallback `"Ha Noi Branch"` hardcode, dùng `data.get("vcb_branch", "")` hoặc generic bank branch field

### Phase 7 — Unit tests cập nhật

- [ ] **7.1** `tests/test_docx_filler.py`: cập nhật `TEMPLATE` path → `data/templates/docx/vietcombank/Application-for-LC-issuance.docx`
- [ ] **7.2** `tests/test_lc_rules_validator.py`: kiểm tra `test_vn03_vietcombank_authorized` vẫn pass (logic VN-03 dùng BIC lookup, không liên quan default inject)
- [ ] **7.3** `tests/test_models.py`: cập nhật nếu có assertion về output_dir path format
- [ ] **7.4** Thêm `TestMultiBankConfig` trong `tests/test_config.py` (file mới):
  - `test_get_bank_template_path_vcb`
  - `test_get_bank_template_path_bidv`
  - `test_get_bank_output_dir_creates_path`
  - `test_slugify_company_normal`
  - `test_slugify_company_special_chars`
  - `test_slugify_company_empty`

### Phase 8 — ETE test + evidence

- [ ] **8.1** `tests/test_ete.py`: thêm `test_ete_explicit_bank_vcb` — gọi `run_lc_application(contract, bank="vietcombank")`, assert template vcb được dùng, output path chứa "vietcombank"
- [ ] **8.2** Chạy pipeline thực, capture `run_id`, quality_score, output_path
- [ ] **8.3** Ghi `ete-evidence/ete-run-008.json` với field `bank`, `company_slug`, `output_path` mới

### Phase 9 — Cleanup & docs

- [ ] **9.1** Cập nhật `plans/plan.md` — move checklist này sang Đã hoàn thành khi xong
- [ ] **9.2** Cập nhật README.md: mục "Run pipeline" thêm ví dụ với tham số `bank`
- [ ] **9.3** Cập nhật Notes trong `plans/plan.md`: template path mới, output path format

---

## Rủi ro & cách xử lý

| Rủi ro | Xử lý |
|---|---|
| Template cũ vẫn được test_docx_filler.py dùng | Cập nhật path trong test (Phase 7.1) trước khi xóa file cũ |
| VN-03 rule check Vietcombank BIC dùng bank data từ contract, không từ default | Giữ nguyên logic VN-03 (không liên quan) |
| Backward compat `output_dir` override | `state["output_dir"]` vẫn ưu tiên — ETE tests dùng tmpdir như cũ |
| `lc_application.py` default None → Pydantic validate fail | Kiểm tra tất cả test có `issuing_bank_name` trong test data |

---

## Thứ tự thực hiện song song

```
Phase 1 (config) ──────┬─→ Phase 3 (state) ──┬─→ Phase 4 (graph)
                       │                      │
Phase 2 (move file) ───┘   Phase 6 (cleanup) ─┴─→ Phase 5 (fill_node)
                                                         │
Phase 7 (unit tests) ────────────────────────────────────┤
Phase 8 (ETE) ───────────────────────────────────────────┘
```

Phase 1+2 song song. Phase 3+6 song song sau Phase 1. Phase 4+5 sau Phase 3. Phase 7+8 sau Phase 5.

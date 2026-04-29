# DOCX Template Renderer — Design & Variable Mapping

Tài liệu này mô tả thiết kế và mapping đầy đủ cho `src/utils/docx_template.py`:
module render file output `credit-proposal.docx` trực tiếp từ template gốc
`data/templates/docx/giay-de-nghi-vay-von.docx` thay vì tạo DOCX mới từ Markdown.

---

## 0. Root Cause Analysis — Tại sao output khác template

### So sánh cấu trúc

| Chỉ số | Template gốc | Output cũ (markdown_to_docx) | Output mới (render_from_template) |
|---|---|---|---|
| Paragraphs | 334 | 78 | ~334 (giữ nguyên) |
| Tables | 35 | 14 | 35 (giữ nguyên) |
| Sections | 19 | 1 | 19 (giữ nguyên) |
| Images (VPBank logo) | 13 | 0 | 13 (giữ nguyên) |
| Font/style | Arial, green borders #339966 | Default Calibri, không border | Giữ nguyên template |

### Nguyên nhân gốc — `markdown_to_docx()` (approach cũ)

Approach cũ (`src/utils/docx_converter.py`) **tạo DOCX mới hoàn toàn** từ Markdown text:

```
Markdown string → Document() (blank) → add_paragraph/add_table → save
```

Hệ quả:
- **Mất 13 ảnh**: Logo VPBank (rId6) được nhúng trong header XML của từng section — khi tạo DOCX mới, không có section headers → không có logo.
- **Mất 19 sections**: Template có 19 section breaks với margin riêng (section[10] là LANDSCAPE orientation cho bảng rộng) — DOCX mới chỉ có 1 section mặc định.
- **Mất màu border #339966**: Tables 1,2,3,7,10,14,15,16,17,19 có border màu xanh lá VPBank — DOCX mới tạo bảng không có border color.
- **Mất 35 tables**: PHỤ LỤC 1–6 (Table[13–34]) không có — DOCX mới chỉ có 14 bảng do Markdown parser tạo.
- **Font sai**: Template dùng Arial; DOCX mới dùng Calibri mặc định của python-docx.
- **Thiếu PHỤ LỤC 1–6**: Các phụ lục nội bộ của form (danh sách thành viên, tín dụng hiện hữu, KQKD lịch sử...) hoàn toàn bị thiếu.

### Giải pháp — Template Injection (`render_from_template`)

Approach mới **mở template gốc như base**, chỉ modify nội dung cell mà giữ nguyên XML:

```
Document(template_path) → fill cells by coordinate → add_row() → save(output_path)
```

Kết quả:
- **Tự động giữ nguyên**: images, sections, margins, orientation, borders, fonts, styles, PHỤ LỤC 1–6 tables.
- **Chỉ inject data** vào các cells được xác định trong mapping bên dưới.
- **Phụ lục A/B** (LLM analysis output của subgraph2/3) được **append sau PHỤ LỤC 6** — đây là nội dung mở rộng không có trong template gốc.

---

## 1. Approach

```
Template gốc (DOCX)       CompanyInfo + FinancialData + section2/3
        │                              │
        └──────────┬────────────────────┘
                   ▼
        DocxTemplateRenderer
        (open template → fill cells → inject rows → append appendices)
                   │
                   ▼
        credit-proposal.docx
        (giống hệt template về font/layout/style + dữ liệu thật)
```

**Nguyên tắc:**
- **Không** tạo DOCX mới — mở template gốc và modify in-place
- Cells đơn: ghi đè bằng `_set_cell(cell, value)` — preserve paragraph style
- Cells có label+value chung: dùng `_append_cell()` để append sau text hiện có
- Multi-row sections: dùng `table.add_row()` (HĐQT/BGĐ/BKS) hoặc fill rows có sẵn (cổ đông, PHỤ LỤC 1)
- Phụ lục A/B: append sau trang cuối template qua `_append_markdown()` (sau PHỤ LỤC 6)

---

## 2. Single-value Cell Mapping

Chi tiết đầy đủ xem `docs/requirements/human_mapping.md`. Tóm tắt implement:

### Table[1] — Section 1.1 Thông tin Khách hàng (Pháp nhân)
*(13 rows × 2 cols; col 0 = label, col 1 = value cell)*

| Variable | Table | Row | Col | Source |
|---|---|---|---|---|
| `customer_name` | 1 | 2 | 1 | `CompanyInfo.company_name` |
| `tax_code + ngày cấp + cơ quan cấp` | 1 | 3 | 1 | `CompanyInfo.tax_code + established_date + registration_authority` (set cell[1]) |
| `registered_address` | 1 | 4 | 1 | `CompanyInfo.address` |
| `current_address` | 1 | 5 | 1 | `CompanyInfo.address` |
| `phone` | 1 | 6 | 1 | `CompanyInfo.phone` |
| `main_business` | 1 | 7 | 1 | `CompanyInfo.main_business` |
| `charter_capital` | 1 | 9 | 1 | `CompanyInfo.charter_capital` |
| `vot_thuc_gop` | 1 | 10 | 1 | `FinancialStatement.equity` (năm mới nhất) — **= Vốn CSH** |

### Table[2] — Section 1.2 Người đại diện

| Variable | Row | Col | Source |
|---|---|---|---|
| `legal_representative` | 14 | 1 | `CompanyInfo.legal_representative` |

*HĐQT/BGĐ/BKS không điền vào form — chỉ fill trong analyst memo.*

### Table[8] — Thông tin hoạt động kinh doanh

| Variable | Row | Col | Source |
|---|---|---|---|
| `main_business_line_1` | 1 | 0 | `CompanyInfo.main_business` |

### Table[29] — PHỤ LỤC 6: KQKD lịch sử (2 năm)
*(8 rows × 5 cols; col 2 = Năm N-1, col 3 = Năm N)*

| Row | Chỉ tiêu | Source |
|---|---|---|
| 1 | Doanh thu | `net_revenue` |
| 2 | Tổng chi phí | `cost_of_goods_sold + selling_expenses + admin_expenses` |
| 3 | Lợi nhuận sau thuế | `net_profit` |
| 4 | Tổng nhu cầu vốn lưu động | `current_assets - current_liabilities` |
| 5 | Nguồn vốn tự có | `equity` (= Vốn CSH) |
| 6 | Nhu cầu vốn vay TCTD khác | `total_liabilities` (proxy — xem human_mapping note #2) |

### Table[32] — PHỤ LỤC 6: Chi tiết KQKD 12 tháng (năm mới nhất)
*(9 rows × 4 cols; col 2 = value)*

| Row | Label | Source |
|---|---|---|
| 1 | Doanh thu bán hàng | `net_revenue` |
| 2 | Giá vốn hàng bán | `cost_of_goods_sold` |
| 3 | Lợi nhuận gộp | `gross_profit` |
| 7 | Chi phí khác | `admin_expenses + selling_expenses` |
| 8 | Lợi nhuận sau thuế | `net_profit` |

---

## 3. Multi-row Injection

### 1.3 Cổ đông (Table[3], rows 10–12)

Template có 3 placeholder rows trống. Cols (dedup merged):
`[0]=STT | [1+2]=Họ tên | [3+4]=Mối QH | [5]=Tỷ lệ% | [6+7]=KN | [8]=Dư nợ`

| Col | Nội dung | Source |
|---|---|---|
| 0 | STT | index 1,2,3 |
| 1 | Họ và tên | `Shareholder.name` |
| 5 | Tỷ lệ góp vốn | `Shareholder.percentage` |

### PHỤ LỤC 1 — Thành viên góp vốn chính (Table[14] + Table[15])

PHỤ LỤC 1 là **form dạng label|value** (không phải data table). Fill cổ đông lớn nhất
(`shareholders[0]`) vào section cá nhân:

| Table | Row | Col | Nội dung | Source |
|---|---|---|---|---|
| 14 | 15 | 1 | Mối quan hệ với KH | `"Cổ đông chính"` (fixed) |
| 14 | 16 | 1 | Họ và tên | `shareholders[0].name` |
| 15 | 5 | 1 | Tỷ lệ góp vốn | `shareholders[0].percentage` |

*Section Doanh nghiệp (Table[14] r0–r13): bỏ qua — MST shareholders là cá nhân.*

### HĐQT / BGĐ / BKS (Table[2], append rows)

Template không có section HĐQT riêng. Renderer thêm rows vào cuối Table[2]
(sau row 16 — representative section). Mỗi board được inject 1 header row + N member rows.

*Không inject gì — HĐQT/BGĐ/BKS không thuộc loan application form. Section 1.2 chỉ có legal representative (Table[2] r14).*

*Table[2] có 4 cols → injected rows: col0=name, col1=role, col2=age.*

---

## 4. Appendices (Phụ lục A & B) — MD only, không thêm vào DOCX

Phụ lục A (thông tin ngành) và Phụ lục B (phân tích tài chính) là output LLM của subgraph2/3.
Chúng **chỉ được ghi vào `credit-proposal.md`** — không được append vào DOCX.

**Lý do**: Output DOCX phải giống hệt cấu trúc template gốc (35 tables, 19 sections).
Append thêm nội dung sau PHỤ LỤC 6 sẽ làm sai lệch cấu trúc form chính thức.

| Output file | Nội dung |
|---|---|
| `credit-proposal.md` | Header + 3 sections + Phụ lục A + Phụ lục B (đầy đủ) |
| `credit-proposal.docx` | Template gốc với data filled vào các cells — không thêm gì |

---

## 5. Những gì Template Injection bảo tồn tự động

Khi mở template gốc (`Document(template_path)`), tất cả XML nội bộ được giữ nguyên:

| Thành phần | Chi tiết | Số lượng |
|---|---|---|
| VPBank logo | Nhúng trong header XML của mỗi section (relationship rId6) | 13 images |
| Section breaks | Margin riêng per section; section[10] LANDSCAPE orientation | 19 sections |
| Border màu xanh | `#339966` trên Tables 1,2,3,7,10,14,15,16,17,19 | Green borders |
| PHỤ LỤC 1–6 tables | Table[13–34] có sẵn trong template, chỉ fill data | 22 tables |
| Font Arial | Defined trong paragraph/character styles của template | All text |

Không cần code gì để bảo tồn các thành phần này — chúng tự động xuất hiện vì ta mở template gốc.

---

## 6. Out-of-scope (no data available)

| Section | Lý do |
|---|---|
| Table[4-6] — Thông tin đề nghị cấp tín dụng | Số tiền/kỳ hạn vay do khách hàng điền |
| Table[7] — Tài sản đảm bảo | Không có data TSBĐ từ input |
| Table[9] — Đối tác đầu vào/ra | Không extract từ BCTC/MD |
| Table[10] — Dư nợ tại TCTD khác | Tên TCTD N/A; Số dư tín dụng cần mã 311+341 chưa extract |
| Table[15] r0-r4, r6-r12 — PHỤ LỤC 1 chi tiết | Ngày sinh, CMND, địa chỉ, bảo lãnh — không extract |
| Table[16-17] — PHỤ LỤC 1 Nhóm KH | Không có data |
| PHỤ LỤC 2-5 (Table[18-27]) — Tín dụng hiện hữu, quyền đòi nợ, XNK | Không có data |
| Table[30-31, 33-34] — Phương án vay, KQKD hộ kinh doanh | Do khách hàng điền / không áp dụng |

---

## 7. File layout

```
src/utils/docx_template.py      # Renderer module (main)
src/agents/assembler.py         # Updated: swap markdown_to_docx → render_from_template
data/templates/docx/
    giay-de-nghi-vay-von.docx  # Template gốc (không sửa)
docs/requirements/
    overview.md                 # Đề bài gốc
    docx_template_design.md     # File này
```

---

## 8. Key functions

```python
# Public API
render_from_template(output_path, company_info, financial_data,
                     template_path=_TEMPLATE_PATH) -> str

# Internal fillers
_fill_company_info(doc, info)           # Table[1] r2-r9 + Table[2] r14
_fill_vot_thuc_gop(doc, financial_data) # Table[1] r10 — equity từ năm mới nhất
_fill_shareholders(doc, info)           # Table[3] r10-r12
_fill_phu_luc_1(doc, info)             # Table[14] r15-r16 + Table[15] r5 (cá nhân section)
_fill_board_and_management(doc, info)   # Table[2] add_row() injection
_fill_business_ops(doc, info)           # Table[8]
_fill_financial_history(doc, data)      # Table[29] rows 1-6
_fill_income_statement(doc, data)       # Table[32]

# Low-level helpers
_set_cell(cell, text)     # Clear + set (preserve style)
_append_cell(cell, text)  # Append after existing text
_fmt(value, unit)         # Format financial number → "1,234.5 tỷ đồng"
_add_page_break(doc)
_append_markdown(doc, md_text)   # Markdown → DOCX elements
_md_table_to_docx(doc, lines)    # Markdown table → DOCX Table Grid
_add_heading_safe(doc, text, level)  # Workaround BabelFish lowercase style bug
```

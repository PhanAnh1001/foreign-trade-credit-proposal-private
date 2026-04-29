# Field Mapping — Giấy Đề Nghị Cấp Tín Dụng

Mapping toàn bộ các ô cần điền trong `data/templates/docx/giay-de-nghi-vay-von.docx`
sang data source từ `CompanyInfo`, `FinancialStatement`, hoặc lý do N/A.

**Legends:**
- ✅ Đã implemented và đúng
- 🆕 Cần implement / đang fix
- ⬜ Không có data — để trống
- 📝 Khách hàng tự điền (ngoài scope AI)

---

## MỤC 1.1 — Thông tin Khách hàng Pháp nhân (Table[1], 13 rows × 2 cols)

| Row | Col | Label trong form | Data source | Tính toán | Status |
|-----|-----|------------------|-------------|-----------|--------|
| 2 | 1 | Tên Khách hàng | `CompanyInfo.company_name` | — | ✅ |
| 3 | 0 | Giấy CNĐKKD/CNĐKDN (MST) | `CompanyInfo.tax_code` | append sau label | ✅ |
| 3 | 1 | Ngày cấp / Cơ quan cấp | — | không extract | ⬜ |
| 4 | 1 | Địa chỉ trụ sở (trên CNĐKKD) | `CompanyInfo.address` | — | ✅ |
| 5 | 1 | Địa chỉ giao dịch hiện tại | `CompanyInfo.address` | dùng chung trụ sở | ✅ |
| 6 | 1 | Điện thoại | `CompanyInfo.phone` | — | ✅ |
| 7 | 1 | Ngành nghề kinh doanh chính | `CompanyInfo.main_business` | — | ✅ |
| 8 | 1 | Tình trạng sở hữu cơ sở KD | — | không extract | ⬜ |
| 9 | 1 | Vốn điều lệ | `CompanyInfo.charter_capital` | — | ✅ |
| 10 | 1 | **Vốn thực góp đến ngày…** | `FinancialStatement.equity` (năm mới nhất) | **= Vốn chủ sở hữu** trên CĐKT *(human_mapping note #1)* | 🆕 |

> **Note #1**: "Vốn thực góp" trong form tín dụng tương đương "Vốn chủ sở hữu" (mã 400 trên CĐKT).
> Dùng năm tài chính mới nhất có trong `FinancialData`.

---

## MỤC 1.2 — Người đại diện pháp luật (Table[2])

| Row | Col | Label | Data source | Status |
|-----|-----|-------|-------------|--------|
| 14 | 1 | Họ và tên | `CompanyInfo.legal_representative` | ✅ |
| 15 | 1 | Ngày sinh | — | ⬜ |
| 16 | 1 | Số CMND/Hộ chiếu/CCCD | — | ⬜ |

**HĐQT / BGĐ / BKS**: inject thêm rows vào cuối Table[2] bằng `add_row()`.
Mỗi nhóm: 1 header row + N member rows (col0=Tên, col1=Chức vụ, col2=Tuổi). ✅

---

## MỤC 1.3 — Cơ cấu vốn góp (Table[3], rows 10–12)

Template có 3 rows trống (r10, r11, r12). Cols sau dedup merged:
`[0]=STT | [1+2]=Họ tên | [3+4]=Mối QH | [5]=Tỷ lệ% | [6+7]=Kinh nghiệm | [8]=Dư nợ VPB`

| Col | Label | Data source | Status |
|-----|-------|-------------|--------|
| 0 | STT | index 1,2,3 | ✅ |
| 1 | Họ và tên | `Shareholder.name` | ✅ |
| 3 | Mối quan hệ | — | ⬜ |
| 5 | Tỷ lệ góp vốn (%) | `Shareholder.percentage` | ✅ |
| 6 | Kinh nghiệm, năng lực | — | ⬜ |
| 8 | Dư nợ/lịch sử tín dụng VPB | — | ⬜ |

---

## MỤC 2 — Thông tin đề nghị cấp tín dụng (Table[4–6])

📝 **Khách hàng tự điền**: Vay món / Hạn mức / Cho vay tái tài trợ / Thấu chi / Thẻ tín dụng / Bảo lãnh / L/C.
Bao gồm: số tiền, mục đích, thời hạn, phương thức giải ngân, phương thức trả nợ.
**Tổng số tiền cấp tín dụng** (Table[6] r2 c1): 📝

---

## MỤC 3 — Tài sản đảm bảo (Table[7], 4 rows × 4 cols)

| Col | Label | Status |
|-----|-------|--------|
| 0 | Tên tài sản bảo đảm | ⬜ không có data TSBĐ từ input |
| 1 | Tên chủ sở hữu | ⬜ |
| 2 | Mối quan hệ chủ sở hữu—KH | ⬜ |
| 3 | Tài sản đang bảo đảm nghĩa vụ khác? | ⬜ |

---

## MỤC 4 — Thông tin hoạt động kinh doanh (Table[8–9])

| Table | Row | Col | Label | Data source | Status |
|-------|-----|-----|-------|-------------|--------|
| 8 | 1 | 0 | Lĩnh vực KD chính / sản phẩm chính | `CompanyInfo.main_business` | ✅ |
| 8 | 1 | 1 | Tỷ trọng trên tổng doanh thu | — | ⬜ |
| 8 | 2 | 0–1 | Dòng thứ 2 (nếu nhiều ngành) | — | ⬜ |
| 9 | 1–3 | 0 | Đối tác đầu vào (3 đối tác) | — | ⬜ |
| 9 | 1–3 | 1 | Đối tác đầu ra (3 đối tác) | — | ⬜ |

---

## MỤC 6 — Dư nợ tại TCTD khác (Table[10], 3 rows × 6 cols)

| Col | Label | Data source | Tính toán | Status |
|-----|-------|-------------|-----------|--------|
| 0 | Tên TCTD | — | không có thông tin ngân hàng cụ thể | ⬜ |
| 1 | Hình thức cấp tín dụng | — | ⬜ | ⬜ |
| 2 | Mục đích | — | ⬜ | ⬜ |
| 3 | Giá trị hạn mức | — | ⬜ | ⬜ |
| 4 | **Số dư tín dụng** | `FinancialStatement.total_liabilities` | **= Vay và nợ thuê tài chính ngắn hạn + dài hạn** *(human_mapping note #2 — xem lưu ý bên dưới)* | ⬜ TODO |
| 5 | Tên TSBĐ | — | ⬜ | ⬜ |

> **Note #2**: "Số dư tín dụng" = "Vay và nợ thuê tài chính ngắn hạn" (mã 311) + "Vay và nợ thuê tài chính dài hạn" (mã 341) trên CĐKT.
> Hiện tại `FinancialStatement` chỉ có `total_liabilities` (mã 300 — tổng nợ phải trả, rộng hơn).
> Để fill chính xác: thêm `short_term_borrowings` (mã 311) và `long_term_borrowings` (mã 341) vào `FinancialStatement` và cập nhật LLM extraction prompt.
> Workaround tạm: điền `total_liabilities` vào 1 row với ghi chú "Tổng nợ phải trả (proxy)".

---

## PHỤ LỤC 1 — Thành viên góp vốn chính (Table[14–17])

PHỤ LỤC 1 là form dạng label|value (không phải data table). Có 2 section:
- **Section Doanh nghiệp** (Table[14] r0–r13): thành viên góp vốn là pháp nhân
- **Section Cá nhân** (Table[14] r14–r16 + Table[15]): thành viên góp vốn là cá nhân

MST: cổ đông là cá nhân → chỉ fill Section Cá nhân. Chỉ fill cổ đông lớn nhất (`shareholders[0]`).

### Section Cá nhân — Table[14] rows 14–16

| Table | Row | Col | Label | Data source | Status |
|-------|-----|-----|-------|-------------|--------|
| 14 | 14 | — | Header: "Thành viên góp vốn chính (nếu là cá nhân)" | — | header, skip |
| 14 | 15 | 1 | Mối quan hệ với khách hàng | `"Cổ đông chính"` (fixed) | 🆕 |
| 14 | 16 | 1 | Họ và tên | `CompanyInfo.shareholders[0].name` | 🆕 |

### Section Cá nhân — Table[15]

| Table | Row | Col | Label | Data source | Status |
|-------|-----|-----|-------|-------------|--------|
| 15 | 0 | 1 | Ngày sinh | — | ⬜ |
| 15 | 1 | 1 | Số CMND/Hộ chiếu/CCCD | — | ⬜ |
| 15 | 2 | 1 | Hộ khẩu thường trú | — | ⬜ |
| 15 | 3 | 1 | Địa chỉ hiện tại | — | ⬜ |
| 15 | 4 | 1 | Điện thoại di động | — | ⬜ |
| 15 | 5 | 1 | **Tỷ lệ góp vốn** | `CompanyInfo.shareholders[0].percentage` | 🆕 |

### Section Doanh nghiệp — Table[14] rows 0–13

⬜ Bỏ qua — cổ đông MST là cá nhân. Nếu cần fill DN: `r1 col1`=mối QH, `r2 col1`=tên DN, `r13 col2`=tỷ lệ, `r8 col2`=tên người góp vốn cao nhất.

### Các section còn lại

| Table | Section | Status |
|-------|---------|--------|
| 15 | r6–r12: Thành viên góp vốn ký bảo lãnh cá nhân | ⬜ |
| 16–17 | Nhóm KH được coi như một KH (DN / cá nhân) | ⬜ |

---

## PHỤ LỤC 2–5 (Table[18–27])

| PHỤ LỤC | Nội dung | Status |
|---------|---------|--------|
| 2 (Table[19]) | Tín dụng hiện hữu (hợp đồng, TSBĐ) | ⬜ |
| 3 (Table[20]) | header only | ⬜ |
| 4 (Table[22–25]) | Quyền đòi nợ (hóa đơn, đối tác mua) | ⬜ |
| 5 (Table[27]) | Hoạt động XNK | ⬜ |

---

## PHỤ LỤC 6 — Kết quả hoạt động kinh doanh (Table[28–34])

### Table[29] — KQKD lịch sử (8 rows × 5 cols)

Header cols: `[0]=TT | [1]=Chỉ tiêu | [2]=Năm N-1 | [3]=Năm kế hoạch | [4]=Ghi chú`
Renderer: đổi col 2 → năm N-1 thực tế, col 3 → năm N thực tế (năm mới nhất).

| Row | Label | Col 2 (Năm N-1) | Col 3 (Năm N) | Tính toán | Status |
|-----|-------|-----------------|---------------|-----------|--------|
| 0 | header | năm N-1 (string) | năm N (string) | — | ✅ |
| 1 | Doanh thu | `net_revenue` | `net_revenue` | — | ✅ |
| 2 | Tổng chi phí | COGS+selling+admin | same | sum các khoản chi phí | ✅ |
| 3 | Lợi nhuận sau thuế | `net_profit` | `net_profit` | — | ✅ |
| 4 | **Tổng nhu cầu vốn lưu động** | `current_assets - current_liabilities` | same | working capital | 🆕 |
| 5 | **Nguồn vốn tự có** | `equity` | `equity` | = Vốn CSH (note #1) | 🆕 |
| 6 | **Nhu cầu vốn vay TCTD khác** | `total_liabilities` | same | proxy cho note #2 | 🆕 |
| 7 | Nhu cầu vốn vay tại VPBank | — | — | 📝 khách hàng điền | 📝 |

> Ghi chú row 6: giá trị chính xác là Vay và nợ thuê tài chính ngắn + dài hạn (mã 311+341).
> Hiện dùng `total_liabilities` (mã 300+phần dài hạn) làm proxy — lớn hơn thực tế.

### Table[30–31] — Phương án kinh doanh năm kế hoạch

📝 Khách hàng tự điền: doanh thu/chi phí/lợi nhuận/nhu cầu vốn kế hoạch.

### Table[32] — Chi tiết KQKD 12 tháng — Doanh nghiệp (9 rows × 4 cols)

`[0]=STT | [1]=Chi tiết | [2]=Giá trị 12 tháng | [3]=Ghi chú`
Dùng năm mới nhất trong `FinancialData`.

| Row | Label | Data source | Status |
|-----|-------|-------------|--------|
| 0 | header (năm) | `f"Năm {year}"` | ✅ |
| 1 | Doanh thu bán hàng và CCDV | `net_revenue` | ✅ |
| 2 | Giá vốn hàng bán | `cost_of_goods_sold` | ✅ |
| 3 | Lợi nhuận gộp (1-2) | `gross_profit` | ✅ |
| 4 | Thu nhập khác | — | ⬜ |
| 5 | Chi phí tài chính | — | ⬜ |
| 6 | Chi phí thuế | — | ⬜ |
| 7 | Chi phí khác | `admin_expenses + selling_expenses` | ✅ |
| 8 | Lợi nhuận sau thuế (3+4-5-6-7) | `net_profit` | ✅ |

### Table[33–34] — Chi tiết KQKD 12 tháng — Hộ kinh doanh

⬜ Không áp dụng — MST là doanh nghiệp pháp nhân, không phải hộ kinh doanh.

---

## Tổng kết

| Trạng thái | Số fields | Ghi chú |
|------------|-----------|---------|
| ✅ Đã implement đúng | 19 | company info, shareholders list, board, financials |
| 🆕 Cần implement | 6 | vốn thực góp, PHỤ LỤC 1 fix, T29 r4-r6 |
| ⬜ Không có data | ~35 | CMND, TSBĐ, đối tác, ngày sinh… |
| 📝 Khách hàng điền | ~20 | số tiền vay, kỳ hạn, phương án kế hoạch… |

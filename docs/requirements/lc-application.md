# PRD — LC Application Agent

> AI draft từ `docs/intent/lc-application.md` và `docs/design/document.md`.

## Bài toán

Nhân viên xuất nhập khẩu phải tự điền thủ công đơn xin mở L/C dựa trên hợp đồng ngoại thương — dễ sai, mất thời gian, và phải tra cứu các quy tắc UCP 600/ISBP 821/Incoterms. Agent tự động trích xuất ~30 trường từ hợp đồng, áp dụng các quy tắc thương mại quốc tế, và điền vào mẫu DOCX của ngân hàng — không cần sửa code khi thêm ngân hàng mới.

## Input

- 1 file hợp đồng ngoại thương: TXT, PDF, hoặc DOCX
  - Ví dụ: `data/sample/contract.txt` (VN-CN-2024-001, USD 450K, CIF)
- Template DOCX của ngân hàng: `data/templates/docx/{bank}/Application-for-LC-issuance.docx`
  - Included: `data/templates/docx/vietcombank/Application-for-LC-issuance.docx`

## Output

- File DOCX đơn mở L/C đã điền tại: `data/outputs/{bank}/{company_slug}/LC-Application-{contract}.docx`
  - Ví dụ: `data/outputs/vietcombank/viet_nam_technology_importexport_jsc/LC-Application-contract.docx`
- Checkboxes Wingdings được tick đúng (■ U+25A0)
- `state["quality_score"]` ≥ 7.0/10 (LLM-as-Judge)

## Acceptance criteria

- [ ] Output DOCX tồn tại và có kích thước > 1 KB
- [ ] Tên applicant từ hợp đồng xuất hiện đúng trong DOCX
- [ ] Currency và amount điền đúng theo hợp đồng
- [ ] Với CIF/CIP: insurance certificate xuất hiện trong danh sách chứng từ
- [ ] Quality score ≥ 7.0/10 trên hợp đồng mẫu `data/sample/contract.txt`
- [ ] 52 unit tests PASS (`pytest tests/ --ignore=tests/test_ete.py`)

## Out of scope (v1)

- LC amendments (chỉ xử lý issuance lần đầu)
- UI/UX — chỉ có CLI và Python API
- Multi-bank DOCX filler tổng quát: ngân hàng mới cần kiểm tra cấu trúc bảng riêng
- Incoterms 2000/2010 rule differences ngoài insurance (chỉ label khác nhau)
- Hỗ trợ tiếng Việt trong contract (extraction prompt dùng tiếng Anh)

## Câu hỏi mở cho người

- [?] Ngân hàng tiếp theo sau Vietcombank cần hỗ trợ là ngân hàng nào? (ảnh hưởng đến test fixtures)
- [?] Có cần hỗ trợ LC amendment trong v2 không?

---

## Approved by anh @ 2026-05-01

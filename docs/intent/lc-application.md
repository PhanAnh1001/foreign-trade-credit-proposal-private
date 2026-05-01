# Intent — LC Application Agent

**Mục tiêu**: Tự động tạo đơn xin mở L/C (Letter of Credit) từ hợp đồng ngoại thương, tuân thủ UCP 600, ISBP 821 và Incoterms, dùng được với mọi ngân hàng và mọi công ty.

**Input có sẵn**: 1 file hợp đồng ngoại thương (TXT / PDF / DOCX) + template DOCX của ngân hàng tại `data/templates/docx/{bank}/Application-for-LC-issuance.docx`.

**Output mong đợi**: 1 file DOCX đơn mở L/C điền sẵn tại `data/outputs/{bank}/{company_slug}/LC-Application-{contract}.docx`.

**Ràng buộc**: Groq free tier (llama-3.3-70b extraction + openai/gpt-oss-20b judge); thêm ngân hàng mới không cần sửa code.

GENAI/AI AGENT IMPLEMENTATION
1. Mục tiêu
Đánh giá khả năng thiết kế và phát triển ứng dụng GenAI/AI Agent (tập trung chính vào kỹ năng coding và implementation)
2. Bài toán: Viết ứng dụng GenAI/AI Agent tạo tờ trình tín dụng
- Input: File báo cáo tài chính của công ty
- Output: Tờ trình tín dụng bao gồm 3 outputs sau:
+ Thông tin chung về công ty: địa chỉ, người đại diện, cổ đông…
+ Thông tin về lĩnh vực kinh doanh: thông tin về lĩnh vực kinh doanh của công ty; đánh giá sự phát triển của lĩnh vực này và các rủi ro hiện tại
+ Phân tích tình hình kinh doanh: đọc báo cáo tài chính và phân tích tình hình kinh doanh (so sánh giữa các năm, đánh giá điểm tốt/chưa tốt…)
3. Yêu cầu
- Design: 1-2 trang tài liệu mô tả thiết kế GenAI/AIAgent application (AI Agent với memory, planning, tool, action; liệt kê các tool cần dùng…)
- Implementation
+ Có thể implement với các framework quen dùng nhưng ưu tiên sử dụng langgraph để phù hợp với techstack của team
+ Chỉ cần implement BE, ko cần implement UI/UX
- Deliverables:
+ Video demo show kết quả của ứng dụng
+ Code của ứng dụng
4. Tham khảo
+ Ví dụ về mẫu tờ trình: data/templates/docx/giay-de-nghi-vay-von.docx
+ Thông tin công ty: data/uploads/mst/general-information/md/mst-information.md
+ Báo cáo tài chính: data/uploads/mst/financial-statements/pdf
* Lưu ý:
+ Có thể sử dụng các công cụ AI hỗ trợ coding nhưng phải do bản thân trực tiếp thực hiện (tỷ lệ  code do AI hỗ trợ không được quá 20%; không được nhờ người khác hoặc member trong team)
+ Do yêu cầu về thời gian nên ko cần implement các mục trong 3 outputs mà có thể implement điểm trọng tâm của từng output. Ví dụ: output 3 (phân tích tình hình kinh doanh) có thể chọn một số trang trong báo cáo tài chính rồi viết tool trích xuất, phân tích đánh giá chứ ko cần input toàn bộ file báo cáo tài chính….

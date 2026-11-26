# Danh sách tính năng đã chốt (đóng băng từ tuần 7, release v0.9)

Từ tuần 7 không thêm tính năng mới; chỉ sửa lỗi, bảo mật, UX theo góp ý, tài liệu và đo đạc.

| # | Tính năng | Trạng thái | Nơi kiểm chứng |
|---|---|---|---|
| 1 | Chọn ảnh khách, trả top-10 mẫu giống nhất (CLIP ViT-B/32, cosine) | Hoàn thành | `POST /search`, `api/tests/` |
| 2 | Danh mục (tên, giá, kích thước) và nhật ký tìm qua Google Sheet, có hàng đợi khi mất mạng | Hoàn thành | `integration/`, `api/sheets.py` |
| 3 | Phản hồi Đúng / Sai / Shop không có mẫu; ca sai thành ca eval | Hoàn thành | `POST /feedback`, `eval/` |
| 4 | Bộ đánh giá Recall@5, MRR, chẩn đoán lỗi | Hoàn thành | `eval/run_eval.py`, `eval/diagnose.py` |

Phi chức năng đã thêm ở tuần 7 (không phải tính năng mới): kiểm tra ảnh tải lên, giới hạn tần suất, khoá API, làm sạch tên file, Docker không chạy root, CI chạy test + build Docker.

Ngoài phạm vi (không làm): đăng nhập từng người dùng, HTTPS tự cấu hình (cần reverse proxy khi triển khai thật), tìm theo nhiều ảnh mỗi mẫu (dự kiến sau nếu còn thời gian).

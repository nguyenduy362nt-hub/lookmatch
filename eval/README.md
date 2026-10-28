# Đánh giá LookMatch

## Bộ dữ liệu
- Catalog: ảnh sản phẩm của shop pilot (mỗi sản phẩm ≥1 ảnh), mã sản phẩm là nhãn.
- Query: **≥50 ảnh khách gửi thật** (xin phép shop, ẩn thông tin cá nhân), mỗi ảnh gán 1 mã sản phẩm đúng do chủ shop xác nhận. Không đưa ảnh lên repo công khai; chỉ lưu `queries.csv` (tên file ẩn danh, nhãn).
- Tách bộ test từ đầu, không dùng để chỉnh tham số. Seed cố định = 42.

## Chỉ số
- Recall@1/5/10: tỉ lệ ảnh query mà sản phẩm đúng nằm trong top-K.
- mAP (phụ). Chỉ số chính: **Recall@5** (H1 ≥ 80%).
- Thời gian tìm (giây/lượt): bấm giờ từ lúc mở ảnh đến lúc chọn đúng sản phẩm, ≥30 lượt, ghi ngày + bằng chứng. Cách thủ công (trước) và dùng app (sau). H2 ≤ 20 s.

## So sánh (CH1)
CLIP vs DINOv2, mỗi mô hình chạy có/không cắt nền → 4 dòng kết quả.

## Định dạng queries.csv
`file,product_id,loai_anh(chup_that|man_hinh|mo),ngay`

# ADR-1: Chọn mô hình biểu diễn ảnh (CLIP hay DINOv2)
- Trạng thái: Đề xuất, chốt bằng số đo ở W6
- Bối cảnh: cần biến ảnh thành vector để so độ giống. Ảnh khách gửi khác ảnh shop (góc chụp, ánh sáng, nền, ảnh chụp màn hình).
- Lựa chọn: (a) CLIP ViT-B/32, (b) DINOv2 ViT-S/14.
- Quyết định: cài cả hai sau cùng một giao diện `embed(image)->vector`; chọn mô hình có Recall@5 cao hơn trên ≥50 ảnh khách thật đã gán nhãn (bộ test tách riêng từ đầu).
- Hệ quả: nếu chênh lệch <2 điểm % thì chọn mô hình nhẹ/nhanh hơn. Kết quả ghi vào eval/results.

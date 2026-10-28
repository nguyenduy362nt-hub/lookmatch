# ADR-2: Suy luận (inference) chỉ chạy trên server
- Bối cảnh: người làm chỉ quen Flutter; mô hình ML nặng, điện thoại nhân viên đa dạng.
- Lựa chọn: (a) chạy mô hình trên máy (TFLite/ONNX), (b) gửi ảnh lên FastAPI và chạy ở server.
- Quyết định: (b). App chỉ chọn ảnh, gọi API, hiển thị kết quả.
- Đánh đổi: cần mạng và server chạy; đổi lại một nơi cập nhật mô hình, app đơn giản, dễ đo thời gian.
- Rủi ro: ảnh khách gửi lên server → chỉ dùng ảnh khi có đồng ý của shop, không đưa lên repo công khai.

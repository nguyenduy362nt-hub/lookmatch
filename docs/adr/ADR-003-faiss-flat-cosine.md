# ADR-3: Chỉ mục FAISS Flat, cosine trên vector đã chuẩn hoá
- Bối cảnh: danh mục dự kiến ~300 sản phẩm (có thể vài nghìn ảnh).
- Lựa chọn: Flat (so sánh toàn bộ), IVF, HNSW.
- Quyết định: `IndexFlatIP` trên vector chuẩn hoá L2 (tích vô hướng = cosine).
- Lý do: với <10 nghìn vector, Flat tìm trong mili-giây, kết quả chính xác 100%, không cần huấn luyện chỉ mục. IVF/HNSW chỉ đáng khi >100 nghìn vector.
- Đánh giá lại nếu danh mục vượt 50 nghìn ảnh.

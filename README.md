# LookMatch

**Xây dựng LookMatch: ứng dụng tìm sản phẩm thời trang từ ảnh khách gửi dựa trên truy hồi ảnh bằng vector đặc trưng**

*Building LookMatch: A Fashion Product Finder from Customer Photos Based on Embedding-based Image Retrieval*

Đồ án chuyên ngành CMP436, HK1 2026-2027, Khoa CNTT, HUTECH.
Sinh viên: Nguyễn Quốc Duy, MSSV 2380600360, lớp 23DTHC4.
GVHD: TS. Nguyễn Quang Trung.

## Câu định vị

> Đồ án giải quyết **việc nhân viên shop thời trang online mất vài phút và hay nhầm khi tìm sản phẩm từ ảnh khách gửi** cho **nhân viên các shop thời trang online nhỏ**, đo bằng **Recall@5 và thời gian tìm (giây/lượt)**.

## Câu hỏi nghiên cứu và giả thuyết

- **CH1.** Mô hình biểu diễn ảnh nào (CLIP hay DINOv2, có hoặc không cắt nền) cho Recall@5 cao nhất trên ảnh khách gửi thật của shop?
- **CH2.** Dùng LookMatch có giảm thời gian tìm đúng sản phẩm của nhân viên so với tìm thủ công không?
- **H1.** Mô hình tốt nhất đạt Recall@5 >= 80% trên bộ >= 50 ảnh khách gửi thật đã gán nhãn.
- **H2.** Thời gian tìm trung bình giảm từ mức đo thật ở W2 xuống <= 20 giây.

## Bảng trước-sau

| Chỉ số | Cách đo | Trước | Sau | Ngày đo | Bằng chứng |
|---|---|---|---|---|---|
| 1. Recall@5 | >= 50 ảnh khách gửi thật có nhãn mã sản phẩm | (chưa đo) | | | |
| 2. Thời gian tìm đúng sản phẩm (giây/lượt) | Bấm giờ >= 30 lượt, cùng nhân viên | (chưa đo, hạn W2) | | | |

Cột "Sau", "Ngày đo" và "Bằng chứng" để trống cho đến khi có số đo thật. Mục tiêu (H1: Recall@5 >= 80%; H2: <= 20 giây) nằm ở phần giả thuyết ở trên.

## Cấu trúc repo (dự kiến)

```
lookmatch/
  api/          # FastAPI + Dockerfile
  app/          # Flutter
  eval/         # bộ ảnh kiểm thử (đã ẩn danh), nhãn, script tính Recall@K, mAP
  evidence/     # bảng bấm giờ, ảnh xác nhận của chủ shop (đã che thông tin cá nhân)
  docs/         # ADR, C4, báo cáo
  AI_LOG.md     # Nhật ký AI
```

## Cách chạy

(Sẽ bổ sung khi có API và ứng dụng.)

## Quy ước

- Dữ liệu người dùng chỉ thu khi có đồng ý, ẩn danh trước khi đưa vào repo.
- Commit có hỗ trợ của AI dùng tiền tố `[AI]`.
- Tập kiểm thử tách riêng từ đầu, không dùng để chỉnh mô hình.

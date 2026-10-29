# LookMatch

**Xây dựng LookMatch: ứng dụng tìm sản phẩm chăn ga gối nệm từ ảnh khách gửi dựa trên truy hồi ảnh bằng vector đặc trưng**

*Building LookMatch: A Bedding Product Finder from Customer Photos Based on Embedding-based Image Retrieval*

Đồ án chuyên ngành CMP436, HK1 2026-2027, Khoa CNTT, HUTECH.
Sinh viên: Nguyễn Quốc Duy, MSSV 2380600360, lớp 23DTHC4.
GVHD: TS. Nguyễn Quang Trung.

## Câu định vị

> Đồ án giải quyết **việc nhân viên shop chăn ga gối nệm online mất vài phút và hay nhầm khi tìm sản phẩm từ ảnh khách gửi** cho **nhân viên các shop chăn ga gối nệm online nhỏ**, đo bằng **Recall@5 và thời gian tìm (giây/lượt)**.

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

## Cấu trúc repo

```
lookmatch/
  api/          # FastAPI + Dockerfile + tests
  app/          # Flutter (sẽ thêm)
  eval/         # đặc tả đánh giá, bộ ảnh kiểm thử (đã ẩn danh), nhãn, script Recall@K, mAP
  evidence/     # bảng bấm giờ, ảnh xác nhận của chủ shop (đã che thông tin cá nhân)
  docs/         # C4, ADR, ERD
  .github/workflows/ci.yml   # CI chạy pytest
  AI_LOG.md     # Nhật ký AI
```

## Cách chạy

Yêu cầu: Python 3.11 trở lên (hoặc Docker).

**Cách 1: Python**

```bash
pip install -r api/requirements.txt
python -m pytest -q                      # chạy test, kỳ vọng: 2 passed
python -m uvicorn api.main:app --reload  # chạy server
```

Mở trình duyệt: `http://localhost:8000/health` trả về `{"status":"ok"}`; giao diện thử API tại `http://localhost:8000/docs`.

**Cách 2: Docker**

```bash
docker build -t lookmatch -f api/Dockerfile .
docker run -p 8000:8000 lookmatch
```

**Kiểm thử tự động:** GitHub Actions chạy `pytest` mỗi lần push (xem tab Actions).

**Demo (video 30–60 giây):** <https://drive.google.com/file/d/1SOBUdQ74zOjgbhquBs_k333wuubYw1Ed/view?usp=sharing>

## Tài liệu kiến trúc

- [C4 mức 1–3](docs/c4.md)
- ADR: [ADR-1](docs/adr/ADR-001-chon-mo-hinh-bieu-dien.md), [ADR-2](docs/adr/ADR-002-suy-luan-tren-server.md), [ADR-3](docs/adr/ADR-003-faiss-flat-cosine.md)
- [ERD sơ bộ](docs/erd.md)
- [Đặc tả đánh giá](eval/README.md)

## Quy ước

- Dữ liệu người dùng chỉ thu khi có đồng ý, ẩn danh trước khi đưa vào repo.
- Commit có hỗ trợ của AI dùng tiền tố `[AI]`.
- Tập kiểm thử tách riêng từ đầu, không dùng để chỉnh mô hình.

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

## Tình trạng hiện tại (W04)

- Tính năng #1 (chọn ảnh khách, trả top mẫu giống nhất) chạy đầu-cuối: app Flutter, API FastAPI, CLIP, xếp hạng.
- Catalog thử nghiệm: 8 mẫu chăn ga thật của shop Quý Hòa. Ảnh catalog và ảnh khách không đưa lên repo công khai.
- Recall@5 chưa có kết quả chính thức: cần >= 50 ảnh khách thật khác ảnh catalog. Lần chạy thử 4/4 dùng ảnh chụp từ chính catalog nên không dùng làm kết luận.

## Cấu trúc repo

```
lookmatch/
  api/          # FastAPI + Dockerfile + tests
  app/          # Flutter: màn hình chọn ảnh và hiện top kết quả
  eval/         # đặc tả đánh giá, script build_index.py và eval_recall.py
  evidence/     # bảng bấm giờ (khi có), đã che thông tin cá nhân
  docs/         # C4, ADR, ERD
  .github/workflows/ci.yml   # CI chạy pytest
  AI_LOG.md     # Nhật ký AI
```

## Cách chạy

Yêu cầu: Python 3.12 (hoặc Docker cho phần test), Flutter để chạy app.

**Cách 1: Python**

```bash
pip install -r api/requirements-ml.txt   # gồm torch, transformers
python -m pytest -q                      # kỳ vọng: 5 passed
python eval/build_index.py               # tạo chỉ mục từ data/catalog (ảnh catalog không có trên repo)
python -m uvicorn api.main:app --port 8000
```

Thử API không cần app: mở `http://localhost:8000/docs`, chọn `POST /search` và tải ảnh lên.

**Chạy app Flutter**

```bash
cd app
flutter run -d web-server --web-port=5000
```

Mở `http://localhost:5000`, bấm "Chọn ảnh khách".

**Cách 2: Docker (chỉ chạy API/test)**

```bash
docker build -t lookmatch -f api/Dockerfile .
docker run -p 8000:8000 lookmatch
```

**Kiểm thử tự động:** GitHub Actions chạy `pytest` mỗi lần push (xem tab Actions).

**Demo W04 (video 1–2 phút):** <https://drive.google.com/file/d/1BB1ewkq1RC8Vl2q9C4eQ_Wlny1Nb9JLN/view?usp=sharing>

## Tài liệu kiến trúc

- [C4 mức 1–3](docs/c4.md)
- ADR: [ADR-1](docs/adr/ADR-001-chon-mo-hinh-bieu-dien.md), [ADR-2](docs/adr/ADR-002-suy-luan-tren-server.md), [ADR-3](docs/adr/ADR-003-faiss-flat-cosine.md)
- [ERD sơ bộ](docs/erd.md)
- [Đặc tả đánh giá](eval/README.md)

## Quy ước

- Dữ liệu người dùng chỉ thu khi có đồng ý, ẩn danh trước khi đưa vào repo.
- Commit có hỗ trợ của AI dùng tiền tố `[AI]`. Test W04 do AI viết theo đặc tả của sinh viên (xem AI_LOG.md).
- Tập kiểm thử tách riêng từ đầu, không dùng để chỉnh mô hình.

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
| 1. Recall@5 | >= 50 ảnh khách gửi thật có nhãn mã sản phẩm | (chưa đo) | Tạm thời 14/15 ảnh thật = 93,3% (chưa đủ 50, chưa kết luận H1) | 19/11/2026 | `eval/run_eval.py`, báo cáo W06 |
| 2. Thời gian tìm đúng sản phẩm (giây/lượt) | Bấm giờ >= 30 lượt, cùng nhân viên | (xem báo cáo W05) | | | |

Cột "Sau" của chỉ số 1 là số tạm thời trên 15 ảnh thật (trong đó 4 khung hình cùng một video, nên không độc lập). Chưa đủ 50 ảnh nên chưa dùng để kết luận H1. Mục tiêu (H1: Recall@5 >= 80%; H2: <= 20 giây) nằm ở phần giả thuyết ở trên.

## Tình trạng hiện tại (W07, đóng băng tính năng, release v0.9)

- **Tính năng chốt (không thêm mới):** (1) tìm mẫu từ ảnh, (2) danh mục và nhật ký qua Google Sheet, (3) phản hồi Đúng/Sai và thu ca sai, (4) bộ đánh giá Recall@5/MRR. Danh sách đầy đủ: [FEATURES_FROZEN.md](FEATURES_FROZEN.md).
- **Bảo mật (W07):** kiểm tra ảnh tải lên theo nội dung (chỉ JPEG/PNG/WebP, tối đa 8 MB và 40 triệu điểm ảnh, chống bom giải nén), giới hạn tần suất theo IP (mặc định 60 yêu cầu/phút), khoá API `X-API-Key`, làm sạch tên file trước khi ghi Sheet (chống chèn công thức), ảnh lưu lại không còn EXIF/GPS, CORS và khoá đọc từ biến môi trường, container không chạy root. Bằng chứng: `python tools/attack_demo.py`.
- **Kiểm thử:** `python -m pytest -q` (gồm test bảo mật và quét bí mật trong mã nguồn). CI chạy test, build Docker và kiểm tra `/health` mỗi lần push.
- **Đánh giá (W06, `eval/run_eval.py`):** 30 ca, Recall@5 = 28/30 = 93,3%, MRR = 0,781. Riêng ảnh thật: Recall@5 = 14/15, Recall@1 = 8/15. Mới có 15 ảnh khách thật, chưa đủ 50 nên chưa kết luận H1.
- Ảnh catalog và ảnh khách không đưa lên repo công khai.

## Cấu trúc repo

```
lookmatch/
  api/          # FastAPI: main.py, security.py, feedback.py, evaluation.py, sheets.py, Dockerfile, tests/
  app/          # Flutter: chọn ảnh, hiện top kết quả, nút Đúng/Sai
  eval/         # build_index.py, eval_recall.py, run_eval.py, harvest_failures.py,
                # import_real.py, diagnose.py, make_scenarios.py
  integration/  # apps_script.gs (webhook Google Sheet)
  tools/        # attack_demo.py (tấn công thử), bench_nfr.py (đo độ trễ, tỉ lệ lỗi)
  docker-compose.yml, .dockerignore
  evidence/     # bảng bấm giờ (khi có), đã che thông tin cá nhân
  docs/         # C4, ADR, ERD
  .github/workflows/ci.yml   # CI chạy pytest
  AI_LOG.md     # Nhật ký AI
  .env.example  # mẫu biến môi trường (không có giá trị thật)
```

## Cách chạy

Yêu cầu: Python 3.12 (hoặc Docker cho phần test), Flutter để chạy app.

**Cách 1: Python (PowerShell)**

```powershell
pip install -r api/requirements-ml.txt   # gồm torch, transformers
python -m pytest -q                      # kỳ vọng: 30 passed
python eval/build_index.py               # tạo chỉ mục từ data/catalog (ảnh catalog không có trên repo)

$env:LOOKMATCH_CATALOG_CSV_URL='<URL CSV tab danh_muc>'
$env:LOOKMATCH_LOG_WEBHOOK='<URL web app Apps Script>'
$env:LOOKMATCH_LOG_KEY='<KEY tự đặt>'
python -m uvicorn api.main:app --port 8000
```

Ba biến môi trường là tuỳ chọn. Không đặt thì server vẫn chạy, chỉ không đồng bộ Sheet. Không đưa KEY và URL webhook lên repo (xem `.env.example`).

Thử API không cần app: mở `http://localhost:8000/docs`, chọn `POST /search` và tải ảnh lên. `POST /feedback` nhận `search_id`, `verdict` (`dung`, `sai`, `khong_co`) và `true_product`.

**Chạy app Flutter**

```bash
cd app
flutter run -d chrome
```

Bấm "Chọn ảnh khách", rồi bấm Đúng hoặc Sai ở dòng "Mẫu hạng 1 có đúng không?".

**Đánh giá**

```bash
python eval/import_real.py     # nhập ảnh thật theo eval/manifest_real.csv
python eval/run_eval.py        # in tỉ lệ đạt, ghi eval/report.md và eval/hand_read.csv
python eval/diagnose.py        # chẩn đoán ca sai (độ giống mẫu đúng và mẫu nhầm)
```

**Cách 2: Docker Compose (đầy đủ, có mô hình)**

```powershell
copy .env.example .env     # điền giá trị thật vào .env (không commit .env)
python eval/build_index.py # tạo data/index.npy, data/ids.json trên máy (ảnh catalog không có trên repo)
docker compose up --build
```
Mở `http://localhost:8000/health`. Cổng chỉ mở cho máy này (`127.0.0.1`). Bí mật vào container qua `env_file: .env`, không nằm trong image. Lần build đầu tải PyTorch nên lâu.

**Docker nhẹ (chỉ API và test, không có mô hình)**

```bash
docker build -f api/Dockerfile -t lookmatch:light .
docker run --rm -p 8000:8000 lookmatch:light
```

**Biến môi trường bảo mật:** `LOOKMATCH_API_KEY` (khoá API), `LOOKMATCH_CORS_ORIGINS` (nguồn được gọi), `LOOKMATCH_RATE_LIMIT`/`LOOKMATCH_RATE_WINDOW` (giới hạn tần suất). Mô tả trong `.env.example`. App: `flutter run -d chrome --dart-define=LOOKMATCH_API_KEY=<khoá>`.

**Thử tấn công và đo NFR (server đang chạy):**

```powershell
python tools/attack_demo.py --api-key <khoá>
python tools/bench_nfr.py --image data\catalog\<mẫu>\anh1.jpg --api-key <khoá> --n 40
```

**Kiểm thử tự động:** GitHub Actions chạy `pytest`, build Docker và kiểm tra `/health` mỗi lần push (xem tab Actions).

**Video demo:**
- W04: <https://drive.google.com/file/d/1BB1ewkq1RC8Vl2q9C4eQ_Wlny1Nb9JLN/view?usp=sharing>
- W06 (tính năng #3): <https://drive.google.com/file/d/1ZnAAHWk_PBzHSkP-nZsL6waIZuq-v9Bm/view?usp=sharing>

## Tài liệu kiến trúc

- [C4 mức 1–3](docs/c4.md)
- ADR: [ADR-1](docs/adr/ADR-001-chon-mo-hinh-bieu-dien.md), [ADR-2](docs/adr/ADR-002-suy-luan-tren-server.md), [ADR-3](docs/adr/ADR-003-faiss-flat-cosine.md)
- [ERD sơ bộ](docs/erd.md)
- [Đặc tả đánh giá](eval/README.md)

## Quy ước

- Không thêm tính năng mới từ W07 (đã đóng băng). Giới hạn đã biết: app web gửi khoá API trong trình duyệt nên khoá chỉ chống truy cập ngẫu nhiên; chưa có đăng nhập từng người; HTTPS cần reverse proxy khi triển khai thật.
- Dữ liệu người dùng chỉ thu khi có đồng ý, ẩn danh trước khi đưa vào repo. Không đưa ảnh khách, `data/`, `eval/real/`, KEY và URL webhook lên repo.
- Commit có hỗ trợ của AI dùng tiền tố `[AI]`. Code và test W04, W06 do AI viết cùng lượt theo đặc tả của sinh viên, không làm kiểu viết test trước (xem AI_LOG.md).
- Tập kiểm thử tách riêng từ đầu, không dùng để chỉnh mô hình. Mỗi ca eval có nhãn nguồn gốc: `sai_that`, `anh_khach_that`, `ai_tao`, `mo_phong`.

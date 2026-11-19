LookMatch
Xây dựng LookMatch: ứng dụng tìm sản phẩm chăn ga gối nệm từ ảnh khách gửi dựa trên truy hồi ảnh bằng vector đặc trưng
Building LookMatch: A Bedding Product Finder from Customer Photos Based on Embedding-based Image Retrieval
Đồ án chuyên ngành CMP436, HK1 2026-2027, Khoa CNTT, HUTECH.
Sinh viên: Nguyễn Quốc Duy, MSSV 2380600360, lớp 23DTHC4.
GVHD: TS. Nguyễn Quang Trung.
Câu định vị
> Đồ án giải quyết **việc nhân viên shop chăn ga gối nệm online mất vài phút và hay nhầm khi tìm sản phẩm từ ảnh khách gửi** cho **nhân viên các shop chăn ga gối nệm online nhỏ**, đo bằng **Recall@5 và thời gian tìm (giây/lượt)**.
Câu hỏi nghiên cứu và giả thuyết
CH1. Mô hình biểu diễn ảnh nào (CLIP hay DINOv2, có hoặc không cắt nền) cho Recall@5 cao nhất trên ảnh khách gửi thật của shop?
CH2. Dùng LookMatch có giảm thời gian tìm đúng sản phẩm của nhân viên so với tìm thủ công không?
H1. Mô hình tốt nhất đạt Recall@5 >= 80% trên bộ >= 50 ảnh khách gửi thật đã gán nhãn.
H2. Thời gian tìm trung bình giảm từ mức đo thật ở W2 xuống <= 20 giây.
Bảng trước-sau
Chỉ số	Cách đo	Trước	Sau	Ngày đo	Bằng chứng
1. Recall@5	>= 50 ảnh khách gửi thật có nhãn mã sản phẩm	(chưa đo)	Tạm thời 14/15 ảnh thật = 93,3% (chưa đủ 50, chưa kết luận H1)	19/11/2026	`eval/run_eval.py`, báo cáo W06
2. Thời gian tìm đúng sản phẩm (giây/lượt)	Bấm giờ >= 30 lượt, cùng nhân viên	(xem báo cáo W05)			
Cột "Sau" của chỉ số 1 là số tạm thời trên 15 ảnh thật (trong đó 4 khung hình cùng một video, nên không độc lập). Chưa đủ 50 ảnh nên chưa dùng để kết luận H1. Mục tiêu (H1: Recall@5 >= 80%; H2: <= 20 giây) nằm ở phần giả thuyết ở trên.
Tình trạng hiện tại (W06, 20/11/2026)
Tính năng #1: chọn ảnh khách, trả top mẫu giống nhất (app Flutter, API FastAPI, CLIP ViT-B/32, cosine).
Tính năng #2: danh mục và nhật ký qua Google Sheet (CSV công khai và Apps Script webhook, thư mục `integration/`).
Tính năng #3 (mới W06): sau mỗi lượt tìm, nhân viên bấm Đúng, Sai (chọn mã mẫu đúng) hoặc "Shop không có mẫu này". Server lưu ảnh truy vấn và top-K, ghi `data/feedback.jsonl` và tab `phan_hoi` của Sheet. Mỗi lần sai trở thành một ca đánh giá.
Kiểm thử: `python -m pytest -q` cho kết quả 30 passed.
Đánh giá (`eval/run_eval.py`): 30 ca, Recall@5 = 28/30 = 93,3%, MRR = 0,781. Riêng ảnh thật: Recall@5 = 14/15, Recall@1 = 8/15. Ba loại đầu đạt 8/8 (ảnh khách thật), 6/7 (sai thật), 1/2 (ảnh AI); 13/13 ca mô phỏng (ca dễ).
Giới hạn: mới có 15 ảnh khách thật, chưa đủ 50 nên chưa kết luận H1. Ca sai thật mới có 7 (4 lỗi độc lập).
Lỗi chính đã phân tích: các mẫu cùng họ họa tiết sao, khác màu, dễ bị nhầm thứ hạng; catalog chỉ có một ảnh mỗi mẫu. Kế hoạch tuần 7: thêm ảnh catalog khác góc, lấy điểm cao nhất theo mẫu, đo lại.
Ảnh catalog và ảnh khách không đưa lên repo công khai.
Cấu trúc repo
```
lookmatch/
  api/          # FastAPI: main.py, feedback.py, evaluation.py, sheets.py, tests/
  app/          # Flutter: chọn ảnh, hiện top kết quả, nút Đúng/Sai
  eval/         # build_index.py, eval_recall.py, run_eval.py, harvest_failures.py,
                # import_real.py, diagnose.py, make_scenarios.py
  integration/  # apps_script.gs (webhook Google Sheet)
  evidence/     # bảng bấm giờ (khi có), đã che thông tin cá nhân
  docs/         # C4, ADR, ERD
  .github/workflows/ci.yml   # CI chạy pytest
  AI_LOG.md     # Nhật ký AI
  .env.example  # mẫu biến môi trường (không có giá trị thật)
```
Cách chạy
Yêu cầu: Python 3.12 (hoặc Docker cho phần test), Flutter để chạy app.
Cách 1: Python (PowerShell)
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
Chạy app Flutter
```bash
cd app
flutter run -d chrome
```
Bấm "Chọn ảnh khách", rồi bấm Đúng hoặc Sai ở dòng "Mẫu hạng 1 có đúng không?".
Đánh giá
```bash
python eval/import_real.py     # nhập ảnh thật theo eval/manifest_real.csv
python eval/run_eval.py        # in tỉ lệ đạt, ghi eval/report.md và eval/hand_read.csv
python eval/diagnose.py        # chẩn đoán ca sai (độ giống mẫu đúng và mẫu nhầm)
```
Cách 2: Docker (chỉ chạy API/test)
```bash
docker build -t lookmatch -f api/Dockerfile .
docker run -p 8000:8000 lookmatch
```
Kiểm thử tự động: GitHub Actions chạy `pytest` mỗi lần push (xem tab Actions).
Video demo:
W04: https://drive.google.com/file/d/1BB1ewkq1RC8Vl2q9C4eQ_Wlny1Nb9JLN/view?usp=sharing
W06 (tính năng #3): https://drive.google.com/file/d/1ZnAAHWk_PBzHSkP-nZsL6waIZuq-v9Bm/view?usp=sharing
Tài liệu kiến trúc
C4 mức 1–3
ADR: ADR-1, ADR-2, ADR-3
ERD sơ bộ
Đặc tả đánh giá
Quy ước
Dữ liệu người dùng chỉ thu khi có đồng ý, ẩn danh trước khi đưa vào repo. Không đưa ảnh khách, `data/`, `eval/real/`, KEY và URL webhook lên repo.
Commit có hỗ trợ của AI dùng tiền tố `[AI]`. Code và test W04, W06 do AI viết cùng lượt theo đặc tả của sinh viên, không làm kiểu viết test trước (xem AI_LOG.md).
Tập kiểm thử tách riêng từ đầu, không dùng để chỉnh mô hình. Mỗi ca eval có nhãn nguồn gốc: `sai_that`, `anh_khach_that`, `ai_tao`, `mo_phong`.

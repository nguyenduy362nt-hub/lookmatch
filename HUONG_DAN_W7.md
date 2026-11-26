# Hướng dẫn thực hiện tuần 7 (LookMatch)

Lệnh PowerShell, chạy ở thư mục `lm` (nơi có `api\`, `eval\`, `app\`) trừ khi ghi khác.
Giải nén gói `LookMatch_W7.zip`, chép đè các file vào `lm\` (giữ nguyên cấu trúc thư mục).

## Bước 0. Chép file và chạy test (10 phút)
```powershell
cd D:\DoAn\LookMatch_W3_scaffold\lm
.\.venv\Scripts\Activate.ps1
python -m pytest -q
```
Kỳ vọng: khoảng 63 passed (30 test cũ + 19 test bảo mật thuần Python + 1 quét bí mật + 13 test bảo mật qua HTTP). Nếu con số khác, cứ ghi con số thật em thấy.
Test nào đỏ thì chụp màn hình và gửi lại, đừng sửa assert cho khớp.

## Bước 1. Bảo mật: chạy thật và thu minh chứng (30 phút)
Terminal 1 (server, đặt khoá API của em, chuỗi tự đặt, không chụp lộ ra màn hình):
```powershell
$env:LOOKMATCH_API_KEY='<khoá API tự đặt>'
$env:LOOKMATCH_CATALOG_CSV_URL='<URL CSV danh_muc>'
$env:LOOKMATCH_LOG_WEBHOOK='<URL Apps Script>'
$env:LOOKMATCH_LOG_KEY='<KEY Apps Script>'
python -m uvicorn api.main:app --port 8000
```
Terminal 2 (tấn công thử, chụp bảng kết quả làm Hình W7-1):
```powershell
python tools/attack_demo.py --api-key <khoá API tự đặt>
```
Kỳ vọng 10/10 đúng mong đợi. Dòng 7 (tên file công thức): mở Sheet tab `nhat_ky`, chụp ô cột file có dấu nháy `'=HYPERLINK...` (Hình W7-2).
Lưu ý: sau lần chạy này IP của em bị giới hạn khoảng 1 phút (đó chính là biện pháp chặn đang hoạt động).

App Flutter có khoá:
```powershell
cd app
flutter run -d chrome --dart-define=LOOKMATCH_API_KEY=<khoá API tự đặt>
```
Thử thêm: chạy app KHÔNG có `--dart-define` thì app báo "Chưa được phép dùng: thiếu hoặc sai khoá API" (Hình W7-3).

## Bước 2. Đo NFR (20 phút)
Khi server đang chạy:
```powershell
python tools/bench_nfr.py --image data\catalog\panda_kem\anh1.jpg --api-key <khoá API> --n 40
python eval/run_eval.py
```
Ghi bảng p50/p95/tỉ lệ lỗi và dòng "Đạt x/y" vào Phần D của Word. Chạy trên máy nào (CPU gì) thì ghi rõ.

## Bước 3. Docker (30–45 phút, lần build đầu có torch nên lâu)
```powershell
copy .env.example .env      # rồi mở .env, điền giá trị thật, chỉ điền sau dấu =
docker compose up --build
```
Mở `http://localhost:8000/health` thấy `{"status":"ok"}`. Chụp terminal `docker compose ps` có trạng thái `healthy` (Hình W7-4).
Muốn thử nhanh image nhẹ (không mô hình):
```powershell
docker build -f api/Dockerfile -t lookmatch:light .
docker run --rm -p 8000:8000 lookmatch:light
```
Kiểm tra không chạy root: `docker exec <tên container> id -u` phải ra `10001`.
Nếu chạy `docker compose up` báo lỗi quyền ghi thư mục `data`, chụp lỗi gửi lại.

## Bước 4. Đẩy lên GitHub và lấy CI xanh (20 phút)
Thêm/ghi đè qua GitHub web (Add file → Upload files hoặc Create new file cho file ẩn):
`api/security.py`, `api/main.py`, `api/Dockerfile`, `api/tests/*` (test_security.py, test_security_api.py, test_no_secrets.py, conftest.py), `tools/*`, `.github/workflows/ci.yml`, `docker-compose.yml`, `.dockerignore`, `.env.example`, `app/lib/main.dart`, `FEATURES_FROZEN.md`, `README.md`. Thêm 3 dòng trong `gitignore_them_dong_W7.txt` vào `.gitignore`.
Vào tab Actions: đợi 3 job `test`, `docker`, `audit`. `audit` có thể vàng (cảnh báo thư viện), không sao. Hai job `test` và `docker` phải xanh. Chụp (có ngày giờ) và copy link lần chạy xanh gần nhất (Hình W7-5).
Nếu đỏ: bấm vào job đỏ, mở bước đỏ, đọc dòng lỗi đầu tiên, chụp gửi lại.

## Bước 5. Tag v0.9 (5 phút)
GitHub → Releases → Draft a new release → Tag: `v0.9` (Create new tag on publish) → Title `LookMatch v0.9 (đóng băng tính năng)` → mô tả dán nội dung `FEATURES_FROZEN.md` → Publish. Copy link release.

## Bước 6. UX theo góp ý của người dùng thật (hạn chót: sáng 26/11)
Gửi tin nhắn cho chủ shop Quý Hòa hoặc nhân viên (xem mẫu trong chat), nhờ dùng thử app khoảng 5 phút rồi trả lời 3 câu hỏi. Chụp tin nhắn (che số điện thoại, tên). Em chuyển lời họ cho mình, mình soạn sửa giao diện; em chụp ảnh trước/sau.
Không tự đặt ra góp ý. Nếu chỉ có 2 người dùng thật, ghi đúng số đó.

## Bước 7. Tự học (bắt buộc, em tự đọc)
- OWASP Top 10: đọc 3 mục (gợi ý trong Word, em chọn 3 mục thật sự đọc), ghi 1 dòng mỗi mục.
- Docker "Get started" và GitHub Actions quickstart: làm theo, ghi 2–3 ý đã áp dụng.

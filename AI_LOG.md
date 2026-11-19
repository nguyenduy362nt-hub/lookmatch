# Nhật ký AI (W04)

## 05/11/2026 — Tính năng #1: POST /search

- **Test (commit 691f048):** AI viết 3 test theo đặc tả em đưa; em đã đọc và giải thích được từng dòng.
  Chạy lúc chưa có code: lỗi `No module named 'api.search'` (test đỏ).
- **Code (commit d742656, message mặc định "Add files via upload"):** AI viết `api/search.py`,
  `api/main.py`, `api/embedder.py`. Chạy lại test: 5 passed, CI xanh.
- Em chưa hiểu / đã sửa: (em ghi 3 điều thật sau khi đọc diff)
## W06 (16–22/11/2026)
- Công cụ: Claude. Nhờ viết code và test cho tính năng #3 (phản hồi Đúng/Sai), các script eval (harvest_failures, run_eval, import_real, diagnose) và bản nháp Chương 3.
- Code và test do AI viết trong cùng một lượt, không làm kiểu viết test trước (TDD). Em chạy pytest trên máy (30 passed), chạy app và kiểm tra đầu–cuối.
- Lỗi phát hiện khi chạy thật: phản hồi "sai" nhưng mã đúng trùng hạng 1 (TC15). Em và AI sửa bằng cách trả lỗi 422 và thêm test.
- Em tự đọc, chạy lại và sửa: [ghi những chỗ em đã sửa hoặc đọc hiểu].

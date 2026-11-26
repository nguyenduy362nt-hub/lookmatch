"""Bắn thử các đầu vào độc hại vào server LookMatch đang chạy và in bảng kết quả (làm minh chứng bảo mật).

Cách dùng (server đang chạy ở cổng 8000, đã đặt LOOKMATCH_API_KEY):
    python tools/attack_demo.py --api-key <khoá>
Bước 'đoán khoá' và 'gọi dồn' để cuối cùng vì sau đó IP của em bị giới hạn khoảng 1 phút.
"""
import argparse
import io
import sys

import httpx
from PIL import Image


def anh(fmt="PNG", size=(8, 8), mode="RGB"):
    buf = io.BytesIO()
    Image.new(mode, size, "white" if mode == "RGB" else 0).save(buf, fmt)
    return buf.getvalue()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", default="http://127.0.0.1:8000")   # 127.0.0.1, không dùng "localhost": trên Windows localhost thử IPv6 trước làm mỗi yêu cầu chậm ~2 giây
    ap.add_argument("--api-key", default="")
    ap.add_argument("--flood", type=int, default=80, help="số yêu cầu gọi dồn")
    a = ap.parse_args()
    client = httpx.Client(timeout=60)      # dùng lại kết nối, để gọi dồn đủ nhanh
    ok_h = {"X-API-Key": a.api_key} if a.api_key else {}
    rows = []

    def tim(ten, noi_dung, headers=ok_h):
        return client.post(f"{a.url}/search", files={"file": (ten, noi_dung, "image/jpeg")},
                          headers=headers, timeout=60).status_code

    def ghi(ten, mong_doi, thuc_te, nghia=""):
        rows.append((ten, mong_doi, thuc_te, "CHẶN/ĐÚNG" if thuc_te in mong_doi else "KHÔNG NHƯ MONG ĐỢI", nghia))

    ghi("1. File HTML/script đổi đuôi .jpg", (400,), tim("virus.jpg", b"<script>alert(1)</script>"))
    ghi("2. Ảnh GIF (định dạng không cho phép)", (415,), tim("a.gif", anh("GIF")))
    ghi("3. Ảnh 9 MB (vượt 8 MB)", (413,), tim("big.jpg", b"\xff\xd8\xff" + b"0" * (9 * 1024 * 1024)))
    ghi("4. PNG 8000x8000 điểm ảnh (64 triệu)", (413,), tim("pixel.png", anh("PNG", (8000, 8000), "1")))
    ghi("5. Bom giải nén 20000x20000", (413,), tim("bomb.png", anh("PNG", (20000, 20000), "1")))
    r = client.post(f"{a.url}/feedback", json={"search_id": "../../etc/passwd", "verdict": "dung"},
                   headers=ok_h, timeout=30).status_code
    ghi("6. search_id kiểu path traversal", (400, 422), r)
    ghi("7. Tên file chứa công thức Sheet", (200,), tim('=HYPERLINK("http://evil.example","x").png', anh()),
        "Được nhận nhưng phải kiểm tra tab nhat_ky: ô file bắt đầu bằng dấu nháy '")
    ghi("8. Không có khoá API", (401,), tim("a.png", anh(), headers={}),
        "" if a.api_key else "Server chưa đặt khoá thì trả 200 là đúng")
    ghi("9. Khoá API sai", (401,), tim("a.png", anh(), headers={"X-API-Key": "sai-khoa"}))
    codes = [client.post(f"{a.url}/feedback", json={"search_id": "x", "verdict": "zzz"}, headers=ok_h,
                        timeout=30).status_code for _ in range(a.flood)]
    dau = next((i + 1 for i, c in enumerate(codes) if c == 429), None)
    ghi(f"10. Gọi dồn {a.flood} yêu cầu liên tiếp", (429,), 429 if dau else codes[-1],
        f"Bị chặn từ yêu cầu thứ {dau}" if dau else "Không bị chặn")

    print("\n| Tấn công | Mã mong đợi | Mã nhận được | Kết luận | Ghi chú |")
    print("|---|---|---|---|---|")
    for t, m, c, k, n in rows:
        print(f"| {t} | {'/'.join(map(str, m))} | {c} | {k} | {n} |")
    bad = [r for r in rows if r[3] != "CHẶN/ĐÚNG"]
    # Khi server chưa bật khoá API, dòng 8 trả 200 là bình thường
    bad = [r for r in bad if not (r[0].startswith("8.") and not a.api_key)]
    print(f"\nKết quả: {len(rows) - len(bad)}/{len(rows)} đúng mong đợi")
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
